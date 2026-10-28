#!/usr/bin/env python3
"""Build the scene graph skeleton from the matches, structures and detections.

Deterministic bookkeeping only: it turns per-image ids into global ones, gathers
every view of each object, resolves each parent to a global id and merges the
clusters and areas. It makes no judgements — where two views disagree about an
object's parent it takes the better view's answer and records the disagreement
in `parent_conflicts` for the emit stage to look at.

Prints a summary to stdout and writes the graph with --out. Exit codes:
0 built, 1 the inputs disagree in a way that needs a person, 2 unreadable.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ID_RANK = {"high": 3, "medium": 2, "low": 1}


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_folder(folder: pathlib.Path) -> dict[str, dict]:
    """Every *.json in a folder, keyed by its image_id."""
    files = sorted(folder.glob("*.json")) if folder.is_dir() else [folder]
    if not files:
        raise FileNotFoundError(f"no JSON files in {folder.as_posix()}")
    out = {}
    for path in files:
        data = load(path)
        out[data.get("image_id") or path.stem] = data
    return out


def area(bbox) -> float:
    if not isinstance(bbox, list) or len(bbox) != 4:
        return 0.0
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def ancestors_of(node_of: dict, global_of: dict, local_id) -> list:
    """Global ids of everything above `local_id` in its own image's structure.

    Used to tell a more specific parent from a competing one: a view that says
    "on the dish" and a view that says "on the tray" agree if the dish is on the
    tray, and the first is simply the better answer.
    """
    out: list = []
    seen = set()
    current = local_id
    while current and current not in seen:
        seen.add(current)
        node = node_of.get(current)
        if node is None:
            break
        current = node.get("parent")
        if current:
            out.append(global_of.get(current))
    return out


def build(matches: dict, structures: dict, detections: dict) -> tuple[dict, list[str]]:
    problems: list[str] = []

    objects = {}
    for obj in matches.get("objects") or []:
        if isinstance(obj, dict) and obj.get("global_id"):
            objects[obj["global_id"]] = obj

    # local_id -> global_id, the map everything else is built on.
    global_of: dict[str, str] = {}
    for global_id, obj in objects.items():
        for member in obj.get("members") or []:
            if isinstance(member, dict) and member.get("local_id"):
                global_of[member["local_id"]] = global_id

    det_of: dict[str, dict] = {}
    for image_id, data in detections.items():
        for entry in data.get("objects") or []:
            if isinstance(entry, dict) and entry.get("local_id"):
                det_of[entry["local_id"]] = entry

    node_of: dict[str, dict] = {}
    for image_id, data in structures.items():
        for node in data.get("nodes") or []:
            if isinstance(node, dict) and node.get("local_id"):
                node_of[node["local_id"]] = node

    nodes = []
    conflicts = []
    for global_id, obj in sorted(objects.items()):
        views = []
        for member in obj.get("members") or []:
            local_id = member.get("local_id")
            detection = det_of.get(local_id)
            if detection is None:
                problems.append(f"{global_id}: '{local_id}' is in no detections file")
                continue
            views.append({
                "image_id": member.get("image_id"),
                "local_id": local_id,
                "bbox": detection.get("bbox"),
                "occluded": bool(detection.get("occluded")),
                "occlusion": detection.get("occlusion") or ("partial" if detection.get("occluded") else "none"),
                "truncated": detection.get("truncated") or [],
                "id_confidence": detection.get("id_confidence", "high"),
                "frame_share": round(area(detection.get("bbox")), 6),
            })
        if not views:
            problems.append(f"{global_id}: has no usable view")
            continue
        # The better view wins: biggest in frame, then most confident about what it is.
        views.sort(key=lambda v: (v["frame_share"], ID_RANK.get(v["id_confidence"], 0)),
                   reverse=True)
        best = views[0]
        best_detection = det_of[best["local_id"]]

        # Parent, as each view's structure saw it, mapped to global ids.
        candidates = []
        for view in views:
            node = node_of.get(view["local_id"])
            if node is None:
                continue
            parent_local = node.get("parent")
            parent_global = global_of.get(parent_local) if parent_local else None
            if parent_local and parent_global is None:
                problems.append(
                    f"{global_id}: parent '{parent_local}' of '{view['local_id']}' is in no "
                    "global object"
                )
                continue
            candidates.append({
                "image_id": view["image_id"],
                "parent": parent_global,
                "parent_local": parent_local,
                "relation": node.get("relation"),
                "support_inferred": bool(node.get("support_inferred")),
            })
        # Two views can name different parents without disagreeing. Where one view's
        # parent sits ABOVE the other's in that other view's own structure — a candle on
        # a dish on a tray, against a candle on the tray by a view with no dish — the
        # deeper answer is the same claim with more detail, and it wins outright.
        # Otherwise the views really do disagree, and then a view that SAW what holds the
        # object beats a bigger view that had to reason about it. (A run put a worktop on
        # the floor: the view with more of it in frame could not see the base units and
        # inferred the floor, while the smaller view observed them.) `candidates` is
        # already in view order, biggest and most confident first, and the sort is stable.
        def deeper_than(a, b):
            """True when a's parent sits below b's parent in a's own structure."""
            if a["parent"] is None or b["parent"] is None or a["parent"] == b["parent"]:
                return False
            return b["parent"] in ancestors_of(node_of, global_of, a["parent_local"])

        shallow = [any(deeper_than(other, c) for other in candidates) for c in candidates]
        ordered = sorted(
            range(len(candidates)),
            key=lambda i: (shallow[i], candidates[i]["support_inferred"], i))
        ordered = [candidates[i] for i in ordered]
        chosen = ordered[0] if ordered else {"parent": None, "relation": None,
                                             "image_id": None, "support_inferred": False}
        distinct = {(c["parent"], c["relation"]) for c in candidates}
        if len(distinct) > 1:
            conflicts.append({
                "global_id": global_id,
                "label": obj.get("label"),
                "chose": {"parent": chosen["parent"], "relation": chosen["relation"],
                          "from": chosen["image_id"],
                          "because": "saw the support, then largest in frame, then most confident"
                                     if not chosen["support_inferred"]
                                     else "largest in frame, then most confident; every view "
                                          "inferred the support"},
                "others": [c for c in candidates if (c["parent"], c["relation"])
                           != (chosen["parent"], chosen["relation"])],
            })

        # Size from the view most sure of it, falling back to the better view.
        sized = sorted(
            (det_of[v["local_id"]] for v in views if det_of.get(v["local_id"])),
            key=lambda d: (ID_RANK.get(d.get("size_confidence"), 0), area(d.get("bbox"))),
            reverse=True)
        size_from = sized[0] if sized else best_detection

        # How hidden the object is, from the view that shows the most of it. Where every view
        # shows it heavily hidden, the context-built description of the whole object travels
        # with the node, from the least hidden view that wrote one: a generator working from a
        # crop of a chair back needs the prompt to say what the rest of the chair is.
        hidden_rank = {"none": 0, "partial": 1, "heavy": 2}
        least = min(views, key=lambda v: hidden_rank.get(v["occlusion"], 0))
        inferred = None
        if hidden_rank.get(least["occlusion"], 0) == 2:
            for view in sorted(views, key=lambda v: hidden_rank.get(v["occlusion"], 0)):
                detection = det_of[view["local_id"]]
                if str(detection.get("whole_description") or "").strip():
                    inferred = {"whole_description": detection["whole_description"],
                                "visible": detection.get("visible"),
                                "from": view["image_id"]}
                    break
        extra = {"occlusion": least["occlusion"]}
        if inferred:
            extra["inferred_whole"] = inferred

        nodes.append({
            "global_id": global_id,
            # Several views: the best one names it, as it describes it. The first member listed
            # is often the wide view's guess ('hair claw' for the sunglasses the close-up saw).
            "label": (obj.get("label") if obj.get("named_by_agent") or len(views) == 1
                      else best_detection.get("label") or obj.get("label")),
            "description": best_detection.get("description"),
            **extra,
            "category": best_detection.get("category"),
            "parent": chosen["parent"],
            "relation": chosen["relation"],
            "support_inferred": chosen["support_inferred"],
            "parent_source": chosen["image_id"],
            "size_m": size_from.get("size_m"),
            "size_confidence": size_from.get("size_confidence"),
            "size_basis": size_from.get("size_basis"),
            "seen_in": len(views),
            "views": views,
        })

    # Clusters and areas: map members to global ids, then merge the ones that are the
    # same group seen twice. Two images rarely list identical membership for "the dining
    # area", so an exact-match dedupe would leave one area per image.
    def gather(key: str, id_prefix: str) -> list[dict]:
        found = []
        for image_id, data in sorted(structures.items()):
            for group in data.get(key) or []:
                members = {global_of[m] for m in group.get("members") or [] if m in global_of}
                if len(members) < 2:
                    continue
                found.append({
                    "label": group.get("label"),
                    "members": members,
                    "notes": [group.get("note")] if group.get("note") else [],
                    "seen_in": [image_id],
                    "kinds": [group.get("kind")] if key == "clusters" else [],
                })

        merged: list[dict] = []
        for group in found:
            key_label = (group["label"] or "").strip().lower()
            for other in merged:
                same_label = (other["label"] or "").strip().lower() == key_label
                if same_label and (group["members"] & other["members"]):
                    other["members"] |= group["members"]
                    other["notes"] += group["notes"]
                    other["seen_in"] += group["seen_in"]
                    other["kinds"] += group["kinds"]
                    break
            else:
                merged.append(dict(group))

        result = []
        for index, group in enumerate(merged, start=1):
            entry = {
                f"{id_prefix}_id": f"{id_prefix}{index:03d}",
                "label": group["label"],
                "members": sorted(group["members"]),
                "seen_in": sorted(set(group["seen_in"])),
            }
            if group["notes"]:
                entry["note"] = " ".join(dict.fromkeys(group["notes"]))
            if key == "clusters":
                kinds = [k for k in dict.fromkeys(group["kinds"]) if k]
                entry["kind"] = kinds[0] if kinds else None
                if len(kinds) > 1:
                    entry["kind_disagreement"] = kinds
            result.append(entry)
        return result

    # Unresolved sets become identity groups: a handful of global objects that stand for
    # a known smaller number of physical things. The ontology counts with these.
    identity_groups = []
    for index, issue in enumerate(matches.get("unresolved") or [], start=1):
        members, per_image = [], {}
        for candidate in issue.get("candidates") or []:
            local_id = candidate.get("local_id") if isinstance(candidate, dict) else None
            global_id = global_of.get(local_id)
            if global_id and global_id not in members:
                members.append(global_id)
            if isinstance(candidate, dict) and candidate.get("image_id"):
                per_image[candidate["image_id"]] = per_image.get(candidate["image_id"], 0) + 1
        if len(members) < 2:
            continue
        floor = max(per_image.values()) if per_image else 1
        distinct = issue.get("distinct_objects")
        if distinct is None:
            distinct = min(max(floor, 1), len(members))
            basis = ("assumed from the candidates alone: the match stage gave no "
                     "distinct_objects, so this is the floor")
        else:
            basis = issue.get("distinct_basis")
        identity_groups.append({
            "group_id": f"ig{index:03d}",
            "label": issue.get("label"),
            "from": issue.get("issue_id"),
            "members": sorted(members),
            "distinct": distinct,
            "at_least": min(floor, len(members)),
            "at_most": len(members),
            "basis": basis,
        })

    graph = {
        "schema": "scene-decompose/scene-graph@1",
        "bbox_convention": "normalised [x0,y0,x1,y1], 0-1 of the image, origin top-left",
        "images": sorted(structures),
        "nodes": nodes,
        "clusters": gather("clusters", "cl"),
        "areas": gather("areas", "ar"),
        "parent_conflicts": conflicts,
        "identity_groups": identity_groups,
    }
    return graph, problems


REGION_SLACK = 0.01


def mark_unconfirmed(graph: dict, registration: dict | None) -> int:
    """Mark wide-view readings a close-up should have confirmed and did not.

    A wide shot names small things at a scale that cannot support the name: in one kitchen
    the checkered shakers became 'candle jar', the camera 'small figurine', the serving board
    'wooden tray'. The close-up of that table named each correctly, the names did not match,
    and every guess survived as a second object, which the asset plan then counted as an
    asset that does not exist. An object seen only in the wider image of a close-up pair,
    inside the region the close-up covers, named with low confidence, is most likely one of
    the close-up's objects misread. It stays in the graph, marked, so nothing is lost; the
    asset plan reviews it instead of making it.
    """
    pairs = [p for p in (registration or {}).get("pairs") or []
             if p.get("relation") == "close-up" and p.get("closer") and p.get("region")]
    marked = 0
    for node in graph["nodes"]:
        if node.get("parent") is None or len(node.get("views") or []) != 1:
            continue
        view = node["views"][0]
        if view.get("id_confidence") != "low":
            continue
        box = view.get("bbox") or []
        for pair in pairs:
            wide = pair["b"] if pair["closer"] == pair["a"] else pair["a"]
            region = pair["region"]
            if view.get("image_id") != wide or len(box) != 4:
                continue
            if all((box[0] >= region[0] - REGION_SLACK, box[1] >= region[1] - REGION_SLACK,
                    box[2] <= region[2] + REGION_SLACK, box[3] <= region[3] + REGION_SLACK)):
                node["unconfirmed"] = {
                    "closer_view": pair["closer"],
                    "reason": f"named with low confidence in {wide} and not found in the "
                              f"close-up {pair['closer']}, which covers about that part of the scene; "
                              "possibly a misreading of an object the close-up recorded, or just outside its frame"}
                marked += 1
                break
    return marked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--matches", required=True, help="matches.json")
    parser.add_argument("--structures", required=True, help="folder of structure files")
    parser.add_argument("--detections", required=True, help="folder of detections files")
    parser.add_argument("--out", help="write the graph here as well as summarising to stdout")
    parser.add_argument("--force", action="store_true", help="overwrite an existing --out file")
    parser.add_argument("--registration", help="registration.json, to mark wide-view readings "
                                               "a close-up did not confirm")
    args = parser.parse_args(argv)

    try:
        matches = load(pathlib.Path(args.matches))
        structures = load_folder(pathlib.Path(args.structures))
        detections = load_folder(pathlib.Path(args.detections))
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: not valid JSON: {exc}", file=sys.stderr)
        return 2

    graph, problems = build(matches, structures, detections)
    registration = None
    if args.registration and pathlib.Path(args.registration).exists():
        try:
            registration = load(pathlib.Path(args.registration))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"registration could not be read: {exc}")
    unconfirmed = mark_unconfirmed(graph, registration)

    if args.out:
        out = pathlib.Path(args.out)
        if out.exists() and not args.force:
            print(f"error: {out.as_posix()} exists; pass --force to overwrite", file=sys.stderr)
            return 1
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "nodes": len(graph["nodes"]),
        "anchors": [n["global_id"] for n in graph["nodes"] if n["parent"] is None],
        "seen_in_more_than_one_image": sum(1 for n in graph["nodes"] if n["seen_in"] > 1),
        "clusters": len(graph["clusters"]),
        "areas": len(graph["areas"]),
        "parent_conflicts": len(graph["parent_conflicts"]),
        "identity_groups": len(graph["identity_groups"]),
        "unconfirmed": unconfirmed,
        "objects_that_may_be_duplicates": sum(
            len(g["members"]) - g["distinct"] for g in graph["identity_groups"]),
        "problems": problems,
        "out": args.out,
    }, indent=2))
    for line in problems:
        print(f"error: {line}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
