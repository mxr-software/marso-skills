---
name: marso-blender-texture
description: "Use when texturing a Blender asset with Marso (New or Edit Texture, Restyle, PBR from an existing look), making a flat or tileable PBR material from an image, or baking a colour guide or export."
license: Apache-2.0
---

# Texture assets with Marso

## Overview

This skill gives Blender assets from any source Marso textures and PBR materials: New Texture, Edit Texture, PBR from an existing look, or a 2D material from an image. On request it bakes a colour guide or writes a texture-ready export. It preserves shape, dimensions, hierarchy, pivots, kit connections and the authored UV layout. It works through the working Blender connection and the Marso add-on.

- **Geometry and UVs only for a new model.** Submit a newly modelled asset with no materials. `retexture` and a batch item add a blank `Marso Retexture` material before upload and wire the returned maps into it; the staged route adds the same blank itself. Colours assigned while modelling are not an existing look; do not bake them to run Edit.
- **Use returned materials exactly as applied.** Add no constant colour, metallic or roughness over the maps, no procedural bumps, remapped channels or corrective lights for the acceptance render.
- **Repair the cause, never the paint.** Fix the prompt, reference, submission pose, UVs or geometry, then retexture the original model again. That is a new batch item, a rerun from the same Load 3D node on the staged route, or `retexture` after `reset_look`. Never repaint the returned paint locally and upload it again.
- **Always pass `workflow="multiview"`.** Use `sequential` only when the user asks for it or a documented use requires it, never as an automatic fallback after a weak result.

Model approval belongs to the modelling stage. Before any cloud job on new or substantially remodelled geometry, this skill needs that approval or an explicit waiver ([model approval](#model-approval-before-cloud-jobs)).

Adjacent work belongs to siblings, each "when installed":

- **UVs and the shared atlas:** `marso-blender-uv`. Without it, use the add-on's `prepare_assembly` and its own UV validation, and report that the atlas is automatic.
- **Modelling and form repair:** `marso-blender-asset`. Without it, report form defects rather than asking textures to invent missing structure.
- **Image generation or editing:** `marso-image`. Without it, use verified image tools and the handoff checks in [prompts and image handoff](references/prompts.md).
- **Blender control missing:** `marso-blender-setup`. Without it, report the missing connection.

Through an authorised Blender Python tool, find the enabled Marso module in `bpy.context.preferences.addons` (it may be `bl_ext.<repository>.marso`; do not assume `import marso`). Import its `bridge.commands`, read `all_commands()` and the command's `describe()` schema, then call `execute(name, params)`.

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| An untextured asset or a complete change of look | New Texture: `mode="blank"`, `workflow="multiview"`, then conditioned PBR | [conditioned PBR](references/conditioned-pbr.md) |
| Modify a good existing texture, keeping its design | Edit Texture: `mode="edit"`, `workflow="multiview"`; say what to keep and what changes | [prompts](references/prompts.md) |
| Keep the existing base colour; derive PBR | `pbr_generate`, preserving the existing appearance | [commands](references/commands.md) |
| A flat image or swatch to turn into a 2D PBR material | `image_material` with its tiling and displacement options | [flat images](references/commands.md#flat-images-and-2d-materials) |
| Baked guide or texture-ready export; no cloud | [Prepare the submission](#prepare-the-submission) and stop before jobs | [preparation helper](references/preparation-helper.md) |
| Same-shaped objects with distinct labels or finishes | One master per shape, independent looks, then instances | [appearance families](references/appearance-families.md) |
| Alternative styles from an existing asset | Branch from the preserved original or prepared baseline | [variants and naming](references/variants.md) |
| Deliberate clean, worn and burnt states | Sibling or explicitly cumulative edits, PBR for every state | [appearance states](references/appearance-states.md) |
| Reusable modular components | Preserve surfaces exposed across intended arrangements | [kit texturing](references/kits.md) |
| Several targets in one run (kit parts, set piece masters and variants, props) | Stage by stage: each stage for every target together | [many objects](references/many-objects.md), then [conditioned PBR](references/conditioned-pbr.md) for the calls |
| Several approved Edit Texture targets | Native batches when exposed | [batches](references/batches.md) |
| Preparation, upload, pose, transparency or placement detail | The matching section | [preparation](references/preparation.md) |
| Repeated parts, mirrored geometry or wrong normal directions | Diagnose before reuse | [normals and repeats](references/normals-and-repeats.md) |
| Qualifying an export route or investigating a defect | Conditional round-trip check | [validated handoff](references/validated-handoff.md) |

Scripts:

- `scripts/prepare_asset.py` (inside Blender): single-mesh working copy, atlas validation, colour-guide bake and GLB export.
- `scripts/verify_export.py` (inside Blender): compares an exported GLB with its source when qualifying a route or chasing a defect.
- `scripts/contact_sheet.py` (command line, `--help` for arguments, needs Pillow): builds and splits an appearance-family contact sheet.

## Choose the target

1. Before cloud operations, read [commands and jobs](references/commands.md), discover the installed schemas, and select or create the user's Studio project. Do not substitute a generic Blender project when a specific destination is required.
2. Verify target, root and parts with `assembly_state`; a tagged child can resolve to a previous assembly. Include only the intended geometry group, not supported assets under its entity Empty. A fixed multipart asset is one target; a kit collection is several.
3. Read the root's `marso_poly_path` when present. The add-on uploads the evaluated mesh. For low-poly, submit the base mesh without detail modifiers and rely on the returned normal and texture maps for fine relief.
4. For medium-poly, keep the bevels. For high-poly, set the subdivision level that shows the modelled detail. Record the uploaded triangle count; report a rejected upload rather than silently decimating.

Done when the project, the target with its parts, and the upload level for the path are recorded.

## Prepare the submission

1. **Preserve and scope.** Inspect exact sources, shared data, anchor and material roles. Work on independent copies; isolate shared data only where the change should be independent. Keep rebuild materials and images distinct. Resolve known form, attachment and shading defects before final preparation.
2. **Keep the UV layout.** With `marso-blender-uv`, the parts arrive with a passing `MarsoUV` atlas and its review images; keep it unchanged. Otherwise keep satisfactory existing UVs, or use `prepare_assembly` (below). Preserve corner normals through any conversion.
3. **Check uniqueness per image.** Within each shared material and image, every textured face needs unique space across all included parts and instances. Separate materials with independent images may each use the full tile. Keep existing material assignments; a newly modelled asset has none.
4. **Choose the submission route.** The assembly route (`prepare_assembly`, which Retexture also runs on an unprepared multi-part root) lays a fresh Smart UV `MarsoAtlas` over every part. Submit an authored multi-part atlas as a single-mesh working copy from `scripts/prepare_asset.py` instead.
5. **Submit the working copy.** Build it with the [preparation helper](references/preparation-helper.md) and validate it with `validate_atlas`. Then submit `target.name` as `object_name` with `auto_uv: false` on the route chosen in [Describe and submit](#describe-and-submit). The returned material lands on the working copy: assign it to every source part, whose shared `MarsoUV` its UV Map node reads. Inspect the parts under changed lighting and report that this transfer is not live-tested. Submit a single mesh directly with `auto_uv: false`.
6. **Use the automatic route deliberately.** Without an authored atlas, `prepare_assembly` with `object_name`, `size` (2048 or 4096) and `bake_colours` prepares the assembly: `false` for New Texture, `true` only to keep an existing look for Edit. Follow its job with `get_job`. It collapses buried faces and replaces all slots with one shared material.
7. **Bind the image for the mode.** For New on bare geometry, leave the parts without materials and say in the prompt which material each surface takes, such as "the rim is brushed steel, the outer wall satin enamel". Do not create materials, paint or bake region colours. For Edit, preserve the existing bound texture, or bake its visible appearance if export requires it.
8. **Local-only work stops here.** A guide is a lighting-free UV image bound to the mesh, not a camera render. Use the native submission, or export a GLB when requested.

- **Thin two-sided assets or overhanging fittings:** present both broad faces to opposing views, or texture the groups separately ([submission pose](references/preparation.md#submission-pose-and-occlusion)).
- **Parts stay assembled:** Retexture frames the whole submitted object, so parts spread apart leave every surface fewer pixels. Move only a fitting that covers a named surface, within the [spread limit](references/preparation.md#keep-the-spread-small).
- **Checks:** let a helper or native operation supply the checks it already performs; do not repeat a validator for another report. A successful helper or an existing PBR material is not proof of correct input.
- **Failures:** resume only the affected stage ([recovery](references/preparation.md#prepare-once-resume-the-affected-stage)). UV changes invalidate the guide; a preview failure does not. Leave unrelated accepted parts alone.
- **Transparency:** Marso generates none; exclude and restore clear parts, or apply local transparency after maps ([transparent parts](references/preparation.md#transparent-parts)).
- **Normals:** never flatten normal vectors or disable the map as a claimed repair.

Done when the submitted target passes the add-on's validation, its image binding matches the mode and the submission pose is chosen.

## Model approval before cloud jobs

New or substantially remodelled geometry needs useful neutral-clay evidence and user approval before Retexture or PBR. If the task states approval or a waiver, proceed. Respect explicit waivers and approval of unchanged parts.

- With nobody to answer, finish local reversible preparation, stop before any cloud job, and report the previews and the pending approval.
- Routine UV work that preserves appearance does not renew approval. Direct retexture of an existing unchanged asset needs no extra model-approval question.
- Major unresolved form defects return to modelling; report them rather than asking textures to invent structure.
- A model built with `marso-blender-asset` carries its finish check on the root, as the JSON property `marso_finish`. Read its `status` before any cloud job. A waiver covers the wait for a person, never this check. If the property is missing or its `status` is `repair`, return the asset to `marso-blender-asset` to run its finish check, and start no Retexture. Without that skill installed, report that the model's quality checks were not run.

Done when the approval, the waiver or the pending state, and for a modelled asset a finish status of `pass` or `partial`, are recorded before the first cloud job.

## Describe and submit

Read [prompts and image handoff](references/prompts.md) when authoring a new look. The text prompt is the main control. Write two or three short, plain sentences: what the object is and its main materials, its condition at the strength the brief asks, then "Lots of detail, photorealistic." Nothing real is perfectly clean: every prompt names some wear, dust or marks. Leave out shape, part lists and hedging words. For a kit, [lock one look first](references/kits.md#lock-the-look-before-the-parts). Prompts are not an exact mask.

- **Precise artwork:** record fixed landmarks such as stripe ends and label panels, and stage Retexture so they are checked on the unlit paint.
- **Every `retexture` call:** pass `enhance: ""` unless the user wants the panel's enhancement, which is otherwise appended to the prompt.
- **Every `retexture` and `run_3d_retexture` call:** state `mode`. Left out, it means Edit Texture: the panel's setting, which starts on Edit, or the function's default.
- **No reference image:** Retexture runs with no reference image at all. On `retexture`, pass `reference_path: ""`, which means "none" and sends no image; leaving it out would reuse the panel's earlier pick. Turn any photograph, of the object or of its material, into words in the prompt ([no reference image](references/prompts.md#no-reference-image)). A render, drawing or clay view guides shape only.
- **Reusable or coordinated looks:** keep a compact [appearance brief](references/appearance.md).

Submit eligible jobs once and retain job and result identity and the project. Reconcile a timeout rather than resubmit.

- **Several targets:** work stage by stage, not object by object ([many objects](references/many-objects.md)). Send every target in one batch, read them all in one status read, and move each finished target on one stage at a time.
- **A pilot** comes first only for an unproven method: one part's paint for a kit, the kit skill's pilot for a reference-image kit, and the pilot in [appearance families](references/appearance-families.md) for edited-image looks. Targets textured from a text look need none.
- **Batches** take Edit Texture targets with `review: []`. From Marso 1.22.0 they take New Texture targets too, with `review: ["edit"]`: the paint's approval carries the condition image ([conditioned PBR](references/conditioned-pbr.md#batch-route-marso-1220-and-later)). PBR-only targets use `pbr_generate`, because batches have no PBR-only pipeline. Let the add-on monitor and advance a batch's stages.

Choose the PBR route before submitting Retexture:

- **New Texture (default):** Retexture alone, inspect the unlit paint, make a condition image from that paint, then PBR with the condition. New paint carries no lighting cues, so this is the default without being asked.
- **The user supplied a real photograph of the same object and finish** (cleaned if needed; not a render or drawing, and not an image you rendered or generated): pass the file as `condition_image_path` on the combined Retexture and PBR run, or `condition_image_asset_id` when it is already in the account. To get an ID for a file, call `upload_image` with `add_node: false` (1.21.1 and later). Without it, that command adds a Load Image node for mesh generation, which is then left unconnected in the project.
- **Edit Texture or PBR-only on an existing look with clear finish cues** (a texture the user supplied or an accepted Marso result, not a colour atlas baked from stand-in materials): the combined run may continue directly into PBR. Pass `condition_image_path: ""` on `retexture` or `pbr_generate` when no condition image is intended; an omitted one uses the panel's earlier pick.

A New Texture run never ends at the paint. If the paint cannot be brought into Blender or the condition image cannot be made, run PBR with no condition image, apply it and report the paint as not reviewed ([sequence](references/conditioned-pbr.md#sequence)).

Follow a running add-on chain to avoid duplicate PBR.

A run that stays queued or running is still alive, however slow Marso is. Keep following that same run and do local work meanwhile. If nothing changes for half an hour, save the file, record the IDs and report those targets as pending, so the run can be resumed. Deliver a Marso result or a pending report, never a hand-made material in its place. When reads keep timing out, read again later; never replace or patch an add-on function, even for a moment, to feed a batch results it could not fetch.

Done when each job is submitted once, with its route, project and job identity recorded.

## Review the result

1. Import the painted mesh as a temporary object ([bring the paint into Blender](references/conditioned-pbr.md#bring-the-paint-into-blender)): a batch item's `review_file`, or the fetched file on the staged route. The library import commands take only a PBR result. Inspect the unlit paint region by region against the brief before any condition image ([accept the paint](references/conditioned-pbr.md#accept-the-paint-before-conditioning)).
2. If a region or finish is wrong, find its cause. On the batch route, reject the item and send the target again. On the staged route, rerun `run_3d_retexture` from the same Load 3D node, first binding a corrected bare mesh there after a geometry or UV fix. On the combined command, run `reset_look` on the target, fix the cause and run `retexture` again; record both node sets. If one repair attempt reproduces the same unexplained failure, report the job evidence and stop resubmitting.
3. Inspect returned maps per material under changed lighting, including seams and visible backs or interiors. Use the returned Marso materials exactly as the add-on applies them.
4. Reuse accepted geometry previews. Start with one useful material preview and inspect other relevant angles interactively; add a small targeted diagnostic only for a specific uncertainty. Requested beauty stills and films follow acceptance.
5. Preserve packed images or valid dependencies on save. Keep names stable while jobs are pending; after success follow [identity-safe naming](references/variants.md#name-materials-after-successful-application).

Done when every requested region passes on the unlit paint, or the paint is reported as not reviewed, and the applied materials have been inspected under changed lighting.

## Hand off

Finish with one short handoff: operation, affected asset, project and result IDs where available, output, acceptance and remaining defects. Name the UV route (authored `MarsoUV` working copy or the automatic `MarsoAtlas`). No per-stage essays, routine normal-on/off galleries, or simulation-ready claim from texturing alone.

Done when the handoff lists the operation, IDs, output and remaining defects.

## Worked example: New Texture on a modelled dining chair

1. The task approves the model. `marso-blender-uv` hands over `Chair` with a passing `MarsoUV` atlas. `assembly_state` on `Chair` reports an assembly of 14 parts with no materials.
2. `save_to_state` shows an unrelated project; the task names "Dining set". `list_studio_projects`, then `set_save_project` with its `project_id`.
3. The atlas is authored, so `prepare_asset.working_copy(parts, name="Chair_Texture_v1", frame=root.matrix_world, addon_module=addon)` joins a working copy. `validate_atlas` passes. Retexture on `Chair` itself would have replaced the atlas with `MarsoAtlas`.
4. The .blend is saved to the path it will keep. One `batch_submit` item on `Chair_Texture_v1` runs Retexture alone: `mode: "blank"`, `workflow: "multiview"` and `review: ["edit"]`. The prompt describes oiled oak with straight grain on the frame and a charcoal wool seat pad.
5. `batch_status` shows the item in `needs_review`, and its `review_file` is imported as a temporary object. Its unlit paint shows the wool colour bleeding onto the front rail. The item is rejected, the prompt is changed to name the rail as oak, and the target is sent again; the paint is not touched up locally.
6. An unlit capture of the second paint goes through `edit_scene_image` with a two-sentence prompt asking for photorealistic lighting and naming how the oak and wool catch the light. `batch_review` approves the paint with that image as `condition_image_asset_id`. The add-on runs PBR and applies the result, which is inspected unchanged under new lighting.
7. The handoff lists the batch and its item, the Retexture, Image Edit and PBR IDs, the project, the authored `MarsoUV` route and one remaining defect.

## Common mistakes

- Retexturing the root after authoring an atlas: submit the single-mesh working copy, because the assembly route replaces the atlas.
- Adding materials or baking stand-in colours before New Texture: submit geometry and UVs only.
- Repainting returned paint and uploading it: fix the cause and retexture the original model again.
- Running the combined chain after New Texture: hold the paint for review in a batch and condition PBR on a lit image of it.
- Texturing several objects one at a time: send each stage for every target together and check them in one status check.
- Switching to `sequential` after a weak multiview result: keep `workflow="multiview"` and fix the cause.
- Spreading an asset's parts apart after a weak result: keep it assembled and move only a fitting that covers a named surface, within the spread limit.
- Adjusting returned maps or adding lights for the acceptance render: apply them unchanged and correct the stage at fault.
- Starting a cloud job on an unapproved new model: finish local preparation and report the pending approval.
