# Files, ids and schemas

Read this when you need the run folder's layout, what an id means, or the shape of a file a script wrote. The files a pass writes are described in [detect.md](detect.md), [match.md](match.md) and [register.md](register.md).

## The run folder

```text
runs/<job_name>/
|- manifest.json              # intake: every image with an id, path and pixel size
|- fast.json                  # the mode, the images' folder, and how long each phase took
|- tiles/                     # downscaled whole views and, in Fine mode, native-resolution tiles
|- parts/                     # what each detect pass wrote; raw, one file per pass
|- detections/<image_id>.json # merged objects per image, with local ids
|- structure/<image_id>.json  # the support tree per image, built from the `on` names
|- qc/<image_id>.png          # one overlay per image: every merged box drawn on the photograph
|- verify/                    # crop sheets, each image's verify decisions, and the files before them
|- registration.json          # the register pass (two or more images)
|- match/                     # automatic matches, contact sheets, briefs and decisions
|- matches.json               # every global object and what it was merged from
|- scene_graph.json           # the deliverable
|- view_scores.json           # which view shows each object best
|- confusion.json             # everything the run was not sure of
`- viewer.html                # what the user opens
```

Raw pass output goes in `parts/`, never in `detections/`: the graph builder reads every file in `detections/`, so a stray tile file there corrupts an image's merged result. Use the paths the scripts print.

## Ids

| Id | Looks like | Made by | Means |
|---|---|---|---|
| image id | `img001` | intake, in file order | one photograph. Stable across re-runs |
| local id | `img001-011` | the detect merge | one object **as seen in one image** |
| global id | `g029` | the graph builder, from `matches.json` | one physical thing, standing for every local id the match round decided was the same object |
| cluster id | `cl001` | the graph builder | a set of repeated things |
| area id | `ar001` | the graph builder | a place a person would name |
| group id | `ig001` | the graph builder, from refusals | several global objects that may be fewer real things; carries `at_least` and `at_most` |

A local id appears in the scene graph only inside a node's `views`. A global id never appears in a detections file.

## Conventions every file shares

- **Boxes** are `[x0, y0, x1, y1]`, normalised 0–1 of the image they were seen in, origin top-left. Never pixels; the pixel width and height are in the manifest.
- **Sizes** are `size_m`, the largest real dimension in metres, with `size_confidence` and a `size_basis` saying what it was judged against.
- **Relations** come from the closed vocabulary in [relations.md](relations.md).
- Every file carries a `schema` string such as `scene-decompose/scene-graph@1`.

## `scene_graph.json`

```json
{
  "schema": "scene-decompose/scene-graph@1",
  "bbox_convention": "normalised [x0,y0,x1,y1], 0-1 of the image, origin top-left",
  "images": ["img001", "img003"],
  "nodes": [],
  "clusters": [],
  "areas": [],
  "identity_groups": [],
  "parent_conflicts": []
}
```

A node:

| Field | What |
|---|---|
| `global_id` | the object's identity across every view |
| `label`, `description`, `category` | taken from the best view of it |
| `parent`, `relation` | the one thing that holds it, as a `global_id` (null for an anchor), and how |
| `parent_source` | which image's structure that answer came from |
| `support_inferred` | true when that view could not see what holds it |
| `size_m`, `size_confidence`, `size_basis` | from the view most sure of the size |
| `occlusion` | `none`, `partial` or `heavy`, from the view that shows the most of it |
| `inferred_whole` | only when every view shows it heavily hidden: `whole_description` (the complete object, built from context, with inferred parts named), `visible` (what was actually seen) and `from` (the image id). Use it as the prompt text for a reference image; the crop alone shows too little |
| `unconfirmed` | only on an object seen in one view, the wider of a close-up pair, inside the region the close-up covers, named with low confidence and never matched: `closer_view` and `reason`. Probably a misreading of something the close-up recorded; kept, but not to be made into an asset unconfirmed |
| `seen_in` | how many views show it |
| `views` | one per image: `image_id`, `local_id`, `bbox`, `occluded`, `occlusion`, `truncated`, `id_confidence`, `frame_share` |

`clusters` are `{cl_id, label, members[], seen_in[], kind}` where `kind` is `instances` (the same thing repeated) or `variants` (genuinely different). `areas` are `{ar_id, label, members[], seen_in[]}`. `identity_groups` come from the match round's refusals: `{group_id, label, members[], distinct, at_least, at_most, basis}`. `parent_conflicts` lists objects whose views disagreed about what holds them, what the script chose and why; read every one.

There are no crops and nothing in pixels: a later step multiplies a box by its image's dimensions when it wants one.

## `view_scores.json`

One entry per object, its views ranked best first, with `best_view`, each view's `score` and `share_of_best`, the `penalties` that cut each score down, and `decisive` (false when the second-best view is nearly as good). Scores compare views of one object, never one object with another.

## `confusion.json`

Everything the run was not sure of. It resolves nothing and removes nothing from the graph.

| Field | What |
|---|---|
| `unresolved` | the match round's refusals, with their candidates, the case for and against, and the `global_ids` they became |
| `corrections` | readings a better view contradicted |
| `low_confidence_merges` | objects merged across views on the weakest evidence the rules allow |
| `inferred_supports` | objects whose parent was reasoned rather than seen |
| `parent_conflicts` | objects whose views disagreed about what holds them |
| `identity_groups` | sets of nodes that stand for fewer physical things, with how many and why |

## `matches.json`

Built by script from the automatic matches and every batch's decisions. One entry per global object with `members` (at most one per image), `evidence` and `confidence`; `corrections` and `unresolved` sets as the match pass wrote them. A merge with fewer than two lines of evidence, with two objects from one photograph, or against an automatic match is refused and listed, and its objects stay separate.
