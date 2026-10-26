"""ticket_check.py: a file cited as existing but created by another ticket needs a `depends_on` on it;
abuse cases and legal constraints are acceptance criteria; a dependency never ranks after its ticket."""
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


SECURITE = """## Note sécurité (expert cybersécurité)
- **Règles** : `limitation-de-debit` — 10 échecs par 15 min par couple
- **Cas d'abus** :
  - Étant donné un attaquant, quand il essaie 11 mots de passe, alors le 11e est refusé → CA2
  - Étant donné un attaquant, quand il forge `X-Forwarded-For`, alors l'adresse réelle compte
- **Contrôle d'accès** : aucun
- **Journalisation** : `connexion_refusee` au journal technique
- **Données sensibles** : mot de passe — jamais au journal
"""

JURIDIQUE = """## Note juridique (expert conformité)
- **Contraintes** : aucun
- **Données personnelles** : traitement 1 — identifiant — contrat — 12 mois
- **Hors logiciel** : aucun
"""


class SecurityAndLegalNotes(unittest.TestCase):
    def setUp(self):
        self.tickets = Path(tempfile.mkdtemp()) / "tickets"
        self.tickets.mkdir()

    def write(self, slug, front, body):
        p = self.tickets / f"{slug}.md"
        state = "" if "state:" in front else "state: todo\n"
        p.write_text(f"---\ntype: Ticket\n{state}{front}---\n{body}", encoding="utf-8")
        return p

    def test_abuse_case_without_criterion_and_unknown_criterion(self):
        body = "## Critères d'acceptation\n- CA1 — nominal\n" + SECURITE + JURIDIQUE
        gaps = tc.gaps(self.write("connexion", "", body))
        self.assertTrue(any("sans critère" in g and "X-Forwarded-For" in g for g in gaps))
        self.assertIn("`Note sécurité (expert cybersécurité)` cite `CA2`, absent des critères d'acceptation", gaps)

    def test_legal_note_required_with_its_bullets(self):
        body = "## Critères d'acceptation\n- CA1 — nominal\n- CA2 — refus\n" + SECURITE.replace(
            "l'adresse réelle compte", "l'adresse réelle compte → CA1")
        gaps = tc.gaps(self.write("connexion", "", body))
        self.assertIn("section `## Note juridique (expert conformité)` absente", gaps)
        self.assertFalse(any("sans critère" in g for g in gaps))
        gaps = tc.gaps(self.write("connexion", "", body + JURIDIQUE.replace("- **Hors logiciel** : aucun\n", "")))
        self.assertIn("`Note juridique (expert conformité)` : puce « Hors logiciel » absente", gaps)

    def test_dependency_ranked_after_its_ticket(self):
        self.write("journal", "priority: 43\n", "")
        self.write("fait", "state: done\n", "")
        p = self.write("pas-moi", "priority: 17\ndepends_on: [journal, fait]\n", "")
        self.assertEqual(tc.late_dependencies(p, tc.split(p.read_text(encoding="utf-8"))[0]),
                         ["dépend de `journal` (priorité 43), classé après lui → remonter `journal` avant 17"])


if __name__ == "__main__":
    unittest.main()
