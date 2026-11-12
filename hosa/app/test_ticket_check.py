"""ticket_check.py: a file cited as existing but created by another ticket needs a `depends_on` on it;
abuse cases and legal constraints are acceptance criteria; a dependency never ranks after its ticket."""
import contextlib
import importlib.util
import io
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

    def test_more_than_ten_criteria_blocks_and_a_criterion_is_the_same_for_every_script(self):
        many = "## Critères d'acceptation\n" + "".join(f"- CA{i} — c\n" for i in range(1, 12))
        gaps = tc.gaps(self.write("gros", "priority: 1\n", many))
        self.assertIn("11 critères, 10 au plus — plusieurs variantes ou règles : découper le ticket", gaps)
        self.assertEqual(tc.criteria_ids("- CA1 — a\n  * CA2 — b\n- CA1 — a\n-CA3"), ["CA1", "CA2"])
        av_spec = importlib.util.spec_from_file_location("avancement", SCRIPT.parents[2] / "status" / "scripts" /
                                                         "avancement.py")
        av = importlib.util.module_from_spec(av_spec)
        av_spec.loader.exec_module(av)
        self.assertEqual(av.criteria("## Critères d'acceptation\n- CA1 — a\n  * CA2 — b\n"), ["CA1", "CA2"])

    def test_story_with_an_elided_que(self):
        for story in ("En tant qu'administrateur,", "En tant qu’administrateur,", "En tant que parent,"):
            self.assertNotIn("story « En tant que … » absente", tc.gaps(self.write("s", "", story + "\n")))
        self.assertIn("story « En tant que … » absente", tc.gaps(self.write("s", "", "En tant quelconque\n")))

    def test_skipped_stage_note_is_written_from_the_plan_and_accepted(self):
        plan = self.tickets.parent / "project" / "avancement.md"
        plan.parent.mkdir()
        plan.write_text("| Étape | Statut | Date | Détail |\n|---|---|---|---|\n"
                        "| `securite` | fait | 2026-11-01T10:00:00Z |  |\n"
                        "| `juridique` | non applicable | 2026-11-01T11:50:34Z | Utilisateur : usage de test |\n",
                        encoding="utf-8")
        waiting = "## Note juridique (expert conformité)\nAnalyse juridique pas encore faite — contraintes non déterminées.\n"
        body = "## Critères d'acceptation\n- CA1 — nominal\n" + waiting + "\n## Suite\nfin\n"
        p = self.write("import", "", body)
        self.assertTrue(any("encore au texte d'attente — étape `juridique` écartée" in g for g in tc.gaps(p)))
        skipped = tc.skipped_stages(self.tickets.parent)
        self.assertEqual(skipped, {"juridique": "Utilisateur : usage de test"})
        self.assertEqual(tc.write_skipped(p, skipped), ["## Note juridique (expert conformité)"])
        text = p.read_text(encoding="utf-8")
        self.assertIn("## Note juridique (expert conformité)\nNon applicable — étape `juridique` écartée : "
                      "Utilisateur : usage de test\n\n## Suite\nfin\n", text)
        self.assertTrue(text.startswith("---\ntype: Ticket\nstate: todo\n---\n## Critères d'acceptation\n"))
        self.assertFalse(any("Note juridique" in g for g in tc.gaps(p)))
        self.assertEqual(tc.write_skipped(p, skipped), [])  # written once
        absent = self.write("sans", "", "## Critères d'acceptation\n- CA1 — nominal\n")
        tc.write_skipped(absent, skipped)
        self.assertTrue(absent.read_text(encoding="utf-8").endswith(
            "\n\n## Note juridique (expert conformité)\nNon applicable — étape `juridique` écartée : "
            "Utilisateur : usage de test\n"))
        real = self.write("reel", "", JURIDIQUE)
        self.assertEqual(tc.write_skipped(real, skipped), [])  # a real note is never touched

    def test_non_applicable_note_refused_when_the_plan_keeps_the_stage(self):
        p = self.write("import", "", "## Note sécurité (expert cybersécurité)\nNon applicable — étape `securite` écartée\n")
        self.assertIn("section `## Note sécurité (expert cybersécurité)` « Non applicable » alors que le plan "
                      "d'avancement n'écarte pas l'étape `securite`", tc.gaps(p))

    def test_a_criterion_cites_rules_its_exigence_has_and_every_rule_is_cited(self):
        kb = self.tickets.parent
        (kb / "cdc").mkdir()
        (kb / "cdc" / "envoi.md").write_text(
            "---\ntype: Exigence\n---\n## Règles de gestion\n- **RG1** — une seule notification\n"
            "- **RG2** — retirée : remplacée par RG3\n- **RG3** — 50 articles au plus\n"
            "## Cas d'erreur\n- **CE1** — liste vide → refus\n", encoding="utf-8")
        (kb / "cdc" / "ancien.md").write_text("---\ntype: Exigence\n---\n## Règles de gestion\n- **RG1** — a\n", encoding="utf-8")
        story = "En tant que parent,\nLié à : [p](../personnas/p.md), [e](../cdc/envoi.md)\n## Critères d'acceptation\n"
        p = self.write("envoyer", "", story + "- CA1 [RG1, CE1] — nominal\n- CA2 [RG2] — retirée\n- CA3 [RG9] — inconnue\n- CA4 — sans règle\n")
        gaps = tc.gaps(p)
        self.assertIn("un critère cite `RG2`, absent de l'exigence liée (ou retiré)", gaps)
        self.assertIn("un critère cite `RG9`, absent de l'exigence liée (ou retiré)", gaps)
        self.assertFalse(any("`RG1`" in g or "`CE1`" in g for g in gaps))
        self.write("avant", "state: done\n", story.replace("envoi.md", "ancien.md") + "- CA1 — écrit avant les identifiants\n")
        self.assertEqual(tc.rule_coverage(kb), ["✗ cdc/envoi.md — RG3 : aucun critère de ses tickets ne les cite (`- CAn [RG3] — …`)"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(tc.main([str(kb), "--regles"]), 1)
        self.write("limite", "", story + "- CA1 [RG3] — 51e article refusé\n")   # another ticket of the exigence takes it
        self.assertEqual(tc.rule_coverage(kb), [])

    def test_dependency_ranked_after_its_ticket(self):
        self.write("journal", "priority: 43\n", "")
        self.write("fait", "state: done\n", "")
        p = self.write("pas-moi", "priority: 17\ndepends_on: [journal, fait]\n", "")
        self.assertEqual(tc.late_dependencies(p, tc.split(p.read_text(encoding="utf-8"))[0]),
                         ["dépend de `journal` (priorité 43), classé après lui → remonter `journal` avant 17"])


if __name__ == "__main__":
    unittest.main()
