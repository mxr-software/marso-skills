---
name: marso-scene
description: "Build or finish a complete scene from photographs, a prompt or an existing layout. Coordinate concepts, blockout, asset choices, placement, Marso materials and library reuse."
license: Apache-2.0
---

# Build a complete scene

Own the requested outcome across stages; discover installed companions by name. For image-only, decomposition-only, blockout-only or an existing-scene render request, use that specialist and stop at the requested scope. Skills supply instructions, not connections. In Blender, inspect and use the working Marso add-on first. Do not assume a separate hosted Marso MCP is installed or silently switch to it for concept work. Report missing add-on operations and continue supported stages; another connection is optional only when already part of the user's chosen workflow.

## Establish the route

- **Photographs:** inspect real views and dimensions; use `marso-scene-decompose` for the inventory and `marso-blender-blockout` for a coherent room shell and reference cameras. Generated reverse views are proposals, not evidence of hidden architecture.
- **Prompt:** use `marso-image` to generate one anchor concept in the relevant Studio project by default. A list of desired objects alone is not a settled design; that exception needs an accepted layout/visual direction or an explicit instruction to build directly. Skip concept generation for a settled design, a direct blockout request, or an unavailable/declined image route. Read [concept exploration](references/concepts.md) before probing details or alternative views.
- **Existing layout:** preserve accepted assets, shell, corrections and project; build only what remains requested. Do not restart with a concept merely because this skill was selected.

Use a single run record with input provenance, project, scene intent, quality/use, source revisions, decisions and unresolved items. Reuse the existing graph/asset-plan/import/placement records rather than inventing another orchestration system. A proposed plan, user approval and completed operation are distinct facts.

## Build and finish

1. Establish room scale, major masses, openings and intended views. In Blender use `marso-blender-blockout`. Ordinary wall corners default to 90 degrees in plan, with evidence-based exceptions. Fit the camera before distorting the room to explain photographic perspective.
2. Inspect the blockout and continue without a user pause unless they requested sign-off or an important ambiguity needs their answer. A blockout-only request ends here. This is not approval to texture newly modelled final assets.
3. Use `marso-scene-graph` for the mixed asset plan, from a photographic graph or a direct design plan. Preserve explicit creation routes, reuse identified assets directly, and consider library candidates before making unnecessary replacements. Set scene-level resource targets and per-asset effort from intended views/function. Consolidate decisions requiring review; delegated routine choices are agent decisions, not fabricated user approvals.
4. Route modelled assets to `marso-blender-asset`, fitting components to `marso-blender-kit`, existing assets to `marso-library`, generated scene props to `marso-blender-scene-assets`. Keep the plan mixed. Honour preferred supported generation options. Break compound dressing groups into distinct reusable masters: a toolboard is not one modelling brief for the board and every different tool. Choose each master’s route separately: static hand tools can favour generation/reuse even when their rack is modelled. Give modelled masters a focused construction pass, and all masters isolated visual acceptance before repetition and final placement; a separate collection/root in the same file is sufficient. Repeated identical assets share an accepted master; packaging styles use the texture appearance-family workflow rather than separate meshes for every label.
5. Place and dress through `marso-blender-place-scene`, preserving the accepted shell and entity ids. Replace proxies beneath their owning geometry groups. Check support, contact, orientation and necessary access clearance, especially after size/pose changes. An object list or placeholder scene is not a completed build.
6. Newly modelled geometry needs useful previews and user approval before Marso finishing unless explicitly waived. Respect existing unchanged approvals and requested batch review gates. For visible assets needing new appearances, use `marso-blender-texture`: Retexture continues directly to PBR. Preserve satisfactory PBR on reused/generated assets; do not retexture every object automatically.
7. Inspect geometry, material response and requested views. An attractive room view does not replace individual master acceptance: retain compact isolated views for distinct assets and inspect scene contacts separately. Report proxies and unfinished masters as unresolved even when small in the room image. Save the scene and dependencies; deliver lightweight reviews by default. Use `marso-blender-render` for realistic lighting/review, and `marso-blender-camera` for requested camera work. Final high-quality stills or sequences require that output scope; scene creation alone does not request a film.

## Continue and reuse

Follow native jobs/batches without duplicating submissions; continue independent work while review/service steps wait. Do not assume a server-side dependency trigger or automatic chat wakeup. Reconcile existing job identities on resume.

Keep each portable master independent of its scene placement. Record supported source/result ids and useful descriptive style/material labels. Verify mint/library availability when required, then reuse the completed result in later scenes; a local save or completed request alone does not prove search availability. Existing library masters may already satisfy the brief.

Report every selected item as completed, reused, deliberately excluded or unresolved. Distinguish technical completion, visual acceptance and library availability. Missing tools or known visible defects are scoped limitations, not reasons to silently substitute another product or lower the quality target.
