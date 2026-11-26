---
name: marso-unreal-setup
description: "Use when connecting an agent to the Marso Unreal plugin (closed beta), checking its connection, account or project, fixing a fault (no answer, refused token, no Marso tab), or asked to install it."
license: Apache-2.0
---

# Set up Marso for Unreal Engine

## Overview

This skill connects the host to the Marso Unreal plugin's MCP server in an Unreal editor where the Marso Unreal plugin is already installed. It then checks the connection, the Marso account and the project without spending credits, and fixes connection faults. It keeps the user's Unreal project, its settings and the open level as they are.

**Closed beta.** The Marso Unreal plugin is in closed beta, by invitation. This skill never installs, updates or fetches it, and never says where to get it:

- Asked to install or update it: say the Marso Unreal plugin is in closed beta, by invitation, and that these skills do not install or update it. Then check what is installed, if anything.
- No Marso Unreal plugin answers and the user has none: say it is in closed beta, by invitation, and that you cannot install it. Stop the Unreal step.
- Where the task is one Blender can do (finding, making or texturing an asset), offer the Blender route through `marso-blender-setup` when installed; without it, name that route. With nobody to answer, start nothing in Blender: report the offer.

Never show the MCP token or the API key in chat, logs or screenshots; report only whether each is set and where it comes from.

Level work after setup belongs to `marso-unreal-level`, and library work to `marso-unreal-library`, each when installed. Without them, hand back a checked connection and name what is left.

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| Any Unreal request in a new session | [Find the Marso Unreal plugin](#find-the-marso-unreal-plugin) | nothing |
| First connection for this host | [Connect an agent](#connect-an-agent) | [hosts](references/hosts.md) |
| Is everything working? | [Check without spending](#check-without-spending) | nothing |
| No answer, refused token, no Marso tab, key or folder problems | [Fix a fault](#fix-a-fault) | [faults](references/faults.md) |
| Install or update the Marso Unreal plugin | Closed beta: answer as in the Overview | nothing |

## Find the Marso Unreal plugin

Through the Marso Unreal plugin's MCP tools, call `marso_state` first. Find a command with `marso_search` and read its schema with `marso_describe`, then run it with `marso_run`. A command that returns `job_id` runs in the background: wait with `marso_wait`, at most 50 seconds a call, and never resubmit on a timeout.

1. If `marso_state` answers, go to [Check without spending](#check-without-spending).
2. If the host has no Marso Unreal tools, the host is not connected yet: [Connect an agent](#connect-an-agent). Reach the server only through the host's MCP tools; never call its URL yourself or read the token to do so, which bypasses the host's approvals.
3. If the tools exist but get no answer or are refused: [Fix a fault](#fix-a-fault).
4. Ask the user whether Unreal Engine is open and shows a **Marso** button on its toolbar. With no Marso button in any project they have, they have no Marso Unreal plugin: answer as in the Overview. With nobody to answer, report that no Marso Unreal plugin answered and stop.

Done when `marso_state` answers, or the report says which of the cases above applies.

## Connect an agent

Each step below is the user's, in the Unreal editor or the host's settings. With nobody to answer, report the first step not yet done and stop.

1. Open the Marso tab (the **Marso** toolbar button). The line under **Agents on this computer** reads `MCP on 127.0.0.1:<port>` when the MCP server is running, or `Agent servers off` when it is not.
2. If it reads `Agent servers off`, ask the user to press **Start** beside it. **Enable MCP server** and **Start servers with the editor** are on by default in Editor Preferences > Plugins > Marso.
3. The server listens at `http://127.0.0.1:<port>/mcp`, with the port from that line, and needs the header `Authorization: Bearer <token>`. The token belongs to the open Unreal project and is mirrored to `<Project>/Saved/Marso/mcp_token.txt`.
4. **Connect an agent...** in the same section shows ready-made entries with this project's port and token. Add the server to the host as [hosts](references/hosts.md) describes.
5. Let the user paste the token into the host, or set it through an environment variable from the token file without displaying it. Restart or reload the host's MCP servers.
6. Call `marso_state`.

A host that cannot reach `127.0.0.1` on this computer cannot use the Marso Unreal plugin's MCP server: say so and stop. Connect only through the MCP server under **Agents on this computer**; leave the Marso tab's other connection switches as they are.

Done when `marso_state` answers with `servers.running` true and `editor.project` naming the project the user intends.

## Check without spending

1. From `marso_state`, record:
   - `version` (the Marso Unreal plugin) and `unreal_version`;
   - `editor.project`, `editor.level_name` and whether `editor.pie_running` is true;
   - `servers.port`;
   - `configuration.api_key_set` and `configuration.api_key_source`, never the key;
   - `configuration.storage_configured`, with `storage_problem` when it is false;
   - `commands`, the number of commands this build has.
2. Run `refresh_credits`. It is a live request to Marso that needs the key and spends nothing. A finished job proves the key works; a failed one goes to [Fix a fault](#fix-a-fault).
3. Run `list_studio_projects`, then `save_to_state`. Record how many Marso projects the account has and which one Create and Retexture runs save into (none until one is chosen). An empty account is not a fault. A setup-only request creates and changes no project.
4. If the task needs a particular command, look for it with `marso_search`. If it is missing, name the command and the installed `version`, say that this build of the Marso Unreal plugin lacks it, and stop that step.

Done when every item above has a recorded result, and each failure names its check.

## Fix a fault

Read [faults](references/faults.md) and work through the row that matches what was seen. Check one cause at a time and call `marso_state` again after each fix.

- An Unreal editor setting changes only when the user asks for it or the fault needs it. The user enters an API key in the editor themselves.
- With nobody to answer, apply no setting change: report the symptom, the checks made and the fix that needs the user.

Done when `marso_state` answers and the failed check passes, or the report names the fault, what was checked, and the user's next action.

## Report

Report the Marso Unreal plugin `version`, `unreal_version`, the Unreal project and open level, the server port, whether the key is set and its source, the account and project checks, and any setting changed. Say which checks were not run. Never include the token or the key.

Done when the final message holds each item above, or says why it is missing.

## Worked example: connecting to a second editor

1. The user has two Unreal projects open and asks the host to "connect to Marso in the Harbour project". The host has no Marso Unreal tools.
2. In the Harbour editor's Marso tab, the line under **Agents on this computer** reads `MCP on 127.0.0.1:9888`: the other editor holds 9887, so this server moved to the next free port.
3. The host's settings get a `marso-unreal` server at `http://127.0.0.1:9888/mcp`, with the token read from an environment variable. The user sets that variable from Harbour's `Saved/Marso/mcp_token.txt`; the token is never shown.
4. After a restart, `marso_state` answers: `editor.project` is Harbour, `servers.port` is 9888, `api_key_set` is true from Editor Preferences.
5. `refresh_credits` finishes. `list_studio_projects` lists 12 projects; `save_to_state` shows none chosen yet, which is reported, not changed.
6. The report gives the Marso Unreal plugin version, Unreal 5.7, Harbour, the open level, port 9888, the key's source, both checks, and no setting changed.

## Common mistakes

- Installing, updating or fetching the Marso Unreal plugin: it is in closed beta; say so and stop.
- Showing the token or API key to check it: report `api_key_set` and the token file's presence only.
- Calling the server's URL from a script when the host's tools are missing: connect the host, or report and stop.
- Assuming port 9887: a second editor moves to the next free port; read the line under **Agents on this computer** or `servers.port`.
- Reusing a token from another Unreal project: each project has its own; read the open project's token file.
- Testing the account with a generation: `refresh_credits` proves the key and spends nothing.
- Connecting through any switch in the Marso tab other than **Agents on this computer**: that one is the MCP server the skills use.
- Treating an empty account or no chosen project as a fault: record it and continue.
