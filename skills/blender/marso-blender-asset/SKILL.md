---
name: marso-blender-asset
description: Model or refine an editable 3D asset in Blender from a brief, dimensions, or reference images. Use for agent-built furniture, props, and building components, including geometry intended for later Marso texturing. Texture-only requests belong to marso-blender-texture; reusable component families belong to marso-blender-kit.
license: Apache-2.0
---

# Build an asset in Blender

Create the requested geometry, inspect it, and leave an editable asset ready for its next use. Modelling does not require generating textures. If the user asks for a finished textured asset, complete geometry first and then use `marso-blender-texture` when available.

## Establish the target

Honour a request to model the asset. When the user instead asks to generate it, or an ambiguous brief favours an organic/complex form without controlled topology or construction requirements, use the `marso` entry skill when available to choose the generative route. Structured geometry, animation/articulation preparation and modular interfaces favour this modelling workflow. These are defaults, not guarantees of clean topology; inspect the result. Do not silently substitute generation for requested editable construction, or hand modelling for requested generation.

Inspect the connected Blender session, selection, units, existing objects and available control tools. The default is the official Blender MCP for modelling, with the Marso add-on for subsequent texturing. A Marso cloud connection alone does not establish general modelling access. If Blender control is missing, identify the missing capability; use `marso-blender-setup` if installed. Do not pretend a script delivered in chat was executed.

Use the brief and references to establish dimensions, proportions, silhouette, functional parts and required movement. Ask for a dimension only when its uncertainty materially changes the result; otherwise state an assumption. A single image does not establish hidden construction or absolute scale. Separate observed details from inferred ones.

Keep changes within the requested asset. Inspect an existing model before choosing to repair or rebuild it. Save a recoverable checkpoint before substantial changes to existing work, without overwriting another file.

## Build and inspect

- Work at the intended real-world scale. Check evaluated dimensions, including modifiers; do not change the whole scene's unit scale to fix one object.
- Block out the silhouette and major proportions first, then refine joints, thickness, bevels and shading. Match detail to the intended view and use.
- Keep moving, replaceable or independently reusable parts separate. Use clear names, a deliberate root and pivots appropriate to their function. Preserve editable modifiers where they help.
- Inspect normals, duplicate surfaces, unintended intersections, unsupported thin geometry and shading at representative distances. Watertight geometry is required when the requested downstream use needs it, not for every decorative surface.
- Inspect front, side and perspective views through the available viewport or render tools. Geometry counts and successful Python execution do not establish visual quality. If images cannot reach the assistant, report visual inspection as pending.

Before a photorealistic texturing handoff, compare a neutral-clay view with the reference at the intended viewing distance, including an oblique angle. Model features that need silhouette, depth, parallax, articulation or substantial contact shadows: for example a recessed plate, open vent or projecting trim. Leave coating grain, shallow scratches and small finish variation to textures. This is a feature-and-scale decision, not a minimum polygon count; excessive tiny bevel faces can waste UV sampling without improving the result. Restyle should finish the modelled structure, not be asked to invent missing structural detail on sparse geometry.

For a reusable family, use `marso-blender-kit` when available; establish shared dimensions, connection frames and fit tests before multiplying variants. Do not independently model each piece and hope their edges line up.

## Leave a useful texturing handoff

Give parts descriptive roles such as frame, upholstery, handle and fastener. Simple base colours can distinguish intended materials. Record grain direction, exposed interiors and any surfaces that become visible when parts move or are rearranged.

Keep existing usable UVs and materials. Do not automatically prepare an atlas or invoke Marso during a geometry-only task. The texture workflow owns the final UV/bake decisions: assembly preparation can replace material assignments and collapse UVs for currently hidden faces.

For kits, place component masters in a collection rather than parenting the entire kit under an asset root that might be accidentally retextured as one object. A multipart component can have its own root.

## Completion

Verify the requested dimensions, silhouette and editable part structure. Save the result to the agreed or clearly stated new location when file output is requested. Report the asset root, dimensions, meaningful assumptions and checks actually performed. Identify geometry-only work as untextured; do not call a model simulation-ready merely because it has scale or pivots.
