#!/usr/bin/env python3
"""Crop a reference image and write a brief for each asset in an asset plan.

Usage:
    crop_objects.py <scene_graph.json> --manifest manifest.json --plan asset_plan.json
                    --out <dir> [--ids g001 a002 ...] [--pad 0.15] [--keep-children]
                    [--exclude-parent] [--image-root dir] [--force] [--all-routes]

Writes <out>/<asset_id>/crop.png and brief.json for every asset routed to
`generate` (or every asset with --all-routes), plus <out>/index.json. Boxes in
the brief are in the crop's own pixel frame, origin top-left. Children of the
subject are filled with flat black unless --keep-children; --exclude-parent also
blacks out the parent's box outside the subject's box. Requires Pillow.

Exit codes: 0 crops written, 1 something was wrong with the inputs, the images
or the output location, 2 a JSON input could not be read.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

SCHEMA_OUT = "marso/reference-brief@1"
EVIDENCE_NOTE = (
    "This crop is evidence of what the object is, what it is made of and how the "
    "camera saw it. It is not a pose, framing or lighting to copy."
)
WHOLE_OBJECT = (
    "Produce the complete object on its own, upright, at the stated real size, on a "
    "neutral background. The visible side must match the crop; unseen sides must be "
    "consistent with it. Nothing blacked out and nothing listed as not the subject "
    "belongs in the result."
)


def read_json(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"error: no such file: {path.as_posix()}", file=sys.stderr)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"error: {path.as_posix()} is not valid JSON: {exc}", file=sys.stderr)
    except OSError as exc:
        print(f"error: cannot read {path.as_posix()}: {exc}", file=sys.stderr)
    return None


def to_pixels(bbox, width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return (
        int(round(min(x0, x1) * width)),
        int(round(min(y0, y1) * height)),
        int(round(max(x0, x1) * width)),
        int(round(max(y0, y1) * height)),
    )


def padded(box, pad: float, width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    margin = int(round(pad * max(x1 - x0, y1 - y0)))
    return (max(0, x0 - margin), max(0, y0 - margin), min(width, x1 + margin), min(height, y1 + margin))


def intersect(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return None
    return (x0, y0, x1, y1)


def shift(box, origin) -> list[int]:
    return [box[0] - origin[0], box[1] - origin[1], box[2] - origin[0], box[3] - origin[1]]


def size_text(size_m) -> str:
    if isinstance(size_m, (int, float)) and not isinstance(size_m, bool) and size_m > 0:
        return f"about {size_m:g} m across its largest dimension"
    if isinstance(size_m, dict):
        parts = [f"{k} {v} m" for k, v in size_m.items() if isinstance(v, (int, float))]
        return ", ".join(parts) if parts else "size unknown"
    if isinstance(size_m, (list, tuple)) and size_m:
        return " x ".join(f"{v} m" for v in size_m if isinstance(v, (int, float)))
    return "size unknown"


def descendants(gid: str, children: dict[str, list[str]]) -> set[str]:
    out, stack = set(), list(children.get(gid, []))
    while stack:
        cur = stack.pop()
        if cur in out:
            continue
        out.add(cur)
        stack.extend(children.get(cur, []))
    return out


def resolve_image(entry: dict, manifest_path: pathlib.Path, image_root: pathlib.Path | None) -> pathlib.Path:
    raw = pathlib.Path(str(entry.get("path") or ""))
    if raw.is_absolute():
        return raw
    if image_root is not None:
        return image_root / raw
    # The decompose run writes paths relative to the project folder it ran from; older or
    # hand-made manifests are relative to themselves. Try the working folder first.
    for base in (pathlib.Path.cwd(), manifest_path.parent):
        if (base / raw).exists():
            return base / raw
    return manifest_path.parent / raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("graph", help="scene_graph.json")
    parser.add_argument("--manifest", required=True, help="manifest.json listing the images")
    parser.add_argument("--plan", required=True, help="asset_plan.json from plan_assets.py")
    parser.add_argument("--out", required=True, help="folder to write crops and briefs into")
    parser.add_argument("--ids", nargs="*", default=[], help="asset_ids or global_ids to crop; default all")
    parser.add_argument("--pad", type=float, default=0.15, help="margin as a fraction of the box's longer side")
    parser.add_argument("--keep-children", action="store_true", help="do not black out the subject's children")
    parser.add_argument("--exclude-parent", action="store_true", help="black out the parent outside the subject's box")
    parser.add_argument("--image-root", help="folder that relative manifest paths are under")
    parser.add_argument("--all-routes", action="store_true", help="crop every asset, not only generate")
    parser.add_argument("--force", action="store_true", help="overwrite existing crops and briefs")
    args = parser.parse_args(argv)

    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("error: Pillow is required (pip install Pillow)", file=sys.stderr)
        return 1

    graph = read_json(pathlib.Path(args.graph))
    manifest_path = pathlib.Path(args.manifest)
    manifest = read_json(manifest_path)
    plan = read_json(pathlib.Path(args.plan))
    if graph is None or manifest is None or plan is None:
        return 2
    if not isinstance(plan, dict) or not isinstance(plan.get("assets"), list):
        print("error: the plan has no assets list", file=sys.stderr)
        return 1

    nodes = {n["global_id"]: n for n in graph.get("nodes") or [] if n.get("global_id")}
    images = {i["image_id"]: i for i in manifest.get("images") or [] if i.get("image_id")}
    children: dict[str, list[str]] = {}
    for gid, node in nodes.items():
        if node.get("parent") in nodes:
            children.setdefault(node["parent"], []).append(gid)

    wanted = set(args.ids)
    selected = []
    for asset in plan["assets"]:
        if wanted:
            if asset.get("asset_id") in wanted or wanted & set(asset.get("members") or []):
                selected.append(asset)
        elif args.all_routes or asset.get("route") == "generate":
            selected.append(asset)
    if not selected:
        print("error: no assets matched; check --ids or the plan's routes", file=sys.stderr)
        return 1

    out_dir = pathlib.Path(args.out)
    image_root = pathlib.Path(args.image_root) if args.image_root else None
    opened: dict[str, object] = {}
    index = []
    problems = []
    for asset in selected:
        asset_id = asset.get("asset_id")
        view = asset.get("best_view") or {}
        image_id = view.get("image_id")
        subject_id = asset.get("global_id")
        entry = images.get(image_id)
        if not entry or not view.get("bbox"):
            problems.append(f"{asset_id}: no best view or the image {image_id!r} is not in the manifest")
            continue
        path = resolve_image(entry, manifest_path, image_root)
        if image_id not in opened:
            try:
                opened[image_id] = Image.open(path).convert("RGB")
            except (FileNotFoundError, OSError) as exc:
                problems.append(f"{asset_id}: cannot open {path.as_posix()}: {exc}")
                continue
        source = opened[image_id]
        width, height = source.size
        if entry.get("width") and entry.get("height") and (entry["width"], entry["height"]) != (width, height):
            problems.append(f"{asset_id}: manifest says {entry['width']}x{entry['height']} but "
                            f"{path.name} is {width}x{height}; using the file")

        target = out_dir / str(asset_id)
        if target.exists() and not args.force and any(target.iterdir()):
            problems.append(f"{target.as_posix()} exists; pass --force to overwrite")
            continue

        subject_px = to_pixels(view["bbox"], width, height)
        crop_px = padded(subject_px, args.pad, width, height)
        crop = source.crop(crop_px)
        draw = ImageDraw.Draw(crop)
        subject_in_crop = shift(subject_px, crop_px)

        members = set(asset.get("members") or [subject_id])
        kids = set()
        for member in members:
            kids |= descendants(member, children)
        parent_id = nodes.get(subject_id, {}).get("parent")

        others = []
        for gid, node in nodes.items():
            if gid == subject_id:
                continue
            if node.get("parent") is None and gid != parent_id:
                continue  # anchors span every crop; list one only when it holds the subject
            for v in node.get("views") or []:
                if v.get("image_id") != image_id or not v.get("bbox"):
                    continue
                box = intersect(to_pixels(v["bbox"], width, height), crop_px)
                if box is None:
                    continue
                if gid in kids:
                    role, sits = "child", "resting on this object"
                elif gid == parent_id:
                    role, sits = "parent", "this object rests on it"
                elif gid in members:
                    role, sits = "sibling-instance", "shares the frame, unrelated"
                else:
                    role, sits = "other", "shares the frame, unrelated"
                relation = None
                if role == "child":
                    relation = node.get("relation")
                elif role == "parent":
                    relation = nodes[subject_id].get("relation")
                pixels = "still visible"
                # A child whose box covers the subject (a kettle standing on its base) cannot be
                # blacked out without blacking out the subject: leave it and say so.
                covers = role == "child" and intersect(subject_px, box) is not None and (
                    (min(box[2], subject_px[2]) - max(box[0], subject_px[0])) *
                    (min(box[3], subject_px[3]) - max(box[1], subject_px[1]))
                    >= 0.6 * (subject_px[2] - subject_px[0]) * (subject_px[3] - subject_px[1]))
                if covers:
                    pixels = "still visible: it covers most of the subject, so it was not masked"
                elif role == "child" and not args.keep_children:
                    draw.rectangle(shift(box, crop_px), fill=(0, 0, 0))
                    pixels = "blacked out"
                others.append({
                    "global_id": gid,
                    "label": node.get("label"),
                    "role": role,
                    "relation": relation,
                    "sits": sits,
                    "pixels": pixels,
                    "box": shift(box, crop_px),
                })
                break

        parent_masked = False
        if args.exclude_parent and parent_id in nodes:
            for entry_other in others:
                if entry_other["role"] != "parent":
                    continue
                keep = crop.crop(tuple(subject_in_crop))
                draw.rectangle(entry_other["box"], fill=(0, 0, 0))
                crop.paste(keep, (subject_in_crop[0], subject_in_crop[1]))
                entry_other["pixels"] = "blacked out"
                parent_masked = True

        target.mkdir(parents=True, exist_ok=True)
        crop.save(target / "crop.png")

        label = asset.get("label") or subject_id
        lines = [f"Subject: {label}, {size_text(asset.get('size_m'))}"
                 + (f" ({asset.get('size_basis')})." if asset.get("size_basis") else ".")]
        inferred = asset.get("inferred_whole") or {}
        if inferred.get("whole_description"):
            # Mostly hidden in every photograph: the crop shows a fragment, so the text leads.
            lines.append(f"Most of it is hidden in the crop; only {inferred.get('visible') or 'part of it'} "
                         f"is visible. The whole object, inferred from context: "
                         f"{inferred['whole_description']} Match the visible part exactly and "
                         "complete the rest as described.")
        elif asset.get("description"):
            lines.append(str(asset["description"]))
        for o in others:
            lines.append(f"Not the subject: {o['label']} ({o['sits']}; {o['pixels']}).")
        if view.get("truncated"):
            lines.append("The subject runs off the image edge in this view; the crop is partial.")
        lines.append(WHOLE_OBJECT)

        brief = {
            "schema": SCHEMA_OUT,
            "asset_id": asset_id,
            "global_id": subject_id,
            "members": sorted(members),
            "route": asset.get("route"),
            "subject": {
                "label": label,
                "description": asset.get("description"),
                "category": asset.get("category"),
                "size_m": asset.get("size_m"),
                "size_basis": asset.get("size_basis"),
                "size_confidence": asset.get("size_confidence"),
                "parent": parent_id,
                "relation": asset.get("relation"),
                "occlusion": asset.get("occlusion", "none"),
                "inferred_whole": inferred or None,
            },
            "view": {
                "image_id": image_id,
                "local_id": view.get("local_id"),
                "source_path": path.as_posix(),
                "crop_px": list(crop_px),
                "crop_size": [crop_px[2] - crop_px[0], crop_px[3] - crop_px[1]],
                "pad": args.pad,
                "occluded": bool(view.get("occluded")),
                "truncated": view.get("truncated") or [],
            },
            "subject_box": subject_in_crop,
            "not_the_subject": others,
            "masking": {"children_masked": not args.keep_children, "parent_masked": parent_masked},
            "prompt": " ".join(lines),
            "evidence_note": EVIDENCE_NOTE,
            "flags": asset.get("flags") or [],
        }
        (target / "brief.json").write_text(json.dumps(brief, indent=2) + "\n", encoding="utf-8")
        index.append({
            "asset_id": asset_id,
            "global_id": subject_id,
            "label": label,
            "route": asset.get("route"),
            "crop": (target / "crop.png").as_posix(),
            "brief": (target / "brief.json").as_posix(),
            "image_id": image_id,
            "not_the_subject": len(others),
        })

    out_dir.mkdir(parents=True, exist_ok=True)
    # Crops are often made a few at a time with different masking: keep earlier entries.
    earlier = read_json(out_dir / "index.json") if (out_dir / "index.json").exists() else None
    done = {row["asset_id"] for row in index}
    kept = [row for row in (earlier or {}).get("assets") or [] if row.get("asset_id") not in done]
    index_doc = {"schema": "marso/reference-index@1", "assets": kept + index, "problems": problems}
    (out_dir / "index.json").write_text(json.dumps(index_doc, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": out_dir.as_posix(), "written": len(index), "problems": problems}, indent=2))
    if not index:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
