# The verify pass

Read this when a brief names you as the verify pass for one photograph, or when you are doing it yourself in a serial run.

The detect passes looked once, each at part of the photograph, and named what they saw at that scale. You now see every object they found as a crop of the full photograph, numbered, with its box in red and its name underneath. Your job is to catch the names that are wrong, the boxes that are not objects, and the objects listed twice. Everything later is matched and built by name: a wrong name here becomes a duplicate object in the graph or an asset that does not exist.

## Hard rules

- **Look at the whole photograph first**, then the sheets. A crop out of context can mislead: a dark blob is a camera once you see it sits beside the headphones.
- **Judge the thing inside the red box**, not something else the crop happens to show. If the box sits on one thing and the name describes its neighbour, the name is wrong for that box: rename it to what the box is on.
- **Rename only when you can see what it is.** A crop too small or blurred to tell is left alone; the name already says it is uncertain.
- **Remove only what is not an object**: a shadow, a reflection, glare, a printed picture, the cut-off edge of something nobody could name, a patch of wall boxed as a thing. Never remove an object just because it is small, hidden or oddly named.
- **Mark a duplicate only when two numbers box the same physical object**, for example a whole case and a box on just its lid. Two objects of one kind side by side are two objects.
- **Fix what a thing rests on when the list is plainly wrong** with `reparent`: `on` is the number of the object that holds it, and `relation` one of `on-top-of`, `inside`, `hanging-on`, `leaning-against`, `under`, `attached-to`, `part-of`. Only when you can see it; never to tidy the tree.
- Use the shortest common name, the same one the other objects of that kind use, at most three words.
- Write only the one file your brief names. Never edit the detections yourself; a script applies your decisions.

## What you write

```json
{
  "image_id": "img004",
  "renames": [
    {"n": 21, "label": "candle", "description": "white candle in a glass jar with a blue round label", "why": "the box is on the candle jar; 16 was the vase behind it"}
  ],
  "remove": [
    {"n": 9, "why": "cut-off corner of something at the frame edge; not identifiable"}
  ],
  "same_as": [
    {"n": 30, "as": 31, "why": "30 boxes only the lid of the earbuds case 31"}
  ],
  "reparent": [
    {"n": 12, "on": 8, "relation": "inside", "why": "the water is in the glass vase 8, not the black vase"}
  ],
  "notes": "anything the match round should know"
}
```

`n` and `as` are the numbers on the sheet. Joins the merge made across a tile seam carry a low-confidence name and a note: look at those crops with special care. Leave a list empty when there is nothing to do; an image with nothing to fix is a real result. A removed or duplicated object's children are moved to its parent or to the object it duplicates, so nothing resting on it is lost.

## Workflow

1. Open the whole photograph.
2. Open each sheet. For each crop, ask: is the red box on one real object, and is that object what the name says?
3. Write the file and reply with one line: how many renames, removals and duplicates.
