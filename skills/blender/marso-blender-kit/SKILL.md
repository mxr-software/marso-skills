---
name: marso-blender-kit
description: "Use when building a modular kit of reusable parts in Blender (walls, shelving, pipes, crates), splitting an existing asset into kit parts, or adding finish variants to a kit."
license: Apache-2.0
---

# Build a modular kit

## Overview

This skill produces a family of reusable components that fit together, plus the record needed to assemble and texture them. It starts from a brief, images or an existing asset, and builds the smallest family that covers the requested arrangements. It preserves the source asset, the masters and every earlier version.

It never claims manufacturing fit or structural safety from Blender alignment, and it never starts a cloud job itself. Adjacent work belongs to siblings, each "when installed":

- **Modelling each master:** `marso-blender-asset`. Without it, model with the Blender MCP tools and report that its gates were not run.
- **References and shape comparison:** `marso-blender-reference`. Without it, record that no reference was compared.
- **UVs and the atlas check:** `marso-blender-uv`. Without it, keep the original UVs and hand the UV requirements on.
- **Texturing and finish variants' materials:** `marso-blender-texture`. Without it, do not guess generation commands; deliver the texture requirements as a handoff.
- **Assembling an existing kit:** `marso-blender-compose`. Without it, deliver the masters and the contract.
- **Missing setup:** `marso-blender-setup`. Without it, report what is missing.

General modelling needs Blender control.

**Model approval.** Before texturing newly modelled components, show neutral-clay previews, dimensions, fit checks and visible defects, then wait for model approval. Honour an explicit instruction to skip review. With nobody to answer, use the approval or waiver the task states; otherwise stop before texturing and report. A request for a textured kit is not a waiver. Ask again after a material change to geometry.

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| Kit from a brief | [Decompose around reuse](#decompose-around-reuse), then the sections in order | [connections and handoff](references/kit-contract.md) |
| Kit from reference images | [Decompose around reuse](#decompose-around-reuse) | [reference-driven kit creation](references/reference-images.md) |
| Split an existing asset into parts | [Decompose around reuse](#decompose-around-reuse) on duplicates | [connections and handoff](references/kit-contract.md) |
| Decomposition only | Deliver the component schedule and evidence | nothing |
| Part families, shared sections, triangle budgets | [Build masters and test reuse](#build-masters-and-test-reuse) | [part families and finish variants](references/families-and-variants.md) |
| The same parts in several colours or finishes | [Add finish variants](#add-finish-variants) | [part families and finish variants](references/families-and-variants.md) |
| Texture the kit | [Prepare for Marso](#prepare-for-marso), then `marso-blender-texture` when installed | nothing |
| Assemble an existing kit | `marso-blender-compose` when installed | nothing |

## Decompose around reuse

1. Inspect the working Blender connection, source objects, dimensions and available references.
2. For supplied reference images, read [reference-driven kit creation](references/reference-images.md) before defining the parts. Establish each image's role, separate observed construction from inferred dimensions, and prepare a component schedule with per-piece appearance instructions.
3. Identify repeated parts, variable dimensions, interfaces, corners, endings and openings. Separate a repeatable component from decoration that can stay attached to it. A shelf system might need uprights, shelf boards and connectors; a wall kit might need straight sections, corners, door openings and end caps. Derive the set from the brief, not from this list.
4. For an image, separate visible evidence from inferred back faces, dimensions and joints. Use a known dimension to set scale, or state an assumption. One photograph does not give exact concealed geometry.
5. For an existing asset, inspect topology and hierarchy. Keep the source, then extract or rebuild components on duplicates. Loose mesh islands are not necessarily reusable parts.
6. For a decomposition-only request, deliver the component proposal and evidence without rebuilding the source unnecessarily.

Done when a component schedule lists each part's ID, purpose, dimensions, interfaces and evidence (observed or inferred).

## Establish the kit contract

Read [connections and handoff](references/kit-contract.md) before creating masters.

1. Record units, dimensions, grid or pitch where useful, origin conventions, connection frames, allowed joins, tolerances and material roles. Use declared defaults where the brief leaves them open.
2. Ask only when an unknown changes compatibility or the intended design. With nobody to answer, take the default and record it.
3. Resolve one poly path (low, medium or high) for the whole kit, so pieces that meet share edge treatment and density. Use the path rule in `marso-blender-asset` when installed; without it, take the path the brief names, else medium, and record it.
4. Use shared dimensions for mating interfaces. Separate mating dimensions from overall bounds: two pieces of the same bounding-box width do not necessarily connect.
5. Build and check one representative connection before making the family.
6. Design the visible join before splitting components. Each interface does one of three things: it hides the texture break behind a post, trim, rebate or shadow gap; it expresses a deliberate material joint; or it needs continuous pattern alignment. Record the choice and any shared mapping frame in the contract. Place cuts at construction joints, never through a prominent continuous surface.

Done when the `Marso Kit` text records the contract and one representative connection has been built and measured within tolerance.

## Build masters and test reuse

1. Resolve one representative master's form before multiplying it. Compare its silhouette, depth, proportions, joins and curved transitions with the reference in neutral views. Record the source revision, inspected views and the repair or proceed decision before final UV preparation or family replication. A fitting connector or a valid UV layout does not establish model quality. If the form fails, reshape or rebuild the region before adding fittings; an unresolved master stays partial.
2. Build each family from shared construction, and give each part its triangle budget, as [part families and finish variants](references/families-and-variants.md) describes.
3. Keep masters in a dedicated collection with stable component IDs. Use a separate root for each multipart component, with no asset parent over the whole kit.
4. Create named connector empties under each component root. Keep geometry editable and pivots meaningful. Bake scale into newly built master geometry before placing connection frames. Leave the transforms of existing rigs and linked data alone unless the task covers them.
5. Instances share geometry and materials when they should look identical. Keep variants distinct when dimensions, handedness or appearance differ. A negative scale is an unchecked shortcut for a directional or asymmetric component: check the mirrored result, or build the handed component as its own variant.
6. Assemble representative tests from the actual masters through the connection frames: a repeated run, each declared corner and end interface, and a second arrangement that exposes different surfaces. Measure gaps and orientation against the tolerances, inspect collisions and confirm consistent dimensions. Repair the master, never only the demonstration copy.
7. Check every part twice: alone, as it would ship, and inside its parent assembly.
8. Show the model for approval as the Overview states. Batch previews can cover a family; approval of one representative part does not cover unseen, substantially different parts. Save the editable source and record the approved revision and the components it covers.

Done when each master passes its own checks and the assembly tests, the measured errors are recorded, and the approved revision is saved.

## Add finish variants

A finish variant changes appearance only. One accepted shape serves every finish: a shape is never remodelled for a finish.

1. Finish the shape's master first: model approval, then a passing UV report.
2. Create the variants through `marso-blender-texture` when installed; it owns how each copy's mesh data, UVs and materials are kept apart. Without it, make each variant a full copy of the finished master with its own mesh data and material, and hand the texture requirements on.
3. Name the shape and the finish separately (`crate_600_oak`, `crate_600_painted`), and record each variant with its master and revision in the contract.
4. Compare every variant with its master in the script: same vertex count, zero position difference, identical UV coordinates.
5. Keep one original source revision for all looks. A generated variant never replaces that source.
6. A variant that changes a dimension, a section or a part count is a new shape: give it its own master, checks and approval.

Read [part families and finish variants](references/families-and-variants.md) for the variant record.

Done when every finish variant reports the same vertex count, positions and UV layout as its master, and the contract lists them.

## Prepare for Marso

1. Give components persistent material-role descriptions, and record grain direction where the appearance needs it.
2. Identify faces exposed in any allowed arrangement, including connection ends and moving interiors. Keep full usable UVs on them. Keep permanently hidden surfaces in the atlas too, and record them for the texturing stage once every intended state has been checked.
3. Keep original UVs and material intent until the texture strategy is chosen.
4. Validate packed texel density against viewing distance across different-sized components before baking. Equal map resolution or similar fill is not enough. Keep physical pattern scale without reducing close-view parts to the largest component's density.
5. When the kit has an appearance brief, keep its identity, revision and approved references in the contract, and hand it on with the new components' material roles and pattern directions.
6. When cloud generation is part of the task, resolve and record the Studio project before submission: an intended existing project, or a new descriptive one. An unrelated or generic Blender destination must not collect the kit's outputs. Verify the saved file keeps the choice. Geometry-only kits need no Studio project.
7. Hand every approved component or geometry family to `marso-blender-texture` in one group when installed, including components made by a custom builder or for a film. It sends one part first, then textures the rest stage by stage. Texture unique masters. An atlas made from a fully assembled kit with hidden faces collapsed does not give reusable parts.
8. For a textured reference-driven kit, take one approved representative component through source-bake and generated-appearance review before the rest. Check its material boundaries and finish. A failed pilot changes the preparation or the brief before any batch runs. These quality checks stay the agent's job after the user approves the geometry.
9. After assembly or export, verify the complete texture target. A shared atlas, a joined mesh or a successful pack does not prove that repeated surfaces have unique UVs.

Done when each component has material roles and UVs on every exposable face, checked by `marso-blender-uv` or handed on as requirements without it. The texture handoff names the project, brief and source revision, or states that texturing was not requested.

## Deliver

Save the editable kit and its contract in the requested location, or a stated new one. Keep demonstration assemblies separate from masters. Report:

- component and root names, connector definitions, dimensions and compatibility;
- finish variants and the mesh each one shares;
- material roles, inferred details and test outcomes with measured errors;
- untested combinations and unsupported texture paths, named precisely.

A manifest or an attractive preview is not proof of a working kit.

Done when the final message itself lists the masters, connectors, tested arrangements with measured errors, variants, and what was not tested.

## Worked example: a stacking crate kit in two finishes

1. The brief asks for stackable storage crates in two sizes, each in raw and painted timber, medium path. The schedule lists `crate_600`, `crate_300` and `lid_600`, with a stacking interface (rim into foot recess) and a lid interface.
2. The contract records metres, a 300 mm module, +Z connector normals, 0.1 mm and 0.1 degree tolerances, and a concealed join: the foot recess hides the texture break.
3. `crate_600` is built first with `marso-blender-asset` and compared with the reference. Its rim connector and foot connector are measured in a two-crate stack: gap 0.0 mm.
4. `crate_300` reuses the rim and foot sections of `crate_600`, so two small crates sit on one large crate. The run, the stack and the mixed arrangement are assembled from the masters and measured.
5. Each part is checked alone and in the stack. The lid fails alone: its underside lip was left open because the stack hid it. The lip is closed on the master.
6. The task states that the model is approved unseen, so the approval is recorded with the revision.
7. After the UV report passes, the painted finish is added as `crate_600_painted`, a full copy of `crate_600`. The script reports the same vertex count, zero position difference and identical UVs.
8. The handoff lists three masters, five connectors, three tested arrangements, two finishes per shape, and the untested case: lids under a stacked crate.

## Common mistakes

- Making the whole family before one connection is tested: build and measure one representative connection first.
- Matching bounding boxes and assuming fit: share the mating dimensions and measure the evaluated surfaces.
- Rebuilding a shape for each finish: copy the finished master for every finish and verify the copy matches.
- Checking parts only inside the assembly: check each part alone as well, since the assembly hides open or missing faces.
- Repairing the demonstration copy: repair the master and reassemble.
- Cutting through a continuous surface and hoping separate textures line up: place the cut at a construction joint or behind a cover.
- Mirroring with a negative scale and not checking it: check the mirrored result or build the handed variant.
- Treating a request for a textured kit as model approval: wait for approval or a stated waiver.
