# Build geometry and charts together

For scripted structured parts, prefer [geometry_uv.py](../scripts/geometry_uv.py) when its supported surface matches the reference. It runs inside Blender through the existing control route. It is local geometry code, not an add-on command. Organic forms or complex topology still need edit operations on a quad cage; do not force them into these primitives.

Before expanding a family, choose its profile/sections, cap treatment and chart boundaries together. Model one representative, inspect its reference-matched silhouette and connections, and check its evaluated geometry and charts. Reuse the accepted recipe; edits to its topology, bevel or section invalidate that check. A different silhouette requires another design decision, not merely another scaled copy.

## Minimal API

Add this skill's `scripts` folder to Blender's Python path. Coordinates are metres in the object's local frame. Assign an asset Empty and placement explicitly. Leave `material` unset for a model going to Retexture; it exists for assets that keep their own materials.

```python
import geometry_uv as geo

# (height, radius) stations; both end rings get quad grid caps by default.
part = geo.revolve('Turned leg', [(0, .012), (.02, .018), (.30, .014), (.40, .02)], segments=16)
# A real point (cone, nib) may end on the axis when declared as a tip.
nib = geo.revolve('Nib', [(0, .006), (.01, .006), (.025, 0)], segments=16, tips=(False, True))
# Closed CCW section rings, corresponding vertices, no duplicated closing vertex.
part = geo.loft('Profiled housing', sections, caps=(True, True))
# Counterclockwise XY outline with an even point count, positive extrusion depth along Z.
part = geo.extrude('Plate', outline, .006)
part = geo.sweep('Curved tube', path, radii, segments=16, caps=(True, True))
# Closed loop without repeating its first point: piping, rims, hoops.
piping = geo.sweep('Seat piping', loop, .004, segments=8, closed=True)
# Cushions, mattresses, soft housings: every edge rounded, side band cut at the four corners.
cushion = geo.rounded_box('Seat cushion', (.6, .55, .12), .03, corner=.05, segments=3)
outline = geo.rounded_rectangle(.2, .14, .02, segments=3)  # even-count CCW outline for extrude or loft
```

- Every face is a quad except the triangles round a declared tip. Caps are quad grids, so a capped ring needs an even point count. An odd ring, or an outline too concave to split into convex quads, raises an error: add or move outline points rather than accepting another cap.
- `revolve` caps both ends unless told otherwise (`caps=(False, False)` for a horn open at both ends). Radial `segments` must be even. A zero radius is allowed only at an end listed in `tips`.
- All return separate editable mesh objects with `MarsoUV`. **The metric charts are intentionally unpacked**, may lie outside 0–1 and may overlap other parts. Preserve their relative scale; the shared atlas is packed afterwards across all parts. Do not independently normalise each component to fill a tile.
- `seams` lists the point indices round each ring (outline indices) where the side band is cut into charts. One seam gives one wrap-around strip. Cut long bands at their corners: a single strip round a large outline sets the scale of the whole atlas and leaves it mostly empty. `rounded_box` cuts at its four corners already.
- Chart boundaries are also marked as mesh seams. Profile bands use a common average perimeter to avoid shear on short radial steps. Strong radius variation (a horn) can still stretch; split such a band into deliberate panels and leave the stretch check to `marso-blender-uv` when installed.
- `loft` bridges closed section rings in order. Correspondence and winding are the caller's design responsibility. `closed=True` bridges the last ring back to the first and takes no caps. A panel with a hole is a closed loft of four rings: outer front, inner front, inner back, outer back.
- `sweep` transports circular section frames along the path. It rejects repeated or reversing paths but does not fillet sharp bends or detect collisions. A closed sweep spreads its frame twist evenly so the closing band matches. Use explicit loft sections for noncircular or twisted shapes. Inspect the bend and attachment clearance.
- End caps must be planar; concave simple outlines are supported, holes and self-intersections are not.
- `construction_faces` is a JSON mapping of `side`, `start`, `end` face IDs. Use it for justified contact-face exclusions **before topology changes**. Modifiers change evaluated IDs; re-establish the mapping instead of applying stale exclusions. The helpers never guess which faces are hidden.
- Bevel modifiers are not automatically chart-checked. Test one evaluated representative before repeating it. Where a bevel is part of a known profile, include it as profile stations so its strip stays continuous.
- Extrusion sides are flat-shaded by default; `smooth_sides=True` is appropriate for a deliberately rounded outline. Loft sides default to smooth; use `smooth_sides=False` for sharp section corners. Shading remains a visual decision.

## Panels with lettering, stripes or stamped relief

When creating a panel, retain its face set, physical right/up axes and the intended flat artwork area. Finish the silhouette, taper and relief before writing its UVs. Work at applied physical scale. For each corner on the flat field, subtract a common panel origin from its finished position; use the dot products with the perpendicular unit right and up vectors as U and V. This gives equal distances in both directions and straight rows even when the panel has a sloping outline. For a rear face, choose right/up as seen from outside. Keep continuous supplied print nets on their original sheet coordinates.

For a pressing, that projection is the starting chart; relaxing its ribs and returns, and packing, belong to `marso-blender-uv` when installed. Without it, report that the panel charts are unchecked. A cylinder or conical wrap instead develops around its circumference; projecting the entire object from the front would collapse its sides.

Build this into the component constructor and reuse it for parts with the same construction. One representative checker can settle an unfamiliar surface. Routine copies can reuse that evidence. Revisit only affected charts after a shape-changing bevel, taper, topology change or a visible defect; keep the final shared-domain overlap check.

## Representative check and handoff

The review pack shows each construction family at once: render it with `review_model.py` after building one representative, and fix its topology before repeating the part. When the `marso-blender-uv` skill is installed, its part check packs and measures a disposable copy of the representative while leaving the master untouched. Without it, leave the helper charts and their marked seams as they are, and report that the shared atlas is not unwrapped, packed or checked. Neither check passes the form, contact, symmetry or path-style gates.

Keep one useful neutral/oblique inspection and the short numerical result. Run additional views only for an unresolved feature. Do not repeat full export round trips or render galleries for every duplicate.

The review renders use Workbench with a neutral colour, so the parts need no materials. Fit attached plates, braces and straps to the evaluated receiving surface before repetition; an approximate bounding box does not establish contact on a curved body.

For a model going to Retexture, printed paint, labels and material colour regions belong in the texture brief, painted onto the existing surface. Do not add a duplicate conforming mesh solely to mark colour. A physical sticker, stitched panel or raised plate can justify geometry, but its thickness/contact and covered surfaces need deliberate treatment. Texture details cannot replace missing silhouette or volume.
