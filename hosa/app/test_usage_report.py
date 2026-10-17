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
        by_actor, by_model, _ = ur.scan(base, None, None)
        row = by_actor["session principale"]
        self.assertEqual((row["calls"], row["cache_read"]), (2, 2000))
        self.assertEqual(by_model["m"]["cache_write"], 200)


if __name__ == "__main__":
    unittest.main()
