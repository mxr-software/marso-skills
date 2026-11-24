# Containers and closures

Bottles, jars, cans, cups, tubs and their lids. Read this before building any vessel that holds something, has a lid, or can be seen into.

Contents: [Measure before modelling](#measure-before-modelling) · [Bodies](#bodies) · [Walls, rims and interiors](#walls-rims-and-interiors) · [Lids, caps and closures](#lids-caps-and-closures) · [Metal cans](#metal-cans) · [Paper cups](#paper-cups) · [Review views](#review-views)

## Measure before modelling

- Record the profile landmarks from the reference: crown, cap and body split, shoulder, widest section, waist, lower taper, heel and standing foot. Build from these, not from a rounded primitive.
- Work in millimetres in the record and convert to metres once, in the build script.
- Keep three sizes apart: the body, the overall bounds with the closure on, and any published capacity. A wall of 90 mm with an outward rim roll is wider than 90 mm overall.
- Fit the model by changing its stations. Never rescale a finished body or end panel to reach a nominal size: stamped and moulded details then scale wrongly.
- A front view gives no depth. For a body that is not round, get a second view or record the depth as assumed.

## Bodies

- Build a round body as one `revolve` of its measured profile, and a non-round body as a `loft` through measured sections.
- Join the profile points with straight segments or with a curve that stays between its neighbours. A curve that overshoots between a wall and a shoulder leaves a false ledge.
- On a non-round body, change the section's shape gradually through the shoulder, over several stations. An abrupt change from a rounded square to a circle leaves a ridge.
- Shape the base: a heel radius, a standing ring or foot, and a recessed or domed underside. A body that ends in a flat disk reads as a primitive.
- Proportions outrank edge treatment. A waist at the right height and a taper of the right length matter more than a larger bottom bevel.
- A printed or flush label is texture and has no shell. Model a label, sleeve or wrap as its own shell only where its edge or thickness shows at the closest view. It then follows the body's sampled profile, offset outward by its thickness; record the body faces it covers for the UV stage.

## Walls, rims and interiors

A container that can be seen into, or shown with its lid off, needs an inside.

- Give the wall real thickness: an outer skin, a rim that returns, and an inner skin. Build it as one profile that runs up the outside, over the rim and down the inside to the floor.
- The interior floor sits above the underside by the base thickness. Recheck that clearance after any scaling or deformation.
- Check a section through the wall: the inner skin never crosses the outer skin, at the shoulder and the heel above all.
- Keep every face that a use can expose: the interior, the underside and the surfaces a lid covers.
- A glass or clear wall is still two skins. Its thickness shows at the rim and through the wall.

## Lids, caps and closures

- A lid or cap is its own part, parented to the root. It touches the body at its seat and never shares vertices with it.
- Build a pressed or moulded lid as one continuous `revolve` profile: lower bead, skirt, rolled rim and recessed panel. Stacked rings and tori lose the transitions between them.
- A recess needs four things: a floor, a short drafted wall, a transition to the surface round it, and depth enough to shade. A bevel or a dark line on an unchanged surface does not read as a recess.
- Close a flat lid or end panel with a quad grid, and run loops round real openings. A fan of triangles to one centre point pinches the highlight.
- Leave the seating gap the real closure has: a lid skirt stands off the neck by its own thickness plus clearance.
- A screw cap has a skirt taller than the thread it covers, grip ribs as geometry on the high path only, and a tamper band below it as a separate ring where the reference shows one.
- A peel-off foil is a thin disk with a rounded tab that projects past the rim and lifts slightly at its tip.
- When revising a closure, keep the accepted body unchanged and edit only the closure part.

## Metal cans

- Keep these sizes apart in the record: body diameter, finished seam diameter, neck diameter, standing ring diameter, height and tab size. For a 330 ml drinks can the body is about 66 mm across and 115 mm tall, with a neck near 52 mm and a standing ring near 48 mm.
- Model the seam, the wall inside it and the countersink as one revolved section, joined to the end panel. A torus on a cylinder loses those transitions.
- A drinks can has a domed base formed in one piece with a narrow standing ring. A food can has a separately seamed flat base with a different profile. Add a side seam only when the reference shows one.
- A pull tab is formed sheet with curled edges: a finger opening, a nose, a rivet island and a raised perimeter. Build it as a lofted outline with thickness, not a wire ring on a slab.
- The rivet is a low dome raised from the panel. The score line is a shallow groove on the panel, not an open cut.
- Fit the opening outline inside the panel with clearance all round. An outline that reaches past the panel radius folds back on itself.
- The tab sits above the panel on its rivet with clearance. Check that gap in a section view.

## Paper cups

- The wall is a tapered `revolve`. A common 350 ml cup is about 90 mm across the rim, 58 to 60 mm across the base and 110 mm tall.
- The rim is a rolled return that turns outward and back to the wall, not a flat cap.
- The base is recessed: a short near-vertical foot of about 4 mm, an inward return, and a floor about 6 mm above the standing edge. The taper never ends in a flush disk.
- A sleeve ends above the foot and below the rim, so the plain wall and the sleeve's edge both show. Corrugation on a sleeve is geometry on the medium and high paths.
- A cup lid is a separate part with its own skirt, rim channel and raised panel, built as one profile.

## Review views

`review_model.review` renders two fixed oblique views. Render these extra views yourself in neutral clay, save them beside the review pack and list them in the handoff.

- **Every container:** a level side view against the reference, and a view from below that shows the base.
- **Open or lidded:** a raised view into the mouth, with the lid moved aside on a duplicate, and a section through wall and rim.
- **Closures:** a top view and a close oblique view. Check the recess in the pack's `gloss.png` as well, where it shows as a broken highlight.
- **Cans:** the top, a close view of the tab, a section through the seam, and the underside. A top view alone cannot approve a can.
