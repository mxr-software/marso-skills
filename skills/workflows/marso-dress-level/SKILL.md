---
name: marso-dress-level
description: "Use when asked to dress an Unreal level from the Marso library end to end (Marso Unreal plugin, closed beta), brief or blockouts to lit stills, or when the user names the dress-level workflow."
license: Apache-2.0
---

# Dress an Unreal level from the library

Takes a brief or a blocked-out Unreal level to a dressed, lit level with stills, using only assets already in the Marso library. Nothing is generated or modelled: an item the library lacks stays a blockout and is reported, to be made in Blender. This workflow only orders the skills below. Each skill owns its own rules, checks and completion criterion: load it and follow it for that step. Every skill named is required. If one is not installed, name it and stop.

## Inputs

- **Level:** the Unreal level the user names, or a new one.
- **Brief:** what the space is and what it holds, from the request. A level already blocked out needs no brief beyond its blockouts.
- **Style:** words for the whole space ("rustic kitchen"), from the request or inferred and recorded.
- **Shots:** the stills the request asks for; with none named, a wide shot and closer views of the main pieces.
- **Approval:** any approval or waiver the request states, passed on word for word.

## Steps

1. `marso-unreal-setup`: only when the Marso Unreal plugin's tools cannot be reached.
2. `marso-unreal-level`: pass the level. Carry forward the open level.
3. `marso-unreal-blockout`: with a brief and no blockouts, pass the brief to lay them out. Then pass the blockouts, the style and the approval to match and swap. Carry forward the swapped assets, the blockouts left unfilled or unnamed, and any download still waiting.
4. `marso-unreal-library`: pass only the items the request names that no blockout stands for. Carry forward the actors placed.
5. `marso-unreal-stage`: pass the dressed level, the shots and the approval. Carry forward the lighting chosen, each render and its camera.
6. `marso-unreal-level` again: pass the level to save. Carry forward the saved level.

## Stops

1. **Marso Unreal plugin**, at step 1: without it, `marso-unreal-setup` says it is in closed beta, and the workflow stops. It is never installed.
2. **Layout and choices**, owned by `marso-unreal-blockout`: the blockout layout and the swap choices are shown before swapping.
3. **Dressed level**, before step 5: show a screenshot of the dressed level. With nobody to answer, continue and record it as not reviewed.

## Hand off

Report the saved level, each swap with its asset and size difference, the items placed, the lighting chosen and each render. Name the blockouts left unfilled (to be made in Blender) or unnamed, downloads still waiting, items not found, each inferred choice, and each stop that passed without a review.
