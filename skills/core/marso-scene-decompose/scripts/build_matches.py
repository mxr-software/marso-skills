#!/usr/bin/env python3
"""Build matches.json from the automatic matches and the agents' short-form decisions.

An agent judging a contact sheet writes only what it decided, in a form short enough to
write in a minute: merges (the local ids, a confidence, at least two lines of evidence),
refusals (the candidates and why not) and corrections. This turns that and `auto.json` into
the full matches file the rest of the pipeline reads, and does the bookkeeping the old
reconcile pass did: every object ends up in exactly one global object, ids are numbered once,
and nothing is dropped.

It decides no identity, and it will not let a decision break a rule:

- a merge with fewer than two lines of evidence is not made; it is kept separate and noted,
  because one line is not enough to merge on;
- a merge that would put two objects from one image in one global object is not made;
- a merge that contradicts an automatic one is not made;
- a refusal must say what argues against; an empty one becomes "not enough evidence to merge";
- a veto of an automatic match (an agent looked at both crops and they are not the same object)
  always stands: it only undoes a merge, which is the safe direction.

Anything not decided stays its own object. That is the safe direction.

Exit codes: 0 written, 1 written but some decisions were not applied (listed), 2 an input
could not be read.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

DECISIONS_PER_IMAGE_KEYS = ("merges", "refusals", "corrections", "vetoes")


STOP = {"a", "an", "the", "of", "with", "and", "on", "in", "small", "large", "dark", "light",
        "left", "right", "hand", "upper", "lower", "back", "front", "second", "round", "black",
        "white", "grey", "gray", "silver", "gold", "golden", "clear", "glass", "plastic", "metal",
        "wooden", "red", "blue", "green", "pink", "tall", "short"}


def head(label) -> str:
    """The word that says what a thing is: its last real word."""
    found = [w for w in re.findall(r"[a-z]+", str(label or "").lower()) if len(w) > 2 and w not in STOP]
    return found[-1] if found else ""


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_labels(detections: pathlib.Path) -> tuple[dict, dict]:
    """local_id -> label, and local_id -> image_id, from the merged detections files."""
    labels, images = {}, {}
    for path in sorted(detections.glob("*.json")):
        if "." in path.stem:
            continue
        data = load(path)
        image_id = data.get("image_id") or path.stem
        for obj in data.get("objects") or []:
            if obj.get("local_id"):
                labels[obj["local_id"]] = obj.get("label") or obj["local_id"]
                images[obj["local_id"]] = image_id
    return labels, images


def as_list(value) -> list:
    return list(value) if isinstance(value, list) else ([value] if value else [])


def union_refusals(refusals: list[dict]) -> list[dict]:
    """Refusals that share a candidate are one question, asked twice.

    Two groups can offer the same object (a carrier group and a position group), and two agents
    then refuse overlapping sets. An object can only be in one identity group, so they are joined:
    the candidates are the union, the reasons are both, and the number of distinct things is the
    larger of the two answers (it is clamped to the floor and ceiling afterwards).
    """
    out: list[dict] = []
    for refusal in refusals:
        ids = [str(c) for c in refusal.get("candidates") or []]
        hits = [o for o in out if set(o["candidates"]) & set(ids)]
        if not hits:
            out.append({**refusal, "candidates": list(dict.fromkeys(ids))})
            continue
        base = hits[0]
        for other in hits[1:]:
            out.remove(other)
        for source in hits[1:] + [{**refusal, "candidates": ids}]:
            base["candidates"] = list(dict.fromkeys(base["candidates"] + list(source["candidates"])))
            base["for"] = list(dict.fromkeys(as_list(base.get("for")) + as_list(source.get("for"))))
            base["against"] = list(dict.fromkeys(as_list(base.get("against")) + as_list(source.get("against"))))
            counts = [n for n in (base.get("distinct_objects"), source.get("distinct_objects"))
                      if isinstance(n, int) and not isinstance(n, bool)]
            if counts:
                base["distinct_objects"] = max(counts)
    return out


def build(auto: dict, decisions: list[dict], labels: dict, images: dict) -> tuple[dict, list[str]]:
    problems: list[str] = []
    members_of: list[dict] = []           # each: {"members": {image: local}, label, confidence, evidence}
    where: dict[str, int] = {}

    def add(item: dict) -> int:
        members_of.append(item)
        index = len(members_of) - 1
        for lid in item["members"].values():
            where[lid] = index
        return index

    for found in auto.get("matched") or []:
        add({"members": {m["image_id"]: m["local_id"] for m in found["members"]},
             "label": found.get("label"), "confidence": found.get("confidence", "medium"),
             "evidence": list(found.get("evidence") or []), "source": "automatic"})

    refusals: list[dict] = []
    corrections: list[dict] = []
    notes: list[str] = []
    vetoed: list[dict] = []
    checks = {c["check_id"]: c for c in auto.get("checks") or []}

    for decision in decisions:
        batch = decision.get("batch_id") or "agent"
        for merge in decision.get("merges") or []:
            ids = [str(x) for x in merge.get("members") or []]
            evidence = [str(e).strip() for e in merge.get("evidence") or [] if str(e).strip()]
            confidence = merge.get("confidence") if merge.get("confidence") in ("high", "medium", "low") else "low"
            unknown = [i for i in ids if i not in images]
            if len(ids) < 2 or unknown:
                problems.append(f"{batch}: merge {ids} names ids that do not exist: {unknown or ids}")
                continue
            if len(evidence) < 2:
                problems.append(f"{batch}: merge {ids} has {len(evidence)} line(s) of evidence; "
                                "a merge needs two, so these stay separate")
                refusals.append({"candidates": ids, "for": evidence or ["the agent thought they matched"],
                                 "against": ["only one line of evidence was given, which is not "
                                             "enough to merge on"],
                                 "from": batch})
                continue
            by_image: dict[str, str] = {}
            clash = False
            for lid in ids:
                if images[lid] in by_image and by_image[images[lid]] != lid:
                    clash = True
                by_image[images[lid]] = lid
            if clash:
                problems.append(f"{batch}: merge {ids} holds two objects from one image; refused")
                continue
            owners = {where[lid] for lid in ids if lid in where}
            if len(owners) > 1:
                problems.append(f"{batch}: merge {ids} would join two different matches; refused")
                continue
            if owners:
                owner = members_of[next(iter(owners))]
                if any(images[lid] in owner["members"] and owner["members"][images[lid]] != lid
                       for lid in ids):
                    problems.append(f"{batch}: merge {ids} contradicts an automatic match; refused")
                    continue
                for lid in ids:
                    owner["members"][images[lid]] = lid
                    where[lid] = next(iter(owners))
                owner["evidence"] += evidence
                continue
            add({"members": by_image, "label": merge.get("label") or labels.get(ids[0]),
                 "named_by_agent": bool(merge.get("label")),
                 "confidence": confidence, "evidence": evidence, "source": batch})
        for veto in decision.get("vetoes") or []:
            check = checks.get(str(veto.get("check")))
            first = next((m["local_id"] for m in (check or {}).get("members") or [] if m["local_id"] in where), None)
            if check is None or first is None:
                problems.append(f"{batch}: veto of {veto.get('check')} names no automatic match")
                continue
            owner = members_of[where[first]]
            held = set(owner["members"].values())
            drop = [str(d) for d in veto.get("drop") or [] if str(d) in held] or sorted(held)
            for lid in drop:
                del owner["members"][images[lid]]
                del where[lid]
            if len(owner["members"]) < 2:
                for lid in owner["members"].values():
                    del where[lid]
                owner["members"] = {}
            reason = str(veto.get("reason") or "an agent judged them different objects").strip()
            vetoed.append({"check": check["check_id"], "was": check.get("label"), "separated": drop,
                           "reason": reason, "from": batch})
            notes.append(f"[{batch}] separated {', '.join(drop)}: {reason}")
        for refusal in decision.get("refusals") or []:
            refusals.append({**refusal, "from": batch})
        for correction in decision.get("corrections") or []:
            corrections.append({**correction, "from": batch})
        if decision.get("notes"):
            notes.append(f"[{batch}] {decision['notes']}")

    # A group nobody decided is not a group of different things. Two chairs in the wide shot and
    # one in the close-up, offered to an agent that never mentioned them, came out as three
    # chairs in a room with two. Anything left in a group that is the same kind of thing in more
    # than one photograph becomes an unresolved set, whose floor is the most that share a photograph.
    already = {str(c) for r in refusals for c in (r.get("candidates") or [])}
    for group in auto.get("groups") or []:
        left_over: dict[str, list[str]] = {}
        for members in (group.get("members") or {}).values():
            for m in members:
                lid = m["local_id"]
                if lid in already or (lid in where and len(members_of[where[lid]]["members"]) > 1):
                    continue
                kind = head(m.get("label") or labels.get(lid))
                if kind:
                    left_over.setdefault(kind, []).append(lid)
        for kind, ids in sorted(left_over.items()):
            if len({images[i] for i in ids}) < 2:
                continue
            refusals.append({
                "candidates": ids, "label": f"which {kind}",
                "for": [f"the same kind of thing ('{kind}') in more than one photograph"],
                "against": ["nobody judged these and nothing separates them, so they are kept apart"],
                "basis": "the floor: candidates in one photograph are certainly different things, "
                         "and nobody decided the rest",
                "from": "automatic"})
            already.update(ids)
            problems_note = f"{kind}: {len(ids)} candidates left undecided in {group.get('group_id')}"
            notes.append(f"[automatic] {problems_note}")

    # A correction says the target IS the better view's object, read wrongly. Left alone, the
    # misreading stays a second object: 'hair claw' beside the sunglasses it was, and the asset
    # plan then made both. Join them when nothing argues against it: the target is matched to
    # nothing else and in no refusal, and the better view's object has no view in the target's
    # image yet. The better view names it.
    joined_by_correction = 0
    for c in corrections:
        target, better = str(c.get("target") or ""), str(c.get("better_view") or "")
        if target not in images or better not in images or images[target] == images[better]:
            continue
        if target in already or better in already:
            continue
        if target in where and len(members_of[where[target]]["members"]) > 1:
            continue
        evidence = [f"correction: {c.get('problem') or 'named differently'}",
                    f"the better view shows {c.get('shows') or labels.get(better, 'it')}"]
        if better in where:
            owner = members_of[where[better]]
            if images[target] in owner["members"]:
                continue
            if target in where:
                members_of[where[target]]["members"] = {}
            owner["members"][images[target]] = target
            owner["evidence"] += evidence
            where[target] = where[better]
        else:
            if target in where:
                members_of[where[target]]["members"] = {}
            add({"members": {images[better]: better, images[target]: target},
                 "label": labels.get(better), "confidence": "medium", "evidence": evidence,
                 "source": "correction"})
        joined_by_correction += 1
    if joined_by_correction:
        notes.append(f"[automatic] {joined_by_correction} misreading(s) joined to the object a "
                     "correction said they were")

    # Everything left is its own object.
    for lid in sorted(images):
        if lid not in where:
            add({"members": {images[lid]: lid}, "label": labels.get(lid), "confidence": None,
                 "evidence": [], "source": "single"})

    objects = []
    global_of: dict[str, str] = {}
    for index, item in enumerate((m for m in members_of if m["members"]), start=1):
        global_id = f"g{index:03d}"
        entry = {"global_id": global_id, "label": item["label"] or "object",
                 "members": [{"image_id": i, "local_id": l} for i, l in sorted(item["members"].items())]}
        if len(item["members"]) > 1:
            if item.get("named_by_agent"):
                entry["named_by_agent"] = True
            entry["confidence"] = item["confidence"]
            entry["evidence"] = list(dict.fromkeys(item["evidence"]))
            entry["matched_by"] = item["source"]
        objects.append(entry)
        for lid in item["members"].values():
            global_of[lid] = global_id

    unresolved = []
    for number, refusal in enumerate(union_refusals(refusals), start=1):
        ids = [str(c) for c in refusal.get("candidates") or []]
        ids = [i for i in ids if i in images]
        if len(ids) < 2:
            problems.append(f"refusal {refusal.get('candidates')}: needs two or more known candidates")
            continue
        per_image: dict[str, int] = {}
        for lid in ids:
            per_image[images[lid]] = per_image.get(images[lid], 0) + 1
        floor, ceiling = max(per_image.values()), len(ids)
        distinct = refusal.get("distinct_objects")
        basis = refusal.get("basis") or refusal.get("distinct_basis")
        if not isinstance(distinct, int) or isinstance(distinct, bool) or not floor <= distinct <= ceiling:
            distinct = floor
            basis = ("the floor: candidates in one photograph are certainly different things; "
                     "the agent gave no number" if len(per_image) > 1 else None)
        entry = {"issue_id": f"u{number:03d}",
                 "label": refusal.get("label") or " / ".join(dict.fromkeys(labels.get(i, i) for i in ids))[:80],
                 "candidates": [{"image_id": images[i], "local_id": i} for i in ids],
                 "for": [str(x) for x in (refusal.get("for") if isinstance(refusal.get("for"), list)
                                          else [refusal.get("for") or "they look alike"]) if str(x).strip()],
                 "against": [str(x) for x in (refusal.get("against") if isinstance(refusal.get("against"), list)
                                              else [refusal.get("against") or ""]) if str(x).strip()]
                            or ["not enough evidence to merge"],
                 "decision": "kept separate"}
        if len(per_image) > 1:
            entry["distinct_objects"] = distinct
            entry["distinct_basis"] = basis or "the number the agent judged from the contact sheet"
        if refusal.get("would_settle_it"):
            entry["would_settle_it"] = refusal["would_settle_it"]
        unresolved.append(entry)

    fixed_corrections = []
    for number, c in enumerate(corrections, start=1):
        target, better = str(c.get("target") or ""), str(c.get("better_view") or "")
        if target not in images or better not in images or images[target] == images[better]:
            problems.append(f"correction {target}->{better}: both must be known objects in "
                            "different images")
            continue
        fixed_corrections.append({
            "correction_id": f"c{len(fixed_corrections) + 1:03d}",
            "target": {"image_id": images[target], "local_id": target},
            "stage": c.get("stage") or "scene-decompose-detect",
            "problem": c.get("problem") or "named differently in a better view",
            "better_view": {"image_id": images[better], "local_id": better},
            "shows": c.get("shows") or labels.get(better, ""),
        })

    result = {"schema": "scene-decompose/matches@1", "images": sorted(set(images.values())),
              "registration_used": True, "notes": " ".join(notes),
              "objects": objects, "corrections": fixed_corrections, "unresolved": unresolved}
    if vetoed:
        result["vetoed"] = vetoed
    return result, problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--auto", required=True, help="auto.json from match_auto.py")
    parser.add_argument("--detections", required=True, help="folder of merged detections files")
    parser.add_argument("--decisions", nargs="*", default=[],
                        help="each agent's decisions file (none is fine: everything undecided stays separate)")
    parser.add_argument("--out", required=True, help="where to write matches.json")
    parser.add_argument("--force", action="store_true", help="overwrite an existing --out")
    args = parser.parse_args(argv)

    try:
        auto = load(pathlib.Path(args.auto))
    except FileNotFoundError:
        print(f"error: no such file: {args.auto}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"error: could not read {args.auto}: {exc}", file=sys.stderr)
        return 2
    if not pathlib.Path(args.detections).is_dir():
        print(f"error: no such folder: {args.detections}", file=sys.stderr)
        return 2
    decisions = []
    for raw in args.decisions:
        try:
            decisions.append(load(pathlib.Path(raw)))
        except FileNotFoundError:
            print(f"error: no such file: {raw}", file=sys.stderr)
            return 2
        except (OSError, ValueError) as exc:
            print(f"error: could not read {raw}: {exc}", file=sys.stderr)
            return 2
    labels, images = read_labels(pathlib.Path(args.detections))
    if not images:
        print("error: no detections were found", file=sys.stderr)
        return 2

    out = pathlib.Path(args.out)
    if out.exists() and not args.force:
        print(f"error: {out.as_posix()} exists; pass --force to overwrite", file=sys.stderr)
        return 1
    result, problems = build(auto, decisions, labels, images)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    summary = {"out": out.as_posix(), "objects": len(result["objects"]),
               "matched_across_images": sum(1 for o in result["objects"] if len(o["members"]) > 1),
               "unresolved": len(result["unresolved"]), "corrections": len(result["corrections"]),
               "decisions_files": len(decisions), "problems": problems}
    print(json.dumps(summary, indent=2))
    for line in problems:
        print(f"warning: {line}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
