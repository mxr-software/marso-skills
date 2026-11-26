---
name: marso-blender-asset
description: "Use when modelling or refining an editable Blender asset (props, furniture, hard-surface, soft goods) from a brief, photo or scene, on a low-, medium- or high-poly path."
license: Apache-2.0
---

# Build an asset in Blender

## Overview

This skill builds editable, real-scale geometry in Blender: separate named parts under one asset root, every face a quad, on a recorded low-, medium- or high-poly path. It preserves the user's scene, units and accepted work. It never adds materials, material slots or Principled shaders to a model going to Marso: Retexture paints the bare model: the add-on adds a blank-textured material when it prepares the upload and wires the returned maps into it. Before cloud Retexture or PBR of new or remodelled geometry, show the review pack and wait for model approval or an explicit waiver ([Hand off](#hand-off)).

Honour explicit model-versus-generate intent. For an ambiguous request, structured, articulated and modular forms favour modelling; organic or complex forms may favour generation through the `marso` entry skill when installed. Without it, model the asset and report that generation was not offered. Neither route guarantees quality.

Adjacent work belongs to siblings, each "when installed":

- **References and shape comparison:** `marso-blender-reference`. Without it, see design step 3.
- **UVs and the shared atlas:** `marso-blender-uv`. Without it, leave the helpers' own charts, list the parts with no `MarsoUV` layer, and report that the shared atlas is not packed.
- **Retexture and PBR:** `marso-blender-texture`. Without it, deliver the untextured model and say so.
- **Baked colour guide or texture-ready export:** `marso-blender-texture` as well; a colour render is not a baked guide.
- **Mating component families:** `marso-blender-kit`. One kit collection is not one texture target. Without it, build each component as a part of this asset.
- **Blender control missing:** `marso-blender-setup`. Without it, report the missing connection; never claim an unexecuted script built an asset.

Model through the working Blender control connection (the Blender MCP tools), using Blender Python. Inspect the actual session, units and existing work first.

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| New asset from a brief or photo | [Choose the path and design](#choose-the-path-and-design), then [Build with quads](#build-with-quads) | [poly paths](references/poly-paths.md), all of it |
| A specific shape or part (leg, cushion, opening, housing, moulded body), furniture sizes | Use its recipe | [shape recipes](references/shape-recipes.md) |
| Bottle, jar, can, cup, tub or anything with a lid | Build the vessel, wall and closure | [containers and closures](references/containers.md) |
| Carton, box, sleeve, bag or pouch | Model the flat sheet, then fold it | [folded-sheet packaging](references/folded-sheet.md) |
| Scripted structured parts | `scripts/geometry_uv.py` helpers | [construction helpers](references/construction-helpers.md) |
| Unfamiliar topology, form repair, scene masters | [Pass the gates](#pass-the-gates-and-render-the-review-pack) | [construction and quality](references/construction.md) |
| Show the model for review or approval | `scripts/review_model.py` | nothing |
| Measure contacts, floating parts, symmetry | `scripts/check_contacts.py` | nothing |
| Decide whether the asset is finished | [Finish check](#finish-check) | nothing |
| Reference images, shape comparison | `marso-blender-reference` when installed | nothing |
| UVs, atlas, checker | `marso-blender-uv` when installed | nothing |
| Retexture, PBR, appearance | `marso-blender-texture` when installed | nothing |

## Choose the path and design

1. Resolve the path from the user's specification, the existing scene or the workflow handoff, defaulting to medium. Read all of [poly paths](references/poly-paths.md) for the rule, budgets, each path's modelling style and the gates. A path sets budget and style, never a lower quality bar.
2. Record the path on the asset root as `marso_poly_path` (`low`, `medium` or `high`) and `marso_path_basis` (one short phrase).
3. For a realistic object, get the reference set with `marso-blender-reference` when installed, before scripting finished geometry: the primary design, its landmark proportions, and later the comparisons. Without it, take landmarks from a supplied photo, or model from the brief and record that no reference was checked.
4. A generic brief stays generic: combine the category's common features and drop marks and logos, but keep the reference's proportions. Ignore watermarks, captions and background objects in any image. Establish scale, material regions (as notes for the texture brief), movement and closest intended view.
5. Obtain another view only for a consequential uncertainty. State reasonable assumptions; ask only when the answer materially changes the result. With nobody to answer, take the assumption and record it for the handoff.
6. Keep a compact working record (path, reference, landmarks, scale, root and parts, current revision, gate results, unresolved issues) instead of a separate planning dossier.

Done when the root carries `marso_poly_path` and `marso_path_basis`, and the working record lists the reference, its landmarks, scale, closest view and inferred features.

## Build with quads

Build with the `geometry_uv` helpers and scripted edit operations on quad meshes. Modifiers are allowed and stay live: Mirror, Bevel (2 or 4 segments), Subdivision, Cast, Solidify, Weighted Normal, Array and Simple Deform. Judge every result on the evaluated mesh. Mirror, Array and Solidify copy each chart onto the same texels, so they are applied once the form is accepted, before the final unwrap. Do not use Booleans, cloth simulation, sculpting or automatic remeshing; build openings as ring topology and soft forms on a quad cage instead ([shape recipes](references/shape-recipes.md)).

- **Every face is a quad.** The one exception is the ring of triangles round a real pointed tip (a cone point, nib or blade tip). Triangles anywhere else, n-gons and vertices where seven or more edges meet fail ([topology](references/poly-paths.md#topology-every-path)).
- **Every face serves the shape.** Use as few faces as hold the silhouette, highlights and bevels; add faces only where they add detail. Faces that hold a shape (curvature samples, support loops, silhouette edges) are not waste. The [density check](references/poly-paths.md#density-check) flags a part as `over_dense` when halving its loops barely moves its surface. It is a gate, not advice: rebuild the part until it passes, never hand it off flagged. Spend loops at rolls, edges and silhouettes, not across flat spans.
- **Continuous members stay continuous.** A leg that rises into an arm post or back post is one part built through the joint, not two stacked pieces with mismatched sections. A rail ends inside or flush with the member it meets, never past its face.
- **Close ends with quad grids.** End a revolved profile at a small ring with a quad cap, never at a pole. Give capped outlines an even point count. The helpers raise an error otherwise; add or move outline points rather than accepting another cap.
- **Avoid Blender's default cylinder, cone and UV sphere.** They carry n-gon caps or triangle fans; the [shape recipes](references/shape-recipes.md#instead-of-blender-primitives) give the quad replacements.
- **Build geometry and charts together.** The helpers write metric charts on `MarsoUV` and cut the side bands at their `seams`. For a manufactured panel, carry its right and up directions and face groups through the build ([panel recipe](references/construction-helpers.md#panels-with-lettering-stripes-or-stamped-relief)).
- **Model both surfaces** and the joining edge wherever both sides can be seen. For a thin two-sided part, keep the main faces continuous and put seams along its perimeter.
- **Keep overhanging fittings identifiable** in the editable model so the texture stage can expose the surfaces behind them.

Use one rerunnable build script or the existing working session, with named components and parameters. Keep building and final preparation as separate stages so inspection can change the result. Amend the affected component rather than cloning the whole script for each repair. Build and review one representative of each construction family before repeating it. Batch independent local operations between inspection points; do not launch Blender separately for every getter or report.

Done when `topology.json` holds `totals.density` for the recorded path and shows no triangles off a tip, no n-gons, no 7+ poles and no `over_dense` part on the evaluated mesh, and the handoff names every part whose `density.judged` is false. Density is judged only when `review` is given the root that carries `marso_poly_path`.

## Pass the gates and render the review pack

The four shared gates block every path: primary form, construction and contact, symmetry and handedness, and path style with topology. A review waiver removes the wait for a person, never these checks. See [shared gates](references/poly-paths.md#shared-gates-every-path) for each gate's evidence.

1. Inspect the images you render: a neutral oblique against the reference, a top or end view for depth, the opposite side, and close views of each consequential interface. With `marso-blender-reference` installed, compare the model with each reference after the blockout and again here. Fix the mismatch it names first, and repeat until its measured gate passes or its stop rule ends the rounds. One failing comparison never ends them.
2. Measure contacts and floating parts with [check_contacts.py](scripts/check_contacts.py); `mirror_deviation` measures a supposedly symmetric part. Parenting, names and bounding-box overlap do not prove contact.
3. Render the review pack with [review_model.py](scripts/review_model.py): `review(root, out_dir, joints=pairs)` writes `sheet.png`, a contact sheet of the clay and wire views. It also writes full-size `clay.png` (two opposite neutral-clay views), `gloss.png` (the same views with a glossy surface) and `wire.png` (the evaluated mesh's edges over clay). `topology.json` holds the counts and density verdicts. `pairs` lists the structural part-name pairs that meet (legs to rails and seat, posts to arms); each gets a close clay view in `joints.png`. It refuses to overwrite earlier files unless `overwrite=True`. Once the UVs are packed, the [finish check](#finish-check) with `render=True` renders the same pack and the UV images in one call, and only when the asset changed.
4. Open `clay.png`, `gloss.png`, `wire.png` and `joints.png`, or every image a finish check lists in `rendered`. Each joint must read as built: matching sections where a member continues, no collar, step or protruding rail end the design does not have. In `gloss.png`, follow the highlights: a highlight that wobbles, breaks into facets or stops at a seam marks a surface to repair, even where the clay looks smooth. Fix the largest failure first and render the same views again.
5. A failed gate is repaired, not reported. A measured failure that names a part always has a repair: make it and measure again. The [finish check](#finish-check) measures every gate again and releases a failure only after two repairs.

A recognisable primitive, a high part count, parenting or a valid atlas is not accepted form. Keep one short note per gate: revision, views inspected, findings and the repair or proceed decision. Keep accepted checkpoints, not a gallery after every operation. Stop when the path's style and the gates are met; never lower them to meet a time target, and do not polish a minor fitting while the overall form is weak.

Done when all four gates pass on the latest revision and its clay, gloss, wireframe and joint images have been opened.

## Preserve the asset

- Keep changes scoped to the asset and save recoverably before substantial edits. Keep rebuilds distinct from earlier versions.
- Use real dimensions, a deliberate asset anchor and suitable pivots. Export independent copies relative to the anchor; do not move the user's scene to the world origin or change the scene unit scale to fix an object.
- Keep independently reusable or moving parts separate under an entity Empty. Supported objects must not inherit mesh-only scaling. Preserve intentional rigs inside the group.
- Retain useful existing UVs, existing material assignments and accepted corner normals. Do not add duplicate surfaces just to mark colour.
- Decide exposed interiors and fixed covered contacts from intended use, not from one camera.
- Model each distinct scene-object master in isolation before repeating it. Same-shape finish variants belong to the texture workflow.

## Finish check

The agent does not decide when the asset is finished; [finish_check.py](scripts/finish_check.py) does. Run it after the gates and the UV stage, before any handoff, once per repair round:

```python
result = finish_check.check(root, "renders/finish", review_dir="renders/review", uv_dir="renders/uv",
                            joints=pairs, render=True)
```

One call measures the recorded path, each reference comparison, contacts, topology, density, the triangle budget and the shared atlas. With `render=True` it then renders each review pack that no longer shows the asset, checks both folders and writes `finish.json`. The comparison and atlas are measured when those sibling skills are installed; a missing sibling is listed in `notes`.

- A review pack is stale when the geometry changed after it was rendered; the UV pack is also stale when the UVs changed. `render=True` renders only stale packs and lists each image it wrote in `rendered`, so a call on an unchanged asset renders nothing.
- Open every image in `rendered` before the next call, as in [step 4 of the gates](#pass-the-gates-and-render-the-review-pack). Without `render=True`, a stale pack blocks as `review:stale` or `uv:review`.
- The check keeps each part's results on the root and measures only the parts that changed. A kept result is used only when the part's change mark matches.
- `render=True` leaves a folder alone if it holds review files those scripts did not stamp, and the blocker stays: pass an empty folder. It never runs `compare` or `match_view`, so compare again yourself after an outline change.

1. On status `repair`, fix the first entry of `blockers` as its `repair` says, then run the check again. Do not write the handoff yet.
2. A blocker still measured after two repairs moves to `partial`. A step never done (no path, comparison, atlas or review pack) is never released.
3. A count below the budget range means the model is too simple for its path: build the forms the path lists and run the check again. `budget=(low, high)` replaces the range only with figures the brief states.
4. For a stylised or invented object with no reference, pass `no_reference="<reason>"`.
5. With nobody watching there is no time limit to save: keep repairing until the status changes.

Done when the last call returned `pass` or `partial`, the asset has not changed since, and every image the calls listed in `rendered` has been opened.

## Hand off

1. Hand a new model to Marso as geometry and UVs only. Prepare the shared atlas with `marso-blender-uv` when installed, before Retexture.
2. Before cloud Retexture or PBR of new or substantially remodelled geometry, show the review pack, state the path, dimensions and remaining defects, and wait for model approval. Respect an explicit waiver or an approval of unchanged geometry; UV work that preserves the shape does not invalidate it.
3. With nobody to answer and no waiver, stop after the review pack and report the model as awaiting approval. Local reversible work, such as UV preparation, may continue meanwhile. A request for a finished asset is not approval of an unseen model.
4. Geometry-only work needs no approval for an unrequested texture stage; it ends with the editable asset and any requested export.
5. Report in one short handoff: path and basis, root, dimensions, evaluated triangle count (`totals.evaluated.triangles` in `topology.json`), inferred features and assumptions, the review pack location, output files and unresolved limitations. Give the finish check's status, every entry of its `partial` list as a remaining defect, and its `notes`. A `partial` asset is not handed to texturing as finished. Keep form acceptance, UV readiness and approval distinct. Do not label untextured geometry as finished PBR or simulation-ready. Add no extra turnaround, gallery or technical report unless requested or needed to explain a defect.

Done when the handoff lists the review pack, the finish check's status, and either the approval, the waiver, or "awaiting approval".

## Worked example: medium-poly dining chair from a photo

1. The user supplies one photo of a dining chair and asks for a model to texture later. No path is named, so the path is medium ("unspecified; default"), recorded on the root `Chair` as `marso_poly_path="medium"`.
2. Landmarks from the photo: seat height 0.46 m, overall height 0.86 m, tapered rear legs continuing into curved back posts, three back slats. The far-side stretcher is inferred and recorded.
3. Legs are tapered `loft` parts from four-point rings; the rear legs carry stations up the back curve. Aprons and stretchers are `extrude` rails entering the legs. The seat is a `rounded_box` dished with `crown(seat, -0.006)`. The slats are lofts along the back curve. Bevel modifiers use 2 segments, not 3, so the corners stay quads.
4. A first attempt at a turned finial with Blender's UV sphere shows `poles_7plus: 2` and 32 triangles in `topology.json`. It is rebuilt as `revolve` with small-ring caps, and the counts return to zero.
5. `check_contacts.py` reports the back stretcher 4 mm short of the left leg; the rail is lengthened into the leg and the contact rechecked.
6. `review_model.review(root, "renders/review", joints=[("Leg.RL", "Apron.Back"), ("Leg.FL", "Apron.Front")])` writes the pack with `joints.png`. The wireframe shows dense loops on the flat seat underside; they are removed because they shape nothing.
7. UV preparation goes to `marso-blender-uv`. Then `finish_check.check(root, "renders/finish", review_dir="renders/review", uv_dir="renders/uv", joints=pairs, render=True)` returns `pass`. The seat loops were removed after step 6, so the model pack was stale: the call rendered it again with the UV images and listed them in `rendered`. Each listed image is opened before the handoff; a second call renders nothing.
8. With no approval and no waiver in the task, the run stops here. The handoff gives the path, 0.46 m seat and 0.86 m height, 21k evaluated triangles, the review pack folder, finish status `pass` and "awaiting approval".

## Common mistakes

- Accepting an n-gon cap or a pole at a revolved end: close it with a quad grid, ending the profile at a small ring.
- Using Blender's default cylinder, cone or UV sphere: build the shape with the helpers or a subdivided cube.
- A Bevel modifier with 1 or 3 segments: use 2 or 4 so the corners stay quads.
- Cutting openings with Booleans or sculpting soft goods: build ring topology and shape a quad cage with crown, roll and piping.
- Adding materials, slots or Principled shaders to a model going to Retexture: hand over geometry and UVs only.
- Judging the cage instead of the evaluated mesh: render the review pack, which reads the evaluated mesh.
- Raising every segment count or Subdivision level for smoothness: add faces only where they add detail, and let the density check confirm it.
- Stacking a leg and its post as two pieces, or letting a rail run past a leg: build continuous members through the joint and open `joints.png`.
- Modelling a recognisable kind of object from memory: get references and landmarks first, and compare the model with them.
- Handing off a part still flagged `over_dense` as a judgement call: the flag is a failed gate.
- Writing the handoff while `finish_check.check` returns `repair`: fix the first blocker and run it again; only its `partial` entries are reported as defects.
- Passing the check without opening what it rendered: open every image in `rendered`, since a pass measures the gates, not the look.
- Starting Retexture on an unseen model: show the review pack and wait for approval or an explicit waiver.
