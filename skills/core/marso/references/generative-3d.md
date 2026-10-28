# Generative 3D and model selection

Use this route when the user wants generation, or the brief favours an organic/complex form over controlled construction. Prefer agent modelling for structured parts, clean controllable topology, animation/articulation structure and modular interfaces when that meets the user's intent. Texturing an existing mesh does not require generating its geometry again.

## Select a supported generator

Before generating an object the user's library might already hold, check the library unless the user asked for a new asset; read [library](library.md). Generate only when nothing suitable came back or the user declines what did.

First establish the source (description, one object image, or consistent views of that same object), required geometric detail and intended use. A fabric swatch is a look reference, not the object to reconstruct. A whole-room image needs an object extraction workflow rather than being treated as one prop: decompose it into a scene graph (`marso-scene-decompose`) and generate each object from its own reference brief (`marso-scene-graph`), when those skills are installed.

Inspect the installed Blender `generate_state` model catalogue and `create_3d_asset` schema, or Studio `get_capabilities` with `section: "generation_3d_models"` and full detail. Refresh after a capability error. Model availability and option names can differ between routes and versions. Use catalogue IDs, not guessed names. The catalogue's source support does not prove that a particular tool accepts that input directly.

Select in this order:

1. Honour the user's explicit supported model and settings.
2. Keep a compatible saved/panel preference.
3. Filter by required input and supported polygon/texture settings; use the route's advertised default if it satisfies those constraints.
4. If constraints exclude the default, select a compatible catalogue entry and state why. If several remain and the user has no preference, a current offered version in the qualifying family is a starting choice, not a claim of superior quality. Do not run a model comparison unless requested.

Filter polygon counts, source modes and texture options against the live catalogue and the chosen tool's schema. Do not rely on a saved catalogue or an example model ID as a current default. A higher polygon count does not establish cleaner topology or better articulation. Texture resolution/quality controls appearance sampling, not geometric accuracy. Do not infer "best for furniture" or "best for organics" rankings from version numbers or option lists; those preferences need representative tests or user-provided evidence.

Do not silently replace an unsupported requested setting. Explain the nearest supported choice or missing capability. Keep the final imported count/dimensions distinct from the requested generation parameters. If the mesh will later go through Blender Retexture, inspect its input image limits before selecting higher texture resolutions; the inspected add-on preflight rejects images over 4096 pixels. Preserve the original and prepare a compatible working copy when necessary.

## Blender add-on route

Use the existing authorized Blender connection. Discover Marso's enabled extension module and its command registry if no dedicated tool exposes the operation; inspect `all_commands()` / `describe()` before using `execute(name, params)`. This internal interface is version-bound. Do not assume that a source checkout's commands are installed.

The reviewed implementation exposes `generate_state`, `upload_image`, `generate_image` and `create_3d_asset`. Read state and in-flight jobs first. For an object photo, upload it through the discovered `filepath` parameter; for a description, generate an object reference image. Inspect the reference before reconstruction without adding a mandatory approval pause. Use the user's requested review points.

Resolve the task's Studio destination before generation. Recent add-ons expose `save_to_state`, asynchronous `list_studio_projects` and `create_studio_project`, and `set_save_project` with a returned `project_id`. Refresh the list, retain/select a relevant project or create a descriptive new one, then read back the selected ID/name and save the .blend. Library browsing is separate. Verify the selection after reopening and check completed outputs in the intended graph. If an older build cannot select the required destination, resolve that capability gap rather than defaulting to an unrelated Blender project. Reconcile uncertain project creation before repeating it.

The current `create_3d_asset` schema accepts `model`, `polygon_count`, `texture` and `wait_for_mint`. `texture` is a Meshy resolution (`2k`, `4k`, `8k`) or Tripo quality (`standard`, `detailed`); omit it for Hunyuan. Older builds may expose fewer or no model controls. Read the chosen values back; do not claim an override was used if that build cannot accept it. Preserve a working add-on route when sufficient.

Follow the returned `job_id` with later `get_job` calls; do not block Blender's main thread or reset busy flags. Reconcile existing work after interruption before creating another asset. The inspected route imports after PBR by default; waiting for mint is a separate option. Inspect the actual artifact's scale/physics state rather than labelling an early import simulation-ready.

## Studio route

Use this when the user works in Studio or its connected tools supply the needed capability. Inspect the connected service's guides and schemas for the recipe and use the current project/graph. Keep the user's authorized task scope and review preferences; this skill adds no spending-allowance or credit-confirmation workflow.

Confirm that the current project belongs to the user's task. If none does, create a descriptively named project through the available project tool and retain its returned project/graph references for every node and execution. Verify outputs there and save those references with the deliverable. Do not assume a project selected in a different application, account or Library view is this route's destination.

The inspected `generate-3d` node takes an image even when a model catalogue lists text support. A description therefore becomes an object-mode image before the mesh. `build_object_chain` can create that linked chain from an image asset, an existing image node or a prompt source. Do not feed a scene-mode image or its descendants into direct 3D generation; use the supported object-extraction recipe. Do not invent a direct text-to-mesh or multiview parameter.

Pass the selected model and supported settings through the actual builder/node schema. Studio uses `texture_resolution` for Meshy and `texture_quality` for Tripo; those are not interchangeable with the Blender command's `texture` parameter. Run the image step when needed, then the mesh, and PBR if requested. Retain run and node IDs, recover uncertain outcomes, and read completed outputs from the graph. Preserve the source image and the project for later use.

## Inspect the asset

Review silhouette and unseen sides, thin/merged surfaces, normals, topology, material coverage, scale and the intended level of detail. Verify imported geometry and map dependencies. If animation, articulation or modular fit is required, validate those separately and perform the necessary modelling cleanup. Record model ID, settings, source reference, output IDs and remaining limitations with the deliverable.
