---
name: marso-blender-render
description: "Optimize Blender render time, GPU memory and repeated assets, or render requested images. Diagnose bottlenecks, preserve shared geometry/materials and benchmark quality before changing settings."
license: Apache-2.0
---

# Render and optimize a Blender scene

Use the user's established Blender connection. Discover the installed version, renderer, available devices and actual settings before editing. No Marso cloud operation is required for render optimization.

1. Establish the requested output: interactive viewport, lightweight review images or final renders. Preserve camera, resolution and quality requirements. Finished-scene workflows default to lightweight reviews; do not begin a final render campaign without a request.
2. Save a baseline and record current settings. Inspect unique versus placed geometry, evaluated modifiers, shared mesh/material/image datablocks, texture dimensions, subdivision/displacement, lights and render buffers. For an out-of-memory report, diagnose memory before changing samples.
3. Read [instancing and render decisions](references/performance.md). Share repeated geometry; create required style variants once and instance those sets. Preserve Empty entity roots and separate geometry groups. Do not convert everything to unique meshes for convenient selection.
4. Benchmark a representative camera/frame at matched resolution and quality, including scene preparation time. Record renderer/device, elapsed time and observed peak memory if measurable. Report missing memory telemetry; do not infer VRAM savings from object counts.
5. Change one relevant group of settings, rerun the same view and inspect silhouette, shadows, reflections, fine textures and noise. Retain only a measured useful tradeoff that meets the brief. A crop can assess detail but does not prove the complete scene fits in memory.
6. Restore temporary preview overrides, retain the chosen final settings, save dependencies and deliver requested images with measured results. Preserve original high-resolution maps and editable geometry. Do not overwrite source textures to reduce render memory.

When the issue is asset creation, use installed modelling/generation skills; optimization is not permission to regenerate or retexture assets. See the reference for version-dependent choices and official Blender documentation.
