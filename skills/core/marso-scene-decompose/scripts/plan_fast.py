#!/usr/bin/env python3
"""Write every agent's brief for a round, from the files already in the run folder.

A brief is facts copied in, and the last pipeline spent about twelve minutes of a fifty-minute
run with the lead hand-writing them, stage by stage and image by image. A script does it in
milliseconds, so the lead's job in each round is to start the agents and wait.

    plan_fast.py detect --run <run>    round A: register, plus a whole-view agent and a tile agent
                                       per image, all started together
    plan_fast.py match  --run <run>    round B: one agent per batch of residue groups

Prints JSON: a list of agents, each with a `name` and a `prompt` to send as its task message.
For match, the prompt is a short pointer to a brief file, because the tables of candidates are
too long to be worth the lead copying out; every other prompt carries its facts inline.

Exit codes: 0 done, 1 nothing to plan, 2 an input could not be read.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

SCRIPTS = pathlib.Path(__file__).resolve().parent
REFERENCES = SCRIPTS.parent / "references"


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def posix(path) -> str:
    return pathlib.Path(path).resolve().as_posix()


LABEL_RULE = ("**Name things with the shortest common name** (\"wishbone chair\", \"red onion\", "
              "\"paper towel holder\"), at most three words, and the same name every time for "
              "the same kind of thing. Put colour and detail in the description. Later stages "
              "match objects across photographs by name, and two agents calling one thing "
              "different things is what stops them.")


def whole_brief(run: str, image_id: str, entry: dict, count_images: int, detections: str) -> str:
    whole = entry["whole"]
    tiled = entry.get("tiled")
    scope = ("the **anchors** (floor, walls, ceiling) and every **large** thing: furniture, "
             "appliances, built-in cabinet runs, worktops, large surfaces. A small-object pass "
             "runs in parallel on tiles of this photograph and covers the rest, so do not list "
             "small things." if tiled else
             "**everything**: the anchors, the furniture, and every small object. This photograph "
             "is small enough that there is no tile pass, so you are the only one looking.")
    return f"""Stage: detect, WHOLE-VIEW pass, {image_id} — scene-decompose run `{run}`.

Read `{posix(REFERENCES / 'detect.md')}` and then work. That file and this message are everything you need; do not open anything else unless it tells you to.

Look at: `{whole['path']}` — the WHOLE photograph, downscaled to {whole['pixels'][0]}x{whole['pixels'][1]} px. It is one of {count_images} photographs of one environment. Boxes are `[x0, y0, x1, y1]`, 0 to 1 of this picture, origin top-left.

Record {scope}

{LABEL_RULE}

Say what each thing rests on in `on` (a name, e.g. "oak dining table"), and mark anything other things sit on with `"surface": true`. Floors and walls have no `on`.

Write exactly one file: `{posix(detections)}/{image_id}.whole.json`, in the envelope the skill shows. Then reply with one line: how many objects. Do not draw overlays, zoom, or re-check: a script merges and checks your file, and a person reviews the result."""


def tile_brief(run: str, image_id: str, tile: dict, entry: dict, detections: str) -> str:
    x0, y0, x1, y1 = tile["region"]
    return f"""Stage: detect, TILE pass {tile['tile_id']} of {image_id} — scene-decompose run `{run}`.

Read `{posix(REFERENCES / 'detect.md')}` and then work. That file and this message are everything you need; do not open anything else unless it tells you to.

Look at: `{tile['path']}` — a native-resolution crop of one part of a photograph, {tile['pixels'][0]}x{tile['pixels'][1]} px. It shows the region `[{x0}, {y0}, {x1}, {y1}]` of the whole photograph (row {tile['row'] + 1}, column {tile['col'] + 1} of the tiles). **Boxes are `[x0, y0, x1, y1]`, 0 to 1 of THIS crop, origin top-left, not of the photograph.** A script maps them back; never convert anything yourself.

Record **everything small enough to be an object in this crop**, including small surfaces (a placemat, a tray, a laptop, a caddy). Do not list floors, walls, or large furniture such as a whole table or cabinet run: a whole-view pass has those. Look twice at what holds things: what is under, behind and between what you listed. An object the crop edge cuts: box what you can see; leave it out if less than a third is visible, because the neighbouring crop has it.

{LABEL_RULE}

Say what each thing rests on in `on` (a name, e.g. "wooden tray") and mark anything other things sit on with `"surface": true`. Give `relation` when it is not simply resting on top (`inside`, `hanging-on`, `leaning-against`, `attached-to`).

Write exactly one file: `{posix(detections)}/{image_id}.{tile['tile_id']}.json`, in the envelope the skill shows. Then reply with one line: how many objects. Do not draw overlays, zoom, or re-check: a script merges and checks your file, and a person reviews the result."""


def register_brief(run: str, run_dir: pathlib.Path, plan: dict, manifest: dict, out: str) -> str:
    images = sorted(plan["images"])
    lines = []
    for row in manifest.get("images") or []:
        entry = plan["images"].get(row["image_id"])
        if entry:
            lines.append(f"- **{row['image_id']}**: `{entry['whole']['path']}` "
                         f"({entry['whole']['pixels'][0]}x{entry['whole']['pixels'][1]} px, "
                         f"downscaled from {entry['width']}x{entry['height']})")
    pairs = [f"{a}-{b}" for i, a in enumerate(images) for b in images[i + 1:]]
    return f"""Stage: register — scene-decompose run `{run}`.

Read `{posix(REFERENCES / 'register.md')}` and then work. That file and this message are everything you need.

The photographs, as downscaled whole views (boxes and regions are normalised 0-1, so the downscale does not matter):
{chr(10).join(lines)}

{len(images)} images means {len(pairs)} pairs: {', '.join(pairs)}. Every pair gets a verdict, including `no-overlap` where that is the truth. Name the widest establishing view.

Write exactly one file: `{out}`. Then run `python "{posix(SCRIPTS / 'check_registration.py')}" "{out}" --manifest "{posix(run_dir / 'manifest.json')}"` and fix what it lists. Write the verdicts and evidence the skill asks for, but keep it quick: do not write a progress file, do not make crops unless a verdict genuinely depends on one, and reply with the one-line verdict per pair."""


def plan_detect(run_dir: pathlib.Path) -> tuple[list[dict], list[str]]:
    plan = load(run_dir / "tiles" / "tiles.json")
    manifest = load(run_dir / "manifest.json")
    run = run_dir.name
    # Raw agent output goes in parts/, never in detections/: apply_matches.py reads every file
    # in that folder, and a tile's partial overwrote its image's merged file.
    detections = run_dir / "parts"
    detections.mkdir(parents=True, exist_ok=True)
    agents = [{"name": "register",
               "prompt": register_brief(run, run_dir, plan, manifest, posix(run_dir / "registration.json")),
               "writes": posix(run_dir / "registration.json")}]
    skipped = []
    for image_id in sorted(plan["images"]):
        entry = plan["images"][image_id]
        target = detections / f"{image_id}.whole.json"
        if target.exists():
            skipped.append(target.name)
        else:
            agents.append({"name": f"{image_id}-whole", "writes": posix(target),
                           "prompt": whole_brief(run, image_id, entry, len(plan["images"]),
                                                  posix(detections))})
        for tile in entry.get("tiles") or []:
            target = detections / f"{image_id}.{tile['tile_id']}.json"
            if target.exists():
                skipped.append(target.name)
                continue
            agents.append({"name": f"{image_id}-{tile['tile_id']}", "writes": posix(target),
                           "prompt": tile_brief(run, image_id, tile, entry, posix(detections))})
    # One photograph has no pairs to register, and a finished registration is not redone.
    if len(plan["images"]) < 2:
        agents = [a for a in agents if a["name"] != "register"]
        skipped.append("registration (a single image has no pairs)")
    elif (run_dir / "registration.json").exists():
        agents = [a for a in agents if a["name"] != "register"]
        skipped.append("registration.json")
    return agents, skipped


def describe(member: dict) -> str:
    size = member.get("size_m")
    parts = [member["local_id"], f"**{member.get('label')}**"]
    if member.get("parent_label"):
        parts.append(f"on/in: {member['parent_label']}")
    if isinstance(size, (int, float)):
        parts.append(f"~{size:g} m")
    if member.get("id_confidence") == "low":
        parts.append("name uncertain")
    text = " | ".join(parts)
    desc = str(member.get("description") or "").strip()
    return f"- {text}\n  {desc[:160]}" if desc and desc.lower() != str(member.get("label")).lower() else f"- {text}"


def match_brief(run: str, run_dir: pathlib.Path, auto: dict, batch: dict, registration: dict | None) -> str:
    groups = {g["group_id"]: g for g in auto["groups"]}
    reg = []
    for pair in (registration or {}).get("pairs") or []:
        line = f"- {pair.get('a')} and {pair.get('b')}: **{pair.get('relation')}**"
        if pair.get("closer"):
            line += f" (closer view: {pair['closer']})"
        reg.append(line)
    context = batch.get("context") or {}
    context_lines = chr(10).join(f"- {image_id}: `{path}`" for image_id, path in sorted(context.items()))
    sections = []
    for group_id in batch["groups"]:
        group = groups[group_id]
        sheet = group.get("sheet")
        body = [f"## Group {group_id} — carrier: {group['carrier']}"]
        body.append(f"Close-up of this carrier in each photograph, for detail: `{sheet}`" if sheet
                    else "(no close-up could be made; use the whole photographs above)")
        for image_id in group["images"]:
            body.append(f"\n{image_id}:")
            body.extend(describe(m) for m in group["members"][image_id])
        sections.append("\n".join(body))
    checks = {c["check_id"]: c for c in auto.get("checks") or []}
    mine = [checks[i] for i in batch.get("checks") or [] if i in checks]
    if mine:
        sheets = sorted({c.get("sheet") for c in mine if c.get("sheet")})
        rows = chr(10).join(
            f"- **{c['check_id']}**: " + " / ".join(f"{m['local_id']} '{m['label']}'" for m in c["members"])
            for c in mine)
        sections.append(
            "## Automatic matches to verify\n"
            "The script paired these on their names. Each row of the picture shows the pair side by side, "
            "each cropped with its surroundings and boxed. Are they the same physical object? If you can see "
            "they are not (a different colour, material, or neighbour), veto it. If they are, or you cannot "
            "tell, say nothing.\n"
            + (chr(10).join(f"Pictures: `{s}`" for s in sheets) if sheets else "(no picture could be made)")
            + chr(10) + rows)
    out = posix(run_dir / "match" / f"decisions.{batch['batch_id']}.json")
    return f"""# Match brief — batch {batch['batch_id']} of run `{run}`

Read `{posix(REFERENCES / 'match.md')}` first; it is short. A script has already matched everything unmistakable. You judge only the cases below, which it could not settle.

## How the photographs relate (registration, copied in)
{chr(10).join(reg) or '- not available'}
Believe the closer view about *what* a thing is, and the wider view about *where* it sits.

## What to do
Each group below is one carrier (the worktop, a tray, the table) and what is unmatched on it in each photograph.

**Look at the whole photographs first**, so you see each candidate in its surroundings: which bottle is beside the kettle, which mat is under the tray. Each has every candidate in this batch boxed and numbered, the number being the last digits of its id in the tables below, and the groups in different colours:
{context_lines or '- (none could be made; use the close-ups and descriptions)'}

Then, where you need detail, open a group's close-up. Decide, per object, which one in the other photograph it is, or that it has no counterpart.

Write exactly one file, `{out}`, in this shape, and nothing else:

```json
{{
  "batch_id": "{batch['batch_id']}",
  "merges": [
    {{"members": ["img001-041", "img003-016"], "confidence": "high",
     "evidence": ["both stand behind the headphones, left of the laptop",
                  "the only camera in either photograph"]}}
  ],
  "refusals": [
    {{"candidates": ["img001-050", "img001-052", "img003-025", "img003-026"],
     "for": "same design, same caddy", "against": "left and right cannot be told apart between views",
     "distinct_objects": 2}}
  ],
  "corrections": [
    {{"target": "img001-039", "better_view": "img003-008",
     "problem": "named 'chain strap'", "shows": "tortoiseshell sunglasses"}}
  ],
  "vetoes": [
    {{"check": "k2", "reason": "one is a clear glass vase, the other a matt black one",
     "drop": ["img001-031"]}}
  ],
  "notes": ""
}}
```

## Rules
1. **A merge needs two independent lines of evidence** in `evidence` (what it looks like; what it rests on or stands next to; where it is). One line is not enough and the script will not make the merge.
2. **When two candidates fit equally well, refuse.** A refusal costs nothing and is never a wrong merge. Give `distinct_objects`: how many physical things the candidates stand for (at least the most that share one photograph, at most the number of candidates).
3. Never merge two objects from the same photograph, and never merge a thing with something that does not exist in the other view. A thing at or past the edge of the closer view is simply absent there: that is not evidence either way.
4. `corrections` are for when the better view shows the other one *got it wrong* (a different name, a different object). A difference in detail is not one.
5. `vetoes` only answer the "Automatic matches to verify" section, if there is one: name the check and, in `drop`, the object that does not belong (leave `drop` out to separate them all). Omit `vetoes` when every pair is right.
6. Do not draw anything, zoom, or re-check. Reply with one line: merges, refusals, corrections, vetoes.

{chr(10).join(sections)}
"""


def plan_match(run_dir: pathlib.Path) -> tuple[list[dict], list[str]]:
    auto = load(run_dir / "match" / "auto.json")
    registration = None
    if (run_dir / "registration.json").exists():
        registration = load(run_dir / "registration.json")
    run = run_dir.name
    agents = []
    for batch in auto.get("batches") or []:
        brief = run_dir / "match" / f"brief.{batch['batch_id']}.md"
        brief.write_text(match_brief(run, run_dir, auto, batch, registration), encoding="utf-8", newline="\n")
        out = posix(run_dir / "match" / f"decisions.{batch['batch_id']}.json")
        agents.append({"name": f"match-{batch['batch_id']}", "writes": out, "brief_file": posix(brief),
                       "prompt": (f"Stage: match, batch {batch['batch_id']} — scene-decompose run `{run}`. "
                                  f"Your brief is `{posix(brief)}`. Read it, then the skill it names, "
                                  f"and work. Write exactly one file, `{out}`, and reply with one line.")})
    return agents, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("round", choices=("detect", "match"))
    parser.add_argument("--run", required=True, help="the run folder")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    run_dir = pathlib.Path(args.run)
    if not run_dir.is_dir():
        print(f"error: no such folder: {args.run}", file=sys.stderr)
        return 2
    try:
        agents, skipped = plan_detect(run_dir) if args.round == "detect" else plan_match(run_dir)
    except FileNotFoundError as exc:
        print(f"error: no such file: {exc.filename} (has the earlier step run?)", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: could not read the run folder's files: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"round": args.round, "agents": agents, "count": len(agents),
                      "skipped_because_done": skipped}, indent=2, ensure_ascii=False))
    if not agents:
        print("nothing to start", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
