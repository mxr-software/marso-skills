---
name: marso-generate
description: "Generate 3D assets from images or descriptions with Marso. Choose supported mesh options, remember preferences and inspect results. Use for generation, not explicit agent modelling or retexturing."
license: Apache-2.0
---

# Generate an asset with Marso

Use the existing Marso connection in the user's application or Studio. Read [generation](references/generation.md) for source preparation, live capability discovery and the command differences between those routes. A skill supplies instructions, not tool access.

For an image-only request, use `marso-image` when installed rather than starting 3D generation. When this asset workflow needs an authored reference image, that companion can prepare and inspect it; continue with the already authorized mesh workflow after the image meets its intended shape/appearance brief. Appearance variants for an existing mesh belong to image authoring and Retexture, not repeated mesh generation.

1. Respect the requested route. Generate for explicit generation requests and organic/complex reconstruction when suitable. Do not substitute generation for a request to model editable geometry, build articulated parts or make precise modular interfaces. Existing geometry that only needs a new look goes to texturing.
2. Check whether the user already identified a source/library asset. Use it directly when unambiguous. Otherwise check the library when reuse fits the brief, using `marso-library` if installed or the connection's verified search tools. Skip searching when the user explicitly wants a newly generated asset. Never replace a chosen source with a lookalike.
3. Establish the user's preferred mesh model/options using [preferences and budgets](references/preferences.md). Reuse their supported choices on later runs. A single asset normally does not need a polygon-budget interview; a multi-object scene needs a shared budget.
4. Resolve the relevant Studio project, verify its returned id and record it. Preserve existing source, node and job identifiers when resuming.
5. Inspect the object reference, run the supported chain, follow its result and inspect the actual geometry and materials. Honour the user's review points. Native scene batches have separate image/mesh checkpoints; a standalone generation command can combine mesh and PBR and cannot provide a checkpoint it does not expose.
6. Deliver the asset, saved project/source identifiers, effective settings and remaining quality issues. Generated PBR is not proof of simulation physics, clean animation topology or modular fit.

Use `marso` when installed to coordinate a larger scene workflow; a completed prop is only one stage of that request.
