# Worked cases

Six set pieces broken into parts. Use the nearest one as a pattern for the routes, then write the parts list for the actual piece.

| Set piece | Modelled once, placed once | Modelled once, instanced | Generated once, instanced | Variants |
| --- | --- | --- | --- | --- |
| Market clothing stall | Canopy, table top, drape | Upright, rail, foot | T-shirt, shirt, shorts, jeans and trousers, each on its hanger; a folded stack | Colours and prints for each garment |
| Greengrocer's stand | Each tier board, price board | Leg, wooden crate | Apple, orange, banana bunch, lettuce | Red and green apple; plain and stencilled crate |
| Bookcase | Back panel, top | Side panel, shelf board; thin, thick and tall book | None | Several covers for each book |
| Back-bar bottle shelf | Mirrored back | Shelf, bracket; two bottle shapes, a glass | None | A label and glass tint for each bottle |
| Garden centre bench | None | Leg, slat; terracotta pot in two sizes | Three plants | Pot weathering; flower colour |
| Warehouse pallet rack | None | Upright, beam; pallet, carton in two sizes | A shrink-wrapped load | Printed carton labels |

## What each case shows

**Market clothing stall.** Soft goods at a high count, on a structure split by material: steel uprights and rails instanced, a canvas canopy and drape, a timber table top. Each garment is generated with its hanger as one master and hangs from `anchor: top`. About sixty instances come from six meshes.

**Greengrocer's stand.** Organic parts on a sloped surface. Fruit sits in `grid` slots whose `back` vector rises with the tier, with `jitter_m` and a full turn of `jitter_deg` so no two sit alike. Crates are rigid and instanced.

**Bookcase.** No generation at all. Three book shapes carry many variants, so the piece looks full of different books from three masters. Books stand in `row` slots with `spacing_m` equal to their width.

**Back-bar bottle shelf.** Bottles are turned forms, so they are modelled. A label is a variant. Each `row` slot faces `across` so the labels show.

**Garden centre bench.** A modelled pot in two sizes and three generated plants. A plant and its pot are separate parts here, because any plant may sit in either pot: two instances share one position.

**Warehouse pallet rack.** A carton is a box, so it is modelled and stacked with `stack` slots. Only the shrink-wrapped load, with its irregular wrapped surface, is generated.

## Reading a new piece

1. Name what holds everything up, piece by piece: poles, boards, covers. Each is its own part; the ones that repeat are instanced.
2. For each kind of thing it holds, ask whether a ruler and a compass could draw it. If so, model it once. If it sags, folds or grew, generate it once.
3. Ask whether two things that look different differ in shape or only in surface. Surface differences are variants.
4. Count the masters. Most pieces need six to twelve. Many more usually means items are being listed where shapes should be.
