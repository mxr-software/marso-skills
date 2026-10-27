# Marso Skills

Skills for working with [Marso](https://marso.app/) in creative applications using an AI assistant.

Install the skills you need in your preferred assistant. Blender is the first available collection, covering setup, modelling, texturing and modular kits. For Blender, the Marso add-on connects directly to Marso's cloud services and works alongside Blender's official MCP connection; the hosted Marso MCP is optional for this route.

**Artist pilot:** use the `development` branch for small, reviewable tasks and feedback. The packages use the shared Agent Skills format; full client-to-Blender execution and artistic quality still need validation in your environment. Start with the [artist pilot guide](docs/artist-pilot.md).

## Available skills

| Skill | Purpose |
| --- | --- |
| [marso](skills/core/marso/SKILL.md) | Choose generation, modelling, restyling or kit workflows; discover supported 3D model settings. |
| [marso-blender-setup](skills/blender/marso-blender-setup/SKILL.md) | Install, configure, update, and troubleshoot Marso for Blender. |
| [marso-blender-asset](skills/blender/marso-blender-asset/SKILL.md) | Model editable assets from briefs, dimensions and images. |
| [marso-blender-texture](skills/blender/marso-blender-texture/SKILL.md) | Add textures, retexture, restyle and generate PBR using Marso. |
| [marso-blender-kit](skills/blender/marso-blender-kit/SKILL.md) | Decompose references or assets into reusable components and build fitting kits. |
| [marso-blender-compose](skills/blender/marso-blender-compose/SKILL.md) | Assemble existing kits using connection frames and fit checks. |

The workflows compose: model an asset, texture it with Marso, or build a reusable kit and assemble its components into a larger structure. Geometry-only requests do not trigger texture generation. General scene dressing remains deferred.

Start from what you want to achieve using the [installation bundles](docs/installation.md#choose-by-outcome). The `marso` entry skill helps choose a route; the five Blender skills carry out application-specific tasks. Explicit generation or modelling requests take priority. Organic and complex forms often suit generation; structured, articulated and modular assets often suit agent modelling.

## Get started

1. Follow [skill installation](docs/installation.md) for your assistant.
2. Choose the skills for your application and install their complete folders.
3. Use the relevant setup skill to check prerequisites, then describe the task you want to complete. For the current Blender collection, start with **"Use marso-blender-setup to get Marso working in Blender."**

Other requests:

- "Update my Marso Blender add-on and keep my existing settings."
- "Marso is installed, but its Library panel isn't loading. Diagnose it."
- "I already use the official Blender MCP. Set up Marso without the hosted Marso MCP."
- "Model an editable cabinet, then texture it with Marso as walnut with steel handles."
- "Restyle this chair in blue fabric, keeping the wooden frame."
- "Give this chair three finish variants from the original source, with clearly named materials."
- "Use Marso to generate an organic rock formation from this image."
- "Turn this shelving reference into a modular kit with compatible shelves and uprights."
- "Use this wall kit to make an L-shaped room with a doorway."

You need a Marso account for the add-on's cloud features. Enter credentials in the add-on, not in chat. Setup checks do not generate assets.

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

For the complete Blender modelling-to-texturing and kit workflow, install all five Blender folders; add `marso` for workflow and generation routing. Each skill states when a companion skill would help; none assumes sibling files are available at runtime. Behavioural acceptance cases live in [workflow cases](tests/blender/workflow-cases.md); [compatibility](docs/compatibility.md) distinguishes local checks from live assistant and cloud testing.

See [contributing](CONTRIBUTING.md) for authoring and validation. Skills are licensed under [Apache-2.0](LICENSE); Blender, its MCP, and the Marso add-on retain their own licences.
