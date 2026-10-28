# The reference brief

One `brief.json` and one `crop.png` per asset, written by `crop_objects.py` into `<out>/<asset_id>/`. The brief is what an image or 3D generator is told; the crop is what it is shown. Together they must leave no doubt about which pixels are the subject.

## What the brief holds

- `subject`: the asset's label, description and category, and its real size in metres with the `size_basis` that produced it. Size is the one thing a crop cannot show, so it is always stated.
- `view`: the source `image_id`, the crop rectangle in source pixels, the crop's pixel size and the `pad` used.
- `subject_box`: the subject's box in the crop's own frame, pixels, origin top-left.
- `not_the_subject`: every other object whose box overlaps the crop. Each entry has the object's `global_id`, `label`, `role` (`child`, `parent`, `sibling-instance` or `other`), its `relation` to the subject where there is one, a `box` in the crop frame, and two fields the generator reads:
  - `sits`: `"resting on this object"`, `"this object rests on it"`, or `"shares the frame, unrelated"`.
  - `pixels`: `"blacked out"` or `"still visible"`.
- `masking`: which direction was applied, `children_masked` and `parent_masked`.
- `prompt`: a plain-language paragraph built from the above for a generator that takes text, ending with the whole-object instruction below.
- `evidence_note`: the reminder that the crop is identity and camera evidence, not a pose.

Boxes in the brief are in the crop's frame, so a reader of `crop.png` can draw them without the manifest.

## Mostly hidden objects

When every photograph shows an object mostly hidden, the decompose step records `occlusion: "heavy"` and an `inferred_whole` on its node: what was actually `visible`, and a `whole_description` of the complete object built from context (a matching object elsewhere in the room, the visible parts, the setting, the usual form of that kind of thing), with the inferred parts named. The crop of such an object is a fragment, so the brief's prompt leads with that description: it says which part is visible, asks for the visible part to be matched exactly and the rest completed as described. `subject.inferred_whole` carries the same fields for a generator that reads structured input.

Two things come first, before relying on inference. If the asset has several members (an `instances` cluster or identity group), `plan_assets.py` already picks the least hidden member as the representative, so a chair half behind the table borrows its clearly seen twin's crop. If the representative is still mostly hidden, the plan flags it `mostly-hidden`, and `no-inferred-whole` when the decompose step left no description; review those with the user, who may have a better photograph.

## The two directions

The default is **the table without what is on it**: every child of the subject (and the children's children) is filled with flat black. The generator sees the table's material and legs, and a black hole where the fruit bowl was; the brief tells it the hole is a bowl that rests on the table, and to produce the table alone.

`--exclude-parent` adds **the onion without the bowl**: the parent's box is also blacked out, except for the subject's own box. The onion stays, the bowl around it goes. Use this when the parent's surface would otherwise read as part of the subject, such as a cushion on a chair or food in a bowl.

`--keep-children` turns off child masking. Use it when the children are tiny and masking would destroy the subject's surface, and say so in the review.

Anchors (floor, walls, ceiling) are left out of the list unless one is the subject's parent, since they span every crop. Objects that share the frame but are neither parent nor child are never masked. They are listed as `still visible` so the generator can be told to ignore them.

## Padding

`--pad` (default 0.15) adds a margin around the subject's box as a fraction of the box's longer side, clamped to the image edge. The margin shows the object's surroundings and the ground contact, which helps a generator judge scale and camera height. A truncated box (the object runs off the image) cannot be padded past the edge; the brief says so.

## Why the output must show the whole object

A crop is one camera's partial view. The subject may be cut by the frame, half hidden by a child, or seen only from above. The generator is asked for the complete object, upright, at the stated size, on a neutral background, with the visible side matching the crop and the unseen sides consistent with it. The crop fixes what the object is and what it is made of; it does not fix the pose, the framing or the lighting of the output. Say this in every brief, because a generator given a crop with no instruction will reproduce the crop.
