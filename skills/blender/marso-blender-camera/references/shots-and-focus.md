# Shots, focus and handheld movement

## Shot design

Define meaningful start and end views and the camera move between them. Keep subject framing and headroom deliberate. Keep the lens fixed unless a lens change is intended, and keep the camera clear of geometry and of its aim and focus targets.

For an orbit, use linear easing and place keys densely around the subject (for example every 15 to 30 degrees). The helper interpolates positions in straight lines, so sparse keys cut chords toward the subject. Inspect intermediate views.

## Rig helper spec

Set `camera_helper_path` to the absolute path of `scripts/camera_rig.py` in the installed skill folder, readable by the Blender process. Then, in Blender, `import runpy, bpy`, load the helper with `runpy.run_path` and call its `build` function with a spec:

```python
spec = {"id": "bench-dolly-v1", "fps": 24, "lens_mm": 45,
        "fstop": 5.6, "shutter_frames": 0.5, "resolution": [960, 540],
        "handheld": "none", "easing": "smoothstep", "keys": [
          {"frame": 1, "position": [1, -3, 1.6], "aim": [1, 1, 1.1]},
          {"frame": 49, "position": [2, -2, 1.6], "aim": [1, 1, 1.1]}]}
```

- `id` and `keys` are required. Each build needs a new `id`; a reused one raises "Shot exists; use a new revision", so version it (`bench-dolly-v2`).
- Omitted fields default to `fps` 24, `lens_mm` 50, `fstop` 5.6, `shutter_frames` 0.5, `resolution` `[1920, 1080]`, `handheld` `"none"` and `easing` `"linear"`. The rig always enables depth of field at `fstop`.
- Keys have strictly increasing integer frames; one key is a still. Positions, `aim` and the optional `focus` are world-space 3-vectors, as lists or `mathutils.Vector`. Focus defaults to aim.
- `build` raises before creating anything if the camera path comes within 1 cm of the aim or focus target.

Interpolation defaults to `easing: "linear"`. Set `easing: "smoothstep"` for ease-in and ease-out on each segment: the base path stops at every supplied key, including intermediate keys. Positions, aim and focus use the same easing. Both modes bake per-frame keys with linear subframes, so smoothstep is a sampled approximation, not a continuous spline. Use linear mode or a deliberately sampled path when intermediate keys should not be stops.

## Holds and handheld

For a two-second base hold at 24 fps, repeat the initial position, aim and focus at frames 1 and 49. Then put the first move's endpoint at a later frame (for example 97). With smoothstep the next segment eases out of the hold.

`handheld: "none"` gives a stationary hold and smooth stabilised motion. `handheld` also accepts `"standing"` or `"walking"`; optional `amount` (0 to 3, default 1) scales the movement. Walking contribution fades with smoothed travel speed, and the base sway remains at pauses, so a base hold with handheld enabled is not perfectly static. Defaults are starting points to inspect, not a universal natural camera.

At `amount` 1, handheld offsets reach about 3 mm standing and 1 cm walking, in scene units assumed to be metres; check the scene unit scale before enabling handheld. Added shake does not make a shot realistic; judge it on the preview.

## Output settings and motion blur

Apply output settings explicitly after building:

```python
import runpy, bpy
helpers = runpy.run_path(camera_helper_path)
build, apply_output_settings = helpers['build'], helpers['apply_output_settings']
shot = build(spec)
# Uses the current renderer; does not change materials, lighting or render quality.
applied = apply_output_settings(shot, motion_blur=False)
# Helper blur is verified for Cycles only. On an accepted Cycles scene:
applied = apply_output_settings(shot, motion_blur=True)
# On another accepted engine, keep it: apply with motion_blur=False, then enable
# that engine's own motion blur and verify a short rendered segment.
```

`apply_output_settings` sets the active camera, frame range, `fps` and `fps_base` (including fractional rates), resolution at 100%, shutter and the explicit blur toggle. It returns the settings actually applied. It checks Blender RNA limits before changing anything, rather than accepting silently clamped output.

Blur enablement was verified for Cycles in Blender 5.2; `motion_blur=True` rejects other engines before changing settings. `motion_blur=False` explicitly disables blur and also supports lightweight Workbench output. In Blender 5.2, EEVEE reads the shared `scene.render.use_motion_blur` and `scene.render.motion_blur_shutter`, so on an accepted EEVEE scene set `use_motion_blur` after applying; Workbench has no motion blur. The helper does not choose a device, alter shutter position, render frames or prove that moving edges are sufficiently sampled. Switch the scene to Cycles only when the task asks for it.

Shutter is a fraction of a frame: 0.5 corresponds to a 180-degree exposure interval, and actual duration depends on frame rate. Recording shutter intent alone does not enable blur; verify the installed renderer's motion-blur settings and enable them deliberately. When blur is part of the requested output, render a short segment with blur on and compare it with blur off; a Workbench preview cannot establish blur quality.

## Clearance

After building, run `clearance_report = helpers['clearance_report']`, then `clearance_report(bpy.data.objects[shot['camera']], obstacle_meshes, clearance=.15)` on the relevant static obstacles. Pass Blender objects, not names, and pass the mesh objects inside each obstacle's entity group. The report lists non-mesh objects and meshes without faces under `skipped`, and raises when no mesh with faces remains. It passes only when nothing was skipped and no issue was found.

It reports frames where the camera centre is nearer than `clearance` to a mesh, and crossings along adjacent sampled positions in world space. It is a diagnostic, not a full near-plane, frustum, swept-volume or animated-obstacle proof. Check hollow or interior geometry, the camera housing and changing objects visually. Set `clearance` from the shot scale: the default is 0.15, and a macro shot may need only a few centimetres.

## Sequence review

Check turns, starts and stops, aim drift and focus across the whole preview. Inspect moving edges, pauses, focus transitions and temporal noise. Keep a static reference view to tell motion artefacts from material defects. Save clean rendering and optional effects (grain, bloom) separately, so effects never hide broken geometry or normals.
