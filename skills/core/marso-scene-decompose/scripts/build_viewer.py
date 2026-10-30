#!/usr/bin/env python3
"""Build a self-contained viewer for a finished scene graph.

Fills the template in this skill's assets/ with the run's data and writes one
HTML file. By default it points at the source images where they sit on disk, so
the viewer must stay beside them; --embed puts the images inside the file as
data URIs instead, which makes it portable at the cost of size.

Prints a JSON summary to stdout. Exit codes: 0 written, 1 the inputs were
unusable, 2 a file could not be read.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "viewer_template.html"
EMBED_BUDGET = 14 * 1024 * 1024  # the page must stay openable; leave room for the rest


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def optional(raw: str | None):
    if not raw:
        return None
    return load(pathlib.Path(raw))


def image_src(path: pathlib.Path, out_dir: pathlib.Path, embed: bool) -> tuple[str, int]:
    """Either a relative href, or a data URI. Returns the src and its cost in bytes."""
    if embed:
        data = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}", len(data) * 4 // 3
    try:
        rel = os.path.relpath(path, out_dir)
    except ValueError:                      # a different drive on Windows
        rel = path.as_uri()
    return rel.replace(os.sep, "/"), 0


def build(graph: dict, manifest: dict | None, scores: dict | None, confusion: dict | None,
          ontology: dict | None, out_dir: pathlib.Path, embed: bool,
          image_root: pathlib.Path | None, choices: dict | None = None,
          asset_record: dict | None = None) -> tuple[str, list[str], list[str]]:
    problems: list[str] = []
    warnings: list[str] = []
    key = hashlib.sha256(json.dumps(graph, sort_keys=True, ensure_ascii=True,
                                   separators=(",", ":")).encode()).hexdigest()
    if choices is not None and (not isinstance(choices, dict) or choices.get("schema") != "marso/scene-choices@1"
                                or choices.get("graph_key") != key):
        problems.append("choices do not belong to this graph revision")
    if asset_record is not None and (not isinstance(asset_record, dict) or asset_record.get("graph_key") != key):
        problems.append("asset record does not belong to this graph revision; initialise it from this plan")
    if problems:
        return "", problems, warnings

    rows = {r.get("image_id"): r for r in (manifest or {}).get("images") or []}
    images, cost = [], 0
    for image_id in graph.get("images") or []:
        row = rows.get(image_id)
        if row is None:
            problems.append(f"{image_id} is in the graph but not in the manifest")
            continue
        raw = pathlib.Path(row.get("path", ""))
        path = (image_root / raw.name) if image_root else raw
        if not path.exists():
            problems.append(f"{image_id}: no image at {path.as_posix()}")
            continue
        src, bytes_added = image_src(path, out_dir, embed)
        cost += bytes_added
        images.append({
            "image_id": image_id, "src": src,
            "width": row.get("width") or 1, "height": row.get("height") or 1,
        })
    if embed and cost > EMBED_BUDGET:
        warnings.append(
            f"embedded images come to about {cost // (1024 * 1024)} MB; the page may be slow "
            "to open. Drop --embed and keep the viewer beside the photographs instead"
        )

    data = {
        "nodes": graph.get("nodes") or [],
        "clusters": graph.get("clusters") or [],
        "areas": graph.get("areas") or [],
        "identity_groups": graph.get("identity_groups") or [],
        "parent_conflicts": graph.get("parent_conflicts") or [],
        "images": images,
        "view_scores": (scores or {}).get("objects") or [],
        "confusion": confusion or {},
        "ontology": (ontology or {}).get("categories") or [],
        "distinct_objects": (ontology or {}).get("total_objects"),
        "graph_key": key,
        "choices": choices,
        "library_candidates": {},
    }
    for asset in (asset_record or {}).get("assets") or []:
        candidates = []
        for candidate in (asset.get("library") or {}).get("candidates") or []:
            if not candidate.get("pbr_asset_id"):
                continue
            item = {k: candidate.get(k) for k in ("name", "verdict", "pbr_asset_id")}
            thumbnail = pathlib.Path(candidate.get("thumbnail_path") or "")
            if thumbnail.is_file():
                item["thumbnail_src"], _ = image_src(thumbnail, out_dir, embed)
            candidates.append(item)
        for gid in asset.get("members") or [asset.get("global_id")]:
            data["library_candidates"][gid] = candidates
    if data["distinct_objects"] is None:
        slack = sum(max(0, len(g.get("members") or []) - (g.get("distinct") or 0))
                    for g in data["identity_groups"])
        data["distinct_objects"] = len(data["nodes"]) - slack

    title = f"Scene graph · {len(data['nodes'])} objects · {len(images)} view" \
            f"{'' if len(images) == 1 else 's'}"
    data["title"] = title
    html = TEMPLATE.read_text(encoding="utf-8-sig")
    # Order matters: the data blob may itself contain the title placeholder's text.
    html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("<", "\\u003c"))
    html = html.replace("__TITLE__", title)
    return html, problems, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("graph", help="scene_graph.json")
    parser.add_argument("--manifest", required=True, help="manifest.json, for the image paths")
    parser.add_argument("--scores", help="view_scores.json")
    parser.add_argument("--confusion", help="confusion.json")
    parser.add_argument("--ontology", help="ontology.json")
    parser.add_argument("--choices", help="restore exported scene_choices.json")
    parser.add_argument("--asset-record", help="assets.json with recorded find_in_library candidates")
    parser.add_argument("--image-root", help="look for the images in this folder instead of the "
                                             "paths in the manifest")
    parser.add_argument("--embed", action="store_true",
                        help="put the images inside the HTML, so it opens anywhere")
    parser.add_argument("--out", required=True, help="where to write viewer.html")
    parser.add_argument("--force", action="store_true", help="overwrite an existing --out file")
    args = parser.parse_args(argv)

    if not TEMPLATE.exists():
        print(f"error: the template is missing: {TEMPLATE.as_posix()}", file=sys.stderr)
        return 2
    out = pathlib.Path(args.out)
    if out.exists() and not args.force:
        print(f"error: {out.as_posix()} exists; pass --force to overwrite", file=sys.stderr)
        return 1

    try:
        graph = load(pathlib.Path(args.graph))
        manifest = load(pathlib.Path(args.manifest))
        scores = optional(args.scores)
        confusion = optional(args.confusion)
        ontology = optional(args.ontology)
        choices = optional(args.choices)
        asset_record = optional(args.asset_record)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: not valid JSON: {exc}", file=sys.stderr)
        return 2

    if not graph.get("nodes"):
        print("error: the graph has no nodes", file=sys.stderr)
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    html, problems, warnings = build(
        graph, manifest, scores, confusion, ontology, out.parent, args.embed,
        pathlib.Path(args.image_root) if args.image_root else None, choices, asset_record)

    if problems:
        for line in problems:
            print(f"error: {line}", file=sys.stderr)
        print(json.dumps({"out": None, "problems": problems}, indent=2))
        return 1

    out.write_text(html, encoding="utf-8")
    for line in warnings:
        print(f"warning: {line}", file=sys.stderr)
    print(json.dumps({
        "out": out.as_posix(),
        "bytes": out.stat().st_size,
        "nodes": len(graph["nodes"]),
        "images": len(graph.get("images") or []),
        "embedded": bool(args.embed),
        "warnings": warnings,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
