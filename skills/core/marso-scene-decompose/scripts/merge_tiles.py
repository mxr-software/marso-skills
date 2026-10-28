#!/usr/bin/env python3
"""Join one image's whole-view and tile detections into its detections file and support tree.

Agents wrote their boxes in the picture they were shown: the whole-view agent in 0-1 of the
whole view, each tile agent in 0-1 of its own tile. This puts every box back in the whole
photograph, joins the objects a tile seam cut in two, drops the ones two tiles both found
(by the label-aware rule in merge_detections.py: one object in front of another is not a
duplicate, a holder is never the thing it holds), numbers the result, and works out what
each object rests on.

An agent says what it saw something rest on as a label in `on`, because it saw it there.
That is resolved to an object by label, then by geometry: the smallest surface whose box
holds the object's base. Nothing downstream re-derives it from boxes.

It decides no identity and invents no object. Everything it had to guess at is counted in
the report, so a bad tile shows up as a number instead of a surprise three stages later.

Exit codes: 0 written, 1 written with problems a person should look at, 2 an input could
not be read.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import merge_detections as md          # noqa: E402  (the dedupe rule lives there, once)

SEAM = 0.012            # a box this close to a tile edge was probably cut by it
NEAR_SEAM = 0.04        # ... and this close may have been: agents box a cut edge loosely
SPAN = 0.7              # pieces of one cut object line up across the seam by this share
SLIVER = 0.75           # share of a cut piece inside a bigger object for it to be that one's sliver
EDGE = 0.003            # ... and this close to the photograph's own edge, truncated by it
ABSORB = 0.8            # share of a tile object inside a whole-view one for it to be that one's partial
JOIN_GAP = 0.012        # two halves of one cut object may be this far apart
SATURATED = 40          # a tile with this many objects was probably not finished
SURFACE_CATEGORIES = {"furniture", "architecture", "appliance", "fixture"}
RELATIONS = {"on-top-of", "inside", "hanging-on", "leaning-against", "under",
             "attached-to", "part-of", "unknown"}
# What agents write when they mean one of the above.
RELATION_ALIASES = {"on": "on-top-of", "on top": "on-top-of", "resting-on": "on-top-of",
                    "in": "inside", "within": "inside", "contained": "inside",
                    "against": "leaning-against", "leaning": "leaning-against",
                    "hanging": "hanging-on", "hung-on": "hanging-on", "mounted-on": "attached-to",
                    "fixed-to": "attached-to", "attached": "attached-to", "part": "part-of",
                    "below": "under", "beneath": "under"}


def area(box) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def to_image(box: list, region: list) -> list:
    """A box in 0-1 of a tile, in 0-1 of the whole photograph."""
    rx0, ry0, rx1, ry1 = region
    x0, y0, x1, y1 = box
    out = [rx0 + clamp(x0) * (rx1 - rx0), ry0 + clamp(y0) * (ry1 - ry0),
           rx0 + clamp(x1) * (rx1 - rx0), ry0 + clamp(y1) * (ry1 - ry0)]
    return [round(clamp(min(out[0], out[2])), 5), round(clamp(min(out[1], out[3])), 5),
            round(clamp(max(out[0], out[2])), 5), round(clamp(max(out[1], out[3])), 5)]


def seams(local: list, region: list, tolerance: float = SEAM) -> list[str]:
    """Which edges of a tile this box touches where the tile does not end the photograph."""
    out = []
    if local[0] <= tolerance and region[0] > EDGE:
        out.append("left")
    if local[2] >= 1 - tolerance and region[2] < 1 - EDGE:
        out.append("right")
    if local[1] <= tolerance and region[1] > EDGE:
        out.append("top")
    if local[3] >= 1 - tolerance and region[3] < 1 - EDGE:
        out.append("bottom")
    return out


def photo_edges(box: list) -> list[str]:
    out = []
    if box[0] <= EDGE:
        out.append("left")
    if box[2] >= 1 - EDGE:
        out.append("right")
    if box[1] <= EDGE:
        out.append("top")
    if box[3] >= 1 - EDGE:
        out.append("bottom")
    return out


def gap(a: list, b: list) -> float:
    """The distance between two boxes along the axis they are furthest apart on; 0 if they touch."""
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return max(dx, dy)


def normalise(raw: dict, source: str, region: list, tile_id: str | None) -> dict | None:
    box = raw.get("bbox")
    if not (isinstance(box, list) and len(box) == 4
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in box)):
        return None
    global_box = to_image([float(v) for v in box], region)
    if area(global_box) <= 0:
        return None
    out = {k: v for k, v in raw.items() if k not in ("bbox", "local_id")}
    out["bbox"] = global_box
    out["label"] = str(raw.get("label") or "object").strip()
    out["pass"] = "overview" if tile_id is None else "tile"
    out["_source"] = source
    out["_tile"] = tile_id
    out["_seam"] = seams([float(v) for v in box], region) if tile_id else []
    out["_near"] = seams([float(v) for v in box], region, NEAR_SEAM) if tile_id else []
    out["_region"] = region
    out["_aliases"] = []
    return out


def fill_required(obj: dict, notes: dict) -> None:
    """The fields the downstream scripts require, defaulted honestly where an agent left them."""
    if not str(obj.get("description") or "").strip():
        obj["description"] = obj["label"]
    if not str(obj.get("category") or "").strip():
        obj["category"] = "other"
    size = obj.get("size_m")
    if not (isinstance(size, (int, float)) and not isinstance(size, bool) and size > 0):
        obj["size_m"] = 0.1
        obj["size_confidence"] = "low"
        obj["size_basis"] = "not estimated by the detector; a placeholder"
        notes["size_placeholders"] += 1
    if not str(obj.get("size_basis") or "").strip():
        obj["size_basis"] = "estimated from context in the view"
    if obj.get("size_confidence") not in md.CONFIDENCE_RANK:
        obj["size_confidence"] = "low" if obj.get("id_confidence") == "low" else "medium"
    if obj.get("id_confidence") not in md.CONFIDENCE_RANK:
        obj.pop("id_confidence", None)
    occlusion = str(obj.get("occlusion") or "").strip().lower()
    if occlusion not in ("none", "partial", "heavy"):
        occlusion = "partial" if obj.get("occluded") else "none"
    obj["occlusion"] = occlusion
    obj["occluded"] = occlusion != "none"
    if occlusion == "heavy" and not str(obj.get("whole_description") or "").strip():
        notes.setdefault("heavy_without_context", []).append(obj["label"])


def join_seams(objects: list[dict], notes: dict) -> list[dict]:
    """Join the two halves of one thing a tile seam cut: same name, touching, cut at a seam."""
    parts = list(objects)
    changed = True
    while changed:
        changed = False
        for i, a in enumerate(parts):
            for b in parts[i + 1:]:
                if not (a["_tile"] and b["_tile"]) or a["_tile"] == b["_tile"]:
                    continue
                if not (a["_seam"] or b["_seam"]):
                    continue
                if not md.alike(a, b) or gap(a["bbox"], b["bbox"]) > JOIN_GAP:
                    continue
                if md.iou(a["bbox"], b["bbox"]) >= 0.6:
                    continue                      # a plain duplicate; the dedupe will take it
                keep, other = (a, b) if md.richness(a) >= md.richness(b) else (b, a)
                keep["bbox"] = [round(min(a["bbox"][0], b["bbox"][0]), 5),
                                round(min(a["bbox"][1], b["bbox"][1]), 5),
                                round(max(a["bbox"][2], b["bbox"][2]), 5),
                                round(max(a["bbox"][3], b["bbox"][3]), 5)]
                keep["_seam"] = []
                parts.remove(other)
                notes["seam_joins"].append([a["label"], b["label"]])
                changed = True
                break
            if changed:
                break
    return parts


OPPOSITE = {"bottom": "top", "top": "bottom", "right": "left", "left": "right"}


def span_share(a: list, b: list, horizontal: bool) -> float:
    """How well two boxes line up along an axis: shared extent over the larger extent."""
    lo, hi = (0, 2) if horizontal else (1, 3)
    shared = min(a[hi], b[hi]) - max(a[lo], b[lo])
    larger = max(a[hi] - a[lo], b[hi] - b[lo])
    return shared / larger if larger > 0 else 0.0


def merge_into(keep: dict, other: dict, notes: dict, kind: str) -> None:
    """Fold `other` into `keep`: union box, and the other name kept so children naming it resolve."""
    keep["bbox"] = [round(min(keep["bbox"][0], other["bbox"][0]), 5),
                    round(min(keep["bbox"][1], other["bbox"][1]), 5),
                    round(max(keep["bbox"][2], other["bbox"][2]), 5),
                    round(max(keep["bbox"][3], other["bbox"][3]), 5)]
    keep["_aliases"] = keep.get("_aliases", []) + [other["label"]] + other.get("_aliases", [])
    keep["_seam"], keep["_near"] = [], []
    if not md.alike(keep, other):
        # Joined on geometry alone: say so where the viewer and the match round will see it.
        keep["id_confidence"] = "low"
        keep["note"] = (str(keep.get("note") or "") +
                        f" Joined across a tile seam with a piece named '{other['label']}'.").strip()
    notes[kind].append([keep["label"], other["label"]])


def join_across_seams(objects: list[dict], notes: dict) -> list[dict]:
    """Join the two pieces of one thing a seam cut when the tiles gave them different names.

    Two tiles told to name things briefly still called one tray 'wooden tray' and 'serving
    board', and one caddy 'shaker caddy' and 'wire caddy'. join_seams() needs the names to agree,
    so each survived as its own object, both carrying the same shakers. Geometry decides here:
    two pieces from tiles on either side of one seam, each cut (or nearly) at that seam,
    touching, and lined up along it, are one object. Lined up is what keeps a placemat crossing
    the same seam under a tray apart from it: one is narrower or wider than the other.
    """
    parts = list(objects)
    changed = True
    while changed:
        changed = False
        for a in parts:
            for b in parts:
                if a is b or not (a["_tile"] and b["_tile"]) or a["_tile"] == b["_tile"]:
                    continue
                for side in a["_near"]:
                    if OPPOSITE[side] not in b["_near"]:
                        continue
                    horizontal_seam = side in ("top", "bottom")
                    first, second = (a, b) if side in ("bottom", "right") else (b, a)
                    axis = 1 if horizontal_seam else 0
                    if first["bbox"][axis] > second["bbox"][axis]:
                        continue                  # not on either side of the seam
                    if gap(a["bbox"], b["bbox"]) > JOIN_GAP:
                        continue
                    if span_share(a["bbox"], b["bbox"], horizontal_seam) < SPAN:
                        continue
                    keep, other = (a, b) if md.richness(a) >= md.richness(b) else (b, a)
                    merge_into(keep, other, notes, "seam_joins")
                    parts.remove(other)
                    changed = True
                    break
                if changed:
                    break
            if changed:
                break
    return parts


def drop_slivers(objects: list[dict], notes: dict) -> list[dict]:
    """Drop the sliver of an object a seam cut, when another tile recorded the whole of it.

    A tile edge through a glasses case left 'hat' (a fifth of the case) on one side and the
    case on the other. A cut piece mostly inside a bigger object that crosses the cut line, and
    about as tall as it (for a cut on a left or right edge; as wide for top or bottom), is that
    object. 'About as tall' is what keeps a ring cut by the same seam on a placemat: it sits
    inside the placemat but is a fraction of its height. Only another tile's object can be the
    whole: an oven glove hanging on a tall housing the whole-view pass boxed floor to ceiling is
    inside it and as narrow as it, and is still its own thing. absorb_partials() handles
    whole-view objects, by name.
    """
    kept = []
    for obj in objects:
        whole = None
        for side in obj["_near"] if obj["_tile"] else []:
            region = obj["_region"]
            cut = {"left": region[0], "right": region[2], "top": region[1], "bottom": region[3]}[side]
            horizontal_seam = side in ("top", "bottom")
            lo, hi = (1, 3) if horizontal_seam else (0, 2)
            for big in objects:
                if big is obj or big["_tile"] in (None, obj["_tile"]) or area(big["bbox"]) <= area(obj["bbox"]):
                    continue
                if not big["bbox"][lo] < cut < big["bbox"][hi]:
                    continue
                if contained(obj["bbox"], big["bbox"]) < SLIVER:
                    continue
                if span_share(obj["bbox"], big["bbox"], horizontal_seam) < SPAN:
                    continue
                whole = big
                break
            if whole:
                break
        if whole:
            whole["_aliases"] = whole.get("_aliases", []) + [obj["label"]]
            notes["slivers"].append([obj["label"], whole["label"]])
        else:
            kept.append(obj)
    return kept


head = md.head


def contained(inner: list, outer: list) -> float:
    """What share of `inner` lies inside `outer`."""
    ix0, iy0 = max(inner[0], outer[0]), max(inner[1], outer[1])
    ix1, iy1 = min(inner[2], outer[2]), min(inner[3], outer[3])
    if ix0 >= ix1 or iy0 >= iy1:
        return 0.0
    return (ix1 - ix0) * (iy1 - iy0) / area(inner) if area(inner) else 0.0


def absorb_partials(objects: list[dict], notes: dict) -> list[dict]:
    """Drop a tile's object that is only part of something the whole-view pass already recorded.

    A tile agent told to leave large things alone still records a chair because it is
    chair-sized, under another name and a partial box ('dining chair' inside 'wishbone chair'
    overlapped by 0.54, under the duplicate threshold). A placemat cut by a seam came back as
    two halves the whole-view pass also had whole, and the chair count came out as four. The same
    head noun and almost all of the box inside a whole-view object is the same thing. Both of the
    two have to hold: 'table lamp' sits inside 'oak dining table' and is not a table.
    Only tile objects inside whole-view ones are absorbed, never two tile objects into each other,
    so a bottle standing in front of another bottle is untouched.
    """
    wholes = [o for o in objects if o["_tile"] is None]
    kept = []
    for obj in objects:
        if obj["_tile"] is not None:
            for big in wholes:
                if area(big["bbox"]) >= area(obj["bbox"]) and head(big["label"])                         and head(big["label"]) == head(obj["label"])                         and contained(obj["bbox"], big["bbox"]) >= ABSORB:
                    notes["absorbed"].append([obj["label"], big["label"]])
                    break
            else:
                kept.append(obj)
        else:
            kept.append(obj)
    return kept


def is_floor(obj: dict) -> bool:
    return "floor" in md.nouns(obj.get("label")) and obj.get("category") == "architecture"


def is_wall(obj: dict) -> bool:
    return bool(md.nouns(obj.get("label")) & {"wall", "ceiling"}) \
        and obj.get("category") == "architecture"


def base_point(box: list) -> tuple[float, float]:
    return ((box[0] + box[2]) / 2, box[3])


def inside(point: tuple, box: list, slack: float = 0.004) -> bool:
    return box[0] - slack <= point[0] <= box[2] + slack and box[1] - slack <= point[1] <= box[3] + slack


def resolve_parents(objects: list[dict], notes: dict) -> None:
    by_id = {o["local_id"]: o for o in objects}
    surface_ids = {o["local_id"] for o in objects
                   if o.get("surface") or o.get("category") in SURFACE_CATEGORIES}
    floors = [o for o in objects if is_floor(o)]

    def likeness(label_a: str, label_b: str) -> float:
        one, two = md.nouns(label_a), md.nouns(label_b)
        return len(one & two) / min(len(one), len(two)) if one and two else 0.0

    for obj in objects:
        if is_floor(obj) or is_wall(obj):
            obj["parent"], obj["relation"] = None, None
            continue
        point = base_point(obj["bbox"])
        own_area = area(obj["bbox"])
        candidates = [s for s in objects if s is not obj and area(s["bbox"]) > own_area
                      and s["local_id"] in surface_ids]
        chosen = None
        reason = None

        wanted = str(obj.get("on") or "").strip()
        if wanted:
            named = [s for s in objects if s is not obj and
                     max(likeness(wanted, name) for name in [s["label"], *s.get("_aliases", [])]) >= 0.5]
            if named:
                # A stack of three bowls each 'on bowl': the support is the one below, not the
                # smaller one sitting on top, or the stack loops.
                below = obj["bbox"][3]
                chosen = min(named, key=lambda s: (not inside(point, s["bbox"], 0.03),
                                                   s["bbox"][3] < below - 0.002,
                                                   area(s["bbox"])))
                reason = "named"
            else:
                notes["unresolved_on"].append([obj["local_id"], wanted])
        if chosen is None:
            held = [s for s in candidates if inside(point, s["bbox"])]
            non_floor = [s for s in held if not is_floor(s)]
            pool = non_floor or held
            if pool:
                chosen = min(pool, key=lambda s: area(s["bbox"]))
                reason = "geometry"
        if chosen is None and floors and obj.get("category") != "architecture":
            chosen, reason = floors[0], "floor"
        if chosen is None:
            obj["parent"], obj["relation"] = None, None
            notes["unparented"].append(obj["local_id"])
            continue

        obj["parent"] = chosen["local_id"]
        relation = str(obj.get("relation") or "").strip().lower().replace(" ", "-")
        relation = RELATION_ALIASES.get(relation, relation)
        if relation not in RELATIONS:
            relation = ""
            notes["relations_assumed"] += 1
        if not relation:
            relation = "attached-to" if (is_wall(chosen) or "splashback" in md.nouns(chosen["label"])) \
                and obj.get("category") in ("architecture", "fixture") else "on-top-of"
        obj["relation"] = relation
        obj["_parent_by"] = reason
        notes["parent_by"][reason] = notes["parent_by"].get(reason, 0) + 1

    # A parent chain that loops would make every later tree check meaningless. Cut one link per
    # loop, never the parents of everything that merely rests on a loop: a worktop and its base
    # units placed on each other must not orphan the kettle on the worktop. The link cut is the
    # least trustworthy one (geometry before a name the agent gave), then the largest object,
    # because a big thing resting on a smaller one is the likelier mistake.
    trust = {"named": 0, "geometry": 1, "floor": 1}
    for obj in objects:
        path, walk = [], obj["local_id"]
        while walk and walk not in path:
            path.append(walk)
            walk = by_id.get(walk, {}).get("parent")
        if not walk:
            continue
        loop = [by_id[i] for i in path[path.index(walk):]]
        cut = max(loop, key=lambda o: (trust.get(o.get("_parent_by"), 0), area(o["bbox"])))
        cut["parent"], cut["relation"] = None, None
        notes["loops_broken"].append(cut["local_id"])


def clusters_of(objects: list[dict], image_id: str) -> list[dict]:
    """Siblings with the same name are one cluster of instances: four onions, two chairs."""
    groups: dict[tuple, list[dict]] = {}
    for obj in objects:
        key = (obj.get("parent"), obj.get("category"), tuple(sorted(md.nouns(obj["label"]))))
        if key[2]:
            groups.setdefault(key, []).append(obj)
    clusters = []
    for (_parent, _cat, _nouns), members in groups.items():
        if len(members) >= 2:
            clusters.append({"cluster_id": f"{image_id}-c{len(clusters) + 1}",
                             "label": members[0]["label"], "kind": "instances",
                             "members": [m["local_id"] for m in members],
                             "note": "grouped by script: same parent and the same name"})
    return clusters


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--tiles", required=True, help="tiles.json from tile_images.py")
    parser.add_argument("--image-id", required=True, help="the image to merge, e.g. img001")
    parser.add_argument("--dir", required=True,
                        help="the folder holding <image_id>.whole.json and <image_id>.t<N>.json (the run's parts/)")
    parser.add_argument("--out", required=True, help="where to write detections/<image_id>.json")
    parser.add_argument("--structure", required=True, help="where to write structure/<image_id>.json")
    parser.add_argument("--iou", type=float, default=0.6)
    parser.add_argument("--iou-unlike", type=float, default=0.75)
    parser.add_argument("--force", action="store_true", help="overwrite existing outputs")
    args = parser.parse_args(argv)

    try:
        plan = load_json(pathlib.Path(args.tiles))
    except FileNotFoundError:
        print(f"error: no such file: {args.tiles}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"error: could not read {args.tiles}: {exc}", file=sys.stderr)
        return 2
    entry = (plan.get("images") or {}).get(args.image_id)
    if not entry:
        print(f"error: {args.image_id} is not in {args.tiles}", file=sys.stderr)
        return 2

    folder = pathlib.Path(args.dir)
    sources = [("whole", None, [0.0, 0.0, 1.0, 1.0])]
    sources += [(t["tile_id"], t["tile_id"], t["region"]) for t in entry.get("tiles") or []]

    notes = {"absorbed": [], "invalid": [], "size_placeholders": 0, "relations_assumed": 0, "unresolved_on": [], "unparented": [],
             "loops_broken": [], "parent_by": {}, "seam_joins": [], "slivers": []}
    per_source: dict[str, int] = {}
    missing: list[str] = []
    objects: list[dict] = []
    for name, tile_id, region in sources:
        path = folder / f"{args.image_id}.{name}.json"
        if not path.exists():
            missing.append(name)
            continue
        try:
            data = load_json(path)
        except (OSError, ValueError) as exc:
            print(f"error: could not read {path.as_posix()}: {exc}", file=sys.stderr)
            return 2
        raw = data.get("objects") if isinstance(data, dict) else None
        if not isinstance(raw, list):
            print(f"error: {path.as_posix()} has no 'objects' list", file=sys.stderr)
            return 2
        count = 0
        for item in raw:
            made = normalise(item, name, region, tile_id) if isinstance(item, dict) else None
            if made:
                objects.append(made)
                count += 1
            else:
                notes["invalid"].append(f"{name}: {str(item.get('label') if isinstance(item, dict) else item)[:40]}")
        per_source[name] = count

    if not objects:
        print("error: no object survived in any file", file=sys.stderr)
        return 2

    for obj in objects:
        fill_required(obj, notes)
    objects = join_seams(objects, notes)
    objects = join_across_seams(objects, notes)
    objects = drop_slivers(objects, notes)
    objects = absorb_partials(objects, notes)
    kept, dropped = md.merge(objects, args.iou, args.iou_unlike)
    possible = md.possible_duplicates(kept)

    for index, obj in enumerate(kept, start=1):
        obj["local_id"] = f"{args.image_id}-{index:03d}"
    resolve_parents(kept, notes)
    for obj in kept:
        edges = photo_edges(obj["bbox"])
        obj["truncated"] = edges
        for key in [k for k in obj if k.startswith("_")] + ["on", "surface"]:
            obj.pop(key, None)
        obj.setdefault("size_confidence", "medium")

    width_height = {"width": entry.get("width"), "height": entry.get("height")}
    detections = {
        "schema": "scene-decompose/detections@1", "image_id": args.image_id,
        "image": width_height,
        "passes": {"overview": sum(1 for o in kept if o["pass"] == "overview"),
                   "tile": sum(1 for o in kept if o["pass"] == "tile")},
        "objects": kept,
        "merge": {"sources": per_source, "inputs": sum(per_source.values()), "kept": len(kept),
                  "dropped": dropped, "seam_joins": notes["seam_joins"], "slivers": notes["slivers"]},
    }
    # The tree, in the shape check_structure.py reads.
    nodes = []
    for o in kept:
        node = {"local_id": o["local_id"], "label": o["label"], "parent": o.get("parent")}
        if o.get("parent"):
            node["relation"] = o["relation"]
        nodes.append(node)
    tree = {"schema": "scene-decompose/structure@1", "image_id": args.image_id,
            "anchors": sorted(n["local_id"] for n in nodes if not n["parent"]),
            "nodes": nodes, "clusters": clusters_of(kept, args.image_id), "areas": [],
            "built_by": "merge_tiles.py, from the parents the detection agents recorded"}

    flagged = []
    for name, tile_id, _region in sources:
        if name in missing:
            flagged.append(f"{name}: no result file, so that part of the photograph is missing")
        elif per_source.get(name, 0) == 0 and name != "whole":
            flagged.append(f"{name}: found nothing; check the tile really is empty")
        elif per_source.get(name, 0) >= SATURATED and name != "whole":
            flagged.append(f"{name}: {per_source[name]} objects, which looks unfinished; "
                           "split this tile and run it again")
    if notes["invalid"]:
        flagged.append(f"{len(notes['invalid'])} object(s) had no usable box and were left out: "
                       f"{notes['invalid'][:4]}")
    if notes["unresolved_on"]:
        flagged.append(f"{len(notes['unresolved_on'])} object(s) named a support that no object "
                       "matches; placed by geometry instead")
    if notes["unparented"]:
        flagged.append(f"{len(notes['unparented'])} object(s) have no parent: "
                       f"{notes['unparented'][:5]}")

    for path, data in ((pathlib.Path(args.out), detections), (pathlib.Path(args.structure), tree)):
        if path.exists() and not args.force:
            print(f"error: {path.as_posix()} exists; pass --force to overwrite", file=sys.stderr)
            return 1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    report = {
        "image_id": args.image_id, "objects": len(kept), "per_source": per_source,
        "missing": missing, "dropped_as_duplicates": len(dropped),
        "seam_joins": notes["seam_joins"], "slivers": notes["slivers"], "absorbed": notes["absorbed"],
        "possible_duplicates": possible, "parent_by": notes["parent_by"],
        "anchors": tree["anchors"], "clusters": len(tree["clusters"]),
        "invalid": notes["invalid"], "size_placeholders": notes["size_placeholders"], "relations_assumed": notes["relations_assumed"],
        "loops_broken": notes["loops_broken"], "flagged": flagged,
        "heavy_without_context": notes.get("heavy_without_context", []),
        "dropped": [{"labels": d.get("labels"), "iou": d.get("iou")} for d in dropped],
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    for line in flagged:
        print(f"warning: {line}", file=sys.stderr)
    return 1 if (missing or flagged) else 0


if __name__ == "__main__":
    sys.exit(main())
