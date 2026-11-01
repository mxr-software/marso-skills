# Colour, lens effects and delivery

Inspect installed colour-management and compositor capabilities before setting properties. Keep colour images and data maps interpreted correctly. Establish the intended display/output transform; avoid double-applying it during external encoding or comparing differently managed viewers as though the materials changed.

Use restrained bloom/glare on appropriate bright highlights, judged at output size. Preserve highlight shape and material detail. Bloom is optional, not a realism requirement or a remedy for flat lighting. Keep a clean comparison and reversible compositor settings. Add grain, vignette, distortion or chromatic effects only when the photographic intent benefits; avoid making every scene look like the same camera preset.

For a compositing handoff or repeated lighting balance work, save suitable scene-linear passes alongside display-ready reviews where supported. A simple still need not produce a large EXR package. Keep the original scene/material outputs intact and effects separate. Sharpening must not create halos or disguise missing source detail.

For motion, receive the camera skill's actual frame range, frame rate, shutter intent and focus. Explicitly enable renderer-supported motion blur, then inspect a short rendered segment. Check moving silhouettes, focus pulls, pauses, noise flicker and exposure continuity. Do not infer camera blur support from a setting name alone.

Resume a sequence only with matching scene/assets/lighting/camera/settings revisions. Check missing frames and duration before encoding; do not skip gaps silently. Save the configured Blender file, dependencies and requested outputs, and report any remaining visible defect separately from a successful render command.
