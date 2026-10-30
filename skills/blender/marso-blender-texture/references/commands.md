# Marso command workflow

This describes the inspected add-on implementation. Resolve installed capabilities before use. The default route is the official Blender MCP controlling Blender with Marso enabled; no separate hosted Marso connection is required.

## Access and asynchronous work

Prefer exposed Marso tools when they cover the requested operation. Through an authorized Blender Python tool, discover the enabled extension identifier from `bpy.context.preferences.addons` and verify it is Marso. It may be `bl_ext.<repository>.marso`; do not assume `import marso`. Import its `<module>.bridge.commands`, inspect `all_commands()` / `describe()`, then use `execute(name, params)` with the discovered schema. This is a version-bound internal interface, not a guarantee for every release.

Individual long operations return a `job_id`; follow it with `get_job`. Native batches return a `batch_id`; use batch status/item commands instead, as described in [batches](batches.md). Never block Blender's main thread with `wait_job`, `batch_wait`, a polling loop or sleep: local stages need that thread to finish. An external HTTP client can use bounded waits. Marso's local HTTP Control Server is not itself an MCP endpoint. Do not change connection routes to bypass an interface restriction.

Inspect `list_jobs` after interruption. Do not reset a busy flag or cancel someone else's job to force progress. A terminal job is not proof that every item or material succeeded; inspect its result and log.

## Retexture project selection

Discover project commands before following this sequence. The reviewed source supports `save_to_state` and explicit project selection, but a locally installed build also reporting 1.7.1 lacked those commands and used the legacy `Blender AddOn` destination automatically. A manifest version alone does not establish these capabilities. On that legacy route, retain the add-on's destination and record the project actually used; do not invent project-selection commands or mutate internal graph IDs. If a particular destination is required, resolve that capability before generation.

When the installed commands support project selection, Retexture saves its graph into the .blend's chosen Marso Studio project:

1. Read `save_to_state`. Keep a valid existing destination unless the user requested another.
2. If a destination must be selected, call `list_studio_projects`, follow the job, then read `save_to_state` again.
3. Use `set_save_project` with a returned `project_id`. Match the user's named project; ask when multiple plausible destinations leave intent unclear.
4. If the task needs a new project and no destination was specified, state a descriptive task-based name and use `create_studio_project` with `name`. Follow its job; it also selects the project. Inspect refreshed state before retrying an uncertain creation.

Never invent project IDs. A deleted project must be resolved before retrying. Auto PBR does not use this Save to project mechanism.

### Match the user's project

Read the task, asset/kit contract and current Save to selection together. An existing value is appropriate only when it belongs to the intended task; a Library browser selection or an asset's source project is not automatically the output destination. Use an explicit user-specified project first. Otherwise preserve a clearly relevant current destination. For a new project/task without a relevant destination, choose a descriptive task name, list projects to avoid an accidental duplicate, then create/select it through the commands above. Ask when plausible existing destinations remain ambiguous, rather than asking for permission to create a project already implied by the task.

After `create_studio_project`, follow the job and read `save_to_state` back; the current implementation selects the new project too. Record its returned ID and the graph identity where exposed. Save the .blend and verify the selection survives reopening. Before each generation, confirm the destination still matches the recorded project; never silently move pending work after changing it. Confirm actual output membership from job/graph evidence afterwards, not from the panel label alone.

If a project-specific task meets a legacy build without these controls, resolve the capability through an appropriate add-on update or another supported, explicitly targeted route before generation. Do not silently submit to `Blender AddOn`. After an uncertain project-creation outcome, refresh and reconcile the existing project rather than creating another. A manifest version alone cannot distinguish the older build from the new picker implementation.

## Relevant commands

Only pass parameters supported by the installed schema. These are the inspected names, not assistant-specific MCP tool names.

| Command | Relevant parameters / behaviour |
| --- | --- |
| `assembly_state` | `object_name`; read returned root, parts and prepared state. |
| `group_as_asset` | `object_names`, `name`; groups loose meshes under a new bottom-centre root, preserving world placement. Not a kit connector placement tool. |
| `prepare_assembly` | `object_name`, `size` (2048 or 4096), `bake_colours`; local asynchronous preparation. Replaces slots with one shared material. |
| `retexture_state` | Panel prompt, enhancement, reference/target state and busy state; active-object state is not a substitute for inspecting a named target. |
| `retexture` | `object_name`, `prompt`, `enhance`, `auto_uv`, `reference_path`, `reference_label`; explicit target and appearance choices avoid stale UI state. |
| Newer `retexture` options | `scope: "target" or "family"`, explicit `family` where supported, `source: "auto" or "upload"`; inspect shared users and source provenance before choosing. |
| `reset_look` (when exposed) | `object_name`; restores a retained original appearance/UV arrangement locally. Inspect `assembly_state.has_original` first and revalidate preparation afterwards; this is not a geometry rollback. |
| Native `batch_*` commands (when exposed) | Submission, status, item details, review, control and external bounded waits; follow the exact workflow in [batches](batches.md). |
| `pbr_state` | Inspect existing queue and status before generation. |
| `pbr_generate` | `object_names`; adds named objects and processes the pending/resubmittable queue, not necessarily only those names. |
| `pbr_remove` | `index`; can remove explicitly managed queue entries. Refresh indices after each removal. Do not discard unrelated work. |
| `image_material` | Exactly one of `image_asset_id` or `filepath`; optional `material_name`, `object_names`, `apply`. |
| `get_job` | `job_id`, optional `cursor` for new log entries. |
| `list_jobs` | Optional `active_only`; recover a running operation after interruption. |
| `list_failures` (when exposed) | Optional `limit` (1–200), `kind`; read durable failed/cancelled job diagnostics. Verify availability in the installed schema. |
| `viewport_screenshot` | Optional `max_px`; confirm the assistant actually receives the image. |

When Auto PBR has unrelated pending items, do not call `pbr_generate` as though it targets only your list. Resolve the queue with the user or use another appropriate isolated route; there is no inspected per-call queue exclusion parameter. Check each intended queue item and returned material application result for failures.

For `image_material`, local images support PNG/JPEG/WebP up to 10 MiB in the inspected implementation. It does not unwrap or set physical pattern scale. `apply: true` replaces every slot on target meshes. For selected faces or material roles, use `apply: false`, then assign the returned material through Blender only to those faces/slots. Verify the face mapping, not just material names.

Retexture requires UVs and a base-colour texture. Prefer agent-authored or verified existing UVs and set `auto_uv: false` on the supported single-mesh route. `auto_uv` handles missing UVs; it does not fix bad existing UVs and does not prevent automatic assembly preparation. Use the [authored-layout handoff](preparation.md#agent-authored-layouts) to preserve a curated atlas. Reference paths must resolve on Blender's machine and be accepted by the current connection; a client attachment is not automatically a local Blender path.

## Recovery

Keep source and output identifiers distinct. In the reviewed Blender Retexture result, `mesh_asset_id` identifies the original uploaded mesh, while `pbr_asset_id` identifies the generated PBR result. The edited mesh is on the linked Studio edit node. Check the graph/output meaning before importing an asset or branching a style; do not assume every returned asset ID names the finished appearance.

Retexture may reuse a completed edit when only PBR failed. Follow the existing result rather than launching duplicate edits. Older resume fingerprints use geometry counts; newer builds use surface revisions. Cloud-source reuse and pending batch guards are separate decisions; their supported inputs and limitations are described in [batches](batches.md). After geometry, UV or appearance changes, do not assume a resumed result reflects the edits. Use a clean, independent working target without old run metadata or a supported reset if available; do not silently alter internal resume records. If one repair attempt reproduces the same unexplained failure, report the job evidence and stop automatic resubmission.
