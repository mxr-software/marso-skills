---
name: marso-blender-render
description: "Optimize Blender render time, GPU memory and repeated assets, or render requested images. Diagnose bottlenecks, preserve shared geometry/materials and benchmark quality before changing settings."
license: Apache-2.0
---

# Render and optimize a Blender scene

Use the user's established Blender connection. Discover the installed version, renderer, available devices and actual settings before editing. No Marso cloud operation is required for render optimization.

For a showcase, build film or tutorial requiring new assets, route geometry to `marso-blender-asset`/`marso-blender-kit` and requested Marso finishing to `marso-blender-texture` when installed. Presentation scripts must not substitute their own unchecked upload, UV or material-reuse path. Render the accepted version and record which result its images show. Do not overwrite raw normal maps or apply blanket map/gamma corrections to conceal a preparation defect; diagnose it through the texture workflow first.

For ordinary asset creation, use the first useful review frame as the device/performance check; a separate optimization study is unnecessary unless performance or memory is a problem. Plan a compact view set: an oblique view, a complementary view revealing hidden construction, and targeted views only for unresolved regions. Geometry checks can use the viewport or low-cost clay renders. After a local correction, rerender affected views rather than the entire set. Final PBR review still checks relevant backs/interiors and material response; add matched normal-on/off diagnostics when a defect is reported or observed. Do not render a showcase, turntable or duplicate camera set merely to complete the workflow.

1. Establish the requested output: interactive viewport, lightweight review images or final renders. Preserve camera, resolution and quality requirements. Finished-scene workflows default to lightweight reviews; do not begin a final render campaign without a request.
2. Save a baseline and record current settings. Inspect unique versus placed geometry, evaluated modifiers, shared mesh/material/image datablocks, texture dimensions, subdivision/displacement, lights and render buffers. For an out-of-memory report, diagnose memory before changing samples.
3. Read [instancing and render decisions](references/performance.md). Share repeated geometry; create required style variants once and instance those sets. Preserve Empty entity roots and separate geometry groups. Do not convert everything to unique meshes for convenient selection.
4. Benchmark a representative camera/frame at matched resolution and quality, including scene preparation time. Record renderer/device, elapsed time and observed peak memory if measurable. Report missing memory telemetry; do not infer VRAM savings from object counts.
5. Change one relevant group of settings, rerun the same view and inspect silhouette, shadows, reflections, fine textures and noise. Retain only a measured useful tradeoff that meets the brief. A crop can assess detail but does not prove the complete scene fits in memory.
6. Restore temporary preview overrides, retain the chosen final settings, save dependencies and deliver requested images with measured results. Preserve original high-resolution maps and editable geometry. Do not overwrite source textures to reduce render memory.

When the issue is asset creation, use installed modelling/generation skills; optimization is not permission to regenerate or retexture assets. See the reference for version-dependent choices and official Blender documentation.
