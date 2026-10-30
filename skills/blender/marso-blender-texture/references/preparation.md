# UVs, materials and assembly preparation

## Agent-authored layouts

When the agent can control Blender, preserve satisfactory existing UVs or author deliberate seams, unwrap and pack before submission. Use the add-on's automatic unwrap only as a fallback when that route is unavailable or the user requests quick automatic preparation; inspect its result to the same acceptance standard. A fallback does not waive UV quality requirements.

For a single mesh, validate the chosen export UV layer, provide the required base-colour texture, and pass `auto_uv: false` when supported. For multipart geometry, prefer an independent single-mesh texture working copy with a shared authored atlas and colour bake, while keeping the editable assembly intact. Keep this target outside tagged assemblies and inspect `assembly_state` to confirm the command will resolve to the intended target. Record source-to-working geometry correspondence and verify transfer back as described in [kit texturing](kits.md); matching counts alone are insufficient.

The inspected assembly path creates a fresh Smart UV layout; retaining older UV layers does not mean Retexture uses them. `auto_uv: false` controls missing UVs on a single mesh and does not disable automatic assembly preparation. Do not send a curated multipart layout through that path expecting preservation, or invent a preserve-UV parameter. Establish a verified working-copy handoff or report the capability gap if the installed route cannot preserve the required layout.

## Single mesh

Inspect faces, active/render UV layers, material slots, source images and evaluated modifiers. A UV layer's existence does not prove a usable unwrap. Retexture needs unique, non-mirrored, non-overlapping UV coverage for every surface being textured. Unstack mirrored/repeated islands on a working copy even when their final appearance should repeat; shared materials or instancing can be restored after generation. Check degenerate islands, coverage, padding, scale and direction with a checker where useful.

Read [UV acceptance](uv-acceptance.md) for the deterministic audit, authored-UV preparation and permanently hidden surfaces. Inspect a UV layout as well as the numerical result; packing coverage alone is not a quality score.

Keep final model form/construction acceptance separate from UV readiness. For newly modelled geometry with known major shape defects, return to modelling before final atlas/bake work unless the user specifically requested a UV diagnostic. For a ready target, validate useful narrow-chart sampling and spacing at the intended lower texture resolution, not only at the generation resolution. Re-bake and re-export after any atlas revision.

In the inspected implementation, missing UVs can be Smart UV projected, and missing base-colour textures get a blank 4096-pixel image filled from material colours. Every image texture node is checked for images over 4096 pixels; even an unused oversized image can block the single-mesh preflight. Preserve the source and resize a working copy when needed. Do not downsample shared source images globally.

Prefer a verified 0-1 UV layout for this workflow. Export's UV offset adjustment is not a complete UDIM conversion. Bake multiple tiles or complex procedural appearances to a supported working texture layout when necessary, preserving the editable source. Multiple material slots or unusual shader graphs require inspecting the returned slot mapping; do not assume every graph survives PBR application unchanged.

## Verify the actual upload

Every exported part used by 3D Asset Edit needs a usable colour texture. A plain material colour, an unused image node or a prepared-state flag is not sufficient. Verify that the intended shader uses the colour image and that the exported material carries it. Bake a simple material-region guide when needed; preserve distinct label/body/cap regions instead of flattening their intent.

Check the export's actual object and material inventory, especially with multiple scenes or an unfamiliar add-on build. Selection in the current view layer alone may not establish the exporter scope. Unintended objects can introduce untextured materials even when the intended target is valid. Use a recoverable, isolated working export when necessary, restoring temporary selection/visibility changes afterwards. Do not delete unrelated objects to make validation pass.

If the service returns `ASSET_EDIT_INVALID_INPUT`, retain the original response and inspect the uploaded file and named material. Correct the export or colour-texture preparation before another submission; retrying the same invalid input cannot fix it. The service's suggestion to run PBR is an alternative operation, not evidence that the requested Retexture succeeded. Report add-on preflight gaps separately rather than describing a skill workaround as an add-on fix.

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

The layout accounts for world-space scale, but linked mesh duplicates share their UV islands. Make repeated mesh data independent within a single Retexture target before preparation so surfaces do not stack in the upload. Differently scaled linked instances also cannot be assumed to have consistent density. Check for users outside the target before changing data. Separately placed instances can reuse a textured master afterwards.

Hidden-face detection samples the current assembly and collapses those faces' atlas coordinates to a point. It is an approximation, not proof of invisibility in every view or future pose. Read [kit texturing](kits.md) for reusable or moving parts before allowing this operation.

When using the automatic fallback, explicit preparation allows inspection of the bake and UVs before generation. The prepared flag checks tags, layers and materials; it is not a geometry-change detector. Reinspect after edits. Repair an authored layout through its working-copy route; reprepare only when deliberately using the automatic assembly route. Repreparation changes UVs, so do not expect old generated maps to remain correctly aligned.

Record material-role intent before preparation replaces the original slot assignments. If the user needs an existing shader graph or exact slot separation preserved, work on independent copies and establish a verified transfer route or explain the constraint before replacing it. Do not claim the standard assembly path preserves those assignments.

Inspect the baked appearance on the upload copy before submission. Check a few recognisable contrasting regions against the editable source, not just whether an image exists. When custom preparation scripts replace material slots, preserve polygon assignments until the colour bake is complete; clearing slots can reset their indices and flatten the source's material guidance without failing UV or mesh preflight.
