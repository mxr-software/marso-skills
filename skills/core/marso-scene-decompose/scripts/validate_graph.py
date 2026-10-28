#!/usr/bin/env python3
"""Validate the finished scene graph.

Checks the things a script can: the hierarchy is a tree, every reference
resolves, every box is in range, every view names an image in the manifest, and
the ontology's counts reconcile with the nodes. It cannot see the photographs,
so it says nothing about whether the graph is true.

Prints a JSON report to stdout. Exit codes: 0 clean, 1 problems found,
2 a file could not be read.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

RELATIONS = {"on-top-of", "inside", "hanging-on", "leaning-against", "under",
             "attached-to", "part-of", "unknown"}


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def walk_to_root(start: str, parents: dict) -> tuple[list[str], str | None]:
    path, seen, node = [], set(), start
    while node is not None:
        if node in seen:
            return path, node
        seen.add(node)
        path.append(node)
        node = parents.get(node)
    return path, None


def check(graph: dict, manifest: dict | None, ontology: dict | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    nodes = graph.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return ["the graph must have a non-empty 'nodes' list"], warnings

    known_images = None
    if manifest is not None:
        known_images = {row.get("image_id") for row in manifest.get("images") or []}

    parents: dict[str, str | None] = {}
    for index, node in enumerate(nodes):
        where = f"nodes[{index}]"
        if not isinstance(node, dict):
            errors.append(f"{where}: must be an object")
            continue
        global_id = node.get("global_id")
        if not isinstance(global_id, str) or not global_id:
            errors.append(f"{where}: missing 'global_id'")
            continue
        if global_id in parents:
            errors.append(f"{where}: '{global_id}' appears more than once")
            continue
        if not str(node.get("label") or "").strip():
            errors.append(f"{global_id}: needs a label")

        parent, relation = node.get("parent"), node.get("relation")
        if parent is None:
            if relation is not None:
                errors.append(f"{global_id}: an anchor has no parent, so relation must be null")
        elif relation not in RELATIONS:
            errors.append(f"{global_id}: relation '{relation}' is not in the vocabulary")
        parents[global_id] = parent

        views = node.get("views")
        if not isinstance(views, list) or not views:
            errors.append(f"{global_id}: needs at least one view")
            continue
        seen_images = set()
        for view in views:
            if not isinstance(view, dict):
                errors.append(f"{global_id}: views must be objects")
                continue
            image_id = view.get("image_id")
            if image_id in seen_images:
                errors.append(
                    f"{global_id}: has two views in image '{image_id}'; one physical thing is "
                    "in a photograph once"
                )
            seen_images.add(image_id)
            if known_images is not None and image_id not in known_images:
                errors.append(f"{global_id}: view names image '{image_id}', not in the manifest")
            bbox = view.get("bbox")
            if not isinstance(bbox, list) or len(bbox) != 4:
                errors.append(f"{global_id}: a view's bbox must be four numbers")
            elif any(not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0 or v > 1
                     for v in bbox):
                errors.append(f"{global_id}: a view's bbox is outside 0-1")
            elif bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                errors.append(f"{global_id}: a view's bbox must have x0 < x1 and y0 < y1")
        if node.get("seen_in") is not None and node["seen_in"] != len(views):
            errors.append(f"{global_id}: seen_in says {node['seen_in']} but it has {len(views)} views")

    known = set(parents)
    for global_id, parent in parents.items():
        if parent is not None and parent not in known:
            errors.append(f"{global_id}: parent '{parent}' is not a node")

    roots = [i for i, p in parents.items() if p is None]
    if not roots:
        errors.append("no anchors: at least one node must have a null parent")
    for global_id in parents:
        _, cycle = walk_to_root(global_id, parents)
        if cycle:
            errors.append(f"cycle through '{cycle}'")
            break

    for key, id_key in (("clusters", "cl_id"), ("areas", "ar_id")):
        for index, group in enumerate(graph.get(key) or []):
            where = f"{key}[{index}]"
            if not isinstance(group, dict):
                errors.append(f"{where}: must be an object")
                continue
            members = group.get("members")
            if not isinstance(members, list) or len(members) < 2:
                errors.append(f"{where}: needs two or more members")
                continue
            for member in members:
                if member not in known:
                    errors.append(f"{where}: member '{member}' is not a node")
            if key == "clusters" and group.get("kind") not in {"instances", "variants"}:
                errors.append(f"{where}: kind must be 'instances' or 'variants'")

    # Identity groups: several global objects that stand for fewer physical things.
    redundancy: dict[str, int] = {}          # global_id -> group it belongs to
    group_slack: dict[str, int] = {}         # group_id -> how many ids are spare
    for index, group in enumerate(graph.get("identity_groups") or []):
        where = f"identity_groups[{index}]"
        if not isinstance(group, dict):
            errors.append(f"{where}: must be an object")
            continue
        group_id = group.get("group_id") or where
        members = group.get("members")
        if not isinstance(members, list) or len(members) < 2:
            errors.append(f"{where}: needs two or more members")
            continue
        for member in members:
            if member not in known:
                errors.append(f"{where}: member '{member}' is not a node")
            elif member in redundancy:
                errors.append(
                    f"{where}: '{member}' is already in group '{redundancy[member]}'; an object "
                    "belongs to at most one identity group"
                )
            else:
                redundancy[member] = group_id
        distinct = group.get("distinct")
        if not isinstance(distinct, int) or isinstance(distinct, bool):
            errors.append(f"{where}: 'distinct' must be a whole number")
        elif not 1 <= distinct <= len(members):
            errors.append(
                f"{where}: distinct is {distinct}, which is not between 1 and the "
                f"{len(members)} members"
            )
        else:
            group_slack[group_id] = len(members) - distinct
        if not str(group.get("basis") or "").strip():
            errors.append(f"{where}: needs a 'basis' saying how 'distinct' was arrived at")

    if ontology is not None:
        counted = 0
        placed: dict[str, str] = {}
        for index, row in enumerate(ontology.get("categories") or []):
            where = f"categories[{index}]"
            members = row.get("members")
            if not isinstance(members, list) or not members:
                errors.append(f"{where}: needs members")
                continue
            # An identity group's members stand for fewer physical things, so a category
            # holding them counts fewer than it lists. A group must sit in one category.
            slack = 0
            for group_id, spare in group_slack.items():
                in_here = [m for m in members if redundancy.get(m) == group_id]
                if not in_here:
                    continue
                total_in_group = sum(1 for m, g in redundancy.items() if g == group_id)
                if len(in_here) != total_in_group:
                    errors.append(
                        f"{where}: identity group '{group_id}' is split across categories; "
                        "objects that may be the same thing belong in one category"
                    )
                    continue
                slack += spare
            expected = len(members) - slack
            if row.get("count") is not None and row["count"] != expected:
                errors.append(
                    f"{where}: count says {row['count']} but it lists {len(members)} members"
                    + (f", of which {slack} may be another member seen again, so it should be "
                       f"{expected}" if slack else "")
                )
            counted += len(members)
            for member in members:
                if member not in known:
                    errors.append(f"{where}: member '{member}' is not a node")
                elif member in placed:
                    errors.append(
                        f"{where}: '{member}' is also in '{placed[member]}'; every object sits "
                        "in exactly one category"
                    )
                else:
                    placed[member] = row.get("label") or where
        missing = known - set(placed)
        for global_id in sorted(missing):
            errors.append(f"'{global_id}' is in the graph but in no ontology category")
        total_slack = sum(group_slack.values())
        if counted and counted != len(known):
            warnings.append(
                f"the ontology lists {counted} objects and the graph has {len(known)}"
            )
        declared_total = ontology.get("total_objects")
        expected_total = len(known) - total_slack
        if declared_total is not None and declared_total != expected_total:
            errors.append(
                f"total_objects says {declared_total}, but the graph holds {len(known)} objects "
                f"of which {total_slack} may be another seen again, so it should be "
                f"{expected_total}"
            )

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("graph", help="scene_graph.json")
    parser.add_argument("--manifest", help="manifest.json, to check the view image ids")
    parser.add_argument("--ontology", help="ontology.json, to reconcile the counts")
    parser.add_argument("--strict", action="store_true", help="fail on warnings as well as errors")
    args = parser.parse_args(argv)

    paths = {"graph": args.graph, "manifest": args.manifest, "ontology": args.ontology}
    loaded = {}
    for name, raw in paths.items():
        if raw is None:
            loaded[name] = None
            continue
        path = pathlib.Path(raw)
        try:
            loaded[name] = load(path)
        except FileNotFoundError:
            print(f"error: no such file: {path.as_posix()}", file=sys.stderr)
            return 2
        except json.JSONDecodeError as exc:
            print(f"error: {path.as_posix()} is not valid JSON: {exc}", file=sys.stderr)
            return 2

    graph = loaded["graph"]
    if not isinstance(graph, dict):
        print("error: the graph must hold a JSON object", file=sys.stderr)
        return 2

    errors, warnings = check(graph, loaded["manifest"], loaded["ontology"])
    nodes = [n for n in graph.get("nodes") or [] if isinstance(n, dict)]
    groups = [g for g in graph.get("identity_groups") or [] if isinstance(g, dict)]
    slack = sum(max(0, len(g.get("members") or []) - (g.get("distinct") or 0)) for g in groups)
    report = {
        "graph": args.graph,
        "nodes": len(nodes),
        "anchors": [n.get("global_id") for n in nodes if n.get("parent") is None],
        "seen_in_more_than_one_image": sum(1 for n in nodes if (n.get("seen_in") or 1) > 1),
        "clusters": len(graph.get("clusters") or []),
        "areas": len(graph.get("areas") or []),
        "identity_groups": len(groups),
        "distinct_objects": len(nodes) - slack,
        "errors": errors,
        "warnings": warnings,
        "checked": "references, ranges and counts; a script cannot see the photographs",
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
