---
name: marso-blender-camera
description: "Use when composing a still shot, making a camera move (dolly, orbit, path) or handheld walkthrough, or setting camera focus or motion blur in an existing Blender scene."
license: Apache-2.0
---

# Cameras for an existing scene

## Overview

This skill adds still compositions and camera moves to an existing Blender scene, saved as editable camera data. It preserves accepted geometry, materials, lighting and render engine: a camera request never authorises asset regeneration or an engine change. If the task also includes new assets, their model approval still applies through `marso-blender-asset` when installed; camera work on accepted geometry continues meanwhile.

Build cameras with Blender camera data or the shipped rig helper. The add-on's studio commands build or rearrange the add-on's own product-shot studio scene, so use them only on that scene or when the user asks for it. `create_scene` and `clear_scene` remove Blender's default camera and earlier Marso setup, `arrange_objects` moves showcase objects onto a grid, and `create_camera` makes `Marso_Camera` the active camera. Confirm any add-on command in `all_commands()` and its `describe()` schema before calling it.

Hand lighting and final rendering to `marso-blender-render` when installed, and follow its lighting and render steps without recreating the scene. Without it, render the requested shots with the scene's current lighting and report that no lighting pass was made.

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| Still of an existing scene | [Compose a still](#compose-a-still); no animation setup | nothing |
| Simple product still on the add-on's studio scene | Adjust `Marso_Camera` with `frame_subject` (after `set_subject`) or `nudge_camera` | their `describe()` schemas |
| Match a reference photo's view | [Compose a still](#compose-a-still), step 2 | nothing |
| Dolly, orbit or path | [Plan and check a camera move](#plan-and-check-a-camera-move) | [shots and focus](references/shots-and-focus.md) |
| Handheld walkthrough | Same steps with `handheld: "standing"` or `"walking"` | [shots and focus](references/shots-and-focus.md) |
| Smooth or stabilised move | Same steps with `handheld: "none"` | [shots and focus](references/shots-and-focus.md) |
| Blockout or playblast | Workbench with `motion_blur=False`, labelled as blur-free | nothing |
| Final sequence with blur | [Deliver](#deliver): blur on the accepted engine, short blur test | [motion blur](references/shots-and-focus.md#output-settings-and-motion-blur) |
| Lighting, render quality or render time | `marso-blender-render` when installed | nothing |

## Establish the shot

1. Take the subject, output aspect, still or motion, intended duration and camera behaviour from the request.
2. Infer any routine choice the request leaves open, and record each inferred choice for the handoff. This skill has no approval step; with nobody to answer, proceed on the recorded inferences.
3. Treat an explicit smooth or stabilised request as excluding handheld noise.

Done when subject, aspect, still or motion, duration and behaviour are each stated or recorded as inferred.

## Compose a still

1. Place the camera at a plausible height and viewpoint, then choose lens and framing together.
2. When matching a reference, match its perspective with camera height and lens before changing any object proportions.
3. Focus on the actual surface of interest, not the centre of a deep object, and keep depth of field useful.
4. Leave animation unset: a still needs no keys, frame range or motion settings.

Done when a camera-view render shows the subject framed as requested, with focus on the intended surface.

## Plan and check a camera move

Read [shots and focus](references/shots-and-focus.md) before building any move: it holds the helper spec, easing, holds, handheld modes, output settings and clearance limits.

1. Block the path through clear space, with aim and focus targets and any pauses, before adding handheld movement.
2. Build the rig in Blender through the Blender MCP tools, with the optional helper `scripts/camera_rig.py` or with Blender camera data. The helper builds a new camera from explicit keys. It does not solve cinematic composition, reconstruct cameras from an image or select focus automatically.
3. Run `clearance_report` on the mesh objects of the relevant static obstacles (inside each entity group, not the group Empty), and resolve or explain every issue and skipped object it returns.
4. Apply output settings with `apply_output_settings`; `build` leaves the active camera and scene output unchanged.
5. Render a cheap moving preview and representative frames, and inspect both. Framing samples alone cannot establish clearance, focus stability or pleasing motion.

The helper's returned `revision` identifies the requested rig and settings; reusing rendered output also needs the scene, assets and lighting to be unchanged. After any change to the rig, scene, assets or lighting, build with a new `id` (the helper refuses one already in the file) and re-render every frame you deliver.

Done when the preview has been inspected across turns, stops, aim and focus, and the clearance report passes or each issue is explained.

## Deliver

1. For a final sequence with blur, keep the accepted render engine. On Cycles, apply with `motion_blur=True`; on another engine, apply with `motion_blur=False` and enable that engine's own motion blur (for EEVEE, `scene.render.use_motion_blur`). Switch to Cycles only when the task asks for it.
2. Test a short rendered segment with blur on and off before the full run.
3. Leave a requested blockout or playblast in Workbench without blur, and label it so.
4. Hand the camera, frame range, frame rate, resolution, focus, shutter intent and `revision` to `marso-blender-render` when installed.
5. Save the rig as editable Blender data and deliver only the requested shots.

Done when the saved file holds the rig camera tagged with `marso_shot_revision`, `apply_output_settings` has returned the delivered frame range, resolution and blur state, and the handoff lists the inferred choices and checks run.

## Worked example: smooth three-second dolly past the bench

Request: "Make a smooth three-second dolly past the bench, holding on the bench for two seconds first. Render it with motion blur." The accepted scene renders in Cycles.

1. Record the inferences: 16:9 at 24 fps, subject the bench, motion, smooth, so `handheld: "none"`.
2. Load the helper with `runpy.run_path` and call `shot = build(spec)` with `id` `bench-dolly-v1`, `easing` `"smoothstep"`, and keys at frames 1 and 49 repeating the start position, aim and focus (the hold), then the end key at frame 121. No intermediate key is added, because smoothstep stops at every key.
3. Run `clearance_report(bpy.data.objects[shot['camera']], [bench_mesh, table_mesh, wall], clearance=.15)`. It reports a crossing near frame 90; move the end key, then build `bench-dolly-v2`, because `v1` already exists.
4. Call `apply_output_settings(shot, motion_blur=False)`, render a low-resolution preview, and check the hold, the ease out of it, aim drift and focus on the bench seat.
5. The engine is already Cycles, so call `apply_output_settings(shot, motion_blur=True)` and render frames 60 to 70 with blur on and off to confirm real blur.
6. Save the file and hand the camera, frames 1 to 121, 24 fps, resolution, focus, a 0.5 shutter and the `revision` to `marso-blender-render`.

## Common mistakes

- Running `create_scene`, `clear_scene` or `arrange_objects` on an accepted scene: build the camera with Blender data or the helper instead.
- Switching an accepted scene to Cycles for blur: keep its engine and enable that engine's blur.
- Changing the lens to fake a dolly: a dolly moves the camera, which changes perspective; keep the lens fixed.
- Adding handheld noise to a smooth or stabilised request: use `handheld: "none"`.
- Expecting `build` to set the active camera or output: call `apply_output_settings` after it.
- Judging motion blur from a recorded shutter or a Workbench preview: render a short blurred segment.
- Treating framing samples or a passed `clearance_report` as proof of a clear, steady move: inspect a moving preview too.
