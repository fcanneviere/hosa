"""ticket_check.py: a file cited as existing but created by another ticket needs a `depends_on` on it."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "backlog" / "scripts" / "ticket_check.py"
spec = importlib.util.spec_from_file_location("ticket_check", SCRIPT)
tc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tc)


def ticket(placement: str, deps: str = "") -> str:
    return f"---\ntype: Ticket\nstate: todo\n{deps}---\n## Placement architecture (architecte)\n{placement}\n"


class PhantomPaths(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.tickets = self.root / ".hosa" / "kb" / "tickets"
        self.tickets.mkdir(parents=True)
        (self.root / "core").mkdir()
        (self.root / "core" / "views.py").write_text("", encoding="utf-8")
        (self.tickets / "limite.md").write_text(ticket("- `core/limitation.py` — à créer"), encoding="utf-8")

    def check(self, text):
        p = self.tickets / "inscription.md"
        p.write_text(text, encoding="utf-8")
        return tc.phantom_paths(p, *tc.split(text))

    def test_missing_dependency_names_the_creator(self):
        gaps = self.check(ticket("- **Points d'appel** : `core/views.py:connexion` ; `core/limitation.py`"))
        self.assertEqual(gaps, ["`core/limitation.py` cité comme existant, créé par `limite` → ajouter `depends_on: [limite]`"])

    def test_dependency_kb_path_and_unknown_path(self):
        self.assertEqual(self.check(ticket("- `core/limitation.py` ; `kb/interface/lexique.md`", "depends_on: [limite]\n")), [])
        self.assertIn("absent du projet", self.check(ticket("- `core/inconnu.py`"))[0])


if __name__ == "__main__":
    unittest.main()
