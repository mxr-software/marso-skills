"""Regression: repeated surfaces can have valid normals but conflicting upload UVs.

Run with Blender --background --factory-startup --python this_file.py.
Uses synthetic geometry only; no add-on, service or user asset is required.
"""
import importlib.util
import math
from pathlib import Path
import tempfile

import bpy
from mathutils import Vector

if not bpy.app.background:
    raise RuntimeError('Run only in a disposable background Blender process')

path = Path(__file__).resolve().parents[2] / 'skills/blender/marso-blender-texture/scripts/audit_uv.py'
spec = importlib.util.spec_from_file_location('audit_uv', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

bpy.ops.wm.read_factory_settings(use_empty=True)
mesh = bpy.data.meshes.new('master')
mesh.from_pydata([(0,0,0),(1,0,0),(0,1,0)], [], [(0,1,2)])
layer = mesh.uv_layers.new(name='GenerationUV')
coords = [(.1,.1),(.3,.1),(.1,.3)]
for loop, uv in zip(layer.data, coords):
    loop.uv = uv
parts = []
for i in range(4):
    obj = bpy.data.objects.new('part_%d' % i, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location.x = i * 2
    if i % 2:
        obj.rotation_euler.y = math.pi
    parts.append(obj)
bpy.context.view_layer.update()

# Every source/master passes alone; opposite-facing instances are otherwise valid.
assert all(module.audit_uv([obj])['passed'] for obj in parts)
normals = [(obj.matrix_world.to_3x3().inverted().transposed() @ mesh.polygons[0].normal).normalized()
           for obj in parts]
assert normals[0].dot(normals[1]) < -.999
assert all(obj.matrix_world.determinant() > 0 for obj in parts)
report = module.audit_uv(parts)
assert not report['passed'] and report['overlap_pairs'] == 6
assert [tuple(loop.uv) for loop in layer.data] == [tuple(Vector(c)) for c in coords]
print('PASS linked repeated parts: each alone passes; complete target fails')

# Making data single-user does not repair already stacked coordinates.
for obj in parts:
    obj.data = obj.data.copy()
assert len({obj.data.as_pointer() for obj in parts}) == 4
assert module.audit_uv(parts)['overlap_pairs'] == 6
print('PASS independent mesh data: existing UV collisions remain detectable')

# Joining preserves the conflict within one mesh, even with no negative transform.
for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
joined = bpy.context.object
assert len(joined.data.polygons) == 4
assert module.audit_uv([joined])['overlap_pairs'] == 6
print('PASS joined upload: cross-component UV collisions are not ignored')

# Keep a real texture binding so glTF exports the UV attribute.
mat = bpy.data.materials.new('synthetic_colour')
mat.use_nodes = True
image = bpy.data.images.new('synthetic_colour', width=8, height=8)
tex = mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = image
mat.node_tree.links.new(tex.outputs['Color'], mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
joined.data.materials.clear(); joined.data.materials.append(mat)
with tempfile.TemporaryDirectory(prefix='marso-uv-regression-') as temp:
    filepath = str(Path(temp) / 'repeated.glb')
    bpy.ops.export_scene.gltf(filepath=filepath, export_format='GLB', use_selection=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=filepath)
    imported = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    assert len(imported) == 1
    report = module.audit_uv(imported)
    assert not report['passed'] and report['overlap_pairs'] == 6
    print('PASS real GLB round trip: overlap survives export and is rejected')

    # Positive control: allocate unique tiles within 0-1 on the synthetic target.
    target = imported[0]
    layer = target.data.uv_layers.active
    for i, polygon in enumerate(target.data.polygons):
        offset = Vector((.5 * (i % 2), .5 * (i // 2)))
        for loop_index in polygon.loop_indices:
            layer.data[loop_index].uv += offset
    report = module.audit_uv([target])
    assert report['passed'] and report['overlap_pairs'] == 0
    print('PASS unique combined atlas control')

print('PASS all repeated UV regressions; no cloud execution')
