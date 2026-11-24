# Folded-sheet packaging

Cartons, boxes, sleeves, bags and pouches: anything made by cutting one flat sheet and folding or sealing it. Read this before building one. The method is to model the sheet, then fold it.

Contents: [Start from the flat blank](#start-from-the-flat-blank) · [Fold it](#fold-it) · [Add thickness last](#add-thickness-last) · [Liquid cartons](#liquid-cartons) · [Boxes with flaps](#boxes-with-flaps) · [Bags and pouches](#bags-and-pouches) · [Checks](#checks)

## Start from the flat blank

- Draw the blank at real size: every panel, the fold lines between them, the glue lap and the seal strips. One sheet is one connected mesh.
- Give each panel a regular quad grid, with an edge loop on every fold line. A face that spans a fold stretches when the sheet folds.
- Keep the flat state as a separate mesh copy, hidden and outside the asset root; a shape key would block applying Solidify. The flat blank is the sheet's natural chart layout: pass it to `marso-blender-uv` when installed, and without it report the sheet as not unwrapped.
- Work out which construction the object has before drawing. A drinks carton is a tube with sealed ends, not a cross of six panels. A tuck box, a tray and a sleeve each have their own blank.

## Fold it

- Fold by rotating each panel's vertices about its fold line, from the centre panel outward. Derive each fold angle from the finished dimensions.
- Folds stay connected: the vertices on a fold line belong to both panels. Layers that only lie against each other after folding stay separate, with no welding.
- Weld only where the real sheet is bonded along its own seam, such as the glue lap of a tube.
- Layers that are not bonded never share a plane. Offset each layer by its thickness plus a small clearance, so nothing flickers or crosses.
- Fold lines keep a small radius, about the sheet thickness. A larger radius or a broad bulge across a panel pushes one layer through the next.

## Add thickness last

- Fold the sheet at zero thickness and check it. Where a cut edge or the inside can be seen, add a Solidify modifier inward by the board thickness (about 0.35 mm for carton board, 1.5 to 4 mm for corrugated board). A sealed pack on the low path stays one skin; record that in the handoff.
- Check the layered regions again after Solidify. Where two folded layers collide, increase their clearance in the folded sheet.
- Exposed cut edges show the board thickness on the high path: a flap's free edge, a tray's rim, a hand hole.
- Panels of card are nearly flat. Limit any panel bulge to under 1 mm and fade it to nothing at the panel's edges.

## Liquid cartons

- The body is a rectangular tube: four panels and one narrow glue lap of about 5 mm down a rear corner.
- A gable top has two sloped roof panels that meet at a sealed fin, and two side panels that fold inward as gussets under the roof. Model the gusset folds with fold loops on a quad grid.
- Derive the roof from the dimensions. For depth `D` and a fin at mid-depth, each roof panel rises at `atan(rise / (D / 2))` and has the slant length that angle gives. Do not drag it into place by eye.
- A flat-topped brick carton has transverse seals at top and bottom, with triangular ears folded down at the sides and under the base.
- The base is folded layers with a slight recess, not one inset rectangle.
- A screw cap is a separate part on its own flange. The flange seats on a flat ring on one roof panel.

## Boxes with flaps

- A closing flap is a panel of its own that lies on the wall panels, with a small lift at its free edge and its cut edge visible. A welded cube corner reads as a solid block.
- Main flap, dust flaps and tuck-in return are distinct panels. Check which the reference shows before assuming a tuck end.
- Stop an exposed edge strip before it reaches a hidden hinge, so the strip does not cross the layers there.

## Bags and pouches

- Decide what holds the film's shape: the contents, a rigid insert, or the seals. Wrinkles gather near the seals and crimps; the supported faces stay smooth.
- Build wrinkles as a few short tapered creases and local buckles, with extra loops only there. Evenly repeated waves look synthetic.
- A fin seal is the sheet's two edges bonded face to face, standing off the pack. Build it from the sheet's own edge loops so it follows the seam.
- A bonded mouth or seal stays flat: merge the two layers into one there, welding their matching edge loops and removing the doubled faces, as for a glue lap.
- A rolled closure is a flattened return fold. A stand-up pouch has an opened gusset at its base, not a pillow seam.
- A fold-over top needs room: half the layered thickness must fit inside the bend radius.
- Crimp ribs deform the sheet itself, with at least four edge loops across each rib.

## Checks

- **One sheet:** the folded mesh is one connected piece per real sheet, before Solidify.
- **No stretch:** edge lengths match between the flat and folded states. Compare them in the script and report the largest change; more than 1% means a face spans a fold or a panel was moved instead of rotated.
- **No crossing:** no layer passes through another, checked after Solidify and from below.
- **Views:** render the flat blank beside the folded model, and low views of seals, fins and the base, in neutral clay yourself. Check panel flatness in the pack's `gloss.png`.
- **A second size:** before reusing a build script for another size, rebuild and recheck; folds that clear at one size can collide at another.
