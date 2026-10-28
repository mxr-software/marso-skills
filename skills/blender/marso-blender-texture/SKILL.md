---
name: marso-blender-texture
description: Add textures, change textures, restyle, make style variants, or generate PBR for existing Blender assets using Marso. Includes UV preparation, reusable appearance briefs, named materials and variants from the original source. Use for appearance changes rather than rebuilding geometry.
license: Apache-2.0
---

# Texture and restyle with Marso

Use Marso to create the requested appearance on the existing asset. Treat "add a texture", "change the texture", "retexture" and "restyle" as entry points to this workflow. Prepare geometry only as needed for texturing; preserve dimensions, shape, hierarchy, pivots and kit connections.

## 1. Inspect and choose the operation

Identify the intended Blender session and exact objects, their materials and UVs, shared mesh/material users, and whether they are fixed assemblies or reusable/moving parts. Inspect the current appearance before changing it. Use the working Blender connection and Marso add-on; hosted Marso MCP is optional. Missing configuration belongs to `marso-blender-setup` when available.

Read [commands and jobs](references/commands.md) before invoking Marso. Discover the installed schemas rather than assuming tool prefixes or command availability.

| Intent | Route |
| --- | --- |
| New appearance from a description or style reference | `retexture`: edit appearance, generate PBR and apply maps. |
| Keep the existing base-colour appearance and derive PBR maps | Auto PBR via `pbr_generate`, after inspecting the queue. |
| Make a reusable surface material from a flat fabric, wood or other swatch | `image_material`; create without automatic application when only selected slots should change. |

A photographed object is a style reference for Retexture, not automatically a seamless surface swatch. Prefer the requested route; do not substitute an ordinary Blender procedural material for a requested Marso result.

## 2. Prepare the target

Read [UVs and assemblies](references/preparation.md). Save a recoverable checkpoint before replacing authored UV/material arrangements. Isolate shared data when only one instance should change; retain sharing when a change is meant to affect the whole family.

Check that the geometry can support the requested appearance at its intended viewing distance. Large recesses, openings, panel depth and prominent hardware should already exist when they are essential to the reference. Do not compensate with requests for intricate painted machinery. If a texture-only task needs modelling to meet the reference, explain that limitation rather than silently rebuilding the asset.

For Retexture, require non-mirrored, non-overlapping UVs on textured faces. Exclude faces only when they remain hidden across all intended views, movements and kit arrangements. Temporary occlusion or being off-camera is insufficient. Keep editable source geometry when simplifying a texture/export copy.

For a scene built with entity Empties, select only the intended geometry group or its parts. Do not prepare the entity/support Empty recursively: its children can include separate supported assets. Keep support transforms and metadata outside the texture target.

Always inspect `assembly_state` for the named target. A fixed multipart asset is retextured as one assembly, with a prompt describing all its material roles. A kit collection is several reusable components, not automatically one texture target. A tagged child may resolve to the whole previously prepared assembly: verify the returned root and parts before proceeding.

For reusable components, read [kit texturing](references/kits.md). Resolve surfaces that can become exposed before running assembly preparation. Do not invent a preserve-hidden-faces parameter.

## 3. Describe and run the change

For a kit, a coordinated set or a look that will be reused, save a compact [appearance brief](references/appearance.md) with the asset. For multiple looks of the same mesh, read [source-based variants and material naming](references/variants.md): branch each look from the preserved original/prepared baseline, never from the previous generated look. This is a finite requested set, not an automatic refinement loop.

Write a concrete material brief: what each part is made of, colour, finish, grain direction and intentional wear. Preserve features outside the requested change. For example: "Walnut cabinet panels with vertical grain, satin finish, brushed steel handles; retain the existing panel divisions."

For a reference-driven kit, add a separate explicit description for each piece: its existing features, material regions, fine/medium surface detail, wear placement, backs and returns, and what the reference should contribute. Separate coloured scene lighting from base colour. A shared style phrase alone is insufficient for a housing, seal, glass screen and diffuser to receive different plausible finishes.

Keep one coherent brief for related kit parts, with each reference's role explicit. A shared reference can guide the family; a component-specific image can explain its own material treatment. Describe finishes on features that actually exist, without asking Restyle to add new vents, fasteners or panel divisions. Matching prompts alone do not guarantee matching generated materials. For selective changes, prompt language is guidance, not an exact region mask; inspect protected regions afterwards.

Pass an explicit prompt, intended target and reference choice. Use `reference_path: ""` when no reference is intended, so an old panel image is not silently reused. Pass `enhance: ""` for the literal authored brief unless the user wants the panel's added enhancement text. Use `@reference_label` to describe where a supplied reference should apply.

Resolve Retexture's destination using the installed capabilities and the [command workflow](references/commands.md); some builds use a legacy automatic destination. Start one job, retain its ID, return control to Blender and poll in later calls. A tool timeout is not a reason to submit again. Inspect existing jobs and results before retrying; repair a diagnosed cause instead of repeatedly regenerating.

Match that destination to the user's actual project or create/select a relevant new project before generation. Record the selection with the asset, verify persistence, and check the outputs belong there. A legacy generic Blender project is not an acceptable fallback when a specific project is required.

## 4. Verify the result

Check the job result and warnings, then the scene itself:

- Expected objects have the intended material bindings and UV map; no unrelated shared instances changed.
- Returned maps are present and connected; colour maps use colour space appropriate to colour, data maps use Non-Color, and returned normal maps have the expected interpretation.
- Appearance matches the brief in material/rendered views, including seams, stretch, grain scale, bevels, backs, interiors and changed arrangements where relevant.
- Painted panel lines, vents, fasteners or shadows do not contradict the modelled structure. Inspect the actual upload bake when material regions drift; do not assume a longer prompt will fix it.
- Shape, dimensions, hierarchy and connection frames remain intact. Partial success or a quality warning requires inspection, not a blanket success claim.
- Texture images remain available after saving: verify packed images or valid dependencies. Do not promise a map type the service did not return.

Give the applied material sets clear asset/style/role names using [the naming rules](references/variants.md#name-materials-after-successful-application). Preserve submission-time material names while a job runs because the add-on uses them for map matching. Record final bindings and results in the appearance brief when one is in use.

Report the operation, affected objects, project and returned asset IDs where available, saved output, and any remaining visual defect. Retexturing and PBR alone do not establish simulation readiness.
