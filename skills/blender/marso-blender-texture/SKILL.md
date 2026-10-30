---
name: marso-blender-texture
description: "Texture, retexture or restyle Blender assets with Marso, create appearance packs, or add PBR. Includes UV preparation and material checks. Preserve geometry; use asset modelling for new shapes."
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
| Many differently labelled/finished copies of the same shape | Read [appearance families](references/appearance-families.md): one master per geometry family, independent looks, then instances. The edited-grid option needs a pilot. |
| Keep the existing base-colour appearance and derive PBR maps | Auto PBR via `pbr_generate`, after inspecting the queue. |
| Make a reusable surface material from a flat fabric, wood or other swatch | `image_material`; create without automatic application when only selected slots should change. |

A photographed object is a style reference for Retexture, not automatically a seamless surface swatch. Prefer the requested route; do not substitute an ordinary Blender procedural material for a requested Marso result.

## Model approval checkpoint

When this workflow follows new modelling or substantial geometry edits, confirm that the user has seen useful neutral-clay previews and approved the current source revision and target parts before submitting Retexture or PBR. If not, save and show the model, state dimensions and visible defects, ask whether it is ready for texturing, and wait. An overall request for a textured asset is not approval of an unseen model; elapsed time is not approval either. If images cannot be shown, let the user review the saved model or explicitly waive review.

Respect an explicit instruction to proceed without model review. Reuse approval for unchanged geometry; renew it after material changes to shape, proportions or visible detail. Routine UV preparation that preserves the approved appearance does not invalidate approval. For kits, record which components the approval covers. A direct request to retexture an existing asset without geometry changes needs no additional model-approval question. Once internal form/construction checks pass, local inspection and reversible preparation may continue while user approval is pending, but cloud texturing must wait. Known major form defects return to modelling before final UV/bake work; an explicitly requested UV diagnostic on unfinished geometry remains a separate result.

## 2. Prepare the target

Read [UVs and assemblies](references/preparation.md). Save a recoverable checkpoint before replacing authored UV/material arrangements. Isolate shared data when only one instance should change; retain sharing when a change is meant to affect the whole family.

Marso does not currently generate transparency. Resolve clear parts before upload using the [transparency handoff](references/preparation.md#transparent-parts): exclude and restore them, or use returned maps with a locally defined transparent region. Preserve opaque labels and material-role correspondence.

With Blender control available, prefer agent-authored seams, unwrapping and packing, and preserve an existing layout that passes inspection. The add-on's automatic unwrap is a fallback, not the default preparation for agent workflows. Validate the actual upload layout and select a handoff that preserves it: automatic assembly preparation can replace the layout even when missing-UV generation is disabled. Read the authored-layout route in [preparation](references/preparation.md#agent-authored-layouts).

Check that the geometry can support the requested appearance at its intended viewing distance. Large recesses, openings, panel depth and prominent hardware should already exist when they are essential to the reference. Do not compensate with requests for intricate painted machinery. If a texture-only task needs modelling to meet the reference, explain that limitation rather than silently rebuilding the asset.

For Retexture, require non-mirrored, non-overlapping UVs on textured faces. Exclude faces only when they remain hidden across all intended views, movements and kit arrangements. Temporary occlusion or being off-camera is insufficient. Keep editable source geometry when simplifying a texture/export copy.

For a scene built with entity Empties, select only the intended geometry group or its parts. Do not prepare the entity/support Empty recursively: its children can include separate supported assets. Keep support transforms and metadata outside the texture target.

Always inspect `assembly_state` for the named target. A fixed multipart asset is retextured as one assembly, with a prompt describing all its material roles. A kit collection is several reusable components, not automatically one texture target. A tagged child may resolve to the whole previously prepared assembly: verify the returned root and parts before proceeding.

For reusable components, read [kit texturing](references/kits.md). Resolve surfaces that can become exposed before running assembly preparation. Do not invent a preserve-hidden-faces parameter.

## 3. Describe and run the change

For a kit, a coordinated set or a look that will be reused, save a compact [appearance brief](references/appearance.md) with the asset. For multiple looks of the same mesh, read [source-based variants and material naming](references/variants.md): branch each look from the preserved original/prepared baseline, never from the previous generated look. This is a finite requested set, not an automatic refinement loop.

Read [appearance prompts and image handoff](references/prompts.md) before authoring a new look. Write a concise visual brief: material roles, colour, finish, fine detail and condition. Keep UV/topology preservation and export checks in local preparation/validation, outside the Retexture prompt. For requested image-guided looks, use `marso-image` when installed and inspect the returned image before transfer; the local reference also supports this skill on its own.

For a reference-driven kit, add a separate explicit description for each piece: its existing features, material regions, fine/medium surface detail, wear placement, backs and returns, and what the reference should contribute. Separate coloured scene lighting from base colour. A shared style phrase alone is insufficient for a housing, seal, glass screen and diffuser to receive different plausible finishes.

Keep one coherent brief for related kit parts, with each reference's role explicit. A shared reference can guide the family; a component-specific image can explain its own material treatment. Describe finishes on features that actually exist, without asking Restyle to add new vents, fasteners or panel divisions. Matching prompts alone do not guarantee matching generated materials. For selective changes, prompt language is guidance, not an exact region mask; inspect protected regions afterwards.

Default to a detailed text brief and `reference_path: ""`. Scene photographs guide the brief; do not attach a crop to Retexture unless the user explicitly requests an image reference. Clutter can be painted onto the target. When a reference is requested, inspect it for neighbours, markings and coloured lighting and explain which material features it should guide. Pass `enhance: ""` for the literal authored brief unless the user wants the panel's added enhancement text. Use `@reference_label` to describe where a supplied reference should apply.

Resolve Retexture's destination using the installed capabilities and the [command workflow](references/commands.md); some builds use a legacy automatic destination. For several approved targets, prefer the native batch route when available. For an individual job, retain its ID, return control to Blender and inspect it in later calls. A tool timeout is not a reason to submit again. Reconcile existing jobs/batches before retrying; repair a diagnosed cause instead of repeatedly regenerating.

For several assets, read [batch completion](references/batches.md). Establish an acceptable representative final result before expanding a new method. Submit eligible items once and let the add-on monitor and advance them. Preserve requested review checkpoints, prepared baselines and the captured Studio project. Older builds retain the documented individual-job fallback.

Match that destination to the user's actual project or create/select a relevant new project before generation. Record the selection with the asset, verify persistence, and check the outputs belong there. A legacy generic Blender project is not an acceptable fallback when a specific project is required.

## 4. Verify the result

Retexture proceeds directly to PBR before final application and review; do not insert an intermediate appearance-approval step unless explicitly requested. Follow an add-on-owned chain rather than submitting duplicate PBR. Report technical completion and visual acceptance separately; a conditional pilot with unresolved quality problems is not permission to scale the method.

Check the job result and warnings, then the scene itself:

- Expected objects have the intended material bindings and UV map; no unrelated shared instances changed.
- Returned maps are present and connected; colour maps use colour space appropriate to colour, data maps use Non-Color, and returned normal maps have the expected interpretation.
- Appearance matches the brief in material/rendered views, including seams, stretch, grain scale, bevels, backs, interiors and changed arrangements where relevant.
- Under changed light, material response is plausible; inspect residual baked highlights and false embossed print. Keep raw maps and any local shader adjustments distinct. Use the established quality/viewing target rather than lowering it after a weak result.
- Painted panel lines, vents, fasteners or shadows do not contradict the modelled structure. Inspect the actual upload bake when material regions drift; do not assume a longer prompt will fix it.
- Shape, dimensions, hierarchy and connection frames remain intact. Partial success or a quality warning requires inspection, not a blanket success claim.
- Texture images remain available after saving: verify packed images or valid dependencies. Do not promise a map type the service did not return.

Give appearances clear asset/style/role labels using [the naming rules](references/variants.md#name-materials-after-successful-application). Keep material names stable while jobs are pending. After successful application, rename only with verified identity-based tracking or a supported rename operation; with legacy name-based tracking preserve prepared-material names and use external style labels instead. Record final bindings and results in the appearance brief when one is in use.

Report the operation, affected objects, project and returned asset IDs where available, saved output, and any remaining visual defect. Retexturing and PBR alone do not establish simulation readiness.
