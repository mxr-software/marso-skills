---
name: marso-library
description: "Find, reuse and import existing Marso library assets by name, image or asset id. Use before unnecessary generation, or to source meshes for scene instances and new texture variants."
license: Apache-2.0
---

# Reuse assets from Marso

Reuse is a first-class creation route. Preserve a user-selected asset and its identifiers; generation is a fallback only when it fits the request.

1. Discover the current connection's search and import schemas. Read [search and selection](references/search.md) when searching. A cached name search is not proof that the whole library has no match.
2. If the user supplies an exact asset id or has already chosen a candidate, resolve and inspect that asset directly. Do not search for substitutes or ask them to choose it again.
3. Otherwise search by a short description and a tight unmarked object crop when available. Show plausible candidates and material differences. Respect an already delegated reuse decision; record your selection as an agent decision. A similarity score alone is not user approval.
4. Import through the verified command, preserving returned asset/source ids and scale. Check geometry, material dependencies and suitability for the requested use.
5. For repeated objects, share mesh data or use collection instances where supported; keep independent entity transforms. For style variants, preserve the original and isolate material bindings by style before Retexture. Create each required style once, then reuse it. Never restyle all linked copies accidentally.

For placement driven by a photographed scene graph, use `marso-blender-place-scene` when installed. A single asset in an existing scene can be placed through verified Blender controls without creating a graph. For new looks use `marso-blender-texture`. These companions are optional until the task requires them. Do not read assumed sibling paths.

Deliver the actual reused asset ids, instance/style mapping and saved file. If a requested source is unavailable, report that gap instead of generating an unrequested replacement.
