---
name: marso-scene-graph
description: "Plan assets from photographs or a direct scene design: choose reuse, modelling, generation, instances or kits, with effort, references and scene resource targets."
license: Proprietary. See LICENSE.txt in this skill folder.
---

# Plan scene assets

For a prompt or settled design without real detections, read [direct design input](references/design-input.md). Use its adapter and explicit routes; skip the photographic graph/crop steps below. For photograph-based work, continue here. Category and size rules are provisional: explicit user choice and functional requirements take priority. Record effort from intended views, articulation, exact fit and reuse, not size alone.

A scene graph is a finished inventory of a photographed scene: every object has a `global_id`, a label, a size estimate, the thing that holds it, and a box in each image that shows it. This skill turns that inventory into the work list Marso needs. It does not generate anything, and it does not re-detect objects; if the graph is wrong, fix the graph first.

Expect the `scene-decompose/scene-graph@1` layout: `nodes[]` with `parent`, `relation`, `size_m`, `views[]`; `clusters[]` of kind `instances` or `variants`; `identity_groups[]` with `at_least` and `at_most`; `parent_conflicts[]`. A `manifest.json` beside it maps each `image_id` to a file and its pixel size. An optional `view_scores.json` names the best view of each object.

## Four questions this answers

1. How many unique assets are there, and how many instances of each? Read [asset plan](references/asset-plan.md).
2. What is cropped and said for each one? Read [reference brief](references/reference-brief.md).
3. Is each asset generated, modelled, reused from the library or skipped? Read [route](references/route.md).
4. What metadata travels with the asset into generation and the application? Read [metadata](references/metadata.md).

In shell examples, `python` means an installed Python 3.10+ interpreter. Check its version first; on Windows, use `py -3.13` or another installed compatible version if the default `python` is older. Blender-only scripts run in Blender instead.

## Workflow

Work from the user's project folder, with the run folder that holds the graph. Run the scripts by their full quoted path; `<skill>` below stands for this skill folder's path. They need Python 3.10+, and `crop_objects.py` needs Pillow.

1. Build the plan. `python "<skill>/scripts/plan_assets.py" "<run>/scene_graph.json" --scores "<run>/view_scores.json" --out "<run>/asset_plan.json"` writes one entry per unique asset with its route, count, floor and ceiling, members, best view and flags, and prints a summary. Omit `--scores` when there is no scores file; the script ranks views itself. Read [scene polygon budgets](references/polycount.md) to allocate targets by scene needs. Optional `--polycount` presets are provisional estimates, not a scene budget or verified generator settings.
2. Review material plan choices with the user before generation. Prepare local crops and library candidates first when needed for one consolidated review; cropping alone is not generation approval. Walk through the summary, every flagged asset, every route the user might disagree with, and every entry under `unconfirmed`: each is probably a wide view's misreading of something already planned, and becomes an asset only if the user says it is a separate thing. Record changes by editing `asset_plan.json`; the route and count fields are the agreement, not the script's opinion. Add one line per decision to its `review` list, saying who decided: when the user has delegated those decisions, record them as yours. Otherwise retain unresolved material choices for the user. Consolidate this review with library choices and the scene budget rather than asking twice about an unchanged plan.
3. Crop the references. `python "<skill>/scripts/crop_objects.py" "<run>/scene_graph.json" --manifest "<run>/manifest.json" --plan "<run>/asset_plan.json" --out "<run>/references"` writes `<asset_id>/crop.png`, `search.png` (the subject alone, unmarked, for a library search) and `brief.json` for every asset the plan routes to generation, plus an `index.json`. `--ids` picks assets by `asset_id` or `global_id` whatever their route, so a modelled asset can have a reference too; `--pad` changes the margin, the subject is outlined in red on an unmasked crop by default, `--mask-children` or `--exclude-parent` opt in to masking, and runs with different flags add to the same `index.json`. Run it from the project folder the decompose run used; `--image-root` is only for photographs that have moved. Requires Pillow.
4. Hand over. Each brief names the subject, its real size and everything else in the crop; its `prompt` is written for an object-mode image node shown the crop as `@crop`. In Blender, `marso-blender-scene-assets` executes the generation rows when installed, checking library candidates where reuse fits the approved choices. Explicit new-generation rows and identified local sources skip that search; model/instance/kit rows retain their own handoffs. Otherwise give the brief and crop to `marso-generate` when installed; it chooses the generator and settings from live capabilities. Modelled assets go to the application's modelling skill with the same metadata block. Do not invent a generation command when no route is installed; deliver the plan and briefs as the handoff.

For repeated shapes with distinct appearances (such as labelled cans), keep placement and appearance identities while planning one reusable master per compatible geometry family. A `variants` cluster alone cannot distinguish shape changes from style changes. Record family/master/style mappings in the run ledger, then use the texture skill's appearance-family workflow when installed. Do not regenerate a mesh per label, collapse all labels into one appearance, or treat different weapon/shield shapes as texture-only variants.

Inspect the clearest crop for each proposed family and the members whose proportions/construction differ. Record the visible evidence for sharing a master; label keywords, script routes and successful graph validation are only planning aids. Pass inspected references, uncertain dimensions and defining form landmarks to the modelling workflow before repetition. Obtain complementary references when needed to resolve an unclear shape. A `part-of` or included component still needs a suitable creation method: generated/reused contents may belong inside a modelled container. Do not silently downgrade difficult visible geometry to placeholders because it is not a separate plan row.

For compound groups, distinguish placement identity from modelling work units. A shelf of containers or a board of tools can retain its group in the scene plan while its different object families receive separate master briefs in the existing run record. For each master, record its route, reference/design basis, defining construction, intended view/reuse and acceptance status. Share a master only where shape and construction permit it. Do not create a separate task for every fastener or instance, or change graph identities just to organise modelling. Hand these briefs to the modelling workflow; accepting the group layout does not accept its component geometry.

For a reference assortment, record shape families, appearance variants and placements separately. A rack of many objects may need several silhouettes as well as repeats. Compare the group's size range, family mix and visible arrangement with the reference before accepting its master inventory; a high instance count or many colours is not evidence that the assortment is covered. Inferred identities remain labelled as design choices.

## Hard rules

For a photographed room, resolve material ambiguities in shell shape, corner angles and major object identity at the plan checkpoint, before bulk asset creation. Record known measurements separately from estimated dimensions. Have the application workflow show a rough top-down layout and check all source views; the establishing view alone cannot account for objects visible only elsewhere.

When the viewer supplied `scene_choices.json`, pass it to `plan_assets.py` with `--choices <run>/scene_choices.json`. Explicit choices override heuristic routes; unpicked objects get `skip`. Read [viewer choices](references/choices.md) for the format, identity rules and library-search handoff. Crop selected assets with `--all-routes` so modelling, instancing and kit work receive reference and search images too. Do not interpret an agent proposal as user approval, or submit modelling, instancing or kit rows to the generation queue. Selected room-shell anchors remain under `anchors` for a separate application handoff.

- Every count resolves to `global_id`s. An asset with count 3 lists three members; never a bare number.
- Identity groups give a floor and a ceiling. Report `count_at_least` and `count_at_most` as they stand; do not collapse them by guessing which view showed which object. Only the user, or a better view, closes the gap.
- A crop is evidence of identity, material and camera, not a pose or composition to copy. The generator must be asked for the whole object; the crop can show it cut by the frame, hidden behind a child or resting on a parent.
- Anchors (parent `null`: ground, walls, ceiling) are not assets. They are listed separately so the application can build the room shell.
- Add no pricing, credit or spending steps. The plan is non-generating.
- Write only into the run folder. Never modify the scene graph, the manifest or the source images.

## Deliver

Report the number of unique assets and the instance range (`instances_at_least` to `instances_at_most`), the route split, the unconfirmed readings left out, the assets flagged for the user, the decisions in `review`, and where `asset_plan.json`, the crops and briefs were written. For an already requested scene build, continue to creation and placement using installed companion skills; do not treat this plan as the final scene. State what was not checked: a crop has not been viewed unless you opened it, and report visual validation separately from user confirmation or delegated agent decisions.
