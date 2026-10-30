# Appearance direction and review

## Give realism a material basis

Specify the object, materials, condition and distinctive finish. Describe detail at the scale the returned image can show. Select a few relevant cues instead of adding every imperfection to every surface:

| Material and condition | Useful visible cues |
| --- | --- |
| Clean printed metal packaging | Fine formed-metal texture at exposed rims, subtle lacquer variation, flush ink, restrained handling scuffs near contact edges |
| New paper or card | Fine fibres, slight surface variation, believable fold edges and print response; exposed fibres at worn edges only where appropriate |
| Maintained wood furniture | Natural variation in grain and pores, finish variation across the surface, restrained contact wear consistent with use |
| Glazed ceramic | Small glaze variation, believable transitions around edges and recesses; crazing, chips or stains only for a condition that calls for them |

"Photorealistic" is a target, not a complete material description. Do not default realistic work to flawless advertising/product photography, extreme gloss, uniform smoothing or dramatic studio glare. Lighting should reveal volume and material behavior while leaving the surface readable. Preserve a requested commercial studio aesthetic, but do not infer it merely from a request for realism.

Realism also depends on correct shape and construction. Surface detail cannot repair an implausible shoulder, rim, joint or proportion. Keep subtle natural variation; avoid uniform dirt, noise or scratches spread indiscriminately over an otherwise clean object. Do not demand imperfections below the useful pixel size and then claim they were generated.

## Separate the prompt jobs

**Image generation:** describe the intended object/scene, appearance, condition and useful view. Add reference roles when references are supplied. Do not constrain an imaginary source layout.

**Image editing:** describe the new appearance and what the actual source contributes. A concise shape-guide instruction is enough; do not repeat it in every sentence. For grids, include cell identity and explicit per-cell differences, with only the arrangement constraints needed to recover each variant.

Example for an existing blank can guide:

> Use the supplied image for the can's shape and blank label region. Give it a believable red beverage finish: deep crimson printed lacquer, crisp white lettering sitting flush with the surface, subtle coating variation and tiny handling scuffs near the rolled edges. Exposed aluminium has fine forming marks and a softer brushed finish. Clean, recently handled packaging with natural material detail and lighting that reveals the curved surface. Keep the same framing and label placement.

For several variants, establish shared materials/condition once, then describe each cell's own palette, print character and finish. Avoid a long list of prohibitions or operational directions that overwhelms the appearance description. Exact text, logos or barcodes need controlled artwork when fidelity is required; generative images are not a guarantee of correct print.

**Retexture handoff:** use the accepted image for appearance and a brief description of each material region. Do not repeat grid coordinates, image-camera instructions, UV preservation, mesh export or unsupported rear-seam controls. A useful brief is "Use the reference for the crimson print; flat white ink on subtly varied lacquer, lightly brushed exposed aluminium and faint rim handling marks." Preserve technical requirements in the run record and validate them with application tools.

## Check the image, then the transferred material

An appearance image is ready for transfer when its shape/regions are compatible, its finish matches the brief, the material has believable scale and variation, and the actual crop has enough detail for the intended use. A glossy highlight does not by itself demonstrate realistic surface detail. Inspect at the intended view and close enough to distinguish surface features from blur or illustration.

Keep image acceptance separate from the final Retexture → PBR assessment. Inspect the final material under changed lighting for residual baked glare, false raised print, lost regions or transfer seams. A visually weak reference should be corrected before generating many variants; a successful image can still fail on the mesh. Record the cause and fix that stage, rather than making every downstream prompt longer.

During a deliberate prompt comparison, keep the approved shape guide, framing and other supported settings fixed so changes can be assessed. Do not claim that a prompt alone caused an improvement when the source render, geometry and lighting changed too. Record uncontrollable service variation; no deterministic seed is assumed.
