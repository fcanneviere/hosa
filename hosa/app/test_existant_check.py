"""The `adoption` stage's proofs (`existant_check.py`) and how the progress plan applies them."""
import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "skills" / "adoption" / "scripts"), str(ROOT / "skills" / "status" / "scripts")]
import avancement as av  # noqa: E402
import existant_check as ex  # noqa: E402

INVENTAIRE = """---
type: Inventaire Existant
---
## Périmètre lu
- Dossiers lus : `src/` — commit : abc123 du 2026-11-01
## Stack constatée
- Django 5.1 — source : `requirements.txt:1`
## Processus constatés
- **EX1** — passer une commande
  - Code : `src/commandes.py:3`, `src/gabarits`
  - Rôles : client
  - Données : commande, ligne
  - État : complet
- **EX2** — exporter les ventes
  - Code : `src/export.py`
  - Rôles : gérant
  - État : partiel — pas de filtre par date
## Rôles constatés
- client — `src/commandes.py:1` — persona : [Claire](../personnas/claire.md)
- gérant — `src/export.py:1` — persona : aucun
## Données constatées
- commande — `src/commandes.py:2`
## Architecture constatée
- vues et modèles dans `src/`
## Tests constatés
Aucun.
## Révisions
- 2026-11-01T10:00Z — création
"""

DIAGNOSTIC = """---
type: Diagnostic Existant
---
## Sources
- [Inventaire](inventaire.md)
- [Audit qualité](../qualite/adoption.md)
## Points forts
- modèles clairs — `src/commandes.py:2` — à garder
## Problèmes
- **D1** — Bloquant — `src/commandes.py:3` — mot de passe en clair — source : sécurité
  - Proposition : corriger — exploitable
- **D2** — Mineur — `src/export.py:1` — nommage — source : qualité
  - Proposition : plus tard — touché par l'export
## Révisions
- 2026-11-01T11:00Z — création
"""

DECIDED = DIAGNOSTIC.replace("  - Proposition : corriger — exploitable\n",
                             "  - Proposition : corriger — exploitable\n  - Décision : corriger — oui\n") \
    .replace("  - Proposition : plus tard — touché par l'export\n",
             "  - Proposition : plus tard — touché par l'export\n  - Décision : plus tard — oui\n")
IDENTITY = "---\ntype: Project\nstatus: stable\n---\n## Point de départ\n{}\n- Rien de particulier.\n"


def project(inventaire=INVENTAIRE, diagnostic=DIAGNOSTIC, depart="Existant", **files) -> Path:
    """A project with its code and its KB at `<root>/.hosa/kb`. Returns the KB."""
    root = Path(tempfile.mkdtemp())
    kb = root / ".hosa" / "kb"
    code = {"requirements.txt": "django==5.1\n", "src/commandes.py": "a\nb\nc\n", "src/export.py": "x\n",
            "src/gabarits/liste.html": "<p></p>\n"}
    kbf = {"existant/inventaire.md": inventaire, "existant/diagnostic.md": diagnostic,
           "qualite/adoption.md": "---\ntype: Audit Qualité\n---\n", "personnas/claire.md": "---\ntype: Persona\n---\n## Besoins\n- commander vite\n",
           "project/identity.md": IDENTITY.format(depart), **files}
    for base, table in ((root, code), (kb, kbf)):
        for rel, text in table.items():
            if text is not None:
                (base / rel).parent.mkdir(parents=True, exist_ok=True)
                (base / rel).write_text(text, encoding="utf-8")
    return kb


def root(kb: Path) -> Path:
    return kb.parent.parent


def plan(kb, *argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = av.main([str(kb), *argv])
    return code, out.getvalue()


class Inventaire(unittest.TestCase):
    def test_a_complete_inventory_passes(self):
        kb = project()
        self.assertEqual(ex.inventaire_gaps(kb, root(kb)), [])

    def test_a_wrong_path_a_line_past_the_end_and_a_state_without_its_gap_are_refused(self):
        bad = INVENTAIRE.replace("`src/export.py`", "`src/absent.py`").replace("commandes.py:3", "commandes.py:9") \
            .replace("partiel — pas de filtre par date", "partiel").replace(" — persona : aucun", "") \
            .replace(" — source : `requirements.txt:1`", "")
        kb = project(inventaire=bad)
        gaps = "\n".join(ex.inventaire_gaps(kb, root(kb)))
        for word in ("`src/absent.py` absent", "`src/commandes.py:9` au-delà", "`État : partiel` sans",
                     "sans `persona :`", "sans `source :"):
            self.assertIn(word, gaps)

    def test_an_empty_section_and_no_process_are_refused(self):
        bad = INVENTAIRE.split("## Processus constatés")[0] + "## Processus constatés\n## Tests constatés\nAucun.\n"
        kb = project(inventaire=bad)
        gaps = "\n".join(ex.inventaire_gaps(kb, root(kb)))
        self.assertIn("aucun processus", gaps)
        self.assertIn("`## Rôles constatés` vide", gaps)


DOCS = "## Documentation constatée\n" \
       "- `README.md` — présentation — cible : `README.md` — état : à jour\n" \
       "- `doc/install.rst` — installation — cible : `docs/technique/installation.md` — état : périmé — Python 3.8 " \
       "annoncé, `requirements.txt:1` en demande plus\n" \
       "- `LICENSE.md` — licence — cible : aucune — texte juridique, gardé tel quel\n"


def with_docs(text=DOCS, **files) -> Path:
    kb = project(inventaire=INVENTAIRE.replace("## Révisions", text + "## Révisions"), **files)
    for rel in ("README.md", "doc/install.rst", "LICENSE.md", "node_modules/x/README.md", ".github/notes.md"):
        (root(kb) / rel).parent.mkdir(parents=True, exist_ok=True)
        (root(kb) / rel).write_text("x\n", encoding="utf-8")
    return kb


class Documentation(unittest.TestCase):
    def test_every_document_of_the_project_is_found_outside_dependencies(self):
        kb = with_docs()
        self.assertEqual(ex.doc_files(root(kb)), ["LICENSE.md", "README.md", "doc/install.rst"])
        self.assertEqual(ex.inventaire_gaps(kb, root(kb)), [])

    def test_a_document_missed_without_target_or_state_is_refused(self):
        kb = with_docs(DOCS.replace("- `README.md` — présentation — cible : `README.md` — état : à jour\n", "")
                       .replace(" — état : périmé — Python 3.8 annoncé, `requirements.txt:1` en demande plus", "")
                       .replace("cible : aucune — texte juridique, gardé tel quel", "cible : `docs/licence.md`"))
        gaps = "\n".join(ex.inventaire_gaps(kb, root(kb)))
        for word in ("`README.md` (documentation existante) absent", "`doc/install.rst` : `état :`",
                     "cible `docs/licence.md` hors de l'arborescence"):
            self.assertIn(word, gaps)

    def test_each_target_is_rebuilt_with_its_register_entry_citing_its_source(self):
        kb = with_docs()
        gaps = "\n".join(ex.documentation_gaps(kb, root(kb)))
        self.assertIn("`docs/technique/installation.md` pas encore reconstruit", gaps)
        self.assertIn("`kb/documentation/racine-readme.md`", gaps)       # rewritten in place: still a register entry
        (root(kb) / "docs" / "technique").mkdir(parents=True)
        (root(kb) / "docs" / "technique" / "installation.md").write_text("# Installation\n", encoding="utf-8")
        (kb / "documentation").mkdir()
        (kb / "documentation" / "technique-installation.md").write_text("sources:\n  - doc/install.rst\n", encoding="utf-8")
        (kb / "documentation" / "racine-readme.md").write_text("sources:\n  - src/\n", encoding="utf-8")
        self.assertEqual([g[:50] for g in ex.documentation_gaps(kb, root(kb))],
                         ["`kb/documentation/racine-readme.md` ne cite pas `R"])
        (kb / "documentation" / "racine-readme.md").write_text("sources:\n  - README.md\n", encoding="utf-8")
        self.assertEqual(ex.documentation_gaps(kb, root(kb)), [])

    def test_the_task_is_controlled_and_comes_after_the_inventory(self):
        self.assertEqual(av.after("adoption", "documentation"), ["inventaire"])
        self.assertIn("documentation", av.after("adoption", "diagnostic"))
        self.assertIn("documentation", av.task_controls("adoption", "documentation"))
        self.assertEqual(av.GRAPH["dispatch"]["adoption"]["model"]["hosa-documentation"], "sonnet")

    def test_the_agents_carry_the_reprise(self):
        doc = (ROOT / "agents" / "documentation.md").read_text(encoding="utf-8")
        self.assertIn("## Mode 4 — Reprise", doc)
        self.assertIn("racine-<name>.md", doc)
        self.assertIn("cible : `docs/technique/installation.md`", (ROOT / "agents" / "analyst.md").read_text(encoding="utf-8"))


class Diagnostic(unittest.TestCase):
    def test_a_complete_diagnostic_passes(self):
        kb = project()
        self.assertEqual(ex.diagnostic_gaps(kb, root(kb)), [])

    def test_a_problem_without_severity_source_or_proposal_and_a_missing_audit_are_refused(self):
        bad = DIAGNOSTIC.replace("Bloquant — ", "").replace(" — source : qualité", "") \
            .replace("  - Proposition : plus tard — touché par l'export\n", "") \
            .replace("../qualite/adoption.md", "../qualite/absent.md")
        kb = project(diagnostic=bad)
        gaps = "\n".join(ex.diagnostic_gaps(kb, root(kb)))
        for word in ("D1 : gravité", "D2 : pas de `source :`", "D2 : `Proposition :`", "`../qualite/absent.md` absent"):
            self.assertIn(word, gaps)

    def test_the_stage_needs_each_decision_and_an_existing_project(self):
        kb = project()
        gaps = "\n".join(ex.adoption_gaps(kb, root(kb)))
        self.assertIn("D1 : pas de `Décision :`", gaps)
        kb = project(diagnostic=DECIDED.replace("Décision : corriger — oui", "Décision : accepter"), depart="Neuf")
        gaps = "\n".join(ex.adoption_gaps(kb, root(kb)))
        self.assertIn("Bloquant accepté sans sa raison", gaps)
        self.assertIn("n'est pas `Existant`", gaps)
        self.assertEqual(ex.adoption_gaps(project(diagnostic=DECIDED), root(project())), [])


class Downstream(unittest.TestCase):
    def test_each_process_is_gathered_by_the_interview(self):
        cr = "---\ntype: Compte Rendu\nstatus: stable\n---\n- [x] Passer une commande (EX1)\n"
        kb = project(**{"cdc/interviews/2026-11-02-cr.md": cr})
        self.assertEqual([g[:3] for g in ex.interview_gaps(kb)], ["EX2"])
        kb = project(**{"cdc/interviews/2026-11-02-cr.md": cr + "- [x] Export (EX2, abandonné)\n"})
        self.assertEqual(ex.interview_gaps(kb), [])

    def test_each_process_kept_is_taken_over_by_an_exigence(self):
        cr = "---\ntype: Compte Rendu\n---\n- EX1\n- Export (EX2, abandonné)\n"
        exi = "---\ntype: Exigence\nexistant: [EX1]\n---\n"
        kb = project(**{"cdc/interviews/cr.md": cr, "cdc/commande.md": exi})
        self.assertEqual(ex.cdc_gaps(kb), [])
        kb = project(**{"cdc/interviews/cr.md": cr.replace(", abandonné", ""), "cdc/commande.md": exi})
        self.assertEqual([g[:3] for g in ex.cdc_gaps(kb)], ["EX2"])

    def test_each_problem_to_fix_gets_a_ticket(self):
        kb = project(diagnostic=DECIDED)
        self.assertEqual([g[:2] for g in ex.backlog_gaps(kb)], ["D1"])
        (kb / "tickets").mkdir()
        (kb / "tickets" / "mdp.md").write_text("---\ntype: Ticket\ndiagnostic: [D1]\n---\n", encoding="utf-8")
        self.assertEqual(ex.backlog_gaps(kb), [])

    def test_a_new_project_has_nothing_to_cover(self):
        kb = project(inventaire=None, diagnostic=None, depart="Neuf")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ex.main([str(kb), "backlog"]), 0)
        self.assertEqual(av.script(av.EXISTANT, kb, "interview"), [])


class Plan(unittest.TestCase):
    def test_done_adoption_reads_the_proofs(self):
        kb = project()
        self.assertIn("pas de `Décision :`", "\n".join(av.check(kb, "adoption", None)))
        self.assertEqual(av.check(project(diagnostic=DECIDED), "adoption", None), [])

    def test_an_existing_project_cannot_skip_the_stage(self):
        kb = project()
        plan(kb, "done", "hosa", "--force")
        self.assertEqual(plan(kb, "skip", "adoption", "--detail", "pas envie")[0], 1)
        kb = project(depart="Neuf")
        plan(kb, "done", "hosa", "--force")
        self.assertEqual(plan(kb, "skip", "adoption", "--detail", "projet neuf")[0], 0)
        self.assertEqual(plan(kb, "start", "interview")[0], 0)

    def test_the_inventory_task_is_controlled(self):
        kb = project(inventaire=INVENTAIRE.replace("`src/export.py`", "`src/absent.py`"))
        plan(kb, "done", "hosa", "--force")
        plan(kb, "start", "adoption")
        plan(kb, "task", "add", "adoption", "inventaire", "--agent", "hosa-analyst")
        code, out = plan(kb, "task", "done", "adoption", "inventaire", "--sortie", "kb/existant/inventaire.md")
        self.assertEqual(code, 1)
        self.assertIn("src/absent.py", out)

    def test_a_plan_past_the_interview_is_not_blocked_by_the_stage(self):
        kb = project(inventaire=None, diagnostic=None)
        path = kb / "project" / "avancement.md"
        path.write_text("## Cahier des charges\n| `hosa` | fait |  |  |\n| `interview` | fait |  |  |\n"
                        "| `redaction` | en cours |  |  |\n", encoding="utf-8")
        status = {r[0]: r[1] for rows in av.load(path)[0].values() for r in rows}
        self.assertEqual(status["adoption"], av.SKIPPED)

    def test_init_skips_the_stage_of_a_new_project(self):
        kb = project(inventaire=None, diagnostic=None, depart="Neuf")
        sections, report = av.init(kb)
        self.assertNotIn("arrêt à `hosa`", "\n".join(report))
        self.assertEqual({r[0]: r[1] for r in sections["Cahier des charges"]}["adoption"], av.SKIPPED)

    def test_the_switch_turns_the_checks_off(self):
        kb = project(diagnostic=None)
        os.environ["HOSA_ADOPTION"] = "0"
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ex.main([str(kb), "adoption"]), 0)
        finally:
            del os.environ["HOSA_ADOPTION"]


class Wiring(unittest.TestCase):
    def test_the_agent_templates_carry_each_checked_heading_and_field(self):
        agent = (ROOT / "agents" / "analyst.md").read_text(encoding="utf-8")
        for heading in (*ex.SECTIONS, "Sources", "Points forts", "Problèmes"):
            self.assertIn(f"## {heading}\n", agent)
        for field in ("Code :", "Rôles :", "État :", "persona :", "source :", "Proposition :"):
            self.assertIn(field, agent)
        self.assertIn("Décision :", (ROOT / "skills" / "adoption" / "SKILL.md").read_text(encoding="utf-8"))

    def test_downstream_skills_cite_the_ids(self):
        self.assertIn("existant: [EX1]", (ROOT / "skills/redaction/redaction-exigences.md").read_text(encoding="utf-8"))
        self.assertIn("diagnostic: [D1]", (ROOT / "skills/backlog/redaction-tickets.md").read_text(encoding="utf-8"))
        self.assertIn("back interview adoption", (ROOT / "skills/interview/SKILL.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
