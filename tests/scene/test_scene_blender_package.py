"""The scene planning and Blender scene skills install on their own: frontmatter, links, licence, scripts."""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILLS = [os.path.join(ROOT, "skills", *parts) for parts in (
    ("core", "marso-scene-graph"),
    ("blender", "marso-blender-scene-assets"),
    ("blender", "marso-blender-place-scene"),
)]


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class PackageTests(unittest.TestCase):
    def test_frontmatter_licence_and_metadata(self):
        for skill in SKILLS:
            head = read(os.path.join(skill, "SKILL.md")).split("---")[1]
            self.assertIn(f"name: {os.path.basename(skill)}\n", head, skill)
            self.assertRegex(head, r"\ndescription: .{40,}")
            self.assertIn("license: Proprietary", head, skill)
            self.assertTrue(os.path.exists(os.path.join(skill, "LICENSE.txt")), skill)
            self.assertIn("display_name:", read(os.path.join(skill, "agents", "openai.yaml")))

    def test_every_relative_link_resolves_inside_the_folder(self):
        for skill in SKILLS:
            for folder, _, files in os.walk(skill):
                for name in files:
                    if not name.endswith(".md"):
                        continue
                    for target in re.findall(r"\]\(([^)#]+)\)", read(os.path.join(folder, name))):
                        if "://" in target:
                            continue
                        resolved = os.path.normpath(os.path.join(folder, target))
                        self.assertTrue(os.path.exists(resolved), f"{name} links to missing {target}")
                        self.assertTrue(resolved.startswith(skill), f"{name} links outside the skill: {target}")

    def test_every_script_is_named_and_reaches_nothing_outside(self):
        for skill in SKILLS:
            text = "".join(read(os.path.join(folder, n)) for folder, _, files in os.walk(skill)
                           for n in files if n.endswith(".md"))
            scripts = os.path.join(skill, "scripts")
            for name in os.listdir(scripts):
                if name.endswith(".py"):
                    self.assertIn(name, text, f"{name} is shipped but no instruction names it")
                    body = read(os.path.join(scripts, name))
                    self.assertNotIn("parents[", body, name)
                    self.assertNotIn("../", body, name)


if __name__ == "__main__":
    unittest.main()
