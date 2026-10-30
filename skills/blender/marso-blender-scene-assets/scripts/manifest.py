#!/usr/bin/env python3
"""Keep the per-asset record of a scene's generation run: runs/<job>/assets.json.

Usage:
    manifest.py init <asset_plan.json> --references <references/index.json> --out <assets.json>
                     [--project NAME] --project-id ID --model MODEL [--polycount COUNT] [--texture OPTION]
                     [--ids a001 a002 ...] [--skip-library] [--force]
    manifest.py record <assets.json> --stage library <asset_id> (--result found.json | --json '{...}')
    manifest.py choose <assets.json> --reuse a001=<pbr_asset_id> ... | --make a002 ... [--note TEXT]
    manifest.py record <assets.json> --stage reference|mesh|import <asset_id>
                       (--job JOB_ID | --result result.json | --json '{...}' | --error TEXT)
    manifest.py record <assets.json> --stage mint (--result status.json | --json '{...}')
    manifest.py review <assets.json> --approve a001 a002 ... | --reject a003 [--note TEXT]
    manifest.py bind-project <assets.json> --project-id ID
    manifest.py check-project <assets.json> --state save_to_state.json
    manifest.py pending <assets.json> [--stage library|choose|reference|review|mesh|mint|import]

`init` makes one entry per asset that has a crop in the references index, with the
plan's id, label, count, members, crop and brief paths and its prompt. Each asset starts
with a library check (skipped with --skip-library): `record --stage library` stores the
add-on's find_in_library candidates, and `choose` records the user's decision to reuse a
library asset (by its pbr_asset_id, which must be one of the candidates) or make a new one.
A reused asset skips the reference image and the mesh and goes on to minting and import.
`record` stores a submitted job id, a finished job's result, or a failure. `review` records
the user's decision on each reference image; only approved references go on to meshes.
`pending` prints, for each stage, the assets still waiting and the jobs to follow up.
Standard library only.

Exit codes: 0 done, 1 something was wrong with the inputs (an unknown asset, a result
missing its fields, an existing output), 2 a JSON input could not be read.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys
import uuid

SCHEMA = "marso/scene-assets@1"
STAGES = ("library", "choose", "handoff", "reference", "review", "mesh", "mint", "import")
MINT_STATES = ("minted", "minting", "failed", "not_minted")

# The fields each finished job must return, as the add-on's bridge commands report them.
RESULT_FIELDS = {
    "library": ("results",),
    "reference": ("crop_asset_id", "image_node_id", "generation_node_id", "image_asset_id", "image_path"),
    "mesh": ("mesh_node_id", "pbr_node_id", "pbr_asset_id"),
    "import": ("objects", "dimensions_m"),
}


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


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


def write_json(path: pathlib.Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def unwrap(result):
    """Accept a bare result or a get_job snapshot that carries it under `result`."""
    if isinstance(result, dict) and isinstance(result.get("result"), dict) and "status" in result:
        return result["result"]
    # mint_status answers {"status": {pbr_asset_id: state}}: the mapping is what gets recorded.
    if isinstance(result, dict) and set(result) == {"status"} and isinstance(result["status"], dict):
        return result["status"]
    return result


# What is kept of each find_in_library result: enough to show it and to reuse it.
CANDIDATE_FIELDS = ("name", "verdict", "image_score", "text_score", "pbr_asset_id", "mesh_asset_id",
                    "project_ids", "thumbnail_path")
CANDIDATES_KEPT = 5


def new_entry(asset: dict, row: dict, brief: dict | None, settings: dict, library: bool = True) -> dict:
    return {
        "asset_id": asset["asset_id"],
        "global_id": asset.get("global_id"),
        "label": asset.get("label"),
        "route": asset.get("route"),
        "creation_choice": asset.get("creation_choice"),
        "count": asset.get("count"),
        "count_at_least": asset.get("count_at_least"),
        "count_at_most": asset.get("count_at_most"),
        "members": asset.get("members") or [],
        "size_m": asset.get("size_m"),
        "crop": row.get("crop"),
        "search_crop": row.get("search_crop"),
        "brief": row.get("brief"),
        "prompt": (brief or {}).get("prompt"),
        "settings": {key: value for key, value in {
            "model": asset.get("model", settings["model"]),
            "polygon_count": asset.get("polygon_count", settings["polygon_count"]),
            "texture": asset.get("texture", settings["texture"]),
        }.items() if value is not None},
        "library": {"status": "pending"} if library else {"status": "make", "note": "library check skipped"},
        "reference": {"status": "pending"},
        "review": {"status": "pending"},
        "mesh": {"status": "pending"},
        "pbr_asset_id": None,
        "minted": "not_minted",
        "import": {"status": "pending"},
    }


def cmd_init(args) -> int:
    plan = read_json(pathlib.Path(args.plan))
    index_path = pathlib.Path(args.references)
    index = read_json(index_path)
    if plan is None or index is None:
        return 2
    if not isinstance(plan.get("assets"), list) or not isinstance(index.get("assets"), list):
        print("error: the plan or the references index has no assets list", file=sys.stderr)
        return 1
    out = pathlib.Path(args.out)
    if out.exists() and not args.force:
        print(f"error: {out.as_posix()} exists; pass --force to start again", file=sys.stderr)
        return 1

    if not args.project_id or not args.project_id.strip():
        print("error: --project-id must be the verified Save to project id", file=sys.stderr)
        return 1

    if args.polycount is not None and args.polycount <= 0:
        print("error: --polycount must be positive", file=sys.stderr)
        return 1
    settings = {"model": args.model, "polygon_count": args.polycount, "texture": args.texture}
    plan_assets = {a.get("asset_id"): a for a in plan["assets"] if a.get("asset_id")}
    wanted = set(args.ids or [])
    entries, problems = [], []
    for row in index["assets"]:
        asset_id = row.get("asset_id")
        if wanted and asset_id not in wanted:
            continue
        asset = plan_assets.get(asset_id)
        if asset is None:
            problems.append(f"{asset_id}: in the references index but not in the plan")
            continue
        if asset.get("route") == "skip":
            problems.append(f"{asset_id}: not selected for creation; left out")
            continue
        if asset.get("route") not in ("generate", None) and not wanted and not plan.get("selection_mode"):
            problems.append(f"{asset_id}: routed {asset.get('route')!r} in the plan; left out "
                            "(name it with --ids to record its specialist handoff)")
            continue
        brief = None
        if row.get("brief"):
            brief_path = pathlib.Path(row["brief"])
            if not brief_path.is_absolute() and not brief_path.exists():
                brief_path = index_path.parent / asset_id / "brief.json"
            brief = read_json(brief_path) if brief_path.exists() else None
        if brief is None or not brief.get("prompt"):
            problems.append(f"{asset_id}: no brief with a prompt; rerun the crop step for it")
        search = (asset.get("creation_choice") or {}).get("search_library", True)
        entries.append(new_entry(asset, row, brief, settings, library=not args.skip_library and search))
    if any(e["route"] == "generate" and not str(e["settings"].get("model", "")).strip() for e in entries):
        print("error: --model or per-asset model must be selected from live capabilities and user preferences", file=sys.stderr)
        return 1
    missing = sorted(a for a, asset in plan_assets.items() if (asset.get("route") == "generate"
                     or (plan.get("selection_mode") and asset.get("route") != "skip"))
                     and a not in {e["asset_id"] for e in entries} and (not wanted or a in wanted))
    for asset_id in missing:
        problems.append(f"{asset_id}: selected for creation but has no crop in the references index; crop all selected routes")
    if not entries:
        print("error: no assets to record; check the references index and --ids", file=sys.stderr)
        for line in problems:
            print(f"  {line}", file=sys.stderr)
        return 1

    entries.sort(key=lambda e: e["asset_id"])
    for row, entry in enumerate(entries):
        entry["row"] = row
    doc = {
        "schema": SCHEMA,
        "graph_key": plan.get("graph_key"),
        "project": args.project,
        "project_id": args.project_id,
        "run_id": str(uuid.uuid4()),
        "created": now(),
        "plan": pathlib.Path(args.plan).as_posix(),
        "references": index_path.as_posix(),
        "defaults": settings,
        "assets": sorted(entries, key=lambda e: e["asset_id"]),
        "log": [],
    }
    write_json(out, doc)
    print(json.dumps({"out": out.as_posix(), "assets": len(entries), "problems": problems}, indent=2))
    return 0


def load(path: str):
    """(exit code, doc, assets by id); the code is non-zero when the file is unusable."""
    doc = read_json(pathlib.Path(path))
    if doc is None:
        return 2, None, None
    if not isinstance(doc, dict) or not isinstance(doc.get("assets"), list):
        print("error: not an assets.json: no assets list", file=sys.stderr)
        return 1, None, None
    return 0, doc, {a["asset_id"]: a for a in doc["assets"]}


def record_mint(doc: dict, assets: dict, result) -> list[str]:
    """mint_status returns {pbr_asset_id: state}; match each to the asset that produced it."""
    result = unwrap(result)
    if isinstance(result.get("statuses"), dict):
        result = result["statuses"]
    by_pbr = {}
    for asset in assets.values():
        if asset.get("pbr_asset_id"):
            by_pbr.setdefault(asset["pbr_asset_id"], []).append(asset)
    problems = []
    for pbr_id, state in result.items():
        matching = by_pbr.get(pbr_id)
        if not matching:
            problems.append(f"{pbr_id}: no asset in this run has that pbr_asset_id")
            continue
        if state not in MINT_STATES:
            problems.append(f"{pbr_id}: unknown mint state {state!r}")
            continue
        for asset in matching:
            asset["minted"] = state
    return problems


def record_library(args, doc: dict, asset: dict, result) -> int:
    """Store the find_in_library candidates for the user to choose from; nothing is decided here."""
    if args.job:
        print("error: find_in_library answers at once; record its result, not a job", file=sys.stderr)
        return 1
    if args.error:
        asset["library"] = {"status": "failed", "error": args.error, "at": now()}
    elif result is None:
        print("error: give --result, --json or --error", file=sys.stderr)
        return 1
    else:
        result = unwrap(result)
        if not isinstance(result.get("results"), list):
            print("error: the library result has no results list", file=sys.stderr)
            return 1
        candidates = [{k: r.get(k) for k in CANDIDATE_FIELDS} for r in result["results"][:CANDIDATES_KEPT]
                      if isinstance(r, dict) and r.get("pbr_asset_id")]
        asset["library"] = {"status": "checked", "query": result.get("query"), "image": result.get("image"),
                            "candidates": candidates, "at": now()}
    doc["log"].append({"at": now(), "asset_id": args.asset_id, "stage": "library",
                       "status": asset["library"]["status"]})
    write_json(pathlib.Path(args.manifest), doc)
    print(json.dumps({"asset_id": args.asset_id, "stage": "library", "status": asset["library"]["status"],
                      "candidates": [[c["name"], c["verdict"]] for c in asset["library"].get("candidates", [])]},
                     indent=2))
    return 0


def cmd_choose(args) -> int:
    code, doc, assets = load(args.manifest)
    if code:
        return code
    reuse, problems = {}, []
    for item in args.reuse or []:
        asset_id, _, pbr_id = item.partition("=")
        if not pbr_id:
            problems.append(f"{item}: write it as <asset_id>=<pbr_asset_id>")
        else:
            reuse[asset_id] = pbr_id
    make = list(args.make or [])
    if not reuse and not make and not problems:
        problems.append("give --reuse, --make or both")
    for asset_id in [*reuse, *make]:
        if asset_id not in assets:
            problems.append(f"{asset_id}: no such asset")
    both = sorted(set(reuse) & set(make))
    if both:
        problems.append(f"both reused and made: {', '.join(both)}")
    for asset_id, pbr_id in reuse.items():
        library = (assets.get(asset_id) or {}).get("library") or {}
        if asset_id in assets and pbr_id not in {c.get("pbr_asset_id") for c in library.get("candidates") or []}:
            problems.append(f"{asset_id}: {pbr_id} is not one of its library candidates")
    if problems:
        for line in problems:
            print(f"error: {line}", file=sys.stderr)
        return 1
    for asset_id, pbr_id in reuse.items():
        asset = assets[asset_id]
        library = asset["library"]
        chosen = next(c for c in library["candidates"] if c.get("pbr_asset_id") == pbr_id)
        library.update(status="reuse", chosen=chosen, note=args.note, decided=now())
        asset["pbr_asset_id"] = pbr_id
        asset["minted"] = "not_minted"  # mint_status says whether the library asset is ready
        asset["import"] = {"status": "pending"}
        for stage in ("reference", "review", "mesh"):
            asset[stage] = {"status": "skipped", "reason": "reused from the library"}
    for asset_id in make:
        asset = assets[asset_id]
        library = asset.setdefault("library", {})
        if library.get("status") == "reuse":
            # Back to making it: the reused asset's id goes, and the chain starts from the reference.
            asset["pbr_asset_id"], asset["minted"] = None, "not_minted"
            for stage in ("reference", "review", "mesh", "import"):
                asset[stage] = {"status": "pending"}
        library.update(status="make", note=args.note, decided=now())
        library.pop("chosen", None)
    doc["log"].append({"at": now(), "stage": "choose", "reuse": reuse, "make": make, "note": args.note})
    write_json(pathlib.Path(args.manifest), doc)
    print(json.dumps({"reuse": reuse, "make": make}, indent=2))
    return 0


def cmd_record(args) -> int:
    code, doc, assets = load(args.manifest)
    if code:
        return code
    result = None
    if args.result:
        result = read_json(pathlib.Path(args.result))
        if result is None:
            return 2
    elif args.json is not None:
        try:
            result = json.loads(args.json)
        except json.JSONDecodeError as exc:
            print(f"error: --json is not valid JSON: {exc}", file=sys.stderr)
            return 2
    if result is not None and not isinstance(result, dict):
        print("error: the result must be a JSON object", file=sys.stderr)
        return 1

    if args.stage == "mint":
        if result is None:
            print("error: --stage mint needs the mint_status result (--result or --json)", file=sys.stderr)
            return 1
        problems = record_mint(doc, assets, result)
        doc["log"].append({"at": now(), "stage": "mint", "result": unwrap(result)})
        write_json(pathlib.Path(args.manifest), doc)
        print(json.dumps({"recorded": "mint", "problems": problems}, indent=2))
        return 1 if problems else 0

    if not args.asset_id:
        print(f"error: --stage {args.stage} needs an asset id", file=sys.stderr)
        return 1
    asset = assets.get(args.asset_id)
    if asset is None:
        print(f"error: no asset {args.asset_id} in {args.manifest}", file=sys.stderr)
        return 1
    if args.stage == "library":
        return record_library(args, doc, asset, result)
    if args.stage in ("reference", "mesh") and asset.get("route") not in ("generate", None):
        print("error: this creation route requires a specialist handoff, not a generation job", file=sys.stderr)
        return 1
    stage = asset[args.stage]
    if args.job:
        if stage.get("status") == "submitted":
            if stage.get("job_id") != args.job:
                print("error: reconcile the submitted job before replacing it", file=sys.stderr)
                return 1
            print(json.dumps({"asset_id": args.asset_id, "stage": args.stage, "status": "submitted"}))
            return 0
        if stage.get("status") not in {None, "pending"}:
            asset.setdefault("attempts", {}).setdefault(args.stage, []).append(dict(stage))
        asset[args.stage] = stage = {"status": "submitted", "job_id": args.job, "submitted": now()}
        if args.stage == "reference":
            asset["review"] = {"status": "pending"}  # a new image needs a new look
    elif args.error:
        stage.update(status="failed", error=args.error, at=now())
    elif result is not None:
        result = unwrap(result)
        missing = [f for f in RESULT_FIELDS[args.stage] if f not in result]
        if missing:
            print(f"error: the {args.stage} result has no {', '.join(missing)}", file=sys.stderr)
            return 1
        stage.update(result)
        stage.update(status="done", at=now())
        if args.stage == "mesh":
            asset["pbr_asset_id"] = result["pbr_asset_id"]
        if args.stage == "import" and "minted" in result:
            asset["minted"] = "minted" if result["minted"] is True else asset["minted"]
    else:
        print("error: give --job, --result, --json or --error", file=sys.stderr)
        return 1
    doc["log"].append({"at": now(), "asset_id": args.asset_id, "stage": args.stage,
                       "status": stage["status"], "job_id": stage.get("job_id"),
                       "record": dict(stage)})
    write_json(pathlib.Path(args.manifest), doc)
    print(json.dumps({"asset_id": args.asset_id, "stage": args.stage, "status": stage["status"]}, indent=2))
    return 0


def cmd_review(args) -> int:
    code, doc, assets = load(args.manifest)
    if code:
        return code
    unknown = [a for a in (args.approve or []) + (args.reject or []) if a not in assets]
    if unknown:
        print(f"error: no such assets: {', '.join(unknown)}", file=sys.stderr)
        return 1
    not_ready = [a for a in args.approve or [] if assets[a]["reference"].get("status") != "done"]
    if not_ready:
        print(f"error: no finished reference image to approve for: {', '.join(not_ready)}", file=sys.stderr)
        return 1
    for asset_id in args.approve or []:
        assets[asset_id]["review"] = {"status": "approved", "note": args.note, "at": now()}
    for asset_id in args.reject or []:
        assets[asset_id]["review"] = {"status": "rejected", "note": args.note, "at": now()}
    doc["log"].append({"at": now(), "stage": "review", "approved": args.approve or [],
                       "rejected": args.reject or [], "note": args.note})
    write_json(pathlib.Path(args.manifest), doc)
    print(json.dumps({"approved": args.approve or [], "rejected": args.reject or []}, indent=2))
    return 0


def pending(assets: dict) -> dict:
    out = {stage: [] for stage in STAGES}
    running = {stage: [] for stage in ("reference", "mesh", "import")}
    failed = {stage: [] for stage in ("reference", "mesh", "import")}
    for asset_id, asset in sorted(assets.items()):
        for stage in ("reference", "mesh", "import"):
            status = asset[stage].get("status")
            if status == "submitted":
                running[stage].append({"asset_id": asset_id, "job_id": asset[stage].get("job_id")})
            elif status == "failed":
                failed[stage].append({"asset_id": asset_id, "error": asset[stage].get("error")})
        ref, review, mesh = asset["reference"], asset["review"], asset["mesh"]
        library = (asset.get("library") or {"status": "make"}).get("status")
        if library in ("pending", "failed"):
            out["library"].append(asset_id)
        elif library == "checked":
            out["choose"].append(asset_id)
        elif asset.get("route") not in ("generate", None):
            out["handoff"].append(asset_id)
        elif library == "reuse":
            if asset.get("minted") not in ("minted", "failed"):
                out["mint"].append(asset_id)
            elif asset.get("minted") == "minted" and asset["import"].get("status") in ("pending", "failed"):
                out["import"].append(asset_id)
        elif ref.get("status") in ("pending", "failed") or (
                ref.get("status") == "done" and review.get("status") == "rejected"):
            out["reference"].append(asset_id)
        elif ref.get("status") == "done" and review.get("status") == "pending":
            out["review"].append(asset_id)
        elif review.get("status") == "approved" and mesh.get("status") in ("pending", "failed"):
            out["mesh"].append(asset_id)
        elif mesh.get("status") == "done" and asset.get("minted") not in ("minted", "failed"):
            out["mint"].append(asset_id)
        elif asset.get("minted") == "minted" and asset["import"].get("status") in ("pending", "failed"):
            out["import"].append(asset_id)
    mint_ids = sorted({assets[a]["pbr_asset_id"] for a in out["mint"] if assets[a].get("pbr_asset_id")})
    return {
        "pending": out,
        # What to send find_in_library for each asset still to check: its label and its search crop.
        "library_searches": [{"asset_id": a, "query": assets[a].get("label"),
                              "image_path": assets[a].get("search_crop")} for a in out["library"]],
        "handoffs": [{"asset_id": a, "route": assets[a].get("route"),
                      "creation_choice": assets[a].get("creation_choice"),
                      "chosen_library_asset": (assets[a].get("library") or {}).get("chosen")}
                     for a in out["handoff"]],
        "reused": sorted(a for a, asset in assets.items() if (asset.get("library") or {}).get("status") == "reuse"),
        "running": running,
        "failed": failed,
        "mint_status_asset_ids": mint_ids,
        "mint_failed": sorted(a for a, asset in assets.items() if asset.get("minted") == "failed"),
        "done": sorted(a for a, asset in assets.items() if asset["import"].get("status") == "done"),
    }


def cmd_pending(args) -> int:
    code, doc, assets = load(args.manifest)
    if code:
        return code
    report = pending(assets)
    if not doc.get("project_id"):
        print("error: legacy record has no project_id; verify its original project and use bind-project", file=sys.stderr)
        return 1
    if args.stage:
        report = {"stage": args.stage, "pending": report["pending"][args.stage],
                  **({"running": report["running"][args.stage], "failed": report["failed"][args.stage]}
                     if args.stage in report["running"] else {}),
                  **({"library_searches": report["library_searches"]} if args.stage == "library" else {}),
                  **({"handoffs": report["handoffs"]} if args.stage == "handoff" else {}),
                  **({"mint_status_asset_ids": report["mint_status_asset_ids"],
                      "mint_failed": report["mint_failed"]} if args.stage == "mint" else {})}
    report.update(project=doc.get("project"), project_id=doc["project_id"], run_id=doc.get("run_id"))
    print(json.dumps(report, indent=2))
    return 0


def cmd_project(args) -> int:
    code, doc, assets = load(args.manifest)
    if code:
        return code
    if args.command == "bind-project":
        if not args.project_id.strip():
            print("error: project id must not be blank", file=sys.stderr)
            return 1
        if doc.get("project_id") and doc["project_id"] != args.project_id:
            print("error: this record belongs to another project; start a separate run", file=sys.stderr)
            return 1
        doc["project_id"] = args.project_id
        doc.setdefault("run_id", str(uuid.uuid4()))
        for row, asset in enumerate(doc["assets"]):
            asset.setdefault("row", row)
        write_json(pathlib.Path(args.manifest), doc)
        print(json.dumps({"project_id": doc["project_id"], "run_id": doc["run_id"]}))
        return 0
    state = read_json(pathlib.Path(args.state))
    if state is None:
        return 2
    if not isinstance(state, dict):
        print("error: expected a save_to_state object", file=sys.stderr)
        return 1
    selected = (unwrap(state).get("save_to") or {}).get("project_id")
    ok = bool(doc.get("project_id")) and selected == doc["project_id"]
    print(json.dumps({"matches": ok, "project_id": doc.get("project_id"), "selected": selected}))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="start assets.json from the plan and the references index")
    p.add_argument("plan", help="asset_plan.json")
    p.add_argument("--references", required=True, help="references/index.json from the crop step")
    p.add_argument("--out", required=True, help="runs/<job>/assets.json")
    p.add_argument("--project", help="the Marso Studio project name the user gave")
    p.add_argument("--project-id", help="stable project id from save_to_state")
    p.add_argument("--model", help="live-selected model; required for generated entries without a plan override")
    p.add_argument("--polycount", type=int,
                   help="used where the plan gives no polygon_count")
    p.add_argument("--texture", help="omit when unsupported; no model-specific default is injected")
    p.add_argument("--ids", nargs="*", help="only these asset ids")
    p.add_argument("--skip-library", action="store_true", help="make every asset without a library check")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("record", help="record a submitted job, a finished result or a failure")
    p.add_argument("manifest", help="assets.json")
    p.add_argument("asset_id", nargs="?")
    p.add_argument("--stage", required=True, choices=("library", "reference", "mesh", "mint", "import"))
    group = p.add_mutually_exclusive_group()
    group.add_argument("--job", help="the job id the command returned")
    group.add_argument("--result", help="a JSON file holding the job result")
    group.add_argument("--json", help="the job result as a JSON string")
    group.add_argument("--error", help="why the job failed")
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("choose", help="record the user's decision to reuse a library asset or make one")
    p.add_argument("manifest", help="assets.json")
    p.add_argument("--reuse", nargs="*", help="<asset_id>=<pbr_asset_id> of a library candidate")
    p.add_argument("--make", nargs="*", help="asset ids to make despite, or for want of, a candidate")
    p.add_argument("--note")
    p.set_defaults(func=cmd_choose)

    p = sub.add_parser("review", help="record the user's decision on reference images")
    p.add_argument("manifest", help="assets.json")
    p.add_argument("--approve", nargs="*")
    p.add_argument("--reject", nargs="*")
    p.add_argument("--note")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("pending", help="what is waiting at each stage")
    p.add_argument("manifest", help="assets.json")
    p.add_argument("--stage", choices=STAGES)
    p.set_defaults(func=cmd_pending)

    p = sub.add_parser("bind-project", help="bind a legacy record to its verified original project")
    p.add_argument("manifest")
    p.add_argument("--project-id", required=True)
    p.set_defaults(func=cmd_project)
    p = sub.add_parser("check-project", help="compare a saved save_to_state response with this run")
    p.add_argument("manifest")
    p.add_argument("--state", required=True)
    p.set_defaults(func=cmd_project)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
