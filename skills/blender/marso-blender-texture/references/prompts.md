# Appearance prompts and image handoff

## Retexture prose is visual

The text prompt is the main control. It carries the whole look: Retexture is run without a reference image.

Write it the way you would describe the object to a person: plainly and quickly. Use two or three short sentences, about 150 to 300 characters. Extra words dilute what matters.

1. Say what the object is and what each main material is: "an old watering can painted in green enamel paint, with a golden brass spout".
2. Say its condition, at the strength the brief asks: "the green paint is flaking off in areas, and there is heavy corrosion and general weathering".
3. Add a marking only when the brief has one, and say which flat face it sits on. Lettering that crosses a raised batten, groove or step smears down its side faces and looks stretched.
4. End with "Lots of detail, photorealistic."

The whole prompt for that brief:

> An old watering can painted in green enamel paint, with a golden brass spout. The green paint is flaking off in areas, and there is heavy corrosion and general weathering. Lots of detail, photorealistic.

Cut these before sending:

- **Part lists.** Name a part only where its material differs from the rest ("a golden brass spout"). Never list the parts a material covers.
- **Stacked description.** "Small irregular flakes lifting at the rolled edges" becomes "the paint is flaking off in areas".
- **Hedges.** "Most of the paint is intact", "subtle", "occasional" and "varies naturally" weaken the wear the brief asked for.
- **Shape, UV, topology, seam, export and camera words.** The mesh holds the shape; enforce the rest in Blender.

Nothing in the real world is truly clean, so every prompt names some wear, dust or marks, even for a new object. Leave out "plain", "uniform", "flawless", "pristine", "factory-new" and "clean", and never write "no wear", "no patina" or "no scratches": those return a computer-generated look.

Say how dark a stone or timber is in a plain word ("mid-grey limestone"): the name alone returns its palest form.

More examples, adapted to the actual asset:

- **Timber crate:** "A weathered pine supply crate with dark iron nail heads. The wood is bleached and worn at the edges. A faded black stencil '07' sits on the flat boards of the front. Lots of detail, photorealistic."
- **Wood and steel:** "A counter stool with an oiled dark walnut seat and graphite powder-coated steel legs. The seat is worn smooth and the paint is chipped at the feet. Lots of detail, photorealistic."
- **Dressed stone:** "Medieval masonry in mid-grey limestone blocks with rough chisel marks and chipped edges. The mortar is crumbling, with damp, soot and green algae in the joints. Lots of detail, photorealistic."
- **Painted steel shelving:** "Wall shelving in ivory powder-coated steel. It is dusty on top, scuffed where boxes slide and chipped to bare steel on the front edges. Lots of detail, photorealistic."

Prompt wording guides where finishes appear but is not an exact mask. Use real geometry or material assignments, or supported masks, for exact region control. Exact readable artwork needs a controlled artwork or material route.

## No reference image

Retexture always runs on text alone, with no reference image at all. On the `retexture` command, state that by passing `reference_path: ""`: the empty string means "run without one" and sends no image. Leaving the parameter out would reuse an image picked earlier in the panel. On the staged route, give `run_3d_retexture` no `reference_image_asset_id`. An image passed as a reference can be projected onto the mesh, keep a computer-generated look, or contradict the prompt, and a well-written prompt avoids all three.

Every image becomes words:

- **A photograph of the object or of its material.** Look at it and write what it shows, as plainly as the first section asks: each material, its condition, and any marking with the face it sits on.
- **A render, clay view, drawing or diagram.** It guides the shape during modelling. It says nothing reliable about the surface, so write the look from the brief.
- **A user who asks for an image to be used as the look.** Describe that image in the prompt and say in the handoff that the look was carried as text.

A PBR condition is a different input and keeps its own rule: only a real photograph of the same object and finish may be passed as the supplied condition. Otherwise use the staged route.

## When an image comes first

Use `marso-image` when installed for requested image generation/editing. With only this skill installed, use verified image tools and the following handoff checks. Do not require a new image when a direct material brief already serves the task.

### A user's photo of the object

A supplied photograph of the object counts as a request for a look that follows it. Carry that look in the text prompt ([no reference image](#no-reference-image)). Read the photograph for surface facts only: ignore watermarks, captions, background objects, coloured lighting and reflections, and never describe them as part of the finish. A requested change ("same chair in green velvet") changes the description, never the geometry.

A broad window reflection on dark metal is lighting, not a silver patch, and a cast shadow is not a stain: describe the uninterrupted finish beside it. Keep identifiable surface marks such as a chipped corner or printed lettering in the description.

1. Establish whether each image supplies shape, material regions or appearance. A blank/clay master is a shape guide, not an instruction to retain a synthetic appearance. Fix an implausible master before preserving its silhouette in an edit.
2. Put realism into the image-edit/generation prompt: concrete finish, material-specific fine detail and appropriate imperfections. A better lit source render alone is not that instruction. Keep image layout constraints concise and separate from downstream Retexture prose.
3. Inspect the returned image at its actual size for believable material detail, compatible shape and region placement. Compare source/output dimensions, aspect ratios and object landmarks without stretching either image. A changed canvas is not automatically a changed object, but a plausible finish does not excuse a changed silhouette. Repair the image or explicitly use it only for finish/palette inspiration with independent region checks; do not claim exact correspondence. Do not pass an illustrative, airbrushed or blurry result onward merely because count/layout survived. For grids, read appearance families; use one accepted object crop per mesh.
4. Record the accepted source/crop, actual pixel dimensions, baseline master and material-region intent. Hand Retexture a concise appearance brief, not the full image prompt. A front image does not establish the rear design; use visual region descriptions, coherent views where supported or controlled artwork when exact placement matters.

## Diagnose at the right stage

| Observation | Appropriate next step |
| --- | --- |
| Wrong profile, proportions or construction | Return to the model/reference; do not repair it with texture words. |
| Layout correct but image finish looks synthetic | Correct image art direction and inspect a new bounded pilot; do not expand the set. |
| Image too small or blurred for required detail | Fewer cells, an individual image or a verified higher-resolution route; enlarging pixels does not restore information. |
| Reference good, final material has region bleed, false embossed ink or residual glare | Inspect final PBR maps/bindings and source preparation; correct the diagnosed stage. Do not assume more prompt text or more pixels will solve it. |

## Precise artwork

If a product depends on precise artwork, identify its fixed landmarks before submission: where a stripe starts and ends, which panel carries each label, and where the finish changes. Check the returned unlit colour at those landmarks even when the job succeeds without warnings. Use controlled UV artwork or a decal for exact placement, and preserve accepted lettering and material detail elsewhere.

For an Edit Texture run on an existing look, follow the combined PBR job to completion. For New Texture, or when exact artwork needs an unlit check, choose the conditioned PBR workflow before submission: a batch held at the paint, or the staged route on an earlier add-on. Compare stripe continuity, labels and adjacent controls against the intended design. After a fix, retexture the original again and use the new paint for both the unlit capture and mesh PBR. Honour explicit review holds.

Separate technical checks from visual acceptance. A pilot with correct geometry/UVs but unresolved visible defects is diagnostic; do not scale that method yet. Keep the original quality target, diagnose a correction and test the affected stage within the authorized scope. Do not keep rerunning unchanged requests or quietly lower the viewing standard to make a weak result pass. These internal checks do not add user approval questions for every variant.

## Prompt limit

Read the current operation’s prompt/enhancement limits, including documented downstream constraints. Validate the final expanded reference text and enhancement, not just the draft. Remove repeated adjectives, duplicated context and optional details before compressing essential material regions or source intent; never truncate blindly. Keep UV/export/camera workflow instructions out of Retexture. The limit is far above a good prompt: stay near the two or three sentences above. Preserve the full appearance brief separately and inspect the actual image-to-PBR result.
