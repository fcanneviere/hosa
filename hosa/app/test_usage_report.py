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
        by_actor, by_model, _, _ = ur.scan(base, None, None)
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


if __name__ == "__main__":
    unittest.main()
