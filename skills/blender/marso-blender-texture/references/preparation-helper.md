# Reusable local preparation helpers

Use [prepare_asset.py](../scripts/prepare_asset.py) to submit an asset whose parts already share one authored `MarsoUV` atlas. It joins an independent single-mesh working copy that keeps that atlas, validates it with the add-on's own validator, and can bake a colour guide or export a GLB. Parts without materials are accepted, which is how a model going to New Texture should arrive. The colour-guide bake and GLB export need **flat Principled Base Color regions**; use them only when the user asks for a local colour guide or texture-ready export, never as the route into Retexture. The script does not unwrap, pack, design geometry, discover hidden faces, generate textures or replace visual acceptance.

Run inside Blender through the existing control connection or an isolated background process. The helpers use the installed Marso add-on's local Python validator/exporter; they are **not new MCP commands**. Resolve the actual installed module through the command-discovery recipe in `SKILL.md`, then supply its `__name__` as `addon_module`. Extension module names vary. A missing/incompatible local function is a compatibility failure; do not bypass it or install another cloud connection.

## Short staged recipe

Add this skill's `scripts` directory to Blender's Python path. `marso_module` below is the actual module already discovered in that Blender session; `parts` is the explicit mesh-occurrence list and `root` is the intended asset anchor. Do not recursively include unrelated scene objects.

```python
import prepare_asset as prep

addon = marso_module.__name__
target = prep.working_copy(parts, name="Asset_Texture_v1",
                          frame=root.matrix_world, addon_module=addon)
atlas = prep.validate_atlas(target, addon_module=addon)
print(f"Shared UV tile used: {atlas['occupied_fraction']:.1%}", atlas.get('packing_advice', ''))
prep.uv_outline(target, output_dir / "uv-v1.svg")
# Only when a colour guide or texture-ready export was requested:
prep.bake_guide(target, output_dir / "guide-v1.png", addon_module=addon)
prep.export_glb(target, output_dir / "asset-v1.glb", addon_module=addon)
```

For a requested guide on a model without materials, assign flat Principled colours per region on the working copy only, never the source, then run `bake_guide`.

Use new filenames/target names for new revisions; helpers refuse file overwrites. The example is staged so inspection can change the next action. A validation failure names the source part and face: return that part to the UV stage, then make a new working copy. Save checkpoints with Blender's normal save operation; do not overwrite a pending job's pinned file to save a review copy. A separate GLB is needed for a requested deliverable or route qualification; ordinary native submission already exports its own file. The explicit validation gates atlas inspection; the bake's internal recheck protects its immediate input. Keep those built-in guards, but do not add another equivalent audit or launch a separate process just to repeat their results.

### Inputs and scope

- `working_copy` accepts evaluated mesh occurrences, including modifiers and object-linked material overrides. It preserves source geometry/materials, corner normals and marked seams, and copies the specifically named `MarsoUV` layer exactly. Missing source layers are recorded in `target["preparation_missing_uv"]`; their blank coordinates fail validation, so return those parts to the UV stage. It never adopts an arbitrary primitive UV layer.
- For a reflected transform, native geometry conversion reverses polygon winding and the charts stay mirrored, which the add-on's validator accepts. The flag `reflected_transform` is recorded in provenance; the source is not altered.
- The required `frame` supplies the asset anchor's placement/orientation. Pass the asset root's matrix even when the object stands elsewhere in the scene. The helper separates its rigid anchor from scale, preserving scale in the copied geometry. Do not default an offset asset to world origin. These operations affect the independent upload copy, not the source scene. This adapter requires a metre-scale working scene (`scale_length=1`); other unit conventions are rejected because later native re-export must agree. Convert physical geometry into a separate metre-scale working file when needed; merely changing the unit setting changes its interpreted size.
- Joining occurs **only on the new independent working target**. The editable source parts, instances and hierarchy remain intact. This distinction reconciles assembly guidance against destructive joining with the curated single-mesh route.
- `excluded_faces={source_name: [evaluated_face_ids]}` is optional and explicit. Retain the reason/allowed poses in the run record. No camera-based invisibility inference occurs. Re-evaluate IDs after geometry changes. `part_faces(target, source_name)` resolves the stored source range before further geometric filtering, preventing a passage-wall selector from accidentally selecting the neighbouring spout.
- Parts may have no materials. Any material present must have an active Material Output directly connected to Principled BSDF, with unlinked Base Color and opaque alpha/transmission. Existing image/procedural/complex materials and glass require their own preparation route; these helpers reject them for copy/bake instead of losing their appearance. An existing textured single mesh can use `export_glb` without rebaking only under these conditions: no modifiers, unshared mesh data, and exactly one material slot whose base colour is a connected UV image. It also needs the named UV layer (pass `uv_name`; the default is `MarsoUV`). The call makes that layer active and render on the object, so export from a working copy when the source must stay unchanged.

### Validation and recovery

Native validation failures include the source object and evaluated face ID through working-copy provenance. `face_source(target, working_face)` gives the same mapping for a diagnostic. Face IDs remain meaningful only while that working topology is unchanged; rebuild provenance after geometry edits. Repair charts on the source parts at the UV stage, never on the working copy, so the editable asset and the upload keep one layout.

Visible charts below one pixel in area at the intended minimum resolution cannot carry independent generated detail. Return them to the UV stage or explicitly classify the affected detail as unresolved/common-colour-only. Do not label a full close-view handoff ready merely because overlap and export checks pass. Do not retain a UV data handle across Blender operators yourself; `use_uv` returns a current handle when a direct read is needed.

The native validator checks all included triangles as **one shared generation domain**, including across initial material slots. `bake_guide` repeats this check immediately before the bake. It uses temporary emission materials for lighting-free Base Color, preserves face roles until baking completes, restores scene/bake settings, and installs one packed guide material only after success. A failed bake restores the target's original bindings. Reopen the pre-bake checkpoint to change flat colours or UVs, then use a new guide path. Export rejects geometry/UV changes made after a helper bake. This guard is not a general source-lineage or arbitrary shader-change tracker.

For a preview/load failure, keep the valid bake and repair only the preview. `uv_outline` writes SVG without needing a graphics context and includes only the chosen target. Inspect it through available browser/image tools. For clay previews, create or retain the temporary material explicitly across file reopen; an unused material may be discarded by Blender.

## Conditional export verification

On a changed/unverified route or when investigating a defect, use [verify_export.py](../scripts/verify_export.py) instead of writing another comparator:

```python
from verify_export import verify_glb
report = verify_glb(target, output_dir / "asset-v1.glb", addon_module=addon)
```

It temporarily imports the actual GLB into an isolated scene, checks single-target/material/colour-texture scope, runs native UV validation and compares triangle occurrences, UVs and corner normals in the export frame. It enforces the same metre-scale contract as export. Imported data is removed and the original scene restored. The defaults allow 1 micrometre position error, 0.000001 UV error and 0.1 degree normal error; they accommodate floating-point/normal encoding differences, not visibly changed shading. Tighten tolerances when the asset scale warrants it; inspect the report instead of using bit equality or hiding an actual failure. Different triangle counts, reversed winding, mismatched maps and materially wrong normals fail.

Keep this diagnostic conditional under the validated-handoff policy (validated handoff reference). Record `addon_info(addon)` alongside a successful qualification to identify the loaded exporter. An unchanged qualified route does not require a fresh full round-trip audit for every asset. No helper certifies future service-generated normal maps, optimal UV sampling, user approval or simulation readiness.
