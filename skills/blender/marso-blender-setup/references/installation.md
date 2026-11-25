# Installation and Blender access

## Identify the two components

The **Marso add-on** provides the Library, Auto PBR, Retexture, Create, and Studio panels. The **official Blender MCP** provides the assistant's connection into Blender. Installing one does not install the other.

Use [Blender Lab's official MCP page](https://www.blender.org/lab/mcp-server/) and its linked project for the Blender connection. Other projects also use the name "Blender MCP"; identify the provider rather than substituting one silently.

Marso 1.21.2 on Blender 5.2 is the inspected baseline; the add-on requires Blender 5.2.0 or later. Read the installed release's manifest or current release information before installation; a newer package can have different requirements. Blender Lab's MCP has its own requirements, so satisfy both. Do not describe the inspected version as the latest without checking.

## Install or enable Marso

1. Inspect Blender's version and installed extensions. If Marso is present but disabled, enable it before considering a reinstall.
2. Enable **Edit → Preferences → System → Allow Online Access**. Open **Get Extensions**, open its repository menu, then choose **Add Remote Repository**.
3. Paste `https://marso.app/plugins/blender/repo/index.json` and leave the access token empty. Refresh the repository, search for **Marso**, install it and enable the extension.
4. In a 3D Viewport press `N` and open **Marso**. Verify the loaded version. A **Get started** card at the top of the tab lists whatever is still missing. The public [installation page](https://marso.app/plugins/blender) also describes installation.
5. Only when the repository cannot be reached, install a downloaded official extension ZIP with **Install from Disk**. A ZIP copy is not subscribed to Blender's repository updates, but the add-on's own update button still updates it.
6. Continue with [configuration](configuration.md). Installing and updating need no Marso account or API key; Marso service operations need the API key, created in the dashboard under **Settings → API Keys**, and both storage paths set.

Completion: the Marso panel and add-on preferences are available in the intended Blender session. This alone does not prove account access or the assistant connection.

## Connect the official Blender MCP

1. Inspect the assistant's available connections. Reuse an already-working official Blender MCP connection.
2. Follow the current [Blender Lab instructions](https://www.blender.org/lab/mcp-server/) for its Blender-side add-on and MCP server. Install the official MCP bundle where the client supports it; otherwise use the project's documented server configuration.
3. Configure the assistant's supported local MCP connection. Read current server instructions and tool schemas rather than guessing executable paths, ports, or tool names from another Blender MCP project.
4. With Blender open, use a read-only operation to return the Blender version and scene identity. Verify it is the same session containing Marso.

Installing a skill does not install an MCP server. A remote connector does not automatically reach a server on the user's loopback address. If the current assistant surface cannot use the official local connection, report that limitation and offer guided desktop setup; Marso work needs that connection.

Do not enable Marso's **Connect to Marso Agents** or **Control Server** solely because the official MCP was installed. Those are separate add-on features described in [configuration](configuration.md#connection-settings).
