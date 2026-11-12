"""kb_query.py reads the KB's frontmatter as YAML would: lists, quoted values, hidden folders, output cap."""
import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "okf" / "scripts" / "kb_query.py"
spec = importlib.util.spec_from_file_location("kb_query", SCRIPT)
kb_query = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kb_query)


def run(*args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        kb_query.main([str(a) for a in args])
    return buf.getvalue()


class KbQuery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.kb = Path(self.tmp.name)
        files = {
            "cdc/a.md": '---\ntype: Exigence\nespace: [front-office, "back-office"]\ndescription: "Dit \\"oui\\"."\n---\n',
            "cdc/b.md": "---\ntype: Exigence\nespace:\n  - back-office\ntags:\n- securite\n---\n",
            "cdc/c.md": "---\ntype: Exigence\nespace: front-office\n---\n## Objectif\n" + "x" * 500 + "\n",
            ".claude/agent-memory/m.md": "---\ntype: Exigence\nespace: front-office\n---\n",
        }
        for rel, text in files.items():
            (self.kb / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.kb / rel).write_text(text, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_split_reads_lists_and_quoted_values(self):
        fm, _ = kb_query.split((self.kb / "cdc/a.md").read_text(encoding="utf-8"))
        self.assertEqual(fm["espace"], ["front-office", "back-office"])
        self.assertEqual(fm["description"], 'Dit "oui".')
        fm, _ = kb_query.split((self.kb / "cdc/b.md").read_text(encoding="utf-8"))
        self.assertEqual((fm["espace"], fm["tags"]), (["back-office"], ["securite"]))

    def test_equality_matches_one_item_of_a_list(self):
        self.assertEqual(run(self.kb, "--where", "espace=front-office", "--count").strip(), "2")  # a, c ; pas .claude
        self.assertEqual(run(self.kb, "--where", "espace=back-office", "--count").strip(), "2")  # a (flux), b (bloc)
        self.assertEqual(run(self.kb, "--where", "tags~secu", "--count").strip(), "1")

    def test_one_long_concept_is_shown_whole(self):  # relecture, cahier des charges : lus en entier par les audits
        self.assertIn("x" * 500, run(self.kb, "--slug", "c", "--full", "--max-chars", "100"))


if __name__ == "__main__":
    unittest.main()
