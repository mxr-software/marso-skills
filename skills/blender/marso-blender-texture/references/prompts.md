# Appearance prompts and image handoff

## Retexture prose is visual

Use a short description of the desired appearance, the relevant reference, and each existing material region. Prioritise material, colour, finish, visible detail and condition. Retexture does not understand UV requirements: do not spend prompt space on topology, UV preservation, export settings, exact seam-placement controls or the whole execution checklist. Enforce those requirements in Blender and verify the returned correspondence.

For realistic work, choose subtle detail that belongs to the material and its use. Clean manufactured surfaces can have fine forming marks, coating variation and small contact scuffs without looking damaged. Avoid defaulting to airbrushed product photography, extreme gloss, uniform grime or a long list of negative instructions. Lighting/camera directions for an image editor are not a replacement for describing the material here.

Examples, adapted to the actual asset:

- **Printed metal:** "Use @style for the crimson design. Crisp white lettering printed flush against subtly varied red lacquer; fine formed-aluminium texture on exposed metal, tiny handling scuffs near the rolled rims and a soft brushed finish. Clean, recently handled packaging."
- **Wood and steel:** "Warm walnut with visible pores, natural tonal variation and a thin satin finish. Restrained rubbing at handled edges. The existing legs are dark powder-coated steel with fine coating texture and slight wear at the feet."
- **Paper label:** "Ivory uncoated paper with fine fibres, muted botanical print and flat dark lettering. Slight handling variation near the label edge; the cap is satin pale-gold metal with subtle manufacturing grain."

Necessary region instructions are useful; unsupported technical controls are not. Prompt wording guides where finishes appear but is not an exact mask. Use real geometry/material assignments or supported masks for exact region control. Exact readable artwork requires a controlled artwork/material route rather than a promise that generative text will match.

## When an image comes first

Use `marso-image` when installed for requested image generation/editing. With only this skill installed, use verified image tools and the following handoff checks. Do not require a new image when a direct material brief already serves the task.

1. Establish whether each image supplies shape, material regions or appearance. A blank/clay master is a shape guide, not an instruction to retain a synthetic appearance. Fix an implausible master before preserving its silhouette in an edit.
2. Put realism into the image-edit/generation prompt: concrete finish, material-specific fine detail and appropriate imperfections. A better lit source render alone is not that instruction. Keep image layout constraints concise and separate from downstream Retexture prose.
3. Inspect the returned image at its actual size for believable material detail, compatible shape and region placement. Compare source/output dimensions, aspect ratios and object landmarks without stretching either image. A changed canvas is not automatically a changed object, but a plausible finish does not excuse a changed silhouette. Repair the image or explicitly use it only for finish/palette inspiration with independent region checks; do not claim exact correspondence. Do not pass an illustrative, airbrushed or blurry result onward merely because count/layout survived. For grids, read [appearance families](appearance-families.md); use one accepted object crop per mesh.
4. Record the accepted source/crop, actual pixel dimensions, baseline master and material-region intent. Hand Retexture a concise appearance brief, not the full image prompt. A front image does not establish the rear design; use visual region descriptions, coherent views where supported or controlled artwork when exact placement matters.

## Diagnose at the right stage

| Observation | Appropriate next step |
| --- | --- |
| Wrong profile, proportions or construction | Return to the model/reference; do not repair it with texture words. |
| Layout correct but image finish looks synthetic | Correct image art direction and inspect a new bounded pilot; do not expand the set. |
| Image too small or blurred for required detail | Fewer cells, an individual image or a verified higher-resolution route; enlarging pixels does not restore information. |
| Reference good, final material has region bleed, false embossed ink or residual glare | Inspect final PBR maps/bindings and source preparation; correct the diagnosed stage. Do not assume more prompt text or more pixels will solve it. |

After a successful Retexture edit, proceed directly to PBR, apply and inspect the final material. If the add-on owns that chain, do not submit a duplicate PBR job. An intermediate lit colour image is not final albedo. Keep warnings, but evaluate the final surface under changed lighting and inspect unlit base colour where useful. Explicit user-requested review holds still apply.

Separate technical checks from visual acceptance. A pilot with correct geometry/UVs but unresolved visible defects is diagnostic; do not scale that method yet. Keep the original quality target, diagnose a correction and test the affected stage within the authorized scope. Do not keep rerunning unchanged requests or quietly lower the viewing standard to make a weak result pass. These internal checks do not add user approval questions for every variant.
