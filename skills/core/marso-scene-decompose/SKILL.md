---
name: marso-scene-decompose
description: "Decompose room or environment photographs into an object scene graph and interactive viewer. Identify objects, match them across views and review relationships before planning assets."
license: Proprietary. See LICENSE.txt in this skill folder.
---

# Decompose a scene

Turn photographs of one environment into `scene_graph.json`: every object found and described, boxed in each view it appears in, hung off physical anchors (floor, wall, ceiling) in a support hierarchy, and matched across views. Deliver it with per-view quality scores, a confusion list and `viewer.html`. Write the room down so completely that someone who has never seen it could rebuild it: the spoon as well as the table, and what the spoon rests on. Where two photographs disagree about whether they show the same spoon, say so rather than quietly picking one.

Needs a shell with Python 3.10+ and Pillow (`pip install Pillow`), and an assistant that can look at local image files. It uses no network access or API keys.

Scripts do the bookkeeping: cutting photographs up, putting boxes back, building the tree, pairing obvious matches, checking and building the viewer. You do the looking. Run scripts by full quoted path from the user's project folder; `<skill>` in the commands below stands for this skill folder's path, as in `python "<skill>/scripts/fast.py"`. Never change into or write inside the skill folder. If `python` is not found, try `python3` or `py -3`.

In shell examples, `python` means an installed Python 3.10+ interpreter. Check its version first; on Windows, use `py -3.13` or another installed compatible version if the default `python` is older. Blender-only scripts run in Blender instead.

## Hard rules

- Write only inside `runs/<job_name>/` in the user's project folder, including your own working files such as saved script output. Never edit this skill's files; report a workflow problem instead of patching around it.
- Boxes are `[x0, y0, x1, y1]` normalised 0–1 of the picture looked at, origin top-left; never pixels.
- Send each brief a script prints as it is. Do not rewrite briefs or add checks, passes or reviews the workflow does not ask for; they made an earlier version take an hour.
- One image or tile failing does not stop the run. Record it, carry on, and say what is missing.
- Every count you report must resolve to graph ids. Objects that may be the same thing are an identity group with a floor and a ceiling; give both numbers.
- Never upload the viewer, crops or photographs anywhere without a clear yes. They show the user's own space, and the viewer embeds them.
- Never report the job done without evidence: every phase ran, the graph validated, and you looked at each overlay.

## Start

Ask for the photographs if none were given; a folder means every image in it, non-recursive. `<job_name>` is lowercase-hyphenated from the user's words, else the folder name unless it is generic (`photos`, `images`), else what the photographs show (`kitchen`), else `scene`. One photograph is a normal job with no register or match round; say the result is one view with nothing to check it against. Above about twenty, offer to split by room.

```
python "<skill>/scripts/fast.py" start --run runs/<job_name> --images <files or folder>
```

It writes `manifest.json` and chooses a mode: **Fine** (each photograph tiled and looked at in detail, plus a whole view) up to four images, **Coarse** (each looked at whole) above four. Fine finds many more small objects; Coarse is faster and lighter. Tell the user the chosen mode, the trade and that `--mode fine|coarse` switches it, then carry on without waiting unless they asked to choose. Switching modes discards decomposition results and runs them again; say so first. Once an asset plan or downstream output exists, use a new run folder. Changed source images or changed tiling within a mode are refused when prior results exist: keep those results and start a new run rather than relabelling old detections. If Pillow is missing, ask the user to install it.

Every script prints JSON and exits 0 when clean, 1 when it finished but listed something for a person to look at (`flagged`, `problems`, `needs_retry`), and 2 when an input could not be read. Exit 1 is not a failure; read what it listed.

## Round A: detect

`python "<skill>/scripts/plan_fast.py" detect --run runs/<job_name>` prints a JSON object whose `agents` list has one entry per unit of looking (`register` for two or more images, then each image's whole-view and tile passes), each with a `name`, the `prompt` to send and the file it `writes`.

Where the host can start helper agents, start all of them together, one per prompt, and wait; if the host caps how many run at once, start as many as it allows and the rest as a second wave. Otherwise do each prompt yourself in turn, in the order printed, as if it were your whole task, and say the run was serial and slower. Each prompt names the reference to read: [detect.md](references/detect.md) or [register.md](references/register.md).

Then run `fast.py detect --run runs/<job_name>`. It merges each image's passes, builds its support tree, runs the gates and draws `qc/<image_id>.png`.

- `needs_retry` lists missing pass files. Run `plan_fast.py detect` again (it prints only those), do them, and run `fast.py detect` again. One retry; then carry on.
- **Look at each overlay once** and say what you saw. Check that boxes land on the picture, not shifted or squashed into a corner. A gross failure is a workflow bug: report it and stop.
- **Read each image's `anchors` list** (in the `fast.py detect` output, by id and name). Anchors should be floors, walls, ceilings, built-in cabinet runs and a few free-standing units; a built-in run has no anchor of its own when its photograph shows no floor. Ordinary objects there (a kettle, a cup) mean that image's support tree failed: report it as a workflow problem with the image id, carry on, and say so when you deliver.
- `flagged` lists what a script thought worth a look. Mention what matters; don't chase it.

## Round B: verify

`fast.py verify-plan --run runs/<job_name>` draws, for each photograph, sheets of every merged object as a numbered crop of the full photograph with its box and name, and prints one verify prompt per photograph. Do them as in round A; each points at [verify.md](references/verify.md). The verifier renames what is misnamed, removes what is not an object, marks duplicates and fixes plainly wrong supports; a wrong name left here becomes a duplicate object or an asset that does not exist.

Then `fast.py verify --run runs/<job_name>` applies the decisions, rebuilds each image's tree and redraws the overlays. It lists any photograph left unverified, and keeps the merged files it changed in `verify/` for comparison. Mention the renames, removals and duplicates when you deliver.

## Round C: match

`fast.py match-plan --run runs/<job_name>` pairs the obvious matches, makes contact sheets for groups it could not settle, and prints match prompts. If `count` is 0, go to the build. Otherwise do the prompts as in round A; each points at a brief file and at [match.md](references/match.md).

## Build and check

`fast.py graph --run runs/<job_name>` builds `matches.json`, `scene_graph.json`, `view_scores.json`, `confusion.json`, validates the graph and writes `viewer.html` with the photographs embedded. A refused merge listed under `problems` is the safe direction working.

Open `viewer.html` where you can: the tree is not blank, an object seen in two photographs is boxed on the right thing in both, a deep leaf is reachable from an anchor, and Gallery crops show what their captions name. If the browser refuses a local file, serve the run folder with `python -m http.server <port> --bind 127.0.0.1` from inside it, open `http://127.0.0.1:<port>/viewer.html`, and stop the server afterwards. If you cannot open a browser at all, say the viewer is built but unchecked and give the user that list. [schema.md](references/schema.md) describes every file and id; read [gotchas.md](references/gotchas.md) when a phase fails or a result surprises you.

The graph's `parent` and `relation` describe support, not physics or a required mesh-parent hierarchy. Downstream applications should use separate entity transforms and geometry groups so one object can be resized independently of its supported objects.

## Deliver

Give the output paths; the counts from the last `fast.py graph` output (objects, `matched_across_images`, `refusals`, identity groups each with floor and ceiling, and `physical_objects` as the scene's range of real things; the viewer's single "distinct" figure is the match round's best estimate inside that range), the objects with `occlusion: "heavy"` and whether each node carries `inferred_whole`; the `unconfirmed` count (wide-view readings the close-up never saw, probably misreadings); what the overlays showed; the time per phase from the last `fast.py` output (script time only; give the wall-clock total as well); the problems listed; and what is least certain. State which checks you did not run. Offer, without doing: publishing the viewer (only on a clear yes), re-running in the other mode, and planning assets from the graph with `marso-scene-graph` when installed.
