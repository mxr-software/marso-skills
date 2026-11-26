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
import hashlib
import json
import math
import tempfile
import time
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
PACK_VERSION = 1
# Modifier settings that change neither the mesh nor a render.
MARK_SKIPS = {'rna_type', 'name', 'show_expanded', 'is_active', 'show_in_editmode', 'show_on_cage'}


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
        nearest = tree.find_nearest
        moved = np.array([(nearest(p)[3] or 0.0) * scale for p in (sample / scale).tolist()])
    finally:
        bm.free()
    diagonal = float(np.linalg.norm(original.max(axis=0) - original.min(axis=0)))
    tolerance = DENSITY_TOLERANCE.get(path, DENSITY_TOLERANCE['medium']) * diagonal
    p90 = float(np.percentile(moved, 90))
    return {'judged': True, 'over_dense': p90 < tolerance, 'moved_p90_mm': round(p90 * 1000, 3),
            'tolerance_mm': round(tolerance * 1000, 3), 'faces': before, 'faces_halved': after}


@contextmanager
def evaluated(objects, depsgraph=None):
    """The evaluated mesh of each object by name, converted once and cleared on exit.

    Pass the result as `meshes` to the measuring functions so one conversion serves them all. Never render,
    edit the scene or change an object while it is open: Blender frees these meshes when it evaluates again.
    """
    depsgraph = depsgraph or bpy.context.evaluated_depsgraph_get()
    held, meshes = [], {}
    try:
        for obj in objects:
            item = obj.evaluated_get(depsgraph)
            meshes[obj.name] = item.to_mesh()
            held.append(item)
        yield meshes
    finally:
        for item in held:
            item.to_mesh_clear()


def _part_report(obj, mesh, path):
    part = {'base': topology(obj.data), 'evaluated': topology(mesh), 'modifiers': [m.type for m in obj.modifiers]}
    if path:
        part['density'] = density(obj, mesh, path)
    return part


def topology_report(objects, path=None, *, meshes=None, known=None):
    """Per-part topology of the modelled and the evaluated mesh, with asset totals.

    With a poly path (`low`, `medium`, `high`), each part also gets a `density` verdict and the totals list
    the over-dense parts and their share of the evaluated triangles. `meshes` is the open result of
    `evaluated(objects)`, read instead of converting each part again. `known` maps part names to entries an
    earlier report measured on the same geometry and path; those parts are not measured again.
    """
    known = known or {}
    depsgraph = None
    parts = {}
    for obj in objects:
        entry = known.get(obj.name)
        if isinstance(entry, dict) and {'base', 'evaluated', 'modifiers'} <= set(entry) \
                and ('density' in entry) == bool(path):
            parts[obj.name] = entry
        elif meshes is not None:
            parts[obj.name] = _part_report(obj, meshes[obj.name], path)
        else:
            depsgraph = depsgraph or bpy.context.evaluated_depsgraph_get()
            item = obj.evaluated_get(depsgraph)
            mesh = item.to_mesh()
            try:
                parts[obj.name] = _part_report(obj, mesh, path)
            finally:
                item.to_mesh_clear()
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


def _hash_mesh(digest, mesh):
    """Feed a mesh's positions, face sizes, corner vertices, edges and corner normals to the digest."""
    for collection, name, kind, width in ((mesh.vertices, 'co', np.float32, 3),
                                          (mesh.polygons, 'loop_total', np.int32, 1),
                                          (mesh.loops, 'vertex_index', np.int32, 1),
                                          (mesh.edges, 'vertices', np.int32, 2),
                                          (getattr(mesh, 'corner_normals', ()), 'vector', np.float32, 3)):
        values = np.empty(len(collection) * width, dtype=kind)
        if len(values):
            collection.foreach_get(name, values)
        digest.update(str(len(values)).encode())
        digest.update(values.tobytes())


def _hash_modifiers(digest, obj):
    """Feed every setting of every modifier to the digest: a render level changes the images, not the counts."""
    for modifier in obj.modifiers:
        values = [modifier.type]
        for prop in modifier.bl_rna.properties:
            if prop.identifier in MARK_SKIPS or prop.is_readonly or prop.type == 'COLLECTION':
                continue
            try:
                value = getattr(modifier, prop.identifier)
            except AttributeError:
                continue
            if prop.type == 'POINTER':
                value = getattr(value, 'name_full', None)
            elif isinstance(value, (set, frozenset)):
                value = sorted(value)
            elif not isinstance(value, (bool, int, float, str)):
                value = tuple(value)
            values.append((prop.identifier, value))
        try:
            values += [(key, modifier[key]) for key in modifier.keys()
                       if isinstance(modifier[key], (bool, int, float, str))]
        except (AttributeError, TypeError):
            pass
        digest.update(repr(values).encode())


def marks(objects, meshes=None):
    """A change mark for each part and one for the asset: `{'asset': hex, 'parts': {name: hex}}`.

    A part's mark is a hash of its modelled and evaluated meshes (positions, face sizes, corner vertices,
    edges, corner normals), its world matrix and every modifier setting. It changes when the part does and
    stays the same otherwise, so a review pack or a kept measurement can be matched to the asset as it is
    now. `meshes` is the open result of `evaluated(objects)`.
    """
    if meshes is None:
        with evaluated(objects) as meshes:
            return _marks(objects, meshes)
    return _marks(objects, meshes)


def _marks(objects, meshes):
    parts, whole = {}, hashlib.sha1()
    for obj in objects:
        digest = hashlib.sha1()
        _hash_mesh(digest, obj.data)
        _hash_mesh(digest, meshes[obj.name])
        digest.update(np.array(obj.matrix_world, dtype=np.float32).tobytes())
        _hash_modifiers(digest, obj)
        parts[obj.name] = digest.hexdigest()[:20]
    # The asset mark does not depend on the order the parts were listed in.
    whole.update(repr(sorted(parts.items())).encode())
    return {'asset': whole.hexdigest()[:20], 'parts': parts}


def _joint_names(joints):
    return [[p if isinstance(p, str) else p.name for p in pair] for pair in joints or ()]


def _stamp(folder):
    """The stamp `review` left in topology.json, or None when the file is absent, unreadable or has none."""
    try:
        pack = json.loads((folder / 'topology.json').read_text(encoding='utf-8')).get('pack')
    except (OSError, ValueError, AttributeError):
        return None
    if not isinstance(pack, dict) or pack.get('v') != PACK_VERSION or not isinstance(pack.get('files'), list):
        return None
    return pack


def pack_state(out_dir, marks, *, joints=None, reason=None):
    """Whether the review pack in `out_dir` shows the asset as it is now.

    `marks` is the result of `marks(objects)`. Returns `current` when the pack carries this script's stamp
    for the same marks and all its files exist; `stale` when the stamp is for other marks, a stamped file is
    gone or, with `joints` given, the pack shows other joints; `missing` when the folder holds no pack file;
    `foreign` when it holds pack files without a stamp, so this script cannot say what they show. A list
    passed as `reason` receives one sentence saying why.
    """
    folder = Path(out_dir)
    why = [] if reason is None else reason
    if not any((folder / name).exists() for name in OUTPUTS + ('joints.png',)):
        why.append('the folder holds no review pack')
        return 'missing'
    pack = _stamp(folder)
    if pack is None:
        why.append('the pack carries no stamp from review_model.review, so it cannot be matched to the asset')
        return 'foreign'
    if pack.get('asset') != marks['asset']:
        changed = sorted(name for name, mark in marks['parts'].items() if (pack.get('parts') or {}).get(name) != mark)
        why.append('the pack was rendered before the asset last changed' + (
            ' ({}{})'.format(', '.join(changed[:6]), ' ...' if len(changed) > 6 else '') if changed else ''))
        return 'stale'
    gone = [name for name in pack['files'] if not (folder / name).is_file()]
    if gone:
        why.append('pack files are gone: ' + ', '.join(gone))
        return 'stale'
    if joints is not None and _joint_names(joints) != pack.get('joints'):
        why.append('the pack shows other joints')
        return 'stale'
    return 'current'


def update_report(out_dir, report):
    """Write newer counts into a pack whose images are still current, keeping its stamp. Returns whether
    topology.json changed. A folder without this script's stamp is left alone."""
    folder = Path(out_dir)
    pack = _stamp(folder)
    if pack is None:
        return False
    path = folder / 'topology.json'
    held = json.loads(path.read_text(encoding='utf-8'))
    report = {key: value for key, value in report.items() if key not in ('timings', 'pack')}
    if {key: value for key, value in held.items() if key not in ('timings', 'pack')} == json.loads(json.dumps(report)):
        return False
    path.write_text(json.dumps(dict(report, timings=held.get('timings', {}), pack=pack), indent=2), encoding='utf-8')
    return True


def _lap(since):
    return round(time.perf_counter() - since, 3)


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


def review(root_or_objects, out_dir, *, size=1024, overwrite=False, path=None, joints=None, report=None,
           marks=None):
    """Write sheet.png, clay.png, gloss.png, wire.png and topology.json; returns their paths and the topology.

    `gloss` is None, with the reason in `gloss_skipped`, when this Blender build lacks the glossy matcap.

    `path` (`low`, `medium` or `high`) adds the density verdicts; it defaults to the root's `marso_poly_path`.
    `joints` is a list of part-name pairs that should meet; each gets a close clay view in `joints.png`.
    `report` is a `topology_report` result already measured on these parts at this path; it is written as
    given instead of being measured again. The result's `timings` give the seconds each stage took.

    topology.json also gets a `pack` stamp: the change marks of the parts, the size, the joints and the
    files written. `pack_state` reads it to say whether the pack still shows the asset. `marks` is the
    result of `marks(objects)` when the caller has it already.
    """
    started = time.perf_counter()
    timings = {}
    objects = asset_meshes(root_or_objects)
    if size < 128:
        raise ValueError('Use a render size of at least 128 pixels')
    if report is not None:
        if set(report.get('parts', ())) != {o.name for o in objects} or 'totals' not in report:
            raise ValueError('The report does not describe these parts; measure them again')
        report = {key: value for key, value in report.items() if key not in ('timings', 'pack')}
    else:
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
    if marks is None or report is None:
        with evaluated(objects) as meshes:
            marks = marks or _marks(objects, meshes)
            if report is None:
                report = topology_report(objects, path, meshes=meshes)
    timings['measure'] = _lap(started)
    framing = _bounds(objects)
    pixel = 2 * _camera_distance(framing[1]) * (18 / 50) / size
    shading = bpy.context.scene.display.shading
    with _studio(objects, size):
        shading.color_type = 'SINGLE'
        shading.single_color = CLAY[:3]
        lap = time.perf_counter()
        clay = _render_views(objects, framing, out / 'clay.png')
        timings['clay'], lap = _lap(lap), time.perf_counter()
        gloss_skipped = _render_gloss(objects, framing, out / 'gloss.png')
        timings['gloss'], lap = _lap(lap), time.perf_counter()
        if joints:
            shots = _joint_shots(joints, objects, framing)
            scene = bpy.context.scene
            scene.render.resolution_x = scene.render.resolution_y = size // 2
            with tempfile.TemporaryDirectory() as scratch:
                _write_png(_grid(_render_tiles(shots, 'joints', Path(scratch))), out / 'joints.png')
            scene.render.resolution_x = scene.render.resolution_y = size
            timings['joints'], lap = _lap(lap), time.perf_counter()
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
        timings['wire'] = _lap(lap)
    lap = time.perf_counter()
    _write_png(np.concatenate([_half(wired), _half(clay)], axis=0), out / 'sheet.png')
    timings['sheet'] = _lap(lap)
    timings['total'] = _lap(started)
    files = ['sheet.png', 'clay.png', 'wire.png', 'topology.json'] + ([] if gloss_skipped else ['gloss.png']) \
        + (['joints.png'] if joints else [])
    pack = {'v': PACK_VERSION, 'asset': marks['asset'], 'parts': marks['parts'], 'size': size,
            'joints': _joint_names(joints), 'files': files}
    (out / 'topology.json').write_text(json.dumps(dict(report, timings=timings, pack=pack), indent=2),
                                       encoding='utf-8')
    made = {'sheet': str(out / 'sheet.png'), 'clay': str(out / 'clay.png'), 'wire': str(out / 'wire.png'),
            'gloss': None if gloss_skipped else str(out / 'gloss.png'),
            'topology': str(out / 'topology.json'), 'report': report, 'timings': timings, 'pack': pack}
    if gloss_skipped:
        made['gloss_skipped'] = gloss_skipped
    if joints:
        made['joints'] = str(out / 'joints.png')
    return made
