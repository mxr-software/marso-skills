---
name: marso-scene-graph
description: Plan Marso asset work from a finished scene graph. Use when a scene_graph.json already exists and the user wants the list of unique assets and instance counts, a cropped reference and brief for each object, or a decision on what to generate, model in the application, or reuse from the library. Produces the plan and briefs; marso-blender-scene-assets or the marso entry skill performs any generation.
license: Proprietary. See LICENSE.txt in this skill folder.
---

# Plan assets from a scene graph

A scene graph is a finished inventory of a photographed scene: every object has a `global_id`, a label, a size estimate, the thing that holds it, and a box in each image that shows it. This skill turns that inventory into the work list Marso needs. It does not generate anything, and it does not re-detect objects; if the graph is wrong, fix the graph first.

Expect the `scene-decompose/scene-graph@1` layout: `nodes[]` with `parent`, `relation`, `size_m`, `views[]`; `clusters[]` of kind `instances` or `variants`; `identity_groups[]` with `at_least` and `at_most`; `parent_conflicts[]`. A `manifest.json` beside it maps each `image_id` to a file and its pixel size. An optional `view_scores.json` names the best view of each object.

## Four questions this answers

1. How many unique assets are there, and how many instances of each? Read [asset plan](references/asset-plan.md).
2. What is cropped and said for each one? Read [reference brief](references/reference-brief.md).
3. Is each asset generated, modelled, reused from the library or skipped? Read [route](references/route.md).
4. What metadata travels with the asset into generation and the application? Read [metadata](references/metadata.md).

In shell examples, `python` means an installed Python 3.10+ interpreter. Check its version first; on Windows, use `py -3.13` or another installed compatible version if the default `python` is older. Blender-only scripts run in Blender instead.

## Workflow

Work from the user's project folder, with the run folder that holds the graph. Run the scripts by their full quoted path; `<skill>` below stands for this skill folder's path. They need Python 3.10+, and `crop_objects.py` needs Pillow.

1. Build the plan. `python "<skill>/scripts/plan_assets.py" "<run>/scene_graph.json" --scores "<run>/view_scores.json" --out "<run>/asset_plan.json"` writes one entry per unique asset with its route, count, floor and ceiling, members, best view and flags, and prints a summary. Omit `--scores` when there is no scores file; the script ranks views itself. Add `--polycount by-size` (or a number such as `40000`) to write a default polygon budget per generated asset; read [polycount](references/polycount.md).
2. Review the plan with the user before cropping. Walk through the summary, every flagged asset, every route the user might disagree with, and every entry under `unconfirmed`: each is probably a wide view's misreading of something already planned, and becomes an asset only if the user says it is a separate thing. Record changes by editing `asset_plan.json`; the route and count fields are the agreement, not the script's opinion. Add one line per decision to its `review` list, saying who decided: when the user cannot be asked, make the call yourself, record it there as yours, and say so when you deliver.
3. Crop the references. `python "<skill>/scripts/crop_objects.py" "<run>/scene_graph.json" --manifest "<run>/manifest.json" --plan "<run>/asset_plan.json" --out "<run>/references"` writes `<asset_id>/crop.png`, `search.png` (the subject alone, unmarked, for a library search) and `brief.json` for every asset the plan routes to generation, plus an `index.json`. `--ids` picks assets by `asset_id` or `global_id` whatever their route, so a modelled asset can have a reference too; `--pad` changes the margin, the subject is outlined in red on an unmasked crop by default, `--mask-children` or `--exclude-parent` opt in to masking, and runs with different flags add to the same `index.json`. Run it from the project folder the decompose run used; `--image-root` is only for photographs that have moved. Requires Pillow.
4. Hand over. Each brief names the subject, its real size and everything else in the crop; its `prompt` is written for an object-mode image node shown the crop as `@crop`. In Blender, `marso-blender-scene-assets` runs the whole plan through Marso when it is installed, looking for each asset in the account's library first. Otherwise give the brief and crop to the `marso` entry skill's generation route when it is installed; it chooses the generator and settings from live capabilities. Modelled assets go to the application's modelling skill with the same metadata block. Do not invent a generation command when no route is installed; deliver the plan and briefs as the handoff.

## Hard rules

- Every count resolves to `global_id`s. An asset with count 3 lists three members; never a bare number.
- Identity groups give a floor and a ceiling. Report `count_at_least` and `count_at_most` as they stand; do not collapse them by guessing which view showed which object. Only the user, or a better view, closes the gap.
- A crop is evidence of identity, material and camera, not a pose or composition to copy. The generator must be asked for the whole object; the crop can show it cut by the frame, hidden behind a child or resting on a parent.
- Anchors (parent `null`: ground, walls, ceiling) are not assets. They are listed separately so the application can build the room shell.
- Add no pricing, credit or spending steps. The plan is non-generating.
- Write only into the run folder. Never modify the scene graph, the manifest or the source images.

## Deliver

Report the number of unique assets and the instance range (`instances_at_least` to `instances_at_most`), the route split, the unconfirmed readings left out, the assets flagged for the user, the decisions in `review`, and where `asset_plan.json`, the crops and briefs were written. State what was not checked: a crop has not been viewed unless you opened it, and the plan has not been validated against the room unless the user confirmed it.
