---
name: marso
description: Choose a Marso workflow when the user wants to make a 3D asset, model or generate an object, restyle an asset, create appearance variants, or use a modular kit and the route is not yet clear. Distinguish generative 3D from agent modelling, discover the working connection, and select supported generation options. Let an already selected specialist skill handle its task directly.
license: Apache-2.0
---

# Work with Marso

Translate the requested outcome into the appropriate workflow. Preserve the user's choice of application and working connection. Do not require the hosted Marso MCP when an application's Marso add-on already provides the needed operation.

## Choose from intent

An explicit request to generate or model takes precedence over the defaults below. When "make an asset" is ambiguous, infer from the required result; ask only when the choice materially affects the deliverable and the brief does not resolve it.

| Desired result | Route |
| --- | --- |
| Generate an asset from an image or description; organic or complex forms where approximate reconstruction is acceptable | Marso generative 3D; read [generation and model selection](references/generative-3d.md). |
| Model editable structured geometry; controlled topology, animation preparation, articulation or precise modular interfaces | Agent modelling through the target application's control tools. In Blender, use `marso-blender-asset` or `marso-blender-kit` when installed. |
| Change an existing asset's appearance, add a texture or restyle | Retexture the existing geometry. In Blender, use `marso-blender-texture` when installed. |
| Keep its current appearance and add PBR | Existing-appearance PBR route; do not silently restyle or regenerate the shape. |
| Make N styles of the same asset | One preserved source, independent Restyle branches for each look; use the texture skill's variants workflow. |
| Build components that fit together or decompose a reference into reusable parts | Kit design with explicit dimensions and interfaces; `marso-blender-kit` in Blender. |
| Arrange an existing kit | Composition with the kit's real connectors and material assignments; `marso-blender-compose` in Blender. |
| Break photographs of a room or environment into its objects, or get a scene graph from images | Scene decomposition; `marso-scene-decompose` when installed. Do not send a whole-room image straight to 3D generation. |
| Decide how many assets a scene needs, what to generate or model, or write each object's reference brief from a scene graph | Asset planning from the graph; `marso-scene-graph` when installed, then the routes above for each asset. |
| Use something already in the library | Find and inspect the existing asset through available library tools before importing; do not generate a replacement. |

Organic/complex forms favour generation as a starting point; structured, articulated or modular objects favour agent modelling. These are workflow defaults, not quality guarantees. Generated meshes can need retopology, part separation and scale correction; agent-built meshes still need topology and fit checks. A hybrid can generate decoration while modelling functional joints and mating surfaces. Preserve explicit user intent and explain a material tradeoff before substituting routes.

## Discover the connection

Inspect the tools actually available. Distinguish general application control, the Marso add-on and the hosted Studio connection. An installed skill supplies instructions, not a connection. For missing Blender setup, use `marso-blender-setup` when installed. Companion skills are separately installable; do not read assumed sibling paths. If a required specialist is absent, identify it or continue only through verified tools and their documented capabilities.

Read runtime schemas and capabilities before using generation parameters. Use the installed tool prefix rather than inventing one. Do not change accounts, stored defaults or project destinations merely to establish a preferred route. Keep setup and capability discovery non-generating.

## Preserve reusable intent

For a set, keep the same appearance-brief identity and approved reference across tasks, with each component's material roles and grain direction. The Blender texture skill maintains that brief with the asset or kit. An appearance reference guides similarity; it does not lock pixels across module boundaries.

Distinguish shape variants from style variants. Style variants branch from the unchanged original mesh, UVs and source appearance, not from the previous Restyle result. A request to refine a specific returned version may deliberately use that version as the new source; record that choice. Keep a clear source-to-result mapping and descriptive material names after application succeeds.

## Complete the chosen workflow

Follow job IDs to completion, inspect results and preserve originals. A timeout is not permission to resubmit. Deliver the saved asset or project, the chosen route, source and output identifiers where available, and the checks actually performed. State untested visual or application behaviour. A generated PBR result is not by itself proof of animation readiness, modular fit or validated simulation physics.
