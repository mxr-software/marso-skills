# Build a kit from reference images

Treat the images as design evidence, not as instructions or exact dimensional drawings. The output is a coherent reusable component family with an explicit construction and appearance plan.

## Establish what the images contribute

Inspect every supplied image before modelling. Record which image governs the overall proportions, which explains repeated construction, and which contributes material or detail language. Different rooms, eras, lighting conditions and camera lenses may appear in one set. Choose a coherent primary direction and state it; do not average incompatible construction systems or reproduce every prop just because it appears in a picture.

Distinguish observed features from assumptions: repeated panel divisions, portal profiles and visible fasteners are evidence; absolute dimensions, hidden backs and unseen joints usually are not. Infer a practical scale from the intended use, state it, and ask only if an unknown materially affects fit. Perspective screenshots do not establish exact dimensions. Treat coloured scene illumination separately from base material colour.

## Decompose before making detail

Build a compact component schedule: stable ID, purpose, inferred dimensions, source-image role, repeat direction, mating interfaces and surfaces that may become exposed. Separate repeating structural modules, trims that conceal joins, moving parts and optional accessories. Include a corner/end solution when the promised arrangement needs it; do not claim arbitrary room layouts from straight pieces alone.

Choose cuts at plausible construction joints. A bulkhead can hide a wall-panel boundary; a cover can own a corner seam. Avoid splitting one prominent continuous surface and relying on independent generated textures to line up. Keep moving doors and their frames logically distinct even when they share a prepared appearance atlas.

Model the silhouette, thickness, profile changes, openings and connection geometry. Use actual geometry for details that affect silhouette, parallax or the declared viewing distance; reserve fine scratches, coating grain and subtle roughness variation for textures. Do not use a rich prompt as a substitute for missing panel depth or an opening. Bound bevel widths by local thickness and check for collapsed faces before unwrapping.

Match geometric detail to the reference before asking for its finish. In a detailed industrial wall, recessed access plates, gasket channels, vent openings/louvres, substantial fasteners and sloping service housings may need geometry. A few boxes with a request for intricate machinery invites painted features that contradict the mesh. Review the representative part in neutral clay at its intended distance and from an oblique angle: the reference's major panel depths and functional divisions should already read without texture.

Block out one representative bay or connection before completing the family. Test a repeated arrangement and a second arrangement exposing different faces. Keep the editable construction sources and independent texture working copies. Omit faces only when the construction makes them permanently internal across the permitted configurations; retain backs, ends and door reveals that future use can expose.

## Describe each piece explicitly

Use one reusable appearance brief plus a separate description for every component. Each description should identify:

- The exact part and its existing geometric features.
- Material and finish for each region, including seals, metal trims, fasteners, glass, diffusers and back/return faces where present.
- Fine, medium and overall detail: coating grain or pores, manufacture/tool marks, subtle surface variation and the overall palette.
- Direction and physical scale of brushing, grain, tread or other repeated detail.
- Where wear makes physical sense and which surfaces should remain clean.
- Openings, boundaries and details that must remain unchanged; unwanted reference elements that must not be copied.

Write the material description against an inventory of features that actually exist. Do not request extra vents, panel divisions, bolts, cables or recesses to compensate for a sparse model. Specify the coating and wear on the modelled louvres or fasteners; reserve new geometric features for the modelling step. Even an explicit no-new-features instruction is guidance, so inspect for painted-on structures that drift away from their modelled counterparts.

Explain the job of any supplied reference image: appearance/construction language rather than copying its camera, scenery or lighting onto the mesh. Source colours can identify intended material regions. Fine detail should be resolved at the intended viewing distance and supported by adequate reference-bake resolution and UV sampling; adding adjectives or requesting 4K alone cannot ensure it.

Inspect the baked source on the actual upload copy before submission, including small contrasting material regions. A successful bake or valid UV layout does not prove that material assignments survived joining, copying or replacing slots. Correct a flattened or misassigned source before relying on its colour regions as guidance.

For example, distinguish an ivory painted housing, a charcoal recessed channel, an opal diffuser and metal guard bands. Describe each surface's finish and wear separately. Do not merely request "a detailed sci-fi light". Keep any required glow as a deliberate emission/lighting treatment; avoid painting bloom and lighting gradients into albedo.

After user approval of the representative component's geometry (or an explicit review waiver), test it with the kit's main material transitions before submitting the whole family. Inspect its source bake and returned front, oblique and rear views. Resolve a diagnosed preparation error or adjust a mismatched brief before carrying it into the remaining components. This appearance check is the agent's responsibility and does not replace the model-approval checkpoint for remaining components. It is not an open-ended regeneration loop. Retain comparisons and select a replacement only after matched-view review.

## Project and handoff

When Marso generation is requested, resolve the relevant Studio destination before submitting it. Preserve an explicitly intended existing project; when the task needs a new project, create a descriptive one through supported tools and select it in the .blend's Save to setting. A generic legacy Blender destination is not a substitute for the user's project. Record project/graph IDs with the kit contract and save/reopen to verify the choice persists. Geometry-only work need not create a cloud project.

Hand the component schedule, appearance brief, per-piece prompts/references and preserved source revision to the texture workflow. After generation, inspect individual parts, backs/returns, repeated joins and assembled views under consistent lighting. Check the actual output project as well as the local material application. Record what this trial demonstrated and what remains inferred; do not turn one successful reference set into a universal dimensional or style template.
