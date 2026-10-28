# Compatibility

Reviewed 2026-10-27. Format compatibility, available application tools and successful end-to-end execution are separate checks.

## Shared skill format

All eight packages use the [Agent Skills format](https://agentskills.io/specification): a leaf folder named after the skill, a `SKILL.md` with `name` and `description`, and supporting files inside that folder. Optional `agents/openai.yaml` supplies OpenAI UI metadata; the workflow does not depend on it. The same instructions are used by OpenAI- and Claude-based hosts.

The repository's `skills/core/` and `skills/blender/` directories organise source. They are not themselves installable skills. Follow [installation](installation.md) to place each leaf folder in the client's discovery directory or attach it through its API. No published marketplace/plugin bundle is included.

| Host | Loading route | Verification boundary |
| --- | --- | --- |
| Codex | `.agents/skills/<skill-name>/SKILL.md` | Format/package and isolated installation checks passed; fresh-client Blender workflow not yet verified. |
| Claude Code | `.claude/skills/<skill-name>/SKILL.md` | Format/package and isolated installation checks passed; fresh-client Blender workflow not yet verified. |
| OpenAI API agent | Supported skill attachment or local runtime loading | Host must expose the skill files and the required application tools; live API integration not tested here. |
| Claude API agent | Custom skill upload/attachment or host-managed skill loading | Host must expose the required application tools; live API integration not tested here. |
| ChatGPT / Claude desktop | Client's supported custom-skill or plugin workflow | Availability and application access depend on the client/account; fresh installation remains unverified. |

The repository is an artist pilot. Structural validation does not certify model behaviour or photorealistic output.

The Skills CLI discovered the six Blender and entry skills and installed them into isolated Codex and Claude Code project directories. All twelve installed copies matched their source resources. Frontmatter, standalone ZIP packages, package-local links and public repository links passed validation. This checks distribution and file accessibility, not live model execution.

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

`marso-scene-decompose` and `marso-scene-graph` need a host that can run shell commands, Python 3.10+ with Pillow, and an assistant that can look at local image files. They use no network, account or application connection. They are licensed separately (see each folder's `LICENSE.txt`).

Checked on 2026-10-28:

- Script tests (`python -m unittest discover tests/scene`) pass, covering intake, tiling, the tile merge, verify, matching, the graph, the viewer, the asset plan and the crops.
- Blind runs in Claude Code: a fresh agent given only the installed skill folders and a one-line request, on four photographs of one kitchen (Fine mode, helper agents in parallel with a host cap of 20). Four decomposition runs and one asset-planning run were reviewed against the photographs. Each fixed what the previous one exposed: duplicate objects at tile seams, a support tree broken by a loop, a gallery that failed on large runs, names guessed at wide-shot scale surviving as separate objects and assets, and asset routing and counting errors.
- On the last run the graph validated, the viewer opened and was clicked through, and every heavily hidden object carried a context-built description.

Not checked: Codex, ChatGPT and API hosts; serial execution on a host without helper agents; Coarse mode on this set; scenes other than one kitchen; handing reference briefs to generation. Detected names and boxes remain model readings: the verify round and the match round reduce misnamed and duplicated objects but do not remove them, and some boxes stay loose.

## Scene generation and placement in Blender

`marso-blender-scene-assets` and `marso-blender-place-scene` drive the Marso add-on's scene bridge commands (`scene_reference`, `scene_mesh`, `mint_status`, `import_scene_asset`, and `find_in_library` for the library check) through the official Blender MCP. They are licensed separately (see each folder's `LICENSE.txt`).

These commands come from add-on development builds that are not yet released: the scene commands from the `feature/scene-assets` branch of the add-on, and `find_in_library` from `feature/library-search` (both on the 1.8.0 manifest; sources `marso/services/scene_assets.py`, `marso/services/semantic_search.py`, `marso/bridge/handlers.py`). The released 1.8.0 add-on has none of them; the skills report a missing command and stop. `find_in_library` calls `POST /mcp/library/search/text` and `POST /mcp/library/search/image`, which the service answers but its published API description does not list.

Checked on 2026-10-28:

- Script tests (`python -m unittest discover tests/scene`) cover the generation record (`manifest.py`), the layout (`layout_plan.py`), the asset plan's polygon budget and routes, and the reference prompt.
- `place_in_blender.py` was run in Blender 4.5 in background mode on a fixture: hierarchy, linked duplicates, bottom-centre placement, camera and a repeated run.
- Live in Blender 5.2 with the development add-on, driven by the maintainer in Claude Code (not a blind run): one kitchen, twelve assets through a new Studio project. Reference images from crops (one regenerated after review), Tripo meshes at 40,000 polygons with PBR, all twelve minted, imported with linked duplicates and placed against the establishing photograph.
- Library check, live on the same account: each of the twelve, searched with its label and `search.png`, came back with its own library asset first (ten as match or possible, two as weak); reuse, `mint_status` and import were run without generating anything.

Not checked: a blind run of either skill; Codex, ChatGPT and API hosts; a second scene; placing objects seen only in photographs that share nothing with the establishing view. Placement is a first layout from one photograph, and minted sizes are taken as they come (one table minted at the height of a coffee table). Library verdict thresholds were set on one account's library.
