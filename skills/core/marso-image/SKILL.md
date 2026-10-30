---
name: marso-image
description: "Generate or edit images with Marso, including realistic appearance references and style variants for existing 3D assets. Image work only; use generation or texturing for the downstream mesh."
license: Apache-2.0
---

# Create and edit images with Marso

Use the user's working Marso connection and a relevant Studio project. This workflow creates images; it does not automatically generate a mesh or retexture an asset. Preserve an explicitly requested illustrative or stylised look. For realistic work, read [appearance direction and review](references/appearance.md) before writing the prompt.

## Establish the image's job

Distinguish a standalone image, a shape/construction reference, an appearance reference for an existing mesh, and a flat surface swatch. A photograph of an object is not automatically a seamless texture or PBR material.

- Generate when a new image is needed; edit when an existing source supplies useful composition, shape or appearance.
- Give each input a role: shape/proportions, material regions, appearance inspiration or scene context. A clay model or blank label guide supplies structure, not the rendering style to imitate. A cluttered scene crop may explain context but is a poor direct material reference.
- For an existing mesh, check that the source silhouette and material boundaries match it. Resolve an incorrect master before asking the image editor to preserve its shape. For a new concept image without a mesh, do not invent a geometry-preservation constraint.
- Decide the intended viewing size and condition from the brief. Natural realism can be clean and new; it does not require damage or dirt. Do not silently lower the quality target after seeing weak results.

## Write and execute

Lead with the desired visual result. Add concrete material/finish/detail descriptions, then only the source-role and composition constraints needed for this operation. Keep per-variant differences explicit. Avoid copying export settings, UV requirements or the full run checklist into the prompt. Describe realism in the image-edit/generation prompt; polishing a source render alone is not a substitute.

Discover the current tool schemas and prompt constraints. In Studio, verify image-generation or image-edit nodes and source/reference links before execution. An edit source and additional appearance references have different roles; use the connection's actual reference syntax. If the endpoint manages lighting/background and forbids those directions, omit them and carry realism through the material/finish descriptions. Never invent resolution, seed, mask or layout-lock controls. Source canvas size is not a guarantee of output size.

Record the source, exact submitted prompt, project/node and returned execution identifiers. Retain raw responses before parsing. Follow accepted runs; reconcile unknown outcomes rather than resubmitting. For an explicit rejection that started nothing, follow the actual error/backoff. Do not hard-code a concurrency limit from another account or assume the service accepts a new run because a different route does.

## Inspect before downstream use

Open the actual result at its returned resolution. Check both the visual brief and its structural use: plausible material response and detail, coherent form, correct region placement, readable subject, usable per-object resolution, and no unintended appearance inherited from a crude guide. Count/layout preservation alone does not establish realism.

For an edit supplying appearance to an existing mesh, record source and returned pixel dimensions/aspect ratios and compare the object's proportions and region landmarks in views that preserve each image's aspect ratio. A changed canvas can be harmless padding or a changed view, but can also conceal a reshaped object; distinguish these before accepting it. Do not stretch the output to the old rectangle or reuse old crop coordinates to manufacture correspondence. If the shape differs, repair the image step or explicitly limit it to finish/palette inspiration with independent region checks; do not call it a shape-preserving edit or use it to silently remodel the master.

For a contact sheet, choose rows, columns and a standard overall aspect ratio around subject shape and required detail. Frame each subject tightly with safe margins; prefer a consistent black field when it gives suitable contrast. Keep a light background when the subject or brief requires it. Check actual crop detail; use fewer cells or individual images if the sheet cannot carry it. Do not stretch objects or clip their edges to improve occupancy.

If a result misses the brief, identify whether the cause is shape, composition, appearance direction, insufficient detail or a service limitation. Correct the relevant input within the authorized scope; avoid repeated unchanged submissions or endless "more realistic" prompts. Retain useful outputs and report an unresolved limit when the available route cannot meet the brief. Internal quality checks do not require a user approval at every image; honour requested review points.

## Handoff

For image-only work, deliver the image and its project/source record. For appearance work, pass the inspected image or one accepted object crop, its material-region intent, source master identity and concise visual brief to the application's texture workflow. In Blender, use `marso-blender-texture` when installed. The user's request for image-guided variants covers those accepted references; an unrelated image-generation request does not authorize 3D work.

Retexture uses the preserved mesh and a short appearance prompt, then proceeds directly to PBR before final material review. Geometry/UV checks remain outside the model prompt. Do not generate a new mesh from each style image. A successful image is not evidence of successful 3D transfer; establish one representative final PBR result per meaningfully different geometry/material treatment before expanding the method.
