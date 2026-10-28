"""Tests for the scene-decompose-register scripts."""
import copy
import json
import os
import shutil
import tempfile
import unittest

from helpers import SKILL as SKILL_DIR, SCRIPTS as SCRIPTS_DIR, ROOT, run, run_json

SKILL = SKILL_DIR
SCRIPTS = SCRIPTS_DIR

GOOD = {
    "schema": "scene-decompose/registration@1",
    "images": ["img001", "img002", "img003"],
    "establishing_view": "img001",
    "no_overview": False,
    "pairs": [
        {"a": "img001", "b": "img002", "relation": "different-viewpoint",
         "confidence": "high",
         "evidence": "the same oak table and the framed picture above it, from the other side"},
        {"a": "img001", "b": "img003", "relation": "close-up", "closer": "img003",
         "region": [0.3, 0.39, 0.73, 0.87], "confidence": "high",
         "evidence": "the same laptop, headphones and woven mat on the same table"},
        {"a": "img002", "b": "img003", "relation": "no-overlap", "confidence": "medium",
         "evidence": "img002 shows the worktop along the far wall; nothing on it is in img003"},
    ],
}

MANIFEST = {"images": [{"image_id": "img001"}, {"image_id": "img002"}, {"image_id": "img003"}]}


class RegisterScriptTests(unittest.TestCase):
    def setUp(self):
        self.check = os.path.join(SCRIPTS, "check_registration.py")
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, data, name="registration.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def edit(self, **changes):
        data = copy.deepcopy(GOOD)
        data.update(changes)
        return data







    # --- check_registration: the happy path ---------------------------------

    def test_a_good_file_passes(self):
        code, report, _ = run_json(self.check, self.write(GOOD))
        self.assertEqual(code, 0)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["warnings"], [])


    def test_it_checks_every_image_in_the_manifest_is_registered(self):
        man = self.write({"images": [{"image_id": "img001"}, {"image_id": "img002"},
                                     {"image_id": "img003"}, {"image_id": "img004"}]},
                         "manifest.json")
        code, report, _ = run_json(self.check, self.write(GOOD), "--manifest", man)
        self.assertEqual(code, 1)
        self.assertTrue(any("img004" in e for e in report["errors"]))

    # --- check_registration: the rules --------------------------------------

    def test_a_missing_pair_is_named(self):
        """A pair that shares nothing still gets a verdict; silence is not an answer."""
        data = self.edit(pairs=GOOD["pairs"][:2])
        code, report, _ = run_json(self.check, self.write(data))
        self.assertEqual(code, 1)
        self.assertTrue(any("no verdict" in e and "img002+img003" in e
                            for e in report["errors"]))

    def test_a_pair_given_twice_is_rejected(self):
        data = self.edit(pairs=GOOD["pairs"] + [copy.deepcopy(GOOD["pairs"][0])])
        code, report, _ = run_json(self.check, self.write(data))
        self.assertEqual(code, 1)
        self.assertTrue(any("already has a verdict" in e for e in report["errors"]))

    def test_a_pair_in_the_wrong_order_is_rejected(self):
        pairs = copy.deepcopy(GOOD["pairs"])
        pairs[0]["a"], pairs[0]["b"] = pairs[0]["b"], pairs[0]["a"]
        code, report, _ = run_json(self.check, self.write(self.edit(pairs=pairs)))
        self.assertEqual(code, 1)
        self.assertTrue(any("put the pair in order" in e for e in report["errors"]))

    def test_an_unknown_relation_is_rejected(self):
        pairs = copy.deepcopy(GOOD["pairs"])
        pairs[0]["relation"] = "sort-of-overlapping"
        code, report, _ = run_json(self.check, self.write(self.edit(pairs=pairs)))
        self.assertEqual(code, 1)
        self.assertTrue(any("relation must be one of" in e for e in report["errors"]))

    def test_evidence_with_no_reason_in_it_is_rejected(self):
        """'similar scene' cannot be checked, argued with or corrected later."""
        pairs = copy.deepcopy(GOOD["pairs"])
        pairs[0]["evidence"] = "similar"
        code, report, _ = run_json(self.check, self.write(self.edit(pairs=pairs)))
        self.assertEqual(code, 1)
        self.assertTrue(any("what you actually saw" in e for e in report["errors"]))

    def test_a_close_up_without_a_region_is_rejected(self):
        pairs = copy.deepcopy(GOOD["pairs"])
        del pairs[1]["region"]
        code, report, _ = run_json(self.check, self.write(self.edit(pairs=pairs)))
        self.assertEqual(code, 1)
        self.assertTrue(any("needs a region" in e for e in report["errors"]))

    def test_a_close_up_without_a_closer_image_is_rejected(self):
        pairs = copy.deepcopy(GOOD["pairs"])
        pairs[1]["closer"] = "img009"
        code, report, _ = run_json(self.check, self.write(self.edit(pairs=pairs)))
        self.assertEqual(code, 1)
        self.assertTrue(any("closer must be" in e for e in report["errors"]))

    def test_a_region_in_pixels_is_rejected(self):
        pairs = copy.deepcopy(GOOD["pairs"])
        pairs[1]["region"] = [1200, 1170, 2920, 2610]
        code, report, _ = run_json(self.check, self.write(self.edit(pairs=pairs)))
        self.assertEqual(code, 1)
        self.assertTrue(any("normalised" in e for e in report["errors"]))

    def test_a_backwards_region_is_rejected(self):
        pairs = copy.deepcopy(GOOD["pairs"])
        pairs[1]["region"] = [0.73, 0.87, 0.3, 0.39]
        code, report, _ = run_json(self.check, self.write(self.edit(pairs=pairs)))
        self.assertEqual(code, 1)
        self.assertTrue(any("x0 < x1" in e for e in report["errors"]))

    def test_a_region_on_a_pair_that_is_not_a_close_up_is_warned_about(self):
        pairs = copy.deepcopy(GOOD["pairs"])
        pairs[0]["region"] = [0.1, 0.1, 0.2, 0.2]
        code, report, _ = run_json(self.check, self.write(self.edit(pairs=pairs)))
        self.assertEqual(code, 0)
        self.assertTrue(any("only means something on a close-up" in w
                            for w in report["warnings"]))

    def test_a_region_may_carry_its_own_confidence(self):
        """A pair can be certainly a close-up and only roughly located."""
        pairs = copy.deepcopy(GOOD["pairs"])
        pairs[1]["region_confidence"] = "medium"
        code, report, _ = run_json(self.check, self.write(self.edit(pairs=pairs)))
        self.assertEqual(code, 0, report)
        pairs[1]["region_confidence"] = "roughly"
        code, report, _ = run_json(self.check, self.write(self.edit(pairs=pairs)))
        self.assertEqual(code, 1)
        self.assertTrue(any("region_confidence must be one of" in e for e in report["errors"]))

    def test_region_confidence_on_a_non_close_up_is_warned_about(self):
        pairs = copy.deepcopy(GOOD["pairs"])
        pairs[0]["region_confidence"] = "high"
        code, report, _ = run_json(self.check, self.write(self.edit(pairs=pairs)))
        self.assertEqual(code, 0)
        self.assertTrue(any("region_confidence only means something" in w
                            for w in report["warnings"]))

    def test_no_establishing_view_must_be_said_deliberately(self):
        """An empty field is indistinguishable from a forgotten one."""
        data = self.edit(establishing_view=None, no_overview=False)
        code, report, _ = run_json(self.check, self.write(data))
        self.assertEqual(code, 1)
        self.assertTrue(any("no_overview" in e for e in report["errors"]))

    def test_a_set_with_no_overview_passes_when_it_says_so(self):
        data = self.edit(establishing_view=None, no_overview=True)
        code, report, _ = run_json(self.check, self.write(data))
        self.assertEqual(code, 0, report)

    def test_an_establishing_view_that_is_not_an_image_is_rejected(self):
        code, report, _ = run_json(self.check,
                                   self.write(self.edit(establishing_view="img009")))
        self.assertEqual(code, 1)
        self.assertTrue(any("not one of the images" in e for e in report["errors"]))

    def test_the_widest_view_cannot_be_the_close_shot(self):
        data = self.edit(establishing_view="img003")
        code, report, _ = run_json(self.check, self.write(data))
        self.assertEqual(code, 0)
        self.assertTrue(any("should not be a close-up" in w for w in report["warnings"]))

    def test_strict_turns_a_warning_into_a_failure(self):
        code, _, _ = run(self.check, self.write(self.edit(establishing_view="img003")),
                         "--strict")
        self.assertEqual(code, 1)

    def test_an_unreadable_file_exits_two(self):
        code, _, err = run(self.check, os.path.join(self.tmp, "nope.json"))
        self.assertEqual(code, 2)
        self.assertIn("no such file", err)

    # --- the house rules ----------------------------------------------------

    def test_the_scripts_have_help_and_do_not_prompt(self):
        for script in (self.check,):
            code, out, _ = run(script, "--help")
            self.assertEqual(code, 0)
            self.assertIn("usage:", out)
            with open(script, encoding="utf-8-sig") as f:
                body = f.read()
            self.assertNotIn("input(", body)




if __name__ == "__main__":
    unittest.main()
