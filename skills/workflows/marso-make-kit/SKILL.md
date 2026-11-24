---
name: marso-make-kit
description: "Use when asked to make a finished, textured modular kit in Blender end to end from a brief or an image (walls, crates, pipes, shelving), or when the user names the make-kit workflow."
license: Apache-2.0
---

# Make a finished modular kit in Blender

Takes a brief or an image to a kit of reusable parts that share one Marso appearance and carry PBR maps. This workflow only orders the skills below. Each skill owns its own rules, checks and completion criterion: load it and follow it for that step. The parts are modelled in Blender: this workflow never starts mesh generation, even when a reference image exists. A detailed or difficult object is still modelled by hand: never load `marso-generate` or run an image-to-mesh command here. Every skill named is required. If one is not installed, name it and stop.

## Inputs

- **Kit:** what it builds and the parts the request names. With none named, leave the part list to `marso-blender-kit`.
- **Image:** when supplied, it sets the shape and the parts to find in it. The look is carried as text; no image is passed to Retexture.
- **Path:** a named path, budget, platform or use from the request. With none, leave the choice to `marso-blender-kit`.
- **Look:** one appearance for the whole kit, from the request. With none, a photorealistic look for the material, written as text and recorded as inferred.
- **Approval:** any approval or waiver the request states, passed on word for word.

## Steps

1. `marso-blender-setup`: only when the Marso commands cannot be reached.
2. `marso-blender-reference`: only with an image or a real object to match. Carry forward the chosen reference and the dimensions.
3. `marso-blender-kit`: pass the kit, the path signals, the reference and the dimensions. Carry forward the masters, the kit contract and the previews.
4. `marso-blender-uv`: pass each master. Carry forward each UV report and its review images.
5. `marso-blender-texture`: pass every master as one group, with the look as text and the approval. Run Retexture on each part from that one look, then PBR.

## Stops

1. **Model approval**, owned by `marso-blender-kit`, comes before step 5. With nobody to answer and no approval or waiver in the request, end after step 4 and report the kit as awaiting approval.
2. **Look**, before Retexture: state the one look for the kit in a sentence. When the request names none, offer up to three ideas. With nobody to answer, take the first and record it.
3. **Retexture result**, before PBR: show the parts side by side. With nobody to answer, continue to PBR and report the result as not reviewed.

## Hand off

Report the file, the masters and what each is for, the review images from each step, the look used, and each stop that passed without a review.
