# Scene polygon budget

Establish a budget before bulk creation from intended use, target hardware when relevant, screen coverage, hero/background roles, unique assets, instances and material variants. Propose reasonable provisional targets where the brief permits; ask about material unknowns once rather than interviewing for every prop.

Use the user's preferred mesh options where compatible with live capabilities. Allocate per-asset `polygon_count` in `asset_plan.json` and record reasoning/limits in `review`. Count modelled and reused assets too.

Track unique geometry separately from the count across instances. Sharing can save memory without eliminating traversal/shading work. Texture images, displacement, subdivision and buffers also affect GPU memory. Generator polygon targets are not measured triangle counts; inspect imports and update the budget.

## Optional helper presets

`plan_assets.py --polycount` writes a provisional value on generate-route entries; `crop_objects.py` copies it into briefs. Without it, no value is written. This is not a live validator or scene allocator.

| Argument | Provisional value |
| --- | --- |
| A positive whole number | That target on each generated asset |
| `by-size` | Largest dimension below 0.3 m: 40000; below 1 m: 50000; below 2 m: 100000; otherwise 250000 |

Unknown dimensions receive the smallest preset; that does not establish the right detail level. Prefer purposeful allocation over size-only presets. A tiny hero mechanism may need more detail than a large flat cabinet.

## Reconcile capabilities

Read the selected model's live options and actual command schema. Use supported values within agreed ceilings; never silently round upward. If the lowest value exceeds a strict cap, propose a compatible model or an authorized reduction workflow with a preserved original and validated result. Keep the requested ceiling distinct from the service setting and final measured count. Do not promise fixed VRAM usage from these numbers.
