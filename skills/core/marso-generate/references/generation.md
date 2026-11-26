# Generative 3D and model selection

Use this route when the user wants generation, or the brief favours an organic/complex form over controlled construction. Prefer agent modelling for structured parts, clean controllable topology, animation/articulation structure and modular interfaces when that meets the user's intent. Texturing an existing mesh does not require generating its geometry again.

## Select a supported generator

Before generating an object the user's library might already hold, check the library unless the user asked for a new asset; use `marso-library` when installed or the add-on's library search. Respect an exact selected asset or an already delegated reuse decision. Generate when no suitable asset is selected and generation fits the brief.

First establish the source (description, one object image, or consistent views of that same object), required geometric detail and intended use. A fabric swatch is a look reference, not the object to reconstruct. A whole-room image needs an object extraction workflow rather than being treated as one prop: decompose it into a scene graph (`marso-scene-decompose`) and generate each object from its own reference brief (`marso-scene-graph`), when those skills are installed.

Inspect the installed add-on's `generate_state` model catalogue and `create_3d_asset` schema. Refresh after a capability error. Model availability and option names can differ between versions. Use catalogue IDs, not guessed names. The catalogue's source support does not prove that a particular tool accepts that input directly.

Apply the preference order from the skill's preferences and budgets reference: explicit task choice, recorded user preference, compatible panel state, then a supported advertised default. Establish an unknown preference once and retain user choices for later runs. A fallback is not a comparative quality claim. Do not run a model comparison unless requested.

Filter polygon counts, source modes and texture options against the live catalogue and the chosen tool's schema. Do not rely on a saved catalogue or an example model ID as a current default. A higher polygon count does not establish cleaner topology or better articulation. Texture resolution/quality controls appearance sampling, not geometric accuracy. Do not infer "best for furniture" or "best for organics" rankings from version numbers or option lists; those preferences need representative tests or user-provided evidence.

Do not silently replace an unsupported requested setting. Explain the nearest supported choice or missing capability. Keep the final imported count/dimensions distinct from the requested generation parameters. If the mesh will later go through Blender Retexture, inspect its input image limits before selecting higher texture resolutions; the inspected add-on preflight rejects images over 4096 pixels. Preserve the original and prepare a compatible working copy when necessary.

## Blender add-on route

Use the existing authorized Blender connection. Discover Marso's enabled extension module and its command registry if no dedicated tool exposes the operation; inspect `all_commands()` / `describe()` before using `execute(name, params)`. This internal interface is version-bound. Do not assume that a source checkout's commands are installed.

The reviewed implementation exposes `generate_state`, `upload_image`, `generate_image` and `create_3d_asset`. Read state and in-flight jobs first. For an object photo, upload it through the discovered `filepath` parameter; for a description, generate an object reference image. Each of these two commands adds a node to the Studio project, so call one this way only for an image that the next step turns into a mesh. From 1.21.1, `upload_image` with `add_node: false` uploads for an ID alone and adds no node. Inspect the reference before reconstruction without adding a mandatory approval pause. Use the user's requested review points.

Resolve the task's Studio destination before generation. Recent add-ons expose `save_to_state`, asynchronous `list_studio_projects` and `create_studio_project`, and `set_save_project` with a returned `project_id`. Refresh the list, retain/select a relevant project or create a descriptive new one, then read back the selected ID/name and save the .blend. Library browsing is separate. Verify the selection after reopening and check completed outputs in the intended graph. If an older build cannot select the required destination, resolve that capability gap rather than defaulting to an unrelated Blender project. Reconcile uncertain project creation before repeating it.

The current `create_3d_asset` schema accepts `model`, `polygon_count`, `texture` and `wait_for_mint`. `texture` is a Meshy resolution (`2k`, `4k`, `8k`) or Tripo quality (`standard`, `detailed`); omit it for Hunyuan. Older builds may expose fewer or no model controls. Read the chosen values back; do not claim an override was used if that build cannot accept it. Preserve a working add-on route when sufficient.

Follow the returned `job_id` with later `get_job` calls; do not block Blender's main thread or reset busy flags. Reconcile existing work after interruption before creating another asset. The inspected route imports after PBR by default; waiting for mint is a separate option. Inspect the actual artifact's scale/physics state rather than labelling an early import simulation-ready.

## A mesh that will be repeated

When the asset is a master for many instances (a garment on a rail, fruit on a stand), generate it once:

- Use a source image of the subject alone, whole, on a plain background, in the most typical of its planned looks. Frame it tightly in its own proportions: a tall subject padded out to a square comes back too small to reconstruct.
- Choose the lowest polygon option in the live catalogue that still holds its shape; every instance repeats that cost.
- Further colours or prints are Retexture variants of this mesh, not further generations.

## Inspect the asset

Review silhouette and unseen sides, thin/merged surfaces, normals, topology, material coverage, scale and the intended level of detail. Verify imported geometry and map dependencies. If animation, articulation or modular fit is required, validate those separately and perform the necessary modelling cleanup. Record model ID, settings, source reference, output IDs and remaining limitations with the deliverable.
