# Marso command workflow

This describes the inspected add-on implementation. Resolve installed capabilities before use. The default route is the official Blender MCP controlling Blender with Marso enabled; no separate hosted Marso connection is required.

## Access and asynchronous work

Prefer exposed Marso tools when they cover the requested operation. Through an authorized Blender Python tool, discover the enabled extension identifier from `bpy.context.preferences.addons` and verify it is Marso. It may be `bl_ext.<repository>.marso`; do not assume `import marso`. Import its `<module>.bridge.commands`, inspect `all_commands()` / `describe()`, then use `execute(name, params)` with the discovered schema. This is a version-bound internal interface, not a guarantee for every release.

Individual long operations return a `job_id`; follow it with `get_job`. Native batches return a `batch_id`; use batch status/item commands instead, as described in the batches reference. Never block Blender's main thread with `wait_job`, `batch_wait`, a polling loop or sleep: local stages need that thread to finish. An external HTTP client can use bounded waits. Marso's local HTTP Control Server is not itself an MCP endpoint. Do not change connection routes to bypass an interface restriction.

Inspect `list_jobs` after interruption. Do not reset a busy flag or cancel someone else's job to force progress. A terminal job is not proof that every item or material succeeded; inspect its result and log.

## Retexture project selection

Discover project commands before following this sequence. The reviewed source supports `save_to_state` and explicit project selection, but some installed builds lack those commands and save to the legacy `Blender AddOn` destination automatically. A manifest version alone does not establish these capabilities. On that legacy route, retain the add-on's destination and record the project actually used; do not invent project-selection commands or mutate internal graph IDs. If a particular destination is required, resolve that capability before generation.

When the installed commands support project selection, Retexture saves its graph into the .blend's chosen Marso Studio project:

1. Read `save_to_state`. Keep a valid existing destination unless the user requested another.
2. If a destination must be selected, call `list_studio_projects`, follow the job, then read `save_to_state` again.
3. Use `set_save_project` with a returned `project_id`. Match the user's named project. If several plausible destinations remain, ask; with nobody to answer, stop before generation and report the candidates.
4. If the task needs a new project and no destination was specified, state a descriptive task-based name and use `create_studio_project` with `name`. Follow its job; it also selects the project. Inspect refreshed state before retrying an uncertain creation.

Never invent project IDs. A deleted project must be resolved before retrying. Auto PBR does not use this Save to project mechanism.

### Match the user's project

Read the task, asset/kit contract and current Save to selection together. An existing value is appropriate only when it belongs to the intended task; a Library browser selection or an asset's source project is not automatically the output destination. Use an explicit user-specified project first. Otherwise preserve a clearly relevant current destination. For a new project/task without a relevant destination, choose a descriptive task name, list projects to avoid an accidental duplicate, then create/select it through the commands above. Ask only when plausible existing destinations remain ambiguous (unattended, follow step 3 above), never for permission to create a project the task already implies.

After `create_studio_project`, follow the job and read `save_to_state` back; the current implementation selects the new project too. Record its returned ID and graph identity where exposed, and save the .blend. Verify selection again when resuming/reopening; test save/reopen persistence explicitly when qualifying a new or suspect integration, rather than interrupting every routine project creation. Before generation, confirm the destination still matches the recorded project; never silently move pending work after changing it. Confirm actual output membership from job/graph evidence afterwards, not from the panel label alone.

If a project-specific task meets a legacy build without these controls, resolve the capability through an appropriate add-on update or another supported, explicitly targeted route before generation. Do not silently submit to `Blender AddOn`. After an uncertain project-creation outcome, refresh and reconcile the existing project rather than creating another. A manifest version alone cannot distinguish the older build from the new picker implementation.

## Relevant commands

Only pass parameters supported by the installed schema. These are the inspected names, not assistant-specific MCP tool names.

| Command | Relevant parameters / behaviour |
| --- | --- |
| `assembly_state` | `object_name`; read returned root, parts and prepared state. |
| `group_as_asset` | `object_names`, `name`; groups loose meshes under a new bottom-centre root, preserving world placement. Not a kit connector placement tool. |
| `prepare_assembly` | `object_name`, `size` (2048 or 4096), `bake_colours`; local asynchronous preparation. Replaces slots with one shared material. |
| `retexture_state` | Panel prompt, enhancement, reference/target state and busy state; active-object state is not a substitute for inspecting a named target. |
| `retexture` | `object_name`, `prompt`, `enhance`, `auto_uv`, `reference_path`, `reference_label`, `result` (`replace`, `new_object`, `add_material`). Pass each explicitly: a given value becomes the panel's default. |
| Retexture choices | `mode="blank"` (New) or `mode="edit"` (Edit), always with `workflow="multiview"`. Check shared users and source provenance before choosing `scope`, `family` or `source`. |
| `reset_look` (when exposed) | `object_name`; restores a retained original appearance/UV arrangement locally. Inspect `assembly_state.has_original` first and revalidate preparation afterwards; this is not a geometry rollback. |
| Native `batch_*` commands (when exposed) | Submission, status, item details, review, control and external bounded waits; follow the exact workflow in batches. |
| `pbr_state` | Inspect existing queue and status before generation. |
| `pbr_generate` | `object_names`; adds named objects and processes the pending/resubmittable queue, not necessarily only those names. |
| `pbr_remove` | `index`; can remove explicitly managed queue entries. Refresh indices after each removal. Do not discard unrelated work. |
| `image_material` | Exactly one of `image_asset_id` or `filepath`; optional `material_name`, `object_names`, `apply`, `tiling_mode`, `displacement`, `displacement_scale`. |
| `get_job` | `job_id`, optional `cursor` for new log entries. |
| `list_jobs` | Optional `active_only`; recover a running operation after interruption. |
| `list_failures` (when exposed) | Optional `limit` (1–200), `kind`; read durable failed/cancelled job diagnostics. Verify availability in the installed schema. |
| `viewport_screenshot` | Optional `max_px`; confirm the assistant actually receives the image. |

When Auto PBR has unrelated pending items, do not call `pbr_generate` as though it targets only your list: it processes the whole pending queue, and `object_names` only moves your meshes to the front. There is no per-call queue exclusion parameter. Ask the user how to treat the other items; with nobody to answer, leave the queue untouched, do not call `pbr_generate`, and report the pending items. Check each intended queue item and returned material application result for failures.

Before PBR-only submission, run the same upload UV and surface checks (preparation reference) as for Retexture. Existing colour textures and correct-looking shading do not establish that repeated parts have unique UVs for generated normal data.

For a condition image, 1.19.0 and later expose `condition_image_asset_id` on `retexture` and `pbr_generate`. A local call passes the file as `condition_image_path`; over the agent connection, use the ID of an image already in the account. For an ID alone, call `upload_image` with `add_node: false` (1.21.1 and later): it uploads, returns `image_asset_id` and adds no node. Its default adds a Load Image node meant to feed mesh generation, and that node stays unconnected when no generation follows. On an earlier add-on, reuse an asset ID a job already returned. New Texture defaults to a condition image made from the newly returned paint: follow conditioned PBR instead of starting the combined command. The direct graph client spells the field `conditioning_image_asset_id` on `run_project_pbr`.

Poll direct graph executions about every 30–60 s while queued and 15–30 s while running, outside Blender's main thread, without reporting each unchanged status. When intentionally testing a different condition image on the same mesh, use a fresh Studio PBR node: re-running a completed node can return its previous execution.

## Flat images and 2D materials

Use `tiling_mode="non_tiled"` for a one-off panel or printed design, `"already_tiled"` for seamless artwork whose PBR maps should also repeat, and `"make_tileable"` for a flat swatch whose opposing edges need to match. Select from the intended use and the actual input. Set the material’s physical repeat size in Blender and preview several repeats for a tiling job.

When surface height matters, request `displacement=true` and choose `displacement_scale` in metres to suit the relief. Inspect the returned height map and displacement under grazing light on sufficiently subdivided geometry. Leave displacement off for flat print. Use `apply=false` to create the material alone or assign only selected roles yourself; automatic application replaces all slots on target meshes.

Retexture needs UVs; the add-on gives a UV-mapped mesh with no base-colour texture a blank one. Prefer agent-authored or verified existing UVs and set `auto_uv: false` on the supported single-mesh route. `auto_uv` handles missing UVs; it does not fix bad existing UVs and does not prevent automatic assembly preparation. Use the authored-layout handoff (preparation reference) to preserve a curated atlas. Reference paths must resolve on Blender's machine and be accepted by the current connection; a client attachment is not automatically a local Blender path.

## Recovery

Keep source and output identifiers distinct. In the reviewed Blender Retexture result, `mesh_asset_id` identifies the original uploaded mesh, while `pbr_asset_id` identifies the generated PBR result. The edited mesh is on the linked Studio edit node. Check the graph/output meaning before importing an asset or branching a style; do not assume every returned asset ID names the finished appearance.

Retexture may reuse a completed edit when only PBR failed. Follow the existing result rather than launching duplicate edits. Older resume fingerprints use geometry counts; newer builds use surface revisions. Cloud-source reuse and pending batch guards are separate decisions; their supported inputs and limitations are described in the batches reference. After geometry, UV or appearance changes, do not assume a resumed result reflects the edits. Run `reset_look` on the target, or make a fresh working copy after a geometry or UV fix, then retexture again; never upload a locally repainted mesh, and do not silently alter internal resume records. If one repair attempt reproduces the same unexplained failure, report the job evidence and stop automatic resubmission.
