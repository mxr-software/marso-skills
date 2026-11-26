---
name: marso-unreal-stage
description: "Use when lighting, framing or rendering stills of an Unreal level (Marso Unreal plugin, closed beta): a lighting preset, cameras and shots, still renders, or a visual check of what was placed."
license: Apache-2.0
---

# Light and shoot an Unreal level

## Overview

This skill lights an Unreal level with a Marso lighting preset, sets up cameras, renders still images and checks each one before handing it back. It keeps what the user made: the level's own lights stay on unless the user asks to replace them, and the user's own cameras are never moved. Each shot gets a camera of its own.

Output is still images only. Image sequences, turntables and Movie Render Queue renders are not available through the Marso Unreal plugin: say so, and offer several stills from different angles instead. With nobody to answer, render no extra stills: report the offer.

The Marso Unreal plugin is in closed beta, by invitation. If no Marso Unreal plugin answers, say so and stop the Unreal step; connection problems belong to `marso-unreal-setup` when installed. Placing assets belongs to `marso-unreal-library` and `marso-unreal-set-piece`, each when installed; without them, stage what is already in the level.

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| Light the level | [Light it](#light-it) | nothing |
| A shot of something | [Set up a shot](#set-up-a-shot) | nothing |
| Render stills | [Render and check](#render-and-check) | nothing |
| A video, turntable or sequence | Say stills only; offer several angles | nothing |
| A quick look at the editor view | `viewport_screenshot` | nothing |

## Before staging

Through the Marso Unreal plugin's MCP tools, call `marso_state` first. Find a command with `marso_search` and read its schema with `marso_describe`, then run it with `marso_run`. A command that returns `job_id` runs in the background: wait with `marso_wait`, at most 50 seconds a call, and never resubmit on a timeout.

If `editor.pie_running` is true, ask the user to stop Play In Editor first; with nobody to answer, stage nothing and report it. Work in metres and degrees, in Unreal's frame (X forward, Y right, Z up).

Done when the open level and the Play In Editor state are known.

## Light it

1. List the lights: `list_actors {classes: ["Light", "SkyLight"]}`. Lights in the Outliner folder `Marso/Lighting` are a Marso rig; any other light is the level's own.
2. If the level has lights of its own, keep them and add no rig, unless the user asked for a preset or to replace the lighting. To replace them, hide them with `set_visibility {actors, visible: false}`, which the user can undo; never delete them.
3. Choose a preset for the brief and run `lighting_preset {preset}`:
   - `studio`: a product studio with a backdrop on the -X side, soft lights and fixed exposure. Shoot it from the +X side.
   - `daylight`: sun, sky and haze, for an outdoor or open scene.
   - `warehouse`: dim light under overhead panels, for an interior.
4. The rig surrounds the selection, else the Marso assets, else all geometry. Calling `lighting_preset` again replaces the previous Marso rig; `lighting_preset {preset: "none"}` removes it.

With nobody to answer, choose the preset the brief points to and record the choice as inferred.

Done when `list_actors {classes: ["Light", "SkyLight"]}` shows the intended lighting, and the level's own lights are on, or hidden at the user's request.

## Set up a shot

1. Make a camera for each shot: `create_camera {name, location, look_at, focal_length}`. Label it after the shot (`Shot_Front`). On a rerun, move the camera with that label instead of adding another.
2. Aim it at the subject with `frame {actors, camera, yaw_deg, elevation_deg, margin}`: it moves the camera to the nearest distance that keeps the actors in frame. `yaw_deg` 0 looks from +X back along -X; `elevation_deg` is the angle above. Or place it exactly with `look_at {eye, target, camera}`.
3. Choose the focal length for the shot: about 50 mm for a single object, 35 mm (the default) for a group, 24 mm for a wide view of the level.
4. Leave the user's own cameras and the editor viewport where they are; `create_camera` with `set_active` moves the viewport, so leave it off.

Done when every shot has its own labelled camera aimed at its subject.

## Render and check

1. Render each shot: `render_image {camera, width, height, name}`. It writes `Saved/Marso/Renders/<name>.png` in the Unreal project (1920 by 1080 by default) and returns a preview.
2. Look at every preview before handing it back:
   - the subject is whole, fills a good part of the frame and is not cut at the edges;
   - the horizon is level and nothing floats above or sinks into a surface;
   - the image is neither near black nor washed out.
3. Correct a fault and render again, at most twice for each shot:
   - framing: `frame` again with a different `margin`, `yaw_deg` or `elevation_deg`, or another focal length;
   - floating or sinking: report the actor, since placement belongs to the placing skill;
   - too dark or too bright under a Marso preset: try the preset that suits the scene better. Under the level's own lights, report it and offer a preset; with nobody to answer, add none.
4. `render_image` draws the game view: Marso blockouts and editor icons do not appear in it. Use `viewport_screenshot` to show them.

Done when every shot has a render file that passed the checks, or the report names the fault left.

## Report

Report the lighting (preset chosen and why, the level's own lights kept or hidden), each camera with its label, and each render's file path. Name every fault left after two corrections and every inferred choice.

Done when the final message holds each item above.

## Worked example: shooting a dressed harbour level

1. The user asks for "a few nice shots of the harbour". `marso_state` shows `/Game/Maps/Harbour` open and no Play In Editor.
2. `list_actors {classes: ["Light", "SkyLight"]}` finds the level's own directional light and sky light. They stay; no rig is added.
3. Three cameras: `Shot_Wide` at 24 mm, `Shot_Quay` at 35 mm framed on the crates with `frame {actors: [...], camera: "Shot_Quay", yaw_deg: 30, elevation_deg: 15}`, and `Shot_Detail` at 50 mm on one crate.
4. `render_image` for each. `Shot_Detail` cuts off the crate's top: `frame` again with `margin` 0.2 and a second render passes.
5. The user then asks for a turntable of the crate. The answer is stills only, with four renders offered from `yaw_deg` 0, 90, 180 and 270.
6. The report lists the kept lighting, the three cameras and the three render paths.

## Common mistakes

- Adding a preset over the level's own lights: keep them unless the user asks; hide them, never delete them, when asked.
- Moving the user's camera or viewport for a shot: create a labelled camera for each shot.
- Handing back a render without looking at it: check every preview, and correct at most twice.
- Promising a turntable or sequence: stills only; offer several angles.
- Shooting the `studio` preset from its backdrop side: shoot it from +X.
- Expecting blockouts in `render_image`: it draws the game view; use `viewport_screenshot`.
