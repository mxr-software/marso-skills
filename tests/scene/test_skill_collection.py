"""Validate every independently installable skill, including new entry points."""
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[2]


class SkillCollectionTests(unittest.TestCase):
    def test_isolated_packages(self):
        names = set()
        for entry in sorted((ROOT / 'skills').glob('*/*/SKILL.md')):
            with self.subTest(skill=entry.parent.name), tempfile.TemporaryDirectory() as tmp:
                package = Path(tmp) / entry.parent.name
                shutil.copytree(entry.parent, package, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                text = (package / 'SKILL.md').read_text(encoding='utf-8')
                front = yaml.safe_load(text.split('---', 2)[1])
                name = front['name']
                self.assertEqual(name, package.name)
                self.assertRegex(name, r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
                self.assertLessEqual(len(name), 64)
                self.assertNotIn(name, names)
                names.add(name)
                self.assertIsInstance(front['description'], str)
                self.assertTrue(front['description'].strip())
                self.assertLessEqual(len(front['description']), 1024)
                self.assertLessEqual(len(front['description']), 200, 'Repository account-upload compatibility limit')
                self.assertLess(len(text.splitlines()), 500)
                if 'Proprietary' in front.get('license', ''):
                    self.assertTrue((package / 'LICENSE.txt').is_file())
                metadata = package / 'agents/openai.yaml'
                if metadata.exists():
                    self.assertIsInstance(yaml.safe_load(metadata.read_text()), dict)
                for doc in package.rglob('*.md'):
                    for link in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
                        target = urlsplit(link.strip('<>'))
                        if target.scheme or not target.path:
                            continue
                        resolved = (doc.parent / unquote(target.path)).resolve()
                        self.assertTrue(resolved.is_relative_to(package.resolve()), f'{doc.name}: {link}')
                        self.assertTrue(resolved.exists(), f'{doc.name}: {link}')


if __name__ == '__main__':
    unittest.main()
