"""Single-mesh working copy, atlas validation, colour-guide bake and export inside Blender. No service calls.

The parts arrive with their shared `MarsoUV` atlas already authored; this module does not unwrap or pack.
See references/preparation-helper.md for the staged API and supported materials.
"""
from contextlib import contextmanager
from array import array
import hashlib
import importlib
import json
import math
import re
from pathlib import Path

import bpy
from mathutils import Matrix


def _module(addon_module, leaf):
    package = addon_module if isinstance(addon_module, str) else addon_module.__name__
    return importlib.import_module(package + '.core.' + leaf)


def _metre_scene():
    if abs(bpy.context.scene.unit_settings.scale_length - 1.0) > 1e-8:
        raise ValueError('Use a metre-scale working scene (scale_length=1) with physically converted geometry; changing only the unit setting is not conversion')


def _anchor(matrix):
    if abs(matrix.to_3x3().determinant()) < 1e-12:
        raise ValueError('Asset anchor has a singular transform')
    # Anchor placement/orientation is separate from scale in the asset geometry.
    return Matrix.Translation(matrix.translation) @ matrix.to_quaternion().to_matrix().to_4x4()


def addon_info(addon_module):
    """Record the actual local implementation, without enabling listeners/jobs."""
    module = _module(addon_module, 'mesh_export')
    return {'module': addon_module, 'exporter_sha256': hashlib.sha256(
        Path(module.__file__).read_bytes()).hexdigest()}


def _mesh(obj):
    if obj.type != 'MESH' or obj.mode != 'OBJECT':
        raise ValueError('Use a mesh in Object mode')
    if obj.data.users != 1 or obj.modifiers:
        raise ValueError('Use an independent evaluated working copy without modifiers')
    return obj.data


def use_uv(obj, name='MarsoUV', *, create=False):
    """Reacquire this handle AFTER every edit-mode/operator boundary."""
    mesh = _mesh(obj)
    layer = mesh.uv_layers.get(name)
    if layer is None:
        if not create:
            raise ValueError('Missing UV layer: ' + name)
        layer = mesh.uv_layers.new(name=name)
    mesh.uv_layers.active_index = list(mesh.uv_layers).index(layer)
    layer.active_render = True
    return layer


@contextmanager
def _selected(obj):
    if bpy.context.mode != 'OBJECT':
        raise ValueError('Finish the current edit operation first')
    if obj.name not in bpy.context.view_layer.objects:
        raise ValueError('Working target must belong to the current view layer')
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    hidden = obj.hide_get()
    hidden_render, hidden_viewport = obj.hide_render, obj.hide_viewport
    try:
        for other in selected:
            other.select_set(False)
        obj.hide_set(False)
        obj.hide_render = obj.hide_viewport = False
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        yield
    finally:
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        obj.select_set(False)
        obj.hide_set(hidden)
        obj.hide_render, obj.hide_viewport = hidden_render, hidden_viewport
        for other in selected:
            other.select_set(True)
        bpy.context.view_layer.objects.active = active


def working_copy(objects, *, name, addon_module, frame, uv_name='MarsoUV',
                 excluded_faces=None):
    """Copy explicit evaluated mesh occurrences; exclusions use evaluated face IDs.

    Frame is an explicit asset-to-world matrix (normally the asset root). Sources,
    instances and their materials remain unchanged. No visibility inference.
    """
    objects = list(objects)
    _metre_scene()
    exclusions = excluded_faces or {}
    if not objects or len(set(objects)) != len(objects):
        raise ValueError('Supply distinct mesh occurrences')
    if bpy.data.objects.get(name):
        raise ValueError('Target already exists; reuse it or choose a new name')
    if set(exclusions) - {o.name for o in objects}:
        raise ValueError('Exclusions refer to an object outside the target')
    frame = _anchor(frame)
    inverse = frame.inverted()  # Reject singular anchors before creating data.
    transform = _module(addon_module, 'asset_frame').transform_mesh
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    vertices, faces, normals, coords, slots, roles, smooth = [], [], [], [], [], [], []
    seams, provenance, missing_uv = set(), [], []
    for obj in objects:
        if obj.type != 'MESH' or obj.mode != 'OBJECT':
            raise ValueError('Convert non-mesh parts on a separate working copy first')
        mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(deps),
            preserve_all_data_layers=True, depsgraph=deps)
        try:
            omit = set(exclusions.get(obj.name, []))
            if any(not isinstance(i, int) or i < 0 or i >= len(mesh.polygons) for i in omit):
                raise ValueError('Invalid evaluated face exclusion: ' + obj.name)
            matrix = inverse @ obj.matrix_world
            reflected = matrix.to_3x3().determinant() < 0
            transform(mesh, matrix)
            layer = mesh.uv_layers.get(uv_name)
            if layer is None:
                missing_uv.append(obj.name)
            offset = len(vertices)
            used = sorted({i for p in mesh.polygons if p.index not in omit for i in p.vertices})
            remap = {i: offset+j for j, i in enumerate(used)}
            vertices.extend(tuple(mesh.vertices[i].co) for i in used)
            seams.update(tuple(sorted((remap[e.vertices[0]], remap[e.vertices[1]])))
                         for e in mesh.edges if e.use_seam and all(i in remap for i in e.vertices))
            start = len(faces)
            kept = []
            for poly in mesh.polygons:
                if poly.index in omit:
                    continue
                index = poly.material_index
                material = obj.material_slots[index].material if index < len(obj.material_slots) else None
                if material not in slots:
                    if material is not None:
                        _colour_source(material, uv_name, flat_only=True)
                    slots.append(material)
                roles.append(slots.index(material))
                faces.append(tuple(remap[i] for i in poly.vertices))
                smooth.append(poly.use_smooth)
                normals.extend(tuple(mesh.corner_normals[i].vector) for i in poly.loop_indices)
                # The native transform reverses polygon loops for a reflection; the packed atlas is kept as
                # authored, so a reflected part's charts stay mirrored, which the add-on's validator accepts.
                coords.extend(tuple(layer.data[i].uv) if layer else (0, 0) for i in poly.loop_indices)
                kept.append(poly.index)
            provenance.append({'source': obj.name, 'start': start, 'count': len(kept),
                               'evaluated_faces': kept, 'excluded_faces': sorted(omit),
                               'reflected_transform': reflected})
        finally:
            bpy.data.meshes.remove(mesh)
    if not faces:
        raise ValueError('No included faces')
    mesh = bpy.data.meshes.new(name)
    obj = None
    try:
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        for material in slots if slots != [None] else []:
            mesh.materials.append(material)
        for poly, role, flag in zip(mesh.polygons, roles, smooth):
            poly.material_index, poly.use_smooth = role, flag
        for edge in mesh.edges:
            edge.use_seam = tuple(sorted(edge.vertices)) in seams
        mesh.normals_split_custom_set(normals)
        layer = mesh.uv_layers.new(name=uv_name)
        layer.active_render = True
        for loop, uv in zip(layer.data, coords):
            loop.uv = uv
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.matrix_world = frame
        obj['preparation_sources'] = json.dumps(provenance)
        obj['preparation_missing_uv'] = json.dumps(missing_uv)
        return obj
    except Exception:
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)
        raise


def part_faces(obj, source_name):
    """Select by recorded source identity, then refine by geometry if needed."""
    for part in json.loads(obj['preparation_sources']):
        if part['source'] == source_name:
            return list(range(part['start'], part['start'] + part['count']))
    raise ValueError('Unknown source part: ' + source_name)


def validate_atlas(obj, *, addon_module, uv_name='MarsoUV'):
    """One shared generation domain, even while source material slots differ."""
    mesh = _mesh(obj)
    uv = use_uv(obj, uv_name)
    missing = json.loads(obj.get('preparation_missing_uv', '[]'))
    if missing:
        raise ValueError('Parts without ' + uv_name + ': ' + ', '.join(missing))
    mesh.calc_loop_triangles()
    covered = 0.0

    def triangles():
        nonlocal covered
        for tri in mesh.loop_triangles:
            if not math.isfinite(tri.area) or tri.area <= 0:
                raise ValueError('Degenerate geometry: ' + str(face_source(obj, tri.polygon_index)))
            points = tuple(tuple(uv.data[i].uv) for i in tri.loops)
            a, b, c = points
            covered += abs((b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])) * 0.5
            yield 0, tri.polygon_index, points

    conflict = _module(addon_module, 'uv_validation').first_conflict(triangles())
    if conflict:
        match = re.search(r'faces? (\d+)(?: and (\d+))?', conflict)
        owners = [face_source(obj, int(i)) for i in match.groups() if i] if match else []
        raise ValueError('Shared atlas: ' + conflict + ('; sources=' + json.dumps(owners) if owners else ''))
    report = {'uv_valid': True, 'triangles': len(mesh.loop_triangles), 'occupied_fraction': covered}
    if covered < 0.25:
        report['packing_advice'] = 'Over three quarters of this tile is empty. Check principal chart size and long perimeter strips before submitting.'
    return report


def face_source(obj, face):
    """Map an unchanged working polygon back to the evaluated source occurrence."""
    if face < 0 or face >= len(obj.data.polygons):
        raise ValueError('Face outside working mesh')
    for part in json.loads(obj.get('preparation_sources', '[]')):
        local = face-part['start']
        if 0 <= local < part['count']:
            return {'object': part['source'], 'evaluated_face': part['evaluated_faces'][local], 'working_face': face}
    return {'object': obj.name, 'working_face': face}


def _colour_source(material, uv_name, *, flat_only=False):
    if material is None or not material.use_nodes:
        raise ValueError('Assign a node-based Principled material to every included face')
    outputs = [n for n in material.node_tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output]
    if len(outputs) != 1 or not outputs[0].inputs['Surface'].is_linked:
        raise ValueError('Material needs one active connected surface output')
    shader = outputs[0].inputs['Surface'].links[0].from_node
    if shader.type != 'BSDF_PRINCIPLED':
        raise ValueError('Guide bake supports a directly connected Principled shader')
    if flat_only and any(shader.inputs[key].is_linked or shader.inputs[key].default_value != value
                         for key, value in [('Alpha', 1), ('Transmission Weight', 0)]):
        raise ValueError('Resolve transparent parts explicitly before opaque guide preparation')
    colour = shader.inputs['Base Color']
    if colour.is_linked:
        if flat_only:
            raise ValueError('Working-copy guide supports flat Base Color only; preserve/bake existing textured materials separately')
        node = colour.links[0].from_node
        if node.type != 'TEX_IMAGE' or not node.image:
            raise ValueError('Bake procedural/complex colour before joining; guide supports flat colour or UV images')
        if node.projection != 'FLAT':
            raise ValueError('Export supports flat UV image projection')
        vector = node.inputs['Vector']
        if vector.is_linked:
            source = vector.links[0]
            if not ((source.from_node.type == 'UVMAP' and source.from_node.uv_map in ('', uv_name)) or
                    (source.from_node.type == 'TEX_COORD' and source.from_socket.name == 'UV')):
                raise ValueError('Base-colour image must use the selected UV layer')
    return outputs[0], colour


def _layout_hash(obj, uv_name):
    mesh = obj.data
    digest = hashlib.sha256()
    for collection, field, code, width in [(mesh.vertices, 'co', 'f', 3),
            (mesh.loops, 'vertex_index', 'i', 1), (mesh.polygons, 'loop_total', 'i', 1),
            (mesh.uv_layers[uv_name].data, 'uv', 'f', 2)]:
        values = array(code, [0]) * (len(collection)*width)
        collection.foreach_get(field, values)
        digest.update(str(len(values)).encode())
        digest.update(values.tobytes())
    return digest.hexdigest()


def bake_guide(obj, path, *, addon_module, uv_name='MarsoUV', resolution=2048, margin_px=8):
    """Lighting-free base-colour bake on private material copies; replace only on success."""
    mesh = _mesh(obj)
    path = Path(path)
    if path.exists():
        raise FileExistsError('Choose a new guide filename to retain the previous checkpoint')
    if resolution not in (1024, 2048, 4096) or not 0 <= margin_px < resolution/4:
        raise ValueError('Use a supported guide size and valid bake margin')
    validate_atlas(obj, addon_module=addon_module, uv_name=uv_name)
    originals = [slot.material for slot in obj.material_slots]
    if not originals or any(slot.link != 'DATA' for slot in obj.material_slots):
        raise ValueError('Use data-linked materials on an independent working copy')
    for material in originals:
        _colour_source(material, uv_name, flat_only=True)
    roles = [p.material_index for p in mesh.polygons]
    scene = bpy.context.scene
    engine, samples = scene.render.engine, scene.cycles.samples
    bake = scene.render.bake
    settings = {key: getattr(bake, key) for key in ('margin', 'use_selected_to_active', 'use_clear', 'target')}
    copies, image, guide = [], None, None
    succeeded = False
    try:
        image = bpy.data.images.new(obj.name + ' colour guide', width=resolution, height=resolution, alpha=False)
        for index, material in enumerate(originals):
            cp = material.copy()
            copies.append(cp)
            output, colour = _colour_source(cp, uv_name)
            nodes, links = cp.node_tree.nodes, cp.node_tree.links
            emit = nodes.new('ShaderNodeEmission')
            if colour.is_linked:
                links.new(colour.links[0].from_socket, emit.inputs['Color'])
            else:
                emit.inputs['Color'].default_value = colour.default_value
            links.new(emit.outputs[0], output.inputs['Surface'])
            tex = nodes.new('ShaderNodeTexImage')
            tex.image = image
            nodes.active = tex
            mesh.materials[index] = cp
        scene.render.engine, scene.cycles.samples = 'CYCLES', 1
        bake.margin, bake.use_selected_to_active, bake.use_clear, bake.target = margin_px, False, True, 'IMAGE_TEXTURES'
        with _selected(obj):
            bpy.ops.object.bake(type='EMIT', uv_layer=uv_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        image.filepath_raw, image.file_format = str(path), 'PNG'
        image.save()
        _ = image.pixels[0]  # Confirm pixel storage before packing; loading may be lazy.
        image.pack()
        guide = bpy.data.materials.new(obj.name + ' | colour guide')
        guide.use_nodes = True
        nodes, links = guide.node_tree.nodes, guide.node_tree.links
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = image
        uv = nodes.new('ShaderNodeUVMap')
        uv.uv_map = uv_name
        links.new(uv.outputs['UV'], tex.inputs['Vector'])
        links.new(tex.outputs['Color'], nodes.get('Principled BSDF').inputs['Base Color'])
        mesh.materials.clear()
        mesh.materials.append(guide)
        obj['preparation_guide_revision'] = _layout_hash(obj, uv_name)
        succeeded = True
        return {'path': str(path), 'resolution': resolution, 'material': guide.name}
    finally:
        if not succeeded:
            mesh.materials.clear()
            for material in originals:
                mesh.materials.append(material)
            for poly, role in zip(mesh.polygons, roles):
                poly.material_index = role
            if guide:
                bpy.data.materials.remove(guide)
        for material in copies:
            bpy.data.materials.remove(material)
        if not succeeded and image and image.users == 0:
            bpy.data.images.remove(image)
        scene.render.engine, scene.cycles.samples = engine, samples
        for key, value in settings.items():
            setattr(bake, key, value)


def export_glb(obj, path, *, addon_module, uv_name='MarsoUV'):
    """Native export in the working target's anchor frame; never submit to Marso."""
    path = Path(path)
    if path.exists():
        raise FileExistsError('Choose a new export filename')
    _metre_scene()
    use_uv(obj, uv_name)
    if obj.get('preparation_guide_revision') and obj['preparation_guide_revision'] != _layout_hash(obj, uv_name):
        raise ValueError('Geometry/UVs changed after baking; return to the pre-bake checkpoint and rebake')
    if len(obj.material_slots) != 1:
        raise ValueError('Bake one shared colour guide before this export')
    _, colour = _colour_source(obj.material_slots[0].material, uv_name)
    if not colour.is_linked:
        raise ValueError('Export requires a connected base-colour texture')
    frame = _anchor(obj.matrix_world)
    data = _module(addon_module, 'mesh_export').export_object_to_glb_bytes(
        bpy.context, obj, frame=frame, validate_uvs=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)
    return {'path': str(path), 'bytes': len(data)}


def uv_outline(obj, path, *, uv_name='MarsoUV', size=1024):
    """Graphics-context-free SVG of the chosen target only; no hidden source meshes."""
    uv = use_uv(obj, uv_name)
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">',
             '<rect width="100%" height="100%" fill="#eee"/>',
             '<g fill="none" stroke="#234" stroke-width="0.5">']
    for poly in obj.data.polygons:
        points = ' '.join(f'{uv.data[i].uv.x*size:.3f},{(1-uv.data[i].uv.y)*size:.3f}' for i in poly.loop_indices)
        lines.append(f'<polygon points="{points}"/>')
    lines.append('</g></svg>')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write('\n'.join(lines))
