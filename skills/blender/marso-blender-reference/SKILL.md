---
name: marso-blender-reference
description: "Use when finding reference images before modelling a realistic object in Blender, or checking a model's proportions and shape against a reference (side-by-side or overlay comparison)."
license: Apache-2.0
---

# Find references and compare the model with them

## Overview

This skill gives a modelling run a reference set and keeps the model honest against it. It finds side and front images of the object, records the landmark proportions read from them, and measures the model's silhouette against each reference until the shape passes and is believable. It changes no geometry itself and never generates a mesh.

Adjacent work belongs to siblings, each "when installed":

- **Modelling, topology and the review pack:** `marso-blender-asset`. It calls this skill before building and again at each shape checkpoint. Without it, deliver the references, landmarks and comparisons, and say the model was not changed.
- **Generated reference images:** `marso-image`. Without it, a generated reference is unavailable: keep the web references, or record that none was found.

A generated reference starts a Marso image job. Generate one only when the task allows Marso jobs; if it forbids them, use web references or record that none was available. Never start mesh generation or Retexture from this skill.

Run the comparison inside Blender through the working control connection: add this skill's `scripts` folder to `sys.path`, then `import compare_reference`.

- `scripts/compare_reference.py`: `compare`, used for every comparison, and `match_view`, which finds the camera direction of a three-quarter photo.

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| The user supplied a photo or drawing | Use it as the primary reference; [Find the references](#find-the-references) only for a missing view | nothing |
| Realistic object, no reference supplied | [Find the references](#find-the-references) | nothing |
| Web search finds nothing usable | Generate a clean side view with `marso-image` when installed and the task allows Marso jobs | nothing |
| A real product, sizes that matter, or references that disagree | [Record the landmarks](#record-the-landmarks) with the evidence rules | [reference evidence](references/evidence.md) |
| Shape checkpoint during modelling | [Compare the model](#compare-the-model) | nothing |
| The only reference is a three-quarter photo | [Compare the model](#compare-the-model), matching its view first | nothing |
| The model looks wrong but the outline matches | [Review believability](#review-believability) | nothing |
| Stylised or invented object | References for mood only; no comparison gate | nothing |

## Find the references

1. Start from the user's references. A supplied photo is the primary design even when it is one view.
2. Otherwise search the web with the host's search tool for side and front views of comparable objects of the same kind ("cordless drill side view"). Open each candidate image; a search result counts only once you have looked at it.
3. Choose one primary design and keep it. Compare against views that show the whole object uncropped on a plain background: level side or front views, and any three-quarter photo the user supplied. Keep cropped photos for named details. If no level view exists, search again or generate one. Use other designs only for construction you name, never to average silhouettes.
4. Save each chosen image beside the working file (for example `references/side.jpg`) and record its source address and what it shows.
5. If search is unavailable or finds no usable view, generate one with `marso-image` when installed. Ask for the object alone, seen exactly from the side, on a plain light background, with the brief's design features. Generate only when the task allows Marso jobs.
6. A generated reference guides silhouette and proportions only. Take real size from the brief or published dimensions, never from a generated image.

With nobody to answer, choose the primary design yourself and record why.

Done when at least one uncropped reference is saved locally and has been opened, its source is recorded, and the primary design is named. It is a level side or front view, or the user's own photo.

## Record the landmarks

Write down 5 to 8 landmark proportions from the primary reference, as ratios of the object's overall length or height measured on the image. Choose the features that make this design recognisable: handle angle, the position of an opening or button, the height of a shoulder, the length of a nose, leg splay. Note which landmarks the reference cannot show and what was assumed instead.

Positions alone let a model match the outline with members of the wrong thickness. So record two more kinds of ratio in the same list:

- **Section sizes.** For each main part, its thickness or diameter as a ratio of the overall size: a leg at its top and at its foot, a cushion's depth, a rail's height, the widest point of a rounded body.
- **Reach.** For each part that sticks out (a spout, handle, lever, arm or bracket), how far it reaches from its mount, as well as its angle.

For a real product, or when sizes matter or references disagree, read [reference evidence](references/evidence.md) first. It ranks the sources, and adds a dimension ledger and a feature inventory to this record.

Done when the working record lists the landmark, section and reach ratios, and any assumed hidden features.

## Compare the model

Compare once the primary forms are blocked out, after each round that changed the outline, and once more before the review pack. A fix inside the outline (a dial, a vent, a panel step) changes no figure: check it in a clay render against the reference instead. The user's own photo is always one of the references compared, whatever its angle.

1. For a level side, front or top reference, call `compare_reference.compare(root, "references/side.jpg", "renders/compare-side.png", view="right")`. `view` is the side the reference shows (`front`, `back`, `right`, `left` or `top`).
2. For a three-quarter photo, match its camera first, then pass the result on:

   ```python
   found = compare_reference.match_view(root, "references/photo.jpg", near=(-1, -1.3, 0.6), drop_shadow=True)
   result = compare_reference.compare(root, "references/photo.jpg", "renders/compare-photo.png",
                                      view=found["view"], lens=found["lens"], drop_shadow=True)
   ```

   `near` is your estimate of the direction from the object to the camera. The match takes a minute or two, since it tries several lenses. Check that the model panel shows the same faces as the photo; if it does not, correct `near` and match again. Reuse the matched `view` and `lens` in later rounds, and match once more before the final comparison, because the first match was fitted to the blockout. `match_view` takes the same `mirror`, `box`, `ignore` and `drop_shadow` as `compare` and needs a plain background. For a three-quarter photo on a busy background, skip the match: call `compare` with your estimated direction as `view=(x, y, z)` and a `box`, and judge the first two panels by eye.
3. Clean the reference outline before reading any figure, and leave the scene's render settings to the helper. Pass `mirror=True` if the object faces the other way, `drop_shadow=True` when the blue outline includes a cast shadow, and `ignore=[(left, top, right, bottom)]` in reference pixels for a watermark or stand. Pass `drop_shadow` only when the object's colour differs from the background's; it would erase a white or grey object on a white background. A busy background needs `box=(left, top, right, bottom)` in reference pixels and gives no measurement.
4. Open the image. Its panels show the reference, the model in clay, and an overlay: model outline in red, reference outline in blue. Red areas are model the reference lacks; blue areas are reference the model lacks.
5. Read the result. `overlap` is the share of the two silhouettes that coincides. `rows` and `columns` give the filled size of each silhouette at ten stations up the height and along the length. `largest_difference` is the worst station's error, scaled so that 0.05 is the limit. `worst` names the three largest differences in words, such as "at 0.05 of the height the model is narrower by 52% of the reference there".
6. Name the part each entry of `worst` describes: a station near the floor that is too narrow is the legs or feet, one at mid-height the body. Fix the first entry at its source in the model: a part's section, length, position or angle. Then compare again with `overwrite=True`. Do not rescale the whole asset or move the camera to raise the score.
7. The silhouette cannot see inside the outline. Measure each recorded section and reach ratio on the model, and compare interior landmarks (openings, dials, buttons, panels) between the first two panels.

**The gate.** `passed` is true when the overlap is at least 0.85, no station is more than 5% of the overall size out, and no station is more than a quarter thinner or thicker than the reference there. On a level view the outline's edge positions count too. On a matched three-quarter view they depend on the camera, so they are listed in `shifts` and do not count.

**The stop rule.** Each round costs minutes. Stop work on a reference at the first of these:

- `passed` is true.
- On a matched three-quarter view only: `overlap` is at least 0.85, `largest_difference` is at most 0.08, and no entry of `worst` ends "of the reference there". Figures on a matched view vary by about 0.03 between matches of one model, so a further round cannot be told from that variation. When an entry does end that way, fix that station and compare once more first.
- A round fixed the first entry of `worst` and `largest_difference` did not fall.
- Five rounds have run.

A first comparison that fails meets none of these: fix the first entry of `worst` and compare again. Unless `passed` is true, record the last measured result as a remaining mismatch. A landmark changed on purpose, such as a part shrunk to make room for another, is a remaining mismatch, not a fix.

Pass the asset root, not a list of parts: `compare` then records each round on the root as `marso_comparisons`. With `marso-blender-asset` installed, its finish check reads that record and blocks the handoff until a stop condition is met.

When `passed` is None the reference has no plain background: judge the first two panels by eye against the landmark list, and say the comparison was not measured.

Done when a final comparison image exists for each reference view, and the working record gives each one's `overlap`, `largest_difference` and `passed`, with the remaining mismatches or none.

## Review believability

A model can match the outline and still look like a toy. On the final comparison and the clay render, check each of these against the reference:

- **Sections, not slabs.** Real parts taper, round over and change thickness; a constant-thickness extrusion reads as cut-out card.
- **Feature scale.** Openings, guards, buttons and handles are sized like the reference's, not enlarged for readability.
- **Shaped details.** Vents, grooves and cut-outs follow the reference's shape, count and spacing, not generic boxes and slots.
- **Transitions.** Parts blend with the fillets, steps and overlaps the reference shows.

Fix each failing item at its source in the model. Compare again if the fix changed the outline; otherwise check the item in a new clay render.

Done when each item matches the reference on the final images, or the handoff names the item that does not.

## Hand off

Report the reference files with their sources (and which were generated), the primary design, the landmark list and the final comparison images. For each view give the final `overlap`, `largest_difference` and `passed`, and the remaining mismatches. Say which features were inferred rather than seen.

Done when the final message itself, not only a linked report, names every reference, the comparison images and what still differs.

## Worked example: a cordless drill for a game

1. The brief asks for a generic cordless drill, about 230 mm tall. Search for "cordless drill side view" returns product photos; three are opened, and one with a straight side view on white is saved as `references/side.jpg`.
2. Landmarks from the photo: handle at 105° to the motor housing, handle length 0.55 of the height, chuck 0.22 of the length, battery 0.3 of the height, trigger top at 0.62 of the height. Section sizes: handle 0.17 of the height front to back, motor housing diameter 0.3 of the length. Reach: the chuck stands 0.22 of the length beyond the housing.
3. After the blockout, `compare(root, "references/side.jpg", "renders/compare-side.png", view="right", mirror=True)` returns overlap 0.78 and `passed` false. `worst` starts with "at 0.25 of the height the model is narrower by 31% of the reference there": the handle is too thin. Measured on the model, its section is 0.12 against the photo's 0.17.
4. The handle section is fixed in the build script, then its angle and the chuck length as later rounds name them. The fourth comparison returns overlap 0.93, largest difference 0.03 and `passed` true.
5. The believability review finds the vents are plain rectangles where the photo shows angled slots; they are rebuilt and checked in a new clay render. The outline did not change, so the earlier figures stand.
6. The handoff lists the photo and its source, the landmarks, the final `compare-side.png` and the hidden rear battery latch as inferred.

## Common mistakes

- Modelling a realistic object from memory: find and open a reference first.
- Citing a search result without opening it: look at the image before using it.
- Averaging several designs: keep one primary design and borrow named details only.
- Reading proportions off a three-quarter photo by eye: match its view with `match_view` and measure.
- Stopping while `passed` is false, `worst` still names a fixable part and no stop condition is met: fix it and compare again.
- Raising the score by rescaling the asset or shifting the camera: change the part that `worst` names.
- Comparing against a cropped photo: the figures then measure the crop, not the object.
- Judging only the outline overlay: a dial or opening at half the reference's size leaves the silhouette unchanged.
- Taking size from a generated image: size comes from the brief or published dimensions.
- Generating a reference when the task forbids Marso jobs: use web references or record that none was found.
- Comparing once at the end: compare after the blockout, while the large forms are still cheap to change.
- Polishing details while a large mismatch remains: fix the largest mismatch first.
