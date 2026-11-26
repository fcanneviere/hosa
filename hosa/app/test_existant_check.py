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
## Interface constatée
- Liste des commandes — source : `src/gabarits/liste.html` — client
## Fondamentaux constatés
- connexion — source : `src/commandes.py:1` — sans limite de tentatives
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
            .replace(" — source : `requirements.txt:1`", "").replace("source : `src/gabarits/liste.html`", "`x`")
        kb = project(inventaire=bad)
        gaps = "\n".join(ex.inventaire_gaps(kb, root(kb)))
        for word in ("`src/absent.py` absent", "`src/commandes.py:9` au-delà", "`État : partiel` sans",
                     "sans `persona :`", "sans `source :", "`## Interface constatée` :"):
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
        problems = lambda: [g[:2] for g in ex.backlog_gaps(kb) if g.startswith("D")]  # noqa: E731
        self.assertEqual(problems(), ["D1"])
        (kb / "tickets").mkdir()
        (kb / "tickets" / "mdp.md").write_text("---\ntype: Ticket\ndiagnostic: [D1]\n---\n", encoding="utf-8")
        self.assertEqual(problems(), [])


def ticket(slug: str, kb: Path, state="todo", existant="", body="") -> None:
    (kb / "tickets").mkdir(exist_ok=True)
    head = f"---\ntype: Ticket\nstate: {state}\n" + (f"existant: [{existant}]\n" if existant else "") + "---\n"
    (kb / "tickets" / f"{slug}.md").write_text(head + body, encoding="utf-8")


CRITERIA = "## Critères d'acceptation\n- CA1 [R1] — commande créée\n- CA2 [R2] — total juste\n"


class Backlog(unittest.TestCase):
    """What the existing code does is a delivered ticket, never one to build again."""

    def setUp(self):
        self.kb = project(diagnostic=DECIDED)
        ticket("mdp", self.kb)  # the ticket of D1, decided `corriger`
        (self.kb / "tickets" / "mdp.md").write_text("---\ntype: Ticket\ndiagnostic: [D1]\n---\n", encoding="utf-8")

    def gaps(self):
        return "\n".join(ex.backlog_gaps(self.kb))

    def test_a_process_the_code_does_needs_its_delivered_ticket_and_a_partial_one_its_gap(self):
        gaps = self.gaps()
        self.assertIn("EX1 (complet) : aucun ticket `state: done`", gaps)
        self.assertIn("EX2 (partiel) : aucun ticket `state: done`", gaps)
        self.assertIn("EX2 (partiel) : aucun ticket `todo`", gaps)

    def test_a_delivered_ticket_proves_each_criterion_with_a_path_that_exists(self):
        ticket("commande", self.kb, "done", "EX1", CRITERIA + "## Preuve\n- CA1 — `src/commandes.py:3`\n")
        self.assertIn("`commande` CA2 : absent de `## Preuve`", self.gaps())
        ticket("commande", self.kb, "done", "EX1", CRITERIA + "## Preuve\n- CA1 — `src/commandes.py:3`\n"
                                                             "- CA2 — `tests/absent.py`\n")
        self.assertIn("`tests/absent.py` absent", self.gaps())
        ticket("commande", self.kb, "done", "EX1", CRITERIA)
        self.assertIn("`commande` (livré, code existant) : pas de `## Preuve`", self.gaps())

    def test_a_todo_ticket_on_existing_code_says_what_it_changes(self):
        ticket("export", self.kb, "todo", "EX2", "## Critères d'acceptation\n- CA1 — filtre par date\n")
        self.assertIn("`export` (todo, EX2 partiel) : pas de `## Écart à l'existant`", self.gaps())

    def test_a_complete_backlog_passes(self):
        proof = "## Preuve\n- CA1 — `src/commandes.py:3`\n- CA2 — `src/commandes.py:2` (aucun test)\n"
        ticket("commande", self.kb, "done", "EX1", CRITERIA + proof)
        ticket("export-actuel", self.kb, "done", "EX2", "## Critères d'acceptation\n- CA1 — export\n"
                                                        "## Preuve\n- CA1 — `src/export.py`\n")
        ticket("export-dates", self.kb, "todo", "EX2", "## Écart à l'existant\nAujourd'hui sans filtre "
                                                       "(`src/export.py:1`) ; ajoute le filtre par date.\n")
        self.assertEqual(ex.backlog_gaps(self.kb), [])

    def test_a_dropped_process_needs_no_ticket(self):
        (self.kb / "cdc" / "interviews").mkdir(parents=True)
        (self.kb / "cdc" / "interviews" / "cr.md").write_text("- EX1\n- Export (EX2, abandonné)\n", encoding="utf-8")
        self.assertNotIn("EX2", self.gaps())

    def test_the_ticket_guide_carries_the_rules(self):
        guide = (ROOT / "skills/backlog/redaction-tickets.md").read_text(encoding="utf-8")
        for word in ("existant: [EX1]", "## Preuve", "## Écart à l'existant", "state: done"):
            self.assertIn(word, guide)

    def test_a_new_project_has_nothing_to_cover(self):
        kb = project(inventaire=None, diagnostic=None, depart="Neuf")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ex.main([str(kb), "backlog"]), 0)
        self.assertEqual(av.script(av.EXISTANT, kb, "interview"), [])


def reprise(kb: Path, *rows: str) -> None:
    (kb / "stack").mkdir(exist_ok=True)
    (kb / "stack" / "existant.md").write_text("---\ntype: Stack Decision\n---\n## Stack reprise\n"
                                             + "".join(f"- {r}\n" for r in rows), encoding="utf-8")


class Stack(unittest.TestCase):
    """The stack in place is kept, or replaced for a reason the user decided, at a stated cost."""

    def setUp(self):
        self.kb = project(diagnostic=DECIDED)

    def gaps(self):
        return "\n".join(ex.stack_gaps(self.kb))

    def test_each_element_found_must_be_taken_over(self):
        self.assertIn("pas de `kb/stack/existant.md`", self.gaps())
        reprise(self.kb, "Python 3.12 — source : `src/commandes.py:1` — conservé")
        self.assertIn("« Django 5.1 » (`requirements.txt:1`) absent de `## Stack reprise`", self.gaps())

    def test_kept_passes(self):
        reprise(self.kb, "Django 5.1 — source : `requirements.txt:1` — conservé")
        self.assertEqual(ex.stack_gaps(self.kb), [])

    def test_a_replacement_needs_a_decided_reason_and_its_migration_cost(self):
        reprise(self.kb, "Django 5.1 — source : `requirements.txt:1` — remplacé par FastAPI — raison : plus moderne")
        gaps = self.gaps()
        self.assertIn("remplacé sans `raison :`", gaps)
        self.assertIn("remplacé sans `migration :`", gaps)
        reprise(self.kb, "Django 5.1 — source : `requirements.txt:1` — remplacé par FastAPI — raison : D2 — "
                         "migration : 12 vues")
        self.assertIn("remplacé sans `raison :`", self.gaps())  # D2 is decided `plus tard`, not `corriger`
        reprise(self.kb, "Django 5.1 — source : `requirements.txt:1` — remplacé par FastAPI — raison : D1 — "
                         "migration : 12 vues")
        self.assertEqual(ex.stack_gaps(self.kb), [])

    def test_a_replacement_for_an_exigence_passes(self):
        (self.kb / "cdc").mkdir(exist_ok=True)
        (self.kb / "cdc" / "temps-reel.md").write_text("---\ntype: Exigence\n---\n", encoding="utf-8")
        reprise(self.kb, "Django 5.1 — source : `requirements.txt:1` — remplacé par Channels — raison : "
                         "[temps réel](../cdc/temps-reel.md) — migration : 3 vues")
        self.assertEqual(ex.stack_gaps(self.kb), [])

    def test_done_stack_reads_it_and_a_new_project_has_nothing_to_keep(self):
        self.assertIn("existant_check", "\n".join(av.check(self.kb, "stack", None)))
        kb = project(inventaire=None, diagnostic=None, depart="Neuf")
        self.assertNotIn("existant_check", "\n".join(av.check(kb, "stack", None)))


TESTS = INVENTAIRE.replace("## Tests constatés\nAucun.", "## Tests constatés\n- pytest — 3 tests dans `tests/` — "
                                                         "commandes — non lancés (pas d'environnement avant `infra`)")
FAILED = "  - Décision : plus tard — oui\n- **D3** — À corriger — `tests/test_commandes.py:1` — test en échec — source : tests\n" \
         "  - Proposition : corriger — la règle du total\n"


def first_run(kb: Path, *rows: str) -> None:
    (kb / "infra").mkdir(exist_ok=True)
    (kb / "infra" / "environnement-docker.md").write_text(
        "---\ntype: Infra\n---\n## Tests existants\n" + "".join(f"- {r}\n" for r in rows), encoding="utf-8")


class Infra(unittest.TestCase):
    """The existing tests run once before any sprint; each failure is a problem the user decides, set aside."""

    def setUp(self):
        self.kb = project(inventaire=TESTS, diagnostic=DECIDED.replace("  - Décision : plus tard — oui\n", FAILED))
        (root(self.kb) / "tests").mkdir()
        (root(self.kb) / "tests" / "test_commandes.py").write_text("def test_total(): ...\n", encoding="utf-8")

    def gaps(self):
        return "\n".join(ex.infra_gaps(self.kb, root(self.kb)))

    def test_the_first_run_is_required(self):
        self.assertIn("sans `## Tests existants`", self.gaps())
        first_run(self.kb, "Tests : `pytest`")
        self.assertIn("pas de ligne `- Premier lancement", self.gaps())

    def test_each_failure_is_listed_with_its_decided_problem_and_set_aside(self):
        first_run(self.kb, "Premier lancement : `pytest` — 3 tests — 1 passés — 2 en échec",
                  "`tests/absent.py::test_x` — ImportError")
        gaps = self.gaps()
        for word in ("2 en échec annoncés, 1 listés", "`tests/absent.py` absent", "sans son problème `Dn`",
                     "sans `exclu :`"):
            self.assertIn(word, gaps)
        first_run(self.kb, "Premier lancement : `pytest` — 3 tests — 2 passés — 1 en échec",
                  "`tests/test_commandes.py::test_total` — AssertionError — D3 — exclu : `xfail(strict=True, reason=\"D3\")`")
        self.assertIn("D3 (`tests/test_commandes.py::test_total` en échec) : pas de `Décision :`", self.gaps())
        first_run(self.kb, "Premier lancement : `pytest` — 3 tests — 2 passés — 1 en échec",
                  "`tests/test_commandes.py::test_total` — AssertionError — D1 — exclu : désélectionné")
        self.assertIn("D1 : `source : tests` attendu", self.gaps())

    def test_a_decided_failure_passes_and_a_green_run_needs_no_problem(self):
        self.kb.joinpath("existant/diagnostic.md").write_text(DECIDED.replace(
            "  - Décision : plus tard — oui\n", FAILED + "  - Décision : corriger — oui\n"), encoding="utf-8")
        first_run(self.kb, "Premier lancement : `pytest` — 3 tests — 2 passés — 1 en échec",
                  "`tests/test_commandes.py::test_total` — AssertionError — D3 — exclu : `xfail(strict=True, reason=\"D3\")`")
        self.assertEqual(ex.infra_gaps(self.kb, root(self.kb)), [])
        first_run(self.kb, "Premier lancement : `pytest` — 3 tests — 3 passés — 0 en échec")
        self.assertEqual(ex.infra_gaps(self.kb, root(self.kb)), [])

    def test_done_infra_reads_it_and_a_project_without_tests_has_nothing_to_run(self):
        self.assertIn("existant_check", "\n".join(av.check(self.kb, "infra", None)))
        kb = project(diagnostic=DECIDED)
        self.assertEqual(ex.infra_gaps(kb, root(kb)), [])
        self.assertNotIn("existant_check", "\n".join(av.check(kb, "infra", None)))

    def test_the_agent_carries_the_format(self):
        agent = (ROOT / "agents" / "infra.md").read_text(encoding="utf-8")
        for word in ("## Tests existants", "Premier lancement :", "source : tests", "exclu :"):
            self.assertIn(word, agent)
        self.assertIn("source : qualité | sécurité | bdd | inventaire | tests",
                      (ROOT / "agents" / "analyst.md").read_text(encoding="utf-8"))


def reprises(kb: Path, *rows: str) -> None:
    (kb / "infra").mkdir(exist_ok=True)
    (kb / "infra" / "schema-base-de-donnees.md").write_text(
        "---\ntype: Infra\n---\n## Schéma de la base de données\n## Données reprises\n"
        + "".join(f"- {r}\n" for r in rows), encoding="utf-8")


class SchemaDb(unittest.TestCase):
    """The data the existing code stores is kept, changed by a new migration, or dropped for a decided reason."""

    def setUp(self):
        self.kb = project(diagnostic=DECIDED)

    def gaps(self):
        return "\n".join(ex.schema_db_gaps(self.kb, root(self.kb)))

    def test_each_table_found_must_be_taken_over(self):
        self.assertIn("sans `## Données reprises`", self.gaps())
        reprises(self.kb, "ligne — source : `src/export.py` — conservée")
        self.assertIn("« commande » (`src/commandes.py:2`) absent de `## Données reprises`", self.gaps())
        reprises(self.kb, "commande — source : `src/commandes.py:2` — gardée")
        self.assertIn("ni `conservée`", self.gaps())
        reprises(self.kb, "commande — source : `src/commandes.py:2` — conservée")
        self.assertEqual(ex.schema_db_gaps(self.kb, root(self.kb)), [])

    def test_a_change_needs_its_new_migration_and_what_the_rows_become(self):
        reprises(self.kb, "commande — source : `src/commandes.py:2` — modifiée")
        gaps = self.gaps()
        self.assertIn("modifiée sans `reprise :`", gaps)
        self.assertIn("modifiée sans `migration :`", gaps)
        reprises(self.kb, "commande — source : `src/commandes.py:2` — modifiée — migration : "
                          "`migrations/0002_total.py` — reprise : total recalculé")
        self.assertIn("migration `migrations/0002_total.py` absente", self.gaps())
        (root(self.kb) / "migrations").mkdir()
        (root(self.kb) / "migrations" / "0002_total.py").write_text("ops = []\n", encoding="utf-8")
        self.assertEqual(ex.schema_db_gaps(self.kb, root(self.kb)), [])

    def test_a_drop_needs_a_decided_reason(self):
        reprises(self.kb, "commande — source : `src/commandes.py:2` — supprimée — raison : D2 — reprise : export CSV")
        self.assertIn("supprimée sans `raison :`", self.gaps())  # D2 is decided `plus tard`
        reprises(self.kb, "commande — source : `src/commandes.py:2` — supprimée — raison : D1 — reprise : export CSV")
        self.assertEqual(ex.schema_db_gaps(self.kb, root(self.kb)), [])

    def test_done_schema_db_reads_it_and_a_project_without_data_has_nothing_to_keep(self):
        self.assertIn("Données reprises", "\n".join(av.check(self.kb, "schema-db", None)))
        kb = project(inventaire=INVENTAIRE.replace("- commande — `src/commandes.py:2`\n", "Aucun.\n"))
        self.assertEqual(ex.schema_db_gaps(kb, root(kb)), [])
        new = project(inventaire=None, diagnostic=None, depart="Neuf")
        self.assertNotIn("Données reprises", "\n".join(av.check(new, "schema-db", None)))

    def test_the_agents_carry_the_format(self):
        agent = (ROOT / "agents" / "data-engineer.md").read_text(encoding="utf-8")
        for word in ("## Données reprises", "conservée", "modifiée", "supprimée", "migration :", "reprise :",
                     "raison :"):
            self.assertIn(word, agent)
        self.assertIn("Données reprises", (ROOT / "agents" / "dba.md").read_text(encoding="utf-8"))


def archi(kb: Path, *rows: str) -> None:
    (kb / "infra").mkdir(exist_ok=True)
    (kb / "infra" / "architecture-existante.md").write_text(
        "---\ntype: Infra\n---\n## Architecture reprise\n" + "".join(f"- {r}\n" for r in rows), encoding="utf-8")


class Architecture(unittest.TestCase):
    """The architecture in place is kept, extended, or replaced for a decided reason with what moves."""

    def setUp(self):
        self.kb = project(diagnostic=DECIDED)

    def gaps(self):
        return "\n".join(ex.architecture_gaps(self.kb))

    def test_each_layer_found_must_be_taken_over(self):
        self.assertIn("sans `## Architecture reprise`", self.gaps())
        archi(self.kb, "export — `src/export.py` — conservé")
        self.assertIn("« vues et modèles dans `src/` » (`src/`) absent", self.gaps())
        archi(self.kb, "vues et modèles — `src/` — gardé")
        self.assertIn("ni `conservé`", self.gaps())
        archi(self.kb, "vues et modèles — `src/` — étendu")
        self.assertIn("étendu sans ce qui s'ajoute", self.gaps())
        archi(self.kb, "vues et modèles — `src/` — étendu — `src/services/` pour la règle du total")
        self.assertEqual(ex.architecture_gaps(self.kb), [])

    def test_a_replacement_needs_a_decided_reason_and_what_moves(self):
        archi(self.kb, "vues et modèles — `src/` — remplacé par une architecture hexagonale — raison : plus propre")
        gaps = self.gaps()
        self.assertIn("remplacé sans `raison :`", gaps)
        self.assertIn("remplacé sans `migration :`", gaps)
        archi(self.kb, "vues et modèles — `src/` — remplacé par des services — raison : D1 — migration : 4 vues")
        self.assertEqual(ex.architecture_gaps(self.kb), [])

    def test_done_architecture_reads_it_and_a_new_project_has_nothing_to_keep(self):
        self.assertIn("Architecture reprise", "\n".join(av.check(self.kb, "architecture", None)))
        new = project(inventaire=None, diagnostic=None, depart="Neuf")
        self.assertNotIn("Architecture reprise", "\n".join(av.check(new, "architecture", None)))
        agent = (ROOT / "agents" / "architect.md").read_text(encoding="utf-8")
        for word in ("architecture-existante.md", "## Architecture reprise", "conservé", "étendu", "remplacé par",
                     "raison :", "migration :"):
            self.assertIn(word, agent)


NAV = "---\ntype: Plan de navigation\n---\n## Écrans\n| Écran | Route |\n|---|---|\n| Commandes | `/commandes` |\n" \
      "## Écrans repris\n"


def ecrans(kb: Path, *rows: str) -> None:
    (kb / "interface").mkdir(exist_ok=True)
    (kb / "interface" / "navigation.md").write_text(NAV + "".join(f"- {r}\n" for r in rows), encoding="utf-8")


class Interface(unittest.TestCase):
    """No screen the users already have disappears: kept, replaced by a screen of the navigation, or dropped for a
    decided reason."""

    def setUp(self):
        self.kb = project(diagnostic=DECIDED)

    def gaps(self):
        return "\n".join(ex.ecrans_gaps(self.kb))

    def test_each_screen_found_must_be_taken_over(self):
        self.assertIn("sans `## Écrans repris`", self.gaps())
        ecrans(self.kb, "Export — source : `src/export.py` — conservé")
        self.assertIn("« Liste des commandes » (`src/gabarits/liste.html`) absent", self.gaps())
        ecrans(self.kb, "Liste des commandes — source : `src/gabarits/liste.html` — refait")
        self.assertIn("ni `conservé`", self.gaps())
        ecrans(self.kb, "Liste des commandes — source : `src/gabarits/liste.html` — conservé")
        self.assertEqual(ex.ecrans_gaps(self.kb), [])

    def test_a_replacement_names_a_screen_of_the_navigation(self):
        ecrans(self.kb, "Liste des commandes — source : `src/gabarits/liste.html` — remplacé par Tableau de bord")
        self.assertIn("absent du tableau `## Écrans`", self.gaps())
        ecrans(self.kb, "Liste des commandes — source : `src/gabarits/liste.html` — remplacé par Commandes")
        self.assertEqual(ex.ecrans_gaps(self.kb), [])

    def test_a_drop_needs_a_decided_reason(self):
        ecrans(self.kb, "Liste des commandes — source : `src/gabarits/liste.html` — supprimé — raison : D2")
        self.assertIn("supprimé sans `raison :`", self.gaps())  # D2 is decided `plus tard`
        ecrans(self.kb, "Liste des commandes — source : `src/gabarits/liste.html` — supprimé — raison : D1")
        self.assertEqual(ex.ecrans_gaps(self.kb), [])

    def test_done_interface_reads_it_and_an_api_has_no_screen_to_keep(self):
        self.assertIn("Écrans repris", "\n".join(av.check(self.kb, "interface", None)))
        api = project(inventaire=INVENTAIRE.replace(
            "- Liste des commandes — source : `src/gabarits/liste.html` — client\n", "Aucune.\n"))
        self.assertEqual(ex.ecrans_gaps(api), [])
        self.assertEqual(ex.inventaire_gaps(api, root(api)), [])
        agent = (ROOT / "agents" / "ux-designer.md").read_text(encoding="utf-8")
        for word in ("## Écrans repris", "conservé", "remplacé par", "supprimé", "raison :"):
            self.assertIn(word, agent)
        self.assertIn("## Interface constatée", (ROOT / "agents" / "analyst.md").read_text(encoding="utf-8"))


def fichier(kb: Path, rel: str, ctype: str, heading: str, *rows: str) -> None:
    body = "".join(f"- {r}\n" for r in rows)
    (kb / rel).parent.mkdir(parents=True, exist_ok=True)
    (kb / rel).write_text(f"---\ntype: {ctype}\n---\n## {heading}\n{body}", encoding="utf-8")


EXIGENCE = "---\ntype: Exigence\nstatus: draft\nexistant: [EX1]\n---\n## Objectif\nse connecter\n"


class Fondamentaux(unittest.TestCase):
    """A basic function the code already has is taken over by an exigence, never written again beside it."""

    def setUp(self):
        self.kb = project(diagnostic=DECIDED, **{"cdc/connexion.md": EXIGENCE})

    def bilan(self, *rows):
        fichier(self.kb, "cdc/fondamentaux.md", "Revue Fondamentaux", "Bilan", *rows)
        return ex.fondamentaux_gaps(self.kb)

    def test_each_basic_function_found_must_be_in_the_review(self):
        self.assertIn("sans `## Bilan`", "\n".join(ex.fondamentaux_gaps(self.kb)))
        self.assertIn("absent du `## Bilan`", "\n".join(self.bilan("Socle comptes — Ajouté : [x](connexion.md)")))

    def test_an_existing_function_needs_the_exigence_that_describes_it(self):
        self.assertIn("sans l'exigence", "\n".join(self.bilan("Socle comptes — Existant : `src/commandes.py:1`")))
        self.assertIn("sans l'exigence", "\n".join(
            self.bilan("Socle comptes — Existant : `src/commandes.py:1` — [exigence](absente.md)")))
        self.assertEqual(self.bilan("Socle comptes — Existant : `src/commandes.py:1` — [exigence](connexion.md)"), [])

    def test_a_drop_needs_a_decided_reason(self):
        self.assertIn("sans `raison :`",
                      "\n".join(self.bilan("Socle comptes — `src/commandes.py:1` — Supprimé — raison : D2")))
        self.assertEqual(self.bilan("Socle comptes — `src/commandes.py:1` — Supprimé — raison : D1"), [])

    def test_done_reads_it_and_a_project_without_basics_has_nothing_to_keep(self):
        self.assertIn("Bilan", "\n".join(av.check(self.kb, "fondamentaux", None)))
        bare = project(inventaire=INVENTAIRE.replace(
            "- connexion — source : `src/commandes.py:1` — sans limite de tentatives\n", "Aucun.\n"))
        self.assertEqual(ex.fondamentaux_gaps(bare), [])
        self.assertEqual(ex.inventaire_gaps(bare, root(bare)), [])
        self.assertIn("Existant :", (ROOT / "agents" / "product-owner.md").read_text(encoding="utf-8"))


class Failles(unittest.TestCase):
    """Each security flaw of the existing code reaches the security analysis and the threat model, as decided."""

    def setUp(self):
        self.kb = project(diagnostic=DECIDED, **{"cdc/hachage.md": EXIGENCE})

    def secu(self, *rows):
        fichier(self.kb, "cdc/securite.md", "Analyse de sécurité", "Failles existantes", *rows)
        return ex.faille_gaps(self.kb, ex.SECU, "lien", "risque")

    def menaces(self, *rows):
        fichier(self.kb, "securite/modele-menaces.md", "Modèle de Menaces", "Failles existantes", *rows)
        return ex.faille_gaps(self.kb, ex.MENACES, "atténuation", "résiduel")

    def test_each_security_flaw_must_be_listed_and_only_those(self):
        gaps = self.secu()
        self.assertEqual(len(gaps), 1)  # D1 (sécurité), not D2 (qualité)
        self.assertIn("D1", gaps[0])

    def test_the_decision_is_the_users_and_a_fix_needs_its_measure(self):
        self.assertIn("l'utilisateur a décidé `corriger`",
                      "\n".join(self.secu("**D1** — mot de passe en clair — accepter — risque : faible")))
        self.assertIn("sans la mesure", "\n".join(self.secu("**D1** — mot de passe en clair — corriger : à voir")))
        self.assertEqual(self.secu("**D1** — mot de passe en clair — corriger : [exigence](hachage.md)"), [])

    def test_a_flaw_kept_states_what_stays_exposed(self):
        self.kb = project(diagnostic=DECIDED.replace("Décision : corriger — oui", "Décision : plus tard — oui"))
        self.assertIn("sans `risque :`", "\n".join(self.secu("**D1** — mot de passe en clair — plus tard")))
        self.assertEqual(self.secu("**D1** — mot de passe en clair — plus tard — risque : exposés jusqu'au sprint 2"), [])
        self.assertIn("sans `résiduel :`", "\n".join(self.menaces("**D1** — connexion — I — plus tard")))

    def test_the_threat_model_places_each_flaw_with_its_mitigation(self):
        self.assertIn("absent de `## Failles existantes`", "\n".join(self.menaces()))
        self.assertIn("sans `atténuation :`", "\n".join(self.menaces("**D1** — connexion — I — corriger")))
        self.assertEqual(self.menaces("**D1** — connexion — I — corriger — atténuation : hachage argon2"), [])

    def test_done_reads_them_and_the_agent_carries_the_format(self):
        self.assertIn("Failles existantes", "\n".join(av.check(self.kb, "securite", None)))
        self.assertIn("Failles existantes", "\n".join(av.check(self.kb, "menaces", None)))
        new = project(inventaire=None)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual([ex.main([str(new), m]) for m in ("fondamentaux", "securite", "menaces")], [0, 0, 0])
        agent = (ROOT / "agents" / "security.md").read_text(encoding="utf-8")
        for word in ("## Failles existantes", "risque :", "atténuation :", "résiduel :"):
            self.assertIn(word, agent)


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
