# UVs, materials and assembly preparation

## Single mesh

Inspect faces, active/render UV layers, material slots, source images and evaluated modifiers. A UV layer's existence does not prove a usable unwrap. Retexture needs unique, non-mirrored, non-overlapping UV coverage for every surface being textured. Unstack mirrored/repeated islands on a working copy even when their final appearance should repeat; shared materials or instancing can be restored after generation. Check degenerate islands, coverage, padding, scale and direction with a checker where useful.

Read [UV acceptance](uv-acceptance.md) for the deterministic audit, authored-UV preparation and permanently hidden surfaces. Inspect a UV layout as well as the numerical result; packing coverage alone is not a quality score.

In the inspected implementation, missing UVs can be Smart UV projected, and missing base-colour textures get a blank 4096-pixel image filled from material colours. Every image texture node is checked for images over 4096 pixels; even an unused oversized image can block the single-mesh preflight. Preserve the source and resize a working copy when needed. Do not downsample shared source images globally.

Prefer a verified 0-1 UV layout for this workflow. Export's UV offset adjustment is not a complete UDIM conversion. Bake multiple tiles or complex procedural appearances to a supported working texture layout when necessary, preserving the editable source. Multiple material slots or unusual shader graphs require inspecting the returned slot mapping; do not assume every graph survives PBR application unchanged.

## Fixed multipart asset

Use an explicit `object_name` for `assembly_state`, preparation and Retexture. Omitted names can include selected objects. Inspect actual parts: visible mesh descendants are included; hidden parts can be excluded. A previously tagged child can resolve to its entire assembly.

When loose objects really form one asset, `group_as_asset` can establish a root. Preserve existing pivots and hierarchies when they already serve the task; its bottom-centre root is not a replacement for a deliberate kit anchor.

`prepare_assembly` adds `MarsoAtlas` to each part, packs one shared 0-1 layout, optionally bakes current colours (default enabled), and replaces all slots with a shared material. The inspected sizes are 2048 and 4096, default 4096. Existing UV layers and separate objects remain. A temporary joined, evaluated copy is used for upload; original objects are not joined.

The layout accounts for world-space scale, but linked mesh duplicates share their UV islands. Make repeated mesh data independent within a single Retexture target before preparation so surfaces do not stack in the upload. Differently scaled linked instances also cannot be assumed to have consistent density. Check for users outside the target before changing data. Separately placed instances can reuse a textured master afterwards.

Hidden-face detection samples the current assembly and collapses those faces' atlas coordinates to a point. It is an approximation, not proof of invisibility in every view or future pose. Read [kit texturing](kits.md) for reusable or moving parts before allowing this operation.

Explicit preparation is useful for inspecting the bake and UVs before generation. The prepared flag checks tags, layers and materials; it is not a geometry-change detector. Reinspect after edits, and reprepare a fixed assembly when its layout no longer fits. Repreparation changes UVs, so do not expect old generated maps to remain correctly aligned.

Record material-role intent before preparation replaces the original slot assignments. If the user needs an existing shader graph or exact slot separation preserved, work on independent copies and establish a verified transfer route or explain the constraint before replacing it. Do not claim the standard assembly path preserves those assignments.

Inspect the baked appearance on the upload copy before submission. Check a few recognisable contrasting regions against the editable source, not just whether an image exists. When custom preparation scripts replace material slots, preserve polygon assignments until the colour bake is complete; clearing slots can reset their indices and flatten the source's material guidance without failing UV or mesh preflight.
