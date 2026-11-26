# Generation preferences and polygon budgets

Read live model capabilities and the actual operation schema before resolving options. Names, input modes and texture options differ by add-on version; a saved choice is intent, not proof of current support.

## Establish a preference once

Use this precedence: explicit task instruction; a recorded user preference for this project; a preference in the host's memory; compatible panel settings; the add-on's advertised default. An explicit request to model always wins over a remembered preference for a generator.

If no user preference is known, ask once early: "Do you have a preferred Marso mesh generator or options? Otherwise I'll use the current supported default for this run." Continue setup and reference inspection while awaiting an optional answer. If the user leaves it to you, or nobody can answer, choose the compatible advertised default, say which, and record it as chosen for this run. Do not invent rankings for object categories.

Record an expressed preference through the host's supported durable memory, or in a local `marso-preferences.json` in the user's working project. Keep model id, semantic texture/detail choice, scope, and whether the choice came from the user. Record temporary overrides in the run record, not as a new global preference. An agent-selected fallback is not a confirmed user preference. Do not modify add-on defaults or claim cross-project/account memory unless that mechanism actually exists. Keep these personal records out of the public skills repository.

On future runs read the record before asking again. Revalidate against live options. If a preference is unavailable or incompatible, explain the mismatch and propose supported alternatives without overwriting it. Ask only for a material tradeoff; an already delegated choice can be resolved and reported. With nobody to answer, use the nearest supported choice inside any stated ceiling and report it as a temporary override. Never silently round a strict ceiling upwards.

## Budget at scene level

For one asset, use the brief's purpose and compatible saved/live settings. Ask about a polygon limit only if the user supplied one, export/runtime constraints require it, or the choice materially changes the result.

For multiple assets, establish the intended use, target device if relevant, hero versus background roles, unique meshes, placed instances and material variants. Propose a scene budget once; infer sensible provisional targets when no hard limit is given and state the assumptions. Do not ask the same question for every object.

Record both unique-geometry cost and the count across placed instances. Shared geometry can reduce memory but does not make draw, traversal or shading work free. Texture images, subdivision, displacement, lights and render buffers also consume memory; polygons alone cannot predict VRAM.

Allocate per-asset targets by silhouette/detail, screen coverage and reuse. Keep generator-request counts distinct from measured imported triangles. Choose supported options within the agreed limit; if the lowest option exceeds a strict ceiling, offer a supported alternative or a preserved-source reduction workflow and validate its result. Do not submit an over-budget source unless the user accepts that intermediate or has delegated that tradeoff. With nobody to answer, leave that asset unsubmitted and report it with the lowest supported option.
