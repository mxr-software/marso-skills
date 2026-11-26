# Collections and favourites

## Collections

Collections live in the Marso account and show on marso.app too. Removing an asset from a collection, or deleting a collection, never deletes the asset from the library or from this project.

| Task | Command |
| --- | --- |
| List them | `list_collections`: each has an `id` written `collection:<id>`, a name and an asset count |
| Open one | `open_project {project_id: "collection:<id>"}` |
| Make one | `create_collection {name, tags, asset_ids}` |
| Add or remove assets | `add_to_collection {collection_id, asset_ids}`, `remove_from_collection {collection_id, asset_ids}` |
| Rename or delete | `rename_collection {collection_id, name}`, `delete_collection {collection_id}` |

- Each except `list_collections` is a job. `list_collections` reads the last sync: run `sync_projects` first when a collection made elsewhere is missing.
- Collection names need not be unique, so `create_collection` is sent once. If it fails, run `sync_projects`, then read `list_collections` before trying again, or the account can end up with two collections of one name.
- Delete only a collection the user named. With nobody to answer, keep any other.

## Favourites

Stars are the user's own, kept on this computer; they do not change stars on marso.app.

- `list_favourites` lists the starred assets, newest star first. `open_project {project_id: "favourites"}` opens them as a view.
- `set_favourite {asset_id, favourite}` stars or unstars one. Star only when the user asks.
