# Entity transforms and geometry

`place(placement_path, imports_path, collection_name=None, photo=True)` runs inside Blender. It returns the actual collection/camera names, run id, placed entity and geometry-group names, dimensions, duplicates, boxes, unused imports and warnings.

## Editable structure

```text
Table [entity Empty]
├── Table__geometry [geometry Empty]
│   ├── tabletop mesh
│   └── leg parts / imported hierarchy
└── Bowl [entity Empty]
    ├── Bowl__geometry [geometry Empty]
    │   └── bowl mesh
    └── Fruit [entity Empty]
        └── Fruit__geometry [geometry Empty]
            └── fruit mesh
```

Select a mesh to edit that part, or the geometry Empty to resize all parts of one asset. Supported entity Empties do not inherit those edits. Select the entity Empty to move, rotate or scale the entire supported assembly deliberately. Linked instances share mesh/material data: object-mode scale is independent, while editing shared mesh data changes every linked instance.

A geometry-height change does not lift objects onto the new surface automatically. After an authorised correction, check contact and adjust supported entity positions separately. Record corrections in the run's review notes. Preserve imported dimensions unless the user requests a correction.

## Identity and ownership

`run_id` persists in `assets.json` and `placement.json`. A rerun reuses the owning scene collection and objects by `marso_run_id`, `marso_global_id` and `marso_role`, never by a display name alone. Blender may suffix names to avoid collisions; use the names returned by `place`.

Every graph node, including anchors and walls, has an entity Empty. A wall's surface is geometry below that frame. Entity properties include `marso_parent_id`, `marso_relation`, `marso_asset_id` when applicable, and `marso_project_id` when known. Missing support parents are reported. Cyclic support plans are refused before placement.

Keep run ids stable when moving or resuming a project. A genuinely new scene needs a new run id. Legacy plans derive an id from their path and project; regenerate their layout from a bound generation record before relocating them. Scenes made by older scripts without ownership metadata are not automatically migrated: work in a fresh collection with explicitly identified imports, or review a separate migration with the user. Do not infer ownership from a matching name.

## Imports and instances

Preserve `import_scene_asset`'s `instances`: each entry lists every object in one complete imported asset. Its `copies` argument counts total instances, minimum one. A legacy result containing only `objects` is one compound asset, since flat names do not establish instance boundaries.

Placement preserves each instance's internal hierarchy and groups its root parts under its geometry Empty. Fallback duplication copies the complete tree, remaps parents, and shares mesh data. Cross-instance parent links from import are detached with world poses preserved. Assets already owned by another run are left untouched and reported. Unused imports are reported, not removed.

At first adoption, the complete asset's bottom centre is placed at the entity origin, keeping import axis corrections. Any planned laid-flat correction applies once to geometry. The entity frame carries planned location and yaw. Reruns restore planned entity placement but keep local geometry transforms, including user scale edits. Imported rig constraints and physics are not validated by this helper.

## Modelled handoff

Pass `asset_plan.json` to the layout helper. Model-route rows retain their plan `asset_id` and `route: "model"`, even while represented by placeholders. Supply each complete modelled working assembly in `imports.json` under that asset id, using `{"instances": [["root", "part_one", "part_two"]]}` with every object in each complete instance listed. Alternatively, `{"objects": ["root"]}` expands that root's descendants as one assembly. These are local placement-helper inputs, not new Marso commands.

Provide unowned working objects, outside the user's source master and unrelated hierarchies. Adoption reparents and tags them; preserve the editable master separately first. Make the working parts visible, check their actual dimensions and neutral origin, and preserve any materials needed for preparation. The helper normalises the complete assembly to bottom centre and shares mesh data when duplicating it. Rig/constraint targets are not remapped or certified; resolve those explicitly before using this path.

After adoption the geometry group is marked `modelled`. Reruns preserve it and its local geometry edits, without creating more copies or resetting it to a box. Placeholder meshes are excluded from real-geometry bounds and duplication. Changing the supplied master or merely keeping the same part count does not update an existing placed assembly: this helper deliberately preserves placed content. For a revised master, review a separate working instance/run and perform an explicit owned-content replacement; do not append another hierarchy beneath the old one. Check identities, mesh revisions, transforms and materials, not just object counts.

## Rerun ownership

The support tree parents entity Empties while preserving their world transforms. Geometry groups are never support parents. A rerun reuses owned entities, including after renaming, and does not delete scene objects or unlink their unrelated collection memberships. A missing-import box is hidden when the real geometry arrives and retained for recovery. Items removed from the plan are not deleted automatically; review stale objects explicitly.

The run-owned camera takes its pose, field of view and render resolution from the plan and becomes the active scene camera. When available, the photograph is a half-opacity background. An unrelated camera with the same name is preserved.

## Future USD handoff

Entity frames can map to USD Xforms; geometry can sit below a separate Xform, and repeated geometry can use references or instances. Keep stable ids and support relationships as metadata. Support is not a physics joint or rigid attachment. Export, units, physics hierarchy, colliders, mass and joints need a separate authoring/validation step; this helper does not export USD or certify Isaac Sim readiness.
