"""Offline shader checks for appearance-state guidance; no Marso calls or artistic benchmark.

Run in disposable Blender: blender --background --factory-startup --python this_file.py
"""
import tempfile
from pathlib import Path

import bpy
import numpy as np


def make_material():
    material = bpy.data.materials.new('State fixture')
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    mix = nodes.new('ShaderNodeMixShader')
    links.new(mix.outputs[0], output.inputs['Surface'])
    amount = nodes.new('ShaderNodeValue')
    amount.name = 'State'
    amount.outputs[0].default_value = 0
    mask = nodes.new('ShaderNodeValue')
    mask.name = 'Mask'
    mask.outputs[0].default_value = 1
    factor = nodes.new('ShaderNodeMath')
    factor.operation = 'MULTIPLY'
    factor.use_clamp = True
    links.new(amount.outputs[0], factor.inputs[0])
    links.new(mask.outputs[0], factor.inputs[1])
    links.new(factor.outputs[0], mix.inputs[0])
    for index, colour in enumerate(((0.7, 0.03, 0.01, 1), (0.01, 0.03, 0.7, 1))):
        shader = nodes.new('ShaderNodeBsdfPrincipled')
        shader.inputs['Roughness'].default_value = 0.3 + index * 0.5
        image = bpy.data.images.new(f'State {index} colour', 2, 2)
        image.generated_color = colour
        image.pack()
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = image
        links.new(tex.outputs['Color'], shader.inputs['Base Color'])
        uv = nodes.new('ShaderNodeUVMap')
        uv.uv_map = 'UVMap'
        links.new(uv.outputs['UV'], tex.inputs['Vector'])
        normal_image = bpy.data.images.new(f'State {index} normal', 2, 2)
        normal_image.generated_color = (0.5, 0.5, 1, 1)
        normal_image.colorspace_settings.name = 'Non-Color'
        normal_image.pack()
        normal_tex = nodes.new('ShaderNodeTexImage')
        normal_tex.image = normal_image
        normal = nodes.new('ShaderNodeNormalMap')
        normal.uv_map = 'UVMap'
        links.new(uv.outputs['UV'], normal_tex.inputs['Vector'])
        links.new(normal_tex.outputs['Color'], normal.inputs['Color'])
        links.new(normal.outputs['Normal'], shader.inputs['Normal'])
        links.new(shader.outputs['BSDF'], mix.inputs[index + 1])
    return material


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 8
    scene.render.resolution_x = 64
    scene.render.resolution_y = 32
    scene.render.resolution_percentage = 100
    scene.world = bpy.data.worlds.new('Fixture world')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1)
    bpy.ops.mesh.primitive_plane_add(size=1.5, location=(-0.9, 0, 0))
    left = bpy.context.object
    left.name = 'Independent state A'
    material = make_material()
    left.data.materials.append(material)
    right = left.copy()
    scene.collection.objects.link(right)
    right.name = 'Independent state B'
    right.location.x = 0.9
    right.material_slots[0].link = 'OBJECT'
    right.material_slots[0].material = material.copy()
    left['appearance_state'] = 0.0
    driver = material.node_tree.nodes['State'].outputs[0].driver_add('default_value').driver
    driver.type = 'AVERAGE'
    variable = driver.variables.new()
    variable.type = 'SINGLE_PROP'
    variable.targets[0].id = left
    variable.targets[0].data_path = '["appearance_state"]'
    geometry = [tuple(v.co) for v in left.data.vertices]
    uvs = [tuple(loop.uv) for loop in left.data.uv_layers.active.data]
    bpy.ops.object.camera_add(location=(0, 0, 4))
    scene.camera = bpy.context.object
    scene.camera.data.type = 'ORTHO'
    scene.camera.data.ortho_scale = 4

    with tempfile.TemporaryDirectory(prefix='marso-states-') as tmp:
        def render(state, mask=1):
            left['appearance_state'] = state
            left.update_tag()
            material.node_tree.nodes['Mask'].outputs[0].default_value = mask
            bpy.context.view_layer.update()
            scene.render.filepath = str(Path(tmp) / 'sample.exr')
            scene.render.image_settings.file_format = 'OPEN_EXR'
            bpy.ops.render.render(write_still=True)
            pixels_image = bpy.data.images.load(scene.render.filepath, check_existing=False)
            pixels = np.array(pixels_image.pixels[:]).reshape(32, 64, 4)
            bpy.data.images.remove(pixels_image)
            return pixels[12:20, 12:22, :3].mean((0, 1)), pixels[12:20, 42:52, :3].mean((0, 1))

        a, other_a = render(0)
        midpoint, other_mid = render(0.5)
        b, other_b = render(1)
        masked, _ = render(1, 0)
        assert a[0] > a[2] * 3, (a, b)
        assert b[2] > b[0] * 3, (a, b)
        assert b[0] < midpoint[0] < a[0] and a[2] < midpoint[2] < b[2]
        assert np.allclose(masked, a, atol=0.01), (masked, a)
        assert np.allclose(other_a, other_b, atol=0.01)
        assert np.allclose(other_a, other_mid, atol=0.01)
        assert left.data is right.data
        assert geometry == [tuple(v.co) for v in left.data.vertices]
        assert uvs == [tuple(loop.uv) for loop in left.data.uv_layers.active.data]
        saved_pixels = {image.name: list(image.pixels[:]) for image in bpy.data.images if image.name.startswith('State ')}
        path = str(Path(tmp) / 'states.blend')
        bpy.ops.wm.save_as_mainfile(filepath=path)
        bpy.ops.wm.open_mainfile(filepath=path)
        loaded = bpy.data.objects['Independent state A']
        other = bpy.data.objects['Independent state B']
        assert loaded.data is other.data
        assert loaded.active_material is not other.active_material
        restored_driver = loaded.active_material.node_tree.animation_data.drivers[0].driver
        assert restored_driver.variables[0].targets[0].id is loaded
        for image in bpy.data.images:
            if image.name.startswith('State '):
                assert np.allclose(image.pixels[:], saved_pixels[image.name]), image.name
                assert image.packed_file or image.source == 'GENERATED', (image.name, image.source, image.filepath)
        print('PASS: rendered endpoints/midpoint, protected mask, independent shared-mesh users, unchanged UVs, saved drivers and self-contained maps')


if __name__ == '__main__':
    main()
