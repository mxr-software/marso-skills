#!/usr/bin/env python3
"""Drive the fast path: one call per phase, so the lead's job is to start agents and wait.

The last pipeline spent about twelve of its fifty minutes on the lead running a dozen small
scripts between stages by hand. Everything between the two rounds of agents is bookkeeping,
so it is one command per phase here, and each prints a summary short enough to act on.

    fast.py start      --run <run> --images <folder or files>
                       intake and tiling: manifest.json, tiles/, and the clock starts
    fast.py detect     --run <run>
                       after round A: merge every image's passes, build its tree, run the
                       gates, draw one overlay per image into <run>/qc/
    fast.py verify-plan --run <run>
                       one verify agent per photograph: numbered crop sheets beside every name
    fast.py verify     --run <run>
                       after the verify round: apply renames, removals and duplicates, redraw
                       the overlays
    fast.py match-plan --run <run>
                       pair what is obvious, make the contact sheets, print the agents for round B
    fast.py graph      --run <run>
                       after round B: matches.json, the graph, scores, confusion, validation
                       and the viewer

Each phase records how long it took in <run>/fast.json, so a run says where its time went.
Between `start` and `detect` the lead runs `plan_fast.py detect` and starts those agents; between
`match-plan` and `graph` it starts the match agents.

Exit codes: 0 phase done cleanly, 1 done but something needs a person or a retry (listed),
2 an input could not be read.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import pathlib
import shutil
import subprocess
import sys
import time

# The two ways to run detect, in the words a user hears.
#   Fine:   every photograph is cut into overlapping tiles, each looked at in full detail.
#           About 3.5 minutes for three photographs, and it finds the small objects.
#   Coarse: every photograph is looked at whole. About 2.5 minutes, and it finds roughly two
#           thirds as many objects, mostly missing the small ones on a busy shot.
# Measured on one three-photograph kitchen against an earlier, slower run: Fine found 82% of
# its objects (75% of the tiny ones), Coarse 68% (33%). Fine starts five agents per image, so
# past a handful of photographs it is slow and heavy; Coarse starts one.
FINE_GRID, COARSE_GRID = "2x2", "1x1"
COARSE_ABOVE = 4          # recommend Coarse when there are more images than this
HERE = pathlib.Path(__file__).resolve().parent
# Every stage script lives in this folder; the skill is self-contained.
DETECT = MATCH = STRUCTURE = VIEW = HERE


def call(script: pathlib.Path, *args: str) -> tuple[int, dict | None, str]:
    """Run another script in this folder and return (exit code, its JSON if it printed any, its stderr)."""
    done = subprocess.run([sys.executable, "-X", "utf8", str(script), *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        data = json.loads(done.stdout) if done.stdout.strip() else None
    except ValueError:
        data = None
    return done.returncode, data, done.stderr.strip()


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def state_path(run: pathlib.Path) -> pathlib.Path:
    return run / "fast.json"


def read_state(run: pathlib.Path) -> dict:
    try:
        return load(state_path(run))
    except (OSError, ValueError):
        return {"phases": {}}


def finish(run: pathlib.Path, name: str, started: float, extra: dict | None = None) -> dict:
    state = read_state(run)
    now = time.time()
    state.setdefault("phases", {})[name] = {
        "seconds": round(now - started, 1),
        "since_start": round(now - state.get("started_epoch", started), 1),
        "finished": datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%SZ"),
        **(extra or {})}
    state_path(run).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return state["phases"][name]


def need(run: pathlib.Path, *names: str) -> str | None:
    for name in names:
        if not (run / name).exists():
            return f"{(run / name).as_posix()} is missing; has the earlier step run?"
    return None


# Everything a run derives from the photographs. Switching mode starts a clean run: these go,
# and run.json, FEEDBACK.md and the photographs themselves are never touched.
DERIVED = ("tiles", "parts", "detections", "structure", "verify", "match", "qc", "registration.json",
           "matches.json", "scene_graph.json", "view_scores.json", "confusion.json", "viewer.html")


def clear_derived(run: pathlib.Path) -> list[str]:
    removed = []
    for name in DERIVED:
        target = run / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
        else:
            continue
        removed.append(name)
    return removed


def phase_start(args) -> int:
    run = pathlib.Path(args.run)
    run.mkdir(parents=True, exist_ok=True)
    started = time.time()
    code, manifest, err = call(HERE / "scan_images.py", *args.images,
                               "--out", str(run / "manifest.json"), "--force")
    if manifest is None:
        print(f"error: intake failed: {err}", file=sys.stderr)
        return 2
    problems = list(manifest.get("problems") or [])
    count = int(manifest.get("count") or 0)
    if args.grid:
        grid = args.grid
        mode, why = ("coarse" if grid == COARSE_GRID else "fine"), f"the grid was set by hand ({grid})"
    elif args.mode in ("fine", "coarse"):
        mode, why = args.mode, "chosen by the user"
        grid = FINE_GRID if mode == "fine" else COARSE_GRID
    else:
        mode = "coarse" if count > COARSE_ABOVE else "fine"
        grid = COARSE_GRID if mode == "coarse" else FINE_GRID
        why = (f"{count} images: Coarse is recommended above {COARSE_ABOVE}" if mode == "coarse"
               else f"{count} images: Fine is recommended up to {COARSE_ABOVE}")
    previous = read_state(run).get("mode")
    cleared: list[str] = []
    if previous and previous != mode:
        cleared = clear_derived(run)
    code, tiles, err = call(HERE / "tile_images.py", "--manifest", str(run / "manifest.json"),
                            "--out", str(run / "tiles"), "--root", str(pathlib.Path.cwd()), "--force",
                            "--grid", grid, "--long-edge", str(args.long_edge))
    if tiles is None:
        print(f"error: tiling failed: {err}", file=sys.stderr)
        return 2
    problems += tiles.get("problems") or []
    first = (manifest.get("images") or [{}])[0].get("path")
    root = None
    for candidate in (pathlib.Path(first or ""), pathlib.Path.cwd() / (first or "")):
        if first and candidate.exists():
            root = candidate.resolve().parent.as_posix()
            break
    state = {"phases": {}} if previous and previous != mode else read_state(run)
    state.update({"started_epoch": started,
                  "started": datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%SZ"),
                  "images_root": root, "mode": mode, "mode_reason": why, "grid": grid,
                  "long_edge": args.long_edge})
    state_path(run).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    phase = finish(run, "start", started)
    other = "coarse" if mode == "fine" else "fine"
    print(json.dumps({"phase": "start", "mode": mode, "mode_reason": why,
                      "other_mode": {"fine": "Fine: cut into tiles; finds the small objects; about 3.5 "
                                             "minutes for three photographs",
                                     "coarse": "Coarse: each photograph looked at whole; about a minute "
                                               "faster; finds roughly two thirds as many objects"}[other],
                      "switch": f"run start again with --mode {other}; this starts a clean run",
                      "cleared": cleared,
                      "notice": (f"Switched from {previous} to {mode}: this is a clean run, so "
                                 "earlier detections, matches and the graph were discarded and "
                                 "every agent runs again.") if cleared or (previous and previous != mode) else None,
                      "images": manifest.get("count"), "tiles": tiles.get("tiles"),
                      "untiled": tiles.get("untiled"), "problems": problems,
                      "warnings": tiles.get("warnings"), "timing": phase}, indent=2))
    return 1 if problems else 0


def anchor_labels(det: pathlib.Path, anchors: list[str]) -> list[str]:
    """The image's anchors by name, so a kettle among them is plain to see."""
    try:
        names = {o["local_id"]: o.get("label") for o in load(det).get("objects") or []}
    except (OSError, ValueError):
        return anchors
    return [f"{a} {names.get(a, '?')}" for a in anchors]


def phase_detect(args) -> int:
    run = pathlib.Path(args.run)
    missing = need(run, "tiles/tiles.json")
    if missing:
        print(f"error: {missing}", file=sys.stderr)
        return 2
    started = time.time()
    plan = load(run / "tiles" / "tiles.json")
    (run / "qc").mkdir(exist_ok=True)
    (run / "detections").mkdir(exist_ok=True)
    (run / "structure").mkdir(exist_ok=True)
    report, needs_retry, flagged = {}, [], []
    for image_id, entry in sorted(plan["images"].items()):
        det = run / "detections" / f"{image_id}.json"
        tree = run / "structure" / f"{image_id}.json"
        code, merged, err = call(DETECT / "merge_tiles.py", "--tiles", str(run / "tiles" / "tiles.json"),
                                 "--image-id", image_id, "--dir", str(run / "parts"),
                                 "--out", str(det), "--structure", str(tree), "--force")
        if merged is None:
            report[image_id] = {"error": err or "the merge failed"}
            flagged.append(f"{image_id}: {err}")
            continue
        needs_retry += [f"{image_id}.{n}.json" for n in merged.get("missing") or []]
        gate_d, gate_s, overlay = None, None, None
        if det.exists():
            gate_d, report_d, _ = call(DETECT / "check_detections.py", str(det))
            gate_s, report_s, _ = call(STRUCTURE / "check_structure.py", str(tree))
            for label, body in (("detections", report_d), ("structure", report_s)):
                for line in (body or {}).get("errors") or []:
                    flagged.append(f"{image_id} {label}: {line}")
            whole = entry["whole"]
            overlay = run / "qc" / f"{image_id}.png"
            call(DETECT / "draw_boxes.py", str(det), "--image", whole["path"],
                 "--width", str(whole["pixels"][0]), "--height", str(whole["pixels"][1]),
                 "--out", str(overlay), "--png", "--no-labels", "--force")
        report[image_id] = {
            "objects": merged.get("objects"), "per_source": merged.get("per_source"),
            "dropped_as_duplicates": merged.get("dropped_as_duplicates"),
            "possible_duplicates": len(merged.get("possible_duplicates") or []),
            "seam_joins": merged.get("seam_joins"), "parent_by": merged.get("parent_by"),
            "anchors": anchor_labels(det, merged.get("anchors") or []), "flagged": merged.get("flagged"),
            "detections_gate": gate_d, "structure_gate": gate_s,
            "overlay": overlay.as_posix() if overlay and overlay.exists() else None}
        flagged += [f"{image_id}: {f}" for f in merged.get("flagged") or []]
    phase = finish(run, "detect", started)
    print(json.dumps({"phase": "detect", "images": report, "needs_retry": needs_retry,
                      "flagged": flagged, "timing": phase,
                      "next": "look at each overlay once; then run verify-plan"}, indent=2,
                     ensure_ascii=False))
    return 1 if (needs_retry or flagged) else 0


def phase_verify_plan(args) -> int:
    run = pathlib.Path(args.run)
    missing = need(run, "detections", "structure")
    if missing:
        print(f"error: {missing}", file=sys.stderr)
        return 2
    started = time.time()
    code, planned, err = call(HERE / "make_verify.py", "plan", "--run", str(run))
    if planned is None:
        print(f"error: the verify sheets could not be made: {err}", file=sys.stderr)
        return 2
    phase = finish(run, "verify-plan", started)
    agents = planned.get("agents") or []
    print(json.dumps({"phase": "verify-plan", "agents": agents, "count": len(agents),
                      "skipped_because_done": planned.get("skipped_because_done"),
                      "problems": planned.get("problems"), "timing": phase,
                      "next": ("start these agents together, then run verify" if agents else
                               "nothing to verify; run verify")}, indent=2, ensure_ascii=False))
    return code


def phase_verify(args) -> int:
    run = pathlib.Path(args.run)
    started = time.time()
    code, applied, err = call(HERE / "make_verify.py", "apply", "--run", str(run))
    if applied is None:
        print(f"error: the verify decisions could not be applied: {err}", file=sys.stderr)
        return 2
    plan = load(run / "tiles" / "tiles.json")
    for image_id, entry in sorted(plan["images"].items()):
        det = run / "detections" / f"{image_id}.json"
        if det.exists():
            whole = entry["whole"]
            call(DETECT / "draw_boxes.py", str(det), "--image", whole["path"],
                 "--width", str(whole["pixels"][0]), "--height", str(whole["pixels"][1]),
                 "--out", str(run / "qc" / f"{image_id}.png"), "--png", "--no-labels", "--force")
    phase = finish(run, "verify", started)
    totals = {k: sum(v.get(k, 0) for v in (applied.get("applied") or {}).values())
              for k in ("renamed", "removed", "joined", "reparented")}
    print(json.dumps({"phase": "verify", **totals, "per_image": applied.get("applied"),
                      "not_verified": applied.get("not_verified"), "problems": applied.get("problems"),
                      "timing": phase, "next": "run match-plan"}, indent=2, ensure_ascii=False))
    return code


def phase_match_plan(args) -> int:
    run = pathlib.Path(args.run)
    missing = need(run, "detections", "structure")
    if missing:
        print(f"error: {missing}", file=sys.stderr)
        return 2
    started = time.time()
    state = read_state(run)
    (run / "match").mkdir(exist_ok=True)
    options = ["--structures", str(run / "structure"), "--detections", str(run / "detections"),
               "--manifest", str(run / "manifest.json"), "--sheets", str(run / "match" / "sheets"),
               "--context", str(run / "match" / "context"),
               "--checks", str(run / "match" / "checks"),
               "--out", str(run / "match" / "auto.json"), "--force", "--root", str(pathlib.Path.cwd())]
    if state.get("images_root"):
        options += ["--root", state["images_root"]]
    if (run / "registration.json").exists():
        options += ["--registration", str(run / "registration.json")]
    code, auto, err = call(MATCH / "match_auto.py", *options)
    if auto is None:
        print(f"error: automatic matching failed: {err}", file=sys.stderr)
        return 2
    agents = []
    if auto.get("batches"):
        code, planned, err = call(HERE / "plan_fast.py", "match", "--run", str(run))
        agents = (planned or {}).get("agents") or []
    phase = finish(run, "match-plan", started)
    print(json.dumps({"phase": "match-plan", **{k: auto.get(k) for k in (
        "nodes", "matched_objects", "automatic_matches", "groups", "objects_for_agents", "sheets",
        "checks")},
        "agents": agents, "count": len(agents), "timing": phase,
        "next": ("start these agents together, then run graph" if agents else
                 "nothing for an agent to judge; run graph")}, indent=2, ensure_ascii=False))
    return 0


def phase_graph(args) -> int:
    run = pathlib.Path(args.run)
    missing = need(run, "match/auto.json")
    if missing:
        print(f"error: {missing}", file=sys.stderr)
        return 2
    started = time.time()
    problems: list[str] = []
    decisions = sorted(glob.glob(str(run / "match" / "decisions.*.json")))
    code, built, err = call(MATCH / "build_matches.py", "--auto", str(run / "match" / "auto.json"),
                            "--detections", str(run / "detections"), "--decisions", *decisions,
                            "--out", str(run / "matches.json"), "--force")
    if built is None:
        print(f"error: building the matches failed: {err}", file=sys.stderr)
        return 2
    problems += built.get("problems") or []
    code, checked, _ = call(MATCH / "check_matches.py", str(run / "matches.json"),
                            "--structures", str(run / "structure"))
    for line in (checked or {}).get("errors") or []:
        problems.append(f"matches gate: {line}")

    steps = [
        ("graph", HERE / "apply_matches.py", ["--matches", str(run / "matches.json"),
                                               "--structures", str(run / "structure"),
                                               "--detections", str(run / "detections"),
                                               "--out", str(run / "scene_graph.json"), "--force",
                                               *(["--registration", str(run / "registration.json")]
                                                 if (run / "registration.json").exists() else [])]),
        ("scores", HERE / "score_views.py", [str(run / "scene_graph.json"),
                                              "--out", str(run / "view_scores.json"), "--force"]),
        ("confusion", HERE / "make_confusion.py", ["--graph", str(run / "scene_graph.json"),
                                                    "--matches", str(run / "matches.json"),
                                                    "--scores", str(run / "view_scores.json"),
                                                    "--out", str(run / "confusion.json"), "--force"]),
    ]
    results = {}
    for name, script, rest in steps:
        code, body, err = call(script, *rest)
        results[name] = body
        if code not in (0,) and not (name == "graph" and code == 1 and body):
            problems.append(f"{name}: exit {code}: {err[:200]}")
        if code == 2:
            print(json.dumps({"phase": "graph", "problems": problems}, indent=2))
            return 2
        for line in (body or {}).get("problems") or []:
            problems.append(f"{name}: {line}")
    valid_code, valid, err = call(HERE / "validate_graph.py", str(run / "scene_graph.json"),
                                  "--manifest", str(run / "manifest.json"))
    for line in (valid or {}).get("errors") or []:
        problems.append(f"validate_graph: {line}")
    state = read_state(run)
    viewer_args = [str(run / "scene_graph.json"), "--manifest", str(run / "manifest.json"),
                   "--scores", str(run / "view_scores.json"), "--confusion", str(run / "confusion.json"),
                   "--embed", "--out", str(run / "viewer.html"), "--force"]
    if state.get("images_root"):
        viewer_args += ["--image-root", state["images_root"]]
    code, viewer, err = call(VIEW / "build_viewer.py", *viewer_args)
    if code != 0 or not viewer or not viewer.get("out"):
        problems.append(f"viewer: {err[:200] or 'could not be built'}")
    phase = finish(run, "graph", started)
    state = read_state(run)
    total = state["phases"].get("graph", {}).get("since_start")
    graph = results.get("graph") or {}
    # Physical objects, as a range: each identity group stands for between at_least and at_most
    # real things, whatever number of nodes it holds. Nodes outside every group count once.
    try:
        nodes = load(run / "scene_graph.json")
        groups = nodes.get("identity_groups") or []
        grouped = {m for g in groups for m in g.get("members") or []}
        single = len(nodes.get("nodes") or []) - len(grouped)
        physical = {"at_least": single + sum(int(g.get("at_least") or 0) for g in groups),
                    "at_most": single + sum(int(g.get("at_most") or 0) for g in groups)}
    except (OSError, ValueError):
        physical = None
    print(json.dumps({
        "phase": "graph", "objects": built.get("objects"),
        "matched_across_images": built.get("matched_across_images"),
        "physical_objects": physical,
        "unconfirmed": graph.get("unconfirmed"),
        "refusals": built.get("unresolved"), "corrections": built.get("corrections"),
        "identity_groups": graph.get("identity_groups"), "validate_graph_exit": valid_code,
        "viewer": (viewer or {}).get("out"), "problems": problems, "timing": phase,
        "total_seconds": total,
        "phases": {k: v.get("seconds") for k, v in state["phases"].items()}}, indent=2,
        ensure_ascii=False))
    for line in problems:
        print(f"warning: {line}", file=sys.stderr)
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="phase", required=True)
    for name in ("start", "detect", "verify-plan", "verify", "match-plan", "graph"):
        p = sub.add_parser(name)
        p.add_argument("--run", required=True, help="the run folder")
        if name == "start":
            p.add_argument("--images", nargs="+", required=True, help="image files or folders")
            p.add_argument("--mode", choices=("auto", "fine", "coarse"), default="auto",
                           help="Fine cuts each photograph into tiles and finds the small objects; "
                                "Coarse looks at each photograph whole and is faster. auto picks "
                                f"Fine up to {COARSE_ABOVE} images and Coarse above (default auto)")
            p.add_argument("--grid", default=None,
                           help="advanced: tiles per image, columns x rows, overriding --mode")
            p.add_argument("--long-edge", type=int, default=1568,
                           help="cap on the long edge of every picture an agent is shown")
    args = parser.parse_args(argv)
    # Labels and messages carry non-ASCII text; a piped Windows console would otherwise get cp1252.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    return {"start": phase_start, "detect": phase_detect, "verify-plan": phase_verify_plan,
            "verify": phase_verify, "match-plan": phase_match_plan,
            "graph": phase_graph}[args.phase](args)


if __name__ == "__main__":
    sys.exit(main())
