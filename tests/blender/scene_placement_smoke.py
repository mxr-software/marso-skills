"""Run in a NEW background Blender process, never an artist's open scene.

blender --background --factory-startup --python-exit-code 1 --python tests/blender/scene_placement_smoke.py
Offline checks only; no Marso connection or generated assets required.
"""
import json
import pathlib
import runpy
import tempfile
import unittest

import bpy
from mathutils import Vector

SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "skills/blender/marso-blender-place-scene/scripts/place_in_blender.py"
place = runpy.run_path(str(SCRIPT))["place"]


def row(gid, parent="floor", asset="asset", location=(0, 3, 0), order=1):
    return dict(global_id=gid, name=gid, parent=parent, relation="on-top-of", asset_id=asset,
                kind="asset", dimensions_m=[2, 2, 2], location=location, rotation_z_deg=0, order=order)


class PlacementTests(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = pathlib.Path(self.tmp.name)
        self.plan = dict(run_id="run-one", project="Room", project_id="project-one", anchors=[
            dict(global_id="floor", name="Floor", location=[0, 0, 0], parent=None)], objects=[])

    def tearDown(self):
        self.tmp.cleanup()

    def cube(self, name):
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.object
        obj.name = name
        return obj

    def run_place(self, imports=None):
        path = self.folder / "placement.json"
        path.write_text(json.dumps(self.plan))
        ipath = self.folder / "imports.json"
        ipath.write_text(json.dumps(imports or {}))
        return place(str(path), str(ipath), photo=False)

    def owned(self, gid, role="entity", run="run-one"):
        return next(o for o in bpy.data.objects if o.get("marso_global_id") == gid
                    and o.get("marso_role") == role and o.get("marso_run_id") == run)

    def assertVector(self, actual, expected):
        self.assertLess((Vector(actual) - Vector(expected)).length, 1e-5)

    def test_geometry_scale_is_independent_and_frames_move_the_assembly(self):
        table, bowl = self.cube("table_mesh"), self.cube("bowl_mesh")
        self.plan["objects"] = [row("table"), row("bowl", "table", "bowl", (.2, 3, 2), 2)]
        imports = {"asset": {"objects": [table.name]}, "bowl": {"objects": [bowl.name]}}
        result = self.run_place(imports)
        frame, child = self.owned("table"), self.owned("bowl")
        self.assertEqual(frame.type, "EMPTY")
        self.assertIs(child.parent, frame)
        self.assertIsNot(child.parent, table)
        before = child.matrix_world.copy()
        table.scale *= 2
        self.owned("table", "geometry").scale *= 1.5
        bpy.context.view_layer.update()
        self.assertEqual(child.matrix_world, before)
        frame.location.x += 4
        bpy.context.view_layer.update()
        self.assertVector(child.matrix_world.translation, before.translation + Vector((4, 0, 0)))
        count = len(bpy.data.objects)
        self.run_place(imports)
        self.assertEqual(len(bpy.data.objects), count)
        self.assertVector(child.matrix_world.translation, (.2, 3, 2))
        self.assertVector(table.scale, (2, 2, 2))
        self.assertVector(self.owned("table", "geometry").scale, (1.5, 1.5, 1.5))

    def test_unrelated_objects_and_two_runs_are_isolated(self):
        unrelated = self.cube("table")
        unrelated.location = (99, 99, 99)
        owners = set(unrelated.users_collection)
        self.plan["objects"] = [row("table")]
        self.run_place()
        self.assertVector(unrelated.location, (99, 99, 99))
        self.assertEqual(set(unrelated.users_collection), owners)
        first = self.owned("table")
        before = first.matrix_world.copy()
        self.plan["run_id"] = "run-two"
        self.plan["objects"][0]["location"] = [10, 0, 0]
        self.run_place()
        self.assertEqual(first.matrix_world, before)
        self.assertVector(self.owned("table", run="run-two").matrix_world.translation, (10, 0, 0))

    def test_complete_multipart_and_nested_instances_are_linked(self):
        top, leg = self.cube("top"), self.cube("leg")
        root = bpy.data.objects.new("root", None)
        middle = bpy.data.objects.new("middle", None)
        for obj in (root, middle):
            bpy.context.scene.collection.objects.link(obj)
        middle.parent, top.parent = root, middle
        leg.location.x = 3
        self.plan["objects"] = [row("table"), row("copy", location=(6, 3, 0), order=2)]
        result = self.run_place({"asset": {"instances": [[root.name, middle.name, top.name, leg.name]]}})
        self.assertEqual(result["unused_imports"], [])
        a, b = self.owned("table", "geometry"), self.owned("copy", "geometry")
        amesh = [o for o in a.children_recursive if o.type == "MESH"]
        bmesh = [o for o in b.children_recursive if o.type == "MESH"]
        self.assertEqual(len(amesh), 2)
        self.assertEqual(len(bmesh), 2)
        self.assertEqual({o.data for o in amesh}, {o.data for o in bmesh})
        self.assertEqual(len(a.children_recursive), len(b.children_recursive))
        self.assertTrue(all(o.parent not in a.children_recursive for o in b.children_recursive))

    def test_cross_instance_import_parent_links_are_separated(self):
        one, child = self.cube("one"), self.cube("part")
        child.parent = one
        two, twin = one.copy(), child.copy()
        for obj in (two, twin):
            bpy.context.scene.collection.objects.link(obj)
        # The copied child initially points at the first instance's root.
        self.plan["objects"] = [row("first"), row("second", location=(8, 3, 0), order=2)]
        self.run_place({"asset": {"instances": [[one.name, child.name], [two.name, twin.name]]}})
        self.assertEqual(len([o for o in self.owned("second", "geometry").children_recursive if o.type == "MESH"]), 2)
        before = twin.matrix_world.copy()
        self.owned("first").location.x += 2
        bpy.context.view_layer.update()
        self.assertEqual(twin.matrix_world, before)

    def test_placeholder_upgrade_and_camera_reuse(self):
        self.plan["objects"] = [row("table")]
        self.plan["camera"] = dict(hfov_deg=60, location=[0, 0, 1.5], rotation_euler_deg=[90, 0, 0], resolution=[640, 480])
        existing = bpy.data.objects.new("establishing_camera", bpy.data.cameras.new("Artist camera"))
        bpy.context.scene.collection.objects.link(existing)
        existing.location = (77, 77, 77)
        self.run_place()
        mesh = self.cube("imported")
        imports = {"asset": {"objects": [mesh.name]}}
        self.run_place(imports)
        box = self.owned("table", "retired-placeholder")
        self.assertTrue(box.hide_render)
        count = len(bpy.data.objects)
        self.run_place(imports)
        self.assertEqual(len(bpy.data.objects), count)
        self.assertVector(existing.location, (77, 77, 77))
        self.assertIsNot(bpy.context.scene.camera, existing)

    def test_foreign_imports_are_not_adopted(self):
        mesh = self.cube("imported")
        self.plan["objects"] = [row("table")]
        imports = {"asset": {"objects": [mesh.name]}}
        self.run_place(imports)
        before = mesh.matrix_world.copy()
        self.plan["run_id"] = "run-two"
        result = self.run_place(imports)
        self.assertTrue(result["not_imported"])
        self.assertEqual(mesh.matrix_world, before)

    def test_cycle_rejected_before_scene_changes(self):
        self.plan["objects"] = [row("one", "two"), row("two", "one", order=2)]
        count = len(bpy.data.objects)
        with self.assertRaises(ValueError):
            self.run_place()
        self.assertEqual(len(bpy.data.objects), count)

    def test_ownership_survives_rename_collection_nesting_and_save_reopen(self):
        mesh = self.cube("source")
        self.plan["objects"] = [row("table")]
        result = self.run_place({"asset": {"objects": [mesh.name]}})
        entity, geometry = self.owned("table"), self.owned("table", "geometry")
        entity.name = "Artist renamed table"
        geometry.scale = (2, 1, 1)
        coll = bpy.data.collections[result["collection"]]
        folder = bpy.data.collections.new("Artist organisation")
        bpy.context.scene.collection.children.link(folder)
        folder.children.link(coll)
        bpy.context.scene.collection.children.unlink(coll)
        path = str(self.folder / "roundtrip.blend")
        bpy.ops.wm.save_as_mainfile(filepath=path)
        bpy.ops.wm.open_mainfile(filepath=path)
        count = len(bpy.data.objects)
        self.run_place()
        self.assertEqual(len(bpy.data.objects), count)
        self.assertEqual(self.owned("table").name, "Artist renamed table")
        self.assertVector(self.owned("table", "geometry").scale, (2, 1, 1))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PlacementTests))
    if not result.wasSuccessful():
        raise RuntimeError("Scene placement checks failed")
