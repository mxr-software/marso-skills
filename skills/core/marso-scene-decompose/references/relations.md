# The relation vocabulary

Read this when a placement is not obvious. These eight are the whole vocabulary: no others, and no new names. Almost everything really does rest on something; where nothing fits, use `unknown` and say why in `note`.

## Why every relation has a physical meaning

The hierarchy is read by something that has to place these objects: a 3D scene, a simulator, a generator making reference images. A relation that only says two things are related is no use to any of them. So each one below says what contact it implies, what the parent gives the child, and what that constrains.

## The eight relations

| Relation | Contact | What the parent gives the child | Constrains |
|---|---|---|---|
| `on-top-of` | resting on the parent's upper surface | a support plane and its height | child's base sits on that plane; free to move within it |
| `inside` | contained by the parent's volume | an enclosing volume | child is within it; may be hidden; no support plane implied |
| `hanging-on` | hung from a vertical face, or from a rail, handle or hook on another object; weight carried by the fixing | a vertical plane or fixing, and a height | child hangs from that point at that height |
| `leaning-against` | touching a vertical face, weight on the ground | a vertical plane, with the floor taking the weight | base on the floor, top against the plane, tilted |
| `under` | below, touching lightly or not at all | a volume overhead | child's position in plan matches the parent; its height is below |
| `attached-to` | rigidly fixed, at any angle | a mounting face and an orientation | child is rigid to the parent and moves with it |
| `part-of` | not a separate object at all | identity | the child is a component of the parent, not something to place or generate separately |
| `unknown` | you could not tell | nothing | record it honestly; the viewer shows it as unresolved |

Two things side by side on a table are both children of the table, not of each other. Being near something is not a relation.

## Choosing between the ones people confuse

**`inside` or `part-of`?** Would you ever pick this up and move it on its own? A spoon in a drawer is `inside`. The drawer's handle is `part-of` the drawer. This matters: `part-of` is how a 3D step knows a table's legs must not be generated separately, where `on-top-of` is how it knows the place mats must.

**`on-top-of` or `inside`?** Does the parent's volume enclose it, or does its surface hold it up? Fruit in a bowl is `inside`. A bowl on a mat is `on-top-of`. Shakers in a wire caddy are `inside`, because the caddy surrounds them even though it is open at the top.

**`hanging-on` or `leaning-against`?** Who takes the weight. A picture on a wall is `hanging-on`: remove the wall and it falls. A board propped against the wall is `leaning-against`: remove the wall and it slides, but the floor was already carrying it.

**`attached-to` or `on-top-of`?** Would it stay put if the parent were turned upside down? A tap on a worktop is `attached-to`. A kettle on a worktop is `on-top-of`.

**`under` or nothing?** `under` is for things whose only useful relation is that something is above them: a rug under a table, a box under a bed. If the thing above actually rests on it, that is the other way round.

**A built-in appliance in its housing** (an oven in a tall unit, an integrated fridge behind a door) is `attached-to` that housing, not `inside`: nobody lifts an oven out of its cabinet. An inset hob or sink is `attached-to` the worktop it is cut into.

**Something draped over a handle, rail or hook** that is itself part of another object (an oven glove over the oven door handle, a tea towel over a rail) is `hanging-on` the object that handle belongs to.

**Tucked under or pulled up to something?** A chair pushed under a table, a bin under a worktop: the floor holds its weight, so the floor is the parent with `on-top-of`.
