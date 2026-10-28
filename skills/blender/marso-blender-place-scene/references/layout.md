# Layout from one photograph

`layout_plan.py` reads `scene_graph.json`, `assets.json`, `registration.json` and `manifest.json` and writes `placement.json` (`marso/placement@1`). It uses the establishing view the register pass chose; `--view` picks another, and with neither it uses the image that shows the most objects and says so under `assumptions`.

## The coordinate frame

Metres, z up, the floor at z = 0. The establishing camera stands at x = 0, y = 0, at the camera height, looking along +Y, so the room lies at positive y. An object's `location` is the bottom centre of its bounding box.

## The camera model

A pinhole camera with no roll and no lens distortion.

| Option | Default | Notes |
| --- | --- | --- |
| `--camera-height` | 1.5 m | A standing person's phone. Lower it for a seated or held-low shot. |
| `--focal-35mm` | 26 | A typical phone main lens, as a 35 mm-equivalent focal length; the horizontal field of view follows from it and the photo's aspect. Use the photograph's EXIF value when there is one. |
| `--hfov` | from the lens | A horizontal field of view in degrees; overrides `--focal-35mm`. |
| `--pitch` | 0 | Degrees, positive looking up. Most room photographs look slightly down: try -5 to -15 when objects come out too far away. |
| `--ceiling-height` | 2.4 m | Where the ceiling empty and ceiling-hung objects go; walls with no height in the graph use it. |

Every value used is written to `camera` and `assumptions`.

## How positions are found

| The object | Its position |
| --- | --- |
| On the floor (its parent is a floor anchor), in the establishing view | The bottom centre of its box is projected onto the floor; the object's centre is half its depth further away. |
| The same, with its floor contact out of frame or above the horizon | Distance from its apparent size against its estimated size; flagged `depth-from-size`. |
| On a wall | The centre of its box is projected onto the wall plane; it faces into the room. |
| On the ceiling | The top of its box is projected onto the ceiling plane. |
| On another object | On the parent's top (`on-top-of`), low inside it (`inside`), level with it (`under`), or at the height its box has inside the parent's box (other relations). Sideways, at the offset its box has inside the parent's box, in the view that shows both best; flagged `offset-from-other-view` when that is not the establishing view, and `no-shared-view` (centred) when no photograph shows both. |
| Not in the establishing view, not on a placed parent | Beside a placed twin from its cluster, flagged `position-guessed`; otherwise `unplaced`. |

Walls are planes. A wall's floor line is the bottom edge of its box projected onto the floor (`wall-from-box`; a box is not the true floor line of a wall seen at an angle). When that edge is out of frame or above the horizon, the wall is put behind the furthest floor object, facing the camera (`wall-guessed`).

## Rotation

Each object faces the camera: its front, taken as the -Y side of the generated mesh, is turned towards the camera position in plan. Objects on a wall face into the room; objects hanging on or fixed to another object take its rotation. `--facing none` leaves every rotation at 0. Whether a generated mesh's front really is its -Y side is not known until it is imported; fix it in the review loop.

## Sizes

`dimensions_m` is width, depth and height. Before import it is the graph's estimate: the largest dimension `size_m`, shaped by the box's aspect in the photograph (depth taken as the smaller of width and height). After import (`--imports`) it is the minted `dimensions_m`, and `size_source` says `minted`. When the minted largest dimension differs from the graph's by more than 25%, the object is flagged `size-disagrees`. Do not rescale automatically: the graph may be wrong. A user-authorised correction belongs on the geometry group; record it and recheck contacts. Support entities must not inherit that geometry scale.

## What is placed

- Every member of an asset in `assets.json` is one instance: a cluster's members and an identity group's members each get their own position. Members of an identity group are flagged `identity-group`, because they may be fewer real objects; check them in review.
- A modelled object, or one routed to reuse without a recorded library asset, becomes a placeholder box, or is left out with `--placeholders skip`. Library assets recorded in `assets.json` are placed like generated assets.
- `part-of` objects are made with their parent and are skipped. `unconfirmed` readings are skipped unless `--unconfirmed boxes`. Anything whose parent is skipped is skipped too, so nothing floats.

## Correcting placement.json

Edit an entity's `location` or `rotation_z_deg` by hand, and keep the rest, especially `run_id`. Layout carries the generation record's run and project ids; legacy records derive a stable run id from the manifest location and project. `copies` is the total import count. Transforms describe logical entity frames, not mesh transforms. Re-running `layout_plan.py --force` rewrites the file and loses hand edits, so settle the camera options first and hand-edit last.
