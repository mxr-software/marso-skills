<p align="center">
  <a href="https://marso.app/"><img src="docs/assets/marso-skills.png" alt="Marso Skills — create in 3D with your AI agent. Model or generate, retexture with PBR, and reuse your assets." width="100%"></a>
</p>

# Marso Skills

**Build, texture and assemble 3D assets with your AI agent and [Marso](https://marso.app/).**

Start with an idea, a reference image or an existing asset. These skills guide your agent through modelling, generation, realistic materials and reusable kits. **Blender is the first supported application.**

[Install](#install) · [Try a workflow](#try-a-workflow) · [Available skills](#available-skills) · [Getting started](docs/getting-started.md) · [Compatibility](docs/compatibility.md)

## Install

Choose the assistant you use. Each route installs the complete collection; you only need one.

### Codex, Claude Code and other local agents

Run this in **PowerShell or Terminal on your computer**, inside your project folder:

```bash
npx skills add mxr-software/marso-skills --skill '*'
```

Requires **Node.js and Git**. Choose your agent when prompted. Add `--global` to use the skills across projects. This installs skills from `main` on your computer; it does not install them into a web chat account.

### Claude web or desktop

Open **Customize → Plugins → Add → Add marketplace → Add from a repository**. Enter:

```text
mxr-software/marso-skills
```

Then install **marso** for the whole collection. Requires an account and plan that allow plugins. [Step-by-step guide and ZIP fallback →](docs/installation.md#claude-desktop)

<details>
<summary><strong>Prefer the Claude Code plugin?</strong></summary>

Paste this into a **Claude Code conversation** (version 2.1.275 or later):

```text
/plugin install marso --marketplace mxr-software/marso-skills
```

Use this instead of installing standalone skills with the terminal command above.

</details>

[Other clients and API hosts](docs/installation.md) · [Update your installation](docs/installation.md#install-the-complete-collection)

## Your first asset

Tell your agent:

> Use Marso to model an editable wooden cabinet in Blender. Show me the model before texturing it, then finish it with worn walnut and steel handles. Check my setup first and save the Blender file.

You do not need to choose individual skills. Describe the result, attach references if you have them, and say whether you want the agent to **model** the object or **generate** it with Marso. The `marso` entry skill coordinates the workflow.

**For Blender:** you need Blender, a Marso account, the Marso Blender add-on and an agent connection that can control Blender. The setup skill checks what is available. The default connection uses Blender MCP alongside the Marso add-on; a separate hosted Marso MCP is optional. Enter credentials in the add-on, not in chat.

Installing skills adds instructions. It does not install Blender or connect your assistant to it. [Check your setup →](docs/getting-started.md)

## Try a workflow

| What you want | What to tell your agent |
| --- | --- |
| **Model an editable asset** | “Model a coffee table in Blender from this reference. Match its proportions and show me the geometry before texturing.” |
| **Generate a 3D asset** | “Use Marso to generate an organic rock formation from this image.” |
| **Texture or restyle** | “Restyle this chair in blue woven fabric with an oak frame, then generate PBR textures.” |
| **Create appearance variants** | “Give this can six label designs, keeping its shape. Make each variation from the original source.” |
| **Build and assemble a kit** | “Turn this shelving reference into compatible shelves and uprights, then assemble three shelving units.” |
| **Reuse and optimize** | “Find a chair in my Marso library and use shared instances around this table. Check the scene’s GPU memory use.” |

The skills guide the agent to prepare geometry and UVs for texturing, show newly modelled geometry for approval, and follow Retexture with PBR. Geometry-only requests stay geometry-only. Image generation and editing can also run as standalone workflows.

### From photographs to a scene · Preview

> Decompose these room photographs, identify the unique assets, and help me choose which to model, generate or reuse before building the scene in Blender.

Four scene skills cover decomposition, planning, asset creation and placement. They are included in every complete installation. **The Blender scene workflows require a supporting development add-on build** with the named commands. [Check the requirements before starting →](docs/installation.md#choose-by-outcome)

## Available skills

**14 skills, one collection.** Start with `marso` to coordinate a task, or use a specialist directly.

<details>
<summary><strong>Core workflows · 4 skills</strong></summary>

| Skill | What it does |
| --- | --- |
| [marso](skills/core/marso/SKILL.md) | Choose and coordinate workflows across creation, texturing, reuse and scenes. |
| [marso-image](skills/core/marso-image/SKILL.md) | Generate and edit images, appearance references and coordinated style variations. |
| [marso-generate](skills/core/marso-generate/SKILL.md) | Generate 3D assets using supported options and the user’s preferred models. |
| [marso-library](skills/core/marso-library/SKILL.md) | Find and reuse library assets, instances and original style sources. |

</details>

<details>
<summary><strong>Blender workflows · 6 skills</strong></summary>

| Skill | What it does |
| --- | --- |
| [marso-blender-setup](skills/blender/marso-blender-setup/SKILL.md) | Install, configure, update and troubleshoot the Marso connection. |
| [marso-blender-asset](skills/blender/marso-blender-asset/SKILL.md) | Model editable assets from briefs, dimensions and images. |
| [marso-blender-texture](skills/blender/marso-blender-texture/SKILL.md) | Prepare assets for Marso, retexture, restyle and generate PBR. |
| [marso-blender-kit](skills/blender/marso-blender-kit/SKILL.md) | Decompose references into reusable parts and build fitting kits. |
| [marso-blender-compose](skills/blender/marso-blender-compose/SKILL.md) | Assemble existing kits using connection frames and fit checks. |
| [marso-blender-render](skills/blender/marso-blender-render/SKILL.md) | Optimize render settings, GPU memory and instances; create requested images. |

</details>

<details>
<summary><strong>Scene workflows · 4 preview skills</strong></summary>

| Skill | What it does |
| --- | --- |
| [marso-scene-decompose](skills/core/marso-scene-decompose/SKILL.md) | Identify objects in photographs and build a scene graph with an interactive viewer. |
| [marso-scene-graph](skills/core/marso-scene-graph/SKILL.md) | Plan unique assets, counts, reference briefs and creation routes. |
| [marso-blender-scene-assets](skills/blender/marso-blender-scene-assets/SKILL.md) | Create the planned scene assets in Marso through Blender. |
| [marso-blender-place-scene](skills/blender/marso-blender-place-scene/SKILL.md) | Import and place assets with an editable transform hierarchy. |

See [compatibility and verification status](docs/compatibility.md) for required capabilities and testing limits.

</details>

## Help and contributing

- **New to Marso?** Start with [your first project](docs/getting-started.md).
- **Installing, updating or changing agents?** Use the [installation guide](docs/installation.md).
- **Checking whether a workflow is supported?** Read [compatibility](docs/compatibility.md).
- **Found an issue?** [Report it](https://github.com/mxr-software/marso-skills/issues) with your assistant, Blender/add-on versions and the step that failed. Keep credentials and private project data out of reports.
- **Contributing a skill?** Read [contributing](CONTRIBUTING.md) for layout and validation.

Skills use the shared `SKILL.md` format. Install each complete skill folder with its references and scripts. Client support depends on the host’s installation and tool access; the format alone does not establish a tested integration.

## Licence

Most skills use [Apache-2.0](LICENSE). The four scene preview skills have their own proprietary `LICENSE.txt` files permitting installation and use with Marso. Blender, its MCP and the Marso add-on retain their own licences.

Header: woven chair from the Marso library. [Artwork source and editing notes](docs/assets/README.md).
