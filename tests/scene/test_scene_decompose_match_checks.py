"""Tests for colour conflicts and for the picture check of weak automatic matches.

A blind run merged a black vase with a glass vase at "high" confidence because colour words are
dropped from names and both were 'vase'. Two things follow: names that disagree about colour or
material are never an automatic match, and the automatic matches that rest on different names are
shown, cropped with their surroundings, to an agent who can veto them.
"""
import json
import os
import unittest

from helpers import SKILL as SKILL_DIR, SCRIPTS as SCRIPTS_DIR, ROOT, run_json
from test_scene_decompose_fast_match import AUTO, BUILD, Scene, Image

PLAN_FAST = os.path.join(SCRIPTS_DIR, "plan_fast.py")
PAIR = [("img001", "img002", "partial-overlap")]


class ColourConflictTests(Scene):
    def rooms(self, left, right):
        self.image("img001", [(1, "oak table", None), (2, left, 1)])
        self.image("img002", [(1, "oak table", None), (2, right, 1)])

    def test_two_vases_of_different_colour_are_not_one_object(self):
        self.rooms("black vase", "glass vase")
        _, _, data, _ = self.auto(pairs=PAIR)
        self.assertNotIn("vase", " ".join(m["label"] for m in data["matched"]))
        pair = {m["local_id"] for g in data["groups"] for ms in g["members"].values() for m in ms}
        self.assertEqual(pair, {"img001-002", "img002-002"}, "left for an agent, not dropped")

    def test_the_same_colour_still_matches(self):
        self.rooms("black vase", "matt black vase")
        _, _, data, _ = self.auto(pairs=PAIR)
        self.assertIn("black vase", self.matched_labels(data))

    def test_a_name_with_no_colour_still_matches_one_with(self):
        self.rooms("vase", "glass vase")
        _, _, data, _ = self.auto(pairs=PAIR)
        self.assertEqual(len(data["matched"]), 2, "the table and the vase")

    def test_steel_and_silver_are_one_colour(self):
        self.rooms("stainless kettle", "silver kettle")
        _, _, data, _ = self.auto(pairs=PAIR)
        self.assertIn("stainless kettle", self.matched_labels(data))

    def test_wood_and_oak_are_one_material(self):
        self.rooms("wooden stool", "oak stool")
        _, _, data, _ = self.auto(pairs=PAIR)
        self.assertIn("wooden stool", self.matched_labels(data))


class ChecksTests(Scene):
    def room(self):
        self.image("img001", [(1, "oak table", None, {"bbox": [0.2, 0.4, 0.8, 0.9]}),
                              (2, "jug", 1, {"bbox": [0.4, 0.3, 0.45, 0.4]}),
                              (3, "blue mug", 1, {"bbox": [0.5, 0.3, 0.55, 0.4]})])
        self.image("img002", [(1, "oak table", None, {"bbox": [0.2, 0.4, 0.8, 0.9]}),
                              (2, "ceramic jug", 1, {"bbox": [0.4, 0.3, 0.45, 0.4]}),
                              (3, "blue mug", 1, {"bbox": [0.5, 0.3, 0.55, 0.4]})])

    def test_only_matches_with_different_names_are_checked(self):
        self.room()
        _, report, data, _ = self.auto(pairs=PAIR)
        self.assertEqual([c["label"] for c in data["checks"]], ["jug"])
        self.assertEqual(report["checks"], 1)

    def test_big_objects_are_not_worth_a_picture(self):
        self.image("img001", [(1, "oak parquet floor", None, {"bbox": [0, 0.5, 1, 1]})])
        self.image("img002", [(1, "parquet floor", None, {"bbox": [0, 0.5, 1, 1]})])
        _, _, data, _ = self.auto(pairs=PAIR)
        self.assertEqual(data["matched"][0]["label"], "oak parquet floor")
        self.assertEqual(data["checks"], [])

    def test_a_check_with_no_groups_still_gets_an_agent(self):
        self.room()
        _, _, data, _ = self.auto(pairs=PAIR)
        self.assertTrue(data["batches"], "a batch exists for the check alone")
        self.assertEqual(data["batches"][0]["checks"], ["k1"])

    @unittest.skipIf(Image is None, "Pillow is not installed; check sheets need it")
    def test_a_picture_is_drawn_for_each_check(self):
        self.room()
        for name in ("a.jpg", "b.jpg"):
            Image.new("RGB", (800, 600), (50, 60, 70)).save(os.path.join(self.tmp, name))
        manifest = os.path.join(self.tmp, "manifest.json")
        with open(manifest, "w", encoding="utf-8") as f:
            json.dump({"images": [{"image_id": "img001", "path": "a.jpg"},
                                  {"image_id": "img002", "path": "b.jpg"}]}, f)
        _, _, data, _ = self.auto("--manifest", manifest, "--checks", os.path.join(self.tmp, "checks"),
                                  pairs=PAIR)
        self.assertTrue(os.path.exists(data["checks"][0]["sheet"]))

    @unittest.skipIf(Image is None, "Pillow is not installed; check sheets need it")
    def test_the_brief_names_the_picture_and_the_veto_format(self):
        run_dir = os.path.join(self.tmp, "run")
        os.makedirs(os.path.join(run_dir, "match"))
        self.room()
        for name in ("a.jpg", "b.jpg"):
            Image.new("RGB", (800, 600), (50, 60, 70)).save(os.path.join(self.tmp, name))
        manifest = os.path.join(self.tmp, "manifest.json")
        with open(manifest, "w", encoding="utf-8") as f:
            json.dump({"images": [{"image_id": "img001", "path": "a.jpg"},
                                  {"image_id": "img002", "path": "b.jpg"}]}, f)
        code, _, _ = run_json(AUTO, "--structures", self.str, "--detections", self.det,
                              "--manifest", manifest, "--checks", os.path.join(run_dir, "match", "checks"),
                              "--out", os.path.join(run_dir, "match", "auto.json"), "--force")
        self.assertEqual(code, 0)
        code, report, _ = run_json(PLAN_FAST, "match", "--run", run_dir)
        self.assertEqual(code, 0)
        with open(os.path.join(run_dir, "match", "brief.m1.md"), encoding="utf-8") as f:
            brief = f.read()
        self.assertIn("Automatic matches to verify", brief)
        self.assertIn("k1", brief)
        self.assertIn('"vetoes"', brief)


class VetoTests(Scene):
    def setUp(self):
        super().setUp()
        self.image("img001", [(1, "oak table", None, {"bbox": [0.2, 0.4, 0.8, 0.9]}),
                              (2, "jug", 1, {"bbox": [0.4, 0.3, 0.45, 0.4]})])
        self.image("img002", [(1, "oak table", None, {"bbox": [0.2, 0.4, 0.8, 0.9]}),
                              (2, "ceramic jug", 1, {"bbox": [0.4, 0.3, 0.45, 0.4]})])
        self.auto(pairs=PAIR)
        self.auto_path = os.path.join(self.tmp, "auto.json")

    def build(self, **body):
        path = os.path.join(self.tmp, "decisions.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"batch_id": "m1", **body}, f)
        out = os.path.join(self.tmp, "matches.json")
        code, report, err = run_json(BUILD, "--auto", self.auto_path, "--detections", self.det,
                                     "--decisions", path, "--out", out, "--force")
        with open(out, encoding="utf-8") as f:
            return code, report, json.load(f)

    def jug_members(self, data):
        return [{m["local_id"] for m in o["members"]} for o in data["objects"]
                if any("jug" in m["local_id"] or o["label"] == "jug" for m in o["members"])]

    def test_without_a_veto_the_match_stands(self):
        _, _, data = self.build()
        self.assertIn({"img001-002", "img002-002"}, self.jug_members(data))

    def test_a_veto_separates_them_and_says_why(self):
        code, report, data = self.build(vetoes=[{"check": "k1", "reason": "one has a spout, one does not"}])
        self.assertEqual(code, 0, report)
        owners = [o for o in data["objects"] if o["label"] in ("jug", "ceramic jug")]
        self.assertEqual(len(owners), 2)
        self.assertTrue(all(len(o["members"]) == 1 for o in owners))
        self.assertEqual(data["vetoed"][0]["reason"], "one has a spout, one does not")
        self.assertIn("separated", data["notes"])
        seen = [m["local_id"] for o in data["objects"] for m in o["members"]]
        self.assertEqual(len(seen), len(set(seen)), "nothing lost or doubled")
        self.assertEqual(len(seen), 4)

    def test_a_veto_of_an_unknown_check_is_a_problem_not_a_crash(self):
        code, report, data = self.build(vetoes=[{"check": "k9", "reason": "x"}])
        self.assertEqual(code, 1)
        self.assertTrue(any("k9" in p for p in report["problems"]))
        self.assertIn({"img001-002", "img002-002"}, self.jug_members(data), "the match is untouched")


class PositionTests(Scene):
    """A close-up covers a known region of the wide shot, so what is in that region is offered."""

    REGION = [0.4, 0.4, 0.6, 0.6]

    def registration_with_region(self):
        path = os.path.join(self.tmp, "registration.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"pairs": [{"a": "img001", "b": "img002", "relation": "close-up",
                                  "closer": "img002", "region": self.REGION}]}, f)
        return path

    def run_auto(self):
        out = os.path.join(self.tmp, "auto.json")
        run_json(AUTO, "--structures", self.str, "--detections", self.det, "--out", out, "--force",
                 "--registration", self.registration_with_region())
        with open(out, encoding="utf-8") as f:
            return json.load(f)

    def room(self, wide_name, close_name):
        """Ten look-alike pens and keys on each side make the table's group too big to send whole,
        so a thing with no look-alike on the other side is pruned from it: the case this is for."""
        fill = [(n, name, 1, {"bbox": [0.25 + 0.04 * k, 0.8, 0.27 + 0.04 * k, 0.85]})
                for k, (n, name) in enumerate(zip(range(4, 14), ["pen"] * 5 + ["key"] * 5))]
        self.image("img001", [(1, "oak table", None, {"bbox": [0.2, 0.4, 0.8, 0.9]}),
                              (2, wide_name, 1, {"bbox": [0.48, 0.48, 0.52, 0.52]}),
                              (3, "far lamp", 1, {"bbox": [0.9, 0.1, 0.95, 0.2]})] + fill)
        self.image("img002", [(1, "oak table", None, {"bbox": [0, 0, 1, 1]}),
                              (2, close_name, 1, {"bbox": [0.45, 0.45, 0.55, 0.55]})]
                   + [(n, name, 1, {"bbox": [0.1 + 0.05 * k, 0.8, 0.12 + 0.05 * k, 0.85]})
                      for k, (n, name) in enumerate(zip(range(4, 14), ["pen"] * 5 + ["key"] * 5))])

    def position_group(self, data):
        return next((g for g in data["groups"] if "position" in g["carrier"]), None)

    def test_two_names_that_share_nothing_are_still_offered_by_position(self):
        """'earbuds case' and 'hockey puck' share no word, and sit in the same place."""
        self.room("earbuds case", "hockey puck")
        group = self.position_group(self.run_auto())
        self.assertIsNotNone(group)
        self.assertEqual({m["local_id"] for ms in group["members"].values() for m in ms},
                         {"img001-002", "img002-002"})

    def test_an_object_outside_the_region_is_not_offered(self):
        self.room("earbuds case", "hockey puck")
        group = self.position_group(self.run_auto())
        ids = {m["local_id"] for ms in group["members"].values() for m in ms}
        self.assertNotIn("img001-003", ids, "the lamp is nowhere near the region")

    def test_no_region_means_no_position_group(self):
        self.room("earbuds case", "hockey puck")
        out = os.path.join(self.tmp, "auto.json")
        run_json(AUTO, "--structures", self.str, "--detections", self.det, "--out", out, "--force",
                 "--registration", self.registration([("img001", "img002", "close-up")]))
        with open(out, encoding="utf-8") as f:
            self.assertIsNone(self.position_group(json.load(f)))

    def test_a_pair_already_matched_by_name_is_not_offered_again(self):
        self.room("blue mug", "blue mug")
        self.assertIsNone(self.position_group(self.run_auto()))


class OverlappingRefusalTests(Scene):
    """Two groups can offer one object, so two agents can refuse overlapping sets. An object can
    be in only one identity group, and the graph's validator rejects the file otherwise."""

    def test_refusals_that_share_a_candidate_become_one_unresolved_set(self):
        for image in ("img001", "img002"):
            self.image(image, [(1, "oak table", None)] + [(n, "bottle", 1) for n in (2, 3, 4)])
        self.auto(pairs=PAIR)
        paths = []
        for batch, candidates in (("m1", ["img001-002", "img002-002", "img002-003"]),
                                  ("m2", ["img002-003", "img001-003"])):
            path = os.path.join(self.tmp, f"decisions.{batch}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"batch_id": batch, "refusals": [
                    {"candidates": candidates, "for": "same bottle", "against": "cannot tell",
                     "distinct_objects": 2}]}, f)
            paths.append(path)
        out = os.path.join(self.tmp, "matches.json")
        code, report, _ = run_json(BUILD, "--auto", os.path.join(self.tmp, "auto.json"),
                                   "--detections", self.det, "--decisions", *paths, "--out", out, "--force")
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        sets = [{c["local_id"] for c in u["candidates"]} for u in data["unresolved"]
                if "img002-003" in {c["local_id"] for c in u["candidates"]}]
        self.assertEqual(len(sets), 1, "one set, not two that overlap")
        self.assertEqual(sets[0], {"img001-002", "img001-003", "img002-002", "img002-003"})
        counted = [c["local_id"] for u in data["unresolved"] for c in u["candidates"]]
        self.assertEqual(len(counted), len(set(counted)), "no object is in two sets")


if __name__ == "__main__":
    unittest.main()
