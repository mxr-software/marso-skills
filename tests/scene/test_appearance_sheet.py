"""Deterministic layout/crop checks; these do not test generative image fidelity."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageDraw

SCRIPT = Path(__file__).resolve().parents[2] / 'skills/blender/marso-blender-texture/scripts/contact_sheet.py'
spec = importlib.util.spec_from_file_location('appearance_sheet', SCRIPT)
sheet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sheet)


class AppearanceSheetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'master.png'
        Image.new('RGB', (60, 100), 'white').save(self.source)

    def test_rectangles_preserve_identity_on_two_grid_sizes(self):
        for columns, rows, width, height in [(2, 3, 2048, 2048), (3, 5, 4096, 4096), (3, 5, 205, 307)]:
            ids = [f'style_{i}' for i in range(columns * rows)]
            base = self.root / f'grid_{columns}_{width}'
            doc = sheet.build(self.source, base, ids, columns, rows, width, height, 3)
            # Synthetic editing fixture: each saved cell receives its known test colour.
            image = Image.new('RGB', (width, height), 'black')
            draw = ImageDraw.Draw(image)
            for i, cell in enumerate(doc['cells']):
                x0, y0, x1, y1 = cell['box']
                draw.rectangle((x0, y0, x1-1, y1-1), fill=(10+i, 30+i, 60+i))
            edited = base / 'edited.png'
            image.save(edited)
            result = sheet.split(edited, base / 'layout.json', base / 'crops')
            self.assertEqual(len(result['crops']), len(ids))
            for i, crop in enumerate(result['crops']):
                with Image.open(base / 'crops' / crop['file']) as out:
                    self.assertEqual(out.getextrema(), ((10+i,10+i),(30+i,30+i),(60+i,60+i)))

    def test_changed_dimensions_require_explicit_proportional_scaling(self):
        base = self.root / 'grid'
        doc = sheet.build(self.source, base, ['a','b'], 2, 1, 200, 100, 4)
        edited = self.root / 'double.png'
        Image.new('RGB', (400,200), 'white').save(edited)
        out = self.root / 'crops'
        with self.assertRaises(ValueError):
            sheet.split(edited, base/'layout.json', out)
        self.assertFalse(out.exists())
        result = sheet.split(edited, base/'layout.json', out, allow_scale=True, ids=['b'])
        self.assertEqual(result['crops'][0]['box'], [v*2 for v in doc['cells'][1]['box']])
        self.assertEqual(len(result['crops']), 1)
        Image.new('RGB', (401,200), 'white').save(edited)
        with self.assertRaises(ValueError):
            sheet.split(edited, base/'layout.json', self.root/'bad-aspect', allow_scale=True)

    def test_bad_identity_and_bounds_never_write_outputs(self):
        for ids in [['../escape'], ['a','a'], ['a','A'], ['CON']]:
            with self.assertRaises(ValueError):
                sheet.build(self.source, self.root/'invalid', ids, 2, 1, 200, 100)
            self.assertFalse((self.root/'invalid').exists())
        base = self.root/'grid'
        doc = sheet.build(self.source, base, ['a'], 1, 1, 100, 100)
        for box in [[-1,0,50,50], [0,0,101,100], [2,2,2,50]]:
            doc['cells'][0]['box'] = box
            (base/'layout.json').write_text(json.dumps(doc))
            with self.assertRaises(ValueError):
                sheet.split(base/'sheet.png',base/'layout.json',self.root/'invalid')
            self.assertFalse((self.root/'invalid').exists())

    def test_outputs_and_sources_are_not_overwritten(self):
        original = self.source.read_bytes()
        base=self.root/'grid'
        sheet.build(self.source, base, ['a'], 1, 1, 100, 100)
        before=(base/'sheet.png').read_bytes()
        with self.assertRaises(FileExistsError):
            sheet.build(self.source, base, ['a'], 1, 1, 100, 100)
        self.assertEqual((base/'sheet.png').read_bytes(),before)
        self.assertEqual(self.source.read_bytes(),original)
        with self.assertRaises(ValueError):
            sheet.split(base/'sheet.png',base/'layout.json',self.root/'unknown',ids=['missing'])

    def test_portrait_grid_preserves_shape_and_composites_on_black(self):
        source = Image.new('RGBA', (20, 40), (0, 0, 0, 0))
        ImageDraw.Draw(source).rectangle((4, 4, 15, 35), fill=(255, 255, 255, 255))
        source.save(self.source)
        base = self.root/'portrait'
        ids = [f'look-{i}' for i in range(6)]
        doc = sheet.build(self.source, base, ids, 3, 2, 180, 270, gutter=4)
        with Image.open(base/'sheet.png') as out:
            self.assertEqual(out.size, (180, 270))
            self.assertEqual(out.getpixel((0, 0)), (0, 0, 0))
            for cell in doc['cells']:
                crop = out.crop(cell['box'])
                bounds = crop.getbbox()
                self.assertIsNotNone(bounds)
                # Source silhouette is 12:32; fitting must not stretch it to the cell.
                ratio = (bounds[2]-bounds[0]) / (bounds[3]-bounds[1])
                self.assertAlmostEqual(ratio, 12/32, delta=.05)
                self.assertEqual(crop.getpixel((0, 0)), (0, 0, 0))
        self.assertEqual(doc['background_rgb'], [0, 0, 0])
        light = self.root/'light'
        sheet.build(self.source, light, ['a'], 1, 1, 60, 100, background='white')
        with Image.open(light/'sheet.png') as out:
            self.assertEqual(out.getpixel((0, 0)), (255, 255, 255))

    def test_invalid_background_does_not_write(self):
        out = self.root/'invalid-colour'
        with self.assertRaises(ValueError):
            sheet.build(self.source, out, ['a'], 1, 1, 100, 100, background='not-a-colour')
        self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
