"""okf_validate.py: hidden folders are no concepts, a link out of the KB is checked on disk, old warnings are grouped."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "okf" / "scripts" / "okf_validate.py"


@unittest.skipUnless(importlib.util.find_spec("yaml"), "okf_validate needs pyyaml")
class OkfValidate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.kb = self.root / ".hosa" / "kb"
        files = {
            ".hosa/kb/index.md": 'okf_version: "0.2"\n\n# KB\n',
            ".hosa/kb/cdc/a.md": "---\ntype: Exigence\ntitle: A\ndescription: \"A.\"\ntags: [x]\n"
                                 "generated: { by: human:t, at: '2026-01-01T00:00:00Z' }\n---\n"
                                 "[adr](../../../docs/adr.md) [perdu](../../../docs/perdu.md)\n",
            ".hosa/kb/.claude/agent-memory/x/MEMORY.md": "# mémoire, sans frontmatter\n",
            "docs/adr.md": "# ADR\n",
        }
        for i in range(5):
            files[f".hosa/kb/cdc/old{i}.md"] = "---\ntype: Exigence\n---\n"
        for rel, text in files.items():
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text(text, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def validate(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.kb), *args], capture_output=True, text=True,
                              encoding="utf-8")

    def test_hidden_folder_is_skipped_and_outside_link_checked_on_disk(self):
        r = self.validate("--all")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn(".claude", r.stdout)
        self.assertNotIn("adr.md", r.stdout)  # existe hors de la KB : pas d'avertissement
        self.assertIn("perdu.md", r.stdout)

    def test_warnings_of_unchanged_files_are_grouped(self):
        for args in (["init", "-q"], ["add", "."], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "kb"]):
            subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)
        (self.kb / "cdc" / "old0.md").write_text("---\ntype: Exigence\ntitle: Neuf\n---\n", encoding="utf-8")
        out = self.validate().stdout
        self.assertIn("cdc/old0.md: recommended field `description`", out)  # modifié : en entier
        self.assertIn("4 ×", out)  # old1..old4, sans `title` : regroupés
        self.assertNotIn("cdc/old3.md: recommended", out)
        self.assertIn("cdc/old3.md: recommended", self.validate("--all").stdout)


if __name__ == "__main__":
    unittest.main()
