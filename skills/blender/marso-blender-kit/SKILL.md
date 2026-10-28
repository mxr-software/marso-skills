---
name: marso-blender-kit
description: "Design modular Blender kits from briefs, images or existing assets. Build reusable parts with matching dimensions, joins and Marso-ready UVs. Use compose to assemble an existing kit."
license: Apache-2.0
---

# Build a modular kit

Produce reusable components that actually fit together, plus the information needed to assemble and texture them. Support starting from a brief, an image or an existing asset. Build the smallest component family that covers the requested arrangements.

Inspect the working Blender connection, source objects, dimensions and available references first. General modelling needs Blender control; the Marso hosted connection alone does not supply arbitrary modelling. Use `marso-blender-setup` for missing setup and `marso-blender-asset` for modelling when available. These are optional companion skills, not hidden runtime dependencies.

## Decompose around reuse

For supplied reference images, read [reference-driven kit creation](references/reference-images.md) before defining the parts. Establish each image's role, distinguish observed construction from inferred dimensions, and prepare a component schedule plus explicit per-piece appearance instructions.

Identify repeated parts, variable dimensions, interfaces, corners, endings and openings. Distinguish a repeatable component from decoration that can remain attached to it. A shelf system might need uprights, shelf boards and connectors; a wall kit might need straight sections, corners, door openings and end caps. Derive the actual set from the brief rather than always creating this list.

For an image, separate visible evidence from inferred back faces, dimensions and joints. Use a known dimension to establish scale, or state an assumption. Do not claim to recover exact concealed geometry from one photograph.

For an existing asset, inspect topology and hierarchy. Preserve the source, then use duplicates to extract or rebuild components. Loose mesh islands do not necessarily correspond to reusable parts. For a decomposition-only request, deliver the component proposal and evidence without unnecessarily rebuilding the source.

## Establish the kit contract

Read [connections and handoff](references/kit-contract.md) before creating masters. Record units, dimensions, grid/pitch where useful, origin conventions, connection frames, allowed joins, tolerances and material roles. Use sensible declared defaults when the brief leaves them open. Ask only when an unknown changes compatibility or the intended design.

Build and check one representative connection before making the whole family. Use shared dimensions for mating interfaces. Separate mating dimensions from overall bounds: two pieces of the same bounding-box width do not necessarily connect correctly.

For a textured reference-driven kit, take one representative component through geometry, source-bake and generated-appearance review before scaling up the family. Check its structural detail in neutral clay, then its material boundaries and finish after Restyle. A failed pilot changes the preparation or brief; it should not become an unattended batch of the same mistake. This review is part of the agent's work, not a mandatory user approval step.

Design the visible join before splitting components. Choose whether each interface hides the texture break behind a post, trim, rebate or shadow gap, deliberately expresses a material joint, or requires continuous pattern alignment. Record the chosen strategy and any shared texture/mapping frame in the kit contract. Do not place an arbitrary cut through a prominent continuous surface and expect independent Retexture jobs to disguise it.

## Build masters and test reuse

Keep masters in a dedicated collection with stable component IDs. Use separate roots for multipart components; avoid an asset parent over the entire kit. Create named connector empties under each component root. Keep geometry editable and pivots meaningful. Bake scale into newly built master geometry before establishing connection frames; do not apply transforms blindly to existing rigs or linked data.

Instances may share geometry and materials when they should look identical. Keep variants distinct when dimensions, handedness or appearance differ. Avoid negative-scale mirroring as an unchecked shortcut for directional or asymmetric components.

Assemble representative tests using the connection frames: a repeated run, each declared corner/end interface, and a second arrangement exposing different surfaces. Reuse the actual masters; do not repair only a demonstration copy. Measure gaps and orientation against the chosen tolerances, inspect collisions and verify consistent dimensions. Do not claim manufacturing fit or structural safety from visual Blender alignment.

## Prepare for Marso

Give components persistent material-role descriptions and grain directions. Identify faces exposed in any allowed arrangement, including connection ends and moving interiors. Keep original UVs and material intent until the texture strategy is chosen.

When a kit already has an appearance brief, retain its identity, revision and approved references in the contract. Hand it to the texture workflow with the new components' material roles and grain directions. When making style variants, retain one original source revision for all looks; never replace that source with a generated variant.

When cloud generation is part of the task, resolve and record the relevant Studio project before submission. Use a specifically intended existing project or create/select a descriptive new one; do not let an unrelated or generic Blender destination collect the kit's outputs. Verify the saved .blend retains that choice. Geometry-only kit creation does not require a Studio project.

Validate packed texel density and intended viewing distance across different-sized components before baking; equal map resolution or similar fill is insufficient. Maintain physical pattern scale without needlessly reducing close-view parts' detail to the largest component's density. Preserve full usable UVs on future-visible faces, and exclude only permanently hidden surfaces whose intended states have been checked.

If texturing is requested, use `marso-blender-texture` when available. Its kit reference handles shared styles, UVs and Marso commands. Without that skill, do not guess generation commands: preserve the texture requirements as a handoff. Never atlas a fully assembled kit with hidden-face collapse and then declare the extracted parts reusable. Texture unique masters, preserving surfaces needed in other arrangements.

## Deliver

Save the editable kit and its contract in the requested location, or a stated new location. Include component/root names, connector definitions, dimensions, compatibility, material roles, inferred details and test outcomes. Keep demonstration assemblies separate from masters. Identify untested combinations and unsupported texture paths precisely; a manifest or attractive preview alone is not proof of a working kit.
