#!/usr/bin/env python3
"""Draw a detections file's boxes onto its photograph, so you can look at them.

Writes one SVG that points at the image and draws every box over it, labelled.
Open it in a browser. Nothing is resampled and no image library is needed: the
SVG references the photograph by relative path and the browser does the rest.

Reading the numbers again never finds a box that is simply in the wrong place.
Looking at them does: a run once found five bad boxes this way, one of them a
plain arithmetic slip no amount of re-reading would have caught.
"""
from __future__ import annotations

import argparse
import colorsys
import html
import json
import os
import pathlib
import sys

# Enough contrast between neighbours that two boxes on the same object are telling apart.
GOLDEN = 0.618033988749895


def colour(index: int) -> str:
    r, g, b = colorsys.hsv_to_rgb((index * GOLDEN) % 1.0, 0.75, 1.0)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def svg(objects: list[dict], image_href: str, width: int, height: int,
        title: str, labels: bool = True, crop: list[float] | None = None) -> str:
    # The viewBox is in real pixels so the boxes land where the numbers say, and a crop
    # is just a smaller one. width 100% fits it to the window rather than showing a corner.
    view = (0.0, 0.0, float(width), float(height))
    if crop:
        cx0, cy0, cx1, cy1 = crop
        view = (cx0 * width, cy0 * height, (cx1 - cx0) * width, (cy1 - cy0) * height)
    font = max(10, round(view[3] / 40))
    stroke = max(1.0, view[3] / 500)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{view[0]:.1f} {view[1]:.1f} {view[2]:.1f} {view[3]:.1f}" '
        f'width="100%" preserveAspectRatio="xMidYMid meet">',
        f'<title>{html.escape(title)}</title>',
        # Clipped for the same reason zoom_region.py clips: a letterboxed viewport would
        # otherwise show photograph outside the cropped area.
        f'<clipPath id="view"><rect x="{view[0]:.1f}" y="{view[1]:.1f}" '
        f'width="{view[2]:.1f}" height="{view[3]:.1f}"/></clipPath>',
        f'<image href="{html.escape(image_href, quote=True)}" x="0" y="0" '
        f'width="{width}" height="{height}" clip-path="url(#view)"/>',
    ]
    for index, obj in enumerate(objects):
        box = obj.get("bbox")
        if not isinstance(box, list) or len(box) != 4:
            continue
        try:
            x0, y0, x1, y1 = (float(v) for v in box)
        except (TypeError, ValueError):
            continue
        px, py = x0 * width, y0 * height
        pw, ph = max((x1 - x0) * width, 1.0), max((y1 - y0) * height, 1.0)
        c = colour(index)
        label = f'{obj.get("local_id", "?")} {obj.get("label", "")}'.strip()
        parts.append(
            f'<rect x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" '
            f'fill="none" stroke="{c}" stroke-width="{stroke:.1f}"/>'
        )
        if labels:
            parts.append(
                f'<text x="{px + 2:.1f}" y="{max(py - 2, view[1] + font):.1f}" '
                f'font-size="{font}" font-family="monospace" fill="{c}" '
                f'stroke="#000" stroke-width="{stroke / 2:.1f}" paint-order="stroke">'
                f'{html.escape(label)}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_png(out, image_path, boxes, region, width, height, labels):
    """Burn the same picture into a PNG, for a reader that cannot open an SVG.

    Needs Pillow. The SVG is the standard-library default and is what a person
    opens in a browser; an agent cannot see one, so it renders this instead.
    `boxes` is a list of (x0, y0, x1, y1, colour, label) in normalised coordinates
    and `region` is the normalised crop to show, or None for the whole frame.
    """
    from PIL import Image, ImageDraw          # imported late: only --png needs it

    with Image.open(image_path) as source:
        picture = source.convert("RGB")
    if picture.size != (width, height):
        picture = picture.resize((width, height))
    if region:
        rx0, ry0, rx1, ry1 = region
        box = (int(rx0 * width), int(ry0 * height), int(rx1 * width), int(ry1 * height))
        picture = picture.crop(box)
        origin, span = (box[0], box[1]), (box[2] - box[0], box[3] - box[1])
    else:
        origin, span = (0, 0), (width, height)

    # Put the long edge at 1600px, scaling a small crop UP as well as a large one down.
    # A 0.2-wide crop of a 4000px photograph came out 800px, and every agent that got one
    # upscaled it by hand before it could judge a box edge.
    longest = max(span[0], span[1])
    scale = (1600 / longest) if longest else 1.0
    if scale != 1.0:
        picture = picture.resize((max(1, round(span[0] * scale)),
                                  max(1, round(span[1] * scale))))
    draw = ImageDraw.Draw(picture)
    pen = max(1, round(max(picture.size) / 500))
    for x0, y0, x1, y1, colour, label in boxes:
        px0 = (x0 * width - origin[0]) * scale
        py0 = (y0 * height - origin[1]) * scale
        px1 = (x1 * width - origin[0]) * scale
        py1 = (y1 * height - origin[1]) * scale
        draw.rectangle([px0, py0, px1, py1], outline=colour, width=pen)
        # `labels` is the --no-labels flag inverted. It used to be accepted and ignored,
        # so a crowded crop stayed unreadable however you asked for it.
        if label and labels:
            draw.text((px0 + pen + 1, max(0, py0 - 12)), label, fill=colour)
    picture.save(out)
    return picture.size


def as_png_path(out):
    """Pillow picks its format from the suffix, so a .svg name raises a bare KeyError.

    Both scripts' own examples write `zoom.svg`, so adding --png to the command in
    front of you was most agents' first call and it died in a Pillow traceback.
    """
    return out if out.suffix.lower() == ".png" else out.with_suffix(".png")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("detections", help="detections/<image_id>.json")
    parser.add_argument("--image", required=True, help="the photograph it describes")
    parser.add_argument("--out", required=True, help="the SVG to write")
    parser.add_argument("--width", type=int, help="pixel width, from the manifest")
    parser.add_argument("--height", type=int, help="pixel height, from the manifest")
    parser.add_argument("--only", nargs="*", help="draw only these local_ids")
    parser.add_argument("--crop", nargs=4, type=float,
                        metavar=("X0", "Y0", "X1", "Y1"),
                        help="show only this part of the frame, normalised 0-1")
    parser.add_argument("--no-labels", action="store_true",
                        help="draw the boxes without their ids: a crowded frame is "
                             "unreadable with every label on it")
    parser.add_argument("--png", action="store_true",
                        help="write a PNG instead of an SVG, for a reader that cannot open one. Needs Pillow")
    parser.add_argument("--force", action="store_true", help="overwrite an existing --out")
    args = parser.parse_args(argv)

    path = pathlib.Path(args.detections)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"error: no such file: {args.detections}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"error: could not read {args.detections}: {exc}", file=sys.stderr)
        return 2

    image = pathlib.Path(args.image)
    if not image.exists():
        print(f"error: no such image: {args.image}", file=sys.stderr)
        return 2

    objects = data.get("objects")
    if not isinstance(objects, list) or not objects:
        print("error: the detections file has no 'objects' to draw", file=sys.stderr)
        return 1
    if args.only:
        wanted = set(args.only)
        objects = [o for o in objects if o.get("local_id") in wanted]
        if not objects:
            print(f"error: none of {sorted(wanted)} is in the file", file=sys.stderr)
            return 1

    # The aspect ratio is what matters for looking; any size draws the same picture.
    width = args.width or 2000
    height = args.height or 1500
    if not args.width or not args.height:
        print("warning: no --width/--height given, so the boxes are drawn on a 2000x1500 "
              "canvas; pass the manifest's dimensions to see the real shape",
              file=sys.stderr)

    out = pathlib.Path(args.out)
    if out.exists() and not args.force:
        print(f"error: {args.out} exists; pass --force to overwrite", file=sys.stderr)
        return 1
    if out.parent and not out.parent.exists():
        out.parent.mkdir(parents=True, exist_ok=True)

    try:
        href = os.path.relpath(image.resolve(), out.resolve().parent).replace("\\", "/")
    except ValueError:                     # Windows: the photograph is on another drive
        href = image.resolve().as_uri()
    if args.png:
        drawn = [(*[float(v) for v in o["bbox"]], colour(i),
                  f'{o.get("local_id", "?")} {o.get("label", "")}'.strip())
                 for i, o in enumerate(objects)
                 if isinstance(o.get("bbox"), list) and len(o["bbox"]) == 4]
        out = as_png_path(out)
        try:
            rendered = write_png(out, image, drawn, args.crop, width, height,
                                 not args.no_labels)
        except ImportError:
            print("error: --png needs Pillow; drop the flag to write an SVG instead",
                  file=sys.stderr)
            return 1
    else:
        rendered = None
        out.write_text(
            svg(objects, href, width, height,
                f'{data.get("image_id", path.stem)} boxes',
                labels=not args.no_labels, crop=args.crop),
            encoding="utf-8",
        )
    report = {
        "out": str(out).replace("\\", "/"),
        "image": href,
        "boxes": len(objects),
        "canvas": [width, height],
        "shows": list(args.crop) if args.crop else [0.0, 0.0, 1.0, 1.0],
        "format": "png" if args.png else "svg",
        "open_it": "look at every box before reporting: read the PNG, or open the SVG in a browser",
    }
    if rendered:
        report["rendered_pixels"] = list(rendered)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
