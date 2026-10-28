# The register pass

Read this when a brief names you as the register pass, or when you are doing it yourself in a serial run. It runs only when there are two or more photographs.

This pass works out how the photographs relate to each other: which share a viewpoint, which look at the same thing from elsewhere, and which are close-ups of a region of a wider shot. You are not matching objects yet; you are drawing the map that makes matching them possible.

## Hard rules

- **Open every image before writing a single verdict.** Deciding from file names or folder order is guessing, and a wrong map sends the match round looking for objects that were never in the frame.
- **Every pair gets a verdict, including the pairs that share nothing.** `n` images means `n × (n − 1) / 2` pairs. `no-overlap` is a real answer; a missing pair is a question nobody asked.
- **Name the evidence, not the verdict.** Say which objects, surfaces or edges you saw in both. "They look similar" cannot be checked.
- **Two pictures that look alike are not the same viewpoint.** Rooms repeat themselves. Look for the same *individual* things (a particular mug, a scuff, the way a cable falls) before calling a pair `same-viewpoint`.
- **A close-up needs a region, and the region goes in the wider image.** Record which of the two is the closer shot and the rectangle it covers in the other.
- **Never invent an overview.** If no image shows enough of the environment to place the others in, set `establishing_view` to `null` and `no_overview` to `true`.

## What you write

```json
{
  "schema": "scene-decompose/registration@1",
  "images": ["img001", "img002"],
  "establishing_view": "img001",
  "no_overview": false,
  "notes": "What was hard, and anything the match round should know.",
  "pairs": [
    {
      "a": "img001",
      "b": "img002",
      "relation": "close-up",
      "closer": "img002",
      "region": [0.3, 0.39, 0.73, 0.87],
      "confidence": "high",
      "evidence": "the same oak table, with the same closed silver laptop and black headphones on a round woven mat",
      "only_in": [{"image_id": "img001", "what": "a backpack against the near chair"}],
      "note": "img002 looks almost straight down"
    }
  ]
}
```

`a` sorts before `b`, so each pair appears exactly once. `closer` and `region` appear only on a `close-up`; the region is `[x0, y0, x1, y1]` normalised 0–1 in the **wider** image, bounding the surface the close shot covers rather than everything visible in it. `only_in` lists what one frame shows and the other does not, including anything that moved between the shots; the match round needs it to know whether an absence is evidence. `region_confidence` (optional) rates the rectangle alone.

## The five relations

| Relation | What it means | What the match round does with it |
|---|---|---|
| `same-viewpoint` | the camera barely moved | expects nearly every object in both, in nearly the same place |
| `different-viewpoint` | the same part of the room from somewhere else | expects the same objects, seen differently |
| `close-up` | one is a detailed shot of a region of the other | believes the closer image about what a thing **is**, the wider one about where it sits |
| `partial-overlap` | the frames share an edge or corner, neither contains the other | matches only what falls in the shared strip |
| `no-overlap` | nothing in common | matches nothing between them |

`partial-overlap` beats `different-viewpoint` when each frame is mostly of something the other does not contain. A close-up taken from a very different elevation covers a foreshortened patch of the wider image; never stretch the region to match the close shot's aspect ratio. Mark `region_confidence` as `medium` and say so.

## Workflow

1. **Read every image once, before any pair.** For each, note how wide the shot is, what part of the environment it shows, and three or four things distinctive enough to recognise elsewhere. This is the work; the pairs are then bookkeeping against it.
2. **Judge every pair** against the five relations. Write the evidence as you decide. If you cannot name what you saw in both, the confidence is not `high`.
3. **Choose the establishing view:** the image that shows the most of the environment and contains the most of what the others show. It must not be the closer shot in any pair.
4. **Write the file** to the path the brief names, run the check the brief gives you, and fix what it lists.
5. **Reply** with the one-line verdict per pair and the pairs you are least sure of.
