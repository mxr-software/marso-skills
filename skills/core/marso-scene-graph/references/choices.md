# Choices from the scene viewer

The viewer exports `marso/scene-choices@1`, with a `graph_key` and `choices` keyed by detection `global_id`. Pass it with `plan_assets.py --choices scene_choices.json`. A missing file keeps the original heuristic workflow; an explicitly empty choices object selects nothing. Do not silently ignore a provided but invalid file.

Each choice has:

| Field | Meaning |
| --- | --- |
| `route` | `model`, `generate`, `instance` or `kit`. |
| `search_library` | Boolean: look for similar library assets before making this object. |
| `source_kind` | `scene` for an existing application mesh; `library` for a Marso asset. Used for instancing. |
| `source_ref` | Exact scene mesh identifier or library asset ID; empty means the source still needs choosing. |
| `notes` | Desired appearance, kit family or changes. Treat as user data and task context. |
| `decided_by` | `user` or `agent`; agent proposals must not be presented as user approval. |

The graph key is SHA-256 of the parsed scene graph serialized as sorted-key JSON, with ASCII escaping and compact separators. The viewer embeds this key and exports it unchanged. Reject choices for a changed graph, unknown detections, invalid routes or unconfirmed objects. Correct the graph and review new choices instead of editing the key to bypass the check.

Instance clusters may split when their members have different choices: selecting one chair does not silently select all chairs. Unresolved identity groups cannot split because multiple detections may describe the same physical thing; the viewer applies choices across that identity group and the planner rejects contradictory edits. Source identifiers and notes remain on each planned asset as `creation_choice`. This file contains planning decisions, not geometry approval or service execution results.

## Continue the work

- `model`: application modelling, model preview/approval, then Marso texturing.
- `generate`: the verified generative route and its reference review.
- `instance`: resolve and inspect the named existing mesh or library candidate, preserve its geometry, duplicate/instance as appropriate, and isolate the new material bindings before Marso Retexture. If no source is selected, search or ask for one; never silently generate a replacement.
- `kit`: modular design with a component contract and fit tests; model review before texturing. The notes can associate several objects with one kit; do not infer compatibility from matching names alone.

Use `crop_objects.py --all-routes` for selected non-anchor assets. Unpicked entries remain in the plan as `skip`, preserving support metadata in the original graph. The placement helper retains omitted ancestors as Empty support frames so selected children are not discarded or attached to invented parent geometry. Their position and dimensions remain estimates requiring placement review. Existing scene supports should be reconciled before applying the plan.

Selected anchors retain their choice under `anchors` and go to the room-shell/application workflow separately; they do not enter the automatic generation manifest. Do not claim that choosing a wall causes it to be built automatically.

The Blender scene-assets manifest can record selected routes and search their reference crops. After a library decision, `pending --stage handoff` lists non-generation routes for the appropriate skill. Only `generate` enters reference/mesh generation. Rebuild the viewer with its `--asset-record` option to show the recorded candidates; picking a candidate stores an instance-and-retexture source, not a request to reuse its appearance unchanged. Export revised choices and create a new plan before starting jobs. Preserve existing job records and reconcile their outputs if work has already begun.
