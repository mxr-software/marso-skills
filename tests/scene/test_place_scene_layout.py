"""Maintainer checks for skills/blender/marso-blender-place-scene/scripts/layout_plan.py.

Run from the repository root: python -m unittest discover tests/scene
"""
from __future__ import annotations

import json
import math
import pathlib
import tempfile
import unittest

try:
    from test_scene_graph_plan import HEIGHT, WIDTH, fixture_graph, run, view
except ImportError:  # run as a package module rather than by discovery
    from tests.scene.test_scene_graph_plan import HEIGHT, WIDTH, fixture_graph, run, view

REPO = pathlib.Path(__file__).resolve().parents[2]
LAYOUT = REPO / "skills" / "blender" / "marso-blender-place-scene" / "scripts" / "layout_plan.py"


def assets_doc() -> dict:
    """The generation record for the fixture: the bowl and the two onions were generated."""
    return {"schema": "marso/scene-assets@1", "project": "kitchen_test", "assets": [
        {"asset_id": "a002", "label": "bowl", "members": ["g004"], "count": 1, "pbr_asset_id": "P2",
         "minted": "minted", "import": {"status": "pending"}},
        {"asset_id": "a003", "label": "onion", "members": ["g005", "g006"], "count": 2, "pbr_asset_id": "P3",
         "minted": "minted", "import": {"status": "pending"}},
    ]}


class LayoutPlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run_dir = pathlib.Path(self.tmp.name)
        self.graph = fixture_graph()
        (self.run_dir / "manifest.json").write_text(json.dumps({"images": [
            {"image_id": "img001", "path": "img001.png", "width": WIDTH, "height": HEIGHT},
            {"image_id": "img002", "path": "img002.png", "width": WIDTH, "height": HEIGHT}]}), encoding="utf-8")
        (self.run_dir / "registration.json").write_text(json.dumps(
            {"schema": "scene-decompose/registration@1", "establishing_view": "img001", "pairs": []}),
            encoding="utf-8")
        self.assets = self.run_dir / "assets.json"
        self.assets.write_text(json.dumps(assets_doc()), encoding="utf-8")
        self.out = self.run_dir / "placement.json"

    def tearDown(self):
        self.tmp.cleanup()

    def layout(self, *extra: str, code: int | None = None) -> dict:
        (self.run_dir / "scene_graph.json").write_text(json.dumps(self.graph), encoding="utf-8")
        result = run(LAYOUT, str(self.run_dir), "--assets", str(self.assets), "--out", str(self.out),
                     "--hfov", "90", "--force", *extra)
        if code is not None:
            self.assertEqual(result.returncode, code, result.stderr)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return json.loads(self.out.read_text(encoding="utf-8"))

    @staticmethod
    def by_id(placement: dict) -> dict[str, dict]:
        return {o["global_id"]: o for o in placement["objects"]}

    def test_order_parents_and_kinds(self):
        placement = self.layout(code=0)
        self.assertEqual(placement["schema"], "marso/placement@1")
        self.assertEqual(placement["project"], "kitchen_test")
        self.assertEqual({a["kind"] for a in placement["anchors"]}, {"floor", "wall"})
        objects = self.by_id(placement)
        order = [o["global_id"] for o in sorted(placement["objects"], key=lambda o: o["order"])]
        self.assertEqual(order[0], "g003")  # the worktop is the landmark
        self.assertTrue(objects["g003"]["landmark"])
        for gid, obj in objects.items():  # every parent comes before its children
            if obj["parent"] in objects:
                self.assertLess(order.index(obj["parent"]), order.index(gid))
            self.assertEqual(obj["parent"], next(n["parent"] for n in self.graph["nodes"] if n["global_id"] == gid))
        self.assertEqual(objects["g004"]["kind"], "asset")
        self.assertEqual(objects["g007"]["kind"], "placeholder")
        self.assertEqual(placement["assets"]["a003"]["instances"], ["g005", "g006"])
        self.assertEqual(placement["assets"]["a003"]["copies"], 1)
        self.assertEqual(objects["g005"]["name"], "a003_onion_g005")

    def test_a_floor_object_is_projected_onto_the_floor(self):
        objects = self.by_id(self.layout())
        # The worktop's box bottom-centre is u=19/64, v=38/48. With a 90 degree field of view the
        # ray is (2u-1, 1, (1-2v)*0.75) and meets z=0 at t = 1.5 / (-(1-2v)*0.75).
        u, v = 19 / 64, 38 / 48
        t = 1.5 / ((2 * v - 1) * 0.75)
        hit = ((2 * u - 1) * t, t)
        dist = math.hypot(*hit)
        expected = (hit[0] + hit[0] / dist * 0.3, hit[1] + hit[1] / dist * 0.3)  # half its 0.6 m depth
        worktop = objects["g003"]
        self.assertAlmostEqual(worktop["location"][0], expected[0], places=2)
        self.assertAlmostEqual(worktop["location"][1], expected[1], places=2)
        self.assertEqual(worktop["location"][2], 0.0)
        self.assertEqual(worktop["position_basis"], "box bottom-centre projected onto the floor")

    def test_children_rest_on_their_parent(self):
        objects = self.by_id(self.layout())
        worktop, bowl = objects["g003"], objects["g004"]
        self.assertAlmostEqual(bowl["location"][2], worktop["location"][2] + worktop["dimensions_m"][2], places=3)
        self.assertTrue(bowl["position_basis"].startswith("offset of its box inside its parent's"))
        onions = objects["g005"], objects["g006"]
        for onion in onions:  # inside the bowl: above its base, below its rim
            self.assertGreater(onion["location"][2], bowl["location"][2])
            self.assertLess(onion["location"][2], bowl["location"][2] + bowl["dimensions_m"][2])
        self.assertLess(onions[0]["location"][0], onions[1]["location"][0])  # left stays left

    def test_objects_face_the_camera(self):
        objects = self.by_id(self.layout())
        chair = objects["g007"]  # right of centre: turned to face back towards the origin
        self.assertGreater(chair["location"][0], 0)
        self.assertLess(chair["rotation_z_deg"], 0)
        x, y = chair["location"][:2]
        yaw = math.radians(chair["rotation_z_deg"])
        front = (math.sin(yaw), -math.cos(yaw))
        self.assertGreater(front[0] * -x + front[1] * -y, 0.99 * math.hypot(x, y))
        flat = self.by_id(self.layout("--facing", "none"))
        self.assertEqual(flat["g007"]["rotation_z_deg"], 0.0)

    def test_a_wall_without_a_floor_line_stands_behind_the_furthest_object(self):
        placement = self.layout()
        wall = next(a for a in placement["anchors"] if a["kind"] == "wall")
        self.assertIn("wall-guessed", wall["flags"])
        furthest = max(o["location"][1] for o in placement["objects"])
        self.assertGreater(wall["corners"][0][1], furthest)
        self.assertEqual(wall["corners"][2][2], 2.4)  # the graph's wall height

    def test_minted_size_wins_and_disagreement_is_flagged(self):
        imports = self.run_dir / "imports.json"
        imports.write_text(json.dumps({"a002": {"objects": ["bowl"], "dimensions_m": [0.6, 0.6, 0.25]},
                                       "a003": {"objects": ["onion"], "dimensions_m": [0.085, 0.08, 0.08]}}),
                           encoding="utf-8")
        placement = self.layout("--imports", str(imports), code=1)
        objects = self.by_id(placement)
        self.assertIn("size-disagrees", objects["g004"]["flags"])
        self.assertEqual(objects["g004"]["dimensions_m"], [0.6, 0.6, 0.25])
        self.assertEqual(objects["g004"]["size_source"], "minted")
        self.assertEqual(objects["g004"]["target_size_m"], 0.3)
        self.assertNotIn("size-disagrees", objects["g005"]["flags"])
        self.assertTrue(any("size-disagrees" in p for p in placement["problems"]))

    def test_skips(self):
        nodes = {n["global_id"]: n for n in self.graph["nodes"]}
        nodes["g004"]["unconfirmed"] = {"closer_view": "img002", "reason": "x"}
        self.graph["nodes"].append({"global_id": "g010", "label": "chair leg", "parent": "g007",
                                    "relation": "part-of", "size_m": 0.4,
                                    "views": [view("img001", "o10", (42, 40, 44, 46))]})
        placement = self.layout()
        objects = self.by_id(placement)
        skipped = {s["global_id"]: s["reason"] for s in placement["skipped"]}
        self.assertEqual(skipped["g004"], "unconfirmed reading")
        self.assertIn("g005", skipped)  # its parent, the bowl, is not placed
        self.assertEqual(skipped["g010"], "part of its parent")
        self.assertNotIn("g004", objects)
        placement = self.layout("--placeholders", "skip")
        self.assertEqual({o["kind"] for o in placement["objects"]}, set())  # the bowl's parent is a box

    def test_a_member_outside_the_establishing_view_stands_beside_its_twin(self):
        objects = self.by_id(self.layout())
        self.assertIn("position-guessed", objects["g009"]["flags"])
        self.assertIn("identity-group", objects["g009"]["flags"])

    def test_camera(self):
        placement = self.layout("--pitch", "-10", "--camera-height", "1.6")
        camera = placement["camera"]
        self.assertEqual(camera["image_id"], "img001")
        self.assertEqual(camera["hfov_deg"], 90.0)
        self.assertEqual(camera["location"], [0.0, 0.0, 1.6])
        self.assertEqual(camera["rotation_euler_deg"], [80.0, 0.0, 0.0])
        self.assertEqual(camera["resolution"], [WIDTH, HEIGHT])
        (self.run_dir / "scene_graph.json").write_text(json.dumps(self.graph), encoding="utf-8")
        result = run(LAYOUT, str(self.run_dir), "--assets", str(self.assets), "--out", str(self.out), "--force")
        lens = json.loads(self.out.read_text(encoding="utf-8"))["camera"]["hfov_deg"]
        self.assertAlmostEqual(lens, 2 * math.degrees(math.atan(43.27 * 0.8 / 2 / 26)), places=1)
        self.assertIn(result.returncode, (0, 1))

    def test_exit_codes(self):
        self.layout()
        (self.run_dir / "scene_graph.json").write_text(json.dumps(self.graph), encoding="utf-8")
        self.assertEqual(run(LAYOUT, str(self.run_dir), "--assets", str(self.assets), "--out",
                             str(self.out)).returncode, 1)
        self.assertEqual(run(LAYOUT, str(self.run_dir), "--assets", str(self.run_dir / "missing.json"),
                             "--out", str(self.out), "--force").returncode, 2)
        self.assertEqual(run(LAYOUT, str(self.run_dir), "--assets", str(self.assets), "--out", str(self.out),
                             "--force", "--view", "img999").returncode, 1)


if __name__ == "__main__":
    unittest.main()
