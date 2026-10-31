# From a good-looking mesh to a reusable asset

[Back to Marso Skills](../README.md) · [Try a workflow](workflows.md)

## What is PBR?

PBR means **physically based rendering**. A colour texture describes what a surface looks like; PBR describes how it responds to light. That is why brushed metal, worn leather and painted wood can feel different even when they have similar colours.

| Surface information | What you see |
| --- | --- |
| Base colour / albedo | The surface colour and artwork. |
| Roughness | Broad, soft reflections or sharper highlights. |
| Metallic | The difference between a metal surface and a non-metal coating. |
| Normal | Fine surface relief without adding geometry. |
| Index of refraction (IOR), when supplied | A material property used in its light response. |

Marso predicts material properties from the asset's appearance. These are predictions, not measurements of the original object. Use the maps actually returned by the operation, then review the result under more than one lighting condition.

Generate PBR keeps the existing appearance as its starting point. **Retexture changes the appearance first, then generates PBR.** Use Retexture for a new finish; use PBR alone when you already like the colour texture.

## What “minted” means in Marso

Completed PBR assets go through **USD minting**: Marso packages the asset and enriches it with information for reuse and simulation. USD is Universal Scene Description; USDZ packages a USD asset and its dependencies together. Minting here means creating that enriched asset package.

The minted result can carry much more than a mesh and textures:

| Information in the package | Why it matters |
| --- | --- |
| Geometry, material bindings and PBR textures | Render and relight the asset in another application. |
| Units, up axis, dimensions and scale information | Place it in a scene at a meaningful size. |
| Rigid-body, mass and collider information | Give a simulator a starting point for physical interaction. |
| Material density, friction and restitution | Describe weight, sliding and bounce. |
| Semantic labels, categories and material descriptions | Help tools understand and find the asset. |
| Condition, style and other descriptive enrichment | Support selection, organisation and downstream behaviours. |

This enrichment is what Marso calls **sim-ready**. An application still needs to read the supported USD fields, and a particular use may need review of scale, collision shape or predicted physical properties. A hinged mechanism also needs appropriate joints and articulation; PBR does not infer a working rig from every mesh.

**Wait for minting to finish.** PBR maps may be ready while USD enrichment is still running. A basic USD fallback is not evidence that enrichment succeeded. Ask your agent to verify the minted result and retain its library identity.

[![Marso assets in an Isaac Sim demonstration](assets/demos/sim-ready.jpg)](assets/demos/sim-ready.mp4)

[Watch the simulation excerpt →](assets/demos/sim-ready.mp4) The film shows Marso assets in Isaac Sim. Its numeric metadata overlays are illustrative; inspect your own minted file for its actual values.

## Use the information for more than rendering

A game can use a material label to choose a metal impact sound, or a surface condition to select interaction effects. A simulation can consume the authored collision and physics properties. An asset-search workflow can use appearance and meaning to find the right prop again.

These are uses for the asset's data, not an automatic sound-effect or gameplay generator. Your engine or application must connect the data to the behaviour you want. Exporting to a different format can omit USD metadata or custom shaders, so retain the minted USDZ as well as any engine-specific version.

## Your library becomes part of the workflow

Assets that complete Marso's PBR pipeline become reusable content in your personal Marso library, including assets made or retextured through the Blender add-on. Keep them in the relevant Studio project so the work remains understandable later.

Your agent can search the library by a short description, an object image, or both where the connection supports full-library search. It can then reuse the actual asset instead of creating a similar one from scratch. Reuse preserves a project's visual language and avoids unnecessary modelling or generation.

> Find the worn leather chair I made earlier. Show the closest matches, import the one I choose and place six shared instances around this table.

For a useful handoff, keep the original source, final asset ID, project, chosen appearance and local file together. A folder of downloaded files is useful; a searchable library with stable asset identities is far more useful for the next agent task.
