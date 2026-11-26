---
name: marso-set-piece
description: "Use when planning one object built from many parts (market stall, bookcase, shop display): which parts to model, instance or generate, their variants, and where each instance sits."
license: Apache-2.0
---

# Plan a set piece

## Overview

A set piece is one object made of many parts, most of them repeated: a clothing stall, a stocked bookcase, a greengrocer's stand. This skill plans it. It writes a parts list that gives each part a route, a master and its variants, then a placement list with one row per instance. It names no application, so the same two files serve any tool that builds or places the parts.

The saving comes from four rules:

- **One master per shape.** Sixty T-shirts are one mesh. A difference in colour, print, label or wear is a variant of that master, never a new mesh.
- **Split the structure too.** A stall is poles, a canopy, a table and drapes: each is its own master with its own look, never one block.
- **Model what is rigid, generate what is soft.** Structure and regular parts are modelled; draped, folded and organic parts are generated.
- **Compute the placement.** Positions come from the script, from a fixed seed, so a layout can be repeated and checked.

This skill makes no geometry, starts no Marso job and places nothing. Adjacent work belongs to siblings, each "when installed":

- **Modelled parts:** `marso-blender-asset`. Without it, deliver the parts list and say which masters are still to model.
- **Generated masters:** `marso-generate`. Without it, report the generated parts as not made.
- **Variants:** `marso-blender-texture`, with UVs from `marso-blender-uv`. Without them, deliver the masters untextured and list the variants still to make.
- **Readying masters and placing the instances in Blender:** `marso-blender-set-piece`. Without it, deliver the placement list for the user's own tool.
- **Placing it in Unreal** (Marso Unreal plugin, closed beta): `marso-unreal-set-piece`. Without it, deliver the placement list.

`scripts/set_piece.py` is a command-line script (Python 3.10 or later, standard library only). `check` validates the parts list and counts what it asks for; `place` writes the placement list.

## Quick reference

| Request | Do this | Read first |
| --- | --- | --- |
| An image or brief of a composite object | [Write the parts list](#write-the-parts-list) | [parts list](references/parts-list.md) |
| Unsure whether a part is modelled or generated | [Choose each route](#choose-each-route) | nothing |
| Unsure what the piece breaks into | Compare it with a worked case | [examples](references/examples.md) |
| The parts list passes `check` | [Write the placement list](#write-the-placement-list) from the listed sizes, before any variant is made | [placement](references/placement.md) |
| One object with no repeated parts | Not a set piece: use `marso-blender-asset` when installed | nothing |
| Parts that fit together in many arrangements | A kit: use `marso-blender-kit` when installed | nothing |
| A whole room or environment | Use `marso-scene` when installed | nothing |

## Write the parts list

1. Look at the whole image or read the whole brief before listing anything. Name the pieces of the structure first, then each kind of thing it holds.
2. Group what repeats into shape families. Two objects share a family when one mesh could stand for both: same silhouette and proportions. Folded, hanging and lying versions of a garment are different families.
3. Give each family one part with an `id`, a `label`, a `route` and its `size_m` as width, depth and height.
4. Record each part's `features`: the few things that make it recognisable in the image, counted where they repeat. For a canopy: "eight panels, about twenty narrow stripes, scalloped valance, centre cap". The modeller builds from these, so a part with none comes out generic.
5. List the variants seen for each part, each with an `id` and a `look`: a plain phrase for the surface, such as "red cotton, slightly creased". From an image, list every clearly different colour, print or wash it shows for that part, up to the cap; from a brief, choose enough to make the piece read as varied. A pattern belongs in the look with its scale: "narrow sage and cream stripes".
6. Keep to the variant cap of six for each part. Merge near-identical looks before raising `variant_cap`. Give a part with many instances enough variants that repeats are not obvious: about one for every six to eight instances, up to the cap.
7. Set `anchor` to `top` for a part that hangs and leave it `bottom` for a part that stands.
8. Run `python "<skill>/scripts/set_piece.py" check set_piece.json`, where `<skill>` is this skill's folder. Fix every problem it lists.

The image fixes the kind of piece, its structure and its mix of parts. Counts, order and exact colours may differ unless the user asks for a match.

**Review the parts list** before any master is made. Show the parts by route, the variants of each, and the `jobs` the check printed: reference images, mesh generations and Retextures. With nobody to answer, continue and record the list as not reviewed.

Done when `check` exits 0 and its output is in the working record.

## Choose each route

| The part is | Route | Why |
| --- | --- | --- |
| A structural piece that appears once: a canopy, a table top, a drape, a sign | `model` | Its own master and its own look |
| A structural or rigid piece that repeats: a pole, a rail, a clamp, a foot, a shelf board, a crate, a bottle | `instance` | Modelled once, exact and light, then repeated |
| Soft, draped, folded or organic: garment, cushion, fruit, plant, loaf | `generate` | Generated once from one image, then repeated |

**Split the structure by material and by piece.** Never route a whole stall, rack or stand as one part. One block gets one Retexture, which smears canvas, steel and timber into each other. For each piece ask what it is made of and whether it repeats:

- Poles and rails are one material and repeat: one `instance` part for each length and direction, such as `upright` and `rail`.
- Joints and feet repeat: `clamp`, `foot`.
- The canopy, the table top and each drape are single pieces in their own material: one `model` part each.

Further rules:

- A stretched awning, a flat banner or a taut drape is modelled. Cloth is generated only where it hangs or folds freely.
- When a rigid part and a soft part always appear together, such as a shirt on its hanger, make them one generated part.
- A pile of many small things (folded shirts, a heap of potatoes) is one generated part: the pile, not the item.
- Generate at most one mesh for each shape family. If a second generation seems needed for a new colour, it is a variant.
- Model each structural master in the direction it is used: an upright standing, a rail lying along X. A slot turns an instance about the vertical only.

A generated master will be repeated many times, so pass its maker three things: the subject alone, in its first variant's look, at the lowest polygon option that holds the shape.

Done when every part has a route from this table, no two parts share a shape, and no part mixes two materials that could be separate pieces.

## Write the placement list

The structure is placed from the list like everything else, so its slots come first and the rest are measured from them.

1. Work in the set piece's frame: metres, Z up, right-handed, the front facing -Y, the origin on the ground under the centre.
2. Lay out the structure. Give each upright, rail, foot, canopy, table and drape a slot, from the sizes in the parts list. Read [placement](references/placement.md) for the four kinds (`single`, `row`, `grid`, `stack`) and their fields.
3. Add the slots for what the structure holds. A row of hanging parts takes its `start` and `end` from the rail's own slot; a row on the table takes its height from the table's slot and thickness.
4. Run `python "<skill>/scripts/set_piece.py" place set_piece.json --out placements.json`.
5. Read its report. `per_part` gives the instances of each variant; `notes` names any variant no instance uses. Make only the variants the placement list uses.
6. Hand `placements.json` to the placing skill.
7. After the first placement, look at the render. If a master's real size differs from its `size_m`, correct the size and the slots that depend on it, then run `place` again with `--force`.
8. When the placing skill reports the masters' Marso asset IDs and asset turns, record each on its variant in `set_piece.json` as `pbr_asset_id` and `asset_yaw_deg`, and run `place` again with `--force`. Nothing moves; the list now names each master's asset and how to turn it, so another application imports it by ID. The report `place` prints names the masters still without an ID under `without_pbr_asset_id`.

`place` cycles each part's variants in a seeded order, so every variant appears before one repeats and neighbours differ. Change `seed` for another arrangement. To fix a look in one place, such as the white shirt facing the street, give that slot a `variants` list.

Done when `place` exits 0, and the instance count for each slot matches what the piece needs.

## Hand off

Report the parts by route, the variants of each, the instance count for each part, and where `set_piece.json` and `placements.json` are. Say which choices were inferred from the image, which masters or variants are not made yet, and which masters have no asset ID.

Done when the final message names both files, every inferred choice and every master without an asset ID.

## Worked example: a market clothing stall from one image

1. The image shows a pipe frame with a striped canopy and a striped drape round a table, three rails of hanging clothes and four folded stacks.
2. The structure is split by material. Steel: `upright` (2.2 m, standing), `rail` (2.4 m, lying along X) and `foot`, each routed `instance`. Canvas: `canopy` and `drape`, each `model`. Timber: `table-top`, `model`.
3. Hanging garments are five shape families, each routed `generate` with `anchor: top`: `tee`, `shirt`, `shorts`, `jeans`, `trousers`. Each includes its hanger. The folded stacks are one more generated part, `folded-stack`.
4. Variants from the image: `tee` in white, red, yellow, black and grey; `shirt` in two floral prints; `jeans` in light, mid and black denim. Every other part has one variant. Several red T-shirts are still one master and one variant.
5. `check` exits 0 and prints six reference images, six mesh generations and thirteen Retextures: one for each of the six structural parts, and one for each variant after a generated part's first. The parts list is shown for review; nobody answers, so the run continues and records that.
6. Structure slots: four `single` slots stand the `upright` at the corners, each with a `foot`. Two `single` slots lay a `rail` across the front at 2.05 m and 1.25 m. The `canopy` sits on the uprights, the `table-top` at 0.9 m and the `drape` below it.
7. The top rail's slot runs from (-1.15, -0.9, 2.05) to (1.15, -0.9, 2.05), so the `row` slot `front-top-rail` uses those ends, at the top of the tube. It names `tee` and `shirt`, with `count: 26`, `facing: along` and `jitter_deg: 4`. A second `row` on the lower rail holds 14 `jeans` and `trousers`.
8. A `single` slot at each end of the top rail holds one `shirt` facing the street, each fixed to one print with `variants`. Another holds the `shorts`. A `row` of four puts the `folded-stack` along the table.
9. `place` writes its instances and notes no unused variant. The placement list goes to `marso-blender-set-piece`.

## Common mistakes

- Making a new mesh for each colour: one master per shape, one variant per look.
- Routing the whole structure as one part: split it into poles, canopy, table and drapes, each with its own look.
- Generating the frame or the shelves: model structural pieces, so the rails are straight and sized.
- Modelling a draped garment by hand: generate soft parts once.
- Listing every visible item as a part: group by shape first, then count instances.
- Guessing where a rail is for the row that hangs from it: take the row's ends from the rail's own slot.
- Typing instance positions by hand: let `place` compute them from the slots.
- Splitting a shirt from its hanger: parts that always travel together are one master.
- Making every variant the image hints at: keep to the cap and make only those the placement list uses.
- Giving a part with dozens of instances one or two variants: the repeats show; list each distinct look the image has.
- Leaving a structural part without `features`: the canopy then loses its stripes and scallops.
