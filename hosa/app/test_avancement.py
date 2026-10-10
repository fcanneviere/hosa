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

    def test_non_sprint_stages_have_no_proof_to_check(self):
        self.assertEqual(av.check(kb({}), "stack", None), [])


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
