# Validated handoff to Marso

Use this reference to qualify an export route, investigate a reported defect, or resolve uncertain evidence. The ordinary workflow is in the texture skill; this is not an extra audit to repeat after it. Keep evidence tied to the target revision and loaded implementation.

## Before submission

### Ordinary preparation versus investigation

On a qualified route, preserve the source, choose exposed surfaces, retain valid charts and check the sampled UV domain per material and image. For New on bare meshes verify the blank binding; for Edit verify the existing textured appearance. Pack or bake only when the selected handoff needs it. Submit once.

A separate GLB is useful when requested as an output. Full export/reimport comparison is warranted by an unverified or changed exporter, unsupported geometry/material/transform arrangement, reported defect, or explicit regression test; not simply because the asset is new or a GLB was requested.

Verify the loaded implementation: evaluated-normal preservation is export revision 4. An add-on release label or source checkout does not establish what Blender loaded. Reuse qualification evidence only for that implementation and its tested scope. When needed, use the packaged checker (preparation helper reference), not a bespoke rounded-coordinate/normal comparison.

Keep these invariants even on the short route:

- Correct root/parts and anchor; unrelated scene selections or supported assets excluded. Isolate export if the installed route cannot guarantee scope.
- Full evaluated generation domain has valid actual material-bound UVs, including repeated occurrences. Shared maps require a shared check; separate domains require their own checks. No suppression of native errors.
- Current geometry/UV revision owns the colour guide and bindings. Reused names do not establish identity; stale normal/roughness links must not survive a rebuild.
- Accepted source corner normals, dimensions and editable hierarchy preserved. Temporary off-camera occlusion is not permanent hidden-face evidence.
- Visual form, useful sampling and required model approval are separate from numerical validity. Never claim pending checks passed.

Use stage recovery (preparation reference): a UV edit invalidates the bake; preview failure does not. Diagnose the changed part and rerun its dependent stages, retaining unrelated accepted work. Do not spend the remaining effort exporting a known-defective asset merely to complete a checklist.

## After completion

After New Texture, PBR runs on a fresh node conditioned on a lit image of the new paint (conditioned PBR); after Edit Texture, the combined `retexture` may continue directly into PBR. Correlate result identity, source revision and actual material bindings. Inspect the applied maps and retain originals. A technical success or an old preview does not establish current visual acceptance.

Accept the material exactly as the add-on applied it. Make the acceptance render with the returned maps and the add-on's node setup, under neutral lighting you would use for any asset. Do not mix constant colour, metallic or roughness over the maps, add procedural bumps, remap channels or add a light aimed at hiding a weak finish. If a region or finish is wrong, report it and correct the stage that produced it (geometry, UVs, Retexture prompt or reference, or condition image).

### Economical review

Use the cheapest view that resolves the question. Reuse accepted geometry captures; inspect UV outlines directly and use a checker/guide viewport instead of rendering each intermediate atlas. One useful final material preview is the starting point, not a fixed gallery. Inspect additional angles interactively; save a targeted view when it reveals unresolved detail. In headless work, small low-sample previews are sufficient until the intended viewing scale requires more resolution.

Normal-on/off pairs, dense map sampling, extra relighting and repeated export comparisons belong to diagnosis. For a reported shading defect, directly light the affected surface and compare matched views differing only in normal strength. If disabling the normal removes the defect, record the failure; disabling it is not a repair. Follow normal diagnosis (normals and repeats reference), preserving raw maps and restoring diagnostic shaders. Do not automatically flatten vectors, flip channels or apply fixed metallic/roughness gamma corrections.

Requested final stills/films retain their quality and scope; create them after acceptance. Save image dependencies and provide one concise handoff with unresolved limits. Retexture/PBR completion alone does not establish simulation readiness.

If timing is requested, include authoring and failed/repeated attempts; distinguish measured execution, cloud waiting and uninstrumented gaps. A fast replay is not fresh-agent build time. Use existing logs before adding instrumentation. Parallel asset times are not additive, and regression-test duration is not a normal production estimate.
