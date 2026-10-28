---
name: marso-blender-scene-assets
description: Generate every planned asset of a photographed scene through Marso from Blender. Use when an asset_plan.json and its reference crops exist and the user wants the objects made in a Marso Studio project - an object-mode reference image per asset, a 3D mesh, PBR, and a minted, real-scale result ready to import. Stops for review after the plan and after the reference images. Placing the results in Blender belongs to marso-blender-place-scene.
license: Proprietary
---

# Generate a scene's assets with Marso

Turn a reviewed asset plan into minted Marso assets, one per unique asset, through the Marso Blender add-on. For each asset the chain is: upload the crop and make an object-mode reference image from it, then a 3D mesh and PBR from that image, then wait for the asset to be minted (simulation-ready, at real-world scale). Nothing is placed in the scene here.

Inputs, from the `marso-scene-graph` skill's run folder: `asset_plan.json`, and `references/index.json` with each asset's `crop.png` and `brief.json`. If they do not exist, run that skill first. If the Blender connection or the Marso add-on is missing or not configured, use `marso-blender-setup` when installed; do not work around it.

## Before the first job

1. **The Studio project name comes from the user.** Ask for it if they did not give one; never pick one yourself. Create it with `create_studio_project {name}`, follow the job, read `save_to_state`, and select it with `set_save_project {project_id}` if it is not already selected. Record the returned id. Read [studio chain](references/studio-chain.md) for every command used.
2. **Settings.** Model `tripo_h3_1`, `polygon_count` 40000 and texture `standard`, unless the plan gives an asset its own `polygon_count` or the user says otherwise. Read the model's live options before sending any value, and clip a budget to an offered one.
3. **Start the record.** `python "<skill>/scripts/manifest.py" init "<run>/asset_plan.json" --references "<run>/references/index.json" --out "runs/<job>/assets.json" --project "<name>"`. It lists every asset with a crop, its prompt and settings, and prints what it left out and why.
4. **Checkpoint 1, the plan.** Stop and review with the user before anything is generated. Read [checkpoints](references/checkpoints.md).

## Reference images

For each asset that `manifest.py pending runs/<job>/assets.json --stage reference` lists, call `scene_reference {label, crop_path, prompt, row}` with the brief's prompt unchanged, and record the job id with `manifest.py record ... --stage reference <asset_id> --job <id>`. Run at most four jobs at once; start the next one as one finishes. Follow each with `get_job` in a later tool call and record its result (`--result` or `--json`) or its failure (`--error`).

**Checkpoint 2, the reference images.** Stop. Show the user every reference image beside its crop, and record their decision with `manifest.py review`. A rejected image goes back to `reference` with the user's note worked into the prompt; never send a mesh job from an image the user has not approved.

## Meshes, PBR and minting

For each asset `--stage mesh` lists, call `scene_mesh {generation_node_id, image_asset_id, model, polygon_count, texture, label}` with the asset's recorded node ids and settings, again at most four at once, and record each job and result. The result carries the `pbr_asset_id`.

Then poll `mint_status {asset_ids}` with the ids `--stage mint` prints, record each answer with `manifest.py record ... --stage mint --json '<result>'`, and keep polling at a modest interval (a minute or two between calls) until every asset is `minted` or `failed`, or the user stops you. Report each asset that is not minted and its state. Do not regenerate a `failed` or slow asset without the user's say.

## Hard rules

- One job per call, followed by `get_job` in a later call. Never block Blender's main thread with `wait_job`, sleep or a polling loop. A timeout is not permission to resubmit: check the job and the record first.
- The API has no negative prompt and no crop or mask field. Exclusions are instructions in the prompt; the crop reaches the image node as a linked image named `@crop`. Do not invent parameters for either.
- Never force a minted asset to the graph's size. The minted size is the authority; a disagreement is a flag for the placement step.
- Every result goes into `assets.json` as it arrives, so an interrupted run resumes from `pending` rather than from memory.
- Add no pricing, credit or spending steps.

## Deliver

Report the Studio project and its id, how many assets reached each stage, every asset not minted with its state, the failures and their errors, and where `assets.json` is. Hand over to `marso-blender-place-scene` for import and placement. State what was not checked: reference images you did not open, meshes you did not inspect.
