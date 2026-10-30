# Install Marso skills

Marso skills are publicly available instructions for working with Marso in supported applications. Install the complete collection below, or choose individual skills from the [available skills](../README.md#available-skills).

Install each complete skill folder containing `SKILL.md`, including its `references/`, `scripts/`, and optional `agents/` metadata. Each folder packages independently; companion skills must be installed separately when needed. Installing skills provides instructions, but does not install creative applications, add-ons or tool connections.

In the examples below, `<skill-name>` means the actual folder name of the skill you selected. Keep that name unchanged when installing it. The first available collection is for Blender; its application setup is covered separately below.

The public collection is on the [`main` branch](https://github.com/mxr-software/marso-skills/tree/main). Download the repository ZIP from that branch, or clone it with `git clone --branch main https://github.com/mxr-software/marso-skills.git`. Start with [your first Marso project](getting-started.md). Installation commands and client capabilities change, so use the official client documentation linked below when the visible UI differs.

## Install the complete collection

**Choose by where you use the assistant.** For skills in your Claude account, [install the Marso plugin](#claude-desktop). For a local Codex or Claude Code installation, use the terminal command below. You do not need both. Running that command in a cloud chat's sandbox does not install skills on your computer or upload them to your Claude account.

### Codex and Claude Code

With Node.js and Git installed, open PowerShell or Terminal on your computer and run this in the project folder where you will use your assistant:

```bash
npx skills add mxr-software/marso-skills --skill '*'
```

The [Skills CLI](https://github.com/vercel-labs/skills) discovers the nested skill folders and installs every published skill from `main`, the repository's default branch. Keep the quotes around `'*'`, choose your agent when prompted, and select project or user-level installation. Add `--global` to install across projects. Choose one scope to avoid duplicate installations. This third-party installer is optional; manual routes are below.

To explicitly select Codex and Claude Code, install for your user account, and use copies rather than links:

```bash
npx skills add mxr-software/marso-skills --skill '*' --agent codex claude-code --global --copy
```

Keep only the agent name you use. To explicitly select `main` instead of following the default branch, replace `mxr-software/marso-skills` with `https://github.com/mxr-software/marso-skills/tree/main`.

The command installs the complete skill collection on `main`: the workflow coordinator, generation and library routes, Blender creation/render workflows, and four scene skills. The scene workflows remain development previews with additional requirements listed below. Future skills published on `main` are included when you run the command again; unmerged changes on other branches are not.

**Verify:** run `npx skills list --agent codex claude-code` in the same project (add `--global` for a global installation), then start a session in that project. Ask the assistant to list its available Marso skills and use `marso-blender-setup` to check Blender. If a skill is missing, check the install scope and restart the client. A successful file installation does not verify Blender access.

**Update:** rerun the installation command with the same branch, agents and scope, reviewing any replacement prompt. Keep personal edits elsewhere because updating installed copies can replace them.

### Other assistants

| Assistant | How to install the collection |
| --- | --- |
| Claude web / desktop account | Add `mxr-software/marso-skills` as a plugin marketplace and install `marso` once for the complete skill collection. Individual skill ZIPs are a fallback. |
| ChatGPT desktop | Local Codex skill discovery is documented below. A packaged ChatGPT plugin for installing the whole collection is not provided yet; the standalone ChatGPT installation route has not been verified for this repository. |
| API or custom agent | Configure the host to load each complete skill folder. See the API section below; a repository link alone does not install them. |

There is no single installer verified across all of these surfaces. The shared skill format makes the instructions portable; each host still needs its own installation and application connection.

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
npx skills add https://github.com/mxr-software/marso-skills/tree/main --skill marso-blender-texture --agent codex claude-code
```

Replace the skill name or list several names from the bundles below; choose only the clients you use. The manual installation routes below work without this third-party installer.

## Choose by outcome

These are recommended combinations of existing folders, not separate packages. Install each listed folder using your assistant's instructions below. Add the application-independent [`marso`](../skills/core/marso/SKILL.md) entry skill from `skills/core/marso/` when you want help choosing the route.

| What you want | Skills to install |
| --- | --- |
| Choose or coordinate a complete workflow | `marso` plus the relevant specialists below |
| Generate/edit images or prepare realistic appearance references | `marso-image`; add `marso-blender-texture` for an authorized Blender Retexture/PBR handoff |
| Reuse assets from the Marso library | `marso-library` |
| Optimize Blender render time, memory or repeated assets | `marso-blender-render` |
| Model an asset in Blender and texture it with Marso | `marso-blender-setup`, `marso-blender-asset`, `marso-blender-texture` |
| Restyle an existing Blender asset or make several looks from its original source | `marso-blender-setup`, `marso-blender-texture` |
| Build, texture and assemble a modular Blender kit | Blender setup, asset, texture, kit and compose |
| Generate an asset through the Blender add-on | `marso-generate`, `marso-blender-setup`; add texture for later Restyle and style variants |
| Turn photographs of a room into a scene graph and plan its assets | `marso-scene-decompose`, `marso-scene-graph`; add `marso-generate` to generate planned objects |
| Rebuild a photographed room in Blender from Marso assets | `marso`, `marso-library`, `marso-generate`, `marso-blender-asset`, `marso-blender-texture`, `marso-scene-decompose`, `marso-scene-graph`, `marso-blender-setup`, `marso-blender-scene-assets`, `marso-blender-place-scene` |
| Generate through a connected Marso Studio service | `marso-generate`, plus the service's current tools and workflow guides |

The two scene skills run Python scripts from their own folders and need Python 3.10+ with Pillow (`pip install Pillow`) and a host that can run shell commands and look at local images. They need no application connection or network access. `marso-blender-scene-assets` and `marso-blender-place-scene` run standard-library Python scripts and need Blender with the official MCP and a Marso add-on that provides the scene commands they name.

The four scene skills are included on `main` as development previews. The two scene workflows in Blender require a development add-on with their named commands; a release version number alone is insufficient. See [compatibility](compatibility.md). Each preview folder has its own proprietary licence permitting installation and use with Marso; its terms apply separately from the Apache-2.0 skills.

If you prefer to install from a local checkout, run these commands in your working project directory:

```bash
git clone --branch main https://github.com/mxr-software/marso-skills.git marso-skills
npx skills add ./marso-skills --skill '*' --agent codex claude-code --copy
```

The installer places skills in that project's agent directories. Review the [compatibility status](compatibility.md) before starting a scene workflow.

The entry skill discovers available capabilities; it does not supply Studio credentials or install connections. A working Blender add-on route does not require a separate hosted Marso MCP. See compatibility for the execution checks completed for each route.

## Codex

Copy the selected skill folder into your user-level `~/.agents/skills/`, or a project's `.agents/skills/` directory. The resulting path ends in `<skill-name>/SKILL.md`. On Windows, `~` means your user profile directory.

Start a fresh session if necessary and invoke `$<skill-name>`, replacing the placeholder with the installed skill's name. Alternatively, ask Codex's skill installer to install the selected folder from your local checkout or the appropriate repository ref. Avoid installing duplicate copies at multiple scopes.

See [OpenAI's skill documentation](https://learn.chatgpt.com/docs/build-skills) for current discovery and plugin distribution options.

## Claude Code

Copy the selected skill folder into `~/.claude/skills/` for personal use, or `.claude/skills/` in a project. Invoke `/<skill-name>`, replacing the placeholder with the installed skill's name, in a session where it is available.

Alternatively, enter this directly in a **Claude Code conversation** (version 2.1.275 or later) to install the plugin:

```text
/plugin install marso --marketplace mxr-software/marso-skills
```

On versions without that shortcut, use:

```text
/plugin marketplace add mxr-software/marso-skills
/plugin install marso@marso-skills
```

These commands target Claude Code's plugin manager, not an ordinary Claude web chat. Use either the plugin or standalone skill installation to avoid duplicates. Plugin skill commands are namespaced, for example `/marso:marso-blender-setup`.

See [Claude Code skills](https://code.claude.com/docs/en/skills). Claude Code's local skill directories are distinct from account-uploaded skills used by other Claude surfaces.

## Claude desktop

### Recommended: install the collection as one plugin

In Claude on the web or desktop:

1. Open **Customize > Plugins**.
2. Choose **Add > Add marketplace > Add from a repository**.
3. Enter `mxr-software/marso-skills` (or its full GitHub URL).
4. Open the added marketplace and install **marso**. It contains the complete skill collection and its supporting files.
5. Start a new chat and ask Claude to use Marso to check your Blender setup.

Claude documents plugins for paid plans; organization settings can restrict them. See [Claude's plugin guide](https://support.claude.com/en/articles/13837440-use-plugins-in-claude) if the UI differs. The repository supplies the marketplace and plugin manifests; account UI installation must still be verified in your environment. The plugin bundles skills only, so Blender and Marso connections must be configured separately.

### Fallback: upload individual skills

Use this if your account supports custom skills but the plugin route is unavailable:

1. [Download the released skill ZIPs](https://github.com/mxr-software/marso-skills/releases/latest/download/marso-skills-claude.zip).
2. Unzip that download on your computer. It contains one ZIP per skill in that release. Keep those inner ZIPs zipped.
3. In Claude, open **Customize > Skills > + > Create skill > Upload a skill**.
4. Upload one inner ZIP, then repeat for the other skills you want. To install the complete collection, upload all included skills.
5. Enable the uploaded skills and start a new chat. Ask Claude to use `marso-blender-setup` to check the Blender connection.

Each inner ZIP contains the complete skill folder, including its references, scripts, assets and licence. Do not upload the outer download as one skill, paste the terminal command into chat, or save only `SKILL.md`: those routes do not install the complete collection into your account. Individual ZIPs are also available on the [release downloads page](https://github.com/mxr-software/marso-skills/releases/latest).

For manual packaging, ZIP each complete skill folder with that folder at the archive root. Follow the current [Claude skill instructions](https://support.claude.com/en/articles/12512180-use-skills-in-claude), including account settings. If Skills is unavailable, check that code execution and file creation are enabled.

Some Claude Code versions also sync enabled account skills when signed in with the same Claude account. That sync does not upload locally installed skills back into the account. Avoid installing duplicate local copies if account sync already provides the skills; see [Claude's documentation](https://support.claude.com/en/articles/12512180-use-skills-in-claude).

Configure any application or tool connections required by the selected skill separately. Uploading a skill does not establish those connections.

## ChatGPT desktop

OpenAI documents local skill directories for Codex and recommends plugins for distributing collections across ChatGPT. Use the [Codex route](#codex) for a local Codex session. A published ChatGPT plugin is not included, and this repository does not yet have a verified standalone ChatGPT import procedure. Follow [OpenAI's skill documentation](https://learn.chatgpt.com/docs/build-skills) for the installation options available in your client. A ZIP uploaded as ordinary chat context is not an installed skill.

Verify that the skill appears in the client and that its required tools or application connections are actually available. Four-client live testing and OpenAI plugin distribution are still pending; see [compatibility](compatibility.md).

## OpenAI- and Claude-based API agents

Use the same complete skill folders. An API call or repository URL alone does not install a skill; configure the agent host's supported loading route:

- **OpenAI API:** attach a skill bundle to a supported hosted shell environment, or make the files available through the local runtime's skill configuration. Local and hosted attachment formats differ. Follow the [OpenAI Skills API guide](https://developers.openai.com/api/docs/guides/tools-skills).
- **Claude API:** upload each custom skill and attach it through the supported Skills integration, or use a host that loads local Agent Skills. Follow the [Claude Agent Skills documentation](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).
- **Custom host:** expose each skill's name, description and path for discovery, load its `SKILL.md` when selected, and make package-relative references/scripts accessible on demand. Preserve the distinction between instructions and executable supporting resources.

Blender skills also need a tool connection that can inspect and control the intended Blender session. A hosted code sandbox does not automatically reach the user's desktop or contain `bpy`; Blender Python helpers must run inside Blender. Do not claim application access merely because the skill files loaded successfully.

## Use an installed skill

Ask your assistant to use the skill by name and describe the result you want. Check the skill's prerequisites before starting. Where a setup skill is available, use it to verify the relevant application, account and connection.

## First available collection: Blender

The application skills are under `skills/blender/`: `marso-blender-setup`, `marso-blender-asset`, `marso-blender-texture`, `marso-blender-kit` and `marso-blender-compose` for modelling, texturing and modular work, and `marso-blender-scene-assets` and `marso-blender-place-scene` for rebuilding a photographed room. Install the ones you need; the scene pair also needs `marso-scene-decompose` and `marso-scene-graph` from `skills/core/`. The application-independent `marso` entry skill is under `skills/core/`. Collections for other applications are not yet included.

After installation, ask: "Use marso-blender-setup to configure my Marso Blender add-on. I use the official Blender MCP."

The [Blender setup skill](../skills/blender/marso-blender-setup/SKILL.md) covers application-specific installation, account and folder settings, connections, troubleshooting and updates. Desktop control is optional; without it, the skill guides the necessary UI steps. Composition's optional snapping helper runs inside Blender through an available Python control tool, not in the assistant's ordinary Python environment.
