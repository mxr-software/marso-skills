---
name: marso-blender-asset
description: "Model or refine editable Blender assets from briefs, dimensions or reference images. Use for structured props and furniture; route texture-only work to texture and reusable component families to kit."
license: Apache-2.0
---

# Build an asset in Blender

Create the requested geometry, inspect it, and leave an editable asset ready for its next use. Modelling does not require generating textures. If the user asks for a finished textured asset, complete geometry and obtain model approval before using `marso-blender-texture` when available.

## Establish the target

Honour a request to model the asset. When the user instead asks to generate it, or an ambiguous brief favours an organic/complex form without controlled topology or construction requirements, use the `marso` entry skill when available to choose the generative route. Structured geometry, animation/articulation preparation and modular interfaces favour this modelling workflow. These are defaults, not guarantees of clean topology; inspect the result. Do not silently substitute generation for requested editable construction, or hand modelling for requested generation.

Inspect the connected Blender session, selection, units, existing objects and available control tools. The default is the official Blender MCP for modelling, with the Marso add-on for subsequent texturing. A Marso cloud connection alone does not establish general modelling access. If Blender control is missing, identify the missing capability; use `marso-blender-setup` if installed. Do not pretend a script delivered in chat was executed.

Use the brief and references to establish dimensions, proportions, silhouette, functional parts and required movement. Ask for a dimension only when its uncertainty materially changes the result; otherwise state an assumption. A single image does not establish hidden construction or absolute scale. Separate observed details from inferred ones.

Infer the quality target from the intended use: distant dressing, close-view prop, deforming mesh, articulated assembly or reusable kit. State useful defaults instead of asking the user to choose topology algorithms. Unless a blockout or faceted style is requested, aim for resolved surfaces and smooth silhouettes at the closest intended view. A low triangle count is not a success when the object still looks unfinished. Preserve an explicit modelling request for soft or complex objects too.

Keep changes within the requested asset. Inspect an existing model before choosing to repair or rebuild it. Save a recoverable checkpoint before substantial changes to existing work, without overwriting another file.

## Build and inspect

Before building a realistic or reference-matched asset, read [construction and quality](references/construction.md). Establish reference landmarks and choose construction per part. Save and inspect a geometry checkpoint before final UV preparation: record the inspected views, unresolved form/construction defects and the decision to repair or proceed. When scripting, separate geometry/preview execution from final atlas/bake/export execution so a render can actually change the next action. These internal checks need no extra user approvals. For a requested blockout, keep acceptance at blockout fidelity.

Before multiplying a master, retain a compact reference-backed comparison of its defining proportions and construction. Obtain complementary real-object references when the supplied view cannot resolve them. An arbitrary profile or scaled primitive does not become accurate because it has clean topology or fits a polygon budget.

- Work at the intended real-world scale. Check evaluated dimensions, including modifiers; do not change the whole scene's unit scale to fix one object.
- Block out the silhouette and major proportions first, then refine joints, thickness, bevels and shading. Match detail to the intended view and use.
- Keep moving, replaceable or independently reusable parts separate. Use clear names, a deliberate root and pivots appropriate to their function. Preserve editable modifiers where they help.
- Inspect normals, duplicate surfaces, unintended intersections, unsupported thin geometry and shading at representative distances. Watertight geometry is required when the requested downstream use needs it, not for every decorative surface.
- Inspect front, side and perspective views through the available viewport or render tools. Geometry counts and successful Python execution do not establish visual quality. If images cannot reach the assistant, report visual inspection as pending.

Before a photorealistic texturing handoff, compare a neutral-clay view with the reference at the intended viewing distance, including an oblique angle. Model features that need silhouette, depth, parallax, articulation or substantial contact shadows: for example a recessed plate, open vent or projecting trim. Leave coating grain, shallow scratches and small finish variation to textures. This is a feature-and-scale decision, not a minimum polygon count; excessive tiny bevel faces can waste UV sampling without improving the result. Restyle should finish the modelled structure, not be asked to invent missing structural detail on sparse geometry.

If the model is merely recognisable but its defining proportions, volumes or connections are wrong, the form check has failed. Diagnose and reshape or rebuild the affected part using the reference's repair guidance. Do not advance by adding fittings, subdivision, final UVs or texture prompts. If the available method cannot resolve the defect, deliver the saved model as partial with the specific limitation; do not spend the remaining effort completing a downstream checklist. An explicitly requested UV-only diagnostic can still run on unfinished geometry, with those results labelled separately. A successful script, clean topology or valid atlas cannot override a failed visual check.

For reusable modular components that must fit together, use `marso-blender-kit` when available; establish shared dimensions, connection frames and fit tests. Same-shaped objects with different labels/finishes use one master and the texture skill's appearance-family workflow instead. Do not independently model mating pieces and hope their edges line up.

## Review the model before texturing

Complete the internal form and construction checks first. Show the user the saved model in neutral clay from useful angles, including an oblique view at the intended viewing distance. State dimensions and remaining geometry or shading defects; avoid lighting that hides them. Ask whether the model is ready for Marso texturing, and wait for their answer before submitting Retexture or PBR. If essential geometry is still unresolved, present it as work in progress with the specific failure, not as a texture-ready candidate. A request for a finished textured asset is not approval of an unseen model.

Honour an explicit instruction to skip this review. Approval of the same unchanged model remains valid; record the approved source revision and covered parts with the handoff. Material changes to shape, proportions or visible detail require a new preview and approval. Routine UV preparation that preserves the approved appearance does not. If previews cannot be shown, disclose that limitation and wait for the user to review the saved model or explicitly waive review.

## Leave a useful texturing handoff

Give parts descriptive roles such as frame, upholstery, handle and fastener. Simple base colours can distinguish intended materials. Record exposed interiors and surfaces that become visible when parts move or are rearranged; record grain direction only when it matters to the brief.

Keep existing usable UVs and materials. Do not automatically prepare an atlas or invoke Marso during a geometry-only task. The texture workflow owns the final UV/bake decisions: assembly preparation can replace material assignments and collapse UVs for currently hidden faces.

For kits, place component masters in a collection rather than parenting the entire kit under an asset root that might be accidentally retextured as one object. A multipart component can have its own root. In a scene support hierarchy, use an entity Empty with a separate geometry group; independent supported assets attach to the entity Empty, not to its mesh. Preserve intentional rig/joint hierarchies inside the geometry group.

## Completion

Verify the requested dimensions, silhouette and editable part structure. Save the result to the agreed or clearly stated new location when file output is requested. Report the asset root, dimensions, meaningful assumptions and checks actually performed. Keep form/construction, mesh validity, UV readiness and user approval as separate statuses; identify pending or failed stages instead of reporting one overall pass. Identify geometry-only work as untextured; do not call a model simulation-ready merely because it has scale or pivots.
