---
name: marso
description: "Coordinate Marso image, asset and scene workflows: edit, reuse, generate, model, texture and place. Start here for broad or multi-stage requests; preserve explicit modelling/generation intent."
license: Apache-2.0
---

# Work with Marso

Translate the requested outcome into the appropriate workflow. Preserve the user's choice of application and working connection. Do not require the hosted Marso MCP when an application's Marso add-on already provides the needed operation.

## Choose from intent

An explicit request to generate or model takes precedence over the defaults below. When "make an asset" is ambiguous, infer from the required result; ask only when the choice materially affects the deliverable and the brief does not resolve it.

| Desired result | Route |
| --- | --- |
| Generate or edit an image, or author realistic appearance references and style images | `marso-image` when installed. Image work does not automatically authorize mesh generation or Retexture. |
| Generate an asset from an image or description; organic or complex forms where approximate reconstruction is acceptable | `marso-generate` when installed: live model selection and reusable user preferences. |
| Model editable structured geometry; controlled topology, animation preparation, articulation or precise modular interfaces | Agent modelling through the target application's control tools. In Blender, use `marso-blender-asset` or `marso-blender-kit` when installed. |
| Change an existing asset's appearance, add a texture or restyle | Retexture the existing geometry, then PBR and final material review. In Blender, use `marso-blender-texture` when installed; use `marso-image` for a requested image-reference authoring stage. |
| Keep its current appearance and add PBR | Existing-appearance PBR route; do not silently restyle or regenerate the shape. |
| Populate a scene with differently labelled/finished cans, boxes or other repeated shapes | Group by actual geometry; one master per shape family, multiple appearances, then instances. Use the texture skill's appearance-families route. Different weapon/shield silhouettes remain distinct geometry; identical chairs need ordinary instances. |
| Make N styles of the same asset | One preserved source, independent Restyle branches for each look; use the texture skill's variants workflow. |
| Animate or control a change from clean to dirty, rusty, wet or scorched | Source-based PBR states, then the Blender texture skill's appearance-state workflow for a slider/mask. Geometry damage and physical simulation are separate tasks. |
| Build components that fit together or decompose a reference into reusable parts | Kit design with explicit dimensions and interfaces; `marso-blender-kit` in Blender. |
| Arrange an existing kit | Composition with the kit's real connectors and material assignments; `marso-blender-compose` in Blender. |
| Break photographs of a room or environment into its objects, or get a scene graph from images | Scene decomposition; `marso-scene-decompose` when installed. Do not send a whole-room image straight to 3D generation. |
| Decide how many assets a scene needs, what to generate or model, or write each object's reference brief from a scene graph | Asset planning from the graph; `marso-scene-graph` when installed, then the routes above for each asset. |
| Rebuild a photographed room or complete a Blender scene | Read [complete scene workflow](references/scene-workflow.md). Coordinate decomposition, planning, reuse/generation/modelling, placement and finish; do not stop at the graph. |
| Generate an already reviewed scene asset plan | `marso-blender-scene-assets`; preserve non-generation routes for their own handoffs. |
| Reduce render time or memory, use repeated assets efficiently, or render a Blender scene | `marso-blender-render` when installed. |
| Use something already in the library, or check for one before generating | `marso-library` when installed: resolve a selected asset directly, or search by description/image. Do not generate a replacement for an asset the user chose to reuse. |

Organic/complex forms favour generation as a starting point; structured, articulated or modular objects favour agent modelling. These are workflow defaults, not quality guarantees. Generated meshes can need retopology, part separation and scale correction; agent-built meshes still need topology and fit checks. A hybrid can generate decoration while modelling functional joints and mating surfaces. Preserve explicit user intent and explain a material tradeoff before substituting routes.

## Discover the connection

Inspect the tools actually available. Distinguish general application control, the Marso add-on and the hosted Studio connection. An installed skill supplies instructions, not a connection. For missing Blender setup, use `marso-blender-setup` when installed. Companion skills are separately installable; do not read assumed sibling paths. If a required specialist is absent, identify it or continue only through verified tools and their documented capabilities.

Read runtime schemas and capabilities before using generation parameters. Use the installed tool prefix rather than inventing one. Do not change accounts, stored defaults or project destinations merely to establish a preferred route. Keep setup and capability discovery non-generating.

For recurring generation, establish the user's preferred model/options once and reuse supported choices. Record explicit preferences through supported host memory or a local project record; never claim memory that is not available. Set scene-level geometry/texture targets for multi-object work, rather than repeatedly asking each prop's polygon count. Read live capabilities before every new run.

## Preserve reusable intent

For a set, keep the same appearance-brief identity and approved reference across tasks, with each component's material roles and grain direction. The Blender texture skill maintains that brief with the asset or kit. An appearance reference guides similarity; it does not lock pixels across module boundaries.

Distinguish shape variants from style variants. Style variants branch from the unchanged original mesh, UVs and source appearance, not from the previous Restyle result. A request to refine a specific returned version may deliberately use that version as the new source; record that choice. Keep a clear source-to-result mapping and descriptive style labels. Keep managed material names stable during jobs and on legacy name-based prepared state; rename after application only with verified identity-based tracking or a supported rename operation.

Explicit cumulative appearance states are a separate route: state 1 may feed state 2, then state 3, with PBR for every state. Preserve the original and intermediate results, record the selected lineage, and use the texture skill's state workflow to verify correspondence and controls. Independent finishes still default to sibling branches.

For agent-modelled assets that will be textured, show neutral-clay previews and wait for the user's approval of the current geometry before Marso Retexture or PBR. Honour an explicit review waiver or existing approval of unchanged geometry. A finished-asset request alone does not waive model review; directly retexturing an existing unchanged asset needs no extra model-approval step.

## Complete the chosen workflow

Follow job IDs to completion, inspect results and preserve originals. A timeout is not permission to resubmit. Deliver the saved asset or project, the chosen route, source and output identifiers where available, and the checks actually performed. State untested visual or application behaviour. A generated PBR result is not by itself proof of animation readiness, modular fit or validated simulation physics.
