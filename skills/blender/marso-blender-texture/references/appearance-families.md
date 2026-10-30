# One shape, many appearances

Use for shelves of differently labelled cans, cartons, jars or other assets whose geometry repeats but whose appearance should vary. This is an extension of [source-based variants](variants.md), not a route for different weapon/shield silhouettes. The reusable master/independent-style pattern is established; the edited-grid technique below requires a representative live pilot before bulk use. No grid-preservation or label-fidelity guarantee is established.

## 1. Classify what actually repeats

| What differs | Plan |
| --- | --- |
| Neither geometry nor appearance | Ordinary shared instances; no per-placement Retexture. |
| Only labels, colours, print, finish or surface wear | One geometry/UV master, independent appearance variants, then instances of each style. |
| Proportions, silhouette, openings, handles or construction | Separate geometry families or distinct assets; model/generate each required master. |
| Pose or articulated state | Preserve the rig/parts and use the appropriate modelling/animation workflow; a new texture cannot change pose. |

Do not infer identical geometry from a category or bounding box alone. A small can and tall can, sealed carton and open box, or flat shield and domed shield may need separate masters. Size-only differences can share geometry when proportion, UV density and label placement remain suitable; resolve dimensions before preparation. Different shield graphics on one identical shield can use this appearance route; an assortment of different shield shapes cannot.

Inspect a clear reference for each proposed family and any member that appears to differ in construction or proportions. Record the features that justify reuse: profile, shoulder/base transitions, openings, caps or handles as relevant. A label keyword such as "slim" is a candidate grouping, not evidence that scaling one generic master produces the right shape. Resolve missing form information with complementary references rather than repeating an unverified approximation.

Keep physical placements, geometry families and unique appearances as separate counts. A shelf of 60 cans with six labels might need one master and six looks, not 60 mesh generations or 60 Retextures. A generic scene `variants` cluster does not prove shape compatibility. Preserve scene asset ids/member mappings; record the master and style mapping in a local family ledger. Do not collapse distinct appearances into one identical-instance asset.

With multiple geometry families, create only the family/style combinations actually needed. Six designs across two can sizes could require six to twelve texture targets depending on placement; do not automatically expand every design onto every shape. Shared label artwork may transfer, but each different master still needs verified placement and material application.

For a mixed scene, make each master once through the chosen modelling/generation route. Preserve explicit intent and generation preferences. Once a master exists, route its appearance rows through existing instance/Retexture handoffs using real source identifiers; do not send every appearance row into mesh generation. A family ledger is planning data, not a new Marso command or an automatically consumed asset-plan field.

## 2. Prepare a useful master

Model simple controlled shapes when appropriate, or generate once if requested/advantageous. "Primitive" means economical geometry with the correct full silhouette, not missing rolled rims, lid profiles, panel thickness or important seams. Use actual geometry for visible form. Create deliberately blank, distinguishable material regions: a white rectangle for a box label, a white wraparound can band, and separate exposed metal/cardboard/tape regions. Keep these regions free of existing branding and specify their intended placement. Name their roles in the local ledger, so prompts can say "replace the white label rectangle with ...; keep the cardboard and tape unchanged." Use physical region boundaries and clear contrasting materials where useful, not arbitrary painted guides that could leak into the final design. These colours guide semantic editing; they are not guaranteed masks. Record what must remain unchanged.

Author clean UV islands and adequate packing for all surfaces that may be visible in the scene. Avoid mirrored/overlapping islands within the master; sharing the same UV layout across style copies is intentional. Keep label regions continuous where possible and inspect seams, front/back and top/bottom. Do not remove the back just because the initial still does not show it. Preserve the original geometry, UVs and baseline appearance, then prepare a working master without silently replacing authored UVs.

Show newly modelled geometry for approval before Marso texturing unless already approved/waived. Take a fast, clean still that makes the required silhouette and label region legible. A cheap render can be high-resolution; a blurry thumbnail does not become a good guide by enlarging it. Use a camera/view that exposes relevant surfaces. Do not bake row numbers or helper annotations into the object. In the inspected add-on, `capture_reference` with `SELECTED_MESH` uploads a mesh; use a verified camera/viewport image capture or saved render for an image.

The still is a shape/region guide. Spend effort on correct proportions and readable framing, not polishing its shaders into an advertising render. Desired realism belongs in the image-edit prompt and its output review. Transparent parts need the [local transparency handoff](preparation.md#transparent-parts), not a promise that image editing or Retexture will create transparency.

## 3. Choose how to author appearances

- **Per-style briefs:** use directly when colours/materials/wear are sufficient. No reference image is needed.
- **Individual edited images:** use when each look needs high detail, strong layout control or several inspectable views.
- **Edited contact sheet:** useful for a coordinated variety set; repeat the exact same master still in known cells, then vary appearances in one image edit. Keep one geometry family per sheet by default. This is an option, not a mandatory grid/count limit.
- **Exact artwork:** specified readable labels, logos or barcodes need approved graphics and controlled UV/decal/material placement. Generative references and Retexture do not guarantee exact text or identity. Apply exact artwork separately when required and inspect it at delivery size; do not promise that a preserve instruction locks those pixels.

A contact sheet is an appearance reference, not a UV atlas and not a scene to convert into multiple meshes. The user's request for this reference-guided route authorizes these references; ordinary Retexture elsewhere remains brief-only unless a reference is requested.

Use `marso-image` when installed for image generation/editing and realism review. When using this texture skill alone, follow [appearance prompts and handoff](prompts.md) with the verified image tools. Do not turn a request for style images into mesh generation.

## 4. Size and construct the sheet

Choose columns, rows and a standard overall aspect ratio from the subject's shape, quantity and required detail; do not default to square. For six tall objects, three columns by two rows on a 2:3 portrait canvas can use space better than two columns by three rows on a square. Broad objects may need a landscape layout. State columns and rows explicitly. Each cell receives approximately canvas width/columns by canvas height/rows before gutters; the subject occupies less. These are arithmetic limits, not quality thresholds.

Frame the source tightly with safe space around its silhouette and use small gutters. Prefer a consistent black source/grid background where contrast permits; preserve another background required by the subject or brief. The helper fills gutters and transparency, not opaque white backgrounds already in the source. Prepare a matching source background instead of leaving white cards on grey padding. Never stretch or clip the object to fill a cell.

Use fewer cells, multiple sheets or individual images when small print/material detail needs more pixels. Store exact pixel rectangles, style ids and the master revision before editing. `scripts/contact_sheet.py` builds a repeated-source sheet and layout manifest, then splits a returned sheet by that manifest; it requires Pillow. Run `python <skill>/scripts/contact_sheet.py --help` for arguments. Width/height are explicit and the default background is black; it does not choose the layout for you or certify image composition. Example for tall shapes: `python <skill>/scripts/contact_sheet.py build master.png sheet --ids red green blue ochre cream black --columns 3 --rows 2 --width 1536 --height 2304 --gutter 12 --family can-standard`. After visual review: `python <skill>/scripts/contact_sheet.py split edited.png sheet/layout.json accepted --ids red green blue`.

The inspected Studio `image-edit` tool exposes a source, references and prompt, but no output-size or aspect-ratio argument. Request 2K/4K only through a currently verified control that actually supports it. Inspect actual returned dimensions; an upscaled image adds no missing design detail. Local sheet construction can be 2K/4K regardless, but that does not establish service output size. Check current upload byte/dimension limits as well.

Measure useful detail in the actual returned object crop, not the source sheet or eventual PBR map size. A high-resolution PBR output does not establish that a small reference supplied equally fine artwork. If the returned crop cannot support the intended view, repair the image stage before Retexture rather than accepting blur as natural texture.

## 5. Edit with stable identity and rich per-cell briefs

Retain the sheet as the source and link the inspiration image as a separate appearance reference in the same relevant Studio project. Reference syntax is route-specific: Studio uses `@[name](asset:<id>)` for linked references; Blender Retexture uses its verified `reference_path`/`reference_label` interface. Do not pass bare placeholder syntax or invent a seed, mask or layout-lock parameter.

Example prompt structure, adapted to the actual family:

> Give these six blank guides believable manufactured finishes. Use the source for shape, label regions and the three-column, two-row layout, not its clay appearance. Clean printed lacquer with fine coating variation, flush ink and tiny handling scuffs near the rolled metal edges; exposed aluminium has subtle forming marks. Natural lighting reveals the surface without airbrushing away its detail. Top left: crimson print with white lettering and a fine ivory stripe. Top centre: deep green with muted lemon-yellow graphics. [Describe each remaining cell's distinct appearance.] Keep each complete object in its existing cell on the same background; use the linked inspiration for print character and palette.

Define uniqueness across deliberate dimensions—palette, label layout, illustration, print age or wear—without demanding a new object shape. Choose details appropriate to the actual material/condition; do not add blanket damage to clean products. Follow the image endpoint's prompt constraints and supported parameters. Visual lighting/background directions belong in image prose when useful, not invented API controls. Keep operational rules and UV constraints outside the prompt, and maintain cell ids in the ledger rather than relying on generated lettering.

## 6. Verify before cropping or texturing

Open the result and compare it with the seed. Check count/order, one subject per cell, unchanged shape/pose, correct label zones, distinct designs, usable resolution, no cross-cell graphics and no unwanted neighbouring objects. Fixed source coordinates do not prove output alignment. If the editor moved or merged subjects, reject those cells or deliberately re-identify/re-crop with a reviewed mapping; never blindly split and send a mismatched style to a mesh.

Also inspect realism at the actual crop size: plausible material response, meaningful surface variation, readable form and detail consistent with the brief. Correct cells with flat illustrative finishes, airbrushed surfaces or dominant glare before transferring them, even if the grid is perfect. Preserve deliberately stylised user intent. An image-quality pass and a layout pass are separate decisions.

The split helper fails on changed dimensions by default. Its explicit uniform-rescale option handles a verified proportional size change, not layout drift or shape changes. A larger canvas with the same aspect ratio still needs visual review. Keep original sheet/result and crop provenance. Repair only deficient variants with individual edits or a smaller sheet; retain accepted ones. Follow existing retry authorization and reconcile uncertain runs before resubmission.

Each accepted crop contains one object and enough context to identify its material regions, with no grid annotation or neighbour. Never pass the whole sheet to each mesh. A front view cannot specify an unseen rear label: describe the rear/sides explicitly, add verified coherent views where supported, or use controlled artwork. Do not invent multi-reference support for a single-reference Retexture endpoint or treat several views as several styles.

## 7. Pilot, branch and reuse

Retexture one representative look per geometry family from the preserved original/prepared baseline, with its accepted crop and a concise appearance brief. Proceed directly to PBR, then inspect the applied final material; do not treat the intermediate lit edit as final albedo. Verify shape/UV correspondence locally and inspect label boundaries, wrap/seams, front/oblique/back/top and material response at the established viewing distance. The image may preserve shape while suggesting impossible printed geometry; inspect the actual 3D result. Diagnose whether a failure comes from master form, image quality/resolution, preparation or the final material before correcting that stage.

Expand only when the representative final result meets the original quality target. A technical pass with unresolved visible defects is diagnostic, not an acceptable pilot. Do not lower the standard after the result or launch a dependent batch while the pilot remains visually unresolved; independent accepted work may continue. Keep user-approved approximations distinct from general method validation. These checks do not require repeated user approvals. Once acceptable, branch every remaining look independently from that baseline, never the first restyled output. Use native batches when available, coordinating local preparation/application. Count unique appearances, not placements. Preserve material names during jobs and on legacy prepared state; use external style labels unless identity-based renaming is verified.

After application, verify correspondence before sharing geometry or remapping slots; retain independent appearance sets. Instance each accepted style as many times as needed, reusing mesh/image data where supported. Inspect the populated shelf for repetition, style distribution and GPU memory. Do not claim one mesh makes hundreds of unique 4K texture sets cheap. Save dependencies and the family/master/style/placement mapping.

## Evidence before calling the grid route reliable

Test a cylinder with a wrapping label, a box with graphics on adjacent faces, a second distinct size/shape family, and a larger dense sheet. Include negative routing checks for identical chairs and a pack of different weapon/shield shapes. Report layout survival, accepted/rejected crops, actual resolution, label placement around the mesh, material separation and measured resource use. Until tested, describe the grid step as a pilot, not a verified automatic pipeline.
