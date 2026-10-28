# Handoff

## Goal

Add public, host-neutral Agent Skills (usable from Claude- and OpenAI-based hosts) that turn photographs of a room into a scene graph, and use that graph to plan Marso asset work (reference image, 3D generation, PBR): how many unique assets and instances, the per-object crop and prompt, what to model instead of generate, and what metadata travels with each asset. Blender scene placement from the graph comes later.

Constraints: these two skills are proprietary (own `LICENSE.txt`), unlike the Apache-2.0 skills. Every skill folder is self-contained. Public files and commit messages stay free of internal names and of the terms the local publication hook blocks.

## Current State

- Branch `feature/scene-decompose`, cut from `development`. Nothing committed or pushed yet.
- `skills/core/marso-scene-decompose/`: done and blind-tested four times.
  - **Rounds:** detect, verify, match.
  - **Scripts:** in `scripts/`, run through `fast.py` and `plan_fast.py`.
  - **Viewer:** `assets/viewer_template.html`.
- `skills/core/marso-scene-graph/`: done and blind-tested once.
  - `plan_assets.py` writes `asset_plan.json`.
  - `crop_objects.py` writes a crop and brief per asset.
- `tests/scene/`: 361 tests, all passing (`python -m unittest discover tests/scene`).
- **Wired in:**
  - routing rows in `skills/core/marso/SKILL.md`;
  - a pointer in `skills/core/marso/references/generative-3d.md`;
  - `README.md`;
  - an install bundle and the Pillow note in `docs/installation.md`;
  - a compatibility section in `docs/compatibility.md`.
- **Unresolved:**
  - Detect still misnames some objects within a single photograph, and the verify round is conservative.
  - Some boxes are loose.
  - Not tested on Codex, ChatGPT, API hosts or serial (no helper agents) execution.

## Plan

- [x] Port the fast path into one self-contained skill folder.
- [x] Host-neutral SKILL.md and references (detect, register, verify, match, relations, schema, gotchas).
- [x] Scene-graph skill: asset plan, reference brief, routes, metadata.
- [x] Fixes from the blind runs (see the progress log).
- [x] Context-built descriptions for heavily hidden objects (`occlusion`, `whole_description`, node `inferred_whole`).
- [x] Verify round (numbered crop sheets; renames, removals, duplicates, reparents).
- [ ] Commit on `feature/scene-decompose`, once the maintainer approves.
- [ ] Optional: a box-tightening step; a blind run on another scene; tests on other hosts.
- [ ] Later: placing the scene graph in Blender.

## Progress Log

**Blind run 1:**
- `merge_tiles.py` loop-breaking orphaned every object resting on a support loop (worktop and base units). It now cuts one link per loop.
- The viewer gallery crashed (`RangeError`) because every crop copied the embedded photograph into the markup. Crops now share one string through `fillCrops()`.
- SKILL.md instruction gaps were fixed: job naming, agent caps, exit codes, anchor check, local-server fallback for the viewer.

**After run 1, from user review:**
- Duplicates at tile seams with different names: added `join_across_seams()` and `drop_slivers()`.
- A whole-view housing must never swallow a hanging object.

**Blind run 2:**
- Stacked same-name objects looped; the named support is now the one below.
- Geometry-only joins are now marked low confidence.

**User request:** heavily hidden objects carry a context-built whole description through to the reference brief. In the asset plan, the least hidden member of a group stands for the asset.

**Blind run 3 and the scene-graph blind run:**
- Wide-view guesses inside a close-up's region that the close-up never matched are now marked `unconfirmed` (`apply_matches.py --registration`) and listed for review, not made into assets.
- Planner fixes:
  - whole-word route matching;
  - numeric `size_m`;
  - `cl_id` key;
  - clusters merged with identity groups;
  - image paths relative to the project;
  - merged `index.json`;
  - no masking of a child that covers the subject.

**User request:** verify round. `make_verify.py` plus `fast.py verify-plan` and `fast.py verify`.

**Blind run 4:**
- Added a `reparent` decision.
- A merged object is now named by its best view; it used to take the first-listed member's name, which was often a wide-view guess.
- Corrections that were never merged are now joined.
- Run 4 graph: 125 objects, 119–125 physical. The plan: 96 assets, 109–111 instances. Run 3's raw plan was 104 assets and 118–127 instances.

## What Worked

- Blind runs with a fresh general-purpose subagent, given only the installed skill folder and a one-line user request, then a review against the photographs. Starting a separate session for this was refused by the app's auto-mode check.
- Reading the overlays (`qc/*.png`) and labelled overlays (`draw_boxes.py` without `--no-labels`) to find seam duplicates and misnames.
- The registration region of a close-up pair, as a cheap signal for wide-view misreadings.

## What Did Not Work

- Name-based dedupe alone at tile seams: two tiles name one object differently.
- Choosing an asset's representative by view count or size alone: it picked low-confidence or hidden members.
- Expecting the verify round to fix supports without a `reparent` decision: the agents could only describe them in notes.

## Important Context

- **Skill rules:** `AGENTS.md`, `CONTRIBUTING.md`, and the local `.internal/publication-policy.md`, which is never staged. Never stage `.internal/` or `.local-tests/`.
- **Commits:** the local hooks in `.git/hooks/` block restricted terms in files and commit messages. Stage explicit paths.
- **Run layout and schemas:** `skills/core/marso-scene-decompose/references/schema.md`. Clusters use `cl_id`, areas `ar_id`.
- **Script exit codes:** 0 clean; 1 done, with something listed for a person to look at; 2 an input could not be read.
- **Blind-run folders and reviews** are on the maintainer's machine, outside the repository. They are not part of this branch.

## Next Steps

1. Review the diff: `git status`, then `git diff`; the untracked folders are the two skills and `tests/scene`.
2. Commit on `feature/scene-decompose` with explicit paths, once the maintainer approves, and include this file.
3. Decide on a box-tightening step, and whether the verify round should be stricter about renames.
4. Blind-run another scene (a different room) and, if available, a Codex host.
