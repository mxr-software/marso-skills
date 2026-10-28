#!/usr/bin/env python3
"""The verify round: one look per photograph at every merged object, crop beside name.

Detect agents look once, at whatever scale they were shown, and a name given at that scale is
often wrong: a candle called a dish, a jar's corner called a vinyl record. Matching works by
name, so every wrong name downstream becomes a duplicate object or an asset that does not
exist. One agent per photograph, shown each object as a numbered crop from the full photograph
with its box drawn, catches what a single tile pass cannot see: the crop is of the thing named.

    make_verify.py plan  --run <run>   draw the sheets, write each brief, print the agents
    make_verify.py apply --run <run>   apply verify/<image_id>.json to detections and structure

Each agent writes verify/<image_id>.json:

    {"image_id": "img004",
     "renames":  [{"n": 21, "label": "candle", "description": "...", "why": "..."}],
     "remove":   [{"n": 9,  "why": "the cut-off corner of a book, not identifiable"}],
     "same_as":  [{"n": 30, "as": 31, "why": "one box on the case, one on its lid"}],
     "reparent": [{"n": 12, "on": 8, "relation": "inside", "why": "the water is in the glass vase"}],
     "notes": ""}

`n` is the number on the sheet: the last digits of the object's local id. apply keeps the merged
files it changed as verify/<image_id>.before.json, so a run can be compared or undone.

Exit codes: 0 done, 1 done with problems listed, 2 an input could not be read.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REFERENCES = HERE.parent / "references"
sys.path.insert(0, str(HERE))
import merge_tiles as mt                    # noqa: E402  (clusters_of lives there, once)

TILE = 220            # each crop is drawn this many pixels on its longer side
CAPTION = 34          # room under each crop for its number and name
COLUMNS = 6
PER_SHEET = 30        # 6 x 5: large enough to read, few enough sheets to open
PAD = 0.3             # context around each box, as a share of the box


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def posix(path) -> str:
    return pathlib.Path(path).resolve().as_posix()


def number(local_id: str) -> int:
    return int(str(local_id).rsplit("-", 1)[-1])


def source_image(run: pathlib.Path, image_id: str) -> pathlib.Path | None:
    """The full-resolution photograph, wherever intake found it."""
    manifest = load(run / "manifest.json")
    state = {}
    if (run / "fast.json").exists():
        state = load(run / "fast.json")
    for row in manifest.get("images") or []:
        if row.get("image_id") != image_id:
            continue
        raw = pathlib.Path(str(row.get("path") or ""))
        candidates = [raw, pathlib.Path.cwd() / raw]
        if state.get("images_root"):
            candidates.append(pathlib.Path(state["images_root"]) / raw.name)
        for candidate in candidates:
            if candidate.exists():
                return candidate
    whole = run / "tiles" / image_id / "whole.jpg"     # downscaled, but better than nothing
    return whole if whole.exists() else None


def draw_sheets(objects: list[dict], photo: pathlib.Path, out_dir: pathlib.Path, image_id: str) -> list[str]:
    from PIL import Image, ImageDraw
    source = Image.open(photo).convert("RGB")
    width, height = source.size
    paths = []
    for start in range(0, len(objects), PER_SHEET):
        chunk = objects[start:start + PER_SHEET]
        rows = (len(chunk) + COLUMNS - 1) // COLUMNS
        sheet = Image.new("RGB", (COLUMNS * TILE, rows * (TILE + CAPTION)), (24, 24, 24))
        draw = ImageDraw.Draw(sheet)
        for i, obj in enumerate(chunk):
            x0, y0, x1, y1 = obj["bbox"]
            bw, bh = (x1 - x0) * width, (y1 - y0) * height
            pad = max(bw, bh) * PAD + 8
            left, top = max(0, x0 * width - pad), max(0, y0 * height - pad)
            right, bottom = min(width, x1 * width + pad), min(height, y1 * height + pad)
            crop = source.crop((int(left), int(top), int(right), int(bottom)))
            scale = TILE / max(crop.size)
            crop = crop.resize((max(1, round(crop.size[0] * scale)), max(1, round(crop.size[1] * scale))))
            ImageDraw.Draw(crop).rectangle(
                [(x0 * width - left) * scale, (y0 * height - top) * scale,
                 (x1 * width - left) * scale - 1, (y1 * height - top) * scale - 1],
                outline=(255, 40, 40), width=2)
            col, row = i % COLUMNS, i // COLUMNS
            ox, oy = col * TILE, row * (TILE + CAPTION)
            sheet.paste(crop, (ox + (TILE - crop.size[0]) // 2, oy + (TILE - crop.size[1]) // 2))
            draw.text((ox + 4, oy + TILE + 3), f"{number(obj['local_id'])}  {obj['label']}"[:34],
                      fill=(255, 255, 255))
            if obj.get("id_confidence") == "low":
                draw.text((ox + 4, oy + TILE + 17), "name uncertain", fill=(255, 190, 80))
        path = out_dir / f"{image_id}.sheet{start // PER_SHEET + 1}.jpg"
        sheet.save(path, quality=88)
        paths.append(posix(path))
    return paths


def brief(run: pathlib.Path, image_id: str, objects: list[dict], sheets: list[str],
          whole: str | None, out: str) -> str:
    by_id = {o["local_id"]: o for o in objects}
    rows = []
    for obj in objects:
        parent = by_id.get(obj.get("parent") or "", {}).get("label")
        bits = [f"**{number(obj['local_id'])}** {obj['label']}"]
        if parent:
            bits.append(f"on {parent}")
        if obj.get("occlusion") in ("partial", "heavy"):
            bits.append({"partial": "partly hidden", "heavy": "mostly hidden"}[obj["occlusion"]])
        if obj.get("id_confidence") == "low":
            bits.append("name uncertain")
        desc = str(obj.get("description") or "").strip()
        rows.append("- " + " | ".join(bits) + (f"\n  {desc[:140]}" if desc and desc != obj["label"] else ""))
    sheet_lines = "\n".join(f"- `{p}`" for p in sheets)
    return f"""Stage: verify, {image_id} — scene-decompose run `{run.name}`.

Read `{posix(REFERENCES / 'verify.md')}` and then work. That file and this message are everything you need.

The whole photograph: `{whole or 'not available'}`. Look at it first, for context.

Every object found in it, as a numbered crop from the full photograph with its box in red and its name underneath:
{sheet_lines}

The same objects, with what each was said to rest on:
{chr(10).join(rows)}

Write exactly one file: `{out}`, in the shape verify.md shows, and reply with one line: renames, removals, duplicates."""


def plan(run: pathlib.Path) -> int:
    out_dir = run / "verify"
    out_dir.mkdir(parents=True, exist_ok=True)
    agents, skipped, problems = [], [], []
    for det_path in sorted((run / "detections").glob("*.json")):
        image_id = det_path.stem
        target = out_dir / f"{image_id}.json"
        if target.exists():
            skipped.append(target.name)
            continue
        objects = load(det_path).get("objects") or []
        photo = source_image(run, image_id)
        if photo is None:
            problems.append(f"{image_id}: the photograph could not be found")
            continue
        try:
            sheets = draw_sheets(objects, photo, out_dir, image_id)
        except ImportError:
            print("error: Pillow is required (pip install Pillow)", file=sys.stderr)
            return 2
        whole = run / "tiles" / image_id / "whole.jpg"
        agents.append({"name": f"{image_id}-verify", "writes": posix(target), "sheets": sheets,
                       "prompt": brief(run, image_id, objects, sheets,
                                       posix(whole) if whole.exists() else None, posix(target))})
    print(json.dumps({"round": "verify", "agents": agents, "count": len(agents),
                      "skipped_because_done": skipped, "problems": problems}, indent=2, ensure_ascii=False))
    return 1 if problems else 0


def union(a: list, b: list) -> list:
    return [round(min(a[0], b[0]), 5), round(min(a[1], b[1]), 5),
            round(max(a[2], b[2]), 5), round(max(a[3], b[3]), 5)]


def overlaps(a: list, b: list) -> bool:
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def apply_one(run: pathlib.Path, image_id: str, decisions: dict) -> dict:
    det_path = run / "detections" / f"{image_id}.json"
    tree_path = run / "structure" / f"{image_id}.json"
    detections = load(det_path)
    objects = detections.get("objects") or []
    by_n = {number(o["local_id"]): o for o in objects}
    report = {"renamed": [], "removed": [], "joined": [], "reparented": [], "problems": []}

    def lookup(n, what):
        obj = by_n.get(n) if isinstance(n, int) else None
        if obj is None:
            report["problems"].append(f"{image_id}: {what} names number {n!r}, which is not on the sheet")
        return obj

    for row in decisions.get("renames") or []:
        obj = lookup(row.get("n"), "a rename")
        label = str(row.get("label") or "").strip()
        if obj is None or not label:
            continue
        report["renamed"].append([obj["local_id"], obj["label"], label])
        obj["verified"] = f"renamed from '{obj['label']}': {row.get('why') or 'no reason given'}"
        obj["label"] = label
        if str(row.get("description") or "").strip():
            obj["description"] = row["description"].strip()
        obj["id_confidence"] = row.get("id_confidence") if row.get("id_confidence") in ("high", "medium", "low") else "high"

    gone: dict[str, str | None] = {}       # local id -> where its children go
    for row in decisions.get("same_as") or []:
        obj, keep = lookup(row.get("n"), "a duplicate"), lookup(row.get("as"), "a duplicate's 'as'")
        if obj is None or keep is None or obj is keep or obj["local_id"] in gone or keep["local_id"] in gone:
            continue
        if overlaps(obj["bbox"], keep["bbox"]):
            keep["bbox"] = union(obj["bbox"], keep["bbox"])
        gone[obj["local_id"]] = keep["local_id"]
        report["joined"].append([obj["local_id"], keep["local_id"], row.get("why")])
    for row in decisions.get("remove") or []:
        obj = lookup(row.get("n"), "a removal")
        if obj is None or obj["local_id"] in gone:
            continue
        if obj.get("parent") is None:
            report["problems"].append(f"{image_id}: {obj['local_id']} is an anchor; not removed")
            continue
        gone[obj["local_id"]] = obj.get("parent")
        report["removed"].append([obj["local_id"], obj["label"], row.get("why")])

    def destination(local_id):
        seen = set()
        while local_id in gone and local_id not in seen:
            seen.add(local_id)
            local_id = gone[local_id]
        return local_id

    kept = [o for o in objects if o["local_id"] not in gone]
    by_id = {o["local_id"]: o for o in kept}
    for row in decisions.get("reparent") or []:
        obj, holder = lookup(row.get("n"), "a reparent"), lookup(row.get("on"), "a reparent's 'on'")
        if obj is None or holder is None or obj is holder:
            continue
        target = destination(holder["local_id"])
        if obj["local_id"] not in by_id or target not in by_id:
            continue
        walk, seen = target, set()               # never hang a thing under its own descendant
        while walk and walk not in seen:
            seen.add(walk)
            walk = by_id.get(walk, {}).get("parent")
        if obj["local_id"] in seen:
            report["problems"].append(f"{image_id}: {obj['local_id']} cannot rest on its own descendant {target}")
            continue
        relation = str(row.get("relation") or "on-top-of").strip()
        if relation not in mt.RELATIONS:
            relation = "on-top-of"
        report["reparented"].append([obj["local_id"], obj.get("parent"), target, row.get("why")])
        obj["parent"], obj["relation"] = target, relation
    for obj in kept:
        if obj.get("parent") in gone:
            obj["parent"] = destination(obj["parent"])
            if obj["parent"] is None:
                obj.pop("relation", None)

    if not (report["renamed"] or report["removed"] or report["joined"] or report["reparented"]):
        return report
    backup = run / "verify" / f"{image_id}.before.json"
    if not backup.exists():
        backup.write_text(json.dumps({"detections": detections, "structure": load(tree_path)},
                                     indent=2) + "\n", encoding="utf-8")
    detections["objects"] = kept
    detections["verify"] = {k: v for k, v in report.items() if k != "problems"}
    det_path.write_text(json.dumps(detections, indent=2) + "\n", encoding="utf-8")

    tree = load(tree_path)
    nodes = []
    for o in kept:
        node = {"local_id": o["local_id"], "label": o["label"], "parent": o.get("parent")}
        if o.get("parent"):
            node["relation"] = o.get("relation") or "on-top-of"
        nodes.append(node)
    tree.update({"anchors": sorted(n["local_id"] for n in nodes if not n["parent"]), "nodes": nodes,
                 "clusters": mt.clusters_of(kept, image_id)})
    tree_path.write_text(json.dumps(tree, indent=2) + "\n", encoding="utf-8")
    return report


def apply(run: pathlib.Path) -> int:
    summary, problems = {}, []
    for path in sorted((run / "verify").glob("img*.json")):
        if path.name.endswith(".before.json"):
            continue
        image_id = path.stem
        if not (run / "detections" / f"{image_id}.json").exists():
            problems.append(f"{path.name}: no detections file for {image_id}")
            continue
        try:
            decisions = load(path)
        except (OSError, ValueError) as exc:
            problems.append(f"{path.name}: unreadable: {exc}")
            continue
        report = apply_one(run, image_id, decisions)
        problems += report.pop("problems")
        summary[image_id] = {k: len(v) for k, v in report.items()} | {"details": report}
    missing = [p.stem for p in sorted((run / "detections").glob("*.json"))
               if not (run / "verify" / f"{p.stem}.json").exists()]
    print(json.dumps({"applied": summary, "not_verified": missing, "problems": problems},
                     indent=2, ensure_ascii=False))
    return 1 if (problems or missing) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("step", choices=("plan", "apply"))
    parser.add_argument("--run", required=True, help="the run folder")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    run = pathlib.Path(args.run)
    if not (run / "detections").is_dir() or not (run / "manifest.json").exists():
        print(f"error: {run.as_posix()} has no detections yet; run fast.py detect first", file=sys.stderr)
        return 2
    try:
        return plan(run) if args.step == "plan" else apply(run)
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: could not read the run folder's files: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
