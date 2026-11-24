"""Measure contact, floating parts and mirror symmetry on evaluated Blender meshes.

Run inside Blender. Distances are world-space metres. These are measurements, not visual
acceptance: inspect each reported interface in a close view as well.
"""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _world_mesh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        matrix = obj.matrix_world
        verts = [matrix @ v.co for v in mesh.vertices]
        polys = [tuple(p.vertices) for p in mesh.polygons]
    finally:
        evaluated.to_mesh_clear()
    return verts, polys


class _Part:
    def __init__(self, obj, depsgraph):
        self.name = obj.name
        self.verts, polys = _world_mesh(obj, depsgraph)
        self.tree = BVHTree.FromPolygons(self.verts, polys) if polys else None
        if self.verts:
            self.lo = Vector([min(v[i] for v in self.verts) for i in range(3)])
            self.hi = Vector([max(v[i] for v in self.verts) for i in range(3)])
        else:
            self.lo = self.hi = Vector()

    def box_gap(self, other):
        d = [max(other.lo[i] - self.hi[i], self.lo[i] - other.hi[i], 0.0) for i in range(3)]
        return Vector(d).length


def _gap(a, b, max_samples=4000):
    if a.tree is None or b.tree is None:
        return float("inf"), 0
    intersecting = len(a.tree.overlap(b.tree))
    if intersecting:
        return 0.0, intersecting
    best = float("inf")
    for src, dst in ((a, b), (b, a)):
        step = max(1, len(src.verts) // max_samples)
        for v in src.verts[::step]:
            hit = dst.tree.find_nearest(v)
            if hit[0] is not None and hit[3] < best:
                best = hit[3]
    return best, 0


def _parts(objects, depsgraph=None):
    depsgraph = depsgraph or bpy.context.evaluated_depsgraph_get()
    return [_Part(o, depsgraph) for o in objects if o.type == "MESH"]


def _mesh_descendants(root):
    """The root and its visible, rendered mesh descendants with faces; fails closed when there are none."""
    meshes = [o for o in [root, *root.children_recursive]
              if o.type == "MESH" and o.visible_get() and not o.hide_render and len(o.data.polygons)]
    if not meshes:
        raise ValueError("No visible mesh with faces under " + root.name)
    return meshes


def gap(a, b):
    """Return (gap_m, intersecting_face_pairs) between two mesh objects or names."""
    a = bpy.data.objects[a] if isinstance(a, str) else a
    b = bpy.data.objects[b] if isinstance(b, str) else b
    pa, pb = _parts([a, b])
    return _gap(pa, pb)


def report(pairs, tolerance=0.0005):
    """Check named part pairs. Each result: a, b, gap_m, intersecting, status (contact/gap/missing)."""
    out = []
    for a, b in pairs:
        if a not in bpy.data.objects or b not in bpy.data.objects:
            out.append({"a": a, "b": b, "status": "missing"})
            continue
        g, hits = gap(a, b)
        out.append({"a": a, "b": b, "gap_m": round(g, 6), "intersecting": hits,
                    "status": "contact" if g <= tolerance else "gap"})
    return out


def floating_parts(root, tolerance=0.0005):
    """Visible mesh parts under root that touch no other part within tolerance."""
    root = bpy.data.objects[root] if isinstance(root, str) else root
    parts = _parts(_mesh_descendants(root))
    if len(parts) < 2:
        return []
    floating = []
    for part in parts:
        nearest = float("inf")
        for other in parts:
            if other is part or part.box_gap(other) > tolerance:
                continue
            nearest = min(nearest, _gap(part, other)[0])
            if nearest <= tolerance:
                break
        if nearest > tolerance:
            floating.append({"part": part.name, "nearest_gap_m": None if nearest == float("inf") else round(nearest, 6)})
    return floating


def mirror_deviation(obj, axis=0, center=None, max_samples=4000):
    """Mirror a part across a world plane and measure how far it departs from itself.

    axis is the world axis normal to the mirror plane (0=X). center defaults to the part's
    bounding-box centre on that axis; pass the asset root's position for paired parts.
    Returns {"max_m", "mean_m"}.
    """
    obj = bpy.data.objects[obj] if isinstance(obj, str) else obj
    part = _parts([obj])[0]
    if part.tree is None:
        return {"max_m": None, "mean_m": None}
    c = (part.lo[axis] + part.hi[axis]) / 2 if center is None else center
    step = max(1, len(part.verts) // max_samples)
    distances = []
    for v in part.verts[::step]:
        m = v.copy()
        m[axis] = 2 * c - m[axis]
        hit = part.tree.find_nearest(m)
        if hit[0] is not None:
            distances.append(hit[3])
    if not distances:
        return {"max_m": None, "mean_m": None}
    return {"max_m": round(max(distances), 6), "mean_m": round(sum(distances) / len(distances), 6)}
