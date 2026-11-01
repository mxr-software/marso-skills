# Explore a scene concept

Generate one useful anchor image through the verified Marso image route. Describe spatial zones, defining objects, plausible light sources and concrete material cues at the intended view. Keep the exact submitted prompt and source/project/result identifiers. Use the image skill's operation-specific prompt guidance and limits.

Only probe a detail or alternate view to answer a named design question, usually one or two views at a time. A crop reveals existing pixels; an image-edit close-up invents detail; a new viewpoint proposes unseen areas. Label those roles. Do not claim image editing provides a calibrated 3D camera or measured dimensions.

Branch probes from the accepted anchor. A deliberately accepted redesign can become a new anchor; do not accumulate accidental drift. Compare openings, furniture identity/counts, supports and material landmarks. Resolve conflicting geometry before generating a room's full asset set. Prefer real photographs/plans for reconstruction evidence.

Once a blockout exists, render its intended view and use it as a layout reference with the accepted appearance concept when the available image tool supports those roles. The returned image remains a design visualization, not proof the 3D scene contains its generated detail.

Discover actual capabilities first. On a supporting Blender add-on, `scene_image_options` describes `generate_scene_image` (use `mode: "scene"`) and `edit_scene_image`. Discover the installed `marso-image` companion for execution details. These mutation commands require the local Blender control route; Agent Connection alone exposes only their read commands. A command existing in a remote catalog does not establish permission to execute it there.

Select the relevant Studio project before submitting and retain a stable `request_id` with the exact request. Follow the returned job; an uncertain submit is held and must be reconciled with the same id, not silently replaced with a new paid request. Preserve the source concept and branch edits from its node. On older builds with only object-mode `generate_image`/`scene_reference`, retain supplied anchors and continue useful local blockout/planning with explicit assumptions. Report the missing capability instead of using private functions or silently switching to a separate hosted MCP. Scene images and their edits cannot directly feed mesh generation.

Keep concept images separate from asset-generation crops and Retexture references. Default Retexture to rich text briefs unless image guidance was requested. Image-only requests stop with inspected images, not an unsolicited 3D build.
