"""Tests for scene-decompose-view's build_viewer.py and its template."""
import base64
import glob
import json
import math
import os
import re
import shutil
import struct
import tempfile
import unittest
import zlib

from helpers import SKILL as SKILL_DIR, SCRIPTS as SCRIPTS_DIR, ROOT, run, run_json

SKILL = SKILL_DIR
SCRIPT = os.path.join(SKILL, "scripts", "build_viewer.py")
TEMPLATE = os.path.join(SKILL_DIR, "assets", "viewer_template.html")


def png_bytes(width, height):
    def chunk(tag, payload):
        body = tag + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def view(image_id, local_id, bbox, **extra):
    out = {"image_id": image_id, "local_id": local_id, "bbox": bbox,
           "occluded": False, "truncated": [], "id_confidence": "high"}
    out.update(extra)
    return out


class ViewerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.images = os.path.join(self.tmp, "img")
        os.makedirs(self.images)
        for name in ("a.png", "b.png"):
            with open(os.path.join(self.images, name), "wb") as f:
                f.write(png_bytes(40, 30))
        self.manifest = self.write("manifest.json", {"images": [
            {"image_id": "img001", "path": os.path.join(self.images, "a.png").replace("\\", "/"),
             "width": 40, "height": 30},
            {"image_id": "img002", "path": os.path.join(self.images, "b.png").replace("\\", "/"),
             "width": 40, "height": 30}]})
        self.graph = self.write("graph.json", {
            "schema": "scene-decompose/scene-graph@1",
            "images": ["img001", "img002"],
            "nodes": [
                {"global_id": "g001", "label": "floor", "parent": None, "relation": None,
                 "category": "architecture", "seen_in": 2,
                 "views": [view("img001", "img001-1", [0, 0.5, 1, 1]),
                           view("img002", "img002-1", [0, 0.6, 1, 1])]},
                {"global_id": "g002", "label": "table", "parent": "g001", "relation": "on-top-of",
                 "category": "furniture", "size_m": 1.4, "size_confidence": "medium",
                 "size_basis": "a guess", "seen_in": 1,
                 "views": [view("img001", "img001-2", [0.2, 0.3, 0.8, 0.9])]},
                {"global_id": "g003", "label": "bowl", "parent": "g002", "relation": "on-top-of",
                 "category": "tableware", "seen_in": 1,
                 "views": [view("img002", "img002-3", [0.3, 0.2, 0.7, 0.6], occluded=True)]},
            ],
            "clusters": [{"cl_id": "cl001", "label": "pair", "kind": "instances",
                          "members": ["g002", "g003"], "seen_in": ["img001"]}],
            "areas": [{"ar_id": "ar001", "label": "dining area",
                       "members": ["g002", "g003"], "seen_in": ["img001"]}],
            "identity_groups": [{"group_id": "ig001", "label": "which one",
                                 "members": ["g002", "g003"], "distinct": 1,
                                 "at_least": 1, "at_most": 2, "basis": "they may be the same"}],
            "parent_conflicts": [],
        })

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, data):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def build(self, *extra, out="viewer.html"):
        target = os.path.join(self.tmp, out)
        code, report, err = run_json(SCRIPT, self.graph, "--manifest", self.manifest,
                                     "--out", target, "--force", *extra)
        return code, report, target

    def html(self, path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    def payload(self, path):
        body = self.html(path)
        start = body.index("const DATA = ") + len("const DATA = ")
        return json.loads(body[start:body.index("\n", start)].rstrip(";"))

    def test_help_works(self):
        code, out, _ = run(SCRIPT, "--help")
        self.assertEqual(code, 0)
        self.assertIn("--embed", out)

    def test_builds_a_single_html_file(self):
        code, report, target = self.build()
        self.assertEqual(code, 0, report)
        self.assertTrue(os.path.exists(target))
        self.assertEqual(report["nodes"], 3)
        self.assertEqual(report["images"], 2)

    def test_no_placeholders_survive(self):
        _, _, target = self.build()
        body = self.html(target)
        self.assertNotIn("__DATA__", body)
        self.assertNotIn("__TITLE__", body)

    def test_the_data_carries_everything_the_panels_need(self):
        _, _, target = self.build(
            "--scores", self.write("scores.json", {"objects": [
                {"global_id": "g001", "label": "floor", "best_view": "img001",
                 "best_local_id": "img001-1", "decisive": True,
                 "views": [{"image_id": "img001", "score": 0.5, "frame_share": 0.5,
                            "penalties": []}]}]}),
            "--confusion", self.write("confusion.json", {"unresolved": [{"label": "which one"}],
                                                         "corrections": []}),
            "--ontology", self.write("ontology.json", {"total_objects": 2, "categories": [
                {"label": "things", "count": 2, "members": ["g001", "g002"]}]}))
        data = self.payload(target)
        self.assertEqual(len(data["nodes"]), 3)
        self.assertEqual(len(data["view_scores"]), 1)
        self.assertEqual(len(data["ontology"]), 1)
        self.assertEqual(data["confusion"]["unresolved"][0]["label"], "which one")
        self.assertEqual(data["identity_groups"][0]["distinct"], 1)

    def test_distinct_objects_falls_back_to_the_identity_groups(self):
        """Without an ontology it still counts physical things, not nodes."""
        _, _, target = self.build()
        self.assertEqual(self.payload(target)["distinct_objects"], 2)

    def test_distinct_objects_prefers_the_ontology(self):
        _, _, target = self.build("--ontology", self.write(
            "o.json", {"total_objects": 2, "categories": []}))
        self.assertEqual(self.payload(target)["distinct_objects"], 2)

    def test_relative_paths_by_default(self):
        _, _, target = self.build()
        for image in self.payload(target)["images"]:
            self.assertFalse(image["src"].startswith("data:"))
            self.assertNotIn("\\", image["src"])

    def test_embed_inlines_the_photographs(self):
        _, report, target = self.build("--embed")
        for image in self.payload(target)["images"]:
            self.assertTrue(image["src"].startswith("data:image/png;base64,"))
            base64.b64decode(image["src"].split(",", 1)[1])      # it is real base64
        self.assertTrue(report["embedded"])

    def test_embedding_is_bigger_than_linking(self):
        _, linked, _ = self.build(out="linked.html")
        _, embedded, _ = self.build("--embed", out="embedded.html")
        self.assertGreater(embedded["bytes"], linked["bytes"])

    def test_a_data_uri_appears_once_per_image_not_once_per_node(self):
        """Repeating it per node once made the page enormous."""
        _, _, target = self.build("--embed")
        body = self.html(target)
        for image in self.payload(target)["images"]:
            head = image["src"][:80]
            # once in the data blob, once in the <img> of the source-image strip
            self.assertLessEqual(body.count(head), 3, "data URI repeated per node")

    def test_image_root_overrides_the_manifest_paths(self):
        moved = os.path.join(self.tmp, "moved")
        os.makedirs(moved)
        for name in ("a.png", "b.png"):
            shutil.copy(os.path.join(self.images, name), os.path.join(moved, name))
        shutil.rmtree(self.images)
        code, report, _ = self.build("--image-root", moved)
        self.assertEqual(code, 0, report)

    def test_a_missing_image_fails_rather_than_shipping_blank_pictures(self):
        os.remove(os.path.join(self.images, "b.png"))
        code, report, target = self.build()
        self.assertEqual(code, 1)
        self.assertTrue(any("no image at" in p for p in report["problems"]))
        self.assertFalse(os.path.exists(target))

    def test_an_image_missing_from_the_manifest_is_named(self):
        self.manifest = self.write("manifest.json", {"images": [
            {"image_id": "img001", "path": os.path.join(self.images, "a.png").replace("\\", "/"),
             "width": 40, "height": 30}]})
        code, report, _ = self.build()
        self.assertEqual(code, 1)
        self.assertTrue(any("not in the manifest" in p for p in report["problems"]))

    def test_refuses_to_overwrite_without_force(self):
        target = os.path.join(self.tmp, "v.html")
        args = (SCRIPT, self.graph, "--manifest", self.manifest, "--out", target)
        self.assertEqual(run(*args)[0], 0)
        code, _, err = run(*args)
        self.assertEqual(code, 1)
        self.assertIn("--force", err)

    def test_exit_1_on_a_graph_with_no_nodes(self):
        empty = self.write("empty.json", {"images": [], "nodes": []})
        code, _, err = run(SCRIPT, empty, "--manifest", self.manifest,
                           "--out", os.path.join(self.tmp, "x.html"))
        self.assertEqual(code, 1)
        self.assertIn("no nodes", err)

    def test_exit_2_on_a_missing_file(self):
        code, _, err = run(SCRIPT, os.path.join(self.tmp, "nope.json"),
                           "--manifest", self.manifest, "--out", os.path.join(self.tmp, "x.html"))
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())


class TemplateTests(unittest.TestCase):
    def setUp(self):
        with open(TEMPLATE, encoding="utf-8") as f:
            self.body = f.read()

    def test_the_template_has_both_placeholders(self):
        self.assertIn("__DATA__", self.body)
        self.assertIn("__TITLE__", self.body)

    def test_it_loads_nothing_from_the_network(self):
        """The viewer must open offline, including with no internet at all."""
        for pattern in (r'src\s*=\s*["\']https?:', r'href\s*=\s*["\']https?://(?!www\.w3\.org)',
                        r'@import', r'fetch\(', r'XMLHttpRequest'):
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, self.body), pattern)

    def test_it_draws_node_crops_through_a_single_shared_image(self):
        """One <image> per photograph in <defs>, reused by every node with <use>."""
        self.assertIn("el('defs'", self.body)
        self.assertIn("'src-' + im.image_id", self.body)   # one per photograph
        self.assertIn("'#src-' + v.image_id", self.body)   # every node points at it
        self.assertIn("el('use'", self.body)
        self.assertIn("clipPath", self.body)

    def test_nothing_is_selected_on_load(self):
        """Selecting fades everything else, which made a full graph look empty."""
        tail = self.body[self.body.rindex("clear();"):]
        self.assertNotIn("select(", tail)

    def test_it_offers_tree_orbit_and_views(self):
        for mode in ('tree', 'orbit', 'views'):
            with self.subTest(mode=mode):
                self.assertIn(f'data-mode="{mode}"', self.body)
        self.assertIn("function setMode(", self.body)

    def test_orbit_turns_the_model_rather_than_panning(self):
        self.assertIn("azim +=", self.body)
        self.assertIn("MODE === 'orbit'", self.body)

    def test_selecting_does_not_move_the_camera(self):
        """The reader's framing is theirs; selecting traces the lineage in place."""
        start = self.body.index("function select(id)")
        body = self.body[start:self.body.index("window.select", start)]
        self.assertNotIn("vx =", body)
        self.assertNotIn("vy =", body)
        self.assertIn("function centreOn(", self.body)   # deliberate, on double-click

    def test_hovering_previews_an_object(self):
        self.assertIn("function hover(", self.body)
        self.assertIn("pointerenter", self.body)
        self.assertIn("pointerleave", self.body)

    def test_the_views_overlay_is_hidden_until_asked_for(self):
        """`hidden` alone loses to display:flex, which once left it open on load."""
        self.assertIn("#views[hidden]", self.body)
        self.assertIn('id="views" hidden', self.body)

    def test_views_boxes_follow_the_letterboxed_picture(self):
        """object-fit: contain leaves margins; boxes must be offset by them."""
        self.assertIn("object-fit:contain", self.body.replace(" ", ""))
        self.assertIn("ox = (rw - dw) / 2", self.body)
        self.assertIn("oy = (rh - dh) / 2", self.body)

    def test_views_paints_without_waiting_for_a_frame(self):
        """requestAnimationFrame never runs while the window is not painting, which
        left Views empty; the tiles' ResizeObserver places the boxes once sized."""
        start = self.body.index("function setMode(")
        body = self.body[start:self.body.index("document.getElementById('tabs')", start)]
        self.assertIn("paintViews(); return;", body)
        # the word appears in the comment explaining why it is not used
        code = [l for l in body.splitlines() if not l.strip().startswith("//")]
        self.assertNotIn("requestAnimationFrame", "\n".join(code))
        self.assertIn("new ResizeObserver(paint)", self.body)

    def test_the_lineage_folds(self):
        self.assertIn("const collapsed = new Set()", self.body)
        self.assertIn("function applyFolds(", self.body)
        self.assertIn("collapsed.delete(a.global_id)", self.body)   # selecting unfolds the way

    def test_hovering_spotlights_the_box_in_views(self):
        self.assertIn("function spotlight(", self.body)
        self.assertIn("backdrop-filter:blur", self.body.replace(" ", ""))
        self.assertIn("saturate(.35)", self.body)

    def test_hovering_always_reveals_that_object_box(self):
        start = self.body.index("function hover(")
        body = self.body[start:self.body.index("/* ---------- selection", start)]
        self.assertIn("b.style.display = (on ||", body)

    def test_orbit_uses_a_perspective_camera(self):
        self.assertIn("function camera(", self.body)
        self.assertIn("FOCAL / Math.max", self.body)

    def test_links_are_sampled_along_the_surface(self):
        self.assertIn("ARC_STEPS", self.body)
        start = self.body.index("function arc(")
        body = self.body[start:self.body.index("function project3", start)]
        # Angle closes early and radius opens late, so most of a link runs radially and
        # links fan out instead of crossing each other.
        self.assertIn("Math.pow(t, 1.45)", body)    # radius opens late
        self.assertIn("Math.pow(t, 0.5)", body)     # angle closes early

    def test_every_geometry_constant_is_declared_before_arc_uses_it(self):
        """ARC_STEPS and MODE were both declared after the links were built."""
        use = self.body.index("function arc(")
        for name in ("let MODE =", "const ARC_STEPS", "let FOCAL", "const ORBIT_SPREAD"):
            with self.subTest(name=name):
                self.assertLess(self.body.index(name), use)

    def test_it_offers_a_gallery_of_every_object(self):
        self.assertIn('data-mode="gallery"', self.body)
        self.assertIn("function paintGallery(", self.body)

    def test_views_and_gallery_sit_inside_the_layout(self):
        """They share the rails, so the list, the pictures and the detail stay in step."""
        self.assertIn('<div id="gw">', self.body)
        gw = self.body[self.body.index('<div id="gw">'):self.body.index('<div class="col r">')]
        self.assertIn('id="views"', gw)
        self.assertIn('id="gallery"', gw)
        self.assertNotIn("position:fixed", self.body[:self.body.index("</style>")])

    def test_sibling_branches_get_a_capped_gap(self):
        """A fixed share taken at every level compounded and squashed deep branches."""
        self.assertIn("WEDGE_GAP", self.body)
        self.assertIn("Math.min(w * 0.14, WEDGE_GAP)", self.body)

    def test_crops_are_sized_in_percentages_and_scaled_uniformly(self):
        """Framing against a hard-coded pixel size showed the wrong part of the room,
        and scaling width and height separately stretched the object."""
        start = self.body.index("function cropImg(")
        body = self.body[start:self.body.index("function select(", start)]
        self.assertIn("bw * pad", body)            # margin is a share of the box
        self.assertNotIn("Math.max(0, x0", body)   # no clamping to the image edge
        self.assertIn("const hPct = wPct * im.height / im.width", body)  # one scale
        self.assertIn("%;", body)                  # positioned in percentages
        self.assertNotIn("frame(", self.body)      # the measured version is gone

    def test_the_crop_draws_the_box_it_claims_to_show(self):
        """The crop shows a margin around the box, so the box is drawn on it: that is
        the only way to tell a wrong crop from a wrong box."""
        self.assertIn(".cpbox", self.body)
        start = self.body.index("function cropImg(")
        body = self.body[start:self.body.index("function select(", start)]
        self.assertIn("const bx = left + x0 * wPct", body)
        self.assertIn("by = top + y0 * hPct", body)
        self.assertIn("bw * wPct", body)

    def test_the_shell_is_flex_not_a_hard_coded_height(self):
        """The header wraps to two rows when narrow; calc(100vh - 42px) pushed the
        layout off the screen."""
        css = self.body[:self.body.index("</style>")]
        code = [l for l in css.splitlines() if "/*" not in l and "*/" not in l]
        self.assertNotIn("calc(100vh - 42px)", "\n".join(code))
        self.assertIn("flex:1; min-height:0", self.body)

    def test_folding_a_panel_collapses_it_rather_than_hiding_it(self):
        """A display:none grid item leaves its track, and the middle pane fell into it."""
        self.assertIn("body.noleft .col.l, body.noright .col.r { width:0", self.body)

    def test_fit_measures_the_nodes_not_the_labels(self):
        start = self.body.index("function fit()")
        body = self.body[start:self.body.index("svg.addEventListener('wheel'", start)]
        code = [l for l in body.splitlines() if not l.strip().startswith("//")]
        self.assertNotIn("getBBox", "\n".join(code))
        self.assertIn("project(pos.get(id))", body)

    def test_nodes_have_a_fixed_hit_area(self):
        """The picture grew on hover, left the cursor, shrank, re-entered: a flicker loop."""
        self.assertIn("class: 'hit'", self.body)
        self.assertIn(".nd .inner { transition:transform", self.body)
        self.assertIn("pointer-events:none", self.body)

    def test_boxes_are_stacked_biggest_first(self):
        """A small box inside a large one has to end up on top to be clickable."""
        self.assertIn("Biggest first", self.body)

    def test_the_depth_rings_follow_the_camera(self):
        self.assertIn("function drawRings(", self.body)
        start = self.body.index("function drawRings(")
        self.assertIn("project3(polar(d * RING", self.body[start:start + 700])

    def test_views_tiles_zoom_and_pan(self):
        self.assertIn("Math.min(8, z *", self.body)
        self.assertIn("applyZoom", self.body)

    def test_anchors_sit_near_the_middle(self):
        self.assertIn("const ROOT_R = RING * 0.34", self.body)

    def test_the_focal_length_follows_the_scene_size(self):
        self.assertIn("FOCAL = Math.max(520, maxDepth * RING", self.body)

    def test_hovering_grows_the_node_and_warms_its_links(self):
        self.assertIn(".nd.hov .inner { transform:scale(", self.body)
        self.assertIn(".lk.warm", self.body)
        self.assertIn("touching.add(k.global_id)", self.body)

    def test_the_near_half_of_the_orbit_is_the_bottom_of_the_screen(self):
        """Near had to be down: the model once drew largest where it sat highest."""
        body = self.body[self.body.index("function camera("):]
        body = body[:body.index("function project(")]
        lines = [l.strip() for l in body.splitlines()
                 if l.strip().startswith("const Yr") or l.strip().startswith("const Zr")]
        self.assertEqual(len(lines), 2)
        exprs = {}
        for line in lines:
            name, rhs = line[len("const "):].split(" = ", 1)
            exprs[name] = rhs.rstrip(";").replace("Math.", "math.")
        best = None
        for degrees in range(0, 360, 15):
            a = math.radians(degrees)
            env = {"math": math, "Y": 0.0, "Z": math.sin(a) * 300.0, "tilt": 1.0}
            yr = eval(exprs["Yr"], {"math": math}, env)
            env["Yr"] = yr
            zr = eval(exprs["Zr"], {"math": math}, env)
            scale = 1000.0 / max(350.0, 1000.0 - zr)
            if best is None or scale > best[0]:
                best = (scale, yr)
        self.assertGreater(best[1], 0, "the largest node must sit below the centre")

    def test_selecting_lifts_the_lit_chain_above_the_other_links(self):
        """A lit ancestor link under dozens of dim ones read as a broken lineage."""
        self.assertIn("for (const a of chain(id)) { const l = linkEls.get(a.global_id);"
                      " if (l) gLinks.append(l); }", self.body)

    def test_no_control_characters(self):
        with open(TEMPLATE, "rb") as f:
            raw = f.read()
        self.assertEqual([b for b in raw if b < 9 or 13 < b < 32], [])




if __name__ == "__main__":
    unittest.main()
