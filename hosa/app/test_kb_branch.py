"""kb_branch.py commit: every pending KB change it takes is named in the commit, whatever the summary says."""
import contextlib
import importlib.util
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "kb_branch", Path(__file__).resolve().parents[2] / "skills" / "kb-commit" / "scripts" / "kb_branch.py")
kb_branch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kb_branch)


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8",
                          check=True).stdout


def quiet(fn, *args):  # its ✓ lines on a cp1252 pipe
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args)


class Commit(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        git(self.root, "init", "-q")
        for k, v in (("user.name", "t"), ("user.email", "t@t")):
            git(self.root, "config", k, v)
        (self.root / "a.txt").write_text("a")
        git(self.root, "add", "a.txt")
        git(self.root, "commit", "-qm", "init")
        self.assertEqual(quiet(kb_branch.init, self.root), 0)
        self.kb = self.root / ".hosa" / "kb"

    def test_body_names_every_file_taken(self):
        # rieki sprint-3: a checkpoint's `add -A` took 52 pending files under a message naming part of them.
        for name in ("tickets/t1.md", "sprints/s1.md"):
            (self.kb / name).parent.mkdir(parents=True, exist_ok=True)
            (self.kb / name).write_text("x", encoding="utf-8")
        self.assertEqual(quiet(kb_branch.commit, self.root, "kb: ticket t1"), 0)
        msg = git(self.kb, "log", "-1", "--format=%B")
        self.assertIn("Fichiers KB (2) :\n- sprints/s1.md\n- tickets/t1.md", msg)
        trailer = git(self.kb, "log", "-1", "--format=%(trailers:key=Hosa-Code-Commit,valueonly)").strip()
        self.assertEqual(trailer, git(self.root, "rev-parse", "HEAD").strip())

    def test_long_lists_are_cut(self):
        for i in range(kb_branch.FILES_SHOWN + 3):
            (self.kb / f"f{i:02}.md").write_text("x", encoding="utf-8")
        quiet(kb_branch.commit, self.root, "kb: lot")
        msg = git(self.kb, "log", "-1", "--format=%B")
        self.assertIn(f"Fichiers KB ({kb_branch.FILES_SHOWN + 3}) :", msg)
        self.assertIn("… et 3 autres", msg)


if __name__ == "__main__":
    unittest.main()
