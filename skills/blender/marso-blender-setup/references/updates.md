# Update Marso for Blender

## Determine whether an update is available

Read the loaded Marso and Blender versions. With **Allow Online Access** on, the add-on reads its extension repository once a session, when the Marso panel is first shown. When a newer version is published, the **Check for Updates** button at the top of the panel becomes **Update to X**. **Check for Updates** asks again at any time. Neither needs a Marso API key. Builds before 1.17.0 direct users to the downloads page instead.

## Install the update

1. Let active jobs finish and save the scene. Preserve storage and connection settings.
2. Press **Update to X**. It asks first, downloads the new version and has Blender install it over the current copy. Blender stays open, the Marso panels reload, and the API key, paths and other settings are kept. It is refused while a job is running. It works for a copy installed from the repository and for one installed from a ZIP.
3. Without that button, refresh the Marso repository in **Preferences → Get Extensions** and apply the update there, or install a downloaded official ZIP with **Install from Disk**.
4. Verify the loaded version and repeat [configuration verification](configuration.md#verification).

If installation fails, preserve the existing installation and report the error. Reinstall a previously working compatible official package only when recovery is needed and supported; do not delete user data or upgrade Blender itself merely to bypass an incompatibility.

Updating this skill, the Marso add-on, and the official Blender MCP are separate operations. Update only the requested component and any dependency whose incompatibility is established.
