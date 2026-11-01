"""Run in disposable headless Blender: preserve unevaluated import axis/scale corrections."""
import json
import math
from pathlib import Path
import runpy
import tempfile

import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
place = runpy.run_path(str(ROOT / "skills/blender/marso-blender-place-scene/scripts/place_in_blender.py"))["place"]

with tempfile.TemporaryDirectory() as directory:
    folder = Path(directory)
    plan = {"run_id": "import-transform-test", "objects": [{
        "global_id": "item", "order": 0, "name": "Imported asset", "kind": "asset",
        "asset_id": "asset", "location": [0, 0, 0], "rotation_z_deg": 0,
        "dimensions_m": [1, .5, .2]}]}
    (folder / "placement.json").write_text(json.dumps(plan), encoding="utf-8")
    (folder / "imports.json").write_text(json.dumps({"asset": {"instances": [["Geometry"]]}}), encoding="utf-8")
    for caller_updates in (False, True):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        parent = bpy.data.objects.new("Importer conversion", None)
        bpy.context.scene.collection.objects.link(parent)
        parent.scale = (.01, .01, .01)
        parent.rotation_euler.x = math.pi / 2
        parent.location = (4, 5, 6)
        mesh = bpy.data.meshes.new("Asymmetric mesh")
        mesh.from_pydata([(x * 50, y * 10, z * 25) for z in (-1, 1) for y in (-1, 1) for x in (-1, 1)], [],
                         [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)])
        mesh.update()
        obj = bpy.data.objects.new("Geometry", mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = parent
        expected = Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Diagonal((.01, .01, .01, 1))
        if caller_updates:
            bpy.context.view_layer.update()
        for _ in range(2):  # First adoption and owned-placement resume.
            place(str(folder / "placement.json"), str(folder / "imports.json"), photo=False)
            bpy.context.view_layer.update()
            points = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
            dimensions = [max(p[i] for p in points) - min(p[i] for p in points) for i in range(3)]
            assert max(abs(a - b) for a, b in zip(dimensions, (1, .5, .2))) < 1e-5, dimensions
            assert max(abs(obj.matrix_world[i][j] - expected[i][j]) for i in range(3) for j in range(3)) < 1e-6
print("PLACEMENT_IMPORT_TRANSFORMS_PASS")
