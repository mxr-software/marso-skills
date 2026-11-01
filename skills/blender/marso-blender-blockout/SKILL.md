---
name: marso-blender-blockout
description: "Block out a Blender room or scene from photographs, a floor plan or a brief. Establish metric walls, openings, major masses and camera fit before detailed assets."
license: Apache-2.0
---

# Block out a scene

Use the existing Blender connection. Preserve accepted work and unrelated objects. A blockout request needs neither cloud generation nor PBR. Within a complete scene, receive the accepted concept/observations and return a stable shell/layout to `marso-scene`.

1. Record known dimensions versus assumptions, room floor frame, major objects and intended views. Use real plans/photographs as evidence; generated views can propose a design but cannot measure hidden walls.
2. Build a coherent room shell: adjacent ordinary walls meet at 90 degrees in plan unless visual/measurement/design evidence supports an exception. Rotate the whole shell as needed rather than making it world-axis aligned. Connect corners; do not project each wall independently and assume they fit. Bay windows, angled wings and sloped ceilings need explicit treatment.
3. Fit camera pose, field of view and scale anchors before changing architecture to mimic image slopes. Use complementary real views when available; disclose underdetermined dimensions. Do not stretch assets to conceal a camera mismatch.
4. Add dominant proxy masses at real scale under entity Empties with separate geometry groups. Record stable ids, support relations and intended routes. Keep doors, access paths and camera clearance in mind. Proxy colour identifies roles, not finished materials.
5. Inspect a plan view and a useful eye/reference view. Fix major proportions, room corners, contact and clearance first. Agent review normally continues the full-scene task; pause only for requested blockout approval or important unresolved ambiguity. Final model approval before Marso textures is a separate gate.

Use [room-shell helper and handoff](references/room-and-camera.md) for a bounded rectangular or explicitly non-square shell. Arbitrary reconstruction and automatic camera calibration are outside that helper. Native modelling can build geometry it does not support.

Deliver a saved blockout and concise assumptions/remaining issues. For blockout-only work stop here. For complete scenes, preserve shell and entity identities through the scene planner and placement workflow; replace proxies rather than recreating guessed architecture.
