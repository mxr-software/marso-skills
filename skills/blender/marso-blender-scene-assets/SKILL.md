---
name: marso-blender-scene-assets
description: "Generate planned scene assets with the Marso Blender add-on: check library reuse, create references and meshes, then PBR and mint. Use a scene asset plan; requires supporting scene commands."
license: Proprietary. See LICENSE.txt in this skill folder.
---

# Generate a scene's assets with Marso

Turn a reviewed asset plan into minted Marso assets, one per unique asset, through the Marso Blender add-on. Check library candidates where reuse is requested or appropriate; preserve explicit new-generation choices and identified local sources. An asset chosen for direct library reuse skips generation and proceeds to mint-state checking. For each asset still to make, the chain is: upload the crop and make an object-mode reference image from it, then a 3D mesh and PBR from that image, then wait for the asset to be minted (service mint/scale state; validate physics separately before claiming simulation readiness). Nothing is placed in the scene here.

Inputs, from the `marso-scene-graph` skill's run folder: `asset_plan.json`, and `references/index.json` with each asset's `crop.png`, `search.png` and `brief.json`. If they do not exist, run that skill first. `<skill>` in the commands below stands for this skill folder's path; its script needs Python 3.10+ and nothing else. If the Blender connection or the Marso add-on is missing or not configured, use `marso-blender-setup` when installed; do not work around it.

In shell examples, `python` means an installed Python 3.10+ interpreter. Check its version first; on Windows, use `py -3.13` or another installed compatible version if the default `python` is older. Blender-only scripts run in Blender instead.

## Before the first job

1. **Resolve the relevant Studio project.** Reuse the user-designated project by id when it exists. If none is identified, discover relevant existing projects and create a descriptively named task project when appropriate to the authorized creation request. Ask only when destination ambiguity materially matters; honour any earlier project instruction. Use `create_studio_project {name}` only for a new project; follow the job and read `save_to_state`. Select the intended id with `set_save_project {project_id}` and verify it. Never silently accept a generic Blender destination. Read [studio chain](references/studio-chain.md) for every command used.
2. **Settings.** Read [settings and scene budgets](references/settings.md). Establish/reuse the user's preferred mesh options, validate live capabilities and resolve the scene budget. No fixed generator, texture or polygon count is prescribed. Never silently raise a strict limit to a model's minimum.
3. **Start the record.** `python "<skill>/scripts/manifest.py" init "<run>/asset_plan.json" --references "<run>/references/index.json" --out "runs/<job>/assets.json" --project "<name>" --project-id "<verified-id>" --model "<selected-live-model>"`. Pass `--polycount` and `--texture` only for resolved supported options; the helper injects neither. Per-asset `model`, `polygon_count` and `texture` in the plan override these run settings (explicit null omits an optional field). It stores the stable project/run ids and canvas rows, lists every asset with a crop, its prompt and settings, and prints what it left out and why.
4. **Check the library.** For each asset `manifest.py pending runs/<job>/assets.json --stage library` lists, call `find_in_library` with its label and `search.png` and record the answer with `manifest.py record ... --stage library`. Read [library check](references/library-check.md).
5. **Checkpoint 1, the plan.** Consolidate with the planning skill's review; retain approval of unchanged decisions and review new library candidates/settings before generation, the library candidates included, with their thumbnails. Record the user's reuse-or-make decisions with `manifest.py choose`. Read [checkpoints](references/checkpoints.md).

Before batch submission or an individual reference/mesh submission, read `save_to_state`, save its response locally and run `manifest.py check-project runs/<job>/assets.json --state "<state.json>"`. On mismatch, reselect the recorded id and verify again. A native batch captures its explicit project; later panel changes do not redirect its stages. On resume, reconcile the existing batch's captured destination rather than creating a replacement. For a legacy record without an id, first verify its original project and use `manifest.py bind-project ... --project-id "<id>"`; never reinitialise a running record to resume it.

## Choose the execution route

When the installed add-on exposes the batch commands, use [add-on-managed batches](references/batches.md) after checkpoint 1. Submit all approved independent items; the add-on monitors and advances each chain, pausing for image and mesh review. Keep batch records mapped to `assets.json` for minting and placement. Do not also run the individual reference/mesh loops below for batch-owned items.

If batch commands are absent, disclose that limitation and use the following individual-command fallback. A repository update is not an installed capability. Retain the user's existing connection and approval requirements.

## Reference images

For plans created with viewer choices, use references cropped with `--all-routes`. The manifest retains `creation_choice` and checks the library only where requested. **Model**, **instance** and **kit** routes never enter reference/mesh generation: after the library decision, read `manifest.py pending <assets.json> --stage handoff` and continue through the corresponding application skill. An existing-scene source needs no library lookup when the user disabled it. Instancing a library candidate for Retexture is not finished by importing its current appearance. Preserve its source and isolate material bindings before texturing. Room-shell anchor choices stay in the plan for a separate handoff.

To let users compare search results in the detection artifact, rebuild that viewer with `--asset-record <assets.json>` and its saved `--choices` file. It displays the recorded candidates and allows selection for instancing plus Retexture. Its export is a revised planning input; reconcile it into a new plan before any jobs. Do not reinitialise an active manifest or silently replace an explicit route. Choosing a route does not approve newly modelled geometry.

For each unowned asset that `manifest.py pending runs/<job>/assets.json --stage reference` lists, call `scene_reference {label, crop_path, prompt, row}` with the brief's prompt unchanged, and record the job id with `manifest.py record ... --stage reference <asset_id> --job <id>`. Respect the installed add-on's scheduling; older inspected builds hold four whole-job slots, whereas newer builds release networking slots during cloud waits. Prefer the native batch path for large sets rather than launching hundreds of individual worker jobs. Follow each with `get_job` in a later tool call and record its result (`--result` or `--json`) or its failure (`--error`).

**Checkpoint 2, the reference images.** Open the actual generated images before showing them beside their source crops. Check a complete isolated subject, useful framing, retained thin tips/handles, plausible unseen structure and absence of neighbouring objects. A square source crop does not guarantee a well-framed generated result. Excess empty space can cause the mesh service to reject the image; no universal area/50% threshold is verified. Repair unsuitable framing through a supported image workflow and review the replacement before submission. Newer builds expose `framing: "square"` and `margin` for input preparation; older builds do not. Check the live schema, avoid repadding an already prepared crop, and do not mistake input framing for guaranteed output composition. Stop for the user's review and record their decision with `manifest.py review`; never send a mesh job from an unapproved image.

## Meshes, PBR and minting

Follow the [job scheduling guidance](references/studio-chain.md#jobs) to refill available slots promptly, keep polling responsive during local work and distinguish observed completion time from actual job duration.

For each unowned asset `--stage mesh` lists, call `scene_mesh {generation_node_id, image_asset_id, model, polygon_count, texture, label, row}` with the asset's recorded node ids, stable `row` and settings, following the installed scheduling capability, and record each job and result. The result carries the `pbr_asset_id`. This standalone command already includes PBR; do not add a duplicate PBR stage.

Then poll `mint_status {asset_ids}` with the ids `--stage mint` prints, record each answer with `manifest.py record ... --stage mint --json '<result>'`, and keep polling at a modest interval (a minute or two between calls) until every asset is `minted` or `failed`. Stop after ten status checks without a state change (or the user's requested limit), preserve the record, and report the remaining ids for later resume. Do not poll failed assets automatically. Report each asset that is not minted and its state. Do not regenerate a `failed` or slow asset without the user's say.

## Hard rules

- For individual-command fallback only, one job per call followed by `get_job` in a later call. Native batches use their own batch status/review tools and own their scheduling; never follow a batch id with `get_job`. Never block Blender's main thread with `wait_job`, sleep or a polling loop. A timeout is not permission to resubmit: check the job and the record first.
- The API has no negative prompt and no crop or mask field. Exclusions are instructions in the prompt; the crop reaches the image node as a linked image named `@crop`. Do not invent parameters for either.
- Reuse only a user-selected asset or a choice within explicitly delegated reuse authority; do not ask for unchanged choices again, and never search the library with `crop.png`: its padding and red outline find the neighbours.
- Preserve imported scale by default; flag disagreements for placement review. Explicit user corrections are recorded on the geometry group, not the support hierarchy.
- Every result goes into `assets.json` as it arrives, so an interrupted run resumes from `pending` rather than from memory.
- Preserve exact failure messages and any returned execution id, node id and error code in the local run record. The helper retains completed/failed stage snapshots when a new job is recorded and refuses to replace an unresolved submitted job. If the add-on omits diagnostic identifiers on failure, record that limitation; do not reconstruct them as if they were observed. Save setup/check results to a file too.
- Add no pricing, credit or spending steps.

## Deliver

Report the Studio project and its id, which assets were reused from the library and which library assets they are, how many assets reached each stage, every asset not minted with its state, the failures and their errors, and where `assets.json` is. Hand over to `marso-blender-place-scene` for import and placement. State what was not checked: reference images you did not open, meshes you did not inspect.
