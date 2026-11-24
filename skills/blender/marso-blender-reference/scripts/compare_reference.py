"""Compare a model with a reference image from the same side, inside Blender.

`compare` renders a clay view of the asset, fits the reference to it, and writes one image of three panels: the
reference, the model, and an overlay with the model outline in red and the reference outline in blue. Where the
reference background is plain it also measures the match: the share of the two silhouettes that overlaps, and
their filled sizes at ten stations each way. `match_view` finds the camera direction of a three-quarter photo,
so the same measurement works on it.
"""

from contextlib import contextmanager
import json
import math
from pathlib import Path
import tempfile

import bpy
import numpy as np
from mathutils import Vector

VIEWS = {'front': (0, -1, 0), 'back': (0, 1, 0), 'right': (1, 0, 0), 'left': (-1, 0, 0), 'top': (0, 0, 1)}
MARGIN = 0.08
STATIONS = 10
OVERLAP_LIMIT = 0.85
STATION_LIMIT = 0.05
THIN_LIMIT, THIN_FLOOR = 0.25, 0.015
RECORD = 'marso_comparisons'
RED, BLUE = np.array([0.85, 0.1, 0.1]), np.array([0.1, 0.3, 0.9])


def _meshes(root_or_objects):
    if isinstance(root_or_objects, bpy.types.Object):
        candidates = [root_or_objects] + list(root_or_objects.children_recursive)
    else:
        candidates = list(root_or_objects)
    meshes = [o for o in candidates if o.type == 'MESH' and o.visible_get() and not o.hide_render
              and len(o.data.polygons)]
    if not meshes:
        raise ValueError('No visible mesh with faces in the selection')
    return meshes


def _read(path):
    """RGBA pixels, top row first."""
    image = bpy.data.images.load(str(path), check_existing=False)
    try:
        width, height = image.size
        if not width or not height:
            raise ValueError('Could not read the image: ' + str(path))
        pixels = np.empty(width * height * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        return pixels.reshape(height, width, 4)[::-1].copy()
    finally:
        bpy.data.images.remove(image)


def _write(array, path):
    height, width = array.shape[:2]
    rgba = np.concatenate([array[..., :3], np.ones((height, width, 1), dtype=np.float32)], axis=2)
    image = bpy.data.images.new('MarsoReferenceCompare', width, height, alpha=True)
    try:
        image.pixels.foreach_set(np.ascontiguousarray(rgba[::-1], dtype=np.float32).ravel())
        image.filepath_raw = str(path)
        image.file_format = 'PNG'
        image.save()
    finally:
        bpy.data.images.remove(image)


def _box(mask):
    rows, cols = np.nonzero(mask)
    if not len(rows):
        return None
    return int(cols.min()), int(rows.min()), int(cols.max()) + 1, int(rows.max()) + 1


def _outline(mask):
    inner = mask.copy()
    inner[1:, :] &= mask[:-1, :]
    inner[:-1, :] &= mask[1:, :]
    inner[:, 1:] &= mask[:, :-1]
    inner[:, :-1] &= mask[:, 1:]
    edge = mask & ~inner
    thick = edge.copy()
    thick[1:, :] |= edge[:-1, :]
    thick[:, 1:] |= edge[:, :-1]
    return thick


def _object_mask(pixels, box, drop_shadow=False):
    """The object's pixels and its box (left, top, right, bottom). A plain background is separated by colour;
    a busy one needs `box` and gives no mask. `drop_shadow` also removes pixels that are the background's
    colour evenly darkened, which is what a soft cast shadow is."""
    rgb = pixels[..., :3]
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    background = np.median(border, axis=0)
    plain = float(np.abs(border - background).max(axis=1).mean()) < 0.06
    if plain:
        mask = np.abs(rgb - background).max(axis=2) > 0.12
        if drop_shadow:
            ratio = rgb / np.maximum(background, 1e-3)
            level = ratio.mean(axis=2)
            mask &= ~((np.abs(ratio - level[..., None]).max(axis=2) < 0.05) & (level > 0.55))
        if pixels.shape[2] == 4 and pixels[..., 3].min() < 0.5:
            mask &= pixels[..., 3] > 0.5
        if box is not None:
            left, top, right, bottom = box
            keep = np.zeros_like(mask)
            keep[top:bottom, left:right] = True
            mask &= keep
        found = _box(mask)
        if found is None:
            raise ValueError('No object found against the plain background; pass box=(left, top, right, bottom)')
        return mask, found, 'plain background'
    if box is None:
        raise ValueError('The background is not plain; pass box=(left, top, right, bottom) in image pixels '
                         'around the object')
    return None, tuple(int(v) for v in box), 'box only'


@contextmanager
def _clay(objects, width, height):
    scene = bpy.context.scene
    shading = scene.display.shading
    render = scene.render
    saved = (render.engine, render.resolution_x, render.resolution_y, render.resolution_percentage,
             render.filepath, render.image_settings.file_format, render.image_settings.color_mode,
             render.film_transparent,
             scene.view_settings.view_transform, scene.view_settings.look, shading.light, shading.color_type,
             tuple(shading.single_color), scene.camera, bpy.context.view_layer.material_override)
    keep = {o.name for o in objects}
    hidden = {o.name: o.hide_render for o in scene.objects}
    try:
        render.engine = 'BLENDER_WORKBENCH'
        render.resolution_x, render.resolution_y, render.resolution_percentage = width, height, 100
        render.image_settings.file_format = 'PNG'
        render.image_settings.color_mode = 'RGBA'
        render.film_transparent = True
        scene.view_settings.view_transform, scene.view_settings.look = 'Standard', 'None'
        shading.light, shading.color_type, shading.single_color = 'STUDIO', 'SINGLE', (0.7, 0.7, 0.7)
        bpy.context.view_layer.material_override = None
        for o in scene.objects:
            if o.name not in keep:
                o.hide_render = True
        yield scene
    finally:
        for name, value in hidden.items():
            if name in scene.objects:
                scene.objects[name].hide_render = value
        (render.engine, render.resolution_x, render.resolution_y, render.resolution_percentage,
         render.filepath, render.image_settings.file_format, render.image_settings.color_mode,
             render.film_transparent,
         scene.view_settings.view_transform, scene.view_settings.look, shading.light, shading.color_type,
         shading.single_color, scene.camera, bpy.context.view_layer.material_override) = saved


def _direction(view):
    """The unit vector from the asset towards the camera for a named view or an (x, y, z) direction."""
    if isinstance(view, str):
        if view not in VIEWS:
            raise ValueError('Unknown view: ' + str(view))
        return Vector(VIEWS[view])
    try:
        direction = Vector([float(v) for v in view])
    except (TypeError, ValueError):
        raise ValueError('Unknown view: ' + str(view))
    if len(direction) != 3 or direction.length < 1e-6:
        raise ValueError('Unknown view: ' + str(view))
    return direction.normalized()


def _render_model(objects, view, size, lens=None):
    """Clay render from `view`, framed on the asset: RGBA pixels, top row first. Orthographic unless `lens`
    (millimetres on a 36 mm sensor) asks for perspective."""
    direction = _direction(view)
    data = bpy.data.cameras.new('MarsoReferenceCamera')
    data.type = 'PERSP' if lens else 'ORTHO'
    cam = bpy.data.objects.new('MarsoReferenceCamera', data)
    bpy.context.scene.collection.objects.link(cam)
    try:
        if abs(direction.z) > 0.999:
            cam.rotation_euler = (0, 0, 0) if direction.z > 0 else (math.pi, 0, 0)
        else:
            cam.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        right = cam.matrix_world.to_3x3() @ Vector((1, 0, 0))
        up = cam.matrix_world.to_3x3() @ Vector((0, 1, 0))
        corners = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
        across = [c.dot(right) for c in corners]
        along = [c.dot(up) for c in corners]
        depth = [c.dot(direction) for c in corners]
        span_x, span_y = max(across) - min(across), max(along) - min(along)
        span = max(span_x, span_y, 1e-6) * (1 + 2 * MARGIN)
        centre = (right * (max(across) + min(across)) / 2 + up * (max(along) + min(along)) / 2)
        reach = max(depth) - min(depth) + span
        width = height = size
        if lens:
            data.lens, data.sensor_width, data.sensor_fit = lens, 36, 'HORIZONTAL'
            distance = span * lens / 36 + (max(depth) - min(depth)) / 2
            cam.location = centre + direction * ((max(depth) + min(depth)) / 2 + distance)
            data.clip_start, data.clip_end = distance / 100, distance * 4 + reach
        else:
            cam.location = centre + direction * (max(depth) + span)
            data.ortho_scale = span
            data.clip_start, data.clip_end = span / 1000, reach * 4
            if span_x >= span_y:
                height = max(64, round(size * (span_y * (1 + 2 * MARGIN) / span)))
            else:
                width = max(64, round(size * (span_x * (1 + 2 * MARGIN) / span)))
        with _clay(objects, width, height) as scene, tempfile.TemporaryDirectory() as scratch:
            scene.camera = cam
            scene.render.filepath = str(Path(scratch) / 'model.png')
            bpy.ops.render.render(write_still=True)
            return _read(scene.render.filepath)
    finally:
        bpy.data.objects.remove(cam)
        bpy.data.cameras.remove(data)


def _sample(shape, source_shape, ref_box, model_box, scale, step=1):
    """For each output pixel, the reference pixel under it, and whether that lies inside the reference."""
    rl, rt, rr, rb = ref_box
    ml, mt, mr, mb = model_box
    ys, xs = np.mgrid[0:shape[0]:step, 0:shape[1]:step]
    sx = np.round((rl + rr) / 2 + (xs + 0.5 - (ml + mr) / 2) / scale - 0.5).astype(int)
    sy = np.round((rt + rb) / 2 + (ys + 0.5 - (mt + mb) / 2) / scale - 0.5).astype(int)
    inside = (sx >= 0) & (sx < source_shape[1]) & (sy >= 0) & (sy < source_shape[0])
    return np.clip(sx, 0, source_shape[1] - 1), np.clip(sy, 0, source_shape[0] - 1), inside


def _overlap(a, b):
    union = np.count_nonzero(a | b)
    return float(np.count_nonzero(a & b) / union) if union else 0.0


def _fit(model_mask, ref_mask, ref_box, axis, grids=((0.08, 9), (0.015, 7))):
    """Scale and model box that lay the reference over the model: box against box, then the uniform scale and
    shift nearby with the greatest silhouette overlap. A uniform fit cannot hide a wrong proportion."""
    model_box = _box(model_mask)
    ml, mt, mr, mb = model_box
    rl, rt, rr, rb = ref_box
    scale = (mr - ml) / (rr - rl) if axis == 'width' else (mb - mt) / (rb - rt)
    if ref_mask is None:
        return scale, model_box, None
    size = max(mr - ml, mb - mt)
    step = max(1, max(model_mask.shape) // 256)
    small = model_mask[::step, ::step]
    best = (-1.0, scale, model_box)
    for spread, count in grids:
        centre_scale, (cl, ct, cr, cb) = best[1], best[2]
        for factor in np.linspace(1 - spread, 1 + spread, count):
            for dx in np.linspace(-spread, spread, count) * size:
                for dy in np.linspace(-spread, spread, count) * size:
                    box = (cl + dx, ct + dy, cr + dx, cb + dy)
                    sx, sy, inside = _sample(model_mask.shape, ref_mask.shape, ref_box, box,
                                             centre_scale * factor, step)
                    score = _overlap(small, ref_mask[sy, sx] & inside)
                    if score > best[0]:
                        best = (score, centre_scale * factor, box)
    return best[1], best[2], best[0]


def _profile(mask, frame, rows):
    """Filled size and both edges at each station across `frame` (left, top, right, bottom), as fractions of
    the frame's longer side. `rows` walks up the height; otherwise along the width."""
    left, top, right, bottom = frame
    unit = max(right - left, bottom - top)
    area = mask[top:bottom, left:right]
    if not rows:
        area = area.T
    length = area.shape[0]
    stations = []
    for index in range(STATIONS):
        a = round(length * index / STATIONS)
        band = area[a:max(round(length * (index + 1) / STATIONS), a + 1)]
        filled = band.sum(axis=1)
        used = band[filled > 0]
        if len(used):
            first = used.argmax(axis=1).mean()
            last = (used.shape[1] - used[:, ::-1].argmax(axis=1)).mean()
        else:
            first = last = 0.0
        at = (index + 0.5) / STATIONS
        stations.append({'at': round(1 - at if rows else at, 2), 'filled': float(filled.mean()) / unit,
                         'low': first / unit, 'high': last / unit})
    return stations


def _measure(model_mask, placed_mask, valid, gate_edges=True):
    """Overlap and station figures for two silhouettes in the same frame. Edge positions depend on the camera,
    so with `gate_edges` off they are reported as `shifts` and do not count towards `passed`."""
    model_mask, placed_mask = model_mask & valid, placed_mask & valid
    frame = _box(placed_mask)
    if frame is None:
        return None
    report = {'overlap': round(_overlap(model_mask, placed_mask), 3), 'rows': [], 'columns': []}
    findings, shifts = [], []
    for rows, key, along, words, edges in (
            (True, 'rows', 'height', ('wider', 'narrower'), ('left edge', 'right edge')),
            (False, 'columns', 'length', ('taller', 'shorter'), ('top edge', 'bottom edge'))):
        for ref, model in zip(_profile(placed_mask, frame, rows), _profile(model_mask, frame, rows)):
            gap = model['filled'] - ref['filled']
            share = abs(gap) / ref['filled'] if ref['filled'] else 0.0
            report[key].append({'at': ref['at'], 'reference': round(ref['filled'], 3),
                                'model': round(model['filled'], 3), 'difference': round(gap, 3)})
            where = 'at {:.2f} of the {}'.format(ref['at'], along)
            word = words[0] if gap > 0 else words[1]
            findings.append((abs(gap) / STATION_LIMIT,
                             '{} the model is {} by {:.0%} of the overall size ({:.3f} against {:.3f})'.format(
                                 where, word, abs(gap), model['filled'], ref['filled'])))
            if abs(gap) > THIN_FLOOR:
                findings.append((share / THIN_LIMIT * 0.999,
                                 '{} the model is {} by {:.0%} of the reference there ({:.3f} against {:.3f})'.format(
                                     where, word, share, model['filled'], ref['filled'])))
            if ref['filled'] and model['filled']:
                for side, edge in zip(('low', 'high'), edges):
                    shift = abs(model[side] - ref[side])
                    (findings if gate_edges else shifts).append((shift / STATION_LIMIT * 0.998,
                                     "{} the model's {} is out by {:.0%} of the overall size".format(
                                         where, edge, shift)))
    findings.sort(key=lambda item: -item[0])
    report['largest_difference'] = round(findings[0][0] * STATION_LIMIT, 3)
    report['worst'] = [text for amount, text in findings[:3] if amount > 0.5]
    if report['overlap'] < OVERLAP_LIMIT:
        report['worst'].append('the silhouettes share only {:.0%} of their area; check the view, mirror and '
                               'outline before changing the model'.format(report['overlap']))
    if not gate_edges:
        shifts.sort(key=lambda item: -item[0])
        report['shifts'] = [text for amount, text in shifts[:2] if amount > 1]
    report['passed'] = bool(report['overlap'] >= OVERLAP_LIMIT and findings[0][0] <= 1)
    return report


def _load_reference(reference, mirror, box, drop_shadow, ignore=()):
    """The reference pixels, the object's mask and box, and how the mask was found. Boxes in `ignore` are
    cleared from the mask before the box is taken, so a watermark or stand cannot steer the fit."""
    source = _read(reference)
    width = source.shape[1]
    ignore = [tuple(int(v) for v in item) for item in ignore]
    if mirror:
        source = source[:, ::-1].copy()
        if box is not None:
            box = (width - box[2], box[1], width - box[0], box[3])
        ignore = [(width - right, top, width - left, bottom) for left, top, right, bottom in ignore]
    mask, found, how = _object_mask(source, box, drop_shadow)
    if mask is not None and ignore:
        for left, top, right, bottom in ignore:
            mask[max(top, 0):bottom, max(left, 0):right] = False
        found = _box(mask)
        if found is None:
            raise ValueError('The ignore boxes cover the whole object')
    return source, mask, found, how, ignore


def match_view(root_or_objects, reference, *, near='front', mirror=False, box=None, ignore=(),
               drop_shadow=False, spread=30, lenses=(None, 85, 50, 35), size=160):
    """Find the camera direction of a photo that is not a level side or front view.

    Searches directions within `spread` degrees of `near` (a view name or an (x, y, z) direction from the asset
    towards the camera) for each lens in `lenses` (None is orthographic). It keeps the camera that best explains
    the photo: the greatest silhouette overlap less the largest station difference. The lens matters: a
    perspective photo measured through an orthographic camera reports near parts as too thin. Returns `view`
    and `lens` to pass to `compare`. Pass the same `mirror`, `box`, `ignore` and `drop_shadow` as to `compare`.
    The reference needs a plain background.
    """
    reference = Path(reference)
    if not reference.is_file():
        raise FileNotFoundError(reference)
    objects = _meshes(root_or_objects)
    _, ref_mask, ref_box, _, _ = _load_reference(reference, mirror, box, drop_shadow, ignore)
    if ref_mask is None:
        raise ValueError('match_view needs a plain background; crop or clean the reference first')
    start = _direction(near)

    def score(direction, lens):
        """Overlap less the largest station difference: the camera that best explains the photo."""
        mask = _render_model(objects, direction, size, lens)[..., 3] > 0.5
        if not mask.any():
            return -1.0, 0.0
        scale, box, _ = _fit(mask, ref_mask, ref_box, 'width', ((0.06, 5),))
        sx, sy, inside = _sample(mask.shape, ref_mask.shape, ref_box, box, scale)
        measured = _measure(mask, ref_mask[sy, sx] & inside, np.ones(mask.shape, dtype=bool), False)
        if measured is None:
            return -1.0, 0.0
        return measured['overlap'] - min(measured['largest_difference'], 0.5), measured['overlap']

    results = []
    for lens in lenses:
        best = (-2.0, start, 0.0)
        for reach, count in ((math.radians(spread), 7), (math.radians(spread) / 6, 5),
                             (math.radians(spread) / 24, 5)):
            azimuth = math.atan2(best[1].y, best[1].x)
            elevation = math.asin(max(-1.0, min(1.0, best[1].z)))
            for az in np.linspace(azimuth - reach, azimuth + reach, count):
                for el in np.linspace(elevation - reach, elevation + reach, count):
                    el = max(-1.5, min(1.5, float(el)))
                    direction = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
                    value, overlap = score(direction, lens)
                    if value > best[0]:
                        best = (value, direction, overlap)
        results.append(best + (lens,))
    value, direction, overlap, lens = max(results, key=lambda item: item[0])
    return {'view': [round(v, 4) for v in direction], 'lens': lens, 'overlap': round(overlap, 3)}


def compare(root_or_objects, reference, out_path, *, view='right', lens=None, mirror=False, box=None,
            ignore=(), drop_shadow=False, fit='auto', size=1024, overwrite=False):
    """Write `out_path` (reference | model | overlay) and return the measured match.

    `view` is the side the reference shows: `front` (looking along +Y), `back`, `right` (looking along -X),
    `left` or `top`, or the `view` and `lens` that `match_view` returned for a three-quarter photo. `mirror`
    flips the reference left to right when the object faces the other way. `box` is (left, top, right, bottom)
    in reference pixels around the object; it is required when the background is not plain. `ignore` lists
    boxes in reference pixels left out of the measurement (a watermark, a stand). `drop_shadow` removes a soft
    cast shadow from the reference outline. `fit` sets the first fit to the object's `width`, `height` or,
    with `auto`, the model's longer side.

    With a plain background the result holds `overlap` (shared share of the two silhouettes), `rows` and
    `columns` (filled size at ten stations, as fractions of the reference's longer side), `worst` (the three
    largest differences in words), `largest_difference` (the worst, scaled so the limit is 0.05) and `passed`.
    It passes when the overlap is at least 0.85, no station's filled size or edge is more than 0.05 of the
    overall size out, and no station is more than a quarter thinner or thicker than the reference there.
    For a matched view (a direction, not a name) edge positions depend on the camera: they are listed in
    `shifts` and do not count.
    Without a plain background, `passed` is None and the comparison is by eye.
    """
    if fit not in ('auto', 'width', 'height'):
        raise ValueError('Unknown fit: ' + str(fit))
    _direction(view)
    out_path, reference = Path(out_path), Path(reference)
    if not reference.is_file():
        raise FileNotFoundError(reference)
    if out_path.exists() and not overwrite:
        raise FileExistsError('{} exists; pass overwrite=True to replace it'.format(out_path))
    objects = _meshes(root_or_objects)
    source, ref_mask, ref_box, mask_source, ignore = _load_reference(reference, mirror, box, drop_shadow, ignore)
    rl, rt, rr, rb = ref_box

    model = _render_model(objects, view, size, lens)
    model_mask = model[..., 3] > 0.5
    ml, mt, mr, mb = _box(model_mask)
    height, width = model_mask.shape
    axis = fit if fit != 'auto' else ('width' if mr - ml >= mb - mt else 'height')
    scale, placed_box, _ = _fit(model_mask, ref_mask, ref_box, axis)

    sx, sy, inside = _sample(model_mask.shape, source.shape, ref_box, placed_box, scale)
    white = np.ones((height, width, 3), dtype=np.float32)
    placed = np.where(inside[..., None], source[sy, sx, :3], white)
    placed_mask = (ref_mask[sy, sx] & inside) if ref_mask is not None else None
    valid = np.ones((height, width), dtype=bool)
    for left, top, right, bottom in ignore:
        valid &= ~((sx >= left) & (sx < right) & (sy >= top) & (sy < bottom) & inside)

    alpha = model[..., 3:4]
    clay = model[..., :3] * alpha + white * (1 - alpha)
    overlay = placed * 0.45 + white * 0.55
    if placed_mask is not None:
        for only, colour in ((model_mask & ~placed_mask & valid, RED), (placed_mask & ~model_mask & valid, BLUE)):
            overlay[only] = overlay[only] * 0.65 + colour * 0.35
        overlay[_outline(placed_mask)] = BLUE
    overlay[_outline(model_mask)] = RED
    gap = np.ones((height, 12, 3), dtype=np.float32)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _write(np.concatenate([placed, gap, clay, gap, overlay], axis=1), out_path)

    model_aspect = (mr - ml) / (mb - mt)
    reference_aspect = (rr - rl) / (rb - rt)
    result = {'path': str(out_path), 'view': view if isinstance(view, str) else [round(float(v), 4) for v in view],
              'lens': lens, 'fit': axis, 'mask': mask_source, 'reference_box_px': [rl, rt, rr, rb],
              'model_aspect': round(model_aspect, 3), 'reference_aspect': round(reference_aspect, 3),
              'aspect_difference': round(model_aspect / reference_aspect - 1, 3), 'passed': None}
    measured = _measure(model_mask, placed_mask, valid, isinstance(view, str)) if placed_mask is not None else None
    if measured:
        result.update(measured)
    if isinstance(root_or_objects, bpy.types.Object):
        _record(root_or_objects, reference, result, objects)
    return result


def _record(root, reference, result, objects):
    """Keep each round's figures on the root as `marso_comparisons`, so a later check can read the history."""
    try:
        records = json.loads(root.get(RECORD, '{}'))
    except (TypeError, ValueError):
        records = {}
    corners = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    scale = bpy.context.scene.unit_settings.scale_length
    worst = result.get('worst') or []
    rounds = records.setdefault(reference.name, [])
    rounds.append({'passed': result['passed'], 'overlap': result.get('overlap'),
                   'largest_difference': result.get('largest_difference'), 'worst': worst[:1],
                   'matched': not isinstance(result['view'], str),
                   'relative': any(str(w).endswith('of the reference there') for w in worst),
                   'size': [round((max(c[i] for c in corners) - min(c[i] for c in corners)) * scale, 5)
                            for i in range(3)]})
    del rounds[:-8]
    root[RECORD] = json.dumps(records)
