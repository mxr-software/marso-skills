# Connections and handoff

Use a Blender Text datablock named `Marso Kit` for the kit description so it travels with the .blend. A companion `kit.md` is useful when delivering external files. This is a skill convention, not an add-on API or a cloud-library format. Honour an existing kit's format instead of renaming it unnecessarily.

Record the following compactly:

| Item | Content |
| --- | --- |
| Identity | Kit name, revision, source and known assumptions. |
| Units | Blender scene unit scale, real-world units, axes, grid/pitch where applicable. |
| Components | Stable component ID, root object/collection, dimensions, variant and intended purpose. |
| Connectors | Owning component, empty object name, local position/orientation, interface type, permitted mates and twists. |
| Fit | Position and angle tolerance; intended clearance, overlap or flush seating for each interface. |
| Appearance | Material roles, grain direction/pattern scale where relevant, texture target and surfaces that must remain mapped. |
| Reusable look | Appearance-brief location/revision, accepted reference component, original source revision, and named style variants when present. |
| Reference evidence | Role of each source image, observed versus inferred dimensions/construction, and per-component appearance instructions. |
| Studio destination | Relevant project name/ID and graph ID when generation is used; saved-file selection and output membership verification. |
| Visible joins | Concealed, deliberate material break, or continuous; cover/trim ownership and depth; shared texture identity and boundary mapping for continuous surfaces. |
| Evidence | Tested connections/arrangements, measured errors, unresolved cases and saved outputs. |

Connector empties are the authoritative frames; document values from the actual .blend after building them. Names such as `wall_1m.end_a` and `wall_1m.end_b` are readable examples, not required literals. Do not set the add-on's internal assembly tags to represent kit membership.

## Frame convention

For a newly created kit, use +Z along the connector's outward mating normal and +Y along its alignment/up direction. The resulting +X completes a right-handed frame. Component geometry can still use Blender's normal Z-up world convention; connector axes are local to the interface.

Compatible connectors coincide at the intended seating plane, with their +Z normals opposed and +Y directions aligned at zero twist. Put required clearance into connector placement or an explicit documented offset, not an unexplained post-snap translation. Record allowed twist angles and interface compatibility; coincident frames do not make different connector types compatible.

Use unit-scale component roots and connector empties. Check ancestor scale as well as local scale. Nonuniform scale/shear and reflections make an orthonormal connector contract ambiguous. For imported models, normalise a working copy carefully or document a different valid convention before assembly.

For a new metre-scale visual kit without specified tolerances, 0.1 mm position and 0.1 degree angle are reasonable initial numerical checks; state them and adjust for the task. These are scene-alignment tolerances, not manufacturing claims. Convert metres to Blender units using the actual scene unit scale.

## Fit checks

Validate straight repetition without cumulative drift, each connection type, end/corner closures and any openings. Inspect actual evaluated surfaces: aligned anchors alone do not prove the modelled surfaces fit. For intentional insertions, test the specified overlap/clearance instead of treating every bounding-box overlap as failure.

Test another permitted arrangement that exposes different faces. Repeated components should retain their dimensions, connector frames and material direction. If a longer span requires a distinct component rather than scaling a connector-bearing master, record that as a variant.

For concealed joins, inspect the cover from oblique and grazing views, including allowed rotations. Model real cover depth/clearance rather than coplanar overlapping faces, which can flicker. A cover's visible surface should belong to one reusable part. For continuous joins, record physical repeat size, orientation, mapping origin/phase and permitted rotations; equal texel density alone does not align a pattern. Test repeated modules and corners before generating the whole kit.
