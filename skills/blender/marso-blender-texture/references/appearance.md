# Reusable appearance briefs

Save a compact appearance brief beside the editable asset/kit or in a named Blender Text datablock. Follow an existing project format when present. This is portable workflow data, not a new Marso API or native style-lock feature. Keep private source/result IDs in the user's deliverable, not in public skill examples.

Record only what the task needs:

| Field | What to preserve |
| --- | --- |
| Identity | Human-readable style name and revision; asset/kit identity. |
| Source | Preserved source revision/checkpoint, object roots and UV layer; original mesh/node ID when available. |
| Viewing target | Intended distance/use and which visible features require actual geometry rather than a surface treatment. |
| Approved appearance | Reference images and their role, a representative accepted part, and whether approval came from the user or only an agent review. Never label an unreviewed result user-approved. |
| Material roles | Which parts are wood, plaster, metal, fabric, etc.; palette, finish, roughness intent and wear. |
| Source guide | Existing modelled features and corresponding baked colour regions; whether the actual upload appearance was visually checked. Colours guide placement but are not guaranteed masks. |
| Direction and scale | Physical grain/pattern size, member direction and end-grain intent. |
| Fixed features | Geometry, colours, markings or regions that should remain unchanged. Prompt protection is guidance, not a guaranteed mask. |
| Join strategy | Natural material breaks, covers or separately verified shared mapping; rotations/arrangements that have been checked. |
| Results | Style/variant ID, prompt and reference used, output IDs, final material names, bound objects/slots and known warnings. |
| Pilot review | Geometry, source-bake and generated-appearance findings separately; comparison conditions, unresolved defects and whether the approach is ready to extend. |

For a new kit component, reuse the baseline style wording and references, then add the new component's material roles, grain directions and relevant constraints. Inspect it beside the accepted part under the same lighting. Do not assume matching words enforce texture continuity.

Keep the technical fields above in the asset record; do not paste the whole record into a generative prompt. Describe each visible region as **material/finish → useful surface detail → condition/contact wear**, with only necessary placement guidance. For example: "Satin brushed steel louvres with faint cleaning marks and slight edge rubs; dark matte recesses." Read [appearance prompts](prompts.md) for the image-to-Retexture handoff. Prompt detail should clarify materials, not increase the apparent geometric complexity beyond the mesh or restate UV/export requirements.

For style variants, keep the source revision fixed and record one deliberate appearance change per variant (which may cover several materials if the brief calls for a complete look). Each output points back to that source. A reference can guide all variants while differing style instructions define their individual looks. Save the brief with the file so a later agent can extend the set without reconstructing intent from chat history.
