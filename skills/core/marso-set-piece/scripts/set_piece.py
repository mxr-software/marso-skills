#!/usr/bin/env python3
"""Check a set piece's parts list and expand its slots into a placement list.

Usage:
    set_piece.py check <set_piece.json>
    set_piece.py place <set_piece.json> --out <placements.json> [--force]

`check` validates the parts list and prints what it implies: the masters to make, the
variants of each, and how many reference images, mesh generations and Retextures that is.
`place` also needs the slots. It writes one row per instance: which part and variant, where
its anchor point sits and how far it is turned. The layout depends only on the file and its
`seed`, so the same file always gives the same placement list.

Coordinates are metres in the set piece's own frame: Z up, the piece's front facing -Y, the
origin on the ground under its centre. A turn (`yaw_deg`) is anticlockwise about Z seen from
above; at 0 an instance faces -Y like the piece.

Standard library only. Exit codes: 0 done, 1 the parts list has problems (each is printed),
2 a file could not be read or would be overwritten.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import re
import sys

SCHEMA = "marso/set-piece@1"
PLACEMENT_SCHEMA = "marso/set-piece-placements@1"
ROUTES = ("model", "instance", "generate")
KINDS = ("single", "row", "grid", "stack")
ANCHORS = ("bottom", "top")
FACINGS = ("across", "along")
ORDERS = ("blocks", "mixed")
DEFAULT_VARIANT_CAP = 6
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def read_json(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as ex:
        print(f"error: cannot read {path.as_posix()}: {ex}", file=sys.stderr)
        return None


def vector(value, length=3, positive=False):
    """The value as a tuple of floats, or None when it is not `length` finite numbers."""
    if not isinstance(value, (list, tuple)) or len(value) != length:
        return None
    out = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item):
            return None
        if positive and item <= 0:
            return None
        out.append(float(item))
    return tuple(out)


def whole(value, minimum=1):
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def check_parts(doc: dict) -> tuple[dict, list[str]]:
    """Parts by id, and every problem found in the parts."""
    problems = []
    if doc.get("schema") != SCHEMA:
        problems.append(f"schema must be {SCHEMA!r}")
    if not str(doc.get("name") or "").strip():
        problems.append("name is missing")
    cap = doc.get("variant_cap", DEFAULT_VARIANT_CAP)
    if not whole(cap):
        problems.append("variant_cap must be a whole number of at least 1")
        cap = DEFAULT_VARIANT_CAP
    parts = {}
    rows = doc.get("parts")
    if not isinstance(rows, list) or not rows:
        return parts, problems + ["parts is missing or empty"]
    for index, part in enumerate(rows):
        if not isinstance(part, dict):
            problems.append(f"parts[{index}] is not an object")
            continue
        part_id = part.get("id")
        where = f"part {part_id!r}"
        if not isinstance(part_id, str) or not ID.match(part_id):
            problems.append(f"parts[{index}]: id must be lowercase letters, digits and single hyphens")
            continue
        if part_id in parts:
            problems.append(f"{where}: id is used twice")
            continue
        parts[part_id] = part
        if not str(part.get("label") or "").strip():
            problems.append(f"{where}: label is missing")
        route = part.get("route")
        if route not in ROUTES:
            problems.append(f"{where}: route must be one of {', '.join(ROUTES)}")
        if part.get("anchor", "bottom") not in ANCHORS:
            problems.append(f"{where}: anchor must be bottom or top")
        if "size_m" in part or route in ("instance", "generate"):
            if vector(part.get("size_m"), positive=True) is None:
                problems.append(f"{where}: size_m must be three positive numbers (width, depth, height)")
        features = part.get("features")
        listed = isinstance(features, list) and features and all(isinstance(f, str) and f.strip() for f in features)
        if "features" in part and not listed and not (isinstance(features, str) and features.strip()):
            problems.append(f"{where}: features must be a phrase or a list of phrases")
        variants = part.get("variants")
        if not isinstance(variants, list) or not variants:
            problems.append(f"{where}: variants needs at least one entry with an id and a look")
            continue
        seen = set()
        for variant in variants:
            variant_id = variant.get("id") if isinstance(variant, dict) else None
            if not isinstance(variant_id, str) or not ID.match(variant_id):
                problems.append(f"{where}: each variant needs an id of lowercase letters, digits and hyphens")
                continue
            if variant_id in seen:
                problems.append(f"{where}: variant {variant_id!r} is listed twice")
            seen.add(variant_id)
            if not str(variant.get("look") or "").strip():
                problems.append(f"{where}: variant {variant_id!r} has no look")
        if len(variants) > cap:
            problems.append(f"{where}: {len(variants)} variants is over the cap of {cap}; "
                            "merge similar looks or raise variant_cap")
    return parts, problems


def slot_parts(slot: dict) -> list:
    if slot.get("kind") in ("single", "stack"):
        return [slot.get("part")]
    listed = slot.get("parts")
    return list(listed) if isinstance(listed, list) else []


def check_slots(doc: dict, parts: dict) -> list[str]:
    problems = []
    slots = doc.get("slots", [])
    if not isinstance(slots, list):
        return ["slots must be a list"]
    seen = set()
    for index, slot in enumerate(slots):
        if not isinstance(slot, dict):
            problems.append(f"slots[{index}] is not an object")
            continue
        slot_id = slot.get("id")
        where = f"slot {slot_id!r}"
        if not isinstance(slot_id, str) or not ID.match(slot_id):
            problems.append(f"slots[{index}]: id must be lowercase letters, digits and single hyphens")
            continue
        if slot_id in seen:
            problems.append(f"{where}: id is used twice")
        seen.add(slot_id)
        kind = slot.get("kind")
        if kind not in KINDS:
            problems.append(f"{where}: kind must be one of {', '.join(KINDS)}")
            continue
        named = slot_parts(slot)
        if not named or any(not isinstance(p, str) for p in named):
            problems.append(f"{where}: name its part" + ("" if kind in ("single", "stack") else "s as a list"))
        for part_id in named:
            if isinstance(part_id, str) and part_id not in parts:
                problems.append(f"{where}: no part {part_id!r} in the parts list")
        wanted = slot.get("variants")
        if wanted is not None:
            if not isinstance(wanted, list) or not wanted:
                problems.append(f"{where}: variants must be a list of variant ids")
            else:
                for part_id in named:
                    known = {v.get("id") for v in parts.get(part_id, {}).get("variants", []) if isinstance(v, dict)}
                    if part_id in parts and not known.intersection(wanted):
                        problems.append(f"{where}: part {part_id!r} has none of the variants {wanted}")
        if "headroom_m" in slot:
            if vector([slot["headroom_m"]], 1, positive=True) is None:
                problems.append(f"{where}: headroom_m must be a positive number")
            else:
                for part_id in named:
                    size = vector(parts.get(part_id, {}).get("size_m"), positive=True)
                    if size and size[2] > slot["headroom_m"]:
                        problems.append(f"{where}: part {part_id!r} is {size[2]} m tall, over the "
                                        f"headroom of {slot['headroom_m']} m")
        if "yaw_deg" in slot and vector([slot["yaw_deg"]], 1) is None:
            problems.append(f"{where}: yaw_deg must be a number")
        for key in ("jitter_deg", "jitter_m"):
            if key in slot and (vector([slot[key]], 1) is None or slot[key] < 0):
                problems.append(f"{where}: {key} must be zero or more")
        if kind == "single":
            if vector(slot.get("position")) is None:
                problems.append(f"{where}: position must be three numbers")
        elif kind == "row":
            start, end = vector(slot.get("start")), vector(slot.get("end"))
            if start is None or end is None:
                problems.append(f"{where}: start and end must each be three numbers")
            elif math.dist(start, end) == 0:
                problems.append(f"{where}: start and end are the same point")
            has_count, has_spacing = "count" in slot, "spacing_m" in slot
            if has_count == has_spacing:
                problems.append(f"{where}: give count or spacing_m, not both")
            elif has_count and not whole(slot["count"]):
                problems.append(f"{where}: count must be a whole number of at least 1")
            elif has_spacing and (vector([slot["spacing_m"]], 1, positive=True) is None):
                problems.append(f"{where}: spacing_m must be a positive number")
            if slot.get("facing", "across") not in FACINGS:
                problems.append(f"{where}: facing must be across or along")
            if slot.get("order", "blocks") not in ORDERS:
                problems.append(f"{where}: order must be blocks or mixed")
        elif kind == "grid":
            for key in ("origin", "across", "back"):
                if vector(slot.get(key)) is None:
                    problems.append(f"{where}: {key} must be three numbers")
            for key in ("columns", "rows"):
                if not whole(slot.get(key)):
                    problems.append(f"{where}: {key} must be a whole number of at least 1")
            if slot.get("order", "blocks") not in ORDERS:
                problems.append(f"{where}: order must be blocks or mixed")
        elif kind == "stack":
            if vector(slot.get("base")) is None:
                problems.append(f"{where}: base must be three numbers")
            if not whole(slot.get("count")):
                problems.append(f"{where}: count must be a whole number of at least 1")
            if "step_m" in slot and vector([slot["step_m"]], 1, positive=True) is None:
                problems.append(f"{where}: step_m must be a positive number")
    return problems


def jobs(parts: dict) -> dict:
    """What the parts list asks Marso for. A generated master arrives in its first variant's look."""
    generated = [p for p in parts.values() if p.get("route") == "generate"]
    built = [p for p in parts.values() if p.get("route") in ("model", "instance")]
    count = lambda part: len(part.get("variants") or [])  # noqa: E731
    return {"reference_images": len(generated), "mesh_generations": len(generated),
            "retextures": sum(count(p) for p in built) + sum(max(count(p) - 1, 0) for p in generated)}


def summary(doc: dict, parts: dict) -> dict:
    by_route = {route: sorted(i for i, p in parts.items() if p.get("route") == route) for route in ROUTES}
    notes = []
    if len(by_route["model"]) == 1 and not by_route["instance"]:
        notes.append("one modelled part and none instanced: if {!r} is a whole structure, split it into its "
                     "pieces by material (poles, covers, tops), each its own part".format(by_route["model"][0]))
    return {"name": doc.get("name"), "parts": len(parts), "masters": by_route, "notes": notes,
            "variants": {i: [v.get("id") for v in p.get("variants", []) if isinstance(v, dict)]
                         for i, p in sorted(parts.items())},
            "jobs": jobs(parts), "slots": len(doc.get("slots") or [])}


# ---------------------------------------------------------------- placement

def shuffled(items: list, rng: random.Random) -> list:
    """A seeded shuffle that depends only on rng.random(), so it is stable across Python versions."""
    items = list(items)
    for index in range(len(items) - 1, 0, -1):
        other = int(rng.random() * (index + 1))
        items[index], items[other] = items[other], items[index]
    return items


class Variants:
    """Hands out each part's variants in a seeded order, so every variant is used before one repeats."""

    def __init__(self, parts: dict, seed: int):
        self.parts, self.seed, self.orders, self.used = parts, seed, {}, {}

    def next(self, part_id: str, allowed=None) -> str:
        key = (part_id, tuple(allowed) if allowed else None)
        if key not in self.orders:
            ids = [v["id"] for v in self.parts[part_id]["variants"] if not allowed or v["id"] in allowed]
            self.orders[key] = shuffled(ids, random.Random(f"{self.seed}:{part_id}:{allowed}"))
            self.used[key] = 0
        order = self.orders[key]
        chosen = order[self.used[key] % len(order)]
        self.used[key] += 1
        return chosen


def sequence(named: list, count: int, order: str, rng: random.Random) -> list:
    """Which part sits at each of `count` positions: contiguous runs, or the same shares mixed."""
    shares = [count // len(named) + (1 if index < count % len(named) else 0) for index in range(len(named))]
    run = [part for part, share in zip(named, shares) for _ in range(share)]
    return shuffled(run, rng) if order == "mixed" else run


def jitter(value: float, rng: random.Random) -> float:
    return (rng.random() * 2 - 1) * value


def place_slot(slot: dict, parts: dict, variants: Variants, seed: int) -> list[dict]:
    rng = random.Random(f"{seed}:{slot['id']}")
    kind, turn = slot["kind"], float(slot.get("yaw_deg", 0.0))
    wobble_deg, wobble_m = float(slot.get("jitter_deg", 0.0)), float(slot.get("jitter_m", 0.0))
    allowed = slot.get("variants")
    spots = []  # (part id, position, yaw)
    if kind == "single":
        spots.append((slot["part"], vector(slot["position"]), turn))
    elif kind == "stack":
        base = vector(slot["base"])
        step = float(slot.get("step_m", parts[slot["part"]]["size_m"][2]))
        for index in range(slot["count"]):
            spots.append((slot["part"], (base[0], base[1], base[2] + step * index), turn))
    elif kind == "row":
        start, end = vector(slot["start"]), vector(slot["end"])
        length = math.dist(start, end)
        count = slot["count"] if "count" in slot else max(int(length / slot["spacing_m"] + 1e-9), 1)
        # An instance faces -Y at yaw 0. Across the row: its front is square to the row. Along: it looks down the row.
        heading = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))
        turn += heading if slot.get("facing", "across") == "across" else heading + 90.0
        run = sequence(slot["parts"], count, slot.get("order", "blocks"), rng)
        for index, part_id in enumerate(run):
            t = (index + 0.5) / count
            spots.append((part_id, tuple(a + (b - a) * t for a, b in zip(start, end)), turn))
    else:  # grid
        origin, across, back = (vector(slot[key]) for key in ("origin", "across", "back"))
        columns, rows = slot["columns"], slot["rows"]
        turn += math.degrees(math.atan2(across[1], across[0]))
        run = sequence(slot["parts"], columns * rows, slot.get("order", "blocks"), rng)
        for index, part_id in enumerate(run):
            u, v = (index % columns + 0.5) / columns, (index // columns + 0.5) / rows
            spots.append((part_id, tuple(o + a * u + b * v for o, a, b in zip(origin, across, back)), turn))
    out = []
    for number, (part_id, position, yaw) in enumerate(spots, 1):
        moved = (position[0] + jitter(wobble_m, rng), position[1] + jitter(wobble_m, rng), position[2])
        out.append({"id": f"{slot['id']}-{number:03d}", "slot": slot["id"], "part": part_id,
                    "variant": variants.next(part_id, allowed),
                    "position": [round(c, 4) for c in moved],
                    "yaw_deg": round((yaw + jitter(wobble_deg, rng)) % 360.0, 2)})
    return out


def placements(doc: dict, parts: dict) -> tuple[dict, list[str]]:
    seed = doc.get("seed", 0)
    slots = list(doc.get("slots") or [])
    problems, notes = [], []
    if not whole(seed, 0):
        return {}, ["seed must be a whole number of zero or more"]
    placed = {part for slot in slots for part in slot_parts(slot)}
    for part_id, part in sorted(parts.items()):
        if part_id in placed:
            continue
        if part.get("route") == "model":
            slots.append({"id": part_id, "kind": "single", "part": part_id, "position": [0.0, 0.0, 0.0]})
            notes.append(f"part {part_id!r} has no slot: placed once at the origin")
        else:
            problems.append(f"part {part_id!r} is routed {part.get('route')} but no slot places it")
    if problems:
        return {}, problems
    variants = Variants(parts, seed)
    instances = [row for slot in slots for row in place_slot(slot, parts, variants, seed)]
    used = sorted({(row["part"], row["variant"]) for row in instances})
    unused = [f"{i}/{v['id']}" for i, p in sorted(parts.items()) for v in p["variants"] if (i, v["id"]) not in used]
    counts = {}
    for row in instances:
        counts[row["part"]] = counts.get(row["part"], 0) + 1
    for part_id, count in sorted(counts.items()):
        have = len(parts[part_id]["variants"])
        if count >= 12 and have < min(count // 8, doc.get("variant_cap", DEFAULT_VARIANT_CAP)):
            notes.append(f"part {part_id!r} has {count} instances and {have} variants: repeats will show; "
                         "add variants, about one for every six to eight instances")
    if unused:
        notes.append("variants with no instance (make them only if they are wanted): " + ", ".join(unused))
    masters = [{"part": part_id, "variant": variant, "route": parts[part_id]["route"],
                "anchor": parts[part_id].get("anchor", "bottom"), "label": parts[part_id].get("label"),
                "size_m": parts[part_id].get("size_m")} for part_id, variant in used]
    return {"schema": PLACEMENT_SCHEMA, "set_piece": doc.get("name"), "seed": seed, "units": "m", "up": "Z",
            "front": "-Y", "masters": masters, "instances": instances, "notes": notes}, []


# ---------------------------------------------------------------- commands

def load(path: str):
    doc = read_json(pathlib.Path(path))
    if doc is None:
        return 2, None, None
    if not isinstance(doc, dict):
        print("error: the parts list must be a JSON object", file=sys.stderr)
        return 1, None, None
    parts, problems = check_parts(doc)
    problems += check_slots(doc, parts)
    if problems:
        print(json.dumps({"problems": problems}, indent=2))
        return 1, None, None
    return 0, doc, parts


def cmd_check(args) -> int:
    code, doc, parts = load(args.set_piece)
    if code:
        return code
    print(json.dumps(dict(summary(doc, parts), problems=[]), indent=2))
    return 0


def cmd_place(args) -> int:
    code, doc, parts = load(args.set_piece)
    if code:
        return code
    out = pathlib.Path(args.out)
    if out.exists() and not args.force:
        existing = read_json(out)
        if not isinstance(existing, dict) or existing.get("schema") != PLACEMENT_SCHEMA:
            print(f"error: {out.as_posix()} exists and is not a placement list; choose another path", file=sys.stderr)
            return 2
        print(f"error: {out.as_posix()} exists; pass --force to replace it", file=sys.stderr)
        return 2
    result, problems = placements(doc, parts)
    if problems:
        print(json.dumps({"problems": problems}, indent=2))
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    per_part = {}
    for row in result["instances"]:
        per_part.setdefault(row["part"], {}).setdefault(row["variant"], 0)
        per_part[row["part"]][row["variant"]] += 1
    print(json.dumps({"out": out.as_posix(), "instances": len(result["instances"]),
                      "masters": len(result["masters"]), "per_part": per_part, "notes": result["notes"]}, indent=2))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check", help="validate the parts list and count what it asks for")
    p.add_argument("set_piece", help="set_piece.json")
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("place", help="expand the slots into placements.json")
    p.add_argument("set_piece", help="set_piece.json")
    p.add_argument("--out", required=True, help="placements.json")
    p.add_argument("--force", action="store_true", help="replace an existing placement list")
    p.set_defaults(func=cmd_place)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
