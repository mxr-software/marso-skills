# README artwork

`marso-skills.png` is the GitHub header. `marso-skills.svg` is its editable source, with the original Marso symbol and an embedded Marso library preview.

The typeface is Geist Sans, with Geist Mono for labels. The background is black; model and PBR accents use Marso blue and violet. Render the SVG at its native 1600 × 560 size with those fonts available when updating the PNG. The PNG keeps typography consistent across GitHub clients without loading external fonts.

The chair is an example from the Marso library, not a claimed result of a particular agent or skill test. Keep that distinction when changing the artwork. Preserve the preview’s aspect ratio and the Marso symbol’s proportions.

## Demonstrations

The `demos/` clips are short, silent excerpts of Marso demonstrations. They show the product and example results; they are not recordings of a fresh installation of this skill release. Posters link directly to the corresponding MP4 rather than loading every movie with the README. GitHub serves these repository videos as raw files; a browser may download them for playback. Aspect ratios are preserved.

| Files | What they show |
| --- | --- |
| `agent-car-to-pbr.mp4` | The supplied agent-built vintage racing car demonstration, from Blender construction through its Marso finish. |
| `generated-pbr-turntable.mp4` | A turntable encoded from the supplied PBR raygun render sequence. |
| `generated-grinder-cycles.jpg` | A fresh Marso image → Hunyuan 3D 3.1 Pro → Marso PBR result, rendered in Blender 5.2 Cycles at 2400 × 2400 with an OptiX GPU, adaptive sampling, a 512-sample cap and denoising. The lighting, AgX contrast, display gamma and material roughness gamma were adjusted for presentation; the downloaded maps remain unchanged. |
| `agent-model-to-pbr.*` | An agent modelling a bucket in Blender, followed by Marso texturing and the finished appearance. |
| `modular-ducts.mp4` | The revised-lighting v2 duct-kit film, showing finished parts and assembled layouts. |
| `appearance-states.*` | A chair's appearance changing from clean to scorched. This is not a combustion or geometry-damage demonstration. |
| `sim-ready.*` | Marso assets in an Isaac Sim demonstration. Numeric metadata overlays in this film are illustrative. |
| `retexture-blender.*` | The single-mesh and multipart sections of the Blender Retexture tutorial, recorded with Marso 1.6. Newer UI can differ. |
| `blender-retexture-panel.jpg` | An actual Blender 5.2 / Marso 1.6 panel capture, used to locate the sidebar, not to document every current setting. |
| `generated-reference.jpg`, `generated-pbr.jpg` | A generated reference and the resulting PBR 3D prop from the same Marso example. |
| `detect-objects.jpg` | An example of the optional Marso Detect Objects output. The agent-led scene workflow uses the decomposition skills by default. |

When replacing UI images, capture the supported version, omit credentials, account balances and private paths, and update the caption. Keep demonstration lineage separate from evidence that the current client, add-on and skills have passed an end-to-end test.

## Explanatory graphics

The `explain/` SVGs are editable diagrams; the matching PNGs provide consistent typography in GitHub. They combine real source media with captions and workflow arrows. Their images retain the source aspect ratio. Use Geist Sans and Geist Mono when rendering the SVGs. These are explanations, not product-UI screenshots or execution benchmarks.

| Graphic | Evidence and meaning |
| --- | --- |
| `modelled-car-pbr` | Clay and finished PBR frames from the supplied agent-built vintage-car demonstration. Views differ to show the construction and material detail. This is a presentation of an existing asset, not a new modelling or cloud run. |
| `generation-coffee-grinder` | The freshly generated coffee-grinder reference, its actual generated mesh with Marso PBR rendered in Cycles, and four material display passes. This example completed the image, 3D and PBR stages; it is not a blind-agent or fresh-installation benchmark. |
| `grinder-pbr-passes` | The same coffee grinder beside its original base-colour, roughness, metallic and IOR maps displayed on the 3D model. The final beauty image includes presentation adjustments described above. No UV sheets or texture atlases are shown. |
| `usd-data` | A conceptual table pairing USD package contents with their uses. No asset-specific numeric values or automatic application behaviours are claimed. See the USD guide for fields and use cases. |
| `library-monitor-search` | A text query, nine supplied Marso reference images, two highlighted monitor candidates and one selected monitor. Collection membership, result ranking and the import step are illustrative; this is not a live query or UI capture. |
| `banana-looks` | Four fruit appearances from the supplied banana demonstration; the corresponding silent clip is `demos/banana-looks.mp4`. |
| `chair-states` | Clean, worn and scorched frames from the supplied chair transition, with a conceptual state control. Camera angles vary across the original video. |
| `modular-kit-v2` | Six individually cropped PBR masters and an assembled network from the revised-lighting v2 renders. The connected film uses that same version. |
| `office-support-hierarchy` | An office reference photo and object crops from an actual scene-decomposition test. The diagram follows its recorded table, vase, flowers and tabletop-prop support relationships. It depicts the support graph, not Blender mesh parenting or a newly generated scene. |

`search-reference.png` is an unused alternative made with the built-in image-generation tool solely as an illustrative search input. It is not a Marso generation or library asset.

Earlier leather-chair thumbnails were rendered from supplied Marso meshes and their corresponding colour, roughness and metallic maps. The current library diagram uses supplied reference imagery instead. The layout is explanatory, not a screenshot of the product or a claim about search ranking.
