"""run.py: serves the managed project's KB (not a sprint worktree's stale copy), builds its venv once."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

spec = importlib.util.spec_from_file_location("run", Path(__file__).resolve().parents[2] / "run.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


class KbRoot(unittest.TestCase):
    def test_walks_up_and_skips_worktrees(self):
        root = Path(tempfile.mkdtemp()).resolve()
        (root / ".hosa" / "kb").mkdir(parents=True)
        wt = root / ".worktrees" / "s1"
        (wt / ".hosa" / "kb").mkdir(parents=True)
        (wt / "src").mkdir()
        self.assertEqual(run.kb_root(wt / "src"), root / ".hosa" / "kb")
        self.assertIsNone(run.kb_root(Path(tempfile.mkdtemp()).resolve()))


class Setup(unittest.TestCase):
    def test_reinstalls_only_when_requirements_change(self):
        d = Path(tempfile.mkdtemp())
        (d / "requirements.txt").write_text("pyyaml\n")
        py = d / "py"
        py.write_text("")
        with mock.patch.multiple(run, VENV=d, PY=py, REQS=d / "requirements.txt", STAMP=d / "stamp"), \
                mock.patch.object(run.subprocess, "check_call") as pip:
            run.setup()
            run.setup()
            self.assertEqual(pip.call_count, 1)
            (d / "requirements.txt").write_text("pyyaml\nnh3\n")
            run.setup()
            self.assertEqual(pip.call_count, 2)


if __name__ == "__main__":
    unittest.main()
