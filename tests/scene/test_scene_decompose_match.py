"""Tests for the scene-decompose-match scripts."""
import copy
import glob
import json
import os
import shutil
import tempfile
import unittest

from helpers import SKILL as SKILL_DIR, SCRIPTS as SCRIPTS_DIR, ROOT, run, run_json

SKILL = SKILL_DIR
SCRIPTS = SCRIPTS_DIR
EXAMPLE = os.path.join(SKILL, "examples", "example.json")

EVIDENCE = ["registration: img003 is a close-up of img001's table region",
            "matched parent: both hang off the matched table"]

GOOD = {
    "schema": "scene-decompose/matches@1",
    "images": ["img001", "img003"],
    "objects": [
        {"global_id": "g001", "label": "dining table",
         "members": [{"image_id": "img001", "local_id": "img001-001"},
                     {"image_id": "img003", "local_id": "img003-001"}],
         "evidence": EVIDENCE, "confidence": "high"},
        {"global_id": "g002", "label": "laptop",
         "members": [{"image_id": "img001", "local_id": "img001-002"},
                     {"image_id": "img003", "local_id": "img003-002"}],
         "evidence": EVIDENCE, "confidence": "medium"},
        {"global_id": "g003", "label": "backpack",
         "members": [{"image_id": "img003", "local_id": "img003-003"}]},
    ],
    "unresolved": [],
}

STRUCTURES = {
    "img001": [("img001-001", None), ("img001-002", "img001-001")],
    "img003": [("img003-001", None), ("img003-002", "img003-001"), ("img003-003", None)],
}


class CheckMatchesTests(unittest.TestCase):
    def setUp(self):
        self.script = os.path.join(SCRIPTS, "check_matches.py")
        self.tmp = tempfile.mkdtemp()
        self.structures = os.path.join(self.tmp, "structure")
        os.makedirs(self.structures)
        for image_id, nodes in STRUCTURES.items():
            with open(os.path.join(self.structures, f"{image_id}.json"), "w", encoding="utf-8") as f:
                json.dump({"image_id": image_id,
                           "nodes": [{"local_id": i, "parent": p} for i, p in nodes]}, f)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, data, name="matches.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def doc(self, **changes):
        out = copy.deepcopy(GOOD)
        out.update(changes)
        return out

    def test_help_works(self):
        code, out, _ = run(self.script, "--help")
        self.assertEqual(code, 0)
        self.assertIn("--structures", out)

    def test_a_clean_file_passes(self):
        code, report, _ = run_json(self.script, self.write(GOOD), "--structures", self.structures)
        self.assertEqual(code, 0, report)
        self.assertEqual(report["matched_across_images"], 2)
        self.assertEqual(report["seen_once"], 1)

    def test_two_objects_from_one_image_cannot_be_one_identity(self):
        """The rule that stops two lookalikes in one photograph becoming one thing."""
        doc = self.doc(objects=[{
            "global_id": "g001", "label": "chair",
            "members": [{"image_id": "img001", "local_id": "img001-001"},
                        {"image_id": "img001", "local_id": "img001-002"}],
            "evidence": EVIDENCE, "confidence": "high"}])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("one physical thing is in a photograph once" in e
                            for e in report["errors"]))

    def test_a_merge_needs_two_lines_of_evidence(self):
        doc = copy.deepcopy(GOOD)
        doc["objects"][0]["evidence"] = ["they are both chairs"]
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("at least 2 lines of evidence" in e for e in report["errors"]))

    def test_a_merge_needs_a_confidence(self):
        doc = copy.deepcopy(GOOD)
        del doc["objects"][0]["confidence"]
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("confidence must be one of" in e for e in report["errors"]))

    def test_an_object_seen_once_needs_no_evidence(self):
        code, report, _ = run_json(self.script, self.write(GOOD), "--structures", self.structures)
        self.assertEqual(code, 0, report["errors"])

    def test_an_object_in_two_global_objects_is_caught(self):
        doc = copy.deepcopy(GOOD)
        doc["objects"][1]["members"][0]["local_id"] = "img001-001"
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("is a member of both" in e for e in report["errors"]))

    def test_an_object_left_out_entirely_is_caught(self):
        doc = copy.deepcopy(GOOD)
        doc["objects"] = doc["objects"][:2]
        code, report, _ = run_json(self.script, self.write(doc), "--structures", self.structures)
        self.assertEqual(code, 1)
        self.assertTrue(any("in no global object" in e for e in report["errors"]))

    def test_a_member_not_in_any_structure_is_caught(self):
        doc = copy.deepcopy(GOOD)
        doc["objects"][2]["members"][0]["local_id"] = "img003-999"
        code, report, _ = run_json(self.script, self.write(doc), "--structures", self.structures)
        self.assertEqual(code, 1)
        self.assertTrue(any("not in any structure file" in e for e in report["errors"]))

    def test_a_member_attributed_to_the_wrong_image_is_caught(self):
        doc = copy.deepcopy(GOOD)
        doc["objects"][2]["members"][0]["image_id"] = "img001"
        code, report, _ = run_json(self.script, self.write(doc), "--structures", self.structures)
        self.assertEqual(code, 1)
        self.assertTrue(any("is in image 'img003'" in e for e in report["errors"]))

    def test_a_child_merged_without_its_parent_is_warned_about(self):
        """Matching bottom-up: the laptop is merged but the table it sits on is not."""
        doc = self.doc(objects=[
            {"global_id": "g001", "label": "laptop",
             "members": [{"image_id": "img001", "local_id": "img001-002"},
                         {"image_id": "img003", "local_id": "img003-002"}],
             "evidence": EVIDENCE, "confidence": "high"},
            {"global_id": "g002", "label": "table",
             "members": [{"image_id": "img001", "local_id": "img001-001"}]},
            {"global_id": "g003", "label": "table",
             "members": [{"image_id": "img003", "local_id": "img003-001"}]},
            {"global_id": "g004", "label": "backpack",
             "members": [{"image_id": "img003", "local_id": "img003-003"}]},
        ])
        code, report, _ = run_json(self.script, self.write(doc), "--structures", self.structures)
        self.assertEqual(code, 0)
        self.assertTrue(any("parents were not matched to each other" in w
                            for w in report["warnings"]))

    def test_nothing_matched_across_overlapping_images_is_warned_about(self):
        doc = self.doc(objects=[
            {"global_id": "g001", "label": "a", "members": [{"image_id": "img001", "local_id": "img001-001"}]},
            {"global_id": "g002", "label": "b", "members": [{"image_id": "img003", "local_id": "img003-001"}]},
        ])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 0)
        self.assertTrue(any("no object was matched across images" in w for w in report["warnings"]))

    def correction(self, **changes):
        out = {
            "correction_id": "c001",
            "target": {"image_id": "img001", "local_id": "img001-002"},
            "stage": "scene-decompose-detect",
            "problem": "named one object from a shape forty pixels tall",
            "better_view": {"image_id": "img003", "local_id": "img003-002"},
            "shows": "a caddy holding two shakers, close and unoccluded",
        }
        out.update(changes)
        return out

    def test_a_correction_passes(self):
        doc = self.doc(corrections=[self.correction()])
        code, report, _ = run_json(self.script, self.write(doc), "--structures", self.structures)
        self.assertEqual(code, 0, report["errors"])
        self.assertEqual(report["corrections"], 1)

    def test_a_correction_must_name_a_stage_that_owns_the_file(self):
        doc = self.doc(corrections=[self.correction(stage="scene-decompose-match")])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("stage must be one of" in e for e in report["errors"]))

    def test_a_correction_needs_a_problem_and_what_the_better_view_shows(self):
        for field in ("problem", "shows"):
            doc = self.doc(corrections=[self.correction(**{field: "  "})])
            code, report, _ = run_json(self.script, self.write(doc))
            self.assertEqual(code, 1, field)
            self.assertTrue(any(f"'{field}' must say something" in e for e in report["errors"]))

    def test_a_correction_cannot_prefer_a_view_in_the_same_image(self):
        """One view beats another only across images."""
        doc = self.doc(corrections=[self.correction(
            better_view={"image_id": "img001", "local_id": "img001-001"})])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("no view beats the other" in e for e in report["errors"]))

    def test_a_correction_never_removes_its_target_from_the_graph(self):
        doc = self.doc(corrections=[self.correction(
            target={"image_id": "img001", "local_id": "img001-404"})])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("never removes an object from the graph" in e
                            for e in report["errors"]))

    def test_duplicate_correction_ids_are_rejected(self):
        doc = self.doc(corrections=[self.correction(), self.correction()])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("used more than once" in e for e in report["errors"]))


    def test_an_unresolved_set_needs_an_against(self):
        doc = copy.deepcopy(GOOD)
        doc["unresolved"] = [{"issue_id": "u001", "label": "which chair",
                              "candidates": [{"image_id": "img001", "local_id": "img001-001"},
                                             {"image_id": "img003", "local_id": "img003-001"}],
                              "for": ["same design"], "against": [], "decision": "kept separate"}]
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("should have been merged" in e for e in report["errors"]))

    def test_an_unresolved_set_needs_two_candidates(self):
        doc = copy.deepcopy(GOOD)
        doc["unresolved"] = [{"issue_id": "u001", "label": "which chair",
                              "candidates": [{"image_id": "img001", "local_id": "img001-001"}],
                              "for": ["x"], "against": ["y"], "decision": "kept separate"}]
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("two or more candidates" in e for e in report["errors"]))

    def test_an_unresolved_candidate_must_still_be_a_global_object(self):
        """Being unresolved never removes an object from the graph."""
        doc = copy.deepcopy(GOOD)
        doc["unresolved"] = [{"issue_id": "u001", "label": "which chair",
                              "candidates": [{"image_id": "img001", "local_id": "img001-001"},
                                             {"image_id": "img001", "local_id": "img001-404"}],
                              "for": ["x"], "against": ["y"], "decision": "kept separate"}]
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("not in any global object" in e for e in report["errors"]))

    def unresolved(self, **changes):
        out = {"issue_id": "u001", "label": "which chair",
               "candidates": [{"image_id": "img001", "local_id": "img001-001"},
                              {"image_id": "img001", "local_id": "img001-002"},
                              {"image_id": "img003", "local_id": "img003-001"}],
               "for": ["same design"], "against": ["two match it equally"],
               "decision": "kept separate",
               "distinct_objects": 2,
               "distinct_basis": "two are in one photograph, so they are certainly different"}
        out.update(changes)
        return out

    def test_an_unresolved_set_spanning_images_must_say_how_many_things_it_holds(self):
        """Refusing to say which is which is not a reason to leave the count wrong."""
        issue = self.unresolved()
        del issue["distinct_objects"]
        doc = copy.deepcopy(GOOD)
        doc["unresolved"] = [issue]
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("needs 'distinct_objects'" in e for e in report["errors"]))

    def test_distinct_objects_passes_when_it_is_in_range(self):
        doc = copy.deepcopy(GOOD)
        doc["unresolved"] = [self.unresolved()]
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 0, report["errors"])

    def test_distinct_objects_cannot_be_below_the_candidates_in_one_image(self):
        """Two candidates in one photograph are certainly two different things."""
        doc = copy.deepcopy(GOOD)
        doc["unresolved"] = [self.unresolved(distinct_objects=1)]
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("between 2 and 3" in e for e in report["errors"]))

    def test_distinct_objects_cannot_exceed_the_candidates(self):
        doc = copy.deepcopy(GOOD)
        doc["unresolved"] = [self.unresolved(distinct_objects=4)]
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("between 2 and 3" in e for e in report["errors"]))

    def test_distinct_objects_needs_a_basis(self):
        doc = copy.deepcopy(GOOD)
        doc["unresolved"] = [self.unresolved(distinct_basis="  ")]
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("distinct_basis" in e for e in report["errors"]))

    def test_candidates_all_in_one_image_need_no_count(self):
        """They are already known to be different objects."""
        issue = self.unresolved(candidates=[{"image_id": "img001", "local_id": "img001-001"},
                                            {"image_id": "img001", "local_id": "img001-002"}])
        del issue["distinct_objects"]
        del issue["distinct_basis"]
        doc = copy.deepcopy(GOOD)
        doc["unresolved"] = [issue]
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 0, report["errors"])

    def test_a_bad_decision_is_rejected(self):
        doc = copy.deepcopy(GOOD)
        doc["unresolved"] = [{"issue_id": "u001", "label": "which chair",
                              "candidates": [{"image_id": "img001", "local_id": "img001-001"},
                                             {"image_id": "img003", "local_id": "img003-001"}],
                              "for": ["x"], "against": ["y"], "decision": "probably fine"}]
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("decision must be one of" in e for e in report["errors"]))

    def test_duplicate_global_ids_are_rejected(self):
        doc = copy.deepcopy(GOOD)
        doc["objects"][1]["global_id"] = "g001"
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("used more than once" in e for e in report["errors"]))

    def test_exit_2_on_a_missing_or_broken_file(self):
        code, _, err = run(self.script, os.path.join(self.tmp, "nope.json"))
        self.assertEqual(code, 2)
        self.assertIn("no such file", err)
        broken = os.path.join(self.tmp, "broken.json")
        with open(broken, "w", encoding="utf-8") as f:
            f.write("{nope")
        code, _, err = run(self.script, broken)
        self.assertEqual(code, 2)
        self.assertIn("not valid JSON", err)

    def test_exit_2_when_the_structures_folder_is_empty(self):
        empty = os.path.join(self.tmp, "empty")
        os.makedirs(empty)
        code, _, err = run(self.script, self.write(GOOD), "--structures", empty)
        self.assertEqual(code, 2)
        self.assertIn("no structure files", err)







if __name__ == "__main__":
    unittest.main()
