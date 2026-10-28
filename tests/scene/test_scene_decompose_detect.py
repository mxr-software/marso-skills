"""Tests for the scene-decompose-detect scripts."""
import copy
import glob
import json
import os
import shutil
import tempfile
import unittest

from helpers import SKILL as SKILL_DIR, SCRIPTS as SCRIPTS_DIR, ROOT, run, run_json

SCRIPTS = SCRIPTS_DIR

GOOD_OBJECT = {
    "local_id": "img003-001",
    "label": "signet ring",
    "description": "gold band with a dark oval stone, lying flat on the woven mat",
    "category": "jewellery",
    "bbox": [0.27, 0.58, 0.29, 0.61],
    "truncated": [],
    "occluded": False,
    "size_m": 0.022,
    "size_confidence": "medium",
    "size_basis": "about a sixth of the width of the earcup beside it",
    "pass": "overview",
}


def detections(*objects):
    return {"schema": "scene-decompose/detections@1", "image_id": "img003",
            "objects": [copy.deepcopy(o) for o in objects]}


class CheckDetectionsTests(unittest.TestCase):
    def setUp(self):
        self.script = os.path.join(SCRIPTS, "check_detections.py")
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, data, name="detections.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def obj(self, **changes):
        out = copy.deepcopy(GOOD_OBJECT)
        out.update(changes)
        return out

    def test_help_works(self):
        code, out, _ = run(self.script, "--help")
        self.assertEqual(code, 0)
        self.assertIn("--strict", out)

    def test_a_clean_file_passes(self):
        code, report, _ = run_json(self.script, self.write(detections(GOOD_OBJECT)))
        self.assertEqual(code, 0, report)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["objects"], 1)

    def test_pixel_coordinates_are_rejected_with_an_explanation(self):
        path = self.write(detections(self.obj(bbox=[1200, 800, 1260, 860])))
        code, report, _ = run_json(self.script, path)
        self.assertEqual(code, 1)
        self.assertTrue(any("outside 0-1" in e for e in report["errors"]))
        self.assertTrue(any("pixel" in e for e in report["errors"]))

    def test_reversed_box_is_rejected(self):
        path = self.write(detections(self.obj(bbox=[0.6, 0.6, 0.2, 0.2])))
        code, report, _ = run_json(self.script, path)
        self.assertEqual(code, 1)
        self.assertTrue(any("x0 < x1" in e for e in report["errors"]))

    def test_missing_required_fields_are_each_named(self):
        bad = self.obj()
        del bad["size_basis"]
        del bad["category"]
        code, report, _ = run_json(self.script, self.write(detections(bad)))
        self.assertEqual(code, 1)
        self.assertTrue(any("size_basis" in e for e in report["errors"]))
        self.assertTrue(any("category" in e for e in report["errors"]))

    def test_an_empty_size_basis_is_rejected(self):
        path = self.write(detections(self.obj(size_basis="   ")))
        code, report, _ = run_json(self.script, path)
        self.assertEqual(code, 1)
        self.assertTrue(any("size_basis" in e for e in report["errors"]))

    def test_duplicate_local_ids_are_rejected(self):
        path = self.write(detections(GOOD_OBJECT, self.obj(bbox=[0.1, 0.1, 0.2, 0.2])))
        code, report, _ = run_json(self.script, path)
        self.assertEqual(code, 1)
        self.assertTrue(any("more than once" in e for e in report["errors"]))

    def test_bad_enums_are_rejected(self):
        path = self.write(detections(self.obj(size_confidence="quite sure", **{"pass": "guess"})))
        code, report, _ = run_json(self.script, path)
        self.assertEqual(code, 1)
        self.assertTrue(any("size_confidence" in e for e in report["errors"]))
        self.assertTrue(any("pass" in e for e in report["errors"]))

    def test_id_confidence_is_optional_but_must_be_valid(self):
        """A wide view that cannot identify a tiny object says so with id_confidence."""
        code, _, _ = run_json(self.script, self.write(detections(self.obj(id_confidence="low"))))
        self.assertEqual(code, 0)
        code, report, _ = run_json(
            self.script, self.write(detections(self.obj(id_confidence="probably"))))
        self.assertEqual(code, 1)
        self.assertTrue(any("id_confidence must be one of" in e for e in report["errors"]))

    def test_bad_truncated_edges_are_rejected(self):
        path = self.write(detections(self.obj(truncated=["north"])))
        code, report, _ = run_json(self.script, path)
        self.assertEqual(code, 1)
        self.assertTrue(any("truncated" in e for e in report["errors"]))

    def test_an_empty_object_list_is_rejected(self):
        code, report, _ = run_json(self.script, self.write(detections()))
        self.assertEqual(code, 1)
        self.assertTrue(any("empty" in e for e in report["errors"]))

    def test_a_logo_is_warned_about_but_does_not_fail(self):
        path = self.write(detections(self.obj(label="apple logo")))
        code, report, _ = run_json(self.script, path)
        self.assertEqual(code, 0)
        self.assertTrue(any("printed on another object" in w for w in report["warnings"]))

    def test_a_holder_named_only_in_a_description_is_warned_about(self):
        """A kitchen roll once carried its holder in a sentence instead of a box."""
        path = self.write(detections(self.obj(
            label="kitchen roll",
            description="roll of white kitchen paper on an upright metal holder")))
        code, report, _ = run_json(self.script, path)
        self.assertEqual(code, 0)
        self.assertTrue(any("is on or in a 'holder'" in w for w in report["warnings"]))

    def test_a_holder_that_was_detected_is_not_warned_about(self):
        a = self.obj(label="kitchen roll",
                     description="roll of paper on an upright metal holder")
        b = self.obj(local_id="img003-002", label="kitchen roll holder",
                     description="upright metal post with a round base",
                     bbox=[0.4, 0.4, 0.45, 0.5])
        code, report, _ = run_json(self.script, self.write(detections(a, b)))
        self.assertEqual(code, 0)
        self.assertEqual([w for w in report["warnings"] if "holder" in w], [])

    def test_the_verb_to_stand_is_not_a_missing_fixture(self):
        """A run full of upright objects uses that verb constantly."""
        for text in ("the camera stands against its upper left edge",
                     "a tall bottle standing on the worktop",
                     "the label understates its size"):
            path = self.write(detections(self.obj(label="camera", description=text)))
            code, report, _ = run_json(self.script, path)
            self.assertEqual(code, 0)
            self.assertEqual([w for w in report["warnings"] if "is on or in a" in w], [],
                             text)

    def test_the_fixture_describing_itself_is_not_a_missing_fixture(self):
        """A dish drainer's own description necessarily contains the word 'rack'."""
        path = self.write(detections(self.obj(
            label="dish drainer rack", description="a wire rack holding washed pans")))
        code, report, _ = run_json(self.script, path)
        self.assertEqual(code, 0)
        self.assertEqual([w for w in report["warnings"] if "is on or in a" in w], [])

    def test_a_holder_recorded_under_another_name_is_not_a_missing_fixture(self):
        """A run described a roll "on its stand" and was told no stand existed, when the
        object right underneath it was labelled "kitchen roll holder"."""
        roll = self.obj(label="kitchen roll", bbox=[0.13, 0.24, 0.17, 0.32],
                        description="roll of embossed cream kitchen paper on its stand")
        holder = self.obj(local_id="img003-002", label="kitchen roll holder",
                          bbox=[0.135, 0.22, 0.172, 0.33],
                          description="chrome post with a round base")
        code, report, _ = run_json(self.script, self.write(detections(roll, holder)))
        self.assertEqual(code, 0)
        self.assertEqual([w for w in report["warnings"] if "is on or in a" in w], [])

    def test_a_fixture_elsewhere_does_not_excuse_a_missing_one(self):
        mug = self.obj(label="mug", bbox=[0.5, 0.5, 0.55, 0.56],
                       description="a mug hanging on a wall hook")
        rack = self.obj(local_id="img003-002", label="plate rack", bbox=[0.1, 0.1, 0.2, 0.2],
                        description="a wooden rack by the sink")
        code, report, _ = run_json(self.script, self.write(detections(mug, rack)))
        self.assertEqual(code, 0)
        self.assertTrue(any("is on or in a 'hook'" in w for w in report["warnings"]))

    def test_a_chairs_back_rail_is_not_a_missing_fixture(self):
        """A part of an object reads like a fixture; 'rail' is deliberately not checked."""
        path = self.write(detections(self.obj(
            label="chair", description="pale wood frame with a curved back rail")))
        code, report, _ = run_json(self.script, path)
        self.assertEqual(code, 0)
        self.assertEqual(report["warnings"], [])

    def test_strict_turns_a_warning_into_a_failure(self):
        path = self.write(detections(self.obj(label="apple logo")))
        code, _, _ = run_json(self.script, path, "--strict")
        self.assertEqual(code, 1)

    def test_near_identical_boxes_are_warned_about(self):
        a = self.obj()
        b = self.obj(local_id="img003-002", bbox=[0.2705, 0.5805, 0.2895, 0.6095])
        code, report, _ = run_json(self.script, self.write(detections(a, b)))
        self.assertEqual(code, 0)
        self.assertTrue(any("overlap" in w for w in report["warnings"]))

    def test_an_anchor_overlapping_its_contents_is_not_a_duplicate(self):
        """Anchors are boxed at full extent, so everything on them overlaps them. A real run
        warned that a floor and the table standing on it might be the same object."""
        floor = self.obj(local_id="img003-001", label="floor", category="architecture",
                         bbox=[0.0, 0.0, 1.0, 1.0])
        table = self.obj(local_id="img003-004", label="dining table", category="furniture",
                         bbox=[0.13, 0.0, 1.0, 1.0])
        code, report, _ = run_json(self.script, self.write(detections(floor, table)))
        self.assertEqual(code, 0, report)
        self.assertEqual(report["warnings"], [])

    def test_two_overlapping_non_anchors_are_still_warned_about(self):
        a = self.obj(local_id="a1", category="tableware", bbox=[0.1, 0.1, 0.4, 0.4])
        b = self.obj(local_id="b1", category="tableware", bbox=[0.102, 0.102, 0.398, 0.398])
        _, report, _ = run_json(self.script, self.write(detections(a, b)))
        self.assertTrue(any("overlap" in w for w in report["warnings"]))

    def test_says_it_cannot_see_the_image(self):
        _, report, _ = run_json(self.script, self.write(detections(GOOD_OBJECT)))
        self.assertIn("cannot see the image", report["checked"])

    def test_exit_2_on_a_missing_or_broken_file(self):
        code, _, err = run(self.script, os.path.join(self.tmp, "nope.json"))
        self.assertEqual(code, 2)
        self.assertIn("no such file", err)
        broken = os.path.join(self.tmp, "broken.json")
        with open(broken, "w", encoding="utf-8") as f:
            f.write("{not json")
        code, _, err = run(self.script, broken)
        self.assertEqual(code, 2)
        self.assertIn("not valid JSON", err)





class MergeDetectionsTests(unittest.TestCase):
    def setUp(self):
        self.script = os.path.join(SCRIPTS, "merge_detections.py")
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, *objects):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(detections(*objects), f)
        return path

    def obj(self, **changes):
        out = copy.deepcopy(GOOD_OBJECT)
        out.update(changes)
        return out

    def test_help_works(self):
        code, out, _ = run(self.script, "--help")
        self.assertEqual(code, 0)
        self.assertIn("--iou", out)

    def test_the_same_object_from_two_tiles_is_merged_once(self):
        a = self.write("a.json", self.obj(local_id="a1", description="gold signet ring on the mat"))
        b = self.write("b.json", self.obj(local_id="b1", description="a ring"))
        code, merged, _ = run_json(self.script, a, b)
        self.assertEqual(code, 0)
        self.assertEqual(len(merged["objects"]), 1)
        self.assertEqual(merged["objects"][0]["local_id"], "a1")

    def test_every_drop_is_reported_rather_than_silent(self):
        a = self.write("a.json", self.obj(local_id="a1", description="gold signet ring on the mat"))
        b = self.write("b.json", self.obj(local_id="b1", description="a ring"))
        _, merged, _ = run_json(self.script, a, b)
        dropped = merged["merge"]["dropped"]
        self.assertEqual(len(dropped), 1)
        self.assertEqual(dropped[0]["dropped"], "b1")
        self.assertEqual(dropped[0]["kept"], "a1")
        self.assertEqual(merged["merge"]["inputs"], 2)

    def test_the_richer_description_wins(self):
        a = self.write("a.json", self.obj(local_id="terse", description="ring"))
        b = self.write("b.json", self.obj(local_id="rich",
                                          description="gold band with a dark oval stone on the mat"))
        _, merged, _ = run_json(self.script, a, b)
        self.assertEqual(merged["objects"][0]["local_id"], "rich")

    def test_distinct_objects_are_both_kept(self):
        a = self.write("a.json", self.obj(local_id="a1", bbox=[0.1, 0.1, 0.2, 0.2]))
        b = self.write("b.json", self.obj(local_id="b1", bbox=[0.7, 0.7, 0.8, 0.8]))
        _, merged, _ = run_json(self.script, a, b)
        self.assertEqual(len(merged["objects"]), 2)
        self.assertEqual(merged["merge"]["dropped"], [])

    def test_partial_overlap_below_the_threshold_keeps_both(self):
        a = self.write("a.json", self.obj(local_id="a1", bbox=[0.1, 0.1, 0.3, 0.3]))
        b = self.write("b.json", self.obj(local_id="b1", bbox=[0.25, 0.25, 0.45, 0.45]))
        _, merged, _ = run_json(self.script, a, b)
        self.assertEqual(len(merged["objects"]), 2)

    def test_writes_utf8_and_refuses_to_overwrite_without_force(self):
        a = self.write("a.json", GOOD_OBJECT)
        out = os.path.join(self.tmp, "sub", "merged.json")
        code, _, _ = run(self.script, a, "--out", out)
        self.assertEqual(code, 0)
        with open(out, encoding="utf-8") as f:
            self.assertEqual(len(json.load(f)["objects"]), 1)
        code, _, err = run(self.script, a, "--out", out)
        self.assertEqual(code, 1)
        self.assertIn("--force", err)
        code, _, _ = run(self.script, a, "--out", out, "--force")
        self.assertEqual(code, 0)

    def test_exit_2_on_a_missing_file_or_a_file_with_no_objects(self):
        code, _, err = run(self.script, os.path.join(self.tmp, "nope.json"))
        self.assertEqual(code, 2)
        self.assertIn("no such file", err)
        bad = os.path.join(self.tmp, "bad.json")
        with open(bad, "w", encoding="utf-8") as f:
            json.dump({"schema": "x"}, f)
        code, _, err = run(self.script, bad)
        self.assertEqual(code, 2)
        self.assertIn("objects", err)

    def test_bad_iou_exits_2(self):
        a = self.write("a.json", GOOD_OBJECT)
        code, _, err = run(self.script, a, "--iou", "0")
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())


class OverlayTests(unittest.TestCase):
    """draw_boxes.py: the overlay that shows whether a box is right."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.image = os.path.join(self.tmp, "photo.jpg")
        with open(self.image, "wb") as f:
            f.write(b"not parsed: the scripts reference the file, they never decode it")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, data, name="detections.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_the_overlay_draws_every_box_over_the_image(self):
        """Looking at the boxes is half the gate; a script can only check the numbers."""
        script = os.path.join(SCRIPTS, "draw_boxes.py")
        obj = copy.deepcopy(GOOD_OBJECT)
        obj["bbox"] = [0.25, 0.5, 0.75, 0.9]
        out = os.path.join(self.tmp, "boxes.svg")
        code, report, _ = run_json(script, self.write(detections(obj)), "--image",
                                   self.image, "--out", out,
                                   "--width", "4000", "--height", "3000")
        self.assertEqual(code, 0)
        self.assertEqual(report["boxes"], 1)
        with open(out, encoding="utf-8-sig") as f:
            body = f.read()
        self.assertIn('viewBox="0.0 0.0 4000.0 3000.0"', body)
        self.assertIn('width="100%"', body)   # fits the window, not one corner of it
        self.assertIn('x="1000.0" y="1500.0" width="2000.0" height="1200.0"', body)
        self.assertIn("photo.jpg", body)
        self.assertIn(GOOD_OBJECT["local_id"], body)

    def test_the_overlay_can_crop_and_drop_labels(self):
        """85 boxes on one frame is unreadable: a run had to strip the labels by hand."""
        script = os.path.join(SCRIPTS, "draw_boxes.py")
        obj = copy.deepcopy(GOOD_OBJECT)
        obj["bbox"] = [0.4, 0.4, 0.5, 0.5]
        path = self.write(detections(obj))
        out = os.path.join(self.tmp, "boxes.svg")
        code, _, _ = run_json(script, path, "--image", self.image, "--out", out,
                              "--width", "4000", "--height", "3000",
                              "--crop", "0.38", "0.40", "0.62", "0.56", "--no-labels")
        self.assertEqual(code, 0)
        with open(out, encoding="utf-8-sig") as f:
            body = f.read()
        self.assertIn('viewBox="1520.0 1200.0 960.0 480.0"', body)
        self.assertNotIn("<text", body, "--no-labels still drew a label")
        self.assertIn("<rect", body)

    def test_the_overlay_refuses_to_overwrite_without_force(self):
        script = os.path.join(SCRIPTS, "draw_boxes.py")
        out = os.path.join(self.tmp, "boxes.svg")
        args = (self.write(detections(copy.deepcopy(GOOD_OBJECT))), "--image", self.image,
                "--out", out, "--width", "40", "--height", "30")
        self.assertEqual(run(script, *args)[0], 0)
        self.assertEqual(run(script, *args)[0], 1)
        self.assertEqual(run(script, *args, "--force")[0], 0)

    def test_the_overlay_reports_a_missing_image(self):
        script = os.path.join(SCRIPTS, "draw_boxes.py")
        code, _, err = run(script, self.write(detections(copy.deepcopy(GOOD_OBJECT))),
                           "--image", os.path.join(self.tmp, "nope.jpg"),
                           "--out", os.path.join(self.tmp, "b.svg"))
        self.assertEqual(code, 2)
        self.assertIn("no such image", err)

    def test_png_writes_an_image_a_reader_can_open(self):
        """A stage agent cannot view an SVG, so half the gate needed another form."""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is not installed; --png is documented as needing it")
        script = os.path.join(SCRIPTS, "draw_boxes.py")
        photo = os.path.join(self.tmp, "photo.png")
        Image.new("RGB", (80, 60), (20, 40, 60)).save(photo)
        obj = copy.deepcopy(GOOD_OBJECT)
        obj["bbox"] = [0.25, 0.5, 0.75, 0.9]
        out = os.path.join(self.tmp, "boxes.png")
        code, report, _ = run_json(script, self.write(detections(obj)), "--image", photo,
                                   "--out", out, "--width", "80", "--height", "60", "--png")
        self.assertEqual(code, 0)
        self.assertEqual(report["format"], "png")
        with Image.open(out) as drawn:
            # Scaled up to a readable size, keeping the photograph's shape. A native-size
            # crop of a small region came out a few hundred pixels across and every agent
            # that got one upscaled it by hand before it could judge a box edge.
            self.assertEqual(max(drawn.size), 1600)
            self.assertAlmostEqual(drawn.size[0] / drawn.size[1], 80 / 60, places=1)
            width, height = drawn.size
            colours = {drawn.getpixel((x, y))
                       for x in range(0, width, 7) for y in range(0, height, 7)}
        self.assertGreater(len(colours), 1, "nothing was drawn over the photograph")

    def test_png_respects_no_labels(self):
        """The flag was accepted and ignored, so a crowded crop stayed unreadable."""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is not installed; --png is documented as needing it")
        script = os.path.join(SCRIPTS, "draw_boxes.py")
        photo = os.path.join(self.tmp, "photo.png")
        Image.new("RGB", (400, 300), (0, 0, 0)).save(photo)
        obj = copy.deepcopy(GOOD_OBJECT)
        obj["bbox"] = [0.25, 0.5, 0.75, 0.9]
        written = self.write(detections(obj))

        def ink(name, *extra):
            out = os.path.join(self.tmp, name)
            code, _, _ = run_json(script, written, "--image", photo, "--out", out,
                                  "--width", "400", "--height", "300", "--png", *extra)
            self.assertEqual(code, 0)
            with Image.open(out) as drawn:
                width, height = drawn.size
                return sum(1 for x in range(width) for y in range(height)
                           if drawn.getpixel((x, y)) != (0, 0, 0))

        self.assertLess(ink("bare.png", "--no-labels"), ink("labelled.png"),
                        "--no-labels drew just as much ink, so the label is still there")

    def test_png_fixes_a_name_that_would_crash_pillow(self):
        """Both scripts' own examples write a .svg, so --png on them died in a traceback."""
        try:
            from PIL import Image                                  # noqa: F401
        except ImportError:
            self.skipTest("Pillow is not installed; --png is documented as needing it")
        script = os.path.join(SCRIPTS, "draw_boxes.py")
        photo = os.path.join(self.tmp, "photo.png")
        from PIL import Image as Im
        Im.new("RGB", (80, 60), (20, 40, 60)).save(photo)
        out = os.path.join(self.tmp, "boxes.svg")
        code, report, _ = run_json(script, self.write(detections(copy.deepcopy(GOOD_OBJECT))),
                                   "--image", photo, "--out", out,
                                   "--width", "80", "--height", "60", "--png")
        self.assertEqual(code, 0)
        self.assertTrue(report["out"].endswith(".png"), report["out"])
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "boxes.png")))









if __name__ == "__main__":
    unittest.main()
