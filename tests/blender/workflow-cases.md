# Blender workflow acceptance cases

These are behavioural checks, not claims that every case has been executed. Record actual versions, input, outcome and evidence in `docs/compatibility.md`. Use disposable working copies. Cloud cases need an intentionally configured test account and requested generation; local smoke checks do not call cloud services.

## Routing and execution

| ID | Request / fixture | Required observable outcome |
| --- | --- | --- |
| A01 | "Model a 900 mm cabinet; no textures yet." | Asset workflow; measured dimensions, editable parts, no generation. |
| A02 | One image without dimensions. | Assumptions identified; plausible scale stated or material ambiguity clarified; hidden construction not presented as recovered fact. |
| A03 | "Model and texture this chair with Marso." | Geometry inspected before texture preparation; actual Marso result inspected; no claim of execution from a script alone. |
| T01 | "Add a texture to", "change the texture of", "restyle" the same mesh. | All route to texture; operation chosen from intent and actual material state. |
| T02 | Fixed cabinet assembly with authored UVs and material slots. | Explicit target/parts inspected; source recoverable; shared atlas consequences understood; objects and hierarchy preserved. |
| T03 | Missing UVs; then existing degenerate UVs; then an 8K image. | Missing UVs can be created; bad existing UVs are not accepted merely because present; oversized images handled on independent copies. |
| T04 | Old reference image/enhance text in panel; user requests a new text-only style. | Explicit reference/enhance choices prevent stale input from contaminating the run. |
| T05 | Build exposes project-selection commands, but no Save to project is selected. | Valid destination selected/created and verified before Retexture; no invented IDs or duplicate creations after timeouts. |
| T06 | Auto PBR queue contains another pending asset. | Agent does not inadvertently submit that asset through `pbr_generate`. |
| T07 | Texture job tool times out while Blender is still working. | Agent follows the existing job in separate calls; no main-thread blocking or duplicate submission. |
| T08 | "Change only the seat material" with a swatch. | `image_material` does not replace every slot indiscriminately; protected frame assignments unchanged. |
| T09 | Partial map/slot failure or quality warning. | Agent inspects individual results and appearance; does not report blanket success. |
| T10 | Geometry/UV edits after a failed PBR stage. | Old completed-edit resume is not assumed valid solely because vertex/face counts match. |
| K01 | Shelving photo with several repeated parts. | Small useful part family, inferred details labelled, actual mating dimensions and connector frames recorded. |
| K02 | Decompose an existing joined model into a reusable kit. | Source retained; logical components identified instead of blindly separating loose islands. |
| K03 | Wall kit: straight, corner, doorway and end pieces. | Masters remain editable; representative connections and two arrangements checked; missing interfaces reported. |
| K04 | Texture a kit while all modules are assembled. | Reusable masters/surfaces considered first; no hidden-face-collapse promise or invented option. |
| K05 | Door interior hidden in closed position. | Interior remains mapped in the reusable/moving workflow; evaluated in an open state. |
| K06 | Restyle a kit with linked repeated parts of different sizes. | Unique masters processed deliberately; sharing and physical texture scale checked; generated style consistency visually reviewed. |
| C01 | Build a repeated wall run from an existing kit. | Frame placement with measured endpoint/fit errors; original masters unchanged. |
| C02 | Close an L-shaped or looped structure. | Every required endpoint checked; one successful snap is not treated as full closure. |
| C03 | Wrong connector type, disallowed twist or missing corner part. | Agent resolves compatibility/variant instead of forcing a geometric snap. |
| C04 | Nonuniform scale, mirrored root or constrained connector. | Helper rejects unsupported frames or fails/rolls back verification; no silent distortion. |
| C05 | Restyle one placed instance of a shared master. | Intended instance isolated; other instances keep their original appearance. |
| X01 | Install each skill folder alone. | Its own references/scripts resolve; missing companions handled explicitly. |
| X02 | Assistant can call tools but cannot view returned images. | Structural and visual evidence distinguished; no fabricated visual inspection. |
| T11 | Mirrored, stacked, partially overlapping or out-of-tile UVs. | UV audit fails; shared boundaries alone pass; no intentional-stacking exception for Retexture. |
| T12 | Sealed fixed internal part versus openable cabinet interior. | Permanently enclosed part can be excluded; future-visible interior retains mapped area. |
| T13 | Installed build lacks project-selection commands documented in a newer checkout. | Discover actual capabilities; use and report the supported legacy destination when appropriate, or resolve a required destination before generation. Never assume capability from the version label alone. |
| T14 | Transfer generated maps from a working copy to a linked master. | Verify coordinates, polygon connectivity and loop order before index-based UV transfer; preserve connectors and intended sharing, pack dependencies, and inspect the assembled result. Equal counts alone do not pass. |
| K07 | Three different-sized kit components each independently filling a 4K atlas. | Density differences measured and resolved before the reference bake; appearance/distortion still inspected. |
| K08 | Prominent modular wall join with independently generated textures. | Boundary intentionally uses a natural break, documented cover or continuous shared-material strategy; cover tested from oblique views without coplanar flicker. |
| T15 | Continuous wood grain or masonry pattern across repeated/rotated modules. | Shared source and mapping phase/direction/repeat checked; reference-image guidance is not claimed as an exact edge lock; unique-atlas baking keeps the common boundary sampling. |
| T16 | Photorealistic timber and plaster kit. | Material-specific detail at multiple scales, directional/end grain and plausible roughness/normal response; close and assembled views checked for incorrect material boundaries, baked lighting and exaggerated wear. |
| T17 | A nominally 4K texture looks soft on a long, thin component. | Inspect actual atlas density, source-bake resolution and close renders; do not equate output dimensions with resolved detail or blindly equalise density. Re-bake an independent target after UV changes and compare the actual result before replacing the original. |

## Model approval before texturing

These cases describe expected assistant behaviour; adding them does not establish a live conversational test pass.

| ID | Request / fixture | Observable acceptance |
| --- | --- | --- |
| Q01 | "Model and texture a cabinet"; newly built geometry has not been shown. | Save and show neutral-clay previews with dimensions and defects, ask for model approval, and wait without submitting Retexture or PBR. Silence does not authorize submission. |
| Q02 | User approves the shown model, or explicitly says to skip model review. | Proceed within the requested texture scope; retain the source revision and approval or waiver without asking again. |
| Q03 | User requests a different silhouette after approving the first model. | Show and obtain approval of the materially revised geometry before cloud texturing. Routine appearance-preserving UV preparation alone does not require another approval. |
| Q04 | "Retexture this existing chair as walnut" with no geometry edits. | Follow the existing-asset texture workflow without adding a model-approval question. |
| Q05 | User approves one kit wall; an unseen doorway is substantially different. | Approval covers the wall only unless the user explicitly waived review of the rest. Show the remaining components together for approval before their texturing. |
| Q06 | New model cannot be previewed through the connection. | Disclose the limitation and provide the saved model for review; wait for approval or an explicit waiver rather than claiming visual acceptance. |

## Routing, reusable looks and style variants

| ID | Request / fixture | Observable acceptance |
| --- | --- | --- |
| R01 | "Generate an ornate organic rock" versus "Model an editable hinged cabinet". | Generative route for the first, agent modelling with separate articulated parts for the second; neither gets substituted silently. |
| R02 | Explicitly "model this organic shape" or "generate this building module". | Explicit intent wins; explain topology/fit tradeoffs and validate the relevant result instead of overriding the request. |
| R03 | "Make a modular wall pack" without a route preference. | Structured modelling with controlled interfaces; no independent generative reconstructions assumed to fit. |
| R04 | Generation with a named model, a 30K constraint, or multiple source views. | Inspect runtime catalogue and route schema; respect compatible preferences, select supported options, and do not mistake model input support for an exposed tool parameter. No invented model-quality rankings. |
| R05 | Add-on already supports the desired generation; hosted Studio is disconnected. | Keep the working add-on route; no unnecessary hosted-MCP prerequisite. |
| R06 | Older Create handler has no model parameter. | Do not silently claim a requested model was applied; disclose the limitation and resolve the route. |
| V01 | "Three finish variants of this stool from the original." | Each submission uses the same source geometry, UVs and base appearance; no A-to-B-to-C Restyle chain. Source stays unchanged and each result is separately named. |
| V02 | Shared material/mesh users across source and copies. | Isolate variant data before generation; applying one output leaves the source and other variants unchanged. Keep intended sharing inside each assembly. |
| V03 | Material rename requested during a job; returned maps have named slots. | Retain submission names through application, then name resulting materials descriptively; correct slot/map bindings survive saving. Preserve cache paths and node names. |
| V04 | One material atlas spans oak and plaster. | Name it as an asset/style atlas, not two independently editable materials; record its material roles in the brief. |
| V05 | Add a doorway to a kit in a later session. | Load the saved appearance brief and reference component, add component-specific direction/roles, compare under matched lighting, and preserve the brief's source/revision. |
| V06 | Original source missing, or user asks to refine a returned look. | Disclose a missing original; do not silently use a returned look as it. An explicitly selected returned version can become the recorded source for refinement. |

These are behavioural acceptance cases, not a claim that a fresh assistant has passed them. The local material test below covers only part of V02/V03.

Run `style_variant_smoke.py` with the same disposable Blender flags as below and `-- --addon-root <checkout>`. It supplies synthetic images to the actual add-on material application code, checks source/variant isolation and post-application names, then saves/reopens a temporary file. It does not test cloud generation, assembly duplication or agent decisions.

## Reference images and project destinations

| ID | Request / fixture | Observable acceptance |
| --- | --- | --- |
| I01 | Several room references with different lighting and detail levels. | Assign image roles and a primary design direction; distinguish observed features from inferred scale and hidden construction. Produce a component schedule instead of one reconstruction of the entire scene. |
| I02 | Reference-driven housing with metal trim, rubber seals, glass and a light strip. | Per-piece brief locates each material, surface detail and wear; geometry defines openings/profile changes. Inspect the source bake's actual regions before submission and the returned boundaries afterwards. |
| I03 | New kit while Save to still names an unrelated Blender project. | Refresh the relevant account's project list, create/select a descriptive task project, read back the selection, save/reopen, and verify actual output membership. Library browsing alone does not pass. |
| I04 | Project creation times out, or another client uses a different account. | Reconcile the job and fresh project list before retrying; preserve the task's authorized route and account. Do not duplicate creation or assume another connector shares its destination. |
| I05 | Installed add-on and reviewed checkout report the same version but different project commands. | Discover loaded capabilities; resolve the required feature gap without pretending checkout review is an installed update. |
| I06 | Narrow bevels, alternate exposed backs, and repeated thresholds. | Audit non-degenerate unique UVs, retain future-visible faces, inspect repeated joins and usable passage/floor alignment at real scale. Correct master/placement rules, not only a presentation copy. |
| I07 | A multi-part kit's representative result has misplaced material regions or a service view warning. | Inspect source and returned front/oblique/rear views before submitting the family; diagnose any correction, preserve the first result and compare under matched conditions. A rich prompt or successful job alone does not pass visual acceptance. |
| I08 | Detailed industrial reference but a sparse box-based mesh. | Compare neutral-clay front and oblique views at the target distance. Model structural recesses, sloping profiles, vents and substantial hardware before texturing. Restyle describes finishes on existing features; reject painted structures that contradict the mesh. |

These are acceptance criteria. Record executed checks separately from untested assistant behaviour.

## Local Blender smoke check

Run the script only in a new background Blender process. It refuses a GUI session and uses factory startup rather than an existing file:

```text
blender --background --factory-startup --offline-mode --python-exit-code 1 --python tests/blender/offline_smoke.py
```

Optionally append `-- --addon-root <path-to-virtuoso-add-on-blender>` to probe the actual local preparation code. This imports only the relevant core modules through a temporary package name; it does not register the add-on, read account preferences, generate textures, or exercise the MCP transport. No .blend is saved.

The smoke check exercises rigid placement, twist, repetition, invalid hierarchy/scale and rollback, plus (when a checkout is supplied) full-face UVs, hidden-face atlas collapse, preserved source UVs and assembly membership. It supplies a known hidden-face set to the atlas function; it does not validate the GPU/CPU visibility detector or generation quality.

## Local experiment evidence

Keep experiment-specific scene builders, generated artifacts and detailed reports in ignored local storage. Promote the reusable lesson into the relevant skill and record only concise verification limits in [compatibility](../../docs/compatibility.md). These cases are maintainer acceptance criteria, not runtime instructions or a record that every case passed.
