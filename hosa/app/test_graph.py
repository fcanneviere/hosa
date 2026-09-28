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


if __name__ == "__main__":
    unittest.main()
