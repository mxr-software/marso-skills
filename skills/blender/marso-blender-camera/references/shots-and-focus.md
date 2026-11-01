# Shots, focus and handheld movement

Define meaningful start/end views and the route between them. A dolly changes perspective; changing lens alone is not a dolly. For an orbit, choose explicit positions around the subject and inspect intermediate views. Keep subject framing and headroom deliberate. Avoid accidental lens changes, camera clipping and zero-distance focus targets.

If using the optional helper, load `scripts/camera_rig.py` from this skill with `runpy.run_path`, assign its `build` function to a variable, and call it with the following spec in Blender:

```python
spec = {"id": "bench-dolly-v1", "fps": 24, "lens_mm": 45,
        "fstop": 5.6, "shutter_frames": 0.5, "resolution": [960, 540],
        "handheld": "none", "easing": "smoothstep", "keys": [
          {"frame": 1, "position": [1, -3, 1.6], "aim": [1, 1, 1.1]},
          {"frame": 49, "position": [2, -2, 1.6], "aim": [1, 1, 1.1]}]}
```

Keys have strictly increasing integer frames; one key is a still. Optional `focus` is a world-space position independent of aim. Default focus follows aim. Interpolation defaults to `easing: "linear"`. Set `easing: "smoothstep"` for ease-in/ease-out on each segment: the base path stops at every supplied key, including intermediate keys. Positions, aim and focus use the same easing. Both modes bake per-frame keys with linear subframes, so smoothstep is a sampled approximation, not a continuous spline. Use linear mode or a deliberately sampled path when intermediate keys should not be stops.

For a two-second base hold at 24 fps, repeat the initial position, aim and focus at frames 1 and 49, then put the first move's endpoint at a later frame (for example 97). With smoothstep the next segment eases out of the hold. `handheld: "none"` gives a stationary hold and smooth stabilized motion. `handheld` also accepts `standing` or `walking`; optional `amount` controls bounded millimetre-scale movement. Walking contribution fades with smoothed travel speed and standing sway remains at pauses, so a base hold with handheld enabled is not perfectly static. Defaults are starting points to inspect, not a universal natural camera.

Building a rig leaves the active camera and scene output settings unchanged. Apply them explicitly if wanted:

```python
helpers = runpy.run_path(camera_helper_path)
build_rig = helpers['build']
apply_settings = helpers['apply_output_settings']
shot = build_rig(spec)
# Uses the current renderer; does not change materials, lighting or render quality.
applied = apply_settings(shot, motion_blur=False)
# For verified real motion blur, choose Cycles deliberately before applying:
bpy.context.scene.render.engine = 'CYCLES'
applied = apply_settings(shot, motion_blur=True)
```

The optional helper sets the active camera, frame range, fps/fps_base (including fractional rates), resolution at 100%, shutter and the explicit blur toggle. It returns actual applied settings. It validates Blender RNA limits before mutation rather than accepting silently clamped output. Blur enablement is verified for Cycles in Blender 5.2; `motion_blur=True` rejects other engines before changing settings. `False` explicitly disables blur and also supports lightweight Workbench output. It does not choose a device, alter shutter position, render frames or prove that moving edges are sufficiently sampled. Render a short real Cycles blur segment and compare it with blur disabled when blur is part of the requested output; a Workbench preview cannot establish blur quality.

Use `clearance_report(camera, objects, clearance=.15)` on relevant static obstacles after building. It checks proximity at frames and intersections along adjacent sampled camera positions in world space. It is a diagnostic, not a full near-plane/frustum swept-volume or animated-obstacle proof. Hollow/interior geometry, camera housing and changing objects need visual/targeted checks. Do not apply a universal half-metre clearance to macro shots.

Keep scene scale meaningful; handheld amplitudes are metres. Check turns, starts/stops, aim drift and focus across the whole preview. Do not equate added shake with realism. Preserve a static reference view to distinguish motion artifacts from material defects.

Shutter is a fraction of a frame: 0.5 corresponds to a 180-degree exposure interval. Actual duration depends on frame rate. Verify the installed renderer's motion-blur settings and enable them deliberately; recording shutter intent alone does not enable blur. For sequence review inspect moving edges, pauses, focus transitions and temporal noise. Save clean rendering and optional effects separately; grain/bloom must not hide broken geometry or normals.
