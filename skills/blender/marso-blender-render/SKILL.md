---
name: marso-blender-render
description: "Light, render and composite realistic Blender scenes or optimize render time and memory. Preserve accepted assets, inspect image quality and use compact previews before final output."
license: Apache-2.0
---

# Light, render and optimize a Blender scene

Choose the branch from intent. For flat/unconvincing images or realistic presentation, read [lighting](references/lighting.md) and then [compositing and output](references/compositing.md) as needed. For camera composition/movement use `marso-blender-camera` when installed; do not load motion instructions for a simple still. For speed or memory requests, use the performance branch below without changing accepted art direction.

Use Marso finishing for requested new material appearances through `marso-blender-texture`, and reuse satisfactory library PBR assets. A lighting/render request alone does not authorize retexturing or regenerating the scene. Keep raw materials intact and diagnose form, placement, lighting and material defects separately.

Use the user's established Blender connection. Discover the installed version, renderer, available devices and actual settings before editing. No Marso cloud operation is required for render optimization.

For a showcase, build film or tutorial requiring new assets, route geometry to `marso-blender-asset`/`marso-blender-kit` and requested Marso finishing to `marso-blender-texture` when installed. Presentation scripts must not substitute their own unchecked upload, UV or material-reuse path. Render the accepted version and record which result its images show. Do not overwrite raw normal maps or apply blanket map/gamma corrections to conceal a preparation defect; diagnose it through the texture workflow first.

For ordinary asset creation, use the first useful review frame as the device/performance check; a separate optimization study is unnecessary unless performance or memory is a problem. Plan a compact view set: an oblique view, a complementary view revealing hidden construction, and targeted views only for unresolved regions. Geometry checks can use the viewport or low-cost clay renders. After a local correction, rerender affected views rather than the entire set. Final PBR review still checks relevant backs/interiors and material response; add matched normal-on/off diagnostics when a defect is reported or observed. Do not render a showcase, turntable or duplicate camera set merely to complete the workflow.

1. Establish the requested output: interactive viewport, lightweight review images or final renders. Preserve camera, resolution and quality requirements. Finished-scene workflows default to lightweight reviews; do not begin a final render campaign without a request. When finishing an in-progress reference reconstruction, inspect its coverage review and a cheap matched scene view first; return missing defining groups or visible defects to the owning stage before final sampling. A request to render an existing scene as-is does not authorize filling or redesigning it: render to that scope and disclose relevant limitations.
2. Save a baseline and record current settings. For performance work, inspect unique versus placed geometry, evaluated modifiers, shared mesh/material/image datablocks, texture dimensions, subdivision/displacement, lights and render buffers. For an out-of-memory report, diagnose memory before changing samples.
3. When repetition, speed or memory is relevant, read [instancing and render decisions](references/performance.md). Share repeated geometry; create required style variants once and instance those sets. Preserve Empty entity roots and separate geometry groups. Do not convert everything to unique meshes for convenient selection.
4. For lighting work, compare matched inexpensive previews and record render time. For performance work, benchmark a representative camera/frame at matched resolution and quality, including scene preparation time. Record renderer/device, elapsed time and observed peak memory if measurable. Report missing memory telemetry; do not infer VRAM savings from object counts.
5. Change one relevant group of settings, rerun the same view and inspect silhouette, shadows, reflections, fine textures and noise. Retain useful changes that meet the brief; performance claims require measured tradeoffs. A crop can assess detail but does not prove the complete scene fits in memory.
6. Restore temporary preview overrides, retain the chosen final settings, save dependencies and deliver requested images with measured results. Preserve original high-resolution maps and editable geometry. Do not overwrite source textures to reduce render memory.

When the issue is asset creation, use installed modelling/generation skills; optimization is not permission to regenerate or retexture assets. See the reference for version-dependent choices and official Blender documentation.
