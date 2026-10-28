"""Maintainer checks for skills/blender/marso-blender-scene-assets/scripts/manifest.py.

Run from the repository root: python -m unittest discover tests/scene
"""
from __future__ import annotations

import json
import pathlib
import tempfile
import unittest

try:
    from test_scene_graph_plan import PLAN, fixture_graph, run
except ImportError:  # run as a package module rather than by discovery
    from tests.scene.test_scene_graph_plan import PLAN, fixture_graph, run

REPO = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = REPO / "skills" / "blender" / "marso-blender-scene-assets" / "scripts" / "manifest.py"
REFERENCE = {"crop_asset_id": "c1", "image_node_id": "n1", "generation_node_id": "gn1",
             "image_asset_id": "ia1", "image_path": "ref.png"}


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = pathlib.Path(self.tmp.name)
        graph = self.folder / "scene_graph.json"
        graph.write_text(json.dumps(fixture_graph()), encoding="utf-8")
        self.plan = self.folder / "asset_plan.json"
        result = run(PLAN, str(graph), "--out", str(self.plan), "--polycount", "by-size")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(self.plan.read_text(encoding="utf-8"))
        self.ids = {a["label"]: a["asset_id"] for a in plan["assets"]}
        # A references index as the crop step writes it, for the two generated assets.
        rows = []
        for label in ("bowl", "onion"):
            asset_id = self.ids[label]
            brief = self.folder / "references" / asset_id / "brief.json"
            brief.parent.mkdir(parents=True)
            brief.write_text(json.dumps({"prompt": f"Generate the {label} shown in @crop"}), encoding="utf-8")
            rows.append({"asset_id": asset_id, "label": label, "crop": str(brief.parent / "crop.png"),
                         "search_crop": str(brief.parent / "search.png"), "brief": str(brief)})
        self.index = self.folder / "references" / "index.json"
        self.index.write_text(json.dumps({"assets": rows}), encoding="utf-8")
        self.out = self.folder / "runs" / "kitchen" / "assets.json"

    def tearDown(self):
        self.tmp.cleanup()

    def mf(self, *args: str):
        return run(MANIFEST, *args)

    def init(self, *extra: str) -> dict:
        result = self.mf("init", str(self.plan), "--references", str(self.index), "--out", str(self.out),
                         "--project", "kitchen_test", *extra)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(self.out.read_text(encoding="utf-8"))

    def pending(self, stage=None) -> dict:
        args = ["pending", str(self.out)] + (["--stage", stage] if stage else [])
        result = self.mf(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_init_records_the_plan_and_briefs(self):
        doc = self.init()
        self.assertEqual(doc["schema"], "marso/scene-assets@1")
        self.assertEqual(doc["project"], "kitchen_test")
        assets = {a["label"]: a for a in doc["assets"]}
        self.assertEqual(set(assets), {"bowl", "onion"})
        onion = assets["onion"]
        self.assertEqual(onion["members"], ["g005", "g006"])
        self.assertEqual(onion["count"], 2)
        self.assertEqual(onion["prompt"], "Generate the onion shown in @crop")
        self.assertTrue(onion["brief"].endswith("brief.json"))
        # The plan's by-size budget wins over the default; the model and texture are the defaults.
        self.assertEqual(onion["settings"], {"model": "tripo_h3_1", "polygon_count": 40000,
                                             "texture": "standard"})
        self.assertEqual(assets["bowl"]["settings"]["polygon_count"], 50000)
        self.assertEqual(onion["minted"], "not_minted")
        # The library is checked first, with each asset's label and search crop.
        library = self.pending("library")
        self.assertEqual(library["pending"], sorted(self.ids[l] for l in ("bowl", "onion")))
        search = {row["query"]: row for row in library["library_searches"]}
        self.assertTrue(search["onion"]["image_path"].endswith("search.png"))
        self.assertEqual(self.pending("reference")["pending"], [])
        self.init("--skip-library", "--force")
        self.assertEqual(self.pending("reference")["pending"], sorted(self.ids[l] for l in ("bowl", "onion")))

    def test_init_refuses_to_overwrite_and_reports_bad_input(self):
        self.init()
        self.assertEqual(self.mf("init", str(self.plan), "--references", str(self.index),
                                 "--out", str(self.out)).returncode, 1)
        bad = self.folder / "bad.json"
        bad.write_text("{", encoding="utf-8")
        self.assertEqual(self.mf("init", str(bad), "--references", str(self.index), "--out",
                                 str(self.folder / "x.json")).returncode, 2)

    def test_the_stages_run_in_order(self):
        self.init("--skip-library")
        bowl, onion = self.ids["bowl"], self.ids["onion"]
        out = str(self.out)
        self.assertEqual(self.mf("record", out, "--stage", "reference", bowl, "--job", "job-1").returncode, 0)
        running = self.pending()["running"]["reference"]
        self.assertEqual(running, [{"asset_id": bowl, "job_id": "job-1"}])
        self.assertEqual(self.pending("reference")["pending"], [onion])
        # A get_job snapshot is unwrapped; a result missing a field is refused.
        snapshot = json.dumps({"status": "done", "result": REFERENCE})
        self.assertEqual(self.mf("record", out, "--stage", "reference", bowl, "--json", snapshot).returncode, 0)
        self.assertEqual(self.mf("record", out, "--stage", "reference", onion, "--json",
                                 json.dumps({"image_path": "x"})).returncode, 1)
        self.assertEqual(self.mf("record", out, "--stage", "reference", onion, "--json",
                                 json.dumps(REFERENCE)).returncode, 0)
        self.assertEqual(self.pending("review")["pending"], [bowl, onion])
        # No mesh before approval; a rejection sends the asset back for a new reference image.
        self.assertEqual(self.pending("mesh")["pending"], [])
        self.assertEqual(self.mf("review", out, "--approve", bowl, "--reject", onion, "--note",
                                 "the onion, not the bowl").returncode, 0)
        report = self.pending()
        self.assertEqual(report["pending"]["mesh"], [bowl])
        self.assertEqual(report["pending"]["reference"], [onion])
        self.assertEqual(self.mf("record", out, "--stage", "mesh", bowl, "--json",
                                 json.dumps({"mesh_node_id": "m", "pbr_node_id": "p", "pbr_asset_id": "PBR-1",
                                             "options": {}})).returncode, 0)
        mint = self.pending("mint")
        self.assertEqual(mint["pending"], [bowl])
        self.assertEqual(mint["mint_status_asset_ids"], ["PBR-1"])
        self.assertEqual(self.mf("record", out, "--stage", "mint", "--json",
                                 json.dumps({"PBR-1": "minting"})).returncode, 0)
        self.assertEqual(self.pending("mint")["pending"], [bowl])
        self.assertEqual(self.mf("record", out, "--stage", "mint", "--json",
                                 json.dumps({"PBR-1": "minted", "PBR-9": "minted"})).returncode, 1)
        self.assertEqual(self.pending("import")["pending"], [bowl])
        self.assertEqual(self.mf("record", out, "--stage", "import", bowl, "--json",
                                 json.dumps({"objects": ["bowl"], "dimensions_m": [0.3, 0.3, 0.12],
                                             "minted": True})).returncode, 0)
        report = self.pending()
        self.assertEqual(report["done"], [bowl])
        doc = json.loads(self.out.read_text(encoding="utf-8"))
        recorded = {a["asset_id"]: a for a in doc["assets"]}[bowl]
        self.assertEqual(recorded["pbr_asset_id"], "PBR-1")
        self.assertEqual(recorded["reference"]["image_asset_id"], "ia1")
        self.assertEqual(recorded["import"]["dimensions_m"], [0.3, 0.3, 0.12])
        self.assertTrue(doc["log"])

    def test_failures_and_unknown_assets(self):
        self.init("--skip-library")
        bowl = self.ids["bowl"]
        out = str(self.out)
        self.assertEqual(self.mf("record", out, "--stage", "reference", bowl, "--error", "timed out").returncode, 0)
        report = self.pending()
        self.assertEqual(report["failed"]["reference"], [{"asset_id": bowl, "error": "timed out"}])
        self.assertIn(bowl, report["pending"]["reference"])
        self.assertEqual(self.mf("record", out, "--stage", "reference", "a999", "--job", "j").returncode, 1)
        self.assertEqual(self.mf("review", out, "--approve", bowl).returncode, 1)  # no image yet
        self.assertEqual(self.mf("record", out, "--stage", "mesh", "--job", "j").returncode, 1)  # no asset id

    def test_a_library_match_is_reused_and_a_miss_is_made(self):
        self.init()
        bowl, onion = self.ids["bowl"], self.ids["onion"]
        out = str(self.out)
        found = {"query": "bowl", "image": "search.png", "results": [
            {"name": "Grey Bowl", "verdict": "match", "image_score": 0.85, "text_score": 0.47,
             "pbr_asset_id": "LIB-PBR", "mesh_asset_id": "LIB-MESH", "thumbnail_path": "t.png", "extra": 1},
            {"name": "Plate", "verdict": "weak", "image_score": 0.7, "text_score": None, "pbr_asset_id": "P2"}]}
        self.assertEqual(self.mf("record", out, "--stage", "library", bowl, "--json", json.dumps(found)).returncode, 0)
        self.assertEqual(self.mf("record", out, "--stage", "library", onion, "--json",
                                 json.dumps({"results": []})).returncode, 0)
        self.assertEqual(self.mf("record", out, "--stage", "library", onion, "--job", "j").returncode, 1)
        self.assertEqual(self.pending("choose")["pending"], [bowl, onion])
        # Only one of the asset's own candidates can be reused.
        self.assertEqual(self.mf("choose", out, "--reuse", f"{bowl}=NOT-A-CANDIDATE").returncode, 1)
        self.assertEqual(self.mf("choose", out, "--reuse", f"{bowl}=LIB-PBR", "--make", bowl).returncode, 1)
        self.assertEqual(self.mf("choose", out, "--reuse", f"{bowl}=LIB-PBR", "--make", onion).returncode, 0)
        report = self.pending()
        self.assertEqual(report["reused"], [bowl])
        self.assertEqual(report["pending"]["reference"], [onion])
        self.assertEqual(report["pending"]["mint"], [bowl])
        self.assertEqual(report["mint_status_asset_ids"], ["LIB-PBR"])
        self.assertEqual(report["pending"]["review"] + report["pending"]["mesh"], [])
        self.assertEqual(self.mf("record", out, "--stage", "mint", "--json",
                                 json.dumps({"status": {"LIB-PBR": "minted"}})).returncode, 0)
        self.assertEqual(self.pending("import")["pending"], [bowl])
        doc = json.loads(self.out.read_text(encoding="utf-8"))
        recorded = {a["asset_id"]: a for a in doc["assets"]}[bowl]
        self.assertEqual(recorded["library"]["chosen"]["name"], "Grey Bowl")
        self.assertNotIn("extra", recorded["library"]["candidates"][0])
        self.assertEqual(recorded["mesh"]["status"], "skipped")
        # Changing one's mind sends it back to the start of the chain.
        self.assertEqual(self.mf("choose", out, "--make", bowl).returncode, 0)
        report = self.pending()
        self.assertEqual(report["reused"], [])
        self.assertEqual(report["pending"]["reference"], [bowl, onion])
        doc = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertIsNone({a["asset_id"]: a for a in doc["assets"]}[bowl]["pbr_asset_id"])


if __name__ == "__main__":
    unittest.main()
