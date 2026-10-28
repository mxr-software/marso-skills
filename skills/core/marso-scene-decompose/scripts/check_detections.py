#!/usr/bin/env python3
"""Check a detections file: the half of the gate a script can do.

It reads the numbers and the required fields. It cannot see the image, so it
says nothing about whether a box contains what it claims or whether anything is
missing. Those are step 6's job.

Prints a JSON report to stdout. Exit codes: 0 clean, 1 problems found,
2 the file could not be read.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

REQUIRED = ("local_id", "label", "description", "category", "bbox", "size_m",
            "size_confidence", "size_basis", "pass")
CONFIDENCES = {"high", "medium", "low"}
PASSES = {"overview", "surface-recheck", "tile"}
EDGES = {"left", "right", "top", "bottom"}
# Floors, walls and ceilings are boxed at their full extent, so they overlap everything.
ANCHOR_CATEGORY = "architecture"
# Below this, a box is almost certainly a stray click rather than an object.
TINY = 1e-6

# Words for a thing whose whole job is holding another thing. A description that names
# one is naming an object: a kitchen roll was once recorded as "a roll on an upright
# metal holder", and the holder — a separate thing a 3D pipeline has to build — was
# never detected at all.
# "rail" and "plinth" are deliberately not here: a chair's curved back rail and a base
# unit's plinth are parts of those objects, not things that hold other things.
FIXTURES = ("holder", "stand", "rack", "hook", "bracket", "mount", "hanger",
            "dispenser", "caddy", "pedestal", "easel", "tripod")
# Only where the word is the object of a preposition: "on an upright metal holder" is a
# fixture, "the camera stands against the wall" is a verb, and a run full of upright
# objects uses that verb constantly.
PREPOSITIONS = "on|in|from|over|onto|into|against|atop|beneath|under|off"
ARTICLES = "a|an|the|its|his|her|their|one|two|some|this|that"


def check_bbox(bbox) -> list[str]:
    if not isinstance(bbox, list) or len(bbox) != 4:
        return ["bbox must be a list of four numbers"]
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in bbox):
        return ["bbox values must be numbers"]
    problems = []
    x0, y0, x1, y1 = bbox
    if any(v < 0 or v > 1 for v in bbox):
        problems.append(
            "bbox is outside 0-1; these look like pixel coordinates, which are wrong at "
            "every scale because the image is shown downscaled"
        )
    if x0 >= x1 or y0 >= y1:
        problems.append("bbox must have x0 < x1 and y0 < y1")
    elif (x1 - x0) * (y1 - y0) < TINY:
        problems.append("bbox has almost no area")
    return problems


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


def check(data: dict, duplicate_iou: float) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    objects = data.get("objects")
    if not isinstance(objects, list):
        return ["the file must have an 'objects' list"], warnings
    if not objects:
        return ["'objects' is empty; an image with nothing in it is not a result"], warnings

    seen_ids: set[str] = set()
    boxes: list[tuple[str, list]] = []

    for index, obj in enumerate(objects):
        where = f"objects[{index}]"
        if not isinstance(obj, dict):
            errors.append(f"{where}: must be an object")
            continue
        for field in REQUIRED:
            if field not in obj:
                errors.append(f"{where}: missing '{field}'")

        local_id = obj.get("local_id")
        if isinstance(local_id, str):
            if local_id in seen_ids:
                errors.append(f"{where}: local_id '{local_id}' is used more than once")
            seen_ids.add(local_id)

        for problem in check_bbox(obj.get("bbox")):
            errors.append(f"{where}: {problem}")
        if isinstance(obj.get("bbox"), list) and len(obj["bbox"]) == 4:
            boxes.append((str(local_id), obj["bbox"], obj.get("category")))

        confidence = obj.get("size_confidence")
        if confidence is not None and confidence not in CONFIDENCES:
            errors.append(f"{where}: size_confidence must be one of {sorted(CONFIDENCES)}")

        id_confidence = obj.get("id_confidence")
        if id_confidence is not None and id_confidence not in CONFIDENCES:
            errors.append(f"{where}: id_confidence must be one of {sorted(CONFIDENCES)}")

        stage_pass = obj.get("pass")
        if stage_pass is not None and stage_pass not in PASSES:
            errors.append(f"{where}: pass must be one of {sorted(PASSES)}")

        basis = obj.get("size_basis")
        if isinstance(basis, str) and not basis.strip():
            errors.append(f"{where}: size_basis is empty; an unexplained number can't be checked")

        size = obj.get("size_m")
        if isinstance(size, (int, float)) and not isinstance(size, bool) and size <= 0:
            errors.append(f"{where}: size_m must be greater than 0")

        truncated = obj.get("truncated", [])
        if not isinstance(truncated, list) or set(truncated) - EDGES:
            errors.append(f"{where}: truncated must be a list drawn from {sorted(EDGES)}")

        label = obj.get("label")
        if isinstance(label, str) and "logo" in label.lower():
            warnings.append(
                f"{where}: '{label}' looks like a marking printed on another object, "
                "not an object in its own right"
            )

    labels = " ".join(str(o.get("label", "")) for o in objects).lower()
    for obj in objects:
        described = str(obj.get("description", "")).lower()
        own_label = str(obj.get("label", "")).lower()
        # A fixture describes itself. An object labelled "wire holder" will say "caddy",
        # "rack" or "stand" in its own description, and none of those is a missing object.
        if any(re.search(r"\b" + w + r"s?\b", own_label) for w in FIXTURES):
            continue
        # The holder may be recorded under one of its other names. A run described a roll
        # "on its stand" and was told no stand existed, when the object right underneath
        # it was labelled "kitchen roll holder". If something overlapping this object is
        # labelled as a fixture, the fixture is there.
        if any(any(re.search(r"\b" + other + r"s?\b", str(o.get("label", "")).lower())
                   for other in FIXTURES)
               and iou(obj.get("bbox"), o.get("bbox")) > 0.02
               for o in objects if o is not obj):
            continue
        for word in FIXTURES:
            noun = r"\b" + word + r"s?\b"
            if re.search(noun, labels):
                continue
            phrase = (r"\b(?:" + PREPOSITIONS + r")\s+(?:(?:" + ARTICLES + r")\s+)?"
                      r"(?:[\w-]+\s+){0,3}" + word + r"s?\b")
            if re.search(phrase, described):
                warnings.append(
                    f"{obj.get('local_id', '?')}: the description says it is on or in a "
                    f"'{word}' but nothing in this file is one; the thing an object sits "
                    f"on or hangs from is an object of its own"
                )

    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            # Anchors are boxed at their full extent, not their visible part, so a floor
            # and the table standing on it overlap almost completely by design.
            if ANCHOR_CATEGORY in (boxes[i][2], boxes[j][2]):
                continue
            overlap = iou(boxes[i][1], boxes[j][1])
            if overlap >= duplicate_iou:
                warnings.append(
                    f"{boxes[i][0]} and {boxes[j][0]} overlap by {overlap:.2f}; "
                    "check they aren't the same object found twice"
                )

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", help="the detections JSON file to check")
    parser.add_argument("--iou", type=float, default=0.85,
                        help="warn when two boxes overlap by at least this (default 0.85)")
    parser.add_argument("--strict", action="store_true", help="fail on warnings as well as errors")
    args = parser.parse_args(argv)

    path = pathlib.Path(args.path)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"error: no such file: {path.as_posix()}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: {path.as_posix()} is not valid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("error: the file must hold a JSON object", file=sys.stderr)
        return 2

    errors, warnings = check(data, args.iou)
    report = {
        "path": path.as_posix(),
        "objects": len(data.get("objects") or []),
        "errors": errors,
        "warnings": warnings,
        "checked": "numbers and required fields only; a script cannot see the image",
    }
    print(json.dumps(report, indent=2))
    for line in errors:
        print(f"error: {line}", file=sys.stderr)
    for line in warnings:
        print(f"warning: {line}", file=sys.stderr)

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
