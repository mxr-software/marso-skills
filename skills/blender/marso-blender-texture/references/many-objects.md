# Texture many objects

Use when one run has more than one New Texture target: kit masters, set piece masters and their variants, or scene props. Work stage by stage, not object by object. Marso runs them side by side, so the time is lost in waiting between them, not in the runs.

Several Edit Texture targets go in one native batch with `review: []`. Several PBR-only targets go in one `pbr_generate` call, with every name in `object_names`. The `retexture` and `create_3d_asset` commands take one target and refuse a second call while one runs (code `busy`).

## Before any run

1. Every new or remodelled model has its approval or its waiver.
2. Every target has its UV layout, its working copy and its prompt.
3. The Studio project is selected and verified.
4. The run record exists, with one row for each target ([run record](#run-record)).
5. The .blend file is saved at the path it will keep. A batch Retexture item applies its maps only in the file it was submitted from: an unsaved file, or a Save As to another path, holds every item before apply.

## Pilot only an unproven method

Send every target together unless the method is unproven:

- **A kit:** one representative part's paint first, then every other part together. Compare all the paints side by side before any PBR.
- **A reference-image kit:** keep the pilot the kit skill sets for it.
- **Looks authored as edited images or an edited grid:** keep the pilot that route sets.
- **Set piece masters, variants and props textured from a text look:** no pilot.

A pilot is a batch of its own, sent first. While it runs, do the local work listed under [Between checks](#between-checks).

## One batch for every target (Marso 1.22.0 and later)

When the installed `batch_review` takes `condition_image_asset_id`, send all the targets in one `batch_submit`, as the conditioned PBR reference describes for a single item:

1. One `retexture` item for each target, each with `mode: "blank"` and `review: ["edit"]`. A variant is its own item on the source object, with `result: "new_object"` and a `name`.
2. The add-on prepares, submits and follows every item itself. Leave those targets to it: add no `retexture`, PBR or preparation call for them.
3. Read `batch_status` about every 30 to 60 seconds. At each read, serve every item in `needs_review`:
   - bring its paint into Blender and accept it, or reject it;
   - capture it unlit and start its `edit_scene_image`. Start one for every accepted paint in this read before other work; these run side by side.
4. As each condition image lands, answer its item with `batch_review`, carrying `condition_image_asset_id`. One call can carry several decisions.
5. The add-on runs each PBR and applies each material. Inspect every applied target under changed lighting.
6. A rejected target is repaired alone and sent again as a new item; the others continue.

For a kit, hold the approvals until every paint has landed and been compared, then approve them in one `batch_review` call.

## On an earlier add-on: the staged route, stage by stage

1. Create each target's nodes and start its Retexture, one target after another, without waiting for any to finish. Each is its own run on its own node.
2. Submit from one background thread, in turn. A submission returns its execution ID in seconds, or in about a minute while Marso settles a fresh upload. On these add-ons a submission has no idempotency key, so submissions fired at the same instant can time out and be sent twice.
3. If a submission times out or is rate limited, read that node with `fetch_node_properties`. When it holds an `execution_id`, follow that run; send again only when it holds none.
4. Check every outstanding run in one call with `poll_execution`. A run has finished when its `status` is `SUCCEEDED`, `PARTIAL_SUCCEEDED`, `FAILED` or `CANCELED`. `PARTIAL_SUCCEEDED` still returns a result: inspect it for missing maps.
5. At each check, move every finished target on one stage: paints to their Image Edits together, accepted conditions to their PBR runs together, finished PBR to its target.

## Between checks

- Return from each status read at once. A wait loop or a sleep on Blender's main thread blocks the other stages.
- Report progress when a status changes, not at every read.
- If a read times out, read the run record and try again. A timeout is not a failed run and not a reason to resubmit, and never a reason to patch the add-on: an item it cannot collect stays pending.
- A submission can time out while Marso still accepts it. On the batch route the add-on recovers it: from 1.22.1 it sends the same submission again under its idempotency key, so Marso returns the first run and charges once. Wait for the item rather than submitting a new one; a held item's `batch_control retry` is the same submission again. On the staged route, read the node for an `execution_id` before sending again.

Do local work that leaves the submitted targets alone:

- the camera and capture set-up for the paints;
- the Image Edit prompt for each target;
- a repaired target's UV layout and working copy, before it is sent again;
- tags, the placement list and review renders of finished targets.

Keep each piece short enough to return before the next read. Leave a submitted target's mesh, UVs, materials and names unchanged until its PBR is applied: a batch holds an item whose target changed.

## Run record

Keep one JSON file in the run folder with one row for each target:

- the object, its prompt, and the batch ID and item key, or the staged node IDs;
- the painted mesh asset and whether the paint was accepted;
- the capture, the Image Edit request and the condition image chosen;
- the PBR asset, the status, and the time of each change.

After an interruption, read the record, then `batch_list` and `batch_status`, or every unfinished execution, before starting anything again.

Done when every row is applied and inspected, or reported with its error.
