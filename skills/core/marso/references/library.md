# Find an asset in the library

Use this before generating an object the user's Marso library might already hold, and whenever the user asks to find, reuse or import something they have made before. Reusing an asset costs nothing and keeps a set consistent; generating a near copy does neither. Skip it when the user asks for a new asset, a different version, or a hand-modelled one.

## Search

Inspect the tools actually available, as for generation.

- **Blender add-on route.** Builds with a `find_in_library` bridge command search the whole library by meaning and appearance: `query` (a few words), `image_path` (a picture of the object), or both. Each result is one asset with its name, `verdict` (`match`, `possible` or `weak`), image and text scores, `pbr_asset_id` and a downloaded `thumbnail_path`. `show_in_library: true` also shows the results in the Library panel's Find mode, where `import_assets` imports them. `search_library` is a different command: it matches names, tags and materials in the projects already cached on this machine, and finds nothing it has not cached.
- **Other routes.** Use a library search tool the connection offers, reading its schema first. Without one, say that the library cannot be searched from here and browse the user's projects only if they ask. Do not invent a search call.

Search with both a description and an image whenever there is an image:

- **The image is the object alone.** Crop it tight to the object's own bounds, with no drawn outline. A search finds whatever fills the picture: a crop of glasses on their case finds the glasses.
- **The description is the object's name**, a few words. Long descriptions score lower, not higher.
- **With both, a result counts only where the two agree.** An image alone rates lookalikes and neighbours highly and is never a match by itself; a description alone cannot tell this kettle from any kettle.

## Read the results

- A `match` is a strong candidate, not a decision. Below the first result there is often noise: other kettles as `possible`, or the whole of an object when its part was searched for. Show every `match` and `possible`.
- **An object that others sit on or in** (a table, a tray, a bowl of fruit) is found by its description: what it holds fills its picture. Expect `possible` or `weak`, and read the description's results.
- **A library asset can carry the wrong name.** Minting names an asset from what it looks like, and can be wrong. The image can still find it when the picture shows the object alone; otherwise it comes back `weak` at best. When nothing better came back, show the best `weak` thumbnail; the user may recognise it.
- The verdict thresholds were set on one library: defaults to review, not calibrated constants.

## Decide with the user

Show each candidate's thumbnail with its name and verdict beside the user's picture, and let the user choose to reuse one or make a new asset. Never reuse on a score alone: a library asset can differ in size, style or material from what the user wants. When the user chooses one, import it through the route's import command by the id it takes (`pbr_asset_id` in Blender), and inspect its scale as for any imported asset. When the user declines, or nothing came back, continue with generation or modelling and say the library was checked.

Report what was searched (the description, the picture), what came back, and what the user chose.
