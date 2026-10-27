# Place compatible components

Use the source kit's definitions. New Marso kit skills use connector +Z outward, +Y up, unit-scale right-handed frames. Zero-twist mating opposes +Z while preserving +Y. Other conventions need a corresponding mating transform; do not silently reinterpret imported anchors.

For a moving component root world matrix `M`, source connector world matrix `S` and fixed target connector world matrix `T`:

```text
L = inverse(M) * S                  source connector relative to its root
F = rotation_about_Y(180 degrees)   oppose normals, keep up aligned
M_new = T * rotation_about_Z(twist) * F * inverse(L)
```

All products are matrix multiplication. The twist is in the target connector's frame and must be allowed by the interface. A documented clearance offset belongs in the mating transform or seating-frame placement, not a guessed world-axis nudge.

The [snap helper](../scripts/snap_component.py) implements this convention using Blender's `mathutils`. Read/load it into the running Blender interpreter through the available authorised tool, then call `snap_component(root, source_anchor, target_anchor, ...)` with actual Blender objects. Parameters `position_tolerance` are in Blender units; angle/twist values are degrees. It does not create objects, select mates, choose allowed twists or infer units. Those decisions belong to the workflow. Do not execute a skill file from an unverified source.

The helper requires the source anchor to be a child of the moving root, the target outside that hierarchy, and rigid unit-scale world frames. It returns measured errors and restores the root transform if verification fails. Constraints/drivers on any moved part need separate evaluation; a successful anchor check does not prove every constrained child followed the root correctly.

After placement, verify all other connections, evaluated dimensions and actual surface clearances. AABB overlap is only a broad collision candidate: connector insertion may intentionally overlap, and hollow shapes may have overlapping bounds without colliding.

For a repeated run, compare each instance to the intended grid/connection chain and measure the final endpoint. For a loop, check closure on every terminal mate. For an instance with multiple required attachment points, do not accept a solution that fits only one.
