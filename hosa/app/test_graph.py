import io
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import graph
import kb

VALIDATOR = Path(__file__).resolve().parents[2] / "skills" / "okf" / "scripts" / "okf_validate.py"

FILES = {
    ".hosa/kb/index.md": 'okf_version: "0.2"\n\n# KB\n\n* [cdc](cdc/) - Exigences\n',
    ".hosa/kb/cdc/facturation.md": "---\ntype: Exigence\ntitle: Facturation\nstatus: stable\n---\nExporter les factures.\n",
    ".hosa/kb/tickets/export-csv.md": "---\ntype: Ticket\ntitle: Export CSV\nstate: doing\n---\n"
                                      "Lié à : [exigence](../cdc/facturation.md)\n\nPlacement : `app/billing.py`\n",
    "app/__init__.py": '"""Paquet applicatif."""\n',
    "app/billing.py": '"""Facturation."""\nfrom .util import fmt\n\nclass Invoice:\n    """Une facture."""\n'
                      "    def total(self):\n        return fmt(1)\n\nclass Credit(Invoice):\n    pass\n\n"
                      "def export_csv():\n    return Invoice().total()\n",
    "app/util.py": 'def fmt(x):\n    """Formate."""\n    return str(x)\n\ndef helper():\n    pass\n',
    "lib/other.py": "def helper():\n    pass\n",
    "tools/run.py": "def go():\n    helper()\n",
    "web/store.py": "def save():\n    pass\n",
    "web/main.js": "import { save } from './store';\nexport function run() { save(); helper(); }\n",
    "web/store.js": "// Stockage\nexport function save() {}\n",
}


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


class GraphTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        for rel, text in FILES.items():
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text(text, encoding="utf-8")
        git(self.root, "init", "-q")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")
        (self.root / "app/billing.py").write_text(FILES["app/billing.py"] + "\n# v2\n", encoding="utf-8")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "feat: export",
            "-m", "Hosa-Ticket: export-csv")
        self.g = graph.refresh(self.root)
        self.ix = graph.Index(self.g)

    def tearDown(self):
        self.tmp.cleanup()

    def edges(self, rel):
        return {(e["src"], e["dst"]): e["conf"] for e in self.g["edges"] if e["rel"] == rel}

    def touch(self, rel, text):
        p = self.root / rel
        p.write_text(text, encoding="utf-8")
        future = time.time() + 5
        os.utime(p, (future, future))

    def test_find_filters_and_pages(self):
        self.assertEqual({self.ix.nodes[i]["file"] for i in self.ix.find("helper", path="lib/*")}, {"lib/other.py"})
        self.assertTrue(all(self.ix.nodes[i]["kind"] == "function" for i in self.ix.find("app", kind="function")))
        both = self.ix.find("helper", limit=2)
        self.assertEqual(self.ix.find("helper", limit=1) + self.ix.find("helper", limit=1, offset=1), both)

    def test_status_reports_freshness_and_exclusions(self):
        self.assertIn("à jour", graph.status(self.root))
        (self.root / "app/util.py").write_text(FILES["app/util.py"] + "\n# v3\n", encoding="utf-8")
        os.utime(self.root / "app/util.py", (time.time() + 5, time.time() + 5))
        self.assertIn("1 modifié(s)", graph.status(self.root))
        old = graph.MAX_FILE_BYTES
        graph.MAX_FILE_BYTES = 10
        try:
            self.assertIn("Exclus (> 0 Ko", graph.status(self.root))
            self.assertNotIn("app/billing.py", graph.tracked_files(self.root))
        finally:
            graph.MAX_FILE_BYTES = old

    def test_definitions_with_lines_kinds_and_docs(self):
        n = self.ix.nodes
        self.assertEqual((n["app/billing.py::Invoice"]["kind"], n["app/billing.py::Invoice"]["line"]), ("class", 4))
        self.assertEqual(n["app/billing.py::Invoice.total"]["kind"], "method")
        self.assertEqual(n["app/util.py::fmt"]["doc"], "Formate.")
        self.assertEqual(n["app/billing.py"]["doc"], "Facturation.")
        self.assertEqual(n["web/store.js::save"]["kind"], "function")

    def test_code_edges(self):
        self.assertIn(("app/billing.py", "app/billing.py::Invoice"), self.edges("contains"))
        self.assertIn(("app/billing.py::Invoice", "app/billing.py::Invoice.total"), self.edges("contains"))
        self.assertIn(("app/billing.py", "app/util.py"), self.edges("imports"))
        self.assertIn(("web/main.js", "web/store.js"), self.edges("imports"))
        self.assertNotIn(("web/main.js", "web/store.py"), self.edges("imports"))
        calls = self.edges("calls")
        self.assertEqual(calls[("app/billing.py::Invoice.total", "app/util.py::fmt")], "exact")
        self.assertEqual(calls[("app/billing.py::export_csv", "app/billing.py::Invoice")], "exact")
        self.assertEqual(self.edges("inherits")[("app/billing.py::Credit", "app/billing.py::Invoice")], "exact")

    def test_homonyms_are_ambiguous_not_guessed(self):
        calls = self.edges("calls")
        self.assertEqual(calls[("tools/run.py::go", "app/util.py::helper")], "ambiguous")
        self.assertEqual(calls[("tools/run.py::go", "lib/other.py::helper")], "ambiguous")

    def test_no_call_edge_across_languages(self):
        self.assertFalse([k for k in self.edges("calls") if k[0] == "web/main.js::run" and k[1].endswith("::helper")])
        self.assertEqual(self.edges("calls")[("web/main.js::run", "web/store.js::save")], "exact")

    def test_kb_links(self):
        self.assertIn(("ticket:export-csv", "app/billing.py"), self.edges("touches"))
        self.assertIn(("ticket:export-csv", "exigence:facturation"), self.edges("implements"))
        self.assertIn(("ticket:export-csv", "app/billing.py"), self.edges("mentions"))
        self.assertEqual(self.ix.nodes["ticket:export-csv"]["state"], "doing")

    def test_incremental_replaces_and_prunes(self):
        self.touch("app/util.py", "def fmt2(x):\n    return str(x)\n\ndef helper():\n    pass\n")
        (self.root / "web/store.js").unlink()
        g = graph.refresh(self.root)
        ids = {n["id"] for n in g["nodes"]}
        self.assertNotIn("app/util.py::fmt", ids)
        self.assertIn("app/util.py::fmt2", ids)
        self.assertNotIn("web/store.js", ids)
        self.assertFalse(any(e["dst"] in ("app/util.py::fmt", "web/store.js") for e in g["edges"]))

    def test_targeted_index_of_one_file(self):
        self.touch("app/util.py", "def only():\n    pass\n")
        g = graph.refresh(self.root, [str(self.root / "app/util.py")])
        self.assertIn("app/util.py::only", {n["id"] for n in g["nodes"]})

    def test_code_map_is_okf_and_stable(self):
        concept = self.root / ".hosa/kb/code/app.md"
        fm, body = kb.parse(concept.read_text(encoding="utf-8"))
        self.assertEqual((fm["type"], fm["resource"], fm["generated"]["by"]), ("Module", "app", "process:hosa-graph"))
        self.assertIn("`app/billing.py:4`", body)
        self.assertIn("[Export CSV](../tickets/export-csv.md)", body)
        self.assertIn("[Facturation](../cdc/facturation.md)", body)
        self.assertIn("](code/)", (self.root / ".hosa/kb/index.md").read_text(encoding="utf-8"))
        before = concept.read_text(encoding="utf-8")
        log = (self.root / ".hosa/kb/code/log.md").read_text(encoding="utf-8")
        graph.refresh(self.root)
        self.assertEqual(concept.read_text(encoding="utf-8"), before)
        self.assertEqual((self.root / ".hosa/kb/code/log.md").read_text(encoding="utf-8"), log)
        r = subprocess.run([sys.executable, str(VALIDATOR), str(self.root / ".hosa/kb")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_vanished_module_is_deprecated(self):
        (self.root / "lib/other.py").unlink()
        graph.refresh(self.root)
        fm, _ = kb.parse((self.root / ".hosa/kb/code/lib.md").read_text(encoding="utf-8"))
        self.assertEqual(fm["status"], "deprecated")

    def test_gitignore_written_once(self):
        graph.refresh(self.root)
        lines = (self.root / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines.count(".hosa/graph/"), 1)

    def test_extraction_failure_keeps_the_file_node(self):
        broken = graph.gx.extract
        graph.gx.extract = lambda path, data: (_ for _ in ()).throw(RuntimeError("grammaire indisponible"))
        try:
            self.touch("app/util.py", "def later():\n    pass\n")
            g = graph.refresh(self.root)
        finally:
            graph.gx.extract = broken
        ids = {n["id"] for n in g["nodes"]}
        self.assertIn("app/util.py", ids)
        self.assertNotIn("app/util.py::later", ids)
        self.assertIn("app/billing.py::Invoice", ids)
        g = graph.refresh(self.root)  # grammaire revenue : le fichier en échec est reparsé
        self.assertIn("app/util.py::later", {n["id"] for n in g["nodes"]})

    def test_affected_file_reaches_method_callers(self):
        self.touch("tools/pay.py", "def pay(inv):\n    inv.total()\n")
        ix = graph.Index(graph.refresh(self.root))
        hit = {n["node"]["id"] for n in ix.affected("app/billing.py")["nodes"]}
        self.assertIn("tools/pay.py::pay", hit)

    def test_linked_worktree_stays_clean(self):
        wt = Path(self.tmp.name) / "wt"
        git(self.root, "worktree", "add", "-q", str(wt))
        graph.refresh(wt)
        status = subprocess.run(["git", "-C", str(wt), "status", "--porcelain"],
                                capture_output=True, text=True).stdout
        self.assertEqual(status, "")
        self.assertTrue((wt / ".hosa/graph/graph.json").exists())

    def test_stale_lock_is_taken_over(self):
        lock = self.root / ".hosa/graph/lock"
        lock.write_text("", encoding="utf-8")
        old = time.time() - 120
        os.utime(lock, (old, old))
        graph.refresh(self.root)
        self.assertFalse(lock.exists())

    def test_edit_outside_the_checkout_is_ignored(self):
        outside = Path(self.tmp.name).parent / "elsewhere.py"
        g = graph.refresh(self.root, [str(outside), "README.md"])
        self.assertIn("app/billing.py", {n["id"] for n in g["nodes"]})

    def test_queries_are_fresh_without_explicit_index(self):
        self.touch("app/util.py", FILES["app/util.py"] + "\ndef extra():\n    pass\n")
        self.assertIn("app/util.py::extra", graph.run(self.root, "explain", "extra"))

    def test_query_outputs(self):
        out = graph.run(self.root, "explain", "fmt")
        self.assertIn("function app/util.py::fmt  app/util.py:1", out)
        self.assertIn("← calls", out)
        self.assertIn("app/billing.py::Invoice.total", out)
        self.assertIn("app/billing.py::export_csv", graph.run(self.root, "affected", "app/util.py::fmt"))
        self.assertIn("ticket:export-csv", graph.run(self.root, "affected", "app/util.py::fmt"))
        out = graph.run(self.root, "ticket", "export-csv")
        self.assertIn("exigence:facturation", out)
        self.assertIn("app/billing.py", out)
        self.assertIn("app/util.py::fmt", graph.run(self.root, "find", "fmt"))
        self.assertTrue((self.root / ".hosa/graph/last_query").exists())

    def test_ambiguous_name_lists_candidates(self):
        with self.assertRaisesRegex(graph.GraphError, "ambigu"):
            graph.run(self.root, "explain", "helper")

    def test_budget_truncates(self):
        out = graph.budgeted([f"ligne {i}" for i in range(1000)], budget=10)
        self.assertIn("éléments de plus", out)
        self.assertLess(len(out), 200)

    def test_cli(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = graph.main(["--root", str(self.root), "ticket", "export-csv"])
        self.assertEqual(code, 0)
        self.assertIn("app/billing.py", buf.getvalue())



if __name__ == "__main__":
    unittest.main()
