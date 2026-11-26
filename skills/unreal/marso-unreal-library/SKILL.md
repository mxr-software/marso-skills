---
name: marso-unreal-library
description: "Use when finding, importing or placing Marso library assets in an Unreal level (Marso Unreal plugin, closed beta), reusing assets already in the project, or switching a mesh's looks."
license: Apache-2.0
---

# Reuse Marso library assets in Unreal

## Overview

This skill finds assets in the account's Marso library and in the open Unreal project, imports each one once, and places it in the level as actors. It also switches a mesh's looks. Searching, importing and placing spend no credits.

It keeps what the user chose and what is already there:

- An asset the user named or picked is used as it is, never swapped for a search result.
- It imports only what the task needs. It never updates, deletes or replaces an asset already in the project unless the user asks; imports cannot be undone.
- It leaves the user's selection and view as they were: it imports without placing (`spawn: false`) and places each actor itself.
- It makes nothing new: no generation, Retexture or modelling in Unreal. A part the library lacks is reported as missing, to be made in Blender (`marso-generate` or `marso-blender-asset`, when installed).

The Marso Unreal plugin is in closed beta, by invitation. If no Marso Unreal plugin answers, say so and stop the Unreal step; to find or check a library asset without it, offer `marso-library` when installed. Connection problems belong to `marso-unreal-setup` when installed. Moving, grouping and saving follow `marso-unreal-level` when installed; without it, this skill's own rules below are enough to place and check.

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| A named or picked asset in the level | [Import it](#import-it), then [Place it](#place-it) | nothing |
| Find something to use | [Find it](#find-it) | [search](references/search.md) for views and filters |
| Many copies of one asset | [Place it](#place-it): one import, many actors | nothing |
| A different look on a mesh | [Switch looks](#switch-looks) | nothing |
| A newer version of an imported asset | [Newer versions](#newer-versions) | nothing |
| A library material (maps, no mesh) on a mesh | `library_material {asset_id, object_names}` | nothing |
| Blockouts in the level to swap for library assets, or suggestions for the level | `marso-unreal-blockout` when installed; without it, name that skill and leave the blockouts | nothing |
| Collections or favourites | Read the reference | [collections](references/collections.md) |

## Find it

Through the Marso Unreal plugin's MCP tools, call `marso_state` first. Find a command with `marso_search` and read its schema with `marso_describe`, then run it with `marso_run`. A command that returns `job_id` runs in the background: wait with `marso_wait`, at most 50 seconds a call, and never resubmit on a timeout.

If `editor.pie_running` is true, ask the user to stop Play In Editor before placing anything; with nobody to answer, place nothing and report it. Work in the Marso Unreal plugin's units: metres, degrees, and `rotation_deg` as `[x roll, y pitch, z yaw]` in Unreal's frame (X forward, Y right, Z up).

1. For an asset the user named by ID, read `asset_card {asset_id}` to confirm what it is. Do not search. If it answers `not_found`, run `sync_projects`, then open the asset's project with `open_project {project_id}` and read the card again; with no project known, ask the user for it, or report the ID as not found.
2. Look in this Unreal project first: `find_local {query}` searches the Marso assets already imported here.
3. Search the library with `find_in_library {query, image_path}` (a job). Give words and, when there is one, an image of the object: a photo, a render, or a `viewport_screenshot` saved with `name` (pass its `file_path`). Each result has `pbr_asset_id` (what `import_assets` takes), its `project_ids`, and a `verdict`: `match`, `possible` or `weak`.
4. Read the verdict:
   - Words alone or an image alone never say more than `possible`; with both, `match` means the two searches agree.
   - Show `possible` results to the user to choose. With nobody to answer, take the best `possible` result whose `asset_card` fits the brief (category and size) and record the choice as inferred.
   - A `weak` result is usually something else: report it as weak and place nothing in its stead.
5. Read [search](references/search.md) to browse a project or the whole library, or to filter what is in this project.

Done when each wanted item has an asset ID or a content path with its verdict, or is listed as not found.

## Import it

1. If the asset is already in the project, use it: `asset_card` gives `imported_path`, and `find_local` results are already imported. Skip to [Place it](#place-it).
2. Run `import_assets {asset_ids, spawn: false}` (a job). A `find_in_library` result imports directly. Without `spawn: false`, the import places an actor of its own, selects it and moves the view to it.
3. If the import says an asset is not in the open project, open its project with `open_project {project_id}` (from the result's `project_ids` or its `asset_card`) and import again.
4. Read the result:
   - each imported mesh and its content path;
   - `materials` for an asset that is maps with no mesh: put it on meshes with `library_material {asset_id, object_names}`;
   - `added_as_look` and `look` when the asset is a retexture of a mesh already here: it became a look of that mesh, not a second mesh. Say so;
   - a retexture expected as a look but imported as its own mesh: its geometry differs from the mesh here, or Project Settings > Plugins > Marso > **Merge retextures into looks** is off. Report which, and that it did not merge;
   - `minted` false: Marso has not minted the asset, so it has no real-world scale or physics yet. Report it.

Done when each asset has a content path, or is listed with the import's error, and every look made is reported.

## Place it

1. Import each asset once. Place each actor with `spawn_static_mesh {asset_path, name, location, rotation_deg, folder}`; every copy is another actor on the same Static Mesh.
2. Give each actor a label (`name`) that says what it is, and put this run's actors in one Outliner folder (`folder`). On a rerun, move the actors with those labels instead of adding more.
3. Find the height of the surface each actor stands on: `get_actor {actor, bbox: true}` on that surface (the level's floor, a table) gives its top as the highest `bbox` value.
4. Check each placed actor with `get_actor {actor, bbox: true}`: its lowest `bbox` value is at the surface's height, so nothing floats or sinks. Correct the height with `set_transform`.
5. Check the copies with `list_actors {name_contains}`: every copy shows the same `asset_path`.

Done when `list_actors` shows each placed actor with its label, mesh and location, resting on its surface.

## Switch looks

1. `list_looks {actor}` lists the looks of an actor's mesh: "Original" and each retexture added as a look, with the one that actor shows (`actor_look`). `list_looks {asset_path}` gives the asset's default (`asset_default`) instead.
2. `set_look {look, actors}` changes those actors only, materials and physical material together. `set_look {look, asset_path}` changes what the asset shows by default, on every actor without its own choice.
3. `delete_look` deletes a look's assets and cannot be undone: ask first. With nobody to answer, keep the look.

Done when `list_looks {actor}` gives the requested look as `actor_look` for each named actor.

## Newer versions

1. Run `sync_projects` and open the whole library with `open_project {project_id: "all"}`: `list_updates` compares only what the library has read.
2. `list_updates` lists imported assets with a newer version in the library, each with its imported `asset_id` and its `newer_asset_id`.
3. `update_assets {asset_ids}` takes the imported (older) IDs and imports each newer version over the mesh already here, so every actor using it changes; it cannot be undone. Update only the assets the user named, and ask before updating more. With nobody to answer, update only the named ones.

Done when `list_updates` no longer lists the updated assets.

## Report

Report what was searched and where, with the verdicts. List each asset ID imported with its content path, the actor labels placed, and every look made or switched. Name unminted assets, anything not found, and what was not checked (fit at the user's camera, scale against neighbours).

Done when the final message holds each item above.

## Worked example: forty crates for a harbour level

1. The user asks for forty wooden crates along the quay, and one crate painted blue by the gate. `marso_state` shows `/Game/Maps/Harbour` open and no Play In Editor.
2. `find_local {query: "wooden crate"}` finds nothing imported. `find_in_library {query: "wooden crate", image_path: <the user's photo>}` returns one `match` and two `possible` results; the match is used.
3. `import_assets {asset_ids: [<match>], spawn: false}` imports one Static Mesh, `/Game/Marso/Props/WoodenCrate/SM_WoodenCrate`.
4. `get_actor {actor: "Quay", bbox: true}` puts the quay's top at 1.2 m. Forty `spawn_static_mesh` calls place `Crate_01` to `Crate_40` along it, in the folder `Props/Crates`. `get_actor {actor: "Crate_01", bbox: true}` shows its base at 1.2 m. `list_actors {name_contains: "Crate_"}` shows forty actors on the one mesh.
5. The library holds a blue retexture of the same crate. `import_assets {asset_ids: [<blue>], spawn: false}` adds it with `added_as_look: true` as the look `Blue`. `set_look {look: "Blue", actors: ["Crate_40"]}` paints the crate by the gate only.
6. A search for "harbour bollard" returns only `weak` results. Nothing is placed for it; the report names it as missing, to be made in Blender.

## Common mistakes

- Importing an asset once for every copy: import once and place many actors on its mesh.
- Importing with `spawn` left on: it adds an actor, selects it and moves the view; import with `spawn: false` and place each actor.
- Placing a `weak` result in place of what was asked: report it and place nothing.
- Searching for a substitute when the user named an asset: use the named one, opening its project if needed.
- Making a missing asset in Unreal: report it; it is made in Blender.
- Updating every imported asset when the user named one: update only the named ones, and ask before more.
- Leaving actors floating or sunk: compare each base with the top of its surface and correct the height.
