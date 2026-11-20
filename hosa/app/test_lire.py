"""lire.py gives a part of a file, numbered, under a cap: a range, a Markdown section, the outline past the cap."""
import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "using-hosa" / "scripts" / "lire.py"
spec = importlib.util.spec_from_file_location("lire", SCRIPT)
lire = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lire)


def run(*args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = lire.main([str(a) for a in args])
    return code, buf.getvalue()


class Lire(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.code = d / "app.py"
        self.code.write_text("".join(f"x{i} = {i}\n" for i in range(1, 51)) + "def calcul(a):\n    return a\n", encoding="utf-8")
        self.md = d / "ticket.md"
        self.md.write_text("---\ntype: Ticket\n---\n# Titre\n## Histoire\nEn tant que…\n### Détail\nici\n"
                           "## Critères d'acceptation\n- CA1\n```\n## pas un titre\n```\n## Notes\nfin\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_range_forms_are_numbered(self):
        _, out = run(f"{self.code}:10-12")
        self.assertIn("lignes 10-12 sur 52", out)
        self.assertIn("10\tx10 = 10\n", out)
        self.assertNotIn("x13", out)
        _, out = run(f"{self.code}:10:2")
        self.assertIn("lignes 10-11", out)
        _, out = run(f"{self.code}:51")
        self.assertIn("lignes 51-52", out)

    def test_section_stops_at_same_level_and_skips_fences(self):
        _, out = run(f"{self.md}#Histoire")
        self.assertIn("En tant que", out)
        self.assertIn("### Détail", out)
        self.assertNotIn("CA1", out)
        _, out = run(f"{self.md}#critères")
        self.assertIn("## pas un titre", out)  # inside a fence: part of the section, not a heading
        self.assertNotIn("fin", out)

    def test_missing_section_lists_headings(self):
        code, out = run(f"{self.md}#Inconnu")
        self.assertEqual(code, 1)
        self.assertIn("## Notes", out)
        self.assertNotIn("pas un titre", out)

    def test_over_the_cap_gives_the_outline(self):
        code, out = run(self.code, "--max-chars", "100")
        self.assertEqual(code, 0)
        self.assertIn("au-delà du plafond", out)
        self.assertIn("51\tdef calcul(a):", out)
        self.assertNotIn("x20 = 20", out)

    def test_targets_share_the_cap(self):
        _, out = run(self.md, self.code, "--max-chars", "400")
        self.assertIn("En tant que", out)
        self.assertIn("au-delà du plafond", out)

    def test_missing_file_suggests_close_names(self):
        code, out = run(Path(self.tmp.name) / "tiket.md")
        self.assertEqual(code, 1)
        self.assertIn("ticket.md", out)

    def test_windows_drive_path_is_not_a_range(self):
        self.assertEqual(lire.parse("C:/dev/a.md"), ("C:/dev/a.md", None, None, None))
        self.assertEqual(lire.parse("C:/dev/a.md:3-4"), ("C:/dev/a.md", 3, 4, None))


if __name__ == "__main__":
    unittest.main()
