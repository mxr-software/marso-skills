---
name: marso-blender-set-piece
description: "Use when assembling a planned set piece in Blender: preparing its masters and variants, placing its instances from a placement list, or checking a placed set piece against its list."
license: Apache-2.0
---

# Assemble a set piece in Blender

## Overview

This skill turns a set piece's plan into a Blender scene. It takes the parts list and placement list, readies one master object for each part and variant, and places every instance as a linked duplicate. The result is the assembled piece under one root, with its masters kept in the file for reuse.

It preserves each master's geometry, UVs and materials: an instance shares its master's data and is never edited on its own. It writes no plan, models nothing, generates nothing and starts no Marso job itself.

Adjacent work belongs to siblings, each "when installed":

- **The parts list and placement list:** `marso-set-piece`. Without it, this skill needs a placement list from elsewhere, and reports that none was planned here.
- **Modelled masters:** `marso-blender-asset`, which also owns model approval. Without it, report the masters still to model.
- **Generated masters:** `marso-generate`. Without it, report the generated parts as not made.
- **UVs and variants:** `marso-blender-uv` and `marso-blender-texture`. Without them, place the untextured masters and list the variants not made.

Run the script inside Blender through the working control connection: add this skill's `scripts` folder to `sys.path`, then `import place_instances`.

- `scripts/place_instances.py`: `tag_master`, `place` and `check`.

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| A parts list exists; nothing is built | [Ready the masters](#ready-the-masters) | nothing |
| Masters exist in one look each | [Make the variants](#make-the-variants) | nothing |
| Masters and variants exist | [Place the instances](#place-the-instances) | nothing |
| The piece is placed and needs checking, or was edited by hand | `place_instances.check(placements_path)` | nothing |
| A different arrangement of the same parts | Change the slots or the seed, write a new placement list, and run `place` again | nothing |
| No parts list yet | Plan first with `marso-set-piece` when installed | nothing |

## Ready the masters

One master object stands for each part. Build them apart from where the piece will stand, such as in a row beside it, so nothing overlaps.

1. Read `set_piece.json`. Pass each part's `features` to whoever makes its master: they say what to build. For each part, make its master by the part's route: `model` and `instance` parts with `marso-blender-asset`, `generate` parts with `marso-generate`, each when installed.
2. Build each structural part as its own master to the size the parts list gives: an upright standing, a rail lying along X, a canopy, a table top. Never join them into one object; each gets its own look.
3. Give each master one root: a single mesh, or one Empty or parent with the part's meshes under it.
4. Turn each master so its front faces -Y. For a garment, the front is the chest; for a book, the spine; for a bottle, the label.
5. Scale each generated master so its height matches the part's `size_m`. Generated meshes do not arrive at real size. Scale the object and leave the scale unapplied: editing the mesh makes a later Retexture upload it again as a new mesh.
6. Leave every master's own origin where it is. `place` finds the anchor point from the master's bounds.

Model approval for modelled masters belongs to `marso-blender-asset`; this skill builds nothing on them until that skill reports them approved or waived. A generated master is a Marso result, not new modelling.

Done when each part has one master object, facing -Y and at its listed size.

## Make the variants

Each variant of a part becomes its own object, so a part with four variants has four masters of identical shape.

1. Hand each master and its variants' `look` phrases to `marso-blender-texture` when installed. Ask for one object for each variant, each made from the untouched original, never from another variant.
2. A generated master already carries its first variant's look. Make only the others.
3. Skip any variant the placement list's `notes` name as unused.
4. Tag each result: `place_instances.tag_master(obj, part="tee", variant="red")`. Tag the root when the master is a hierarchy.
5. Put the variants of one part side by side under one light and look at them. Variants that cannot be told apart at the piece's viewing distance add cost for nothing: report them.
6. Check each variant for texture faults: a bleached or smeared band, a pattern at the wrong scale, colour from one area leaking into another. Make a faulty variant again from the original; do not place it.
7. A master found in the project from an earlier run may be reused, but the variants the parts list names are still all made.

Done when every `part/variant` the placement list's `masters` names has exactly one tagged object.

## Place the instances

1. Measure each master's real width, depth and height. Where one differs from its `size_m`, report the real size to `marso-set-piece` when installed, so the slots are worked out from it.
2. Get the placement list from that skill. The structure's pieces are in it too: nothing is positioned by hand.
3. A hanger's hook passes over its rail, so a hanging row belongs at the top of the tube, not its underside.
4. Call `report = place_instances.place("<path>/placements.json")`.
5. Read the report. `passed` must be true; `instances` must equal `expected`; `per_master` gives the count for each part and variant.
6. Render one overview and one close view. Check that hanging parts hang from their rail, standing parts sit on their surface, and nothing floats or sinks.
7. If a row sits off its rail, the slot was measured wrongly. Correct the slot, write the placement list again and run `place` again; it replaces the instances it made before.

`place` raises an error and changes nothing when a master is missing. It makes instances under one Empty named `<set piece> instances`, in a collection of the same name, and hides the masters from the render and from the view layer. The masters stay enabled, so the file still checks after it is reopened. Pass `masters={"tee/red": "Object name"}` to name a master without tagging it, `root_name` to choose the Empty, and `hide_masters=False` to keep the masters visible.

Move or turn the whole piece by its root Empty. Never move single instances by hand: change the slot and place again, so the list and the scene stay equal.

Done when `report["passed"]` is true and both renders have been opened.

## Hand off

Save the file with the masters still in it. Report the set piece root, the instance count for each part and variant, the number of unique masters, the two renders, and the paths of `set_piece.json` and `placements.json`. Name any variant not made and any part left untextured.

Done when the final message gives the counts from `report` and names what is missing.

## Worked example: a clothes rail with twelve T-shirts

1. `set_piece.json` lists three instanced steel parts (`upright`, `rail`, `foot`) and a generated `tee` with `anchor: top` and four variants: white, red, yellow and floral.
2. `marso-blender-asset` models the three steel masters, each on its own: the upright standing 1.6 m, the rail lying 1.5 m along X. Their model approval is waived in the task. They share one steel look.
3. `marso-generate` returns one white T-shirt on a hanger. It arrives 1.9 units tall, so it is scaled to the listed 0.75 m and turned to face -Y. The scale stays on the object; the mesh is not edited.
4. `marso-blender-texture` makes three more objects from the white original: red, yellow and floral. The four stand in a row and read as four different shirts.
5. Each master is tagged: `tag_master(obj, "tee", "white")` and so on, and the steel parts as `upright`, `rail` and `foot`.
6. `marso-set-piece` writes the placement list: two uprights, two feet, one rail at 1.57 m, and a `row` of twelve shirts along the rail's own ends with `facing: along`.
7. `place_instances.place(".../placements.json")` returns `passed: True`, `instances: 17`, and three of each shirt. The close render shows the hooks hanging clear below the tube.
8. The row used the tube's centre height. A hook passes over the tube, whose top is 15 mm higher. The slot is corrected, the list rewritten and `place` run again. The hooks now sit on the rail.
9. The handoff gives the counts, the two renders and both files.

## Common mistakes

- Generating or modelling one mesh for each instance: make one master for each part and place linked duplicates.
- Retexturing a placed instance: make the variant on a master, then place.
- Making a variant from another variant: branch every variant from the untouched original.
- Leaving a generated master at its imported size: scale it to the part's `size_m`.
- Placing before the masters face -Y: turn each master first, or every row points the wrong way.
- Nudging instances by hand after placing: fix the slot and run `place` again.
- Joining the frame, canopy and table into one object: keep each structural part its own master with its own look.
- Deleting the masters after placing: keep them; the instances share their data.
