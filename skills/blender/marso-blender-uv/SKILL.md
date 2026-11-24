---
name: marso-blender-uv
description: "Use when unwrapping, repairing or checking UVs on a Blender model (seams, stretch, texel density, one shared atlas), or preparing a modelled asset's UVs before Marso texturing."
license: Apache-2.0
---

# Unwrap an asset into one shared atlas

## Overview

This skill gives every visible part of an asset one shared 0-1 atlas on the `MarsoUV` layer: seams chosen by the agent, even texel density, low stretch and a well-filled tile. It renders review images (checker, UV layout, stretch heatmap) and records the metrics. It preserves geometry, hierarchy, pivots, part names, existing materials and other UV layers. Outside the automatic fallback it never adds materials, paints or bakes; it never starts a cloud job.

The add-on's assembly route lays its own Smart UV atlas (`MarsoAtlas`) over every part. That route is `prepare_assembly`, and Retexture also runs it on an unprepared multi-part asset. So after authoring, call neither on the asset root except through the [automatic fallback](#automatic-fallback-prepare_assembly): the authored atlas reaches Retexture through a single-mesh working copy made at the texturing stage.

Adjacent work belongs to siblings, each "when installed":

- **Modelling, topology and model approval:** `marso-blender-asset`. Without it, unwrap the model as given and report any form or topology defect you notice.
- **Retexture, PBR, colour guides and export:** `marso-blender-texture`. Without it, deliver the unwrapped asset and its review images, and say it is untextured.

UV work is local and reversible, so it may proceed while model approval is pending; the approval itself stays with the modelling stage.

Run the scripts inside Blender through the working control connection: add this skill's `scripts` folder to `sys.path`, then `import uv_atlas, review_uv`. The atlas layer is `MarsoUV` throughout; pass `uv_name` only to work on another layer.

- `scripts/uv_atlas.py`: the layer, `unwrap`, `pack`, `join_small_charts`, `report` and `check_part`, used on every run.
- `scripts/review_uv.py`: the review images, used on every run.
- `scripts/audit_uv.py` and `scripts/measure_uv_quality.py`: the overlap and spacing measurements `report` runs. Call them directly only for the diagnostics in [UV acceptance](references/uv-acceptance.md).

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| Unwrap a new or remodelled asset | [Prepare the parts](#prepare-the-parts), then [Author the atlas](#author-the-atlas) | nothing |
| Parts built with the modelling helpers | Unwrap along the seams they marked | nothing |
| Rings, bands or sweeps whose surface coordinates the builder knows | `scripts/parametric_uv.py` | [parametric charts](references/parametric-charts.md) |
| A failed check or a doubtful image | [Repair a failing atlas](#repair-a-failing-atlas) | [UV acceptance](references/uv-acceptance.md) |
| Check existing UVs without changing them | `uv_atlas.report`, then `review_uv.review` | nothing |
| Automatic preparation requested, or authored charts cannot pass | [Automatic fallback](#automatic-fallback-prepare_assembly) | nothing |
| An exported GLB reports extra charts or zero padding | `measure_uv_quality(..., match_split_vertices=True)` | [exported vertex splits](references/uv-acceptance.md#exported-vertex-splits) |

## Prepare the parts

1. Unwrap the accepted form. If the model still has major shape defects, return it to modelling and report them. Only an explicit request for a UV diagnostic on unfinished geometry overrides this.
2. List the parts with `uv_atlas.asset_meshes(root)`: every visible mesh with faces under the root. It raises on an empty selection and skips meshes hidden in the viewport or render, which `report` then lists as a failure. Unhide every part that belongs to the asset, and move hidden helpers out from under the root.
3. Give every occurrence its own mesh data. `ensure_layer` refuses linked duplicates, because they would share one set of texels.
4. Apply Mirror, Array and Solidify modifiers. Each copies its charts onto the same texels, which Retexture rejects. Record what was applied in the handoff.
5. Keep Bevel (2 or 4 segments), Weighted Normal and Simple Deform live; they keep the charts. Keep Subdivision live and set its UV Smooth to Keep Corners (`uv_smooth = 'PRESERVE_CORNERS'`). If a part still fails stretch with it live after reseaming (tight welts and rolls), apply that part's Subdivision, unwrap the result and record it.
6. Apply scale so every part has the same uniform world scale. `pack` evens density in mesh space and refuses mixed scales.
7. Check the evaluated geometry for non-finite coordinates, zero-area faces and slivers. A degenerate UV report often starts in collapsed geometry; fix the face, not the chart.
8. Keep every face in the atlas, including backs, undersides, interiors and surfaces revealed by movement. Record a permanently covered face in a fixed assembly, with its reason, for the texturing stage; never infer that from one camera.

Done when every part has single-user mesh data and the same uniform world scale, no Mirror, Array or Solidify modifier remains, and any Subdivision keeps corners.

## Author the atlas

1. **Mark seams.** Parts from the `geometry_uv` modelling helpers already carry seams at their chart boundaries. Mark the rest yourself: at construction breaks, less visible returns and sharp changes of curvature. Keep broad surfaces whole. Cut long perimeter bands at corners into panels (a wooden member whose grain must run unbroken stays one strip), and open rings and tubes along one deliberate seam with separate caps.
2. **Align manufactured panels.** On a face meant for lettering, stripes or a straight finish, keep the chart aligned to the panel's physical axes; give curved returns their own chart. After the report, check that small marks can be drawn: `uv_atlas.mark_pixels(result, part_name, size_m)` takes the step 7 report and gives the texture pixels across the narrowest stroke of the lettering or stripe. Under 4 pixels the mark blurs and under 2 it cannot be drawn. Pack again at 4096 and record why; at 4096, report the mark as too small for the atlas.
3. **Unwrap.** `uv_atlas.unwrap(parts)` unwraps along the marked seams with `MINIMUM_STRETCH`; use `method='ANGLE_BASED'` for organic forms. It reads subdivided positions when a Subdivision modifier is present. Re-unwrap helper parts too: their charts are a seam layout, and unwrapping along those seams cut a rounded box's stretch from 2.3 to 1.0.
4. **Check one representative.** Before repeating a new construction family, run `uv_atlas.check_part(master)` once. It packs and measures a disposable copy and leaves the master unchanged.
5. **Pack.** `uv_atlas.pack(parts, resolution=2048, padding_px=8)` evens texel density across all parts and packs every chart into the tile. Use the resolution the asset will be textured at: the size the brief names, else 2048. Go to 4096 only for a reason you record, such as a mark too small at 2048. `pack` records the resolution and padding on every part, so later measurements use the same size. It packs by bounding box, then by concave outline, which nests small charts in the gaps round discs and curves, and keeps the fuller layout (seconds on a typical prop; bounding box only above 200,000 faces).
6. **Join narrow charts.** `uv_atlas.join_small_charts(parts)` joins every chart narrower than 1/128 of the tile (16 px at 2048) to its neighbour and packs again at the size `pack` recorded. Strips that thin vanish at lower texture resolutions and cause trouble in game engines. It undoes any join that stretches past the limit, folds or would close a surface. Run it after the last `pack`: packing again rescales every chart and can make more of them narrow. Its result gives `narrow_left`. Run it again while that count falls; report the charts left when a run joins none.
7. **Measure.** `uv_atlas.report(root)` measures the evaluated meshes at the resolution and padding `pack` recorded. Padding in pixels halves when the same layout is measured at half the size, so never judge a layout at a size other than the one it will be textured at. `worst_patch` names the most stretched face of the asset and `stretched_area_share` the share of the surface stretched past 1.5: a passing p95 can hide one bad patch on a visible face. For overlaps it calls the add-on's internal UV validator (`core.uv_validation.first_conflict`, inspected in Marso 1.20.0), the check Retexture's export runs. When that function is missing it uses the stricter bundled audit and names it in `overlap.validator`.

The report passes when each part's area-weighted stretch (95th percentile) is at most 2.5, density spread across parts is at most 1.3, and fill is at least 0.65. It also needs no triangle outside the tile, no overlap, padding of at least half the requested pixels and no chart narrower than 1/128 of the tile. A part that is one chart is exempt and listed in `narrow_charts.whole_parts`. Above 150,000 evaluated faces padding is measured on the meshes before modifiers, as `padding.measured_on` says.

Done when `report(...)["passed"]` is true on the final revision.

## Repair a failing atlas

Read each entry of `report["failures"]` and fix its cause; repacking alone never repairs stretch.

| Failure | Repair |
| --- | --- |
| Stretch on a part | Locate the region from `worst_polygons` (evaluated faces, not source indices) and the heatmap. Add a seam there, or unwrap the matching source faces with `faces=` and `ANGLE_BASED`. |
| Density spread | Pack all parts together again; check for a part left at a different object scale. |
| Fill | Cut long curved bands (bent rails, rings) at natural breaks so their charts lie straighter, then pack again. Do not force a curved surface into a rectangle. |
| Overlap | Look for a copy modifier, a linked duplicate or a folded chart; unwrap that part again along its seams. |
| Outside the tile or padding | Pack again; raise `padding_px` or merge tiny charts at the same resolution. |
| Narrow charts | Run `join_small_charts`. Charts it cannot join usually sit on tiny closed parts such as relief ribs: return them to modelling to merge into their surface, or leave the relief to texture. |
| Degenerate or missing | Repair the collapsed face, or unwrap the part that has no `MarsoUV` layer. |

Keep the last passing layout before each comparison. Stop chasing fill once the checks pass and the images read cleanly. After three repair rounds on one failure, use the [automatic fallback](#automatic-fallback-prepare_assembly) if it suits the asset, or report the failure. With nobody to answer, take the fallback, record why, and say in the handoff that `reset_look` on the root restores the earlier materials and UV maps. Read [UV acceptance](references/uv-acceptance.md) for narrow strips, panel alignment, hidden faces and packing that stalls.

Done when the report passes again, or the remaining failure is reported with the part and the metric.

## Render and read the review images

`review_uv.review(root, out_dir)` writes `checker.png` (a plain black-and-white checker on two opposite views), `uv.png` (the whole tile, one tint per part), `stretch.png`, `uv-metrics.json` and `worst-patch.png`, the checker seen straight on at the report's `worst_patch`. The stretch heatmap is green when undistorted, yellow at 1.5, orange at 2.5 and red from 4; magenta marks broken UVs. It refuses to overwrite earlier files unless `overwrite=True`.

Open all four images. In `worst-patch.png` the view is square to the face, so squares that are not square there are UV stretch, not perspective: reseam or unwrap that region when it is on a visible surface. The checker squares must stay square and similar in size across every part, with straight rows on manufactured panels. The heatmap must show no red or magenta patch on a visible surface. The layout must show no slivers or wasted tile, and narrow visible strips need several pixels across at the chosen resolution.

Done when the report passes and the four images, opened on the final revision, show none of those faults.

## Automatic fallback: prepare_assembly

Use the add-on's automatic one-atlas route only when the user asks for automatic preparation or authored charts cannot pass after the repair rounds. Record the choice and why.

Through an authorised Blender Python tool, find the enabled Marso module in `bpy.context.preferences.addons` (it may be `bl_ext.<repository>.marso`; do not assume `import marso`). Import its `bridge.commands`, read `all_commands()` and the command's `describe()` schema, then call `execute(name, params)`.

1. Call `prepare_assembly` with `object_name` (the asset root), `size` (2048 or 4096) and `bake_colours: false`, so modelling colours are not kept as a look. It returns a `job_id` at once: end that Python call and check the job with `get_job` in a later call, never with `wait_job` inside Blender, which blocks the thread the job needs.
2. It adds a Smart UV `MarsoAtlas` layer to every part, collapses faces it finds buried inside other parts and gives every part one shared material.
3. Measure it with `uv_atlas.report(root, uv_name='MarsoAtlas', resolution=<size>)` and render its review images. Collapsed buried faces report as degenerate triangles, a degenerate `overlap` entry and a padding failure. Read those as that route's design and judge the remaining entries.

Done when the job has finished and the handoff names the fallback and its measured results.

## Hand off

Report in one short handoff: the layer (`MarsoUV`, or `MarsoAtlas` on the fallback), resolution and padding, the report's fill, density spread and worst stretch, and the review image paths. Add the modifiers applied, any recorded covered faces, and anything unresolved. On the authored route, tell the texturing stage to submit `MarsoUV` through a single-mesh working copy, not the assembly route. On the fallback, say the asset is prepared and Retexture on the root uses `MarsoAtlas`. Do not call the asset textured or ready for simulation. With `marso-blender-asset` installed, its finish check runs `report` again and needs the review image folder as `uv_dir`; a failing atlas blocks that handoff.

Done when the handoff names the layer, the metrics and the review images.

## Worked example: unwrap a medium-poly dining chair

1. The modelling stage hands over `Chair`: legs and slats from `loft`, a `rounded_box` seat with a live Subdivision, rails with a Mirror modifier, and Bevel modifiers at 2 segments.
2. `asset_meshes(root)` lists 14 parts. The two front legs share mesh data, so the second is made single-user. The rails' Mirror modifier is applied and recorded. The seat's Subdivision UV Smooth is set to Keep Corners.
3. The helper parts already carry seams. The apron rails, made with edit operations, get seams along their lower inside edges. `unwrap(parts)`, `pack(parts, resolution=2048, padding_px=8)`, then `join_small_charts(parts)` joins the rails' thin end strips to their faces.
4. `report(root)` fails: fill 0.58 and the back rail's stretch is 3.1. The back rail's curved band is cut into two panels at its centre and unwrapped with `faces=`. After repacking, fill is 0.71, spread 1.06 and worst stretch 1.8.
5. `review_uv.review(root, "renders/uv")` writes the images. The checker on the seat front bends; a seam along the seat's lower edge is moved under the front roll. The seat is unwrapped again, all parts are packed, `report` passes again, and the images are rendered again with `overwrite=True`.
6. The handoff gives `MarsoUV` at 2048 with 8 px padding, the metrics, the image paths and the applied Mirror. Texturing should use a single-mesh working copy.

## Common mistakes

- Calling `prepare_assembly` or Retexture on the root after authoring: hand the atlas to the texturing stage's single-mesh working copy.
- Leaving Mirror, Array or Solidify live: apply them before the final unwrap so each copy gets its own texels.
- Keeping the helpers' charts as final: unwrap along their seams, then pack and report.
- Repacking or rescaling to cure stretch: add a seam or unwrap the stretched part again.
- Packing parts at different object scales: apply scale first.
- Leaving bevel strips and slot walls as charts of their own: join them to the face beside them.
- Passing the numbers without opening the images: read the checker, worst patch, layout and heatmap on the final revision.
- Adding materials or a checker material to the delivered parts: the review images use temporary copies; hand over geometry and UVs only.
