# Compatibility

## Modelling and UV acceptance revision

Updated 2026-10-30. The asset and kit workflows require an inspected geometry checkpoint before final UV/bake work and distinguish model quality, mesh validity, UV readiness and user approval. UV guidance now covers lower-resolution strip sampling, deliberate detail allocation, alternate layouts for wasteful rings/strips, and rebaking after atlas revisions. Image handoff checks distinguish changed canvas framing from changed object proportions.

Independent Blender 5.2.0 trials of the preceding instructions produced mixed visual results: UV checks passed, but complex soft-form modelling and curved-surface packing still needed improvement. The revised instructions address those failures; they have not yet demonstrated improved modelling in a new blind execution. Do not infer general photorealistic quality from structural tests.

The updated read-only UV helper reports per-chart area/bounds and a labelled width proxy. Optional exact-position/UV matching diagnoses exporter vertex splits without welding geometry; default connectivity remains unchanged. Native regression checks cover narrow strips, split vertices, real seams, positional differences and duplicate faces. Rechecks on four saved assets and their GLBs compare raw and diagnostic reports while retaining independent overlap audits. These are local geometry/UV checks, not live Marso preflight, new cloud generation, or fresh Claude/OpenAI-host installation checks.

Pre-publication validation passed all 416 scene/helper tests, including isolated packages for all 14 skills, plus 11 native Blender placement tests and the UV quality regressions. Hosted CI and a fresh client installation remain separate checks.

## Image and appearance revision

Updated 2026-10-30. The working collection contains 14 skills, adding the application-independent `marso-image` entry point. Skills CLI 1.7.4 discovered all 14 locally. The collection's isolated-package test passed for all skills, and all six contact-sheet helper tests passed. These checks cover package metadata/local links and sheet geometry, cropping, backgrounds and invalid-input handling; they do not establish visual quality or a new Claude installation.

The instructions now distinguish reference-backed master form, image-edit appearance quality, concise Retexture direction and final PBR acceptance. Contact-sheet dimensions must be chosen explicitly; the default padding/transparency background is black. Export checks cover unintended parts and missing colour textures, with local transparency restoration documented separately. Eight additional offline routing cases are specified but have not been run with fresh agents. The stopped scene trial was not resumed for these changes, and no new cloud jobs or visual-quality validation were performed. Earlier checks below refer to their stated revisions.

## Earlier workflow routing revision

The preceding workflow revision contained 13 skills, including dedicated generation, library reuse and Blender render/performance entry points. Skills CLI 1.7.4 discovered all 13 locally. All packages passed metadata and isolated file-link checks. The scene-helper suite passed 408 tests, followed by an 11-test manifest retest after the final settings changes. GitHub CI contains the package/helper checks; its hosted run has not been verified for the current revision.

New scene manifests require an explicitly selected model for generated entries, either in the plan or through `--model`; optional polygon/texture values are no longer injected. Existing manifests retain their recorded settings and can resume without reinitialisation. The plugin manifest is prepared as 0.2.0; this does not establish publication or installation of that version. The Claude CLI was unavailable for a fresh validation in this environment.

Fresh Codex agents exercised generation, reuse, standalone decomposition, complete scenes, preferences, budgets, review gates, variants and recovery in offline workflow simulations. Those checks are distinct from actual asset creation, a Claude-host trial or GPU benchmarking. Earlier installation results below describe the previously published collection, not a new installation of this checkout. No new live cloud or render-performance guarantee is claimed.

The texture skill also defines appearance families: one geometry/UV master with multiple looks, distinct from packs of different shapes and ordinary identical instances. Its contact-sheet helper passed four offline layout/crop tests covering 2K/4K sheets, non-divisible grids, changed dimensions, selective crops, invalid bounds/ids and overwrite protection. A final fresh-agent pass covered eight appearance-family and recovery cases; it preserved the intended routing and identified one broad modular-family phrase that was clarified. Live image-edit grid preservation and 3D label transfer remain unverified; the instructions require a representative pilot before bulk use. The inspected Studio image-edit schema exposes no output-resolution control, and the inspected Blender `capture_reference` selected-mesh mode uploads a mesh rather than an image. Source checks used Studio MCP v0.16.0, local Studio source `e7362d8` and the add-on source identified below.

Reviewed 2026-10-28. Format compatibility, available application tools and successful end-to-end execution are separate checks.

## Shared skill format

All skill packages use the [Agent Skills format](https://agentskills.io/specification): a leaf folder named after the skill, a `SKILL.md` with `name` and `description`, and supporting files inside that folder. Optional `agents/openai.yaml` supplies OpenAI UI metadata; the workflow does not depend on it. The same instructions are used by OpenAI- and Claude-based hosts.

The repository's `skills/core/` and `skills/blender/` directories organise source. They are not themselves installable skills. Follow [installation](installation.md) to place each leaf folder in the client's discovery directory or attach it through its API. The Claude marketplace exposes one `marso` plugin, whose manifest points to those two skill directories. There is no OpenAI marketplace plugin bundle.

Claude account downloads contain one complete ZIP per skill, plus an outer ZIP for downloading the collection. Descriptions are limited to 200 characters for the account upload guidance. Archive contents and package-local resources are checked before publication; actual account upload and execution still need verification in the user's Claude environment. Terminal installation and account upload are distinct routes.

Claude Code 2.1.312 validated the marketplace and plugin manifests and installed `marso@marso-skills` from both a clean local copy and GitHub in isolated configuration directories. All ten skills and 83 skill files in the GitHub installation matched the published source. Validation reported advisory warnings about repository-only `CLAUDE.md` and a missing catalog icon; neither prevents installation. This checks Claude Code packaging, not the Claude account UI or a live Blender task.

| Host | Loading route | Verification boundary |
| --- | --- | --- |
| Codex | `.agents/skills/<skill-name>/SKILL.md` | Format/package and isolated installation checks passed; fresh-client Blender workflow not yet verified. |
| Claude Code | `.claude/skills/<skill-name>/SKILL.md` | Format/package and isolated installation checks passed; fresh-client Blender workflow not yet verified. |
| OpenAI API agent | Supported skill attachment or local runtime loading | Host must expose the skill files and the required application tools; live API integration not tested here. |
| Claude API agent | Custom skill upload/attachment or host-managed skill loading | Host must expose the required application tools; live API integration not tested here. |
| ChatGPT / Claude desktop | Client's supported custom-skill or plugin workflow | Availability and application access depend on the client/account; fresh installation remains unverified. |

The collection is publicly available. Development-preview features are identified separately below. Structural validation does not certify model behaviour or photorealistic output.

The Skills CLI discovered the six published Blender and entry skills and installed them into isolated Codex and Claude Code project directories. All twelve installed copies matched their source resources. Frontmatter, standalone ZIP packages, package-local links and public repository links passed validation. This checks distribution and file accessibility, not live model execution.

The install-all route was rechecked on 2026-10-28 using Skills CLI 1.7.4: the earlier remote collection installed six skills for each of Codex and Claude Code; the ten-skill release candidate installed ten for each. All 166 installed files in those twenty release-candidate packages matched their source files. Reinstallation and CLI discovery also passed. These were isolated project installations; no existing user-level skills were changed. Public installation follows `main`; other development branches may contain different revisions.

## Blender and Marso capabilities

Local workflow checks used Blender 5.2.0 LTS. Add-on source review includes manifest 1.7.1 and the `release/1.8.0` project-picker implementation at `12a97e5`, which still reported that manifest version. A reviewed checkout is not proof of a published release or the user's installed capabilities. Discover the loaded command schemas before use.

Native Blender checks exercised modelling, unique UV preparation, connection helpers, colour baking, map application and real Retexture/PBR jobs. They used the add-on directly, not an independently validated official Blender MCP transport. Results exposed visual defects as well as successful operations; no general artistic-quality guarantee follows.

Relevant operational limits:

- A loaded skill does not supply Blender control. Marso's local Control Server is JSON-over-HTTP, not an MCP server; its hosted Agent Connection is a separate route.
- Project-aware builds expose Save to commands shared by Create and Retexture. The selection is per .blend and separate from Library browsing. Older builds can lack these commands despite sharing a manifest version. Auto PBR uses its own queue.
- Library sync may fall back to cached data. Visible thumbnails or a successful sync alone do not prove a fresh authenticated response.
- The reviewed update action opens a download page; installation and verification are separate steps.
- Assembly preparation can collapse currently hidden faces. It has no inspected preserve-hidden-faces option; reusable/moving surfaces need an appropriate preparation strategy.
- Independent Restyle results can differ in materials, detail and seams. Briefs, source colours and reference images guide generation; they do not enforce exact masks or continuous boundaries.
- The snapping helper checks rigid connector placement, not all collisions, manufacturing fit or structural safety.
- Generator options vary by route and installed version. Use live capabilities; the repository does not publish a frozen model catalogue or comparative quality rankings.

## Maintainer checks

Modelling and authored-UV checks on 2026-10-29 used Blender 5.2.0 LTS. Four local asset trials exercised profile/revolve, sweep, section-loop and layered-surface construction. Saved source and evaluated texture copies were reopened; per-face correspondence confirmed geometry preservation apart from explicitly recorded hidden-face exclusions. All four final layouts passed overlap, winding, bounds and requested pixel-spacing checks. Visual review rejected the modelling quality, especially on complex forms: the UV results do not validate the modelling workflow. Reference-based form checks and explicit rebuild decisions have since been added, but improved modelling outcomes require a fresh trial. No cloud texturing, client transport or blind-agent benchmark was exercised in these trials.

The read-only UV quality helper has native Blender checks for isotropic mapping, equal-area directional stretch, inter-chart and tile-border spacing, degenerate UVs, world scale and connected charts. It complements the overlap audit; a passing spacing result alone is not UV acceptance. Same-chart self-proximity and automatic visibility determination remain outside its scope.

A subsequent direct modelling trial exercised the revised form/construction checkpoints on one complex prop. Intermediate visual checks led to repairs to surface contact, attached-detail clearance and component bounds before final UV work. This demonstrates use of the inspection/repair sequence, not validated artistic quality: the revised result still requires artist review, and no fresh blind-agent, UV-handoff or cloud-texture test was run on it.

The scene viewer supports creation-route choices, browser drafts, JSON export/import and display of recorded library candidates. Offline checks cover the selection-to-plan-to-reference-to-manifest handoff, rejected stale graph revisions, route isolation and Empty support frames for omitted parents. Browser interaction checks passed in Microsoft Edge on desktop and mobile-sized viewports; nine native placement checks passed in Blender 5.2.0. The scene regression suite and focused follow-up tests passed. No new live library search, mesh generation or Retexture was submitted for this viewer update. The HTML displays search results supplied by the agent; it does not call Marso directly. Exported files must be handed back to the agent to update the run.

Validate each complete skill in isolation: frontmatter, package-local links, optional metadata and bundled scripts. Use [setup cases](../tests/blender/setup-cases.md) and [workflow cases](../tests/blender/workflow-cases.md) as acceptance criteria, not as a claim that every case has passed. The offline Blender checks in `tests/blender/` do not call cloud generation or validate client transport.

Detailed experiment journals, prototype scene builders and raw evidence are kept local. Installable skill packages contain only reusable workflow instructions and their supporting resources.

## Scene decomposition and asset planning

`marso-scene-decompose` and `marso-scene-graph` need a shell host, Python 3.10+ with Pillow, and local image inspection. They do not need an application or service connection. Each scene skill carries its own licence.

Offline tests cover intake, tiling, verification, matching, graph validation, viewer generation, asset planning and reference crops. Inputs with changed image hashes are refused when results already exist; start another run. Images from multiple folders retain their individual paths. Prior Claude Code trials informed the instructions, but cross-client behaviour, serial execution and visual generalisation remain unverified. Names, boxes, identities and dimensions are estimates that require review.

## Scene generation and placement in Blender

These workflows require an add-on exposing the documented scene commands. The latest source review on 2026-10-29 used `b0e33e5`, including the revision guards, batch engine/services, persistence and bridge schemas. Earlier reviews covered `c0bdb55`, `3828600`, `8c48342`, `2194155` and diagnostics at `e48e2c7`. Source availability does not establish which build a customer has loaded. Discover installed commands; native batches are preferred when present, with an individual-command fallback for older builds. If library search is missing, the documented skip route is available with disclosure.

Newer source includes identity-based prepared materials, explicit target/family scope, source-auto branching, reset-to-original and input-reference framing. Keep material names stable during jobs and verify installed identity tracking before renaming afterwards. Older builds retain name-based state and upload-only behaviour. Revised guards include connected RGB/Value outputs, Colour Ramps and curves as well as evaluated geometry, preparation transforms, UVs and image pixels. Object-/scene-dependent or otherwise unverified shader inputs prevent cloud-source reuse and produce prepare warnings about inputs that cannot be checked before apply. Keep pending targets and those dependent inputs unchanged. The corrected source-auto route retains an export and falls back to uploading it when its source cannot be used. Pending target lookup still depends on object names; renaming an assembly part also changes its revision. Missing image scores on individual library candidates can mean they were absent from the image result set, even when both searches ran.

Supporting builds expose structured job `details` and `list_failures` for persisted individual-job failures; native batch histories are read with `batch_item`. Native batches submit eligible independent cloud work without waiting for prior jobs to finish, using bounded networking and a coordinated local lane. Marso controls cloud execution queueing. Status and external long-poll monitoring are available; automatic chat wakeup/push notifications are not verified. Submission-to-observation timings are not pure service latency, and no fixed throughput improvement is claimed.

Batch validation on 2026-10-29: all 203 add-on unit tests passed. Independent Blender 5.2.0 probes confirmed the previously missed RGB/Value/Colour Ramp edits now invalidate reuse. Native restart regressions passed with prepare/apply calls queued, just before queueing, and during disable/re-enable; the main thread stayed responsive and the checked stages were not duplicated. Supporting builds can return `batches_restarting` during handover: return control to Blender and repeat the call after a brief external wait, retaining the original submission request id. New status responses support `next_since`/`complete`, and `batch_items` supports full-record pagination; discover these fields before relying on them. Held items use retry, Retexture reprepare or cancel; review rejection applies only to `awaiting_review`. Reprepare starts fresh stages for an accepted changed target. Uncertain non-PBR submissions are held after bounded rechecks; this timeout is not a service guarantee. These offline checks do not establish live cloud recovery or installed client compatibility. No add-on installation or live generation was performed for this review.

Reference crops now default to square with neutral edge padding, while library search crops remain tight and unmarked. Generated references still require visual review before 3D submission; neither square framing nor a fixed subject-area percentage guarantees service acceptance. Placement accepts explicitly mapped modelled working assemblies and preserves them on rerun. It does not synchronize changed masters or solve joint multi-view camera/room reconstruction automatically.

Validation on 2026-10-29: all 406 scene regression tests passed, along with 11 native Blender 5.2.0 placement checks. New coverage includes modelled handoff/rerun preservation, placeholder exclusion from real bounds, square crops at image edges, thin subjects, unchanged search crops and retained failure records across retries. These are offline checks; the revised crop/framing workflow has not yet been retried against the cloud service, and no fresh Claude end-to-end scene test was run.

The generation record persists a stable project id, run id, canvas rows and job/output ids. Resume requires checking the current Save to project before submission. Library status tracking supports several plan entries reusing the same asset. The offline tests do not verify cloud-side execution or current model availability.

Placement uses run-owned entity Empties with separate geometry groups. Support entities do not inherit geometry-only scale edits. Complete imported instances retain their parts, and fallback duplicates share mesh data while keeping independent object transforms. These checks run in a fresh background Blender process using `tests/blender/scene_placement_smoke.py`; they do not modify an artist's open scene or call Marso. The suite covers scaling, reruns, multiple projects, multipart/nested imports, placeholders and cameras.

Validation on 2026-10-28: 391 scene script tests passed; all ten skills passed frontmatter checks; 58 package-local links and 23 command-line helpers were checked in isolated skill copies. Eight native placement checks passed in Blender 4.5.1 LTS and 5.2.0 LTS, including save/reopen and object renaming.

The hierarchy is a foundation for future USD Xforms, not a USD exporter or physics validator. Placement remains an estimate from photographs; support contacts, imported dimensions, mesh orientation and rig/physics behaviour need review. No fresh end-to-end OpenAI/Claude host trial or live cloud regression was performed for this revision. These scene features remain a development preview requiring the supporting add-on; this limitation does not restrict access to the public collection.
