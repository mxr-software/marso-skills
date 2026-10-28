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

Pass only parameters the live `describe()` lists. Do not use `wait_job` from inside Blender: it blocks the thread the job needs.

`crop_path` is read by Blender, so pass the crop's absolute path on Blender's machine; `assets.json` keeps the path the crop step wrote, which may be relative to the project folder.

Persist the verified `save_to.project_id` in the record. Before each generation submission and after resuming, compare a fresh `save_to_state` response using `manifest.py check-project`; reselect and verify on mismatch. Node ids belong to the original project. `import_scene_asset.copies` counts total instances, not additional duplicates. Preserve its `instances` array for multipart placement.

## What each step does in the project

- `scene_reference` uploads the crop as an image node, links it into an object-mode image-generation node, and runs that node with the prompt. The prompt refers to the linked image as `@crop`. `row` lays the asset's nodes out on its own row of the project canvas; use the asset's stored `row` for both the reference and mesh calls (0 for the first), so the canvas reads in plan order.
- `scene_mesh` runs 3D generation from the reference image, then PBR on the mesh. It does not import anything into Blender.
- Minting happens in Marso after PBR. It makes the asset simulation-ready at real-world scale. `mint_status` only reads the state.

## Jobs

- Start a job, record its id at once (`manifest.py record --job`), and return. Check it with `get_job` in a later tool call.
- Keep at most four jobs running. Starting more does not finish the scene sooner and makes failures harder to follow.
- When a job finishes, record its result before starting the next one. When it fails, record the error, read the log, and tell the user; retry once only for a cause you understand.
- After an interruption, run `manifest.py pending` and check every `running` job with `get_job` before submitting anything again.

## Settings

| Setting | Default | Notes |
| --- | --- | --- |
| `model` | `tripo_h3_1` | Read the model list and its options live; a user's choice wins. |
| `polygon_count` | 40000, or the plan's `polygon_count` | Clip to the nearest offered value at or below; the smallest offered when none is below. |
| `texture` | `standard` | Use a value the live options list. |

If the live options do not offer a default, say so and ask; do not send it.
