#!/usr/bin/env python3
"""Turn a set piece's placement list into Unreal actor transforms, and check the placed actors against them.

Usage:
    to_unreal.py plan <placements.json> --meshes <meshes.json> --out <unreal_placements.json>
                      [--at X Y Z] [--yaw DEG] [--folder FOLDER] [--prefix PREFIX] [--force]
    to_unreal.py check <unreal_placements.json> --actors <actors.json> [--tolerance-m 0.005]

The placement list is in the set piece's own frame: metres, Z up, right-handed, front -Y, a turn anticlockwise
about Z seen from above. Unreal's frame is X forward, Y right, Z up: left-handed. Going from one to the other
negates Y and reverses the direction of every turn; nothing is mirrored and no scale is negative. The Marso
Unreal plugin imports an asset in this same relation to the Blender add-on's import of it, so a piece reads the
same in both applications.

meshes.json gives, for each "part/variant" of the placement list's masters, the Unreal mesh and look that stand
for it and the mesh's bounds as measured on an actor at the origin with no turn and scale 1:

    {"tee/red": {"asset_path": "/Game/Marso/.../SM_Tee", "look": "Red",
                 "bounds_m": {"min": [x, y, z], "max": [x, y, z]}}}

An entry may also give "asset_yaw_deg" when the master in the placement list has none.

`plan` writes one row per instance: label, mesh, look, Outliner folder, location (m), rotation_deg [x, y, z] and
a uniform scale that brings the mesh's height to the master's size_m. Every label starts with the plan's prefix.
`--at` and `--yaw` put the whole piece at a point in the level, in Unreal's frame. `check` compares a saved
`list_actors` result with the rows, and lists actors in the plan's folder with its prefix that the plan dropped.

Standard library only. Exit codes: 0 done or passed, 1 problems (each is printed), 2 a file could not be read
or would be overwritten.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import sys

PLACEMENT_SCHEMA = "marso/set-piece-placements@1"
SCHEMA = "marso/set-piece-unreal@1"


def read_json(path):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as ex:
        print(f"error: cannot read {pathlib.Path(path).as_posix()}: {ex}", file=sys.stderr)
        return None


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def vector(value, length=3):
    if isinstance(value, (list, tuple)) and len(value) == length and all(number(v) for v in value):
        return [float(v) for v in value]
    return None


def turn(x, y, degrees):
    """(x, y) turned by degrees with the standard rotation matrix, which is how both frames apply a yaw."""
    a = math.radians(degrees)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def wrap(degrees):
    """An angle in (-180, 180]."""
    value = math.fmod(degrees, 360.0)
    if value <= -180.0:
        value += 360.0
    elif value > 180.0:
        value -= 360.0
    return 0.0 if abs(value) < 5e-7 else value


def slug(name):
    return re.sub(r"[^A-Za-z0-9]+", "_", str(name or "Set piece")).strip("_") or "Set_piece"


def frame_problems(doc):
    problems = []
    if doc.get("schema") != PLACEMENT_SCHEMA:
        problems.append(f"not a placement list: schema must be {PLACEMENT_SCHEMA!r}")
    for key, want in (("units", "m"), ("up", "Z"), ("front", "-Y"), ("handedness", "right")):
        if key not in doc:
            problems.append(f"the placement list states no {key}; write it again with marso-set-piece's place")
        elif doc[key] != want:
            problems.append(f"{key} is {doc[key]!r}; this script converts from {want!r} only")
    if not doc.get("instances"):
        problems.append("the placement list has no instances")
    return problems


def actor_row(instance, master, mesh, piece):
    """One instance's actor in Unreal's frame. The anchor (centre of the base, or of the top for a hanging part)
    is measured on the mesh's own bounds, so a pivot that is off-centre does not move the piece."""
    low, high = mesh["bounds_m"]["min"], mesh["bounds_m"]["max"]
    height = high[2] - low[2]
    size = master.get("size_m")
    scale = size[2] / height if vector(size) and height > 0 else 1.0
    anchor = [(low[0] + high[0]) / 2, (low[1] + high[1]) / 2, high[2] if master.get("anchor") == "top" else low[2]]
    asset_yaw = mesh.get("asset_yaw_deg", master.get("asset_yaw_deg", 0.0))
    yaw = -(float(instance["yaw_deg"]) + float(asset_yaw))  # anticlockwise in the plan is the other way in Unreal
    px, py, pz = instance["position"]
    ox, oy = turn(anchor[0] * scale, anchor[1] * scale, yaw)
    x, y, z = px - ox, -py - oy, pz - anchor[2] * scale
    x, y = turn(x, y, piece["yaw"])
    return {"label": piece["prefix"] + instance["id"], "instance": instance["id"], "slot": instance.get("slot"),
            "master": f"{instance['part']}/{instance['variant']}", "asset_path": mesh["asset_path"],
            "look": mesh.get("look") or "Original", "folder": piece["folder"],
            "location": [round(x + piece["at"][0], 4), round(y + piece["at"][1], 4), round(z + piece["at"][2], 4)],
            "rotation_deg": [0.0, 0.0, round(wrap(yaw + piece["yaw"]), 3)], "scale": round(scale, 5)}


def cmd_plan(args) -> int:
    doc = read_json(args.placements)
    meshes = read_json(args.meshes)
    if doc is None or meshes is None:
        return 2
    if not isinstance(doc, dict) or not isinstance(meshes, dict):
        print(json.dumps({"problems": ["both files must be JSON objects"]}, indent=2))
        return 1
    problems = frame_problems(doc)
    masters = {f"{m.get('part')}/{m.get('variant')}": m for m in doc.get("masters") or [] if isinstance(m, dict)}
    for key in sorted({f"{i.get('part')}/{i.get('variant')}" for i in doc.get("instances") or []}):
        mesh = meshes.get(key)
        if key not in masters:
            problems.append(f"{key}: an instance names it but the placement list's masters do not")
        if not isinstance(mesh, dict):
            problems.append(f"{key}: no entry in {pathlib.Path(args.meshes).name}")
            continue
        if not str(mesh.get("asset_path") or "").startswith("/"):
            problems.append(f"{key}: asset_path must be a content path such as /Game/Marso/...")
        bounds = mesh.get("bounds_m") if isinstance(mesh.get("bounds_m"), dict) else {}
        low, high = vector(bounds.get("min")), vector(bounds.get("max"))
        if low is None or high is None or high[2] <= low[2]:
            problems.append(f"{key}: bounds_m needs min and max of three numbers, max above min")
        asset_yaw = mesh.get("asset_yaw_deg", (masters.get(key) or {}).get("asset_yaw_deg"))
        if not number(asset_yaw):
            problems.append(f"{key}: no asset_yaw_deg in the placement list or {pathlib.Path(args.meshes).name}")
        size = (masters.get(key) or {}).get("size_m")
        if size is not None and (vector(size) is None or min(vector(size)) <= 0):
            problems.append(f"{key}: size_m must be three positive numbers")
    for row in doc.get("instances") or []:
        if vector(row.get("position")) is None or not number(row.get("yaw_deg")):
            problems.append(f"instance {row.get('id')!r}: position and yaw_deg must be numbers")
    if problems:
        print(json.dumps({"problems": problems}, indent=2))
        return 1
    out = pathlib.Path(args.out)
    if out.exists():
        existing = read_json(out)
        if not isinstance(existing, dict) or existing.get("schema") != SCHEMA:
            print(f"error: {out.as_posix()} exists and is not an Unreal placement list; choose another path",
                  file=sys.stderr)
            return 2
        if not args.force:
            print(f"error: {out.as_posix()} exists; pass --force to replace it", file=sys.stderr)
            return 2
    name = doc.get("set_piece") or "Set piece"
    piece = {"at": args.at or [0.0, 0.0, 0.0], "yaw": args.yaw, "folder": args.folder or f"Set pieces/{name}",
             "prefix": args.prefix if args.prefix is not None else slug(name) + "_"}
    rows = [actor_row(i, masters[f"{i['part']}/{i['variant']}"], meshes[f"{i['part']}/{i['variant']}"], piece)
            for i in doc["instances"]]
    labels = [r["label"] for r in rows]
    if len(set(labels)) != len(labels):
        print(json.dumps({"problems": ["two instances share a label; give each instance a unique id"]}, indent=2))
        return 1
    result = {"schema": SCHEMA, "set_piece": name, "placements": pathlib.Path(args.placements).name,
              "frame": "Unreal: metres, X forward, Y right, Z up (left-handed); from the plan's frame by negating Y "
                       "and reversing turns", "at": piece["at"], "yaw_deg": piece["yaw"], "folder": piece["folder"],
              "prefix": piece["prefix"], "actors": rows}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    looks = {}
    for row in rows:
        looks.setdefault(row["asset_path"], set()).add(row["look"])
    print(json.dumps({"out": out.as_posix(), "actors": len(rows), "meshes": len(looks),
                      "looks": {path: sorted(names) for path, names in sorted(looks.items())},
                      "folder": piece["folder"], "prefix": piece["prefix"]}, indent=2))
    return 0


def actor_rows(listing):
    if isinstance(listing, dict):
        for key in ("result", "actors"):
            if key in listing:
                return actor_rows(listing[key])
    return [row for row in listing if isinstance(row, dict)] if isinstance(listing, list) else []


def cmd_check(args) -> int:
    plan, listing = read_json(args.plan), read_json(args.actors)
    if plan is None or listing is None:
        return 2
    if not isinstance(plan, dict) or plan.get("schema") != SCHEMA:
        print(json.dumps({"passed": False, "problems": [f"not an Unreal placement list ({SCHEMA})"]}, indent=2))
        return 1
    actors = actor_rows(listing)
    if not actors or not plan.get("actors"):
        print(json.dumps({"passed": False, "problems": ["the actor listing or the plan is empty or unreadable"]},
                         indent=2))
        return 1
    by_label = {}
    for actor in actors:
        by_label.setdefault(str(actor.get("name") or actor.get("label") or ""), []).append(actor)
    problems, placed = [], 0
    for row in plan.get("actors") or []:
        found = by_label.get(row["label"], [])
        if len(found) != 1:
            problems.append(f"{row['label']}: {len(found)} actors with this label (need 1)")
            continue
        actor = found[0]
        location, rotation = vector(actor.get("location")), vector(actor.get("rotation_deg"))
        if location is None or math.dist(location, row["location"]) > args.tolerance_m:
            problems.append(f"{row['label']}: at {location}, planned {row['location']}")
            continue
        if rotation is None or abs(wrap(rotation[2] - row["rotation_deg"][2])) > 0.5 or \
                abs(rotation[0]) > 0.5 or abs(rotation[1]) > 0.5:
            problems.append(f"{row['label']}: turned {rotation}, planned {row['rotation_deg']}")
            continue
        scale = actor.get("scale")
        scales = [scale] * 3 if number(scale) else (vector(scale) or [None])
        if any(s is None or abs(s - row["scale"]) > 0.001 for s in scales):
            problems.append(f"{row['label']}: scale {scale}, planned {row['scale']}")
            continue
        mesh = str(actor.get("asset_path") or "")
        if mesh.split(".")[0] != row["asset_path"].split(".")[0]:
            problems.append(f"{row['label']}: shows {mesh or 'no mesh'}, planned {row['asset_path']}; "
                            "delete it and place it again")
            continue
        placed += 1
    planned = {row["label"] for row in plan.get("actors") or []}
    folder, prefix = plan.get("folder"), plan.get("prefix") or ""
    extra = sorted(label for label, rows in by_label.items()
                   if label not in planned and label.startswith(prefix)
                   and any(str(r.get("folder") or "") == folder for r in rows))
    if extra:
        problems.append(f"{len(extra)} actors in {folder} are not in the plan: {', '.join(extra[:8])}")
    print(json.dumps({"passed": not problems, "placed": placed, "planned": len(planned),
                      "problems": problems[:30]}, indent=2))
    return 0 if not problems else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan", help="turn the placement list into Unreal actor rows")
    p.add_argument("placements")
    p.add_argument("--meshes", required=True, help="meshes.json: mesh, look and bounds for each part/variant")
    p.add_argument("--out", required=True)
    p.add_argument("--at", type=float, nargs=3, metavar=("X", "Y", "Z"), help="where the piece's origin goes (m)")
    p.add_argument("--yaw", type=float, default=0.0, help="Unreal yaw of the whole piece, degrees")
    p.add_argument("--folder", help="Outliner folder (default 'Set pieces/<name>')")
    p.add_argument("--prefix", help="label prefix (default the set piece name and an underscore)")
    p.add_argument("--force", action="store_true", help="replace an Unreal placement list this script wrote")
    p.set_defaults(func=cmd_plan)
    p = sub.add_parser("check", help="compare a saved list_actors result with the rows")
    p.add_argument("plan")
    p.add_argument("--actors", required=True, help="a list_actors result saved as JSON")
    p.add_argument("--tolerance-m", type=float, default=0.005)
    p.set_defaults(func=cmd_check)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
