# Faults and their checks

Work down the row that matches the symptom. Call `marso_state` again after each fix.

| Symptom | Check, then fix |
| --- | --- |
| The host's Marso Unreal tools get no answer | Unreal is open with the intended project, and the line under **Agents on this computer** reads `MCP on 127.0.0.1:<port>`. |
| No answer, though that line shows a port | The port in the host matches it. See [The port](#the-port). |
| Refused with 401, or the token is rejected | The host has the open project's current token. See [The token](#the-token). |
| Refused with 403 | The host runs on this computer, connects to `127.0.0.1` or `localhost`, and is not a web page. |
| No **Marso** toolbar button or Marso tab | The Marso Unreal plugin is enabled in this project. See [It does not load](#it-does-not-load). |
| `configuration.api_key_set` is false | The user enters a key. See [The API key](#the-api-key). |
| `refresh_credits` fails | The key is refused or Marso cannot be reached. See [The API key](#the-api-key). |
| `configuration.storage_configured` is false | The folders in `storage_problem`. See [Folders](#folders). |

## The port

- The MCP port is set in Editor Preferences > Plugins > Marso > **MCP port** (9887 by default). The environment variable `MARSO_MCP_PORT`, set before Unreal starts, overrides it.
- When the port is busy, usually because another Unreal editor holds it, the server moves to the next free port, up to ten higher. The Output Log says so: "Port 9887 was busy; Marso server moved to 9888".
- Before the host connects, read the port from the line under **Agents on this computer** or from **Connect an agent...**; after, `servers.port` gives it.
- Each open editor has its own server. Connect the host to the port of the editor the user means; `editor.project` confirms which one answered.

## The token

- Each Unreal project has its own token, mirrored to `<Project>/Saved/Marso/mcp_token.txt` when the server starts. Opening another project means another token.
- The environment variable `MARSO_MCP_TOKEN`, set before Unreal starts, replaces the project's token.
- Give the host the current token again, as when connecting, and reload its servers. Never print the token to compare it.

## It does not load

- In Edit > Plugins, search for Marso: it must be enabled for this project. Enabling it asks for an editor restart.
- If it is enabled but does not load, the Output Log names the module that failed. Marso 0.1.20 does not load in a project without Geometry Script enabled; enable **Geometry Script** in Edit > Plugins.
- The skills do not install or repair the Marso Unreal plugin's files. With it missing or broken, report what the Output Log says.

## The API key

- The user enters the key in Editor Preferences > Plugins > Marso > **API key**, presses **Save**, then **Test connection**, which tests the saved key. The Marso Unreal plugin keeps the key outside the project.
- A key can also come from the environment variable `MARSO_API_KEY`. `configuration.api_key_source` says which source is in use.
- `configure` can set a key for the session, but the key never passes through chat: the user enters it in the editor.
- When `refresh_credits` fails with the key set, report the job's error. A refused key is the user's to replace; an unreachable Marso is a network fault, with `configuration.api_endpoint` as the address tried.

## Folders

- The cache and downloads folders are in Editor Preferences > Plugins > Marso > **Cache folder** and **Downloads folder**. `storage_problem` names the one that is unusable.
- Change a folder only when the user asks or it is unusable. Keep folders the user already set.
