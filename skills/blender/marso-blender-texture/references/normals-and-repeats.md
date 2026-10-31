# Normals and repeated geometry

Use this for assemblies with repeated or mirrored parts, PBR-only preparation, or a reported normal-direction defect. Preserve the source. Diagnose on independent evaluated/exported copies; do not change a pending generation target.

## Choose the generation boundary

Repeated colour can look correct on stacked UVs while a direction-dependent map is invalid. Two differently oriented surfaces sharing a texel can need different world-space normals. One RGB value cannot encode both. Correct face normals, smooth shading and a convincing albedo preview do not remove this conflict.

Choose one of these routes before generation:

- **Reusable master:** submit one representative component with valid unique UVs, finish Retexture/PBR, then instance its verified material/mesh. Test the finished tangent-space normal map on rotated copies. A world-space debug map is not a reusable tangent-space normal texture.
- **Whole assembly:** include all required occurrences, give each its own UV region in the generation atlas, and preserve part-to-atlas correspondence through export and application. Independent mesh data is necessary when authoring different layouts on linked parts, but copying data does not unstack existing UVs; repack and rebake the colour guide on the working target.

These are generation-target rules, not a ban on efficient instancing in the final scene. Identical finished assets can share geometry and tangent-space materials. Style variants may share geometry while keeping independent material bindings. A later combined PBR/Retexture submission needs its own validated atlas again.

## Preflight the actual target

1. Inspect the evaluated mesh's face direction and shading/corner normals with normal maps disconnected on a diagnostic copy. Check transforms, especially reflections and nonuniform scale, through the actual export path. Double-sided display can hide an orientation defect; do not use it as evidence of correct normals. Do not blindly recalculate intentional custom normals or flatten an articulation hierarchy.
2. Run the [UV overlap audit](uv-acceptance.md#audit) across all geometry sharing the generated maps, including opposite-facing duplicates. One master passing alone is insufficient. Validate the exported material's actual UV layer after joining, modifier evaluation, automatic preparation and export. Joining meshes does not make their UVs unique.
3. Record file/target identity, UV layer, included parts, overlap result and justified exclusions before either Retexture or PBR-only submission. A prepared flag is not this evidence. Resolve a known conflict locally before cloud execution; do not ask a prompt to fix UVs or repeatedly predict normals from the same conflicting upload.

## Diagnose a returned normal error

Preserve the original returned images. Do not automatically replace low-Z vectors with flat normals, clamp vector components, flip channels or apply fixed roughness/metallic gamma. A percentage of altered texels is not a measured defect rate: unused atlas space and valid grazing directions may be included. Resolve input/map correspondence before considering a bounded, explained repair.

Keep these questions separate:

- **Mesh orientation:** are the underlying faces and shading normals correct without any map? Investigate flipped winding, stale custom normals, degenerate geometry and incorrectly handled transforms.
- **Atlas correspondence:** do multiple included surfaces read the same texels, does the material use the intended UV layer, or did preparation/export change the layout? A single joined mesh can still contain thousands of overlapping surfaces.
- **Map interpretation:** is the returned image tangent-space, object-space or world-space, and which axis/channel convention does it use? Treat normal images as data, not colour. A world-space debug image must not be fed into a tangent-space Normal Map node. Do not flip the green channel or swap axes simply because the preview looks wrong.

For a world-space diagnostic, compare sampled directions with the mesh in the same coordinate frame, allowing for documented axis/encoding conventions. Establish the convention on unaffected surfaces before judging a suspect region. Different RGB colours alone do not prove inverted normals. A shared texel that corresponds to opposing mesh directions establishes an atlas conflict independently of which surface the service selected or blended.

The [glTF specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html) defines `normalTexture` as tangent-space and provides tangent reconstruction guidance when tangents are absent. Missing exported tangents alone is not proof of a defect. Verify the generated map and the application's UV/tangent basis before prescribing a fix.

Separate confirmed input defects from service-side hypotheses. If only the source is available, report what it proves and request the returned map or run evidence needed to trace the rest. Preserve raw results and identifiers. Never claim a local diagnostic reproduced cloud execution.
