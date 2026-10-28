"""Offline material-isolation and naming test; run only in disposable Blender.

blender --background --factory-startup --offline-mode --python-exit-code 1
--python tests/blender/style_variant_smoke.py -- --addon-root <checkout>
"""

import argparse
import importlib
from pathlib import Path
import sys
import tempfile
import types
from unittest.mock import patch

import bpy


def signature(obj):
    return (
        tuple(tuple(v.co) for v in obj.data.vertices),
        tuple(tuple(p.vertices) for p in obj.data.polygons),
        tuple(tuple(uv.uv) for uv in obj.data.uv_layers.active.data),
    )


def main():
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError('Use a new factory-startup background process, with no input file')
    parser = argparse.ArgumentParser()
    parser.add_argument('--addon-root', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    sys.dont_write_bytecode = True
    for name, directory in (
        ('_variant_probe', args.addon_root / 'marso'),
        ('_variant_probe.core', args.addon_root / 'marso/core'),
    ):
        package = types.ModuleType(name)
        package.__path__ = [str(directory)]
        sys.modules[name] = package
    apply = importlib.import_module('_variant_probe.core.material_apply')

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_cube_add()
    source = bpy.context.object
    source.name = 'Stool.Source'
    original = bpy.data.materials.new('Source.Frame')
    original.use_nodes = True
    source.data.materials.append(original)
    geometry = signature(source)
    source_nodes = tuple(node.name for node in original.node_tree.nodes)

    def branch(name):
        copy = source.copy()
        copy.data = source.data.copy()
        copy.name = name
        bpy.context.scene.collection.objects.link(copy)
        copy.data.materials[0] = original.copy()
        return copy

    first, second = branch('Stool.DarkOak'), branch('Stool.Painted')
    first_material, second_material = first.active_material, second.active_material
    assert len({original.as_pointer(), first_material.as_pointer(), second_material.as_pointer()}) == 3
    second_nodes = tuple(node.name for node in second_material.node_tree.nodes)

    # Synthetic inputs replace only file download/loading. The real add-on matches
    # slot names and applies its material/UV/node wiring. No account or cloud calls.
    def fixture_image(job_key, pass_name, data, downloads_root):
        image = bpy.data.images.new(job_key + '.' + pass_name, width=4, height=4)
        image.generated_color = (0.3, 0.15, 0.05, 1) if job_key == 'oak' else (0.1, 0.2, 0.8, 1)
        path = downloads_root / (job_key + '.' + pass_name + '.png')
        image.save_render(str(path))
        bpy.data.images.remove(image)
        image = bpy.data.images.load(str(path))
        image.name = job_key + '.' + pass_name
        image.colorspace_settings.name = 'sRGB' if pass_name == 'albedo' else 'Non-Color'
        image.pack()
        return image

    with tempfile.TemporaryDirectory() as temp, patch.object(apply, '_write_and_load_texture', fixture_image):
        for obj, label, job in [(first, 'DarkOak', 'oak'), (second, 'Painted', 'paint')]:
            submission_name = obj.active_material.name
            apply.apply_to_object(obj, {submission_name + '/albedo': b'fixture'}, job, Path(temp))
            assert obj.active_material.name == submission_name
            obj.active_material.name = 'Stool__' + label + '__Frame__v01'
            shader = next(n for n in obj.active_material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
            image = shader.inputs['Base Color'].links[0].from_node.image
            assert image.name == job + '.albedo' and image.packed_file
            assert signature(obj) == geometry
            assert tuple(n.name for n in original.node_tree.nodes) == source_nodes
            if obj == first:
                assert tuple(n.name for n in second_material.node_tree.nodes) == second_nodes
        saved = Path(temp) / 'variants.blend'
        bpy.ops.wm.save_as_mainfile(filepath=str(saved))
        bpy.ops.wm.open_mainfile(filepath=str(saved))
        assert signature(bpy.data.objects['Stool.Source']) == geometry
        for name, style, job in [('Stool.DarkOak', 'DarkOak', 'oak'), ('Stool.Painted', 'Painted', 'paint')]:
            obj = bpy.data.objects[name]
            assert obj.active_material.name == 'Stool__' + style + '__Frame__v01'
            shader = next(n for n in obj.active_material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
            assert shader.inputs['Base Color'].links[0].from_node.image.name == job + '.albedo'
    print('PASS: source/variant isolation, named-slot application, post-apply naming, packed save/reopen')


if __name__ == '__main__':
    main()
