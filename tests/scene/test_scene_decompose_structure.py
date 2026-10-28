"""Tests for the scene-decompose-structure scripts."""
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

GOOD = {
    "schema": "scene-decompose/structure@1",
    "image_id": "img003",
    "anchors": ["a"],
    "nodes": [
        {"local_id": "a", "parent": None, "relation": None, "note": "anchor"},
        {"local_id": "table", "parent": "a", "relation": "on-top-of"},
        {"local_id": "mat", "parent": "table", "relation": "on-top-of"},
        {"local_id": "bowl", "parent": "mat", "relation": "on-top-of"},
        {"local_id": "spoon", "parent": "bowl", "relation": "inside"},
    ],
    "clusters": [],
    "areas": [],
}


class CheckStructureTests(unittest.TestCase):
    def setUp(self):
        self.script = os.path.join(SCRIPTS, "check_structure.py")
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, data, name="structure.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def doc(self, **changes):
        out = copy.deepcopy(GOOD)
        out.update(changes)
        return out

    def detections(self, ids):
        return self.write({"objects": [{"local_id": i} for i in ids]}, "detections.json")

    def test_help_works(self):
        code, out, _ = run(self.script, "--help")
        self.assertEqual(code, 0)
        self.assertIn("--detections", out)

    def test_a_clean_cascade_passes(self):
        code, report, _ = run_json(self.script, self.write(GOOD))
        self.assertEqual(code, 0, report)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["depth"], 5)
        self.assertEqual(report["anchors"], ["a"])

    def test_a_cycle_is_caught(self):
        doc = self.doc(nodes=[
            {"local_id": "a", "parent": None, "relation": None},
            {"local_id": "x", "parent": "y", "relation": "on-top-of"},
            {"local_id": "y", "parent": "x", "relation": "on-top-of"},
        ])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("cycle" in e for e in report["errors"]))
        self.assertIsNone(report["depth"])

    def test_an_object_cannot_be_its_own_parent(self):
        doc = self.doc(nodes=[
            {"local_id": "a", "parent": None, "relation": None},
            {"local_id": "x", "parent": "x", "relation": "on-top-of"},
        ])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("its own parent" in e for e in report["errors"]))

    def test_a_parent_that_is_not_a_node_is_caught(self):
        doc = self.doc(nodes=GOOD["nodes"] + [
            {"local_id": "ghost", "parent": "nowhere", "relation": "on-top-of"}])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("not a node" in e for e in report["errors"]))

    def test_a_relation_outside_the_vocabulary_is_rejected(self):
        doc = self.doc(nodes=[
            {"local_id": "a", "parent": None, "relation": None},
            {"local_id": "x", "parent": "a", "relation": "near"},
        ])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("vocabulary" in e for e in report["errors"]))

    def test_adjacent_to_is_not_in_the_hierarchy_vocabulary(self):
        doc = self.doc(nodes=[
            {"local_id": "a", "parent": None, "relation": None},
            {"local_id": "x", "parent": "a", "relation": "adjacent-to"},
        ])
        code, _, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)

    def test_an_anchor_may_not_carry_a_relation(self):
        doc = self.doc(nodes=[{"local_id": "a", "parent": None, "relation": "on-top-of"}])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("relation must be null" in e for e in report["errors"]))

    def test_a_file_with_no_anchor_is_rejected(self):
        doc = self.doc(anchors=[], nodes=[
            {"local_id": "x", "parent": "y", "relation": "on-top-of"},
            {"local_id": "y", "parent": "x", "relation": "on-top-of"},
        ])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("no anchors" in e for e in report["errors"]))

    def test_unknown_without_a_note_is_rejected(self):
        doc = self.doc(nodes=[
            {"local_id": "a", "parent": None, "relation": None},
            {"local_id": "x", "parent": "a", "relation": "unknown"},
        ])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("needs a note" in e for e in report["errors"]))

    def test_an_inferred_support_without_a_note_is_rejected(self):
        doc = self.doc(nodes=[
            {"local_id": "a", "parent": None, "relation": None},
            {"local_id": "x", "parent": "a", "relation": "on-top-of", "support_inferred": True},
        ])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("support_inferred" in e for e in report["errors"]))

    def test_everything_being_an_anchor_is_rejected(self):
        doc = self.doc(anchors=["a", "b"], nodes=[
            {"local_id": "a", "parent": None, "relation": None},
            {"local_id": "b", "parent": None, "relation": None},
        ])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("cascade was not done" in e for e in report["errors"]))

    def test_a_flat_list_under_one_anchor_is_warned_about(self):
        nodes = [{"local_id": "a", "parent": None, "relation": None}]
        nodes += [{"local_id": f"x{i}", "parent": "a", "relation": "on-top-of"} for i in range(6)]
        code, report, _ = run_json(self.script, self.write(self.doc(nodes=nodes)))
        self.assertEqual(code, 0)
        self.assertTrue(any("hangs straight off an anchor" in w for w in report["warnings"]))

    def test_declared_anchors_must_match_the_nodes(self):
        code, report, _ = run_json(self.script, self.write(self.doc(anchors=["a", "table"])))
        self.assertEqual(code, 1)
        self.assertTrue(any("'anchors' says" in e for e in report["errors"]))

    def test_a_missing_detection_is_caught(self):
        detections = self.detections(["a", "table", "mat", "bowl", "spoon", "fork"])
        code, report, _ = run_json(self.script, self.write(GOOD), "--detections", detections)
        self.assertEqual(code, 1)
        self.assertTrue(any("'fork' is in the detections file" in e for e in report["errors"]))

    def test_an_invented_object_is_caught(self):
        detections = self.detections(["a", "table", "mat", "bowl"])
        code, report, _ = run_json(self.script, self.write(GOOD), "--detections", detections)
        self.assertEqual(code, 1)
        self.assertTrue(any("nothing may be invented" in e for e in report["errors"]))

    def test_matching_detections_pass(self):
        detections = self.detections(["a", "table", "mat", "bowl", "spoon"])
        code, report, _ = run_json(self.script, self.write(GOOD), "--detections", detections)
        self.assertEqual(code, 0, report["errors"])

    def test_also_touches_does_not_create_a_second_parent(self):
        doc = self.doc(nodes=[
            {"local_id": "a", "parent": None, "relation": None},
            {"local_id": "wall", "parent": "a", "relation": "attached-to"},
            {"local_id": "bag", "parent": "a", "relation": "on-top-of",
             "also_touches": [{"local_id": "wall", "relation": "leaning-against"}]},
        ])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 0, report["errors"])

    def test_also_touches_with_a_bad_relation_is_rejected(self):
        doc = self.doc(nodes=GOOD["nodes"] + [
            {"local_id": "bag", "parent": "a", "relation": "on-top-of",
             "also_touches": [{"local_id": "table", "relation": "beside"}]}])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("also_touches relation" in e for e in report["errors"]))

    def test_a_cluster_needs_two_members_and_a_kind(self):
        doc = self.doc(clusters=[{"cluster_id": "c1", "label": "mats", "members": ["mat"],
                                  "kind": "instances"}])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("two or more members" in e for e in report["errors"]))

        doc = self.doc(clusters=[{"cluster_id": "c1", "label": "mats",
                                  "members": ["mat", "bowl"], "kind": "similar"}])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("kind must be one of" in e for e in report["errors"]))

    def test_a_cluster_member_must_be_a_node(self):
        doc = self.doc(clusters=[{"cluster_id": "c1", "label": "mats",
                                  "members": ["mat", "ghost"], "kind": "instances"}])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("is not a node" in e for e in report["errors"]))

    def test_an_area_needs_two_members(self):
        doc = self.doc(areas=[{"area_id": "a1", "label": "dining area", "members": ["table"]}])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 1)
        self.assertTrue(any("two or more members" in e for e in report["errors"]))

    def test_an_area_named_for_the_picture_is_warned_about(self):
        doc = self.doc(areas=[{"area_id": "a1", "label": "the left side",
                               "members": ["table", "mat"]}])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 0)
        self.assertTrue(any("names where it is in the picture" in w for w in report["warnings"]))

    def test_centrepiece_is_not_mistaken_for_a_picture_position(self):
        """Substring matching flagged 'table centrepiece' on a real run."""
        doc = self.doc(areas=[{"area_id": "a1", "label": "table centrepiece",
                               "members": ["table", "mat"]}])
        code, report, _ = run_json(self.script, self.write(doc))
        self.assertEqual(code, 0)
        self.assertEqual(report["warnings"], [])

    def test_strict_turns_a_warning_into_a_failure(self):
        doc = self.doc(areas=[{"area_id": "a1", "label": "the background",
                               "members": ["table", "mat"]}])
        code, _, _ = run_json(self.script, self.write(doc), "--strict")
        self.assertEqual(code, 1)

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

    def test_exit_2_when_the_detections_file_is_missing(self):
        code, _, err = run(self.script, self.write(GOOD), "--detections",
                           os.path.join(self.tmp, "nope.json"))
        self.assertEqual(code, 2)
        self.assertIn("no such file", err)







if __name__ == "__main__":
    unittest.main()
