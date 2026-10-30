# The Studio chain

These are Marso Blender add-on bridge commands. Reach them through the official Blender MCP: in an authorised Blender Python execution tool, find the enabled Marso extension's module through `bpy.context.preferences.addons` (it may be namespaced, such as `bl_ext.<repository>.marso`; do not assume `import marso`), import `<module>.bridge.commands`, read `all_commands()` and each entry's `describe()`, and call `execute(name, params)`. If a required scene command below is missing from `all_commands()`, report it and stop; do not build the chain from other calls. A missing `find_in_library` alone can use the documented `--skip-library` route with disclosure.

## Commands

| Command | Parameters | Returns (job result) |
| --- | --- | --- |
| `create_studio_project` | `name` | a job; afterwards `save_to_state` shows the new project selected |
| `save_to_state` | none | the project new work is saved into |
| `set_save_project` | `project_id` | selects that project |
| `scene_reference` | `label`, `crop_path`, `prompt`, `row` | `crop_asset_id`, `image_node_id`, `generation_node_id`, `image_asset_id`, `image_path` |
| `scene_mesh` | `generation_node_id`, `image_asset_id`, `model`, `polygon_count`, `texture`, `label`, `row` | `mesh_node_id`, `pbr_node_id`, `pbr_asset_id`, `options` |
| `find_in_library` | `query`, `image_path`, optional `kinds`, `limit`, `thumbnails` | `results`: one per library asset, with `name`, `verdict`, `image_score`, `text_score`, `pbr_asset_id`, `thumbnail_path`; and the `thresholds`. Answers at once, no job. See [library check](library-check.md). |
| `mint_status` | `asset_ids` (a list) | each id mapped to `minted`, `minting`, `failed` or `not_minted` |
| `import_scene_asset` | `pbr_asset_id`, `name`, `collection`, `copies`, `require_minted` | `objects`, `instances`, `dimensions_m`, `minted` (used by `marso-blender-place-scene`) |
| `get_job` | `job_id`, optional `cursor` | the job's state, log and, when finished, its result |
| `list_failures` (when exposed) | optional `limit` (1–200), `kind` | persisted failed/cancelled job records with available stage, ids and error details; inspect the live schema first |

Pass only parameters the live `describe()` lists. Do not use `wait_job` from inside Blender: it blocks the thread the job needs.

`crop_path` is read by Blender, so pass the crop's absolute path on Blender's machine; `assets.json` keeps the path the crop step wrote, which may be relative to the project folder.

Persist the verified `save_to.project_id` in the record. Before each generation submission and after resuming, compare a fresh `save_to_state` response using `manifest.py check-project`; reselect and verify on mismatch. Node ids belong to the original project. `import_scene_asset.copies` counts total instances, not additional duplicates. Preserve its `instances` array for multipart placement.

## What each step does in the project

- `scene_reference` uploads the crop as an image node, links it into an object-mode image-generation node, and runs that node with the prompt. The prompt refers to the linked image as `@crop`. `row` lays the asset's nodes out on its own row of the project canvas; use the asset's stored `row` for both the reference and mesh calls (0 for the first), so the canvas reads in plan order.
- `scene_mesh` runs 3D generation from the reference image, then PBR on the mesh. It does not import anything into Blender.
- Minting happens in Marso after PBR. `mint_status` reads service state; verify actual scale and physics separately before claiming simulation readiness.

## Jobs

For the native batch route, use [batch orchestration](batches.md) instead of this individual-job procedure. Cloud waiting is managed by the add-on. Do not mix schedulers for the same item.

- Start a job, record its id at once (`manifest.py record --job`), and return. Check it with `get_job` in a later tool call.
- Check the installed scheduling behaviour. Older builds hold four slots for complete scene jobs; newer builds hold bounded slots only for network requests and release them during cloud waits. Neither establishes a Marso canvas outstanding-job cap. Use native batches for large sets instead of creating hundreds of individual waiting threads.
- When a job finishes, record its result before starting the next one. When it fails, record the error, read the log, and tell the user; retry once only for a diagnosed cause within existing retry authorization. Without it, present the correction and wait for the user before regenerating; an uncertain outcome must be reconciled first.
- After an interruption, run `manifest.py pending` and check every `running` job with `get_job` before submitting anything again.

Respect reference approval before mesh submission and the installed local limits; keep eligible submissions moving without a fixed-batch barrier. Check individual active jobs in short later calls, using cursors for new log entries. Roughly 30–60 seconds is a fallback observation cadence where no notification/backoff guidance exists; native batch monitoring does not need the agent to poll each cloud execution. Interleave bounded local tasks and keep user progress updates at the host's required cadence.

Save returned job start/finish times separately from the time the agent observed and recorded completion. A long polling gap measures delayed observation, not necessarily slow generation. Give a batch ETA only as a qualified range based on comparable recent completions and current occupancy; exclude user review pauses from claims about service latency. Minted status still needs checking, even when previous jobs were already minted by the first poll.

On supporting builds, `get_job.details` and `list_failures` preserve diagnostic identifiers and service error fields. Save the relevant job snapshot/failure record beside `assets.json`, and record the stage's error through the manifest. Do not pass a failure object as a successful `--result`. On older builds, retain the exact returned message and disclose any missing identifiers.

## Settings

Use [settings and scene budgets](settings.md) for both native and individual routes. Resolve the user's preferred model/options against live capabilities. The helper has no built-in generator, polygon or texture default. Pass supported effective options, preserve strict ceilings and omit unsupported fields; never silently round a budget upward. Verify the operation's returned effective settings, which may differ from panel defaults.
