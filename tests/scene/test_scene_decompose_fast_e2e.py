"""The fast path, end to end, with the agents played by this test.

The agents are the only part that needs a model. Everything around them is scripts, and
nearly every bug in the last pipeline was in that bookkeeping, so this runs the whole chain
with synthetic agent output: tile the photographs, write the briefs, merge the tiles into
detections and trees, pair what is obvious, hand the residue to a "judge", and build the graph
and the viewer. If the scripts disagree about a file's shape, it shows up here.
"""
import json
import os
import shutil
import tempfile
import unittest

from helpers import SKILL as SKILL_DIR, SCRIPTS as SCRIPTS_DIR, ROOT, run, run_json

LEAD = SCRIPTS_DIR
FAST = os.path.join(LEAD, "fast.py")
PLAN = os.path.join(LEAD, "plan_fast.py")

try:
    from PIL import Image
except ImportError:                                    # pragma: no cover
    Image = None


def local(box, region):
    """A box in the photograph, in 0-1 of the tile that shows `region`."""
    x0, y0, x1, y1 = region
    w, h = x1 - x0, y1 - y0
    return [round((box[0] - x0) / w, 5), round((box[1] - y0) / h, 5),
            round((box[2] - x0) / w, 5), round((box[3] - y0) / h, 5)]


def inside(box, region):
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    return region[0] <= cx <= region[2] and region[1] <= cy <= region[3]


def thing(label, box, **extra):
    out = {"label": label, "description": label, "category": "kitchenware",
           "size_m": 0.2, "size_basis": "relative to the worktop", "id_confidence": "high"}
    out.update(extra)
    return out, box


SCENE = {
    "img001": [thing("parquet floor", [0.0, 0.55, 1.0, 1.0], category="architecture", size_m=4),
               thing("stone worktop", [0.10, 0.45, 0.90, 0.58], category="furniture", surface=True),
               thing("steel kettle", [0.30, 0.34, 0.36, 0.46], on="stone worktop"),
               thing("clear bottle", [0.50, 0.30, 0.53, 0.46], on="stone worktop"),
               thing("clear bottle", [0.56, 0.30, 0.59, 0.46], on="stone worktop")],
    "img002": [thing("parquet floor", [0.0, 0.55, 1.0, 1.0], category="architecture", size_m=4),
               thing("stone worktop", [0.12, 0.46, 0.92, 0.59], category="furniture", surface=True),
               thing("steel kettle", [0.32, 0.35, 0.38, 0.47], on="stone worktop"),
               thing("clear bottle", [0.52, 0.31, 0.55, 0.47], on="stone worktop"),
               thing("clear bottle", [0.58, 0.31, 0.61, 0.47], on="stone worktop")],
}


@unittest.skipIf(Image is None, "Pillow is not installed; the fast path needs it")
class FastPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        os.makedirs(os.path.join(self.tmp, "images"))
        for name, colour in (("a.jpg", (90, 70, 50)), ("b.jpg", (60, 80, 90))):
            Image.new("RGB", (3200, 2400), colour).save(os.path.join(self.tmp, "images", name))
        self.run_dir = os.path.join(self.tmp, "runs", "e2e")

    def fast(self, *args):
        return run_json(FAST, *args, cwd=self.tmp)

    def start(self):
        code, report, err = self.fast("start", "--run", self.run_dir, "--images", "images")
        self.assertEqual(code, 0, (report, err))
        return report

    def agents(self, round_name):
        code, report, err = run_json(PLAN, round_name, "--run", self.run_dir, cwd=self.tmp)
        self.assertEqual(code, 0, (report, err))
        return report["agents"]

    def play_detect_agents(self, agents):
        """Write each agent's file as a model would, for what its picture shows."""
        with open(os.path.join(self.run_dir, "tiles", "tiles.json"), encoding="utf-8") as f:
            plan = json.load(f)
        for agent in agents:
            if agent["name"] == "register":
                continue
            image_id, _, part = agent["name"].partition("-")
            entry = plan["images"][image_id]
            tile = next((t for t in entry["tiles"] if t["tile_id"] == part), None)
            region = tile["region"] if tile else [0.0, 0.0, 1.0, 1.0]
            objects = []
            for item, box in SCENE[image_id]:
                big = item["category"] == "architecture" or item["label"] == "stone worktop"
                if part == "whole" and not big:
                    continue
                if part != "whole" and big:
                    continue
                if tile and not inside(box, region):
                    continue
                objects.append({**item, "bbox": local(box, region)})
            # something different in every tile, so none is flagged as having found nothing
            # and none of the fillers is a lookalike of another
            filler = {"whole": "wall clock", "t1": "stapler", "t2": "ruler", "t3": "eraser",
                      "t4": "pencil"}[part]
            objects.append({"label": filler, "category": "paper", "size_m": 0.2,
                            "size_basis": "x", "bbox": [0.45, 0.45, 0.55, 0.55],
                            "on": "parquet floor"})
            with open(agent["writes"], "w", encoding="utf-8") as f:
                json.dump({"schema": "scene-decompose/detections@1", "image_id": image_id,
                           "objects": objects}, f)

    def test_the_whole_chain_runs_and_builds_a_valid_graph_and_viewer(self):
        report = self.start()
        self.assertEqual(report["images"], 2)
        self.assertEqual(report["tiles"], 8)

        agents = self.agents("detect")
        self.assertEqual(len(agents), 11, "register + a whole and four tile agents per image")
        names = {a["name"] for a in agents}
        self.assertIn("img001-whole", names)
        self.assertIn("img002-t4", names)
        tile_prompt = next(a["prompt"] for a in agents if a["name"] == "img001-t2")
        self.assertIn("0 to 1 of THIS crop", tile_prompt)
        self.assertIn("img001.t2.json", tile_prompt)
        self.play_detect_agents(agents)

        code, report, err = self.fast("detect", "--run", self.run_dir)
        self.assertEqual(code, 0, (report, err))
        for image_id in ("img001", "img002"):
            info = report["images"][image_id]
            self.assertEqual(info["detections_gate"], 0, info)
            self.assertEqual(info["structure_gate"], 0, info)
            self.assertTrue(os.path.exists(info["overlay"]), "one overlay per image to look at")
        with open(os.path.join(self.run_dir, "detections", "img001.json"), encoding="utf-8") as f:
            det = json.load(f)
        by = {o["label"]: o for o in det["objects"]}
        kettle = by["steel kettle"]
        # the tile-to-photograph mapping put the kettle back where the scene says it is
        for got, want in zip(kettle["bbox"], [0.30, 0.34, 0.36, 0.46]):
            self.assertAlmostEqual(got, want, places=2)
        self.assertEqual(kettle["parent"], by["stone worktop"]["local_id"])
        self.assertEqual(by["stone worktop"]["parent"], by["parquet floor"]["local_id"])
        # both bottles survived: two of the same name side by side are two objects
        self.assertEqual(len([o for o in det["objects"] if o["label"] == "clear bottle"]), 2)

        with open(os.path.join(self.run_dir, "registration.json"), "w", encoding="utf-8") as f:
            json.dump({"pairs": [{"a": "img001", "b": "img002", "relation": "partial-overlap"}],
                       "establishing_view": "img001"}, f)

        # the verify round: one agent per photograph; here they find nothing to fix
        code, report, err = self.fast("verify-plan", "--run", self.run_dir)
        self.assertEqual(code, 0, (report, err))
        self.assertEqual(report["count"], 2)
        for agent in report["agents"]:
            with open(agent["writes"], "w", encoding="utf-8") as f:
                json.dump({"renames": [], "remove": [], "same_as": []}, f)
        code, report, err = self.fast("verify", "--run", self.run_dir)
        self.assertEqual(code, 0, (report, err))
        self.assertEqual((report["renamed"], report["removed"], report["joined"]), (0, 0, 0))

        code, report, err = self.fast("match-plan", "--run", self.run_dir)
        self.assertEqual(code, 0, (report, err))
        self.assertGreaterEqual(report["automatic_matches"], 2, "floor, worktop and kettle")
        self.assertEqual(report["count"], 1, "one batch: the two bottles are a lookalike group")
        brief = report["agents"][0]["brief_file"]
        with open(brief, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("clear bottle", text)
        self.assertIn("A merge needs two independent lines of evidence", text)
        self.assertTrue(any(os.path.exists(os.path.join(self.run_dir, "match", "sheets", n))
                            for n in os.listdir(os.path.join(self.run_dir, "match", "sheets"))))

        # the judging agent refuses the bottles, which look alike, and merges nothing else
        ids = [o["local_id"] for i in ("img001", "img002") for o in
               json.load(open(os.path.join(self.run_dir, "detections", f"{i}.json"),
                              encoding="utf-8"))["objects"] if o["label"] == "clear bottle"]
        with open(os.path.join(self.run_dir, "match", "decisions.m1.json"), "w", encoding="utf-8") as f:
            json.dump({"batch_id": "m1", "merges": [],
                       "refusals": [{"candidates": ids, "for": "same shape", "against":
                                     "which is which cannot be told from the views", "distinct_objects": 2}]}, f)

        code, report, err = self.fast("graph", "--run", self.run_dir)
        self.assertEqual(code, 0, (report, err))
        self.assertEqual(report["refusals"], 1)
        nodes = json.load(open(os.path.join(self.run_dir, "scene_graph.json"), encoding="utf-8"))["nodes"]
        # Two bottle candidates refused as two real bottles: the node count is the ceiling too.
        self.assertEqual(report["physical_objects"]["at_most"], len(nodes))
        self.assertLessEqual(report["physical_objects"]["at_least"], len(nodes))
        self.assertEqual(report["validate_graph_exit"], 0)
        self.assertTrue(os.path.exists(os.path.join(self.run_dir, "viewer.html")))
        self.assertEqual(report["identity_groups"], 1)
        self.assertIn("graph", report["phases"])
        with open(os.path.join(self.run_dir, "matches.json"), encoding="utf-8") as f:
            matches = json.load(f)
        merged = [o for o in matches["objects"] if len(o["members"]) > 1]
        self.assertTrue(any(o["label"] == "steel kettle" for o in merged))
        for o in merged:
            self.assertGreaterEqual(len(o["evidence"]), 2)
        with open(os.path.join(self.run_dir, "fast.json"), encoding="utf-8") as f:
            clock = json.load(f)
        self.assertEqual({"start", "detect", "verify-plan", "verify", "match-plan", "graph"},
                         set(clock["phases"]))

    def test_a_missing_tile_is_named_so_only_it_is_run_again(self):
        self.start()
        agents = self.agents("detect")
        self.play_detect_agents(agents)
        os.remove(os.path.join(self.run_dir, "parts", "img002.t3.json"))
        code, report, _ = self.fast("detect", "--run", self.run_dir)
        self.assertEqual(code, 1)
        self.assertEqual(report["needs_retry"], ["img002.t3.json"])
        again = self.agents("detect")
        self.assertEqual([a["name"] for a in again if a["name"] != "register"], ["img002-t3"],
                         "a tile that already has a result must not be sent out again")

    def test_match_plan_with_nothing_to_judge_says_so(self):
        """If the script matched everything there is no round B at all."""
        self.start()
        self.play_detect_agents(self.agents("detect"))
        # name the second bottle differently so nothing is ambiguous
        for image_id in ("img001", "img002"):
            for path in [os.path.join(self.run_dir, "parts", f"{image_id}.t{n}.json") for n in range(1, 5)]:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                seen = 0
                for o in data["objects"]:
                    if o["label"] == "clear bottle":
                        seen += 1
                        if seen == 2 or o["bbox"][0] > 0.5:
                            o["label"] = "rum flask"
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
        self.fast("detect", "--run", self.run_dir)
        with open(os.path.join(self.run_dir, "registration.json"), "w", encoding="utf-8") as f:
            json.dump({"pairs": [{"a": "img001", "b": "img002", "relation": "partial-overlap"}]}, f)
        code, report, _ = self.fast("match-plan", "--run", self.run_dir)
        self.assertEqual(code, 0)
        self.assertEqual(report["count"], 0)
        self.assertIn("nothing for an agent", report["next"])
        code, report, _ = self.fast("graph", "--run", self.run_dir)
        self.assertEqual(code, 0, report)

    def test_whole_image_mode_is_one_agent_per_image_with_context_pictures(self):
        """--grid 1x1: no tiles; each photograph is looked at whole, and so is matching."""
        code, report, err = self.fast("start", "--run", self.run_dir, "--images", "images",
                                      "--mode", "coarse")
        self.assertEqual(code, 0, (report, err))
        self.assertEqual(report["tiles"], 0)
        agents = self.agents("detect")
        self.assertEqual(sorted(a["name"] for a in agents), ["img001-whole", "img002-whole", "register"])
        whole = next(a["prompt"] for a in agents if a["name"] == "img001-whole")
        self.assertIn("**everything**", whole, "with no tile pass the whole agent is the only one looking")
        for agent in agents:
            if agent["name"] == "register":
                continue
            image_id = agent["name"].split("-")[0]
            objects = []
            for index, (item, box) in enumerate(SCENE[image_id]):
                objects.append({**item, "bbox": box})
            # forty-odd objects in one file is normal for a whole photograph, not "unfinished"
            for n in range(42):
                objects.append({"label": f"widget{'x' * n}", "category": "other", "size_m": 0.1,
                                "size_basis": "x", "on": "parquet floor",
                                "bbox": [0.01 * (n % 50), 0.9, 0.01 * (n % 50) + 0.005, 0.95]})
            with open(agent["writes"], "w", encoding="utf-8") as f:
                json.dump({"image_id": image_id, "objects": objects}, f)
        code, report, err = self.fast("detect", "--run", self.run_dir)
        self.assertEqual(code, 0, (report, err))
        self.assertFalse(any("unfinished" in f for f in report["flagged"]), report["flagged"])
        with open(os.path.join(self.run_dir, "registration.json"), "w", encoding="utf-8") as f:
            json.dump({"pairs": [{"a": "img001", "b": "img002", "relation": "partial-overlap"}]}, f)
        code, report, err = self.fast("match-plan", "--run", self.run_dir)
        self.assertEqual(code, 0, (report, err))
        self.assertEqual(report["count"], 1)
        with open(report["agents"][0]["brief_file"], encoding="utf-8") as f:
            brief = f.read()
        self.assertIn("Look at the whole photographs first", brief)
        context = os.path.join(self.run_dir, "match", "context")
        self.assertEqual(sorted(os.listdir(context)), ["m1.img001.jpg", "m1.img002.jpg"])
        self.assertIn("m1.img001.jpg", brief)

    def photos(self, count):
        folder = os.path.join(self.tmp, f"set{count}")
        os.makedirs(folder, exist_ok=True)
        for n in range(count):
            Image.new("RGB", (3200, 2400), (25 * n + 10, 200 - 20 * n, 40 + 15 * n)).save(os.path.join(folder, f"p{n}.jpg"))
        return os.path.relpath(folder, self.tmp)

    def start_mode(self, count, *extra):
        code, report, err = self.fast("start", "--run", self.run_dir, "--images", self.photos(count),
                                      *extra)
        self.assertEqual(code, 0, (report, err))
        return report

    def test_up_to_four_images_default_to_fine_and_five_or_more_to_coarse(self):
        """The recommendation: Fine finds the small things but starts five agents per image."""
        for count, expected in ((2, "fine"), (4, "fine"), (5, "coarse"), (8, "coarse")):
            with self.subTest(images=count):
                report = self.start_mode(count)
                self.assertEqual(report["mode"], expected, report["mode_reason"])
                self.assertEqual(report["tiles"], 0 if expected == "coarse" else 4 * count)
                self.assertIn(str(count), report["mode_reason"])

    def test_the_user_can_choose_either_mode_whatever_the_image_count(self):
        self.assertEqual(self.start_mode(6, "--mode", "fine")["mode"], "fine")
        self.assertEqual(self.start_mode(2, "--mode", "coarse")["mode"], "coarse")
        report = self.start_mode(2, "--mode", "coarse")
        self.assertEqual(report["tiles"], 0)
        self.assertIn("chosen by the user", report["mode_reason"])

    def test_the_report_names_the_other_mode_and_how_to_switch(self):
        report = self.start_mode(2)
        self.assertIn("Coarse", report["other_mode"])
        self.assertIn("--mode coarse", report["switch"])
        report = self.start_mode(6)
        self.assertIn("Fine", report["other_mode"])

    def test_switching_mode_is_a_clean_run_and_says_so(self):
        self.start_mode(2, "--mode", "fine")
        marker = os.path.join(self.run_dir, "detections")
        os.makedirs(marker, exist_ok=True)
        with open(os.path.join(marker, "img001.json"), "w", encoding="utf-8") as f:
            f.write("{}")
        with open(os.path.join(self.run_dir, "run.json"), "w", encoding="utf-8") as f:
            f.write("{}")
        same = self.start_mode(2, "--mode", "fine")
        self.assertEqual(same["cleared"], [])
        self.assertIsNone(same["notice"])
        self.assertTrue(os.path.exists(marker))
        report = self.start_mode(2, "--mode", "coarse")
        self.assertIn("detections", report["cleared"])
        self.assertIn("clean run", report["notice"])
        self.assertFalse(os.path.exists(marker))
        self.assertTrue(os.path.exists(os.path.join(self.run_dir, "run.json")))
        with open(os.path.join(self.run_dir, "fast.json"), encoding="utf-8") as f:
            self.assertEqual(list(json.load(f)["phases"]), ["start"])

    def test_the_mode_is_recorded_with_the_run(self):
        self.start_mode(5)
        with open(os.path.join(self.run_dir, "fast.json"), encoding="utf-8") as f:
            state = json.load(f)
        self.assertEqual(state["mode"], "coarse")
        self.assertEqual(state["grid"], "1x1")

    def test_a_grid_set_by_hand_overrides_the_mode(self):
        report = self.start_mode(2, "--grid", "3x2")
        self.assertEqual(report["tiles"], 12)
        self.assertEqual(report["mode"], "fine")

    def test_phases_that_need_an_earlier_one_say_so(self):
        code, _, err = run(FAST, "detect", "--run", os.path.join(self.tmp, "nothing"), cwd=self.tmp)
        self.assertEqual(code, 2)
        self.assertIn("has the earlier step run", err)


if __name__ == "__main__":
    unittest.main()
