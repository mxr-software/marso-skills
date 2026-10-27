# Configuration and verification

Open Marso's add-on preferences through its header menu or Blender Preferences > Add-ons > Marso. Preserve existing valid values.

## Required settings

| Setting | Why it exists | Setup behaviour |
| --- | --- | --- |
| API Key | Authenticates the add-on's own requests to Marso. | Have the user enter it in the masked field. Key presence is not proof of validity. |
| API Endpoint | Selects the Marso API environment. | Keep the shipped production default for a new customer setup. Preserve an intentionally selected environment; use **Reset to Default** only when correcting an unintended endpoint. |
| Cache Path | Stores project listings and thumbnails. | Use a writable, persistent folder outside the extension directory. |
| Downloads Path | Stores assets, texture maps, HDRIs, and renders. | Use a separate writable folder with room for asset files. Preserve its contents and existing links. |
| Online Access | Allows Blender extensions to contact the network. | Enable through Preferences > System for the requested online workflow, then verify the effective state. If blocked by policy or a launch flag, report that cause. |

Both paths must be set for normal interactive use. The setup card checks whether they are filled in, not whether they are writable. A headless fallback directory is not evidence that the user's GUI preferences are configured.

For a new setup with no location preference, state and use sensible user-owned `Marso/Cache` and `Marso/Downloads` folders under an available local data location. Ask only when the user's storage choice matters, such as an explicitly preferred external drive. Resolve real paths on the user's machine; never copy a developer's drive letters.

Downloads contain `Projects/`, `AutoPBR_Output/`, `HDRIs/`, and `Renders/`. They are user assets, not disposable cache. Changing the path does not migrate those files. Keep it stable unless migration is requested.

Ensure Blender's preference-saving behaviour persists intended changes. In the inspected implementation, runtime overrides take precedence over stored preferences, which take precedence over environment fallback values. A `configure` call defaults to session-only changes; `persist: true` also updates the preferences, which must then be saved by Blender. The `overridden` field reports setting names, not their values.

## Project destination for creation

Recent builds have a **Save to** picker at the top of the Marso tab. It is stored in the current .blend and shared by Create 3D Asset and Retexture. Browsing a Library project does not select this destination. Auto PBR uses a separate queue and does not use the picker.

For a creation task, keep a destination that belongs to that task, select the user's intended existing project, or create a descriptive new project when needed. Do not collect unrelated work in a generic Blender project. Setup by itself does not require creating a cloud project.

With desktop control, refresh **Save to**, choose the intended project or use its creation action, then read back the selected name. With command access, discover these commands before using them:

| Command | Parameters | Result/use |
| --- | --- | --- |
| `save_to_state` | `{}` | Current `save_to` selection and loaded project list. |
| `list_studio_projects` | `{}` | Fresh project-list job; wait through later job calls before using its results. |
| `set_save_project` | `{"project_id": "<ID from the refreshed list>"}` | Selects the current file's creation destination. |
| `create_studio_project` | `{"name": "<descriptive task name>"}` | Creates and selects a project asynchronously. Inspect completion and selection. |

Read `save_to_state` after selection/creation, record the returned ID and name with the asset's local handoff, and save the .blend. Verify the choice after reopening and before later submissions. Check actual completed outputs in that project's graph or Library; a selected label alone does not prove where an earlier run went. Reconcile a timed-out creation against jobs and the refreshed list before creating again.

Discover support from the loaded add-on, not only its version string. If project selection is required but absent, resolve the installed-version gap through the supported update workflow; do not silently use a legacy automatic destination. Keep credentials and account-specific project IDs out of public skill examples.

## Connection settings

| Route | Required settings | What it enables |
| --- | --- | --- |
| Official Blender MCP + Marso add-on (default) | Working official MCP connection and the required Marso settings above. | Blender control; Marso operations through available add-on interfaces. Neither Marso relay nor local HTTP server is inherently required for direct in-process calls. |
| Marso local Control Server | **Allow Control Server**, a generated token, an available loopback port, and a running server; configure a compatible local caller. | JSON-over-HTTP command access. This server is not itself an MCP endpoint. Enable only if the integration uses it. |
| Hosted Marso MCP | Connect the assistant to Marso, then enable **Connect to Marso Agents** in Blender using the same Marso account. | Outbound relay for supported Marso commands. It does not provide general Blender Python modelling. |

For local HTTP access, read the actual configured port and schema from `/ping` and `/capabilities`; the inspected default port is 9885. Keep the generated token in the client's credential mechanism. **Allow Control Server** and **Start With Blender** are separate from starting the server now.

For the hosted route, one Blender session per Marso account is connected at a time in the inspected implementation; connecting another replaces the first. Verify the returned session label. The hosted interface deliberately disallows credential, endpoint, and folder configuration. Direct the user to preferences for these changes; do not route around a refusal.

## Using the add-on's command interface

This is a source-inspected integration path, pending live testing through the official MCP. Prefer a working supported tool or UI over assuming this internal Python interface is stable across versions.

Inside Blender, find the enabled Marso extension's actual module identifier through `bpy.context.preferences.addons`; it may be namespaced, such as `bl_ext.<repository>.marso`. Confirm its identity before using it. Avoid hard-coding `import marso`.

The inspected module exposes `<module>.bridge.commands` with:

- `all_commands()` and each entry's `describe()` for the current schemas.
- `execute(name, params)` for a short command invocation on Blender's thread.

Useful commands, when present:

| Command | Parameters | Result/use |
| --- | --- | --- |
| `get_configuration` | `{}` | Version, online access, `api_key_set`, effective folders, and overridden setting names; excludes the key value. |
| `configure` | Only the settings being changed; `persist` for stored preferences. | Session configuration; prefer the UI for credentials. |
| `check_update` | `{}` | Starts a non-generating live request; returns a job ID. |
| `sync_projects` | `{}` | Refreshes library listings and caches thumbnails; returns a job ID. |
| `library_state` | `{}` | Current project/asset listing; may be cached. |
| `get_job` | `{"job_id": "<returned ID>"}` | Snapshot of a previously started job. |

Network jobs return before their work completes. When invoking commands inside a Blender Python execution tool, return immediately, then use `get_job` in a later tool call. **Do not call blocking `wait_job`, sleep, or loop waiting inside Blender's main thread**: job completion may itself need that thread. A separate external HTTP client can use bounded job waits without occupying Blender's main thread.

After an interruption, inspect existing jobs before starting the operation again. If the interface is absent or incompatible, use the UI or report the exact missing capability rather than inventing a replacement API.

## Verification

1. Read version, Online Access, key-presence, and effective-path state. Inspect only selected fields, not the full preferences object or environment.
2. Verify both folders exist and are writable through an authorized local tool. If necessary, create and remove one uniquely named temporary probe file in each, leaving existing files untouched. Without filesystem access, report this check as unverified rather than equating a filled field with write access.
3. Use a fresh non-generating API operation, such as **Check for Updates**, to establish current connectivity. Wait for its actual success; a cached balance is not evidence. A failed check is not "up to date."
4. Refresh the Library and inspect the resulting state. A successfully returned empty account is valid. **In the inspected version, library sync can silently fall back to cached projects after network errors.** A successful sync job or visible thumbnails alone does not prove a fresh library response. Report live API connectivity and library display separately; claim live library access only when a fresh authenticated library response is observed. Otherwise state that freshness remains unverified.
5. For an agent workflow, obtain the intended Blender session's identity through the chosen connection. Desktop visibility alone does not prove an MCP connection works.
6. Check stored preference values for settings meant to persist. If a restart or reload is needed, preserve the current work first; do not restart simply to finish an otherwise adequate inspection.

Report observed, user-confirmed, and unverified checks separately. This setup workflow does not generate or import assets and does not add a credit approval flow.
