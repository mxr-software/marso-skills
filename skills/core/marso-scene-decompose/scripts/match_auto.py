#!/usr/bin/env python3
"""Match what is obvious by script, and leave a small residue for an agent.

Most cross-view matches need no judgement. A floor is the floor. A label that appears
once among its siblings, under a parent already matched, in both views, is that thing.
The last pipeline spent eighteen agent-minutes reasoning about those. This pairs them
top-down — anchors, then the children of every matched pair, then theirs — and records
the two lines of evidence the rules ask for.

What it cannot settle it leaves as *groups*, one per matched carrier (the worktop, the
tray, the table): the unmatched things on that carrier in each view, with a contact sheet
showing the same carrier in every view stacked together. An agent judges those and nothing
else. The default for anything unclear is not to merge, which is cheap and never wrong.

It merges only on its own two lines of evidence, never across two images that registration
says do not overlap, and never puts two objects from one image in one global object.
Pairing runs per image pair, so no match is ever "A is B, B is C" with A and C never compared.

Pillow is needed for the contact sheets only; without it the groups are still written.

Exit codes: 0 done, 2 an input could not be read.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import pathlib
import re
import sys

STOPWORDS = {"a", "an", "the", "of", "with", "and", "on", "in", "small", "large", "dark", "light",
             "left", "right", "hand", "upper", "lower", "back", "front", "second", "round",
             "black", "white", "grey", "gray", "silver", "gold", "golden", "clear", "glass",
             "plastic", "metal", "wooden", "red", "blue", "green", "pink", "tall", "short"}
# Colour and material words are dropped from names so 'steel kettle' matches 'kettle', but two
# names that each carry one and disagree are two things: 'black vase' and 'glass vase' came out
# as one object on the strength of the word 'vase'. Words in one set are the same quality.
QUALITIES = [{"grey", "gray", "silver", "steel", "stainless", "chrome", "metal", "metallic"},
             {"gold", "golden", "brass", "yellow"}, {"clear", "glass", "transparent"},
             {"white", "cream", "ivory"}, {"wooden", "wood", "oak", "walnut", "timber"},
             {"black"}, {"red"}, {"blue"}, {"green"}, {"pink"}, {"brown"}, {"orange"},
             {"purple"}, {"plastic"}, {"ceramic"}, {"cork"}, {"woven"}]
REGION_PAD = 0.1        # a close-up's region is a rough rectangle: widen it by this share
REGION_REACH = 0.32     # how far, in region widths, a mapped position may be from a candidate
SMALL = 0.15            # bigger than this share of the picture is not a position candidate
CHECK_AREA = 0.15       # automatic matches this big in every view are not worth a picture
CHECK_PER_SHEET = 5
CHECK_PANEL = 300
EASY = 0.8              # label likeness for an automatic match
KIND = 0.7              # score of a match made on the kind of thing alone
RELATED = 0.5           # ... for "this might be the same thing"
LOOSE = 0.34            # ... for being worth an agent's look when the parents did not match
SIZE_RATIO = 4.0
GROUP_CAP = 24          # members of one group on one side
BATCH_TARGET = 26       # objects per agent
SHEET_WIDTH = 1568
SHEET_HEIGHT = 1500


def nouns(label) -> set:
    return {w for w in re.findall(r"[a-z]+", str(label or "").lower())
            if len(w) > 2 and w not in STOPWORDS}


def likeness(a, b) -> float:
    one, two = nouns(a), nouns(b)
    return len(one & two) / min(len(one), len(two)) if one and two else 0.0


def head(label) -> str:
    """The word that says what it is: the last real word. 'parquet floor' and 'wood floor' are floors."""
    found = [w for w in re.findall(r"[a-z]+", str(label or "").lower())
             if len(w) > 2 and w not in STOPWORDS]
    return found[-1] if found else ""


def qualities(label) -> set:
    words = set(re.findall(r"[a-z]+", str(label or "").lower()))
    return {i for i, family in enumerate(QUALITIES) if family & words}


def conflict(a, b) -> bool:
    """Each name states a colour or material and they disagree: not an automatic match."""
    one, two = qualities(a), qualities(b)
    return bool(one) and bool(two) and not (one & two)


def jaccard(a, b) -> float:
    """How much two names are the same name. Used for uniqueness, where 'overlap' misleads:
    'blue case' shares its only word with 'earbud charging case', and they are two things."""
    one, two = nouns(a), nouns(b)
    return len(one & two) / len(one | two) if one and two else 0.0


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_nodes(structures: pathlib.Path, detections: pathlib.Path) -> dict[str, dict]:
    """local_id -> everything known about it, from the structure and the detections."""
    nodes: dict[str, dict] = {}
    for path in sorted(detections.glob("*.json")):
        data = load(path)
        image_id = data.get("image_id") or path.stem
        if "." in path.stem:                       # a per-tile partial, not the merge
            continue
        for obj in data.get("objects") or []:
            if obj.get("local_id"):
                nodes[obj["local_id"]] = {
                    "image_id": image_id, "local_id": obj["local_id"], "label": obj.get("label"),
                    "description": obj.get("description"), "category": obj.get("category"),
                    "bbox": obj.get("bbox"), "size_m": obj.get("size_m"),
                    "id_confidence": obj.get("id_confidence", "high"), "parent": None,
                    "relation": None}
    for path in sorted(structures.glob("*.json")):
        data = load(path)
        for node in data.get("nodes") or []:
            entry = nodes.get(node.get("local_id"))
            if entry is not None:
                entry["parent"] = node.get("parent")
                entry["relation"] = node.get("relation")
    return nodes


class Globals:
    """Global objects under construction: at most one member per image, always."""

    def __init__(self) -> None:
        self.members: list[dict[str, str]] = []          # image_id -> local_id
        self.meta: list[dict] = []
        self.of: dict[str, int] = {}

    def try_match(self, a: dict, b: dict, label: str, confidence: str, evidence: list[str]) -> bool:
        ia, ib = self.of.get(a["local_id"]), self.of.get(b["local_id"])
        if ia is not None and ia == ib:
            return True
        if ia is not None and ib is not None:
            ma, mb = self.members[ia], self.members[ib]
            if set(ma) & set(mb):
                return False                              # they already hold different views
            ma.update(mb)
            for lid in mb.values():
                self.of[lid] = ia
            self.meta[ia]["evidence"] += evidence
            self.members[ib], self.meta[ib] = {}, {}
            return True
        if ia is not None:
            if b["image_id"] in self.members[ia]:
                return False
            self.members[ia][b["image_id"]] = b["local_id"]
            self.of[b["local_id"]] = ia
            self.meta[ia]["evidence"] += evidence
            return True
        if ib is not None:
            if a["image_id"] in self.members[ib]:
                return False
            self.members[ib][a["image_id"]] = a["local_id"]
            self.of[a["local_id"]] = ib
            self.meta[ib]["evidence"] += evidence
            return True
        self.members.append({a["image_id"]: a["local_id"], b["image_id"]: b["local_id"]})
        self.meta.append({"label": label, "confidence": confidence, "evidence": list(evidence)})
        index = len(self.members) - 1
        self.of[a["local_id"]] = self.of[b["local_id"]] = index
        return True

    def free(self, node: dict, other_image: str) -> bool:
        """Can this node still be matched to something in `other_image`?"""
        index = self.of.get(node["local_id"])
        return index is None or other_image not in self.members[index]

    def done(self) -> list[dict]:
        out = []
        for members, meta in zip(self.members, self.meta):
            if len(members) > 1:
                out.append({"members": [{"image_id": i, "local_id": l} for i, l in sorted(members.items())],
                            "label": meta["label"], "confidence": meta["confidence"],
                            "evidence": list(dict.fromkeys(meta["evidence"]))})
        return out


def easy_pairs(left: list[dict], right: list[dict]) -> list[tuple[dict, dict, float]]:
    """Mutual-best, unmistakable pairs: a label that appears once on each side.

    A second route: the same *kind* of thing (the same last word) when each side has exactly
    one of that kind among these siblings. 'wood floor' and 'parquet floor' share one word and
    were never matched by name, which left every chair on them unmatched too. It scores lower,
    so the match is `medium` and says why.
    """
    out = []
    for a in left:
        similar_a = [x for x in left if jaccard(a["label"], x["label"]) >= RELATED]
        scored = sorted(((likeness(a["label"], b["label"]), b) for b in right),
                        key=lambda s: (-s[0], -jaccard(a["label"], s[1]["label"])))
        if scored and scored[0][0] >= EASY and len(similar_a) == 1:
            score, b = scored[0]
            similar_b = [x for x in right if jaccard(b["label"], x["label"]) >= RELATED]
            if len(similar_b) != 1:
                continue
            back = max(left, key=lambda x: (likeness(b["label"], x["label"]),
                                            jaccard(b["label"], x["label"])))
            if back is not a:
                continue
        else:
            kind = head(a["label"])
            same_a = [x for x in left if head(x["label"]) == kind]
            same_b = [y for y in right if head(y["label"]) == kind]
            if not kind or len(same_a) != 1 or len(same_b) != 1:
                continue
            score, b = KIND, same_b[0]
        # Category is not compared: two independent agents file one worktop as architecture
        # and as furniture, and requiring a match left it unmatched and everything on it
        # without a matched parent.
        if conflict(a["label"], b["label"]):
            continue
        sa, sb = a.get("size_m"), b.get("size_m")
        if isinstance(sa, (int, float)) and isinstance(sb, (int, float)) and sa > 0 and sb > 0                 and max(sa, sb) / min(sa, sb) > SIZE_RATIO:
            continue
        out.append((a, b, score))
    return out


def pair_up(image_a: str, image_b: str, nodes: dict, globals_: Globals):
    """The matched (a, b) pairs already known between these two images."""
    out = []
    for members in globals_.members:
        if image_a in members and image_b in members:
            out.append((nodes[members[image_a]], nodes[members[image_b]]))
    return out


def prune(left: list[dict], right: list[dict]) -> tuple[list[dict], list[dict]]:
    """Keep a big group small: only the members with a plausible counterpart on the other side.

    A small group is kept whole, so a watch that one view calls 'small black device' still
    reaches an agent. A large one is not: a table with twenty things on it would otherwise
    be sent out whole because three of them are hard.
    """
    if len(left) <= 8 and len(right) <= 8:
        return left, right
    keep_left = [a for a in left if any(likeness(a["label"], b["label"]) >= LOOSE for b in right)]
    keep_right = [b for b in right if any(likeness(a["label"], b["label"]) >= LOOSE for a in left)]
    return keep_left, keep_right


def box_area(node: dict) -> float:
    b = node.get("bbox")
    return (b[2] - b[0]) * (b[3] - b[1]) if b else 0.0


def centre(node: dict):
    b = node.get("bbox")
    return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) if b else None


def by_position(wide: str, close: str, region: list, nodes: dict, globals_: Globals,
                groups: list[dict], first: int) -> None:
    """Candidates by where they are, for what the names could not pair.

    A close-up covers a known region of the wider photograph, so a thing in that region of the
    wide shot and a thing in the close-up are candidates for each other whatever they are
    called: the same puck was 'earbuds case' in one view and 'hockey puck' in the other, and
    names never offered them to an agent. The position is rough (the views differ in angle), so
    this only decides who is *offered*; an agent still judges, and a pair is offered only if one
    of the two was not already in a group for this pair of photographs.
    """
    x0, y0, x1, y1 = region
    w, h = max(x1 - x0, 1e-6), max(y1 - y0, 1e-6)
    seen = {m["local_id"] for g in groups[first:] for ms in g["members"].values() for m in ms}
    in_region = lambda n: (centre(n) and x0 - REGION_PAD * w <= centre(n)[0] <= x1 + REGION_PAD * w
                           and y0 - REGION_PAD * h <= centre(n)[1] <= y1 + REGION_PAD * h)
    left = [n for n in nodes.values() if n["image_id"] == wide and n["parent"] is not None
            and globals_.free(n, close) and 0 < box_area(n) < SMALL and in_region(n)]
    right = [n for n in nodes.values() if n["image_id"] == close and n["parent"] is not None
             and globals_.free(n, wide) and 0 < box_area(n) < SMALL]
    keep_left, keep_right = {}, {}
    for a in left:
        ax, ay = centre(a)
        for b in right:
            if a["local_id"] in seen and b["local_id"] in seen:
                continue
            sa, sb = a.get("size_m"), b.get("size_m")
            if (isinstance(sa, (int, float)) and isinstance(sb, (int, float)) and sa > 0 and sb > 0
                    and max(sa, sb) / min(sa, sb) > SIZE_RATIO):
                continue
            bx, by = centre(b)
            mapped = (x0 + bx * w, y0 + by * h)
            if abs(mapped[0] - ax) / w <= REGION_REACH and abs(mapped[1] - ay) / h <= REGION_REACH:
                keep_left[a["local_id"]], keep_right[b["local_id"]] = a, b
    if keep_left and keep_right:
        groups.append({"carrier": "the same place in both photographs (offered by position)",
                       "images": [wide, close],
                       "members": {wide: list(keep_left.values())[:GROUP_CAP],
                                   close: list(keep_right.values())[:GROUP_CAP]},
                       "relation": "close-up"})


def run_pair(image_a: str, image_b: str, relation: str, nodes: dict, globals_: Globals,
             groups: list[dict], region: list | None = None, closer: str | None = None) -> int:
    """Top-down matching between two images, repeated until nothing new matches."""
    children = {i: {} for i in (image_a, image_b)}
    for n in nodes.values():
        if n["image_id"] in children:
            children[n["image_id"]].setdefault(n["parent"], []).append(n)

    def siblings(parent_a, parent_b):
        left = [n for n in children[image_a].get(parent_a["local_id"] if parent_a else None, [])
                if globals_.free(n, image_b)]
        right = [n for n in children[image_b].get(parent_b["local_id"] if parent_b else None, [])
                 if globals_.free(n, image_a)]
        return left, right

    made = 0
    for _ in range(6):
        new = 0
        # 1. children of every matched pair, and of the anchors, that are unmistakable.
        for pa, pb in [(None, None)] + pair_up(image_a, image_b, nodes, globals_):
            left, right = siblings(pa, pb)
            carrier = (pa or {}).get("label") or "the anchors"
            for a, b, score in easy_pairs(left, right):
                if score >= EASY:
                    line_one = (f"same name in both views ('{a['label']}' / '{b['label']}'), and the "
                                f"only such thing among its siblings")
                else:
                    line_one = (f"the same kind of thing ('{head(a['label'])}': '{a['label']}' / "
                                f"'{b['label']}'), and the only one among its siblings in both views")
                line_two = (f"matched parent: both rest on the {carrier}" if pa else
                            f"registration: the two views overlap ({relation}), and each has one "
                            f"{'/'.join(sorted(nouns(a['label']) & nouns(b['label'])) or ['such anchor'])}")
                if globals_.try_match(a, b, a["label"], "high" if score >= 0.99 else "medium",
                                      [line_one, line_two]):
                    new += 1
        # 2. a weaker pass: the name is unique in the whole image and the parents agree by
        #    name though they were not matched, which is how 'kitchen splashback' and
        #    'splashback panel' strand everything standing against them.
        free_a = [n for n in nodes.values() if n["image_id"] == image_a and globals_.free(n, image_b)]
        free_b = [n for n in nodes.values() if n["image_id"] == image_b and globals_.free(n, image_a)]
        for a, b, score in easy_pairs(free_a, free_b):
            pa, pb = nodes.get(a["parent"]), nodes.get(b["parent"])
            if pa is None or pb is None or likeness(pa["label"], pb["label"]) < RELATED:
                continue
            if globals_.try_match(a, b, a["label"], "medium", [
                    f"same name in both views ('{a['label']}' / '{b['label']}'), unique in each photograph",
                    f"parents agree by name ('{pa['label']}' / '{pb['label']}'), though they were not matched"]):
                new += 1
        made += new
        if not new:
            break

    # What is left, per matched carrier.
    first = len(groups)
    for pa, pb in [(None, None)] + pair_up(image_a, image_b, nodes, globals_):
        left, right = siblings(pa, pb)
        if not (left and right):
            continue
        left, right = prune(left, right)
        if left and right:
            groups.append({"carrier": (pa or {}).get("label") or "the anchors",
                           "images": [image_a, image_b],
                           "members": {image_a: left[:GROUP_CAP], image_b: right[:GROUP_CAP]},
                           "relation": relation})

    # Things whose parent found no counterpart: offer only the pairs that share a word.
    # "Already in a group" is per pair of photographs. It used to be across all of them, so the
    # two chairs of the wide shot, placed in a group against the kitchen where there was nothing
    # to match, were never offered against the chair in the close-up.
    seen = {m["local_id"] for g in groups[first:] for ms in g["members"].values() for m in ms}
    leftover_a = [n for n in nodes.values() if n["image_id"] == image_a and globals_.free(n, image_b)
                  and n["parent"] is not None and n["local_id"] not in seen]
    leftover_b = [n for n in nodes.values() if n["image_id"] == image_b and globals_.free(n, image_a)
                  and n["parent"] is not None and n["local_id"] not in seen]
    loose_a = [a for a in leftover_a if any(likeness(a["label"], b["label"]) >= LOOSE for b in leftover_b)]
    loose_b = [b for b in leftover_b if any(likeness(a["label"], b["label"]) >= LOOSE for a in loose_a)]
    if loose_a and loose_b:
        groups.append({"carrier": "things whose parents did not match", "images": [image_a, image_b],
                       "members": {image_a: loose_a[:GROUP_CAP], image_b: loose_b[:GROUP_CAP]},
                       "relation": relation})
    if region and closer in (image_a, image_b) and len(region) == 4:
        by_position(image_b if closer == image_a else image_a, closer, region, nodes, globals_, groups, first)
    return made


def overlapping(registration: dict | None, images: list[str]) -> list[tuple[str, str, str]]:
    if not registration:
        return [(a, b, "unknown") for a, b in itertools.combinations(sorted(images), 2)]
    out = []
    for pair in registration.get("pairs") or []:
        relation = pair.get("relation")
        if relation and relation != "no-overlap" and pair.get("a") in images and pair.get("b") in images:
            out.append((pair["a"], pair["b"], relation))
    return out


def regions(registration: dict | None) -> dict:
    """(a, b) -> (closer image, region of the wider one) for every close-up that says where."""
    out = {}
    for pair in (registration or {}).get("pairs") or []:
        region = pair.get("region")
        if (pair.get("relation") == "close-up" and pair.get("closer") in (pair.get("a"), pair.get("b"))
                and isinstance(region, list) and len(region) == 4
                and all(isinstance(v, (int, float)) for v in region)):
            out[(pair["a"], pair["b"])] = (pair["closer"], region)
    return out


def find_image(raw: str, roots: list[pathlib.Path]):
    candidate = pathlib.Path(raw)
    if candidate.is_absolute():
        return candidate if candidate.exists() else None
    for root in roots:
        if (root / candidate).exists():
            return root / candidate
    return None


def draw_sheet(group: dict, sources: dict, out: pathlib.Path) -> bool:
    """The same carrier in every view, stacked, with each member's box and id drawn on it."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    images = group["images"]
    height_each = SHEET_HEIGHT // len(images)
    panels = []
    for image_id in images:
        source = sources.get(image_id)
        members = group["members"][image_id]
        if source is None or not members:
            continue
        with Image.open(source) as opened:
            from PIL import ImageOps
            picture = ImageOps.exif_transpose(opened).convert("RGB")
        width, height = picture.size
        boxes = [m["bbox"] for m in members if m.get("bbox")]
        if not boxes:
            continue
        x0, y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
        x1, y1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
        padx, pady = (x1 - x0) * 0.08 + 0.01, (y1 - y0) * 0.08 + 0.01
        region = (max(0.0, x0 - padx), max(0.0, y0 - pady), min(1.0, x1 + padx), min(1.0, y1 + pady))
        crop = picture.crop((round(region[0] * width), round(region[1] * height),
                             round(region[2] * width), round(region[3] * height)))
        scale = min(SHEET_WIDTH / crop.width, (height_each - 16) / crop.height)
        crop = crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))))
        draw = ImageDraw.Draw(crop)
        colours = ["#ff2d55", "#00b8ff", "#ffd400", "#2bd96b"]
        for index, member in enumerate(members):
            if not member.get("bbox"):
                continue
            bx0, by0, bx1, by1 = member["bbox"]
            rect = [(bx0 - region[0]) / (region[2] - region[0]) * crop.width,
                    (by0 - region[1]) / (region[3] - region[1]) * crop.height,
                    (bx1 - region[0]) / (region[2] - region[0]) * crop.width,
                    (by1 - region[1]) / (region[3] - region[1]) * crop.height]
            colour = colours[index % len(colours)]
            draw.rectangle(rect, outline=colour, width=2)
            tag = member["local_id"].split("-")[-1]
            draw.text((rect[0] + 2, max(0, rect[1] - 11)), tag, fill=colour)
        panels.append((image_id, crop))
    if not panels:
        return False
    sheet = Image.new("RGB", (max(c.width for _, c in panels),
                              sum(c.height + 16 for _, c in panels)), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    y = 0
    for image_id, crop in panels:
        draw.text((4, y + 2), f"{image_id}   (carrier: {group['carrier']})", fill="#ffffff")
        sheet.paste(crop, (0, y + 16))
        y += crop.height + 16
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=88)
    return True


def checks_for(matched: list[dict], nodes: dict) -> list[dict]:
    """The automatic matches worth a look: the names differ, and the objects are not huge.

    Two views that call a thing the same name are rarely wrong; two that call it different names
    and were paired by the kind of thing are where a vase meets a different vase. Big objects
    (floors, walls, tables) are easy to judge from the overlays and cost a lot of picture.
    """
    out = []
    for found in matched:
        members = [nodes[m["local_id"]] for m in found["members"] if m["local_id"] in nodes]
        names = {str(m["label"] or "").strip().lower() for m in members}
        areas = [(m["bbox"][2] - m["bbox"][0]) * (m["bbox"][3] - m["bbox"][1])
                 for m in members if m.get("bbox")]
        if len(names) < 2 or (areas and max(areas) > CHECK_AREA):
            continue
        out.append({"check_id": f"k{len(out) + 1}", "label": found["label"],
                    "confidence": found["confidence"],
                    "members": [{"image_id": m["image_id"], "local_id": m["local_id"],
                                 "label": m["label"], "bbox": m.get("bbox")} for m in members]})
    return out


def draw_checks(checks: list[dict], sources: dict, out_dir: pathlib.Path) -> int:
    """One row per automatic match: each member cropped with its surroundings, its box drawn.

    A box alone says nothing about whether it is the right thing; the neighbours do (the vase
    beside the black jug, not the one standing in the water). The crop is three times the box,
    so what is around it is in the picture.
    """
    try:
        from PIL import Image, ImageDraw, ImageOps
    except ImportError:
        return 0
    cache: dict = {}
    sheets = 0
    for start in range(0, len(checks), CHECK_PER_SHEET):
        rows = checks[start:start + CHECK_PER_SHEET]
        width = max(len(c["members"]) for c in rows) * (CHECK_PANEL + 6)
        sheet = Image.new("RGB", (width, len(rows) * (CHECK_PANEL + 20)), (20, 20, 20))
        draw = ImageDraw.Draw(sheet)
        for row, check in enumerate(rows):
            y = row * (CHECK_PANEL + 20)
            names = "  |  ".join(f"{m['local_id']} '{m['label']}'" for m in check["members"])
            draw.text((4, y + 3), f"{check['check_id']}:  {names}", fill="#ffffff")
            for column, member in enumerate(check["members"]):
                source = sources.get(member["image_id"])
                if source is None or not member.get("bbox"):
                    continue
                if source not in cache:
                    with Image.open(source) as opened:
                        cache[source] = ImageOps.exif_transpose(opened).convert("RGB")
                picture = cache[source]
                x0, y0, x1, y1 = (member["bbox"][0] * picture.width, member["bbox"][1] * picture.height,
                                  member["bbox"][2] * picture.width, member["bbox"][3] * picture.height)
                side = max(x1 - x0, y1 - y0) * 3
                side = min(max(side, 240), min(picture.size))
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                left = min(max(cx - side / 2, 0), picture.width - side)
                top = min(max(cy - side / 2, 0), picture.height - side)
                crop = picture.crop((round(left), round(top), round(left + side), round(top + side)))
                crop = crop.resize((CHECK_PANEL, CHECK_PANEL))
                k = CHECK_PANEL / side
                ImageDraw.Draw(crop).rectangle([(x0 - left) * k, (y0 - top) * k,
                                                (x1 - left) * k, (y1 - top) * k],
                                               outline=["#ff2d55", "#00b8ff", "#ffd400", "#2bd96b"][column % 4],
                                               width=2)
                sheet.paste(crop, (column * (CHECK_PANEL + 6), y + 18))
        path = out_dir / f"k{start // CHECK_PER_SHEET + 1}.jpg"
        out_dir.mkdir(parents=True, exist_ok=True)
        sheet.save(path, quality=88)
        for check in rows:
            check["sheet"] = path.resolve().as_posix()
        sheets += 1
    return sheets


def draw_context(batch: dict, groups: dict, sources: dict, out_dir: pathlib.Path) -> dict:
    """Each photograph whole, with every candidate in this batch boxed and numbered.

    A cropped sheet shows a thing in isolation. Matching is easier when you can see what is
    around it: which bottle is the one beside the kettle, which mat is under the tray. So an
    agent also gets each photograph in full, and the number on a box is the last digits of the
    id in its table. Colours separate the groups.
    """
    try:
        from PIL import Image, ImageDraw, ImageOps
    except ImportError:
        return {}
    colours = ["#ff2d55", "#00b8ff", "#ffd400", "#2bd96b", "#c77dff", "#ff8c00"]
    per_image: dict[str, list[tuple[int, dict]]] = {}
    for index, group_id in enumerate(batch["groups"]):
        for image_id, members in groups[group_id]["members"].items():
            per_image.setdefault(image_id, []).extend((index, m) for m in members)
    written = {}
    for image_id, members in sorted(per_image.items()):
        source = sources.get(image_id)
        if source is None:
            continue
        with Image.open(source) as opened:
            picture = ImageOps.exif_transpose(opened).convert("RGB")
        scale = SHEET_WIDTH / max(picture.size)
        if scale < 1.0:
            picture = picture.resize((round(picture.width * scale), round(picture.height * scale)))
        draw = ImageDraw.Draw(picture)
        for index, member in members:
            if not member.get("bbox"):
                continue
            x0, y0, x1, y1 = member["bbox"]
            rect = [x0 * picture.width, y0 * picture.height, x1 * picture.width, y1 * picture.height]
            colour = colours[index % len(colours)]
            draw.rectangle(rect, outline=colour, width=2)
            draw.text((rect[0] + 2, max(0, rect[1] - 11)), member["local_id"].split("-")[-1], fill=colour)
        path = out_dir / f"{batch['batch_id']}.{image_id}.jpg"
        out_dir.mkdir(parents=True, exist_ok=True)
        picture.save(path, quality=88)
        written[image_id] = path.resolve().as_posix()
    return written


def batch_groups(groups: list[dict], max_batches: int) -> list[dict]:
    total = sum(len(m) for g in groups for m in g["members"].values())
    count = max(1, min(max_batches, math.ceil(total / BATCH_TARGET))) if groups else 0
    batches = [{"batch_id": f"m{i + 1}", "groups": [], "size": 0} for i in range(count)]
    for group in sorted(groups, key=lambda g: -sum(len(m) for m in g["members"].values())):
        target = min(batches, key=lambda b: b["size"])
        target["groups"].append(group["group_id"])
        target["size"] += sum(len(m) for m in group["members"].values())
    return [b for b in batches if b["groups"]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--structures", required=True, help="folder of structure files")
    parser.add_argument("--detections", required=True, help="folder of merged detections files")
    parser.add_argument("--registration", help="registration.json; without it every pair is tried")
    parser.add_argument("--manifest", help="manifest.json, for the contact sheets")
    parser.add_argument("--root", action="append", default=[],
                        help="a folder the manifest's image paths may be under; repeat the flag")
    parser.add_argument("--sheets", help="write a contact sheet per group into this folder")
    parser.add_argument("--context", help="write each batch's whole photographs, with its candidates "
                                          "boxed, into this folder")
    parser.add_argument("--checks", help="write a picture of each weak automatic match into this folder")
    parser.add_argument("--max-batches", type=int, default=4, help="agents to spread the groups over")
    parser.add_argument("--out", required=True, help="where to write auto.json")
    parser.add_argument("--force", action="store_true", help="overwrite an existing --out")
    args = parser.parse_args(argv)

    for label, value in (("--structures", args.structures), ("--detections", args.detections)):
        if not pathlib.Path(value).is_dir():
            print(f"error: no such folder: {value} ({label})", file=sys.stderr)
            return 2
    registration = None
    if args.registration:
        try:
            registration = load(pathlib.Path(args.registration))
        except (OSError, ValueError) as exc:
            print(f"error: could not read {args.registration}: {exc}", file=sys.stderr)
            return 2
    try:
        nodes = read_nodes(pathlib.Path(args.structures), pathlib.Path(args.detections))
    except (OSError, ValueError) as exc:
        print(f"error: could not read the structures or detections: {exc}", file=sys.stderr)
        return 2
    if not nodes:
        print("error: no detections were found", file=sys.stderr)
        return 2
    out = pathlib.Path(args.out)
    if out.exists() and not args.force:
        print(f"error: {out.as_posix()} exists; pass --force to overwrite", file=sys.stderr)
        return 1

    images = sorted({n["image_id"] for n in nodes.values()})
    globals_ = Globals()
    groups: list[dict] = []
    auto = 0
    where_is = regions(registration)
    for image_a, image_b, relation in overlapping(registration, images):
        closer, region = where_is.get((image_a, image_b), (None, None))
        auto += run_pair(image_a, image_b, relation, nodes, globals_, groups, region, closer)

    # A node can sit in a residue group for one pair and be matched through another.
    groups = [g for g in groups
              if sum(len([m for m in ms if m["local_id"] not in globals_.of])
                     for ms in g["members"].values()) > 0]
    for index, group in enumerate(groups, start=1):
        group["group_id"] = f"G{index}"
        for image_id in group["members"]:
            group["members"][image_id] = [m for m in group["members"][image_id]
                                          if m["local_id"] not in globals_.of]

    sources: dict[str, pathlib.Path] = {}
    if args.manifest:
        manifest_path = pathlib.Path(args.manifest)
        here = manifest_path.resolve().parent
        roots = [pathlib.Path(r) for r in args.root] + [pathlib.Path.cwd(), here] + list(here.parents)[:4]
        try:
            for row in load(manifest_path).get("images") or []:
                found = find_image(str(row.get("path") or ""), roots)
                if found:
                    sources[row["image_id"]] = found
        except (OSError, ValueError) as exc:
            print(f"warning: could not read the manifest for sheets: {exc}", file=sys.stderr)
    sheets_written = 0
    if args.sheets:
        for group in groups:
            path = pathlib.Path(args.sheets) / f"{group['group_id']}.jpg"
            if draw_sheet(group, sources, path):
                group["sheet"] = path.resolve().as_posix()
                sheets_written += 1

    batches = batch_groups(groups, args.max_batches)
    checks = checks_for(globals_.done(), nodes)
    if checks and args.checks:
        draw_checks(checks, sources, pathlib.Path(args.checks))
    if checks:
        if not batches:
            batches = [{"batch_id": "m1", "groups": [], "size": 0}]
        by_sheet: dict[str, list[dict]] = {}
        for check in checks:
            by_sheet.setdefault(check.get("sheet") or check["check_id"], []).append(check)
        for batch in batches:
            batch["checks"] = []
        for sheet_checks in by_sheet.values():
            min(batches, key=lambda b: len(b["checks"]))["checks"] += [c["check_id"] for c in sheet_checks]
    if args.context:
        by_id = {g["group_id"]: g for g in groups}
        for batch in batches:
            batch["context"] = draw_context(batch, by_id, sources, pathlib.Path(args.context))
    keep = ("local_id", "label", "description", "category", "size_m", "id_confidence", "parent")
    label_of = {n["local_id"]: n["label"] for n in nodes.values()}
    for group in groups:
        group["members"] = {i: [dict({k: m.get(k) for k in keep},
                                     parent_label=label_of.get(m.get("parent")))
                                for m in ms]
                            for i, ms in group["members"].items()}
    result = {
        "schema": "scene-decompose/match-auto@1",
        "images": images,
        "matched": globals_.done(),
        "groups": groups,
        "batches": batches,
        "checks": checks,
        "stats": {"nodes": len(nodes), "matched_objects": len(globals_.done()),
                  "automatic_matches": auto, "groups": len(groups), "checks": len(checks),
                  "objects_for_agents": sum(len(m) for g in groups for m in g["members"].values()),
                  "sheets": sheets_written,
                  "context_images": sum(len(b.get("context") or {}) for b in batches)},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": out.as_posix(), **result["stats"],
                      "batches": [{"batch_id": b["batch_id"], "groups": b["groups"], "size": b["size"]}
                                  for b in batches]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
