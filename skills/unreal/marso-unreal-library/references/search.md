# Searching the library and the project

Three searches look in three places. Pick by where the asset may be.

| Looking in | Command | What it matches |
| --- | --- | --- |
| This Unreal project | `find_local {query}` | Marso assets already imported here, by the data Marso delivered with them |
| The synced Marso projects, by name | `search_library {query}` | Names, tags, materials and categories; every word must match |
| The whole Marso library, by meaning | `find_in_library {query, image_path}` (job) | Marso's own index, by words, by an image, or both |

All three read only and spend nothing.

## In this project

`find_local` matches every word of `query` against each asset's name, description, keywords, materials, conditions, placements, style and region. Narrow it with these filters, each a list of Marso values:

- `category`, such as `furniture` or `kitchenware`;
- `materials`, such as `metal`, `wood` or `glass`;
- `placements`, such as `floor`, `tabletop` or `wall`;
- `conditions`, such as `worn`, `rusted` or `cracked`;
- `size`: small (under 30 cm), medium (to 1.5 m) or large.

`has_looks` keeps meshes with more than one look, and `minted` keeps minted assets. Results come with facets: the count of each value among the assets that match the rest of the query. `semantic: true` searches by meaning in Marso's index and keeps only assets imported here; it runs as a job.

## Projects and views

- `sync_projects` (a job) refreshes the project list. Run it before `search_library` for fresh results.
- `open_project {project_id}` (a job) opens a project, a collection (`collection:<id>`), or one of two views: `all`, every asset in the library, newest first; `recent`, the assets imported last.
- `library_state` lists what is open. With a view open, `assets` holds its first 200, and `assets_truncated` says when there are more; reach a particular asset with `search_library` or `find_in_library` rather than by reading the list.
- The `all` view is read newest first, only as far as anyone looks. `load_more_assets` (a job) reads the next hundred or so. `refresh_library` reads the whole listing again; it takes minutes on a large library and is needed only to drop an asset deleted in Marso.

## One asset

- `asset_card {asset_id}`: name, description, category, size (`dimensions_m`), materials, whether it is minted, kind (model or material), project, `imported_path` when it is already here, and `newer_asset_id` when the library holds a newer version. When `details` is false, Marso has not sent the asset's details yet: say so rather than guessing its size.
- `get_asset_info {asset_id}` or `get_asset_info {asset_path}`: the cached entry, whether its package is downloaded, and the imported Static Mesh.

## More like an actor

`find_like_actor {actor}` (a job) searches the library with a picture of one actor in the level and the words of its label, so a `match` is where both agree. Its results import like `find_in_library`'s.
