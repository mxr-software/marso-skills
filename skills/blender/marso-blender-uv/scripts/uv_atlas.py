"""Author, pack and measure one shared UV atlas across the separate parts of an asset, inside Blender.

The parts stay separate objects; every visible mesh under the asset root shares one 0-1 tile on the named
layer (default `MarsoUV`). Seams are the author's: `unwrap` uses the marked seams and never invents them.
`report` measures the evaluated meshes, so modifiers that add faces are included.
"""

from contextlib import contextmanager
import hashlib
import math
from pathlib import Path
import sys
import time

import bmesh
import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_uv import audit_uv  # noqa: E402
from measure_uv_quality import measure_uv_quality  # noqa: E402

UV = 'MarsoUV'
LIMITS = {'stretch_p95': 2.5, 'density_spread': 1.3, 'fill': 0.65, 'chart_width': 1 / 128}
PADDING_CHECK_FACES = 150000
BEST_PACK_FACES = 200000
# Modifier settings that change neither the mesh nor a render.
MARK_SKIPS = {'rna_type', 'name', 'show_expanded', 'is_active', 'show_in_editmode', 'show_on_cage'}


def _candidates(root_or_objects):
    if isinstance(root_or_objects, bpy.types.Object):
        return [root_or_objects] + list(root_or_objects.children_recursive)
    return list(root_or_objects)


def asset_meshes(root_or_objects):
    """Visible mesh objects with faces under a root (or in a list); fails closed on an empty selection."""
    meshes = [o for o in _candidates(root_or_objects) if o.type == 'MESH' and o.visible_get()
              and not o.hide_render and len(o.data.polygons)]
    if not meshes:
        raise ValueError('No visible mesh with faces in the selection')
    return meshes


def hidden_meshes(root_or_objects):
    """Names of meshes with faces that `asset_meshes` skips because they are hidden."""
    return [o.name for o in _candidates(root_or_objects) if o.type == 'MESH' and len(o.data.polygons)
            and (not o.visible_get() or o.hide_render)]


def shared_meshes(objects):
    """Mesh data used by more than one of the objects; their charts would stack in one atlas."""
    users = {}
    for obj in objects:
        users.setdefault(obj.data.name, []).append(obj.name)
    return {mesh: names for mesh, names in users.items() if len(names) > 1}


def ensure_layer(objects, uv_name=UV):
    """Create the named layer where missing and make it active and rendered on every part."""
    shared = shared_meshes(objects)
    if shared:
        raise ValueError('Make instanced parts single-user before sharing one atlas: ' + str(shared))
    for obj in objects:
        uvs = obj.data.uv_layers
        layer = uvs.get(uv_name) or uvs.new(name=uv_name)
        uvs.active = layer
        layer.active_render = True


@contextmanager
def _editing(objects, faces=None):
    """Multi-object edit mode with only the requested faces selected; restores mode and selection."""
    view_layer = bpy.context.view_layer
    previous_active = view_layer.objects.active
    previous_selected = [o for o in view_layer.objects if o.select_get()]
    settings = bpy.context.scene.tool_settings
    previous_sync, previous_mode = settings.use_uv_select_sync, settings.mesh_select_mode[:]
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in previous_selected:
        o.select_set(False)
    for obj in objects:
        obj.select_set(True)
        chosen = None if faces is None else set(faces.get(obj.name, ()))
        for poly in obj.data.polygons:
            poly.select = chosen is None or poly.index in chosen
    view_layer.objects.active = objects[0]
    settings.use_uv_select_sync = True
    settings.mesh_select_mode = (False, False, True)
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        yield
    finally:
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        settings.use_uv_select_sync, settings.mesh_select_mode = previous_sync, previous_mode
        for obj in objects:
            obj.select_set(False)
        for o in previous_selected:
            o.select_set(True)
        view_layer.objects.active = previous_active


def unwrap(objects, *, uv_name=UV, method='MINIMUM_STRETCH', faces=None, margin=0.001):
    """Unwrap along the marked seams. `faces` maps object names to polygon indices to limit the unwrap.

    Use ANGLE_BASED for organic or curved charts if MINIMUM_STRETCH leaves visible distortion. Unwrapped
    charts are not packed or density-matched until `pack`.
    """
    objects = list(objects)
    if method not in {'ANGLE_BASED', 'CONFORMAL', 'MINIMUM_STRETCH'}:
        raise ValueError('Unknown unwrap method: ' + str(method))
    if faces is not None and set(faces) - {o.name for o in objects}:
        raise ValueError('Face selection names objects outside this asset')
    ensure_layer(objects, uv_name)
    subdivided = any(m.type == 'SUBSURF' and m.show_render for o in objects for m in o.modifiers)
    with _editing(objects, faces):
        bpy.ops.uv.unwrap(method=method, fill_holes=True, correct_aspect=True,
                          use_subsurf_data=subdivided, margin_method='FRACTION', margin=margin)


def pack(objects, *, uv_name=UV, resolution=2048, padding_px=8, shape_method='BEST', rotate=True):
    """Equalise texel density across all parts, then pack every chart into the one 0-1 tile.

    Padding is the requested gap in pixels at `resolution`; `report` measures what was achieved. The
    resolution and padding are recorded on every packed part (`marso_uv_resolution`,
    `marso_uv_padding_px`), and `report` and `review` measure at the recorded size by default.
    `BEST` packs by bounding box (instant), then by concave outline, which nests small charts in the gaps
    round large round or L-shaped ones (seconds on a typical prop), and keeps the fuller layout. Above
    200,000 faces before modifiers only the bounding-box pack runs. Returns the shape kept and the fill of
    each layout tried.
    """
    objects = list(objects)
    if shape_method not in ('BEST', 'AABB', 'CONVEX', 'CONCAVE'):
        raise ValueError('Unknown shape_method: ' + str(shape_method))
    if resolution <= 0 or not 0 < padding_px < resolution / 4:
        raise ValueError('Use a positive resolution and padding below a quarter of it')
    for obj in objects:
        if obj.data.uv_layers.get(uv_name) is None:
            raise ValueError('Unwrap before packing; missing ' + uv_name + ' on ' + obj.name)
    scales = {obj.name: [abs(s) for s in obj.matrix_world.to_scale()] for obj in objects}
    reference = next(iter(scales.values()))[0]
    uneven = [name for name, s in scales.items() if any(abs(c - reference) > 1e-4 * reference for c in s)]
    if uneven:
        raise ValueError('Packing evens density in mesh space; apply scale so every part has the same uniform '
                         'world scale: ' + ', '.join(uneven))
    ensure_layer(objects, uv_name)
    shapes = [shape_method] if shape_method != 'BEST' else ['AABB', 'CONCAVE']
    if shape_method == 'BEST' and sum(len(o.data.polygons) for o in objects) > BEST_PACK_FACES:
        shapes = ['AABB']
    tried, best = {}, None
    for shape in shapes:
        with _editing(objects):
            bpy.ops.uv.select_all(action='SELECT')
            bpy.ops.uv.average_islands_scale(scale_uv=False, shear=False)
            bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=rotate, rotate_method='ANY',
                                    scale=True, merge_overlap=False,
                                    margin_method='FRACTION' if shape == 'AABB' else 'ADD',
                                    margin=padding_px / resolution, shape_method=shape)
        tried[shape] = round(_cage_fill(objects, uv_name), 4)
        if best is None or tried[shape] > best[1]:
            best = (shape, tried[shape], _snapshot(objects, uv_name))
    if shapes[-1] != best[0]:
        for obj, uv in zip(objects, best[2]):
            obj.data.uv_layers[uv_name].data.foreach_set('uv', uv)
            obj.data.update()
    for obj in objects:
        obj['marso_uv_resolution'], obj['marso_uv_padding_px'] = int(resolution), float(padding_px)
    return {'shape_method': best[0], 'fill_before_modifiers': best[1], 'tried': tried}


def recorded(root_or_objects):
    """The resolution and padding the parts were last packed for, or None where parts disagree or none is
    recorded."""
    found = {(o.get('marso_uv_resolution'), o.get('marso_uv_padding_px')) for o in asset_meshes(root_or_objects)}
    if len(found) != 1 or None in next(iter(found)):
        return None
    resolution, padding = next(iter(found))
    return {'resolution': int(resolution), 'padding_px': float(padding)}


def _snapshot(objects, uv_name):
    copies = []
    for obj in objects:
        uv = np.empty(len(obj.data.loops) * 2)
        obj.data.uv_layers[uv_name].data.foreach_get('uv', uv)
        copies.append(uv)
    return copies


def _cage_fill(objects, uv_name):
    total = 0.0
    for obj, uv in zip(objects, _snapshot(objects, uv_name)):
        mesh = obj.data
        mesh.calc_loop_triangles()
        loops = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
        mesh.loop_triangles.foreach_get('loops', loops)
        t = uv.reshape(-1, 2)[loops.reshape(-1, 3)]
        a, b = t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]
        total += float(np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]).sum()) / 2
    return total


def _charts(obj, uv_name):
    """UV charts of the base mesh: faces, UV area, UV boundary length and the mesh edges shared with each
    neighbouring chart."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        uv = bm.loops.layers.uv[uv_name]
        bm.faces.ensure_lookup_table()
        parent = list(range(len(bm.faces)))

        def root(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def joined(edge):
            if len(edge.link_loops) != 2:
                return False
            a, b = edge.link_loops
            return ((a[uv].uv - b.link_loop_next[uv].uv).length < 1e-6
                    and (a.link_loop_next[uv].uv - b[uv].uv).length < 1e-6)

        for edge in bm.edges:
            if joined(edge):
                a, b = edge.link_loops
                parent[root(a.face.index)] = root(b.face.index)
        charts = {}
        for face in bm.faces:
            chart = charts.setdefault(root(face.index), {'faces': set(), 'area': 0.0, 'perimeter': 0.0,
                                                         'neighbours': {}, 'open': False})
            chart['faces'].add(face.index)
            points = [loop[uv].uv for loop in face.loops]
            chart['area'] += abs(sum(p.x * q.y - q.x * p.y for p, q in zip(points, points[1:] + points[:1]))) / 2
            for loop in face.loops:
                edge = loop.edge
                if joined(edge):
                    continue
                chart['perimeter'] += (loop.link_loop_next[uv].uv - loop[uv].uv).length
                chart['open'] |= len(edge.link_faces) < 2
                for other in edge.link_faces:
                    if root(other.index) != root(face.index):
                        chart['neighbours'].setdefault(root(other.index), []).append(
                            (edge.index, edge.calc_length()))
        return charts
    finally:
        bm.free()


def _folds(triangles, cells=512):
    """Whether UV triangles (n, 3, 2) of one chart are wound both ways or cover any of their own area twice."""
    a, b = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    signed = a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]
    if (signed > 1e-12).any() and (signed < -1e-12).any():
        return True
    low = triangles.reshape(-1, 2).min(axis=0)
    span = float((triangles.reshape(-1, 2).max(axis=0) - low).max()) or 1.0
    points = (triangles - low) / span * (cells - 1)
    coverage = np.zeros((cells, cells), dtype=np.int32)
    for a, b, c in points:
        x0, y0 = np.floor(np.minimum(np.minimum(a, b), c)).astype(int)
        x1, y1 = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        sides = [(q[0] - p[0]) * (ys - p[1]) - (q[1] - p[1]) * (xs - p[0]) for p, q in ((a, b), (b, c), (c, a))]
        inside = ((sides[0] > 0) & (sides[1] > 0) & (sides[2] > 0)) | ((sides[0] < 0) & (sides[1] < 0) & (sides[2] < 0))
        rows, cols = ys[inside].astype(int), xs[inside].astype(int)
        keep = (rows < cells) & (cols < cells)
        coverage[rows[keep], cols[keep]] += 1
    return bool((coverage > 1).sum() > 2)


def narrow_charts(objects, *, uv_name=UV, resolution=2048, min_px=None):
    """Charts narrower than `min_px` (default 1/128 of the tile) on the base meshes, measured as twice UV area
    over UV boundary length. A part that is a single chart is listed separately: it has nothing to join."""
    min_px = LIMITS['chart_width'] * resolution if min_px is None else min_px
    narrow, whole_parts = [], []
    for obj in objects:
        charts = _charts(obj, uv_name)
        for chart in charts.values():
            width = 2 * chart['area'] / chart['perimeter'] * resolution if chart['perimeter'] else 0.0
            if width < min_px:
                entry = {'object': obj.name, 'faces': len(chart['faces']), 'width_px': round(width, 2)}
                (whole_parts if len(charts) == 1 else narrow).append(entry)
    return {'min_px': min_px, 'narrow': narrow, 'whole_parts': whole_parts}


def join_small_charts(objects, *, uv_name=UV, resolution=None, padding_px=None, min_px=None, rounds=6,
                      rotate=True):
    """Join each chart narrower than `min_px` to the neighbour it shares the longest edge with: clear the seams
    between them, unwrap the pair together and pack the atlas again. A join that would close a surface is
    skipped; one whose unwrap exceeds the stretch limit is undone and the next neighbour is tried in a later
    round. Repeats up to `rounds` times, because packing changes every chart's scale. `resolution` and
    `padding_px` default to the size `pack` recorded, else 2048 and 8."""
    objects = list(objects)
    packed = recorded(objects)
    if resolution is None:
        resolution = packed['resolution'] if packed else 2048
    if padding_px is None:
        padding_px = packed['padding_px'] if packed else 8
    min_px = LIMITS['chart_width'] * resolution if min_px is None else min_px
    joined = rejected = 0
    failed = set()
    for _ in range(rounds):
        groups = {}
        for obj in objects:
            charts = _charts(obj, uv_name)
            taken = set()
            for key, chart in sorted(charts.items(), key=lambda item: item[1]['area']):
                width = 2 * chart['area'] / chart['perimeter'] * resolution if chart['perimeter'] else 0.0
                if width >= min_px or key in taken:
                    continue
                for target in sorted(chart['neighbours'], key=lambda k: -sum(l for _, l in chart['neighbours'][k])):
                    other = charts[target]
                    pair = (obj.name, min(chart['faces']), min(other['faces']))
                    closes = not (chart['open'] or other['open'] or set(chart['neighbours']) - {target}
                                  or set(other['neighbours']) - {key})
                    if pair in failed or closes or target in taken:
                        continue
                    groups.setdefault(obj.name, []).append(
                        [chart['faces'] | other['faces'], [edge for edge, _ in chart['neighbours'][target]], pair])
                    taken.update((key, target))
                    break
        if not groups:
            break
        by_name = {o.name: o for o in objects}
        saved = {}
        for name, pairs in groups.items():
            mesh = by_name[name].data
            uv, seams = np.empty(len(mesh.loops) * 2), np.empty(len(mesh.edges), dtype=bool)
            mesh.uv_layers[uv_name].data.foreach_get('uv', uv)
            mesh.edges.foreach_get('use_seam', seams)
            saved[name] = (uv, seams)
            merged = []
            for faces, edges, pair in pairs:
                keys = [pair]
                for group in [g for g in merged if g[0] & faces]:
                    merged.remove(group)
                    faces, edges, keys = faces | group[0], edges + group[1], keys + group[2]
                merged.append([faces, edges, keys])
            groups[name] = merged
            for _, edges, _ in merged:
                for edge in edges:
                    mesh.edges[edge].use_seam = False
        unwrap([by_name[n] for n in groups], uv_name=uv_name,
               faces={n: sorted(set().union(*(g[0] for g in merged))) for n, merged in groups.items()})
        accepted = 0
        for name, merged in groups.items():
            obj = by_name[name]
            metrics = face_metrics(obj, obj.data, uv_name, resolution)
            layer, (uv, seams) = obj.data.uv_layers[uv_name], saved[name]
            current = np.empty(len(obj.data.loops) * 2)
            layer.data.foreach_get('uv', current)
            loops = np.empty(len(obj.data.loop_triangles) * 3, dtype=np.int64)
            obj.data.loop_triangles.foreach_get('loops', loops)
            triangles = current.reshape(-1, 2)[loops.reshape(-1, 3)]
            islands = [chart['faces'] for chart in _charts(obj, uv_name).values()]
            for faces, edges, keys in merged:
                mask = np.isin(metrics['polygon'], list(faces))
                stretch = _weighted_percentile(metrics['anisotropy'][mask], metrics['area'][mask], .95)
                folded = any(_folds(triangles[np.isin(metrics['polygon'], list(island))])
                             for island in islands if island & faces)
                if stretch is not None and stretch <= LIMITS['stretch_p95'] and not folded:
                    accepted += len(keys)
                    continue
                for edge in edges:
                    obj.data.edges[edge].use_seam = bool(seams[edge])
                for face in faces:
                    for loop in obj.data.polygons[face].loop_indices:
                        layer.data[loop].uv = uv[2 * loop:2 * loop + 2]
                failed.update(keys)
                rejected += len(keys)
        pack(objects, uv_name=uv_name, resolution=resolution, padding_px=padding_px, rotate=rotate)
        joined += accepted
    left = narrow_charts(objects, uv_name=uv_name, resolution=resolution, min_px=min_px)
    return {'joined': joined, 'rejected': rejected, 'narrow_left': len(left['narrow']),
            'whole_parts': left['whole_parts']}


def face_metrics(obj, mesh, uv_name=UV, resolution=2048):
    """Per-triangle anisotropy (1 is undistorted), world area (m2), UV area and owning polygon.

    `mesh` is the evaluated mesh of `obj`. Degenerate or zero-UV triangles report infinite anisotropy.
    """
    layer = mesh.uv_layers.get(uv_name)
    if layer is None:
        return None
    mesh.calc_loop_triangles()
    count = len(mesh.loop_triangles)
    loops = np.empty(count * 3, dtype=np.int64)
    verts = np.empty(count * 3, dtype=np.int64)
    polys = np.empty(count, dtype=np.int64)
    mesh.loop_triangles.foreach_get('loops', loops)
    mesh.loop_triangles.foreach_get('vertices', verts)
    mesh.loop_triangles.foreach_get('polygon_index', polys)
    co = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get('co', co)
    matrix = np.array(obj.matrix_world)
    co = co.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
    co *= bpy.context.scene.unit_settings.scale_length
    uv = np.empty(len(mesh.loops) * 2)
    layer.data.foreach_get('uv', uv)
    uv = uv.reshape(-1, 2)
    p = co[verts.reshape(-1, 3)]
    t = uv[loops.reshape(-1, 3)]
    e, f = p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]
    du, dv = t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]
    x = np.linalg.norm(e, axis=1)
    cross = np.linalg.norm(np.cross(e, f), axis=1)
    h = np.divide(cross, x, out=np.zeros_like(x), where=x > 0)
    y = np.divide(np.einsum('ij,ij->i', e, f), x, out=np.zeros_like(x), where=x > 0)
    uv_area = np.abs(du[:, 0] * dv[:, 1] - du[:, 1] * dv[:, 0]) * 0.5
    valid = (x > 1e-12) & (h > 1e-12) & (uv_area > 1e-16) & np.isfinite(uv_area)
    xs, hs = np.where(valid, x, 1), np.where(valid, h, 1)
    a, c = du[:, 0] / xs, du[:, 1] / xs
    b, d = (dv[:, 0] - a * y) / hs, (dv[:, 1] - c * y) / hs
    trace = a * a + b * b + c * c + d * d
    det = np.abs(a * d - b * c)
    largest = (trace + np.sqrt(np.maximum(0, trace * trace - 4 * det * det))) * 0.5
    ratio = np.where(valid & (det > 0), largest / np.where(det > 0, det, 1), np.inf)
    scale = bpy.context.scene.unit_settings.scale_length
    normal = np.cross(e, f)
    normal = normal / np.where(cross > 0, cross, 1)[:, None]
    return {'anisotropy': ratio, 'area': cross * 0.5, 'uv_area': uv_area, 'polygon': polys,
            'centre': p.mean(axis=1) / scale, 'normal': normal,
            'outside': int(((t < -1e-6) | (t > 1 + 1e-6)).any(axis=(1, 2)).sum()),
            'resolution': resolution}


def _weighted_percentile(values, weights, fraction):
    finite = np.isfinite(values)
    if not finite.any() or weights[finite].sum() <= 0:
        return None
    order = np.argsort(values[finite])
    cumulative = np.cumsum(weights[finite][order])
    return float(values[finite][order][np.searchsorted(cumulative, fraction * cumulative[-1])])


@contextmanager
def _evaluated(objects):
    """The evaluated mesh of each object by name, converted once and cleared on exit."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
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


def _hash_mesh(digest, mesh, uv_name):
    """Feed a mesh's positions, face sizes, corner vertices, edges, corner normals and atlas UVs to the digest."""
    layer = mesh.uv_layers.get(uv_name)
    for collection, name, kind, width in ((mesh.vertices, 'co', np.float32, 3),
                                          (mesh.polygons, 'loop_total', np.int32, 1),
                                          (mesh.loops, 'vertex_index', np.int32, 1),
                                          (mesh.edges, 'vertices', np.int32, 2),
                                          (getattr(mesh, 'corner_normals', ()), 'vector', np.float32, 3),
                                          (layer.data if layer else (), 'uv', np.float32, 2)):
        values = np.empty(len(collection) * width, dtype=kind)
        if len(values):
            collection.foreach_get(name, values)
        digest.update(str(len(values)).encode())
        digest.update(values.tobytes())


def _hash_modifiers(digest, obj):
    """Feed every setting of every modifier to the digest: a render level changes the images, not the mesh."""
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


def marks(root_or_objects, *, uv_name=UV, meshes=None):
    """A change mark for each part and one for the asset: `{'asset': hex, 'parts': {name: hex}}`.

    A part's mark is a hash of its modelled and evaluated meshes (positions, faces, corner normals and the
    atlas UVs), its world matrix, every modifier setting and the resolution and padding `pack` recorded. It
    changes when the geometry or the atlas does, so review images and a kept report can be matched to the
    asset as it is now. `meshes` maps part names to evaluated meshes that are already open.
    """
    objects = asset_meshes(root_or_objects)
    if meshes is None:
        with _evaluated(objects) as meshes:
            return _marks(objects, uv_name, meshes)
    return _marks(objects, uv_name, meshes)


def _marks(objects, uv_name, meshes):
    parts, whole = {}, hashlib.sha1(uv_name.encode())
    for obj in objects:
        digest = hashlib.sha1()
        _hash_mesh(digest, obj.data, uv_name)
        _hash_mesh(digest, meshes[obj.name], uv_name)
        digest.update(np.array(obj.matrix_world, dtype=np.float32).tobytes())
        _hash_modifiers(digest, obj)
        digest.update(repr((obj.get('marso_uv_resolution'), obj.get('marso_uv_padding_px'))).encode())
        parts[obj.name] = digest.hexdigest()[:20]
    # The asset mark does not depend on the order the parts were listed in.
    whole.update(repr(sorted(parts.items())).encode())
    return {'asset': whole.hexdigest()[:20], 'parts': parts}


class _Measured:
    """An open evaluated mesh, presented to the per-object measuring helpers in place of a temporary copy."""
    type = 'MESH'

    def __init__(self, obj, mesh):
        self.name, self.data, self.matrix_world = obj.name + '.measure', mesh, obj.matrix_world.copy()


def report(root_or_objects, *, uv_name=UV, resolution=None, padding_px=None, addon_module=None, limits=None,
           meshes=None, timings=None):
    """Measure the shared atlas on the evaluated meshes and say whether it meets the limits.

    Per part: area-weighted stretch p95, texel density and invalid triangles. Asset: density spread
    (largest over smallest part density), fill (UV area over the tile), triangles outside the tile,
    overlaps and padding. Overlaps use the installed add-on's own validator, which is what Retexture
    accepts; without the add-on a stricter bundled audit is used and named in the result. Above 150,000
    evaluated faces padding is measured on the meshes before modifiers, and an asset too large even then
    fails as unmeasured. Hidden meshes under the root fail as unmeasured. `worst_polygons` index the
    evaluated mesh, not the source faces.

    `resolution` and `padding_px` default to the size `pack` recorded, else 2048 and 8; `packed_for` gives
    the recorded size, so a measurement at another size shows. `worst_patch` names the single most
    stretched face of the asset with its world position, and `stretched_area_share` is the share of the
    surface stretched past 1.5.

    `meshes` maps part names to evaluated meshes that are already open, read instead of converting each
    part again; do not render or edit the scene while they are open. `timings` is a dict that receives the
    seconds each stage took.
    """
    objects = asset_meshes(root_or_objects)
    if meshes is None:
        with _evaluated(objects) as meshes:
            return _report(root_or_objects, objects, meshes, uv_name, resolution, padding_px, addon_module, limits,
                           timings)
    return _report(root_or_objects, objects, meshes, uv_name, resolution, padding_px, addon_module, limits, timings)


def _report(root_or_objects, objects, meshes, uv_name, resolution, padding_px, addon_module, limits, timings):
    started = lap = time.perf_counter()
    timings = {} if timings is None else timings
    packed = recorded(objects)
    if resolution is None:
        resolution = packed['resolution'] if packed else 2048
    if padding_px is None:
        padding_px = packed['padding_px'] if packed else 8
    worst_patch, stretched_area, total_area = None, 0.0, 0.0
    limits = dict(LIMITS, **(limits or {}))
    addon_module = addon_module or installed_addon()
    parts, missing, outside, records, total_uv = {}, [], 0, [], 0.0
    face_count = 0
    for obj in objects:
        mesh = meshes[obj.name]
        metrics = face_metrics(obj, mesh, uv_name, resolution)
        face_count += len(mesh.polygons)
        if metrics is None:
            missing.append(obj.name)
            continue
        area, uv_area = metrics['area'], metrics['uv_area']
        invalid = int((~np.isfinite(metrics['anisotropy'])).sum())
        worst = np.argsort(np.where(np.isfinite(metrics['anisotropy']), metrics['anisotropy'], 1e9))[-3:]
        finite = np.where(np.isfinite(metrics['anisotropy']), metrics['anisotropy'], 0.0)
        total_area += float(area.sum())
        stretched_area += float(area[finite > 1.5].sum())
        top = int(np.argmax(finite)) if len(finite) else None
        if top is not None and (worst_patch is None or finite[top] > worst_patch['stretch']):
            worst_patch = {'object': obj.name, 'polygon': int(metrics['polygon'][top]),
                           'stretch': round(float(finite[top]), 3),
                           'centre': [round(float(v), 5) for v in metrics['centre'][top]],
                           'normal': [round(float(v), 4) for v in metrics['normal'][top]]}
        density = resolution * math.sqrt(uv_area.sum() / area.sum()) if area.sum() > 0 else 0.0
        parts[obj.name] = {
            'stretch_p95': _weighted_percentile(metrics['anisotropy'], area, .95),
            'stretch_max': float(np.nanmax(np.where(np.isfinite(metrics['anisotropy']),
                                                    metrics['anisotropy'], np.nan)))
            if invalid < len(area) else None,
            'worst_polygons': [int(metrics['polygon'][i]) for i in worst[::-1]],
            'px_per_m': density, 'invalid_triangles': invalid,
            'outside_tile_triangles': metrics['outside'], 'faces': len(mesh.polygons)}
        outside += metrics['outside']
        total_uv += float(uv_area.sum())
        if addon_module is not None:
            uv = np.empty(len(mesh.loops) * 2)
            mesh.uv_layers[uv_name].data.foreach_get('uv', uv)
            count = len(mesh.loop_triangles)
            loops, areas = np.empty(count * 3, dtype=np.int64), np.empty(count)
            mesh.loop_triangles.foreach_get('loops', loops)
            mesh.loop_triangles.foreach_get('area', areas)
            corners = uv.reshape(-1, 2)[loops.reshape(-1, 3)].tolist()
            name = obj.name
            records.extend((0, (name, polygon), tuple(map(tuple, points)), surface) for polygon, points, surface
                           in zip(metrics['polygon'].tolist(), corners, areas.tolist()))
    timings['metrics'], lap = _lap(lap), time.perf_counter()
    densities = [p['px_per_m'] for p in parts.values() if p['px_per_m'] > 0]
    spread = max(densities) / min(densities) if densities else None
    measured = [_Measured(obj, meshes[obj.name]) for obj in objects]
    if addon_module is not None:
        conflict = _addon_module(addon_module, 'uv_validation').first_conflict(records)
        overlap = {'validator': 'add-on', 'conflict': conflict}
    elif not missing:
        audit = audit_uv(measured, uv_name=uv_name, resolution=resolution)
        overlap = {'validator': 'bundled (stricter than the add-on)', 'conflict': None if not audit['overlap_pairs'] else
                   'overlapping triangles: ' + str(audit['overlap_examples'][:3]),
                   'mirrored_triangles': audit['mirrored_triangles']}
    else:
        overlap = {'validator': None, 'conflict': 'missing layer'}
    timings['overlap'], lap = _lap(lap), time.perf_counter()
    cage_faces = sum(len(obj.data.polygons) for obj in objects)
    if missing:
        padding = {'checked': False, 'reason': 'missing layer'}
    elif face_count > PADDING_CHECK_FACES and cage_faces > PADDING_CHECK_FACES:
        padding = {'checked': False, 'reason': 'over 150,000 faces even before modifiers'}
    else:
        evaluated = face_count <= PADDING_CHECK_FACES
        quality = measure_uv_quality(measured if evaluated else objects, uv_name=uv_name,
                                     resolution=resolution, padding_px=padding_px / 2)
        padding = {'checked': True, 'passed': quality['padding_passed'],
                   'measured_on': 'evaluated meshes' if evaluated else 'meshes before modifiers (evaluated over 150,000 faces)',
                   'violation_pairs': quality['padding_violation_pairs'],
                   'examples': quality['padding_examples'][:3],
                   'tile_border_px_min': quality['tile_border_px_min'], 'islands': quality['islands']}
    timings['padding'], lap = _lap(lap), time.perf_counter()
    failures = []
    hidden = hidden_meshes(root_or_objects)
    if hidden:
        failures.append('hidden parts not measured: ' + ', '.join(hidden))
    if missing:
        failures.append('missing ' + uv_name + ': ' + ', '.join(missing))
    for name, part in parts.items():
        if part['invalid_triangles']:
            failures.append('{}: {} zero-area or degenerate UV triangles'.format(name, part['invalid_triangles']))
        if part['stretch_p95'] is None or part['stretch_p95'] > limits['stretch_p95']:
            failures.append('{}: stretch p95 {} above {}'.format(name, _round(part['stretch_p95']),
                                                                  limits['stretch_p95']))
    if spread is not None and spread > limits['density_spread']:
        failures.append('density spread {:.2f} above {}'.format(spread, limits['density_spread']))
    if total_uv < limits['fill']:
        failures.append('fill {:.2f} below {}'.format(total_uv, limits['fill']))
    if outside:
        failures.append('{} triangles outside the 0-1 tile'.format(outside))
    if overlap['conflict']:
        failures.append('overlap: ' + str(overlap['conflict']))
    if padding.get('checked') and not padding['passed']:
        failures.append('padding below {} px'.format(padding_px / 2))
    elif not padding.get('checked') and not missing:
        failures.append('padding not measured: ' + padding['reason'])
    narrow = None if missing else narrow_charts(objects, uv_name=uv_name, resolution=resolution,
                                                min_px=limits['chart_width'] * resolution)
    if narrow and narrow['narrow']:
        failures.append('{} charts narrower than {:g} px; join them with join_small_charts'.format(
            len(narrow['narrow']), narrow['min_px']))
    if narrow:
        narrow = {'min_px': narrow['min_px'], 'count': len(narrow['narrow']),
                  'examples': sorted(narrow['narrow'], key=lambda c: c['width_px'])[:10],
                  'whole_parts': narrow['whole_parts'][:10]}
    timings['narrow_charts'], timings['total'] = _lap(lap), _lap(started)
    return {'passed': not failures, 'failures': failures, 'uv_name': uv_name, 'resolution': resolution,
            'padding_px': padding_px, 'packed_for': packed, 'worst_patch': worst_patch,
            'stretched_area_share': round(stretched_area / total_area, 4) if total_area else None,
            'fill': round(total_uv, 4), 'density_spread': _round(spread), 'outside_tile_triangles': outside,
            'overlap': overlap, 'padding': padding, 'narrow_charts': narrow, 'limits': limits, 'parts': parts,
            'scope': 'measured on evaluated meshes; visual review of checker and stretch images still required'}


def mark_pixels(result, part, size_m):
    """Texture pixels across a mark `size_m` wide on `part`, from a `report` result: the narrowest stroke
    of lettering, a stripe or a stitch. Uses the part's mean density divided by the root of its p95
    stretch, so it is the count in the worse direction."""
    entry = result['parts'][part]
    return round(size_m * entry['px_per_m'] / math.sqrt(max(entry['stretch_p95'] or 1.0, 1.0)), 2)


def _round(value):
    return None if value is None else round(value, 3)


def _lap(since):
    return round(time.perf_counter() - since, 3)


_COPIES = []


def _evaluated_copies(objects):
    """Temporary objects holding each evaluated mesh, for the per-object measuring helpers."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    copies = []
    for obj in objects:
        mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
        copy = bpy.data.objects.new(obj.name + '.measure', mesh)
        copy.matrix_world = obj.matrix_world.copy()
        copies.append(copy)
    _COPIES.extend(copies)
    return copies


def _remove_copies():
    while _COPIES:
        copy = _COPIES.pop()
        mesh = copy.data
        bpy.data.objects.remove(copy)
        bpy.data.meshes.remove(mesh)


def installed_addon():
    """The enabled Marso add-on package, or None when it is not installed."""
    for name, module in list(sys.modules.items()):
        if (name == 'marso' or name.endswith('.marso')) and hasattr(module, '__path__'):
            try:
                if hasattr(_addon_module(module, 'uv_validation'), 'first_conflict'):
                    return module
            except ImportError:
                continue
    return None


def _addon_module(addon_module, name):
    package = addon_module if isinstance(addon_module, str) else addon_module.__name__
    module = sys.modules.get(package + '.core.' + name)
    if module is None:
        import importlib
        module = importlib.import_module(package + '.core.' + name)
    return module


def check_part(obj, *, uv_name=UV, resolution=2048, padding_px=8, addon_module=None):
    """Pack and measure one representative part on a disposable copy, leaving the original untouched.

    Use it once per new construction family before repeating the part. Isolated scale is not the final
    atlas scale; run `report` on the whole asset after the shared pack.
    """
    if obj.type != 'MESH' or obj.data.uv_layers.get(uv_name) is None:
        raise ValueError('Unwrap the part before checking it: ' + obj.name)
    copy = _evaluated_copies([obj])[0]
    _COPIES.remove(copy)
    bpy.context.scene.collection.objects.link(copy)
    try:
        pack([copy], uv_name=uv_name, resolution=resolution, padding_px=padding_px)
        result = report([copy], uv_name=uv_name, resolution=resolution, padding_px=padding_px,
                        addon_module=addon_module, limits={'fill': 0.0})
        result['scope'] = 'isolated part; final shared atlas still required'
        return result
    finally:
        mesh = copy.data
        bpy.data.objects.remove(copy)
        bpy.data.meshes.remove(mesh)
