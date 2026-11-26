# The parts list

`set_piece.json` records what a set piece is made of. `scripts/set_piece.py check` validates it.

## Format

```json
{
  "schema": "marso/set-piece@1",
  "name": "Clothes rail",
  "source": "brief",
  "seed": 7,
  "variant_cap": 6,
  "parts": [
    {
      "id": "upright",
      "label": "steel upright tube",
      "route": "instance",
      "size_m": [0.03, 0.03, 1.6],
      "features": ["round tube", "collar near the top"],
      "variants": [{"id": "steel", "look": "brushed steel, lightly scuffed"}]
    },
    {
      "id": "rail",
      "label": "steel crossbar, lying along X",
      "route": "model",
      "size_m": [1.5, 0.03, 0.03],
      "features": ["round tube with end caps"],
      "variants": [{"id": "steel", "look": "brushed steel, lightly scuffed"}]
    },
    {
      "id": "tee",
      "label": "T-shirt on a hanger",
      "route": "generate",
      "size_m": [0.5, 0.08, 0.75],
      "anchor": "top",
      "variants": [
        {"id": "white", "look": "white cotton, slightly creased"},
        {"id": "red", "look": "red cotton, slightly creased"}
      ]
    }
  ],
  "slots": []
}
```

| Field | Meaning |
| --- | --- |
| `schema` | Always `marso/set-piece@1`. |
| `name` | The set piece's name. |
| `source` | Where the list came from: the image file or `brief`. Optional. |
| `seed` | A whole number that fixes the layout. Default 0. |
| `variant_cap` | Most variants one part may have. Default 6. |
| `parts[].id` | Lowercase letters, digits and single hyphens; unique. |
| `parts[].label` | What the part is, in a few words. |
| `parts[].route` | `model`, `instance` or `generate`. |
| `parts[].size_m` | Width, depth and height in metres. Required for `instance` and `generate`. |
| `parts[].features` | The recognisable details to build, counted where they repeat: a phrase or a list of phrases. Optional, and expected on every structural part. |
| `parts[].anchor` | `bottom` (default) for a part that stands, `top` for one that hangs. |
| `parts[].variants[]` | At least one, each with a unique `id` and a `look`. |
| `parts[].variants[].pbr_asset_id` | The Marso asset ID of this part in this look, once it has been made. Optional; recorded from the placing skill's report, then copied into the placement list. |
| `parts[].variants[].asset_yaw_deg` | Degrees about Z, anticlockwise seen from above, that turn the asset behind `pbr_asset_id` to face -Y; 0 when it already does. Given with `pbr_asset_id`, never alone. |
| `slots` | Where instances sit, the structure's pieces included. May be empty while the parts are being agreed. |

## What the routes mean for the masters

- `model`: a piece that appears once, such as a canopy or a table top. One master, usually one variant and one instance. A structure is several of these plus instanced poles and rails, never one part.
- `instance`: modelled once, textured once for each variant, then repeated.
- `generate`: one reference image and one mesh generation. The mesh arrives in its first variant's look, so list the most typical look first. Each further variant is one New Texture on that same mesh.

`check` prints these as `jobs`: `reference_images`, `mesh_generations` and `retextures`. Every modelled or instanced part needs one Retexture for each variant. Every generated part needs one fewer than its variants. Each Retexture is a New Texture, followed by one image edit for its condition image and one PBR run, so the Marso work is three jobs for each Retexture counted. The jobs of one kind are sent together, so the count sets the cost, not the waiting.

## Writing a look

A look is a plain phrase for the surface: material, colour and condition. "Faded blue denim, worn pale at the knees" is a look. It carries no shape words and no position. The texturing step turns it into a prompt.

Keep the looks of one part clearly different from each other. Six shades of blue read as one look from across a street.

## Sizes

Take sizes from the brief or from known real sizes: a hanger is about 0.42 m wide, a paperback about 0.2 m tall. A size read from one image is an estimate; record it as inferred. The size fixes how many instances fit a slot, so a wrong size shows up as a crowded or sparse rail.
