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

1. Read `set_piece.json`. Pass each part's `features` to whoever makes its master: they say what to build. For each part, make its master by the part's route: `model` and `instance` parts with `marso-blender-asset`, `generate` parts with `marso-generate`, each when installed. Hand all the `generate` parts over together.
2. Build each structural part as its own master to the size the parts list gives: an upright standing, a rail lying along X, a canopy, a table top. Never join them into one object; each gets its own look.
3. Give each master one root: a single mesh, or one Empty or parent with the part's meshes under it.
4. Turn each master so its front faces -Y. For a garment, the front is the chest; for a book, the spine; for a bottle, the label.
5. Scale each generated master so its height matches the part's `size_m`. Generated meshes do not arrive at real size. Scale the object and leave the scale unapplied: editing the mesh makes a later Retexture upload it again as a new mesh.
6. Leave every master's own origin where it is. `place` finds the anchor point from the master's bounds.

Model approval for modelled masters belongs to `marso-blender-asset`; this skill builds nothing on them until that skill reports them approved or waived. A generated master is a Marso result, not new modelling.

Done when each part has one master object, facing -Y and at its listed size.

## Make the variants

Each variant of a part becomes its own object, so a part with four variants has four masters of identical shape.

1. Hand every master and its variants' `look` phrases to `marso-blender-texture` in one group when installed, so it textures them stage by stage. Ask for one object for each variant, each a New Texture made from the untouched original, never from another variant. Hand over each generated master's mesh asset ID with it.
2. A generated master already carries its first variant's look. Make only the others.
3. Make only the variants the placement list's `masters` names. With no placement list yet, get one from `marso-set-piece` when installed; without it, make every variant the parts list names.
4. Tag each result: `place_instances.tag_master(obj, part="tee", variant="red")`. Tag the root when the master is a hierarchy.
5. Note each master's Marso asset ID and asset turn by `part/variant`. The ID is the `pbr_asset_id` in the result of the generation or Retexture job that made it. For a batched Retexture it is in the `pbr` stage outputs that `batch_item` returns. For a staged New Texture it is the PBR asset `marso-blender-texture` records for that variant. For a master taken from the library, the ID is the one it was imported by: `pbr_asset_id` for `import_scene_asset`, or the `asset_id` an `import_assets` result lists, which is the same ID.
6. The asset turn (`asset_yaw_deg`) is how far the asset behind that ID must turn about Z to face -Y. A generated or library master, in its arriving look, takes the turn it was given in [Ready the masters](#ready-the-masters). So does a variant whose Retexture branched from the mesh Marso stores. A mesh that went to Marso from Blender carries its turn, so its turn is 0: a modelled or instanced master, and a variant whose mesh was uploaded. A batch item's `edit` stage gives it as `source_mode`: `branch` or `upload`. A master no Marso job has made has no ID and no turn.
7. Put the variants of one part side by side under one light and look at them. Variants that cannot be told apart at the piece's viewing distance add cost for nothing: report them.
8. Check each variant for texture faults: a bleached or smeared band, a pattern at the wrong scale, colour from one area leaking into another. Make a faulty variant again from the original; do not place it, and drop the ID noted for it.
9. A variant whose Marso run fails twice, or stays unfinished, is not made. Name it as pending with its IDs, and place its slots with another made look of the same part. Never give a master a hand-made Blender material in place of a Marso look.
10. A master found in the project from an earlier run may be reused, with the `pbr_asset_id` and `asset_yaw_deg` the parts list gives it. When the parts list has none, `sim_info` reports the `pbr_asset_id` of a generated or imported master in its arriving look. A variant made as a copy keeps that record, so take its ID from the texture run's record, or name it as having none. Every variant the placement list's `masters` names is still made.

Done when every `part/variant` the placement list's `masters` names has exactly one tagged object, and its asset ID and turn are noted or it is named as having none.

## Place the instances

1. Measure each master's real width, depth and height. Where one differs from its `size_m`, report the real size to `marso-set-piece` when installed, so the slots are worked out from it. Report every master's asset ID and turn with the sizes, so the placement list carries them.
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

Name each master the placement list gives no `pbr_asset_id`: another application cannot import it by ID. Without `marso-set-piece`, list every master's asset ID and turn by `part/variant` in the final message.

Check that Marso has minted every master: run the add-on's `mint_status {asset_ids}` with all their IDs. Marso mints each new asset in the background, giving it real-world scale and physics; another application that imports it before then gets it without them. Check a `minting` asset again every minute, for up to ten minutes, then report it as still minting. Report every other state that is not `minted`, such as `failed` or an error.

Done when the final message gives the counts from `report`, every master's asset ID is in the placement list or the message with its mint state, and it names what is missing.

## Worked example: a clothes rail with twelve T-shirts

1. `set_piece.json` lists two instanced steel parts (`upright`, `foot`), a modelled steel `rail`, and a generated `tee` with `anchor: top` and four variants: white, red, yellow and floral. `marso-set-piece` writes a first placement list from the listed sizes; it uses all four shirts.
2. `marso-blender-asset` models the three steel masters, each on its own: the upright standing 1.6 m, the rail lying 1.5 m along X. Their model approval is waived in the task. They share one steel look.
3. `marso-generate` returns one white T-shirt on a hanger. It arrives 1.9 units tall, so it is scaled to the listed 0.75 m and turned a quarter turn anticlockwise to face -Y. The scale and turn stay on the object; the mesh is not edited.
4. `marso-blender-texture` makes three more objects from the white original, red, yellow and floral, as three New Texture runs sent together. The four stand in a row and read as four different shirts. The white shirt's asset ID is the `pbr_asset_id` from its generation; each other shirt's, and each steel part's, comes from the texture run's record. The white shirt is the stored mesh, so its asset turn is 90. The three variants' `source_mode` is `upload`, so their turn is 0, like the steel parts'.
5. Each master is tagged: `tag_master(obj, "tee", "white")` and so on, and the steel parts as `upright`, `rail` and `foot`.
6. The masters are measured, and their sizes go to `marso-set-piece` with the seven asset IDs and turns. It writes the placement list again: two uprights, two feet, one rail at 1.57 m, and a `row` of twelve shirts along the rail's own ends with `facing: along`, each master with its ID.
7. `place_instances.place(".../placements.json")` returns `passed: True`, `instances: 17`, and three of each shirt. The close render shows the hooks hanging clear below the tube.
8. The row used the tube's centre height. A hook passes over the tube, whose top is 15 mm higher. The slot is corrected, the list rewritten and `place` run again. The hooks now sit on the rail.
9. The handoff gives the counts, the two renders and both files. No master lacks an ID.

## Common mistakes

- Generating or modelling one mesh for each instance: make one master for each part and place linked duplicates.
- Retexturing a placed instance: make the variant on a master, then place.
- Making a variant from another variant: branch every variant from the untouched original.
- Leaving a generated master at its imported size: scale it to the part's `size_m`.
- Placing before the masters face -Y: turn each master first, or every row points the wrong way.
- Nudging instances by hand after placing: fix the slot and run `place` again.
- Joining the frame, canopy and table into one object: keep each structural part its own master with its own look.
- Handing on an asset ID without its turn: a generated shirt turned in Blender faces another way in its stored asset, so report `asset_yaw_deg` with every ID.
