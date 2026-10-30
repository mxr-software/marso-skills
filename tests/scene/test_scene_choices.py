"""Choice handoffs must preserve intent and never leak into the generation queue."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from test_scene_graph_plan import fixture_graph, REPO
import test_scene_assets_manifest as manifest_tests


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


planner = module('choices_planner', REPO / 'skills/core/marso-scene-graph/scripts/plan_assets.py')
viewer = module('choices_viewer', REPO / 'skills/core/marso-scene-decompose/scripts/build_viewer.py')


def choice(route, **extra):
    return dict(route=route, search_library=True, source_kind='scene', source_ref='',
                notes='', decided_by='user', **extra)


def document(graph, choices):
    return {'schema': 'marso/scene-choices@1', 'graph_key': planner.graph_key(graph), 'choices': choices}


class ChoicesTests(unittest.TestCase):
    def setUp(self):
        self.graph = fixture_graph()

    def plan(self, choices):
        return planner.build_plan(self.graph, None, 40000, document(self.graph, choices))

    def test_routes_override_defaults_and_unpicked_stay_out(self):
        plan = self.plan({'g003': choice('generate'), 'g004': choice('model'),
                          'g005': choice('kit'), 'g006': choice('instance')})
        assets = {m: a for a in plan['assets'] for m in a['members']}
        self.assertEqual([assets[g]['route'] for g in ('g003','g004','g005','g006','g007')],
                         ['generate','model','kit','instance','skip'])
        self.assertEqual(assets['g003']['polygon_count'], 40000)
        self.assertNotIn('polygon_count', assets['g004'])
        self.assertIn('source-mesh-needed', assets['g006']['flags'])
        self.assertTrue(plan['selection_mode'])
        self.assertEqual(plan['anchors'][0]['route'], 'skip')

    def test_repeated_objects_can_be_split_but_uncertain_identity_cannot(self):
        plan = self.plan({'g007': choice('model')})
        picked = [a for a in plan['assets'] if a['route'] != 'skip']
        self.assertEqual(picked[0]['members'], ['g007'])
        with self.assertRaisesRegex(ValueError, 'identity'):
            self.plan({'g008': choice('generate')})
        picked = self.plan({'g008': choice('generate'), 'g009': choice('generate')})
        asset = next(a for a in picked['assets'] if a['route'] == 'generate')
        self.assertEqual(asset['count'], 1)
        self.assertEqual(asset['count_at_most'], 2)

    def test_empty_selection_means_no_assets(self):
        plan = self.plan({})
        self.assertTrue(all(a['route'] == 'skip' for a in plan['assets'] + plan['anchors']))

    def test_unconfirmed_needs_graph_review(self):
        self.graph['nodes'][3]['unconfirmed'] = {'reason': 'ambiguous'}
        with self.assertRaisesRegex(ValueError, 'unconfirmed'):
            self.plan({'g004': choice('model')})

    def test_stale_unknown_and_malformed_choices_are_rejected(self):
        doc = document(self.graph, {'g004': choice('model')})
        changed = copy.deepcopy(self.graph)
        changed['nodes'][3]['label'] = 'different object'
        with self.assertRaisesRegex(ValueError, 'revision'):
            planner.read_choices(doc, changed)
        for changes in ({'route': 'run-code'}, {'search_library': 'false'}, {'decided_by': 'automatic'},
                        {'source_kind': 'url'}, {'notes': ['not text']}):
            bad = copy.deepcopy(doc)
            bad['choices']['g004'].update(changes)
            with self.assertRaises(ValueError):
                planner.read_choices(bad, self.graph)
        doc['choices']['missing'] = choice('generate')
        with self.assertRaises(ValueError):
            planner.read_choices(doc, self.graph)

    def test_viewer_and_planner_share_revision_key_and_escape_script_data(self):
        graph = copy.deepcopy(self.graph)
        graph['images'] = []
        graph['nodes'][3]['description'] = '</script><script>alert(1)</script>'
        html, errors, _ = viewer.build(graph, None, None, None, None, Path('.'), False, None)
        self.assertFalse(errors)
        self.assertIn(planner.graph_key(graph), html)
        self.assertNotIn('</script><script>alert(1)', html)
        _, errors, _ = viewer.build(graph, None, None, None, None, Path('.'), False, None,
                                    choices=document(self.graph, {}))
        self.assertTrue(errors)

    def test_candidates_are_bound_to_graph_and_members(self):
        graph = copy.deepcopy(self.graph)
        graph['images'] = []
        record = {'graph_key': planner.graph_key(graph), 'assets': [{'members':['g007','g008'],
            'library': {'candidates': [{'name':'Chair', 'pbr_asset_id':'library-1', 'verdict':'possible'}]}}]}
        html, errors, _ = viewer.build(graph, None, None, None, None, Path('.'), False, None,
                                      asset_record=record)
        self.assertFalse(errors)
        data = json.loads(html.split('const DATA = ', 1)[1].split(';\n',1)[0])
        self.assertEqual(data['library_candidates']['g007'], data['library_candidates']['g008'])
        record['graph_key'] = 'stale'
        self.assertTrue(viewer.build(graph, None, None, None, None, Path('.'), False, None,
                                     asset_record=record)[1])


class ChoiceManifestTests(unittest.TestCase):
    setUp = manifest_tests.ManifestTests.setUp
    tearDown = manifest_tests.ManifestTests.tearDown
    mf = manifest_tests.ManifestTests.mf
    init = manifest_tests.ManifestTests.init
    pending = manifest_tests.ManifestTests.pending
    def test_selected_specialist_route_never_becomes_generation(self):
        plan = json.loads(self.plan.read_text())
        plan['selection_mode'] = True
        for asset in plan['assets']:
            if asset['label'] == 'bowl':
                asset['route'] = 'instance'
                asset['creation_choice'] = choice('instance')
                asset['creation_choice'].update(search_library=False, source_kind='library', source_ref='mesh-1')
        self.plan.write_text(json.dumps(plan))
        doc = self.init()
        self.assertEqual(doc['graph_key'], plan['graph_key'])
        bowl = self.ids['bowl']
        self.assertEqual(self.pending('handoff')['pending'], [bowl])
        self.assertNotIn(bowl, self.pending('reference')['pending'])
        result = self.mf('record', str(self.out), '--stage', 'reference', bowl, '--job', 'wrong-job')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.pending('handoff')['handoffs'][0]['creation_choice']['source_ref'], 'mesh-1')

    def test_selected_model_can_search_library_before_handoff(self):
        plan = json.loads(self.plan.read_text())
        plan['selection_mode'] = True
        for asset in plan['assets']:
            if asset['label'] == 'bowl':
                asset.update(route='model', creation_choice=choice('model'))
        self.plan.write_text(json.dumps(plan))
        self.init()
        bowl = self.ids['bowl']
        self.assertIn(bowl, self.pending('library')['pending'])
        self.assertEqual(self.mf('choose', str(self.out), '--make', bowl).returncode, 0)
        self.assertIn(bowl, self.pending('handoff')['pending'])


if __name__ == '__main__':
    unittest.main()
