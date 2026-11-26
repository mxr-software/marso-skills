# Condition PBR on the new paint

PBR prediction uses visual cues about how the object reacts to light. New Texture paint is unlit, so the default after New Texture is to condition PBR on a lit image of that paint. A mesh generated from an image is different: its source image supplies the condition automatically.

Contents: [Sequence](#sequence) · [Batch route](#batch-route-marso-1220-and-later) · [Bring the paint into Blender](#bring-the-paint-into-blender) · [Accept the paint](#accept-the-paint-before-conditioning) · [Make the condition](#make-the-condition) · [Lineage](#lineage-and-what-studio-shows) · [Staged route](#staged-route-for-earlier-add-ons)

## Sequence

Run this without being asked whenever New Texture is followed by PBR. An asset you modelled has no existing look: Edit Texture over a bake of your own stand-in colours is still New Texture here.

1. Retexture alone with `mode="blank"` and `workflow="multiview"`. The combined `retexture` command starts PBR with no pause, so use the [batch route](#batch-route-marso-1220-and-later), or the [staged route](#staged-route-for-earlier-add-ons) on an earlier add-on.
2. [Bring the paint into Blender](#bring-the-paint-into-blender) and accept it: inspect the unlit result for every requested material region.
3. Make and accept the condition image from that paint.
4. Run PBR on the accepted paint, passing the accepted condition.
5. Record the lineage and use the returned material unchanged.

**PBR always runs.** If the paint cannot be brought into Blender, or the condition image cannot be made, continue to PBR with no condition image. Inspect every requested region on the applied material under changed lighting. Report the paint as not reviewed and the PBR as unconditioned, with the error that caused it.

If the user supplied a real photograph of the same object and finish (cleaned if needed; never a render or drawing), it is already a lighting reference, so skip the staging. An image you rendered or generated before Retexture does not qualify: its lighting belongs to stand-in materials, not the new paint. For a supplied photo, Marso for Blender 1.19.0 accepts its account image ID as `condition_image_asset_id` on the combined Retexture → PBR run. The separate Retexture reference controls the paint. Check the installed command schema on older builds.

## Batch route (Marso 1.22.0 and later)

From Marso for Blender 1.22.0 a batch runs the whole sequence through exposed commands, for one target or for many. Read the `batch_review` schema with `describe()`: when a decision takes `condition_image_asset_id`, use this route.

1. Save the .blend file to the path it will keep. Then send one `retexture` item for each target with `batch_submit`: `object_name`, `prompt`, `mode: "blank"`, `workflow: "multiview"`, `enhance: ""`, `reference_path: ""`, `auto_uv: false` and `review: ["edit"]`. The add-on prepares, uploads and submits every item itself.
2. Read `batch_status` in short calls about every 30 to 60 seconds. An item whose paint is ready appears in `needs_review`. Read it with `batch_item`, or every item at once with `batch_items`: its `edit` outputs give `review_file`, the painted mesh saved as a GLB.
3. Bring that paint into Blender and accept it, as the next two sections say.
4. Capture it unlit to a PNG file. Make the condition image with `edit_scene_image`: `source: {"image_path": "<the capture>"}`, the two-sentence prompt and a new `request_id`. Follow its job with `get_job`; the result gives `image_asset_id`.
5. Answer the item with `batch_review`: `decision: "approve"` and `condition_image_asset_id`. The add-on runs PBR with that image and applies the maps to the target.
6. Read the finished item with `batch_item`. Its `pbr` outputs give `pbr_asset_id` and the `condition_image_asset_id` the run was given.

- The `edit` hold here is this skill's own stage: answer it yourself once the paint is accepted. When the user asked to see the paint first, show it; with nobody to answer, continue and report the paint as not user-reviewed.
- Each item records the file it was submitted in and applies its maps only while that file is open. An item sent from an unsaved file, or followed by a Save As to another path, is held with "Open … to go on". Keep that file open and saved under the same path until every item is applied. An unsaved submission cannot recover: its `pbr` outputs still give `pbr_asset_id`, so bring that asset in with `import_scene_asset`, and report the item as held.
- A wrong paint gets `decision: "reject"`. Fix its cause and send that target again as a new item.
- For **PBR always runs**, approve with no `condition_image_asset_id`.
- `batch_review` checks each image first. One the account does not hold refuses the whole call and applies nothing: correct the ID and send the call again.
- A variant is an item with `result: "new_object"` and a `name`: the add-on copies the object and works on the copy, so several items can start from one object. An asset of several parts takes only `replace`.
- For an unprepared asset of several parts on the automatic route, also pass `bake_colours: false`: left out, the batch bakes its stand-in colours.

## Bring the paint into Blender

The Retexture output is a painted mesh, not a library asset. A USD package exists only for a PBR result, so the library import commands (`import_assets`, `import_scene_asset`) cannot fetch it. They fail with "No USD package available" or `FORMAT_NOT_AVAILABLE`.

- **Batch route:** the file is the item's `review_file`. If the item has none, its warning says why and `review_url` holds a thumbnail.
- **Staged route:** read the painted mesh's asset ID from the Retexture node's `TEXTURE_ASSET_PROPERTY`. Get its download URL with `core.mcp_api.fetch_image_download_url(api_key, base_url, asset_id)`; despite its name, it returns a mesh asset's file URL too, and the URL lasts about a minute. Fetch the file at once with `core.http.download_bytes(url)` and save it as a `.glb` in the run folder.

Import the file with `bpy.ops.import_scene.gltf(filepath=...)` as a temporary object beside the target. Use the temporary object for the unlit inspection and capture only. The target keeps the final material.

Done when the temporary object shows the returned base colour on every part. If any step fails, follow **PBR always runs** above.

## Accept the paint before conditioning

A model approval or review waiver never waives this check. Compare the unlit paint with the brief region by region: each requested finish present, in the right place, the right colour, and not merged with its neighbour. Record pass or fail per region. A condition image guides how the maps respond to light; it cannot correct a wrong region's colour.

If a region fails, find its cause (prompt, reference, submission pose, UVs or geometry) and fix it. On the batch route, reject the item and send the target again. On the staged route, rerun `run_3d_retexture` from the same Load 3D node, first binding the corrected bare mesh there after a geometry or UV fix. Never repaint the returned paint locally and upload it again: the repaint hides the cause and breaks the lineage.

## Make the condition

1. Use the accepted painted mesh. Capture its actual base colour unlit against a plain background, from an angle that shows the principal finishes.
2. In the same Marso project, use Image Edit on that capture with a short prompt of two sentences. The first asks for the same object made photorealistic with more realistic lighting and detail. The second names how each material answers the light. For example: "Make this stool look photorealistic with more realistic lighting and details. Show the soft varnish on the wood and the reflective brass glinting in the light." Leave out camera, background, silhouette and "keep exactly" instructions; the capture already fixes them.
3. Compare candidates at their intended size. Prefer the image that makes the major finishes easiest to distinguish across the object. A broad highlight can reveal gloss, curvature and surface texture while the adjacent midtones carry the base colour. Check small hardware, original wear marks and the blank background too. If glare erases detail, or the edit changes the object or adds scenery, add one short sentence naming that fault and edit the original unlit capture again. Preserve the mesh’s accepted albedo.
4. Start PBR once, with the accepted Image Edit **output** ID. A guide retry can leave several valid images in the project, so check the ID first. Inspect the final material under fresh lighting at the same landmarks, including tint on optics and grain scale on moulded plastics when relevant.

## Lineage and what Studio shows

A mesh PBR node accepts one input link, its mesh. The condition travels as the execution's `conditioning_image_asset_id`, so Studio does not draw it as a link. Record:

- the Retexture node, its execution and the painted mesh asset;
- the capture, the Image Edit node, its execution and its output image asset;
- the PBR node and execution, the condition ID actually submitted, and the returned PBR asset.

On the batch route, `batch_item` gives these in the `edit` and `pbr` stage outputs. Report them in the handoff. Do not claim a visible connection.

## Staged route for earlier add-ons

Use this only when the installed `batch_review` takes no `condition_image_asset_id`. In Marso for Blender 1.19.0 to 1.21.2 the installed extension’s `core.mcp_api` provides the staged graph route through its own Studio client. This is the one documented use of that internal client: use it only for this route, and if the functions below are missing, report the gap rather than substituting another private call.

Open the account session with the installed module's `services.account.open_session()` and pass its `api_key` and `base_url`; never print or record the key. Address the verified project as `core.mcp_api.GraphRef(project_id=<project id>, graph_id="root")`.

To place the working copy in the graph, give it the blank base-colour texture Retexture needs with `core.retexture_prep.add_blank_textures(target)`. Export it with `core.mesh_export.export_object_to_glb_bytes(bpy.context, target)` and upload it with `core.mcp_api.upload_mesh`. Create the Load 3D (`NODE_TYPE_ORIGINAL_3D`) and Retexture (`NODE_TYPE_3D_RETEXTURE`) nodes with `create_node`, and bind the mesh with `set_node_texture`. Link them with `create_link(..., source_socket=SOCKET_MESH, target_socket=SOCKET_MESH)`.

On a Retexture node call `run_3d_retexture` with `mode="blank"` and `workflow="multiview"` for New Texture (its `mode` defaults to edit), and read `TEXTURE_ASSET_PROPERTY` after completion. Upload the unlit capture with the exposed `capture_reference` command (`mode="CAMERA"` once the camera frames the unlit view); it returns a job whose result is the image asset ID. Link the capture to the Image Edit node’s image input, run `run_image_edit`, and read its result with `node_image_asset`. Link the accepted Retexture node to a fresh mesh PBR node and pass the accepted image ID as `conditioning_image_asset_id` to `run_project_pbr`. Apply the returned PBR asset with the exposed `library_material` command (`asset_id`, `object_names`), which downloads its maps without spending credits. These are version-specific client methods; read their signatures in the installed module before calling, and follow existing execution IDs on resume.

Check staged executions with `poll_execution`, from a background thread or between Blender calls, about every 30 to 60 seconds. Return from each check at once, so Blender's main thread stays free, and report only a changed status. With several targets, check them all in one call and run each stage for all of them together.
