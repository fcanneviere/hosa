"""usage_report.py: a response written over several transcript lines is counted once."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "status" / "scripts" / "usage_report.py"
spec = importlib.util.spec_from_file_location("usage_report", SCRIPT)
ur = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ur)


def line(mid: str, block: dict) -> str:
    usage = {"input_tokens": 1, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 1000, "output_tokens": 10}
    return json.dumps({"type": "assistant", "message": {"id": mid, "model": "m", "usage": usage, "content": [block]}})


class UsageOnce(unittest.TestCase):
    def test_split_response_counted_once(self):
        base = Path(tempfile.mkdtemp())
        text = {"type": "text", "text": "x"}
        tool = {"type": "tool_use", "id": "t1", "name": "Bash", "input": {}}
        (base / "s.jsonl").write_text("\n".join([line("a", text), line("a", tool), line("b", text)]), encoding="utf-8")
        by_actor, by_model, *_ = ur.scan(base, None, None)
        row = by_actor["session principale"]
        self.assertEqual((row["calls"], row["cache_read"]), (2, 2000))
        self.assertEqual(by_model["m"]["cache_write"], 200)

    def test_cost_per_model_and_review_verdict(self):
        usage = {"input_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 1_000_000, "output_tokens": 1_000_000}
        self.assertAlmostEqual(ur.usd("claude-sonnet-5", usage), 10.20)
        self.assertAlmostEqual(ur.usd("claude-haiku-5-5", usage), 0.51)
        base = Path(tempfile.mkdtemp())
        sub = base / "s1" / "subagents"
        sub.mkdir(parents=True)
        reply = {"type": "assistant", "isSidechain": True, "timestamp": "2026-10-20T10:00:00Z",
                 "message": {"id": "r", "model": "claude-opus-5-5", "usage": usage, "content": [{"type": "text", "text": "Verdict : FAIL — CA2 non couvert"}]}}
        (sub / "agent-x.jsonl").write_text(json.dumps(reply), encoding="utf-8")
        (sub / "agent-x.meta.json").write_text(json.dumps({"agentType": "hosa:hosa-reviewer"}), encoding="utf-8")
        self.assertEqual(dict(ur.scan(base, None, None)[3]), {"FAIL": 1})
        self.assertEqual(dict(ur.scan(base, None, None, until="2026-10-19")[3]), {})


class SprintMeasures(unittest.TestCase):
    def test_pass_stats_and_proposals(self):
        base = Path(tempfile.mkdtemp())
        big = {"input_tokens": 0, "cache_creation_input_tokens": 60_000, "cache_read_input_tokens": 100_000, "output_tokens": 1}
        shot = {"type": "user", "isSidechain": True, "message": {"content": [{"type": "tool_result", "tool_use_id": "u",
                                                                             "content": [{"type": "image", "source": {}}]}]}}
        sub = base / "s1" / "subagents"
        sub.mkdir(parents=True)
        steps = [json.dumps({"type": "assistant", "isSidechain": True, "message": {"id": f"r{i}", "model": "claude-haiku-5-5", "usage": big,
                 "content": [{"type": "tool_use", "id": f"u{i}", "name": "Bash", "input": {}}]}}) for i in range(51)]
        (sub / "agent-ux.jsonl").write_text("\n".join(steps + [json.dumps(shot)]), encoding="utf-8")
        (sub / "agent-ux.meta.json").write_text(json.dumps({"agentType": "hosa:hosa-ux-designer"}), encoding="utf-8")
        _, by_model, _, verdicts, stats = ur.scan(base, None, None)
        self.assertEqual(stats["passes"]["ux"], {"kind": "hosa:hosa-ux-designer", "tools": 51, "ctx": 160_000, "images": 1})
        self.assertEqual(stats["rewrites"][0], 51)
        out = "\n".join(ur.measures("s1", "2026-10-17", None, {"t1"}, ["t1", "t2"], by_model, {"FAIL": 2, "PASS": 1}, stats, [0.01]))
        self.assertIn("tickets livrés : 1/2", out)
        self.assertIn("HOSA_HAIKU=0", out)
        self.assertIn("Coût par ticket en hausse", out)
        self.assertIn("hosa-ux-designer : un passage de 51 appels (plafond 50)", out)

    def test_quiet_sprint_and_section_rewrite(self):
        stats = {"main_ctx": 40_000, "main_images": 0, "rewrites": [0, 0], "passes": {}}
        lines = ur.measures("s1", "2026-10-17", "2026-10-18", {"t1"}, ["t1"], {}, {}, stats, [])
        self.assertEqual(lines[-1], "- Aucune : rien n'a dépassé les seuils.")
        project = Path(tempfile.mkdtemp())
        path = ur.sprint_file(project, "s1")
        path.parent.mkdir(parents=True)
        path.write_text("---\ngenerated: { by: x, at: 2026-10-17T07:00:00Z }\n---\n## Tickets\n- [T](../tickets/t1.md)\n## Démo\n- T1 OK\n", encoding="utf-8")
        self.assertEqual(ur.sprint_period(project, path.read_text(encoding="utf-8")), ("2026-10-17", None, ["t1"]))
        ur.write_section(path, ["## Mesures", "- Coût : 1.00 $ — tickets livrés : 1/1 — Coût par ticket : 1.00 $"])
        ur.write_section(path, ["## Mesures", "- Coût : 2.00 $ — tickets livrés : 1/1 — Coût par ticket : 2.00 $"])
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count("## Mesures"), 1)
        self.assertIn("## Démo\n- T1 OK\n\n## Mesures", text)
        self.assertEqual(ur.earlier_costs(project, "s2"), [2.0])


if __name__ == "__main__":
    unittest.main()
