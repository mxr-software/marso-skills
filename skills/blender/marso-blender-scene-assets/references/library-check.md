# Check the library first

Before an asset is made, search the account's Marso library for it. A match is imported instead of generated: no reference image, no mesh, no wait. The add-on's `find_in_library` command searches Marso's own index by meaning (text) and by appearance (an image), and returns each library asset once, with a thumbnail.

## The search

For each asset `manifest.py pending runs/<job>/assets.json --stage library` lists, send its `library_searches` row as is:

```
find_in_library {query: <label>, image_path: <absolute path to search.png>, limit: 5}
```

- **Search with both.** With text and image together a result counts only where the two agree, and that is what keeps a lookalike out. An image alone rates a neighbour or a similar shape highly; a text alone cannot tell this kettle from any kettle.
- **Use `search.png`, never `crop.png`.** The search finds whatever fills the picture. A padded crop of glasses lying on their case finds the glasses; the red outline on `crop.png` adds noise. `search.png` is the subject's own box with no marking.
- **The label is the query.** Do not add the description: long queries score lower, not higher. A better word for the object, where the label is vague, is fine.
- The path is read by Blender, so pass it absolute.
- The command reads only and answers at once (no job). Several can run one after another; there is no cap to keep.

Record each answer: `manifest.py record runs/<job>/assets.json --stage library <asset_id> --json '<result>'`. On an error, record it with `--error`; a failed search never blocks the asset, it is made instead if the user says so.

## Reading the results

Each result has `name`, `verdict`, `image_score`, `text_score`, `pbr_asset_id`, `project_ids` and `thumbnail_path` (a downloaded file; the link in `thumbnail_url` lasts five minutes). The verdict, with the thresholds returned alongside it:

| Verdict | Searched with both | Image only | Text only |
| --- | --- | --- | --- |
| `match` | image at or above `match_image`, text at or above `text_agrees` | never | never |
| `possible` | image at or above `possible_image`, text agreeing; or text at or above `text_only` where the image never returned it | image at or above `image_only` | text at or above `text_only` |
| `weak` | anything else | anything else | anything else |

Results come back by verdict, and within a verdict those the text agrees with come first. The thresholds were set on one library and are defaults to review, not calibrated constants. They are behind what the user sees, never a decision on the user's behalf.

Interpret candidates in context:

- Objects that hold other objects can have misleading search images. Check text results for tables, trays, shelves and bowls, whose crops may be dominated by their contents.
- Image similarity can rank neighbours and lookalikes highly. Scores guide review; they are not identity guarantees.
- Check whether a result is the intended part or its whole assembly.
- Library names may be inaccurate. When no stronger candidate exists, show the best weak thumbnail so the user can recognise it.

## The decision is the user's

Show every checked asset at the plan checkpoint: its `search.png` beside the thumbnail of each `match` and `possible` result (and the best `weak` one), with name, verdict and scores. Then record what the user chose:

```
manifest.py choose runs/<job>/assets.json --reuse a079=<pbr_asset_id> a088=<pbr_asset_id> --make a015 a018
```

- `--reuse` takes a `pbr_asset_id` from that asset's own candidates; anything else is refused.
- Never reuse without the user's say, however high the score. A library asset may be a different size, style or material than the photograph shows.
- A reused asset skips the reference image and the mesh. It still goes through `mint_status`: an old library asset may not be minted, and then it imports without real-world scale unless the user accepts that.
- Changing one's mind later is `choose --make <asset_id>`, which sends the asset back to the start of the chain.
- Nothing in the library is changed: reuse imports the asset, it does not move or copy it into the run's project.

## When to skip it

`manifest.py init --skip-library` starts every asset at the reference image. Use it only when the user says so, or when the installed add-on has no `find_in_library` (say that it is missing; do not search another way).
