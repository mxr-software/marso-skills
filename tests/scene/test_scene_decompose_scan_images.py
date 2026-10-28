"""Tests for the scene-decompose lead's scan_images.py."""
import json
import os
import shutil
import struct
import tempfile
import unittest
import zlib

from helpers import SKILL as SKILL_DIR, SCRIPTS as SCRIPTS_DIR, run, run_json, script_dirs


def png_bytes(width, height):
    """A minimal but genuinely valid PNG."""
    def chunk(tag, payload):
        body = tag + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def jpeg_bytes(width, height):
    """A JPEG header with a comment segment before the frame, so the walker has to skip it."""
    comment = b"\xff\xfe" + struct.pack(">H", 2 + 5) + b"hello"
    sof = b"\xff\xc0" + struct.pack(">H", 11) + bytes([8]) + struct.pack(">HH", height, width) + bytes([1, 1, 17, 0])
    return b"\xff\xd8" + comment + sof + b"\xff\xd9"


def gif_bytes(width, height):
    return b"GIF89a" + struct.pack("<HH", width, height) + b"\x00\x00\x00"


def bmp_bytes(width, height):
    header = b"BM" + b"\x00" * 16 + struct.pack("<ii", width, -height)
    return header + b"\x00" * 8


class ScanImagesTests(unittest.TestCase):
    def setUp(self):
        dirs = script_dirs("scan_images.py")
        self.assertTrue(dirs, "no skill ships scan_images.py")
        self.script = os.path.join(dirs[0], "scan_images.py")
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, data):
        path = os.path.join(self.tmp, name)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def test_help_works_and_does_not_prompt(self):
        code, out, _ = run(self.script, "--help")
        self.assertEqual(code, 0)
        self.assertIn("--force", out)

    def test_reads_dimensions_from_every_supported_header(self):
        self.write("a.png", png_bytes(7, 11))
        self.write("b.jpg", jpeg_bytes(640, 480))
        self.write("c.gif", gif_bytes(12, 34))
        self.write("d.bmp", bmp_bytes(20, 30))
        code, manifest, _ = run_json(self.script, self.tmp)
        self.assertEqual(code, 0, manifest["problems"])
        sizes = {os.path.basename(r["path"]): (r["width"], r["height"]) for r in manifest["images"]}
        self.assertEqual(sizes["a.png"], (7, 11))
        self.assertEqual(sizes["b.jpg"], (640, 480))
        self.assertEqual(sizes["c.gif"], (12, 34))
        self.assertEqual(sizes["d.bmp"], (20, 30))
        self.assertTrue(all(r["dims_source"] == "header" for r in manifest["images"]))

    def test_ids_are_stable_across_runs(self):
        self.write("b.png", png_bytes(2, 2))
        self.write("a.png", png_bytes(3, 3))
        first = run_json(self.script, self.tmp)[1]
        second = run_json(self.script, self.tmp)[1]
        self.assertEqual([r["image_id"] for r in first["images"]], ["img001", "img002"])
        self.assertEqual(
            [(r["image_id"], os.path.basename(r["path"])) for r in first["images"]],
            [(r["image_id"], os.path.basename(r["path"])) for r in second["images"]],
        )

    def test_each_image_appears_exactly_once_when_folder_and_file_are_both_given(self):
        path = self.write("a.png", png_bytes(2, 2))
        _, manifest, _ = run_json(self.script, self.tmp, path)
        self.assertEqual(manifest["count"], 1)

    def test_flags_byte_identical_duplicates_without_dropping_them(self):
        self.write("a.png", png_bytes(5, 5))
        self.write("copy.png", png_bytes(5, 5))
        code, manifest, err = run_json(self.script, self.tmp)
        self.assertEqual(code, 1)
        self.assertEqual(manifest["count"], 2)
        flagged = [r for r in manifest["images"] if "duplicate_of" in r]
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["duplicate_of"], "img001")
        self.assertIn("identical", err)

    def test_flags_an_unreadable_header_instead_of_guessing(self):
        self.write("broken.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
        code, manifest, err = run_json(self.script, self.tmp)
        self.assertEqual(code, 1)
        row = manifest["images"][0]
        self.assertIsNone(row["width"])
        self.assertEqual(row["dims_source"], "unknown")
        self.assertIn("dimensions", err)

    def test_ignores_non_images_in_a_folder(self):
        self.write("a.png", png_bytes(2, 2))
        self.write("notes.txt", b"not an image")
        _, manifest, _ = run_json(self.script, self.tmp)
        self.assertEqual(manifest["count"], 1)

    def test_writes_utf8_and_refuses_to_overwrite_without_force(self):
        self.write("a.png", png_bytes(2, 2))
        out = os.path.join(self.tmp, "sub", "manifest.json")
        code, _, _ = run(self.script, self.tmp, "--out", out)
        self.assertEqual(code, 0)
        with open(out, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["count"], 1)
        code, _, err = run(self.script, self.tmp, "--out", out)
        self.assertEqual(code, 1)
        self.assertIn("--force", err)
        code, _, _ = run(self.script, self.tmp, "--out", out, "--force")
        self.assertEqual(code, 0)

    def test_exit_2_when_a_path_does_not_exist(self):
        code, _, err = run(self.script, os.path.join(self.tmp, "nope"))
        self.assertEqual(code, 2)
        self.assertIn("no such file", err)

    def test_exit_1_when_a_folder_holds_no_images(self):
        code, _, err = run(self.script, self.tmp)
        self.assertEqual(code, 1)
        self.assertIn("no images", err)

    def test_records_the_bbox_convention_so_downstream_never_has_to_guess(self):
        self.write("a.png", png_bytes(2, 2))
        _, manifest, _ = run_json(self.script, self.tmp)
        self.assertIn("normalised", manifest["bbox_convention"])


if __name__ == "__main__":
    unittest.main()
