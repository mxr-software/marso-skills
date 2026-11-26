# Several meshes in one run

Use when one run generates more than one mesh: the generated parts of a set piece, or a group of props. The single route works from one image slot and refuses a second call while one runs, so a loop of it makes each mesh wait for the last. This route makes the reference images side by side and sends the meshes as one batch.

## 1. Reference images, side by side

- **From a description:** call `generate_scene_image` with `mode: "object"`, the prompt and a new `request_id` for each mesh. This command takes no generate lock and leaves the Generate panel's image alone. Each result gives `node.node_id`, `image_asset_id` and `image_path`.
- **From an object photo:** call `scene_reference` with `label`, `crop_path`, `prompt` and a `row` of its own for each mesh. It generates a new object reference from the photo, which the prompt names as `@crop`. Each result gives `generation_node_id`, `image_asset_id` and `image_path`. Four of these talk to Marso at once, at authoring time; the rest queue in the add-on.

Start every reference without waiting for the one before. About every 30 to 60 seconds, read every job in one Blender call, with one `get_job` for each `job_id`; `scene_image_result` reads a request by its `request_id`. Record each node ID and image asset ID as it arrives.

Inspect all the reference images together before any mesh. Each shows the subject alone and whole, on a plain background, in its own proportions. Make a failed one again, and send the batch once every reference is accepted.

## 2. One batch for the meshes

Discover `batch_submit`, `batch_status`, `batch_item`, `batch_review` and `batch_control` first. Save the exact request in the run folder, then send one `scene_asset` item for each mesh:

```json
{
  "request_id": "<new-stable-request-id>",
  "name": "Stall masters",
  "items": [{
    "key": "sunhat",
    "pipeline": "scene_asset",
    "start_at": "mesh",
    "label": "sunhat",
    "generation_node_id": "<the reference's node ID>",
    "image_asset_id": "<the reference's image asset ID>",
    "mesh": {"model": "<selected-live-model>", "polygon_count": "<resolved count, as a number>"},
    "review": ["mesh"]
  }]
}
```

- The batch saves into the Save to project. Pass `project_id` only for a project in the list fetched this session with `list_studio_projects`.
- `start_at: "mesh"` begins from the accepted reference. `generation_node_id` is the image node's ID from step 1 and `image_asset_id` is its image.
- `mesh` takes the resolved `model`, `polygon_count` and `texture`. State each one that applies: left out, an option takes the model's own default, not the panel's setting or a recorded preference. An option the model does not offer is refused, not replaced.
- `review: ["mesh"]` holds each item after its mesh. Read the item with `batch_item`: its `mesh` stage outputs give `mesh_asset_id` and, when Marso has a thumbnail, `review_file`. Answer with `batch_review`: `approve` continues to PBR and `reject` ends the item.
- When the user asked to review the meshes, the decision is theirs: show every `review_file` together and pass their answers on. With no review point from the user, the hold is this skill's own check: answer it yourself and record the meshes as not user-reviewed. Pass `review: []` only when the user has waived the check.
- Reuse a `request_id` only to repeat the identical request after an uncertain reply.

The add-on submits every item at once and advances each one itself. Leave the batch's meshes to it: add no `scene_mesh`, `create_3d_asset` or PBR call for them.

Read `batch_status` in short calls about every 30 to 60 seconds, and do local work between reads. `batch_items` returns every item with its stage outputs in one read. A `batch_id` is not a `get_job` ID. `settled` means nothing can progress without you, not that every item succeeded.

## 3. Bring them in

1. Read each finished item's `pbr_asset_id` from its `pbr` stage outputs, and keep its `mesh_asset_id` from the `mesh` stage. Hand both on with the asset: a later New Texture of that mesh starts from the mesh asset.
2. Call `mint_status` with all the IDs at once, about every minute, for up to ten minutes. Each asset reports `minted`, `minting` or `failed`.
3. Import each minted asset with `import_scene_asset`: `pbr_asset_id`, `name` and `collection`. Only a minted asset has real-world scale, and `require_minted` (default true) refuses any other.
4. Report every asset that failed, errored or was rejected. Report one still minting after ten minutes as not yet imported, with its ID, so it can be imported later.

## Without batch commands

Start one `scene_mesh` job for each accepted reference, without waiting between them: `generation_node_id`, `image_asset_id`, `label`, `row` and the mesh options. Follow them with `get_job`. Each runs its mesh and its PBR with no hold between, so inspect the references with more care first. Report that the batch commands were absent.

Done when every mesh is imported with its `pbr_asset_id` and `mesh_asset_id` recorded, or reported with its error.
