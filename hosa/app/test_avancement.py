"""avancement.py: `check` finds a stage's missing proofs, `done` refuses them, `next` names the skill."""
import contextlib
import importlib.util
import io
import re
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "status" / "scripts" / "avancement.py"
spec = importlib.util.spec_from_file_location("avancement", SCRIPT)
av = importlib.util.module_from_spec(spec)
spec.loader.exec_module(av)


def kb(files: dict) -> Path:
    root = Path(tempfile.mkdtemp())
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding="utf-8")
    return root


def run(*argv) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = av.main([str(a) for a in argv])
    return code, out.getvalue()


SPRINT = "---\ntype: Sprint\n---\n## Tickets\n- [T1](../tickets/t1.md)\n"
TICKET = "---\ntype: Ticket\nstate: doing\n---\n## Critères d'acceptation\n- CA1 — a\n- CA2 — b\n"


class Check(unittest.TestCase):
    def test_qa_plan_needs_a_case_per_criterion(self):
        k = kb({"sprints/s1.md": SPRINT, "tickets/t1.md": TICKET, "test/t1-technique.md": "- [CA1] x\n"})
        self.assertEqual(av.check(k, "qa-plan", "s1"), ["t1 : CA2 sans cas de test [CAn] (`qa-plan`)"])
        (k / "test" / "t1-technique.md").write_text("- [CA1] x\n- [CA2] [manuel] y\n", encoding="utf-8")
        self.assertEqual(av.check(k, "qa-plan", "s1"), [])

    def test_develop_needs_a_passed_review(self):
        k = kb({"sprints/s1.md": SPRINT, "tickets/t1.md": TICKET + "## Revue\n- d — PASS — ok\n- d — FAIL — CA2\n"})
        self.assertIn("dernière `## Revue` FAIL", av.check(k, "develop", "s1")[0])

    def test_validation_accepts_a_recette_oui_as_proof(self):
        k = kb({"sprints/s1.md": SPRINT + "## Audit\nBloquant : 0\n## Démo\n- T1 OK\n",
                "tickets/t1.md": TICKET.replace("state: doing", "state: done\nverified: { by: po }"),
                "test/t1-technique.md": "- [CA1] x\n## Résultats techniques\n3/3\n",
                "test/t1-les-parents.md": "### Critères\n- CA2 — Oui — capture\n## Verdict\nAccepté\n"})
        self.assertEqual(av.check(k, "validation", "s1"), [])

    def test_validation_accepts_a_demo_already_played_in_qa(self):
        demo = "## Démo\n- t1 — joué en QA le 2026-10-26 (T2 [manuel] parcours principal)\n"
        k = kb({"sprints/s1.md": SPRINT + "## Audit\nBloquant : 0\n" + demo,
                "tickets/t1.md": TICKET.replace("state: doing", "state: done\nverified: { by: po }"),
                "test/t1-technique.md": "- [CA1] x\n- [CA2] [manuel] y\n## Résultats techniques\n2/2\n"})
        self.assertEqual(av.check(k, "validation", "s1"), [])

    def test_qa_needs_each_required_recette(self):
        plan = "- [CA1] x\n- [CA2] y\n## Résultats techniques\n2/2\n## Recette requise\n- [Karim](../personnas/karim.md)\n"
        k = kb({"sprints/s1.md": SPRINT, "tickets/t1.md": TICKET, "test/t1-technique.md": plan})
        self.assertEqual(av.check(k, "qa", "s1"), ["t1 : recette de karim absente (`kb/test/t1-karim.md`, `qa`)"])
        (k / "test" / "t1-karim.md").write_text("## Verdict\nAccepté\n", encoding="utf-8")
        self.assertEqual(av.check(k, "qa", "s1"), [])

    def test_audit_needs_no_bloquant_left(self):
        k = kb({"sprints/s1.md": SPRINT + "## Audit\n- d1 Bloquant : 1\n- d2 Bloquant : 0\n", "tickets/t1.md": TICKET})
        self.assertEqual(av.check(k, "audit", "s1"), [])
        (k / "sprints" / "s1.md").write_text(SPRINT + "## Audit\nBloquant : 2\n", encoding="utf-8")
        self.assertEqual(av.check(k, "audit", "s1"), ["`## Audit` : Bloquant : 2"])

    def test_upstream_stages_need_what_their_skill_writes(self):
        k = kb({})
        self.assertEqual(av.check(k, "stack", None), ["aucune `Stack Decision` dans `kb/stack/`"])
        (k / "stack").mkdir()
        (k / "stack" / "framework.md").write_text("---\ntype: Stack Decision\n---\n", encoding="utf-8")
        self.assertEqual(av.check(k, "stack", None), [])

    def test_hosa_needs_a_real_persona(self):
        k = kb({"project/identity.md": "---\ntype: Project\n---\n",
                "personnas/exemple-persona.md": "---\ntype: Persona\n---\n"})
        self.assertEqual(av.check(k, "hosa", None), ["aucun persona dans `kb/personnas/` (hors exemple)"])

    def test_securite_needs_its_second_pass(self):
        k = kb({"cdc/securite.md": "---\ntype: Analyse de sécurité\nstatus: draft\n---\n## Choix validés\n- x\n"})
        self.assertEqual(av.check(k, "securite", None), ["`kb/cdc/securite.md` n'a pas sa section `## Menaces et mesures`"])

    def test_relecture_and_redaction_wait_for_open_bloquantes_only(self):
        rel = ("---\ntype: Revue Relecture\n---\n## Anomalies\n- A1 — [x](x.md) § Règles — flou — → redaction — corrigée\n"
               "- A2 [p1, bloquante, texte] — [x](x.md) § Cas — manque — → redaction — ouverte\n"
               "- A3 [p1, bloquante, texte] — [y](y.md) — besoin — → interview — ouverte\n"
               "- A4 [p1, mineure, texte] — [x](x.md) § Glossaire — synonyme — → redaction — ouverte\n")
        k = kb({"cdc/relecture.md": rel, "cdc/x.md": "---\ntype: Exigence\nstatus: draft\n---\n",
                "project/cahier-des-charges.md": "---\ntype: Cahier des charges\n---\n"})
        self.assertEqual(av.check(k, "relecture", None), ["`cdc` : anomalies bloquantes encore `ouverte` : A2, A3"])
        self.assertEqual(av.check(k, "redaction", None), ["`cdc` : anomalies bloquantes → redaction encore `ouverte` : A2"])
        (k / "cdc" / "relecture.md").write_text(rel.replace("texte] — [x](x.md) § Cas — manque — → redaction — ouverte",
                                                            "texte] — [x](x.md) § Cas — manque — → redaction — corrigée")
                                                .replace("→ interview — ouverte", "→ interview — corrigée"), encoding="utf-8")
        self.assertEqual(av.check(k, "relecture", None), [])  # A4, a mineure still open, holds nothing
        self.assertEqual(av.check(k, "redaction", None), [])

    def test_donnees_needs_an_origin_per_data_item(self):
        ex = ("---\ntype: Exigence\nstatus: stable\n---\n## Données en entrée\n- L'adresse — origine : saisie (par un parent)\n"
              "- Le foyer\n## Données en sortie\n- Le compte — origine : générée\n")
        k = kb({"cdc/inscription.md": ex, "cdc/brouillon.md": ex.replace("stable", "draft")})
        self.assertEqual(av.check(k, "donnees", None), ["`inscription` : 1 donnée(s) sans `origine :`"])

    def test_done_refuses_an_upstream_stage_without_its_proof(self):
        k = kb({})
        self.assertEqual(run(k, "done", "stack")[0], 1)
        self.assertEqual(run(k, "done", "stack", "--force")[0], 0)


def cov(k, t="t1"):
    """`av.coverage`, or a clean test failure while it does not exist yet."""
    if not hasattr(av, "coverage"):
        raise AssertionError("avancement.coverage n'existe pas")
    return av.coverage(k, t)

def tk(n=3):
    return "---\ntype: Ticket\n---\n## Critères d'acceptation\n" + "".join(f"- CA{i} — c\n" for i in range(1, n + 1))

class Coverage(unittest.TestCase):
    def test_plan_cases_cover_their_criteria(self):  # cas 1
        k = kb({"tickets/t1.md": tk(), "test/t1-technique.md": "- [CA1] x\n- [CA3] y\n"})
        self.assertEqual(cov(k), {"criteres": ["CA1", "CA2", "CA3"], "couverts": ["CA1", "CA3"], "total": 3, "plan": True})

    def test_recette_oui_covers(self):  # cas 2
        k = kb({"tickets/t1.md": tk(), "test/t1-technique.md": "- [CA1] x\n",
                "test/t1-parents.md": "### Critères\n- CA2 — Oui — capture\n"})
        self.assertIn("CA2", cov(k)["couverts"])

    def test_recette_non_does_not_cover(self):  # cas 3
        k = kb({"tickets/t1.md": tk(), "test/t1-technique.md": "- [CA1] x\n",
                "test/t1-parents.md": "- CA2 — Non — x\n"})
        self.assertNotIn("CA2", cov(k)["couverts"])

    def test_no_plan_file(self):  # cas 4
        self.assertIs(cov(kb({"tickets/t1.md": tk(), "test/autre.md": "x"}))["plan"], False)

    def test_recette_oui_without_plan(self):  # cas 5
        k = kb({"tickets/t1.md": tk(), "test/t1-parents.md": "- CA1 — Oui — capture\n"})
        r = cov(k)
        self.assertIs(r["plan"], False)
        self.assertEqual(r["couverts"], ["CA1"])

    def test_no_criteria(self):  # cas 6
        for text in ("---\ntype: Ticket\n---\nrien\n", "---\ntype: Ticket\n---\n## Critères d'acceptation\nTexte libre\n"):
            r = cov(kb({"tickets/t1.md": text}))
            self.assertEqual((r["criteres"], r["total"]), ([], 0))

    def test_check_gaps_unchanged_by_extraction(self):  # cas 7: lists captured from check() before the extraction
        sp = "---\ntype: Sprint\n---\n## Tickets\n" + "".join(f"- [T{i}](../tickets/t{i}.md)\n" for i in (1, 2, 3))
        t = "---\ntype: Ticket\nstate: done\nverified: { by: po }\n---\n" + tk().split("---\n", 2)[2]
        k = kb({"sprints/s1.md": sp, "tickets/t1.md": t, "tickets/t2.md": t,
                "tickets/t3.md": "---\ntype: Ticket\nstate: done\nverified: { by: po }\n---\nrien\n",
                "test/t1-technique.md": "- [CA1] x\n## Résultats techniques\n3/3\n",
                "test/t1-p.md": "## Verdict\nRefusé\n### Critères\n- CA2 — Non — x\n- CA3 — Oui — y\n"})
        self.assertEqual(av.check(k, "qa-plan", "s1"), [
            "t1 : CA2, CA3 sans cas de test [CAn] (`qa-plan`)",
            "t2 : pas de plan `kb/test/t2-technique.md` (`qa-plan`)",
            "t2 : CA1, CA2, CA3 sans cas de test [CAn] (`qa-plan`)",
            "t3 : pas de plan `kb/test/t3-technique.md` (`qa-plan`)"])
        self.assertEqual(av.check(k, "validation", "s1"), [
            "t1-p.md : recette Refusé",
            "t1-p.md : un critère répondu Non",
            "t1 : CA2 prouvé(s) par aucun cas [CAn] ni recette Oui (`qa-plan`)",
            "t2 : pas de `## Résultats techniques` (`qa`)",
            "t2 : CA1, CA2, CA3 prouvé(s) par aucun cas [CAn] ni recette Oui (`qa-plan`)",
            "t3 : pas de `## Résultats techniques` (`qa`)",
            "pas de `## Audit` avec sa ligne `Bloquant : N` (`qualite`, étape `audit`)",
            "pas de `## Démo` (`validation` étape 3b)"])

    def test_longer_identifier_does_not_cover(self):  # cas 8a
        k = kb({"tickets/t1.md": tk(2), "test/t1-technique.md": "- [CA10] x\n- ACA1 y\n",
                "test/t1-r.md": "- CA10 — Oui — z\n"})
        self.assertEqual(cov(k)["couverts"], [])

    def test_eleven_criteria(self):  # cas 8b
        k = kb({"tickets/t1.md": tk(11), "test/t1-technique.md": "- [CA10] x\n- [CA11] y\n"})
        r = cov(k)
        self.assertEqual((r["total"], r["couverts"]), (11, ["CA10", "CA11"]))

    def test_kb_without_test_dir(self):  # cas 8c
        r = cov(kb({"tickets/t1.md": tk()}))
        self.assertEqual((r["plan"], r["couverts"], r["total"]), (False, [], 3))

class Done(unittest.TestCase):
    def test_done_refuses_a_missing_proof_unless_forced(self):
        k = kb({"sprints/s1.md": SPRINT, "tickets/t1.md": TICKET})
        code, out = run(k, "done", "qa-plan", "--sprint", "s1")
        self.assertEqual(code, 1)
        self.assertIn("preuve(s) manquante(s)", out)
        self.assertEqual(run(k, "done", "qa-plan", "--sprint", "s1", "--force")[0], 0)


class Block(unittest.TestCase):
    def test_block_keeps_the_questions_in_full(self):
        k = kb({})
        q = "2 questions bloquantes\nQ1. Clé primaire ? A. uuid (recommandé) B. entier\nQ2. Casse des e-mails ? A. citext B. lower()"
        self.assertEqual(run(k, "block", "schema-db", "--detail", q)[0], 0)
        sections, resume = av.load(k / "project" / "avancement.md")
        self.assertIn("Q2. Casse des e-mails ? A. citext B. lower()", resume)
        self.assertEqual(next(r for r in sections["Structuration"] if r[0] == "schema-db")[3], "2 questions bloquantes")


class AuditStage(unittest.TestCase):
    def test_audit_sits_between_develop_and_qa(self):
        k = kb({"sprints/s1.md": SPRINT, "tickets/t1.md": TICKET})
        for stage in av.PIPELINES[0][1] + av.PIPELINES[1][1]:
            run(k, "done", stage, "--force")
        for stage in ("sprint", "qa-plan", "git-demarrage", "develop"):
            run(k, "done", stage, "--sprint", "s1", "--force")
        code, out = run(k, "start", "qa", "--sprint", "s1")
        self.assertEqual(code, 1)
        self.assertIn("`audit`", out)
        self.assertIn("`audit` (Sprint s1, à faire) → skill `qualite`", run(k, "next")[1])

    def test_a_sprint_audited_in_validation_is_not_reopened(self):
        head = "| Étape | Statut | Mis à jour | Détail |\n|---|---|---|---|\n"
        rows = "".join(f"| `{s}` | fait | d | |\n" for s in ("sprint", "qa-plan", "git-demarrage", "develop", "qa", "validation"))
        k = kb({"project/avancement.md": f"---\ntype: x\n---\n## Sprint s0\n{head}{rows}"
                                         f"## Sprint s1\n{head}| `develop` | en cours | d | |\n"})
        sections, _ = av.load(k / "project" / "avancement.md")
        self.assertEqual([r[:2] for r in sections["Sprint s0"] if r[0] == "audit"], [["audit", av.SKIPPED]])
        self.assertEqual([r[:2] for r in sections["Sprint s1"] if r[0] == "audit"], [["audit", av.TODO]])
        self.assertEqual([r[0] for r in sections["Sprint s0"]][3:6], ["develop", "audit", "qa"])


class Next(unittest.TestCase):
    def test_next_without_a_plan_points_to_status(self):
        self.assertIn("le skill `status` le crée", run(kb({}), "next")[1])

    def test_next_names_the_skill_and_what_is_left(self):
        k = kb({"sprints/s1.md": SPRINT, "tickets/t1.md": TICKET})
        for stage in av.PIPELINES[0][1] + av.PIPELINES[1][1]:
            run(k, "done", stage, "--force")
        run(k, "done", "sprint", "--sprint", "s1")
        run(k, "start", "qa-plan", "--sprint", "s1")
        code, out = run(k, "next")
        self.assertEqual(code, 0)
        self.assertIn("`qa-plan` (Sprint s1, en cours) → skill `qa-plan`", out)
        self.assertIn("Reste à prouver", out)
        run(k, "done", "qa-plan", "--sprint", "s1", "--force")
        self.assertIn("→ skill `git`", run(k, "next")[1])


class Graph(unittest.TestCase):
    """pipeline.json is the one stage graph: each stage once, each stage's skill exists, loops go backwards."""

    def test_each_stage_once_and_its_skill_exists(self):
        stages = [s for _, ss in av.PIPELINES for s in ss] + av.SPRINT
        self.assertEqual(len(stages), len(set(stages)))
        self.assertLessEqual(set(av.SKILL), set(stages))
        skills = SCRIPT.parents[2]
        for s in stages:
            self.assertTrue((skills / av.SKILL.get(s, s) / "SKILL.md").is_file(), s)

    def test_loops_go_backwards(self):
        # the upstream pipelines are one order (interface → fondamentaux crosses them); a sprint is another
        for pipe in ([s for _, ss in av.PIPELINES for s in ss], av.SPRINT):
            for e in (e for e in av.LOOPS if e["from"] in pipe):
                for s in e["to"] + e.get("then", []):
                    self.assertLess(pipe.index(s), pipe.index(e["from"]), e)
                self.assertGreaterEqual(e["max"], 1)


def closed_until(k, stage):
    """Every upstream stage done up to <stage> included (forced: these tests are about the loops)."""
    with contextlib.redirect_stdout(io.StringIO()):
        for s in [s for _, ss in av.PIPELINES for s in ss]:
            av.main([str(k), "done", s, "--force"])
            if s == stage:
                return


class Loops(unittest.TestCase):
    def test_back_reopens_the_target_and_the_source_and_counts_the_round(self):
        k = kb({})
        closed_until(k, "relecture")
        code, out = run(k, "back", "relecture", "interview", "--detail", "A40 : besoin jamais recueilli")
        self.assertEqual(code, 0)
        self.assertIn("Boucle ouverte : `relecture` → `interview` — tour 1/2", out)
        sections, resume = av.load(k / "project" / "avancement.md")
        status = {r[0]: r[1] for r in sections["Cahier des charges"]}
        self.assertEqual([status[s] for s in ("interview", "redaction", "fondamentaux", "relecture")],
                         [av.TODO, av.TODO, av.DONE, av.TODO])
        self.assertIn("`interview`, puis `redaction`, puis `relecture`", resume)
        self.assertIn("`interview` (Cahier des charges, à faire)", run(k, "next")[1])

    def test_past_max_rounds_the_user_decides(self):
        k = kb({})
        closed_until(k, "relecture")
        for _ in range(2):
            self.assertEqual(run(k, "back", "relecture", "redaction", "--detail", "A2")[0], 0)
        code, out = run(k, "back", "relecture", "redaction", "--detail", "A2")
        self.assertEqual(code, 1)
        self.assertIn("déjà 2 tour(s)", out)
        self.assertEqual(run(k, "back", "relecture", "redaction", "--detail", "A2", "--force")[0], 0)
        self.assertEqual(av.load_loops(k / "project" / "avancement.md")[0]["tours"], 3)

    def test_done_closes_the_loop_and_a_new_one_starts_at_one(self):
        k = kb({})
        closed_until(k, "relecture")
        run(k, "back", "relecture", "redaction", "--detail", "A2")
        run(k, "done", "redaction", "--force")
        run(k, "done", "relecture", "--force")
        self.assertEqual(av.load_loops(k / "project" / "avancement.md")[0]["etat"], av.SHUT)
        self.assertIn("tour 1/2", run(k, "back", "relecture", "redaction", "--detail", "A9")[1])

    def test_sprint_loop_is_counted_per_ticket_and_cause(self):
        k = kb({})
        for s in ("sprint", "qa-plan", "git-demarrage", "develop", "audit"):
            run(k, "done", s, "--sprint", "s1", "--force")
        back = lambda t, c: run(k, "back", "qa", "develop", "--sprint", "s1", "--ticket", t, "--cause", c, "--detail", "KO")
        self.assertEqual(back("t1", "test_a")[0], 0)
        self.assertEqual(back("t1", "test_a")[0], 0)
        self.assertEqual(back("t2", "test_a")[0], 0)   # another ticket: its own count
        self.assertEqual(back("t1", "test_b")[0], 0)   # another failure: the count restarts
        self.assertEqual(back("t1", "test_b")[0], 0)
        self.assertEqual(back("t1", "test_b")[0], 1)
        sections, _ = av.load(k / "project" / "avancement.md")
        self.assertEqual({r[0]: r[1] for r in sections["Sprint s1"]}["develop"], av.TODO)

    def test_unknown_loop_is_a_bad_invocation(self):
        k = kb({})
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(run(k, "back", "relecture", "stack", "--detail", "x")[0], 2)

    def test_the_mod_and_budget_hook_do_not_read_loops_as_stages(self):
        k = kb({})
        closed_until(k, "relecture")
        run(k, "back", "relecture", "redaction", "--detail", "A2")
        text = (k / "project" / "avancement.md").read_text(encoding="utf-8")
        loop_rows = section_rows(text, "Boucles")
        self.assertEqual(len(loop_rows), 1)
        self.assertIsNone(av.ROW.match(loop_rows[0]))


class Init(unittest.TestCase):
    def test_init_marks_the_proved_stages_and_stops_at_the_first_gap(self):
        k = kb({"project/identity.md": "---\ntype: Project\n---\n", "personnas/parent.md": "---\ntype: Persona\n---\n",
                "sprints/s1.md": SPRINT, "tickets/t1.md": TICKET})
        code, out = run(k, "init")
        self.assertEqual(code, 0)
        self.assertIn("Cahier des charges : arrêt à `interview` — aucun compte rendu", out)
        self.assertIn("Sprint s1 : arrêt à `qa-plan`", out)
        sections, _ = av.load(k / "project" / "avancement.md")
        status = lambda t: {r[0]: r[1] for r in sections[t]}
        self.assertEqual((status("Cahier des charges")["hosa"], status("Cahier des charges")["interview"]), (av.DONE, av.TODO))
        self.assertEqual(status("Structuration")["stack"], av.TODO)       # an unproved pipeline stops the next one
        self.assertEqual(status("Sprint s1")["sprint"], av.DONE)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(run(k, "init")[0], 1)                         # never over an existing plan


class Docs(unittest.TestCase):
    """The pipelines written in prose (using-hosa, README) follow pipeline.json."""

    def test_prose_pipelines_follow_the_graph(self):
        expected = [[av.SKILL.get(s, s) for s in ss] for _, ss in av.PIPELINES] + [[av.SKILL.get(s, s) for s in av.SPRINT]]
        root = SCRIPT.parents[3]
        for doc, starts in (("skills/using-hosa/SKILL.md", ("1. **Cahier", "2. **Structuration", "3. **Each sprint")),
                            ("README.md", ("1. **Cahier", "2. **Structuration", "3. **Chaque sprint"))):
            lines = (root / doc).read_text(encoding="utf-8").splitlines()
            for start, want in zip(starts, expected):
                line = next(x for x in lines if x.strip().startswith(start))
                self.assertEqual(re.findall(r"`([\w-]+)`", line)[:len(want)], want, f"{doc} : {start}")


def section_rows(text, heading):
    return [x for x in (av.section(text, heading) or "").splitlines() if x.startswith("| `")]


if __name__ == "__main__":
    unittest.main()
