# Compatibility

Reviewed 2026-10-28. Format compatibility, available application tools and successful end-to-end execution are separate checks.

## Shared skill format

All ten packages use the [Agent Skills format](https://agentskills.io/specification): a leaf folder named after the skill, a `SKILL.md` with `name` and `description`, and supporting files inside that folder. Optional `agents/openai.yaml` supplies OpenAI UI metadata; the workflow does not depend on it. The same instructions are used by OpenAI- and Claude-based hosts.

The repository's `skills/core/` and `skills/blender/` directories organise source. They are not themselves installable skills. Follow [installation](installation.md) to place each leaf folder in the client's discovery directory or attach it through its API. No published marketplace/plugin bundle is included.

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

Validate each complete skill in isolation: frontmatter, package-local links, optional metadata and bundled scripts. Use [setup cases](../tests/blender/setup-cases.md) and [workflow cases](../tests/blender/workflow-cases.md) as acceptance criteria, not as a claim that every case has passed. The offline Blender checks in `tests/blender/` do not call cloud generation or validate client transport.

Detailed experiment journals, prototype scene builders and raw evidence are kept local. Installable skill packages contain only reusable workflow instructions and their supporting resources.

## Scene decomposition and asset planning

`marso-scene-decompose` and `marso-scene-graph` need a shell host, Python 3.10+ with Pillow, and local image inspection. They do not need an application or service connection. Each scene skill carries its own licence.

Offline tests cover intake, tiling, verification, matching, graph validation, viewer generation, asset planning and reference crops. Inputs with changed image hashes are refused when results already exist; start another run. Images from multiple folders retain their individual paths. Prior Claude Code trials informed the instructions, but cross-client behaviour, serial execution and visual generalisation remain unverified. Names, boxes, identities and dimensions are estimates that require review.

## Scene generation and placement in Blender

These workflows require a development Marso add-on exposing `scene_reference`, `scene_mesh`, `mint_status`, `import_scene_asset` and optionally `find_in_library`. Source reviewed at `2194155` on `feature/library-find-panel`, including `marso/bridge/handlers.py`, `marso/services/scene_assets.py` and `marso/services/semantic_search.py`. A 1.8.0 manifest alone does not establish those commands are present. Inspect live schemas and report unsupported commands; do not describe this as available in every released add-on. If library search is missing, the documented skip route is available with disclosure.

The generation record persists a stable project id, run id, canvas rows and job/output ids. Resume requires checking the current Save to project before submission. Library status tracking supports several plan entries reusing the same asset. The offline tests do not verify cloud-side execution or current model availability.

Placement uses run-owned entity Empties with separate geometry groups. Support entities do not inherit geometry-only scale edits. Complete imported instances retain their parts, and fallback duplicates share mesh data while keeping independent object transforms. These checks run in a fresh background Blender process using `tests/blender/scene_placement_smoke.py`; they do not modify an artist's open scene or call Marso. The suite covers scaling, reruns, multiple projects, multipart/nested imports, placeholders and cameras.

Validation on 2026-10-28: 391 scene script tests passed; all ten skills passed frontmatter checks; 58 package-local links and 23 command-line helpers were checked in isolated skill copies. Eight native placement checks passed in Blender 4.5.1 LTS and 5.2.0 LTS, including save/reopen and object renaming.

The hierarchy is a foundation for future USD Xforms, not a USD exporter or physics validator. Placement remains an estimate from photographs; support contacts, imported dimensions, mesh orientation and rig/physics behaviour need review. No fresh end-to-end OpenAI/Claude host trial or live cloud regression was performed for this revision. These scene features remain a development preview requiring the supporting add-on; this limitation does not restrict access to the public collection.
