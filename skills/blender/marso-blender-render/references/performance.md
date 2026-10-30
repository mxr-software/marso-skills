# Instancing and rendering decisions

## Reuse geometry and appearances

Use linked mesh datablocks for repeated editable objects, collection instances for multipart assets, or Geometry Nodes instances where appropriate. Each placement needs an independent transform. Inspect evaluated geometry: different modifiers, material assignments or realization may prevent intended sharing. An object count or matching name proves nothing about rendered memory.

Keep shared meshes when only transforms differ. Isolate material bindings before making a style variant; object-linked material slots can separate appearances without copying mesh geometry when supported. For multipart assets, a collection per style can preserve internal assignments. Do not alter the original or all copies through shared material/image data.

For 100 chairs in four styles, verify four appearance sets from the original source, then instance the appropriate set. Do not make 100 separate Restyle jobs or copies of identical image files. Recheck sharing after import, preparation, application and save/reopen. If a tool requires realized geometry, realize a working copy of the smallest required scope and return to reusable masters afterwards.

Blender documents geometry sharing and the cost of realizing instances in its [instances guide](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/instances.html). Actual GPU savings depend on the evaluated scene and renderer; measure them.

Repeated packaging can share a geometry master while retaining distinct label/finish sets; use the texture skill's appearance-family workflow when creating those looks. Reuse each accepted style for its placements. Identical chairs do not need appearance variation merely because they repeat.

## Choose the change from the bottleneck

| Observed bottleneck | Candidate change and quality check |
| --- | --- |
| Geometry evaluation/build or geometry memory | Preserve instances, reduce needless subdivision on working copies, remove unintended duplicates. Check silhouettes, shading and animation/export requirements. |
| Texture memory | Reuse identical image datablocks and style sets; try available render-time texture limits/cache settings. Check hero close-ups and small markings. Keep original maps. |
| Noisy sampling | In Cycles, test adaptive sampling/noise threshold and denoising with a sample cap. Inspect fine scratches, texture detail, glass and glossy highlights. Samples do not fix a geometry/texture allocation failure. |
| Repeated setup for similar frames | Test Persistent Data if available and memory allows. It can accelerate repeats at the cost of retained memory; it is not an out-of-memory remedy. |
| High-resolution buffers | Test resolution, passes and available tiling settings against output needs. A low-resolution preview does not verify final-resolution peak memory. |
| Renderer/device mismatch | Verify the scene uses the selected GPU/backend. Compare supported choices with the same scene; do not assume the fastest backend or pool multiple GPUs' VRAM. |

Use the installed version's RNA/tool schema rather than guessing property names. Cycles options do not apply unchanged to EEVEE. Avoid blanket bounce cuts, disabling reflections, camera culling or aggressive texture caps: they can remove visible information, including off-camera shadow/reflection contributors.

The Blender manual describes [render-time texture/subdivision limits](https://docs.blender.org/manual/en/5.2/render/cycles/render_settings/simplify.html), [adaptive sampling and denoising](https://docs.blender.org/UATEST/manual/en/4.5/render/cycles/render_settings/sampling.html), [performance and Persistent Data](https://docs.blender.org/manual/en/latest/render/cycles/render_settings/performance.html), and [GPU memory/backend limits](https://docs.blender.org/manual/en/latest/render/cycles/gpu_rendering.html). Features vary by version and device.

## Evidence to return

Record the same camera/frame and output size for before/after comparisons, scene preparation plus rendering time, observed memory source (process RAM is not VRAM), visual checks and retained settings. Distinguish structural sharing checks from render benchmarks. Do not publish a universal speedup, memory guarantee or fixed polygon/texture budget from one scene.
