---
name: marso-blender-setup
description: Install, configure, update, or troubleshoot the Marso Blender add-on and its agent connection. Use for first-time setup, missing Marso panels, API-key or storage configuration, online-access problems, Blender MCP connection issues, and add-on updates. Covers desktop-assisted setup and guided setup without desktop control. Asset modelling and texturing are separate workflows.
license: Apache-2.0
---

# Set up Marso for Blender

Get the user's existing Blender installation ready for Marso work. Complete the requested installation, configuration, repair, or update, then verify the result. Preserve working settings and the open scene.

## 1. Inspect and choose the route

Establish the assistant's actual capabilities: connected Blender tools, desktop control, or instructions only. Use available tools before asking the user for facts they can reveal. Identify the Blender session and installed versions; distinguish a missing add-on from a disabled one.

The default route is **official Blender MCP + Marso Blender add-on**. The MCP controls Blender; the add-on connects directly to Marso. The hosted Marso MCP is not required for this route. A working alternative chosen by the user can stay in place.

Read [installation](references/installation.md) when either component is missing or the Blender connection is unverified. Read [configuration](references/configuration.md) for settings and connection choices. Read [updates](references/updates.md) for an update request, or [troubleshooting](references/troubleshooting.md) for a fault.

Use the installed version's capabilities and current UI labels. The references describe an inspected implementation, not a guarantee that every version exposes the same commands.

## 2. Complete the missing steps

For a setup or repair request, perform routine authorized changes and verify each result. Ask only for missing information that changes the outcome, such as which of two Blender sessions is intended or where the user wants large asset downloads stored.

- With desktop control, inspect the current UI before operating it and check the resulting state. Use the supported installation and preferences UI.
- With a working Blender MCP, prefer its inspection tools and the add-on's existing command interface where available. The [configuration reference](references/configuration.md#using-the-add-ons-command-interface) explains the version-bound interface and asynchronous jobs.
- With neither, give the next small set of concrete UI steps, then continue from the user's reported result. Describe such checks as user-confirmed, not agent-observed.
- Let the user enter an API key in the application or use their established credential mechanism. Inspect key presence, never reveal the value in chat, logs, or screenshots.
- Keep existing valid storage locations. New locations belong outside the extension installation directory. Configure only the connection route being used.
- For an accompanying creation task, configure its [Studio destination](references/configuration.md#project-destination-for-creation): select a relevant project or create a descriptively named one, verify the selection and save it with the .blend. A setup-only request does not require creating a project.

When a tool or application requires a user action, explain that specific action. Work within the available interface; a restricted hosted connection is not permission to switch to Python or desktop control to evade its restrictions.

## 3. Verify without generating an asset

Use [configuration verification](references/configuration.md#verification) to check:

1. Marso is enabled in the intended Blender session, with compatible versions.
2. Online Access is enabled, credentials are configured, and both storage folders are usable.
3. A current non-generating request to Marso succeeds; distinguish live evidence from cached library contents.
4. The library loads or reports a valid empty account. An empty library is not a setup failure.
5. For agent-driven work, the selected Blender connection can inspect that same session.
6. Changes intended to survive restarts are stored in preferences, rather than existing only as session overrides.

Use short calls and follow existing jobs. Return control to Blender between calls so asynchronous work can finish. A timed-out request is not proof that it failed.

## 4. Report the outcome

State the installed versions, connection route, settings changed, and checks actually completed. Give useful folder locations without secrets. For an update, report the loaded version after installation, not just the download's name.

If desktop setup succeeded but the assistant cannot connect, report those as separate outcomes. If a live-library check is inconclusive, say so and name the next check. Finish with any specific user action still required; otherwise hand back a ready setup without creating geometry, importing assets, or running generation.
