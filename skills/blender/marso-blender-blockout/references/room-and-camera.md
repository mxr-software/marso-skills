# Room shell and camera handoff

Load `scripts/room_shell.py` from this skill in Blender with `runpy.run_path`, then call its `build(spec)` function. It needs no cloud connection. The helper creates thick walls, a floor, and Empty/geometry-group hierarchy in a new owned collection; it never overwrites an existing run.

```python
spec = {"run_id": "room-v1", "size": [4, 6, 2.7], "thickness": 0.15,
        "origin": [0, 0, 0], "yaw_deg": 20,
        "openings": [{"wall": 0, "start": 1, "width": 0.9,
                      "bottom": 0, "height": 2.1}]}
```

Default floor corners are `(0,0), (width,0), (width,depth), (0,depth)`. Wall indices follow consecutive counterclockwise corners; opening start is measured along that wall. `origin` and `yaw_deg` move the complete root. Supply `corners` for a convex counterclockwise footprint. Non-right corners require `nonorthogonal_reason`; this is an explicit design/evidence note, not automatic validation of an image. Concave footprints and touching/overlapping openings are refused rather than guessed. The floor uses the inner footprint; adjoining thick wall boxes may overlap at joints. This is blockout construction, not final architectural topology.

Inspect door/window holes and normals. Save the returned `anchors` with the scene record; each anchor identifies its entity and local geometry group. If refining a shell, edit its owned geometry or build a separate version and deliberately transfer corrections. Do not delete accepted architecture to rerun a builder.

For photograph placement, provide existing anchors through the placement helper's `--shell` handoff. Map photographic wall/floor ids to the actual shell entities and supply their shared world-space floor lines for wall projection. Do not infer mapping from matching object names. Keep the accepted shell unchanged during later asset placement; photograph-derived estimates remain reviewable.
