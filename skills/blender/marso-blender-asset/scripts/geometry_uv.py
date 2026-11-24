"""Small Blender construction primitives with all-quad faces, metric charts and explicit end faces.

Every face is a quad except the triangles around a declared pointed tip. Caps are quad grids, so a capped
ring needs an even point count. Charts are deliberately UNPACKED: pack all parts of the asset together into
one atlas afterwards. These helpers do not infer design, visibility, intersections or materials.
"""
import json
import math

import bmesh
import bpy
from mathutils import Quaternion, Vector


def loft(name, sections, *, caps=(False, False), tips=(False, False), seams=(0,), closed=False, material=None,
         uv_name='MarsoUV', smooth_sides=True):
    """Bridge corresponding CCW closed rings into quads, closing capped ends with a quad grid.

    Rings must have the same vertex count, without a duplicate closing vertex.
    Order rings along the surface, with CCW winding viewed along that direction.
    A single-point end ring is a pointed tip (a cone point or nib) and needs `tips` set for that end; its
    triangles are the only ones allowed. A capped ring needs an even point count and a planar outline.
    `seams` lists the ring indices where the side band is cut into separate charts: one seam gives one
    wrap-around strip; cut a long band at its corners so the panels pack well.
    `closed=True` also bridges the last ring back to the first (piping, rims, rings, a panel with a hole
    traced as outer front, inner front, inner back, outer back); it takes no caps or tips.
    No sharp bend/self-intersection or arbitrary nonplanar cap repair is attempted.
    Returns an unparented mesh object; assign the asset root/placement explicitly.
    """
    rings = [[Vector(p) for p in ring] for ring in sections]
    if len(rings) < 2 or len(caps) != 2 or len(tips) != 2 or any(not ring for ring in rings):
        raise ValueError('Supply at least two rings and two explicit cap and tip flags')
    n = max(map(len, rings))
    if n < 3 or any(len(r) != n for r in rings[1:-1]) or any(len(r) not in (1, n) for r in rings):
        raise ValueError('Corresponding rings need >=3 vertices; only endpoints can be single points')
    if closed and (any(caps) or any(tips) or len(rings) < 3 or any(len(r) != n for r in rings)):
        raise ValueError('A closed loft needs at least three full rings and no caps or tips')
    for end, label in ((0, 'start'), (-1, 'end')):
        if len(rings[end]) == 1 and not tips[end]:
            raise ValueError('The {} ring is a single point: end at a small ring and cap it, or set tips '
                             'for a real pointed tip'.format(label))
        if caps[end] and len(rings[end]) > 1 and len(rings[end]) % 2:
            raise ValueError('A capped ring needs an even point count for a quad grid; the {} ring has {}'
                             .format(label, len(rings[end])))
    if any(len(p) != 3 or not all(math.isfinite(v) for v in p) for r in rings for p in r):
        raise ValueError('Use finite 3D coordinates')
    if bpy.data.objects.get(name):
        raise ValueError('Choose a new object name')
    vertices, ids, lengths = [], [], []
    for ring in rings:
        ids.append(list(range(len(vertices), len(vertices)+len(ring))))
        vertices.extend(ring)
        distances = [0.0]
        if len(ring) > 1:
            for a, b in zip(ring, ring[1:]+ring[:1]):
                if (b-a).length <= 1e-12:
                    raise ValueError('Repeated section vertex; omit the closing duplicate')
                distances.append(distances[-1]+(b-a).length)
        lengths.append(distances)
    along = [0.0]
    for a, b in zip(rings, rings[1:] + (rings[:1] if closed else [])):
        step = sum((b[j % len(b)]-a[j % len(a)]).length for j in range(n))/n
        if step <= 1e-12:
            raise ValueError('Coincident consecutive sections')
        along.append(along[-1]+step)
    sizes = [len(r) for r in rings]
    if closed:
        ids.append(ids[0]); lengths.append(lengths[0]); sizes.append(sizes[0])
    # One common perimeter avoids shear when a short profile step changes radius.
    full = [ds for ds in lengths if len(ds)>1]
    perimeter = [sum(ds[j] for ds in full)/len(full) for j in range(n+1)]
    cuts = sorted(set(seams))
    if not cuts or any(not isinstance(s, int) or not 0 <= s < n for s in cuts):
        raise ValueError('Give at least one seam as ring indices from 0 to {}'.format(n-1))
    gap = along[-1]*1.02 + 1e-6

    def band_u(j, corner):
        panel = max([p for p, s in enumerate(cuts) if s <= j] or [len(cuts)-1])
        start = cuts[panel]
        u = perimeter[corner]-perimeter[start] if j >= start else perimeter[corner]+perimeter[n]-perimeter[start]
        return u, panel*gap

    faces, charts, roles = [], [], {'side': [], 'start': [], 'end': []}
    pole_faces = {0: [], len(rings)-1: []}
    for i in range(len(ids)-1):
        for j in range(n):
            k = (j+1) % n
            if sizes[i] == 1:
                f = (ids[i][0], ids[i+1][k], ids[i+1][j])
                uv = ((0, along[i]), (lengths[i+1][j+1], along[i+1]), (lengths[i+1][j], along[i+1]))
                pole_faces[i].append(len(faces))
            elif sizes[i+1] == 1:
                f = (ids[i][j], ids[i][k], ids[i+1][0])
                uv = ((lengths[i][j], along[i]), (lengths[i][j+1], along[i]), (0, along[i+1]))
                pole_faces[i+1].append(len(faces))
            else:
                f = (ids[i][j], ids[i][k], ids[i+1][k], ids[i+1][j])
                (u0, shift), (u1, _) = band_u(j, j), band_u(j, j+1)
                uv = ((u0, along[i]+shift), (u1, along[i]+shift),
                      (u1, along[i+1]+shift), (u0, along[i+1]+shift))
            roles['side'].append(len(faces)); faces.append(f); charts.append(uv)
    offset = max(max(x for x, y in uv) for uv in charts)
    # Pole bands unfold as separate fans, with a single seam, not sliver triangles
    # scattered along a rectangular strip. Circular cones use developed sectors.
    for end, indices in pole_faces.items():
        if not indices:
            continue
        adjacent = 1 if end == 0 else end-1
        slant = abs(along[adjacent]-along[end])
        circumference = lengths[adjacent][-1]
        angle = min(2*math.pi, circumference/slant)
        offset += slant+max(1e-6, along[-1]*.01)
        sign = -1 if end == 0 else 1
        def point(j):
            theta = angle*lengths[adjacent][j]/circumference
            return (offset+slant*math.cos(theta), sign*slant*math.sin(theta))
        for j, face in enumerate(indices):
            charts[face] = ((offset,0),point(j+1),point(j)) if end == 0 else (point(j),point(j+1),(offset,0))
        offset += slant
    pending = []
    for end, label in [(0, 'start'), (-1, 'end')]:
        if not caps[end] or len(rings[end]) == 1:
            continue
        face = ids[end][::-1] if end == 0 else ids[end][:]
        points = [vertices[i] for i in face]
        origin = points[0]
        normal = sum(((a-origin).cross(b-origin) for a, b in zip(points, points[1:]+points[:1])), Vector()).normalized()
        if normal.length < .9:
            raise ValueError('Degenerate cap')
        x = (points[1]-points[0]).normalized(); y = normal.cross(x)
        if max(abs((p-points[0]).dot(normal)) for p in points) > 1e-6:
            raise ValueError('Cap must be planar; build a deliberate end surface instead')
        lo = min(p.dot(x) for p in points); offset += max(1e-6, along[-1]*.01)
        pending.append((label, face, normal, x, y, offset-lo))
        offset = max(p.dot(x) for p in points)-lo+offset
    mesh = bpy.data.meshes.new(name)
    try:
        mesh.from_pydata(vertices, [], faces); mesh.update()
        uv = mesh.uv_layers.new(name=uv_name); uv.active_render = True
        for p, coords in zip(mesh.polygons, charts):
            for loop, value in zip(p.loop_indices, coords):
                uv.data[loop].uv = value
        _quad_caps(mesh, uv_name, pending, roles)
        uv = mesh.uv_layers[uv_name]
        side_faces = set(roles['side'])
        for p in mesh.polygons:
            p.use_smooth = smooth_sides and p.index in side_faces
        mesh.calc_loop_triangles()
        for tri in mesh.loop_triangles:
            a, b, c = (uv.data[i].uv for i in tri.loops)
            if (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x) <= 0 or tri.area <= 0:
                raise ValueError(f'Invalid construction/chart at face {tri.polygon_index}; check section winding and caps')
        uses = {}
        for polygon in mesh.polygons:
            loops = list(polygon.loop_indices)
            for a,b in zip(loops,loops[1:]+loops[:1]):
                corners = tuple(sorted(((mesh.loops[a].vertex_index,tuple(uv.data[a].uv)),
                                        (mesh.loops[b].vertex_index,tuple(uv.data[b].uv)))))
                uses.setdefault(tuple(v for v,coord in corners),[]).append(corners)
        for edge in mesh.edges:
            charts_at_edge = uses[tuple(sorted(edge.vertices))]
            edge.use_seam = len(charts_at_edge)!=2 or charts_at_edge[0]!=charts_at_edge[1]
        if material is not None:
            mesh.materials.append(material)
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj['construction_faces'] = json.dumps(roles)
        obj['construction_uv_units'] = 'unpacked metres; pack together before submission'
        return obj
    except Exception:
        bpy.data.meshes.remove(mesh)
        raise


def _quad_caps(mesh, uv_name, pending, roles):
    """Close each planar end ring with a grid-filled quad cap and a planar chart.

    A four-point ring becomes one quad. An outline too concave for a clean grid raises, so the caller can
    add outline points or split the part.
    """
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        layer = bm.loops.layers.uv[uv_name]
        bm.verts.ensure_lookup_table()
        made = {}
        rings = [[bm.verts[i] for i in ring] for _, ring, *_ in pending]
        for (label, ring, normal, x, y, shift), verts in zip(pending, rings):
            project = lambda co: (co.dot(x)+shift, co.dot(y))
            filled, n = [], len(ring)
            outline = [project(v.co) for v in verts]
            area = abs(_area(outline))
            splits = _cap_rails(outline) if n > 4 and n % 2 == 0 else []
            for start, rail in splits:
                order = verts[start:]+verts[:start]
                edges = [bm.edges.get((order[i], order[(i+1) % n])) for i in range(n)]
                filled = bmesh.ops.grid_fill(bm, edges=edges[:rail]+edges[n//2:n//2+rail],
                                             use_interp_simple=True)['faces']
                for face in filled:
                    face.normal_update()
                    if face.normal.dot(normal) < 0:
                        face.normal_flip()
                if filled and all(_wound(face, project, normal) for face in filled) and abs(
                        sum(abs(_area([project(v.co) for v in face.verts])) for face in filled) - area) <= area*1e-6:
                    break
                bmesh.ops.delete(bm, geom=filled, context='FACES')
                filled = []
            if not filled and n % 2 == 0:
                quads = _quad_ears(outline if area > 0 else outline[::-1])
                if quads is not None:
                    order = verts if area > 0 else verts[::-1]
                    for quad in quads:
                        face = bm.faces.new([order[i] for i in quad])
                        face.normal_update()
                        if face.normal.dot(normal) < 0:
                            face.normal_flip()
                        filled.append(face)
            if not filled:
                raise ValueError('The {} cap outline is too concave for a quad grid; add outline points '
                                 'at its inner corners or split the part'.format(label))
            for face in filled:
                face.smooth = False
                for loop in face.loops:
                    loop[layer].uv = project(loop.vert.co)
            made[label] = filled
        bm.faces.index_update()
        for label, filled in made.items():
            roles[label] = [face.index for face in filled]
        bm.to_mesh(mesh)
        mesh.update()
    finally:
        bm.free()


def _cap_rails(uv, tries=12):
    """Start vertex and rail length splitting an even ring into four sides, opposite sides equal.

    Largest corner quadrilaterals first, so the grid follows the outline's shape.
    """
    n, half = len(uv), len(uv)//2
    splits = []
    for start in range(half):
        for rail in range(1, half):
            a, b, c, d = (uv[(start+k) % n] for k in (0, rail, half, half+rail))
            splits.append((abs((c[0]-a[0])*(d[1]-b[1])-(d[0]-b[0])*(c[1]-a[1])), start, rail))
    return [(start, rail) for _, start, rail in sorted(splits, reverse=True)[:tries]]


def _quad_ears(points):
    """Split a CCW simple polygon with an even point count into convex quads by cutting off quad ears.

    Returns index quads, or None when no convex ear exists at some step.
    """
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

    def inside(p, quad):
        return all(cross(quad[k], quad[(k+1) % 4], p) >= -1e-15 for k in range(4))

    def convex(corners):
        return all(cross(corners[k], corners[(k+1) % 4], corners[(k+2) % 4]) > 1e-15 for k in range(4))

    budget = [5000]

    def split(remaining):
        if len(remaining) == 4:
            return [remaining] if convex([points[j] for j in remaining]) else None
        m = len(remaining)
        for i in range(m):
            budget[0] -= 1
            if budget[0] < 0:
                return None
            ear = [remaining[(i+k) % m] for k in range(4)]
            corners = [points[j] for j in ear]
            if not convex(corners) or any(inside(points[j], corners) for j in remaining if j not in ear):
                continue
            rest = split([j for j in remaining if j not in (ear[1], ear[2])])
            if rest is not None:
                return [ear] + rest
        return None

    return split(list(range(len(points))))


def _area(points):
    return sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(points, points[1:]+points[:1]))/2


def _wound(face, project, normal):
    """A cap face lies on the cap plane and is strictly convex in its planar chart."""
    face.normal_update()
    if face.normal.dot(normal) < .999:
        return False
    uv = [project(v.co) for v in face.verts]
    return all((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]) > 1e-12
               for a, b, c in zip(uv, uv[1:]+uv[:1], uv[2:]+uv[:2]))


def revolve(name, profile, *, segments=48, caps=(True, True), tips=(False, False), seams=(0,), material=None):
    """Revolve a (z, radius) profile about +Z into quad rings, closing each end ring with a quad grid cap.

    End a closed profile at a small ring (a few percent of the body radius) so the cap is a grid, not a pole.
    A zero radius is allowed only at an end declared in `tips`, for a real point such as a cone or nib.
    For a hollow vessel, trace outer wall, rim and inner wall in order and cap the inner end as its floor.
    Pass caps=(False, False) for a part that is open at both ends, such as a horn.
    """
    if not isinstance(segments, int) or segments < 4 or segments % 2:
        raise ValueError('Use an even number of radial segments, at least four')
    profile = list(profile)
    if any(not math.isfinite(z) or not math.isfinite(r) or r < 0 for z, r in profile):
        raise ValueError('Use finite heights and nonnegative radii')
    if any(r == 0 for _, r in profile[1:-1]):
        raise ValueError('Only a profile end can reach the axis')
    rings = [[(0, 0, z)] if r == 0 else
             [(r*math.cos(2*math.pi*j/segments), r*math.sin(2*math.pi*j/segments), z)
              for j in range(segments)] for z, r in profile]
    return loft(name, rings, caps=caps, tips=tips, seams=seams, material=material)


def rounded_rectangle(width, depth, radius, segments=2):
    """CCW outline of a width x depth rectangle centred on the origin with rounded corners.

    Returns 4 x (segments + 1) points, always an even count, so the outline can take a quad grid cap.
    """
    if radius <= 0 or 2*radius >= min(width, depth) or segments < 1:
        raise ValueError('Use a positive corner radius below half the smaller side and at least one segment')
    points = []
    for cx, cy, start in ((width/2-radius, depth/2-radius, 0), (-width/2+radius, depth/2-radius, 90),
                          (-width/2+radius, -depth/2+radius, 180), (width/2-radius, -depth/2+radius, 270)):
        for k in range(segments+1):
            a = math.radians(start + 90*k/segments)
            points.append((cx + radius*math.cos(a), cy + radius*math.sin(a)))
    return points


def rounded_box(name, size, radius, *, corner=None, segments=2, material=None):
    """All-quad box of `size` (x, y, z) metres sitting on z=0 with rounded edges.

    The top and bottom edges roll over with `radius` in `segments` steps; the vertical edges are rounded
    in plan with `corner` (default `radius`). Suits cushions, mattresses and soft housings. Shape crown,
    edge roll or piping afterwards with edit operations on these quads; the caps are quad grids.
    """
    x, y, z = size
    corner = radius if corner is None else corner
    if min(x, y, z) <= 0 or radius <= 0 or corner <= 0 or 2*radius > min(x, y, z) + 1e-12 \
            or 2*corner >= min(x, y) - 2*radius or segments < 1:
        raise ValueError('Use positive sizes, radius up to half the smallest size, and a corner that fits '
                         'inside the top face')
    profile = []
    for k in range(segments+1):
        a = math.radians(90*k/segments)
        profile.append((radius*(1-math.sin(a)), radius*(1-math.cos(a))))
    profile += [(inset, z-height) for inset, height in reversed(profile)]
    rings = []
    for inset, height in profile:
        if rings and abs(height - rings[-1][0][2]) < 1e-12:
            continue
        rings.append([(px, py, height) for px, py in rounded_rectangle(x-2*inset, y-2*inset, corner, segments)])
    return loft(name, rings, caps=(True, True), seams=tuple(k*(segments+1) for k in range(4)), material=material)


def crown(obj, height, *, cap='end'):
    """Dome a helper cap (`start` or `end`): its rim stays put and its centre moves `height` along the cap
    normal, falling off with a rounded-rectangle profile. Negative heights dish the cap (a seat pan).

    Works on the base mesh of a fresh helper object, before modifiers or topology edits.
    """
    roles = json.loads(obj.get('construction_faces', '{}'))
    mesh = obj.data
    faces = roles.get(cap) or []
    if not faces or any(f >= len(mesh.polygons) for f in faces) or not math.isfinite(height):
        raise ValueError('Use a helper object with a {} cap and a finite height'.format(cap))
    uses = {}
    for f in faces:
        for key in mesh.polygons[f].edge_keys:
            uses[key] = uses.get(key, 0) + 1
    rim = {v for key, count in uses.items() if count == 1 for v in key}
    inner = {v for f in faces for v in mesh.polygons[f].vertices} - rim
    if not inner:
        raise ValueError('This cap has no interior vertices; give the outline more points')
    normal = sum((mesh.polygons[f].normal for f in faces), Vector()).normalized()
    points = [mesh.vertices[v].co for v in rim]
    centre = sum(points, Vector()) / len(points)
    x = (points[0] - centre); x = (x - normal*x.dot(normal)).normalized(); y = normal.cross(x)
    hx = max(abs((p-centre).dot(x)) for p in points); hy = max(abs((p-centre).dot(y)) for p in points)
    for v in inner:
        offset = mesh.vertices[v].co - centre
        d = min(1.0, ((offset.dot(x)/hx)**4 + (offset.dot(y)/hy)**4) ** .25)
        mesh.vertices[v].co += normal * height * (1 - d*d)
    mesh.update()
    return obj


def extrude(name, outline, depth, *, caps=(True, True), seams=(0,), material=None, smooth_sides=False):
    """CCW planar XY outline extruded along +Z, with one perimeter band (cut it at `seams` outline indices).

    Supply rounded/profiled outlines explicitly; a later bevel modifier changes
    topology and must be qualified on a representative evaluated copy.
    """
    if not math.isfinite(depth) or depth <= 0:
        raise ValueError('Use positive finite depth')
    outline = list(outline)
    if len(outline) < 3 or sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(outline, outline[1:]+outline[:1])) <= 0:
        raise ValueError('Use a counterclockwise outline without holes')
    return loft(name, [[(x, y, z) for x, y in outline] for z in (0, depth)],
                caps=caps, seams=seams, material=material, smooth_sides=smooth_sides)


def sweep(name, path, radii, *, segments=24, caps=(False, False), seams=(0,), closed=False, material=None):
    """Circular sections along a path using transported frames, no automatic fillets.

    An open path may be capped. `closed=True` joins the last point back to the first (piping round a
    cushion, a rim, a hoop); give the loop without repeating its first point. Reversing paths are rejected.
    Sharp bends and self-intersections still need visual checks; use loft for custom sections.
    """
    points = [Vector(p) for p in path]
    if len(points) < (3 if closed else 2) or segments < 3 or (points[-1]-points[0]).length < 1e-12:
        raise ValueError('Use a path of distinct points (three for a closed loop) and three segments')
    if closed and any(caps):
        raise ValueError('A closed sweep has no ends to cap')
    radii = [float(radii)]*len(points) if isinstance(radii, (int, float)) else list(radii)
    if len(radii) != len(points) or any(not math.isfinite(r) or r <= 0 for r in radii):
        raise ValueError('Supply a positive radius for each path point')
    directions = []
    for a, b in zip(points, points[1:] + (points[:1] if closed else [])):
        if (b-a).length < 1e-12:
            raise ValueError('Repeated path point')
        directions.append((b-a).normalized())
    pairs = list(zip(directions[-1:] + directions[:-1], directions)) if closed else \
        list(zip(directions, directions[1:]))
    for a, b in pairs:
        if a.dot(b) < -.99:
            raise ValueError('Path reverses; split or redesign the bend')
    tangents = [(a+b).normalized() for a, b in pairs]
    if not closed:
        tangents = [directions[0]] + tangents + [directions[-1]]
    axis = min((Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1))), key=lambda a: abs(a.dot(tangents[0])))
    x = axis.cross(tangents[0]).normalized(); previous = tangents[0]; frames = []
    for tangent in tangents:
        x = previous.rotation_difference(tangent) @ x
        x = (x-tangent*x.dot(tangent)).normalized()
        frames.append(x)
        previous = tangent
    twist = 0.0
    if closed:
        back = previous.rotation_difference(tangents[0]) @ x
        back = (back-tangents[0]*back.dot(tangents[0])).normalized()
        twist = math.atan2(frames[0].cross(back).dot(tangents[0]), frames[0].dot(back))
    rings = []
    for i, (point, tangent, radius, x) in enumerate(zip(points, tangents, radii, frames)):
        x = Quaternion(tangent, -twist*i/len(points)) @ x
        y = tangent.cross(x)
        rings.append([point+radius*(x*math.cos(2*math.pi*j/segments)+y*math.sin(2*math.pi*j/segments))
                      for j in range(segments)])
    return loft(name, rings, caps=caps, seams=seams, closed=closed, material=material)
