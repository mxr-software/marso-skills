"""The skill folder installs on its own: no sibling paths, links resolve, every script is used."""
import os
import re
import unittest

from helpers import SKILL, SCRIPTS


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class PackageTests(unittest.TestCase):
    def test_frontmatter_names_the_folder(self):
        head = read(os.path.join(SKILL, "SKILL.md")).split("---")[1]
        self.assertIn(f"name: {os.path.basename(SKILL)}\n", head)
        self.assertRegex(head, r"\ndescription: .{40,}")

    def test_every_relative_link_resolves_inside_the_folder(self):
        for folder, _, files in os.walk(SKILL):
            for name in files:
                if not name.endswith(".md"):
                    continue
                path = os.path.join(folder, name)
                for target in re.findall(r"\]\(([^)#]+)\)", read(path)):
                    if "://" in target:
                        continue
                    resolved = os.path.normpath(os.path.join(folder, target))
                    self.assertTrue(os.path.exists(resolved), f"{name} links to missing {target}")
                    self.assertTrue(resolved.startswith(SKILL), f"{name} links outside the skill: {target}")

    def test_no_script_reaches_outside_the_folder(self):
        for name in os.listdir(SCRIPTS):
            if name.endswith(".py"):
                body = read(os.path.join(SCRIPTS, name))
                self.assertNotIn("parents[2]", body, name)
                self.assertNotIn("HERE.parent.parent", body, name)

    def test_every_script_is_run_or_named(self):
        text = "".join(read(os.path.join(SCRIPTS, n)) for n in ("fast.py", "plan_fast.py", "merge_tiles.py"))
        text += read(os.path.join(SKILL, "SKILL.md"))
        for name in os.listdir(SCRIPTS):
            if name.endswith(".py"):
                self.assertIn(name[:-3], text, f"{name} is shipped but nothing runs it")

    def test_crops_do_not_copy_the_embedded_photograph_into_markup(self):
        """151 crops of a 5 MB data URI overflowed the browser's string limit in the Gallery."""
        body = read(os.path.join(SKILL, "assets", "viewer_template.html"))
        crop = body[body.index("function cropImg("):body.index("function fillCrops(")]
        self.assertNotIn("im.src", crop)
        self.assertIn("fillCrops(galleryEl)", body)

    def test_the_briefs_name_files_that_ship(self):
        body = read(os.path.join(SCRIPTS, "plan_fast.py"))
        for ref in re.findall(r"REFERENCES / '([\w.]+)'", body):
            self.assertTrue(os.path.exists(os.path.join(SKILL, "references", ref)), ref)
        for script in re.findall(r"SCRIPTS / '([\w.]+)'", body):
            self.assertTrue(os.path.exists(os.path.join(SCRIPTS, script)), script)


if __name__ == "__main__":
    unittest.main()
