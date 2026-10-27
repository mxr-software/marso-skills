"""Rigid connector placement inside Blender; no scene changes until called."""

import math

import bpy
from mathutils import Matrix


def _inside(obj, root):
    while obj is not None:
        if obj == root:
            return True
        obj = obj.parent
    return False


def _rigid(matrix):
    basis = matrix.to_3x3()
    gram = basis.transposed() @ basis
    return abs(basis.determinant() - 1.0) < 1e-5 and all(
        abs(gram[i][j] - (1.0 if i == j else 0.0)) < 1e-5
        for i in range(3) for j in range(3)
    )


def snap_component(root, source_anchor, target_anchor, *, twist_degrees=0.0,
                   position_tolerance=1e-4, angle_tolerance_degrees=0.1):
    """Mate +Z-out/+Y-up frames; caller establishes interface compatibility."""
    values = (twist_degrees, position_tolerance, angle_tolerance_degrees)
    if not all(math.isfinite(v) for v in values) or min(values[1:]) <= 0:
        raise ValueError("Use finite values and positive tolerances.")
    if source_anchor == root or not _inside(source_anchor, root):
        raise ValueError("Source connector must be a descendant of the moving root.")
    if _inside(target_anchor, root):
        raise ValueError("Target connector must be outside the moving hierarchy.")
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    matrices = [obj.evaluated_get(depsgraph).matrix_world.copy()
                for obj in (root, source_anchor, target_anchor)]
    if not all(_rigid(matrix) for matrix in matrices):
        raise ValueError("Connector placement needs rigid, unit-scale world frames.")
    root_world, source_world, target_world = matrices
    local = root_world.inverted() @ source_world
    desired = (target_world @ Matrix.Rotation(math.radians(twist_degrees), 4, 'Z')
               @ Matrix.Rotation(math.pi, 4, 'Y'))
    previous = root.matrix_world.copy()
    try:
        root.matrix_world = desired @ local.inverted()
        bpy.context.view_layer.update()
        actual = source_anchor.evaluated_get(depsgraph).matrix_world.copy()
        target_after = target_anchor.evaluated_get(depsgraph).matrix_world.copy()
        if max(abs(target_after[i][j] - target_world[i][j])
               for i in range(4) for j in range(4)) > 1e-6:
            raise ValueError("Target moved during placement; inspect constraints or drivers.")
        position_error = (actual.translation - desired.translation).length
        angle_error = math.degrees(actual.to_quaternion().rotation_difference(
            desired.to_quaternion()).angle)
        angle_error = min(angle_error, abs(360.0 - angle_error))
        if (not _rigid(actual) or position_error > position_tolerance
                or angle_error > angle_tolerance_degrees):
            raise ValueError("Connector fit failed; inspect constraints and hierarchy.")
        return {"position_error": position_error, "angle_error_degrees": angle_error}
    except Exception:
        root.matrix_world = previous
        bpy.context.view_layer.update()
        raise
