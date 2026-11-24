# Condition PBR on the new paint

PBR prediction uses visual cues about how the object reacts to light. New Texture paint is unlit, so the default after New Texture is to condition PBR on a lit image of that paint. In the Studio canvas Image → 3D Generation → PBR route, the original image supplies the condition automatically.

## Sequence

Run this without being asked whenever New Texture is followed by PBR. An asset you modelled has no existing look: Edit Texture over a bake of your own stand-in colours is still New Texture here.

1. Retexture alone with `mode="blank"` and `workflow="multiview"`. The combined Blender Retexture command starts PBR with no pause, so use the staged graph route below.
2. Accept the paint: inspect the unlit result for every requested material region.
3. Make and accept the condition image from that paint.
4. Run a fresh PBR node on the accepted mesh, passing the accepted condition.
5. Record the lineage and apply the returned material unchanged.

If the user supplied a real photograph of the same object and finish (cleaned if needed; never a render or drawing), it is already a lighting reference, so skip the staging. An image you rendered or generated before Retexture does not qualify: its lighting belongs to stand-in materials, not the new paint. For a supplied photo, Marso for Blender 1.19.0 accepts its account image ID as `condition_image_asset_id` on the combined Retexture → PBR run. The separate Retexture reference controls the paint. Check the installed command schema on older builds.

## Accept the paint before conditioning

A model approval or review waiver never waives this check. Compare the unlit paint with the brief region by region: each requested finish present, in the right place, the right colour, and not merged with its neighbour. Record pass or fail per region. A condition image guides how the maps respond to light; it cannot correct a wrong region's colour. If a region fails, find its cause (prompt, reference, submission pose, UVs or geometry), fix it and rerun `run_3d_retexture` from the same Load 3D node (below). Never repaint the returned paint locally and upload it again: the repaint hides the cause and breaks the lineage. A geometry or UV fix binds the corrected bare mesh on that same Load 3D node first.

## Make the condition

1. Use the accepted Retexture output mesh. Capture its actual base colour unlit against a plain background, from an angle that shows the principal finishes.
2. In the same Marso project, use Image Edit on that capture with a short prompt of two sentences. The first asks for the same object made photorealistic with more realistic lighting and detail. The second names how each material answers the light. For example: "Make this stool look photorealistic with more realistic lighting and details. Show the soft varnish on the wood and the reflective brass glinting in the light." Leave out camera, background, silhouette and "keep exactly" instructions; the capture already fixes them.
3. Compare candidates at their intended size. Prefer the image that makes the major finishes easiest to distinguish across the object. A broad highlight can reveal gloss, curvature and surface texture while the adjacent midtones carry the base colour. Check small hardware, original wear marks and the blank background too. If glare erases detail, or the edit changes the object or adds scenery, add one short sentence naming that fault and edit the original unlit capture again. Preserve the mesh’s accepted albedo.
4. Connect the accepted Retexture output from step 1 to a fresh mesh PBR node. Check the incoming mesh asset ID and the accepted Image Edit **output** ID before starting PBR once. A guide retry can leave several valid images in the graph. Inspect the final material under fresh lighting at the same landmarks, including tint on optics and grain scale on moulded plastics when relevant.

## Lineage and what Studio shows

A mesh PBR node accepts one input link, its mesh. The condition travels as the execution's `conditioning_image_asset_id`, so Studio does not draw it as a link, and the execution record does not echo it. Place the capture and Image Edit nodes beside the PBR node so the chain reads clearly, and record:

- Retexture node, execution and output mesh asset;
- capture image node and asset;
- Image Edit node, execution and output image asset;
- PBR node and execution, the condition ID actually submitted, and the returned PBR asset.

Report these in the handoff. Do not claim a visible connection.

## Staged route in the add-on

Prefer an installed staged command when `all_commands()` exposes one. Otherwise, in Marso for Blender 1.19.0 and 1.20.0 the installed extension’s `core.mcp_api` provides the staged graph route through its own Studio client. This is the one documented use of that internal client: use it only for this route, and if the functions below are missing, report the gap rather than substituting another private call.

Open the account session with the installed module's `services.account.open_session()` and pass its `api_key` and `base_url`; never print or record the key. Address the verified project as `core.mcp_api.GraphRef(project_id=<project id>, graph_id="root")`.

To place the working copy in the graph, give it the blank base-colour texture Retexture needs with `core.retexture_prep.add_blank_textures(target)`. Export it with `core.mesh_export.export_object_to_glb_bytes(bpy.context, target)` and upload it with `core.mcp_api.upload_mesh`. Create the Load 3D (`NODE_TYPE_ORIGINAL_3D`) and Retexture (`NODE_TYPE_3D_RETEXTURE`) nodes with `create_node`, and bind the mesh with `set_node_texture`. Link them with `create_link(..., source_socket=SOCKET_MESH, target_socket=SOCKET_MESH)`.

On a Retexture node call `run_3d_retexture` with `mode="blank"` and `workflow="multiview"` for New Texture (its `mode` defaults to edit), and read `TEXTURE_ASSET_PROPERTY` after completion. To rerun after a fix, run `run_3d_retexture` again on the Retexture node fed by the same original-3D (Load 3D) node; after a geometry or UV fix, first bind the corrected bare mesh on that node with `set_node_texture`. Link the unlit capture to the Image Edit node’s image input, run `run_image_edit`, and read its result with `node_image_asset`. Link the chosen mesh node to a fresh mesh PBR node and pass the accepted image ID as `conditioning_image_asset_id` to `run_project_pbr`. Upload the unlit capture with the exposed `capture_reference` command (`mode="CAMERA"` once the camera frames the unlit view); it returns a job whose result is the image asset ID. Apply the returned PBR asset with the exposed `library_material` command (`asset_id`, `object_names`), which downloads its maps without spending credits. These are version-specific client methods; read their signatures in the installed module before calling, and follow existing execution IDs on resume.

Poll staged executions from a background thread or between Blender calls, about every 30–60 s while queued and 15–30 s while running. Do not block Blender's main thread or report each unchanged status.
