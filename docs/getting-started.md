# Your first Marso project

Marso skills are publicly available for anyone to install and use. [Install the complete collection](installation.md#install-the-complete-collection) from `main`, then describe what you want to create. The `marso` entry skill helps your assistant choose the relevant workflow; you do not need to memorise the skill names.

## Connect once, then describe what to build

Start with: "Use marso-blender-setup to check my Blender connection and configure the Marso add-on."

The assistant checks Blender access, the add-on and account configuration, and the appropriate Marso Studio project. It should explain any missing prerequisite and how to resolve it. Enter credentials in the add-on rather than in chat. Setup itself does not generate assets.

Then give the assistant your brief, for example:

> Use Marso to model an editable wooden cabinet, 1.2 metres wide, with separate doors. Texture it as worn walnut with dark steel handles. Keep the doors independently movable and save the Blender file.

Say **model** when you want editable, structured geometry; say **generate** when you want Marso's generative 3D workflow. You can also ask to restyle an existing object, build a modular kit from references, or assemble a kit you already have. Include dimensions, reference images and finish details when available. The assistant should choose the relevant skills, inspect the results and deliver the saved file with any remaining issues.

For newly modelled assets, the assistant shows neutral-clay previews and waits for you to approve the model before Marso texturing. You can request geometry changes at that point, or explicitly ask it to proceed without review. Existing assets you directly ask to retexture do not need an extra model-approval step.

The public collection covers setup, asset modelling, texturing, modular kits and scene workflows. Use Marso 1.12.1 with Blender 5.2 as the public baseline for the Blender scene commands. Start with the [Blender connection guide](blender-setup.md), then try the [learning prompts and advanced recipes](workflows.md).

## Start with a small task

Use a separate test scene or a copy of your asset. You need Blender, the Marso add-on with a working account, and an assistant connection that can actually inspect and control Blender. Begin by asking the setup skill to verify those prerequisites without generating anything. A skill upload alone does not supply that connection.

Try these in order, reviewing the saved result at each step:

1. "Use marso-blender-asset to model a simple wooden stool at real scale. Keep it editable and save the Blender file."
2. "Use marso-blender-texture to texture this stool with Marso as aged oak. Preserve its geometry, check unique non-mirrored UVs, and inspect the result from above and below."
3. "Use marso-blender-kit to build a three-part wall kit: straight panel, doorway and corner. Plan the joins and retain surfaces that could be exposed in another arrangement. Texture the masters with Marso, then use marso-blender-compose to make two different layouts."

For the new guidance, try "Give my stool three finishes, each from its original source, and name the materials clearly," then "Add a matching component using the saved appearance brief." Check that the original remains unchanged and every style has independent material bindings. Also test explicit "generate" versus "model" requests: organic generation and structured/articulated/modular modelling should take different routes. Live cloud style-variant generation and comparative generator quality are not yet validated by this repository's trials.

## Review the result

Local Blender checks cover modelling, UV preparation, source-colour baking, connection helpers, material application and real Retexture/PBR operations. These do not establish fresh-user success on every assistant client or certify the artistic quality of a new asset.

Fresh-client execution, official Blender MCP transport and API-host integration are not yet fully verified. Follow the [installation instructions](installation.md) for your host; Claude can install the collection as a plugin, while other hosts have separate routes. See [compatibility](compatibility.md) for the verification boundaries.

Texture output needs artistic review. Check one representative part in neutral clay, inspect its baked material regions, then inspect the generated front, oblique and rear views before extending a kit. Matching prompts do not guarantee aligned patterns or correct material boundaries. Report warnings and defects even when a job succeeds.

## Send useful feedback

Record the repository commit, assistant/client, Blender and Marso add-on versions, connection used, original request, expected result and actual result. Include the point where you intervened, any error or quality warning, and screenshots of both the individual part and assembled result where relevant. Distinguish setup failure, assistant decisions, UV/geometry problems and generated appearance quality. Share files only when you have permission; remove credentials and private account information from logs. Use your agreed feedback channel or a GitHub issue for non-sensitive reports.
