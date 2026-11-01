---
name: marso-blender-camera
description: "Compose Blender stills or create camera paths, dolly/orbit shots and handheld walkthroughs. Plan framing, focus, clearance and motion blur on an existing scene."
license: Apache-2.0
---

# Cameras for an existing scene

Preserve accepted geometry, materials and lighting. A camera request does not authorize asset regeneration. Establish the subject, output aspect, still versus motion, intended duration and camera behaviour from the request; infer routine choices. Explicit smooth/stabilized work excludes handheld noise.

For a still, compose at a plausible height/viewpoint, then choose lens and framing together. Match reference perspective before changing object proportions. Keep depth of field useful: focus on the actual surface of interest rather than the centre of a deep object. Do not force animation setup for a still.

For motion, read [shots and motion](references/shots-and-focus.md). Block the path through clear space, aim/focus targets and pauses before adding handheld movement. Inspect a cheap moving preview as well as representative frames. Framing samples alone cannot establish clearance, focus stability or pleasing motion.

The optional [rig helper](scripts/camera_rig.py) builds a new owned camera from explicit keys. It does not solve cinematic composition, reconstruct cameras from an image, or implement automatic focus selection. Its returned revision identifies the requested rig/settings; output reuse additionally needs the scene/assets/lighting revision. Do not mix stale frames after a change.

After the motion/framing check, hand the camera, frame range, resolution, focus, shutter intent and revision to `marso-blender-render` when installed. Use its lighting/render route without recreating the scene. For a final rendered sequence, test a short real-motion-blur segment before the full run. A requested blockout/playblast may remain Workbench and blur-free, labelled as such. Save the rig as editable Blender data and deliver only the requested shots. Model-review requirements still apply if the task also includes new assets.
