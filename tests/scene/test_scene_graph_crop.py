"""Maintainer checks for skills/core/marso-scene-graph/scripts/crop_objects.py.

Run from the repository root: python -m unittest discover tests/scene
"""
from __future__ import annotations

import json
import pathlib
import tempfile
import unittest

try:
    from test_scene_graph_plan import BOWL, CROP, ONION, PLAN, PX, run, write_fixture
except ImportError:  # run as a package module rather than by discovery
    from tests.scene.test_scene_graph_plan import BOWL, CROP, ONION, PLAN, PX, run, write_fixture

try:
    from PIL import Image
except ImportError:  # pragma: no cover - the suite then reports the missing dependency
    Image = None


@unittest.skipIf(Image is None, "Pillow is required for the crop tests")
class CropObjectsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = pathlib.Path(self.tmp.name)
        self.paths = write_fixture(self.folder)
        self.plan = self.folder / "asset_plan.json"
        result = run(PLAN, str(self.paths["graph"]), "--out", str(self.plan))
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(self.plan.read_text(encoding="utf-8"))
        self.ids = {a["label"]: a["asset_id"] for a in plan["assets"]}
        self.out = self.folder / "references"

    def tearDown(self):
        self.tmp.cleanup()

    def crop(self, *extra: str):
        result = run(CROP, str(self.paths["graph"]), "--manifest", str(self.paths["manifest"]),
                     "--plan", str(self.plan), "--out", str(self.out), *extra)
        return result

    def load(self, asset_id: str):
        folder = self.out / asset_id
        image = Image.open(folder / "crop.png").convert("RGB")
        brief = json.loads((folder / "brief.json").read_text(encoding="utf-8"))
        return image, brief

    def test_a_separately_made_neighbour_touching_the_subject_is_named_both_ways(self):
        """A kettle came back with its power base attached when the base only 'shared the frame'."""
        try:
            from test_scene_graph_plan import view
        except ImportError:
            from tests.scene.test_scene_graph_plan import view
        graph = json.loads(self.paths["graph"].read_text(encoding="utf-8"))
        graph["nodes"].append({"global_id": "g020", "label": "bowl stand", "description": "low ring stand",
                               "category": "kitchenware", "parent": "g003", "relation": "on-top-of",
                               "size_m": 0.2, "views": [view("img001", "o20", (10, 26, 30, 30))]})
        self.paths["graph"].write_text(json.dumps(graph), encoding="utf-8")
        self.assertEqual(run(PLAN, str(self.paths["graph"]), "--out", str(self.plan), "--force").returncode, 0)
        plan = json.loads(self.plan.read_text(encoding="utf-8"))
        ids = {a["label"]: a["asset_id"] for a in plan["assets"]}
        self.assertEqual(self.crop("--ids", ids["bowl"], ids["bowl stand"], "--force").returncode, 0)
        _, bowl = self.load(ids["bowl"])
        _, stand = self.load(ids["bowl stand"])
        self.assertIn("Do not include the bowl stand: it is made as a separate asset", bowl["prompt"])
        self.assertIn("Do not include the bowl: it is made as a separate asset", stand["prompt"])
        self.assertNotIn("countertop: it is made", bowl["prompt"])      # model-route surroundings are not

    def test_default_outlines_the_subject_on_an_unmasked_crop(self):
        result = self.crop()
        self.assertEqual(result.returncode, 0, result.stderr)
        index = json.loads((self.out / "index.json").read_text(encoding="utf-8"))
        self.assertEqual({row["label"] for row in index["assets"]}, {"bowl", "onion"})
        self.assertEqual(index["problems"], [])
        image, brief = self.load(self.ids["bowl"])
        # Bowl box (8,12,32,30), pad 0.15 x 24 = 4 -> crop (4,8,36,34).
        self.assertEqual(brief["view"]["crop_px"], [4, 8, 36, 34])
        self.assertEqual(image.size, (32, 26))
        self.assertEqual(brief["subject_box"], [4, 4, 28, 22])
        onion_px = (PX["g005"][0] + 4 - 4, PX["g005"][1] + 4 - 8)
        self.assertEqual(image.getpixel(onion_px), ONION)  # neighbours stay visible
        self.assertEqual(image.getpixel((6, 6)), BOWL)
        self.assertEqual(image.getpixel((4, 4)), (255, 0, 0))  # the red outline, 2 px
        self.assertEqual(image.getpixel((5, 10)), (255, 0, 0))
        self.assertEqual(image.getpixel((27, 21)), (255, 0, 0))
        self.assertEqual(brief["marking"], {"subject_box": "red outline", "stroke_px": 2})
        roles = {o["global_id"]: o for o in brief["not_the_subject"]}
        self.assertEqual(set(roles), {"g003", "g005", "g006"})
        self.assertEqual(roles["g005"]["sits"], "resting on this object")
        self.assertEqual(roles["g005"]["pixels"], "still visible")
        self.assertEqual(roles["g005"]["role"], "child")
        self.assertEqual(roles["g005"]["box"], [8, 8, 16, 16])
        self.assertEqual(roles["g003"]["sits"], "this object rests on it")
        self.assertEqual(roles["g003"]["pixels"], "still visible")
        self.assertFalse(brief["masking"]["children_masked"])
        self.assertFalse(brief["masking"]["parent_masked"])
        self.assertEqual(brief["subject"]["size_m"], {"w": 0.3, "d": 0.3, "h": 0.12})
        prompt = brief["prompt"]
        self.assertTrue(prompt.startswith("Generate the bowl inside the red box in @crop, isolated, "
                                          "the whole object"), prompt)
        self.assertTrue(prompt.endswith("Do not draw the red box."), prompt)
        self.assertIn("Everything outside the red box is context, not part of the bowl.", prompt)
        self.assertIn("Leave out the onions: they rest on it and are not part of it.", prompt)
        self.assertIn("Glazed ceramic bowl.", prompt)
        self.assertIn("Only the bowl, not the countertop it sits on.", prompt)
        self.assertNotIn("black", prompt)
        self.assertIn("Real size:", prompt)
        self.assertNotIn("Not the subject", prompt)
        self.assertEqual(brief["schema"], "marso/reference-brief@1")

    def test_a_search_crop_holds_the_subject_alone_unmarked(self):
        """A library search by image finds whatever fills the crop, so it gets the subject's own box."""
        self.assertEqual(self.crop().returncode, 0)
        index = json.loads((self.out / "index.json").read_text(encoding="utf-8"))
        row = next(r for r in index["assets"] if r["asset_id"] == self.ids["bowl"])
        self.assertTrue(row["search_crop"].endswith("search.png"))
        _, brief = self.load(self.ids["bowl"])
        self.assertEqual(brief["search_crop"], row["search_crop"])
        image = Image.open(row["search_crop"]).convert("RGB")
        # Bowl box (8,12,32,30); a 2% margin of 24 px rounds to nothing.
        self.assertEqual(image.size, (24, 18))
        # No outline: the corners, where crop.png draws its red box, are the bowl itself.
        for corner in ((0, 0), (23, 17), (0, 17), (23, 0)):
            self.assertEqual(image.getpixel(corner), BOWL)

    def test_mask_children_is_opt_in(self):
        self.assertEqual(self.crop("--mask-children").returncode, 0)
        image, brief = self.load(self.ids["bowl"])
        self.assertEqual(image.getpixel((12, 12)), (0, 0, 0))
        child = next(o for o in brief["not_the_subject"] if o["global_id"] == "g005")
        self.assertEqual(child["pixels"], "blacked out")
        self.assertTrue(brief["masking"]["children_masked"])
        self.assertIn("The black areas in @crop are removed objects", brief["prompt"])
        self.assertEqual(image.getpixel((4, 4)), (255, 0, 0))  # the outline is drawn over masking

    def test_exclude_parent_by_global_id(self):
        result = self.crop("--ids", "g005", "--exclude-parent")
        self.assertEqual(result.returncode, 0, result.stderr)
        index = json.loads((self.out / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(len(index["assets"]), 1)
        image, brief = self.load(self.ids["onion"])
        # Onion box (12,16,20,24), pad 0.15 x 8 = 1 -> crop (11,15,21,25).
        self.assertEqual(brief["view"]["crop_px"], [11, 15, 21, 25])
        self.assertEqual(brief["subject_box"], [1, 1, 9, 9])
        self.assertEqual(image.getpixel((0, 0)), (0, 0, 0))
        self.assertEqual(image.getpixel((4, 4)), ONION)
        parent = next(o for o in brief["not_the_subject"] if o["role"] == "parent")
        self.assertEqual(parent["global_id"], "g004")
        self.assertEqual(parent["pixels"], "blacked out")
        self.assertTrue(brief["masking"]["parent_masked"])
        self.assertFalse((self.out / self.ids["bowl"]).exists())

    def test_a_mostly_hidden_subject_leads_the_prompt_with_its_inferred_whole(self):
        plan = json.loads(self.plan.read_text(encoding="utf-8"))
        for asset in plan["assets"]:
            if asset["label"] == "bowl":
                asset["occlusion"] = "heavy"
                asset["inferred_whole"] = {"whole_description": "White ceramic bowl with a narrow foot.",
                                           "visible": "the rim", "from": "img001"}
        self.plan.write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual(self.crop().returncode, 0)
        _, brief = self.load(self.ids["bowl"])
        self.assertIn("only the rim is visible", brief["prompt"])
        self.assertIn("White ceramic bowl with a narrow foot.", brief["prompt"])
        self.assertEqual(brief["subject"]["occlusion"], "heavy")
        self.assertEqual(brief["subject"]["inferred_whole"]["visible"], "the rim")

    def test_an_object_inside_its_parent_is_told_apart_from_it(self):
        self.assertEqual(self.crop("--ids", self.ids["onion"], "--exclude-parent").returncode, 0)
        _, brief = self.load(self.ids["onion"])
        self.assertIn("Only the onion, not the bowl it sits in.", brief["prompt"])
        self.assertIn("Generate the onion inside the red box in @crop", brief["prompt"])

    def test_the_plans_polygon_count_reaches_the_brief(self):
        result = run(PLAN, str(self.paths["graph"]), "--out", str(self.plan), "--polycount", "by-size", "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.crop("--ids", self.ids["bowl"]).returncode, 0)
        _, brief = self.load(self.ids["bowl"])
        self.assertEqual(brief["polygon_count"], 50000)

    def test_numeric_size_is_stated(self):
        plan = json.loads(self.plan.read_text(encoding="utf-8"))
        for asset in plan["assets"]:
            if asset["label"] == "bowl":
                asset["size_m"] = 0.24
        self.plan.write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual(self.crop().returncode, 0)
        _, brief = self.load(self.ids["bowl"])
        self.assertIn("about 0.24 m", brief["prompt"])
        self.assertNotIn("size unknown", brief["prompt"])

    def test_a_child_covering_the_subject_is_not_masked(self):
        """A kettle standing on its base hides it; blacking the kettle out would black out the base."""
        graph = json.loads(self.paths["graph"].read_text(encoding="utf-8"))
        onion = next(n for n in graph["nodes"] if n["global_id"] == "g005")
        bowl = next(n for n in graph["nodes"] if n["label"] == "bowl")
        onion["views"][0]["bbox"] = bowl["views"][0]["bbox"]
        self.paths["graph"].write_text(json.dumps(graph), encoding="utf-8")
        self.assertEqual(self.crop("--force", "--mask-children").returncode, 0)
        _, brief = self.load(self.ids["bowl"])
        covering = [o for o in brief["not_the_subject"] if o["global_id"] == "g005"]
        self.assertTrue(covering and covering[0]["pixels"].startswith("still visible"), covering)

    def test_the_index_keeps_earlier_runs(self):
        self.assertEqual(self.crop("--ids", self.ids["bowl"]).returncode, 0)
        self.assertEqual(self.crop("--ids", self.ids["onion"], "--exclude-parent").returncode, 0)
        index = json.loads((self.out / "index.json").read_text(encoding="utf-8"))
        self.assertEqual({row["label"] for row in index["assets"]}, {"bowl", "onion"})

    def test_exit_codes(self):
        bad = self.folder / "bad.json"
        bad.write_text("{", encoding="utf-8")
        self.assertEqual(run(CROP, str(bad), "--manifest", str(self.paths["manifest"]), "--plan",
                             str(self.plan), "--out", str(self.out)).returncode, 2)
        self.assertEqual(self.crop("--ids", "g999").returncode, 1)
        missing = self.folder / "missing_manifest.json"
        missing.write_text(json.dumps({"images": [{"image_id": "img001", "path": "nope.png"}]}), encoding="utf-8")
        self.assertEqual(run(CROP, str(self.paths["graph"]), "--manifest", str(missing), "--plan",
                             str(self.plan), "--out", str(self.out)).returncode, 1)
        self.assertEqual(self.crop().returncode, 0)
        second = self.crop()
        self.assertEqual(second.returncode, 1)
        self.assertIn("--force", json.loads(second.stdout)["problems"][0])
        self.assertEqual(self.crop("--force").returncode, 0)


if __name__ == "__main__":
    unittest.main()
