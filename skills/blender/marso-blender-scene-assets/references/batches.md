# Add-on-managed scene batches

Prefer this route when the loaded add-on exposes `batch_submit`, `batch_status`, `batch_item`, `batch_review` and `batch_control`. A checkout or version label does not prove the running Blender session has them. Discover commands first. Without them, use the individual-command fallback in [Studio chain](studio-chain.md); do not submit the same asset through both routes.

The add-on submits eligible independent operations, monitors them internally and explicitly advances each approved dependency while Blender remains running. Marso queues cloud execution; a network-worker limit is not a limit on outstanding cloud jobs. There is no need for the agent to poll merely to free a submission slot. The inspected implementation offers status/long-poll monitoring, not push notifications that wake an inactive chat.

## Submit after the plan and library decisions

Resolve the Studio project and initialise the local asset manifest as usual. Include only generate-route assets the user chose to make. Keep library reuse, modelling, instancing and kit handoffs outside the generation batch.

Save the exact request locally before sending it. Use a fresh nonempty `request_id` per new batch and reuse it with the identical request after an uncertain reply; the implementation deduplicates by id, not by payload equality. Never reuse an id for changed work. Set `key` to the local plan's stable asset id, retain its canvas `row`, and pass the verified project id explicitly. One request supports up to 1000 items in the inspected schema; that is a payload limit, not a cloud execution limit. Split larger plans without inventing dependencies between independent items.

Example request shape; replace paths/ids and add resolved, live-supported polygon/texture options to `mesh` only when applicable. Do not inherit model-specific defaults from an example:

```json
{
  "request_id": "<new-stable-request-id>",
  "name": "Room assets",
  "project_id": "<verified-project-id>",
  "items": [{
    "key": "a001",
    "pipeline": "scene_asset",
    "row": 0,
    "label": "chair",
    "crop_path": "<absolute-path-to-reviewed-crop.png>",
    "prompt": "<the complete reference brief>",
    "framing": "as_is",
    "mesh": {"model": "<selected-live-model>"},
    "review": ["image", "mesh"]
  }]
}
```

Use `framing: "as_is"` for an already square, correctly padded crop; supported `square` framing can prepare another input but should not add redundant margins. Inspect the generated output either way. For an already approved reference, `start_at: "mesh"` requires its verified `generation_node_id` and `image_asset_id`; keep `review: ["mesh"]` unless that geometry checkpoint was explicitly waived.

Each item's stages are image → mesh → PBR. Unlike standalone `scene_mesh`, the batch mesh stage does not also start PBR. Never call `scene_mesh` or another PBR operation for an item already owned by this chain. `depends_on` names other item keys in the same request and waits for those items to succeed; normal stages within one item already have their dependencies. Include only genuine additional dependencies.

## Observe and review

| Command | Use |
| --- | --- |
| `batch_status` | `batch_id`, optional `since`, `limit`, `states`; compact progress and changed items. |
| `batch_item` | `batch_id`, `item_id`; complete stage ids, outputs, warnings and history. The inspected implementation also accepts the submitted key as `item_id`. |
| `batch_items` (when exposed) | `batch_id`, optional `after`, `limit`, `states`, `keys`; full item records in submission order. Follow `next_after` until `complete`. |
| `batch_review` | `batch_id`, `decisions: [{key, decision: "approve" or "reject", note}]`; apply the user's decision to the stage currently awaiting review. |
| `batch_wait` | `batch_id`, `since`, `timeout`, `until: "change" or "settled"`; optional bounded external wait. |
| `batch_list` | Recover known batches after reconnect. |
| `batch_control` | `batch_id`, `action: "pause", "resume", "cancel" or "retry"`; retry requires explicit `item_ids`. |

Use `batch_wait` only through an external connection that dispatches it off Blender's main thread, with a timeout within the host's limit (normally no more than 60 seconds per call). Calling it from a Blender Python execution block still occupies Blender's main thread: use short `batch_status` calls in that route. The remote Agent Connection may allow monitoring/pause/cancel but prohibit submission, approval, resume or retry. Respect that policy and use the user's established authorized Blender MCP route; do not circumvent a restricted connection.

`settled` means nothing can progress without intervention, not that every asset succeeded. Inspect counts, `needs_review`, `held`, `failed` and cancellation state. Open each review image before presenting it. Mesh thumbnails may be missing or inadequate for geometry approval; obtain an appropriate inspectable mesh/view through a supported route before recording approval. Rejecting stops the item; do not approve a bad result merely to advance the queue. Pass an empty review list only for explicitly waived checkpoints. Batch review advances execution; a local manifest review alone does not.

Status summaries are bounded: review/held/failed lists are short, and `changed` can have `more > 0`. When the response includes `next_since` and `complete`, follow `since = next_since` until `complete`; never jump to `version` while pages remain. Keep separate cursors for state-filtered views, or use unfiltered changes for the completion ledger. Use `batch_items` with `after = next_after` to reconcile full records against saved request keys. A state-filtered traversal is a changing view, not an immutable snapshot; reconcile unfiltered records and final counts before claiming completion. On older builds without pagination, use known-key `batch_item` calls for omitted results.

## Keep the placement handoff current

Save batch id, exact request, asset-key mapping and returned item snapshots beside `assets.json`. Batch ids, item ids and execution ids are not legacy `get_job` ids. The add-on owns scheduling; do not use `manifest.py pending` to launch another job for these assets.

Mirror completed stage results into the existing manifest using `manifest.py record --result <file>` (or `--json`), without inventing job ids:

| Manifest stage | Fields from the complete `batch_item` snapshot |
| --- | --- |
| `reference` | `stages.image.ids.crop_asset_id`, `image_node_id`; `stages.image.outputs.generation_node_id`, `image_asset_id`; map `review_file` to `image_path`. |
| `mesh` | Only after PBR succeeds: `stages.mesh.outputs.mesh_node_id` plus `stages.pbr.outputs.pbr_node_id` and `pbr_asset_id`. |

Record the user's image decision locally with `manifest.py review` as well as in `batch_review`, retaining mesh approval evidence in the batch snapshots. For a chain starting at mesh, retain the existing approved reference record rather than manufacturing an image-stage result. Store exact failures through `--error` on the corresponding manifest stage (mesh or PBR failures map to its combined `mesh` stage); retain their actual stage details separately. Do not mark a failure as a successful result.

Then check mint status and use the existing import/placement handoff. A successful PBR stage does not replace the mint check. A completed batch does not mean its assets have been imported or visually accepted.

## Pause, recovery and limits

Pause stops new submissions/advancement while existing cloud runs remain monitored. Cancel stops future work; the inspected API cannot cancel submitted cloud executions, whose outputs are retained. Never report those executions as cancelled. Retry is an explicit failed/held-stage action, not permission to regenerate every warning. A held item cannot be rejected with `batch_review`: use `batch_control cancel` with explicit `item_ids` to stop it. Review rejection applies only to `awaiting_review`. Retexture's reprepare action does not apply to a scene-asset generation item.

Recover existing batches before submitting replacements. Review unknown outcomes and source/project mismatches. Newer builds recheck a missing execution id over a bounded grace window, then hold uncertain non-PBR submissions instead of automatically resending them. The grace window is not a service guarantee; inspect the node and execution evidence before an explicit retry that could duplicate work. PBR can reuse the same node's execution where that API contract is verified. Live recovery still needs validation.

In supporting builds, `batches_restarting` means the previous engine is handing over its remaining work. Return control to Blender, wait briefly outside its main thread, then repeat the call; existing batches resume automatically after handover. Preserve the identical request and `request_id` when repeating a submission. Do not submit a replacement batch or manually advance its stages. If handover persists, inspect diagnostics rather than looping rapidly or repeatedly restarting. Older builds without this fix should not be reloaded during active local work.
