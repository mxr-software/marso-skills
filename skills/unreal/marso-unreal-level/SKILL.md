---
name: marso-unreal-level
description: "Use when working in an Unreal level through the Marso Unreal plugin (closed beta): opening, creating, saving or inspecting a level, or moving, grouping, hiding or deleting its actors."
license: Apache-2.0
---

# Work in an Unreal level

## Overview

This skill opens, creates, saves and inspects Unreal levels, and moves, groups, hides and deletes actors, through the Marso Unreal plugin's MCP tools. It also holds the conventions every Unreal skill shares. It changes only what the task names: other actors, the selection and the viewport stay as the user left them.

The Marso Unreal plugin is in closed beta, by invitation. If no Marso Unreal plugin answers, say so and stop the Unreal step. Connection problems belong to `marso-unreal-setup` when installed; without it, report what `marso_state` returned and stop.

Ask the user first, every time, before any of these. With nobody to answer, do not do it: report it as waiting for the user.

- discarding unsaved changes (`discard_unsaved`);
- deleting an asset from the project (`delete_assets`), which cannot be undone;
- deleting an actor whose attached children would be left behind (`delete_actors` with `force`);
- writing to a content path the user did not name outside the Marso content root (see the conventions below);
- editing while Play In Editor runs, or stopping a play session the user started.

Adjacent work: library assets belong to `marso-unreal-library` when installed; without it, place only meshes already in the project. Generating, texturing or modelling assets is not done in Unreal by these skills: name what is missing and say it is made in Blender.

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| Anything in a level | [Before any change](#before-any-change) | nothing |
| Open, start or save a level | [Open, create or save](#open-create-or-save) | nothing |
| What is in this level, where is it | [Inspect](#inspect) | nothing |
| Move, turn, scale, copy, group, hide or delete actors | [Change actors](#change-actors) | nothing |
| Place a library asset | `marso-unreal-library` when installed | nothing |

## Before any change

Through the Marso Unreal plugin's MCP tools, call `marso_state` first. Find a command with `marso_search` and read its schema with `marso_describe`, then run it with `marso_run`. A command that returns `job_id` runs in the background: wait with `marso_wait`, at most 50 seconds a call, and never resubmit on a timeout.

1. From `marso_state`, note `editor.level` and `editor.level_name`.
2. If `editor.pie_running` is true, ask the user to stop Play In Editor before any edit. Editing commands do not wait for play to end: they change the editor's level while the user plays. With nobody to answer, make no edit and report it.
3. Work in the Marso Unreal plugin's conventions:
   - Lengths are metres and angles degrees. `rotation_deg` is `[x roll, y pitch, z yaw]`.
   - Positions are in Unreal's frame: X forward, Y right, Z up, which is left-handed. Convert a position from a right-handed plan before using it.
   - Actors are addressed by label, name or path. `list_actors` gives the label as `name` and the full path as `actor_path`. When two actors share a label, use `actor_path`.
   - Assets are addressed by content path (`/Game/...`). Marso imports under the content root, `/Game/Marso` unless Project Settings > Plugins > Marso > **Content root** says otherwise.
   - A command marked undoable in its `marso_describe` schema is one editor undo step. `new_level` clears the undo history. `delete_assets`, `delete_look`, `make_level_instance` and every import write to disk and cannot be undone.
4. Before adding actors, look for the ones an earlier run added, by label or by the run's Outliner folder. Move those instead of adding more.

Done when the open level and the Play In Editor state are known, and no edit has been made during play.

## Open, create or save

1. Open a level with `open_level {path}`, a content path such as `/Game/Maps/Harbour`. Start one with `new_level {template}`: `empty`, `basic` (floor, sky and sun, the default) or `open_world`.
2. Both refuse while the open level has unsaved changes. Then ask whether to save, discard or stop. With nobody to answer, save the open level first if it has a path (`editor.level` is not under `/Temp/`), and report that save as made for the user; otherwise stop and report the unsaved level.
3. Save with `save_level`. An untitled level needs `asset_path`: use the path the user named. With none named, save under `<content root>/Levels/` with a name from the task, and report the path.
4. Save before handing back when the task asks for a saved result; otherwise report the level as unsaved.

Done when `marso_state` shows the intended `editor.level`, and the level is saved or reported unsaved.

## Inspect

- `list_actors` lists actors with label, class, Outliner folder, transform and mesh. Filter with `classes`, `name_contains`, `folder`, `marso_only` or `selected_only`; add `bbox` for world bounds in metres. It returns 500 at most unless `limit` says otherwise; `truncated` says when there are more.
- `get_actor {actor}` gives one actor in full: transform, parent and children, mesh and Marso lineage; add `bbox`, `materials` or `components` as needed.
- `list_marso_assets {scope: "level"}` lists the actors whose mesh came from Marso.
- To see the level, `viewport_screenshot` returns the active viewport as an image. `frame {actors}` aims the viewport at actors first; it moves the user's view, so frame only when the task needs a look, and say so.

Done when the answer names each actor asked about by label, with its class and location.

## Change actors

| Change | Command |
| --- | --- |
| Move, turn or scale | `set_transform {actor, location, rotation_deg, scale}`; values left out stay as they are |
| Copy | `duplicate {actors, count, offset}`, each copy `offset` metres further on |
| Place a mesh already in the project | `spawn_static_mesh {asset_path, name, location, rotation_deg, folder}` |
| Group in the Outliner | `set_folder {actors, folder}`, nested with `/` |
| Parent to another actor | `attach {actor, parent}`; it keeps its world position unless `keep_world` is false |
| Show or hide, in the editor and in game | `set_visibility {actors, visible}` |
| Delete | `delete_actors {actors}` |

1. Change only the actors the task names, or the ones this run made.
2. Give each actor this run places with `spawn_static_mesh` a label (`name`) that says what it is, unique in the level. Copies from `duplicate` get labels Unreal chooses, and these commands cannot rename them.
3. Put every actor this run adds in one Outliner folder named for the task (`folder`, or `set_folder`), so a rerun finds them.
4. If `delete_actors` refuses because an actor has attached children, ask whether to delete the children too or detach them first (`attach` with an empty `parent`). With nobody to answer, leave the actor and report it.
5. Check each change with `get_actor` or `list_actors`: the location, rotation and folder are what was asked.
6. Save as in [Open, create or save](#open-create-or-save).

Done when `list_actors` or `get_actor` shows every requested change, and the level is saved or reported unsaved.

## Report

Report the level path, each actor changed or added by label with what changed, and whether the level was saved. Name any level saved on the user's behalf, anything waiting for the user, and what was not checked.

Done when the final message holds each item above.

## Worked example: tidying the dining area of a saved level

1. `marso_state`: `editor.level` is `/Game/Maps/Harbour`, `editor.pie_running` is false.
2. `list_actors {name_contains: "Chair"}` returns `Chair`, `Chair2` and two actors labelled `Chair3` with different `actor_path` values.
3. `set_folder {actors: [...], folder: "Props/Dining"}` groups them, using `actor_path` for the two `Chair3`s. `set_transform {actor: "Chair2", rotation_deg: [0, 0, 180]}` turns one to face the table.
4. The user also asked to delete the old table. `delete_actors` refuses: two plates are attached to it. Nobody answers the question, so the table stays and is reported.
5. `get_actor {actor: "Chair2"}` shows a yaw of 180. `save_level` saves the level.
6. The report lists the four chairs in `Props/Dining`, the turned chair, the table left in place with its plates, and that the level is saved.

## Common mistakes

- Discarding unsaved changes to open another level: ask, or save a level that has a path.
- Writing rotations in another order: `rotation_deg` is `[x roll, y pitch, z yaw]` in degrees.
- Using centimetres or a right-handed plan's positions as they are: the Marso Unreal plugin takes metres in Unreal's left-handed frame.
- Adding more actors on a rerun: find the earlier ones by label or folder and move them.
- Editing during Play In Editor: the edit lands in the editor's level mid-play; ask the user to stop it first.
- Forcing a delete that orphans attached actors: ask, or leave the actor and report it.
- Moving the user's viewport for no reason: frame only when a look is needed, and say so.
