#!/usr/bin/env python3
"""Check a structure file: the half of the gate a script can do.

It checks that the hierarchy is a tree, that every edge uses a real relation, and
that nothing from the detections file was lost or invented. It cannot see the
image, so it says nothing about whether a parent really holds its child.

Prints a JSON report to stdout. Exit codes: 0 clean, 1 problems found,
2 a file could not be read.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

RELATIONS = {"on-top-of", "inside", "hanging-on", "leaning-against", "under",
             "attached-to", "part-of", "unknown"}
CLUSTER_KINDS = {"instances", "variants"}
# An area named for where it is in the picture rather than what happens there.
# Matched on whole words only: "centrepiece" and "middle shelf" are real names for
# real places, and an earlier substring match flagged "table centrepiece".
PLACE_IN_PICTURE = ("left side", "right side", "top left", "top right", "bottom left",
                    "bottom right", "background", "foreground", "cluttered")


def walk_to_root(start: str, parents: dict) -> tuple[list[str], str | None]:
    """Follow parents up from `start`. Returns the path, and the id a cycle closes on."""
    path: list[str] = []
    seen: set[str] = set()
    node = start
    while node is not None:
        if node in seen:
            return path, node
        seen.add(node)
        path.append(node)
        node = parents.get(node)
    return path, None


def check(data: dict, detection_ids: set[str] | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    nodes = data.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return ["the file must have a non-empty 'nodes' list"], warnings

    parents: dict[str, str | None] = {}
    ids: list[str] = []
    for index, node in enumerate(nodes):
        where = f"nodes[{index}]"
        if not isinstance(node, dict):
            errors.append(f"{where}: must be an object")
            continue
        local_id = node.get("local_id")
        if not isinstance(local_id, str) or not local_id:
            errors.append(f"{where}: missing 'local_id'")
            continue
        if local_id in parents:
            errors.append(f"{where}: '{local_id}' appears more than once")
            continue
        ids.append(local_id)

        if "parent" not in node:
            errors.append(f"{where}: missing 'parent' (use null for an anchor)")
            continue
        parent = node["parent"]
        relation = node.get("relation")

        if parent is None:
            if relation is not None:
                errors.append(f"{local_id}: an anchor has no parent, so relation must be null")
        else:
            if not isinstance(parent, str):
                errors.append(f"{local_id}: parent must be a local_id or null")
            elif parent == local_id:
                errors.append(f"{local_id}: is its own parent")
            if relation not in RELATIONS:
                errors.append(
                    f"{local_id}: relation '{relation}' is not in the vocabulary "
                    f"{sorted(RELATIONS)}"
                )
            if relation == "unknown" and not str(node.get("note") or "").strip():
                errors.append(f"{local_id}: relation 'unknown' needs a note saying why")
        if node.get("support_inferred") and not str(node.get("note") or "").strip():
            errors.append(f"{local_id}: support_inferred needs a note saying what it was based on")

        for touch in node.get("also_touches") or []:
            if not isinstance(touch, dict):
                errors.append(f"{local_id}: also_touches entries must be objects")
                continue
            if touch.get("local_id") == parent:
                warnings.append(
                    f"{local_id}: also_touches repeats its parent '{parent}'; the parent edge "
                    "already records that contact"
                )
            if touch.get("relation") not in RELATIONS:
                errors.append(
                    f"{local_id}: also_touches relation '{touch.get('relation')}' is not in "
                    "the vocabulary"
                )
        parents[local_id] = parent

    known = set(parents)
    for local_id, parent in parents.items():
        if parent is not None and parent not in known:
            errors.append(f"{local_id}: parent '{parent}' is not a node in this file")

    # Tree checks, once the edges are known to point at real nodes.
    roots = [i for i, p in parents.items() if p is None]
    if not roots:
        errors.append("no anchors: at least one node must have a null parent")
    for local_id in parents:
        path, cycle = walk_to_root(local_id, parents)
        if cycle:
            errors.append(f"cycle through '{cycle}': {' -> '.join(path)}")
        elif path and parents.get(path[-1]) is None and path[-1] not in roots:
            errors.append(f"{local_id}: does not reach an anchor")

    declared = data.get("anchors")
    if declared is not None:
        if sorted(declared) != sorted(roots):
            errors.append(
                f"'anchors' says {sorted(declared)} but the nodes with no parent are {sorted(roots)}"
            )

    if detection_ids is not None:
        missing = detection_ids - known
        invented = known - detection_ids
        for local_id in sorted(missing):
            errors.append(f"'{local_id}' is in the detections file but has no node here")
        for local_id in sorted(invented):
            errors.append(f"'{local_id}' is not in the detections file; nothing may be invented")

    if len(roots) == len(known):
        errors.append("every node is an anchor: the cascade was not done")
    elif known and len(roots) < len(known):
        flat = [i for i, p in parents.items() if p in roots]
        if len(flat) == len(known) - len(roots) and len(known) > 4:
            warnings.append(
                "every object hangs straight off an anchor; surfaces and the things on them "
                "should cascade"
            )

    for index, cluster in enumerate(data.get("clusters") or []):
        where = f"clusters[{index}]"
        if not isinstance(cluster, dict):
            errors.append(f"{where}: must be an object")
            continue
        members = cluster.get("members")
        if not isinstance(members, list) or len(members) < 2:
            errors.append(f"{where}: a cluster needs two or more members")
        else:
            for member in members:
                if member not in known:
                    errors.append(f"{where}: member '{member}' is not a node")
            if len(set(members)) != len(members):
                errors.append(f"{where}: the same member is listed twice")
        if cluster.get("kind") not in CLUSTER_KINDS:
            errors.append(f"{where}: kind must be one of {sorted(CLUSTER_KINDS)}")
        if not str(cluster.get("label") or "").strip():
            errors.append(f"{where}: needs a label")

    for index, area in enumerate(data.get("areas") or []):
        where = f"areas[{index}]"
        if not isinstance(area, dict):
            errors.append(f"{where}: must be an object")
            continue
        members = area.get("members")
        if not isinstance(members, list) or len(members) < 2:
            errors.append(f"{where}: an area needs two or more members")
        else:
            for member in members:
                if member not in known:
                    errors.append(f"{where}: member '{member}' is not a node")
        label = str(area.get("label") or "").strip()
        if not label:
            errors.append(f"{where}: needs a label")
        elif any(re.search(rf"\b{re.escape(phrase)}\b", label.lower())
                 for phrase in PLACE_IN_PICTURE):
            warnings.append(
                f"{where}: '{label}' names where it is in the picture, not what happens there"
            )

    return errors, warnings


def depth(parents: dict) -> int:
    best = 0
    for local_id in parents:
        path, cycle = walk_to_root(local_id, parents)
        if not cycle:
            best = max(best, len(path))
    return best


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", help="the structure JSON file to check")
    parser.add_argument("--detections", help="the detections file it was built from")
    parser.add_argument("--strict", action="store_true", help="fail on warnings as well as errors")
    args = parser.parse_args(argv)

    path = pathlib.Path(args.path)
    try:
        data = load(path)
    except FileNotFoundError:
        print(f"error: no such file: {path.as_posix()}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: {path.as_posix()} is not valid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("error: the file must hold a JSON object", file=sys.stderr)
        return 2

    detection_ids = None
    if args.detections:
        dpath = pathlib.Path(args.detections)
        try:
            detections = load(dpath)
        except FileNotFoundError:
            print(f"error: no such file: {dpath.as_posix()}", file=sys.stderr)
            return 2
        except json.JSONDecodeError as exc:
            print(f"error: {dpath.as_posix()} is not valid JSON: {exc}", file=sys.stderr)
            return 2
        objects = detections.get("objects")
        if not isinstance(objects, list):
            print(f"error: {dpath.as_posix()} has no 'objects' list", file=sys.stderr)
            return 2
        detection_ids = {o.get("local_id") for o in objects if isinstance(o, dict)}

    errors, warnings = check(data, detection_ids)

    nodes = [n for n in data.get("nodes") or [] if isinstance(n, dict) and n.get("local_id")]
    parents = {n["local_id"]: n.get("parent") for n in nodes}
    report = {
        "path": path.as_posix(),
        "nodes": len(nodes),
        "anchors": sorted(i for i, p in parents.items() if p is None),
        "depth": depth(parents) if not any("cycle" in e for e in errors) else None,
        "clusters": len(data.get("clusters") or []),
        "areas": len(data.get("areas") or []),
        "support_inferred": sum(1 for n in nodes if n.get("support_inferred")),
        "errors": errors,
        "warnings": warnings,
        "checked": "the shape of the tree only; a script cannot see the image",
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
