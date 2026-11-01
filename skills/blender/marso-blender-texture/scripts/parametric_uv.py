"""Assign a chart from a builder's known surface parameters, before shared packing.

Use for swept tubes/bands or other parameterized surfaces, not arbitrary meshes.
No geometry changes, unwrap solver, atlas packing or service calls are performed.
"""
import math


def assign_chart(mesh, coordinates, *, uv_name="MarsoUV", faces=None,
                 periods=(None, None), flip_v=False):
    """Write per-vertex (u, v) parameters as seam-aware corner UVs.

    ``coordinates`` is a mapping/sequence indexed by mesh vertex index. Supply
    metric arc/perimeter distances for useful relative density. A periodic axis
    wraps in [0, period); each face must span less than half a period. Separate
    caps need their own chart. ``faces`` optionally restricts polygon indices.
    Reversed whole-chart orientation can be requested explicitly with flip_v.
    Invalid/folded triangles raise before any UV layer is changed.
    """
    if len(periods) != 2 or any(p is not None and (not math.isfinite(p) or p <= 0) for p in periods):
        raise ValueError("periods must contain two positive finite lengths or None")
    indices = list(range(len(mesh.polygons))) if faces is None else list(faces)
    if not indices or len(set(indices)) != len(indices):
        raise ValueError("Select nonempty, unique polygon indices")
    pending = {}
    for index in indices:
        if index < 0 or index >= len(mesh.polygons):
            raise ValueError("Polygon index outside mesh")
        face = mesh.polygons[index]
        values = [[float(x) for x in coordinates[mesh.loops[i].vertex_index]] for i in face.loop_indices]
        if any(len(v) != 2 or not all(math.isfinite(x) for x in v) for v in values):
            raise ValueError(f"Face {index}: invalid surface parameters")
        for axis, period in enumerate(periods):
            if period is None:
                continue
            if any(v[axis] < 0 or v[axis] >= period for v in values):
                raise ValueError(f"Face {index}: periodic coordinates must be in [0, period)")
            if max(v[axis] for v in values) - min(v[axis] for v in values) > period / 2:
                for v in values:
                    if v[axis] < period / 2:
                        v[axis] += period
            if max(v[axis] for v in values) - min(v[axis] for v in values) >= period / 2:
                raise ValueError(f"Face {index}: ambiguous wrap; subdivide or supply a nonperiodic chart")
        for loop, value in zip(face.loop_indices, values):
            pending[loop] = (value[0], -value[1] if flip_v else value[1])
    mesh.calc_loop_triangles()
    selected = set(indices)
    for tri in mesh.loop_triangles:
        if tri.polygon_index not in selected:
            continue
        a, b, c = (pending[i] for i in tri.loops)
        area = (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
        if area <= 0:
            raise ValueError(f"Face {tri.polygon_index}: mirrored/degenerate chart; correct parameters or whole-chart orientation")
    layer = mesh.uv_layers.get(uv_name) or mesh.uv_layers.new(name=uv_name)
    for loop, value in pending.items():
        layer.data[loop].uv = value
    mesh.update()
    return {"faces": len(indices), "corners": len(pending), "uv_layer": layer.name}
