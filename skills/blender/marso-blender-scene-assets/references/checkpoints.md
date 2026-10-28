# Review checkpoints

The run stops twice for the user. Each stop is a full stop: end the turn with the question, and start no job until the user answers. When the user is unreachable and told you to continue alone, make the call yourself, record it with `manifest.py review --note "decided by the assistant: ..."`, and say so when you deliver.

## Checkpoint 1: the asset plan

Before any job, show:

- the Studio project name and whether it already exists;
- how many assets will be generated, the instance range, and the settings (model, polygon budget per asset, texture);
- every asset `manifest.py init` left out, and why (modelled, reused, skipped, no crop);
- every flagged asset in the plan, with its flag.

Ask the user to confirm or change the list. Changes go into `asset_plan.json` and its `review` list; re-run the crop step for a changed asset, then `manifest.py init --force`.

## Checkpoint 2: the reference images

When every listed reference job has finished, show each `image_path` beside its `crop.png`, with the asset id and label. For each, the user approves or rejects. Look for:

- the wrong object, or two objects merged into one;
- a child, the parent or a neighbour drawn into the image;
- the object cut off, posed oddly, or on a busy background;
- the wrong material, colour or proportions against the crop.

Record the answer: `manifest.py review runs/<job>/assets.json --approve a001 a004 --reject a002 --note "the bowl, not the fruit in it"`. For a rejection, work the user's note into the prompt as an instruction, start a new `scene_reference` job and return to this checkpoint for that asset only. Approved assets can go on to meshes while rejected ones are redone.

There is no stop after the meshes; the placement step's review covers how they look in the room. Report the minted state at the end.
