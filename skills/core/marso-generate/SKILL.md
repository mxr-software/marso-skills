---
name: marso-generate
description: "Use when generating a 3D mesh with Marso from an image or a description (one asset, or several at once), or choosing its mesh model, polygon and texture options."
license: Apache-2.0
---

# Generate an asset with Marso

## Overview

This skill turns an object image or a description into a generated, PBR-textured mesh in the user's Blender session, through the Marso add-on. It delivers the imported asset with its project, source and result IDs and the settings used. It keeps a source or library asset the user chose, and never swaps it for a lookalike. It never generates in place of a request to model editable geometry, articulated parts or precise modular interfaces. A skill supplies instructions, not tool access.

Adjacent work belongs to siblings, each "when installed":

- **An image alone:** `marso-image`. Without it, report that the image was not made; start no mesh for it.
- **An authored reference image for a mesh:** `marso-image` prepares and inspects it; continue with the mesh once the image meets its shape and appearance brief. Without it, make the reference with the add-on's own image command and inspect it against the brief.
- **Reusing a library asset:** `marso-library`. Without it, use the add-on's library search.
- **A new look for an existing mesh:** image authoring and Retexture, through `marso-image` and `marso-blender-texture`. Without them, report that the look was not changed; never generate the mesh again for a colour or print.
- **A whole room or scene image:** `marso-scene-decompose`, then `marso-scene-graph`. Without them, report that the image must be split into objects first.
- **A larger scene workflow:** `marso`. Without it, deliver the asset and say it is one stage of the request.
- **Blender control missing:** `marso-blender-setup`. Without it, report the missing connection.

Through an authorised Blender Python tool, find the enabled Marso module in `bpy.context.preferences.addons` (it may be `bl_ext.<repository>.marso`; do not assume `import marso`). Import its `bridge.commands`, read `all_commands()` and the command's `describe()` schema, then call `execute(name, params)`.

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| One asset from a description or an object image | [Generate one asset](#generate-one-asset) | [generation](references/generation.md) |
| Several assets in one run | [Generate several assets](#generate-several-assets) | [several meshes](references/several-meshes.md) |
| Mesh model, polygon count or texture option | [Choose the options](#choose-the-options) | [preferences and budgets](references/preferences.md) |
| A master that will be repeated many times | Generate it once, at the lowest option that holds its shape | [a repeated mesh](references/generation.md#a-mesh-that-will-be-repeated) |
| A new look for an existing mesh | `marso-blender-texture` when installed | nothing |
| Editable, articulated or modular geometry | Model it; this skill does not apply | nothing |

## Choose the route and the source

1. Respect the requested route. Generate for an explicit generation request, and for an organic or complex form when generation suits it. A request to model editable geometry, build articulated parts or make precise modular interfaces is modelling. Existing geometry that only needs a new look goes to texturing.
2. For an image-only request, hand over to `marso-image` when installed, and start no 3D generation.
3. Use a source or library asset the user already identified, when it is unambiguous. Otherwise check the library when reuse fits the brief. Skip the search when the user asks for a newly generated asset.
4. Establish the source: a description, one object image, or consistent views of that same object. A fabric swatch is a look reference, not the object.

Done when the route, the source and any reuse decision are recorded.

## Choose the options

1. Read the live model catalogue in `generate_state` and the schema of the command that will run. Use catalogue IDs, never a name from an example.
2. Resolve each option in the order [preferences and budgets](references/preferences.md) gives.
3. With no preference known, ask once, early, and continue the set-up while waiting. With nobody to answer, take the advertised default and record that it was chosen for this run.
4. One asset needs no polygon-budget interview. Several assets share one budget, proposed once.
5. If a requested setting is unsupported, name the nearest supported choice or the missing capability and ask; never replace it silently. With nobody to answer, use the nearest supported choice inside any stated ceiling, record it as a temporary override and report it. With no such choice, stop and report.

Done when the model and options are resolved against the live catalogue and recorded with where each came from.

## Resolve the project

Read `save_to_state`. Keep a destination that belongs to the task, select the user's project with `set_save_project`, or create a descriptive one with `create_studio_project` ([generation](references/generation.md#blender-add-on-route)). Preserve existing source, node and job IDs when resuming.

Done when the selected project's ID is read back and recorded.

## Generate one asset

1. Read `generate_state` and the in-flight jobs first.
2. Make the object reference: `upload_image` for an object photo, `generate_image` for a description. Inspect it before reconstruction, and honour the user's review points. With none asked for, this adds no approval pause. When the user asked to review it, show it and wait; with nobody to answer, stop before the mesh and report the reference as awaiting review.
3. Call `create_3d_asset` with the resolved options. It runs the mesh and PBR, then imports the result.
4. Follow the returned `job_id` with `get_job` in later calls. Return from each call at once; a wait or sleep inside Blender blocks the thread the job needs.
5. After an interruption or a timeout, read the existing jobs before creating another asset.
6. A job that stays queued or running is still alive. If nothing changes for half an hour, record the reference and job IDs and report the asset as pending. Model the part instead only when the user asks.

This single command combines mesh and PBR, so it has no checkpoint between them. `create_3d_asset`, `generate_image` and `upload_image` each refuse a second call while one runs (code `busy`).

Done when the job has finished, the asset is imported and its IDs are recorded.

## Generate several assets

Follow [several meshes](references/several-meshes.md) rather than looping the single route, where each mesh waits for the last:

1. Make every object reference side by side, and inspect them together.
2. Send the meshes as one batch, one item for each accepted reference. The batch holds each item after its mesh for a check, then runs PBR.
3. Follow the batch with short status reads, do local work between them, then import every minted asset.

With no review point from the user, inspect and approve each mesh yourself and record it as not user-reviewed. When the user asked to review the meshes, leave each held item awaiting review and show its review image. With nobody to answer, report those images, import nothing for those items and stop.

Done when every mesh is imported with its ID recorded, or reported with its error.

## Inspect and deliver

1. Review each asset: silhouette and unseen sides, thin or merged surfaces, normals, topology, material coverage and scale ([inspect the asset](references/generation.md#inspect-the-asset)).
2. Validate animation, articulation or modular fit separately when the request needs it. Generated PBR is not proof of simulation physics, clean animation topology or modular fit.
3. Deliver the asset with its project, source and result IDs, the effective model and settings, and the remaining quality issues.

Done when the handoff lists each asset, its IDs, its settings and its remaining issues.

## Worked example: three generated masters for a market stall

1. The parts list routes a sunhat, a tote bag and a T-shirt to generation, each to be repeated many times. The request asks for new assets, so the library search is skipped.
2. `generate_state` lists the models. The user's recorded preference names one; its lowest polygon option holds all three shapes, and that choice is recorded.
3. `save_to_state` shows the right project; its ID is recorded.
4. Three `generate_scene_image` calls with `mode: "object"` and their own `request_id` start without waiting. One status read a minute later shows all three finished.
5. The tote reference shows two bags. It is generated again alone while the other two wait for the batch, not for it.
6. One `batch_submit` carries three `scene_asset` items with `start_at: "mesh"`, each with its `generation_node_id`, `image_asset_id`, the mesh options and `review: ["mesh"]`.
7. `batch_status` shows three items awaiting review. The hat's brim is whole and the shirt hangs on its hanger; nobody asked to review, so `batch_review` approves all three and the handoff records them as not user-reviewed.
8. The `pbr` outputs give three `pbr_asset_id` values. `mint_status` reports them `minted` on the second read, and `import_scene_asset` brings each in.
9. The handoff lists the three assets, their IDs, the model and options, and one thin strap to watch on the tote.

## Common mistakes

- Looping `create_3d_asset` for several meshes: make the references side by side and send one batch.
- Generating a mesh again for a new colour or print: that is a texture variant of the same mesh.
- Taking a model ID or option from an example: read `generate_state` and the command's schema.
- Generating in place of a request for editable or modular geometry: model it.
- Following a `batch_id` with `get_job`: read `batch_status`.
- Waiting or sleeping inside Blender for a job: return, and check in a later call.
- Resubmitting after a timeout: read the job or the batch first.
