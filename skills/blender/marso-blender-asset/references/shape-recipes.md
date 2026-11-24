# Shape recipes

All-quad constructions for the shapes and parts that recur in props and furniture. Each recipe names the build, the topology to watch and the check. Helper names refer to `geometry_uv.py` in this skill's scripts folder.

Contents:

- [Instead of Blender primitives](#instead-of-blender-primitives)
- [Boxes, boards and panels](#boxes-boards-and-panels)
- [Turned parts](#turned-parts)
- [Square and tapered legs](#square-and-tapered-legs)
- [Curved rails, slats and bent parts](#curved-rails-slats-and-bent-parts)
- [Joints between parts](#joints-between-parts)
- [Openings and recesses](#openings-and-recesses)
- [Cushions and upholstery](#cushions-and-upholstery)
- [Handles, tubes and trim](#handles-tubes-and-trim)
- [Hard-surface housings](#hard-surface-housings)
- [Moulded and blown bodies](#moulded-and-blown-bodies)
- [Furniture sizes](#furniture-sizes)
- [Woven, caned and slatted surfaces](#woven-caned-and-slatted-surfaces)
- [Assemblies](#assemblies)

## Instead of Blender primitives

| Shape | Use | Not |
| --- | --- | --- |
| Cylinder, rod, disc | `revolve` with two stations at the same radius; both ends get quad grid caps | The default cylinder (n-gon caps) or its triangle-fan fill |
| Cone, nib, blade point | `revolve` ending at radius 0 with `tips` set for that end | The default cone (n-gon base) |
| Sphere, ball, round knob | A cube with Subdivision (level 2 or more) and Cast (factor 1), or `revolve` with small-ring caps | The UV sphere (triangle fans at both poles) |
| Box with rounded edges | `rounded_box`, or a cube with a Bevel modifier of 2 or 4 segments | A Bevel of 1 or 3 segments (triangles at the corners) |
| Rounded plate | `extrude` of `rounded_rectangle` | A single-face cap |

## Boxes, boards and panels

- Extrude the outline the reference shows with an even point count, so both caps grid-fill. Cut the side band at the outline corners with `seams` when the perimeter is long.
- Bevel visible hard edges with a Bevel modifier (2 or 4 segments, limited by angle), then Weighted Normal with keep sharp. Keep both live and judge the evaluated mesh.
- A table top or seat board with a moulded edge is an extrude of the plan outline, with the edge profile added as loft stations or a Bevel profile.
- Check: the cap grid is even and its faces are not long slivers. If a cap grid shows thin diagonal faces, add outline points along the long sides.

## Turned parts

Legs, spindles, finials, knobs and feet.

- Put a profile station wherever the diameter changes direction: each bead, cove, taper start and foot. A straight taper needs only its two end stations.
- Use 12 to 16 radial segments on the low path, 24 on medium and 32 or more on high, adjusted for the closest view.
- End each turned part at a small ring with a quad cap. A foot that meets the floor ends at its real foot radius.
- Check: the silhouette shows smooth beads at the intended distance, and the ends show a grid cap rather than a pole.

## Square and tapered legs

- A square or tapered leg is a `loft` of four-point rings: one at the top and one at the foot, plus a station where a taper starts. Four-point rings cap with one quad each.
- For eased edges, use `rounded_rectangle` sections at the same stations instead of four-point rings, or add a Bevel modifier of 2 segments.
- A splayed leg is the same loft with the rings offset along the splay; keep the rings horizontal where the leg meets the floor and the seat.
- Check: the taper starts below the apron, and the foot is level with the floor.

## Curved rails, slats and bent parts

- A curved back rail or bent slat is a `loft` of section rings placed along the curve. Use enough stations that the silhouette reads smooth at the intended view; a straight extrusion has only two rings and cannot bend.
- Set the section ring's orientation from the curve's tangent so the thickness stays constant round the bend.
- A Simple Deform bend on a straight part works when the part already has length-wise loops; add them as loft stations first.
- Check: the top view shows the curve, and the section thickness is constant along it.

## Joints between parts

- A rail meets a leg by entering it: end the rail a few millimetres inside the leg, or flush on a face the rail meets squarely. Both are separate parts that touch.
- A stretcher between two legs ends on each leg's surface at the stretcher's height; measure the leg's actual surface there, not its bounding box.
- A cushion rests on its deck: its lowest point touches the deck surface, with no gap and no sinking beyond a deliberate compression.
- Measure every joint in the build script, from the two parts' actual surfaces. The usual defects are a part ending 2 to 30 mm short of its support, and a part passing 10 to 25 mm through its neighbour.
- A splayed leg's end cuts stay horizontal: level with the floor at the foot and with the rail's underside at the top, not square to the leg's own axis.
- Show joinery the reference shows: a through-tenon or wedge as a small proud part, a shadow gap as a real gap.
- Check: `check_contacts.report` gives each listed pair `status` `contact`, and `floating_parts` returns no parts.

## Openings and recesses

- A panel with a round or rounded opening is a closed `loft` of four rings: outer front, inner front, inner back, outer back. Give the outer and inner rings the same point count and matching start angles so the faces between them stay even.
- A recess is the same build with the inner back ring pushed in and capped, or an inset ring on the base mesh followed by a short push.
- A grille of many holes is a texture on the low and medium paths; model the holes only on the high path, one ring of quads per hole.
- Check: the faces round the opening are even and the wall between front and back has real thickness.

## Cushions and upholstery

- Start from `rounded_box`: `radius` sets the edge roll, `corner` the plan corner, `segments` the roll smoothness. Seat and back cushions usually take a roll of a quarter to a half of their thickness.
- Crown the top with `crown(obj, height)` on the fresh object, about 10 to 20 percent of the thickness for a seat cushion. Dish a seat pan with a negative height.
- Add piping as a closed `sweep` of a small radius (3 to 5 mm) along the seam: build the loop from `rounded_rectangle` at the seam height, slightly outside the cushion surface so the piping sits on it.
- A boxed cushion has piping at both the top and the bottom seam. A tight back has no loose cushion; its roll and crown are on the back panel itself.
- A filled cushion bulges at the sides as well as the top: give each side band a slight outward bow, less than the crown.
- A row of seat or back cushions that reads as one run is one part, wall to wall, with a crease about 30 mm deep at each division on the top, front and back.
- A back cushion stands no more than a few centimetres above the frame or board behind it; a cushion leaning on nothing reads as floating.
- Put cushions on an open frame, sculpted side frames or a set-back base, as the reference shows. A plain box plinth under the cushions reads as a placeholder.
- Add a Subdivision modifier (level 1 or 2) on the medium and high paths so the crown reads smooth, and keep it live.
- Check: the clay view shows a soft roll and crown rather than a hard box, and the piping follows the seam all the way round.

## Handles, tubes and trim

- A handle, tube or bent rod is a `sweep` along its centre path, capped where an end shows. A closed loop (a hoop, a ring pull, piping) uses `closed=True`.
- Round each bend with several path points; the helper does not fillet sharp bends.
- A flat strap or band is a `loft` of thin rectangular rings along the path.
- Check: the bend shows no kink or twist, and each end meets its mount.

## Hard-surface housings

- A housing with rounded corners (a radio, a speaker, a router) is a `rounded_box` or an `extrude` of a `rounded_rectangle`, with panel steps as further loft stations.
- Dials and knobs are `revolve` parts with quad caps and a knurled band left to texture on the low and medium paths.
- A slide, receiver or long body with a constant section is an `extrude` of its section outline, rotated to lie along its length; add stations where the section changes.
- Mirror symmetric housings with a Mirror modifier and model one-sided controls after deciding their side.
- Check: panel steps read in the clay view, and the wireframe shows edge loops following each step.

## Moulded and blown bodies

Bottles, jars, cast housings, valve bodies and other forms whose section changes along their length.

- Build the body as one `loft` or `revolve` through measured stations: crown, shoulder, widest point, waist, lower taper and foot. Take each station's width from the reference, not from a rounded primitive.
- Give every section ring the same point count and start angle, so the faces between stations stay even.
- Ease the section size across a shoulder with several stations. One abrupt change of section leaves a ridge the object does not have.
- For a body with flat sides and round corners, use `rounded_rectangle` sections. A circle scaled in one axis has no flats.
- Change a slope with stations on the profile. A Bevel rounds an edge; it does not make a taper or a shoulder.
- Keep the centre-line radius of a bent tube or swept section larger than half the section's width, or the inner wall folds through itself.
- A boss, spout or neck that grows out of the body blends into it: end it inside the body and shape the last stations to the body's surface, as a joint does.
- If repeated radius or bevel changes make the silhouette worse, return to the measured stations and rebuild the profile.
- Check: a side comparison matches the reference at every station, and `gloss.png` shows one continuous highlight down the body.

## Furniture sizes

Use these when the brief gives no size, and check a supplied size against them. A piece outside them needs a reason in the handoff.

| Measure | Range |
| --- | --- |
| Dining chair seat height | 440 to 460 mm |
| Lounge chair and sofa seat height | 400 to 430 mm |
| Dining chair seat depth | 420 to 460 mm |
| Sofa seat depth | 550 to 600 mm |
| Dining table and desk top height | 740 to 750 mm |
| Coffee table height | 350 to 420 mm |
| Seat to table underside | 270 to 300 mm |
| Knee clearance under a desk | 650 mm or more |
| Dining chair back rake | 8 to 10 degrees from vertical |

- An apron or drawer under a table top counts toward the underside: a deep apron over a dining chair leaves no room for legs.
- A pedestal table's feet spread nearly as wide as the top, so a load on the edge cannot tip it.
- A wood edge takes a bevel of 1.5 to 3 mm; a sharper edge reads as cut card.
- A table or seat top with rounded ends is a `rounded_rectangle` extrusion. A circle scaled into an oval has no flats.
- Check: measure seat height, top height and clearance on the model and set them beside the table above.

## Woven, caned and slatted surfaces

- A woven or caned seat is one closed shell that follows the weave's outer surface and wraps the rails as the cord does. The weave itself is texture. Individual cords cost tens of thousands of faces for no gain in silhouette.
- Where the shell meets a leg, notch it round the leg with about 0.5 mm clearance, using a ring of quads as the notch wall. The shell never passes through the leg.
- Slats are separate parts on the medium and high paths, each a `loft` or `extrude` with real thickness, ending inside the rails that hold them.
- Check: the shell's edge follows the rails all the way round, and no slat or shell intersects a leg.

## Assemblies

Sofa:

- Plinth and frame: `rounded_box` or extruded rails, resting on the legs.
- Arms: `rounded_box` with a generous `corner`, or a loft of the arm's front profile along its depth for a scroll arm.
- Inside back: a `rounded_box` tilted to the back angle, touching the deck and arms.
- Seat and back cushions: `rounded_box` with crown and piping, one object per cushion, resting on the deck and against the back.
- Legs: short tapered lofts or turned `revolve` parts, touching the floor and the plinth.

Dining chair:

- Legs: tapered lofts, or turned `revolve` parts on a traditional chair.
- Aprons and stretchers: extruded rails entering the legs.
- Seat: a thin `rounded_box` with a dished crown for a wooden seat, or a crowned cushion for an upholstered seat.
- Back: two back posts continuing the rear legs, a curved top rail and slats or a splat as lofts along the back curve.

Check every assembly with the contact list before the review pack: legs on the floor, rails in the legs, cushions on the deck, backs against their frame.
