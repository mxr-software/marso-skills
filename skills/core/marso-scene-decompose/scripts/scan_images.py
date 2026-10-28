#!/usr/bin/env python3
"""Build the run manifest for a set of images.

Reads pixel dimensions straight out of each file's header, so nothing has to be
decoded and no third-party library is needed. Prints the manifest as JSON to
stdout; errors go to stderr.

Exit codes: 0 manifest written, 1 something was wrong with the inputs,
2 the arguments or paths could not be used at all.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def _png(fh) -> tuple[int, int] | None:
    fh.seek(0)
    if fh.read(8) != b"\x89PNG\r\n\x1a\n":
        return None
    fh.seek(16)
    width, height = struct.unpack(">II", fh.read(8))
    return width, height


def _gif(fh) -> tuple[int, int] | None:
    fh.seek(0)
    if fh.read(6) not in (b"GIF87a", b"GIF89a"):
        return None
    width, height = struct.unpack("<HH", fh.read(4))
    return width, height


def _bmp(fh) -> tuple[int, int] | None:
    fh.seek(0)
    if fh.read(2) != b"BM":
        return None
    fh.seek(18)
    width, height = struct.unpack("<ii", fh.read(8))
    return abs(width), abs(height)


def _webp(fh) -> tuple[int, int] | None:
    fh.seek(0)
    header = fh.read(16)
    if len(header) < 16 or header[:4] != b"RIFF" or header[8:12] != b"WEBP":
        return None
    chunk = header[12:16]
    if chunk == b"VP8 ":
        fh.seek(26)
        width, height = struct.unpack("<HH", fh.read(4))
        return width & 0x3FFF, height & 0x3FFF
    if chunk == b"VP8L":
        fh.seek(21)
        bits = struct.unpack("<I", fh.read(4))[0]
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if chunk == b"VP8X":
        fh.seek(24)
        raw = fh.read(6)
        width = raw[0] | raw[1] << 8 | raw[2] << 16
        height = raw[3] | raw[4] << 8 | raw[5] << 16
        return width + 1, height + 1
    return None


def _jpeg(fh) -> tuple[int, int] | None:
    """Walk the JPEG segments to the first start-of-frame marker."""
    fh.seek(0)
    if fh.read(2) != b"\xff\xd8":
        return None
    while True:
        byte = fh.read(1)
        if not byte:
            return None
        if byte != b"\xff":
            continue
        marker = fh.read(1)
        while marker == b"\xff":  # fill bytes are legal between segments
            marker = fh.read(1)
        if not marker:
            return None
        code = marker[0]
        if code in (0xD8, 0x01) or 0xD0 <= code <= 0xD7:
            continue  # no payload
        length_bytes = fh.read(2)
        if len(length_bytes) < 2:
            return None
        length = struct.unpack(">H", length_bytes)[0]
        # SOF0-SOF15, minus the DHT/JPG/DAC markers that share the range
        if 0xC0 <= code <= 0xCF and code not in (0xC4, 0xC8, 0xCC):
            payload = fh.read(7)
            if len(payload) < 5:
                return None
            height, width = struct.unpack(">HH", payload[1:5])
            return width, height
        fh.seek(length - 2, 1)


READERS = (_png, _jpeg, _webp, _gif, _bmp)


def dimensions(path: pathlib.Path) -> tuple[int, int] | None:
    """Pixel width and height, or None when no reader recognises the file."""
    with path.open("rb") as fh:
        for reader in READERS:
            try:
                size = reader(fh)
            except (struct.error, OSError):
                size = None
            if size and size[0] > 0 and size[1] > 0:
                return size
    return None


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def collect(inputs: list[str]) -> list[pathlib.Path]:
    """Expand folders into their images; keep explicit files as given."""
    found: list[pathlib.Path] = []
    for raw in inputs:
        path = pathlib.Path(raw)
        if path.is_dir():
            found.extend(
                sorted(p for p in path.iterdir() if p.is_file() and p.suffix.lower() in SUFFIXES)
            )
        elif path.is_file():
            found.append(path)
        else:
            raise FileNotFoundError(raw)
    # Stable order, no duplicate paths, so ids survive a re-run.
    seen: set[str] = set()
    unique: list[pathlib.Path] = []
    for path in sorted(found, key=lambda p: str(p).lower()):
        key = str(path.resolve()).lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def build(inputs: list[str]) -> dict:
    paths = collect(inputs)
    images = []
    problems = []
    by_hash: dict[str, str] = {}
    for index, path in enumerate(paths, start=1):
        image_id = f"img{index:03d}"
        size = dimensions(path)
        digest = sha256(path)
        row = {
            "image_id": image_id,
            "path": path.as_posix(),
            "bytes": path.stat().st_size,
            "sha256": digest,
        }
        if size:
            row["width"], row["height"] = size
            row["dims_source"] = "header"
        else:
            row["width"] = None
            row["height"] = None
            row["dims_source"] = "unknown"
            problems.append(
                f"{path.as_posix()}: could not read pixel dimensions from the header; "
                "look at the image and state them, then set dims_source to 'estimated'"
            )
        if digest in by_hash:
            row["duplicate_of"] = by_hash[digest]
            problems.append(
                f"{path.as_posix()}: byte-identical to {by_hash[digest]}; "
                "decide whether to drop it before registering"
            )
        else:
            by_hash[digest] = image_id
        images.append(row)
    return {
        "schema": "scene-decompose/manifest@1",
        "bbox_convention": "normalised [x0,y0,x1,y1], 0-1 of the image, origin top-left",
        "count": len(images),
        "images": images,
        "problems": problems,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("inputs", nargs="+", help="image files, or folders of images")
    parser.add_argument("--out", help="write the manifest here as well as to stdout")
    parser.add_argument("--force", action="store_true", help="overwrite an existing --out file")
    args = parser.parse_args(argv)

    try:
        manifest = build(args.inputs)
    except FileNotFoundError as exc:
        print(f"error: no such file or folder: {exc}", file=sys.stderr)
        return 2

    if not manifest["images"]:
        print("error: no images found in the inputs given", file=sys.stderr)
        return 1

    if args.out:
        out = pathlib.Path(args.out)
        if out.exists() and not args.force:
            print(f"error: {out.as_posix()} exists; pass --force to overwrite", file=sys.stderr)
            return 1
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(manifest, indent=2))
    for problem in manifest["problems"]:
        print(f"warning: {problem}", file=sys.stderr)
    return 1 if manifest["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
