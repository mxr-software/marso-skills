# Scene concepts and probes

For a prompt-to-scene request, normally generate one anchor concept in its relevant Marso Studio project. Skip this for a settled design or direct blockout request. Image-only tasks stop with inspected images.

Describe the room's use, zones, defining objects, material palette, plausible light sources and intended view. Use [prompt structure](prompt-structure.md); do not overload the image with the complete asset inventory or internal workflow instructions.

Probe a named uncertainty with a close-up or alternate view only where a verified tool supports it. A crop preserves pixels; an edit invents extra detail; a changed view invents unseen construction. Record that distinction. Keep the accepted anchor and compare openings, counts, object identity, supports and finish across probes. Do not treat a generated reverse view as evidence contradicting real photographs or measured plans.

Branch from the accepted anchor to limit drift. Once a Blender blockout exists, its actual camera render can supply layout while the concept supplies appearance if the image operation supports those references. Exact geometry or framing preservation is not guaranteed: inspect the result and reconcile conflicts before downstream generation.

For Blender, read [add-on image operations](addon-images.md) and discover the installed commands. Use scene mode for the room anchor, then branch image edits from its node. Older object-only commands are not substitutes for a room concept. Keep full-room concepts separate from isolated asset references and authorized Retexture references. A scene-mode image or its edited descendant is not a mesh-generation source; obtain an isolated object reference through the supported scene asset workflow instead.
