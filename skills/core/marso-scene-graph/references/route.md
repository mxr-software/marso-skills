# Routing: generate, model, reuse or skip

`plan_assets.py` assigns a default route to every asset from the graph alone. These are defaults, not quality claims, and they follow the `marso` entry skill: organic or complex forms favour generation as a starting point; structured, articulated or modular geometry favours agent modelling. The user's explicit intent overrides any row below, and the review step is where that happens.

## Routes

| Route | Meaning |
| --- | --- |
| `generate` | Produce a crop and brief; hand to Marso generative 3D through the entry skill. |
| `model` | Build in the application with its modelling skill, from the metadata block and the crop as reference. |
| `instance` | Use an identified scene mesh or library asset, preserve the source and retexture an independent material variant. Never silently generate a replacement. |
| `kit` | Build a modular component using shared dimensions, connections and fit tests, then review its model before texturing. |
| `reuse` | Find the asset in the library before making anything. The script never assigns this itself; set it in review when the library is known to hold the object. When generating from Blender, `marso-blender-scene-assets` searches the library for every generate-route asset anyway and offers what it finds, so `generate` is the safe default. |
| `skip` | Not a separate asset: an anchor, a part of its parent, or something the user excluded. |

## Rules, in the order applied

An exported viewer choice supplied through `--choices` takes precedence over these defaults. Unpicked objects are skipped. The optional `search_library` choice applies across selected routes; finding a candidate does not change the chosen route without a recorded decision.

1. **Anchors** (`parent: null`) are listed under `anchors` with route `model`: floors, walls and ceilings are built as the room shell, not generated.
2. **Architecture, built-in, fitted and modular units** route to `model`: labels or categories that name walls, floors, ceilings, doors, windows, skirting, cornices, fitted, built-in or modular units, worktops, counters, cabinet runs or cabinet units, sideboards, shelving units, radiators or stairs. These are planar, dimensioned and often tied to the room.
3. **`part-of`** relation routes to `skip`, with the parent's asset naming it under `children`. A drawer front is made with its chest, not alone.
4. **Repeated `instances` of structured things** route to `model`, once, with `count` instances. Structured means a category or label in the furniture, seating, table, storage, shelving, lighting, appliance, electronics or fixture families, or anything whose longest side exceeds 1.2 m.
5. **Organic, complex and small props** route to `generate`: food, plants, textiles, cushions, ceramics, vessels, ornaments, toys, tools, bags, and anything not caught above with a longest side of 0.6 m or less, including a single small appliance or device (a kettle, a camera, a laptop).
6. **Larger structured objects that appear once** route to `model`: furniture, appliances and fixtures over 0.6 m.
7. **Everything else** routes to `generate`, with `route_reason` saying it was the fallback, so the review step looks at it.

Words match whole words only: `tableware` is not a table and `woven` is not an oven. `size_m` is read as the largest dimension in metres.

## Flags

Flags never change the route; they ask the user to look.

| Flag | Raised when |
| --- | --- |
| `low-id-confidence` | The best view's `id_confidence` is `low`, or every view is. |
| `low-size-confidence` | `size_confidence` is `low` or missing: the generator will be told an unreliable size. |
| `occluded-best-view` | The best view is occluded or truncated; the crop will not show the whole object. |
| `parent-conflict` | The node appears in `parent_conflicts`. |
| `identity-group-split` | An identity group spans two assets. |
| `fallback-route` | Rule 7 applied. |
| `mostly-hidden` | Even the best member is heavily hidden; the brief leads with the inferred whole. |
| `no-inferred-whole` | Mostly hidden, and the decompose step left no context description: ask for a better photograph or describe it with the user. |
| `identity-group-has-unconfirmed` | A member of one of its identity groups is unconfirmed; the range was clipped. |

## In review

Ask the user about every flagged asset and every `model` row that might be cheaper to generate at their quality bar. Offer `reuse` wherever the library plausibly has the object. Do not argue a generator is better than modelling or the reverse; state the default and the reason, and record the choice in `asset_plan.json`.
