# Connecting a host

The Marso Unreal plugin's MCP server speaks MCP over HTTP:

- URL: `http://127.0.0.1:<port>/mcp`. Before connecting, read the port from the line under **Agents on this computer** in the Marso tab (`MCP on 127.0.0.1:<port>`); once connected, `servers.port` in `marso_state` gives it. It is 9887 unless changed or busy.
- Header: `Authorization: Bearer <token>`, where the token is the open Unreal project's, mirrored to `<Project>/Saved/Marso/mcp_token.txt`.

The server accepts connections from this computer only. A host running elsewhere, such as a chat in a web browser, cannot reach it.

The token is a secret. The user pastes it, or the host reads it from an environment variable; it never appears in chat or a log.

**Connect an agent...**, under **Agents on this computer**, starts the server if it is off. It shows three ready-made entries with the port and token filled in: a one-line command for Claude Code, a `.mcp.json` entry for Claude Code or Cursor, and an entry for Claude Desktop. The user copies the one for their host.

## Claude Code

The user runs the one-line command in a terminal, or adds the `.mcp.json` entry to the project. The command has this form:

```text
claude mcp add --transport http marso-unreal http://127.0.0.1:<port>/mcp --header "Authorization: Bearer <token>"
```

## Claude Desktop

Claude Desktop reaches the server through a local bridge. The entry **Connect an agent...** shows for it runs `mcp-remote` through `npx`, so Node.js must be installed. The user adds that entry to Claude Desktop's MCP settings and restarts it.

## Codex

Add the server to Codex's `config.toml` and keep the token in an environment variable:

```toml
[mcp_servers.marso-unreal]
url = "http://127.0.0.1:9887/mcp"
bearer_token_env_var = "MARSO_UNREAL_TOKEN"
startup_timeout_sec = 60
tool_timeout_sec = 120
```

Set `MARSO_UNREAL_TOKEN` from the token file in the shell that starts Codex. In PowerShell:

```powershell
$env:MARSO_UNREAL_TOKEN = (Get-Content -Raw "<Project>\Saved\Marso\mcp_token.txt").Trim()
```

Change the port in `url` when the server is not on 9887.

## Other hosts

A host that supports MCP servers over HTTP with a custom request header connects with the URL and header above, under the server name `marso-unreal`. After adding it, restart or reload the host's servers and call `marso_state`.
