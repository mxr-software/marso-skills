"""Place a set piece's instances in Blender from a placement list; no scene changes until called.

    tag_master(obj, part, variant)   mark the object that stands for one part and variant
    place(placements_path, ...)      make every instance as a linked duplicate of its master
    check(placements_path, ...)      compare what is in the scene with the list

The placement list is `marso/set-piece-placements@1`: metres, Z up, front facing -Y, with each
position being where the instance's anchor point goes (the centre of its base, or of its top for a
part that hangs). Instances share their master's mesh and material data.
"""

import json
import math

import bpy
from mathutils import Matrix, Vector

SCHEMA = "marso/set-piece-placements@1"
PART, VARIANT, SLOT, INSTANCE, ROOT = ("marso_set_part", "marso_set_variant", "marso_set_slot",
                                       "marso_set_instance", "marso_set_piece")


def _family(root):
    return [root] + list(root.children_recursive)


def _read(placements_path):
    with open(placements_path, encoding="utf-8") as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        raise ValueError("Not a placement list: schema must be " + SCHEMA)
    if not doc.get("instances"):
        raise ValueError("The placement list has no instances.")
    return doc


def tag_master(obj, part, variant):
    """Record on a master's root which part and variant it is, so `place` can find it."""
    if obj.get(INSTANCE):
        raise ValueError("{} is a placed instance, not a master.".format(obj.name))
    obj[PART], obj[VARIANT] = str(part), str(variant)
    return {"object": obj.name, "part": obj[PART], "variant": obj[VARIANT]}


def _masters(doc, named):
    """The root object for each part and variant the list needs; every missing one is reported together."""
    tagged = {}
    for obj in bpy.data.objects:
        if obj.get(PART) and obj.get(VARIANT) and not obj.get(INSTANCE):
            tagged.setdefault((obj[PART], obj[VARIANT]), []).append(obj)
    found, problems = {}, []
    for master in doc["masters"]:
        key = (master["part"], master["variant"])
        label = "{}/{}".format(*key)
        name = (named or {}).get(label)
        if name is not None:
            obj = bpy.data.objects.get(name)
            if obj is None:
                problems.append("{}: no object named {!r}".format(label, name))
                continue
        else:
            candidates = tagged.get(key, [])
            if len(candidates) != 1:
                problems.append("{}: {} tagged masters (need exactly one; tag it with tag_master)".format(
                    label, len(candidates)))
                continue
            obj = candidates[0]
        if not any(o.type == "MESH" and len(o.data.polygons) for o in _family(obj)):
            problems.append("{}: {} has no mesh with faces".format(label, obj.name))
            continue
        found[key] = obj
    if problems:
        raise ValueError("Masters missing or unusable: " + "; ".join(problems))
    return found


def _anchor_offset(root, anchor):
    """From the master root's origin to its anchor point, in world axes."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    points = []
    for obj in _family(root):
        if obj.type != "MESH" or not len(obj.data.polygons):
            continue
        evaluated = obj.evaluated_get(depsgraph)
        points += [evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box]
    low = Vector((min(p[i] for p in points) for i in range(3)))
    high = Vector((max(p[i] for p in points) for i in range(3)))
    point = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, high.z if anchor == "top" else low.z))
    return point - root.matrix_world.translation


def _expected(root, offset, row):
    """The world matrix that puts this master's anchor at the row's position with its turn."""
    basis = root.matrix_world.copy()
    basis.translation = Vector((0.0, 0.0, 0.0))
    return (Matrix.Translation(Vector(row["position"])) @ Matrix.Rotation(math.radians(row["yaw_deg"]), 4, "Z")
            @ Matrix.Translation(-offset) @ basis)


def _duplicate(root, collection):
    """A linked duplicate of the master's whole hierarchy: new objects, shared mesh and material data."""
    copies = {}
    for obj in _family(root):
        copy = obj.copy()
        copy.hide_render = copy.hide_viewport = False
        for key in (PART, VARIANT):
            if key in copy:
                del copy[key]
        collection.objects.link(copy)
        copies[obj] = copy
    for obj, copy in copies.items():
        if obj is not root:
            copy.parent = copies[obj.parent]
            copy.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
    return copies[root]


def _data_names(root):
    """The mesh data a hierarchy uses, whatever order Blender lists its children in."""
    return sorted(o.data.name for o in _family(root) if o.type == "MESH")


def _hide(obj):
    """Hide from the render and from this view layer. The object stays enabled, so its transform is
    still evaluated after the file is reopened."""
    obj.hide_render = True
    if obj.name in bpy.context.view_layer.objects:
        obj.hide_set(True)


def _clear(holder):
    """Remove instances an earlier `place` made under this root; nothing else is touched."""
    removed = 0
    for child in list(holder.children):
        if child.get(INSTANCE):
            for obj in reversed(_family(child)):
                bpy.data.objects.remove(obj, do_unlink=True)
                removed += 1
    return removed


def place(placements_path, *, masters=None, root_name=None, collection_name=None, hide_masters=True):
    """Make every instance in the list and return a report.

    masters maps "part/variant" to an object name; without it, masters are found by `tag_master`.
    Instances go under one Empty (root_name, default "<set piece> instances") in their own collection.
    Running it again replaces the instances it made before. hide_masters hides each master from the
    render and from this view layer once its instances exist; it stays enabled. Raises ValueError, before any change, when a
    master is missing.
    """
    doc = _read(placements_path)
    bpy.context.view_layer.update()
    found = _masters(doc, masters)
    anchors = {(m["part"], m["variant"]): m.get("anchor", "bottom") for m in doc["masters"]}
    offsets = {key: _anchor_offset(obj, anchors[key]) for key, obj in found.items()}

    title = str(doc.get("set_piece") or "Set piece")
    root_name = root_name or title + " instances"
    collection = bpy.data.collections.get(collection_name or root_name)
    if collection is None:
        collection = bpy.data.collections.new(collection_name or root_name)
        bpy.context.scene.collection.children.link(collection)
    holder = bpy.data.objects.get(root_name)
    if holder is None:
        holder = bpy.data.objects.new(root_name, None)
        holder[ROOT] = title
        collection.objects.link(holder)
    elif not holder.get(ROOT):
        raise ValueError("{!r} exists and is not a set piece root; pass another root_name.".format(root_name))
    replaced = _clear(holder)

    for row in doc["instances"]:
        key = (row["part"], row["variant"])
        if key not in found:
            raise ValueError("Instance {} names {}/{}, which the list's masters do not include.".format(
                row["id"], *key))
        copy = _duplicate(found[key], collection)
        copy.name = row["id"]
        copy.parent = holder
        copy.matrix_parent_inverse = Matrix.Identity(4)
        copy.matrix_world = holder.matrix_world @ _expected(found[key], offsets[key], row)
        copy[PART], copy[VARIANT], copy[SLOT], copy[INSTANCE] = row["part"], row["variant"], row["slot"], row["id"]
    if hide_masters:
        for obj in found.values():
            for member in _family(obj):
                _hide(member)
    bpy.context.view_layer.update()
    report = check(placements_path, masters=masters, root_name=root_name)
    report.update(collection=collection.name, replaced_objects=replaced, masters_hidden=bool(hide_masters))
    return report


def check(placements_path, *, masters=None, root_name=None, tolerance_m=0.001):
    """Compare the scene with the list: every instance present once, on its master's data, at its position."""
    doc = _read(placements_path)
    root_name = root_name or str(doc.get("set_piece") or "Set piece") + " instances"
    holder = bpy.data.objects.get(root_name)
    if holder is None or not holder.get(ROOT):
        raise ValueError("No set piece root named {!r}; run place first.".format(root_name))
    found = _masters(doc, masters)
    anchors = {(m["part"], m["variant"]): m.get("anchor", "bottom") for m in doc["masters"]}
    offsets = {key: _anchor_offset(obj, anchors[key]) for key, obj in found.items()}
    placed = {child[INSTANCE]: child for child in holder.children if child.get(INSTANCE)}
    problems, per_master, data = [], {}, set()
    for row in doc["instances"]:
        obj = placed.get(row["id"])
        if obj is None:
            problems.append("{}: not in the scene".format(row["id"]))
            continue
        key = (row["part"], row["variant"])
        master = found[key]
        if _data_names(master) != _data_names(obj):
            problems.append("{}: does not share its master's data".format(row["id"]))
        want = holder.matrix_world @ _expected(master, offsets[key], row)
        if (obj.matrix_world.translation - want.translation).length > tolerance_m:
            problems.append("{}: {:.4f} m from its position".format(
                row["id"], (obj.matrix_world.translation - want.translation).length))
        per_master["{}/{}".format(*key)] = per_master.get("{}/{}".format(*key), 0) + 1
        data.update(member.data.name for member in _family(obj) if member.type == "MESH")
    extra = sorted(set(placed) - {row["id"] for row in doc["instances"]})
    if extra:
        problems.append("{} instances are not in the list: {}".format(len(extra), ", ".join(extra[:5])))
    return {"passed": not problems, "problems": problems[:20], "root": holder.name,
            "instances": len(doc["instances"]) - sum(1 for r in doc["instances"] if r["id"] not in placed),
            "expected": len(doc["instances"]), "per_master": per_master, "mesh_datablocks": len(data)}
