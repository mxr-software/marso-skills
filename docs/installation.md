# Install Marso skills

Marso skills teach your AI assistant how to work with Marso in supported applications and workflows. Choose the skills you need from the [available skills](../README.md#available-skills), then install them in your assistant using the instructions below.

Install each complete skill folder containing `SKILL.md`, including its `references/`, `scripts/`, and optional `agents/` metadata. Each folder packages independently; companion skills must be installed separately when needed. Installing skills provides instructions, but does not install creative applications, add-ons or tool connections.

In the examples below, `<skill-name>` means the actual folder name of the skill you selected. Keep that name unchanged when installing it. The first available collection is for Blender; its application setup is covered separately below.

The artist pilot is on the [`development` branch](https://github.com/mxr-software/marso-skills/tree/development). Select that branch before downloading the repository ZIP, or clone it with `git clone --branch development https://github.com/mxr-software/marso-skills.git`. Read the [pilot guide](artist-pilot.md) for scope and feedback. Installation commands and client capabilities change, so use the official client documentation linked below when the visible UI differs.

## Package and discovery layout

Each leaf folder is one skill. For example, copy `skills/blender/marso-blender-texture/` directly into the selected client's skill directory:

```text
<client-skill-directory>/
  marso-blender-texture/
    SKILL.md
    references/
    scripts/
    agents/openai.yaml
```

Do not retain the repository's `skills/blender/` grouping inside the client directory, or upload the entire repository as one skill. The shared entry point is `SKILL.md`; `agents/openai.yaml` is optional OpenAI UI metadata and contains no required workflow logic. Keep referenced files together. Repository docs, maintainer tests and local experiments are not skill dependencies.

For Codex and Claude Code, the optional [Skills CLI](https://github.com/vercel-labs/skills) can discover these folders. With Node.js available, install a selected skill using the explicit branch:

```bash
npx skills add https://github.com/mxr-software/marso-skills/tree/development --skill marso-blender-texture --agent codex claude-code
```

Replace the skill name or list several names from the bundles below; choose only the clients you use. The manual installation routes below work without this third-party installer.

## Choose by outcome

These are recommended combinations of existing folders, not separate packages. Install each listed folder using your assistant's instructions below. Add the application-independent [`marso`](../skills/core/marso/SKILL.md) entry skill from `skills/core/marso/` when you want help choosing the route.

| What you want | Skills to install |
| --- | --- |
| Choose whether to generate or model an asset | `marso` |
| Model an asset in Blender and texture it with Marso | `marso-blender-setup`, `marso-blender-asset`, `marso-blender-texture` |
| Restyle an existing Blender asset or make several looks from its original source | `marso-blender-setup`, `marso-blender-texture` |
| Build, texture and assemble a modular Blender kit | All five Blender skills: setup, asset, texture, kit and compose |
| Generate an asset through the Blender add-on | `marso`, `marso-blender-setup`; add texture for later Restyle and style variants |
| Turn photographs of a room into a scene graph and plan its assets | `marso-scene-decompose`, `marso-scene-graph`; add `marso` to generate the planned objects |
| Rebuild a photographed room in Blender from Marso assets | `marso-scene-decompose`, `marso-scene-graph`, `marso-blender-setup`, `marso-blender-scene-assets`, `marso-blender-place-scene` |
| Generate through a connected Marso Studio service | `marso`, plus the service's current tools and workflow guides |

The two scene skills run Python scripts from their own folders and need Python 3.10+ with Pillow (`pip install Pillow`) and a host that can run shell commands and look at local images. They need no application connection or network access. `marso-blender-scene-assets` and `marso-blender-place-scene` run standard-library Python scripts and need Blender with the official MCP and a Marso add-on that provides the scene commands they name.

The entry skill discovers available capabilities; it does not supply Studio credentials or install connections. A working Blender add-on route does not require a separate hosted Marso MCP. The generative routing is capability-reviewed; fresh-client execution remains part of the pilot.

## Codex

Copy the selected skill folder into your user-level `~/.agents/skills/`, or a project's `.agents/skills/` directory. The resulting path ends in `<skill-name>/SKILL.md`. On Windows, `~` means your user profile directory.

Start a fresh session if necessary and invoke `$<skill-name>`, replacing the placeholder with the installed skill's name. Alternatively, ask Codex's skill installer to install the selected folder from your local checkout or the appropriate repository ref. Avoid installing duplicate copies at multiple scopes.

See [OpenAI's skill documentation](https://learn.chatgpt.com/docs/build-skills) for current discovery and plugin distribution options.

## Claude Code

Copy the selected skill folder into `~/.claude/skills/` for personal use, or `.claude/skills/` in a project. Invoke `/<skill-name>`, replacing the placeholder with the installed skill's name, in a session where it is available.

See [Claude Code skills](https://code.claude.com/docs/en/skills). Claude Code's local skill directories are distinct from account-uploaded skills used by other Claude surfaces.

## Claude desktop

Package the entire selected skill folder as a ZIP, with that folder at the archive root. In **Customize > Skills**, use the custom-skill upload option and enable the skill. Follow the current [Claude skill instructions](https://support.claude.com/en/articles/12512180-use-skills-in-claude), including any account requirements.

Configure any application or tool connections required by the selected skill separately. Uploading a skill does not establish those connections.

## ChatGPT desktop

Use the desktop application's available skill installation/authoring flow to add this complete skill folder, following [OpenAI's skill documentation](https://learn.chatgpt.com/docs/build-skills). If the surface requires plugin packaging, this repository does not yet provide a published plugin; use a supported local skill workflow or report the packaging requirement. Do not describe a ZIP uploaded as ordinary chat context as an installed skill.

Verify that the skill appears in the client and that its required tools or application connections are actually available. Four-client live testing and published plugin distribution are still pending; see [compatibility](compatibility.md).

## OpenAI- and Claude-based API agents

Use the same complete skill folders. An API call or repository URL alone does not install a skill; configure the agent host's supported loading route:

- **OpenAI API:** attach a skill bundle to a supported hosted shell environment, or make the files available through the local runtime's skill configuration. Local and hosted attachment formats differ. Follow the [OpenAI Skills API guide](https://developers.openai.com/api/docs/guides/tools-skills).
- **Claude API:** upload each custom skill and attach it through the supported Skills integration, or use a host that loads local Agent Skills. Follow the [Claude Agent Skills documentation](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).
- **Custom host:** expose each skill's name, description and path for discovery, load its `SKILL.md` when selected, and make package-relative references/scripts accessible on demand. Preserve the distinction between instructions and executable supporting resources.

Blender skills also need a tool connection that can inspect and control the intended Blender session. A hosted code sandbox does not automatically reach the user's desktop or contain `bpy`; Blender Python helpers must run inside Blender. Do not claim application access merely because the skill files loaded successfully.

## Use an installed skill

Ask your assistant to use the skill by name and describe the result you want. Check the skill's prerequisites before starting. Where a setup skill is available, use it to verify the relevant application, account and connection.

## First available collection: Blender

The five application skills are under `skills/blender/`: `marso-blender-setup`, `marso-blender-asset`, `marso-blender-texture`, `marso-blender-kit`, and `marso-blender-compose`. Install all five for the complete Blender modelling, texturing and modular workflow, or select the ones you need. The application-independent `marso` entry skill is under `skills/core/`. Collections for other applications are not yet included.

After installation, ask: "Use marso-blender-setup to configure my Marso Blender add-on. I use the official Blender MCP."

The [Blender setup skill](../skills/blender/marso-blender-setup/SKILL.md) covers application-specific installation, account and folder settings, connections, troubleshooting and updates. Desktop control is optional; without it, the skill guides the necessary UI steps. Composition's optional snapping helper runs inside Blender through an available Python control tool, not in the assistant's ordinary Python environment.
