# Construction and quality

Use this when turning a blockout into an editable finished asset. Choose methods from the required surfaces and use; do not require the user to specify algorithms or a polygon count for an ordinary prop.

Contents:

- [Decide what the object needs](#decide-what-the-object-needs)
- [Individual masters within a scene](#individual-masters-within-a-scene)
- [Resolve form before committing to detail](#resolve-form-before-committing-to-detail)
- [Choose construction per part](#choose-construction-per-part)
- [Repair the cause of a failed shape check](#repair-the-cause-of-a-failed-shape-check)
- [Build volume, not just an outline](#build-volume-not-just-an-outline)
- [Control topology where it matters](#control-topology-where-it-matters)
- [Review before texture handoff](#review-before-texture-handoff)

## Decide what the object needs

Resolve the low-, medium- or high-poly path first. The path sets the budget and modelling style; it never lowers the shared gates. A blockout is a separate, explicitly requested deliverable, not a path. A tiny articulated part can require more construction care than large background furniture. Allocate scene-level resources once, test repeated construction families before expansion, and stop when the path style and gates pass. Do not silently lower them after a weak result. Record active authoring time separately from cloud queueing and rendering.

Record a short working brief: path and basis, dimensions or stated scale assumption, closest intended view, visible parts, material regions for the texture brief, symmetry classification, movement and requested deliverables. Infer routine decisions from the task. For an unspecified standalone realistic prop, take the medium-poly path with editable parts and say so; do not imply animation, manufacturing or simulation certification.

Make accepted components reusable and independently rerunnable. A repair to one asset or component should not rebuild and rerender every successful asset in the batch. Carry forward surface parameters/chart boundaries, known fixed contact faces and accepted shading with the geometry, using the existing handoff rather than a separate reporting system. Resolve caps, capped sweeps and shading on one representative component before the shared atlas is packed; discovering them afterwards creates avoidable rework. Preserve source corner normals through joining.

For realistic work, establish a coherent reference target before scripting finished geometry. Use the user's references first. A supplied photo of the object is the primary shape reference even when it is a single view: identify its landmarks, then infer the far side, underside and hidden joints from the object's construction and record those inferences. Watermarks, captions, props and background scenery are not part of the object. For a missing view, use `marso-blender-reference` when installed; without it, record the view as missing and the features inferred from it. With an open brief, choose a representative design and state that choice rather than asking the user to choose every detail. Keep one design as the primary shape reference; use other designs only for explicitly identified construction/material information. Do not average incompatible silhouettes into an invented approximation. If useful references cannot be inspected, identify that limitation and distinguish an inferred design from a faithful reconstruction.

Identify the few landmarks that make this design distinctive: extremes of the silhouette, width/depth changes, centres of major parts, openings and contact points. Compare their proportions relative to a known dimension or the overall bounds; do not treat perspective-image ratios as exact measurements. Include a view that reveals depth or section shape, not just a side outline. A similar-angle overlay can help, but first match camera projection and framing. Record inferred hidden construction without presenting it as measured fact.

Before repeating a master or preparing final UVs, keep compact evidence of the shape decision: the inspected source view(s), key dimensions/ratios with their measured or assumed basis, and a model/reference comparison of the defining transitions. For a container this might be body width/height, shoulder/neck, base profile and rim/lid construction; use landmarks appropriate to the actual object. Labels and bounding boxes alone do not provide this evidence.

When occlusion, perspective or an illustrative source leaves a defining feature unclear, resolve it with `marso-blender-reference` when installed, keeping one primary design. Without it, state the specific assumption and limitation. Never use a generated image as measurement evidence.

## Individual masters within a scene

A scene request does not lower the construction standard for its assets. Work on distinct reusable masters before dressing the room: a storage assembly may contain a shelf master, a bin master and several different tool masters. Keep genuinely different shapes separate; identical copies reuse the accepted master. A board, rack or shelf is not a reason to give every contained object one generic primitive-building recipe.

Use one concise brief per master in the existing run record: reference or stated design basis, dimensions, defining shape/construction features, intended closest view and reuse, then the inspected revision and acceptance decision. A screwdriver might need a shaped grip, credible shaft insertion and an appropriate tip; a bin needs wall thickness, opening and rim; a clamp needs jaws whose contact and adjustment make sense. Choose features from the actual design, not a universal detail checklist. For missing evidence, resolve the uncertain feature before scripting the finished master.

Build in a focused pass with independent roots/collections; separate files or agents are optional, not requirements. Resolve and inspect one representative of each compatible construction family before producing its variations. Do not finish all families in a monolithic script before seeing any result. Different families need their own construction decisions even when both can use a sweep or extrusion helper.

Inspect each distinct master in an isolated neutral oblique view large enough to judge its shape, and a complementary view where depth or hidden connections matter. A contact sheet is sufficient if every asset remains legible. Check proportions, cross-sections, thickness, transitions, openings and attachments against the brief. Then inspect the placed assembly for contact, clearance, scale and orientation. Passing one review does not pass the other: a good shelf can still collide with its bins, and a plausible room can conceal unfinished props.

The path controls detail density and sampling, not whether the defining construction exists. A low-poly prop can omit microscopic fasteners or hidden mechanisms and leave fine relief to texture; it cannot replace a shaped handle with a generic cylinder when that changes its visible design. Use the intended closest view and stated reuse rather than demanding high-poly detail for every distant prop. Record the path before acceptance; do not choose a lower one afterwards to excuse a weak result.

Keep this efficient: inspect one master rather than every identical instance, use viewport/clay captures instead of final renders, and recheck only changed masters and affected contacts. Resolve visible form failures before final UV work or Marso submission. Preserve accepted masters; Retexture and PBR finish their surfaces, not missing geometry. Individual acceptance is an internal agent check, followed by the existing user geometry gate when required; it adds no approval question per prop.

Retain construction knowledge about bonded layers, permanent contacts and movable interfaces for the texture handoff. Avoid unnecessary closed overlapping solids when a surface layer expresses the intended construction just as well; preserve thickness and separate parts where the intended use needs them. Before final atlas allocation, the texture workflow must distinguish permanently covered faces from exposed borders, undersides and faces revealed by movement. A cleanly packed full-face atlas is not automatically economical. Reuse the accepted geometry captures for that handoff instead of rendering them again.

## Resolve form before committing to detail

These are the shared gates of the poly paths, in stage order. They block every path; only a requested blockout stops after primary form. They are agent inspections, not additional user permission steps, and a user's review waiver does not skip them.

| Stage | Evidence needed to advance | Work to defer if it fails |
| --- | --- | --- |
| Primary form | Model and reference agree on silhouette, masses, section widths and negative spaces; a top or end view confirms volume | Small fittings, seams, surface decoration and final UV work |
| Construction and contact | Believable thickness, connections, openings and panel edges; each interface touches, measured with `check_contacts`; nothing floats or clips | Repeating unfinished components and final texture preparation |
| Symmetry and handedness | Parts classified as symmetric, mirrored pairs or one-sided before mirroring; the opposite side inspected in its own view | Mirroring further detail, final UVs |
| Path style and topology | Triangles within budget; review pack shows all quads (triangles only at tips) and the path's edge and detail treatment; movement checked | Claiming model completion or asking for texturing approval |

Keep a short working note for each checkpoint: saved geometry revision, inspected view(s), reference comparison, unresolved defects and repair/proceed decision. Inspect the actual images before running the next stage; generating preview files and immediately continuing in the same unattended script is not inspection. For a failed check, identify the feature and proposed repair, then compare the same useful views after changing it. Naming the object correctly or matching its bounding box does not pass the form check. An asset can be recognisable and still have the wrong design or construction.

For a batch or family, resolve a representative difficult form before applying the approach to the rest. Do not finish every object with one generic generator before looking at any of them. Small scripts are useful for repeatable operations and exact dimensions; the script's available primitives must not determine the design.

A low-poly target permits economical topology, not incorrect proportions. Increasing radial segments cannot repair a badly chosen revolve profile. Likewise, stretching a standard master into a taller variant is valid only if its shoulders, rim, base and other defining proportions still match the reference. Correct the profile/construction first; allocate geometry where silhouette and highlights need it.

## Choose construction per part

| Surface or use | Useful construction | Inspect before continuing |
| --- | --- | --- |
| Flat panels, rails, furniture frames | Dimensioned profiles, extrusion and controlled bevels | Thickness, taper, corner radius, actual joints and contact |
| Rotational bodies, rims and knobs | Revolve a shaped profile with suitable radial sampling | Body curvature, rim thickness, quad cap closure and faceting |
| Handles, tubing, laces and curved trim | Sweep a section along a smooth path | Bend radius, changing section, twist, endpoints and intersections |
| Moulded grips, rounded housings and compound surfaces | Loft matched section loops or build a sparse subdivision cage | Depth variation, section shape, support loops and smooth highlights |
| Soft uppers, padding and organic forms | Shape a low-density quad cage with edit operations (crown, edge roll, piping) | Volume, panel construction and deformation where requested |
| Openings and recesses | Planned inset or ring topology, such as a closed loft round the opening | Pinching, wall thickness and the evaluated bevel |
| Repeated components | Refine one master before arraying or instancing | Master finish, spacing and fit; each occurrence needs its own space in the shared atlas |

These methods can coexist within an asset. Subdivision is useful for curvature; it does not repair an unsuitable cage. There is no universal modifier order: decide whether a cut, thickness or bevel belongs before or after smoothing from the intended surface, then inspect it.

## Repair the cause of a failed shape check

| Visible mismatch | Appropriate change of approach |
| --- | --- |
| Side silhouette matches, but the body is slab-like in other views | Replace constant-depth extrusion with sections or a cage whose widths and transitions follow the reference. Preserve genuine flat panels. |
| A soft fitted form looks like a generic tube or ellipsoid | Establish the underlying volume, asymmetry and local compression from multiple views; reshape the quad cage with edit operations before deriving its surface panels. |
| Separate pieces read as unrelated primitives | Rework their relative proportions, mating surfaces and transitions. A continuous housing may need shared topology; assembled parts need credible contact and separation. |
| Curvature pinches or ripples when bevelled/subdivided | Repair local edge flow and support spacing; inspect the base cage before increasing subdivision or smoothing. |
| Detail and textures are doing the work of missing geometry | Remove their distraction in clay, rebuild the missing depth or silhouette, then restore only detail supported by the form. |

If an edit does not improve the visible mismatch, reconsider the representation or reference interpretation. Do not keep tuning bevels or adding loops to a fundamentally wrong form. Preserve the last useful checkpoint and rebuild the affected region rather than unrelated successful parts. When available control or evidence cannot support the requested quality, stop final UV/bake preparation for that asset and deliver a partial model with the specific limit and remaining work. Independent accepted assets can continue. Do not silently switch a modelling request to generation or describe the approximation as finished. Respect an explicit request to inspect UVs on unfinished geometry, but do not use that diagnostic to pass the form check.

## Build volume, not just an outline

A profile extrusion gives constant thickness. Where the reference changes width or cross-section, add deliberate stations and shape or bridge their loops. Inspect top/end views so a rounded grip, boot toe or curved housing does not remain a slab with softened edges. Keep true flat parts flat.

For fitted soft forms, establish the supporting volume before deriving panels: width and height changes, asymmetry, compression, openings and contact footprint. Footwear, for example, needs a coherent toe box, instep, heel and ankle opening plus a sole following that footprint; a tall symmetric tube with laces is insufficient. Compare top, side and rear sections as well as the oblique silhouette. Establish the sole's arch/heel/toe curvature and panel transitions before adding eyelets, trim or tread. For upholstery or other soft assets, use the corresponding support/contact landmarks rather than copying footwear construction. Surface texture can supply fine grain and shallow creases, not missing volume or structural transitions.

For a surface of revolution, place profile samples where curvature or thickness changes; distribute radial samples for the closest view. End the profile at a small ring closed by a quad cap rather than at the axis, and never stack coincident rings of zero-length edges. Place cap transitions away from prominent curved highlights where possible. For sweeps, preserve a stable section frame and avoid twist or self-intersection on tight bends.

Choose end treatment deliberately. A visible opening needs a rim and an interior surface; a capped sweep with a dark disk can still read as a solid end. For laces, piping or seams laid over a curved panel, follow that panel's actual surface and inspect the whole path: offset endpoints alone do not keep the middle above the surface. Weld intended periodic closures and check their shading instead of hiding a doubled end cap.

Manufactured objects are often mostly symmetric with deliberate one-sided features: controls on one side, a cast arrow, a graphic, an offset handle. Model the symmetric core with a mirror, add one-sided features after deciding which side they belong to, and inspect both sides. Do not mirror a one-sided control or leave a paired feature on only one side.

Separate genuinely assembled parts with credible seams, mounting recesses or mating surfaces. For a continuous surface, join matching boundaries or reconstruct the transition; overlapping primitives are a blockout technique, not proof of continuity. Do not weld independent moving parts merely to satisfy a manifold check.

For layered soft panels, derive the patch from the underlying surface or conform it to the evaluated mesh before adding the required thickness. Independently sampled profiles can intersect between vertices even when their vertices have a positive offset. Inspect panel edges and grazing angles for clipping, floating seams and zero-thickness cutouts; add a thickness or construction transition where it affects the close-view appearance.

Recheck attached details after smoothing, thickness or panel edits. Construction coordinates alone do not establish clearance from the evaluated surface. Projection onto a shell must choose its intended outer surface rather than a nearby inner face; inspect the result instead of trusting a positive offset. Where a path crosses between separate surfaces, preserve a continuous bend and credible contact: projecting each point independently can introduce kinks. A repaired panel invalidates earlier clearance checks for its laces, piping or fittings.

## Control topology where it matters

For manufactured panels, carry the panel's right and up directions and face groups through the build. Panel charts and unwrapping belong to `marso-blender-uv` when installed; without it, report that panel charts are unchecked.

Use an editable subdivision cage when requested or when it improves curved transitions. Shape the section and silhouette first, use support loops to control the physical radius, and inspect an oblique highlight on the evaluated surface. For cylinders and vessels, revolve a measured profile into orderly rings: chart the connected sidewall with a longitudinal seam, and chart the ends separately. Close caps with a quad grid fill, never a fan of slender triangles converging on a centre vertex or a single n-gon.

Build visible front and back surfaces explicitly. An open cup needs outer and inner profiles connected by a rim, an interior floor, and an exterior base. Give each visible surface usable UV space. Apply the same rule to hinged lids in their open pose. Omit permanently buried interfaces of fixed parts when safe; retain moving, removable and externally visible surfaces.

Model with quads unless the user asks otherwise, following the topology rules of the poly paths. Keep edge density where it changes silhouette, highlights or deformation, and remove it where it does not. Save a recoverable revision of the editable source, then apply Mirror, Array and Solidify on the parts once the form is accepted and before the final unwrap; keep the other modifiers live.

Use bevel widths appropriate to the actual feature, not one width on every edge. Weighted normals and smooth shading may improve shading but do not create missing curvature, thickness or edge radii. Check narrow corners for bevel clamping and self-intersection. Keep enough samples for curved highlights as well as silhouettes.

Before unwrapping, check evaluated geometry for non-finite coordinates, zero-area faces, duplicate closure vertices and slivers. A degenerate UV report can originate in collapsed geometry; inspect the corresponding face before changing seams or relaxing it. Repair accidental topology on a recoverable copy and recheck the silhouette. Preserve intentional open boundaries and separate parts; a blanket merge-by-distance or manifold conversion can destroy valid construction.

## Review before texture handoff

Use comparable views that answer the unresolved question, not a mandatory gallery. Start with a neutral oblique view; inspect additional angles interactively where possible. Choose extra captures from the following only when needed:

- Neutral front/side views where the oblique view leaves proportions, negative spaces, thickness or contact unclear.
- The review pack's `gloss.png` on curved surfaces: waviness, pinching, faceting and abrupt normal changes. It is a diagnostic surface, not a substitute for the requested texture, and model approval still rests on neutral clay.
- Cage wireframe plus evaluated surface: whether the intended topology controls the shape and survives modifiers.
- For requested articulation or deformation, test relevant poses and exposed interiors; a static preview cannot validate movement.

Fix the largest visible problem first and inspect the affected views again. Preserve successful proportions and details when repairing a local defect. Use adequate lighting and framing; do not use darkness, distance or one flattering camera to hide defects. If a result remains approximate, say which surfaces need work.

When UV preparation is in scope, preserve good authored UVs and hand the shared atlas to the UV workflow. Its checker, stretch and layout images belong with the clay and wireframe in the review pack. UV preparation must not replace approved geometry or route a curated atlas into an automatic unwrap unnoticed.

Save the editable source; report base/evaluated counts only when relevant to the requested use or a defect. Reopen when delivery dependencies or an unqualified export route need verification, not after every checkpoint. Numerical geometry checks and successful script execution establish technical facts; visual inspection establishes whether the requested object is convincingly modelled. Obtain model approval, as the Hand off section of SKILL.md states, before cloud texturing.
