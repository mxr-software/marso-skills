# Slots and the placement list

A slot is a place on the structure where instances sit. `scripts/set_piece.py place` expands the slots into one row per instance.

## The frame

- Metres, Z up.
- The set piece's front faces -Y. Its origin is on the ground under its centre.
- `yaw_deg` turns an instance anticlockwise about Z, seen from above. At 0 it faces -Y, like the piece.
- A position is where the instance's anchor point goes: the centre of its base for `anchor: bottom`, the centre of its top for `anchor: top`.

Build every master facing -Y, so a turn of 0 means the same for all of them.

## Slot kinds

Every slot has a unique `id` and a `kind`. Give a slot under a shelf or rail its `headroom_m`, the clear height above it; `check` then rejects a part too tall to fit. Any slot may also add `yaw_deg` (an extra turn), `jitter_deg` (a random turn up to that many degrees either way), `jitter_m` (a random sideways shift) and `variants` (the only variant ids allowed there).

### `single`: one instance

```json
{"id": "sign", "kind": "single", "part": "price-board", "position": [0.4, -0.5, 1.1], "yaw_deg": 0}
```

### `row`: instances along a line

```json
{"id": "top-rail", "kind": "row", "parts": ["tee", "shirt"], "start": [-1.1, 0, 2.05], "end": [1.1, 0, 2.05],
 "count": 24, "facing": "along", "order": "blocks", "jitter_deg": 4}
```

- `start` and `end` are the two ends of the rail or shelf edge.
- Give `count`, or `spacing_m` to fill the length at that spacing. Instances are spread evenly, half a space in from each end.
- `facing`: `across` (default) turns each front square to the row, as for books on a shelf or bottles on a bar. `along` turns each front down the row, as for hangers packed on a rail.
- `order`: `blocks` (default) gives each named part one run, in the order listed. `mixed` shuffles them.

### `grid`: instances on a surface

```json
{"id": "top-tier", "kind": "grid", "parts": ["apple"], "origin": [-0.6, -0.4, 0.9],
 "across": [1.2, 0, 0], "back": [0, 0.3, 0.1], "columns": 8, "rows": 2}
```

`origin` is the front-left corner. `across` and `back` are the full extents of the surface as vectors; `back` may rise, for a sloped tier. One instance sits at the centre of each cell.

### `stack`: instances piled up

```json
{"id": "table-pile", "kind": "stack", "part": "folded-shirt", "base": [0.2, -0.3, 0.9], "count": 6, "step_m": 0.035}
```

`step_m` is the rise for each instance; it defaults to the part's height.

## Choosing counts

- A packed rail of hanging clothes takes one garment every 0.04 to 0.06 m. The hook passes over the rail, and a `top` anchor is the highest point of the master, the crown of the hook. So give the row the height of the top of the rail plus the thickness of the hook's wire.
- Books stand at their own thickness apart; give `spacing_m` equal to the width in `size_m`.
- Loose goods such as fruit read better slightly under-filled, with `jitter_m` of a fifth of their width and `jitter_deg` of 180.

Give every structural piece its own slot. A modelled part with no slot is placed once at the origin, which suits only a piece centred on the ground. An instanced or generated part with no slot is an error.

## The placement list

```json
{
  "schema": "marso/set-piece-placements@1",
  "set_piece": "Clothes rail",
  "seed": 7,
  "units": "m", "up": "Z", "front": "-Y",
  "masters": [{"part": "tee", "variant": "red", "route": "generate", "anchor": "top", "label": "T-shirt on a hanger", "size_m": [0.5, 0.08, 0.75]}],
  "instances": [{"id": "top-rail-001", "slot": "top-rail", "part": "tee", "variant": "red", "position": [-1.054, 0.0, 2.05], "yaw_deg": 91.7}],
  "notes": []
}
```

`masters` lists each part and variant that at least one instance uses: these are the objects the placing tool needs. `notes` names any variant no instance uses and any part placed by default.

The script refuses to replace an existing file unless it is given `--force`.
