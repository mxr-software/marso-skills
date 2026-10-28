# Metadata that travels with each asset

Every asset in `asset_plan.json` is a complete handoff record. Whatever makes the asset, generator or modeller, receives this block unchanged, and the finished asset keeps it so the scene can be reassembled.

| Field | Source | Why it travels |
| --- | --- | --- |
| `asset_id` | the plan | Stable handle for the crop folder, the job and the application object. |
| `global_id` | representative node | Links back to the graph; `members` lists every node the asset stands for. |
| `label`, `description`, `category` | the node's best view | The subject line of the brief and the application object's name. |
| `route`, `route_reason` | rules in [route](route.md), edited in review | Which skill makes it and why. |
| `count`, `count_at_least`, `count_at_most` | clusters and identity groups | How many to instance after one is made; the range is the honest answer. |
| `cluster_id`, `identity_groups` | the graph | Keeps variant families and unresolved duplicates visible. |
| `size_m`, `size_basis`, `size_confidence` | the view most sure of the size | Real-world dimensions for scale correction after generation and for modelling. |
| `parent`, `relation` | the graph | What holds it, so placement and masking are known. |
| `children` | every node whose parent is a member | What rests on it; masked in the crop, placed on it in the scene. |
| `best_view` | `view_scores.json` or the script's own ranking | `image_id`, `local_id` and normalised `bbox` of the view the crop was taken from. |
| `source_images` | `seen_in` views | Every image that shows the object, for a second reference if the first fails. |
| `flags` | the rules | What the user was asked to check. |

Keep the block as JSON beside the finished asset, or as custom properties on the application object where the modelling skill supports them. Do not rename `global_id`s or `asset_id`s downstream; they are the only link between a mesh and the photograph it came from.

Record alongside, after the work is done, the generator model and settings or the modelling skill used, the job or output identifiers, and any scale correction applied. The plan does not pre-fill those; a plan is not proof that generation ran.
