# Retexture UV acceptance

Retexture preparation must provide one verified 0-1 layout for each texture target, with unique non-mirrored coverage for all textured surfaces. Authoring extra UV layers is fine; identify the exact layer used by export and materials. Apply these requirements to the upload geometry, including evaluated modifiers and repeated parts, not just the unmodified source cage.

## Choose an unwrap

Use automatic projection for suitable hard-surface parts. Prefer seams following construction and surface flow for curved panels, tubes and swept geometry. Inspect stretching on bends: mapping a whole elbow by centreline length does not equalise density on its inner and outer radii.

Metric coordinates can establish relative scale before packing. Pack islands with a common scale factor, positive orientation and padding suitable for the output resolution and filtering. Cut disproportionately long strips or hollow rings only when the gain outweighs the new seams. Do not impose one island aspect ratio, segment length or fill percentage on every object.

If concave packing with arbitrary rotation stalls, try cardinal rotation with bounding-box packing on a working copy, then recheck the layout and density. The more expensive packing mode is not automatically the best workflow. Do not restart generation to resolve a local packing problem.

For curated UVs, use a separate single-mesh working target if the current assembly preparation would replace the layout. Preserve masters, connector frames and material-role information. Bake a colour-only reference without illumination; restore any temporarily changed metallic/transmission settings and links even on failure. The add-on's existing assembly bake already handles its own temporary shader changes.

## Exclude only permanently hidden surfaces

Record an exclusion reason and the object's allowed states. Internal faces of a sealed, fixed construction may be excluded from a texture working copy or use the add-on's collapsed-UV treatment. A cabinet interior, a door's back and a kit attachment end may become visible and normally need valid UV area.

Do not infer permanent invisibility from a single camera, hidden-in-viewport flags or one assembled pose. Inspect candidate hidden faces against all intended states. Marso's current visibility sampling is evidence for the current arrangement, not a proof for every possible arrangement. Preserve uncertain faces. Never delete required functional/collision geometry just to improve texture coverage.

## Audit

The optional [audit helper](../scripts/audit_uv.py) runs inside Blender. Call `audit_uv(objects, uv_name=..., excluded_faces=...)` on the actual mesh objects comprising one texture target. `excluded_faces` maps object names to polygon indices verified permanently hidden; omission excludes nothing. The helper does not determine visibility or modify data. Run on independent evaluated copies if modifiers change the upload geometry.

It reports negative UV winding (a mirrored-orientation diagnostic), zero-area triangles, out-of-tile coordinates, positive-area triangle overlaps and density. Touching island boundaries alone are not counted as overlaps. Geometry normals and negative object scale must also be checked: the winding diagnostic does not establish correct mesh orientation. Excluded faces are omitted from the area/overlap audit and counted separately, not silently accepted as textured faces.

Fix reported failures before calling the layout ready. Inspect seams, minimum island spacing, distortion and a checker in multiple views separately; the helper does not certify those. In particular, a clean overlap result does not prove sufficient padding.

For non-overlapping in-tile UVs with reasonably uniform density, estimated pixels/metre is `resolution * sqrt(UV_area / surface_area_m2)`. Report density as an estimate, not proof of uniformity. Use per-triangle minimum/maximum density to find severe stretching; investigate tiny triangles separately. Equal atlas resolution and fill across different surface areas do not mean equal density.

Keep test evidence separated: local UV preparation and add-on preflight can pass without proving that a cloud Retexture job will return good maps. Verify an actual generated result before claiming end-to-end success.
