"""Tests for the fast match path: match_auto.py, build_matches.py and make_confusion.py.

The match stage cost eighteen agent-minutes, most of it reasoning about cases a script can
settle. These tests are about the two things that must hold anyway: nothing is merged on
less than two lines of evidence, and nothing is lost, merged twice, or made out of two
objects from one photograph.
"""
import json
import os
import shutil
import tempfile
import unittest

from helpers import SKILL as SKILL_DIR, SCRIPTS as SCRIPTS_DIR, ROOT, run, run_json

MATCH = SCRIPTS_DIR
AUTO = os.path.join(MATCH, "match_auto.py")
BUILD = os.path.join(MATCH, "build_matches.py")
CHECK = os.path.join(MATCH, "check_matches.py")
CONFUSION = os.path.join(SCRIPTS_DIR, "make_confusion.py")

try:
    from PIL import Image
except ImportError:                                    # pragma: no cover
    Image = None


class Scene(unittest.TestCase):
    """Two or three images of one room, written as detections and structures."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.det = os.path.join(self.tmp, "detections")
        self.str = os.path.join(self.tmp, "structure")
        os.makedirs(self.det)
        os.makedirs(self.str)
        self.images = {}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def image(self, image_id, items):
        """items: (n, label, parent_n_or_None, extra) -> ids image_id-00n."""
        objects, nodes = [], []
        for n, label, parent, *rest in items:
            extra = rest[0] if rest else {}
            lid = f"{image_id}-{n:03d}"
            box = extra.get("bbox", [0.1 * (n % 8), 0.1, 0.1 * (n % 8) + 0.05, 0.2])
            objects.append({"local_id": lid, "label": label, "description": label,
                            "category": extra.get("category", "homeware"), "bbox": box,
                            "size_m": extra.get("size_m", 0.2), "size_confidence": "medium",
                            "size_basis": "x", "pass": "tile", "occluded": False, "truncated": []})
            node = {"local_id": lid, "parent": f"{image_id}-{parent:03d}" if parent else None}
            if parent:
                node["relation"] = "on-top-of"
            nodes.append(node)
        for folder, name, body in ((self.det, "detections", {"objects": objects}),
                                   (self.str, "structure", {"nodes": nodes,
                                                            "anchors": [n["local_id"] for n in nodes
                                                                        if not n["parent"]]})):
            with open(os.path.join(folder, f"{image_id}.json"), "w", encoding="utf-8") as f:
                json.dump({"image_id": image_id, "schema": f"x/{name}", **body}, f)
        self.images[image_id] = [i[1] for i in items]

    def registration(self, pairs):
        path = os.path.join(self.tmp, "registration.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"pairs": [{"a": a, "b": b, "relation": r} for a, b, r in pairs]}, f)
        return path

    def auto(self, *extra, pairs=None):
        out = os.path.join(self.tmp, "auto.json")
        args = ["--structures", self.str, "--detections", self.det, "--out", out, "--force"]
        if pairs is not None:
            args += ["--registration", self.registration(pairs)]
        code, report, err = run_json(AUTO, *args, *extra)
        with open(out, encoding="utf-8") as f:
            return code, report, json.load(f), err

    def matched_labels(self, data):
        return {m["label"] for m in data["matched"]}


class AutoMatchTests(Scene):
    def room(self):
        self.image("img001", [(1, "parquet floor", None, {"category": "architecture"}),
                              (2, "oak table", 1, {"category": "furniture"}),
                              (3, "blue mug", 2), (4, "spoon", 3), (5, "wishbone chair", 1),
                              (6, "wishbone chair", 1)])
        self.image("img002", [(1, "parquet floor", None, {"category": "architecture"}),
                              (2, "oak table", 1, {"category": "furniture"}),
                              (3, "blue mug", 2), (4, "spoon", 3), (5, "wishbone chair", 1)])

    def test_an_unmistakable_object_is_matched_with_two_lines_of_evidence(self):
        self.room()
        code, report, data, _ = self.auto(pairs=[("img001", "img002", "partial-overlap")])
        self.assertEqual(code, 0)
        mug = next(m for m in data["matched"] if m["label"] == "blue mug")
        self.assertEqual({m["local_id"] for m in mug["members"]}, {"img001-003", "img002-003"})
        self.assertGreaterEqual(len(mug["evidence"]), 2, "a merge needs two lines")

    def test_the_cascade_reaches_what_a_matched_carrier_holds(self):
        """The spoon is matched because its mug is, not because of its name alone."""
        self.room()
        _, _, data, _ = self.auto(pairs=[("img001", "img002", "partial-overlap")])
        self.assertIn("spoon", self.matched_labels(data))

    def test_lookalikes_are_left_for_an_agent_not_guessed(self):
        """Two chairs in one view and one in the other: which is which is a judgement."""
        self.room()
        _, _, data, _ = self.auto(pairs=[("img001", "img002", "partial-overlap")])
        self.assertNotIn("wishbone chair", self.matched_labels(data))
        group = next(g for g in data["groups"] if g["carrier"] == "parquet floor")
        self.assertEqual(len(group["members"]["img001"]), 2)
        self.assertEqual(len(group["members"]["img002"]), 1)

    def test_images_that_share_nothing_are_never_matched(self):
        self.room()
        self.image("img003", [(1, "parquet floor", None, {"category": "architecture"}),
                              (2, "oak table", 1, {"category": "furniture"}),
                              (3, "blue mug", 2)])
        _, _, data, _ = self.auto(pairs=[("img001", "img002", "partial-overlap"),
                                         ("img001", "img003", "close-up"),
                                         ("img002", "img003", "no-overlap")])
        for match in data["matched"]:
            images = {m["image_id"] for m in match["members"]}
            self.assertFalse({"img002", "img003"} <= images and len(images) == 2,
                             "two images registration says do not overlap were matched directly")

    def test_a_three_view_object_is_matched_through_direct_comparisons_only(self):
        self.room()
        self.image("img003", [(1, "parquet floor", None, {"category": "architecture"}),
                              (2, "oak table", 1, {"category": "furniture"}),
                              (3, "blue mug", 2)])
        _, _, data, _ = self.auto(pairs=[("img001", "img002", "partial-overlap"),
                                         ("img001", "img003", "close-up"),
                                         ("img002", "img003", "no-overlap")])
        mug = next(m for m in data["matched"] if m["label"] == "blue mug")
        self.assertEqual({m["image_id"] for m in mug["members"]}, {"img001", "img002", "img003"})

    def test_no_global_object_holds_two_objects_from_one_image(self):
        self.room()
        _, _, data, _ = self.auto(pairs=[("img001", "img002", "partial-overlap")])
        for match in data["matched"]:
            images = [m["image_id"] for m in match["members"]]
            self.assertEqual(len(images), len(set(images)))

    def test_a_different_category_does_not_stop_a_match(self):
        """Two agents file one worktop as architecture and as furniture; that stranded
        everything on it in a real run."""
        self.image("img001", [(1, "floor", None, {"category": "architecture"}),
                              (2, "worktop", 1, {"category": "architecture"}), (3, "kettle", 2)])
        self.image("img002", [(1, "floor", None, {"category": "architecture"}),
                              (2, "worktop", 1, {"category": "furniture"}), (3, "kettle", 2)])
        _, _, data, _ = self.auto(pairs=[("img001", "img002", "partial-overlap")])
        self.assertIn("worktop", self.matched_labels(data))
        self.assertIn("kettle", self.matched_labels(data))

    def test_a_shared_word_does_not_make_two_different_cases_look_alike(self):
        """'blue case' is not 'earbud charging case', and the second must still be unique."""
        self.image("img001", [(1, "floor", None, {"category": "architecture"}),
                              (2, "table", 1), (3, "earbud charging case", 2), (4, "blue case", 2)])
        self.image("img002", [(1, "floor", None, {"category": "architecture"}),
                              (2, "table", 1), (3, "earbud charging case", 2)])
        _, _, data, _ = self.auto(pairs=[("img001", "img002", "close-up")])
        self.assertIn("earbud charging case", self.matched_labels(data))

    def test_parents_that_agree_by_name_let_the_cascade_continue(self):
        """'kitchen splashback' and 'splashback panel' are one wall, matched or not."""
        self.image("img001", [(1, "floor", None, {"category": "architecture"}),
                              (2, "back wall", None, {"category": "architecture"}),
                              (3, "kitchen splashback", 2), (4, "double socket", 3)])
        self.image("img002", [(1, "floor", None, {"category": "architecture"}),
                              (2, "back wall", None, {"category": "architecture"}),
                              (3, "splashback panel", 2), (4, "double socket", 3),
                              (5, "splashback panel", 2)])
        _, _, data, _ = self.auto(pairs=[("img001", "img002", "partial-overlap")])
        socket = next((m for m in data["matched"] if m["label"] == "double socket"), None)
        self.assertIsNotNone(socket, "the socket stayed unmatched behind its parent")
        self.assertEqual(socket["confidence"], "medium")

    def test_a_small_group_is_kept_whole_so_a_label_mismatch_still_reaches_an_agent(self):
        self.image("img001", [(1, "floor", None, {"category": "architecture"}),
                              (2, "table", 1), (3, "small black device", 2)])
        self.image("img002", [(1, "floor", None, {"category": "architecture"}),
                              (2, "table", 1), (3, "wristwatch", 2)])
        _, _, data, _ = self.auto(pairs=[("img001", "img002", "close-up")])
        group = next(g for g in data["groups"] if g["carrier"] == "table")
        self.assertEqual(len(group["members"]["img001"]), 1)
        self.assertEqual(len(group["members"]["img002"]), 1)

    def test_a_big_group_is_pruned_to_plausible_counterparts(self):
        a = [(1, "floor", None, {"category": "architecture"}), (2, "table", 1)]
        b = [(1, "floor", None, {"category": "architecture"}), (2, "table", 1)]
        for n in range(3, 15):
            a.append((n, f"widget{'x' * n}", 2))           # twelve things nothing matches
        a.append((20, "red kettle", 2))
        a.append((21, "red kettle holder", 2))
        b.append((3, "kettle", 2))
        b.append((4, "kettle stand", 2))
        for n in range(5, 15):
            b.append((n, f"gadget{'y' * n}", 2))
        self.image("img001", a)
        self.image("img002", b)
        _, _, data, _ = self.auto(pairs=[("img001", "img002", "partial-overlap")])
        group = next(g for g in data["groups"] if g["carrier"] == "table")
        self.assertLess(len(group["members"]["img001"]), 6, "the unrelated widgets were all sent")

    def test_groups_are_spread_over_at_most_the_asked_number_of_batches(self):
        self.room()
        _, _, data, _ = self.auto("--max-batches", "1",
                                  pairs=[("img001", "img002", "partial-overlap")])
        self.assertLessEqual(len(data["batches"]), 1)
        placed = [g for b in data["batches"] for g in b["groups"]]
        self.assertEqual(sorted(placed), sorted(g["group_id"] for g in data["groups"]),
                         "a group was left out of every batch")

    def test_a_missing_folder_exits_2(self):
        code, _, err = run(AUTO, "--structures", os.path.join(self.tmp, "nope"),
                           "--detections", self.det, "--out", os.path.join(self.tmp, "o.json"))
        self.assertEqual(code, 2)
        self.assertIn("no such folder", err)

    def test_it_will_not_overwrite_without_force(self):
        self.room()
        out = os.path.join(self.tmp, "auto.json")
        args = ("--structures", self.str, "--detections", self.det, "--out", out)
        run(AUTO, *args)
        code, _, err = run(AUTO, *args)
        self.assertEqual(code, 1)
        self.assertIn("--force", err)

    @unittest.skipIf(Image is None, "Pillow is not installed; contact sheets need it")
    def test_a_contact_sheet_is_written_for_every_group(self):
        self.room()
        for name in ("a.jpg", "b.jpg"):
            Image.new("RGB", (800, 600), (50, 60, 70)).save(os.path.join(self.tmp, name))
        manifest = os.path.join(self.tmp, "manifest.json")
        with open(manifest, "w", encoding="utf-8") as f:
            json.dump({"images": [{"image_id": "img001", "path": "a.jpg"},
                                  {"image_id": "img002", "path": "b.jpg"}]}, f)
        sheets = os.path.join(self.tmp, "sheets")
        _, report, data, _ = self.auto("--manifest", manifest, "--sheets", sheets,
                                       pairs=[("img001", "img002", "partial-overlap")])
        self.assertEqual(report["sheets"], len(data["groups"]))
        for group in data["groups"]:
            self.assertTrue(os.path.exists(group["sheet"]))


class ChairsAcrossViewsTests(Scene):
    """The regression this stage exists for: two chairs, photographed twice, are two chairs.

    A live run counted three. The floors were called 'wood floor' and 'parquet floor' and were
    never matched, and the wide shot's two chairs had already been placed in a group against a
    photograph with no chair in it, so they were never offered against the close-up's chair.
    """

    def setUp(self):
        super().setUp()
        self.image("img001", [(1, "wood floor", None, {"category": "architecture"}),
                              (2, "wishbone chair", 1), (3, "wishbone chair", 1)])
        self.image("img002", [(1, "oak floor", None, {"category": "architecture"})])
        self.image("img003", [(1, "parquet floor", None, {"category": "architecture"}),
                              (2, "wishbone chair", 1)])
        self.pairs = [("img001", "img002", "partial-overlap"), ("img001", "img003", "close-up"),
                      ("img002", "img003", "no-overlap")]

    def test_floors_with_different_qualifiers_are_matched_as_the_same_kind_of_thing(self):
        _, _, data, _ = self.auto(pairs=self.pairs)
        floor = next(m for m in data["matched"] if "floor" in m["label"])
        self.assertEqual({m["image_id"] for m in floor["members"]}, {"img001", "img002", "img003"})
        self.assertEqual(floor["confidence"], "medium", "a match on the kind alone is not high")
        self.assertTrue(any("same kind of thing" in line for line in floor["evidence"]))

    def test_the_wide_shots_chairs_are_offered_against_the_close_ups_chair(self):
        _, _, data, _ = self.auto(pairs=self.pairs)
        offered = [g for g in data["groups"] if "img003" in g["images"]
                   and any("chair" in m["label"] for m in g["members"].get("img003", []))]
        self.assertTrue(offered, "the close-up's chair was never put in front of anyone")
        group = offered[0]
        self.assertEqual(len([m for m in group["members"]["img001"] if "chair" in m["label"]]), 2)

    def test_chairs_nobody_decided_still_count_as_two(self):
        """An agent that says nothing about a group leaves its members as the floor, not as three."""
        _, _, data, _ = self.auto(pairs=self.pairs)
        auto_path = os.path.join(self.tmp, "auto.json")
        out = os.path.join(self.tmp, "matches.json")
        code, report, _ = run_json(BUILD, "--auto", auto_path, "--detections", self.det,
                                   "--out", out, "--force")
        self.assertEqual(code, 0, report)
        with open(out, encoding="utf-8") as f:
            matches = json.load(f)
        issue = next(u for u in matches["unresolved"] if "chair" in u["label"])
        self.assertEqual(len(issue["candidates"]), 3)
        self.assertEqual(issue["distinct_objects"], 2, "two in one photograph are certainly two")
        self.assertEqual(issue["decision"], "kept separate")
        self.assertTrue(issue["against"])
        code, report, _ = run_json(CHECK, out, "--structures", self.str)
        self.assertEqual(code, 0, report)

    def test_an_agents_own_refusal_is_not_duplicated_by_the_safety_net(self):
        _, _, data, _ = self.auto(pairs=self.pairs)
        decisions = os.path.join(self.tmp, "decisions.json")
        with open(decisions, "w", encoding="utf-8") as f:
            json.dump({"batch_id": "m1", "refusals": [{
                "candidates": ["img001-002", "img001-003", "img003-002"],
                "for": "same design", "against": "which is which cannot be told",
                "distinct_objects": 2}]}, f)
        out = os.path.join(self.tmp, "matches.json")
        run_json(BUILD, "--auto", os.path.join(self.tmp, "auto.json"), "--detections", self.det,
                 "--decisions", decisions, "--out", out, "--force")
        with open(out, encoding="utf-8") as f:
            matches = json.load(f)
        self.assertEqual(len([u for u in matches["unresolved"] if "chair" in u["label"]
                              or any("chair" in (c.get("local_id") or "") for c in u["candidates"])]), 1)
        self.assertEqual(len(matches["unresolved"]), 1)


class BuildMatchesTests(Scene):
    def setUp(self):
        super().setUp()
        self.image("img001", [(1, "floor", None, {"category": "architecture"}), (2, "table", 1),
                              (3, "oil bottle", 2), (4, "rum bottle", 2), (5, "wristwatch", 2)])
        self.image("img002", [(1, "floor", None, {"category": "architecture"}), (2, "table", 1),
                              (3, "oil bottle", 2), (4, "rum bottle", 2), (5, "small black device", 2)])
        _, _, self.autodata, _ = self.auto(pairs=[("img001", "img002", "partial-overlap")])
        self.auto_path = os.path.join(self.tmp, "auto.json")

    def decisions(self, **body):
        path = os.path.join(self.tmp, "decisions.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"batch_id": "m1", **body}, f)
        return path

    def build(self, *decisions, expect=None):
        out = os.path.join(self.tmp, "matches.json")
        code, report, err = run_json(BUILD, "--auto", self.auto_path, "--detections", self.det,
                                     "--decisions", *decisions, "--out", out, "--force")
        if expect is not None:
            self.assertEqual(code, expect, report)
        with open(out, encoding="utf-8") as f:
            return code, report, json.load(f), err

    def global_of(self, data, local_id):
        return next(o for o in data["objects"]
                    if any(m["local_id"] == local_id for m in o["members"]))

    def test_every_object_ends_up_in_exactly_one_global_object(self):
        _, _, data, _ = self.build()
        seen = [m["local_id"] for o in data["objects"] for m in o["members"]]
        self.assertEqual(len(seen), len(set(seen)))
        self.assertEqual(set(seen), {f"{i}-00{n}" for i in ("img001", "img002") for n in range(1, 6)})

    def test_an_agents_merge_with_two_lines_of_evidence_is_applied(self):
        path = self.decisions(merges=[{"members": ["img001-005", "img002-005"], "confidence": "medium",
                                       "evidence": ["both lie to the right of the rum bottle",
                                                    "the only black object on the table"]}])
        _, _, data, _ = self.build(path)
        merged = self.global_of(data, "img001-005")
        self.assertEqual({m["local_id"] for m in merged["members"]}, {"img001-005", "img002-005"})
        self.assertEqual(merged["confidence"], "medium")

    def test_a_merge_on_one_line_of_evidence_is_not_made(self):
        """One line is not enough. It becomes a refusal, not a quiet merge."""
        path = self.decisions(merges=[{"members": ["img001-005", "img002-005"], "confidence": "high",
                                       "evidence": ["they look alike"]}])
        code, _, data, _ = self.build(path)
        self.assertEqual(code, 1)
        self.assertEqual(len(self.global_of(data, "img001-005")["members"]), 1)
        self.assertEqual(len(data["unresolved"]), 1)

    def test_a_merge_of_two_objects_from_one_image_is_refused(self):
        path = self.decisions(merges=[{"members": ["img001-003", "img001-004", "img002-003"],
                                       "evidence": ["a", "b"]}])
        code, report, data, _ = self.build(path)
        self.assertEqual(code, 1)
        self.assertTrue(any("two objects from one image" in p for p in report["problems"]))

    def test_a_merge_that_contradicts_an_automatic_one_is_refused(self):
        self.assertTrue(any("oil bottle" == m["label"] for m in self.autodata["matched"]),
                        "the fixture should have matched the oil bottle by script")
        path = self.decisions(merges=[{"members": ["img001-003", "img002-004"],
                                       "evidence": ["a", "b"]}])
        code, report, _, _ = self.build(path)
        self.assertEqual(code, 1)
        self.assertTrue(report["problems"])

    def test_a_merge_naming_an_unknown_id_is_refused(self):
        path = self.decisions(merges=[{"members": ["img001-099", "img002-005"], "evidence": ["a", "b"]}])
        code, report, _, _ = self.build(path)
        self.assertEqual(code, 1)
        self.assertTrue(any("do not exist" in p for p in report["problems"]))

    def test_a_refusal_is_kept_with_a_floor_and_ceiling(self):
        path = self.decisions(refusals=[{"candidates": ["img001-005", "img002-005", "img001-003"],
                                         "for": "similar size", "against": "different colour",
                                         "distinct_objects": 99}])
        _, _, data, _ = self.build(path)
        issue = data["unresolved"][0]
        self.assertEqual(issue["decision"], "kept separate")
        self.assertGreaterEqual(issue["distinct_objects"], 2)       # two candidates share img001
        self.assertLessEqual(issue["distinct_objects"], 3)

    def test_a_refusal_with_nothing_against_is_given_an_honest_default(self):
        path = self.decisions(refusals=[{"candidates": ["img001-005", "img002-005"]}])
        _, _, data, _ = self.build(path)
        self.assertTrue(data["unresolved"][0]["against"])

    def test_corrections_need_two_different_images(self):
        path = self.decisions(corrections=[
            {"target": "img001-005", "better_view": "img002-005", "problem": "p", "shows": "s"},
            {"target": "img001-003", "better_view": "img001-004", "problem": "same image"}])
        code, report, data, _ = self.build(path)
        self.assertEqual(len(data["corrections"]), 1)
        self.assertEqual(code, 1)

    def test_the_result_passes_the_match_gate(self):
        path = self.decisions(
            merges=[{"members": ["img001-005", "img002-005"], "confidence": "medium",
                     "evidence": ["right of the rum bottle", "the only black object"]}],
            refusals=[{"candidates": ["img001-003", "img001-004"], "for": "both bottles",
                       "against": "different caps"}])
        self.build(path)
        code, report, _ = run_json(CHECK, os.path.join(self.tmp, "matches.json"),
                                   "--structures", self.str)
        self.assertEqual(code, 0, report)

    def test_with_no_decisions_everything_undecided_stays_separate(self):
        _, _, data, _ = self.build()
        self.assertEqual(len(self.global_of(data, "img001-005")["members"]), 1)


class ConfusionTests(unittest.TestCase):
    def test_it_collects_what_the_run_was_not_sure_of(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        matches = {"objects": [
            {"global_id": "g001", "label": "chair", "members": [{"image_id": "a", "local_id": "a-1"},
                                                                  {"image_id": "b", "local_id": "b-1"}],
             "confidence": "low", "evidence": ["x", "y"]},
            {"global_id": "g002", "label": "chair", "members": [{"image_id": "a", "local_id": "a-2"}]}],
            "unresolved": [{"issue_id": "u001", "candidates": [{"image_id": "a", "local_id": "a-1"},
                                                                {"image_id": "a", "local_id": "a-2"}]}],
            "corrections": [{"correction_id": "c001", "stage": "scene-decompose-detect",
                             "target": {"image_id": "a", "local_id": "a-1"},
                             "better_view": {"image_id": "b", "local_id": "b-1"}}]}
        graph = {"nodes": [{"global_id": "g002", "label": "chair", "support_inferred": True,
                            "parent": "g001", "relation": "on-top-of"}],
                 "identity_groups": [{"group_id": "ig001", "from": "u001"}], "parent_conflicts": []}
        scores = {"objects": [{"global_id": "g001", "label": "chair", "best_view": "a",
                               "decisive": False, "views": [{"image_id": "a", "score": 1, "share_of_best": 1.0},
                                                            {"image_id": "b", "score": 0.9, "share_of_best": 0.9}]}]}
        paths = {}
        for name, body in (("graph", graph), ("matches", matches), ("scores", scores)):
            paths[name] = os.path.join(tmp, f"{name}.json")
            with open(paths[name], "w", encoding="utf-8") as f:
                json.dump(body, f)
        code, report, _ = run_json(CONFUSION, "--graph", paths["graph"], "--matches", paths["matches"],
                                   "--scores", paths["scores"], "--out", os.path.join(tmp, "c.json"))
        self.assertEqual(code, 0)
        with open(os.path.join(tmp, "c.json"), encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["unresolved"][0]["global_ids"], ["g001", "g002"])
        self.assertEqual(data["unresolved"][0]["identity_group"], "ig001")
        self.assertEqual(data["corrections"][0]["owner_stage"], "scene-decompose-detect")
        self.assertEqual(report["low_confidence_merges"], 1)
        self.assertEqual(report["inferred_supports"], 1)
        self.assertEqual(report["close_view_choices"], 1)


if __name__ == "__main__":
    unittest.main()
