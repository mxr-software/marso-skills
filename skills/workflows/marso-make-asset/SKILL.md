---
name: marso-make-asset
description: "Use when asked to make a finished, textured asset in Blender end to end from a brief or an image (game prop, low-poly asset), or when the user names the make-asset workflow."
license: Apache-2.0
---

# Make a finished asset in Blender

Takes a brief or an image to a modelled, unwrapped asset with a Marso appearance and PBR maps. This workflow only orders the skills below. Each skill owns its own rules, checks and completion criterion: load it and follow it for that step. The asset is modelled in Blender: this workflow never starts mesh generation, even when a reference image exists. A detailed or difficult object is still modelled by hand: never load `marso-generate` or run an image-to-mesh command here. Every skill named is required. If one is not installed, name it and stop.

## Inputs

- **Object:** from the request.
- **Image:** when supplied, it sets the shape. The look is carried as text; no image is passed to Retexture.
- **Path:** a named path, budget, platform or use from the request, such as "low-poly" or "mobile". With none, leave the choice to `marso-blender-asset`.
- **Look:** the material, style or wear the request names. With none, a photorealistic look for the object, written as text and recorded as inferred.
- **Approval:** any approval or waiver the request states, passed on word for word.

## Steps

1. `marso-blender-setup`: only when the Marso commands cannot be reached.
2. `marso-blender-reference`: pass the object and the image. Carry forward the chosen reference and the dimensions.
3. `marso-blender-asset`: pass the object, the path signals, the reference and the dimensions. Carry forward the asset root, the path and the review pack.
4. `marso-blender-uv`: pass the asset root. Carry forward the UV report and the review images.
5. `marso-blender-asset` again: pass the UV review images so it can decide whether the asset is finished. Carry forward that status and any remaining defects.
6. `marso-blender-texture`: pass the asset root, the look as text and the approval. Run Retexture, then PBR. Start this step only when step 5 reports the asset finished or partial; otherwise return to the step that owns the defect.

## Stops

1. **Model approval**, owned by `marso-blender-asset`, comes before step 6. With nobody to answer and no approval or waiver in the request, end after step 5 and report the model as awaiting approval.
2. **Look**, before Retexture: state the look in a sentence. When the request names none, offer up to three ideas. With nobody to answer, take the first and record it.
3. **Retexture result**, before PBR: show it. With nobody to answer, continue to PBR and report the result as not reviewed.

## Hand off

Report the file, the path, the review images from each step, the finish status, the look used, and each stop that passed without a review.
