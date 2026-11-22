"""suite_fusion.py: the merge reruns only the tests a tree diff to a fully passed tree touches."""
import importlib.util
import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "git" / "scripts" / "suite_fusion.py"
spec = importlib.util.spec_from_file_location("suite_fusion", SCRIPT)
sf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sf)

ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


class SuiteFusion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.kb = self.root / "kb"
        (self.kb / "sprints").mkdir(parents=True)
        (self.kb / "test").mkdir()
        self.repo.mkdir()
        self.git("init", "-q")
        self.write("app/main.py", "x = 1\n")
        self.write("tests/test_main.py", "def test(): pass\n")
        self.write("tests/conftest.py", "\n")
        self.write("README.md", "doc\n")
        self.commit()

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True, text=True,
                              env={**os.environ, **ENV}).stdout.strip()

    def write(self, rel, text):
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "c")

    def record(self, line, where="sprints/s1.md", title="Suite complète"):
        (self.kb / where).write_text(f"# S\n\n## {title}\n{line}\n", encoding="utf-8")

    def mark_tested(self, total="10/10", extra=""):
        tree = sf.tree_without_hosa(self.repo, "HEAD")
        self.record(f"- 2026-11-22T10:48Z — Arbre testé : {tree} — suite complète {total}{extra}")
        return tree

    def run_it(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = sf.main([str(self.kb), str(self.repo)])
        return code, out.getvalue()

    def test_same_tree_skips(self):
        self.mark_tested()
        code, out = self.run_it()
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("sauter"))

    def test_hosa_folder_is_left_out_of_the_tree(self):
        self.mark_tested()
        self.write(".hosa/kb/x.md", "kb\n")
        self.commit()
        self.assertEqual(self.run_it()[0], 0)

    def test_rieki_case_only_the_changed_test_files_run(self):
        """rieki sprint-4: a QA commit replaced one browser test file; the merge reran the whole suite."""
        self.write("tests/test_navigateur_parametres.py", "def test(): pass\n")
        self.commit()
        self.mark_tested("1360/1360", " (22 ignorés, navigateur inclus 154/154)")
        (self.repo / "tests/test_navigateur_parametres.py").unlink()
        self.write("tests/test_navigateur_parametres_n.py", "def test_n(): assert 1\n")
        self.write("tests/jeu_de_test/README.md", "jeu\n")
        self.commit()
        code, out = self.run_it()
        self.assertEqual(code, 0)
        self.assertIn("ciblé", out)
        self.assertEqual(out.split("lancer :\n")[1].split(), ["tests/test_navigateur_parametres_n.py"])

    def test_product_code_change_runs_the_full_suite(self):
        self.mark_tested()
        self.write("app/main.py", "x = 2\n")
        self.commit()
        code, out = self.run_it()
        self.assertEqual(code, 1)
        self.assertIn("app/main.py", out)

    def test_a_test_helper_change_runs_the_full_suite(self):
        self.mark_tested()
        self.write("tests/conftest.py", "import os\n")
        self.commit()
        self.assertEqual(self.run_it()[0], 1)

    def test_a_run_without_the_browser_tests_does_not_count(self):
        self.mark_tested("904/904", " (non-navigateur)")
        self.assertEqual(self.run_it()[0], 1)

    def test_a_failed_run_does_not_count(self):
        self.mark_tested("861/885")
        self.assertEqual(self.run_it()[0], 1)

    def test_no_recorded_tree_runs_the_full_suite(self):
        code, out = self.run_it()
        self.assertEqual(code, 1)
        self.assertIn("aucun arbre testé", out)

    def test_a_ticket_result_counts_and_the_closest_tree_wins(self):
        tree = sf.tree_without_hosa(self.repo, "HEAD")
        self.write("tests/test_a.py", "def test(): pass\n")
        self.commit()
        near = sf.tree_without_hosa(self.repo, "HEAD")
        self.record(f"- Arbre testé : {tree} — suite complète 3/3")
        self.record(f"- Arbre testé : {near} — suite complète 4/4", "test/t1-technique.md", "Résultats techniques")
        self.write("tests/test_b.py", "def test(): pass\n")
        self.commit()
        code, out = self.run_it()
        self.assertEqual(code, 0)
        self.assertEqual(out.split("lancer :\n")[1].split(), ["tests/test_b.py"])

    def test_an_unknown_tree_is_ignored(self):
        self.record("- Arbre testé : " + "a" * 40 + " — suite complète 3/3")
        self.assertEqual(self.run_it()[0], 1)

    def test_kinds(self):
        self.assertEqual(sf.kind("src/app.test.ts"), "test")
        self.assertEqual(sf.kind("tests/fixtures/data.json"), "code")
        self.assertEqual(sf.kind("docs/guide.md"), "doc")
        self.assertEqual(sf.kind("app/templates/page.md"), "code")
        self.assertEqual(sf.kind("requirements.txt"), "code")

    def test_bad_ref_exits_2(self):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            self.assertEqual(sf.main([str(self.kb), str(self.repo), "--ref", "nope"]), 2)


if __name__ == "__main__":
    unittest.main()
