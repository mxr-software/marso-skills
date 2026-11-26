---
name: marso-unreal-set-piece
description: "Use when placing a planned set piece in an Unreal level (Marso Unreal plugin, closed beta) from its placement list, moving or rearranging one already placed, or checking it against its list."
license: Apache-2.0
---

# Place a set piece in Unreal

## Overview

This skill places a set piece planned with `marso-set-piece` into an Unreal level. It imports each master once by its Marso asset ID, adds each further variant as a look of that mesh when Marso merges it, and places one actor per instance from the placement list, all in one Outliner folder. It converts the plan's frame to Unreal's with `scripts/to_unreal.py`, so the piece reads the same as in Blender and is never mirrored.

It keeps the plan as it is: positions come from the placement list and the script, never typed by hand. It makes nothing: masters are made in Blender and reach Unreal through the Marso library. It changes only its own actors: those in the plan's folder whose labels start with the plan's prefix.

- The placement list and its asset IDs come from `marso-set-piece`, with each master's ID and turn recorded by `marso-blender-set-piece`, each when installed. Without them, this skill needs a placement list from elsewhere that gives every master a `pbr_asset_id` and `asset_yaw_deg`.
- A master with no `pbr_asset_id` is not in the library yet. Name the missing masters, route them to `marso-blender-set-piece` when installed (it makes and records them), and place nothing until the list is complete. Place the rest only when the user asks for a partial piece; with nobody to answer, place nothing.
- A library stand-in for a missing master needs the user's choice of asset and of its turn, recorded in the parts list through `marso-set-piece` when installed. With nobody to answer, use none.

The Marso Unreal plugin is in closed beta, by invitation. If no Marso Unreal plugin answers, say so and stop the Unreal step; connection problems belong to `marso-unreal-setup` when installed.

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| Place a planned set piece | [Import the masters](#import-the-masters), [Measure the meshes](#measure-the-meshes), [Place the actors](#place-the-actors) | nothing |
| Put it at a spot, or turn it | `to_unreal.py plan` with `--at X Y Z` and `--yaw`, then [Place the actors](#place-the-actors) | nothing |
| The placement list changed (new seed, slots, sizes) | Run `plan` again with `--force`, then [Place the actors](#place-the-actors): actors move, none duplicate | nothing |
| Is the placed piece still right? | [Check](#check) | nothing |
| A master with no asset ID | Route it back as in the Overview | nothing |

## Before placing

Through the Marso Unreal plugin's MCP tools, call `marso_state` first. Find a command with `marso_search` and read its schema with `marso_describe`, then run it with `marso_run`. A command that returns `job_id` runs in the background: wait with `marso_wait`, at most 50 seconds a call, and never resubmit on a timeout.

1. If `editor.pie_running` is true, ask the user to stop Play In Editor before placing; with nobody to answer, place nothing and report it.
2. Read `placements.json`. It must state `units` `m`, `up` `Z`, `front` `-Y` and `handedness` `right`; the script refuses a list that states another frame or none. An older list without `handedness` is written again with `marso-set-piece`.
3. List the masters (each `part/variant`) with their `pbr_asset_id` and `asset_yaw_deg`. If any has no ID, follow the Overview before going on.

Done when every master has an asset ID and a turn, and the level is not in play.

## Import the masters

A part's variants share one mesh when Marso merges them: the first variant brings the mesh, and each further one arrives as a look of it.

1. For each part, run `import_assets {asset_ids: [<first variant's ID>], spawn: false, keep_parts: false}` (a job), so a master made of several parts arrives as one mesh. Record the mesh's content path.
2. If the import says the asset is not in the open project, run `sync_projects`, open the asset's project with `open_project {project_id}` (from its `asset_card`) and import again.
3. Import each further variant the same way. The result should say `added_as_look` and name the `look`. Record that look name for the variant.
4. A variant that arrives as its own mesh did not merge: its geometry differs, or Project Settings > Plugins > Marso > **Merge retextures into looks** is off. Use its own mesh, with the look "Original", and report that it did not merge.
5. An import with `minted` false came in before Marso minted it, without real-world scale or physics, and the editor does not refresh it by itself. Check `mint_status {asset_ids}` every minute, for up to ten minutes. When it says `minted`, rebuild the mesh in place with `import_assets {asset_ids, spawn: false, keep_parts: false, reimport: true}`, then measure. If it says `failed` or `not_minted`, or is still minting, use the mesh as imported and report it: the plan's `size_m` still sizes it, but it has no physics. If it is minted later, rebuild it the same way and place the piece again from a fresh `meshes.json`.

Done when every `part/variant` of the masters has a content path and a look name.

## Measure the meshes

The script needs each mesh's own bounds, because an imported mesh's pivot sits at its base but not always at its centre.

1. For each mesh (once, not per variant), run `model_info {asset_path}`. Its `bounds` give `min` and `max` in metres, in the mesh's own frame.
2. If `model_info` fails for a mesh, place a probe instead: `spawn_static_mesh {asset_path, name: "<prefix>probe", location: [0, 0, 0]}` with no turn and scale 1, read `get_actor {actor, bbox: true}`, then delete the probe.
3. Write `meshes.json` beside the placement list, one entry for each `part/variant`:

```json
{"tee/red": {"asset_path": "/Game/Marso/.../SM_Tee", "look": "Red", "bounds_m": {"min": [-0.29, -0.04, 0.0], "max": [0.33, 0.06, 0.98]}}}
```

Done when `meshes.json` has an entry for every master and no probe actor is left.

## Place the actors

1. Run `python "<skill>/scripts/to_unreal.py" plan placements.json --meshes meshes.json --out unreal_placements.json`, where `<skill>` is this skill's folder. Add `--at X Y Z` and `--yaw` (Unreal's frame, metres and degrees) to put the piece at a spot the user names. Fix every problem it lists. Its output names the plan's `folder` and label `prefix`.
2. `list_actors {folder: <folder>, limit: 5000}` lists the actors an earlier run placed. If `truncated` is true, raise `limit` until it is false.
3. For each row of `unreal_placements.json`:
   - if an actor with that label exists and shows the row's mesh (`asset_path`), move it: `set_transform {actor, location, rotation_deg, scale}`;
   - if it exists with another mesh (its variant moved to a mesh of its own), delete it and place it again;
   - otherwise place it: `spawn_static_mesh {asset_path, name: <label>, location, rotation_deg, scale, folder}`.
4. Delete the actors in exactly that folder whose labels start with the prefix but are no longer in the plan: they are this skill's own, from an earlier arrangement. Leave every other actor alone.
5. Set the looks: `set_look {look, actors: [...]}`, one call for each look, "Original" included.
6. Save the level as the task asks (see `marso-unreal-level` when installed); otherwise report it as unsaved.

Done when every row has exactly one actor, and `list_looks {actor}` on one actor of each look gives that look as `actor_look`.

## Check

1. Save the `list_actors {folder, limit: 5000}` result as `actors.json` and run `python "<skill>/scripts/to_unreal.py" check unreal_placements.json --actors actors.json`. `passed` must be true; fix each problem it lists by placing again.
2. Look at it: `frame {actors}` on the piece, then `viewport_screenshot`. Hanging parts hang from their rail, standing parts sit on their surface, and nothing faces the wrong way.
3. If a part faces the wrong way in every instance, its `asset_yaw_deg` is wrong: correct it in the parts list through `marso-set-piece` when installed, and run `plan` again. Without it, report the part and the turn it needs. Never turn single actors by hand.

Done when `check` reports `passed` and the screenshot has been opened.

## Report

Report the folder, the actor count for each master and look, and the meshes imported (one per part where variants merged). Name any variant that did not merge, unminted masters, and masters left out and why. List the files written (`meshes.json`, `unreal_placements.json`) and say whether the level was saved.

Done when the final message holds each item above.

## Worked example: a clothes rail made in Blender

1. `placements.json` from `marso-set-piece` lists 17 instances: two uprights, two feet, a rail and twelve T-shirts in four variants. Every master has a `pbr_asset_id`; the shirts have `asset_yaw_deg` 90, the steel parts 0.
2. `import_assets` brings the white shirt's mesh. Its red, yellow and floral variants return `added_as_look` with the looks `Red`, `Yellow` and `Floral`. The steel parts import as three meshes.
3. `model_info` on the shirt mesh gives bounds from `[-0.29, -0.04, 0]` to `[0.33, 0.06, 0.98]`. `meshes.json` gets seven entries, the four shirts on one mesh.
4. `to_unreal.py plan ... --at 4 0 0` writes 17 rows in `Set pieces/Clothes rail` with the prefix `Clothes_rail_`. Nothing is there yet, so 17 `spawn_static_mesh` calls place them; four `set_look` calls set the shirts' looks.
5. `check` reports `passed`. The screenshot shows the hooks over the rail and every shirt facing along it, as in the Blender render.
6. The user changes the seed. `marso-set-piece` writes a new placement list; `plan ... --force` and 17 `set_transform` calls move the same actors, and new `set_look` calls follow the reshuffled variants. No actor is added.

## Common mistakes

- Typing Blender positions into Unreal: that mirrors the piece; convert with `to_unreal.py`.
- Importing a mesh for every variant or instance: one mesh per part where variants merge, one actor per instance.
- Placing with the pivot as the anchor: measure each mesh's bounds first; pivots are not always centred.
- Adding actors on a rerun: move the actors with the plan's labels, and delete only the plan's own that it dropped.
- Moving an actor whose variant changed mesh: delete it and place it again.
- Turning single actors to fix a facing: correct `asset_yaw_deg` and plan again.
- Placing a partial piece without being asked: name the missing masters and place nothing.
