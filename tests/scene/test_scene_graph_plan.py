"""Maintainer checks for skills/core/marso-scene-graph/scripts/plan_assets.py.

Run from the repository root: python -m unittest discover tests/scene
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "core" / "marso-scene-graph" / "scripts"
PLAN = SCRIPTS / "plan_assets.py"
CROP = SCRIPTS / "crop_objects.py"

WIDTH, HEIGHT = 64, 48
BACKGROUND = (128, 128, 128)
BOWL = (0, 0, 255)
ONION = (255, 0, 0)
COUNTER = (200, 180, 120)

# Pixel boxes in the 64x48 fixture image, used by both test modules.
PX = {
    "g003": (0, 19, 38, 38),   # countertop
    "g004": (8, 12, 32, 30),   # bowl
    "g005": (12, 16, 20, 24),  # onion
    "g006": (22, 16, 30, 24),  # onion
    "g007": (42, 24, 51, 46),  # chair
    "g008": (53, 24, 62, 46),  # chair
}


def norm(box):
    x0, y0, x1, y1 = box
    return [x0 / WIDTH, y0 / HEIGHT, x1 / WIDTH, y1 / HEIGHT]


def view(image_id, local_id, box, **extra):
    row = {"image_id": image_id, "local_id": local_id, "bbox": norm(box), "occluded": False,
           "truncated": [], "id_confidence": "high", "frame_share": 0.01}
    row.update(extra)
    return row


def fixture_graph() -> dict:
    """A bowl with two onions on a countertop, and two identical chairs on the floor."""
    chair_size = {"w": 0.45, "d": 0.5, "h": 0.9}
    return {
        "schema": "scene-decompose/scene-graph@1",
        "bbox_convention": "normalised [x0,y0,x1,y1], 0-1 of the image, origin top-left",
        "images": ["img001", "img002"],
        "nodes": [
            {"global_id": "g001", "label": "floor", "description": "tiled floor", "category": "room shell",
             "parent": None, "relation": None, "size_m": {"w": 4.0, "d": 3.0, "h": 0.0},
             "size_confidence": "medium", "size_basis": "room", "seen_in": 1,
             "views": [view("img001", "o1", (0, 24, 64, 48))]},
            {"global_id": "g002", "label": "wall", "description": "painted wall", "category": "room shell",
             "parent": None, "relation": None, "size_m": {"w": 4.0, "d": 0.1, "h": 2.4},
             "size_confidence": "medium", "size_basis": "room", "seen_in": 1,
             "views": [view("img001", "o2", (0, 0, 64, 24))]},
            {"global_id": "g003", "label": "countertop", "description": "fitted worktop", "category": "fitted kitchen",
             "parent": "g001", "relation": "on-top-of", "size_m": {"w": 2.0, "d": 0.6, "h": 0.9},
             "size_confidence": "high", "size_basis": "standard worktop height", "seen_in": 1,
             "views": [view("img001", "o3", PX["g003"])]},
            {"global_id": "g004", "label": "bowl", "description": "glazed ceramic bowl", "category": "vessels",
             "parent": "g003", "relation": "on-top-of", "size_m": {"w": 0.3, "d": 0.3, "h": 0.12},
             "size_confidence": "high", "size_basis": "onions inside it", "seen_in": 1,
             "views": [view("img001", "o4", PX["g004"])]},
            {"global_id": "g005", "label": "onion", "description": "brown onion", "category": "food",
             "parent": "g004", "relation": "inside", "size_m": {"w": 0.08, "d": 0.08, "h": 0.08},
             "size_confidence": "high", "size_basis": "typical onion", "seen_in": 1,
             "views": [view("img001", "o5", PX["g005"])]},
            {"global_id": "g006", "label": "onion", "description": "brown onion", "category": "food",
             "parent": "g004", "relation": "inside", "size_m": {"w": 0.08, "d": 0.08, "h": 0.08},
             "size_confidence": "high", "size_basis": "typical onion", "seen_in": 1,
             "views": [view("img001", "o6", PX["g006"])]},
            {"global_id": "g007", "label": "chair", "description": "wooden dining chair", "category": "seating",
             "parent": "g001", "relation": "on-top-of", "size_m": chair_size,
             "size_confidence": "medium", "size_basis": "seat height", "seen_in": 1,
             "views": [view("img001", "o7", PX["g007"])]},
            {"global_id": "g008", "label": "chair", "description": "wooden dining chair", "category": "seating",
             "parent": "g001", "relation": "on-top-of", "size_m": chair_size,
             "size_confidence": "medium", "size_basis": "seat height", "seen_in": 1,
             "views": [view("img001", "o8", PX["g008"], occluded=True)]},
            {"global_id": "g009", "label": "chair", "description": "wooden dining chair", "category": "seating",
             "parent": "g001", "relation": "on-top-of", "size_m": chair_size,
             "size_confidence": "medium", "size_basis": "seat height", "seen_in": 1,
             "views": [view("img002", "o1", (10, 4, 50, 46), id_confidence="low")]},
        ],
        "clusters": [
            {"cluster_id": "cl001", "label": "chairs", "members": ["g007", "g008", "g009"],
             "kind": "instances", "seen_in": ["img001", "img002"]},
            {"cluster_id": "cl002", "label": "onions", "members": ["g005", "g006"],
             "kind": "instances", "seen_in": ["img001"]},
        ],
        "areas": [],
        "identity_groups": [
            {"group_id": "ig001", "members": ["g008", "g009"], "distinct": 1, "at_least": 1,
             "at_most": 2, "basis": "the close-up could be either chair"},
        ],
        "parent_conflicts": [],
    }


def write_fixture(folder: pathlib.Path) -> dict[str, pathlib.Path]:
    """Write the graph, a manifest and the 64x48 PNG; return their paths."""
    from PIL import Image, ImageDraw

    graph_path = folder / "scene_graph.json"
    graph_path.write_text(json.dumps(fixture_graph(), indent=2), encoding="utf-8")

    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.rectangle((PX["g003"][0], PX["g003"][1], PX["g003"][2] - 1, PX["g003"][3] - 1), fill=COUNTER)
    draw.rectangle((PX["g004"][0], PX["g004"][1], PX["g004"][2] - 1, PX["g004"][3] - 1), fill=BOWL)
    for gid in ("g005", "g006"):
        box = PX[gid]
        draw.rectangle((box[0], box[1], box[2] - 1, box[3] - 1), fill=ONION)
    image_path = folder / "img001.png"
    image.save(image_path)

    manifest_path = folder / "manifest.json"
    manifest_path.write_text(json.dumps({
        "schema": "scene-decompose/manifest@1",
        "images": [{"image_id": "img001", "path": "img001.png", "width": WIDTH, "height": HEIGHT}],
    }), encoding="utf-8")
    return {"graph": graph_path, "image": image_path, "manifest": manifest_path, "folder": folder}


def run(script: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)


def by_label(plan: dict) -> dict[str, dict]:
    return {a["label"]: a for a in plan["assets"]}


class PlanAssetsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = pathlib.Path(self.tmp.name)
        self.graph = self.folder / "scene_graph.json"
        self.graph.write_text(json.dumps(fixture_graph()), encoding="utf-8")
        self.out = self.folder / "asset_plan.json"

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self) -> dict:
        result = run(PLAN, str(self.graph), "--out", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["unique_assets"], 4)
        return json.loads(self.out.read_text(encoding="utf-8"))

    def test_counts_and_members(self):
        plan = self.plan()
        self.assertEqual(plan["schema"], "marso/asset-plan@1")
        assets = by_label(plan)
        self.assertEqual(set(assets), {"countertop", "bowl", "onion", "chair"})
        chairs = assets["chair"]
        self.assertEqual(chairs["members"], ["g007", "g008", "g009"])
        self.assertEqual((chairs["count"], chairs["count_at_least"], chairs["count_at_most"]), (2, 2, 3))
        self.assertEqual(chairs["cluster_id"], "cl001")
        self.assertEqual(chairs["identity_groups"], ["ig001"])
        onions = assets["onion"]
        self.assertEqual(onions["count"], 2)
        self.assertEqual(onions["members"], ["g005", "g006"])
        self.assertEqual(assets["bowl"]["children"], ["g005", "g006"])
        self.assertEqual(assets["bowl"]["parent"], "g003")
        self.assertEqual(assets["bowl"]["relation"], "on-top-of")
        self.assertEqual([a["global_id"] for a in plan["anchors"]], ["g001", "g002"])
        self.assertEqual(plan["summary"]["instances"], 6)
        self.assertEqual(plan["summary"]["instances_at_most"], 7)
        self.assertEqual(plan["summary"]["anchors"], 2)

    def test_routes_and_flags(self):
        assets = by_label(self.plan())
        self.assertEqual(assets["countertop"]["route"], "model")
        self.assertEqual(assets["bowl"]["route"], "generate")
        self.assertEqual(assets["onion"]["route"], "generate")
        self.assertEqual(assets["chair"]["route"], "model")
        self.assertIn("instance 2", assets["chair"]["route_reason"])
        self.assertEqual(assets["bowl"]["flags"], [])
        self.assertEqual(assets["bowl"]["best_view"]["image_id"], "img001")
        self.assertEqual(assets["bowl"]["best_view"]["local_id"], "o4")
        self.assertEqual(assets["chair"]["best_view"]["local_id"], "o7")

    def test_scores_file_selects_best_view(self):
        scores = self.folder / "view_scores.json"
        scores.write_text(json.dumps({
            "schema": "scene-decompose/view-scores@1",
            "objects": [{"global_id": "g007", "best_view": "img001", "best_local_id": "o7"}],
        }), encoding="utf-8")
        result = run(PLAN, str(self.graph), "--scores", str(scores), "--out", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(by_label(plan)["chair"]["best_view"]["local_id"], "o7")

    def test_a_mostly_hidden_member_borrows_its_twins_view(self):
        """The chair first in the cluster is mostly hidden; its clearly seen twin stands for the asset."""
        graph = fixture_graph()
        chair = next(n for n in graph["nodes"] if n["global_id"] == "g007")
        chair["occlusion"] = "heavy"
        chair["views"][0].update(occluded=True, occlusion="heavy")
        for node in graph["nodes"]:
            if node["global_id"] == "g008":
                node["occlusion"], node["views"][0]["occluded"] = "none", False
        self.graph.write_text(json.dumps(graph), encoding="utf-8")
        chairs = by_label(self.plan())["chair"]
        self.assertEqual(chairs["best_view"]["local_id"], "o8")
        self.assertEqual(chairs["occlusion"], "none")
        self.assertNotIn("mostly-hidden", chairs["flags"])

    def test_a_mostly_hidden_singleton_carries_its_inferred_whole(self):
        graph = fixture_graph()
        bowl = next(n for n in graph["nodes"] if n["label"] == "bowl")
        bowl["occlusion"] = "heavy"
        bowl["inferred_whole"] = {"whole_description": "white ceramic bowl, foot hidden",
                                  "visible": "the rim", "from": "img001"}
        self.graph.write_text(json.dumps(graph), encoding="utf-8")
        asset = by_label(self.plan())["bowl"]
        self.assertIn("mostly-hidden", asset["flags"])
        self.assertNotIn("no-inferred-whole", asset["flags"])
        self.assertEqual(asset["inferred_whole"]["visible"], "the rim")

    def test_routes_match_whole_words_and_numeric_sizes(self):
        """'tableware' is not a table and 'woven' is not an oven; a 0.1 m mug is a prop."""
        graph = fixture_graph()
        graph["nodes"].append({"global_id": "g020", "label": "mug", "category": "tableware",
                               "parent": "g003", "relation": "on-top-of", "size_m": 0.1,
                               "views": [view("img001", "o20", (40, 2, 44, 6))]})
        graph["nodes"].append({"global_id": "g021", "label": "woven placemat", "category": "textile",
                               "parent": "g003", "relation": "on-top-of", "size_m": 0.35,
                               "views": [view("img001", "o21", (46, 2, 52, 6))]})
        self.graph.write_text(json.dumps(graph), encoding="utf-8")
        result = run(PLAN, str(self.graph), "--out", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        assets = by_label(json.loads(self.out.read_text(encoding="utf-8")))
        self.assertEqual(assets["mug"]["route"], "generate")
        self.assertEqual(assets["woven placemat"]["route"], "generate")
        self.assertNotIn("fallback-route", assets["mug"]["flags"])

    def test_a_cluster_and_an_identity_group_sharing_a_member_are_one_asset(self):
        """Two onions in one photograph, a third elsewhere that may be one of them: 2 to 3 onions."""
        graph = fixture_graph()
        graph["nodes"].append({"global_id": "g030", "label": "onion", "category": "food",
                               "parent": "g003", "relation": "on-top-of", "size_m": 0.08,
                               "views": [view("img002", "o30", (2, 2, 6, 6))]})
        for cluster in graph["clusters"]:          # the graph's own key is cl_id
            if "g005" in cluster["members"]:
                cluster["cl_id"] = cluster.pop("cluster_id", cluster.get("cl_id"))
                onion_cluster = cluster["cl_id"]
        graph["identity_groups"].append({"group_id": "ig009", "members": ["g005", "g030"],
                                         "distinct": 1, "at_least": 1, "at_most": 2, "basis": "x"})
        self.graph.write_text(json.dumps(graph), encoding="utf-8")
        result = run(PLAN, str(self.graph), "--out", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(self.out.read_text(encoding="utf-8"))
        onions = [a for a in plan["assets"] if a["label"] == "onion"]
        self.assertEqual(len(onions), 1, [a["members"] for a in onions])
        self.assertEqual((onions[0]["count_at_least"], onions[0]["count_at_most"]), (2, 3))
        self.assertEqual(onions[0]["cluster_id"], onion_cluster)

    def test_an_unconfirmed_reading_is_listed_not_made(self):
        graph = fixture_graph()
        bowl = next(n for n in graph["nodes"] if n["label"] == "bowl")
        bowl["unconfirmed"] = {"closer_view": "img002", "reason": "not in the close-up"}
        self.graph.write_text(json.dumps(graph), encoding="utf-8")
        result = run(PLAN, str(self.graph), "--out", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertNotIn("bowl", {a["label"] for a in plan["assets"]})
        self.assertEqual([u["label"] for u in plan["unconfirmed"]], ["bowl"])
        self.assertEqual(plan["summary"]["unconfirmed"], 1)
        self.assertEqual(plan["review"], [])

    def test_low_confidence_flag(self):
        graph = fixture_graph()
        graph["nodes"][3]["views"][0]["id_confidence"] = "low"
        graph["nodes"][3]["size_confidence"] = "low"
        self.graph.write_text(json.dumps(graph), encoding="utf-8")
        plan = self.plan()
        self.assertEqual(by_label(plan)["bowl"]["flags"], ["low-id-confidence", "low-size-confidence"])
        self.assertIn(by_label(plan)["bowl"]["asset_id"], plan["summary"]["flagged"])

    def test_exit_codes(self):
        bad = self.folder / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        self.assertEqual(run(PLAN, str(bad), "--out", str(self.out)).returncode, 2)
        self.assertEqual(run(PLAN, str(self.folder / "missing.json"), "--out", str(self.out)).returncode, 2)
        empty = self.folder / "empty.json"
        empty.write_text(json.dumps({"schema": "scene-decompose/scene-graph@1", "nodes": []}), encoding="utf-8")
        self.assertEqual(run(PLAN, str(empty), "--out", str(self.out)).returncode, 1)
        self.assertEqual(run(PLAN, str(self.graph), "--out", str(self.out)).returncode, 0)
        self.assertEqual(run(PLAN, str(self.graph), "--out", str(self.out)).returncode, 1)
        self.assertEqual(run(PLAN, str(self.graph), "--out", str(self.out), "--force").returncode, 0)


if __name__ == "__main__":
    unittest.main()
