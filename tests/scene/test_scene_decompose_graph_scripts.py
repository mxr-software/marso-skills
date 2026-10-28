"""Tests for the scene-decompose lead's graph scripts: apply_matches, score_views, validate_graph."""
import copy
import glob
import json
import os
import shutil
import tempfile
import unittest

from helpers import SKILL as SKILL_DIR, SCRIPTS as SCRIPTS_DIR, ROOT, run, run_json

LEAD = SKILL_DIR
SCRIPTS = SCRIPTS_DIR
EMIT = SKILL_DIR


def detection(local_id, label, bbox, **extra):
    out = {"local_id": local_id, "label": label, "description": f"a {label}",
           "category": "stuff", "bbox": bbox, "truncated": [], "occluded": False,
           "size_m": 1.0, "size_confidence": "medium", "size_basis": "a guess",
           "pass": "overview"}
    out.update(extra)
    return out


class Fixture(unittest.TestCase):
    """Two images of one scene: a floor, a table on it, and a bowl on the table."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.structures = os.path.join(self.tmp, "structure")
        self.detections = os.path.join(self.tmp, "detections")
        os.makedirs(self.structures)
        os.makedirs(self.detections)

        self.det = {
            "img001": [detection("img001-1", "floor", [0.0, 0.5, 1.0, 1.0]),
                       detection("img001-2", "table", [0.2, 0.3, 0.8, 0.9]),
                       detection("img001-3", "bowl", [0.4, 0.4, 0.5, 0.5])],
            "img002": [detection("img002-1", "floor", [0.0, 0.6, 1.0, 1.0]),
                       detection("img002-2", "table", [0.1, 0.1, 0.9, 0.95]),
                       detection("img002-3", "bowl", [0.3, 0.2, 0.7, 0.6])],
        }
        self.struct = {
            "img001": [("img001-1", None, None), ("img001-2", "img001-1", "on-top-of"),
                       ("img001-3", "img001-2", "on-top-of")],
            "img002": [("img002-1", None, None), ("img002-2", "img002-1", "on-top-of"),
                       ("img002-3", "img002-2", "on-top-of")],
        }
        self.clusters = {"img001": [], "img002": []}
        self.areas = {"img001": [], "img002": []}
        self.write_inputs()

        self.matches = {
            "schema": "scene-decompose/matches@1", "images": ["img001", "img002"],
            "objects": [
                {"global_id": "g001", "label": "floor",
                 "members": [{"image_id": "img001", "local_id": "img001-1"},
                             {"image_id": "img002", "local_id": "img002-1"}],
                 "evidence": ["a", "b"], "confidence": "high"},
                {"global_id": "g002", "label": "table",
                 "members": [{"image_id": "img001", "local_id": "img001-2"},
                             {"image_id": "img002", "local_id": "img002-2"}],
                 "evidence": ["a", "b"], "confidence": "high"},
                {"global_id": "g003", "label": "bowl",
                 "members": [{"image_id": "img001", "local_id": "img001-3"},
                             {"image_id": "img002", "local_id": "img002-3"}],
                 "evidence": ["a", "b"], "confidence": "high"},
            ],
        }

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_inputs(self):
        for image_id, rows in self.det.items():
            with open(os.path.join(self.detections, f"{image_id}.json"), "w", encoding="utf-8") as f:
                json.dump({"image_id": image_id, "objects": rows}, f)
        for image_id, nodes in self.struct.items():
            with open(os.path.join(self.structures, f"{image_id}.json"), "w", encoding="utf-8") as f:
                json.dump({"image_id": image_id,
                           # a row may carry a fourth item, support_inferred
                           "nodes": [{"local_id": row[0], "parent": row[1],
                                      "relation": row[2],
                                      "support_inferred": bool(row[3]) if len(row) > 3 else False}
                                     for row in nodes],
                           "clusters": self.clusters[image_id],
                           "areas": self.areas[image_id]}, f)

    def add_rival_surface(self):
        """Give both images a mat beside the table, so two parents can really disagree.

        Without it the fixture can only offer "on the table" against "on the floor",
        which is not a disagreement at all: the table is on the floor, so one answer is
        simply the more specific one.
        """
        self.det["img001"].append(detection("img001-4", "mat", [0.1, 0.35, 0.2, 0.45]))
        self.det["img002"].append(detection("img002-4", "mat", [0.05, 0.15, 0.25, 0.55]))
        self.matches["objects"].append(
            {"global_id": "g004", "label": "mat",
             "members": [{"image_id": "img001", "local_id": "img001-4"},
                         {"image_id": "img002", "local_id": "img002-4"}],
             "evidence": ["a", "b"], "confidence": "high"})

    def path(self, name, data):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return p

    def build(self, matches=None, extra=()):
        out = os.path.join(self.tmp, "scene_graph.json")
        code, report, err = run_json(
            os.path.join(SCRIPTS, "apply_matches.py"),
            "--matches", self.path("matches.json", matches or self.matches),
            "--structures", self.structures, "--detections", self.detections,
            "--out", out, "--force", *extra)
        return code, report, out


class ApplyMatchesTests(Fixture):
    def test_help_works(self):
        code, out, _ = run(os.path.join(SCRIPTS, "apply_matches.py"), "--help")
        self.assertEqual(code, 0)
        self.assertIn("--matches", out)

    def test_builds_a_graph_with_global_parents(self):
        code, report, out = self.build()
        self.assertEqual(code, 0, report["problems"])
        with open(out, encoding="utf-8") as f:
            graph = json.load(f)
        by_id = {n["global_id"]: n for n in graph["nodes"]}
        self.assertIsNone(by_id["g001"]["parent"])
        self.assertEqual(by_id["g002"]["parent"], "g001")
        self.assertEqual(by_id["g003"]["parent"], "g002")
        self.assertEqual(by_id["g003"]["seen_in"], 2)

    def test_gathers_every_view_of_an_object(self):
        _, _, out = self.build()
        with open(out, encoding="utf-8") as f:
            graph = json.load(f)
        bowl = next(n for n in graph["nodes"] if n["global_id"] == "g003")
        self.assertEqual({v["image_id"] for v in bowl["views"]}, {"img001", "img002"})
        self.assertEqual(len(bowl["views"]), 2)

    def test_the_better_view_supplies_the_description(self):
        """img002's bowl fills far more of the frame, so its reading wins."""
        self.det["img002"][2]["description"] = "the closer reading"
        self.write_inputs()
        _, _, out = self.build()
        with open(out, encoding="utf-8") as f:
            graph = json.load(f)
        bowl = next(n for n in graph["nodes"] if n["global_id"] == "g003")
        self.assertEqual(bowl["description"], "the closer reading")

    def test_a_merged_object_is_named_by_its_best_view(self):
        """The wide view called it a 'hair claw'; the close-up, much bigger in frame, saw sunglasses."""
        self.det["img001"][2]["label"] = "hair claw"
        self.det["img002"][2]["label"] = "sunglasses"
        self.write_inputs()
        self.matches["objects"][2]["label"] = "hair claw"        # the first member's name
        _, _, out = self.build()
        with open(out, encoding="utf-8") as f:
            node = next(n for n in json.load(f)["nodes"] if n["global_id"] == "g003")
        self.assertEqual(node["label"], "sunglasses")

    def test_an_agent_given_name_is_kept(self):
        self.det["img002"][2]["label"] = "sunglasses"
        self.write_inputs()
        self.matches["objects"][2].update(label="tortoiseshell sunglasses", named_by_agent=True)
        _, _, out = self.build()
        with open(out, encoding="utf-8") as f:
            node = next(n for n in json.load(f)["nodes"] if n["global_id"] == "g003")
        self.assertEqual(node["label"], "tortoiseshell sunglasses")

    def test_a_mostly_hidden_object_carries_its_inferred_whole(self):
        """Hidden in every view: the context-built description travels with the node."""
        for row, text in ((self.det["img001"][2], "white ceramic bowl, rim only"),
                          (self.det["img002"][2], "white ceramic cereal bowl, matching the stack")):
            row.update(occlusion="heavy", occluded=True, visible="the rim",
                       whole_description=text)
        self.write_inputs()
        _, _, out = self.build()
        with open(out, encoding="utf-8") as f:
            bowl = next(n for n in json.load(f)["nodes"] if n["global_id"] == "g003")
        self.assertEqual(bowl["occlusion"], "heavy")
        self.assertEqual(bowl["inferred_whole"]["visible"], "the rim")
        self.assertIn(bowl["inferred_whole"]["from"], ("img001", "img002"))

    def test_a_clear_view_anywhere_needs_no_inferred_whole(self):
        """One photograph sees the bowl plainly: that wins, and nothing is inferred."""
        self.det["img001"][2].update(occlusion="heavy", occluded=True, visible="the rim",
                                     whole_description="a bowl, assumed")
        self.write_inputs()
        _, _, out = self.build()
        with open(out, encoding="utf-8") as f:
            bowl = next(n for n in json.load(f)["nodes"] if n["global_id"] == "g003")
        self.assertEqual(bowl["occlusion"], "none")
        self.assertNotIn("inferred_whole", bowl)

    def test_a_low_confidence_wide_reading_the_close_up_never_saw_is_unconfirmed(self):
        """img002 is a close-up of the table in img001. img001's 'round tin' sits there, named
        with low confidence, and nothing in img002 matched it: probably a misreading."""
        self.det["img001"].append(detection("img001-5", "round tin", [0.45, 0.42, 0.48, 0.46],
                                            id_confidence="low"))
        self.det["img001"].append(detection("img001-6", "mug", [0.3, 0.42, 0.33, 0.46]))
        self.struct["img001"] += [("img001-5", "img001-2", "on-top-of"),
                                  ("img001-6", "img001-2", "on-top-of")]
        self.write_inputs()
        for gid, local in (("g005", "img001-5"), ("g006", "img001-6")):
            self.matches["objects"].append({"global_id": gid, "label": "x",
                                            "members": [{"image_id": "img001", "local_id": local}]})
        registration = self.path("registration.json", {"pairs": [
            {"a": "img001", "b": "img002", "relation": "close-up", "closer": "img002",
             "region": [0.2, 0.3, 0.8, 0.9]}]})
        code, report, out = self.build(extra=("--registration", registration))
        self.assertEqual(code, 0, report["problems"])
        self.assertEqual(report["unconfirmed"], 1)
        with open(out, encoding="utf-8") as f:
            by_id = {n["global_id"]: n for n in json.load(f)["nodes"]}
        self.assertEqual(by_id["g005"]["unconfirmed"]["closer_view"], "img002")
        self.assertNotIn("unconfirmed", by_id["g006"])      # named with confidence: kept as is

    def test_a_parent_disagreement_is_recorded_not_hidden(self):
        self.struct["img002"] = [("img002-1", None, None),
                                 ("img002-2", "img002-1", "on-top-of"),
                                 ("img002-3", "img002-1", "on-top-of")]
        self.write_inputs()
        code, report, out = self.build()
        self.assertEqual(code, 0)
        self.assertEqual(report["parent_conflicts"], 1)
        with open(out, encoding="utf-8") as f:
            graph = json.load(f)
        conflict = graph["parent_conflicts"][0]
        self.assertEqual(conflict["global_id"], "g003")
        self.assertTrue(conflict["others"])

    def test_a_more_specific_parent_beats_a_shallower_one(self):
        """"On the dish, which is on the tray" and "on the tray" do not disagree."""
        self.struct["img002"] = [("img002-1", None, None),
                                 ("img002-2", "img002-1", "on-top-of"),
                                 ("img002-3", "img002-1", "on-top-of")]
        self.write_inputs()
        _, _, out = self.build()
        with open(out, encoding="utf-8") as f:
            graph = json.load(f)
        bowl = next(n for n in graph["nodes"] if n["global_id"] == "g003")
        self.assertEqual(bowl["parent"], "g002", "the deeper answer is the same claim, with more detail")
        self.assertEqual(bowl["parent_source"], "img001")

    def test_the_better_view_wins_a_real_parent_disagreement(self):
        """Two parents that are siblings: neither reading contains the other."""
        self.add_rival_surface()
        self.struct["img001"] = [("img001-1", None, None),
                                 ("img001-2", "img001-1", "on-top-of"),
                                 ("img001-4", "img001-1", "on-top-of"),
                                 ("img001-3", "img001-2", "on-top-of")]
        self.struct["img002"] = [("img002-1", None, None),
                                 ("img002-2", "img002-1", "on-top-of"),
                                 ("img002-4", "img002-1", "on-top-of"),
                                 ("img002-3", "img002-4", "on-top-of")]
        self.write_inputs()
        _, _, out = self.build()
        with open(out, encoding="utf-8") as f:
            graph = json.load(f)
        bowl = next(n for n in graph["nodes"] if n["global_id"] == "g003")
        self.assertEqual(bowl["parent"], "g004")        # img002 has the bigger boxes
        self.assertEqual(bowl["parent_source"], "img002")
        self.assertTrue(any(c["global_id"] == "g003" for c in graph["parent_conflicts"]))

    def test_a_view_that_saw_the_support_beats_a_bigger_view_that_inferred_it(self):
        """A run put a worktop on the floor: the bigger view could not see the units
        under it and inferred the floor, while the smaller view observed them."""
        self.add_rival_surface()
        # img002 has the bigger boxes, so it wins on frame share — but it inferred.
        self.struct["img001"] = [("img001-1", None, None),
                                 ("img001-2", "img001-1", "on-top-of"),
                                 ("img001-4", "img001-1", "on-top-of"),
                                 ("img001-3", "img001-2", "on-top-of", False)]
        self.struct["img002"] = [("img002-1", None, None),
                                 ("img002-2", "img002-1", "on-top-of"),
                                 ("img002-4", "img002-1", "on-top-of"),
                                 ("img002-3", "img002-4", "on-top-of", True)]
        self.write_inputs()
        _, _, out = self.build()
        with open(out, encoding="utf-8") as f:
            graph = json.load(f)
        bowl = next(n for n in graph["nodes"] if n["global_id"] == "g003")
        self.assertEqual(bowl["parent"], "g002", "the observed support should win")
        self.assertEqual(bowl["parent_source"], "img001")
        self.assertFalse(bowl["support_inferred"])
        conflict = next(c for c in graph["parent_conflicts"] if c["global_id"] == "g003")
        self.assertIn("saw the support", conflict["chose"]["because"])

    def test_frame_share_still_decides_when_every_view_inferred(self):
        self.add_rival_surface()
        self.struct["img001"] = [("img001-1", None, None),
                                 ("img001-2", "img001-1", "on-top-of"),
                                 ("img001-4", "img001-1", "on-top-of"),
                                 ("img001-3", "img001-2", "on-top-of", True)]
        self.struct["img002"] = [("img002-1", None, None),
                                 ("img002-2", "img002-1", "on-top-of"),
                                 ("img002-4", "img002-1", "on-top-of"),
                                 ("img002-3", "img002-4", "on-top-of", True)]
        self.write_inputs()
        _, _, out = self.build()
        with open(out, encoding="utf-8") as f:
            graph = json.load(f)
        bowl = next(n for n in graph["nodes"] if n["global_id"] == "g003")
        self.assertEqual(bowl["parent_source"], "img002")   # the bigger view
        conflict = next(c for c in graph["parent_conflicts"] if c["global_id"] == "g003")
        self.assertIn("every view inferred", conflict["chose"]["because"])

    def test_exit_1_when_a_parent_is_in_no_global_object(self):
        matches = copy.deepcopy(self.matches)
        matches["objects"] = [o for o in matches["objects"] if o["global_id"] != "g002"]
        code, report, _ = self.build(matches)
        self.assertEqual(code, 1)
        self.assertTrue(any("is in no global object" in p for p in report["problems"]))

    def test_the_same_group_seen_in_two_images_becomes_one(self):
        """Two images rarely list identical membership for one area."""
        self.areas["img001"] = [{"area_id": "a1", "label": "Dining area",
                                 "members": ["img001-2", "img001-3"]}]
        self.areas["img002"] = [{"area_id": "a1", "label": "dining area",
                                 "members": ["img002-2", "img002-3", "img002-1"]}]
        self.write_inputs()
        code, report, out = self.build()
        self.assertEqual(code, 0)
        self.assertEqual(report["areas"], 1)
        with open(out, encoding="utf-8") as f:
            area = json.load(f)["areas"][0]
        self.assertEqual(area["members"], ["g001", "g002", "g003"])
        self.assertEqual(area["seen_in"], ["img001", "img002"])

    def test_groups_with_the_same_label_but_no_shared_member_stay_apart(self):
        self.clusters["img001"] = [{"cluster_id": "c1", "label": "mats",
                                    "members": ["img001-1", "img001-2"], "kind": "instances"}]
        self.clusters["img002"] = [{"cluster_id": "c1", "label": "mats",
                                    "members": ["img002-3"], "kind": "instances"}]
        self.write_inputs()
        code, report, _ = self.build()
        self.assertEqual(code, 0)
        self.assertEqual(report["clusters"], 1)

    def test_an_unresolved_set_becomes_an_identity_group(self):
        """Three nodes standing for two things, so the ontology can count the room."""
        # The bowls were not merged, so the three candidates are three separate nodes.
        matches = copy.deepcopy(self.matches)
        matches["objects"][2]["members"] = [{"image_id": "img001", "local_id": "img001-3"}]
        del matches["objects"][2]["evidence"], matches["objects"][2]["confidence"]
        matches["objects"].append({"global_id": "g004", "label": "bowl",
                                   "members": [{"image_id": "img002", "local_id": "img002-3"}]})
        matches["unresolved"] = [{
            "issue_id": "u001", "label": "which bowl",
            "candidates": [{"image_id": "img001", "local_id": "img001-2"},
                           {"image_id": "img001", "local_id": "img001-3"},
                           {"image_id": "img002", "local_id": "img002-3"}],
            "for": ["x"], "against": ["y"], "decision": "kept separate",
            "distinct_objects": 2, "distinct_basis": "two are in one photograph"}]
        code, report, out = self.build(matches)
        self.assertEqual(code, 0, report["problems"])
        self.assertEqual(report["identity_groups"], 1)
        self.assertEqual(report["objects_that_may_be_duplicates"], 1)
        with open(out, encoding="utf-8") as f:
            group = json.load(f)["identity_groups"][0]
        self.assertEqual(group["members"], ["g002", "g003", "g004"])
        self.assertEqual(group["distinct"], 2)
        self.assertEqual(group["at_least"], 2)
        self.assertEqual(group["at_most"], 3)
        self.assertEqual(group["from"], "u001")

    def test_candidates_already_merged_leave_no_slack(self):
        """Two candidates that are the same global object are not two things."""
        matches = copy.deepcopy(self.matches)
        matches["unresolved"] = [{
            "issue_id": "u001", "label": "which bowl",
            "candidates": [{"image_id": "img001", "local_id": "img001-3"},
                           {"image_id": "img002", "local_id": "img002-3"},
                           {"image_id": "img001", "local_id": "img001-2"}],
            "for": ["x"], "against": ["y"], "decision": "kept separate",
            "distinct_objects": 2, "distinct_basis": "two are in one photograph"}]
        code, report, _ = self.build(matches)
        self.assertEqual(code, 0)
        self.assertEqual(report["objects_that_may_be_duplicates"], 0)

    def test_an_unresolved_set_without_a_count_falls_back_to_the_floor(self):
        matches = copy.deepcopy(self.matches)
        matches["unresolved"] = [{
            "issue_id": "u001", "label": "which bowl",
            "candidates": [{"image_id": "img001", "local_id": "img001-2"},
                           {"image_id": "img002", "local_id": "img002-3"}],
            "for": ["x"], "against": ["y"], "decision": "kept separate"}]
        _, _, out = self.build(matches)
        with open(out, encoding="utf-8") as f:
            group = json.load(f)["identity_groups"][0]
        self.assertEqual(group["distinct"], 1)
        self.assertIn("assumed", group["basis"])

    def test_refuses_to_overwrite_without_force(self):
        out = os.path.join(self.tmp, "graph.json")
        args = ("--matches", self.path("matches.json", self.matches),
                "--structures", self.structures, "--detections", self.detections, "--out", out)
        code, _, _ = run(os.path.join(SCRIPTS, "apply_matches.py"), *args)
        self.assertEqual(code, 0)
        code, _, err = run(os.path.join(SCRIPTS, "apply_matches.py"), *args)
        self.assertEqual(code, 1)
        self.assertIn("--force", err)

    def test_exit_2_on_missing_inputs(self):
        code, _, err = run(os.path.join(SCRIPTS, "apply_matches.py"),
                           "--matches", os.path.join(self.tmp, "nope.json"),
                           "--structures", self.structures, "--detections", self.detections)
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())


class ScoreViewsTests(Fixture):
    def score(self, graph_path):
        return run_json(os.path.join(SCRIPTS, "score_views.py"), graph_path)

    def test_help_works(self):
        code, out, _ = run(os.path.join(SCRIPTS, "score_views.py"), "--help")
        self.assertEqual(code, 0)
        self.assertIn("--out", out)

    def test_the_bigger_view_wins(self):
        _, _, out = self.build()
        code, scores, _ = self.score(out)
        self.assertEqual(code, 0)
        bowl = next(o for o in scores["objects"] if o["global_id"] == "g003")
        self.assertEqual(bowl["best_view"], "img002")
        self.assertGreater(bowl["views"][0]["score"], bowl["views"][1]["score"])

    def test_occlusion_can_lose_a_bigger_view_the_top_spot(self):
        self.det["img002"][2]["occluded"] = True
        self.det["img002"][2]["bbox"] = [0.3, 0.3, 0.42, 0.42]
        self.write_inputs()
        _, _, out = self.build()
        _, scores, _ = self.score(out)
        bowl = next(o for o in scores["objects"] if o["global_id"] == "g003")
        self.assertEqual(bowl["best_view"], "img001")
        self.assertTrue(any("hidden" in p for v in bowl["views"] for p in v["penalties"]))

    def test_truncation_and_low_id_confidence_are_penalised(self):
        self.det["img002"][2]["truncated"] = ["left", "top"]
        self.det["img002"][2]["id_confidence"] = "low"
        self.write_inputs()
        _, _, out = self.build()
        _, scores, _ = self.score(out)
        bowl = next(o for o in scores["objects"] if o["global_id"] == "g003")
        view = next(v for v in bowl["views"] if v["image_id"] == "img002")
        self.assertLess(view["score"], view["frame_share"])
        self.assertTrue(any("runs off" in p for p in view["penalties"]))
        self.assertTrue(any("sure what it was" in p for p in view["penalties"]))

    def test_a_close_call_is_not_decisive(self):
        self.det["img002"][2]["bbox"] = [0.4, 0.4, 0.505, 0.505]
        self.write_inputs()
        _, _, out = self.build()
        _, scores, _ = self.score(out)
        bowl = next(o for o in scores["objects"] if o["global_id"] == "g003")
        self.assertFalse(bowl["decisive"])

    def test_a_single_view_is_decisive(self):
        matches = copy.deepcopy(self.matches)
        matches["objects"][2]["members"] = [{"image_id": "img001", "local_id": "img001-3"}]
        matches["objects"].append({"global_id": "g004", "label": "bowl",
                                   "members": [{"image_id": "img002", "local_id": "img002-3"}]})
        _, _, out = self.build(matches)
        _, scores, _ = self.score(out)
        bowl = next(o for o in scores["objects"] if o["global_id"] == "g003")
        self.assertTrue(bowl["decisive"])

    def test_exit_2_on_a_missing_file(self):
        code, _, err = run(os.path.join(SCRIPTS, "score_views.py"),
                           os.path.join(self.tmp, "nope.json"))
        self.assertEqual(code, 2)
        self.assertIn("no such file", err)


class ValidateGraphTests(Fixture):
    def validate(self, graph, *extra):
        return run_json(os.path.join(SCRIPTS, "validate_graph.py"),
                        self.path("graph.json", graph), *extra)

    def graph(self):
        _, _, out = self.build()
        with open(out, encoding="utf-8") as f:
            return json.load(f)

    def ontology(self, **changes):
        out = {"schema": "scene-decompose/ontology@1", "total_objects": 3, "categories": [
            {"label": "room", "count": 1, "members": ["g001"]},
            {"label": "things", "count": 2, "members": ["g002", "g003"]}]}
        out.update(changes)
        return out

    def test_help_works(self):
        code, out, _ = run(os.path.join(SCRIPTS, "validate_graph.py"), "--help")
        self.assertEqual(code, 0)
        self.assertIn("--ontology", out)

    def test_a_built_graph_passes(self):
        code, report, _ = self.validate(self.graph())
        self.assertEqual(code, 0, report["errors"])
        self.assertEqual(report["nodes"], 3)
        self.assertEqual(report["anchors"], ["g001"])

    def test_a_cycle_is_caught(self):
        graph = self.graph()
        by_id = {n["global_id"]: n for n in graph["nodes"]}
        by_id["g001"]["parent"] = "g003"
        by_id["g001"]["relation"] = "on-top-of"
        code, report, _ = self.validate(graph)
        self.assertEqual(code, 1)
        self.assertTrue(any("cycle" in e for e in report["errors"]))

    def test_a_parent_that_is_not_a_node_is_caught(self):
        graph = self.graph()
        graph["nodes"][2]["parent"] = "g999"
        code, report, _ = self.validate(graph)
        self.assertEqual(code, 1)
        self.assertTrue(any("is not a node" in e for e in report["errors"]))

    def test_two_views_in_one_image_are_caught(self):
        graph = self.graph()
        node = graph["nodes"][2]
        node["views"] = node["views"] + [dict(node["views"][0])]
        node["seen_in"] = 3
        code, report, _ = self.validate(graph)
        self.assertEqual(code, 1)
        self.assertTrue(any("two views in image" in e for e in report["errors"]))

    def test_a_bbox_outside_the_range_is_caught(self):
        graph = self.graph()
        graph["nodes"][0]["views"][0]["bbox"] = [0, 0, 1200, 800]
        code, report, _ = self.validate(graph)
        self.assertEqual(code, 1)
        self.assertTrue(any("outside 0-1" in e for e in report["errors"]))

    def test_seen_in_must_match_the_views(self):
        graph = self.graph()
        graph["nodes"][0]["seen_in"] = 7
        code, report, _ = self.validate(graph)
        self.assertEqual(code, 1)
        self.assertTrue(any("seen_in says 7" in e for e in report["errors"]))

    def test_a_view_naming_an_image_outside_the_manifest_is_caught(self):
        manifest = self.path("manifest.json", {"images": [{"image_id": "img001"}]})
        code, report, _ = self.validate(self.graph(), "--manifest", manifest)
        self.assertEqual(code, 1)
        self.assertTrue(any("not in the manifest" in e for e in report["errors"]))

    def test_an_ontology_that_reconciles_passes(self):
        ontology = self.path("ontology.json", self.ontology())
        code, report, _ = self.validate(self.graph(), "--ontology", ontology)
        self.assertEqual(code, 0, report["errors"])

    def test_an_object_in_no_category_is_caught(self):
        ontology = self.path("ontology.json", self.ontology(categories=[
            {"label": "room", "count": 1, "members": ["g001"]}]))
        code, report, _ = self.validate(self.graph(), "--ontology", ontology)
        self.assertEqual(code, 1)
        self.assertTrue(any("in no ontology category" in e for e in report["errors"]))

    def test_an_object_in_two_categories_is_caught(self):
        ontology = self.path("ontology.json", self.ontology(categories=[
            {"label": "room", "count": 2, "members": ["g001", "g002"]},
            {"label": "things", "count": 2, "members": ["g002", "g003"]}]))
        code, report, _ = self.validate(self.graph(), "--ontology", ontology)
        self.assertEqual(code, 1)
        self.assertTrue(any("sits in exactly one category" in e for e in report["errors"]))

    def test_a_count_that_disagrees_with_its_members_is_caught(self):
        ontology = self.path("ontology.json", self.ontology(categories=[
            {"label": "room", "count": 1, "members": ["g001"]},
            {"label": "things", "count": 9, "members": ["g002", "g003"]}]))
        code, report, _ = self.validate(self.graph(), "--ontology", ontology)
        self.assertEqual(code, 1)
        self.assertTrue(any("count says 9" in e for e in report["errors"]))

    def graph_with_group(self, distinct=2):
        graph = self.graph()
        graph["identity_groups"] = [{
            "group_id": "ig001", "label": "which thing",
            "members": ["g002", "g003"], "distinct": distinct,
            "at_least": 1, "at_most": 2, "basis": "they may be the same thing"}]
        return graph

    def test_a_category_counts_physical_things_not_nodes(self):
        """The bug that reported three chairs in a room with two."""
        graph = self.graph_with_group(distinct=1)
        ontology = self.path("ontology.json", self.ontology(total_objects=2, categories=[
            {"label": "room", "count": 1, "members": ["g001"]},
            {"label": "things", "count": 1, "listed": 2, "members": ["g002", "g003"]}]))
        code, report, _ = self.validate(graph, "--ontology", ontology)
        self.assertEqual(code, 0, report["errors"])
        self.assertEqual(report["distinct_objects"], 2)

    def test_a_category_that_counts_nodes_is_rejected(self):
        graph = self.graph_with_group(distinct=1)
        ontology = self.path("ontology.json", self.ontology(total_objects=3, categories=[
            {"label": "room", "count": 1, "members": ["g001"]},
            {"label": "things", "count": 2, "members": ["g002", "g003"]}]))
        code, report, _ = self.validate(graph, "--ontology", ontology)
        self.assertEqual(code, 1)
        self.assertTrue(any("may be another member seen again, so it should be 1" in e
                            for e in report["errors"]))

    def test_total_objects_counts_physical_things(self):
        graph = self.graph_with_group(distinct=1)
        ontology = self.path("ontology.json", self.ontology(total_objects=3, categories=[
            {"label": "room", "count": 1, "members": ["g001"]},
            {"label": "things", "count": 1, "members": ["g002", "g003"]}]))
        code, report, _ = self.validate(graph, "--ontology", ontology)
        self.assertEqual(code, 1)
        self.assertTrue(any("total_objects says 3" in e for e in report["errors"]))

    def test_an_identity_group_split_across_categories_is_rejected(self):
        graph = self.graph_with_group(distinct=1)
        ontology = self.path("ontology.json", self.ontology(total_objects=2, categories=[
            {"label": "room", "count": 2, "members": ["g001", "g002"]},
            {"label": "things", "count": 1, "members": ["g003"]}]))
        code, report, _ = self.validate(graph, "--ontology", ontology)
        self.assertEqual(code, 1)
        self.assertTrue(any("split across categories" in e for e in report["errors"]))

    def test_an_identity_group_needs_a_basis_and_a_sane_distinct(self):
        graph = self.graph_with_group()
        graph["identity_groups"][0]["basis"] = "  "
        code, report, _ = self.validate(graph)
        self.assertEqual(code, 1)
        self.assertTrue(any("needs a 'basis'" in e for e in report["errors"]))

        graph = self.graph_with_group(distinct=5)
        code, report, _ = self.validate(graph)
        self.assertEqual(code, 1)
        self.assertTrue(any("not between 1 and the 2 members" in e for e in report["errors"]))

    def test_an_object_cannot_be_in_two_identity_groups(self):
        graph = self.graph_with_group()
        graph["identity_groups"].append({
            "group_id": "ig002", "label": "again", "members": ["g003", "g001"],
            "distinct": 1, "basis": "x"})
        code, report, _ = self.validate(graph)
        self.assertEqual(code, 1)
        self.assertTrue(any("at most one identity group" in e for e in report["errors"]))


    def test_exit_2_on_a_missing_file(self):
        code, _, err = run(os.path.join(SCRIPTS, "validate_graph.py"),
                           os.path.join(self.tmp, "nope.json"))
        self.assertEqual(code, 2)
        self.assertIn("no such file", err)




if __name__ == "__main__":
    unittest.main()
