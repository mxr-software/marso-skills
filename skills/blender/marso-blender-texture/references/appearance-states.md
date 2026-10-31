# Appearance states and transitions

Use when a user wants one asset to become dirty, rusty, wet, worn or scorched over time, or wants a controllable blend between its looks. Ordinary alternative finishes use [variants](variants.md); different silhouettes or broken parts need geometry work.

## Make compatible states

1. Establish the requested states and control: a simple slider, animation, a painted mask or a named external parameter. Infer a simple 0–1 slider when the user asks for a transition without specifying its control. Do not turn a request for separate colourways into an animated shader.
2. Preserve one approved source and prepared baseline. Choose and record the state lineage: **siblings from the original** for alternative finishes, or an explicitly intended **progression S1 → S2 → S3** when changes should accumulate. Do not substitute one for the other. Every edited state gets its own PBR result, including intermediate states. Keep geometry, UV coordinates, triangle correspondence, part transforms and material-role mapping fixed between states; inspect the actual returned bindings before combining them.
3. Describe plausible visual condition in each prompt. Example: “A used galvanised steel bucket, pale worn zinc with fine handling scratches and irregular orange-brown oxidation concentrated below the rolled rim, dark residue in the bottom seam; the wooden handle remains dry and lightly polished.” Keep UV and shader instructions out of the cloud prompt. Protected regions still need inspection; a prompt is not a pixel mask.
4. Inspect each finished state under the same lighting. Retain its source/result IDs and complete map set. Reproject or repair a mismatched layout before blending; do not force unrelated atlases onto the same mesh. Preserve opacity/transparency locally as described in preparation.

For a progression, retain each edited mesh/colour result as well as its PBR output: `S1 → PBR1`, `S1 → S2 → PBR2`, `S2 → S3 → PBR3`. Use the verified tool's explicit source-node/asset selection to feed the preceding edit into the next. In Blender, confirm whether the installed Retexture route uses the currently displayed appearance or reuses a preserved cloud source; do not assume duplicating the visible object changes lineage. If sequential source selection is unavailable, report the capability gap or use an available supported explicit-source route. Do not change private lineage fields. When the add-on already advances Retexture to PBR, retain that chain and do not submit a second PBR run.

Record `state label → parent source → edit result → PBR result`, and keep all endpoints independently recoverable. Recursive edits can accumulate unwanted detail or region drift: inspect transitions and stop at the requested state count, rather than turning progression into an automatic refinement loop.

In the inspected Marso 1.12.1 Blender route, Retexture `source: auto` can branch from a single target's recorded cloud node when its surface is unchanged. A successful edit advances that recorded lineage. Verify the reported source before each cumulative step; copied objects and multipart groups are not proof of the intended parent. `source: upload` exports the current prepared surface instead. Use it only when that surface represents the intended parent and passes the normal preparation checks. Neither choice removes the need to preserve earlier states and their IDs.

## Build the Blender control

Make a new local transition material; preserve both completed endpoint materials and the original source. Do not add transition nodes inside an add-on-managed material while a job is pending.

For two fully authored PBR looks, the robust starting point is **two complete shader branches → Mix Shader → Material Output**. Each branch retains its own base colour, roughness, metallic, IOR and normal wiring. This avoids treating tangent-space normal maps as ordinary colour images. Use the actual UV map in both branches; data maps and masks use Non-Color.

Expose a clearly named **State** factor, clamped to 0–1: 0 is the baseline, 1 is the changed state. A node-group input on each material instance is a convenient control. Keep the control outside shared node-group internals so all users do not change accidentally.

- **Uniform transition:** use State as the Mix Shader factor. Keyframe or drive it only when requested.
- **Masked amount:** use `clamp(State) × clamp(Mask)`, where white admits the changed state and black protects the baseline. This controls intensity within a fixed region; it does not simulate a spreading burn front.
- **Progressive coverage:** use an explicit threshold/ramp against an authored mask or simulation field, with endpoint handling so 0 is fully original and 1 has the intended final coverage. Explain the mask direction and test it. Do not claim the mask itself simulates heat, moisture or damage.
- **External parameter:** a Blender driver may read a named object custom property, but record the actual driver target. Separate materials/controllers when instances must animate independently; a shared material's unqualified slider affects every user.

For many states, agree which transitions are needed instead of nesting every possible pair. A single-BSDF map blend can be more efficient when compatible properties permit it, but must preserve data-map interpretation and handle normal vectors correctly. Do not optimise by silently dropping a state's normal or roughness maps.

See Blender's [Mix Shader](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/mix.html), [Normal Map](https://docs.blender.org/manual/en/latest/render/shader_nodes/displacement/normal_map.html) and [material assignment](https://docs.blender.org/manual/en/latest/render/materials/assignment.html) documentation for the installed version.

## Share geometry deliberately

During generation, keep variant targets isolated as the variants workflow requires. After maps are finished and correspondence passes, display copies can share the unchanged master mesh. Use verified object-linked material slots for distinct appearances; mesh-linked slots are shared by all objects using that mesh.

Keep repeated geometry sharing separate from texture budgeting: multiple PBR states occupy texture memory, shader mixing adds work, and material differences can reduce batching in another application. Use the scene's viewing distance and budget to choose state count and texture resolution. Do not advertise unlimited looks at no memory cost.

## Deliver and verify

- Inspect State 0, 0.5 and 1 from useful views under changed lighting; endpoints should match their saved standalone materials. Check normal response and material boundaries, not just colour.
- For a mask, test black, white and a visible boundary. Explain whether the control means amount or coverage.
- Test two shared-mesh objects: changing one independent controller must leave the other unchanged. Confirm the mesh remains shared and its geometry/UVs unchanged.
- Save and reopen the `.blend`, verifying image dependencies, driver targets, default state and any keyframes. Keep the endpoint material sets recoverable.
- Report the parameter name, range, endpoint labels, mask meaning, source/result IDs and saved files. The generated endpoints live in Marso; the local transition shader and its animation are separate authored work unless explicitly exported and verified.

A Blender driver or arbitrary shader graph is not automatically portable to USD or a game engine. Deliver endpoint maps plus their semantic roles and mask/control convention; recreate a target-native shader or bake the requested static state. Inspect any exported file before claiming it preserves the interaction. Geometry damage, smoke, combustion, sound effects and physics-property changes are separate tasks.
