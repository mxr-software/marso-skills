"""Read-only UV geometry checks inside Blender; visibility must be supplied separately."""

import math

import bpy


def _cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _area(points):
    return abs(sum(a[0] * b[1] - b[0] * a[1]
                   for a, b in zip(points, points[1:] + points[:1]))) * 0.5


def _intersection_area(first, second):
    # Clip a triangle against three half-planes; winding is normalised by the caller.
    result = list(first)
    for a, b in zip(second, second[1:] + second[:1]):
        source, result = result, []
        if not source:
            break
        previous = source[-1]
        previous_side = _cross(a, b, previous)
        for current in source:
            side = _cross(a, b, current)
            if (side >= 0) != (previous_side >= 0):
                t = previous_side / (previous_side - side)
                result.append((previous[0] + t * (current[0] - previous[0]),
                               previous[1] + t * (current[1] - previous[1])))
            if side >= 0:
                result.append(current)
            previous, previous_side = current, side
    return _area(result) if len(result) >= 3 else 0.0


def audit_uv(objects, *, uv_name=None, excluded_faces=None, resolution=4096,
             area_epsilon=1e-10):
    """Audit one texture target. Exclusions are object-name -> polygon-index lists."""
    objects = list(objects)
    if not objects or resolution <= 0 or area_epsilon <= 0:
        raise ValueError('Supply mesh objects, a positive resolution and area tolerance')
    excluded_faces = excluded_faces or {}
    if set(excluded_faces) - {obj.name for obj in objects}:
        raise ValueError('Exclusions name objects outside this target')
    triangles, issues, densities = [], [], []
    uv_area = surface_area = 0.0
    excluded_count = 0
    unit_scale = bpy.context.scene.unit_settings.scale_length
    for obj in objects:
        if obj.type != 'MESH':
            raise ValueError('Only mesh objects can be audited')
        mesh = obj.data
        layer = mesh.uv_layers.get(uv_name) if uv_name else mesh.uv_layers.active
        if layer is None:
            raise ValueError('Missing UV layer on ' + obj.name)
        omitted = set(excluded_faces.get(obj.name, []))
        if not omitted <= set(range(len(mesh.polygons))):
            raise ValueError('Invalid excluded polygon index on ' + obj.name)
        excluded_count += len(omitted)
        mesh.calc_loop_triangles()
        for triangle in mesh.loop_triangles:
            if triangle.polygon_index in omitted:
                continue
            label = [obj.name, triangle.polygon_index, triangle.index]
            uv = [tuple(layer.data[i].uv) for i in triangle.loops]
            if not all(math.isfinite(v) for point in uv for v in point):
                issues.append({'kind': 'nonfinite', 'triangle': label})
                continue
            signed = _cross(*uv) * 0.5
            world = [obj.matrix_world @ mesh.vertices[i].co for i in triangle.vertices]
            physical = (world[1] - world[0]).cross(world[2] - world[0]).length * 0.5 * unit_scale ** 2
            if signed < -area_epsilon:
                issues.append({'kind': 'mirrored', 'triangle': label})
            if abs(signed) <= area_epsilon or physical <= 1e-14:
                issues.append({'kind': 'degenerate', 'triangle': label})
                continue
            if any(v < -1e-6 or v > 1 + 1e-6 for point in uv for v in point):
                issues.append({'kind': 'outside_tile', 'triangle': label})
            uv_area += abs(signed)
            surface_area += physical
            densities.append(resolution * math.sqrt(abs(signed) / physical))
            if signed < 0:
                uv.reverse()
            bounds = (min(p[0] for p in uv), max(p[0] for p in uv),
                      min(p[1] for p in uv), max(p[1] for p in uv))
            triangles.append((bounds, uv, label))
    triangles.sort(key=lambda item: item[0][0])
    overlaps = 0
    examples = []
    for i, (bounds, uv, label) in enumerate(triangles):
        for j in range(i + 1, len(triangles)):
            other_bounds, other_uv, other_label = triangles[j]
            if other_bounds[0] >= bounds[1]:
                break
            if other_bounds[2] >= bounds[3] or other_bounds[3] <= bounds[2]:
                continue
            if _intersection_area(uv, other_uv) > area_epsilon:
                overlaps += 1
                if len(examples) < 20:
                    examples.append([label, other_label])
    return {'passed': bool(triangles) and not issues and overlaps == 0,
            'triangles': len(triangles), 'excluded_faces': excluded_count,
            'issues': issues, 'overlap_pairs': overlaps, 'overlap_examples': examples,
            'uv_area': uv_area, 'surface_area_m2': surface_area,
            'estimated_px_per_m': resolution * math.sqrt(uv_area / surface_area) if surface_area else None,
            'triangle_density_min': min(densities) if densities else None,
            'triangle_density_max': max(densities) if densities else None}
