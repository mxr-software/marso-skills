"""Run with Blender --background --factory-startup --python this_file.py."""
import importlib.util
from pathlib import Path

import bpy

if not bpy.app.background:
    raise RuntimeError('Run only in a disposable background Blender process')

path = Path(__file__).resolve().parents[2] / 'skills/blender/marso-blender-texture/scripts/measure_uv_quality.py'
spec = importlib.util.spec_from_file_location('measure_uv_quality', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def quad(name, coords):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    layer = mesh.uv_layers.new()
    for loop, uv in zip(layer.data, coords):
        loop.uv = uv
    return obj


a = quad('square', [(.1,.1), (.3,.1), (.3,.3), (.1,.3)])
b = quad('stretch', [(.4,.1), (.8,.1), (.8,.2), (.4,.2)])
report = module.measure_uv_quality([a], resolution=100, padding_px=5)
assert report['islands'] == 1 and report['padding_passed']
assert abs(report['area_weighted_anisotropy_p95'] - 1) < 1e-5
report = module.measure_uv_quality([b], resolution=100, padding_px=5)
assert abs(report['area_weighted_anisotropy_p95'] - 4) < 1e-4
# Equal UV areas and density, different directional stretch.
assert abs(module.measure_uv_quality([a])['area_weighted_density_px_per_m']['50'] -
           module.measure_uv_quality([b])['area_weighted_density_px_per_m']['50']) < .001
c = quad('too_close', [(.31,.1), (.51,.1), (.51,.3), (.31,.3)])
report = module.measure_uv_quality([a,c], resolution=100, padding_px=5)
assert report['islands'] == 2 and not report['padding_passed'] and report['padding_violation_pairs'] > 0
assert module.measure_uv_quality([a,c], resolution=100, padding_px=.5)['padding_passed']
a.scale = (2,2,2)
bpy.context.view_layer.update()
assert abs(module.measure_uv_quality([a], resolution=100)['area_weighted_density_px_per_m']['50'] - 10) < 1e-5
# Shared UV edge is one island, not an inter-island padding failure.
mesh = bpy.data.meshes.new('connected')
mesh.from_pydata([(0,0,0),(1,0,0),(1,1,0),(0,1,0)], [], [(0,1,2),(0,2,3)])
obj = bpy.data.objects.new('connected', mesh); bpy.context.scene.collection.objects.link(obj)
uv = mesh.uv_layers.new()
coords = [(.1,.1),(.4,.1),(.4,.4),(.1,.4)]
for loop in mesh.loops: uv.data[loop.index].uv = coords[loop.vertex_index]
assert module.measure_uv_quality([obj], resolution=100, padding_px=5)['islands'] == 1
assert module.measure_uv_quality([obj], resolution=100, padding_px=5)['padding_passed']
border = quad('border',[(.001,.1),(.2,.1),(.2,.3),(.001,.3)])
assert not module.measure_uv_quality([border],resolution=100,padding_px=5)['padding_passed']
collapsed = quad('collapsed',[(.2,.2)]*4)
assert not module.measure_uv_quality([collapsed])['padding_passed']
assert module.measure_uv_quality([collapsed])['invalid_samples'] > 0
try:
    module.measure_uv_quality([obj], padding_px=-1)
    raise AssertionError('negative padding accepted')
except ValueError:
    pass

# Large chart area can conceal a one-pixel strip at a lower resolution.
thin = quad('thin_strip', [(.1,.1),(.9,.1),(.9,.101),(.1,.101)])
report = module.measure_uv_quality([thin], resolution=1024, padding_px=4)
chart = report['charts'][0]
assert chart['area_px2'] > 800 and .99 < chart['bbox_height_px'] < 1.05
assert .99 < chart['area_perimeter_width_proxy_px'] < 1.05
assert report['padding_passed']  # Spacing does not certify detail sampling.

# glTF normal splits: duplicated vertex IDs, unchanged positions and UVs.
mesh = bpy.data.meshes.new('normal_split')
mesh.from_pydata([(0,0,0),(1,0,0),(1,1,0),(0,0,0),(1,1,0),(0,1,0)], [], [(0,1,2),(3,4,5)])
split = bpy.data.objects.new('normal_split', mesh)
bpy.context.scene.collection.objects.link(split)
uv = mesh.uv_layers.new()
for loop, coord in zip(uv.data, [(.1,.1),(.4,.1),(.4,.4),(.1,.1),(.4,.4),(.1,.4)]):
    loop.uv = coord
before = ([tuple(v.co) for v in mesh.vertices], [tuple(v.uv) for v in uv.data])
raw = module.measure_uv_quality([split], resolution=100, padding_px=5)
diagnostic = module.measure_uv_quality([split], resolution=100, padding_px=5, match_split_vertices=True)
assert raw['islands'] == 2 and not raw['padding_passed']
assert diagnostic['islands'] == 1 and diagnostic['padding_passed'] and diagnostic['matched_split_edges'] == 1
assert diagnostic['connectivity'] == 'exact_position_uv_diagnostic'
assert before == ([tuple(v.co) for v in mesh.vertices], [tuple(v.uv) for v in uv.data])
# A real UV seam or even a tiny positional difference must not be bridged.
for loop in list(uv.data)[3:]:
    loop.uv.x += .001
report = module.measure_uv_quality([split], resolution=100, padding_px=5, match_split_vertices=True)
assert report['islands'] == 2 and report['matched_split_edges'] == 0 and not report['padding_passed']
for loop, coord in zip(uv.data, before[1]):
    loop.uv = coord
for vertex in list(mesh.vertices)[3:]:
    vertex.co.z = 1e-7
assert module.measure_uv_quality([split], match_split_vertices=True)['matched_split_edges'] == 0

# Stacked duplicate faces are ambiguous, not normal-split connectivity.
mesh = bpy.data.meshes.new('duplicate_faces')
mesh.from_pydata([(0,0,0),(1,0,0),(1,1,0),(0,1,0)] * 2, [], [(0,1,2,3),(4,5,6,7)])
duplicate = bpy.data.objects.new('duplicate_faces', mesh)
bpy.context.scene.collection.objects.link(duplicate)
uv = mesh.uv_layers.new()
for loop, coord in zip(uv.data, [(.1,.1),(.4,.1),(.4,.4),(.1,.4)] * 2):
    loop.uv = coord
report = module.measure_uv_quality([duplicate], resolution=100, padding_px=5, match_split_vertices=True)
assert report['islands'] == 2 and report['ambiguous_split_edges'] == 4
assert report['matched_split_edges'] == 0 and not report['padding_passed']
assert module.measure_uv_quality([a,c], match_split_vertices=True)['islands'] == 2
print('PASS UV quality: stretch, spacing, degeneracy, scale, chart sampling, read-only split-vertex diagnostics, real seams and ambiguous duplicates')
