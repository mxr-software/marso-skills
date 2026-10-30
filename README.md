# Marso Skills

**Build, texture and assemble 3D assets with your AI agent and [Marso](https://marso.app/).**

Describe what you want to create. Marso skills guide your agent through the work, from setting up the connection to saving the finished asset. Blender is the first supported application.

- **Make assets:** model editable objects from a brief or reference, or generate 3D assets with Marso.
- **Create images:** generate or edit images, including realistic appearance references and coordinated style variations.
- **Texture and restyle:** add materials, change an asset's look, create finish variants and add PBR.
- **Build modular kits:** design parts that fit together, texture them and assemble reusable structures.
- **Reuse your library:** find existing assets and build scenes with shared instances.
- **Optimize Blender scenes:** diagnose render time and GPU memory, preserving geometry and texture quality.
- **Get connected:** install, configure and troubleshoot the Marso Blender add-on.

## Install all Marso skills

**Claude on the web or desktop:** open **Customize → Plugins → Add → Add marketplace → Add from a repository**, enter `mxr-software/marso-skills`, then install **marso**. One plugin contains the complete skill collection. Requires a plan and account settings that allow plugins. [Step-by-step guide and ZIP fallback](docs/installation.md#claude-desktop).

**Already in Claude Code?** Paste this into its conversation (version 2.1.275 or later):

```text
/plugin install marso --marketplace mxr-software/marso-skills
```

**Codex or other supported local agents:** run this in **PowerShell or Terminal**. This also works for Claude Code if you prefer standalone skills instead of the plugin:

```bash
npx skills add mxr-software/marso-skills --skill '*'
```

Requires **Node.js and Git**. Run it in your project folder and choose your agent when prompted. Add `--global` to use the skills across projects. The command installs the complete skill collection from `main`. It does not upload skills to your Claude account; use the account plugin route above for that.

[Installation, updates and other clients](docs/installation.md#install-the-complete-collection) · [Your first Marso project](docs/getting-started.md) · [Compatibility](docs/compatibility.md)

## Tell your agent what to build

Then tell your assistant:

> Use Marso to model an editable wooden cabinet in Blender and texture it as worn walnut with steel handles. Check my setup first, then save the Blender file.

Use ordinary language; your agent chooses the relevant skills. Include reference images, dimensions and the desired finish when you have them.

For Blender workflows, you need Blender, a Marso account, the Marso add-on and a connection that lets your agent control Blender. Start with `marso-blender-setup` if anything is missing. The default route uses Blender MCP alongside the Marso add-on; a separate hosted Marso MCP is optional. Enter credentials in the add-on, not in chat.

## Available skills

| Skill | Purpose |
| --- | --- |
| [marso](skills/core/marso/SKILL.md) | Coordinate creation and complete scenes across specialist workflows. |
| [marso-image](skills/core/marso-image/SKILL.md) | Generate/edit images and inspect realistic appearance references before 3D transfer. |
| [marso-generate](skills/core/marso-generate/SKILL.md) | Generate 3D assets with supported options and remembered user preferences. |
| [marso-library](skills/core/marso-library/SKILL.md) | Find and reuse library assets, instances and style sources. |
| [marso-blender-render](skills/blender/marso-blender-render/SKILL.md) | Optimize render settings, GPU memory and shared instances; create requested images. |
| [marso-blender-setup](skills/blender/marso-blender-setup/SKILL.md) | Install, configure, update, and troubleshoot Marso for Blender. |
| [marso-blender-asset](skills/blender/marso-blender-asset/SKILL.md) | Model editable assets from briefs, dimensions and images. |
| [marso-blender-texture](skills/blender/marso-blender-texture/SKILL.md) | Add textures, retexture, restyle and generate PBR using Marso. |
| [marso-blender-kit](skills/blender/marso-blender-kit/SKILL.md) | Decompose references or assets into reusable components and build fitting kits. |
| [marso-blender-compose](skills/blender/marso-blender-compose/SKILL.md) | Assemble existing kits using connection frames and fit checks. |

The collection also includes four scene workflows in development preview:

| Preview skill | Purpose |
| --- | --- |
| [marso-scene-decompose](skills/core/marso-scene-decompose/SKILL.md) | Identify objects in room photographs and build a scene graph with an interactive viewer. |
| [marso-scene-graph](skills/core/marso-scene-graph/SKILL.md) | Plan unique assets and counts, per-object reference briefs and crops, and generation or modelling routes. |
| [marso-blender-scene-assets](skills/blender/marso-blender-scene-assets/SKILL.md) | Generate a scene's planned assets in Marso from Blender: reference image, mesh, PBR, minted. |
| [marso-blender-place-scene](skills/blender/marso-blender-place-scene/SKILL.md) | Import and place a scene's minted assets in Blender with an editable transform hierarchy. |

The scene skills are included in the installation. Their Blender generation and placement workflows require a supporting development add-on. See [workflow requirements](docs/installation.md#choose-by-outcome).

The workflows compose: model an asset, texture it with Marso, or build a reusable kit and assemble its components into a larger structure. Geometry-only requests do not trigger texture generation. Photographed-scene workflows add decomposition, asset planning and initial placement; their generation/import commands currently require a development add-on build.

Start from what you want to achieve using the [installation bundles](docs/installation.md#choose-by-outcome). The `marso` entry skill helps choose a route; the specialist workflows carry out each stage. Explicit generation or modelling requests take priority. Organic and complex forms often suit generation; structured, articulated and modular assets often suit agent modelling.

## What you can ask for

- "Update my Marso Blender add-on and keep my existing settings."
- "Marso is installed, but its Library panel isn't loading. Diagnose it."
- "I already use the official Blender MCP. Set up Marso without the hosted Marso MCP."
- "Model an editable cabinet, then texture it with Marso as walnut with steel handles."
- "Restyle this chair in blue fabric, keeping the wooden frame."
- "Give this chair three finish variants from the original source, with clearly named materials."
- "Use Marso to generate an organic rock formation from this image."
- "Turn this shelving reference into a modular kit with compatible shelves and uprights."
- "Use this wall kit to make an L-shaped room with a doorway."
- "Decompose these four kitchen photos into a scene graph and tell me how many unique assets to make."

Setup checks do not generate assets. Photographed-scene requests require the preview skills and their documented prerequisites.

## Compatibility

The skills use the shared `SKILL.md` format for OpenAI- and Claude-based agents. Use the [client or API installation route](docs/installation.md) for your host. Installing instructions does not itself give an assistant desktop or Blender access. See [compatibility and verification status](docs/compatibility.md) before treating a client as tested.

## Repository layout

```text
skills/<application>/<skill-name>/   Installable skills and their own references
skills/core/marso/                  Application-independent workflow entry point
docs/                         Installation and compatibility information
tests/blender/                Behavioural acceptance cases
```

Copy the entire skill folder when installing it. Its runtime references stay inside that folder so it works independently of this repository.

`docs/` explains installation and compatibility; `tests/` and `AGENTS.md` are for repository maintenance. They are not part of an installed skill. Detailed experiments, generated assets and local service snapshots are excluded from distribution.

For the Blender modelling-to-texturing and kit workflow, install setup, asset, texture, kit and compose; add `marso` for coordination, `marso-image` for image authoring, `marso-generate` for 3D generation and `marso-library` for reuse. Each skill states when a companion skill would help; none assumes sibling files are available at runtime. Behavioural acceptance cases live in [workflow cases](tests/blender/workflow-cases.md); [compatibility](docs/compatibility.md) distinguishes local checks from live assistant and cloud testing.

See [contributing](CONTRIBUTING.md) for authoring and validation. Skills are licensed under [Apache-2.0](LICENSE), except `marso-scene-decompose`, `marso-scene-graph`, `marso-blender-scene-assets` and `marso-blender-place-scene`, which carry their own proprietary `LICENSE.txt`; Blender, its MCP, and the Marso add-on retain their own licences.
