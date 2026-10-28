# Contributing

Develop changes on a branch and review them before merging into `main`.

## Skill layout

A skill folder needs `SKILL.md` with YAML `name` and `description`, followed by its workflow. Add `references/` for conditional detail and `scripts/` only for a demonstrated need. The folder name and skill name must match.

Keep application installation steps in the setup skill. A task skill can identify a missing prerequisite and refer to setup without repeating its instructions. If a skill requires another installed skill, declare that dependency in the installation guidance.

Keep the shared frontmatter and instructions client-neutral. `agents/openai.yaml` is optional UI metadata; Claude and custom hosts must be able to use `SKILL.md` without it. Install/package the leaf skill folder, not the repository or its application grouping directory. Do not add duplicate Claude/OpenAI copies of the same workflow.

## Evidence

For changed instructions, inspect the corresponding implementation or official documentation. Record the version and source paths in [compatibility](docs/compatibility.md). A local development checkout is evidence of implementation, not proof of a deployed release.

Test the installed skill folder in isolation: it must not need a sibling repository or a developer's filesystem. Use the [setup acceptance cases](tests/blender/setup-cases.md) for changes to setup behaviour.

Publish general lessons and concise verification limits. Keep detailed trial journals, experiment-specific builders, asset files, account IDs and dated service-catalogue dumps in ignored local storage. Do not turn a successful fixture into a guarantee for a client or artistic result. Public test cases describe expected behaviour and are not instructions to execute during an ordinary user task.

For modelling, texturing and kits, use [workflow acceptance cases](tests/blender/workflow-cases.md). The local Blender smoke script checks the snapping helper and can probe a maintainer's add-on checkout without registering it or contacting Marso. It does not replace assistant-driven or cloud acceptance tests.

## Before submitting

- Validate the YAML frontmatter against the [Agent Skills specification](https://agentskills.io/specification).
- Check every relative Markdown link and optional metadata asset path.
- Confirm that only intended files enter any distributable skill archive.
- Exercise affected acceptance cases and record actual results, assistant/application versions, and outstanding checks.
- Keep source-reviewed, simulated, and live-tested outcomes distinct.

When Codex's skill-creator is available, its `quick_validate.py` also checks basic skill metadata and unfinished placeholders. That check does not establish whether the workflow works in Blender.
