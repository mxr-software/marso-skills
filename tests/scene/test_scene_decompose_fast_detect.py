"""Tests for the fast detect path: tile_images.py and merge_tiles.py.

The previous detect path had the model measure boxes off a magnified grid, which was
20-40 tool calls per agent and most of the time. Now a script makes the magnified view
(a tile) and a script maps the agent's boxes back. These tests are about that geometry
being right, because nothing downstream looks at the pixels again.
"""
import importlib.util
import json
import os
import shutil
import tempfile
import unittest

from helpers import SKILL as SKILL_DIR, SCRIPTS as SCRIPTS_DIR, ROOT, run, run_json

LEAD = SCRIPTS_DIR
DETECT = SCRIPTS_DIR
TILE = os.path.join(LEAD, "tile_images.py")
MERGE = os.path.join(DETECT, "merge_tiles.py")
CHECK_DETECT = os.path.join(DETECT, "check_detections.py")
CHECK_STRUCTURE = os.path.join(SCRIPTS_DIR, "check_structure.py")

try:
    from PIL import Image
except ImportError:                                    # pragma: no cover
    Image = None


def load(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tiler = load(TILE)


class SpanTests(unittest.TestCase):
    def test_tiles_cover_the_whole_frame_with_no_gap(self):
        for count in (1, 2, 3, 4):
            with self.subTest(count=count):
                spans = tiler.spans(count, 0.12)
                self.assertEqual(spans[0][0], 0.0)
                self.assertEqual(spans[-1][1], 1.0)
                for (_, end), (start, _) in zip(spans, spans[1:]):
                    self.assertGreaterEqual(end, start, "a gap between two tiles")

    def test_neighbouring_tiles_overlap_by_about_the_asked_amount(self):
        (a0, a1), (b0, b1) = tiler.spans(2, 0.12)
        self.assertAlmostEqual((a1 - b0) / (a1 - a0), 0.12, places=2)

    def test_regions_are_row_major_and_named(self):
        regions = tiler.tile_regions(2, 2, 0.1)
        self.assertEqual([r["tile_id"] for r in regions], ["t1", "t2", "t3", "t4"])
        self.assertEqual((regions[1]["row"], regions[1]["col"]), (0, 1))
        self.assertEqual((regions[2]["row"], regions[2]["col"]), (1, 0))


@unittest.skipIf(Image is None, "Pillow is not installed; tiling needs it")
class TileImagesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def photo(self, name, size, colour=(40, 80, 120)):
        path = os.path.join(self.tmp, name)
        Image.new("RGB", size, colour).save(path)
        return path

    def manifest(self, rows):
        path = os.path.join(self.tmp, "manifest.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"images": rows}, f)
        return path

    def test_a_big_photograph_gets_a_whole_view_and_four_tiles(self):
        self.photo("big.jpg", (4000, 3000))
        manifest = self.manifest([{"image_id": "img001", "path": "big.jpg",
                                   "width": 4000, "height": 3000}])
        out = os.path.join(self.tmp, "tiles")
        code, report, _ = run_json(TILE, "--manifest", manifest, "--out", out)
        self.assertEqual(code, 0, report)
        self.assertEqual(report["tiles"], 4)
        with open(os.path.join(out, "tiles.json"), encoding="utf-8") as f:
            data = json.load(f)
        entry = data["images"]["img001"]
        self.assertTrue(entry["tiled"])
        self.assertTrue(os.path.isabs(entry["whole"]["path"]), "agents run from anywhere")
        for tile in entry["tiles"]:
            self.assertTrue(os.path.exists(tile["path"]))
            self.assertLessEqual(max(tile["pixels"]), 1568)
        self.assertLessEqual(max(entry["whole"]["pixels"]), 1568)

    def test_a_small_photograph_is_not_tiled(self):
        """A tile of it would show nothing the whole view does not."""
        self.photo("small.jpg", (1200, 900))
        manifest = self.manifest([{"image_id": "img001", "path": "small.jpg"}])
        out = os.path.join(self.tmp, "tiles")
        code, report, _ = run_json(TILE, "--manifest", manifest, "--out", out)
        self.assertEqual(code, 0)
        self.assertEqual(report["tiles"], 0)
        self.assertEqual(report["untiled"], ["img001"])

    def test_a_tile_shows_the_region_it_says_it_does(self):
        """The whole point: a box in a tile maps back to the right place."""
        picture = Image.new("RGB", (2400, 1800), (0, 0, 0))
        for x in range(1800, 2400):            # a white block in the right-hand quarter
            for y in range(0, 900, 4):
                picture.putpixel((x, y), (255, 255, 255))
        picture.save(os.path.join(self.tmp, "p.jpg"), quality=100)
        manifest = self.manifest([{"image_id": "img001", "path": "p.jpg"}])
        out = os.path.join(self.tmp, "tiles")
        run_json(TILE, "--manifest", manifest, "--out", out, "--long-edge", "800")
        with open(os.path.join(out, "tiles.json"), encoding="utf-8") as f:
            tiles = json.load(f)["images"]["img001"]["tiles"]
        right_top = next(t for t in tiles if t["row"] == 0 and t["col"] == 1)
        left_top = next(t for t in tiles if t["row"] == 0 and t["col"] == 0)

        def brightness(tile):
            from PIL import ImageStat
            with Image.open(tile["path"]) as shown:
                return ImageStat.Stat(shown.convert("L")).mean[0]

        self.assertGreater(brightness(right_top), brightness(left_top))

    def test_a_missing_image_is_reported_and_exits_1(self):
        manifest = self.manifest([{"image_id": "img001", "path": "nowhere.jpg"}])
        code, report, _ = run_json(TILE, "--manifest", manifest,
                                   "--out", os.path.join(self.tmp, "tiles"))
        self.assertEqual(code, 1)
        self.assertTrue(report["problems"])

    def test_an_exif_rotation_is_applied_and_warned_about(self):
        """Agents see the rotated picture, so boxes must be in the rotated frame."""
        path = os.path.join(self.tmp, "rot.jpg")
        picture = Image.new("RGB", (400, 300), (10, 10, 10))
        exif = Image.Exif()
        exif[0x0112] = 6                                    # rotate 90 clockwise on display
        picture.save(path, exif=exif)
        manifest = self.manifest([{"image_id": "img001", "path": "rot.jpg",
                                   "width": 400, "height": 300}])
        code, report, _ = run_json(TILE, "--manifest", manifest,
                                   "--out", os.path.join(self.tmp, "tiles"))
        self.assertEqual(code, 0)
        self.assertTrue(report["warnings"], "the size mismatch was not mentioned")

    def test_refuses_to_overwrite_without_force(self):
        self.photo("a.jpg", (3000, 2000))
        manifest = self.manifest([{"image_id": "img001", "path": "a.jpg"}])
        out = os.path.join(self.tmp, "tiles")
        run_json(TILE, "--manifest", manifest, "--out", out)
        code, _, err = run(TILE, "--manifest", manifest, "--out", out)
        self.assertEqual(code, 1)
        self.assertIn("--force", err)


def local(box, region):
    """A box in the photograph, as 0-1 of the tile that shows `region`."""
    x0, y0, x1, y1 = region
    w, h = x1 - x0, y1 - y0
    return [round((box[0] - x0) / w, 5), round((box[1] - y0) / h, 5),
            round((box[2] - x0) / w, 5), round((box[3] - y0) / h, 5)]


def obj(label, bbox, **extra):
    out = {"label": label, "description": label, "category": "homeware", "bbox": bbox,
           "size_m": 0.2, "size_basis": "relative to the table"}
    out.update(extra)
    return out


class MergeTilesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.dir = os.path.join(self.tmp, "detections")
        os.makedirs(self.dir)
        regions = tiler.tile_regions(2, 2, 0.12)
        self.plan = {"images": {"img001": {"width": 4000, "height": 3000, "tiled": True,
                                           "tiles": regions}}}
        self.tiles = os.path.join(self.tmp, "tiles.json")
        with open(self.tiles, "w", encoding="utf-8") as f:
            json.dump(self.plan, f)
        self.regions = {r["tile_id"]: r["region"] for r in regions}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, objects):
        with open(os.path.join(self.dir, f"img001.{name}.json"), "w", encoding="utf-8") as f:
            json.dump({"image_id": "img001", "objects": objects}, f)

    def everything(self, whole=None, **tiles):
        """Write the whole file and every tile, empty where none is given."""
        self.write("whole", whole or [
            obj("parquet floor", [0.0, 0.5, 1.0, 1.0], category="architecture", size_m=4)])
        for tile_id in self.regions:
            self.write(tile_id, tiles.get(tile_id, []))

    def merge(self):
        out = os.path.join(self.tmp, "out", "detections.json")
        structure = os.path.join(self.tmp, "out", "structure.json")
        code, report, err = run_json(MERGE, "--tiles", self.tiles, "--image-id", "img001",
                                     "--dir", self.dir, "--out", out, "--structure", structure,
                                     "--force")
        data = tree = None
        if os.path.exists(out):
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            with open(structure, encoding="utf-8") as f:
                tree = json.load(f)
        return code, report, data, tree, err

    def by_label(self, data):
        return {o["label"]: o for o in data["objects"]}

    # --- the geometry, which nothing downstream re-checks ---------------------

    def test_a_tile_box_is_mapped_into_the_whole_photograph(self):
        self.everything(t2=[obj("mug", [0.0, 0.0, 1.0, 1.0])])
        _, _, data, _, _ = self.merge()
        r = self.regions["t2"]
        box = self.by_label(data)["mug"]["bbox"]
        for got, want in zip(box, r):
            self.assertAlmostEqual(got, want, places=3)

    def test_a_box_in_the_middle_of_a_tile_lands_in_the_middle_of_its_region(self):
        self.everything(t4=[obj("mug", [0.4, 0.4, 0.6, 0.6])])
        _, _, data, _, _ = self.merge()
        x0, y0, x1, y1 = self.regions["t4"]
        want = [x0 + 0.4 * (x1 - x0), y0 + 0.4 * (y1 - y0),
                x0 + 0.6 * (x1 - x0), y0 + 0.6 * (y1 - y0)]
        for got, w in zip(self.by_label(data)["mug"]["bbox"], want):
            self.assertAlmostEqual(got, w, places=3)

    def test_the_whole_view_is_already_in_photograph_coordinates(self):
        self.everything(whole=[obj("oak table", [0.3, 0.4, 0.7, 0.9], category="furniture")])
        _, _, data, _, _ = self.merge()
        self.assertEqual(self.by_label(data)["oak table"]["bbox"], [0.3, 0.4, 0.7, 0.9])

    def test_a_box_off_the_photographs_own_edge_is_marked_truncated(self):
        self.everything(t1=[obj("curtain", [0.0, 0.2, 0.3, 0.8])])
        _, _, data, _, _ = self.merge()
        self.assertIn("left", self.by_label(data)["curtain"]["truncated"])

    # --- duplicates and seams -------------------------------------------------

    def test_an_object_found_in_two_overlapping_tiles_is_kept_once(self):
        # t1 spans x to 0.532 and t2 starts at 0.468: a mug at x 0.49-0.51 is in both.
        x0, x1 = 0.49, 0.51
        r1, r2 = self.regions["t1"], self.regions["t2"]

        def local(region):
            return [(x0 - region[0]) / (region[2] - region[0]), 0.2,
                    (x1 - region[0]) / (region[2] - region[0]), 0.3]

        self.everything(t1=[obj("blue mug", local(r1))], t2=[obj("blue mug", local(r2))])
        code, report, data, _, _ = self.merge()
        self.assertEqual(len([o for o in data["objects"] if o["label"] == "blue mug"]), 1)
        self.assertEqual(report["dropped_as_duplicates"], 1)

    def test_one_object_in_front_of_another_is_not_a_duplicate(self):
        self.everything(t1=[obj("oil bottle", [0.30, 0.2, 0.40, 0.5]),
                            obj("spirit bottle", [0.31, 0.22, 0.41, 0.52])])
        _, _, data, _, _ = self.merge()
        labels = [o["label"] for o in data["objects"]]
        self.assertIn("oil bottle", labels)
        self.assertIn("spirit bottle", labels)

    def test_a_thing_cut_by_a_seam_is_joined_into_one(self):
        """A table spans two tiles: each saw half, each box runs to the seam."""
        seam_x = self.regions["t2"][0] + 0.01          # inside the overlap
        r1, r2 = self.regions["t1"], self.regions["t2"]
        left = [0.3, 0.3, 1.0, 0.7]                     # runs off t1's right edge
        right = [0.0, 0.3, 0.5, 0.7]                    # runs off t2's left edge
        self.everything(t1=[obj("wooden bench", left, category="furniture")],
                        t2=[obj("wooden bench", right, category="furniture")])
        code, report, data, _, _ = self.merge()
        benches = [o for o in data["objects"] if o["label"] == "wooden bench"]
        self.assertEqual(len(benches), 1, [o["bbox"] for o in benches])
        box = benches[0]["bbox"]
        self.assertAlmostEqual(box[0], r1[0] + 0.3 * (r1[2] - r1[0]), places=3)
        self.assertAlmostEqual(box[2], r2[0] + 0.5 * (r2[2] - r2[0]), places=3)
        self.assertEqual(len(report["seam_joins"]), 1)
        del seam_x

    def test_one_thing_cut_by_a_seam_and_named_twice_is_joined(self):
        """Two tiles called one tray 'wooden tray' and 'serving board'. The shakers on it name
        the dropped half and must still find the tray."""
        self.everything(t2=[obj("wooden tray", [0.5, 0.465, 0.918, 1.0], surface=True)],
                        t4=[obj("serving board", [0.515, 0.0, 0.94, 0.39], surface=True),
                            obj("salt shaker", [0.65, 0.05, 0.75, 0.2], on="serving board")])
        _, report, data, _, _ = self.merge()
        by = self.by_label(data)
        trays = [o for o in data["objects"] if o["label"] in ("wooden tray", "serving board")]
        self.assertEqual(len(trays), 1, [o["label"] for o in trays])
        self.assertEqual(by["salt shaker"]["parent"], trays[0]["local_id"])
        self.assertEqual(len(report["seam_joins"]), 1)
        self.assertEqual(trays[0].get("id_confidence"), "low")

    def test_two_things_side_by_side_at_a_seam_are_not_joined(self):
        """A placemat crossing the seam under a narrower tray is a different width: kept apart."""
        self.everything(t2=[obj("placemat", [0.2, 0.6, 0.9, 1.0], surface=True)],
                        t4=[obj("wooden tray", [0.4, 0.0, 0.6, 0.3], surface=True)])
        _, _, data, _, _ = self.merge()
        labels = {o["label"] for o in data["objects"]}
        self.assertTrue({"placemat", "wooden tray"} <= labels, labels)

    def test_a_sliver_a_seam_cut_off_another_tiles_object_is_dropped(self):
        """A tile edge through a glasses case left 'hat', a fifth of it, on the other side."""
        r1, r2 = self.regions["t1"], self.regions["t2"]
        case = [0.025, 0.104, 0.25, 0.306]              # t2, whole case
        cut = r1[2]                                      # t1's right edge, inside the case
        sliver_x0 = (r2[0] + 0.025 * (r2[2] - r2[0]) - r1[0]) / (r1[2] - r1[0])
        self.everything(t1=[obj("hat", [sliver_x0, 0.104, 1.0, 0.275])],
                        t2=[obj("glasses case", case)])
        _, report, data, _, _ = self.merge()
        labels = [o["label"] for o in data["objects"]]
        self.assertNotIn("hat", labels)
        self.assertIn("glasses case", labels)
        folded = report["slivers"] + report["seam_joins"]
        self.assertTrue(any("hat" in pair for pair in folded), folded)
        del cut

    def test_a_small_thing_cut_by_a_seam_on_a_surface_is_kept(self):
        """A ring cut by the same seam sits inside the placemat but is a fraction of its height."""
        self.everything(t1=[obj("signet ring", [0.97, 0.5, 1.0, 0.55])],
                        t2=[obj("woven placemat", [0.0, 0.2, 0.5, 0.9], surface=True)])
        _, _, data, _, _ = self.merge()
        self.assertIn("signet ring", {o["label"] for o in data["objects"]})

    def test_a_thing_hanging_on_a_whole_view_housing_is_not_a_sliver_of_it(self):
        """An oven glove on a tall housing the whole view boxed floor to ceiling stays."""
        self.everything(
            whole=[obj("parquet floor", [0.0, 0.8, 1.0, 1.0], category="architecture", size_m=4),
                   obj("tall cabinet", [0.92, 0.0, 1.0, 1.0], category="architecture", size_m=2.2)],
            t4=[obj("oven glove", [0.877, 0.04, 1.0, 0.46], category="textile")])
        _, _, data, _, _ = self.merge()
        self.assertIn("oven glove", {o["label"] for o in data["objects"]})

    def test_two_separate_things_with_one_name_are_not_joined(self):
        """Two shakers side by side, neither cut by a seam, stay two objects."""
        self.everything(t1=[obj("shaker", [0.40, 0.4, 0.45, 0.5]),
                            obj("shaker", [0.46, 0.4, 0.51, 0.5])])
        _, _, data, _, _ = self.merge()
        self.assertEqual(len([o for o in data["objects"] if o["label"] == "shaker"]), 2)

    # --- partials of something the whole pass already recorded -----------------

    def test_a_tile_object_inside_a_whole_view_one_of_the_same_kind_is_absorbed(self):
        """A tile agent recorded 'dining chair' inside the whole 'wishbone chair', under
        the duplicate threshold, and the chair count came out as four."""
        self.everything(
            whole=[obj("wishbone chair", [0.36, 0.41, 0.50, 0.73], category="furniture", size_m=0.9)],
            t3=[obj("dining chair", local([0.372, 0.531, 0.495, 0.723], self.regions["t3"]))])
        _, report, data, _, _ = self.merge()
        self.assertEqual(len([o for o in data["objects"] if "chair" in o["label"]]), 1)
        self.assertEqual(report["absorbed"], [["dining chair", "wishbone chair"]])

    def test_the_halves_of_a_cut_placemat_are_absorbed_into_the_whole(self):
        whole = [0.415, 0.258, 0.75, 0.725]
        self.everything(
            whole=[obj("woven placemat", whole, category="decor")],
            t2=[obj("round placemat", local([0.468, 0.255, 0.75, 0.532], self.regions["t2"]))],
            t4=[obj("woven placemat", local([0.438, 0.468, 0.75, 0.726], self.regions["t4"]))])
        _, report, data, _, _ = self.merge()
        self.assertEqual(len([o for o in data["objects"] if "placemat" in o["label"]]), 1)
        # The halves meet across the seam and are joined first, then absorbed as one.
        self.assertGreaterEqual(len(report["absorbed"]), 1)

    def test_a_different_kind_of_thing_inside_a_big_one_is_not_absorbed(self):
        """A table lamp sits inside the table's box and is not a table."""
        self.everything(
            whole=[obj("oak dining table", [0.2, 0.4, 0.9, 0.95], category="furniture", size_m=1.6)],
            t4=[obj("table lamp", local([0.6, 0.6, 0.65, 0.7], self.regions["t4"]))])
        _, report, data, _, _ = self.merge()
        self.assertIn("table lamp", [o["label"] for o in data["objects"]])
        self.assertEqual(report["absorbed"], [])

    def test_two_tile_objects_are_never_absorbed_into_each_other(self):
        """A bottle standing in front of another is inside its box and is still a bottle."""
        self.everything(t1=[obj("glass bottle", [0.30, 0.20, 0.45, 0.60]),
                            obj("glass bottle", [0.32, 0.30, 0.38, 0.55])])
        _, report, data, _, _ = self.merge()
        self.assertEqual(len([o for o in data["objects"] if o["label"] == "glass bottle"]), 2)
        self.assertEqual(report["absorbed"], [])

    def test_one_object_named_two_ways_by_two_tiles_is_still_one_object(self):
        """'gas hob' and 'induction hob' overlapped by 0.87, which the old threshold missed."""
        r1, r2 = self.regions["t1"], self.regions["t2"]
        box = [0.485, 0.2, 0.50, 0.3]
        self.everything(t1=[obj("gas hob", local(box, r1))],
                        t2=[obj("induction hob", local([0.486, 0.201, 0.501, 0.301], r2))])
        _, _, data, _, _ = self.merge()
        self.assertEqual(len([o for o in data["objects"] if "hob" in o["label"]]), 1)

    # --- the tree --------------------------------------------------------------

    def test_an_object_rests_on_the_smallest_surface_under_it(self):
        self.everything(
            whole=[obj("parquet floor", [0.0, 0.5, 1.0, 1.0], category="architecture", size_m=4),
                    obj("oak table", [0.2, 0.55, 0.8, 0.95], category="furniture", size_m=1.6)],
            t4=[obj("mug", [0.3, 0.3, 0.4, 0.45])])
        _, _, data, _, _ = self.merge()
        by = self.by_label(data)
        self.assertEqual(by["mug"]["parent"], by["oak table"]["local_id"])
        self.assertEqual(by["oak table"]["parent"], by["parquet floor"]["local_id"])
        self.assertIsNone(by["parquet floor"]["parent"])

    def test_a_support_loop_is_cut_once_and_keeps_what_rests_on_it(self):
        """No floor in frame: the units fall back onto the worktop that names them, a loop.
        One link is cut; the kettle on the worktop keeps its parent."""
        self.everything(
            whole=[obj("back wall", [0.0, 0.0, 1.0, 0.5], category="architecture", size_m=3),
                   obj("worktop", [0.0, 0.5, 1.0, 0.6], category="architecture", size_m=3,
                       on="base cabinets"),
                   obj("base cabinets", [0.0, 0.55, 1.0, 0.59], category="architecture", size_m=3,
                       on="floor"),
                   obj("kettle", [0.4, 0.4, 0.5, 0.55], category="appliance", size_m=0.25,
                       on="worktop")])
        _, report, data, _, _ = self.merge()
        by = self.by_label(data)
        self.assertEqual(by["kettle"]["parent"], by["worktop"]["local_id"])
        self.assertEqual(by["worktop"]["parent"], by["base cabinets"]["local_id"])
        self.assertIsNone(by["base cabinets"]["parent"])
        self.assertEqual(report["loops_broken"], [by["base cabinets"]["local_id"]])

    def test_occlusion_is_normalised_and_a_bare_heavy_object_is_reported(self):
        self.everything(t1=[obj("dining chair", [0.2, 0.2, 0.5, 0.6], occlusion="heavy",
                                visible="top rail", whole_description="spindle-back oak chair"),
                            obj("stool", [0.6, 0.2, 0.8, 0.6], occlusion="heavy"),
                            obj("mug", [0.1, 0.7, 0.15, 0.8], occluded=True)])
        _, report, data, _, _ = self.merge()
        by = self.by_label(data)
        self.assertEqual(by["dining chair"]["occlusion"], "heavy")
        self.assertTrue(by["dining chair"]["occluded"])
        self.assertEqual(by["dining chair"]["whole_description"], "spindle-back oak chair")
        self.assertEqual(by["mug"]["occlusion"], "partial")
        self.assertEqual(report["heavy_without_context"], ["stool"])

    def test_a_stack_of_same_named_things_rests_bottom_up(self):
        """Three bowls stacked, each 'on bowl': each rests on the one below, and nothing loops."""
        self.everything(
            whole=[obj("parquet floor", [0.0, 0.5, 1.0, 1.0], category="architecture", size_m=4),
                   obj("worktop", [0.0, 0.4, 1.0, 0.6], category="architecture", size_m=3,
                       surface=True)],
            t1=[obj("bowl", [0.18, 0.5263, 0.2553, 0.5851], on="worktop", surface=True),
                obj("bowl", [0.1809, 0.4957, 0.2534, 0.541], on="bowl", surface=True),
                obj("bowl", [0.1818, 0.4749, 0.2507, 0.5055], on="bowl", surface=True)])
        _, report, data, _, _ = self.merge()
        bowls = sorted((o for o in data["objects"] if o["label"] == "bowl"), key=lambda o: -o["bbox"][3])
        self.assertEqual(len(bowls), 3)
        self.assertEqual(bowls[1]["parent"], bowls[0]["local_id"])
        self.assertEqual(bowls[2]["parent"], bowls[1]["local_id"])
        self.assertEqual(report["loops_broken"], [])

    def test_a_named_support_beats_geometry(self):
        """The agent saw what the mug stood on; the box only suggests it."""
        self.everything(
            whole=[obj("parquet floor", [0.0, 0.5, 1.0, 1.0], category="architecture", size_m=4),
                    obj("oak table", [0.2, 0.55, 0.8, 0.95], category="furniture", size_m=1.6),
                    obj("wooden tray", [0.45, 0.6, 0.7, 0.8], category="furniture", surface=True)],
            t4=[obj("mug", [0.3, 0.3, 0.4, 0.45], on="oak table")])
        _, report, data, _, _ = self.merge()
        by = self.by_label(data)
        self.assertEqual(by["mug"]["parent"], by["oak table"]["local_id"])
        self.assertGreaterEqual(report["parent_by"].get("named", 0), 1)

    def test_a_support_nothing_matches_is_counted_and_falls_back_to_geometry(self):
        self.everything(
            whole=[obj("parquet floor", [0.0, 0.5, 1.0, 1.0], category="architecture", size_m=4),
                    obj("oak table", [0.2, 0.55, 0.8, 0.95], category="furniture", size_m=1.6)],
            t4=[obj("mug", [0.3, 0.3, 0.4, 0.45], on="chesterfield sofa")])
        code, report, data, _, _ = self.merge()
        by = self.by_label(data)
        self.assertEqual(by["mug"]["parent"], by["oak table"]["local_id"])
        self.assertTrue(any("named a support" in f for f in report["flagged"]))
        self.assertEqual(code, 1, "a person should look at this")

    def test_relation_words_are_normalised_and_unknown_ones_default(self):
        self.everything(
            whole=[obj("parquet floor", [0.0, 0.5, 1.0, 1.0], category="architecture", size_m=4),
                    obj("oak table", [0.2, 0.55, 0.8, 0.95], category="furniture", size_m=1.6)],
            t4=[obj("mug", [0.3, 0.3, 0.4, 0.45], relation="resting on"),
                obj("spoon", [0.5, 0.3, 0.55, 0.4], relation="in"),
                obj("pen", [0.6, 0.3, 0.65, 0.4], relation="levitating")])
        _, _, data, _, _ = self.merge()
        by = self.by_label(data)
        self.assertEqual(by["spoon"]["relation"], "inside")
        self.assertEqual(by["pen"]["relation"], "on-top-of")

    def test_the_tree_passes_the_structure_gate_and_the_detections_pass_theirs(self):
        self.everything(
            whole=[obj("parquet floor", [0.0, 0.5, 1.0, 1.0], category="architecture", size_m=4),
                    obj("oak table", [0.2, 0.55, 0.8, 0.95], category="furniture", size_m=1.6)],
            t4=[obj("mug", [0.3, 0.3, 0.4, 0.45]), obj("spoon", [0.5, 0.3, 0.55, 0.4])])
        _, _, _, _, _ = self.merge()
        out = os.path.join(self.tmp, "out")
        code, report, _ = run_json(CHECK_STRUCTURE, os.path.join(out, "structure.json"))
        self.assertEqual(code, 0, report)
        code, report, _ = run_json(CHECK_DETECT, os.path.join(out, "detections.json"))
        self.assertEqual(code, 0, report)

    def test_same_named_siblings_become_a_cluster_of_instances(self):
        self.everything(
            whole=[obj("parquet floor", [0.0, 0.5, 1.0, 1.0], category="architecture", size_m=4),
                    obj("oak table", [0.2, 0.55, 0.8, 0.95], category="furniture", size_m=1.6)],
            t4=[obj("red onion", [0.30, 0.3, 0.34, 0.36]), obj("red onion", [0.40, 0.3, 0.44, 0.36])])
        _, _, _, tree, _ = self.merge()
        self.assertEqual(len(tree["clusters"]), 1)
        self.assertEqual(tree["clusters"][0]["kind"], "instances")
        self.assertEqual(len(tree["clusters"][0]["members"]), 2)

    # --- what it refuses to hide --------------------------------------------------

    def test_a_missing_tile_is_named_and_exits_1(self):
        self.write("whole", [obj("parquet floor", [0.0, 0.5, 1.0, 1.0],
                                  category="architecture", size_m=4)])
        self.write("t1", [])
        code, report, data, _, _ = self.merge()
        self.assertEqual(code, 1)
        self.assertIn("t2", report["missing"])
        self.assertTrue(any("missing" in f for f in report["flagged"]))

    def test_a_saturated_tile_is_flagged(self):
        crowd = [obj(f"thing {i}", [0.01 * (i % 50), 0.1, 0.01 * (i % 50) + 0.008, 0.15])
                 for i in range(45)]
        self.everything(t3=crowd)
        _, report, _, _, _ = self.merge()
        self.assertTrue(any("unfinished" in f for f in report["flagged"]), report["flagged"])

    def test_an_empty_tile_is_flagged_not_trusted(self):
        self.everything()
        _, report, _, _, _ = self.merge()
        self.assertTrue(any("found nothing" in f for f in report["flagged"]))

    def test_a_missing_size_becomes_a_placeholder_and_is_counted(self):
        self.everything(t1=[{"label": "mystery", "bbox": [0.1, 0.1, 0.2, 0.2]}])
        _, report, data, _, _ = self.merge()
        item = self.by_label(data)["mystery"]
        self.assertEqual(item["size_confidence"], "low")
        self.assertEqual(report["size_placeholders"], 1)

    def test_an_unreadable_tile_exits_2(self):
        self.everything()
        with open(os.path.join(self.dir, "img001.t1.json"), "w", encoding="utf-8") as f:
            f.write("{not json")
        code, _, err = run(MERGE, "--tiles", self.tiles, "--image-id", "img001",
                           "--dir", self.dir, "--out", os.path.join(self.tmp, "o.json"),
                           "--structure", os.path.join(self.tmp, "s.json"))
        self.assertEqual(code, 2)
        self.assertIn("could not read", err)

    def test_it_will_not_overwrite_without_force(self):
        self.everything(t1=[obj("mug", [0.1, 0.1, 0.2, 0.2])])
        out = os.path.join(self.tmp, "o.json")
        structure = os.path.join(self.tmp, "s.json")
        args = ("--tiles", self.tiles, "--image-id", "img001", "--dir", self.dir,
                "--out", out, "--structure", structure)
        run(MERGE, *args, "--force")
        code, _, err = run(MERGE, *args)
        self.assertEqual(code, 1)
        self.assertIn("--force", err)


if __name__ == "__main__":
    unittest.main()
