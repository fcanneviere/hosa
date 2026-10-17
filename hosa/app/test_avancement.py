"""avancement.py: `check` finds a stage's missing proofs, `done` refuses them, `next` names the skill."""
import contextlib
import importlib.util
import io
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

    def test_qa_needs_each_required_recette(self):
        plan = "- [CA1] x\n- [CA2] y\n## Résultats techniques\n2/2\n## Recette requise\n- [Karim](../personnas/karim.md)\n"
        k = kb({"sprints/s1.md": SPRINT, "tickets/t1.md": TICKET, "test/t1-technique.md": plan})
        self.assertEqual(av.check(k, "qa", "s1"), ["t1 : recette de karim absente (`kb/test/t1-karim.md`, `qa`)"])
        (k / "test" / "t1-karim.md").write_text("## Verdict\nAccepté\n", encoding="utf-8")
        self.assertEqual(av.check(k, "qa", "s1"), [])

    def test_non_sprint_stages_have_no_proof_to_check(self):
        self.assertEqual(av.check(kb({}), "stack", None), [])


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
            "pas de `## Audit` avec sa ligne `Bloquant : N` (`validation` étape 3a)",
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


class Next(unittest.TestCase):
    def test_next_without_a_plan_points_to_status(self):
        self.assertIn("le skill `status` le crée", run(kb({}), "next")[1])

    def test_next_names_the_skill_and_what_is_left(self):
        k = kb({"sprints/s1.md": SPRINT, "tickets/t1.md": TICKET})
        for stage in av.PIPELINES[0][1] + av.PIPELINES[1][1]:
            run(k, "done", stage)
        run(k, "done", "sprint", "--sprint", "s1")
        run(k, "start", "qa-plan", "--sprint", "s1")
        code, out = run(k, "next")
        self.assertEqual(code, 0)
        self.assertIn("`qa-plan` (Sprint s1, en cours) → skill `qa-plan`", out)
        self.assertIn("Reste à prouver", out)
        run(k, "done", "qa-plan", "--sprint", "s1", "--force")
        self.assertIn("→ skill `git`", run(k, "next")[1])


if __name__ == "__main__":
    unittest.main()
