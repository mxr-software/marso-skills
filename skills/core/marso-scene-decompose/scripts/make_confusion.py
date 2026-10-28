#!/usr/bin/env python3
"""Collect everything the run was not sure of into confusion.json.

An emit agent used to write this by hand. Every field in it is already in the graph, the
matches or the view scores, so a script does it: the sets the match stage refused to merge,
what a better view contradicted, the merges made on weak evidence, the supports nobody saw,
the objects whose parent disagreed between views, and the objects whose best view is a close
call. Nothing here resolves anything. Nothing in it was removed from the graph.

Exit codes: 0 written, 2 an input could not be read.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build(graph: dict, matches: dict, scores: dict | None) -> dict:
    global_of: dict[str, str] = {}
    for obj in matches.get("objects") or []:
        for member in obj.get("members") or []:
            global_of[member.get("local_id")] = obj.get("global_id")
    group_of_issue = {g.get("from"): g.get("group_id") for g in graph.get("identity_groups") or []}

    unresolved = []
    for issue in matches.get("unresolved") or []:
        entry = dict(issue)
        entry["global_ids"] = sorted({global_of[c["local_id"]] for c in issue.get("candidates") or []
                                      if c.get("local_id") in global_of})
        if group_of_issue.get(issue.get("issue_id")):
            entry["identity_group"] = group_of_issue[issue["issue_id"]]
        unresolved.append(entry)

    corrections = []
    for c in matches.get("corrections") or []:
        entry = dict(c)
        entry["global_ids"] = sorted({global_of[r["local_id"]] for r in (c.get("target"), c.get("better_view"))
                                      if isinstance(r, dict) and r.get("local_id") in global_of})
        entry["owner_stage"] = entry.pop("stage", None)
        corrections.append(entry)

    low = [{"global_id": o["global_id"], "label": o.get("label"), "members": o.get("members"),
            "confidence": o.get("confidence"), "evidence": o.get("evidence")}
           for o in matches.get("objects") or []
           if len(o.get("members") or []) > 1 and o.get("confidence") == "low"]

    inferred = [{"global_id": n["global_id"], "label": n.get("label"), "parent": n.get("parent"),
                 "relation": n.get("relation"), "parent_source": n.get("parent_source")}
                for n in graph.get("nodes") or [] if n.get("support_inferred")]

    close = []
    for entry in (scores or {}).get("objects") or []:
        if entry.get("decisive") is False:
            close.append({"global_id": entry["global_id"], "label": entry.get("label"),
                          "best_view": entry.get("best_view"),
                          "views": [{"image_id": v.get("image_id"), "score": v.get("score"),
                                     "share_of_best": v.get("share_of_best")}
                                    for v in (entry.get("views") or [])[:2]]})

    counts = {"unresolved": len(unresolved), "corrections": len(corrections),
              "low_confidence_merges": len(low), "inferred_supports": len(inferred),
              "parent_conflicts": len(graph.get("parent_conflicts") or []),
              "identity_groups": len(graph.get("identity_groups") or []),
              "close_view_choices": len(close)}
    return {
        "schema": "scene-decompose/confusion@1",
        "note": ("Everything the run was not sure of. It resolves nothing: nothing here was "
                 "removed from the graph. Every entry carries the global_ids it touches."),
        "unresolved": unresolved, "corrections": corrections, "low_confidence_merges": low,
        "inferred_supports": inferred, "parent_conflicts": graph.get("parent_conflicts") or [],
        "identity_groups": graph.get("identity_groups") or [], "close_view_choices": close,
        "notes": [], "counts": counts,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--graph", required=True, help="scene_graph.json")
    parser.add_argument("--matches", required=True, help="matches.json")
    parser.add_argument("--scores", help="view_scores.json, for the close calls")
    parser.add_argument("--out", required=True, help="where to write confusion.json")
    parser.add_argument("--force", action="store_true", help="overwrite an existing --out")
    args = parser.parse_args(argv)

    try:
        graph = load(pathlib.Path(args.graph))
        matches = load(pathlib.Path(args.matches))
        scores = load(pathlib.Path(args.scores)) if args.scores else None
    except FileNotFoundError as exc:
        print(f"error: no such file: {exc.filename}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"error: could not read an input: {exc}", file=sys.stderr)
        return 2
    out = pathlib.Path(args.out)
    if out.exists() and not args.force:
        print(f"error: {out.as_posix()} exists; pass --force to overwrite", file=sys.stderr)
        return 1
    result = build(graph, matches, scores)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": out.as_posix(), **result["counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
