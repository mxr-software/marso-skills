# The reference brief

One `brief.json` and one `crop.png` per asset, written by `crop_objects.py` into `<out>/<asset_id>/`. The brief is what an image or 3D generator is told; the crop is what it is shown. Together they must leave no doubt about which pixels are the subject.

## What the brief holds

- `subject`: the asset's label, description and category, and its real size in metres with the `size_basis` that produced it. Size is the one thing a crop cannot show, so it is always stated.
- `view`: the source `image_id`, the crop rectangle in source pixels, the crop's pixel size and the `pad` used.
- `subject_box`: the subject's box in the crop's own frame, pixels, origin top-left.
- `not_the_subject`: every other object whose box overlaps the crop. Each entry has the object's `global_id`, `label`, `role` (`child`, `parent`, `sibling-instance` or `other`), its `relation` to the subject where there is one, a `box` in the crop frame, and two fields the generator reads:
  - `sits`: `"resting on this object"`, `"this object rests on it"`, or `"shares the frame, unrelated"`.
  - `pixels`: `"blacked out"` or `"still visible"`.
- `masking`: `children_masked` and `parent_masked`, both false unless masking was asked for.
- `marking`: the subject's box is drawn on the crop as a red outline; `stroke_px` is its width.
- `prompt`: the text for an object-mode image node that is shown the crop as a linked image named `@crop`. See [the prompt](#the-prompt).
- `polygon_count`: copied from the plan when `--polycount` set one; see [polycount](polycount.md).
- `evidence_note`: the reminder that the crop is identity and camera evidence, not a pose.

Boxes in the brief are in the crop's frame, so a reader of `crop.png` can draw them without the manifest.

## The prompt

The prompt is written for an image-generation node in object mode whose linked input image is the crop, referred to as `@crop`. That route has no negative prompt and no mask field, so everything to leave out is said as an instruction. In order:

1. `Generate the <label> inside the red box in @crop, isolated, the whole object in full, upright, on a plain neutral background.`
2. The description, or, for a mostly hidden object, the inferred whole (below), which keeps what the decompose step wrote there.
3. Neighbours made as their own assets first: `Do not include the <neighbours>: each is made as a separate asset, even where it touches or joins the <label> in @crop.` A neighbour counts when another generate-route asset of the plan has at least half its box inside the subject's box (a power base under a kettle), or covers at least half of the subject's box without being more than eight times its size (the kettle over its base). Measured on whole boxes, not the parts the crop clips. Without this, a kettle came back with its base attached, because the base only "shared the frame" and the kettle's own description mentioned a base. The brief marks these entries `separate_asset: true`.
4. Other exclusions as instructions: `Leave out the <children>: they rest on it and are not part of it.`; `Only the <label>, not the <parent> it sits in.` (the verb follows the relation: sits on, hangs on, is fixed to, leans against); `Leave out the <others>: they only share the frame.`; then `Everything outside the red box is context, not part of the <label>.`, and, only when masking was asked for, that the black areas are removed objects.
5. The real size, with its basis.
6. When the crop is cut by the image edge, an instruction to complete the missing part.
7. That the visible side must match `@crop`, the unseen sides follow from it, and the crop's framing, pose, lighting and background are not copied; it ends `Do not draw the red box.`

If the route that receives the brief names its linked image differently, replace `@crop` throughout; do not remove the exclusions.

## Mostly hidden objects

When every photograph shows an object mostly hidden, the decompose step records `occlusion: "heavy"` and an `inferred_whole` on its node: what was actually `visible`, and a `whole_description` of the complete object built from context (a matching object elsewhere in the room, the visible parts, the setting, the usual form of that kind of thing), with the inferred parts named. The crop of such an object is a fragment, so the brief's prompt follows its opening line with that description: it says which part is visible, asks for the visible part to be matched exactly and the rest completed as described. `subject.inferred_whole` carries the same fields for a generator that reads structured input.

Two things come first, before relying on inference. If the asset has several members (an `instances` cluster or identity group), `plan_assets.py` already picks the least hidden member as the representative, so a chair half behind the table borrows its clearly seen twin's crop. If the representative is still mostly hidden, the plan flags it `mostly-hidden`, and `no-inferred-whole` when the decompose step left no description; review those with the user, who may have a better photograph.

## The red box, and optional masking

The default crop is unmasked: the subject, its neighbours, what holds it and what rests on it all stay visible, and the subject's box is drawn on it as a red outline (stroke about the crop's longer side / 180, at least 2 px). The outline says which object is meant; the prompt's `Leave out ...` and `Only the <label>, not the <parent> ...` sentences say what to exclude; the generator keeps the real context it needs to read material and scale.

Masking is opt-in, for a generator that keeps copying a neighbour despite the outline:

- `--mask-children` fills every child of the subject (and the children's children) with flat black: **the table without what is on it**.
- `--exclude-parent` blacks out the parent's box outside the subject's own box: **the onion without the bowl**.

A child whose box covers most of the subject (a kettle standing on its base) is never masked. The outline is drawn last, so masking never hides it. Record any masking in the review.

Anchors (floor, walls, ceiling) are left out of the list unless one is the subject's parent, since they span every crop. Objects that share the frame but are neither parent nor child are never masked; they are listed as `still visible` so the generator can be told to ignore them.

## Padding

`--pad` (default 0.15) adds a margin around the subject's box as a fraction of the box's longer side, clamped to the image edge. The margin shows the object's surroundings and the ground contact, which helps a generator judge scale and camera height. A truncated box (the object runs off the image) cannot be padded past the edge; the brief says so.

## Why the output must show the whole object

A crop is one camera's partial view. The subject may be cut by the frame, half hidden by a child, or seen only from above. The generator is asked for the complete object, upright, at the stated size, on a neutral background, with the visible side matching the crop and the unseen sides consistent with it. The crop fixes what the object is and what it is made of; it does not fix the pose, the framing or the lighting of the output. Say this in every brief, because a generator given a crop with no instruction will reproduce the crop.
