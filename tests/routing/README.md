# Blind workflow checks

These are maintainer evaluations, not runtime instructions. Structural/unit tests cannot establish whether an agent discovers the right skill or handles a whole request.

Start a fresh agent without this repository's development chat, AGENTS.md or this rubric. Give it only the installed skill metadata, access to those skill folders, a user request and fixture context from `cases.json`. Let it choose which bodies/references to load. Simulate unavailable tools explicitly; do not present simulated operations as live results. Keep service mutations disabled for routing checks.

Ask for its chosen initial skill, concrete next actions, required questions, review/stopping points and final deliverable. Retain the transcript, files read, host/model/version and decisions under ignored local test storage. Grade after the run using the rubric below. Do not give the rubric to the tested agent. After an instruction failure, revise the smallest owning instruction and repeat the failed request with a fresh agent; also run adjacent requests to catch overcorrection.

## Rubric

| Case | Required behaviour |
| --- | --- |
| prompt-workshop | Concept-first via a scene-capable operation; coherent shell, mixed routes, library reuse, model approval before finishing, lightweight completed-scene review. No unsolicited film. |
| compound-scene-masters | Separates grouped dressing into distinct master briefs, resolves and inspects each family before repetition, rejects primitive placeholders despite a plausible room view, and checks assembly contacts separately. Uses existing records/collections without mandatory separate files, agents or per-prop approval questions. |
| distant-scene-masters | Respects explicit distant-only scope; uses economical but plausible silhouettes and visible construction, with legible master inspection and scene contact checks. Does not impose hero detail, invisible mechanisms or independent work on every identical copy. |
| generated-tool-finishes | Chooses generation/reuse for suitable static tools independently of a modelled rack, inspects each distinct shape, then branches requested finish variants from accepted sources through Retexture and PBR. Continues an accepted pilot to the planned placement count and appearance distribution instead of delivering one of each. Does not generate per colour, substitute finishes for different geometry, promise articulation or share mutable materials accidentally. |
| reference-assortment-fidelity | Separates missing shape families from appearance variants and repeats. Plans distinct masters and reference-informed grouping, graduated sizes, orientation and supports; compares the populated group with the accepted concept before final rendering. Does not declare a matching instance total or rigid grid sufficient. |
| whole-scene-reference-coverage | Reconciles the whole reference with the work list, adds missing visible groups rather than treating absent plan rows as exclusions, preserves successful work, and requires a cheap coverage review before another final render. Does not treat technical success or a limitations list as completed reference matching. |
| scene-pilot-continuation | Updates the blockout's completion scope, inventories the whole concept before bulk work, separates stools from chair finishes, includes fixtures/contents/context, preserves accepted pilots and continues their full population. Uses early matched layout, master/finish pilot and populated-scene reviews; retains the model-approval boundary. Final still follows visual acceptance, not the old report or successful jobs. |
| render-existing-as-is | Renders the requested existing scene without importing the moodboard's missing props or changing composition. Does not turn reconstruction safeguards into scope expansion or an unnecessary approval gate. |
| scene-review-limit | Treats the iteration limit and technical success as inconclusive, diagnoses camera/occlusion and current visible support geometry, inspects newly exposed materials and returns unresolved issues to their owning stage. No blanket normal-map edits, repeated blind offsets or final-quality render labelled complete. |
| delegated-scene-reference-review | Honours delegated generated reference/mesh review on the legacy combined mesh/PBR path, rejects and corrects the cropped handle before meshing, retains accepted reference IDs and continues independent work. Newly modelled geometry still waits for user approval before finishing; no fabricated user approval or repeated image generation for an accepted reference. |
| photo-perspective | Fits camera before changing ordinary right-angle corners; continues after its own blockout inspection but does not invent final-model approval. |
| concept-only | Inspected images and provenance only; novel view labelled as proposal. No mesh, decomposition or PBR work. |
| blockout-only | Direct local shell/openings and useful review; no concept or texture jobs. |
| lighting-only | Render skill first; matched lighting previews preserve accepted mesh and material sources. No optimization campaign unless needed. |
| camera-smooth | Camera skill, no handheld noise; eased motion and clearance preview, explicit output settings and verified final render scope. |
| camera-handheld-pause | Two-second base hold, residual standing sway, speed-dependent walking motion, focus/clearance and real blur-segment review. |
| articulated-geometry-only | Explicit model route and functional parts/pivots despite small size; geometry review delivery, no unrequested texture approval question. |
| object-image-route-only | Recognizes object-mode limitation; no room prompt submitted as isolated-object work or private implementation calls. Reports unavailable concept route and continues useful local blockout with stated assumptions. |
| efficient-repeated-asset | Reuses valid session readiness; tests/repairs representative charts before expanding; previews packing before bake; uses bounded packing and targeted reruns. Still audits the full target, verifies actual upload and reviews final PBR. Does not bypass overlap failures, stack repeated generation UVs, promise a fixed cloud time or start a presentation render campaign. |
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
| cumulative-states | Preserves explicit progressive lineage and every endpoint, generates PBR per state, verifies correspondence and source selection, then authors a local control. Does not replace cumulative wear with siblings or claim the shader automatically exports. |
| alternative-finishes | Uses independent original-source branches and separate PBR appearances; does not add animation or cumulative damage without a request. |
| scene-without-detector | Uses local decomposition and graph skills; a missing optional detector does not block planning. Holds at the requested plan review before creation, then textures visible assets and provides lightweight reviews. |
| custom-builder-texture | Loads the texture workflow even inside a film or custom builder. Rejects coverage as proof, isolates rebuilt materials/images and verifies actual export scope before Retexture/PBR. Does not repeat approval for unchanged approved geometry. |
| repeated-pbr-only | Preserves existing colour and PBR-only intent, holds stacked generation UVs, prepares an independent atlas and rebakes colour or uses verified reusable masters. Does not flatten normal pixels or treat add-on version alone as validation. |

The image/appearance cases added on 2026-10-30 are pending fresh-agent execution. Adding a case or passing package checks does not establish its behavioural result.

The efficiency case added on 2026-11-01 is pending fresh-agent execution and does not establish a measured time reduction.

Score each case pass, fail or blocked, citing actual decisions. A blocked capability is not a pass for execution. Report routing simulation separately from live Blender/service tests and actual Claude/OpenAI host installation. Never infer cross-host success from one model family.

## Scene acceptance beyond routing

For complete-scene changes, also give a fresh reviewer a source image, actual intermediate render and the user's scope, without the implementation report or known gap list. Ask whether it is ready to deliver and what its next actions are. It must identify consequential visible omissions, not merely repeat this rubric or certify the scene from counts. Use a different scene for transfer checks when available; keep fixtures and visual assessments local. Repeat with a later render to check that the reviewer can accept an adequate interpretation without demanding invisible detail or exact reproduction of ambiguous generated pixels. Record routing, visual assessment and live construction separately. A text-only plan passing is not proof of an unattended end-to-end build.
