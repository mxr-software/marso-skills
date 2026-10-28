"""Build a placed scene in Blender from placement.json and the import results.

Runs inside Blender, through a Python-execution tool:

    import runpy
    place = runpy.run_path(r"<skill>/scripts/place_in_blender.py")["place"]
    result = place(r"<run>/placement.json", r"<run>/imports.json")

`imports.json` maps each asset_id to its `import_scene_asset` result ({objects, dimensions_m,
minted}). The function creates or reuses a collection named after the project, builds the
anchors (floor and ceiling empties, wall planes), positions each object instance in
placement order with its bounding-box bottom centre at the planned location, parents it
to its graph parent keeping its world transform, makes linked duplicates when there are
fewer imported objects than instances, builds boxes for placeholders, and adds a camera
matched to the establishing photograph with the photograph as its background. Running it
again re-places the same objects, so placement.json can be corrected and re-run. Returns
a dict report; nothing is deleted.
"""
import json
import math
import pathlib

import bpy
from mathutils import Matrix, Vector

CAMERA_NAME = "establishing_camera"


def read(path):
    if not path:
        return {}
    file = pathlib.Path(path)
    if not file.exists():
        return {}
    return json.loads(file.read_text(encoding="utf-8-sig"))


def collection_for(name):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    return coll


def move_to(obj, coll):
    for target in [obj, *obj.children_recursive]:
        if coll not in target.users_collection:
            coll.objects.link(target)
        for other in list(target.users_collection):
            if other != coll:
                other.objects.unlink(target)


def unparent_keep(obj):
    if obj.parent is not None:
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world


def parent_keep(obj, parent):
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world


def own_parts(obj):
    """The object and the parts it was imported with, not the graph children parented to it."""
    parts, stack = [obj], list(obj.children)
    while stack:
        item = stack.pop()
        if "marso_global_id" in item:
            continue
        parts.append(item)
        stack.extend(item.children)
    return parts


def world_bounds(obj):
    """Min and max corners over the object's own meshes."""
    points = []
    for item in own_parts(obj):
        if item.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"}:
            points += [item.matrix_world @ Vector(corner) for corner in item.bound_box]
    if not points:
        points = [obj.matrix_world.translation.copy()]
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high


def box_object(name, dims, coll):
    w, d, h = (max(v, 0.01) for v in dims)
    obj = bpy.data.objects.get(name)
    if obj is None:
        mesh = bpy.data.meshes.new(name)
        verts = [(x * w / 2, y * d / 2, z * h) for z in (0, 1) for y in (-1, 1) for x in (-1, 1)]
        faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        obj.display_type = "WIRE"
        coll.objects.link(obj)
    return obj


def anchor_object(row, coll):
    name = row["name"]
    obj = bpy.data.objects.get(name)
    if row.get("object") == "plane" and row.get("corners"):
        if obj is None:
            mesh = bpy.data.meshes.new(name)
            mesh.from_pydata([tuple(c) for c in row["corners"]], [], [(0, 1, 2, 3)])
            mesh.update()
            obj = bpy.data.objects.new(name, mesh)
            coll.objects.link(obj)
        else:
            mesh = obj.data
            for vertex, corner in zip(mesh.vertices, row["corners"]):
                vertex.co = Vector(corner)
            mesh.update()
        obj.location = (0.0, 0.0, 0.0)
    else:
        if obj is None:
            obj = bpy.data.objects.new(name, None)
            obj.empty_display_type = "PLAIN_AXES"
            coll.objects.link(obj)
        obj.location = Vector(row.get("location") or (0.0, 0.0, 0.0))
    move_to(obj, coll)
    obj["marso_global_id"] = row["global_id"]
    return obj


def add_camera(camera, coll, photo=True):
    cam = bpy.data.objects.get(CAMERA_NAME)
    if cam is None:
        cam = bpy.data.objects.new(CAMERA_NAME, bpy.data.cameras.new(CAMERA_NAME))
        coll.objects.link(cam)
    data = cam.data
    data.sensor_fit = "HORIZONTAL"
    data.angle = math.radians(camera["hfov_deg"])
    cam.location = Vector(camera["location"])
    cam.rotation_mode = "XYZ"
    cam.rotation_euler = [math.radians(a) for a in camera["rotation_euler_deg"]]
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = camera["resolution"]
    scene.camera = cam
    if photo and camera.get("photo") and pathlib.Path(camera["photo"]).exists():
        image = bpy.data.images.load(camera["photo"], check_existing=True)
        data.show_background_images = True
        background = next((b for b in data.background_images if b.image == image), None)
        if background is None:
            background = data.background_images.new()
            background.image = image
        background.alpha = 0.5
        background.display_depth = "FRONT"
    return cam


def place(placement_path, imports_path=None, collection_name=None, photo=True):
    plan = read(placement_path)
    imports = read(imports_path)
    coll = collection_for(collection_name or plan.get("project") or "placed_scene")
    report = {"collection": coll.name, "placed": [], "duplicated": [], "boxes": [], "not_imported": [],
              "unused_imports": [], "warnings": []}
    made = {}

    for row in plan.get("anchors", []):
        made[row["global_id"]] = anchor_object(row, coll)

    # Imported objects per asset, top-level only; objects already named for an instance are taken.
    names = {row["name"] for row in plan.get("objects", [])}
    pools = {}
    for asset_id, result in imports.items():
        objs = [bpy.data.objects.get(n) for n in (result or {}).get("objects", [])]
        objs = [o for o in objs if o is not None and (o.parent is None or o.parent.name not in
                                                     (result or {}).get("objects", []))]
        pools[asset_id] = [o for o in objs if o.name not in names]
    first = {}

    for row in sorted(plan.get("objects", []), key=lambda r: r["order"]):
        obj = bpy.data.objects.get(row["name"])
        asset_id = row.get("asset_id")
        if obj is None and row["kind"] == "asset" and asset_id in imports:
            if pools.get(asset_id):
                obj = pools[asset_id].pop(0)
            elif asset_id in first:
                source = first[asset_id]
                obj = source.copy()  # a linked duplicate: the mesh data is shared
                coll.objects.link(obj)
                for child in own_parts(source)[1:]:
                    if child.parent is not source:
                        continue
                    twin = child.copy()
                    coll.objects.link(twin)
                    twin.parent = obj
                    twin.matrix_parent_inverse = child.matrix_parent_inverse.copy()
                report["duplicated"].append(row["name"])
            if obj is not None:
                obj.name = row["name"]
        if obj is None:
            if row["kind"] == "asset":
                report["not_imported"].append(row["name"])
            obj = box_object(row["name"] if row["kind"] == "placeholder" else row["name"] + "_box",
                             row["dimensions_m"], coll)
            report["boxes"].append(obj.name)
        if asset_id:
            first.setdefault(asset_id, obj)
        move_to(obj, coll)
        unparent_keep(obj)
        obj.rotation_mode = "XYZ"
        # Every run starts from the orientation the object was imported with, so a second run never
        # turns it again: the first one keeps that rotation on the object.
        if "marso_base_rotation" not in obj:
            obj["marso_base_rotation"] = list(obj.rotation_euler)
        obj.rotation_euler = obj["marso_base_rotation"]
        bpy.context.view_layer.update()
        flags = row.get("flags") or []
        if "laid-flat-x" in flags or "laid-flat-y" in flags:
            # Standing on edge as generated: turn it down onto its broad face, then yaw as planned.
            axis = "Y" if "laid-flat-x" in flags else "X"
            turn = Matrix.Rotation(math.radians(90), 4, axis)
            location = obj.matrix_world.translation.copy()
            obj.matrix_world = turn @ obj.matrix_world
            obj.matrix_world.translation = location
            report["warnings"].append(f"{row['name']}: laid flat (generated standing on edge)")
        obj.rotation_euler.z = math.radians(row["rotation_z_deg"])
        obj.location = Vector(row["location"])
        bpy.context.view_layer.update()
        low, high = world_bounds(obj)
        bottom_centre = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
        obj.location += Vector(row["location"]) - bottom_centre
        bpy.context.view_layer.update()
        parent = made.get(row.get("parent"))
        if parent is not None:
            parent_keep(obj, parent)
        else:
            report["warnings"].append(f"{row['name']}: parent {row.get('parent')} not built; left at top level")
        obj["marso_global_id"] = row["global_id"]
        if asset_id:
            obj["marso_asset_id"] = asset_id
        made[row["global_id"]] = obj
        size = high - low
        report["placed"].append({"name": obj.name, "dimensions_m": [round(size.x, 3), round(size.y, 3),
                                                                     round(size.z, 3)]})

    for asset_id, rest in pools.items():
        report["unused_imports"] += [o.name for o in rest]
    if plan.get("camera"):
        report["camera"] = add_camera(plan["camera"], coll, photo).name
    bpy.context.view_layer.update()
    return report
