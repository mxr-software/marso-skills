# What place_in_blender.py builds

`place(placement_path, imports_path, collection_name=None, photo=True)` runs inside Blender and returns a report: `placed` (with each object's world size), `duplicated`, `boxes`, `not_imported`, `unused_imports` and `warnings`.

## Collection and names

Everything goes into one collection named after the project (`placement.json`'s `project`, which comes from the generation run), linked under the scene collection. Objects are named so a re-run finds them:

| Object | Name |
| --- | --- |
| Floor, ceiling, other anchors | `<label>_<global_id>`, an empty |
| Wall | `<label>_<global_id>`, a single-face plane from the wall's corners |
| Asset instance | `<asset_id>_<label>_<global_id>` |
| Placeholder | `box_<label>_<global_id>`, a wire box at the planned dimensions |
| Asset that was not imported | `<asset_id>_<label>_<global_id>_box` |
| Camera | `establishing_camera` |

Each placed object carries the custom properties `marso_global_id` and, for assets, `marso_asset_id`.

## Hierarchy

The scene graph's support tree becomes Blender's parent tree: the floor empty holds the furniture, the worktop holds the bowl, the bowl holds the onions. Parenting keeps world transforms, so an object stays where it was placed. Anchors have no parent. An object whose parent was not built stays at the top level and is named under `warnings`.

## Instances

`import_scene_asset` returns the imported objects for an asset. They are taken in order for that asset's instances. If there are fewer objects than instances, the rest are made as linked duplicates of the first (`Object.copy()`, which shares the mesh data), with the first's direct child parts duplicated alongside. Imported objects left over are listed in `unused_imports` and left untouched.

## Placement of each object

In placement order: clear its parent (keeping its world transform), set its rotation about z (other rotation axes, such as an importer's axis correction, are kept), move it so the bottom centre of its own geometry is on the planned location, then parent it. Geometry from objects parented to it in the graph is ignored when finding its bottom centre.

## Camera

`establishing_camera` gets the horizontal field of view, location and rotation from `placement.json`, and the scene's render resolution is set to the photograph's. It becomes the scene camera, and the photograph is added as its background image at half opacity, in front, so looking through the camera compares the two directly.

## Re-running

Every object is found again by name and re-placed; nothing is created twice and nothing is deleted. To start an object again, delete it in Blender yourself, or with the user's agreement, before re-running.
