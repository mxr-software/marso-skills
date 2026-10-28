"""Place a scene in Blender using owned entity Empties and separate geometry groups.

Run inside Blender: runpy.run_path(<this file>)["place"](placement_path, imports_path).
Each graph node has an Empty. Its geometry and supported entity Empties are siblings.
Import `instances` contains one list of object names per complete imported asset.
Legacy results with only `objects` are treated as one compound asset. No physics is authored.
"""
import json
import math
import pathlib
import uuid

import bpy
from mathutils import Matrix, Vector


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig")) if path else {}


def tag(obj, run_id, gid, role):
    obj["marso_run_id"], obj["marso_global_id"], obj["marso_role"] = run_id, gid, role


def owned(coll, run_id, gid, role):
    found = [o for o in coll.objects if o.get("marso_run_id") == run_id
             and o.get("marso_global_id") == gid and o.get("marso_role") == role]
    if len(found) > 1:
        raise ValueError(f"Duplicate owned {role} for {gid}; resolve before placing")
    return found[0] if found else None


def collection_for(name, run_id):
    found = [c for c in bpy.context.scene.collection.children_recursive if c.get("marso_run_id") == run_id]
    if len(found) > 1:
        raise ValueError("Multiple collections own this run; resolve before placing")
    if found:
        return found[0]
    coll = bpy.data.collections.new(name)  # Blender uniquifies unrelated names.
    coll["marso_run_id"] = run_id
    bpy.context.scene.collection.children.link(coll)
    return coll


def parent_keep(obj, parent):
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_world = world


def empty(name, coll, run_id, gid, role, parent=None):
    obj = owned(coll, run_id, gid, role)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
        obj.empty_display_type, obj.empty_display_size = "PLAIN_AXES", 0.15
        coll.objects.link(obj)
        tag(obj, run_id, gid, role)
        obj.parent = parent
    elif obj.type != "EMPTY":
        raise ValueError(f"{obj.name}: expected an Empty for {role}")
    return obj


def parts(group):
    return [o for o in group.children_recursive if o.get("marso_role") != "retired-placeholder"]


def bounds(group):
    points = [o.matrix_world @ Vector(c) for o in parts(group)
              if o.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"} for c in o.bound_box]
    if not points:
        points = [group.matrix_world.translation.copy()]
    return (Vector(tuple(min(p[i] for p in points) for i in range(3))),
            Vector(tuple(max(p[i] for p in points) for i in range(3))))


def placeholder(group, dims, coll, run_id, gid):
    obj = owned(coll, run_id, gid, "placeholder")
    if obj is None:
        mesh = bpy.data.meshes.new(group.name + "_box")
        obj = bpy.data.objects.new(mesh.name, mesh)
        coll.objects.link(obj)
        obj.parent, obj.display_type = group, "WIRE"
        tag(obj, run_id, gid, "placeholder")
    w, d, h = (max(float(v), 0.01) for v in dims)
    obj.data.clear_geometry()
    obj.data.from_pydata([(x*w/2, y*d/2, z*h) for z in (0, 1) for y in (-1, 1) for x in (-1, 1)], [],
                        [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    obj.data.update()
    group["marso_content"] = "placeholder"
    return obj


def import_groups(result, run_id, warnings):
    groups = result.get("instances") or ([result.get("objects", [])] if result.get("objects") else [])
    out, seen = [], set()
    for names in groups:
        objects = [bpy.data.objects.get(name) for name in names]
        if any(o is None for o in objects):
            warnings.append("Import instance has missing objects; re-import or use its existing owned entity")
            continue
        expanded = objects if result.get("instances") else list(dict.fromkeys(
            o for obj in objects for o in [obj, *obj.children_recursive]))
        if any(o.get("marso_run_id") for o in expanded):
            if any(o.get("marso_run_id") not in (None, run_id) for o in expanded):
                warnings.append("An import belongs to another run; it was left untouched")
            continue
        if any(o.as_pointer() in seen for o in expanded):
            raise ValueError("An imported object appears in more than one instance")
        seen.update(o.as_pointer() for o in expanded)
        if expanded:
            out.append(expanded)
    return out


def adopt(objects, group, coll, run_id, gid):
    roots = [o for o in objects if o.parent not in objects]
    for obj in objects:
        if coll not in obj.users_collection:
            coll.objects.link(obj)  # Preserve existing collection memberships.
        tag(obj, run_id, gid, "part")
    for obj in roots:
        parent_keep(obj, group)
    group["marso_content"] = "asset"


def duplicate(source, group, coll, run_id, gid):
    twins = {obj: obj.copy() for obj in parts(source)}  # shares mesh data, not object transforms
    for obj, twin in twins.items():
        coll.objects.link(twin)
        twin.parent = twins.get(obj.parent, group)
        twin.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
        twin.matrix_basis = obj.matrix_basis.copy()
        tag(twin, run_id, gid, "part")
    group.matrix_basis = source.matrix_basis.copy()
    group["marso_content"] = "asset"


def normalise(group, flags):
    if "laid-flat-x" in flags or "laid-flat-y" in flags:
        axis = "Y" if "laid-flat-x" in flags else "X"
        group.matrix_world = Matrix.Rotation(math.pi / 2, 4, axis) @ group.matrix_world
    bpy.context.view_layer.update()
    low, high = bounds(group)
    group.location -= Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    bpy.context.view_layer.update()


def add_camera(camera, coll, run_id, photo):
    cam = owned(coll, run_id, "camera", "camera")
    if cam is None:
        cam = bpy.data.objects.new("establishing_camera", bpy.data.cameras.new("establishing_camera"))
        coll.objects.link(cam)
        tag(cam, run_id, "camera", "camera")
    cam.data.sensor_fit, cam.data.angle = "HORIZONTAL", math.radians(camera["hfov_deg"])
    cam.location, cam.rotation_mode = camera["location"], "XYZ"
    cam.rotation_euler = [math.radians(a) for a in camera["rotation_euler_deg"]]
    bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = camera["resolution"]
    bpy.context.scene.camera = cam
    if photo and camera.get("photo") and pathlib.Path(camera["photo"]).exists():
        image = bpy.data.images.load(camera["photo"], check_existing=True)
        cam.data.background_images.clear()
        background = cam.data.background_images.new()
        background.image, background.alpha, background.display_depth = image, 0.5, "FRONT"
        cam.data.show_background_images = True
    return cam


def place(placement_path, imports_path=None, collection_name=None, photo=True):
    plan, imports = read(placement_path), read(imports_path)
    run_id = plan.get("run_id") or str(uuid.uuid5(uuid.NAMESPACE_URL,
                      str(pathlib.Path(placement_path).resolve()) + "|" + str(plan.get("project"))))
    anchors = plan.get("anchors", [])
    rows = [*anchors, *sorted(plan.get("objects", []), key=lambda r: r["order"])]
    ids = [r["global_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate global ids in placement plan")
    parents = {r["global_id"]: r.get("parent") for r in rows}
    for gid in ids:
        visited, current = set(), gid
        while current in parents:
            if current in visited:
                raise ValueError("Cycle in placement support hierarchy")
            visited.add(current)
            current = parents[current]
    coll = collection_for(collection_name or plan.get("project") or "placed_scene", run_id)
    report = dict(collection=coll.name, run_id=run_id, placed=[], duplicated=[], boxes=[],
                  not_imported=[], unused_imports=[], warnings=[])
    pools = {aid: import_groups(result or {}, run_id, report["warnings"]) for aid, result in imports.items()}
    # Some importers leave duplicate parts parented to the original instance. Detach
    # cross-instance links before moving any instance, preserving each part's world pose.
    for groups in pools.values():
        for objects in groups:
            for obj in objects:
                if obj.parent and obj.parent not in objects:
                    parent_keep(obj, None)
    bpy.context.view_layer.update()
    first, made = {}, {}
    for row in rows:
        gid = row["global_id"]
        entity = empty(row["name"], coll, run_id, gid, "entity")
        parent_keep(entity, None)
        entity.matrix_world = Matrix.Identity(4)
        made[gid] = entity
    bpy.context.view_layer.update()
    for row in rows:
        gid, entity = row["global_id"], made[row["global_id"]]
        aid = row.get("asset_id")
        entity["marso_parent_id"] = row.get("parent") or ""
        entity["marso_relation"] = row.get("relation") or ""
        if aid:
            entity["marso_asset_id"] = aid
            pbr_id = (plan.get("assets", {}).get(aid) or {}).get("pbr_asset_id")
            if pbr_id:
                entity["marso_pbr_asset_id"] = pbr_id
        if plan.get("project_id"):
            entity["marso_project_id"] = plan["project_id"]
        group = empty(row["name"] + "__geometry", coll, run_id, gid, "geometry", entity)
        if row.get("object") == "plane" and row.get("corners"):
            wall = owned(coll, run_id, gid, "wall")
            if wall is None:
                wall = bpy.data.objects.new(row["name"] + "__surface", bpy.data.meshes.new(row["name"]))
                coll.objects.link(wall)
                wall.parent = group
                tag(wall, run_id, gid, "wall")
            wall.data.clear_geometry()
            wall.data.from_pydata(row["corners"], [], [(0, 1, 2, 3)])
            wall.data.update()
        elif row in anchors:
            pass
        elif group.get("marso_content") != "asset":
            available = pools.get(aid)
            if row["kind"] == "asset" and (available or aid in first):
                old = owned(coll, run_id, gid, "placeholder")
                if old:
                    old["marso_role"] = "retired-placeholder"
                    old.hide_viewport = old.hide_render = True
                if available:
                    adopt(available.pop(0), group, coll, run_id, gid)
                    normalise(group, row.get("flags", []))
                else:
                    duplicate(first[aid], group, coll, run_id, gid)
                    report["duplicated"].append(entity.name)
            else:
                box = placeholder(group, row["dimensions_m"], coll, run_id, gid)
                report["boxes"].append(box.name)
                if row["kind"] == "asset":
                    report["not_imported"].append(entity.name)
        if aid and group.get("marso_content") == "asset":
            first.setdefault(aid, group)
        entity.matrix_world = Matrix.Translation(Vector(row.get("location") or (0, 0, 0))) @ \
                              Matrix.Rotation(math.radians(row.get("rotation_z_deg", 0)), 4, "Z")
        bpy.context.view_layer.update()
        low, high = bounds(group)
        report["placed"].append(dict(name=entity.name, geometry=group.name, global_id=gid,
                                     dimensions_m=[round(v, 3) for v in high - low]))
    # Parent after placement so moving a parent's frame never double-moves its children.
    for row in rows:
        parent = made.get(row.get("parent"))
        if row.get("parent") and parent is None:
            report["warnings"].append(f"{row['global_id']}: support parent missing; left at top level")
        parent_keep(made[row["global_id"]], parent)
        bpy.context.view_layer.update()
    report["unused_imports"] = [o.name for groups in pools.values() for group in groups for o in group]
    if plan.get("camera"):
        report["camera"] = add_camera(plan["camera"], coll, run_id, photo).name
    bpy.context.view_layer.update()
    return report
