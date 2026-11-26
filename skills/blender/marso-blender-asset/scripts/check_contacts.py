"""Measure contact, floating parts and mirror symmetry on evaluated Blender meshes.

Run inside Blender. Distances are world-space metres. These are measurements, not visual
acceptance: inspect each reported interface in a close view as well.
"""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _world_mesh(obj, depsgraph, mesh=None):
    """World-space vertices and face vertex indices of the evaluated mesh; `mesh` is one already open."""
    evaluated = None
    if mesh is None:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
    try:
        matrix = obj.matrix_world
        verts = [matrix @ v.co for v in mesh.vertices]
        polys = [tuple(p.vertices) for p in mesh.polygons]
    finally:
        if evaluated is not None:
            evaluated.to_mesh_clear()
    return verts, polys


class _Part:
    """One part's world vertices, bounds and BVH tree, each read or built on first use."""

    def __init__(self, obj, depsgraph, mesh=None, box=None):
        self.name = obj.name
        self._source = (obj, depsgraph, mesh)
        self._verts = self._polys = self._box = None
        self._tree = False
        if box is not None:
            self._box = (Vector(box[0]), Vector(box[1]))

    def _read(self):
        if self._verts is None:
            self._verts, self._polys = _world_mesh(*self._source)
            self._source = None

    @property
    def verts(self):
        self._read()
        return self._verts

    @property
    def tree(self):
        if self._tree is False:
            self._read()
            self._tree = BVHTree.FromPolygons(self._verts, self._polys) if self._polys else None
        return self._tree

    def _bounds(self):
        if self._box is None:
            verts = self.verts
            if verts:
                self._box = (Vector([min(v[i] for v in verts) for i in range(3)]),
                             Vector([max(v[i] for v in verts) for i in range(3)]))
            else:
                self._box = (Vector(), Vector())
        return self._box

    @property
    def lo(self):
        return self._bounds()[0]

    @property
    def hi(self):
        return self._bounds()[1]

    def box_gap(self, other):
        d = [max(other.lo[i] - self.hi[i], self.lo[i] - other.hi[i], 0.0) for i in range(3)]
        return Vector(d).length


class Parts:
    """The parts of an asset by name, each read once on first use and shared by every measurement.

    `meshes` maps object names to evaluated meshes that are already open (the asset skill's
    `review_model.evaluated`); a part named there is read from it and not converted again. Use the
    instance only while those meshes are open. `boxes` maps names to (low, high) world bounds measured
    earlier on the same geometry, so a part's vertices are read only when a gap needs them.
    """

    def __init__(self, objects, meshes=None, depsgraph=None, *, boxes=None):
        self.objects = {o.name: o for o in objects if o.type == "MESH"}
        self._meshes = meshes or {}
        self._depsgraph = depsgraph
        self._boxes = boxes or {}
        self._built = {}
        self.measured, self.reused = [], []

    def __contains__(self, name):
        return name in self.objects

    def __iter__(self):
        return iter(self.objects)

    def __len__(self):
        return len(self.objects)

    def add(self, obj):
        """Include one more mesh object, such as a joint member outside the asset."""
        if obj.type != "MESH":
            raise ValueError("Not a mesh object: " + obj.name)
        self.objects.setdefault(obj.name, obj)

    def __getitem__(self, name):
        part = self._built.get(name)
        if part is None:
            if self._depsgraph is None and name not in self._meshes:
                self._depsgraph = bpy.context.evaluated_depsgraph_get()
            part = self._built[name] = _Part(self.objects[name], self._depsgraph, self._meshes.get(name),
                                             self._boxes.get(name))
        return part

    def box(self, name):
        """A part's world bounds as two lists, for `boxes` on a later instance."""
        part = self[name]
        return [list(part.lo), list(part.hi)]

    def boxes(self):
        """The world bounds known so far, as {name: [low, high]}, without reading any further part."""
        return {name: [list(part._box[0]), list(part._box[1])] for name, part in self._built.items()
                if part._box is not None}

    def gap(self, a, b, gaps=None):
        """(gap_m, intersecting_face_pairs) between two named parts, kept in `gaps` under (a, b)."""
        key = (a, b)
        if gaps is not None and key in gaps:
            self.reused.append(key)
            return gaps[key]
        value = _gap(self[a], self[b])
        self.measured.append(key)
        if gaps is not None:
            gaps[key] = value
        return value


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


def report(pairs, tolerance=0.0005, *, parts=None, gaps=None):
    """Check named part pairs. Each result: a, b, gap_m, intersecting, status (contact/gap/missing).

    `parts` is a `Parts` instance to read each member from, so a part named in several pairs is read once.
    `gaps` is a dict that keeps each measured pair under (a, b); pass the same dict to `floating_parts`.
    """
    parts = Parts([]) if parts is None else parts
    out = []
    for a, b in pairs:
        if a not in bpy.data.objects or b not in bpy.data.objects:
            out.append({"a": a, "b": b, "status": "missing"})
            continue
        for name in (a, b):
            if name not in parts:
                parts.add(bpy.data.objects[name])
        g, hits = parts.gap(a, b, gaps)
        out.append({"a": a, "b": b, "gap_m": round(g, 6), "intersecting": hits,
                    "status": "contact" if g <= tolerance else "gap"})
    return out


def floating_parts(root, tolerance=0.0005, *, parts=None, gaps=None):
    """Visible mesh parts under root that touch no other part within tolerance.

    `parts` and `gaps` are as for `report`: the shared `Parts` instance and the dict of measured pairs.
    """
    root = bpy.data.objects[root] if isinstance(root, str) else root
    members = _mesh_descendants(root)
    parts = Parts(members) if parts is None else parts
    for obj in members:
        if obj.name not in parts:
            parts.add(obj)
    names = [obj.name for obj in members]
    if len(names) < 2:
        return []
    floating = []
    for name in names:
        part = parts[name]
        nearest = float("inf")
        for other in names:
            if other == name or part.box_gap(parts[other]) > tolerance:
                continue
            nearest = min(nearest, parts.gap(name, other, gaps)[0])
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
