# Generation preferences and polygon budgets

Read live model capabilities and the actual operation schema before resolving options. Names, input modes and texture options differ by connection; a saved choice is intent, not proof of current support.

## Establish a preference once

When the connected Studio service exposes `get_preferences`, read its account preference as the available user-wide record. For an explicit request to remember a model, a verified `set_preferences` can persist `mesh_model` and supported `polygon_count`; inspect its current schema and preserve unrelated settings. The inspected setter has no texture-quality field, so retain that intent in supported rule/memory or a local project record instead of inventing one. No account write is needed for a temporary run override.

Use this precedence: explicit task instruction; a recorded user preference for this project; an available user-wide preference; compatible panel settings; the connection's advertised default. An explicit request to model always wins over a remembered preference for a generator.

If no user preference is known, ask once early: "Do you have a preferred Marso mesh generator or options? Otherwise I'll use the current supported default for this run." Continue setup and reference inspection while awaiting an optional answer. If the user leaves it to you, choose the compatible advertised default and say which. Do not invent rankings for object categories.

Record an expressed preference through the host's supported durable memory, or in a local `marso-preferences.json` in the user's working project. Keep model id, semantic texture/detail choice, scope, and whether the choice came from the user. Record temporary overrides in the run record, not as a new global preference. An agent-selected fallback is not a confirmed user preference. Do not modify add-on defaults or claim cross-project/account memory unless that mechanism actually exists. Keep these personal records out of the public skills repository.

On future runs read the record before asking again. Revalidate against live options. If a preference is unavailable or incompatible, explain the mismatch and propose supported alternatives without overwriting it. Ask only for a material tradeoff; an already delegated choice can be resolved and reported. Never silently round a strict ceiling upwards.

## Budget at scene level

For one asset, use the brief's purpose and compatible saved/live settings. Ask about a polygon limit only if the user supplied one, export/runtime constraints require it, or the choice materially changes the result.

For multiple assets, establish the intended use, target device if relevant, hero versus background roles, unique meshes, placed instances and material variants. Propose a scene budget once; infer sensible provisional targets when no hard limit is given and state the assumptions. Do not ask the same question for every object.

Record both unique-geometry cost and the count across placed instances. Shared geometry can reduce memory but does not make draw, traversal or shading work free. Texture images, subdivision, displacement, lights and render buffers also consume memory; polygons alone cannot predict VRAM.

Allocate per-asset targets by silhouette/detail, screen coverage and reuse. Keep generator-request counts distinct from measured imported triangles. Choose supported options within the agreed limit; if the lowest option exceeds a strict ceiling, offer a supported alternative or a preserved-source reduction workflow and validate its result. Do not submit an over-budget source unless the user accepts that intermediate or has delegated that tradeoff.
