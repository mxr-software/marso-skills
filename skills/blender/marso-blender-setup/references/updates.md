# Update Marso for Blender

## Determine whether an update is available

Read the loaded add-on version and Blender version first. In the Marso header menu, choose **Check for Updates**, or use the discovered `check_update` command through a supported connection.

The inspected implementation needs Online Access and a configured API key for this request, but does not require configured storage. Follow the returned job to completion. Its result contains `current`, `latest`, and `update_available`.

- A successful comparison with no newer version means up to date against that service response.
- A failed or unavailable check leaves update status unknown. Check the official download page when possible.
- A newer version still needs compatibility checking against the user's Blender installation.

## Install the update

In the inspected add-on, the **Update** banner opens [Marso Dashboard > Plugins](https://marso.app/dashboard/plugins). It does **not** download or install the update automatically.

1. Obtain the appropriate extension ZIP from that page. Use current release information and the package's compatibility requirements.
2. Check for running Marso jobs or rendering. Let active work finish before replacing the add-on. Preserve unsaved work; save an existing file when authorized, or resolve its save destination before any necessary restart.
3. Record the non-secret settings that must survive: storage paths, chosen endpoint, and enabled connection route. Keep credentials in Blender's supported storage, not in notes or chat.
4. Use Blender's supported **Install from Disk** update/replacement flow for the extension. Follow actual UI prompts. Do not delete the downloads folder or manually remove the add-on as the first update step.
5. If Blender requests a reload or restart, complete it after preserving the scene. Reconnect the assistant if needed.
6. Read the version loaded by Blender again, check retained settings, and repeat [configuration verification](configuration.md#verification).

Completion means the intended version is loaded and its setup has been checked. A downloaded ZIP, an opened browser page, or a remaining update banner is not installation success.

If installation fails, preserve the existing installation and report the error. Reinstall a previously working compatible official package only when recovery is needed and supported; do not delete user data or upgrade Blender itself merely to bypass an incompatibility.

Updating this skill, the Marso add-on, and the official Blender MCP are separate operations. Update only the requested component and any dependency whose incompatibility is established.
