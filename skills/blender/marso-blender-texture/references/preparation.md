# UVs, materials and assembly preparation

Contents:

- Agent-authored layouts (prepare once, choose surfaces)
- Submission pose and occlusion
- Single mesh
- Verify the actual upload
- Asset frame and round-trip placement
- Transparent parts
- Fixed multipart asset

## Agent-authored layouts

Preserve satisfactory existing UVs. New seams, unwraps and packing belong to the UV stage (`marso-blender-uv` when installed), which hands over a checked `MarsoUV` atlas. Use the add-on's automatic preparation only as a fallback when that route is unavailable or the user requests quick automatic preparation; inspect its result to the same acceptance standard. A fallback does not waive UV quality requirements.

### Prepare once; resume the affected stage

For New Texture on bare geometry, submit the parts without materials; `retexture` adds a blank `Marso Retexture` material before upload and wires the result into it, and the staged route adds the same blank itself. Describe the intended regions in the prompt. The preparation helper's working copy and atlas validation suit any agent-authored layout; use its guide bake only when a colour guide is requested. The bake-specific recovery instructions below apply to that route.

Reuse the UV stage's accepted layout instead of writing a new preparation pipeline for every asset. Before an expensive bake, resolve known geometry defects, empty material slots, sweep caps and material-role assignments. Test a representative difficult component before multiplying it. Do not lower the approved geometry or UV standard to meet a time target.

UV editing must preserve the accepted surface shading. Avoid a mesh/BMesh topology round-trip merely to edit UV coordinates; write corner UVs directly where possible. When conversion or joining is necessary, preserve evaluated corner normals and their correspondence, not only face normals or smooth flags. UV-only edits must not replace custom normals with recalculated ones. A topology change needs a verified correspondence or deliberately rebuilt and inspected shading; copying an old loop-index list is not valid after loops change. This belongs in the preparation helper, not a late repair after baking.

Keep a recoverable checkpoint after accepted geometry and after valid packed UVs, using the existing local run record. Resume only invalidated work:

| Change or failure | Resume from |
| --- | --- |
| Geometry, included faces or chart layout changed | Return the affected parts to the UV stage, then make a new working copy, validate and rebake; retain unrelated accepted assets |
| Colour guide/material roles changed; geometry and UVs unchanged | Colour bake and material/export checks |
| Saved image missing or not loaded | Repair image loading/binding and inspect the guide; do not unwrap or rebake an intact saved image |
| Camera, lighting or preview failed | Preview only; retain validated preparation |

Save the baked guide to a durable path and confirm it loads and is bound to the current target before submission. A fresh Blender process can load packed image pixels lazily; a transient `has_data` value alone does not prove the bake failed. Do not repeat pack/bake to fix a preview loader. Keep revision identity with checkpoints; never reuse a bake after its UVs change or overwrite a pending batch's pinned working file with a review snapshot.

### Choose surfaces before packing

Decide which surfaces need generated texture before allocating atlas space, including when the agent builds its own joined target. A valid, tightly packed atlas can still waste most of its detail on buried geometry. Classify surfaces against the intended asset use:

- **Visible or potentially exposed:** retain unique coverage for backs, undersides, openings, moving interfaces and reusable parts across intended poses and arrangements. Being outside the current camera is not an exclusion.
- **Permanently covered in a fixed assembly:** omit those faces from the texture/upload working copy and record the source-face correspondence. Preserve the editable source and any closed geometry needed for collision or other uses. Do not spend full-size islands on the two sides of a bonded contact merely because both source parts are closed solids. Keep exposed borders and partially visible faces; separate a covered region only when its boundary can be established reliably.
- **Uncertain:** retain the surface, record the uncertainty and resolve it only if the likely waste warrants further inspection. A poor or blank prediction is not evidence that a face is permanently hidden.

Use construction knowledge and a cheap section/visibility inspection first. For example, a bonded cover needs its outer face and exposed edges, not a second full-size island for its covered underside; the substrate may still have a visible rim. A removable cover or articulated joint needs a different decision. Avoid a whole-asset ray-analysis campaign when the contact is already explicit in the construction.

The add-on's automatic assembly preparation has hidden-face handling, but an agent-authored single-mesh target does not automatically receive it. The authored route owns this decision. Do not rerun automatic unwrap over a curated atlas just to obtain face exclusion, manually collapse arbitrary faces and assume native validation accepts them, or suppress validator failures. Use a supported handoff, or omit justified faces on the independent working copy and verify transfer to the retained source faces. Packing/baking follows surface selection; changing that selection invalidates the old atlas and bake.

For a mesh, validate the UV layer sampled by each material and bind its base-colour image. Set `auto_uv: false` when supported to retain authored charts. Preserve separate material/image pairs where useful. For multipart sources, inspect `assembly_state` before submission. If automatic assembly preparation would replace required layouts, isolate an independent working mesh retaining the original slots, UVs and part correspondence; verify returned maps against each original role. Use a single shared atlas only when that is the chosen handoff.

The inspected assembly path creates a fresh Smart UV layout; retaining older UV layers does not mean Retexture uses them. `auto_uv: false` controls missing UVs on a single mesh and does not disable automatic assembly preparation. Do not send a curated multipart layout through that path expecting preservation, or invent a preserve-UV parameter. Establish a verified working-copy handoff or report the capability gap if the installed route cannot preserve the required layout.

## Submission pose and occlusion

For a thin object with two different broad faces, look along the opposing view directions of the **export copy**. If both show mostly its edge, turn the copy so one direction sees the decorated face and the opposite direction sees the reverse. Identify the sides by visible features in the prompt, such as the panel with mounting holes. Preserve the delivery pose, transforms and UVs for reassembly.

Look through overhanging parts toward the main surface. A wheel, grille or handle can project its finish onto the panel behind it even with unique UVs. If that panel matters, texture it with the removable fittings clear of the artwork, within the limit below. A joined mesh or extra material slots alone will still present the same obstruction.

### Keep the spread small

Retexture frames the whole submitted object in each view. Every part moved outward widens that frame, so every surface gets fewer pixels and the paint loses detail. An asset with all its parts spread apart textures worse than the same asset left assembled.

Change the pose only for a fault the views explain: paint missing from a covered surface, or a fitting's finish printed on the surface behind it. A result that is weak all over has another cause; check the prompt, UVs and geometry.

1. Move only a fitting that covers a surface the brief names. Leave every other part assembled.
2. Work on a temporary copy. Translate the fitting the shortest distance that shows the covered surface in the relevant views.
3. Measure the diagonal of the bounding box around all submitted parts, assembled and then spread. Keep the spread diagonal within 1.25 times the assembled one.
4. If the surface is still covered at that limit, put the fittings back. Texture the panel and its fittings as separate targets, each kept compact.

Preserve each target’s UV/material binding and restore the assembly for delivery.

When the view check reveals substantial obstruction or an unproven two-sided treatment, choose the staged conditioned-PBR route before starting the automatic chain. Inspect the returned **unlit paint**, including the reverse and the surface beneath a temporarily hidden fitting. Stop on missing artwork, duplicated silhouettes or a material bleeding onto its neighbour. Inspect any partial-map warning even if a mesh was returned. Correct the cause before generating the lighting condition. Keep the groups clear through mesh PBR where occlusion matters, and use a guide showing the matching painted target. After reassembly, check the opaque panel for hardware-shaped marks in metallic and normal under a fresh light. Local paint cleanup alone cannot establish that the next prediction will keep those regions clean.

## Single mesh

Inspect faces, active/render UV layers, material slots, source images and evaluated modifiers. A UV layer's existence does not prove a usable unwrap. Retexture and PBR-only generation need unique, non-overlapping UV coverage for every surface being textured in the submitted target; mirrored chart orientation is accepted. Return mirrored or repeated islands that share UV space to the UV stage to unstack them on the source parts, even when their final appearance should repeat; alternatively generate a reusable master separately. Check degenerate islands, coverage, padding, scale and direction with a checker where useful. Read the normals and repeated geometry reference before choosing how finished maps can be reused.

Use the helper/native full-domain check and inspect the layout and useful sampling; packing coverage alone is not a quality score. When a check fails, sampling is unclear, or the route needs independent qualification, return the part to the UV stage, which owns the detailed acceptance checks. Do not add a diagnostic audit to a qualified routine path solely to produce another report.

Keep final model form/construction acceptance separate from UV readiness. For newly modelled geometry with known major shape defects, return to modelling before final atlas/bake work unless the user specifically requested a UV diagnostic. For a ready target, validate useful narrow-chart sampling and spacing at the intended lower texture resolution, not only at the generation resolution. Re-bake and re-export after any atlas revision.

In the inspected implementation, missing UVs can be Smart UV projected, and missing base-colour textures get a blank 4096-pixel image filled from material colours. Every image texture node is checked for images over 4096 pixels; even an unused oversized image can block the single-mesh preflight. Preserve the source and resize a working copy when needed. Do not downsample shared source images globally.

Prefer a verified 0-1 UV layout for this workflow. Export's UV offset adjustment is not a complete UDIM conversion. Bake multiple tiles or complex procedural appearances to a supported working texture layout when necessary, preserving the editable source. Multiple material slots or unusual shader graphs require inspecting the returned slot mapping; do not assume every graph survives PBR application unchanged.

## Verify the actual upload

Every submitted material used by a visible part needs a bound base-colour texture. For New on bare geometry a blank is sufficient. For Edit verify the actual exported material still samples the accepted texture. A populated slot or an unused image node alone does not establish the binding.

Check the export's actual object and material inventory, especially with multiple scenes or an unfamiliar add-on build. Selection in the current view layer alone may not establish the exporter scope. Unintended objects can introduce untextured materials even when the intended target is valid. Use a recoverable, isolated working export when necessary, restoring temporary selection/visibility changes afterwards. Do not delete unrelated objects to make validation pass.

For an unverified, changed or suspect export route, reopen the actual upload in an isolated Blender process and audit its material-bound UV layout across all included parts. On a verified corrected route, use the native validation and established export-preservation evidence under the ordinary preparation policy in the validated handoff reference. A single joined object, independent mesh datablocks, correct face orientation or a successful colour bake does not establish unique UV coverage. Retain the overlap result and any justified hidden-face exclusions before submission; do not infer success from a prepared flag. If neither native coverage nor independent inspection establishes the upload checks, report the gap rather than claiming it passed. A PBR-only request does not bypass this check.

If the service returns `ASSET_EDIT_INVALID_INPUT`, retain the original response and inspect the uploaded file and named material. Correct the export or colour-texture preparation before another submission; retrying the same invalid input cannot fix it. The service's suggestion to run PBR is an alternative operation, not evidence that the requested Retexture succeeded. Report add-on preflight gaps separately rather than describing a skill workaround as an add-on fix.

## Asset frame and round-trip placement

An asset's authored anchor/pivot is distinct from its placement in the current scene. A portable library asset should preserve geometry relative to that anchor, not inherit an arbitrary scene offset. Check the actual upload's vertex bounds as well as its object transform: an object at `(0, 0, 0)` may have offset coordinates baked into its vertices. Do not require the user to build every source asset at world origin.

Before publishing/reusing an assembly through the library, record its intended anchor, real dimensions and relative part transforms. Verify those properties through the established export route. For an unverified or changed route, reopen the export in an isolated scene and test that moving the whole source assembly elsewhere does not change the asset-relative result. Keep the original scene placement recoverable; temporary export copies must not relocate source geometry or change pending targets.

Versions before 1.12.0 could bake world-space placement into an identity-transform upload proxy. Versions 1.12.0 and 1.12.1 include asset-relative export handling; verify the installed route and actual output rather than assuming older library assets were corrected. For an affected build, use a verified isolated working-copy route with a recorded asset-to-scene transform and map correspondence, or report the limitation. Changing upload orientation also changes the coordinate frame of world/object-space diagnostic normals; account for that rather than blindly copying vector maps.

Check a returned multipart import before placing or instancing it: part separation, rotations, dimensions and pivots must survive. Correct a verified placement-only offset by transforming the complete asset through one shared Empty/anchor. Do not zero every part's location, discard rotations or force uniform scale to make the asset appear centred. If the importer already changed internal geometry/relative transforms, return to the source file or a verified import route; moving the group cannot reconstruct lost relationships. Keep visual bounds, authored pivots and articulation requirements distinct.

## Transparent parts

Marso does not currently generate transparency. Choose the appropriate handoff for each clear surface before preparation:

- **Exclude and restore:** omit a transparent object or its faces from the texture/upload working copy, then restore its original geometry and locally authored glass/transparent material after maps are applied. Preserve transforms, source-to-working correspondence and opaque attachments such as frames or labels. Omission from the upload is a deliberate material choice, not a declaration that the surface is permanently invisible.
- **Use maps with local transparency:** include a surface to obtain useful finish/roughness maps, then apply transparency through its known material slot or a verified local mask. Protect opaque label regions. Do not assume an automatically flattened atlas will retain the original slot separation; preserve roles before preparation and verify transfer back.

Keep source geometry and shaders recoverable. Do not delete glass from the editable asset or change a pending target mid-job. Inspect restored clear parts, labels and visible contents in material/rendered views. Credit Marso for its returned maps and the application for local transparency; do not claim Marso generated a transmissive material.

## Fixed multipart asset

Texture an isolated master before creating its placed instances when practical. Prepared-state checks can reject an assembly material used outside the target, including linked scene copies. Newer builds expose target/family scope and isolate data accordingly; inspect the schema, resolved parts and outside users before relying on that capability. On older builds, use an independent working target with isolated mesh/material data and deliberately transfer the chosen appearance to intended instances. Never delete the user's instances to bypass preparation. Preserve their placement and independent styles.

Curves, text and other procedural parts need an evaluated mesh working copy when the export/preparation route only accepts meshes. Preserve the editable source, transforms, material roles and source-to-copy mapping; inspect the evaluated silhouette before UV work. Hidden master collections can cause parts to be omitted. Check the actual included parts and restore any temporary visibility changes after preparation.

Use an explicit `object_name` for `assembly_state`, preparation and Retexture. Omitted names can include selected objects. Inspect actual parts: visible mesh descendants are included; hidden parts can be excluded. A previously tagged child can resolve to its entire assembly.

When loose objects really form one asset, `group_as_asset` can establish a root. Preserve existing pivots and hierarchies when they already serve the task; its bottom-centre root is not a replacement for a deliberate kit anchor.

`prepare_assembly` adds `MarsoAtlas` to each part, packs one shared 0-1 layout, optionally bakes current colours (default enabled), and replaces all slots with a shared material. The inspected sizes are 2048 and 4096, default 4096. Existing UV layers and separate objects remain. A temporary joined, evaluated copy is used for upload; original objects are not joined.

Assembly preparation in 1.12.0 and 1.12.1 gives linked occurrences independent atlas space; earlier builds could share those islands. This does not repair stacks already present in a single mesh. For repeated parts included in one generation target, verify unique UV regions across every occurrence. Copying mesh data or joining objects alone leaves existing coordinates unchanged. Differently scaled linked instances also cannot be assumed to have consistent density. Check for users outside the target before changing data. Separately placed instances can reuse a verified textured master afterwards; do not flatten those instances into a fresh generation target with stacked UVs.

Hidden-face detection samples the current assembly and collapses those faces' atlas coordinates to a point. It is an approximation, not proof of invisibility in every view or future pose. Read the kit texturing reference for reusable or moving parts before allowing this operation.

When using the automatic fallback, explicit preparation allows inspection of the bake and UVs before generation. The prepared flag checks tags, layers and materials; it is not a geometry-change detector. Reinspect after edits. Repair an authored layout through its working-copy route; reprepare only when deliberately using the automatic assembly route. Repreparation changes UVs, so do not expect old generated maps to remain correctly aligned.

Record material-role intent before preparation replaces the original slot assignments. If the user needs an existing shader graph or exact slot separation preserved, work on independent copies and establish a verified transfer route or explain the constraint before replacing it. Do not claim the standard assembly path preserves those assignments.

Inspect the baked appearance on the upload copy before submission. Check a few recognisable contrasting regions against the editable source, not just whether an image exists. When custom preparation scripts replace material slots, preserve polygon assignments until the colour bake is complete; clearing slots can reset their indices and flatten the source's material guidance without failing UV or mesh preflight. When a custom bake temporarily changes metallic or transmission settings or links, restore them even on failure; the add-on's assembly bake handles its own.
