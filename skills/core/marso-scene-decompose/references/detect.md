# The detect pass

Read this when a brief names you as a whole-view or tile pass of the detect round, or when you are doing that pass yourself in a serial run. Everything you need is here and in the brief.

This pass finds the objects in one picture: each with a box, a description, a category, a size and **what it rests on**. It is fast on purpose. A script cut the photograph into pieces and will put your boxes back together, so you look once, write one file, and stop.

Hold this picture: everything downstream can only work with what you find here. Nobody can put a spoon on a place mat if nobody wrote the spoon down. Listing the furniture and stopping is the failure to fear.

## Hard rules

- Never edit the skill's files or an earlier pass's output. Write only the one file the brief names, never into the skill folder.
- **Boxes are four numbers between 0 and 1 of the picture you were shown, never pixels.** A tile pass's boxes are 0–1 of its tile; a script maps them onto the photograph, so never convert anything yourself.
- **Look once and write once.** No zooming, overlays or re-measuring: a script merges and checks your file and a person looks at the result.
- **Go surface by surface, not by sweep.** For everything that holds things, ask what is under, behind and between what you already listed. The misses are the covered things, not the small ones.
- **Every object says what it rests on.** `on` is the name of the thing it stands on, sits in or leans against; floors and walls have none. You saw it there, and nobody downstream can recover it from boxes.
- **What holds a thing is a thing.** A free-standing holder, stand, rack, hook, bracket or dispenser has its own entry. A handle that is part of another object stays part of it.
- **A container and its contents are separate** when a 3D pipeline would build them separately: a vase, its stems and its water; a caddy and its shakers. Not the oil in a sealed bottle.
- **Count repeated things one by one.** Two shakers are two objects, never one called "shakers".
- **Use the shortest common name, the same one every time.** "wishbone chair", "red onion", three words at most; colour and detail go in the description. The match round pairs objects across photographs by name, and two passes calling one thing different things is what stops it.
- **Name only what the scale supports.** A shape a few pixels across is a shape: say what you see and set `id_confidence` to `low`. Never write a brand or model you cannot actually read.
- A graphic printed on an object, a shadow, a reflection and glare are not objects. A view through a window is a region: record the window, not what is beyond it.
- Never hand back a near-empty list because the picture was hard. Say what defeated you and give what you have.

## Which pass you are doing

| Pass | You are shown | You record | Writes |
|---|---|---|---|
| **whole** | the whole photograph, downscaled | the anchors (floor, walls, ceiling) and every large thing: furniture, appliances, built-in cabinet runs, worktops. Boxes need not be tight: a few hundredths out does not matter at this size | `parts/<image_id>.whole.json` |
| **tile** | one native-resolution crop of one part of it | everything smaller, including small surfaces (a placemat, a tray, a laptop). Not floors, walls or whole large furniture. An object the crop edge cuts: box what you see, and leave it out if under a third is visible, because the neighbouring crop has it | `parts/<image_id>.<tile_id>.json` |

A photograph small enough not to be tiled, or a Coarse run, has only a whole-view pass, and then you record **everything**.

## What you write

One JSON file, in this shape. The top-level key is **`objects`**.

```json
{
  "schema": "scene-decompose/detections@1",
  "image_id": "img003",
  "tile_id": "t2",
  "objects": [
    {
      "label": "signet ring",
      "description": "gold band with a dark oval stone, lying flat",
      "category": "jewellery",
      "bbox": [0.5934, 0.5856, 0.617, 0.6185],
      "size_m": 0.022,
      "size_basis": "about a sixth of the headphone earcup beside it",
      "id_confidence": "high",
      "on": "woven placemat",
      "relation": "on-top-of",
      "surface": false
    }
  ]
}
```

| Field | | |
|---|---|---|
| `label`, `bbox`, `category`, `size_m`, `size_basis` | required | `size_m` is the largest real dimension in metres; the basis names what you scaled it against, never empty |
| `description` | short | colour, material, state: what the label leaves out |
| `on` | for everything but floors and walls | a name, as you would call it, e.g. `"oak dining table"` |
| `relation` | when it is not simply resting on top | `inside` (in a bowl, vase, caddy), `hanging-on`, `leaning-against`, `attached-to`, `under`, `part-of`; `on-top-of` is the default. [relations.md](relations.md) explains each |
| `surface` | `true` if other things sit on or in it | tables, mats, trays, worktops, a laptop, a caddy |
| `id_confidence` | `low` when the name is a guess | `high` if you leave it out |
| `occlusion` | when anything hides part of it | `partial`, or `heavy` when about half or more is hidden or the parts that define its shape are. `none` if you leave it out |
| `whole_description`, `visible` | required with `heavy` | see "Heavily hidden objects" below |
| `note` | optional | |

### Heavily hidden objects

A later step generates a 3D asset of each object from its crop and a written prompt. When most of the object is hidden, the crop shows too little, and the prompt has to carry the rest. So for every `heavy` object write two more fields:

- `visible`: the parts you can actually see, in a few words ("top rail and one back spindle").
- `whole_description`: the complete object as it most likely is, in one or two sentences a generator could work from: overall form, parts, materials and finish. Build it from context, strongest first: an identical or matching object elsewhere in the photograph (a chair of the same set, the other shaker), what the visible parts imply, the setting and style of the room, and the usual form of that kind of object. Say which parts are inferred and from what: "spindle-back oak dining chair; seat, legs and lower back hidden by the table, assumed to match the chair at the head of the table".

Never present an inferred part as seen, and never let the context change what the visible parts show. If nothing in the photograph informs the hidden parts, say the usual form is assumed.

Leave `tile_id` out of a whole-view file.

**Categories:** `furniture`, `architecture`, `appliance`, `fixture`, `tableware`, `kitchenware`, `container`, `electronics`, `jewellery`, `accessory`, `decor`, `plant`, `food`, `paper`, `textile`, `personal-care`, `tool`, `other`. Pick the closest. A built-in appliance is `appliance`; a run of cabinets is one `architecture` object. Anchors (floor, wall, ceiling) are `architecture` and are boxed at their full visible extent.

## Workflow

1. **Look** at your picture. Work through it region by region, listing every object you can see, and give each a box as you go.
2. **Look again at each surface** for what is under, behind and between what you listed, and for anything cut by the edge. Add what you find. If a surface gives nothing new, that is a real result. Give every heavily hidden object its `visible` and `whole_description`.
3. **Write** the file and reply with one line: how many objects.

That is the whole pass. The lead's script then merges every pass, drops what two crops both found, joins what a seam cut in two, works out the tree from your `on` names and checks the result.
