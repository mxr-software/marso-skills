#!/usr/bin/env python3
"""Check a registration file: the half of the gate a script can do.

It checks the bookkeeping — every pair present once, every verdict from the
vocabulary, close-ups pointing at a region of the wider image, the establishing
view named or the run flagged as having none. It cannot see the photographs, so
it says nothing about whether a verdict is true.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import sys

RELATIONS = {"same-viewpoint", "different-viewpoint", "close-up", "partial-overlap",
             "no-overlap"}
CONFIDENCES = {"high", "medium", "low"}
# Anything shorter than this is a verdict with no reason behind it.
MIN_EVIDENCE = 20


def check_box(box) -> list[str]:
    if not isinstance(box, list) or len(box) != 4:
        return ["region must be [x0, y0, x1, y1]"]
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in box):
        return ["region must be four numbers"]
    x0, y0, x1, y1 = box
    out = []
    if not all(0.0 <= v <= 1.0 for v in box):
        out.append("region must be normalised to 0-1, not pixels")
    if x0 >= x1 or y0 >= y1:
        out.append("region must have x0 < x1 and y0 < y1")
    return out


def check(data: dict, manifest_ids: list[str] | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    images = data.get("images")
    if not isinstance(images, list) or not images:
        return ["the file must have an 'images' list"], warnings
    images = [str(i) for i in images]
    if len(images) != len(set(images)):
        errors.append("'images' lists the same id more than once")

    if manifest_ids is not None:
        missing = sorted(set(manifest_ids) - set(images))
        extra = sorted(set(images) - set(manifest_ids))
        if missing:
            errors.append(f"the manifest has images this file never registers: {missing}")
        if extra:
            errors.append(f"this file registers images the manifest does not list: {extra}")

    pairs = data.get("pairs")
    if not isinstance(pairs, list):
        return errors + ["the file must have a 'pairs' list"], warnings

    seen: dict[tuple[str, str], int] = {}
    for index, pair in enumerate(pairs):
        where = f"pair {index + 1}"
        if not isinstance(pair, dict):
            errors.append(f"{where}: must be an object")
            continue
        a, b = pair.get("a"), pair.get("b")
        where = f"pair {a}+{b}"
        if a not in images or b not in images:
            errors.append(f"{where}: names an image that is not in 'images'")
            continue
        if a == b:
            errors.append(f"{where}: an image cannot be paired with itself")
            continue
        if a > b:
            errors.append(f"{where}: put the pair in order, '{b}' before '{a}', "
                          "so each pair appears exactly once")
        key = (a, b) if a < b else (b, a)
        if key in seen:
            errors.append(f"{where}: this pair already has a verdict in pair {seen[key] + 1}")
            continue
        seen[key] = index

        relation = pair.get("relation")
        if relation not in RELATIONS:
            errors.append(f"{where}: relation must be one of {sorted(RELATIONS)}")
        if pair.get("confidence") not in CONFIDENCES:
            errors.append(f"{where}: confidence must be one of {sorted(CONFIDENCES)}")

        evidence = pair.get("evidence")
        if not isinstance(evidence, str) or len(evidence.strip()) < MIN_EVIDENCE:
            errors.append(f"{where}: evidence must say what you actually saw; "
                          "a verdict with no reason cannot be checked or argued with")

        if relation == "close-up":
            closer = pair.get("closer")
            if closer not in (a, b):
                errors.append(f"{where}: closer must be '{a}' or '{b}': which one is "
                              "the close shot decides which image the region is in")
            if pair.get("region_confidence") not in (None,) and                     pair.get("region_confidence") not in CONFIDENCES:
                errors.append(f"{where}: region_confidence must be one of {sorted(CONFIDENCES)}")
            region = pair.get("region")
            if region is None:
                errors.append(f"{where}: a close-up needs a region: without it the next "
                              "stage cannot tell which part of the wider image it covers")
            else:
                errors.extend(f"{where}: {m}" for m in check_box(region))
        else:
            if pair.get("region_confidence") is not None:
                warnings.append(f"{where}: region_confidence only means something on a close-up")
            if pair.get("region") is not None:
                warnings.append(f"{where}: a region only means something on a close-up")
            if pair.get("closer") is not None:
                warnings.append(f"{where}: 'closer' only means something on a close-up")

    expected = {tuple(sorted(p)) for p in itertools.combinations(sorted(set(images)), 2)}
    absent = sorted(expected - set(seen))
    if absent:
        errors.append(
            f"{len(absent)} pair(s) have no verdict: {['+'.join(p) for p in absent[:6]]}"
            + (" ..." if len(absent) > 6 else "")
            + ". A pair that shares nothing still gets a 'no-overlap' verdict"
        )

    establishing = data.get("establishing_view")
    no_overview = data.get("no_overview")
    if establishing is None:
        if no_overview is not True:
            errors.append("no establishing view: set 'no_overview' to true to say so "
                          "deliberately, rather than leaving the field empty")
    else:
        if establishing not in images:
            errors.append(f"establishing_view '{establishing}' is not one of the images")
        if no_overview:
            errors.append("no_overview is true but an establishing view is named")

    # The widest view should not be the close shot in any pair.
    if establishing is not None:
        for pair in pairs:
            if not isinstance(pair, dict) or pair.get("relation") != "close-up":
                continue
            if pair.get("closer") == establishing:
                warnings.append(
                    f"the establishing view '{establishing}' is the close-up in pair "
                    f"{pair.get('a')}+{pair.get('b')}; the widest view should not be a "
                    "close-up of anything"
                )

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="registration.json")
    parser.add_argument("--manifest", help="manifest.json, to check every image is covered")
    parser.add_argument("--strict", action="store_true", help="fail on warnings as well")
    args = parser.parse_args(argv)

    path = pathlib.Path(args.path)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"error: no such file: {args.path}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"error: could not read {args.path}: {exc}", file=sys.stderr)
        return 2

    manifest_ids = None
    if args.manifest:
        try:
            man = json.loads(pathlib.Path(args.manifest).read_text(encoding="utf-8-sig"))
            manifest_ids = [str(i.get("image_id")) for i in man.get("images", [])]
        except (OSError, ValueError) as exc:
            print(f"error: could not read {args.manifest}: {exc}", file=sys.stderr)
            return 2

    errors, warnings = check(data, manifest_ids)
    report = {
        "path": str(path).replace("\\", "/"),
        "images": len(data.get("images") or []),
        "pairs": len(data.get("pairs") or []),
        "establishing_view": data.get("establishing_view"),
        "errors": errors,
        "warnings": warnings,
        "checked": "the bookkeeping only; a script cannot see the photographs",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    for line in errors:
        print(f"error: {line}", file=sys.stderr)
    for line in warnings:
        print(f"warning: {line}", file=sys.stderr)
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
