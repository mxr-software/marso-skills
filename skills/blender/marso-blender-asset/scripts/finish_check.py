"""One finish check for a modelled asset: every blocking gate measured in one call, inside Blender.

`check(root, out_dir, review_dir=...)` measures the recorded path, the shape comparisons, contacts, topology,
density, the triangle budget, the shared atlas and the review files, and returns the list of blockers. A run
ends only on status `pass` or `partial`; on `repair`, fix the first blocker and call `check` again.

A blocker that is still measured after two repairs (two calls that each found the asset changed) is released
to `partial`: report it as a remaining defect. Steps that were never done are not released: a missing path,
comparison, atlas or review pack stays a blocker until it exists. The sibling skills' scripts are used when
their folders sit beside this skill; a missing sibling is listed in `notes`, not as a blocker.
"""

import hashlib
import importlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_contacts  # noqa: E402
import review_model  # noqa: E402

PATHS = ('low', 'medium', 'high')
# Evaluated triangles, from the indicative budgets in references/poly-paths.md.
BUDGETS = {'hand-held': {'low': (400, 10000), 'medium': (6000, 80000), 'high': (100000, None)},
           'furniture': {'low': (500, 18000), 'medium': (8000, 180000), 'high': (150000, None)}}
HAND_HELD_M = 0.5
FORMS = {'low': ('silhouette parts',),
         'medium': ('bevels on visible hard edges', 'recesses, ribs, rails and panel steps',
                    'visible hardware as simple parts'),
         'high': ('all visible hardware with real detail', 'fillets where surfaces meet',
                  'tertiary detail such as serrations, grip relief and seams',
                  'support loops or creases on each edge')}
REPAIRS_BEFORE_PARTIAL = 2
SIZE_CHANGE = 0.02
REVIEW_FILES = ('clay.png', 'wire.png', 'sheet.png', 'topology.json')
UV_FILES = ('checker.png', 'uv.png', 'stretch.png', 'worst-patch.png')
RECORD, COMPARISONS = 'marso_finish', 'marso_comparisons'


def _sibling(skill, module):
    if module in sys.modules:
        return sys.modules[module]
    folder = Path(__file__).resolve().parents[2] / skill / 'scripts'
    if not (folder / (module + '.py')).is_file():
        return None
    sys.path.insert(0, str(folder))
    return importlib.import_module(module)


def dimensions(objects):
    """World size of the parts in metres, as [x, y, z]."""
    corners = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    scale = bpy.context.scene.unit_settings.scale_length
    return [round((max(c[i] for c in corners) - min(c[i] for c in corners)) * scale, 5) for i in range(3)]


def fingerprint(root):
    """A short hash of the parts' vertices, transforms, modifiers and UVs: it changes when the asset does."""
    digest = hashlib.sha1()
    for obj in sorted(review_model.asset_meshes(root), key=lambda o: o.name):
        mesh = obj.data
        co = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
        mesh.vertices.foreach_get('co', co)
        digest.update(obj.name.encode())
        digest.update(np.round(co, 5).tobytes())
        digest.update(np.round(np.array(obj.matrix_world, dtype=np.float32), 5).tobytes())
        digest.update(str(len(mesh.polygons)).encode())
        for mod in obj.modifiers:
            digest.update(repr((mod.type, mod.show_viewport, getattr(mod, 'levels', None),
                                getattr(mod, 'segments', None), round(getattr(mod, 'width', 0.0), 6))).encode())
        for layer in mesh.uv_layers:
            uv = np.empty(len(mesh.loops) * 2, dtype=np.float32)
            layer.data.foreach_get('uv', uv)
            digest.update(np.round(uv, 5).tobytes())
    return digest.hexdigest()[:16]


def _blocker(key, gate, found, repair, part=None, must=False):
    return {'id': key, 'gate': gate, 'part': part, 'found': found, 'repair': repair, 'must': must}


def _path(root):
    path = root.get('marso_poly_path')
    if path in PATHS:
        return path, []
    return None, [_blocker('path', 'path', 'marso_poly_path is {!r}'.format(path),
                           'Record marso_poly_path (low, medium or high) and marso_path_basis on the root.',
                           must=True)]


def _stopped(rounds):
    """Whether the comparison stop rule has ended work on one reference."""
    last = rounds[-1]
    if last.get('passed') is not False or len(rounds) >= 5:
        return True
    difference = last.get('largest_difference')
    if last.get('matched') and last.get('overlap', 0) >= 0.85 and difference is not None and difference <= 0.08 \
            and not last.get('relative'):
        return True
    earlier = rounds[-2].get('largest_difference') if len(rounds) > 1 else None
    return earlier is not None and difference is not None and difference >= earlier


def _shape(root, size, no_reference, notes):
    if _sibling('marso-blender-reference', 'compare_reference') is None:
        notes.append('shape: marso-blender-reference is not installed; no comparison was checked')
        return []
    try:
        records = json.loads(root.get(COMPARISONS, '{}'))
    except (TypeError, ValueError):
        records = {}
    if not records:
        if no_reference:
            notes.append('shape: no reference compared (' + str(no_reference) + ')')
            return []
        return [_blocker('shape:none', 'shape', 'no comparison is recorded on the root',
                         'Run compare_reference.compare(root, reference, out_path) against each reference. '
                         'For a stylised or invented object pass no_reference="<why>".', must=True)]
    blockers = []
    for reference, rounds in records.items():
        last = rounds[-1]
        if last.get('passed') is None:
            notes.append('shape: {} was compared by eye, not measured'.format(reference))
        then = last.get('size')
        if then and any(abs(a - b) > SIZE_CHANGE * max(b, 1e-6) for a, b in zip(size, then)):
            blockers.append(_blocker('shape:stale:' + reference, 'shape',
                                     'the asset measured {} m at the last comparison and {} m now'.format(then, size),
                                     'Compare with this reference again with overwrite=True.', must=True))
        elif not _stopped(rounds):
            worst = (last.get('worst') or ['passed is false'])[0]
            blockers.append(_blocker('shape:' + reference, 'shape',
                                     'round {}: overlap {}, largest_difference {}; {}'.format(
                                         len(rounds), last.get('overlap'), last.get('largest_difference'), worst),
                                     'Fix the part that entry names (its section, length, position or angle), '
                                     'then compare again with overwrite=True.', must=True))
        elif last.get('passed') is False:
            notes.append('shape: {} stopped by the stop rule after {} rounds with passed false; report the '
                         'remaining mismatch: {}'.format(reference, len(rounds), (last.get('worst') or ['?'])[0]))
    return blockers


def _contacts(root, joints):
    blockers = []
    for entry in check_contacts.floating_parts(root):
        gap = entry['nearest_gap_m']
        blockers.append(_blocker('contact:' + entry['part'], 'contact',
                                 'touches no other part' + ('' if gap is None else
                                                            '; nearest is {:.1f} mm away'.format(gap * 1000)),
                                 'Move or extend the part into the part it mounts on, or remove it.',
                                 part=entry['part']))
    for entry in check_contacts.report(list(joints)):
        if entry['status'] != 'contact':
            found = 'a part is missing' if entry['status'] == 'missing' else \
                'gap of {:.1f} mm'.format(entry['gap_m'] * 1000)
            blockers.append(_blocker('joint:{}|{}'.format(entry['a'], entry['b']), 'contact', found,
                                     'Lengthen one member into the other, or correct the pair of names.',
                                     part=entry['a']))
    return blockers


def _topology(report):
    blockers = []
    for name, part in report['parts'].items():
        mesh = part['evaluated']
        faults = [text.format(mesh[key]) for key, text in (('tris', '{} triangles off a tip'), ('ngons', '{} n-gons'),
                                                            ('poles_7plus', '{} vertices with 7+ edges')) if mesh[key]]
        if faults:
            blockers.append(_blocker('topology:' + name, 'topology', ', '.join(faults),
                                     'Rebuild the faces as quads: quad-grid caps, even outline counts, Bevel with '
                                     '2 or 4 segments.', part=name))
        if part.get('density', {}).get('over_dense'):
            blockers.append(_blocker('density:' + name, 'density',
                                     'halving its loops moves the surface {} mm (tolerance {} mm)'.format(
                                         part['density']['moved_p90_mm'], part['density']['tolerance_mm']),
                                     'Lower its Subdivision level or segment counts, or remove evenly spaced loops.',
                                     part=name))
    return blockers


def _budget(path, size, triangles, budget):
    kind = 'hand-held' if max(size) < HAND_HELD_M else 'furniture'
    low, high = budget if budget else BUDGETS[kind][path]
    span = '{} to {}'.format(low, 'no upper limit' if high is None else high)
    if high is not None and triangles > high:
        return [_blocker('budget:over', 'budget', '{} evaluated triangles; the {} {} range is {}'.format(
            triangles, kind, path, span), 'Remove density that shapes nothing, starting with the largest parts.')]
    if low is None or triangles >= low:
        return []
    return [_blocker('budget:under', 'budget',
                     '{} evaluated triangles; the {} {} range is {}'.format(triangles, kind, path, span),
                     'The model is too simple for the path. Build the forms the path lists ({}), then run the '
                     'check again.'.format('; '.join(FORMS[path])))]


def _uv_key(failure):
    for word, key in (('stretch p95', 'stretch'), ('density spread', 'density'), ('fill', 'fill'),
                      ('outside', 'outside'), ('overlap', 'overlap'), ('padding', 'padding'),
                      ('charts narrower', 'narrow'), ('hidden parts', 'hidden'), ('missing', 'missing'),
                      ('degenerate', 'degenerate')):
        if word in failure:
            part = failure.split(':')[0] if key in ('stretch', 'degenerate') else None
            return 'uv:' + key + (':' + part if part else ''), part
    return 'uv:' + failure[:24], None


UV_REPAIRS = {'stretch': 'Add a seam at its worst_polygons, or unwrap those faces again; repacking never cures '
                         'stretch.',
              'narrow': 'Run join_small_charts after the last pack, again while narrow_left falls.',
              'fill': 'Cut long curved bands at natural breaks, then pack again.',
              'density': 'Apply scale and pack all parts together again.'}


def _uvs(root, uv_dir, notes):
    atlas = _sibling('marso-blender-uv', 'uv_atlas')
    if atlas is None:
        notes.append('uv: marso-blender-uv is not installed; the atlas was not checked')
        return [], None
    if atlas.recorded(root) is None:
        return [_blocker('uv:unpacked', 'uv', 'no packed atlas is recorded on every part',
                         'Follow marso-blender-uv: unwrap, pack, join narrow charts, then report.', must=True)], None
    report = atlas.report(root)
    blockers = []
    for failure in report['failures']:
        key, part = _uv_key(failure)
        blockers.append(_blocker(key, 'uv', failure, UV_REPAIRS.get(key.split(':')[1], 'See the repair table in '
                                 'marso-blender-uv.'), part=part))
    missing = list(UV_FILES) if uv_dir is None else [n for n in UV_FILES if not (Path(uv_dir) / n).is_file()]
    if missing:
        blockers.append(_blocker('uv:review', 'uv', 'review images not found: ' + ', '.join(missing),
                                 'Run review_uv.review(root, out_dir) and pass that folder as uv_dir.', must=True))
    return blockers, {key: report[key] for key in ('passed', 'resolution', 'padding_px', 'fill', 'density_spread',
                                                   'stretched_area_share', 'worst_patch')}


def _review(review_dir, triangles):
    repair = 'Run review_model.review(root, out_dir, overwrite=True), open its images and pass the folder as ' \
             'review_dir.'
    if review_dir is None:
        return [_blocker('review:missing', 'review', 'no review_dir was given', repair, must=True)]
    folder = Path(review_dir)
    missing = [n for n in REVIEW_FILES if not (folder / n).is_file()]
    if missing:
        return [_blocker('review:missing', 'review', 'not found: ' + ', '.join(missing), repair, must=True)]
    try:
        rendered = json.loads((folder / 'topology.json').read_text(encoding='utf-8'))['totals']['evaluated']['triangles']
    except (ValueError, KeyError):
        rendered = None
    if rendered != triangles:
        return [_blocker('review:stale', 'review', 'the pack shows {} triangles and the asset has {}'.format(
            rendered, triangles), repair, must=True)]
    return []


def check(root, out_dir=None, *, review_dir=None, uv_dir=None, joints=(), budget=None, no_reference=None):
    """Measure every finishing gate on the asset under `root` and return what still blocks the handoff.

    `review_dir` is the folder `review_model.review` wrote and `uv_dir` the one `review_uv.review` wrote.
    `joints` lists part-name pairs that must meet. `budget` is (low, high) evaluated triangles from the brief,
    either end None; it replaces the indicative range, and only a figure the brief states may be passed. A count below
    the range blocks until the path's forms are built. `no_reference` is the reason no reference applies.

    Returns `status` (`pass`, `repair` or `partial`), `finished`, `blockers` (each with `id`, `gate`, `part`,
    `found`, `repair`, `repairs`), `partial` (blockers released after two repairs), `notes`, `triangles`,
    `dimensions_m` and `next`. With `out_dir` it also writes `finish.json` there.
    """
    root = bpy.data.objects[root] if isinstance(root, str) else root
    objects = review_model.asset_meshes(root)
    names = {o.name for o in objects}
    size = dimensions(objects)
    notes = []
    path, found = _path(root)
    found += _shape(root, size, no_reference, notes)
    found += _contacts(root, joints)
    topology = review_model.topology_report(objects, path)
    triangles = topology['totals']['evaluated']['triangles']
    found += _topology(topology)
    unjudged = sorted(n for n, p in topology['parts'].items() if p.get('density', {}).get('judged') is False)
    if unjudged:
        notes.append('density not judged on {} parts; name them in the handoff: {}'.format(
            len(unjudged), ', '.join(unjudged[:12]) + (' ...' if len(unjudged) > 12 else '')))
    if path:
        found += _budget(path, size, triangles, budget)
    uv_blockers, uv_summary = _uvs(root, uv_dir, notes)
    found += uv_blockers
    found += _review(review_dir, triangles)

    mark = fingerprint(root)
    try:
        earlier = json.loads(root.get(RECORD, '{}'))
    except (TypeError, ValueError):
        earlier = {}
    seen, history = earlier.get('seen', {}), {}
    for blocker in found:
        before = seen.get(blocker['id'])
        repairs = 0 if before is None else before['repairs'] + (before['mark'] != mark)
        blocker['repairs'] = repairs
        history[blocker['id']] = {'repairs': repairs, 'mark': mark}
    released = [b for b in found if not b['must'] and b['repairs'] >= REPAIRS_BEFORE_PARTIAL]
    blockers = [b for b in found if b not in released]
    status = 'repair' if blockers else ('partial' if released else 'pass')
    if blockers:
        first = blockers[0]
        following = 'Fix first: {} ({}). {} Then call check again.'.format(first['id'], first['found'], first['repair'])
    elif released:
        following = 'Hand off as partial and name every entry of partial as a remaining defect.'
    else:
        following = 'Hand off.'
    result = {'status': status, 'finished': status != 'repair', 'blockers': blockers, 'partial': released,
              'notes': notes, 'path': path, 'triangles': triangles, 'dimensions_m': size, 'uv': uv_summary,
              'checks': earlier.get('checks', 0) + 1, 'next': following}
    root[RECORD] = json.dumps({'status': status, 'mark': mark, 'checks': result['checks'], 'seen': history,
                               'blockers': [b['id'] for b in blockers], 'partial': [b['id'] for b in released]})
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / 'finish.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


def recorded(root):
    """The last `check` result kept on the root, with `current` false when the asset changed since."""
    root = bpy.data.objects[root] if isinstance(root, str) else root
    try:
        record = json.loads(root.get(RECORD, ''))
    except (TypeError, ValueError):
        return None
    return {'status': record.get('status'), 'checks': record.get('checks'), 'blockers': record.get('blockers', []),
            'partial': record.get('partial', []), 'current': record.get('mark') == fingerprint(root)}
