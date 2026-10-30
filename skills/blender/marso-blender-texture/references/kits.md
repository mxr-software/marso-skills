# Texturing reusable components

The unit of reuse determines the texture target. A wall panel, shelf, leg or corner module is a component; its internal fixed subparts may be one assembly. A whole kit or demonstration building is not automatically one asset for Retexture.

## Preserve future-visible surfaces

Texture component masters before arranging instances into a larger structure. Inspect all allowed orientations and moving states: attachment ends, undersides, door interiors and surfaces hidden by neighbouring modules may become visible later.

- For a single-mesh master, prepare full-face UVs and Retexture that mesh without assembly preparation. Keep it outside any tagged assembly that would redirect the command.
- For a fixed multipart component, isolate it from neighbouring modules and inspect which internal surfaces are permanently buried. Prefer the [agent-authored shared-atlas route](preparation.md#agent-authored-layouts). Automatic assembly preparation is a fallback only when replacing the layout and collapsing those surfaces cannot break reuse.
- For moving or rearrangeable subparts, keep independently reusable masters and texture their exposed surfaces independently. Do not run hidden-face optimisation on their closed/assembled configuration.
- If a required multipart shared atlas must preserve every face, the inspected `prepare_assembly` command has no such option. Do not pretend that it does. Use an explicitly verified full-face UV/bake workflow on an independent working mesh with a validated transfer back, or report that this particular path needs add-on support. Do not silently join the user's editable masters or transfer maps by object name alone.

Texture review must include a second arrangement that exposes different surfaces. A convincing render of the initial arrangement is insufficient.

When transferring a working-copy result back to a master, verify vertex coordinates, polygon connectivity and loop ordering before copying UV coordinates and material bindings. Equal counts or similar object names are insufficient. Check in the same coordinate space, accounting for any evaluated modifiers or transforms. If correspondence differs, use a validated bake/transfer instead of assuming that loop indices match. Confirm which linked instances will inherit the change, and save the generated images with the deliverable.

## Style and scale

Before a new family-wide treatment, test one representative component containing its important material transitions and structural features. Inspect geometry in neutral clay, the actual baked source colours, and the returned front/oblique/rear appearance under matched lighting. Expand only after that example supports the intended result. A job completing without errors is not visual acceptance; a warning or misplaced painted feature needs inspection before the same approach is repeated across the kit. Preserve failed candidates and repair a diagnosed cause rather than running automatic regeneration loops.

Keep a compact style brief for the kit: material roles, reference image, palette, roughness intent, physical pattern size and grain orientation. This is documentation for the agent, not a native Marso style-lock feature.

Persist it using the [appearance brief](appearance.md), including the accepted representative component and source revision. Read it when extending the kit; save component-specific additions and review outcomes with the result. Alternative looks follow [source-based variants](variants.md) so one restyled kit does not become the accidental input for the next.

For realistic packs, describe material structure at several scales: overall age/palette, medium-scale grain or tooling, and fine pores, fibres or mineral texture. Specify where each material belongs and how grain follows individual members; distinguish end grain from long grain. Ask for plausible roughness and surface relief, with restrained contextual wear. Rich detail does not require pervasive grime, deep cracks or high-contrast stains. Avoid requesting baked highlights/shadows as surface colour. Judge close views under neutral lighting as well as the assembled scene; a detailed prompt is guidance, not proof of photorealism.

When identical repeatable surface appearance matters, reuse one generated material on compatible UVs. `image_material` can make a shared PBR material from a flat swatch; check tileability and set UV mapping/physical scale in Blender. Generation does not automatically produce seamless tiling or match grain across a join.

For length variants such as beams, a verified crop of a longer member's material can preserve grain size better than stretching its entire atlas onto the shorter part. Map longitudinal faces at the same physical scale and treat end-grain and bevel charts separately. Establish surface correspondence geometrically; matching face counts alone is insufficient. Audit the new UVs, inspect end transitions and check repeated landmarks across instances. Preserve the original generated result on an independent working copy until the replacement passes review.

Use Retexture for object-specific appearance; compare related outputs side by side under the same lighting. Independently generated outputs are not guaranteed to match. A 4K atlas on each differently sized part does not imply equal texel density or equal physical grain size. Define a common density/pattern scale, measure it and adjust the UV/material strategy accordingly. Do not rescale a baked object's UVs after generation without checking its map alignment.

Measure each master's packed density before baking and choose a target that supports the intended viewing distance. A common target can help compare components, but do not blindly reduce every smaller part to the largest wall's density when that sacrifices needed detail. Use suitable per-component resolutions or higher atlas density for close-view parts, keeping physical grain/pattern scale consistent through the material brief and visual checks. Long thin islands can leave substantial unused atlas area even after packing; do not introduce conspicuous seams through continuous grain solely to fill the square. Numerical density measures sampling, not the pattern sizes or effective detail a generative model produces.

Record reference-bake resolution as well as returned map dimensions. A 4K output does not prove 4K source detail; an upscaled or softly generated image may still look blurred. Low-resolution bakes used for quick preparation tests are not automatically the right delivery setting. Inspect close renders before accepting detail quality, and test a supported higher-resolution reference/atlas on an independent target when it addresses a diagnosed weakness. Re-bake after UV changes and do not reuse an old texture with misaligned UVs.

Texturing linked masters affects their instances. For an individual variation, isolate mesh and material data first and record which version the instance uses. For a whole-kit restyle, operate on unique masters and reuse their results rather than regenerating every placed instance. Protect connector transforms, geometry and the master/instance mapping throughout.

## Visible joins and texture continuity

Read the kit's join strategy before generation. Natural breaks at timber edges, mortar joints, trim, rebates or shadow gaps can conceal differences between separate generated textures. If a join must be hidden by a cover, include that part in the kit and check its actual coverage and depth in allowed arrangements. Do not hide a seam only with camera placement or lighting.

Exact continuity needs a shared texture source and compatible mapping, not just matching prompts, references or texel density. Use a verified tileable material or trim sheet with a recorded physical repeat, direction and mapping origin/phase. At mating edges, sample the same source coordinates, or coordinates separated by whole repeats of a genuinely tileable map. Check normal-map/tangent orientation and roughness as well as colour. Document which rotations remain compatible; one straight join does not prove a rotated corner works.

This shared-surface strategy is distinct from the unique non-overlapping atlas required for a Retexture upload. If the deliverable requires independent unique atlases, bake the continuous shared material into those atlases with consistent sampling and sufficient gutters. Do not independently regenerate those baked boundary regions and assume continuity survives. Retexture has no inspected exact boundary-lock or protected-region parameter. A shared reference can guide appearance but cannot enforce pixel-identical edge values; use a shared material/bake, an explicitly supported constraint, or redesign the join when exact continuity is required.

Inspect close views across every intended join under common lighting, plus oblique views for relief/seam shadows. Check distinctive grain, stains and cracks crossing boundaries and conspicuous repetition. A successful cloud job or a distant room render does not establish seam quality.
