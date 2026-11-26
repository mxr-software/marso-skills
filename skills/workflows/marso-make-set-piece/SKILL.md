---
name: marso-make-set-piece
description: "Use when asked to make a finished object built from many repeated parts end to end in Blender (market stall, stocked shelf, shop display), or when the user names the make-set-piece workflow."
license: Apache-2.0
---

# Make a finished set piece in Blender

Takes a brief or an image to one assembled object made of many parts: a structure split into its own pieces, and a few masters repeated as instances in several variants. This workflow only orders the skills below. Each skill owns its own rules, checks and completion criterion: load it and follow it for that step. Unlike the other making workflows, this one may start mesh generation, but only for the parts the plan routes there. Every skill named is required. If one is not installed, name it and stop.

## Inputs

- **Set piece:** what it is and what it holds, from the request.
- **Image:** when supplied, it sets the kind of piece, its structure and its mix of parts. Counts, order and exact colours are free unless the request asks for a match. No image is passed to Retexture.
- **Path:** a named path, budget, platform or use from the request, passed to the modelling step.
- **Variants:** the looks the request names. With none, those read from the image or chosen for the brief, recorded as inferred.
- **Approval:** any approval or waiver the request states, passed on word for word.

## Steps

1. `marso-blender-setup`: only when the Marso commands cannot be reached.
2. `marso-blender-reference`: only with an image or a real object to match. Carry forward the chosen reference and the dimensions.
3. `marso-set-piece`: pass the set piece, the reference and the variants. Carry forward the parts list, its job count and a first placement list from the listed sizes.
4. `marso-blender-asset`: pass each part the list routes to modelling, one master for each, with the path signals and the dimensions. Carry forward the modelled masters and the review pack.
5. `marso-generate`: pass every part the list routes to generation together, one mesh for each. Carry forward the generated masters.
6. `marso-blender-uv`: pass each modelled master. Carry forward each UV report.
7. `marso-blender-texture`: pass every master together, with the variants the placement list uses, as text, and the approval. Carry forward one textured object for each variant.
8. `marso-blender-set-piece`: pass the masters, the variants and the parts list. It readies and tags them, and measures each master. Carry forward the real sizes and each master's asset ID and turn.
9. `marso-set-piece` again: pass the real sizes and the asset IDs and turns. Carry forward the placement list, structure included, with each master's asset ID.
10. `marso-blender-set-piece` again: pass the placement list. Carry forward the placed set piece, its report and the renders.

## Stops

1. **Parts list**, before step 4: show the parts by route, the variants of each and the job count. With nobody to answer, continue and record the list as not reviewed.
2. **Model approval**, owned by `marso-blender-asset`, comes before step 7. With nobody to answer and no approval or waiver in the request, end after step 6 and report the masters as awaiting approval.
3. **Variants**, before step 9: show the variants of each part side by side. With nobody to answer, continue and report them as not reviewed.

## Hand off

Report the file, the set piece root, the masters and the variants of each, the instance count for each part, the renders and both list files. Name the masters without an asset ID, each inferred choice, and each stop that passed without a review.
