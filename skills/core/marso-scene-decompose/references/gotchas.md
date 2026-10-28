# Gotchas

Read this when a phase fails, a result surprises you, or you are unsure why a rule exists. The headings are symptoms. The rules themselves are in SKILL.md; this file holds the longer stories.

## The quick ones

| Symptom | Cause | Fix |
|---|---|---|
| A tile pass reports success but its tile is flagged empty | The tile may really be empty, or the pass gave up | Look at that region of the overlay. Re-run it only if objects are plainly missing |
| Every box in an overlay is shifted the same way | A tile's region and its picture disagree | A workflow bug: stop and report it with the tile's id |
| Boxes squashed into one corner of a tile's region | A tile pass converted its boxes to whole-photograph coordinates, and the script mapped them again | Boxes are 0–1 of the picture shown. Run that tile again with the brief unchanged |
| An object is missing from the merged detections | It overlapped another box and was read as a duplicate | The merge report's `dropped` shows the labels. One thing in front of another should survive; report it if not |
| An object's parent looks wrong | Its `on` named a surface no object was called, so the merge fell back to geometry | Look at `unresolved_on` in the report. Usually one surface was called two names by two passes |
| The graph has more nodes than the room has objects | Candidates the match round refused to merge | Expected and recorded: check the identity groups' floor and ceiling |
| `fast.py graph` lists a refused merge | A pass gave one line of evidence, or two objects from one photograph | The safe direction working. The objects stay separate |
| A big object has a tiny box | The box was drawn round the visible part of something mostly hidden | That is right: box what you see and set `occluded` |
| The duplicate check warns that an anchor overlaps its contents | Anchors are boxed at full extent, so everything on them overlaps them | Expected when the category is `architecture` |
| A pass wandered off reading files | Its brief was rewritten | Send `plan_fast.py`'s prompt unchanged |
| A path works on Windows but not elsewhere | Backslashes | Use forward slashes in every path |

## When a run takes far longer than the estimate

An earlier seven-stage version with checks at every stage took fifty minutes for three photographs; twelve of those were the lead hand-running small scripts and writing briefs between stages. Adding a pass or a review to catch one failure made every later run slower and caught none of the failures that actually happened, which were bookkeeping bugs in scripts. Hence a fixed set of rounds (detect, verify, match), one command between phases, and no checks the workflow does not ask for. The verify round earned its place: without it, names guessed at the wrong scale became duplicate objects and assets that did not exist. Look at the `phases` timings in the last `fast.py` output: each round should be a few minutes and every script phase seconds. A slow script phase is a bug to report.

## When the graph puts something on the floor that clearly rests on furniture

A worktop once came out resting on the floor: the view with more of the worktop in frame could not see the base units beneath it and inferred the floor, while the smaller view saw the units carrying it. The graph builder now prefers a view that saw the support over a bigger view that reasoned about it, and a deeper parent over a shallower one. Every parent it chose between is listed in `parent_conflicts` with why, so a reader can check it against the photographs. Rebuild the graph; do not edit it by hand.

## When two candidates fit a match equally well

A wide view showed two chairs of the same design at one table; a close-up showed one chair, and it matched both equally. Picking the better-looking one would have produced a confident, unfindable error. Refuse, with every candidate in one set, what argues each way, and `distinct_objects` bounding the count: two candidates in one photograph are certainly two things.

## When one view sees a whole and another sees its parts

A wide view recorded a run of base units as one object; a closer view recorded four door fronts. Neither is wrong; they read the same thing at different grain. A difference in detail is not a correction: refuse, give `distinct_objects` the number the finer view supports, and say the views differ in grain.

## When a later pass argues with a name an earlier one gave

A wide view recorded "flask" for a pale upright shape forty pixels tall; the close-up showed a wire caddy holding two shakers. The confident wrong name could not be matched one-to-one. Name only what the scale supports, with `id_confidence: low` for a shape; the closer view will name it, and the match round knows which to believe. The same goes for brands: a camera was recorded as one model from expectation and the full-resolution crop showed another. Never write a marking you cannot read.

## When almost nothing was matched automatically

Two detect passes called one thing "kitchen splashback" and "splashback panel, back wall", and everything standing against it was left for the match round. The automatic matcher works by name, so the shortest common name, used consistently, is what makes it work. A large residue is a naming problem upstream.

## When the merge flags a tile as empty, saturated or missing

A tile that is mostly bare wall genuinely finds nothing; a tile over a cluttered worktop that comes back with fifty objects is a pass that ran out of steam. The merge flags both and decides nothing. Missing: run only that tile again. Saturated: say so in the delivery; the Fine mode on a closer photograph of that region is the fix. Empty: look at that region of the overlay.

## When the viewer looks empty, or its pictures are blank

Selecting a node fades everything unrelated, so a selection on load can make the tree look empty: click the background to clear it. Blank pictures mean a viewer built without `--embed` was moved away from the photographs it points at: put it back beside them or rebuild with `--embed`. A crop that shows the wrong thing is a wrong box, which is the detect round's problem, not the viewer's: the crop draws the box on itself so the two can be told apart.

## When you are about to share the viewer

A viewer with the photographs embedded was once uploaded to show a result, in a run whose images were of the inside of the user's own home. Nobody had asked. Say exactly what would be uploaded and wait for a clear yes; building it locally is the job, publishing it never is.
