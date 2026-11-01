# Charts from construction parameters

Use [parametric_uv.py](../scripts/parametric_uv.py) when the builder knows a surface's length/perimeter coordinates. This avoids asking a general unwrap solver to rediscover a simple band or sweep. It is not an automatic unwrap for arbitrary meshes.

Import `assign_chart` from the packaged script directory in Blender, then call:

```python
assign_chart(mesh, metric_coordinates, uv_name="MarsoUV",
             faces=side_polygon_indices,
             periods=(None, section_perimeter))
```

`metric_coordinates` maps vertex indices to `(u, v)` distances: for example, cumulative path length and cumulative cross-section perimeter. A closed ring can have a period on both axes. Periodic values must be in `[0, period)` and each face must span less than half a period. The helper splits wrap boundaries into corner UVs without splitting geometry. Caps and other surfaces need separate charts. Use `flip_v=True` only to correct a consistently reversed whole chart; mixed winding is a construction problem.

Invalid coordinates, ambiguous wraps and mirrored/degenerate UV triangles raise before any UV layer is changed. Positive triangle areas alone do not certify global non-overlap, stretch or adequate sampling. Tight bends, taper and variable cross-sections need particular inspection; keep a sound seam-based unwrap when it fits better.

Keep the mapping while building the geometry instead of reverse-engineering vertex order later. If modifiers create new topology, derive the evaluated mapping or unwrap that evaluated copy; do not apply source indices to different geometry. Preserve source-to-working correspondence and evaluated shading normals separately.

After all charts are ready, normalise relative density as appropriate, allocate enough space to important narrow details, and pack every included occurrence together once. Inspect the outline/checker at the intended lower resolution, run the complete native UV check, then bake the colour guide. The helper does not pack, validate the final atlas, export or submit to Marso.
