# Low-, medium- and high-poly paths

Every modelled asset follows one path. A path sets the polygon budget **and** the modelling style; matching a triangle count in the wrong style does not satisfy it. Quality is not a path: all three paths must match the reference, connect their parts credibly and pass the gates below.

## Resolve the path

Use the first signal that applies, then state the path and the deciding signal before building:

1. **Explicit specification.** A named path, triangle budget, target platform or use: "low-poly", "under 5k tris", "mobile game", "VR", "Unity/Unreal game asset" (low or medium), "film close-up", "hero", "product render" (high), "background dressing" (low).
2. **Existing scene.** When adding to a scene, measure the evaluated triangle counts and modelling style of comparable assets, read any recorded scene budget, and estimate the camera's closest distance to the new asset. Match the scene: a faceted stylised scene implies low-poly; a close film camera on the asset implies high-poly; a real-time viewport setup with game-scale assets implies low or medium.
3. **Workflow handoff.** A path or budget passed down by the scene or entry workflow for this master.
4. **Default.** Medium-poly, stated as an assumption.

A reference photo shows the design, not the path. Ask only when strong signals conflict, such as an explicit high-poly request inside a strict low-poly scene budget. With nobody to answer, keep within the strict budget, take the highest path it allows, and record the conflict in `marso_path_basis` and the handoff. Otherwise decide, state the decision and keep it; never silently downgrade after a weak result. Different masters in one scene may take different paths.

Record the decision on the asset root as custom properties `marso_poly_path` (`low`, `medium` or `high`) and `marso_path_basis` (one short phrase), so later stages and reviewers can read it.

## Indicative budgets

Evaluated triangles for the whole asset at its render settings. Case or user budgets override these. The finish check reads the hand-held row when the asset's largest dimension is under 0.5 m, else the furniture row.

| Asset size | Low | Medium | High |
| --- | --- | --- | --- |
| Hand-held (under ~0.5 m: tools, weapons, kitchenware) | 0.4k–10k | 6k–80k | 100k+ |
| Furniture and boards (~0.5–2.5 m) | 0.5k–18k | 8k–180k | 150k+ |

The low and medium ranges overlap, so a count inside the overlap does not name the path. When a stated triangle budget or a scene's counts fall in the overlap, take the path from the other signals in [Resolve the path](#resolve-the-path), else medium, and keep the stated budget as the limit. The recorded path then sets the forms and edge treatment. At 9k a low-poly asset has hard edges and only the parts the silhouette shows; a medium-poly asset has real bevels and secondary forms. A simple piece such as a dining chair sits in the lower half of its range; an upholstered sofa can use the top.

Spend triangles where silhouette and highlights need them. A dense mesh with a weak form fails; so does a low-poly mesh made by decimating a dense one without re-establishing clean silhouette edges.

The top of the range is a limit. The bottom is a cue, not a target: a count below it usually means the path's forms are missing, so add the forms the style table lists. A high-poly chair, for example, gains joinery shoulders, profiled rails, a shaped crest, a seat welt and stitching seams. Never fill the range with density. The [finish check](../scripts/finish_check.py) blocks on a count below the range: build each form the style table lists for the path, then run it again. A listed form with no part is built, not reported as missing. A model that stays below the range after two repairs is reported as partial, with the count. A count reached by density that does not shape anything fails the density check below, whatever the budget allows.

### Density check

`review_model.review` judges each part it can un-subdivide when the root carries `marso_poly_path`. It removes every other edge loop from a copy of the evaluated mesh and measures how far the surface moves. If 90% of the vertices move less than the path's tolerance, the part is `over_dense` in `topology.json`: half its faces add no visible shape. A part whose `density.judged` is false (fewer than 16 faces, or topology that does not un-subdivide) has no verdict. Inspect it in `wire.png` for loops that shape nothing and name it in the handoff as not judged.

| Path | Tolerance (fraction of the part's diagonal) | On a 60 cm cushion |
| --- | --- | --- |
| Low | 0.5% | 4 mm |
| Medium | 0.15% | 1.2 mm |
| High | 0.05% | 0.4 mm |

Fix an over-dense part at its source: lower its Subdivision level, remove evenly spaced loops, or reduce the segment counts of its profiles. Keep the loops that do move the surface (support loops, curvature samples, silhouette edges). On a soft good, Subdivision level 1 on a shaped cage usually holds the form at medium; a second level needs the check to agree. If a part is still flagged at level 1, its cage is too even: a cushion cage needs loops near its rolled edges and only a few spans across its flat or gently crowned top. High-poly density goes into tertiary forms at the hero distance, never into another uniform subdivision level.

## Modelling style per path

| | Low-poly | Medium-poly | High-poly |
| --- | --- | --- | --- |
| Purpose | Real-time and mobile, distant dressing, stylised scenes | General real-time and offline use; mid-distance renders | Close-up film, hero and product shots |
| Separate parts | Structural parts the silhouette shows; no fasteners, bearings or washers | Plus visible hardware as simple parts | All visible hardware, with real detail |
| Geometry carries | Silhouette and major volumes | Primary and secondary forms: recesses, ribs, rails, panel steps | Primary, secondary and visible tertiary forms: serrations, fillets, stitching seams, grip texture where it breaks the silhouette |
| Texture/normal maps carry | Secondary and fine detail | Fine detail: stippling, knurling, engraving, grain, print | Micro detail only |
| Edges | Hard edges by sharp marks or Smooth by Angle; no bevel strips except where the silhouette needs one | Real bevels (2 or 4 segments) on every visible hard edge, Weighted Normal modifier (keep sharp) | Subdivision with support loops or creases controlling each radius; no faceting at close view |
| Topology | Fewest quads that hold the silhouette; no hidden interior faces | Quads with loops placed for the bevels; openings built as ring topology | Quad subdivision cage; holes and recesses by planned edge flow; soft forms shaped on the cage |
| Curves | Sampled just enough for the silhouette at intended distance | Smooth at mid distance | Smooth highlights at the closest view |

### Topology (every path)

Model every face as a quad unless the user asks for another topology. The one exception is a real pointed tip, such as a cone point, pen nib or blade tip: its ring of triangles is allowed. Everything else fails the topology gate:

- triangles anywhere away from a pointed tip;
- n-gons, including single-face caps;
- vertices where seven or more edges meet away from a tip, such as the pole of a triangle fan.

`topology.json` counts a fan as a tip (`tip_tris`) only when its faces bend more than 25 degrees from their mean normal. A blunt point counts as `tris`, so sharpen it or close it with a small-ring cap.

Close every end outline with a quad grid. The `geometry_uv` helpers grid-fill caps and raise an error for an odd point count or an outline they cannot fill. Add or move outline points rather than accepting another cap. End a revolved profile at a small ring with a quad cap, never at a pole on the axis. Blender's default cylinder, cone and UV sphere break this rule (n-gon caps, triangle fans at poles); use the helpers, or a cube with Subdivision and Cast for a sphere.

Modifiers can break quads too. A Bevel modifier keeps box corners all quads only with an even segment count (2 or 4) and the default vertex mesh; one or three segments leave corner triangles. Subdivision, Mirror, Solidify and Weighted Normal keep quads from a quad cage. Judge the evaluated mesh, not the cage.

Every face must serve the shape. Remove loops and segments that do not change the silhouette, a highlight, a bevel radius or movement; a flat panel needs no more faces than its outline and cap grid. Keep the faces that hold a shape: curvature samples, support loops and silhouette edges are not waste. A higher path adds faces where it adds detail (fillets, seams, tertiary forms), never by subdividing the whole asset uniformly or raising every segment count.

### Low-poly method

Block the silhouette first, then delete everything the silhouette and major shading do not need. Small hardware (nuts, bolts, washers, bearings, screw heads) is texture, not geometry, unless it changes the silhouette at the intended distance; keep the structural parts the silhouette shows, not the fasteners between them. Keep openings the silhouette shows through (a trigger guard, chair-back gaps, truck hangers) as real geometry; Marso does not generate transparency. Once the form passes, join each fixed sub-assembly into one mesh (a truck's baseplate, kingpin and bushings; a chair's frame rails), so the asset is roughly one mesh per moving part or distinct material. Keep parts that move in real use separate even on a static prop (a slide and trigger, wheels, a lid), so they can be animated and their contacts checked; never join the whole asset into one mesh. Mark hard edges deliberately and check the shading reads correctly without a bevel. Texture will carry printed and fine relief detail, so leave clean, well-proportioned surfaces for it.

### Medium-poly method

Build each part from sections or a shaped cage, not a constant-depth profile: where the reference changes width, add stations and taper or round them. Bevel every visible hard edge so it catches a highlight, using a Bevel modifier with 2 or 4 segments limited by angle or weight, followed by Weighted Normal. Build recesses and ports as ring topology (inset loops, or a closed loft traced round the opening), then inspect the evaluated bevel for pinching. Leave dense surface patterns to texture.

### High-poly method

Start from the medium-poly volumes, then rebuild each part as a subdivision cage: quads, edge loops following the form, support loops or creases set to the real physical radius of each edge. Model the fillets where surfaces meet instead of relying on separate pieces butted together. Add tertiary detail that would read at the closest view as geometry: serration ridges with depth, grip panels with modelled relief, upholstery seams and piping, wheel hub spokes. Shape cushions, folds and organic transitions on the quad cage with edit operations: soft goods need crown, edge roll and seam tension, not plain rounded boxes. Inspect the evaluated surface under a broad reflective light for pinching, ripples and lumpy highlights.

## Shared gates (every path)

These are agent checks, not user approval steps. An approval or review waiver only removes the wait for a person; it never waives these checks. Each gate needs images you actually opened and inspected. Rendering a file and continuing in the same script is not inspection.

1. **Primary form.** Compare a neutral oblique and the reference at a similar angle: silhouette, proportions, section widths, negative spaces. Add a top or end view to rule out slab-like depth.
2. **Construction and contact.** Assembled parts touch, nest or interlock as the real object does: a slide riding on frame rails, a truck baseplate bolted flat to the deck, a chair rail entering its leg. No floating parts, no visible gaps beyond a deliberate seam, no unintended interpenetration. Inspect each consequential interface in a close view and measure it with [check_contacts.py](../scripts/check_contacts.py). Parenting, names and bounding-box overlap do not prove contact. One touching point is not a joint either: a handle, strap, rail or brace lands on a surface at every end, so look at each end in the close view.
3. **Symmetry and handedness.** Before mirroring, classify parts as symmetric, mirrored pairs, or one-sided (a slide stop on one side, a valve's direction arrow, a skateboard's grip graphic). Mirror only the symmetric and paired parts, and check the opposite side in its own view. `check_contacts.mirror_deviation` measures how far a supposedly symmetric part departs from its mirror.
4. **Path style and topology.** Evaluated triangle count is within the budget's limit (a lower count only as [the budget note](#indicative-budgets) allows), and the edge, topology and detail treatment match the path table above. Render the review pack with [review_model.py](../scripts/review_model.py) and open its wireframe. The topology counts must show no triangles off a tip, no n-gons and no 7+ poles. No part may be `over_dense` in the [density check](#density-check). For low-poly, list the parts and remove any that only a close view would show. For high-poly, render a close view at the hero distance and list the tertiary details modelled on each visible part; if it would read the same as a medium-poly build, the path is not met, however dense the subdivision.

Fix the largest failure first and inspect the same views again. A failed gate is repaired. Report the asset as partial only when `finish_check.check` returns `partial`, and do not hand it to texturing as finished.

Keep one short checkpoint note per gate: revision, views inspected, findings and the repair or proceed decision.

## Texture handoff per path

The texturing stage chooses the upload level from `marso_poly_path` (`marso-blender-texture` when installed). Without it, report the path and the evaluated triangle count in the handoff.
