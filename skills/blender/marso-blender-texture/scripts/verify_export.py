"""Conditional GLB round-trip diagnosis; not a mandatory per-asset production step."""
import math
import time

import bpy
from mathutils.kdtree import KDTree

from prepare_asset import validate_atlas, _anchor, _metre_scene


def _triangles(obj, *, scale=1.0, world=False, uv_name=None, transform=None):
    deps = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(deps),
        preserve_all_data_layers=True, depsgraph=deps)
    try:
        uv = mesh.uv_layers.get(uv_name) if uv_name else mesh.uv_layers.active
        if uv is None:
            raise ValueError('Missing comparison UV layer')
        mesh.calc_loop_triangles()
        transform = obj.matrix_world if world else transform
        normal_matrix = transform.to_3x3().inverted().transposed() if transform else None
        result = []
        for tri in mesh.loop_triangles:
            corners = []
            for li in tri.loops:
                point = mesh.vertices[mesh.loops[li].vertex_index].co.copy()
                normal = mesh.corner_normals[li].vector.copy()
                if transform:
                    point, normal = transform @ point, normal_matrix @ normal
                corners.append((point * scale, uv.data[li].uv.copy(), normal.normalized()))
            result.append(corners)
        return result
    finally:
        bpy.data.meshes.remove(mesh)


def compare_triangles(expected, actual, *, position_tolerance_m=1e-6,
                      uv_tolerance=1e-6, normal_angle_degrees=0.1):
    """Match triangle occurrences and cyclic winding with tolerance, not rounded keys."""
    if (not all(math.isfinite(x) for x in (position_tolerance_m, uv_tolerance, normal_angle_degrees)) or
            not expected or not actual or position_tolerance_m <= 0 or uv_tolerance <= 0 or
            not 0 < normal_angle_degrees < 90):
        raise ValueError('Supply nonempty meshes and positive, bounded tolerances')
    for triangles in (expected, actual):
        if any(not math.isfinite(x) for tri in triangles for corner in tri for v in corner for x in v):
            raise ValueError('Non-finite comparison data')
    tree = KDTree(len(expected)*3)
    for ti, tri in enumerate(expected):
        for ci, corner in enumerate(tri):
            tree.insert(corner[0], ti*3+ci)
    tree.balance()
    threshold = math.cos(math.radians(normal_angle_degrees))
    def candidates(ai):
        tri = actual[ai]
        yielded = set()
        for _, index, _ in tree.find_range(tri[0][0], position_tolerance_m):
            ti, offset = divmod(index, 3)
            if ti in yielded:
                continue
            errors = []
            for ci, (point, uv, normal) in enumerate(tri):
                ep, eu, en = expected[ti][(offset+ci) % 3]
                dp, du, dot = (point-ep).length, (uv-eu).length, normal.dot(en)
                if dp > position_tolerance_m or du > uv_tolerance or dot < threshold:
                    break
                errors.append((dp, du, math.degrees(math.acos(max(-1, min(1, dot))))))
            if len(errors) == 3:
                yielded.add(ti)
                yield ti, errors
    # Reassign only when tolerance neighbourhoods compete for the same triangle.
    # An iterative augmenting path avoids order-dependent greedy false failures.
    owners, assigned = {}, {}
    for ai in range(len(actual)):
        pending, parents, visited = [ai], {ai: None}, set()
        found = None
        while pending and found is None:
            current = pending.pop()
            for ti, errors in candidates(current):
                if ti in visited:
                    continue
                visited.add(ti)
                previous = owners.get(ti)
                if previous is None:
                    found = (current, ti, errors)
                    break
                if previous not in parents:
                    parents[previous] = (current, ti, errors)
                    pending.append(previous)
        while found is not None:
            current, ti, errors = found
            owners[ti] = current
            assigned[current] = (ti, errors)
            found = parents[current]
    unmatched = [i for i in range(len(actual)) if i not in assigned]
    maxima = [max((e[i] for _, errors in assigned.values() for e in errors), default=0.0) for i in range(3)]
    return {'passed': not unmatched and len(owners) == len(expected),
            'expected_triangles': len(expected), 'actual_triangles': len(actual),
            'unmatched_actual': len(unmatched), 'unmatched_expected': len(expected)-len(owners),
            'unmatched_examples': unmatched[:10], 'max_position_error_m': maxima[0],
            'max_uv_error': maxima[1], 'max_normal_angle_degrees': maxima[2],
            'tolerances': {'position_m': position_tolerance_m, 'uv': uv_tolerance,
                           'normal_angle_degrees': normal_angle_degrees}}


def verify_glb(obj, path, *, addon_module, uv_name='MarsoUV', **tolerances):
    """Check an export made by prepare_asset.export_glb in an isolated temporary scene.

    The expected frame is the object's local anchor; GLB import uses metre units.
    Raises on failure and removes imported data; never edits expected geometry.
    """
    if bpy.context.mode != 'OBJECT' or bpy.context.window is None:
        raise ValueError('Run in Object mode with a Blender window context (background is supported)')
    _metre_scene()
    start = time.perf_counter()
    expected = _triangles(obj, uv_name=uv_name, scale=bpy.context.scene.unit_settings.scale_length,
                          transform=_anchor(obj.matrix_world).inverted() @ obj.matrix_world)
    old_scene = bpy.context.window.scene
    collections = ('objects', 'collections', 'meshes', 'materials', 'images')
    before = {name: set(getattr(bpy.data, name)) for name in collections}
    scene = bpy.data.scenes.new('Temporary export verification')
    try:
        bpy.context.window.scene = scene
        bpy.ops.import_scene.gltf(filepath=str(path))
        objects = list(set(bpy.data.objects)-before['objects'])
        meshes = [o for o in objects if o.type == 'MESH']
        if len(meshes) != 1:
            raise ValueError('Expected one prepared mesh in the GLB')
        imported = meshes[0]
        if imported.data.uv_layers.active is None:
            raise ValueError('Missing UV layer in GLB')
        if len(imported.material_slots) != 1:
            raise ValueError('Expected one shared guide material')
        from prepare_asset import _colour_source
        _, colour = _colour_source(imported.material_slots[0].material, imported.data.uv_layers.active.name)
        if not colour.is_linked:
            raise ValueError('Missing connected colour-guide image')
        validate_atlas(imported, addon_module=addon_module, uv_name=imported.data.uv_layers.active.name)
        report = compare_triangles(expected, _triangles(imported, world=True), **tolerances)
        report['seconds'] = time.perf_counter()-start
        if not report['passed']:
            raise ValueError('GLB correspondence failed: ' + str(report))
        return report
    finally:
        bpy.context.window.scene = old_scene
        bpy.data.scenes.remove(scene)
        for obj_new in set(bpy.data.objects)-before['objects']:
            bpy.data.objects.remove(obj_new, do_unlink=True)
        for name in collections[1:]:
            data = getattr(bpy.data, name)
            for block in set(data)-before[name]:
                if block.users == 0:
                    data.remove(block)
