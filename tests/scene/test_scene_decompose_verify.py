"""Tests for the verify round: make_verify.py plan and apply."""
import json
import os
import shutil
import tempfile
import unittest

from helpers import SCRIPTS as SCRIPTS_DIR, run_json

VERIFY = os.path.join(SCRIPTS_DIR, "make_verify.py")

try:
    from PIL import Image
except ImportError:                                    # pragma: no cover
    Image = None


def obj(local_id, label, bbox, parent=None, **extra):
    out = {"local_id": local_id, "label": label, "description": label, "category": "homeware",
           "bbox": bbox, "size_m": 0.2, "size_basis": "x", "parent": parent,
           "relation": "on-top-of" if parent else None}
    out.update(extra)
    return out


@unittest.skipIf(Image is None, "Pillow is required for the verify sheets")
class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.run_dir = os.path.join(self.tmp, "runs", "kitchen")
        for sub in ("detections", "structure"):
            os.makedirs(os.path.join(self.run_dir, sub))
        photo = os.path.join(self.tmp, "kitchen.png")
        Image.new("RGB", (400, 300), (200, 180, 160)).save(photo)
        self.write("manifest.json", {"images": [{"image_id": "img001", "path": photo,
                                                 "width": 400, "height": 300}]})
        self.objects = [
            obj("img001-001", "floor", [0.0, 0.5, 1.0, 1.0], category="architecture"),
            obj("img001-002", "oak table", [0.2, 0.4, 0.8, 0.9], "img001-001"),
            obj("img001-003", "small dish", [0.3, 0.42, 0.36, 0.48], "img001-002", id_confidence="low"),
            obj("img001-004", "vinyl record", [0.95, 0.0, 1.0, 0.1], "img001-002", id_confidence="low"),
            obj("img001-005", "earbuds case", [0.5, 0.5, 0.6, 0.6], "img001-002"),
            obj("img001-006", "plastic case", [0.55, 0.5, 0.6, 0.6], "img001-002"),
            obj("img001-007", "lid", [0.56, 0.5, 0.58, 0.52], "img001-006"),
        ]
        self.write("detections/img001.json", {"image_id": "img001", "objects": self.objects})
        self.write("structure/img001.json", {"image_id": "img001", "anchors": ["img001-001"],
                                             "nodes": [], "clusters": [], "areas": []})

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, data):
        path = os.path.join(self.run_dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def read(self, name):
        with open(os.path.join(self.run_dir, name), encoding="utf-8") as f:
            return json.load(f)

    def test_plan_draws_numbered_sheets_and_one_agent_per_photograph(self):
        code, out, err = run_json(VERIFY, "plan", "--run", self.run_dir)
        self.assertEqual(code, 0, err)
        self.assertEqual(out["count"], 1)
        agent = out["agents"][0]
        self.assertTrue(agent["writes"].endswith("verify/img001.json"))
        self.assertTrue(all(os.path.exists(p) for p in agent["sheets"]))
        self.assertIn("verify.md", agent["prompt"])
        self.assertIn("**3** small dish", agent["prompt"])
        self.assertIn("name uncertain", agent["prompt"])

    def test_apply_renames_removes_and_joins_and_keeps_children(self):
        self.write("verify/img001.json", {"image_id": "img001",
            "renames": [{"n": 3, "label": "candle", "description": "white candle jar", "why": "box is on the jar"}],
            "remove": [{"n": 4, "why": "cut-off corner, not identifiable"}],
            "same_as": [{"n": 6, "as": 5, "why": "6 boxes half of the earbuds case"}]})
        code, out, err = run_json(VERIFY, "apply", "--run", self.run_dir)
        self.assertEqual(code, 0, (out, err))
        det = {o["local_id"]: o for o in self.read("detections/img001.json")["objects"]}
        self.assertEqual(det["img001-003"]["label"], "candle")
        self.assertEqual(det["img001-003"]["id_confidence"], "high")
        self.assertIn("small dish", det["img001-003"]["verified"])
        self.assertNotIn("img001-004", det)
        self.assertNotIn("img001-006", det)
        self.assertEqual(det["img001-007"]["parent"], "img001-005")     # the lid moved to the case
        self.assertEqual(det["img001-005"]["bbox"], [0.5, 0.5, 0.6, 0.6])
        tree = self.read("structure/img001.json")
        self.assertEqual({n["local_id"] for n in tree["nodes"]}, set(det))
        self.assertEqual(tree["anchors"], ["img001-001"])
        before = self.read("verify/img001.before.json")
        self.assertEqual(len(before["detections"]["objects"]), 7)
        self.assertEqual(out["applied"]["img001"]["renamed"], 1)

    def test_reparent_fixes_a_support_and_refuses_a_loop(self):
        self.write("verify/img001.json", {"image_id": "img001", "reparent": [
            {"n": 7, "on": 5, "relation": "on-top-of", "why": "the lid is on the earbuds case"},
            {"n": 2, "on": 7, "why": "the table on the lid would loop"}]})
        code, out, _ = run_json(VERIFY, "apply", "--run", self.run_dir)
        self.assertEqual(code, 1)                                # the loop is reported
        det = {o["local_id"]: o for o in self.read("detections/img001.json")["objects"]}
        self.assertEqual(det["img001-007"]["parent"], "img001-005")
        self.assertEqual(det["img001-002"]["parent"], "img001-001")
        self.assertEqual(out["applied"]["img001"]["reparented"], 1)

    def test_bad_numbers_and_anchors_are_reported_not_applied(self):
        self.write("verify/img001.json", {"image_id": "img001",
            "renames": [{"n": 99, "label": "x"}], "remove": [{"n": 1, "why": "floor"}]})
        code, out, _ = run_json(VERIFY, "apply", "--run", self.run_dir)
        self.assertEqual(code, 1)
        self.assertEqual(len(out["problems"]), 2)
        self.assertEqual(len(self.read("detections/img001.json")["objects"]), 7)

    def test_a_photograph_left_unverified_is_listed(self):
        code, out, _ = run_json(VERIFY, "apply", "--run", self.run_dir)
        self.assertEqual(code, 1)
        self.assertEqual(out["not_verified"], ["img001"])


if __name__ == "__main__":
    unittest.main()
