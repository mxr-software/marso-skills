# Review a photographed scene

## Establish the room before filling it

Separate measurements from guesses. Confirm a corner angle, room dimension or large object's identity only when ambiguity materially changes the layout; batch those questions early. Record approximate dimensions as estimates, with their source and uncertainty. Do not force an entire room to fit a rough remembered measurement.

Show a simple top-down plan and a matched photo view with the shell and major furniture before making small props. Use known dimensions and repeated architectural features as anchors. Where several photographs exist, compare all of them and keep separate camera estimates. A single photo's bounding boxes do not uniquely determine room depth, camera lens and object size; changing every object to hide an incorrect camera fit is unreliable. This helper does not perform joint multi-camera reconstruction or lens-distortion calibration.

Inspect all `unplaced`, `position-guessed`, `wall-guessed`, skipped and missing-parent records. Other-view-only objects need explicit placement or a disclosed exclusion. A `part-of` relationship may mean included geometry, a separately needed context object, or a mistaken detection; resolve it rather than silently losing its descendants. Give additional shell surfaces unique graph ids and distinguish their functional role from their identity; do not overwrite another wall because both are walls.

Preserve hand corrections before regenerating `placement.json`; `--force` replaces them. Keep corrections in a review record, including coordinate frame and source revision. Apply absolute poses or deltas from a saved baseline, not a fresh accumulated offset on every rerun.

## Inspect pose and contact

The assumed generated front (-Y) is a starting convention, not evidence. Inspect the imported mesh from multiple sides, establish its upright/front and compare the side visible in the photo. Use geometry-group rotations for upright corrections and entity yaw for placement. Do not mirror a model just to show its other side.

For `inside`, align the actual insertion feature with the actual opening: a stem bundle with the vase neck, for example. A foliage bounding-box centre is not the stem axis. Inspect the opening, insertion depth and wall clearance in at least two views; vertex-percentile heuristics are not reliable across arbitrary shapes.

Bounding-box/convex-hull overlap is a broad screening test, not proof of interpenetration or clearance. Separate intentional support and nesting contacts from unwanted collisions, and inspect the relevant surfaces. Recheck contacts after size or pose changes. If rigid placement cannot match the source because the generated proportions are wrong, report that geometry mismatch; seek a better source or an authorized geometry correction rather than silently stretching it to match one view.

## Completion evidence

Compare the photo and scene from matched viewpoints, plus a top-down overview. Report missing objects, placeholders, inferred areas and remaining contact or scale errors. For a finished scene, include a material-shaded review after approved assets are textured; final high-quality rendering is a separate requested step. Do not label an unreviewed layout or base-colour screenshot photorealistic.
