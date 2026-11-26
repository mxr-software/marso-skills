---
name: marso-unreal-blockout
description: "Use when greyboxing an Unreal level with blockouts (Marso Unreal plugin, closed beta), swapping blockouts for Marso library assets, or suggesting library assets that suit a level."
license: Apache-2.0
---

# Block out a level and fill it from the library

## Overview

This skill lays out an Unreal level with Marso blockouts: grey boxes with a description and a real-world size that stand for assets not chosen yet. It then swaps each blockout for a Marso library asset, and it can suggest library assets that suit a level the user is building. Searching and swapping spend no credits.

It keeps the user's choices: an asset replaces a box at its real size unless the user asks for the boxes' sizes, and a box with no good match stays as it is and is reported. It replaces only blockouts and adds only what the user approves or the task asks for. It makes nothing new: an asset the library lacks is made in Blender (`marso-generate` or `marso-blender-asset`, when installed).

Moving, grouping and saving follow `marso-unreal-level`, placing a picked asset follows `marso-unreal-library`, and lighting and stills follow `marso-unreal-stage`, each when installed. Without the level skill, save the level when the task asks and otherwise report it unsaved; without the library skill, list the picks for the user.

The Marso Unreal plugin is in closed beta, by invitation. If no Marso Unreal plugin answers, say so and stop the Unreal step; connection problems belong to `marso-unreal-setup` when installed.

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| Greybox a level from a brief ("a small workshop") | [Lay out blockouts](#lay-out-blockouts), then [Match and swap](#match-and-swap) | nothing |
| Swap the boxes in a blocked-out level for real assets | [Match and swap](#match-and-swap) | nothing |
| Fit each asset inside its box | `replace_blockouts` with `fit_to_box: true` | nothing |
| A box whose label says nothing (Cube, StaticMeshActor_3) | Give it words, as in [Match and swap](#match-and-swap) step 3 | nothing |
| What in my library suits this level? | [Suggest assets](#suggest-assets) | nothing |

## Before any change

Through the Marso Unreal plugin's MCP tools, call `marso_state` first. Find a command with `marso_search` and read its schema with `marso_describe`, then run it with `marso_run`. A command that returns `job_id` runs in the background: wait with `marso_wait`, at most 50 seconds a call, and never resubmit on a timeout.

If `editor.pie_running` is true, ask the user to stop Play In Editor before any change; with nobody to answer, change nothing and report it. Work in metres and degrees, in Unreal's frame (X forward, Y right, Z up); `rotation_deg` is `[x roll, y pitch, z yaw]`.

Done when the open level and the Play In Editor state are known.

## Lay out blockouts

1. From the brief, list the items the space needs. Give each a description that says what it is and what it is made of ("a worn oak workbench"), a real-world size `[width, depth, height]` in metres, a place and a turn.
2. Place each one: `add_blockout {description, size_m, location, rotation_deg, label}`. `location` is the middle of its base. Give it a label that names it (`Workbench_01`).
3. Group the blockouts in one Outliner folder with `set_folder {actors, folder}`, such as `Blockout/Workshop`.
4. Check the layout with `viewport_screenshot`: blockouts show in the editor view. Nothing overlaps that should not, and every box stands on the floor or the surface it belongs on.
5. Show the layout before swapping. With nobody to answer, continue and record it as not reviewed.

Done when every planned item has a labelled blockout with its description and size, and the screenshot has been opened.

## Match and swap

1. List the blockouts: Marso blockouts show in `list_actors` with the class `MarsoPlaceholder`. Plain boxes the user made count too, when the user names them.
2. Run `find_blockout_matches {actors, scene}`, naming every blockout; with no actors named it reads only the selection. `scene` describes the whole space ("rustic kitchen"). For each blockout it returns its `words`, its box (`size_m`, `base_m`, `yaw_deg`) and its `candidates`, best first: each with `source` (`project` or `library`), `name`, `asset_id` or `asset_path`, `size_m` where known, `name_score` and `size_match`.
3. A blockout with `needs_words` has a label that says nothing. Ask the user what it is, or take it from the brief, and run `find_blockout_matches` again with `words {<label>: "what it is"}`. With nobody to answer and nothing in the brief, leave it and list it as unnamed.
4. For a blockout with no good candidate, run `find_in_library {query}` with its words and the scene. Its results add a `verdict` (`match`, `possible` or `weak`) and a `pbr_asset_id`, which `replace_blockouts` takes as `asset_id`. The plugin remembers only the latest search's results, so swap a blockout chosen from a search before the next search, or open the asset's project first with `open_project {project_id}` (from the result's `project_ids`).
5. Choose for each blockout the candidate whose name says what the box is, with the closest size. Compare with the box's own `size_m` from step 2; an actor's bounds can include more than the box. Leave a blockout whose candidates are all something else, and list it as unfilled.
6. Show the choices before swapping: each blockout, its asset, and the size difference in each dimension where the asset's size is known. With nobody to answer, swap the choices and record them as inferred.
7. Swap: `replace_blockouts {replacements: [{actor, asset_id}], fit_to_box}`, with `asset_path` in place of `asset_id` for an asset already in the project. Each asset stands on the middle of the box's base, turned as the box was (a quarter turn more when its footprint runs the other way), in the box's Outliner folder, at its real size. `fit_to_box` instead scales each asset evenly to fit inside its box, keeping its proportions; set it only when the user asks for the boxes' sizes.
8. Read the result:
   - `replaced` lists each new actor (`new_actor`, its label, which is the asset's name; `actor_path`; `asset_path`; `scale`).
   - `waiting` lists assets still downloading behind a placeholder. An entry with `job_id`: wait with `marso_wait`. One with `queue_id` starts after the downloads before it: find its job in `marso_jobs`, then wait for it.
   - `failed` gives each failure's `error`.
9. Check with `list_actors` that every swapped blockout and placeholder is gone, and look with `viewport_screenshot`. `replace_blockouts` selects what it places; say so. Name every asset more than a quarter larger or smaller than its box in any dimension, comparing width with depth when it was turned a quarter.
10. Save the level when the task asks; otherwise report it as unsaved.

Done when every blockout is swapped, still waiting with its job or queue entry named, or listed as unfilled or unnamed with the reason.

## Suggest assets

1. Read the level: `list_actors` for what is in it, `list_marso_assets {scope: "level"}` for its Marso assets, and `asset_card` on a few of them for their categories and materials. Save a `viewport_screenshot` with `name` and keep its `file_path`.
2. Put the setting and style in words ("rustic farmhouse kitchen").
3. Search with `find_in_library {query, image_path}`, giving those words and the screenshot, then a few searches for what the level lacks:
   - completing the set: what usually goes with what is there (chairs for a table, utensils by a counter);
   - the same materials: assets that share the materials already in use;
   - empty places: props for bare surfaces and corners.
4. Show the suggestions in those groups, with each result's `name`, `verdict` and `thumbnail_path`. Leave out `weak` results. Place nothing until the user picks.
5. With nobody to answer, place nothing: deliver the suggestions.
6. Place what the user picks with `marso-unreal-library` when installed; without it, list the picks with their `pbr_asset_id` for the user.

Done when the suggestions are delivered in groups, and anything the user picked is placed or listed.

## Report

Report each blockout added with its description and size, and each swap with the asset, its new actor, its size difference and whether it was inferred. Name every blockout left unfilled or unnamed, every asset still waiting, the suggestions made, and whether the level was saved.

Done when the final message holds each item above.

## Worked example: a blocked-out storeroom

1. The level holds three Marso blockouts, `Crate_01`, `Crate_02` and `Anchor`, and a plain box labelled `Cube`. The user asks to fill them from the library at real size, and says `Cube` is another crate.
2. `find_blockout_matches {actors: [...], scene: "harbour storeroom", words: {"Cube": "wooden crate"}}` lists wooden crates for the three crates.
3. `Anchor` gets only a lamp and a rope coil, and `find_in_library {query: "cast-iron ship's anchor"}` returns only `weak` results. It stays a blockout and is listed as unfilled.
4. The choices are shown with their size differences; nobody answers, so they are swapped and recorded as inferred. `replace_blockouts` downloads the crate: the first swap waits on a `job_id`, the other two on `queue_id` entries, whose jobs appear in `marso_jobs` and are followed with `marso_wait` until they land.
5. `list_actors` shows only `Anchor` still a blockout. Each crate is 0.34 m wider than its box, more than a quarter, so the report names it.
6. The report lists three swaps with their size differences, `Anchor` as unfilled (to be made in Blender), that the new crates are selected, and that the level is saved.

## Common mistakes

- Reading a box's size from its actor bounds: use the `size_m` that `find_blockout_matches` gives.
- Scaling every asset to its box: real size is the default; `fit_to_box` only when the user asks.
- Swapping a box for something else when nothing matches: leave it and list it as unfilled.
- Searching for a box labelled `Cube`: give it words first, from the user or the brief.
- Swapping in an asset from an earlier search: swap after each search, or open its project first.
- Leaving queued downloads unfollowed: a `queue_id` becomes a job in `marso_jobs`; wait for it.
- Placing suggestions the user did not pick: suggest, then place only what is chosen.
