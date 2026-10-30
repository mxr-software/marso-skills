"""Build one master's appearance sheet; split a visually reviewed result by saved cells.

Requires Pillow. Coordinates alone cannot verify that an image editor preserved layout.
Outputs must be new directories; source images and accepted results are never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from PIL import Image, ImageColor, ImageOps

SCHEMA = "marso/appearance-sheet@1"


def validate(doc):
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        raise ValueError("unsupported layout schema")
    w, h = doc.get("width"), doc.get("height")
    if any(type(n) is not int or n <= 0 for n in (w, h)):
        raise ValueError("layout dimensions must be positive integers")
    cells, seen = doc.get("cells"), set()
    if not isinstance(cells, list) or not cells:
        raise ValueError("layout needs cells")
    for cell in cells:
        if not isinstance(cell, dict):
            raise ValueError("cells must be objects")
        sid, box = cell.get("style_id"), cell.get("box")
        if (not isinstance(sid, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", sid)
                or sid.casefold() in seen or re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", sid)):
            raise ValueError("style ids must be unique safe filenames (letters, digits, hyphen, underscore)")
        seen.add(sid.casefold())
        if not isinstance(box, list) or len(box) != 4 or any(type(n) is not int for n in box):
            raise ValueError("each crop needs four integer pixel bounds")
        if not (0 <= box[0] < box[2] <= w and 0 <= box[1] < box[3] <= h):
            raise ValueError("crop outside image or empty")
    return w, h, cells


def build(source, out, ids, columns, rows, width, height, gutter=16, family="", background="#000000"):
    if any(type(n) is not int or n <= 0 for n in (columns, rows, width, height)) or gutter < 0:
        raise ValueError("positive dimensions/rows/columns and nonnegative gutter required")
    if not ids or len(ids) > columns * rows:
        raise ValueError("ids must fit the requested grid")
    background_rgb = ImageColor.getcolor(background, "RGB")
    cells = []
    for i, sid in enumerate(ids):
        c, r = i % columns, i // columns
        cells.append({"style_id": sid, "box": [c * width // columns + gutter,
                     r * height // rows + gutter, (c + 1) * width // columns - gutter,
                     (r + 1) * height // rows - gutter]})
    doc = {"schema": SCHEMA, "family": family, "width": width, "height": height,
           "columns": columns, "rows": rows, "gutter": gutter, "cells": cells,
           "background_rgb": list(background_rgb),
           "source_sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest()}
    validate(doc)
    with Image.open(source) as opened:
        source_image = ImageOps.exif_transpose(opened).convert("RGBA")
    sheet = Image.new("RGB", (width, height), background_rgb)
    for cell in cells:
        x0, y0, x1, y1 = cell["box"]
        fitted = ImageOps.contain(source_image, (x1 - x0, y1 - y0))
        position = (x0 + (x1 - x0 - fitted.width) // 2, y0 + (y1 - y0 - fitted.height) // 2)
        sheet.paste(fitted, position, fitted)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    sheet.save(out / "sheet.png")
    (out / "layout.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def split(image, layout, out, allow_scale=False, ids=None):
    doc = json.loads(Path(layout).read_text(encoding="utf-8-sig"))
    w, h, cells = validate(doc)
    selected = set(ids or [c["style_id"] for c in cells])
    if not selected.issubset({c["style_id"] for c in cells}):
        raise ValueError("unknown requested style id")
    with Image.open(image) as opened:
        result = ImageOps.exif_transpose(opened).convert("RGB")
    ow, oh = result.size
    if (ow, oh) != (w, h) and not (allow_scale and ow * h == oh * w):
        raise ValueError("result dimensions changed; only a visually verified proportional resize may use --allow-scale")
    crops = []
    for cell in cells:
        if cell["style_id"] not in selected:
            continue
        x0, y0, x1, y1 = cell["box"]
        box = [round(x0 * ow / w), round(y0 * oh / h), round(x1 * ow / w), round(y1 * oh / h)]
        if box[2] <= box[0] or box[3] <= box[1]:
            raise ValueError("resized crop is empty")
        crops.append({"style_id": cell["style_id"], "box": box, "file": cell["style_id"] + ".png"})
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    for crop in crops:
        result.crop(crop["box"]).save(out / crop["file"])
    record = {"schema": "marso/appearance-crops@1", "family": doc.get("family"),
              "edited_sha256": hashlib.sha256(Path(image).read_bytes()).hexdigest(),
              "layout_sha256": hashlib.sha256(Path(layout).read_bytes()).hexdigest(),
              "width": ow, "height": oh, "crops": crops,
              "visual_layout_verified_by_helper": False}
    (out / "crops.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("build", help="repeat one master still into known cells")
    p.add_argument("source")
    p.add_argument("out")
    p.add_argument("--ids", nargs="+", required=True)
    p.add_argument("--columns", type=int, required=True)
    p.add_argument("--rows", type=int, required=True)
    p.add_argument("--width", type=int, required=True, help="choose canvas dimensions for the subject and grid")
    p.add_argument("--height", type=int, required=True)
    p.add_argument("--gutter", type=int, default=16)
    p.add_argument("--family", default="")
    p.add_argument("--background", default="#000000", help="Pillow colour for gutters/transparency; does not replace an opaque source background")
    p = sub.add_parser("split", help="split known cells AFTER visually checking the edited layout")
    p.add_argument("image")
    p.add_argument("layout")
    p.add_argument("out")
    p.add_argument("--allow-scale", action="store_true", help="accept verified proportional resize; does not verify layout")
    p.add_argument("--ids", nargs="+", help="crop only accepted style ids")
    args = vars(parser.parse_args())
    command = args.pop("command")
    try:
        result = build(**args) if command == "build" else split(**args)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"error: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
