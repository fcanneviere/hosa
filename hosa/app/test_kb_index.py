"""kb_index.py keeps the KB summary short: long descriptions are cut."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "okf" / "scripts" / "kb_index.py"
spec = importlib.util.spec_from_file_location("kb_index", SCRIPT)
kb_index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kb_index)


class KbIndex(unittest.TestCase):
    def test_long_description_is_cut(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "tickets").mkdir()
            (Path(d) / "tickets" / "t.md").write_text(
                f"---\ntype: Ticket\ntitle: T\ndescription: {'x' * 500}\nstate: todo\n---\n", encoding="utf-8")
            line = next(l for l in kb_index.build(Path(d)).splitlines() if l.startswith("- [T]"))
            self.assertTrue(line.endswith("…"))
            self.assertEqual(len(line.split(" — ")[-1]), kb_index.DESC_MAX)

    def test_lists_read_as_values_and_hidden_folders_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            for rel, text in {"cdc/e.md": "---\ntype: Exigence\ntitle: E\nespace: [front-office, back-office]\n---\n",
                              ".claude/agent-memory/MEMORY.md": "# mémoire d'agent\n"}.items():
                (Path(d) / rel).parent.mkdir(parents=True, exist_ok=True)
                (Path(d) / rel).write_text(text, encoding="utf-8")
            text = kb_index.build(Path(d))
            self.assertIn("espace front-office, back-office", text)
            self.assertIn("1 concepts.", text)
            self.assertNotIn("MEMORY", text)

    def test_over_budget_closed_concepts_then_big_descriptions_go(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "tickets").mkdir()
            (Path(d) / "cdc").mkdir()
            for i in range(40):
                (Path(d) / "tickets" / f"t{i}.md").write_text(
                    f"---\ntype: Ticket\ntitle: T{i}\ndescription: \"{'d' * 150}\"\nstate: {'done' if i < 10 else 'todo'}\n---\n",
                    encoding="utf-8")
            (Path(d) / "cdc" / "e.md").write_text("---\ntype: Exigence\ntitle: E\ndescription: \"Courte.\"\n---\n",
                                                  encoding="utf-8")
            full = kb_index.build(Path(d), budget=10**6)
            self.assertIn("[T0]", full)
            text = kb_index.build(Path(d), budget=4000)
            self.assertNotIn("[T0]", text)  # done : une ligne de compte
            self.assertIn("10 concept(s) `done` non listés : `kb_query <kb> --bundle tickets --where state=done`", text)
            self.assertIn("## tickets (40) — descriptions : `kb_query <kb> --bundle tickets --fields description`", text)
            self.assertNotIn("d" * 150, text)
            self.assertIn("Courte.", text)  # un petit dossier garde ses descriptions

    def test_summary_stays_under_budget_and_keeps_active_work(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "tickets").mkdir()
            states = ["todo"] * 1500 + ["doing"] * 3 + ["done"] * 200
            for i, s in enumerate(states):
                (Path(d) / "tickets" / f"ticket-au-titre-assez-long-{i}.md").write_text(
                    f"---\ntype: Ticket\ntitle: Un titre de ticket assez long numéro {i}\nstate: {s}\n---\n",
                    encoding="utf-8")
            text = kb_index.build(Path(d), budget=20_000)
            self.assertLessEqual(len(text.encode("utf-8")), 20_000)
            self.assertIn("1500 concept(s) `todo` non listés", text)
            self.assertIn("numéro 1500]", text)  # doing : le sprint en cours reste listé


if __name__ == "__main__":
    unittest.main()
