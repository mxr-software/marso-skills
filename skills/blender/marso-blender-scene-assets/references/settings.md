# Resolve settings before scene submission

If the selected plan has no generation-route assets, skip generator selection. The manifest needs an explicit model only for generated entries, supplied by a per-asset plan value or `--model`.

Read the live model catalogue and the installed scene/batch command schema. Explicit user options take precedence, then a recorded project/user preference, then compatible panel settings, then an advertised supported default. Do not use a fixed model family or an example request as the default.

If no user preference is recorded, ask once early for preferred mesh generator/options, offering the supported default for this run. Continue independent planning while awaiting an optional answer. Save an expressed preference using supported host memory or a local project `marso-preferences.json`; distinguish user choice from an agent fallback, and temporary overrides from enduring preferences. Never invent cross-account memory or change add-on defaults. Reuse preferences on later runs, revalidating support; explain an unavailable choice without silently overwriting it.

## Resolve one scene budget

If using a Studio connection with `get_preferences`, include that account record before falling back to panel settings. Only persist account changes when the user asks to remember them, using verified supported fields. The inspected account setter does not expose a texture-quality field; retain that preference through supported memory/rules or a project record instead.

Establish intended use, target hardware when relevant, hero/background roles, unique meshes, repeated instances and style sets. Propose a scene-level geometry and texture budget once, using the brief when sufficient. Do not ask for every prop's polygon count.

Allocate targets by silhouette, screen coverage, detail and reuse. Record unique geometry and instance-expanded totals separately, with estimated versus measured triangles clearly labelled. Shared geometry still incurs rendering work; unique texture images, subdivision and render buffers also cost memory. Polygon count alone cannot prove GPU fit.

Choose supported values within agreed ceilings. If a minimum exceeds a strict limit, propose a different supported model or an authorized reduction workflow that retains the source and validates its result. Never clip upward silently or send an unsupported option. Single-asset runs use compatible preferences/defaults unless a real constraint needs clarification.

## Record the effective request

Pass the selected model to `manifest.py init --model <id>`; this helper no longer chooses one. Optional `--polycount` and `--texture` apply only where the plan has no per-asset override. Plan entries may carry `model`, `polygon_count`, and `texture`; explicit null omits an optional field. Omit texture for models that do not accept it, and revalidate every per-asset combination before submission.

Keep requested caps, chosen service options and actual imported counts distinct in the run's review record. Native and legacy commands can have defaults of their own: pass resolved supported options explicitly where needed and inspect returned effective options. If the installed command cannot honour the chosen model/settings, resolve that capability gap before submitting. Do not edit settings of an unresolved job or reinitialise its manifest.
