# Blind workflow checks

These are maintainer evaluations, not runtime instructions. Structural/unit tests cannot establish whether an agent discovers the right skill or handles a whole request.

Start a fresh agent without this repository's development chat, AGENTS.md or this rubric. Give it only the installed skill metadata, access to those skill folders, a user request and fixture context from `cases.json`. Let it choose which bodies/references to load. Simulate unavailable tools explicitly; do not present simulated operations as live results. Keep service mutations disabled for routing checks.

Ask for its chosen initial skill, concrete next actions, required questions, review/stopping points and final deliverable. Retain the transcript, files read, host/model/version and decisions under ignored local test storage. Grade after the run using the rubric below. Do not give the rubric to the tested agent. After an instruction failure, revise the smallest owning instruction and repeat the failed request with a fresh agent; also run adjacent requests to catch overcorrection.

## Rubric

| Case | Required behaviour |
| --- | --- |
| generate | Discovers generation directly; asks once about unknown preference, uses supported options and relevant project; does not claim an agent fallback is a saved user preference. |
| exact-reuse | Resolves the supplied id without replacement generation or redundant candidate selection. |
| complete-scene | Coordinates decomposition through planning, mixed creation, placement and finish; honours real review gates; saves scene and lightweight reviews. |
| decompose-only | Delivers graph/viewer without cloud generation or scene building. |
| remembered-options | Uses compatible recorded user preference over conflicting panel defaults, without repeating a polygon-budget interview. |
| scene-budget | Establishes one scene budget, shares repeated geometry/style sets, and does not silently exceed a hard cap. Does not guarantee VRAM fit from polygons. |
| explicit-model | Preserves modelling intent despite generator preferences; geometry review before texturing. |
| unsupported-preference | Explains mismatch, offers supported alternatives, preserves enduring preference; does not send unsupported options. |
| batch-recovery | Held item uses cancel/retry/reprepare, not review reject; reconciles original batch instead of duplicate submission; drains status pages. |
| material-names | Stable names while jobs run and with legacy name-based tracking; uses external labels instead. Independent styles use original source. |
| memory | Selects render/performance route, diagnoses sharing/images and measures changes; no blanket quality destruction or unsupported memory promise. |
| mixed-legacy | Keeps model/instance/kit out of generation; explains legacy mesh/PBR bundling; retains model approval and finished-scene scope. |
| appearance-families | Inspects shape compatibility, uses one master per family with blank distinct material regions, then independent appearances from that source; preserves placement/style identities. |
| shape-pack | Different weapon/shield silhouettes need different geometry; does not substitute an appearance grid. |
| identical-instances | Same chairs and same texture use ordinary shared instances without appearance-generation work. |
| grid-drift | Does not invent image-edit resolution controls or blindly crop moved subjects; verifies actual cells, rejects/repairs failures and pilots 3D transfer. |
| image-only | Discovers `marso-image`, edits and delivers images without starting mesh generation or Retexture. |
| airbrushed-sheet | Rejects visual quality despite layout success; improves material-specific image-edit direction, not merely source-render polish. Clean realism does not become indiscriminate dirt or damage. |
| wrong-master | Inspects actual family form and repairs proportions/construction before variants; uses complementary references where needed. Passing UVs, more radial segments or label keywords do not establish shape quality. |
| crop-resolution | Assesses actual crop detail, uses smaller sheets or individual images where appropriate; does not promise 4K PBR restores missing artwork or invent image controls. |
| retexture-brief | Keeps Retexture prose focused on material regions, finish and realistic detail; enforces geometry/UV preservation locally rather than relying on unsupported prompt instructions. |
| pbr-handoff | Continues directly to PBR, applies and inspects the final material under changed lighting; no unnecessary intermediate approval. Avoids duplicate PBR if the add-on already owns the chain. |
| conditional-pilot | Treats technical success separately from visual acceptance, diagnoses the affected stage and holds dependent expansion; does not lower the quality target or ask for approval of every variant. |
| transparent-packaging | Preserves the source, excludes/restores clear geometry or uses local transparent material/mask after finish transfer; protects opaque labels and reports local versus generated contributions accurately. |

The image/appearance cases added on 2026-10-30 are pending fresh-agent execution. Adding a case or passing package checks does not establish its behavioural result.

Score each case pass, fail or blocked, citing actual decisions. A blocked capability is not a pass for execution. Report routing simulation separately from live Blender/service tests and actual Claude/OpenAI host installation. Never infer cross-host success from one model family.
