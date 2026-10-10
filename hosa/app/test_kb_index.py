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


if __name__ == "__main__":
    unittest.main()
