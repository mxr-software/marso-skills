#!/usr/bin/env python3
"""Rank the views of every object in the scene graph, best first.

The score is how much of the frame the object fills, cut down by what spoils the
view: being hidden behind something, running off the edge, or the view's own
admission that it could not tell what the thing was. It is the same ranking the
match stage uses to decide which view to believe, so the two always agree.

    score = frame_share
            x (0.6 if partly hidden, 0.3 if heavily hidden, else 1)
            x (1 - 0.15 per truncated edge)
            x (1.0 high / 0.85 medium / 0.6 low id_confidence)

Scores are comparable between views of one object, not between objects: a spoon
seen perfectly still fills less of the frame than a badly seen table.

Prints the ranking as JSON. Exit codes: 0 scored, 1 nothing to score,
2 the file could not be read.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

OCCLUDED_FACTOR = 0.6
TRUNCATED_PER_EDGE = 0.15
ID_FACTOR = {"high": 1.0, "medium": 0.85, "low": 0.6}


def frame_share(bbox) -> float:
    if not isinstance(bbox, list) or len(bbox) != 4:
        return 0.0
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def score_view(view: dict) -> tuple[float, list[str]]:
    """The score, and why it is not simply the frame share."""
    share = frame_share(view.get("bbox"))
    score = share
    why = []
    if view.get("occlusion") == "heavy":
        score *= OCCLUDED_FACTOR / 2
        why.append("mostly hidden")
    elif view.get("occluded"):
        score *= OCCLUDED_FACTOR
        why.append("partly hidden")
    edges = view.get("truncated") or []
    if edges:
        score *= max(0.0, 1 - TRUNCATED_PER_EDGE * len(edges))
        why.append(f"runs off the {', '.join(edges)}")
    id_confidence = view.get("id_confidence", "high")
    factor = ID_FACTOR.get(id_confidence, 1.0)
    if factor < 1.0:
        score *= factor
        why.append(f"the view was {id_confidence}ly sure what it was")
    return score, why


def rank(graph: dict) -> list[dict]:
    out = []
    for node in graph.get("nodes") or []:
        views = node.get("views") or []
        scored = []
        for view in views:
            score, why = score_view(view)
            scored.append({
                "image_id": view.get("image_id"),
                "local_id": view.get("local_id"),
                "frame_share": round(frame_share(view.get("bbox")), 6),
                "score": round(score, 6),
                "penalties": why,
            })
        scored.sort(key=lambda v: v["score"], reverse=True)
        total = sum(v["score"] for v in scored)
        for view in scored:
            view["share_of_best"] = round(view["score"] / scored[0]["score"], 4) if scored and scored[0]["score"] else 0.0
        out.append({
            "global_id": node.get("global_id"),
            "label": node.get("label"),
            "best_view": scored[0]["image_id"] if scored else None,
            "best_local_id": scored[0]["local_id"] if scored else None,
            "decisive": bool(scored and (len(scored) == 1 or scored[1]["score"] < scored[0]["score"] * 0.8)),
            "views": scored,
            "total": round(total, 6),
        })
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("graph", help="scene_graph.json")
    parser.add_argument("--out", help="write the ranking here as well as to stdout")
    parser.add_argument("--force", action="store_true", help="overwrite an existing --out file")
    args = parser.parse_args(argv)

    path = pathlib.Path(args.graph)
    try:
        graph = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"error: no such file: {path.as_posix()}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: {path.as_posix()} is not valid JSON: {exc}", file=sys.stderr)
        return 2

    ranking = rank(graph)
    if not ranking:
        print("error: the graph has no nodes to score", file=sys.stderr)
        return 1

    result = {
        "schema": "scene-decompose/view-scores@1",
        "formula": "frame_share x occlusion x truncation x id_confidence",
        "objects": ranking,
    }
    if args.out:
        out = pathlib.Path(args.out)
        if out.exists() and not args.force:
            print(f"error: {out.as_posix()} exists; pass --force to overwrite", file=sys.stderr)
            return 1
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
