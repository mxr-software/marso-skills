#!/usr/bin/env python3
"""Crop a reference image and write a brief for each asset in an asset plan.

Usage:
    crop_objects.py <scene_graph.json> --manifest manifest.json --plan asset_plan.json
                    --out <dir> [--ids g001 a002 ...] [--pad 0.15] [--shape square|context] [--mask-children]
                    [--exclude-parent] [--image-root dir] [--force] [--all-routes]

Writes <out>/<asset_id>/crop.png, search.png and brief.json for every asset routed to
`generate` (or every asset with --all-routes), plus <out>/index.json. Boxes in
the brief are in the crop's own pixel frame, origin top-left. The default crop is
square and unmasked, with the subject's box drawn on it as a red outline. Masking is
opt-in: --mask-children fills the subject's children with flat black, and
--exclude-parent blacks out the parent's box outside the subject's box. search.png is the
subject's own box with no margin and no marking, for a library search by image: a wider crop
finds its neighbours instead. Requires Pillow.

Exit codes: 0 crops written, 1 something was wrong with the inputs, the images
or the output location, 2 a JSON input could not be read.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

SCHEMA_OUT = "marso/reference-brief@1"
EVIDENCE_NOTE = (
    "This crop is evidence of what the object is, what it is made of and how the "
    "camera saw it. It is not a pose, framing or lighting to copy."
)
# The prompt is written for an image node that is shown the crop as a linked image named @crop.
# There is no negative prompt and no mask field, so every exclusion is an instruction in the text.
WHOLE_OBJECT = (
    "The visible side must match @crop and the unseen sides must be consistent with it. "
    "Do not copy the crop's framing, pose, lighting or background. Do not draw the red box."
)
RED = (255, 0, 0)
TOUCH_SHARE = 0.5     # share of a neighbour's box inside the subject's for it to count as touching
COVER_LIMIT = 8       # ... or a neighbour covering the subject, if no more than this many times its area
SEARCH_PAD = 0.02     # margin around the subject in search.png
SITS = {
    "inside": "it sits in",
    "on-top-of": "it sits on",
    "hanging-on": "it hangs on",
    "leaning-against": "it leans against",
    "attached-to": "it is fixed to",
    "under": "it is under",
}


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


def square_window(box, pad, width, height):
    """Keep the subject in a square; coordinates outside the image need neutral padding."""
    longest = max(box[2] - box[0], box[3] - box[1])
    side = max(1, longest + 2 * round(pad * longest))
    origins = []
    for start, end, extent in ((box[0], box[2], width), (box[1], box[3], height)):
        origin = round((start + end - side) / 2)
        if side <= extent:
            origin = min(max(origin, 0), extent - side)
        origins.append(origin)
    return (*origins, origins[0] + side, origins[1] + side)


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


def names(labels) -> str:
    """'the bowl', 'the bowl and the mat', 'the onions, the mat and the bowl'."""
    labels = [str(label) for label in labels if label]
    unique = list(dict.fromkeys(labels))
    items = [f"the {label}" if labels.count(label) == 1 or label.endswith("s") else f"the {label}s"
             for label in unique]
    if len(items) < 2:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def build_prompt(asset: dict, label: str, others: list[dict], truncated) -> str:
    lines = [f"Generate the {label} inside the red box in @crop, isolated, the whole object in full, upright, "
             "on a plain neutral background."]
    inferred = asset.get("inferred_whole") or {}
    if inferred.get("whole_description"):
        # Mostly hidden in every photograph: the crop shows a fragment, so the text carries the whole.
        lines.append(f"Most of it is hidden in @crop; only {inferred.get('visible') or 'part of it'} "
                     f"is visible. The whole object, inferred from context: "
                     f"{inferred['whole_description']} Match the visible part exactly and "
                     "complete the rest as described.")
    elif asset.get("description"):
        text = str(asset["description"]).strip().rstrip(".")
        lines.append(text[:1].upper() + text[1:] + ".")
    # A neighbour made as its own asset that sits against or inside the subject's box: a kettle's
    # power base, a lid on its pot. "Shares the frame" was too weak; one run's kettle came back with
    # its base attached. Name it, and say why, before anything else is excluded.
    separate = list(dict.fromkeys(o["label"] for o in others if o.get("separate_asset")))
    if separate:
        verb = "it is" if len(separate) == 1 else "each is"
        lines.append(f"Do not include {names(separate)}: {verb} made as a separate asset, even where it "
                     f"touches or joins the {label} in @crop.")
    kids = [o["label"] for o in others if o["role"] == "child"]
    if len(kids) == 1:
        lines.append(f"Leave out {names(kids)}: it rests on the {label} and is not part of it.")
    elif kids:
        lines.append(f"Leave out {names(kids)}: they rest on it and are not part of it.")
    parent = next((o for o in others if o["role"] == "parent"), None)
    if parent:
        sits = SITS.get(asset.get("relation"), "it rests on")
        lines.append(f"Only the {label}, not the {parent['label']} {sits}.")
    rest = [o["label"] for o in others if o["role"] in ("other", "sibling-instance") and not o.get("separate_asset")]
    if rest:
        lines.append(f"Leave out {names(rest)}: they only share the frame.")
    lines.append(f"Everything outside the red box is context, not part of the {label}.")
    if any(o["pixels"] == "blacked out" for o in others):
        lines.append(f"The black areas in @crop are removed objects, not part of the {label}.")
    lines.append(f"Real size: {size_text(asset.get('size_m'))}"
                 + (f" ({asset.get('size_basis')})." if asset.get("size_basis") else "."))
    if truncated:
        lines.append("@crop cuts it off at the image edge; complete the missing part.")
    lines.append("Centre the whole object prominently in a square image with a small clear margin "
                 "on every side; retain thin tips and handles without clipping them.")
    lines.append(WHOLE_OBJECT)
    return " ".join(lines)


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
    parser.add_argument("--shape", choices=("square", "context"), default="square",
                        help="square reference by default; context keeps the padded rectangle")
    parser.add_argument("--mask-children", action="store_true", help="black out the subject's children")
    parser.add_argument("--exclude-parent", action="store_true", help="black out the parent outside the subject's box")
    parser.add_argument("--image-root", help="folder that relative manifest paths are under")
    parser.add_argument("--all-routes", action="store_true", help="crop every asset, not only generate")
    parser.add_argument("--force", action="store_true", help="overwrite existing crops and briefs")
    args = parser.parse_args(argv)
    if not math.isfinite(args.pad) or not 0 <= args.pad <= 1:
        parser.error("--pad must be finite and between 0 and 1")

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
    # Every object some asset of the plan will make, so a crop can tell its subject which
    # neighbours are made on their own.
    planned = {m for a in plan["assets"] if a.get("route") == "generate" for m in a.get("members") or []}
    selected = []
    for asset in plan["assets"]:
        if plan.get("selection_mode") and asset.get("route") == "skip":
            continue
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
        subject_px = intersect(subject_px, (0, 0, width, height))
        if subject_px is None:
            problems.append(f"{asset_id}: subject box has no pixels inside the image")
            continue
        crop_px = (square_window(subject_px, args.pad, width, height) if args.shape == "square"
                   else padded(subject_px, args.pad, width, height))
        crop = Image.new("RGB", (crop_px[2] - crop_px[0], crop_px[3] - crop_px[1]), (128, 128, 128))
        visible = intersect(crop_px, (0, 0, width, height))
        crop.paste(source.crop(visible), (visible[0] - crop_px[0], visible[1] - crop_px[1]))
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
                elif role == "child" and args.mask_children:
                    draw.rectangle(shift(box, crop_px), fill=(0, 0, 0))
                    pixels = "blacked out"
                # Measured on the neighbour's whole box, not the part the crop clips: a table
                # clipped to a camera's crop is not "mostly inside" the camera.
                full = to_pixels(v["bbox"], width, height)
                overlap = intersect(subject_px, full)
                shared = ((overlap[2] - overlap[0]) * (overlap[3] - overlap[1])) if overlap else 0
                full_area = max(1, (full[2] - full[0]) * (full[3] - full[1]))
                subject_area = max(1, (subject_px[2] - subject_px[0]) * (subject_px[3] - subject_px[1]))
                # Either the neighbour sits mostly inside the subject (a power base under a kettle),
                # or it covers most of the subject without being far bigger (the kettle over its base).
                touching = role == "other" and gid in planned and (
                    shared >= TOUCH_SHARE * full_area or
                    (shared >= TOUCH_SHARE * subject_area and full_area <= COVER_LIMIT * subject_area))
                others.append({
                    "global_id": gid,
                    "label": node.get("label"),
                    "role": role,
                    "separate_asset": touching,
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
        # The subject's box as a red outline, drawn last so masking never hides it.
        stroke = max(2, round(max(crop.size) / 180))
        x0, y0, x1, y1 = subject_in_crop
        draw.rectangle((x0, y0, max(x0, x1 - 1), max(y0, y1 - 1)), outline=RED, width=stroke)
        crop.save(target / "crop.png")
        source.crop(padded(subject_px, SEARCH_PAD, width, height)).save(target / "search.png")

        label = asset.get("label") or subject_id
        inferred = asset.get("inferred_whole") or {}

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
                "shape": args.shape,
                "subject_source_size_px": [subject_px[2] - subject_px[0], subject_px[3] - subject_px[1]],
                "subject_long_side_fraction": round(max(subject_px[2] - subject_px[0], subject_px[3] - subject_px[1]) / max(crop.size), 4),
                "occluded": bool(view.get("occluded")),
                "truncated": view.get("truncated") or [],
            },
            "subject_box": subject_in_crop,
            "not_the_subject": others,
            "masking": {"children_masked": args.mask_children, "parent_masked": parent_masked},
            "marking": {"subject_box": "red outline", "stroke_px": stroke},
            "search_crop": (target / "search.png").as_posix(),
            "prompt": build_prompt(asset, label, others, view.get("truncated")),
            "evidence_note": EVIDENCE_NOTE,
            "flags": asset.get("flags") or [],
        }
        if asset.get("polygon_count"):
            brief["polygon_count"] = asset["polygon_count"]
        (target / "brief.json").write_text(json.dumps(brief, indent=2) + "\n", encoding="utf-8")
        index.append({
            "asset_id": asset_id,
            "global_id": subject_id,
            "label": label,
            "route": asset.get("route"),
            "crop": (target / "crop.png").as_posix(),
            "search_crop": (target / "search.png").as_posix(),
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
