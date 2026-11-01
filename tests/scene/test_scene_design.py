import copy
import runpy
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
build=runpy.run_path(str(ROOT/'skills/core/marso-scene-graph/scripts/design_plan.py'))['build']
route=runpy.run_path(str(ROOT/'skills/core/marso-scene-graph/scripts/plan_assets.py'))['route_for']
check=runpy.run_path(str(ROOT/'skills/core/marso-image/scripts/prompt_budget.py'))['check']


class DesignTests(unittest.TestCase):
    def fixture(self):
        return {'schema':'marso/scene-design@1','run_id':'design-test','assets':[
            {'id':'bench','label':'Bench','route':'model','size_m':[2,.7,.9],
             'instances':[{'id':'b1','location':[1,2,0]},{'id':'b2','location':[3,2,0]}]}]}

    def test_plan_preserves_instances_without_detections(self):
        plan,placement=build(self.fixture())
        self.assertEqual(plan['assets'][0]['count'],2)
        self.assertIsNone(plan['assets'][0]['best_view'])
        self.assertEqual(plan['images'],[])
        self.assertEqual(len(placement['objects']),2)

    def test_invalid_design_rejected(self):
        base=self.fixture()
        for key,value in [('size_m',[1,0,1]),('route','automatic'),('effort','unlimited')]:
            doc=copy.deepcopy(base);doc['assets'][0][key]=value
            with self.assertRaises(ValueError):build(doc)
        doc=copy.deepcopy(base);doc['assets'][0]['instances'][0]['parent']='b2';doc['assets'][0]['instances'][1]['parent']='b1'
        with self.assertRaises(ValueError):build(doc)
        doc=copy.deepcopy(base);doc['assets'][0]['instances'][1]['id']='b1'
        with self.assertRaises(ValueError):build(doc)

    def test_function_overrides_size(self):
        self.assertEqual(route({'label':'small kettle','size_m':[.2,.2,.3],'parent':'table','requirements':{'articulated':True}},1)[0],'model')

    def test_skipped_support_cannot_orphan_child(self):
        doc=self.fixture()
        doc['assets'].append({'id':'cup','label':'Cup','route':'model','size_m':[.1,.1,.1],
                             'instances':[{'id':'cup1','location':[1,2,.9],'parent':'b1'}]})
        doc['assets'][0]['route']='skip'
        with self.assertRaisesRegex(ValueError,'Skipped support'):build(doc)

    def test_budget_counts_final_unicode_without_truncation(self):
        text='Metal '+chr(0x1f600)
        self.assertEqual(check(text,7)['length'],7)
        self.assertFalse(check(text,7,counting='utf16')['passed'])
        self.assertEqual(check(text,10,counting='utf8')['length'],10)
        self.assertFalse(check('Reference '+text,10)['passed'])
        with self.assertRaises(ValueError):check(text,10,counting='tokens')


if __name__=='__main__':unittest.main()
