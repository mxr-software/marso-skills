#!/usr/bin/env python3
"""Derive the unique-asset plan from a scene-decompose/scene-graph@1 file.

Usage:
    plan_assets.py <scene_graph.json> [--scores view_scores.json] --out asset_plan.json [--force]

Writes marso/asset-plan@1 to --out and prints a JSON summary. Standard library only.

Exit codes: 0 plan written, 1 something was wrong with the inputs or the output
location, 2 the graph (or scores file) could not be read as JSON.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

SCHEMA_IN = "scene-decompose/scene-graph@1"
SCHEMA_OUT = "marso/asset-plan@1"

# Same penalties as the decompose stage's view ranking, so the two agree when no
# scores file is supplied.
OCCLUDED_FACTOR = 0.6
TRUNCATED_PER_EDGE = 0.15
ID_FACTOR = {"high": 1.0, "medium": 0.8, "low": 0.5}

ARCHITECTURE_WORDS = (
    "wall", "floor", "ceiling", "ground", "door", "window", "skirting", "cornice",
    "fitted", "built-in", "builtin", "worktop", "counter", "cabinet run",
    "kitchen units", "radiator", "stair", "architecture", "room shell", "fireplace",
)
STRUCTURED_WORDS = (
    "furniture", "seating", "chair", "stool", "bench", "sofa", "table", "desk",
    "storage", "shelf", "shelving", "cabinet", "cupboard", "wardrobe", "drawer",
    "bed", "lighting", "lamp", "appliance", "oven", "fridge", "microwave",
    "electronics", "television", "monitor", "fixture", "sink", "tap",
)
ORGANIC_WORDS = (
    "food", "fruit", "vegetable", "plant", "flower", "textile", "fabric", "cushion",
    "pillow", "blanket", "throw", "ceramic", "vessel", "bowl", "vase", "ornament",
    "decor", "toy", "tool", "bag", "organic", "sculpture", "natural", "rug",
)


def read_json(path: pathlib.Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"error: no such file: {path.as_posix()}", file=sys.stderr)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"error: {path.as_posix()} is not valid JSON: {exc}", file=sys.stderr)
    except OSError as exc:
        print(f"error: cannot read {path.as_posix()}: {exc}", file=sys.stderr)
    return None


def frame_share(bbox) -> float:
    if not bbox or len(bbox) != 4:
        return 0.0
    x0, y0, x1, y1 = bbox
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def view_score(view: dict) -> float:
    score = frame_share(view.get("bbox"))
    if view.get("occlusion") == "heavy":
        score *= OCCLUDED_FACTOR / 2
    elif view.get("occluded"):
        score *= OCCLUDED_FACTOR
    edges = view.get("truncated") or []
    if edges:
        score *= max(0.0, 1 - TRUNCATED_PER_EDGE * len(edges))
    score *= ID_FACTOR.get(view.get("id_confidence", "high"), 1.0)
    return score


def best_view(node: dict, scores: dict | None) -> dict | None:
    views = node.get("views") or []
    if not views:
        return None
    chosen = None
    if scores:
        entry = scores.get(node.get("global_id"))
        if entry:
            for view in views:
                if view.get("image_id") == entry.get("best_view") and (
                    entry.get("best_local_id") in (None, view.get("local_id"))
                ):
                    chosen = view
                    break
    if chosen is None:
        chosen = max(views, key=view_score)
    return {
        "image_id": chosen.get("image_id"),
        "local_id": chosen.get("local_id"),
        "bbox": chosen.get("bbox"),
        "occluded": bool(chosen.get("occluded")),
        "occlusion": chosen.get("occlusion") or ("partial" if chosen.get("occluded") else "none"),
        "truncated": chosen.get("truncated") or [],
        "id_confidence": chosen.get("id_confidence", "high"),
    }


def longest_side(size_m) -> float:
    # The decompose graph stores size_m as one number, the largest dimension.
    if isinstance(size_m, (int, float)) and not isinstance(size_m, bool):
        return float(size_m)
    if isinstance(size_m, dict):
        values = [v for v in size_m.values() if isinstance(v, (int, float))]
    elif isinstance(size_m, (list, tuple)):
        values = [v for v in size_m if isinstance(v, (int, float))]
    else:
        values = []
    return max(values) if values else 0.0


def words(node: dict) -> str:
    return " ".join(str(node.get(k) or "") for k in ("label", "category")).lower()


def matches(text: str, vocabulary) -> bool:
    """Whole words only, plurals allowed: 'table' must not catch 'tableware', nor 'oven'
    'woven', which sent mugs and placemats to modelling."""
    return any(re.search(rf"\b{re.escape(word)}(s|es)?\b", text) for word in vocabulary)


def cluster_key(cluster: dict):
    return cluster.get("cluster_id") or cluster.get("cl_id")


def route_for(node: dict, count: int) -> tuple[str, str]:
    text = words(node)
    side = longest_side(node.get("size_m"))
    if node.get("parent") is None:
        return "model", "anchor: built as the room shell, not generated"
    if matches(text, ARCHITECTURE_WORDS):
        return "model", "architecture or built-in run: planar, dimensioned and tied to the room"
    if node.get("relation") == "part-of":
        return "skip", "part of its parent: made with the parent, not separately"
    structured = matches(text, STRUCTURED_WORDS) or side > 1.2
    if count > 1 and structured:
        return "model", f"repeated structured object: model once, instance {count}"
    if matches(text, ORGANIC_WORDS) or (side and side <= 0.6):
        return "generate", "organic, complex or small prop: generation is the starting point"
    if structured:
        return "model", "structured object larger than a hand-held prop: agent modelling is the default"
    return "generate", "fallback: no rule matched, review this route"


def build_plan(graph: dict, scores_doc: dict | None) -> dict:
    nodes = {n["global_id"]: n for n in graph.get("nodes") or [] if n.get("global_id")}
    scores = None
    if scores_doc:
        scores = {o.get("global_id"): o for o in scores_doc.get("objects") or []}

    children: dict[str, list[str]] = {gid: [] for gid in nodes}
    for gid, node in nodes.items():
        parent = node.get("parent")
        if parent in children:
            children[parent].append(gid)

    conflicted = set()
    for conflict in graph.get("parent_conflicts") or []:
        gid = conflict.get("global_id")
        if gid:
            conflicted.add(gid)

    groups = {g.get("group_id"): g for g in graph.get("identity_groups") or [] if g.get("group_id")}
    group_of: dict[str, list[str]] = {}
    for group_id, group in groups.items():
        for member in group.get("members") or []:
            group_of.setdefault(member, []).append(group_id)

    # Objects a close-up should have confirmed and did not are probably a wide view's
    # misreading of something already in the graph: they are reviewed, never made.
    unconfirmed = sorted(gid for gid, n in nodes.items() if n.get("unconfirmed")
                         and n.get("parent") is not None)
    skip = set(unconfirmed)

    # Which nodes become which asset. An instances cluster and an identity group that share a
    # member are one asset: four onions in a bowl in one photograph and one onion in another,
    # which may be one of the four, are 4 to 5 onions, not 4 + 1. Anchors are never assets.
    owner = {gid: gid for gid in nodes}

    def find(gid):
        while owner[gid] != gid:
            owner[gid] = owner[owner[gid]]
            gid = owner[gid]
        return gid

    def usable(members):
        return [m for m in members or [] if m in nodes and m not in skip
                and nodes[m].get("parent") is not None]

    cluster_of: dict[str, str] = {}
    for cluster in graph.get("clusters") or []:
        members = usable(cluster.get("members"))
        for member in members:
            cluster_of.setdefault(member, cluster_key(cluster))
        if cluster.get("kind") == "instances":
            for member in members[1:]:
                owner[find(member)] = find(members[0])
    for group in groups.values():
        members = usable(group.get("members"))
        for member in members[1:]:
            owner[find(member)] = find(members[0])
    components: dict[str, list[str]] = {}
    for gid in nodes:
        if gid in skip or nodes[gid].get("parent") is None:
            continue
        components.setdefault(find(gid), []).append(gid)
    asset_members: list[tuple[list[str], str | None]] = []
    for members in components.values():
        members = sorted(members)
        clusters_here = {cluster_of[m] for m in members if m in cluster_of}
        asset_members.append((members, sorted(clusters_here)[0] if clusters_here else None))

    asset_members.sort(key=lambda item: item[0][0])

    assets = []
    for index, (members, cluster_id) in enumerate(asset_members, start=1):
        member_set = set(members)
        # The member that shows the asset best stands for it: least hidden first, so a chair
        # half behind the table borrows its clearly seen twin's crop; then a confident name;
        # then most views; then the best single view.
        hidden = {"none": 0, "partial": 1, "heavy": 2}
        rep = min((nodes[gid] for gid in members),
                  key=lambda n: (hidden.get(n.get("occlusion"), 1 if any(
                                     v.get("occluded") for v in n.get("views") or []) else 0),
                                 all(v.get("id_confidence") == "low" for v in n.get("views") or []),
                                 -len(n.get("views") or []),
                                 -max((view_score(v) for v in n.get("views") or []), default=0),
                                 n["global_id"]))
        at_most = len(members)
        at_least = at_most
        count = at_most
        flags: list[str] = []
        touched_groups = sorted({g for m in members for g in group_of.get(m, [])})
        for group_id in touched_groups:
            group = groups[group_id]
            g_members = set(group.get("members") or []) - skip
            if g_members <= member_set:
                g_most = min(int(group.get("at_most", len(g_members))), len(g_members))
                g_least = min(int(group.get("at_least", len(g_members))), g_most)
                at_least -= max(0, g_most - g_least)
                distinct = group.get("distinct")
                count -= max(0, len(g_members) - int(distinct if distinct is not None else g_least))
            else:
                flags.append("identity-group-split")
        at_least = max(1, at_least)
        count = max(at_least, min(count, at_most))

        route, reason = route_for(rep, count)
        view = best_view(rep, scores)
        if view is None:
            flags.append("no-view")
        else:
            if view["id_confidence"] == "low":
                flags.append("low-id-confidence")
            if view["occluded"] or view["truncated"]:
                flags.append("occluded-best-view")
        if rep.get("occlusion") == "heavy":
            flags.append("mostly-hidden")
            if not rep.get("inferred_whole"):
                flags.append("no-inferred-whole")
        if rep.get("size_confidence") in (None, "low"):
            flags.append("low-size-confidence")
        if any(group_of.get(m) for m in members) and any(
                set(groups[g].get("members") or []) & skip for m in members for g in group_of.get(m, [])):
            flags.append("identity-group-has-unconfirmed")
        if member_set & conflicted:
            flags.append("parent-conflict")
        if reason.startswith("fallback"):
            flags.append("fallback-route")

        kids = sorted({c for m in members for c in children.get(m, [])})
        images = sorted({v.get("image_id") for m in members for v in nodes[m].get("views") or []
                         if v.get("image_id")})
        asset = {
            "asset_id": f"a{index:03d}",
            "global_id": rep["global_id"],
            "label": rep.get("label"),
            "description": rep.get("description"),
            "category": rep.get("category"),
            "route": route,
            "route_reason": reason,
            "count": count,
            "count_at_least": at_least,
            "count_at_most": at_most,
            "members": members,
            "identity_groups": touched_groups,
            "size_m": rep.get("size_m"),
            "size_basis": rep.get("size_basis"),
            "size_confidence": rep.get("size_confidence"),
            "parent": rep.get("parent"),
            "relation": rep.get("relation"),
            "children": kids,
            "best_view": view,
            "occlusion": rep.get("occlusion") or (view or {}).get("occlusion", "none"),
            "source_images": images,
            "flags": sorted(set(flags)),
        }
        if rep.get("inferred_whole"):
            asset["inferred_whole"] = rep["inferred_whole"]
        if cluster_id:
            asset["cluster_id"] = cluster_id
        assets.append(asset)

    anchors = []
    for gid in sorted(nodes):
        node = nodes[gid]
        if node.get("parent") is not None:
            continue
        anchors.append({
            "global_id": gid,
            "label": node.get("label"),
            "category": node.get("category"),
            "route": "model",
            "route_reason": "anchor: built as the room shell, not generated",
            "size_m": node.get("size_m"),
            "size_basis": node.get("size_basis"),
            "children": sorted(children.get(gid, [])),
            "best_view": best_view(node, scores),
            "source_images": sorted({v.get("image_id") for v in node.get("views") or []
                                     if v.get("image_id")}),
        })

    by_route: dict[str, int] = {}
    for asset in assets:
        by_route[asset["route"]] = by_route.get(asset["route"], 0) + 1
    summary = {
        "objects_in_graph": len(nodes),
        "anchors": len(anchors),
        "unique_assets": len(assets),
        "instances": sum(a["count"] for a in assets),
        "instances_at_least": sum(a["count_at_least"] for a in assets),
        "instances_at_most": sum(a["count_at_most"] for a in assets),
        "by_route": by_route,
        "flagged": [a["asset_id"] for a in assets if a["flags"]],
        "unconfirmed": len(unconfirmed),
    }
    return {
        "schema": SCHEMA_OUT,
        "source_schema": graph.get("schema"),
        "images": graph.get("images") or [],
        "assets": assets,
        "anchors": anchors,
        "unconfirmed": [{"global_id": gid, "label": nodes[gid].get("label"),
                         "reason": nodes[gid]["unconfirmed"].get("reason"),
                         "closer_view": nodes[gid]["unconfirmed"].get("closer_view"),
                         "best_view": best_view(nodes[gid], scores)} for gid in unconfirmed],
        "review": [],
        "summary": summary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("graph", help="scene_graph.json")
    parser.add_argument("--scores", help="view_scores.json from the decompose run")
    parser.add_argument("--out", required=True, help="write asset_plan.json here")
    parser.add_argument("--force", action="store_true", help="overwrite an existing --out file")
    args = parser.parse_args(argv)

    graph = read_json(pathlib.Path(args.graph))
    if graph is None:
        return 2
    if not isinstance(graph, dict) or not isinstance(graph.get("nodes"), list):
        print("error: the graph has no nodes list", file=sys.stderr)
        return 1
    if graph.get("schema") != SCHEMA_IN:
        print(f"warning: expected schema {SCHEMA_IN}, got {graph.get('schema')!r}", file=sys.stderr)
    if not graph["nodes"]:
        print("error: the graph has no nodes", file=sys.stderr)
        return 1

    scores_doc = None
    if args.scores:
        scores_doc = read_json(pathlib.Path(args.scores))
        if scores_doc is None:
            return 2

    out = pathlib.Path(args.out)
    if out.exists() and not args.force:
        print(f"error: {out.as_posix()} exists; pass --force to overwrite", file=sys.stderr)
        return 1

    plan = build_plan(graph, scores_doc)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": out.as_posix(), **plan["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
