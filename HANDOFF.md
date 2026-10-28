# Handoff

## Goal

Public, host-neutral Agent Skills (usable from Claude- and OpenAI-based hosts) that turn photographs of a room into a scene graph, plan Marso asset work from it, generate the assets through the Marso Blender add-on, and rebuild the room in Blender.

The end-to-end workflow (the maintainer's kitchen_test run):

1. Detect every object and remove duplicates.
2. Pick the unique objects Marso should generate; walls, ceilings and cabinet runs are modelled instead.
3. Create a Studio project for the run.
4. Make an object-mode reference image per object, from its crop and a prompt that says what to leave out.
5. Make a Tripo mesh at 40k, then PBR, then wait for the asset to be minted (sim-ready, real-world scale).
6. Import and place in Blender:
   - landmarks first;
   - the Blender hierarchy follows the scene graph;
   - copies are linked duplicates.

Later, the placement logic could serve other editors through their own add-ons.

Constraints:
- The scene skills are proprietary (own `LICENSE.txt`), unlike the Apache-2.0 skills.
- Every skill folder is self-contained.
- Public files and commit messages stay free of internal names and of the terms the local publication hook blocks.

## Current State

- **Now: branch `feature/library-search`, cut from `feature/scene-to-assets` (commit `a58f06b`). Committed and pushed to `origin`.**
  - **Latest commit:** the `marso` entry skill checks the library too.
    - New `references/library.md`: the `find_in_library` search, reading its results, the user's choice. It is host-neutral.
    - `generative-3d.md` checks the library before generating, unless the user asked for a new asset.
    - The routing table and the description cover finding an asset in the library.
    - `marso-blender-asset` is unchanged; it only models by hand.
  - The library check before anything is generated:
  - `crop_objects.py` writes `search.png`: the subject's own box, 2% margin, no outline.
  - `manifest.py` gains:
    - a `library` stage (`record --stage library` stores the add-on's `find_in_library` candidates);
    - `choose --reuse <asset_id>=<pbr_asset_id> | --make`;
    - `--skip-library`;
    - `pending` output carrying `library_searches` and `reused`.
  - A reused asset skips reference, review and mesh, and goes to `mint_status` and import. Placement needed no change.
  - New reference `marso-blender-scene-assets/references/library-check.md`; SKILL.md, checkpoints, studio-chain, route and reference-brief docs updated.
  - Tests: 385 in `tests/scene`, all passing.
  - Needs the add-on's `find_in_library`, now committed on add-on branch `feature/library-find-panel`.
  - **Review for host compatibility (same branch):**
    - All ten skills pass both the Codex and the Claude `quick_validate.py`.
    - The `compatibility` key was dropped from `marso-scene-decompose`; Codex rejects it. Its requirements are now in the body.
    - OpenAI `short_description` values are within 25–64 characters.
    - `<skill>` is defined in each skill. The licence lines match.
    - The place-scene rule on reused objects was corrected.
    - `docs/compatibility.md` and `docs/installation.md` were brought up to date.
    - Each scene skill's scripts ran from a lone copy of its folder.
    - Not run in Codex or ChatGPT.
- Branch `feature/scene-to-assets`, cut from `feature/scene-decompose` (commit `8313f40`, which holds the first two scene skills). Committed; not pushed.
- **`skills/core/marso-scene-decompose/`:** photographs to `scene_graph.json` plus a viewer. Rounds: detect, verify, match.
- **`skills/core/marso-scene-graph/`:** the asset plan, reference crops and briefs.
  - `--polycount`: a fixed count or `by-size`.
  - Modelling words for sideboards and modular units.
  - Crops are unmasked with the subject outlined in red.
  - A neighbour that is made as its own asset and touches the subject is named in the prompt as "made as a separate asset". The first kettle reference came back with its power base attached.
- **New `skills/blender/marso-blender-scene-assets/`:** the generation workflow over the add-on's scene commands. Review stops after the asset plan and after the reference images. `manifest.py` keeps `runs/<job>/assets.json`.
- **New `skills/blender/marso-blender-place-scene/`:**
  - `layout_plan.py` writes `placement.json` from one photograph and a camera model.
  - `place_in_blender.py` builds the collection, the hierarchy, linked duplicates and a matched camera.
- **Tests:** `tests/scene/` has 383, all passing.
- **Live:** kitchen_test ran end to end in Blender 5.2 with a dev build of the add-on (branch `feature/scene-assets` in the add-on repo). Placement is a first layout:
  - the dining table and chairs line up with the establishing photograph;
  - the coffee corner, seen only in its own photograph, is parked out of view;
  - some minted sizes are off (the table is 0.51 m tall).
- **Unresolved:**
  - Detect still misnames some objects within one photograph.
  - Placement needs a shared view to place a second corner of the room.
  - Minted sizes are taken as they come.
  - Untested on Codex, ChatGPT, API hosts and serial execution.

## Plan

- [x] Scene decomposition and asset planning skills (commit `8313f40`).
- [x] Add-on scene commands (add-on repo, `feature/scene-assets`).
- [x] Generation skill and placement skill.
- [x] Live kitchen_test run: 12 assets, references reviewed, kettle redone, meshes, mint, import, placement.
- [ ] Place objects seen only in photographs that share nothing with the establishing view, e.g. by registering them through a shared object or asking for one more photo.
- [ ] Decide what to do when a minted size disagrees with the scene: flag only (now), or rescale on the user's say.
- [ ] Blind run of the placement skill alone on the finished `assets.json`.
- [ ] A second scene; other hosts.

## Progress Log

**kitchen_test (2026-10-28)**
- **Crops:** they were masked at first (children blacked out). The maintainer asked for unmasked crops with the subject's bounding box instead, so the red box is now the default and masking is opt-in.
- **Reference images:** 12, from 120 credits. The maintainer approved them all except the kettle, which included its power base. The fix is the separate-asset rule in `crop_objects.py` (neighbours touching the subject that are generated assets are named in a "Do not include" sentence, in both directions). The regenerated kettle came back clean.
- **Meshes:** 12 Tripo 40k meshes with PBR, at 70 credits each. All 12 minted within minutes.
- **Placement fixes:**
  - The add-on returned local dimensions; it now returns world dimensions.
  - The import result lacked an `objects` list, so placement swapped every asset for a box.
  - Flat objects generated on edge are laid flat, and only once.
  - Placeholder heights are measured from the photograph.
  - Walls are pushed behind the furniture.
  - Unplaced objects are parked behind the camera.
  - `manifest.py` accepts the add-on's `mint_status` reply as is.
- **Camera:** pitch -20 degrees, estimated from where eye level falls in the photograph.

**Library search (2026-10-28, later)**
- The search routes are live but missing from the spec's paths.
  - Text: JSON body.
  - Image: multipart with only the `image` field; any extra field gives a 400.
  - Each asset comes back as a mesh row and a PBR row.
- **Search crop:** a tight crop of the object alone is needed. A padded crop finds the neighbour (glasses lying on their case found the glasses).
- **Live check:**
  - Searched with label and `search.png` in a scratch run kept on the maintainer's machine, with no credits spent.
  - Each of the 12 kitchen_test assets came back with its own library asset first: 10 as match or possible, 2 as weak.
  - The 2 weak ones are the table and the placemat. Both were minted under wrong names ("Wooden coffee table", "Coiled Straw Shield"), and their crops are filled by what sits on or in them.
  - The cork coaster, minted as "Whetstone", was still a match by image.
  - In the same run: choose reuse, then `mint_status` (all minted), and 12 were ready to import.

Earlier work (scene decomposition, blind runs 1 to 4, the verify round) is described in commit `8313f40`'s HANDOFF.

## What Worked

- Blind runs with a fresh subagent, given only the installed skill folders and a one-line request.
- Driving the add-on through `execute_blender_code` and `bridge.commands.execute`, with a Blender timer writing job states to a file and a Monitor reading it. Never call `wait_job` from inside Blender: it blocks the main thread the job needs.
- A review sheet of each crop beside its reference image, before any mesh is paid for.

## What Did Not Work

- Masked crops: black regions removed the parts of objects that the masks were meant to keep (the espresso machine's hopper).
- "Leave out X: they only share the frame" for a neighbour joined to the subject.
- A camera pitch of 0 for a room photograph: everything came out several metres too far away.

## Important Context

- **Skill rules:** `AGENTS.md`, `CONTRIBUTING.md`, and the local `.internal/publication-policy.md`, which is never staged. Never stage `.internal/`, `.local-tests/` or stray files such as `grep.exe.stackdump`.
- **Add-on:** repo `virtuoso-add-on-blender`, branch `feature/scene-assets`. The installed dev build predates the world-dimension and `objects` fixes; rebuild with `scripts/build_archive.py` (set `GITHUB_OUTPUT` to a scratch file) and reinstall.
- **Run folders and reviews** for kitchen_test are on the maintainer's machine, outside the repository.

## Next Steps

0. A blind run of the scene-assets skill on a new room, and of the entry skill on a single-object request, to see the library check from instructions alone. Never stage `grep.exe.stackdump`.
1. Rebuild and reinstall the add-on, then re-run import and placement on kitchen_test to confirm the fixes live.
2. Address the second-corner placement and the size-disagreement policy (see Plan).
3. Blind-run the placement skill, then a second room.
