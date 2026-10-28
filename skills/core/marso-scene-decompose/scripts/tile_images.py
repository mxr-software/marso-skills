#!/usr/bin/env python3
"""Cut every photograph into a whole view and a few overlapping native-resolution tiles.

The model is shown a downscaled copy of a big photograph, so a small object is a few
pixels and a box measured off that copy is a guess. The old answer was a magnified
view with a grid to read numbers off, and agents spent twenty to forty tool calls
doing arithmetic with it. A tile is that magnified view, made once, by a script: the
agent looks at it, and a box is simply "0-1 of the picture in front of me". A later
script maps it back into the whole photograph, so the model never does the geometry.

Writes, per image, `<out>/<image_id>/whole.jpg` (long edge capped at --long-edge) and
`t1.jpg`, `t2.jpg` ... (row-major, overlapping, each capped at the same edge), and
`<out>/tiles.json` recording the region of the photograph each one shows.

Pillow is required: the standard library cannot decode a JPEG. An image no bigger than
the long edge is not tiled, because a tile of it would show nothing the whole view
doesn't.

Exit codes: 0 done, 1 an image could not be tiled, 2 the inputs could not be read or
Pillow is missing.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

LONG_EDGE = 1568        # what an agent is shown without being downscaled again
GRID = (2, 2)
OVERLAP = 0.12          # share of a tile that the next one repeats
QUALITY = 90
MIN_TILE_GAIN = 1.3     # tile only if the photograph is this much bigger than the long edge


def spans(count: int, overlap: float) -> list[tuple[float, float]]:
    """Normalised [start, end] for each of `count` tiles along one axis, overlapping.

    The last tile is pinned to 1.0 so the tiles cover the whole frame exactly, whatever
    the arithmetic leaves over.
    """
    if count <= 1:
        return [(0.0, 1.0)]
    size = 1.0 / (count - (count - 1) * overlap)
    step = size * (1.0 - overlap)
    out = []
    for index in range(count):
        start = min(index * step, 1.0 - size)
        out.append((round(start, 6), round(start + size, 6)))
    out[-1] = (round(1.0 - size, 6), 1.0)
    return out


def tile_regions(cols: int, rows: int, overlap: float) -> list[dict]:
    xs, ys = spans(cols, overlap), spans(rows, overlap)
    regions = []
    for r, (y0, y1) in enumerate(ys):
        for c, (x0, x1) in enumerate(xs):
            regions.append({"tile_id": f"t{len(regions) + 1}", "row": r, "col": c,
                            "region": [x0, y0, x1, y1]})
    return regions


def find_image(raw: str, roots: list[pathlib.Path]) -> pathlib.Path | None:
    candidate = pathlib.Path(raw)
    if candidate.is_absolute():
        return candidate if candidate.exists() else None
    for root in roots:
        if (root / candidate).exists():
            return root / candidate
    return None


def fit(picture, long_edge: int):
    width, height = picture.size
    scale = long_edge / max(width, height)
    if scale >= 1.0:
        return picture
    return picture.resize((max(1, round(width * scale)), max(1, round(height * scale))))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--manifest", required=True, help="manifest.json from scan_images.py")
    parser.add_argument("--out", required=True, help="the folder to write the tiles into")
    parser.add_argument("--root", action="append", default=[],
                        help="a folder the manifest's relative image paths may be under; "
                             "repeat the flag. The manifest's own folder and its parents "
                             "and the current folder are tried as well")
    parser.add_argument("--grid", default=f"{GRID[0]}x{GRID[1]}",
                        help="columns x rows per image (default %(default)s)")
    parser.add_argument("--overlap", type=float, default=OVERLAP,
                        help="how much neighbouring tiles repeat (default %(default)s)")
    parser.add_argument("--long-edge", type=int, default=LONG_EDGE,
                        help="cap on the long edge of every written picture (default %(default)s)")
    parser.add_argument("--force", action="store_true", help="overwrite existing tiles")
    args = parser.parse_args(argv)

    try:
        from PIL import Image, ImageOps
    except ImportError:
        print("error: tiling needs Pillow (pip install Pillow); the standard library "
              "cannot decode a JPEG", file=sys.stderr)
        return 2

    try:
        cols, rows = (int(v) for v in args.grid.lower().split("x"))
    except ValueError:
        print("error: --grid looks like 2x2", file=sys.stderr)
        return 2
    if cols < 1 or rows < 1 or not 0 <= args.overlap < 0.5:
        print("error: --grid needs at least 1x1 and --overlap must be from 0 to 0.5",
              file=sys.stderr)
        return 2

    manifest_path = pathlib.Path(args.manifest)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"error: no such file: {args.manifest}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"error: could not read {args.manifest}: {exc}", file=sys.stderr)
        return 2

    rows_in = manifest.get("images")
    if not isinstance(rows_in, list) or not rows_in:
        print("error: the manifest lists no images", file=sys.stderr)
        return 2

    here = manifest_path.resolve().parent
    roots = [pathlib.Path(r) for r in args.root] + [pathlib.Path.cwd(), here] + list(here.parents)[:4]

    out = pathlib.Path(args.out)
    if (out / "tiles.json").exists() and not args.force:
        print(f"error: {out.as_posix()}/tiles.json exists; pass --force to overwrite",
              file=sys.stderr)
        return 1
    out.mkdir(parents=True, exist_ok=True)

    result: dict = {"schema": "scene-decompose/tiles@1", "long_edge": args.long_edge,
                    "grid": [cols, rows], "overlap": args.overlap, "images": {}}
    problems: list[str] = []
    warnings: list[str] = []

    for row in rows_in:
        image_id = row.get("image_id")
        source = find_image(str(row.get("path") or ""), roots)
        if not image_id or source is None:
            problems.append(f"{image_id or '?'}: no image at {row.get('path')!r}; pass "
                            "--root <the folder it is under>")
            continue
        try:
            with Image.open(source) as opened:
                # A phone photo often carries its rotation as a tag. Agents see the
                # rotated picture, so the boxes have to be in the rotated frame.
                picture = ImageOps.exif_transpose(opened).convert("RGB")
        except Exception as exc:               # an unreadable file is a result, not a crash
            problems.append(f"{image_id}: could not open {source.as_posix()}: {exc}")
            continue

        width, height = picture.size
        if row.get("width") and row.get("height") and \
                (width, height) != (row["width"], row["height"]):
            warnings.append(
                f"{image_id}: the manifest says {row['width']}x{row['height']} but the "
                f"picture opens as {width}x{height} (an EXIF rotation, probably). The tiles "
                "use the opened size; boxes are normalised, so this changes nothing")

        folder = out / image_id
        folder.mkdir(parents=True, exist_ok=True)
        whole_path = folder / "whole.jpg"
        whole = fit(picture, args.long_edge)
        whole.save(whole_path, quality=QUALITY)

        entry = {"width": width, "height": height,
                 "whole": {"path": whole_path.resolve().as_posix(), "pixels": list(whole.size)},
                 "tiled": False, "tiles": []}
        if max(width, height) > args.long_edge * MIN_TILE_GAIN and (cols > 1 or rows > 1):
            entry["tiled"] = True
            for tile in tile_regions(cols, rows, args.overlap):
                x0, y0, x1, y1 = tile["region"]
                box = (round(x0 * width), round(y0 * height),
                       round(x1 * width), round(y1 * height))
                crop = fit(picture.crop(box), args.long_edge)
                path = folder / f"{tile['tile_id']}.jpg"
                crop.save(path, quality=QUALITY)
                tile["path"] = path.resolve().as_posix()
                tile["pixels"] = list(crop.size)
                entry["tiles"].append(tile)
        result["images"][image_id] = entry

    (out / "tiles.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report = {"out": out.as_posix(), "images": len(result["images"]),
              "tiles": sum(len(v["tiles"]) for v in result["images"].values()),
              "untiled": [k for k, v in result["images"].items() if not v["tiled"]],
              "problems": problems, "warnings": warnings}
    print(json.dumps(report, indent=2))
    for line in problems + warnings:
        print(("error: " if line in problems else "warning: ") + line, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
