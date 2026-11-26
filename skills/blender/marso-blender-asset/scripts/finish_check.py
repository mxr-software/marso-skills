"""One finish check for a modelled asset: every blocking gate measured in one call, inside Blender.

`check(root, out_dir, review_dir=...)` measures the recorded path, the shape comparisons, contacts, topology,
density, the triangle budget, the shared atlas and the review files, and returns the list of blockers. A run
ends only on status `pass` or `partial`; on `repair`, fix the first blocker and call `check` again. With
`render=True` the same call also renders each review pack that no longer shows the asset, so one call a
round is enough; it never runs a reference comparison.

A blocker that is still measured after two repairs (two calls that each found the asset changed) is released
to `partial`: report it as a remaining defect. Steps that were never done are not released: a missing path,
comparison, atlas or review pack stays a blocker until it exists. The sibling skills' scripts are used when
their folders sit beside this skill; a missing sibling is listed in `notes`, not as a blocker.

Each review pack carries a stamp of the parts' change marks. A pack whose stamp does not match the asset as it
is now, or that carries no stamp, is stale: `review:stale` for the model pack, `uv:review` for the UV images.
"""

import hashlib
import importlib
import inspect
import json
from pathlib import Path
import sys
import time

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
# Verdicts kept on the root between checks: {"v", "unit", "code", "parts": {name: {"geo", "path", "topology",
# "box", "sum"}}, "gaps": {"A|B": {"pair", "geo", "gap", "hits", "sum"}}, "uv": {"mark", "key", "report", "sum"}}.
CACHE, CACHE_VERSION, MAX_KEPT_GAPS = 'marso_finish_cache', 1, 20000
MAX_JOINT_VIEWS = 12
REVIEW_REPAIR = ('Call check again with render=True and this review_dir, then open every image it lists in '
                 'rendered. review_model.review(root, out_dir, overwrite=True) renders the same pack on its own.')
UV_REVIEW_REPAIR = ('Call check again with render=True and uv_dir, then open every image it lists in rendered. '
                    'review_uv.review(root, out_dir, overwrite=True) renders the same images on its own.')
FOREIGN_REPAIR = ('render=True leaves this folder alone because its files carry no stamp. Pass an empty folder, '
                  'or replace the files yourself with {}(root, out_dir, overwrite=True).')
OLD_UV_NOTE = ('uv: the installed marso-blender-uv is an earlier version; its review images are checked for '
               'presence only and render=True does not render them')


def _sibling(skill, module):
    if module in sys.modules:
        return sys.modules[module]
    folder = Path(__file__).resolve().parents[2] / skill / 'scripts'
    if not (folder / (module + '.py')).is_file():
        return None
    sys.path.insert(0, str(folder))
    return importlib.import_module(module)


def _accepts(function, name):
    """Whether a sibling's function takes the named parameter; an earlier installed version may not."""
    try:
        return name in inspect.signature(function).parameters
    except (TypeError, ValueError):
        return False


def _lap(since):
    return round(time.perf_counter() - since, 3)


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


def _contacts(root, joints, parts=None, gaps=None):
    blockers = []
    for entry in check_contacts.floating_parts(root, parts=parts, gaps=gaps):
        gap = entry['nearest_gap_m']
        blockers.append(_blocker('contact:' + entry['part'], 'contact',
                                 'touches no other part' + ('' if gap is None else
                                                            '; nearest is {:.1f} mm away'.format(gap * 1000)),
                                 'Move or extend the part into the part it mounts on, or remove it.',
                                 part=entry['part']))
    for entry in check_contacts.report(list(joints), parts=parts, gaps=gaps):
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


def _current_uv(atlas):
    """Whether the installed marso-blender-uv shares meshes, makes change marks and stamps its images."""
    images = _sibling('marso-blender-uv', 'review_uv')
    return (hasattr(atlas, 'marks') and _accepts(atlas.report, 'meshes') and hasattr(images, 'pack_state')
            and hasattr(images, 'update_report') and _accepts(images.review, 'report')
            and _accepts(images.review, 'marks'))


def _uvs(root, uv_dir, notes, atlas, report=None, marks=None):
    """The atlas blockers and summary. `report` is the atlas report when it was measured on the shared meshes,
    and `marks` the atlas change marks; both are None with an earlier marso-blender-uv."""
    if atlas is None:
        notes.append('uv: marso-blender-uv is not installed; the atlas was not checked')
        return [], None
    if atlas.recorded(root) is None:
        return [_blocker('uv:unpacked', 'uv', 'no packed atlas is recorded on every part',
                         'Follow marso-blender-uv: unwrap, pack, join narrow charts, then report.', must=True)], None
    if report is None:
        report = atlas.report(root)
    blockers = []
    for failure in report['failures']:
        key, part = _uv_key(failure)
        blockers.append(_blocker(key, 'uv', failure, UV_REPAIRS.get(key.split(':')[1], 'See the repair table in '
                                 'marso-blender-uv.'), part=part))
    missing = list(UV_FILES) if uv_dir is None else [n for n in UV_FILES if not (Path(uv_dir) / n).is_file()]
    why = []
    state = None if marks is None or uv_dir is None else \
        _sibling('marso-blender-uv', 'review_uv').pack_state(uv_dir, marks, reason=why)
    if state == 'foreign':
        blockers.append(_blocker('uv:review', 'uv', why[0], FOREIGN_REPAIR.format('review_uv.review'), must=True))
    elif missing:
        blockers.append(_blocker('uv:review', 'uv', 'review images not found: ' + ', '.join(missing),
                                 UV_REVIEW_REPAIR, must=True))
    elif state not in (None, 'current'):
        blockers.append(_blocker('uv:review', 'uv', why[0], UV_REVIEW_REPAIR, must=True))
    return blockers, {key: report[key] for key in ('passed', 'resolution', 'padding_px', 'fill', 'density_spread',
                                                   'stretched_area_share', 'worst_patch')}


def _review(review_dir, triangles, marks):
    repair = REVIEW_REPAIR
    if review_dir is None:
        return [_blocker('review:missing', 'review', 'no review_dir was given', repair, must=True)]
    folder = Path(review_dir)
    why = []
    state = review_model.pack_state(folder, marks, reason=why)
    if state == 'foreign':
        repair = FOREIGN_REPAIR.format('review_model.review')
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
    if state != 'current':
        return [_blocker('review:stale', 'review', why[0], repair, must=True)]
    return []


def _seal(*payload):
    """A short hash of a kept entry, so an entry that was cut short or edited is not trusted."""
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def _code_mark(atlas):
    """A hash of the scripts that measure, of the add-on's UV validator and of the Blender version. Kept
    verdicts are reused only under the same hash, so an updated script measures again. None if a file
    cannot be read."""
    try:
        files = [Path(__file__), Path(review_model.__file__), Path(check_contacts.__file__)]
        if atlas is not None:
            folder = Path(atlas.__file__).resolve().parent
            files += [folder / name for name in ('uv_atlas.py', 'measure_uv_quality.py', 'audit_uv.py')]
            addon = atlas.installed_addon()
            if addon is not None:
                files.append(Path(atlas._addon_module(addon, 'uv_validation').__file__))
        digest = hashlib.sha1(repr(tuple(bpy.app.version)).encode())
        for path in files:
            digest.update(path.read_bytes())
        return digest.hexdigest()[:16]
    except Exception:  # an unreadable file only means nothing is reused
        return None


def _kept(root, unit, code):
    """The verdicts an earlier check kept on the root, as (parts, gaps, uv). Anything unreadable, or kept
    under another unit scale or by other scripts, is dropped whole."""
    try:
        kept = json.loads(root.get(CACHE, ''))
    except (TypeError, ValueError):
        kept = None
    if not isinstance(kept, dict) or kept.get('v') != CACHE_VERSION or kept.get('unit') != unit \
            or kept.get('code') != code or code is None:
        return {}, {}, None
    return tuple(kept.get(key) if isinstance(kept.get(key), dict) else default
                 for key, default in (('parts', {}), ('gaps', {}), ('uv', None)))


def _still_valid(kept_parts, kept_gaps, marks, path, unit):
    """The kept entries that match a part of the same name and mark: topology by part (also the same path),
    bounds by part and gaps by pair. An entry that fails any test, or its seal, is left out and measured."""
    known, boxes, gaps = {}, {}, {}
    for name, mark in marks.items():
        entry = kept_parts.get(name)
        try:
            if entry['geo'] != mark or entry['sum'] != _seal('part', name, mark, entry['path'], unit,
                                                             entry['topology'], entry['box']):
                continue
            if entry['box'] is not None:
                low, high = entry['box']
                boxes[name] = ([float(v) for v in low], [float(v) for v in high])
            if entry['path'] == path and isinstance(entry['topology'], dict):
                known[name] = entry['topology']
        except (KeyError, TypeError, ValueError):
            continue
    for entry in kept_gaps.values():
        try:
            a, b = entry['pair']
            if entry['geo'] != [marks[a], marks[b]] or entry['sum'] != _seal('gap', a, b, entry['geo'],
                                                                           entry['gap'], entry['hits']):
                continue
            gaps[(a, b)] = (float('inf') if entry['gap'] is None else float(entry['gap']), int(entry['hits']))
        except (KeyError, TypeError, ValueError):
            continue
    return known, boxes, gaps


def _atlas_key(atlas, root, objects):
    """What an atlas report depends on besides the marked meshes: the validator, hidden parts and part order."""
    addon = atlas.installed_addon()
    return [atlas.UV, None if addon is None else addon.__name__, atlas.hidden_meshes(root), [o.name for o in objects]]


def _keep(root, unit, code, marks, path, topology, boxes, gaps, uv):
    """Keep this check's verdicts on the root for the next one, each under the mark of what it measured."""
    if code is None:
        return
    parts = {}
    for name, mark in marks.items():
        box = boxes.get(name)
        parts[name] = {'geo': mark, 'path': path, 'topology': topology[name], 'box': box,
                       'sum': _seal('part', name, mark, path, unit, topology[name], box)}
    pairs = {}
    for (a, b), (gap, hits) in list(gaps.items())[:MAX_KEPT_GAPS]:
        if a in marks and b in marks:
            geo, gap = [marks[a], marks[b]], None if gap == float('inf') else gap
            pairs[a + '|' + b] = {'pair': [a, b], 'geo': geo, 'gap': gap, 'hits': hits,
                                  'sum': _seal('gap', a, b, geo, gap, hits)}
    if uv is not None:
        uv = dict(uv, sum=_seal('uv', uv['mark'], uv['key'], uv['report']))
    root[CACHE] = json.dumps({'v': CACHE_VERSION, 'unit': unit, 'code': code, 'parts': parts, 'gaps': pairs,
                              'uv': uv})


def _render(root, review_dir, uv_dir, size, joints, topology, marks, uv_report, uv_marks):
    """Render each review pack that no longer shows the asset. Returns the images written and what was done
    with each pack: `rendered`, `current` (left as it was), `foreign` (no stamp, left untouched) or None."""
    rendered, packs = [], {'review': None, 'uv': None}
    state = review_model.pack_state(review_dir, marks, joints=joints or None)
    if state in ('missing', 'stale'):
        made = review_model.review(root, review_dir, size=size, overwrite=True, joints=joints, report=topology,
                                   marks=marks)
        rendered += [made[key] for key in ('sheet', 'clay', 'gloss', 'wire', 'joints') if made.get(key)]
        state = 'rendered'
    elif state == 'current':
        review_model.update_report(review_dir, topology)
    packs['review'] = state
    if uv_dir is not None and uv_report is not None and uv_marks is not None:
        images = _sibling('marso-blender-uv', 'review_uv')
        state = images.pack_state(uv_dir, uv_marks)
        if state in ('missing', 'stale'):
            made = images.review(root, uv_dir, uv_name=uv_report['uv_name'], size=size, overwrite=True,
                                 report=uv_report, marks=uv_marks)
            rendered += [made[key] for key in ('checker', 'uv', 'stretch', 'worst_patch') if made.get(key)]
            state = 'rendered'
        elif state == 'current':
            images.update_report(uv_dir, uv_report)
        packs['uv'] = state
    return rendered, packs


def check(root, out_dir=None, *, review_dir=None, uv_dir=None, joints=(), budget=None, no_reference=None,
          render=False, size=1024, reuse=True):
    """Measure every finishing gate on the asset under `root` and return what still blocks the handoff.

    `review_dir` is the folder of the model review pack and `uv_dir` the folder of the UV review images.
    `joints` lists part-name pairs that must meet. `budget` is (low, high) evaluated triangles from the brief,
    either end None; it replaces the indicative range, and only a figure the brief states may be passed. A count below
    the range blocks until the path's forms are built. `no_reference` is the reason no reference applies.

    `render=True` also renders the review packs, after measuring: the model pack into `review_dir` (required)
    and the UV images into `uv_dir` when it is given and the atlas is packed. Only a pack that is missing or
    stale is rendered, at `size` pixels, with a close view of each of the first twelve `joints`. A folder
    whose files carry no stamp from the review scripts is left untouched and stays a blocker. It never runs
    `compare` or `match_view`.

    The verdicts of each part, each pair of parts and the atlas are kept on the root as `marso_finish_cache`,
    each under the change mark of what it measured. The next call measures only what changed: a kept verdict
    is used only when its part has the same name and mark, at the same path and unit scale, under the same
    scripts. `reuse=False` measures everything again.

    Returns `status` (`pass`, `repair` or `partial`), `finished`, `blockers` (each with `id`, `gate`, `part`,
    `found`, `repair`, `repairs`), `partial` (blockers released after two repairs), `notes`, `triangles`,
    `dimensions_m`, `next`, `rendered` (the images written by this call: open each one), `work` (what was
    measured and what was done with each pack) and `timings` (seconds per stage). With `out_dir` it also
    writes `finish.json` there.
    """
    started = lap = time.perf_counter()
    timings = {}
    root = bpy.data.objects[root] if isinstance(root, str) else root
    if render and review_dir is None:
        raise ValueError('render=True needs review_dir: the folder that holds, or will hold, the review pack')
    objects = review_model.asset_meshes(root)
    extent = dimensions(objects)
    notes = []
    path, found = _path(root)
    found += _shape(root, extent, no_reference, notes)
    joints = list(joints)
    atlas = _sibling('marso-blender-uv', 'uv_atlas')
    packed = atlas is not None and atlas.recorded(root) is not None
    shared = packed and _current_uv(atlas)
    if packed and not shared:
        notes.append(OLD_UV_NOTE)
    uv_report = uv_marks = uv_kept = None
    unit = bpy.context.scene.unit_settings.scale_length
    code = _code_mark(atlas)
    kept_parts, kept_gaps, kept_uv = _kept(root, unit, code) if reuse else ({}, {}, None)
    work = {'measured': [], 'reused': [], 'pairs_measured': 0, 'pairs_reused': 0, 'pairs': [], 'uv': None,
            'packs': {}}
    # One conversion of each part serves the marks, contacts, topology, density and the atlas. Nothing
    # below may render or edit the scene until the meshes are released.
    with review_model.evaluated(objects) as meshes:
        marks = review_model.marks(objects, meshes)
        known, boxes, gaps = _still_valid(kept_parts, kept_gaps, marks['parts'], path, unit)
        valid = set(gaps)
        timings['marks'], lap = _lap(lap), time.perf_counter()
        parts = check_contacts.Parts(objects, meshes, boxes=boxes)
        found += _contacts(root, joints, parts, gaps)
        boxes = dict(boxes, **parts.boxes())
        work['pairs_measured'], work['pairs'] = len(parts.measured), [list(p) for p in parts.measured[:24]]
        work['pairs_reused'] = len(valid & set(parts.reused))
        timings['contacts'], lap = _lap(lap), time.perf_counter()
        topology = json.loads(json.dumps(review_model.topology_report(objects, path, meshes=meshes, known=known)))
        work['reused'] = sorted(known)
        work['measured'] = sorted(set(marks['parts']) - set(known))
        timings['topology'], lap = _lap(lap), time.perf_counter()
        if shared:
            uv_marks = atlas.marks(root, meshes=meshes)
            key = _atlas_key(atlas, root, objects)
            try:
                if kept_uv['mark'] == uv_marks['asset'] and kept_uv['key'] == key and kept_uv['sum'] == _seal(
                        'uv', kept_uv['mark'], key, kept_uv['report']) and isinstance(kept_uv['report'], dict):
                    uv_report, work['uv'] = kept_uv['report'], 'reused'
            except (KeyError, TypeError, ValueError):
                pass
            if uv_report is None:
                uv_report, work['uv'] = json.loads(json.dumps(atlas.report(root, meshes=meshes))), 'measured'
            uv_kept = {'mark': uv_marks['asset'], 'key': key, 'report': uv_report}
            timings['uv'], lap = _lap(lap), time.perf_counter()
    _keep(root, unit, code, marks['parts'], path, topology['parts'], boxes, gaps, uv_kept)
    triangles = topology['totals']['evaluated']['triangles']
    found += _topology(topology)
    unjudged = sorted(n for n, p in topology['parts'].items() if p.get('density', {}).get('judged') is False)
    if unjudged:
        notes.append('density not judged on {} parts; name them in the handoff: {}'.format(
            len(unjudged), ', '.join(unjudged[:12]) + (' ...' if len(unjudged) > 12 else '')))
    if path:
        found += _budget(path, extent, triangles, budget)
    names = {o.name for o in objects}
    rendered = []
    if render:
        lap = time.perf_counter()
        shown = [list(pair) for pair in joints if pair[0] in names and pair[1] in names][:MAX_JOINT_VIEWS]
        rendered, work['packs'] = _render(root, review_dir, uv_dir, size, shown, topology, marks, uv_report,
                                          uv_marks)
        timings['render'] = _lap(lap)
    lap = time.perf_counter()
    uv_blockers, uv_summary = _uvs(root, uv_dir, notes, atlas, uv_report, uv_marks)
    found += uv_blockers
    found += _review(review_dir, triangles, marks)
    timings['files'] = _lap(lap)

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
    timings['total'] = _lap(started)
    result = {'status': status, 'finished': status != 'repair', 'blockers': blockers, 'partial': released,
              'notes': notes, 'path': path, 'triangles': triangles, 'dimensions_m': extent, 'uv': uv_summary,
              'checks': earlier.get('checks', 0) + 1, 'next': following, 'rendered': rendered, 'work': work,
              'timings': timings}
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
