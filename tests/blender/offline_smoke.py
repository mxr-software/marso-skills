"""Run in a disposable background Blender process; never touches cloud services."""

import argparse
import importlib
import importlib.util
import math
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True

import bpy
from mathutils import Matrix


def empty(name, parent=None, location=(0, 0, 0)):
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    return obj


def expect_value_error(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("Expected invalid input or fit to be rejected")


def max_difference(a, b):
    return max(abs(a[i][j] - b[i][j]) for i in range(4) for j in range(4))


def placement_checks(repo):
    path = repo / 'skills/blender/marso-blender-compose/scripts/snap_component.py'
    spec = importlib.util.spec_from_file_location('snap_component', str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    snap = module.snap_component
    base = empty('base')
    base.matrix_world = Matrix.Translation((2, 3, 1)) @ Matrix.Rotation(0.7, 4, 'Z')
    target = empty('target', base, (1, 0, 0))
    target.rotation_euler.y = math.pi / 2
    previous = target
    for index in range(8):
        root = empty('component_%d' % index)
        left = empty('left_%d' % index, root)
        left.rotation_euler.y = -math.pi / 2
        right = empty('right_%d' % index, root, (1, 0, 0))
        right.rotation_euler.y = math.pi / 2
        result = snap(root, left, previous)
        assert result['position_error'] < 1e-4
        previous = right
    bpy.context.view_layer.update()
    expected = base.matrix_world @ Matrix.Translation((9, 0, 0))
    assert (previous.matrix_world.translation - expected.translation).length < 1e-4
    twist_root = empty('twist_root')
    source = empty('twist_source', twist_root, (0.2, 0.3, 0.1))
    source.rotation_euler = (0.3, 0.2, 0.1)
    snap(twist_root, source, target, twist_degrees=90)
    want = target.matrix_world @ Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Rotation(math.pi, 4, 'Y')
    assert max_difference(source.matrix_world, want) < 1e-5
    expect_value_error(lambda: snap(twist_root, source, source))
    expect_value_error(lambda: snap(twist_root, target, source))
    for scale in ((2, 1, 1), (-1, 1, 1)):
        twist_root.scale = scale
        expect_value_error(lambda: snap(twist_root, source, target))
    twist_root.scale = (1, 1, 1)
    twist_root.location = (10, 10, 10)
    constraint = twist_root.constraints.new('LIMIT_LOCATION')
    constraint.use_min_x = constraint.use_max_x = True
    constraint.min_x = constraint.max_x = 10
    bpy.context.view_layer.update()
    old = twist_root.matrix_world.copy()
    expect_value_error(lambda: snap(twist_root, source, target))
    assert max_difference(twist_root.matrix_world, old) < 1e-5
    print('PASS placement: rotated chain, twist, hierarchy, scale/reflection, rollback')


def face_area(mesh, layer, polygon):
    points = [mesh.uv_layers[layer].data[i].uv.copy() for i in polygon.loop_indices]
    return abs(sum(a.x * b.y - b.x * a.y for a, b in zip(points, points[1:] + points[:1]))) / 2


def preparation_checks(addon_root):
    # Namespace-only packages avoid the extension __init__ and all registration timers.
    for name, directory in (('_skill_probe', addon_root / 'marso'),
                            ('_skill_probe.core', addon_root / 'marso/core')):
        package = types.ModuleType(name)
        package.__path__ = [str(directory)]
        sys.modules[name] = package
    assembly = importlib.import_module('_skill_probe.core.assembly')
    prep = importlib.import_module('_skill_probe.core.retexture_prep')
    commands = importlib.import_module('_skill_probe.bridge.commands')
    examples = {
        'assembly_state': {'object_name': 'Cabinet'},
        'group_as_asset': {'object_names': ['Panel', 'Frame'], 'name': 'Cabinet'},
        'prepare_assembly': {'object_name': 'Cabinet', 'size': 4096, 'bake_colours': True},
        'retexture': {'object_name': 'Cabinet', 'prompt': 'Walnut panels and steel handles',
                      'enhance': '', 'auto_uv': True, 'reference_path': ''},
        'retexture_state': {}, 'pbr_state': {},
        'pbr_generate': {'object_names': ['Cabinet']}, 'pbr_remove': {'index': 0},
        'image_material': {'filepath': 'swatch.png', 'apply': False},
        'get_job': {'job_id': 'returned-id', 'cursor': 0}, 'list_jobs': {'active_only': True},
        'viewport_screenshot': {'max_px': 768}, 'save_to_state': {},
        'list_studio_projects': {}, 'set_save_project': {'project_id': 'returned-id'},
        'create_studio_project': {'name': 'Example kit'},
    }
    for name, params in examples.items():
        entry = commands.get(name)
        assert entry is not None, name
        assert not commands.validate(entry.params, params), name
    assert 'preserve_hidden_faces' not in commands.get('prepare_assembly').params['properties']
    print('PASS command schemas: %d documented calls (no handlers executed)' % len(examples))
    bpy.ops.mesh.primitive_cube_add()
    part = bpy.context.object
    part.name = 'ReusablePanel'
    for layer in list(part.data.uv_layers):
        part.data.uv_layers.remove(layer)
    prep.auto_unwrap(bpy.context, part)
    original_name = part.data.uv_layers.active.name
    original_uv = [tuple(loop.uv) for loop in part.data.uv_layers[original_name].data]
    assert all(face_area(part.data, original_name, face) > 1e-8 for face in part.data.polygons)
    root = empty('PanelRoot')
    part.parent = root
    bpy.context.view_layer.update()
    found = assembly.find(bpy.context, root, use_selection=False)
    assert found.parts == [part]
    before_objects = set(bpy.data.objects.keys())
    before_world = part.matrix_world.copy()
    assembly.unwrap_atlas(bpy.context, found, {part.data.name: {0}})
    assert face_area(part.data, assembly.ATLAS_UV, part.data.polygons[0]) < 1e-10
    assert all(face_area(part.data, assembly.ATLAS_UV, face) > 1e-8 for face in list(part.data.polygons)[1:])
    assert [tuple(loop.uv) for loop in part.data.uv_layers[original_name].data] == original_uv
    assert set(bpy.data.objects.keys()) == before_objects
    assert max_difference(part.matrix_world, before_world) < 1e-6 and part.parent == root
    part.hide_set(True)
    assert assembly.find(bpy.context, root, use_selection=False) is None
    part.hide_set(False)
    assembly.tag_parts(found)
    assert assembly.find(bpy.context, part, use_selection=False).key == root
    print('PASS preparation: full-face UVs, hidden-face collapse, preserved UVs/hierarchy, membership')


if __name__ == '__main__':
    if not bpy.app.background:
        raise RuntimeError('Run only in a new background Blender process with factory startup')
    parser = argparse.ArgumentParser()
    parser.add_argument('--addon-root', type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    placement_checks(Path(__file__).resolve().parents[2])
    if args.addon_root:
        preparation_checks(args.addon_root.resolve())
    print('PASS offline smoke on Blender ' + bpy.app.version_string)
