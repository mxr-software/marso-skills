# Connect an agent to Marso in Unreal Engine

The Marso Unreal plugin is in closed beta, by invitation. This page is for people in the beta who already have it in their Unreal project. The skills never install the Marso Unreal plugin or say where to get it.

## What connects to what

The Marso Unreal plugin runs its own MCP server inside the Unreal editor. Your agent connects to that server on your computer. The Unreal skills (`marso-unreal-setup`, `marso-unreal-level`, `marso-unreal-library`, `marso-unreal-set-piece`, `marso-unreal-blockout`, `marso-unreal-stage`) use it to read the level, import Marso library assets, place them and set pieces, fill a blocked-out level, and light and shoot it as stills.

Assets are made in Blender: generation, modelling and Retexture use the Blender skills. Unreal is where they are placed and arranged.

## Connect

1. Open your project in Unreal Engine 5.7 and press the **Marso** button on the toolbar.
2. Under **Agents on this computer**, the line reads `MCP on 127.0.0.1:<port>` when the server is running. If it reads `Agent servers off`, press **Start**.
3. Press **Connect an agent...**. It shows ready-made entries for Claude Code (a command or a `.mcp.json` entry) and Claude Desktop, with your project's port and access token filled in. Claude Desktop's entry runs a small bridge through `npx`, so it needs Node.js.
4. For another agent, add an MCP server that uses HTTP at `http://127.0.0.1:<port>/mcp` with the header `Authorization: Bearer <token>`. The token belongs to your Unreal project and is kept in `<Project>/Saved/Marso/mcp_token.txt`. Treat it as a password.
5. Restart your agent, then ask:

> Use marso-unreal-setup to connect to Marso in my Unreal project and check it without spending credits. Tell me what is ready and what is missing.

The agent reports the Marso Unreal plugin and Unreal versions, the open level, whether your API key is set (never the key itself), and whether your Marso account and projects answer.

## When it does not connect

- **Two editors open:** the second takes the next free port (9888, and so on). Use the port shown under **Agents on this computer** in the editor you mean.
- **Another project:** each Unreal project has its own token. Give the agent the open project's token.
- **No Marso button:** the Marso Unreal plugin is not enabled in this project. Check Edit > Plugins.
- **No API key:** enter it in Editor Preferences > Plugins > Marso, press **Save**, then **Test connection**.

`marso-unreal-setup` works through these checks with you.

## Compatibility

Checked against the Marso Unreal plugin's source for Unreal Engine 5.7 on Windows, and run live with an agent; see [compatibility](compatibility.md#unreal-engine-closed-beta) for the build and what was run.
