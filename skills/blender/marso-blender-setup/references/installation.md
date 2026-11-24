# Installation and Blender access

## Identify the two components

The **Marso add-on** provides the Library, Auto PBR, Retexture, Create, and Studio panels. The **official Blender MCP** provides the assistant's connection into Blender. Installing one does not install the other.

Use [Blender Lab's official MCP page](https://www.blender.org/lab/mcp-server/) and its linked project for the Blender connection. Other projects also use the name "Blender MCP"; identify the provider rather than substituting one silently.

Public Marso 1.12.1 on Blender 5.2 is the inspected baseline for the documented scene route. Read the downloaded release's manifest or current release information before installation; a newer package can have different requirements. Blender Lab's MCP has its own requirements, so satisfy both. Do not describe the inspected version as the latest without checking.

## Install or enable Marso

1. Inspect Blender's version and installed extensions. If Marso is present but disabled, enable it before considering a reinstall.
2. Enable **Edit → Preferences → System → Allow Online Access**. Open **Get Extensions**, open its repository menu, then choose **Add Remote Repository**.
3. Paste `https://marso.app/plugins/blender/repo/index.json` and leave the access token empty. Refresh the repository, search for **Marso**, install it and enable the extension.
4. In a 3D Viewport press `N` and open **Marso**. Verify the loaded version. The public [installation page](https://marso.app/plugins/blender) also describes installation. For a downloaded official extension ZIP, use **Install from Disk**.
5. Continue with [configuration](configuration.md). The extension repository needs no Marso API key; configure the account for Marso service operations.

Completion: the Marso panel and add-on preferences are available in the intended Blender session. This alone does not prove account access or the assistant connection.

## Connect the official Blender MCP

1. Inspect the assistant's available connections. Reuse an already-working official Blender MCP connection.
2. Follow the current [Blender Lab instructions](https://www.blender.org/lab/mcp-server/) for its Blender-side add-on and MCP server. Install the official MCP bundle where the client supports it; otherwise use the project's documented server configuration.
3. Configure the assistant's supported local MCP connection. Read current server instructions and tool schemas rather than guessing executable paths, ports, or tool names from another Blender MCP project.
4. With Blender open, use a read-only operation to return the Blender version and scene identity. Verify it is the same session containing Marso.

Installing a skill does not install an MCP server. A remote connector does not automatically reach a server on the user's loopback address. If the current assistant surface cannot use the official local connection, report that limitation; offer guided desktop setup or an available supported route without claiming modelling access.

Do not enable Marso's **Connect to Marso Agents** or **Control Server** solely because the official MCP was installed. Those are separate routes described in [configuration](configuration.md#connection-settings).
