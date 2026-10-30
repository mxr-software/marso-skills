"""Read-only chart, distortion and requested-padding diagnostics inside Blender.

Use alongside audit_uv.py on evaluated working meshes. This does not certify
overlap, visibility, material bindings or artistic quality.
"""

import math

import bpy


def _percentile(samples, fraction):
    total = sum(weight for _, weight in samples)
    if not total:
        return None
    accumulated = 0.0
    for value, weight in sorted(samples):
        accumulated += weight
        if accumulated >= fraction * total:
            return value
    return max(value for value, _ in samples)


def _point_distance(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    squared = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / squared)) if squared else 0.0
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _distance(a, b, c, d):
    def cross(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    if cross(a, b, c) * cross(a, b, d) < 0 and cross(c, d, a) * cross(c, d, b) < 0:
        return 0.0
    return min(_point_distance(a, c, d), _point_distance(b, c, d),
               _point_distance(c, a, b), _point_distance(d, a, b))


def measure_uv_quality(objects, *, uv_name=None, resolution=4096, padding_px=8,
                       excluded_faces=None, match_split_vertices=False):
    """Measure one square atlas. Padding is a checked lower bound, not a packer setting.

    Exclusions use the same object-name -> polygon-index convention as audit_uv.
    Area-weighted anisotropy is >=1: 1 means locally isotropic sampling, not
    necessarily the intended density. Padding includes the tile border.
    match_split_vertices is an opt-in exact position/UV connectivity diagnostic
    for exported normal splits. It never modifies meshes or certifies overlap.
    """
    objects = list(objects)
    if not objects or not math.isfinite(resolution) or resolution <= 0 or not math.isfinite(padding_px) or padding_px < 0:
        raise ValueError('Supply objects, a positive resolution and nonnegative pixel padding')
    excluded_faces = excluded_faces or {}
    if set(excluded_faces) - {o.name for o in objects}:
        raise ValueError('Exclusions name objects outside this target')
    distortions, densities, boundaries, chart_areas, border = [], [], [], {}, []
    chart_bounds, chart_perimeters = {}, {}
    invalid = split_matches = ambiguous_matches = 0
    unit = bpy.context.scene.unit_settings.scale_length
    for obj in objects:
        if obj.type != 'MESH':
            raise ValueError('Only mesh objects can be measured')
        mesh = obj.data
        layer = mesh.uv_layers.get(uv_name) if uv_name else mesh.uv_layers.active
        if layer is None:
            raise ValueError('Missing UV layer on ' + obj.name)
        omitted = set(excluded_faces.get(obj.name, []))
        if not omitted <= set(range(len(mesh.polygons))):
            raise ValueError('Invalid excluded polygon index')
        parent = list(range(len(mesh.polygons)))
        def root(index):
            while parent[index] != index:
                parent[index] = parent[parent[index]]
                index = parent[index]
            return index
        edges = {}
        for polygon in mesh.polygons:
            if polygon.index in omitted:
                continue
            loops = list(polygon.loop_indices)
            for i, j in zip(loops, loops[1:] + loops[:1]):
                a, b = tuple(layer.data[i].uv), tuple(layer.data[j].uv)
                if not all(math.isfinite(x) for x in a + b):
                    invalid += 1
                    continue
                border.extend((a[0], a[1], 1 - a[0], 1 - a[1]))
                key = tuple(sorted(((mesh.loops[i].vertex_index, a), (mesh.loops[j].vertex_index, b))))
                edges.setdefault(key, []).append((polygon.index, a, b))
        groups = list(edges.values())
        if match_split_vertices:
            candidates = {}
            groups = []
            for key, uses in edges.items():
                if len(uses) != 1:
                    groups.append(uses)
                    continue
                endpoints = tuple(sorted((tuple(mesh.vertices[index].co), uv) for index, uv in key))
                candidates.setdefault(endpoints, []).append(uses[0])
            for uses in candidates.values():
                if (len(uses) == 2 and uses[0][0] != uses[1][0]
                        and uses[0][1] == uses[1][2] and uses[0][2] == uses[1][1]
                        and uses[0][1] != uses[0][2]):
                    groups.append(uses)
                    split_matches += 1
                else:
                    groups.extend([use] for use in uses)
                    ambiguous_matches += int(len(uses) > 1)
        for uses in groups:
            for face, _, _ in uses[1:]:
                parent[root(face)] = root(uses[0][0])
        for uses in groups:
            if len(uses) == 1:
                face, a, b = uses[0]
                bounds = (min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]))
                chart = (obj.name, root(face))
                boundaries.append((bounds, a, b, chart))
                chart_perimeters[chart] = chart_perimeters.get(chart, 0) + math.dist(a, b)
        mesh.calc_loop_triangles()
        for tri in mesh.loop_triangles:
            if tri.polygon_index in omitted:
                continue
            u, v, w = [layer.data[i].uv.copy() for i in tri.loops]
            points = [obj.matrix_world @ mesh.vertices[i].co for i in tri.vertices]
            if not all(math.isfinite(value) for point in points for value in point):
                invalid += 1
                continue
            e, f = (points[1] - points[0]) * unit, (points[2] - points[0]) * unit
            x = e.length
            h = e.cross(f).length / x if x else 0
            du, dv = v - u, w - u
            area_uv = abs(du.x * dv.y - du.y * dv.x) * 0.5
            if x <= 1e-15 or h <= 1e-15 or not math.isfinite(area_uv) or area_uv <= 1e-16:
                invalid += 1
                continue
            # J maps a local orthonormal triangle basis to UV coordinates.
            y = e.dot(f) / x
            a, c = du.x / x, du.y / x
            b, d = (dv.x - a * y) / h, (dv.y - c * y) / h
            trace = a*a + b*b + c*c + d*d
            determinant = abs(a*d - b*c)
            largest = (trace + math.sqrt(max(0, trace*trace - 4*determinant*determinant))) * 0.5
            area = x * h * 0.5
            distortions.append((largest / determinant, area))
            densities.append((resolution * math.sqrt(area_uv / area), area))
            chart = (obj.name, root(tri.polygon_index))
            chart_areas[chart] = chart_areas.get(chart, 0) + area_uv
            bounds = (min(u.x, v.x, w.x), min(u.y, v.y, w.y),
                      max(u.x, v.x, w.x), max(u.y, v.y, w.y))
            old = chart_bounds.get(chart, bounds)
            chart_bounds[chart] = (min(old[0], bounds[0]), min(old[1], bounds[1]),
                                   max(old[2], bounds[2]), max(old[3], bounds[3]))
    gap = padding_px / resolution
    boundaries.sort(key=lambda entry: entry[0][0])
    violations, examples = 0, []
    # ponytail: sweep is quadratic for dense charts; use a spatial index if profiling warrants it.
    for i, (bounds, a, b, chart) in enumerate(boundaries):
        for j in range(i + 1, len(boundaries)):
            box, c, d, other_chart = boundaries[j]
            if box[0] > bounds[1] + gap:
                break
            if chart == other_chart or box[2] > bounds[3] + gap or box[3] < bounds[2] - gap:
                continue
            distance = _distance(a, b, c, d) * resolution
            if distance + 1e-4 < padding_px:
                violations += 1
                if len(examples) < 20:
                    examples.append({'charts': [chart, other_chart], 'gap_px': distance})
    border_px = min(border) * resolution if border else None
    charts = []
    for chart, area in sorted(chart_areas.items()):
        bounds = chart_bounds[chart]
        perimeter = chart_perimeters.get(chart, 0)
        charts.append({
            'object': chart[0], 'representative_polygon': chart[1],
            'area_px2': area * resolution**2,
            'bounds_px': [value * resolution for value in bounds],
            'bbox_width_px': (bounds[2] - bounds[0]) * resolution,
            'bbox_height_px': (bounds[3] - bounds[1]) * resolution,
            'area_perimeter_width_proxy_px': 2 * area / perimeter * resolution if perimeter else None,
        })
    return {
        'islands': len(chart_areas), 'uv_area_sum': sum(chart_areas.values()),
        'island_area_px_min': min(chart_areas.values()) * resolution**2 if chart_areas else None,
        'charts': charts,
        'connectivity': 'exact_position_uv_diagnostic' if match_split_vertices else 'vertex_uv',
        'matched_split_edges': split_matches, 'ambiguous_split_edges': ambiguous_matches,
        'area_weighted_anisotropy_p50': _percentile(distortions, .5),
        'area_weighted_anisotropy_p95': _percentile(distortions, .95),
        'area_weighted_density_px_per_m': {str(p): _percentile(densities, p/100) for p in (10, 50, 90)},
        'requested_padding_px': padding_px, 'tile_border_px_min': border_px,
        'padding_violation_pairs': violations, 'padding_examples': examples,
        'padding_passed': bool(chart_areas) and invalid == 0 and violations == 0 and border_px + 1e-4 >= padding_px,
        'invalid_samples': invalid,
        'limits': 'Run overlap/winding audit separately. Area sum is occupancy only for valid nonoverlapping UVs. Bounds and area/perimeter width are candidate diagnostics, not minimum local widths. Same-chart self-proximity is not measured. Exact position matching cannot establish intended part identity. No universal stretch or island-count threshold.'
    }
