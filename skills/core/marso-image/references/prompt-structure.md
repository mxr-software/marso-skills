# Descriptive prompts within the actual limit

Read the selected operation's schema and documented downstream limit. A bridge accepting a string does not prove the model accepts that length. Do not use one limit for image generation, editing and Retexture, or assume characters, bytes and tokens mean the same thing.

Build the prompt from a retained appearance/design brief, in this useful order:

1. Outcome and subject, or the specific edit.
2. Source roles and only essential preservation constraints.
3. Visible structure and distinct material regions.
4. A few observable realism cues appropriate to condition and image scale.
5. View/lighting appropriate to the operation, where supported.
6. Essential exclusions for likely failures.

This is an authoring convention, not a claim about every model's attention. Descriptive precision matters more than repeated adjectives. New objects can be realistic without dirt. Describe subtle lacquer variation, fabric yarn, pores, manufacturing transitions or contact wear where relevant, rather than adding the same scratches to every surface.

Scene concepts need spatial zones, landmarks, material palette and plausible lights. Close-ups need the named region and unchanged design identity. Alternate-view edits propose hidden areas; they do not prove geometry. Isolated mesh references need complete readable shape. Existing-mesh appearance images need the correct shape/region guide and rich finishes. Retexture needs concise region-specific material/condition detail, not camera, UV, polygon, export or grid instructions.

Check the actual submitted text after known reference expansion and enhancement. The optional [length helper](../scripts/prompt_budget.py) checks explicit codepoint, UTF-16-unit or UTF-8-byte limits and never truncates. Select the convention from the endpoint documentation; it cannot infer a service limit or count model tokens. If the tool performs unseen expansion, leave room and require its own final preflight. Keep raw submitted text and response with the run.

If over limit, remove duplicate context/adjectives first, then optional detail; compress wording while preserving intent, source roles, essential region distinctions and critical constraints. Never blindly slice. Split only along a genuine task/asset boundary if essential scope cannot fit. The maximum is a ceiling, not a target length.

For tests, keep source, model and supported settings fixed; record uncontrolled variation. Compare actual returned detail, shape stability, source-role compliance and final PBR transfer. A prompt that fits is not necessarily a good image, and one good result is not a universal quality guarantee.
