"""Neutral-clay and wireframe review renders plus topology counts for a modelled asset.

Run inside Blender (background or live). `review(root, out_dir)` renders two opposite oblique views of the
asset's visible meshes with Workbench and writes `sheet.png` (both clay views above both wire views at half
size), full-size `clay.png`, `gloss.png` and `wire.png`, and `topology.json`; with `joints`, also close clay
views of where named parts meet (`joints.png`). `gloss.png` repeats the clay views with a glossy surface, whose
highlights show ripples, facets and soft edges that matte clay hides. The wireframe is
drawn from the evaluated mesh (modifiers applied), so it shows the faces that will be exported. Scene objects,
materials and render settings are restored afterwards.
"""

from contextlib import contextmanager
import json
import math
import tempfile
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

VIEWS = ((1.0, -1.2, 0.7), (-1.0, 1.2, 0.45))
OUTPUTS = ('sheet.png', 'clay.png', 'gloss.png', 'wire.png', 'topology.json')
GLOSS_MATCAP = 'ceramic_lightbulb.exr'
CLAY = (0.72, 0.72, 0.72, 1.0)
WIRE = (0.04, 0.04, 0.05, 1.0)
TIP_ANGLE_DEG = 25.0
# Surface movement, as a fraction of the part's diagonal, below which halving the density changes nothing visible.
DENSITY_TOLERANCE = {'low': 0.005, 'medium': 0.0015, 'high': 0.0005}
DENSITY_SAMPLES = 20000


def asset_meshes(root_or_objects):
    """Visible mesh objects with faces under a root (or in a list); fails closed on an empty selection."""
    if isinstance(root_or_objects, bpy.types.Object):
        candidates = [root_or_objects] + list(root_or_objects.children_recursive)
    else:
        candidates = list(root_or_objects)
    meshes = [o for o in candidates if o.type == 'MESH' and o.visible_get() and not o.hide_render
              and len(o.data.polygons)]
    if not meshes:
        raise ValueError('No visible mesh with faces in the selection')
    return meshes


def topology(mesh):
    """Face sizes, poles and pointed tips of one mesh.

    A tip is a vertex whose surrounding faces are all triangles and are not coplanar (a cone point or nib).
    Triangles touching a tip are counted as `tip_tris`; every other triangle and every n-gon counts against
    an all-quad build. A flat triangle fan (a cap centre) is not a tip.
    """
    count = len(mesh.polygons)
    if not count:
        return {'faces': 0, 'triangles': 0, 'quads': 0, 'tris': 0, 'tip_tris': 0, 'ngons': 0, 'max_ngon': 0,
                'poles_5_6': 0, 'poles_7plus': 0, 'tip_vertices': 0, 'vertices': len(mesh.vertices)}
    sizes = np.empty(count, dtype=np.int64)
    starts = np.empty(count, dtype=np.int64)
    mesh.polygons.foreach_get('loop_total', sizes)
    mesh.polygons.foreach_get('loop_start', starts)
    normals = np.empty(count * 3)
    mesh.polygons.foreach_get('normal', normals)
    normals = normals.reshape(-1, 3)
    loop_vert = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get('vertex_index', loop_vert)
    order = np.argsort(starts)
    loop_face = np.empty(len(mesh.loops), dtype=np.int64)
    loop_face[np.concatenate([np.arange(s, s + n) for s, n in zip(starts[order], sizes[order])])] = \
        np.repeat(order, sizes[order])
    verts = len(mesh.vertices)
    is_tri = sizes == 3
    adjacent = np.bincount(loop_vert, minlength=verts)
    adjacent_tris = np.bincount(loop_vert, weights=is_tri[loop_face].astype(float), minlength=verts)
    mean = np.zeros((verts, 3))
    np.add.at(mean, loop_vert, normals[loop_face])
    length = np.linalg.norm(mean, axis=1)
    mean = mean / np.where(length > 0, length, 1)[:, None]
    worst = np.ones(verts)
    np.minimum.at(worst, loop_vert, np.einsum('ij,ij->i', normals[loop_face], mean[loop_vert]))
    tips = (adjacent >= 3) & (adjacent == adjacent_tris) & (worst < math.cos(math.radians(TIP_ANGLE_DEG)))
    tip_face = np.zeros(count, dtype=bool)
    np.logical_or.at(tip_face, loop_face, tips[loop_vert])
    ends = np.empty(len(mesh.edges) * 2, dtype=np.int64)
    mesh.edges.foreach_get('vertices', ends)
    valence = np.bincount(ends, minlength=verts)
    return {'faces': count, 'triangles': int((sizes - 2).sum()), 'quads': int((sizes == 4).sum()),
            'tris': int((is_tri & ~tip_face).sum()),
            'tip_tris': int((is_tri & tip_face).sum()), 'ngons': int((sizes > 4).sum()),
            'max_ngon': int(sizes.max()), 'poles_5_6': int(((valence >= 5) & (valence <= 6)).sum()),
            'poles_7plus': int(((valence >= 7) & ~tips).sum()), 'tip_vertices': int(tips.sum()),
            'vertices': verts}


def density(obj, mesh, path='medium'):
    """Whether a part's faces hold its shape: undo one level of density and measure how far the surface moves.

    The evaluated mesh is un-subdivided once on a copy (every other edge loop removed, quads kept). If 90% of
    the original vertices then lie within the path's tolerance of the coarser surface, the removed loops added
    no visible shape and the part is `over_dense`. A mesh that does not un-subdivide (irregular topology) is
    not judged. Movement is in metres.
    """
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.transform(obj.matrix_world)
        scale = bpy.context.scene.unit_settings.scale_length
        original = np.array([v.co[:] for v in bm.verts]) * scale
        before = len(bm.faces)
        if before < 16:
            return {'judged': False, 'reason': 'too few faces'}
        bmesh.ops.unsubdivide(bm, verts=bm.verts[:], iterations=2)
        after = len(bm.faces)
        if after > 0.8 * before or after == 0:
            return {'judged': False, 'reason': 'does not un-subdivide', 'faces': before}
        tree = BVHTree.FromBMesh(bm)
        rng = np.random.default_rng(0)
        sample = original if len(original) <= DENSITY_SAMPLES else \
            original[rng.choice(len(original), DENSITY_SAMPLES, replace=False)]
        moved = np.array([(tree.find_nearest(Vector(p / scale))[3] or 0.0) * scale for p in sample])
    finally:
        bm.free()
    diagonal = float(np.linalg.norm(original.max(axis=0) - original.min(axis=0)))
    tolerance = DENSITY_TOLERANCE.get(path, DENSITY_TOLERANCE['medium']) * diagonal
    p90 = float(np.percentile(moved, 90))
    return {'judged': True, 'over_dense': p90 < tolerance, 'moved_p90_mm': round(p90 * 1000, 3),
            'tolerance_mm': round(tolerance * 1000, 3), 'faces': before, 'faces_halved': after}


def topology_report(objects, path=None):
    """Per-part topology of the modelled and the evaluated mesh, with asset totals.

    With a poly path (`low`, `medium`, `high`), each part also gets a `density` verdict and the totals list
    the over-dense parts and their share of the evaluated triangles.
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    parts = {}
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            parts[obj.name] = {'base': topology(obj.data), 'evaluated': topology(mesh),
                               'modifiers': [m.type for m in obj.modifiers]}
            if path:
                parts[obj.name]['density'] = density(obj, mesh, path)
        finally:
            evaluated.to_mesh_clear()
    totals = {}
    for level in ('base', 'evaluated'):
        total = {k: sum(p[level][k] for p in parts.values())
                 for k in ('faces', 'triangles', 'quads', 'tris', 'tip_tris', 'ngons', 'poles_5_6', 'poles_7plus',
                           'vertices')}
        total['max_ngon'] = max(p[level]['max_ngon'] for p in parts.values())
        total['quad_fraction'] = round(total['quads'] / total['faces'], 4) if total['faces'] else None
        totals[level] = total
    if path:
        dense = [name for name, p in parts.items() if p['density'].get('over_dense')]
        triangles = totals['evaluated']['triangles']
        totals['density'] = {'path': path, 'over_dense_parts': dense,
                             'over_dense_triangle_share': round(sum(parts[n]['evaluated']['triangles']
                                                                    for n in dense) / triangles, 4)
                             if triangles else 0.0}
    return {'totals': totals, 'parts': parts,
            'rule': 'all quads; triangles only around pointed tips; no n-gons; no 7+ poles off a tip; '
                    'no part whose density can halve without moving its surface'}


def _bounds(objects):
    corners = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    low = Vector(min(c[i] for c in corners) for i in range(3))
    high = Vector(max(c[i] for c in corners) for i in range(3))
    return (low + high) / 2, max((high - low).length / 2, 0.01)


def _camera_distance(radius):
    return radius / math.sin(math.radians(18)) * 1.1


@contextmanager
def _studio(objects, size):
    """Workbench at `size` pixels with only `objects` rendered; restores everything afterwards."""
    scene = bpy.context.scene
    shading = scene.display.shading
    saved = {'engine': scene.render.engine, 'x': scene.render.resolution_x, 'y': scene.render.resolution_y,
             'pct': scene.render.resolution_percentage, 'path': scene.render.filepath,
             'format': scene.render.image_settings.file_format, 'transparent': scene.render.film_transparent,
             'view': scene.view_settings.view_transform, 'look': scene.view_settings.look,
             'light': shading.light, 'color_type': shading.color_type, 'single': tuple(shading.single_color),
             'camera': scene.camera, 'world': scene.world,
             'override': bpy.context.view_layer.material_override}
    keep = {o.name for o in objects}
    hidden = {o.name: o.hide_render for o in scene.objects}
    world = bpy.data.worlds.new('MarsoReviewWorld')
    world.color = (0.9, 0.9, 0.92)
    try:
        scene.render.engine = 'BLENDER_WORKBENCH'
        scene.render.resolution_x = scene.render.resolution_y = size
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = 'PNG'
        scene.render.film_transparent = False
        scene.view_settings.view_transform = 'Standard'
        scene.view_settings.look = 'None'
        shading.light = 'STUDIO'
        scene.world = world
        bpy.context.view_layer.material_override = None
        for o in scene.objects:
            if o.name not in keep:
                o.hide_render = True
        yield scene
    finally:
        for name, value in hidden.items():
            if name in scene.objects:
                scene.objects[name].hide_render = value
        scene.render.engine = saved['engine']
        scene.render.resolution_x, scene.render.resolution_y = saved['x'], saved['y']
        scene.render.resolution_percentage = saved['pct']
        scene.render.filepath = saved['path']
        scene.render.image_settings.file_format = saved['format']
        scene.render.film_transparent = saved['transparent']
        scene.view_settings.view_transform = saved['view']
        scene.view_settings.look = saved['look']
        shading.light, shading.color_type = saved['light'], saved['color_type']
        shading.single_color = saved['single']
        scene.camera, scene.world = saved['camera'], saved['world']
        bpy.context.view_layer.material_override = saved['override']
        bpy.data.worlds.remove(world)


def _render_views(objects, framing, path):
    """Render each view to a temporary file, join them side by side into `path` and return the pixels."""
    center, radius = framing
    shots = [(center, _camera_distance(radius), Vector(direction)) for direction in VIEWS]
    with tempfile.TemporaryDirectory() as scratch:
        tiles = _render_tiles(shots, path.stem, Path(scratch))
    joined = np.concatenate(tiles, axis=1)
    _write_png(joined, path)
    return joined


def _render_gloss(objects, framing, path):
    """Render the clay views with a glossy matcap; returns None, or why the render was skipped."""
    shading = bpy.context.scene.display.shading
    shading.light = 'MATCAP'
    previous = shading.studio_light
    try:
        try:
            shading.studio_light = GLOSS_MATCAP
        except TypeError:
            return 'matcap {} is not available in this Blender build'.format(GLOSS_MATCAP)
        shading.color_type = 'SINGLE'
        shading.single_color = (1.0, 1.0, 1.0)
        _render_views(objects, framing, path)
        return None
    finally:
        try:
            shading.studio_light = previous
        except TypeError:
            pass
        shading.light = 'STUDIO'
        shading.single_color = CLAY[:3]


def _half(array):
    height, width = array.shape[0] // 2 * 2, array.shape[1] // 2 * 2
    return array[:height, :width].reshape(height // 2, 2, width // 2, 2, -1).mean(axis=(1, 3))


def _box(obj):
    corners = np.array([(obj.matrix_world @ Vector(c))[:] for c in obj.bound_box])
    return corners.min(axis=0), corners.max(axis=0)


def _joint_shots(pairs, objects, framing):
    """A close camera at each pair's meeting point, looking in from outside the asset."""
    by_name = {o.name: o for o in objects}
    shots = []
    for pair in pairs:
        try:
            a, b = (by_name[p if isinstance(p, str) else p.name] for p in pair)
        except KeyError as missing:
            raise ValueError('Joint part is not a visible asset mesh: ' + str(missing)) from None
        (low_a, high_a), (low_b, high_b) = _box(a), _box(b)
        low, high = np.maximum(low_a, low_b), np.minimum(high_a, high_b)
        center = (low + high) / 2
        thinnest = min((high_a - low_a).min(), (high_b - low_b).min())
        radius = max(0.02, 2.5 * thinnest, 0.75 * float(np.linalg.norm(high - low)))
        outward = Vector(center) - framing[0]
        outward.z = 0
        direction = outward.normalized() + Vector((0, 0, 0.6)) if outward.length > 1e-6 else Vector(VIEWS[0])
        shots.append((Vector(center), _camera_distance(radius), direction))
    return shots


def _grid(tiles, columns=4):
    blank = np.ones_like(tiles[0])
    rows = [tiles[i:i + columns] for i in range(0, len(tiles), columns)]
    rows[-1] = rows[-1] + [blank] * (len(rows[0]) - len(rows[-1]))
    return np.concatenate([np.concatenate(row, axis=1) for row in reversed(rows)], axis=0)


def _render_tiles(shots, stem, scratch):
    scene = bpy.context.scene
    tiles = []
    for index, (center, distance, direction) in enumerate(shots):
        data = bpy.data.cameras.new('MarsoReviewCamera')
        data.lens, data.sensor_width = 50, 36
        cam = bpy.data.objects.new('MarsoReviewCamera', data)
        scene.collection.objects.link(cam)
        cam.location = center + Vector(direction).normalized() * distance
        cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
        data.clip_start, data.clip_end = distance / 1000, distance * 10
        scene.camera = cam
        tile = str(scratch / '{}.view{}.png'.format(stem, index))
        scene.render.filepath = tile
        try:
            bpy.ops.render.render(write_still=True)
            tiles.append(_read_png(tile))
        finally:
            bpy.data.objects.remove(cam)
            bpy.data.cameras.remove(data)
            Path(tile).unlink(missing_ok=True)
    return tiles


def _read_png(path):
    image = bpy.data.images.load(path, check_existing=False)
    try:
        width, height = image.size
        pixels = np.empty(width * height * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        return pixels.reshape(height, width, 4)
    finally:
        bpy.data.images.remove(image)


def _write_png(array, path):
    height, width = array.shape[:2]
    image = bpy.data.images.new('MarsoReviewImage', width, height, alpha=True)
    try:
        image.pixels.foreach_set(np.ascontiguousarray(array, dtype=np.float32).ravel())
        image.filepath_raw = str(path)
        image.file_format = 'PNG'
        image.save()
    finally:
        bpy.data.images.remove(image)


def _wire_objects(objects, thickness):
    """Temporary wireframe copies of each evaluated mesh, drawn as tubes along every real edge."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene
    made = []
    for obj in objects:
        mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
        wire = bpy.data.objects.new('MarsoReviewWire', mesh)
        wire.matrix_world = obj.matrix_world.copy()
        scene.collection.objects.link(wire)
        scale = max(sum(abs(s) for s in obj.matrix_world.to_scale()) / 3, 1e-9)
        modifier = wire.modifiers.new('MarsoReviewWire', 'WIREFRAME')
        modifier.thickness = thickness / scale
        modifier.use_replace = True
        modifier.use_even_offset = True
        modifier.use_relative_offset = False
        modifier.offset = 0.0
        wire.color = WIRE
        made.append(wire)
    return made


def review(root_or_objects, out_dir, *, size=1024, overwrite=False, path=None, joints=None):
    """Write sheet.png, clay.png, gloss.png, wire.png and topology.json; returns their paths and the topology.

    `gloss` is None, with the reason in `gloss_skipped`, when this Blender build lacks the glossy matcap.

    `path` (`low`, `medium` or `high`) adds the density verdicts; it defaults to the root's `marso_poly_path`.
    `joints` is a list of part-name pairs that should meet; each gets a close clay view in `joints.png`.
    """
    objects = asset_meshes(root_or_objects)
    if size < 128:
        raise ValueError('Use a render size of at least 128 pixels')
    if path is None and isinstance(root_or_objects, bpy.types.Object):
        path = root_or_objects.get('marso_poly_path')
    if path is not None and path not in DENSITY_TOLERANCE:
        raise ValueError('Use path low, medium or high')
    joints = list(joints or [])
    if len(joints) > 12:
        raise ValueError('Pass at most 12 joints; choose the structural ones')
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    existing = [name for name in OUTPUTS + (('joints.png',) if joints else ()) if (out / name).exists()]
    if existing and not overwrite:
        raise FileExistsError('Already present (pass overwrite=True to replace): ' + ', '.join(existing))
    report = topology_report(objects, path)
    framing = _bounds(objects)
    pixel = 2 * _camera_distance(framing[1]) * (18 / 50) / size
    shading = bpy.context.scene.display.shading
    with _studio(objects, size):
        shading.color_type = 'SINGLE'
        shading.single_color = CLAY[:3]
        clay = _render_views(objects, framing, out / 'clay.png')
        gloss_skipped = _render_gloss(objects, framing, out / 'gloss.png')
        if joints:
            shots = _joint_shots(joints, objects, framing)
            scene = bpy.context.scene
            scene.render.resolution_x = scene.render.resolution_y = size // 2
            with tempfile.TemporaryDirectory() as scratch:
                _write_png(_grid(_render_tiles(shots, 'joints', Path(scratch))), out / 'joints.png')
            scene.render.resolution_x = scene.render.resolution_y = size
        colours = {o.name: tuple(o.color) for o in objects}
        wires = _wire_objects(objects, pixel * 1.4)
        try:
            shading.color_type = 'OBJECT'
            for obj in objects:
                obj.color = CLAY
            wired = _render_views(objects + wires, framing, out / 'wire.png')
        finally:
            for obj in objects:
                obj.color = colours[obj.name]
            for wire in wires:
                mesh = wire.data
                bpy.data.objects.remove(wire)
                bpy.data.meshes.remove(mesh)
    _write_png(np.concatenate([_half(wired), _half(clay)], axis=0), out / 'sheet.png')
    (out / 'topology.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    made = {'sheet': str(out / 'sheet.png'), 'clay': str(out / 'clay.png'), 'wire': str(out / 'wire.png'),
            'gloss': None if gloss_skipped else str(out / 'gloss.png'),
            'topology': str(out / 'topology.json'), 'report': report}
    if gloss_skipped:
        made['gloss_skipped'] = gloss_skipped
    if joints:
        made['joints'] = str(out / 'joints.png')
    return made
