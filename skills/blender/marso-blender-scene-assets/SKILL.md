---
name: marso-blender-scene-assets
description: "Generate planned scene assets with the Marso Blender add-on: check library reuse, create references and meshes, then PBR and mint. Use a scene asset plan; requires supporting scene commands."
license: Proprietary. See LICENSE.txt in this skill folder.
---

# Generate a scene's assets with Marso

Turn a reviewed asset plan into minted Marso assets, one per unique asset, through the Marso Blender add-on. Each asset is first looked for in the account's library; one the user chooses to reuse skips straight to minting. For each asset still to make, the chain is: upload the crop and make an object-mode reference image from it, then a 3D mesh and PBR from that image, then wait for the asset to be minted (simulation-ready, at real-world scale). Nothing is placed in the scene here.

Inputs, from the `marso-scene-graph` skill's run folder: `asset_plan.json`, and `references/index.json` with each asset's `crop.png`, `search.png` and `brief.json`. If they do not exist, run that skill first. `<skill>` in the commands below stands for this skill folder's path; its script needs Python 3.10+ and nothing else. If the Blender connection or the Marso add-on is missing or not configured, use `marso-blender-setup` when installed; do not work around it.

In shell examples, `python` means an installed Python 3.10+ interpreter. Check its version first; on Windows, use `py -3.13` or another installed compatible version if the default `python` is older. Blender-only scripts run in Blender instead.

## Before the first job

1. **Resolve the relevant Studio project.** Reuse the user-designated project by id when it exists. If none is identified, ask whether to use an existing project or create one, honouring any earlier instruction to create it. Use `create_studio_project {name}` only for a new project; follow the job and read `save_to_state`. Select the intended id with `set_save_project {project_id}` and verify it. Never silently accept a generic Blender destination. Read [studio chain](references/studio-chain.md) for every command used.
2. **Settings.** Model `tripo_h3_1`, `polygon_count` 40000 and texture `standard`, unless the plan gives an asset its own `polygon_count` or the user says otherwise. Read the model's live options before sending any value, and clip a budget to an offered one.
3. **Start the record.** `python "<skill>/scripts/manifest.py" init "<run>/asset_plan.json" --references "<run>/references/index.json" --out "runs/<job>/assets.json" --project "<name>" --project-id "<verified-id>"`. It stores the stable project/run ids and canvas rows, lists every asset with a crop, its prompt and settings, and prints what it left out and why.
4. **Check the library.** For each asset `manifest.py pending runs/<job>/assets.json --stage library` lists, call `find_in_library` with its label and `search.png` and record the answer with `manifest.py record ... --stage library`. Read [library check](references/library-check.md).
5. **Checkpoint 1, the plan.** Stop and review with the user before anything is generated, the library candidates included, with their thumbnails. Record the user's reuse-or-make decisions with `manifest.py choose`. Read [checkpoints](references/checkpoints.md).

Before any reference or mesh submission, including after a pause, read `save_to_state`, save its response locally and run `manifest.py check-project runs/<job>/assets.json --state "<state.json>"`. On mismatch, reselect the recorded id and verify again. For a legacy record without an id, first verify its original project and use `manifest.py bind-project ... --project-id "<id>"`; never reinitialise a running record to resume it.

## Reference images

For each asset that `manifest.py pending runs/<job>/assets.json --stage reference` lists, call `scene_reference {label, crop_path, prompt, row}` with the brief's prompt unchanged, and record the job id with `manifest.py record ... --stage reference <asset_id> --job <id>`. Run at most four jobs at once; start the next one as one finishes. Follow each with `get_job` in a later tool call and record its result (`--result` or `--json`) or its failure (`--error`).

**Checkpoint 2, the reference images.** Stop. Show the user every reference image beside its crop, and record their decision with `manifest.py review`. A rejected image goes back to `reference` with the user's note worked into the prompt; never send a mesh job from an image the user has not approved.

## Meshes, PBR and minting

For each asset `--stage mesh` lists, call `scene_mesh {generation_node_id, image_asset_id, model, polygon_count, texture, label, row}` with the asset's recorded node ids, stable `row` and settings, again at most four at once, and record each job and result. The result carries the `pbr_asset_id`.

Then poll `mint_status {asset_ids}` with the ids `--stage mint` prints, record each answer with `manifest.py record ... --stage mint --json '<result>'`, and keep polling at a modest interval (a minute or two between calls) until every asset is `minted` or `failed`. Stop after ten status checks without a state change (or the user's requested limit), preserve the record, and report the remaining ids for later resume. Do not poll failed assets automatically. Report each asset that is not minted and its state. Do not regenerate a `failed` or slow asset without the user's say.

## Hard rules

- One job per call, followed by `get_job` in a later call. Never block Blender's main thread with `wait_job`, sleep or a polling loop. A timeout is not permission to resubmit: check the job and the record first.
- The API has no negative prompt and no crop or mask field. Exclusions are instructions in the prompt; the crop reaches the image node as a linked image named `@crop`. Do not invent parameters for either.
- Never reuse a library asset without the user's say, and never search the library with `crop.png`: its padding and red outline find the neighbours.
- Preserve imported scale by default; flag disagreements for placement review. Explicit user corrections are recorded on the geometry group, not the support hierarchy.
- Every result goes into `assets.json` as it arrives, so an interrupted run resumes from `pending` rather than from memory.
- Add no pricing, credit or spending steps.

## Deliver

Report the Studio project and its id, which assets were reused from the library and which library assets they are, how many assets reached each stage, every asset not minted with its state, the failures and their errors, and where `assets.json` is. Hand over to `marso-blender-place-scene` for import and placement. State what was not checked: reference images you did not open, meshes you did not inspect.
