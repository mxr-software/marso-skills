# Construction and quality

Use this when turning a blockout into an editable finished asset. Choose methods from the required surfaces and use; do not require the user to specify algorithms or a polygon count for an ordinary prop.

## Decide what the object needs

Record a short working brief: dimensions or stated scale assumption, closest intended view, visible parts, material roles, movement and requested deliverables. Infer routine decisions from the task. For an unspecified standalone realistic prop, use an inspectable close-view asset with editable parts; do not imply animation, manufacturing or simulation certification.

For realistic work, establish a coherent reference target before scripting finished geometry. Use the user's references first; obtain complementary views through available image/search tools when needed. With an open brief, choose a representative design and state that choice rather than asking the user to choose every detail. Keep one design as the primary shape reference; use other designs only for explicitly identified construction/material information. Do not average incompatible silhouettes into an invented approximation. If useful references cannot be inspected, identify that limitation and distinguish an inferred design from a faithful reconstruction.

Identify the few landmarks that make this design distinctive: extremes of the silhouette, width/depth changes, centres of major parts, openings and contact points. Compare their proportions relative to a known dimension or the overall bounds; do not treat perspective-image ratios as exact measurements. Include a view that reveals depth or section shape, not just a side outline. A similar-angle overlay can help, but first match camera projection and framing. Record inferred hidden construction without presenting it as measured fact.

Before repeating a master or preparing final UVs, keep compact evidence of the shape decision: the inspected source view(s), key dimensions/ratios with their measured or assumed basis, and a model/reference comparison of the defining transitions. For a container this might be body width/height, shoulder/neck, base profile and rim/lid construction; use landmarks appropriate to the actual object. Labels and bounding boxes alone do not provide this evidence.

When occlusion, perspective or an illustrative source leaves a defining feature unclear, use available search/image tools to inspect complementary real-object photos, manufacturer dimensions or construction views. Record which feature each source resolves and retain one primary design. Do not average different models together, use a generated image as measurement evidence, or claim a search result was inspected without opening it. No external search is needed when supplied evidence already resolves the form; if tools cannot obtain it, state the specific assumption/limitation.

## Resolve form before committing to detail

For realistic or reference-matched work, use the following internal checks. Scale their effort to the brief; a requested blockout need not pass a close-view finish check. They are agent inspections, not additional user permission steps.

| Stage | Evidence needed to advance | Work to defer if it fails |
| --- | --- | --- |
| Primary form | Neutral model/reference comparison shows the defining silhouette, relative masses, section widths and negative spaces at the intended view; a complementary view confirms volume | Small fittings, seams, surface decoration and final UV work |
| Construction | Close and oblique views show believable thickness, connections, curvature transitions, openings and panel edges; no prominent clipping or floating parts | Repeating unfinished components and final texture preparation |
| Detail and topology | Details fit the resolved structure; cage and evaluated surface shade correctly at the intended distance; required movement is checked | Claiming model completion or asking for texturing approval |

Keep a short working note for each checkpoint: saved geometry revision, inspected view(s), reference comparison, unresolved defects and repair/proceed decision. Inspect the actual images before running the next stage; generating preview files and immediately continuing in the same unattended script is not inspection. For a failed check, identify the feature and proposed repair, then compare the same useful views after changing it. Naming the object correctly or matching its bounding box does not pass the form check. An asset can be recognisable and still have the wrong design or construction.

For a batch or family, resolve a representative difficult form before applying the approach to the rest. Do not finish every object with one generic generator before looking at any of them. Small scripts are useful for repeatable operations and exact dimensions; the script's available primitives must not determine the design.

A low-poly target permits economical topology, not incorrect proportions. Increasing radial segments cannot repair a badly chosen revolve profile. Likewise, stretching a standard master into a taller variant is valid only if its shoulders, rim, base and other defining proportions still match the reference. Correct the profile/construction first; allocate geometry where silhouette and highlights need it.

## Choose construction per part

| Surface or use | Useful construction | Inspect before continuing |
| --- | --- | --- |
| Flat panels, rails, furniture frames | Dimensioned profiles, extrusion and controlled bevels | Thickness, taper, corner radius, actual joints and contact |
| Rotational bodies, rims and knobs | Revolve a shaped profile with suitable radial sampling | Body curvature, rim thickness, pole closure and faceting |
| Handles, tubing, laces and curved trim | Sweep a section along a smooth path | Bend radius, changing section, twist, endpoints and intersections |
| Moulded grips, rounded housings and compound surfaces | Loft matched section loops or build a sparse subdivision cage | Depth variation, section shape, support loops and smooth highlights |
| Soft uppers, padding and organic forms | Shape a low-density cage; sculpt and retopologise when needed | Volume, panel construction and deformation where requested |
| Openings and recesses | Planned inset/ring topology or Boolean cuts with local cleanup | Slivers, pinching, wall thickness and the evaluated bevel |
| Repeated components | Refine one master before arraying or instancing | Master finish, spacing and fit; unique UVs on copies within a Retexture atlas |

These methods can coexist within an asset. A Boolean is useful for a cut; it does not establish finished topology. Subdivision is useful for curvature; it does not repair an unsuitable cage. There is no universal modifier order: decide whether a cut, thickness or bevel belongs before or after smoothing from the intended surface, then inspect it.

## Repair the cause of a failed shape check

| Visible mismatch | Appropriate change of approach |
| --- | --- |
| Side silhouette matches, but the body is slab-like in other views | Replace constant-depth extrusion with sections or a cage whose widths and transitions follow the reference. Preserve genuine flat panels. |
| A soft fitted form looks like a generic tube or ellipsoid | Establish the underlying volume, asymmetry and local compression from multiple views; reshape the cage or sculpt that volume before deriving its surface panels. |
| Separate pieces read as unrelated primitives | Rework their relative proportions, mating surfaces and transitions. A continuous housing may need shared topology; assembled parts need credible contact and separation. |
| Curvature pinches or ripples when bevelled/subdivided | Repair local edge flow and support spacing; inspect the base cage before increasing subdivision or smoothing. |
| Detail and textures are doing the work of missing geometry | Remove their distraction in clay, rebuild the missing depth or silhouette, then restore only detail supported by the form. |

If an edit does not improve the visible mismatch, reconsider the representation or reference interpretation. Do not keep tuning bevels or adding loops to a fundamentally wrong form. Preserve the last useful checkpoint and rebuild the affected region rather than unrelated successful parts. When available control or evidence cannot support the requested quality, stop final UV/bake preparation for that asset and deliver a partial model with the specific limit and remaining work. Independent accepted assets can continue. Do not silently switch a modelling request to generation or describe the approximation as finished. Respect an explicit request to inspect UVs on unfinished geometry, but do not use that diagnostic to pass the form check.

## Build volume, not just an outline

A profile extrusion gives constant thickness. Where the reference changes width or cross-section, add deliberate stations and shape or bridge their loops. Inspect top/end views so a rounded grip, boot toe or curved housing does not remain a slab with softened edges. Keep true flat parts flat.

For fitted soft forms, establish the supporting volume before deriving panels: width and height changes, asymmetry, compression, openings and contact footprint. Footwear, for example, needs a coherent toe box, instep, heel and ankle opening plus a sole following that footprint; a tall symmetric tube with laces is insufficient. Compare top, side and rear sections as well as the oblique silhouette. Establish the sole's arch/heel/toe curvature and panel transitions before adding eyelets, trim or tread. For upholstery or other soft assets, use the corresponding support/contact landmarks rather than copying footwear construction. Surface texture can supply fine grain and shallow creases, not missing volume or structural transitions.

For a surface of revolution, place profile samples where curvature or thickness changes; distribute radial samples for the closest view. Merge axis endpoints into one vertex rather than creating coincident rings of zero-length edges. Place cap transitions away from prominent curved highlights where possible. For sweeps, preserve a stable section frame and avoid twist or self-intersection on tight bends.

Choose end treatment deliberately. A visible opening needs a rim and an interior surface; a capped sweep with a dark disk can still read as a solid end. For laces, piping or seams laid over a curved panel, follow that panel's actual surface and inspect the whole path: offset endpoints alone do not keep the middle above the surface. Weld intended periodic closures and check their shading instead of hiding a doubled end cap.

Separate genuinely assembled parts with credible seams, mounting recesses or mating surfaces. For a continuous surface, join matching boundaries or reconstruct the transition; overlapping primitives are a blockout technique, not proof of continuity. Do not weld independent moving parts merely to satisfy a manifold check.

For layered soft panels, derive the patch from the underlying surface or conform it to the evaluated mesh before adding the required thickness. Independently sampled profiles can intersect between vertices even when their vertices have a positive offset. Inspect panel edges and grazing angles for clipping, floating seams and zero-thickness cutouts; add a thickness or construction transition where it affects the close-view appearance.

Recheck attached details after smoothing, thickness or panel edits. Construction coordinates alone do not establish clearance from the evaluated surface. Projection onto a shell must choose its intended outer surface rather than a nearby inner face; inspect the result instead of trusting a positive offset. Where a path crosses between separate surfaces, preserve a continuous bend and credible contact: projecting each point independently can introduce kinks. A repaired panel invalidates earlier clearance checks for its laces, piping or fittings.

## Control topology where it matters

Use orderly quad flow where subdivision, sculpt refinement or deformation needs it. Put support loops around important rims, openings and changes of curvature; choose their spacing from the required radius. Avoid dense poles and long thin faces in visible curved transitions. Inspect both the cage and the evaluated surface. Simply triangulating a troublesome cap does not resolve pinching.

Triangles and planar n-gons are acceptable when they shade and export correctly for the intended use. An all-quad percentage is not a quality target. Keep edge density where it changes silhouette, highlights or deformation. Retain an editable source; apply or evaluate modifiers on a separate texture/export copy when necessary.

Use bevel widths appropriate to the actual feature, not one width on every edge. Weighted normals and smooth shading may improve shading but do not create missing curvature, thickness or edge radii. Check narrow corners for bevel clamping and self-intersection. Keep enough samples for curved highlights as well as silhouettes.

Before unwrapping, check evaluated geometry for non-finite coordinates, zero-area triangles, duplicate closure vertices and Boolean slivers. A degenerate UV report can originate in collapsed geometry; inspect the corresponding face before changing seams or relaxing it. Repair accidental topology on a recoverable copy and recheck the silhouette. Preserve intentional open boundaries and separate parts; a blanket merge-by-distance or manifold conversion can destroy valid construction.

## Review before texture handoff

Use fixed, useful views so edits can be compared:

- Neutral clay from front/side and an oblique view: proportions, negative spaces, thickness, connections and unwanted intersections.
- A broad reflective light on curved surfaces: waviness, pinching, faceting and abrupt normal changes. This is a diagnostic material, not a substitute for the requested texture.
- Cage wireframe plus evaluated surface: whether the intended topology controls the shape and survives modifiers.
- For requested articulation or deformation, test relevant poses and exposed interiors; a static preview cannot validate movement.

Fix the largest visible problem first and inspect the affected views again. Preserve successful proportions and details when repairing a local defect. Use adequate lighting and framing; do not use darkness, distance or one flattering camera to hide defects. If a result remains approximate, say which surfaces need work.

When UV preparation is in scope, preserve good authored UVs or use the texture skill's agent-authored route. Show a checker and atlas, inspect the evaluated upload mesh, and keep part/material-role correspondence. UV preparation must not replace approved geometry or route a curated atlas into an automatic unwrap unnoticed.

Save the editable source and report base/evaluated counts separately where relevant. Reopen the saved file and inspect requested exports when applicable. Numerical geometry checks and successful script execution establish technical facts; visual inspection establishes whether the requested object is convincingly modelled. Obtain the model approval required by the entry skill before cloud texturing.
