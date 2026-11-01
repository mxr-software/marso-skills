# Validated handoff to Marso

Use this before Retexture, PBR-only or their batch equivalents, regardless of which modelling, scene or presentation workflow produced the target. Use the current installed Marso workflow rather than reproducing private add-on internals from a script. Keep a compact local record; no extra user questionnaire is needed.

## Before submission

1. Record the selected operation, installed add-on capabilities, scene, target root/parts and source revision. Preserve the source. Newly built geometry needs the model review described in the skill; geometry-only tasks stop before cloud operations.
2. Inspect the evaluated target without normal maps, then validate its actual material-bound UVs using [UV acceptance](uv-acceptance.md). Check all included occurrences and material domains, not just a master. Native primitives are not automatically valid: a cylinder's cap can have mirrored UV winding. Planar projection must produce oriented, separated charts; packing cannot repair a fold or overlap within a chart. Island count and summed area alone do not prove acceptance.
3. Bind the correct colour guide to the current geometry and UV revision. A rebuild needs fresh, independently owned working materials/images or explicitly verified reuse. Do not fetch an old material or image by a reused object name and assume it belongs to the new mesh. Old normal/roughness/IOR links must not silently survive a fresh preparation. Preserve earlier results and write previews to version-specific paths.
4. Verify the upload's object/material inventory and exported UV mapping. In a multi-scene file, other scenes' selections may be included by older exporters. Use an isolated working file/process when the installed exporter cannot guarantee scope; do not delete unrelated objects or rely on only the current view-layer selection. Never bypass a validation error. Read [preparation](preparation.md) for assembly, transparent-part and export-frame handling.
5. Record actual pass/fail/pending results: geometry review, map/UV identity, overlap and winding checks, export scope, colour-guide appearance, and intended exclusions. A pending export inspection is not a pass. Repair failed preparation and rebake after UV changes before submitting once through the supported command.

When separate material slots generate independent maps, validate each domain separately. When parts share an atlas or generated maps, validate them together. Document deliberately collapsed permanently hidden faces; do not exclude visible backs, moving surfaces or surfaces merely outside the camera.

## After completion

Retexture continues directly through PBR. Correlate target/source revision, job/result identity and material/image bindings; a stale preview or an earlier run's map cannot validate the current result. Check normals with maps disabled and enabled under more than one light/view, including backs and undersides. Retain untouched returned maps and final visual evidence before making instances or expanding a batch.

For a reported shading defect, light the affected surface directly on a diagnostic copy; a beauty render can conceal underside or contact-area errors. Compare identical views and lighting with only normal strength changed. If the defect disappears with the normal disabled, report the remaining normal-dependent failure even when export validation and the service job passed. Disabling the map is a diagnostic, not a completed repair. Do not request a clean sign-off or scale the workflow while known visible defects remain unresolved.

If normal directions look wrong, follow [normal diagnosis](normals-and-repeats.md). Do not automatically flatten vectors, clamp normal channels, flip green, or apply a fixed metallic/roughness gamma. Those operations cannot repair wrong UV correspondence or the wrong uploaded mesh. Any deliberate artistic adjustment remains separate from the original maps and is not described as a service correction.

Report source validation, service completion and visual acceptance separately. Preserve failed evidence for diagnosis; do not repeatedly generate from unchanged invalid inputs. A render or film is downstream of these checks, not a substitute for them.
