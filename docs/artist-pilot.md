# Artist pilot

Use the `development` branch and choose a bundle from the [installation guide](installation.md#choose-by-outcome). Install all five Blender folders for the complete workflow; add `marso` to test generation-versus-modelling decisions. This pilot is intended for a small group of artists who can inspect Blender results and report where the assistant needs help. The repository is public; sharing it with selected testers does not restrict who can read it.

## Start with a small task

Use a separate test scene or a copy of your asset. You need Blender, the Marso add-on with a working account, and an assistant connection that can actually inspect and control Blender. Begin by asking the setup skill to verify those prerequisites without generating anything. A skill upload alone does not supply that connection.

Try these in order, reviewing the saved result at each step:

1. "Use marso-blender-asset to model a simple wooden stool at real scale. Keep it editable and save the Blender file."
2. "Use marso-blender-texture to texture this stool with Marso as aged oak. Preserve its geometry, check unique non-mirrored UVs, and inspect the result from above and below."
3. "Use marso-blender-kit to build a three-part wall kit: straight panel, doorway and corner. Plan the joins and retain surfaces that could be exposed in another arrangement. Texture the masters with Marso, then use marso-blender-compose to make two different layouts."

For the new guidance, try "Give my stool three finishes, each from its original source, and name the materials clearly," then "Add a matching component using the saved appearance brief." Check that the original remains unchanged and every style has independent material bindings. Also test explicit "generate" versus "model" requests: organic generation and structured/articulated/modular modelling should take different routes. Live cloud style-variant generation and comparative generator quality are not yet validated by this repository's trials.

## What has been tested

Local Blender checks cover modelling, UV preparation, source-colour baking, connection helpers, material application and real Retexture/PBR operations. These do not establish fresh-user success on every assistant client or certify the artistic quality of a new asset.

Fresh-client execution, official Blender MCP transport and API-host integration still need pilot feedback. Follow the [installation instructions](installation.md) for your host; no published plugin is included. See [compatibility](compatibility.md) for the verification boundaries.

Texture output needs artistic review. Check one representative part in neutral clay, inspect its baked material regions, then inspect the generated front, oblique and rear views before extending a kit. Matching prompts do not guarantee aligned patterns or correct material boundaries. Report warnings and defects even when a job succeeds.

## Send useful feedback

Record the repository commit, assistant/client, Blender and Marso add-on versions, connection used, original request, expected result and actual result. Include the point where you intervened, any error or quality warning, and screenshots of both the individual part and assembled result where relevant. Distinguish setup failure, assistant decisions, UV/geometry problems and generated appearance quality. Share files only when you have permission; remove credentials and private account information from logs. Use your agreed feedback channel or a GitHub issue for non-sensitive reports.
