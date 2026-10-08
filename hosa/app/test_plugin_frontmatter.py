"""Every skill and agent of the plugin must have valid YAML frontmatter with a name and a description."""
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


class PluginFrontmatter(unittest.TestCase):
    def test_skills_and_agents_parse(self):
        files = list((ROOT / "skills").glob("*/SKILL.md")) + [p for p in (ROOT / "agents").glob("*.md") if p.name != "README.md"]
        self.assertGreater(len(files), 50)
        for f in files:
            with self.subTest(file=f.relative_to(ROOT).as_posix()):
                m = re.match(r"^---\n(.*?)\n---", f.read_text(encoding="utf-8"), re.S)
                self.assertIsNotNone(m, "no frontmatter")
                meta = yaml.safe_load(m.group(1))
                self.assertTrue(meta.get("name"))
                self.assertIsInstance(meta.get("description"), str)
                self.assertLessEqual(len(meta["description"].split()), 60, "description too long — it loads in every session")


if __name__ == "__main__":
    unittest.main()
