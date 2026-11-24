# Part families and finish variants

Read this when a kit has several parts that share sections or sizes, or when the same parts are wanted in more than one colour or finish.

## Scope the family first

Agree these before modelling, and record them in the `Marso Kit` text. With nobody to answer, choose and record them.

- **The part list.** A first kit of 10 to 20 parts in one family is workable. A blockout of many dozens of parts cannot be reviewed part by part; split it into families.
- **A triangle budget for each part,** taken from the kit's poly path and the part's size. Small fittings take a small share; a budget set only for the whole kit lets one part spend it all.
- **A target texel density for the kit,** in pixels per metre, with named exceptions for close-view parts, and the map size each part needs. A 4096 px map on a part 30 cm long is wasted; a wall panel may need it.
- **Which parts ship together** as one component, and which ship alone.
- **Names:** `<part>` for a shape and `<part>_<finish>` for a finish variant of it.

## Build the family on shared construction

- Lay the family out on one grid: the module or pitch in the contract. Every mating dimension is a multiple of it or a named exception.
- Build shared sections once. A rail, rim or foot profile used by several parts comes from one outline in the build script, so parts that meet match exactly.
- Finish parts that must match together, in the same revision. A part corrected alone drifts from its partner.
- Two revolved parts on one axis with equal segment counts must not share a surface. Build them from one profile, or offset one by its wall thickness, so no faces lie in the same plane.
- No part is a single face thick where both sides can be seen. Give panels, fins and perforated sheets real thickness.
- Build a perforated panel with its holes as ring topology and a plain margin round the field. A through-hole has walls.
- Align repeated features across parts that stack or meet: slats under ribs, bolt circles on mating flanges, panel lines across a join.

## One shape across finishes

- A finish variant is a copy of the finished master that differs only in material. It adds no geometry and changes no UV.
- Each variant has its own mesh data and its own material. Objects that share mesh data also share its material slots, so a material assigned to one would change them all.
- Freeze the master's mesh at model approval and its UVs when the UV report passes. A later mesh change reopens model approval for every finish of that shape. A later UV change means texturing every finish again.
- Check each variant against its master in the script: same vertex count, zero vertex position difference, identical UV coordinates. Record the result.
- If a finish needs different geometry (a handle only on one version, a thicker rim), it is a new shape with its own master.
- Record for each shape: master name, approved revision, the list of finishes and the material each uses.

## Checks for every part

Write these for each part to a report saved with the kit, and for each parent component that ships assembled.

- Evaluated triangle count against the part's budget.
- Open edges: none unless the part is a declared open sheet.
- Thin or zero-area faces: none.
- Faces seen from behind in any allowed arrangement: none. Inspect the part alone from below and behind, since an assembly hides them.
- UVs through `marso-blender-uv` when installed: its report passes.
- A clay render of the part alone. Counts can pass while a hole or a missing face shows.

Review the family in three recorded stages: blockout, finished meshes, then UVs. Only the finished meshes wait for the user, at model approval; record the other two reviews and continue.
