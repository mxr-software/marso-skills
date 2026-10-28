"""Regression checks for preserving run evidence and image identity across restarts."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

SCRIPTS = pathlib.Path(__file__).resolve().parents[2] / "skills/core/marso-scene-decompose/scripts"


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.run = self.root / "runs/room"
        self.image = self.root / "photo.png"
        Image.new("RGB", (80, 60), "red").save(self.image)

    def tearDown(self):
        self.tmp.cleanup()

    def start(self, *extra, images=None):
        return subprocess.run([sys.executable, str(SCRIPTS / "fast.py"), "start", "--run", str(self.run),
                               "--images", *map(str, images or [self.image]), "--mode", "coarse", *extra],
                              cwd=str(self.root), capture_output=True, text=True)

    def test_changed_pixels_preserve_previous_manifest_and_results(self):
        self.assertEqual(self.start().returncode, 0)
        old_manifest = (self.run / "manifest.json").read_bytes()
        parts = self.run / "parts"
        parts.mkdir()
        marker = parts / "img001.whole.json"
        marker.write_text('{"objects": []}')
        Image.new("RGB", (80, 60), "blue").save(self.image)
        result = self.start()
        self.assertEqual(result.returncode, 1)
        self.assertIn("new run folder", result.stdout)
        self.assertEqual((self.run / "manifest.json").read_bytes(), old_manifest)
        self.assertEqual(marker.read_text(), '{"objects": []}')

    def test_unchanged_inputs_resume_but_tiling_change_is_refused(self):
        self.assertEqual(self.start().returncode, 0)
        (self.run / "parts").mkdir()
        marker = self.run / "parts/img001.whole.json"
        marker.write_text('{}')
        self.assertEqual(self.start().returncode, 0)
        self.assertEqual(self.start("--long-edge", "200").returncode, 1)
        self.assertTrue(marker.exists())

    def test_switch_does_not_discard_asset_plan(self):
        self.start()
        plan = self.run / "asset_plan.json"
        plan.write_text('{}')
        self.assertEqual(self.start("--mode", "fine").returncode, 1)
        self.assertEqual(plan.read_text(), '{}')

    def test_individual_paths_survive_different_folders_and_same_basename(self):
        second = self.root / "another/photo.png"
        second.parent.mkdir()
        Image.new("RGB", (80, 60), "blue").save(second)
        self.assertEqual(self.start(images=[self.image, second]).returncode, 0)
        manifest = json.loads((self.run / "manifest.json").read_text())
        self.assertEqual({i["path"] for i in manifest["images"]}, {self.image.resolve().as_posix(), second.resolve().as_posix()})
        graph = self.run / "scene_graph.json"
        graph.write_text(json.dumps({"nodes": [{"global_id": "g1"}], "images": [i["image_id"] for i in manifest["images"]]}))
        viewer = self.run / "viewer.html"
        result = subprocess.run([sys.executable, str(SCRIPTS / "build_viewer.py"), str(graph),
                                 "--manifest", str(self.run / "manifest.json"), "--embed", "--out", str(viewer)],
                                cwd=str(self.root), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(viewer.read_text(encoding="utf-8").count('data:image/png;base64,'), 2)


if __name__ == "__main__":
    unittest.main()
