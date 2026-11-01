# Direct scene design

For a prompt, settled plan or accepted concept without real detections, use a design record rather than manufacturing a photographed graph. The [design adapter](../scripts/design_plan.py) emits the existing asset-plan structure and a direct placement record, retaining explicit route decisions.

```json
{"schema":"marso/scene-design@1","run_id":"workshop-v1","project":"Workshop",
 "assets":[{"id":"bench","label":"Workbench","route":"model","size_m":[2,0.7,0.9],
   "effort":"scene-ready","requirements":{"exact_dimensions":true},
   "instances":[{"id":"bench-1","location":[1.5,3,0],"yaw_deg":0}]}]}
```

Run `python "<skill>/scripts/design_plan.py" design.json --out asset_plan.json --placement placement.json`. Outputs must be new paths; preserve reviewed plans on resume. Sizes and placements are explicit design assumptions in metres; location is bottom-centre, Z up. `effort` is blockout, scene-ready or hero. Routes are model, generate, kit, reuse, instance or skip. Every instance has a stable id; optional `parent` names another instance or an anchor, and `relation` records support. Explicitly check functional requirements before selecting routes; the adapter does not decide them.

Optional `anchors` are records with `global_id`, `existing_entity` and optional parent/name, mapped to accepted Blender shell Empties. The placement skill can consume this direct placement record without invoking its photographic `layout_plan.py`. Use its existing `imports.json` handoff for actual generated, reused or modelled meshes. Until an actual source is supplied, boxes remain unresolved; no generated asset IDs are fabricated.

Do not run photographic cropping helpers on this record: it has no detected views. Generate/reuse real isolated object reference images through `marso-image`, inspect them, then supply the real reference index required by the scene-assets manifest, or use the supported individual generation route. Keep image-only design work separate from executing mesh jobs. Review required image/geometry gates before service submission.

Choose effort from intended screen coverage, closest view, functional requirements and reuse. Background work may be economical but must preserve correct proportions and supports. Hero effort earns visible construction/finish detail, not arbitrary subdivisions. For a multi-object scene establish one resource target and allocate it across unique masters/style sets. Explicit model/generate choices override category/size defaults; identify infeasible combinations before changing the route.
