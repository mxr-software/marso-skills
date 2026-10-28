#!/usr/bin/env python3
"""Check a matches file: the half of the gate a script can do.

It enforces the rules that do not need eyes: one member per image, every object
accounted for, parents matched before children, evidence present on every merge,
and an honest `against` on every unresolved set. It cannot see the photographs,
so it cannot tell a right merge from a wrong one.

Prints a JSON report to stdout. Exit codes: 0 clean, 1 problems found,
2 a file could not be read.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

CONFIDENCES = {"high", "medium", "low"}
DECISIONS = {"kept separate", "merged", "needs another view"}
CORRECTION_STAGES = {"scene-decompose-detect", "scene-decompose-structure"}
MIN_EVIDENCE = 2


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_structures(folder: pathlib.Path) -> tuple[dict, dict]:
    """Returns {local_id: image_id} and {local_id: parent_local_id} across every structure."""
    owner: dict[str, str] = {}
    parent: dict[str, str | None] = {}
    files = sorted(folder.glob("*.json")) if folder.is_dir() else [folder]
    if not files:
        raise FileNotFoundError(f"no structure files in {folder.as_posix()}")
    for path in files:
        data = load(path)
        image_id = data.get("image_id") or path.stem
        for node in data.get("nodes") or []:
            if isinstance(node, dict) and node.get("local_id"):
                owner[node["local_id"]] = image_id
                parent[node["local_id"]] = node.get("parent")
    return owner, parent


def check(data: dict, owner: dict | None, parent: dict | None,
          batch: set | None = None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    objects = data.get("objects")
    if not isinstance(objects, list) or not objects:
        return ["the file must have a non-empty 'objects' list"], warnings

    seen_global: set[str] = set()
    placed: dict[str, str] = {}          # local_id -> global_id
    global_of: dict[str, str] = {}
    members_by_global: dict[str, list[dict]] = {}

    for index, obj in enumerate(objects):
        where = f"objects[{index}]"
        if not isinstance(obj, dict):
            errors.append(f"{where}: must be an object")
            continue
        global_id = obj.get("global_id")
        if not isinstance(global_id, str) or not global_id:
            errors.append(f"{where}: missing 'global_id'")
            continue
        if global_id in seen_global:
            errors.append(f"{where}: global_id '{global_id}' is used more than once")
            continue
        seen_global.add(global_id)
        if not str(obj.get("label") or "").strip():
            errors.append(f"{global_id}: needs a label")

        members = obj.get("members")
        if not isinstance(members, list) or not members:
            errors.append(f"{global_id}: needs at least one member")
            continue
        members_by_global[global_id] = members

        per_image: dict[str, list[str]] = {}
        for member in members:
            if not isinstance(member, dict):
                errors.append(f"{global_id}: members must be objects")
                continue
            image_id, local_id = member.get("image_id"), member.get("local_id")
            if not image_id or not local_id:
                errors.append(f"{global_id}: every member needs an image_id and a local_id")
                continue
            per_image.setdefault(image_id, []).append(local_id)
            if local_id in placed:
                errors.append(
                    f"'{local_id}' is a member of both '{placed[local_id]}' and '{global_id}'"
                )
            placed[local_id] = global_id
            global_of[local_id] = global_id
            if owner is not None:
                if local_id not in owner:
                    errors.append(f"{global_id}: '{local_id}' is not in any structure file")
                elif owner[local_id] != image_id:
                    errors.append(
                        f"{global_id}: '{local_id}' is in image '{owner[local_id]}', "
                        f"not '{image_id}'"
                    )

        for image_id, locals_ in per_image.items():
            if len(locals_) > 1:
                errors.append(
                    f"{global_id}: holds {len(locals_)} objects from image '{image_id}' "
                    f"({', '.join(sorted(locals_))}); one physical thing is in a photograph once"
                )

        if len(members) > 1:
            evidence = obj.get("evidence")
            if not isinstance(evidence, list) or len([e for e in evidence if str(e).strip()]) < MIN_EVIDENCE:
                errors.append(
                    f"{global_id}: a merge needs at least {MIN_EVIDENCE} lines of evidence"
                )
            if obj.get("confidence") not in CONFIDENCES:
                errors.append(f"{global_id}: confidence must be one of {sorted(CONFIDENCES)}")

    # Parents before children: if a child is merged across images, its parents should be too.
    if parent is not None:
        for global_id, members in members_by_global.items():
            if len(members) < 2:
                continue
            parents = []
            for member in members:
                local_id = member.get("local_id")
                parents.append(parent.get(local_id) if local_id else None)
            known = [p for p in parents if p]
            if len(known) == len(members) and len(members) > 1:
                parent_globals = {global_of.get(p) for p in known}
                if None in parent_globals:
                    warnings.append(
                        f"{global_id}: merged across images, but a parent is not in any global "
                        "object; match parents before their children"
                    )
                elif len(parent_globals) > 1:
                    warnings.append(
                        f"{global_id}: merged across images, but its members' parents were not "
                        "matched to each other; check this is not a lookalike in another place"
                    )

    seen_corrections: set[str] = set()
    for index, correction in enumerate(data.get("corrections") or []):
        where = f"corrections[{index}]"
        if not isinstance(correction, dict):
            errors.append(f"{where}: must be an object")
            continue
        correction_id = str(correction.get("correction_id") or "").strip()
        if not correction_id:
            errors.append(f"{where}: needs a correction_id")
        elif correction_id in seen_corrections:
            errors.append(f"{where}: correction_id '{correction_id}' is used more than once")
        seen_corrections.add(correction_id)

        if correction.get("stage") not in CORRECTION_STAGES:
            errors.append(f"{where}: stage must be one of {sorted(CORRECTION_STAGES)}")
        for field in ("problem", "shows"):
            if not str(correction.get(field) or "").strip():
                errors.append(f"{where}: '{field}' must say something")

        for field in ("target", "better_view"):
            ref = correction.get(field)
            if not isinstance(ref, dict) or not ref.get("local_id") or not ref.get("image_id"):
                errors.append(f"{where}: '{field}' needs an image_id and a local_id")
                continue
            local_id = ref["local_id"]
            if owner is not None and local_id not in owner:
                errors.append(f"{where}: '{local_id}' is not in any structure file")
            elif local_id not in placed and (batch is None or local_id in batch):
                errors.append(
                    f"{where}: '{local_id}' is not in any global object; a correction never "
                    "removes an object from the graph"
                )
        target, better = correction.get("target"), correction.get("better_view")
        if (isinstance(target, dict) and isinstance(better, dict)
                and target.get("image_id") == better.get("image_id")):
            errors.append(
                f"{where}: the target and the better view are in the same image, so no view "
                "beats the other"
            )

    for index, issue in enumerate(data.get("unresolved") or []):
        where = f"unresolved[{index}]"
        if not isinstance(issue, dict):
            errors.append(f"{where}: must be an object")
            continue
        if not str(issue.get("issue_id") or "").strip():
            errors.append(f"{where}: needs an issue_id")
        if not str(issue.get("label") or "").strip():
            errors.append(f"{where}: needs a label")
        candidates = issue.get("candidates")
        if not isinstance(candidates, list) or len(candidates) < 2:
            errors.append(f"{where}: needs two or more candidates")
        else:
            for candidate in candidates:
                local_id = candidate.get("local_id") if isinstance(candidate, dict) else None
                if not local_id:
                    errors.append(f"{where}: every candidate needs an image_id and a local_id")
                elif owner is not None and local_id not in owner:
                    errors.append(f"{where}: '{local_id}' is not in any structure file")
                elif local_id not in placed and (batch is None or local_id in batch):
                    errors.append(
                        f"{where}: candidate '{local_id}' is not in any global object; being "
                        "unresolved never removes an object from the graph"
                    )
        for field in ("for", "against"):
            value = issue.get(field)
            if not isinstance(value, list) or not [v for v in value if str(v).strip()]:
                errors.append(
                    f"{where}: '{field}' must say something. An empty 'against' means it "
                    "should have been merged"
                )
        if issue.get("decision") not in DECISIONS:
            errors.append(f"{where}: decision must be one of {sorted(DECISIONS)}")

        # How many physical things the set holds. Candidates sharing an image are
        # certainly different, so that is the floor; the candidate count is the ceiling.
        if isinstance(candidates, list) and len(candidates) >= 2:
            per_image = {}
            for candidate in candidates:
                if isinstance(candidate, dict) and candidate.get("image_id"):
                    per_image[candidate["image_id"]] = per_image.get(candidate["image_id"], 0) + 1
            floor = max(per_image.values()) if per_image else 1
            ceiling = len(candidates)
            distinct = issue.get("distinct_objects")
            if len(per_image) < 2:
                pass  # all in one image: they are already known to be different things
            elif distinct is None:
                errors.append(
                    f"{where}: needs 'distinct_objects' — how many physical things this set "
                    f"holds, between {floor} and {ceiling}. Refusing to say which is which is "
                    "not a reason to leave the count wrong"
                )
            elif not isinstance(distinct, int) or isinstance(distinct, bool):
                errors.append(f"{where}: distinct_objects must be a whole number")
            elif not floor <= distinct <= ceiling:
                errors.append(
                    f"{where}: distinct_objects is {distinct}, but candidates share images in a "
                    f"way that puts it between {floor} and {ceiling}"
                )
            elif not str(issue.get("distinct_basis") or "").strip():
                errors.append(f"{where}: distinct_objects needs a distinct_basis saying why")

    if owner is not None:
        # A batch file only ever covers its own ids. Without --batch the checker reports
        # every other object in the run as missing: a real run buried one true error under
        # 118 of these, which is the same as having no gate at all.
        expected = set(owner) if batch is None else (set(owner) & batch)
        for local_id in sorted(expected - set(placed)):
            errors.append(
                f"'{local_id}' ({owner[local_id]}) is in a structure file but in no global object"
            )

    images = {m.get("image_id") for members in members_by_global.values() for m in members
              if isinstance(m, dict)}
    merged = sum(1 for members in members_by_global.values() if len(members) > 1)
    if len(images) > 1 and merged == 0:
        warnings.append(
            "no object was matched across images; if the images really do overlap, the "
            "evidence was not looked for"
        )

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", help="the matches JSON file to check")
    parser.add_argument("--structures", help="the folder of structure files it was built from")
    parser.add_argument("--batch", nargs="*", metavar="LOCAL_ID",
                        help="check this as one batch's file: only these local ids are "
                             "expected to be in it. Pass the ids, or a plan_subtrees.py "
                             "JSON file and a batch_id")
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

    owner = parent = None
    if args.structures:
        try:
            owner, parent = read_structures(pathlib.Path(args.structures))
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        except json.JSONDecodeError as exc:
            print(f"error: a structure file is not valid JSON: {exc}", file=sys.stderr)
            return 2

    batch = None
    if args.batch is not None:
        batch = set()
        for item in args.batch:
            where = pathlib.Path(item)
            if where.suffix.lower() == ".json" and where.exists():
                try:
                    plan = json.loads(where.read_text(encoding="utf-8-sig"))
                except (OSError, ValueError) as exc:
                    print(f"error: could not read {item}: {exc}", file=sys.stderr)
                    return 2
                for entry in (plan.get("batches") or []) + [plan.get("anchor_batch") or {}]:
                    if entry.get("batch_id") in args.batch:
                        for ids in (entry.get("covers") or {}).values():
                            batch.update(ids)
            elif "-" in item:
                batch.add(item)
        if not batch:
            print("error: --batch named no local ids; give the ids, or a plan file and a "
                  "batch_id from it", file=sys.stderr)
            return 1

    errors, warnings = check(data, owner, parent, batch)

    objects = [o for o in data.get("objects") or [] if isinstance(o, dict)]
    across = [o for o in objects if len(o.get("members") or []) > 1]
    report = {
        "path": path.as_posix(),
        "checked_as": f"one batch of {len(batch)} objects" if batch else "the whole run",
        "images": data.get("images"),
        "global_objects": len(objects),
        "matched_across_images": len(across),
        "seen_once": len(objects) - len(across),
        "corrections": len(data.get("corrections") or []),
        "unresolved": len(data.get("unresolved") or []),
        "errors": errors,
        "warnings": warnings,
        "checked": "the bookkeeping only; a script cannot tell a right merge from a wrong one",
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
