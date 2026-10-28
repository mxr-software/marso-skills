#!/usr/bin/env python3
"""Work out where every object of a scene graph goes in 3D, from the establishing photograph.

Usage:
    layout_plan.py <run folder> --assets <assets.json> --out <placement.json>
                   [--graph scene_graph.json] [--registration registration.json]
                   [--manifest manifest.json] [--plan asset_plan.json] [--imports imports.json]
                   [--view img001] [--camera-height 1.5] [--hfov DEG | --focal-35mm 26]
                   [--pitch 0] [--ceiling-height 2.4] [--facing camera|none]
                   [--placeholders boxes|skip] [--unconfirmed skip|boxes] [--project NAME] [--force]

The graph, registration and manifest default to the files of those names in the run
folder. Writes marso/placement@1: the camera of the establishing view, the anchors
(floor and ceiling as empties, walls as planes), and one entry per object instance
with its graph parent, a bottom-centre position in metres (z up, floor at z=0, the
camera at the origin looking along +Y), a rotation about z, a target size and flags.
Every number is an estimate from one photograph; the review loop corrects them.
Standard library only.

Exit codes: 0 written, 1 written with objects that could not be positioned or sizes
that disagree (listed), or an input problem, 2 a JSON input could not be read.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import sys
import uuid

SCHEMA = "marso/placement@1"
SIZE_TOLERANCE = 0.25
DEFAULT_WALL_DEPTH = 3.0
INSIDE_LIFT = 0.05

# Landmarks are placed first: the room's big, fixed things that everything else is judged against.
LANDMARK_WORDS = (
    "wall", "door", "window", "fitted", "built-in", "builtin", "worktop", "counter", "cabinet",
    "cupboard", "kitchen units", "radiator", "fireplace", "sideboard", "modular", "shelving",
    "furniture", "table", "desk", "sofa", "bed", "wardrobe", "dresser", "island", "fridge",
    "oven", "range", "dishwasher", "washing machine", "appliance", "bookcase",
)
LANDMARK_SIZE = 1.0
OCCLUDED_FACTOR = 0.6


def read_json(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"error: no such file: {path.as_posix()}", file=sys.stderr)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"error: {path.as_posix()} is not valid JSON: {exc}", file=sys.stderr)
    except OSError as exc:
        print(f"error: cannot read {path.as_posix()}: {exc}", file=sys.stderr)
    return None


def matches(text: str, vocabulary) -> bool:
    return any(re.search(rf"\b{re.escape(word)}(s|es)?\b", text) for word in vocabulary)


def slug(text) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(text or "object").lower()).strip("_") or "object"


def longest(size_m) -> float:
    if isinstance(size_m, (int, float)) and not isinstance(size_m, bool):
        return float(size_m)
    if isinstance(size_m, dict):
        values = [v for v in size_m.values() if isinstance(v, (int, float))]
    elif isinstance(size_m, (list, tuple)):
        values = [v for v in size_m if isinstance(v, (int, float))]
    else:
        values = []
    return float(max(values)) if values else 0.0


def as_dims(value) -> list[float] | None:
    """[width x, depth y, height z] from a dict (w/d/h or x/y/z) or a three-number list."""
    if isinstance(value, dict):
        for keys in (("w", "d", "h"), ("x", "y", "z"), ("width", "depth", "height")):
            if all(isinstance(value.get(k), (int, float)) for k in keys):
                return [float(value[k]) for k in keys]
        return None
    if isinstance(value, (list, tuple)) and len(value) == 3 and all(isinstance(v, (int, float)) for v in value):
        return [float(v) for v in value]
    return None


PARK_X, PARK_Y, PARK_STEP = 3.0, 1.0, 1.0   # where unplaced objects wait: behind and left of the camera
MAX_WALL_DISTANCE = 15.0                      # a wall line further out than this is a bad projection
WALL_GAP = 0.02
FLAT = 0.35   # an object whose thinnest side is under this share of the next is flat


def lay_flat(dims: list[float], flags: list[str]) -> list[float]:
    """A flat object (a coaster, a placemat) generated standing on edge goes down on its broad face.

    The generator builds a mesh in the pose of its reference image, so a disc photographed at an
    angle can arrive upright. When the thinnest side is horizontal, the object is turned about the
    other horizontal axis: flagged `laid-flat-x` (thin along x, turn about y) or `laid-flat-y`.
    """
    x, y, z = dims
    thin = min(dims)
    rest = sorted(dims)[1]
    if thin >= FLAT * rest or z == thin:
        return dims
    if x == thin:
        flags.append("laid-flat-x")
        return [z, y, x]
    flags.append("laid-flat-y")
    return [x, z, y]


def frame_share(bbox) -> float:
    if not bbox or len(bbox) != 4:
        return 0.0
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def view_score(view: dict) -> float:
    score = frame_share(view.get("bbox"))
    if view.get("occlusion") == "heavy":
        score *= OCCLUDED_FACTOR / 2
    elif view.get("occluded"):
        score *= OCCLUDED_FACTOR
    return score * (1 - 0.15 * len(view.get("truncated") or []))


def view_in(node: dict, image_id: str) -> dict | None:
    views = [v for v in node.get("views") or [] if v.get("image_id") == image_id and v.get("bbox")]
    return max(views, key=view_score) if views else None


class Camera:
    """A pinhole camera at (0, 0, height) looking along +Y, pitched about X (positive looks up)."""

    def __init__(self, width: int, height: int, hfov_deg: float, cam_height: float, pitch_deg: float):
        self.width, self.height = width, height
        self.hfov = hfov_deg
        self.tx = math.tan(math.radians(hfov_deg) / 2)
        self.ty = self.tx * height / width
        self.vfov = math.degrees(2 * math.atan(self.ty))
        self.z = cam_height
        self.pitch = math.radians(pitch_deg)

    def ray(self, u: float, v: float) -> tuple[float, float, float]:
        x, y, z = (2 * u - 1) * self.tx, 1.0, (1 - 2 * v) * self.ty
        c, s = math.cos(self.pitch), math.sin(self.pitch)
        return x, y * c - z * s, y * s + z * c

    def on_plane_z(self, u: float, v: float, plane_z: float):
        """Where the ray through (u, v) meets the horizontal plane z = plane_z, if in front."""
        dx, dy, dz = self.ray(u, v)
        if abs(dz) < 1e-6:
            return None
        t = (plane_z - self.z) / dz
        if t <= 0:
            return None
        return [t * dx, t * dy, plane_z]

    def by_size(self, u: float, v: float, bbox, size: float):
        """Distance from apparent size: the box's larger angular extent spans `size` metres."""
        extent = max((bbox[2] - bbox[0]) * 2 * self.tx, (bbox[3] - bbox[1]) * 2 * self.ty)
        if extent <= 0 or size <= 0:
            return None
        depth = size / extent
        dx, dy, dz = self.ray(u, v)
        return [depth * dx / dy, depth, self.z + depth * dz / dy] if dy > 1e-6 else None

    def height_at(self, u: float, v: float, horizontal_distance: float):
        """How high the ray through (u, v) is when it is `horizontal_distance` metres away in plan."""
        dx, dy, dz = self.ray(u, v)
        across = math.hypot(dx, dy)
        if across < 1e-9:
            return None
        return self.z + dz * horizontal_distance / across

    def on_wall(self, u: float, v: float, wall: dict):
        (ax, ay), (bx, by) = wall["floor_line"]
        dx, dy, dz = self.ray(u, v)
        nx, ny = -(by - ay), bx - ax
        denom = nx * dx + ny * dy
        if abs(denom) < 1e-9:
            return None
        t = (nx * ax + ny * ay) / denom
        if t <= 0:
            return None
        return [t * dx, t * dy, self.z + t * dz]


def yaw_facing(point, target=(0.0, 0.0)) -> float:
    """Degrees about z that turn an object's front (-Y) towards the target in plan."""
    vx, vy = target[0] - point[0], target[1] - point[1]
    if abs(vx) < 1e-9 and abs(vy) < 1e-9:
        return 0.0
    return round(math.degrees(math.atan2(vx, -vy)), 2)


def anchor_kind(node: dict) -> str:
    text = " ".join(str(node.get(k) or "") for k in ("label", "category")).lower()
    for kind in ("floor", "ground", "wall", "ceiling"):
        if re.search(rf"\b{kind}s?\b", text):
            return "floor" if kind == "ground" else kind
    return "other"


def hfov_from_focal(focal_35mm: float, width: int, height: int) -> float:
    """Horizontal field of view from a 35 mm-equivalent focal length, defined on the 43.27 mm diagonal."""
    diagonal = math.hypot(width, height)
    sensor_w = 43.27 * width / diagonal
    return math.degrees(2 * math.atan(sensor_w / (2 * focal_35mm)))


def resolve_image(entry: dict, manifest_path: pathlib.Path) -> str | None:
    raw = pathlib.Path(str(entry.get("path") or ""))
    if not entry.get("path"):
        return None
    if raw.is_absolute():
        return raw.as_posix()
    for base in (pathlib.Path.cwd(), manifest_path.parent):
        if (base / raw).exists():
            return (base / raw).resolve().as_posix()
    return (manifest_path.parent / raw).as_posix()


def build(graph: dict, assets_doc: dict, registration: dict | None, manifest: dict, manifest_path: pathlib.Path,
          plan: dict | None, imports: dict | None, opts) -> dict:
    nodes = {n["global_id"]: n for n in graph.get("nodes") or [] if n.get("global_id")}
    images = {i["image_id"]: i for i in manifest.get("images") or [] if i.get("image_id")}
    assumptions, problems = [], []

    # The establishing view: the registration's choice, else the one that shows the most objects.
    view_id = opts.view or (registration or {}).get("establishing_view")
    if not view_id:
        counts: dict[str, int] = {}
        for node in nodes.values():
            for v in node.get("views") or []:
                counts[v.get("image_id")] = counts.get(v.get("image_id"), 0) + 1
        view_id = max(sorted(counts), key=lambda k: counts[k]) if counts else None
        assumptions.append(f"no establishing view registered; used {view_id}, the image showing the most objects")
    entry = images.get(view_id)
    if not entry or not entry.get("width") or not entry.get("height"):
        raise ValueError(f"the establishing view {view_id!r} has no width and height in the manifest")
    width, height = int(entry["width"]), int(entry["height"])
    if opts.hfov:
        hfov = opts.hfov
        assumptions.append(f"horizontal field of view {hfov:g} degrees, as given")
    else:
        hfov = hfov_from_focal(opts.focal_35mm, width, height)
        assumptions.append(f"horizontal field of view {hfov:.1f} degrees, from a {opts.focal_35mm:g} mm "
                           "35 mm-equivalent lens (a typical phone main camera); pass --hfov if known")
    cam = Camera(width, height, hfov, opts.camera_height, opts.pitch)
    assumptions.append(f"camera {opts.camera_height:g} m above the floor, pitch {opts.pitch:g} degrees, no roll")

    # Who is what: generated asset instance, placeholder, skipped, anchor.
    asset_of: dict[str, dict] = {}
    for asset in assets_doc.get("assets") or []:
        for member in asset.get("members") or []:
            asset_of[member] = asset
    routes = {}
    for asset in (plan or {}).get("assets") or []:
        for member in asset.get("members") or []:
            routes[member] = asset.get("route")
    imports = imports or {}
    groups_of: dict[str, list[str]] = {}
    for group in graph.get("identity_groups") or []:
        for member in group.get("members") or []:
            groups_of.setdefault(member, []).append(group.get("group_id"))

    def depth(gid: str) -> int:
        seen, d = set(), 0
        while nodes.get(gid, {}).get("parent") in nodes and gid not in seen:
            seen.add(gid)
            gid = nodes[gid]["parent"]
            d += 1
        return d

    anchors = {gid: n for gid, n in nodes.items() if n.get("parent") is None}
    skipped, kinds = [], {}
    for gid, node in nodes.items():
        if gid in anchors:
            continue
        reason = None
        if node.get("relation") == "part-of":
            reason = "part of its parent"
        elif node.get("unconfirmed") and opts.unconfirmed == "skip":
            reason = "unconfirmed reading"
        elif gid in asset_of:
            kinds[gid] = "asset"
        elif routes.get(gid) == "skip":
            reason = "routed skip in the plan"
        elif opts.placeholders == "skip":
            reason = f"not generated (route {routes.get(gid) or 'unknown'}); placeholders off"
        else:
            kinds[gid] = "placeholder"
        if reason:
            skipped.append({"global_id": gid, "label": node.get("label"), "reason": reason})
    # A node whose parent was skipped cannot be stacked on it: skip it too, so nothing floats.
    changed = True
    while changed:
        changed = False
        for gid in list(kinds):
            parent = nodes[gid].get("parent")
            if parent not in anchors and parent not in kinds:
                del kinds[gid]
                skipped.append({"global_id": gid, "label": nodes[gid].get("label"),
                                "reason": f"its parent {parent} is not placed"})
                changed = True

    # Size: the graph's estimate, shaped by the box; the minted size wins where one was imported.
    def best_any(node):
        views = [v for v in node.get("views") or [] if v.get("bbox")]
        return max(views, key=view_score) if views else None

    def dims_for(gid: str) -> tuple[list[float], str, list[str]]:
        node, flags = nodes[gid], []
        graph_dims = as_dims(node.get("size_m"))
        size = longest(node.get("size_m"))
        if graph_dims is None:
            view = view_in(node, view_id) or best_any(node)
            aspect = 1.0
            if view:
                b = view["bbox"]
                image = images.get(view["image_id"]) or entry
                bw = (b[2] - b[0]) * float(image.get("width") or width)
                bh = (b[3] - b[1]) * float(image.get("height") or height)
                aspect = bw / bh if bh > 0 else 1.0
            if aspect >= 1:
                w, h = size, size / aspect
            else:
                w, h = size * aspect, size
            graph_dims = [round(w, 3), round(min(w, h), 3), round(h, 3)]
        asset = asset_of.get(gid)
        minted = None
        if asset:
            result = imports.get(asset["asset_id"]) or asset.get("import") or {}
            minted = as_dims(result.get("dimensions_m"))
        if minted:
            minted = lay_flat(minted, flags)
            graph_size = max(graph_dims)
            if graph_size > 0 and abs(max(minted) / graph_size - 1) > SIZE_TOLERANCE:
                flags.append("size-disagrees")
            return minted, "minted", flags
        if not size:
            flags.append("no-size")
        return graph_dims, "graph", flags

    # Anchors: the floor at z=0, the ceiling at the stated height, walls from their floor line.
    anchor_out, walls = [], {}
    for gid in sorted(anchors):
        node = anchors[gid]
        kind = anchor_kind(node)
        row = {"global_id": gid, "label": node.get("label"), "kind": kind,
               "name": f"{slug(node.get('label'))}_{gid}", "flags": []}
        if kind == "floor" or kind == "other":
            row.update(object="empty", location=[0.0, 0.0, 0.0])
        elif kind == "ceiling":
            row.update(object="empty", location=[0.0, 0.0, opts.ceiling_height])
        else:
            row.update(object="plane")
            view = view_in(node, view_id)
            line = None
            if view and view["bbox"][3] < 0.98:
                b = view["bbox"]
                a = cam.on_plane_z(b[0], b[3], 0.0)
                c = cam.on_plane_z(b[2], b[3], 0.0)
                if a and c and math.dist(a[:2], c[:2]) > 0.05:
                    line = [a[:2], c[:2]]
                    row["basis"] = "the bottom edge of its box projected onto the floor"
                    row["flags"].append("wall-from-box")
            if line is None:
                row["flags"].append("wall-guessed")
            row["floor_line"] = line
            dims = as_dims(node.get("size_m"))
            tall = dims[2] if dims else 0.0  # a single size_m is the wall's width as often as its height
            row["wall_height"] = tall if 1.5 < tall < 6 else opts.ceiling_height
            walls[gid] = row
        anchor_out.append(row)

    placed: dict[str, dict] = {}

    def position(gid: str) -> dict:
        node = nodes[gid]
        dims, size_source, flags = dims_for(gid)
        w, d, h = dims
        parent = node.get("parent")
        relation = node.get("relation")
        view = view_in(node, view_id)
        loc, basis, yaw = None, None, None
        parent_anchor = anchors.get(parent)
        if parent_anchor is not None:
            kind = anchor_kind(parent_anchor)
            if kind == "wall" and walls[parent].get("floor_line") and view:
                b = view["bbox"]
                hit = cam.on_wall((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, walls[parent])
                if hit:
                    (ax, ay), (bx, by) = walls[parent]["floor_line"]
                    nx, ny = -(by - ay), bx - ax
                    norm = math.hypot(nx, ny) or 1.0
                    if nx * (0 - ax) + ny * (0 - ay) < 0:
                        nx, ny = -nx, -ny
                    loc = [hit[0] + nx / norm * d / 2, hit[1] + ny / norm * d / 2, max(0.0, hit[2] - h / 2)]
                    yaw = yaw_facing(loc, (loc[0] + nx, loc[1] + ny))  # its front faces into the room
                    basis = "box centre projected onto the wall plane"
            elif kind == "ceiling" and view:
                b = view["bbox"]
                hit = cam.on_plane_z((b[0] + b[2]) / 2, b[1], opts.ceiling_height)
                if hit:
                    loc, basis = [hit[0], hit[1], opts.ceiling_height - h], "box top projected onto the ceiling"
            if loc is None and view:
                b = view["bbox"]
                hit = cam.on_plane_z((b[0] + b[2]) / 2, b[3], 0.0) if b[3] < 0.995 else None
                if hit:
                    # The box's bottom edge is the object's nearest floor contact; its centre is half
                    # a depth further away.
                    dist = math.hypot(hit[0], hit[1]) or 1.0
                    if size_source == "graph" and b[1] > 0.005:
                        # A box's proportions in a photograph are not the object's: a run of base
                        # units seen at an angle looks square and became a 3.4 m cube. At a known
                        # distance the box's top edge gives the real height.
                        top = cam.height_at((b[0] + b[2]) / 2, b[1], dist)
                        if top and 0.02 < top < opts.ceiling_height:
                            h = round(top, 3)
                            d = min(d, w)
                            dims = [w, d, h]
                            flags.append("height-from-photo")
                    loc = [hit[0] + hit[0] / dist * d / 2, hit[1] + hit[1] / dist * d / 2, 0.0]
                    basis = "box bottom-centre projected onto the floor"
                else:
                    by_size = cam.by_size((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, b, max(dims))
                    if by_size:
                        loc = [by_size[0], by_size[1], 0.0 if kind != "wall" else max(0.0, by_size[2] - h / 2)]
                        basis = "distance from apparent size (the floor contact is out of frame)"
                        flags.append("depth-from-size")
        elif parent in placed:
            p = placed[parent]
            pw, pd, ph = p["dimensions_m"]
            px, py, pz = p["location"]
            # The view that sees both best gives the offset of the child's box inside the parent's.
            best, best_score = None, 0.0
            for v in node.get("views") or []:
                pv = view_in(nodes[parent], v.get("image_id"))
                if pv and v.get("bbox"):
                    score = view_score(v) * view_score(pv)
                    if score > best_score:
                        best, best_score = (v, pv), score
            fx, fz = 0.0, 0.0
            if best:
                cb, pb = best[0]["bbox"], best[1]["bbox"]
                pw_n, ph_n = (pb[2] - pb[0]) or 1e-6, (pb[3] - pb[1]) or 1e-6
                fx = max(-0.5, min(0.5, ((cb[0] + cb[2]) / 2 - pb[0]) / pw_n - 0.5))
                fz = max(0.0, min(1.0, 1 - (cb[3] - pb[1]) / ph_n))
                basis = f"offset of its box inside its parent's in {best[0]['image_id']}"
                if best[0]["image_id"] != view_id:
                    flags.append("offset-from-other-view")
            else:
                basis = "centred on its parent: no photograph shows both"
                flags.append("no-shared-view")
            pyaw = math.radians(p["rotation_z_deg"])
            ox, oy = fx * pw * math.cos(pyaw), fx * pw * math.sin(pyaw)
            if relation == "on-top-of":
                z = pz + ph
            elif relation == "under":
                z = pz
            elif relation == "inside":
                z = pz + max(INSIDE_LIFT * ph, fz * ph if fz < 0.9 else 0.0)
            else:
                z = pz + fz * ph
            loc = [px + ox, py + oy, z]
            if relation in ("hanging-on", "attached-to", "leaning-against"):
                yaw = p["rotation_z_deg"]
        if loc is None:
            # Not in the establishing view and not on a placed parent: stand it beside a placed twin.
            twin = next((placed[m] for c in graph.get("clusters") or [] if gid in (c.get("members") or [])
                         for m in c.get("members") or [] if m in placed), None)
            if twin is not None:
                tx, ty, tz = twin["location"]
                loc = [tx + twin["dimensions_m"][0] * 1.2, ty, tz]
                basis = f"beside {twin['global_id']}, a placed instance: not in the establishing view"
                flags.append("position-guessed")
            else:
                # Parked behind the camera, in a row, so a guess never stands in the photograph's view:
                # an espresso machine from a corner the establishing photo never shows ended up in
                # front of the table. What rests on it follows it there.
                parked[0] += 1
                loc = [-PARK_X - parked[0] * PARK_STEP, -PARK_Y, 0.0]
                basis = "unplaced: not in the establishing view and nothing placed to judge it by; parked out of view"
                flags.append("unplaced")
        if yaw is None:
            yaw = yaw_facing(loc) if opts.facing == "camera" else 0.0
        if node.get("unconfirmed"):
            flags.append("unconfirmed")
        if groups_of.get(gid):
            flags.append("identity-group")
        return {
            "global_id": gid,
            "label": node.get("label"),
            "kind": kinds[gid],
            "parent": parent,
            "relation": relation,
            "location": [round(c, 3) for c in loc],
            "rotation_z_deg": round(yaw, 2),
            "target_size_m": round(longest(node.get("size_m")), 3),
            "dimensions_m": [round(c, 3) for c in dims],
            "size_source": size_source,
            "position_basis": basis,
            "identity_groups": groups_of.get(gid, []),
            "flags": sorted(set(flags)),
        }

    # Order: anchors (already listed), then landmarks, then everything else by support depth.
    def is_landmark(gid: str) -> bool:
        node = nodes[gid]
        text = " ".join(str(node.get(k) or "") for k in ("label", "category")).lower()
        return node.get("parent") in anchors and (matches(text, LANDMARK_WORDS)
                                                  or longest(node.get("size_m")) >= LANDMARK_SIZE)

    parked = [0]
    order = sorted(kinds, key=lambda g: (0 if is_landmark(g) else 1,
                                         -longest(nodes[g].get("size_m")) if is_landmark(g) else depth(g),
                                         -longest(nodes[g].get("size_m")), g))
    # Walls the photograph gave no floor line for stand behind the furthest floor object.
    floor_first = [g for g in order if anchor_kind(anchors.get(nodes[g].get("parent"), {})) in ("floor", "other")
                   and nodes[g].get("parent") in anchors]
    for gid in floor_first:
        placed[gid] = position(gid)
    # A wall's box edge is not its floor line when the wall is seen at an angle, and one run put the
    # back wall through the middle of the table. A wall stands behind whatever stands in front of it.
    for wall in walls.values():
        line = wall["floor_line"]
        if line is None:
            continue
        (ax, ay), (bx, by) = line
        if max(abs(ay), abs(by), abs(ax), abs(bx)) > MAX_WALL_DISTANCE:
            wall["floor_line"] = None
            wall["flags"] = [f for f in wall["flags"] if f != "wall-from-box"] + ["wall-guessed"]
            continue
        lo, hi = min(ax, bx), max(ax, bx)
        push = 0.0
        for row in placed.values():
            if "unplaced" in row["flags"]:
                continue
            x, y, _ = row["location"]
            if not lo <= x <= hi:
                continue
            t = (x - ax) / (bx - ax) if abs(bx - ax) > 1e-9 else 0.5
            wall_y = ay + t * (by - ay)
            far = y + row["dimensions_m"][1] / 2
            if y < wall_y + row["dimensions_m"][1] and far > wall_y:
                push = max(push, far - wall_y + WALL_GAP)
        if push:
            wall["floor_line"] = [[ax, ay + push], [bx, by + push]]
            wall["flags"].append("wall-pushed-back")
    for wall in walls.values():
        if wall["floor_line"] is None:
            far = max((p["location"][1] + p["dimensions_m"][1] / 2 for p in placed.values()),
                      default=DEFAULT_WALL_DEPTH)
            far = max(far + 0.3, 1.0)
            half = far * cam.tx
            wall["floor_line"] = [[-half, far], [half, far]]
            wall["basis"] = "guessed: behind the furthest floor object, facing the camera"
    for wall in walls.values():
        (ax, ay), (bx, by) = wall["floor_line"]
        top = wall["wall_height"]
        wall["corners"] = [[round(ax, 3), round(ay, 3), 0.0], [round(bx, 3), round(by, 3), 0.0],
                           [round(bx, 3), round(by, 3), top], [round(ax, 3), round(ay, 3), top]]
        wall["floor_line"] = [[round(ax, 3), round(ay, 3)], [round(bx, 3), round(by, 3)]]
    for gid in order:
        if gid not in placed:
            placed[gid] = position(gid)

    objects = []
    for index, gid in enumerate(order, start=1):
        row = placed[gid]
        asset = asset_of.get(gid)
        if asset:
            row["asset_id"] = asset["asset_id"]
            row["name"] = f"{asset['asset_id']}_{slug(asset.get('label'))}_{gid}"
        else:
            row["name"] = f"box_{slug(row['label'])}_{gid}"
        row["order"] = index
        row["landmark"] = is_landmark(gid)
        objects.append(row)

    asset_rows = {}
    for asset in assets_doc.get("assets") or []:
        instances = [o["global_id"] for o in objects if o.get("asset_id") == asset["asset_id"]]
        if not instances:
            continue
        asset_rows[asset["asset_id"]] = {
            "label": asset.get("label"),
            "pbr_asset_id": asset.get("pbr_asset_id"),
            "minted": asset.get("minted"),
            "instances": instances,
            "copies": len(instances),
            "count": asset.get("count"),
            "count_at_least": asset.get("count_at_least"),
            "count_at_most": asset.get("count_at_most"),
            "imported": asset["asset_id"] in imports or (asset.get("import") or {}).get("status") == "done",
        }
        if asset.get("minted") != "minted":
            problems.append(f"{asset['asset_id']}: not minted ({asset.get('minted')}); import it only "
                            "after it is")

    for row in objects:
        for flag in ("unplaced", "size-disagrees"):
            if flag in row["flags"]:
                problems.append(f"{row['name']}: {flag}")

    yaw_cam = math.degrees(math.radians(90) + cam.pitch)
    return {
        "schema": SCHEMA,
        "run_id": assets_doc.get("run_id") or str(uuid.uuid5(uuid.NAMESPACE_URL,
                   str(manifest_path.resolve()) + "|" + str(assets_doc.get("project_id") or assets_doc.get("project")))),
        "project_id": assets_doc.get("project_id"),
        "project": opts.project or assets_doc.get("project"),
        "units": "metres; z up; floor z=0; camera at x=0, y=0 looking along +Y",
        "location_means": "the bottom centre of the object's bounding box",
        "camera": {
            "image_id": view_id,
            "photo": resolve_image(entry, manifest_path),
            "resolution": [width, height],
            "hfov_deg": round(hfov, 3),
            "vfov_deg": round(cam.vfov, 3),
            "height_m": opts.camera_height,
            "pitch_deg": opts.pitch,
            "location": [0.0, 0.0, opts.camera_height],
            "rotation_euler_deg": [round(yaw_cam, 3), 0.0, 0.0],
        },
        "assumptions": assumptions,
        "anchors": anchor_out,
        "objects": objects,
        "assets": asset_rows,
        "skipped": sorted(skipped, key=lambda s: s["global_id"]),
        "problems": problems,
        "review": [],
        "summary": {
            "objects": len(objects),
            "assets": sum(1 for o in objects if o["kind"] == "asset"),
            "placeholders": sum(1 for o in objects if o["kind"] == "placeholder"),
            "skipped": len(skipped),
            "landmarks": sum(1 for o in objects if o["landmark"]),
            "flagged": sum(1 for o in objects if o["flags"]),
            "size_disagrees": sum(1 for o in objects if "size-disagrees" in o["flags"]),
            "unplaced": sum(1 for o in objects if "unplaced" in o["flags"]),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run", help="the decompose run folder")
    parser.add_argument("--assets", required=True, help="assets.json from the generation run")
    parser.add_argument("--out", required=True, help="write placement.json here")
    parser.add_argument("--graph", help="default <run>/scene_graph.json")
    parser.add_argument("--registration", help="default <run>/registration.json, if present")
    parser.add_argument("--manifest", help="default <run>/manifest.json")
    parser.add_argument("--plan", help="asset_plan.json, to name the route of objects not generated")
    parser.add_argument("--imports", help="imports.json: {asset_id: import_scene_asset result}")
    parser.add_argument("--view", help="image id to place from, instead of the establishing view")
    parser.add_argument("--camera-height", type=float, default=1.5)
    parser.add_argument("--hfov", type=float, help="horizontal field of view in degrees")
    parser.add_argument("--focal-35mm", type=float, default=26.0, help="35 mm-equivalent focal length")
    parser.add_argument("--pitch", type=float, default=0.0, help="camera pitch in degrees, positive up")
    parser.add_argument("--ceiling-height", type=float, default=2.4)
    parser.add_argument("--facing", choices=("camera", "none"), default="camera")
    parser.add_argument("--placeholders", choices=("boxes", "skip"), default="boxes")
    parser.add_argument("--unconfirmed", choices=("skip", "boxes"), default="skip")
    parser.add_argument("--project", help="collection name; default the project in assets.json")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    run = pathlib.Path(args.run)
    graph_path = pathlib.Path(args.graph) if args.graph else run / "scene_graph.json"
    manifest_path = pathlib.Path(args.manifest) if args.manifest else run / "manifest.json"
    reg_path = pathlib.Path(args.registration) if args.registration else run / "registration.json"
    graph = read_json(graph_path)
    manifest = read_json(manifest_path)
    assets_doc = read_json(pathlib.Path(args.assets))
    if graph is None or manifest is None or assets_doc is None:
        return 2
    registration = None
    if args.registration or reg_path.exists():
        registration = read_json(reg_path)
        if registration is None:
            return 2
    plan = read_json(pathlib.Path(args.plan)) if args.plan else None
    imports = read_json(pathlib.Path(args.imports)) if args.imports else None
    if (args.plan and plan is None) or (args.imports and imports is None):
        return 2
    if not isinstance(graph.get("nodes"), list) or not graph["nodes"]:
        print("error: the graph has no nodes", file=sys.stderr)
        return 1
    if args.hfov is not None and not 1 <= args.hfov < 179:
        print("error: --hfov must be between 1 and 179 degrees", file=sys.stderr)
        return 1
    out = pathlib.Path(args.out)
    if out.exists() and not args.force:
        print(f"error: {out.as_posix()} exists; pass --force to overwrite", file=sys.stderr)
        return 1
    try:
        placement = build(graph, assets_doc, registration, manifest, manifest_path, plan, imports, args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(placement, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": out.as_posix(), **placement["summary"], "problems": placement["problems"]}, indent=2))
    return 1 if placement["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
