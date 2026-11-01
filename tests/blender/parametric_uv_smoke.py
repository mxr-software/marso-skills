"""blender -b --factory-startup --python tests/blender/parametric_uv_smoke.py"""
import math
from pathlib import Path
import sys
import traceback
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'skills/blender/marso-blender-texture/scripts'))
from parametric_uv import assign_chart
from audit_uv import audit_uv


def surface(name, closed):
    count, section, radius, tube = 32, 12, 2.0, .15
    angle = 2*math.pi if closed else 2.2
    stations = count if closed else count+1
    vertices, parameters, faces = [], [], []
    for i in range(stations):
        u = angle*i/count
        for j in range(section):
            v = 2*math.pi*j/section
            vertices.append(((radius+tube*math.cos(v))*math.cos(u),
                             (radius+tube*math.cos(v))*math.sin(u), tube*math.sin(v)))
            parameters.append((radius*u, tube*v))
    for i in range(count):
        nxt = (i+1) % stations
        for j in range(section):
            k = (j+1) % section
            faces.append((i*section+j, nxt*section+j, nxt*section+k, i*section+k))
    mesh = bpy.data.meshes.new(name);mesh.from_pydata(vertices, [], faces);mesh.update()
    obj = bpy.data.objects.new(name, mesh);bpy.context.scene.collection.objects.link(obj)
    original = [tuple(v.co) for v in mesh.vertices]
    periods = (radius*angle if closed else None, 2*math.pi*tube)
    result = assign_chart(mesh, parameters, periods=periods)
    assert result['faces'] == len(faces)
    # Normalize the single chart into a valid test tile; production shares a pack.
    uv = mesh.uv_layers['MarsoUV'].data
    scale = max(max(abs(x) for x in loop.uv) for loop in uv)
    for loop in uv:loop.uv = (.02+loop.uv.x/scale*.96, .02+loop.uv.y/scale*.96)
    audit = audit_uv([obj], uv_name='MarsoUV')
    assert audit['passed'], audit
    assert original == [tuple(v.co) for v in mesh.vertices]
    snapshot = [tuple(loop.uv) for loop in uv]
    for bad in [dict(periods=(0, None)), dict(periods=periods, flip_v=True),
                dict(periods=periods, faces=[0, 0])]:
        try:assign_chart(mesh, parameters, **bad)
        except ValueError:pass
        else:raise AssertionError('Invalid chart accepted')
        assert snapshot == [tuple(loop.uv) for loop in uv], 'Rejected write changed UVs'
    try:assign_chart(mesh, [(0, 0)]*len(vertices), uv_name='Rejected')
    except ValueError:pass
    else:raise AssertionError('Collapsed chart accepted')
    assert mesh.uv_layers.get('Rejected') is None
    for parameters_bad, periods_bad in [([(float('nan'), 0)]*len(vertices), (None, None)),
                                       (parameters, (radius*angle/count*2, None))]:
        try:assign_chart(mesh, parameters_bad, uv_name='Rejected', periods=periods_bad)
        except ValueError:pass
        else:raise AssertionError('Invalid parameters accepted')
        assert mesh.uv_layers.get('Rejected') is None
    # Explicitly reversed source parameters can be corrected as a whole chart.
    # Non-periodic positive patch tests selected-face assignment independently.
    face = mesh.polygons[0]
    subset = dict(zip(face.vertices, [(0,0), (1,0), (1,-1), (0,-1)]))
    assign_chart(mesh, subset, uv_name='Patch', faces=[0], flip_v=True)
    assert len(mesh.uv_layers['Patch'].data) == len(mesh.loops)
    print(name, 'PASSED', audit['triangles'], 'triangles; seams, winding, rollback and geometry checked')


try:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    surface('Closed wheel band', True)
    surface('Bent swept tube', False)
except Exception:
    traceback.print_exc();sys.exit(1)
