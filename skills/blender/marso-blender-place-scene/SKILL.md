---
name: marso-blender-place-scene
description: Import a photographed scene's minted Marso assets into Blender and place them like the photographs, with the Blender hierarchy matching the scene graph and repeated objects as linked duplicates. Use when a scene graph and a generation record (assets.json) exist and the user wants the room rebuilt in Blender. Landmarks go first, a camera matches the establishing photograph, and a review loop compares the two.
license: Proprietary. See LICENSE.txt in this skill folder.
---

# Place a scene's assets in Blender

Rebuild a photographed room in Blender from its scene graph: the floor and walls first, then the large fixed things, then everything that rests on them, each logical object represented by an Empty parented to its support Empty. Geometry lives in a separate child group; supported objects never parent to that geometry. Positions come from one photograph and a simple camera model, so they are a first layout to review, not a measurement.

Inputs: the decompose run folder (`scene_graph.json`, `manifest.json`, `registration.json`), its `asset_plan.json`, and `runs/<job>/assets.json` from the generation run, which holds each asset's `pbr_asset_id`, minted state and members. An asset reused from the library carries the library asset's `pbr_asset_id` and imports the same way. `<skill>` in the commands below stands for this skill folder's path. Generation belongs to `marso-blender-scene-assets`; Blender connection problems to `marso-blender-setup`, when installed.

In shell examples, `python` means an installed Python 3.10+ interpreter. Check its version first; on Windows, use `py -3.13` or another installed compatible version if the default `python` is older. Blender-only scripts run in Blender instead.

## Workflow

1. **Lay out.** `python "<skill>/scripts/layout_plan.py" "<run>" --assets "runs/<job>/assets.json" --plan "<run>/asset_plan.json" --out "<run>/placement.json"`. It prints a summary and the problems. Read [layout](references/layout.md) for the camera model, its defaults (camera 1.5 m high, a 26 mm phone lens, level) and how to override them. If the user knows the camera height or lens, pass it now.
2. **Import.** For each asset under `assets` in `placement.json`, through the Marso add-on bridge: `import_scene_asset {pbr_asset_id, name, collection, copies, require_minted: true}` with the project as `collection` and the asset's `copies` (total instances, minimum one). Read `describe()` first. Preserve the returned `instances` grouping in the result; do not flatten multipart assets. On resume, reuse recorded imports and existing owned entities instead of importing again. Follow each job with `get_job` in a later tool call (never `wait_job` inside Blender), at most four at once, and write every result into `<run>/imports.json` as `{"<asset_id>": <result>}`. An asset that is not minted is not imported: report it, and it stays a box.
3. **Check sizes.** Re-run step 1 with `--imports "<run>/imports.json" --force`. Every `size-disagrees` flag means the minted size and the graph's estimate differ by more than 25%. Keep imported dimensions by default and report disagreements. If the user explicitly requests a size correction, apply it to that entity's geometry group, record the correction, and recheck support contacts; never scale its placement Empty just to resize the mesh.
4. **Place.** In a Blender Python-execution tool: `import runpy; place = runpy.run_path(r"<skill>/scripts/place_in_blender.py")["place"]; result = place(r"<run>/placement.json", r"<run>/imports.json")`, and return `result`. Read [hierarchy](references/hierarchy.md) for what it builds and names.
5. **Review loop.** Look through the camera named in the placement result (normally `establishing_camera`) (the photograph is its background at half opacity), take a viewport screenshot, and set it beside the photograph. Fix the camera first (`--pitch`, `--hfov`, `--camera-height`, then re-run steps 1 and 3), then individual objects by editing their `location` or `rotation_z_deg` in `placement.json` and adding a line to `review`, and re-run step 4. Stop after three rounds or when the remaining errors are small at this distance.
6. **Stop for the user's review.** Show the screenshot beside the photograph and list what is still off. End the turn there; further rounds are the user's call.

## Hard rules

- Represent the support hierarchy with entity Empties. Each entity owns a geometry group; supported entity Empties are its siblings under the supporting entity. Keep world placement when parenting and store support ids/relations as metadata. Read [hierarchy](references/hierarchy.md).
- Landmarks first: anchors, then architecture, furniture and the largest objects, then the rest by support depth. `placement.json` gives the order; keep it.
- One entity Empty per logical instance, containing every part of that asset. Duplicate the complete geometry hierarchy with shared mesh data and independent object transforms.
- Do not automatically rescale minted geometry to an estimated graph size. User-authorised geometry corrections must leave other entities unchanged.
- Reuse only objects owned by this run, identified by metadata, never by name alone. Leave unrelated objects, collections and cameras intact. Keep the run id stable across reruns; use a new run for another scene. Old scenes without run metadata are not automatically migrated.
- A modelled object, an unconfirmed one, or one the plan routes to `reuse` without a library asset recorded in `assets.json` is a wire box at the graph's size, or left out; it is never generated here.

## Deliver

Report the collection, how many objects were placed as assets, duplicates and boxes, every object that was unplaced or guessed, every size disagreement and authorised geometry correction, every asset not imported and why, the camera values used, and the screenshot beside the photograph. State what was not checked: positions are estimates from one photograph and the rotation of each generated mesh's front is assumed.
