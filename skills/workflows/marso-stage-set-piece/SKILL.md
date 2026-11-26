---
name: marso-stage-set-piece
description: "Use when asked to make a set piece (market stall, stocked shelf) in Blender and stage it in an Unreal level (Marso Unreal plugin, closed beta), or when the user names the stage-set-piece workflow."
license: Apache-2.0
---

# Make a set piece in Blender and stage it in Unreal

Takes a brief or an image to one set piece made in Blender, then placed, lit and shot in an Unreal level. The two applications share only the Marso library and the placement list: nothing else passes between them. This workflow only orders the skills below. Each skill owns its own rules, checks and completion criterion: load it and follow it for that step. Every skill named is required. If one is not installed, name it and stop.

## Inputs

- **Set piece:** what it is and what it holds, from the request.
- **Image:** when supplied, passed to the making workflow as its reference.
- **Variants:** the looks the request names, or those the making workflow infers.
- **Level:** the Unreal level the user names, or a new one, and where in it the piece stands.
- **Shots:** the stills the request asks for; with none named, a wide shot and a closer view.
- **Path:** a named path, budget, platform or use from the request, passed to the making workflow.
- **Approval:** any approval or waiver the request states, passed on word for word.
- **Applications:** Blender with the Marso add-on, and Unreal Engine with the Marso Unreal plugin (closed beta), both connected.

## Steps

1. `marso-blender-setup`: only when the Marso commands in Blender cannot be reached.
2. `marso-unreal-setup`: only when the Marso Unreal plugin's tools cannot be reached.
3. `marso-make-set-piece`: pass the set piece, the image, the path, the variants and the approval. Carry forward the parts list, the placement list with each master's asset ID and turn, and the Blender renders.
4. `marso-unreal-level`: pass the level and the spot the request names. Carry forward the open level and the spot for the piece.
5. `marso-unreal-set-piece`: pass the placement list and the spot. Carry forward the placed piece, its folder, its check and any master left out.
6. `marso-unreal-stage`: pass the placed piece and the shots. Carry forward each render and its camera.
7. `marso-unreal-level` again: pass the level to save. Carry forward the saved level.

## Stops

1. **Applications**, at step 1 and step 2: with Blender or the Marso Unreal plugin missing, its setup skill says what is needed, and the workflow stops there. The Marso Unreal plugin is in closed beta and is never installed.
2. **Parts list, model approval and variants**, owned by `marso-make-set-piece` and the skills it orders, come before step 4. If that workflow ends early with nobody to answer, end there and report what it reports.
3. **Masters without an asset ID**, owned by `marso-unreal-set-piece`: it places nothing partial unless the request asks. With nobody to answer, end after step 5 and report the masters to make.
4. **Placed piece**, before step 6: show its screenshot beside the Blender render. With nobody to answer, continue and record it as not reviewed.

## Hand off

Report the Blender file, both list files, the Unreal level and the piece's folder, the actor count for each master, the lighting chosen, and each render from both applications. Name the masters left out or not minted, each inferred choice, and each stop that passed without a review.
