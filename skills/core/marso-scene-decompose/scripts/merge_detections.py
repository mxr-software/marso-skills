#!/usr/bin/env python3
"""Merge detection files from a tile sweep, dropping the duplicates the overlap creates.

Two boxes overlapping by at least --iou are taken to be the same object. The
one kept is the one with more to say about it: a longer description, then a
higher size confidence, then the earlier pass. Nothing is thrown away silently
— every drop is listed in the report.

Prints the merged file to stdout. Exit codes: 0 merged, 1 nothing to merge,
2 a file could not be read.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}
PASS_RANK = {"overview": 3, "surface-recheck": 2, "tile": 1}


def iou(a, b) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix0 >= ix1 or iy0 >= iy1:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    union = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
    return inter / union if union else 0.0


STOPWORDS = {"a", "an", "the", "of", "with", "and", "on", "in", "small", "large", "dark",
             "light", "clear", "glass", "plastic", "metal", "black", "white", "grey",
             "gray", "silver", "gold", "golden", "capped", "lidded", "tall", "short"}


def nouns(label) -> set:
    """The words in a label that say what the thing IS, not what it looks like."""
    return {w for w in re.findall(r"[a-z]+", str(label or "").lower())
            if len(w) > 2 and w not in STOPWORDS} or set()


def head(label) -> str:
    """The word that says what a thing is: the last real word. 'dining chair' is a chair."""
    found = [w for w in re.findall(r"[a-z]+", str(label or "").lower())
             if len(w) > 2 and w not in STOPWORDS]
    return found[-1] if found else ""


LIKENESS = 0.6
# Two agents' boxes this close, for the same kind of thing, are one thing. Not lower: four red
# onions heaped in a bowl overlap each other by about 0.43, and 0.4 merged one of them away. The
# true duplicates measured on a real run (a dish rack seen by two tiles) sat at 0.53 and above.
KIND_IOU = 0.5
# The same list check_detections.py uses, and tests/test_scene_decompose_detect.py keeps
# the two in step. A thing whose whole job is holding another thing shares most of its
# name with what it holds and sits almost exactly behind it: "paper towel roll" and
# "paper towel holder" overlapped by 0.63 and the holder was deleted as a duplicate,
# undoing the rule the stage repeats most.
FIXTURES = ("holder", "stand", "rack", "hook", "bracket", "mount", "hanger",
            "dispenser", "caddy", "pedestal", "easel", "tripod")


def is_fixture(label) -> bool:
    return bool(nouns(label) & set(FIXTURES))


def alike(a: dict, b: dict) -> bool:
    """Do these two entries name the same thing, not just the same kind of thing?

    Sharing the kind-noun is not enough: "yellow-capped oil bottle" and "spirit bottle"
    are two bottles, and that pair is exactly what used to be deleted. What matters is
    whether the *shorter* label is substantially contained in the longer one, so
    "camera" and "compact camera" are one object while those two bottles are not.
    """
    if is_fixture(a.get("label")) != is_fixture(b.get("label")):
        return False          # a holder and the thing it holds are never one object
    one, two = nouns(a.get("label")), nouns(b.get("label"))
    if not one or not two:
        return False          # nothing to go on: treat as unlike, which keeps both
    return len(one & two) / min(len(one), len(two)) >= LIKENESS


def richness(obj: dict) -> tuple:
    """How much this entry tells us; higher wins when two entries are the same object."""
    return (
        len(str(obj.get("description") or "")),
        CONFIDENCE_RANK.get(obj.get("size_confidence"), 0),
        PASS_RANK.get(obj.get("pass"), 0),
        len(str(obj.get("label") or "")),
    )


def _overlaps(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _contained(inner, outer) -> float:
    ix0, iy0 = max(inner[0], outer[0]), max(inner[1], outer[1])
    ix1, iy1 = min(inner[2], outer[2]), min(inner[3], outer[3])
    if ix0 >= ix1 or iy0 >= iy1:
        return 0.0
    area = (inner[2] - inner[0]) * (inner[3] - inner[1])
    return (ix1 - ix0) * (iy1 - iy0) / area if area else 0.0


def _facts(obj: dict):
    """What a comparison needs, worked out once per object rather than once per pair."""
    bbox = obj.get("bbox")
    if not (isinstance(bbox, list) and len(bbox) == 4):
        return None
    label = obj.get("label")
    return {"bbox": bbox, "head": head(label), "fixture": is_fixture(label), "nouns": nouns(label),
            "source": obj.get("_source")}


def judge(a: dict, b: dict, overlap: float, threshold: float, unlike: float,
          kind_iou: float = KIND_IOU) -> str | None:
    """Are these two entries one object? The reason if so, else None.

    Boxes alone cannot tell "found twice" from "one thing in front of another", so what
    decides is who wrote them and what they are called.

    - **Two entries from the same agent are never duplicates.** An agent that lists a vase and
      the water in it, a holder and its roll, or two shakers side by side did so on purpose.
      In a whole-photograph run every overlapping pair is one agent's own list, and the old
      rule dropped "vase water" as a duplicate of "glass vase".
    - A holder is never the thing it holds, however closely the boxes coincide.
    - Across agents, the same kind of thing (the same last word) with boxes overlapping by
      `kind_iou` is one thing: "dish rack" from two tiles, "cooker hood" and "range hood".
    - Names that share their words need `threshold`; names that disagree entirely need
      `unlike`, because a rice bran oil bottle in front of a rum bottle overlapped by 0.66 and
      was once deleted. Over-counting is recoverable; a wrong deletion is invisible.
    """
    if a["source"] is not None and a["source"] == b["source"]:
        return None
    if a["fixture"] != b["fixture"]:
        return None
    one, two = a["nouns"], b["nouns"]
    names_agree = bool(one and two and len(one & two) / min(len(one), len(two)) >= LIKENESS)
    if a["head"] and a["head"] == b["head"]:
        # The same kind of thing. Identical qualifiers ("dish rack" twice) need little overlap;
        # different ones ("rum bottle", "olive oil bottle") need more, because two bottles in a
        # row overlap.
        if names_agree:
            need, why = kind_iou, "the same thing, recorded twice"
        else:
            need, why = threshold, "the same kind of thing under different qualifiers, recorded twice"
    elif names_agree:
        need, why = threshold, "named alike, recorded twice"
    else:
        need, why = unlike, ("boxes almost identical though named differently; check it is not "
                             "one object in front of another")
    return why if overlap >= need else None


def merge(objects: list[dict], threshold: float,
          unlike: float, kind_iou: float = KIND_IOU) -> tuple[list[dict], list[dict]]:
    # Richest first, so the entry we keep is already the one we want.
    ordered = sorted(objects, key=richness, reverse=True)
    kept: list[dict] = []
    facts: list[dict | None] = []
    dropped: list[dict] = []
    for obj in ordered:
        mine = _facts(obj)
        if mine is None:
            kept.append(obj)
            facts.append(None)
            continue
        found = None
        for other, theirs in zip(kept, facts):
            # Boxes that do not touch cannot be one object; this skips almost every pair
            # before any name is looked at.
            if theirs is None or not _overlaps(mine["bbox"], theirs["bbox"]):
                continue
            overlap = iou(mine["bbox"], theirs["bbox"])
            reason = judge(mine, theirs, overlap, threshold, unlike, kind_iou)
            # The best-overlapping one, not the first over the line: in a row of bottles an
            # entry overlaps its neighbour as well as itself.
            if reason and (found is None or overlap > found[1]):
                found = (other, overlap, reason)
        if found:
            other, overlap, reason = found
            dropped.append({"dropped": obj.get("local_id"), "kept": other.get("local_id"),
                            "iou": round(overlap, 4), "reason": reason,
                            "labels": [obj.get("label"), other.get("label")]})
        else:
            kept.append(obj)
            facts.append(mine)
    # Back into reading order, so the output is stable and easy to scan.
    kept.sort(key=lambda o: (o.get("bbox") or [0, 0])[1::-1] if o.get("bbox") else [0, 0])
    return kept, dropped


def possible_duplicates(objects: list[dict]) -> list[dict]:
    """Pairs from different agents that look like one thing but were not merged.

    Reported, never merged: the same object under two different names ("control box" and
    "game controller") cannot be told from a thing standing in front of another by boxes alone,
    and a wrong deletion is the one error nothing downstream can see. A person can.
    """
    facts = [_facts(o) for o in objects]
    out = []
    for i, a in enumerate(objects):
        fa = facts[i]
        if fa is None:
            continue
        for j in range(i + 1, len(objects)):
            fb = facts[j]
            if fb is None or not _overlaps(fa["bbox"], fb["bbox"]):
                continue
            if fa["source"] is not None and fa["source"] == fb["source"]:
                continue
            if fa["fixture"] != fb["fixture"]:
                continue
            overlap = iou(fa["bbox"], fb["bbox"])
            inside = max(_contained(fa["bbox"], fb["bbox"]), _contained(fb["bbox"], fa["bbox"]))
            if overlap >= KIND_IOU and inside >= 0.9:
                b = objects[j]
                out.append({"labels": [a.get("label"), b.get("label")], "iou": round(overlap, 2),
                            "ids": [a.get("local_id"), b.get("local_id")]})
    return out


def build_structure(image_id, objects: list[dict], conflicts: list[dict]) -> tuple[dict, list[str]]:
    """Lift the support tree out of the detections, where the region agents put it.

    Nobody decides anything here. The surfaces pass recorded what each surface rests on
    and each region agent recorded what its finds rest on, because the agent that worked
    out which surface an object was standing on is the one that knew. This gathers those
    answers, checks they make a tree, and writes the file stage 4 reads.
    """
    known = {o["local_id"] for o in objects if o.get("local_id")}
    problems: list[str] = []
    nodes = []
    for obj in objects:
        parent = obj.get("parent") or None
        if parent and parent not in known:
            problems.append(f"{obj['local_id']}: parent '{parent}' is not in this image; "
                            "treated as an anchor")
            parent = None
        node = {"local_id": obj["local_id"], "label": obj.get("label"), "parent": parent}
        if parent:
            node["relation"] = obj.get("relation") or "on-top-of"
            if obj.get("relation") is None:
                problems.append(f"{obj['local_id']}: no relation given, so 'on-top-of' "
                                "was assumed; say which it is")
        if obj.get("support_inferred"):
            node["support_inferred"] = True
        if obj.get("also_touches"):
            node["also_touches"] = obj["also_touches"]
        nodes.append(node)

    # A cycle makes the tree checks downstream meaningless, so find it here and break it.
    parent_of = {n["local_id"]: n["parent"] for n in nodes}
    for node in nodes:
        seen, walk = set(), node["local_id"]
        while walk:
            if walk in seen:
                problems.append(f"{node['local_id']}: its parent chain loops; "
                                "made it an anchor to keep the tree a tree")
                node["parent"] = None
                node.pop("relation", None)
                break
            seen.add(walk)
            walk = parent_of.get(walk)

    anchors = sorted(n["local_id"] for n in nodes if not n["parent"])
    if not anchors:
        problems.append("no object is an anchor; the surfaces pass should give the floor "
                        "and the walls a parent of null")
    return ({"schema": "scene-decompose/structure@1", "image_id": image_id,
             "anchors": anchors, "nodes": nodes,
             "parent_conflicts": conflicts,
             "built_by": "merge_detections.py, from the parents the region passes recorded",
             "clusters": [], "areas": []}, problems)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+", help="detection JSON files to merge")
    parser.add_argument("--iou", type=float, default=0.6,
                        help="treat boxes overlapping by at least this as the same object, "
                             "when both passes named it the same kind of thing (default 0.6)")
    parser.add_argument("--iou-unlike", type=float, default=0.75,
                        help="the threshold when the two names disagree. One object standing "
                             "in front of another overlaps a lot and is not a duplicate "
                             "(default 0.75)")
    parser.add_argument("--structure",
                        help="also write the support tree here, lifted from the parents the "
                             "surfaces and region passes recorded")
    parser.add_argument("--out", help="write the merged file here as well as to stdout")
    parser.add_argument("--renumber", action="store_true",
                        help="give the kept objects fresh local ids, <image_id>-001 up. Region passes number from their own region, so without this the merged file has gaps and repeats")
    parser.add_argument("--force", action="store_true", help="overwrite an existing --out file")
    args = parser.parse_args(argv)

    if not 0 < args.iou <= 1:
        print("error: --iou must be above 0 and at most 1", file=sys.stderr)
        return 2

    objects: list[dict] = []
    sources_seen: list[str] = []
    image_id = None
    for raw in args.paths:
        path = pathlib.Path(raw)
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError:
            print(f"error: no such file: {path.as_posix()}", file=sys.stderr)
            return 2
        except json.JSONDecodeError as exc:
            print(f"error: {path.as_posix()} is not valid JSON: {exc}", file=sys.stderr)
            return 2
        if not isinstance(data, dict) or not isinstance(data.get("objects"), list):
            print(f"error: {path.as_posix()} has no 'objects' list", file=sys.stderr)
            return 2
        image_id = image_id or data.get("image_id")
        # One file is one agent's list. Its entries are never taken for duplicates of each other.
        for entry in data["objects"]:
            if isinstance(entry, dict):
                entry["_source"] = f"file{len(sources_seen)}"
                objects.append(entry)
        sources_seen.append(raw)

    if not objects:
        print("error: the files given held no objects", file=sys.stderr)
        return 1

    kept, dropped = merge(objects, args.iou, args.iou_unlike)
    for entry in kept:
        entry.pop("_source", None)
    conflicts: list[dict] = []
    if args.renumber:
        # Every id a dropped entry carried has to keep working, because another object's
        # parent may point at it: a region agent put the shakers on the caddy, and the
        # caddy was the copy that got dropped.
        now: dict[str, str] = {}
        for index, obj in enumerate(kept, start=1):
            fresh = f"{image_id or 'img'}-{index:03d}"
            if obj.get("local_id"):
                now[obj["local_id"]] = fresh
            obj["local_id"] = fresh
        for entry in dropped:
            entry["kept_as"] = now.get(entry.get("kept"), entry.get("kept"))
            if entry.get("dropped"):
                now[entry["dropped"]] = entry["kept_as"]

        # Rewrite every id that points at another object. Leaving these stale is how a
        # previous run ended up with parents that resolved to a completely different
        # object after renumbering — a pile of pans hanging off a splashback.
        for obj in kept:
            if obj.get("parent"):
                obj["parent"] = now.get(obj["parent"], obj["parent"])
            if obj.get("sits_on"):
                obj["sits_on"] = now.get(obj["sits_on"], obj["sits_on"])
            for touch in obj.get("also_touches") or []:
                if isinstance(touch, dict) and touch.get("local_id"):
                    touch["local_id"] = now.get(touch["local_id"], touch["local_id"])

        # Where two regions both found one object and disagreed about what it rests on,
        # say so rather than silently keeping whichever was richer.
        by_new: dict[str, dict] = {o["local_id"]: o for o in kept}
        original = {o.get("local_id"): o for o in objects if isinstance(o, dict)}
        for entry in dropped:
            lost = original.get(entry.get("dropped")) or {}
            winner = by_new.get(entry.get("kept_as")) or {}
            theirs, ours = lost.get("parent"), winner.get("parent")
            if theirs and ours and now.get(theirs, theirs) != ours:
                conflicts.append({
                    "object": entry.get("kept_as"),
                    "kept_parent": ours,
                    "other_parent": now.get(theirs, theirs),
                    "note": "two regions found this object and placed it differently; "
                            "the closer look wins, but stage 4 should know",
                })

    merged = {
        "schema": "scene-decompose/detections@1",
        "image_id": image_id,
        "objects": kept,
        "merge": {"inputs": len(objects), "kept": len(kept),
                  "renumbered": bool(args.renumber), "dropped": dropped,
                  "parent_conflicts": conflicts},
    }

    if args.out:
        out = pathlib.Path(args.out)
        if out.exists() and not args.force:
            print(f"error: {out.as_posix()} exists; pass --force to overwrite", file=sys.stderr)
            return 1
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")

    if args.structure:
        tree, problems = build_structure(image_id, kept, conflicts)
        merged["structure"] = {"nodes": len(tree["nodes"]),
                               "anchors": tree["anchors"], "problems": problems}
        structure_out = pathlib.Path(args.structure)
        if structure_out.exists() and not args.force:
            print(f"error: {structure_out.as_posix()} exists; pass --force to overwrite",
                  file=sys.stderr)
            return 1
        structure_out.parent.mkdir(parents=True, exist_ok=True)
        structure_out.write_text(json.dumps(tree, indent=2) + "\n", encoding="utf-8")
        for line in problems:
            print(f"warning: {line}", file=sys.stderr)

    print(json.dumps(merged, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
