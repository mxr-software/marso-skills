# Contributing agents

- Skills live at `skills/<application>/<skill-name>/SKILL.md`; application-independent entry skills use `skills/core/<skill-name>/SKILL.md`. Keep required runtime references inside their skill folder.
- This repository owns workflow instructions, not the Blender add-on or MCP implementation. Report implementation gaps; do not invent commands to bridge them.
- Check instructions against the relevant application source and current tool schemas. Record the inspected version and distinguish source review from execution testing in `docs/compatibility.md`.
- Keep the common skill body usable by ChatGPT, Codex, Claude desktop, and Claude Code. Put optional client metadata in `agents/`; do not require a client-specific tool prefix.
- Default Blender route: official Blender MCP plus the Marso add-on. Hosted Marso MCP is optional. Preserve a working user-selected route.
- Keep asset modelling independent of texturing. Modular kit creation and composition are in scope; general scene dressing is deferred. Add only developed skill folders.
- Keep kit connectors, reusable surfaces and material roles intact across texturing. Do not invent an add-on option to preserve hidden-face UVs.
- Do not introduce pricing checks, spending allowances, or extra credit confirmation steps. Setup validation uses non-generating operations.
- Preserve explicit generate-versus-model intent. Default organic/complex forms toward generation and structured, articulated or modular geometry toward agent modelling. Select generators from live capabilities and user preferences; do not invent comparative quality rankings.
- Style variants branch from one preserved original/prepared source, not sequential Restyle outputs. Preserve material names during jobs; assign descriptive local names only after map application. The future texture system and automatic refinement loops are deferred.
- Use progressive disclosure: short entry points, conditional references, and observable completion criteria. Avoid duplicating application manuals or tool schemas.
- Validate frontmatter, local links, standalone packaging, and relevant acceptance cases. State which live checks were not run.
- Keep credentials, account identifiers, machine-specific paths, downloaded add-ons, and customer data out of this public repository.
- Publish reusable instructions and concise compatibility limits. Keep scene-specific trial journals, prototype builders, service snapshots and raw evidence local under `.local-tests/` or the explicitly ignored legacy trial paths. Tests are maintainer verification, not runtime skill dependencies; package only the selected leaf skill folder.
- Keep internal research notes in ignored local storage. Public documentation should describe Marso's workflows and supported integrations. Preserve any legally required third-party attribution.
