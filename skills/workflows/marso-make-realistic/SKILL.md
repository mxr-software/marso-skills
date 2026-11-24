---
name: marso-make-realistic
description: "Use when asked to make an existing asset in the Blender scene look realistic end to end (check UVs, propose looks, Retexture, add PBR), or when the user names the make-realistic workflow."
license: Apache-2.0
---

# Make an existing Blender asset look realistic

Takes an asset already in the scene to a realistic Marso appearance with PBR maps. The geometry stays as it is. This workflow only orders the skills below. Each skill owns its own rules, checks and completion criterion: load it and follow it for that step. Every skill named is required. If one is not installed, name it and stop.

## Inputs

- **Asset:** the one the request names, else the selection, else the only asset in the scene. With several and nobody to answer, take the largest and record the choice.
- **Look:** the material, age or wear the request names, written as text. With none, see the Look stop.
- **Keep:** anything the request says to preserve, such as existing colours or labels.

## Steps

1. `marso-blender-setup`: only when the Marso commands cannot be reached.
2. `marso-blender-uv`: pass the asset to check, and repair what fails. Carry forward the UV report and the review images.
3. `marso-blender-texture`: pass the asset, the look and what to keep. Run Retexture, then PBR.

## Stops

1. **Shape defects:** this workflow never remodels. Report any defect a step finds and continue; `marso-blender-asset` owns the repair as separate work.
2. **Look**, before Retexture: offer three photorealistic looks that suit the object, each naming its materials and their condition. With nobody to answer, take the first and record it.
3. **Retexture result**, before PBR: show it beside the starting asset. With nobody to answer, continue to PBR and report the result as not reviewed.

## Hand off

Report the file, the asset, what the UV step changed, the look used, the review images, and each stop that passed without a review.
