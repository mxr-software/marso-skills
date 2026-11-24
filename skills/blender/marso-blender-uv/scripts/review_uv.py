"""Checker, UV layout and stretch-heatmap review images for an asset's shared atlas, inside Blender.

`review(root, out_dir)` writes `checker.png` and `stretch.png` (two opposite oblique Workbench views),
`uv.png` (every part's charts in the 0-1 tile, one tint per part) and `uv-metrics.json` (the `uv_atlas.report`
result). All images use the evaluated meshes. Scene objects, materials and render settings are restored.
"""

from contextlib import contextmanager
import colorsys
import json
import math
from pathlib import Path
import sys
import tempfile

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uv_atlas import UV, asset_meshes, face_metrics, report as atlas_report  # noqa: E402

VIEWS = ((1.0, -1.2, 0.7), (-1.0, 1.2, 0.45))
OUTPUTS = ('checker.png', 'uv.png', 'stretch.png', 'uv-metrics.json')
PATCH = 'worst-patch.png'
STRETCH_SCALE = ((1.0, (0.10, 0.55, 0.20)), (1.5, (0.95, 0.85, 0.15)), (2.5, (0.95, 0.45, 0.05)),
                 (4.0, (0.80, 0.05, 0.05)))
INVALID = (0.85, 0.0, 0.85)


def stretch_colour(ratio):
    """Green at 1 (undistorted), yellow at 1.5, orange at 2.5, red from 4; magenta for broken UVs."""
    ratio = np.asarray(ratio, dtype=float)
    colours = np.empty(ratio.shape + (3,))
    colours[:] = INVALID
    finite = np.isfinite(ratio)
    stops = np.array([s for s, _ in STRETCH_SCALE])
    palette = np.array([c for _, c in STRETCH_SCALE])
    clipped = np.clip(ratio[finite], stops[0], stops[-1])
    for channel in range(3):
        colours[finite, channel] = np.interp(clipped, stops, palette[:, channel])
    return colours


def _bounds(objects):
    corners = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    low = Vector(min(c[i] for c in corners) for i in range(3))
    high = Vector(max(c[i] for c in corners) for i in range(3))
    return (low + high) / 2, max((high - low).length / 2, 0.01), high - low


@contextmanager
def _studio(keep, size):
    """Workbench at `size` pixels with only `keep` rendered; restores everything afterwards."""
    scene = bpy.context.scene
    shading = scene.display.shading
    saved = {'engine': scene.render.engine, 'x': scene.render.resolution_x, 'y': scene.render.resolution_y,
             'pct': scene.render.resolution_percentage, 'path': scene.render.filepath,
             'format': scene.render.image_settings.file_format, 'transparent': scene.render.film_transparent,
             'view': scene.view_settings.view_transform, 'look': scene.view_settings.look,
             'light': shading.light, 'color_type': shading.color_type, 'camera': scene.camera,
             'world': scene.world, 'override': bpy.context.view_layer.material_override}
    names = {o.name for o in keep}
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
            if o.name not in names:
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
        scene.camera, scene.world = saved['camera'], saved['world']
        bpy.context.view_layer.material_override = saved['override']
        bpy.data.worlds.remove(world)


def _render_views(framing, path, views=None, near=None):
    """`near` clips everything further than that in front of the framed point, so a part standing over
    the worst patch does not hide it."""
    with tempfile.TemporaryDirectory() as scratch:
        _render_tiles(framing, path, Path(scratch), views or VIEWS, near)


def _render_tiles(framing, path, scratch, views=VIEWS, near=None):
    scene = bpy.context.scene
    center, radius = framing[:2]
    tiles = []
    for index, direction in enumerate(views):
        data = bpy.data.cameras.new('MarsoReviewCamera')
        data.lens, data.sensor_width = 50, 36
        cam = bpy.data.objects.new('MarsoReviewCamera', data)
        scene.collection.objects.link(cam)
        distance = radius / math.sin(math.radians(18)) * 1.1
        cam.location = center + Vector(direction).normalized() * distance
        cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
        data.clip_start = distance / 1000 if near is None else max(distance - near, distance / 1000)
        data.clip_end = distance * 10
        scene.camera = cam
        tile = str(scratch / '{}.view{}.png'.format(path.stem, index))
        scene.render.filepath = tile
        try:
            bpy.ops.render.render(write_still=True)
            tiles.append(_read_png(tile))
        finally:
            bpy.data.objects.remove(cam)
            bpy.data.cameras.remove(data)
            Path(tile).unlink(missing_ok=True)
    _write_png(np.concatenate(tiles, axis=1), path)


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


def _copies(objects):
    """Temporary linked objects holding each evaluated mesh, placed like the originals."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    made = []
    for obj in objects:
        mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
        copy = bpy.data.objects.new('MarsoReviewCopy', mesh)
        copy.matrix_world = obj.matrix_world.copy()
        bpy.context.scene.collection.objects.link(copy)
        made.append((obj, copy))
    return made


def _remove(copies):
    for _, copy in copies:
        mesh = copy.data
        bpy.data.objects.remove(copy)
        bpy.data.meshes.remove(mesh)


def checker_image(checks, size=2048):
    """Plain black and white checker with `checks` squares along each side."""
    cells = (np.arange(size) * checks // size) % 2
    value = np.where((cells[:, None] + cells[None, :]) % 2, 0.92, 0.06).astype(np.float32)
    rgba = np.ones((size, size, 4), dtype=np.float32)
    rgba[..., :3] = value[..., None]
    image = bpy.data.images.new('MarsoReviewChecker', size, size, alpha=False)
    image.pixels.foreach_set(rgba.ravel())
    image.pack()
    return image


def _checker_material(image, uv_name):
    material = bpy.data.materials.new('MarsoReviewChecker')
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = image
    texture.interpolation = 'Closest'
    mapping = nodes.new('ShaderNodeUVMap')
    mapping.uv_map = uv_name
    links.new(mapping.outputs['UV'], texture.inputs['Vector'])
    links.new(texture.outputs['Color'], shader.inputs['Base Color'])
    nodes.active = texture
    return material


def _checks_per_tile(objects, metrics, resolution):
    """Checks per 0-1 tile so one square spans about 1/24 of the asset's largest dimension."""
    largest = max(_bounds(objects)[2]) * bpy.context.scene.unit_settings.scale_length
    densities = sorted(p['px_per_m'] for p in metrics['parts'].values() if p['px_per_m'] > 0)
    if not densities or largest <= 0:
        return 32
    uv_per_metre = densities[len(densities) // 2] / resolution
    return int(np.clip(round(1 / (largest / 24 * uv_per_metre)), 8, 256))


def _stretch_attribute(mesh, uv_name, obj):
    metrics = face_metrics(obj, mesh, uv_name)
    colours = np.empty((len(mesh.polygons), 3))
    colours[:] = INVALID
    if metrics is not None:
        worst = np.full(len(mesh.polygons), 1.0)
        np.maximum.at(worst, metrics['polygon'], metrics['anisotropy'])
        colours = stretch_colour(worst)
    starts = np.empty(len(mesh.polygons), dtype=np.int64)
    sizes = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get('loop_start', starts)
    mesh.polygons.foreach_get('loop_total', sizes)
    corner = np.ones((len(mesh.loops), 4), dtype=np.float32)
    for start, total, colour in zip(starts, sizes, colours):
        corner[start:start + total, :3] = colour
    attribute = mesh.color_attributes.new('MarsoStretch', 'FLOAT_COLOR', 'CORNER')
    attribute.data.foreach_set('color', corner.ravel())
    mesh.color_attributes.active_color = attribute


def uv_layout(objects, path, *, uv_name=UV, size=1024):
    """Rasterise every part's charts into one square image: tinted fill, dark polygon edges, tile border."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    canvas = np.ones((size, size, 3), dtype=np.float32)
    lines = np.linspace(0, size - 1, 9).astype(int)
    canvas[lines, :] = canvas[:, lines] = 0.85
    rng = np.random.default_rng(7)
    edges = []
    for index, obj in enumerate(objects):
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            layer = mesh.uv_layers.get(uv_name)
            if layer is None:
                continue
            uv = np.empty(len(mesh.loops) * 2)
            layer.data.foreach_get('uv', uv)
            uv = uv.reshape(-1, 2) * (size - 1)
            mesh.calc_loop_triangles()
            loops = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
            mesh.loop_triangles.foreach_get('loops', loops)
            tri = uv[loops.reshape(-1, 3)]
            area = np.abs(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])) * 0.5
            counts = np.minimum(np.ceil(area * 6).astype(np.int64) + 3, 600000)
            owner = np.repeat(np.arange(len(tri)), counts)
            r1, r2 = np.sqrt(rng.random(len(owner))), rng.random(len(owner))
            points = ((1 - r1)[:, None] * tri[owner, 0] + (r1 * (1 - r2))[:, None] * tri[owner, 1]
                      + (r1 * r2)[:, None] * tri[owner, 2])
            hue = (index * 0.618034) % 1.0
            tint = np.array(colorsys.hsv_to_rgb(hue, 0.35, 0.95), dtype=np.float32)
            _plot(canvas, points, tint, size)
            starts = np.empty(len(mesh.polygons), dtype=np.int64)
            sizes = np.empty(len(mesh.polygons), dtype=np.int64)
            mesh.polygons.foreach_get('loop_start', starts)
            mesh.polygons.foreach_get('loop_total', sizes)
            following = np.arange(len(mesh.loops)) + 1
            following[starts + sizes - 1] = starts
            edges.append((uv, following))
        finally:
            evaluated.to_mesh_clear()
    for uv, following in edges:
        a, b = uv, uv[following]
        steps = np.minimum(np.ceil(np.linalg.norm(b - a, axis=1)).astype(np.int64) + 1, 4 * size)
        owner = np.repeat(np.arange(len(a)), steps)
        t = (np.arange(len(owner)) - np.repeat(np.cumsum(steps) - steps, steps)) / np.repeat(steps, steps)
        _plot(canvas, a[owner] + (b[owner] - a[owner]) * t[:, None], np.array([0.1, 0.1, 0.12]), size)
    canvas[[0, -1], :] = canvas[:, [0, -1]] = 0.0
    rgba = np.ones((size, size, 4), dtype=np.float32)
    rgba[..., :3] = canvas
    _write_png(rgba, path)


def _plot(canvas, points, colour, size):
    pixels = np.round(points).astype(np.int64)
    keep = (pixels >= 0).all(axis=1) & (pixels < size).all(axis=1)
    canvas[pixels[keep, 1], pixels[keep, 0]] = colour


def review(root_or_objects, out_dir, *, uv_name=UV, resolution=None, padding_px=None, size=1024,
           addon_module=None, limits=None, overwrite=False):
    """Write checker.png, uv.png, stretch.png and uv-metrics.json; returns their paths and the report.

    Also writes worst-patch.png: the checker seen straight on at the report's `worst_patch`, so stretch
    there is not confused with perspective. Resolution and padding default to the recorded pack."""
    objects = asset_meshes(root_or_objects)
    if size < 128:
        raise ValueError('Use a render size of at least 128 pixels')
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    existing = [name for name in OUTPUTS + (PATCH,) if (out / name).exists()]
    if existing and not overwrite:
        raise FileExistsError('Already present (pass overwrite=True to replace): ' + ', '.join(existing))
    metrics = atlas_report(objects, uv_name=uv_name, resolution=resolution, padding_px=padding_px,
                           addon_module=addon_module, limits=limits)
    resolution = metrics['resolution']
    framing = _bounds(objects)
    patch = metrics.get('worst_patch')
    shading = bpy.context.scene.display.shading
    copies = _copies(objects)
    image = material = None
    try:
        with _studio([c for _, c in copies], size):
            image = checker_image(_checks_per_tile(objects, metrics, resolution))
            material = _checker_material(image, uv_name)
            for _, copy in copies:
                copy.data.materials.clear()
                copy.data.materials.append(material)
                if copy.data.uv_layers.get(uv_name):
                    copy.data.uv_layers.active = copy.data.uv_layers[uv_name]
            shading.color_type = 'TEXTURE'
            _render_views(framing, out / 'checker.png')
            if patch:
                _render_views((Vector(patch['centre']), framing[1] / 5), out / PATCH,
                              views=(Vector(patch['normal']),), near=framing[1] / 5)
            for obj, copy in copies:
                _stretch_attribute(copy.data, uv_name, copy)
            shading.color_type = 'VERTEX'
            _render_views(framing, out / 'stretch.png')
    finally:
        _remove(copies)
        if material is not None:
            bpy.data.materials.remove(material)
        if image is not None:
            bpy.data.images.remove(image)
    uv_layout(objects, out / 'uv.png', uv_name=uv_name, size=size)
    (out / 'uv-metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    paths = {name.split('.')[0].replace('-', '_'): str(out / name) for name in OUTPUTS}
    if patch:
        paths['worst_patch'] = str(out / PATCH)
    return paths | {'report': metrics}
