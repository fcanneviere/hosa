import json
import os
import subprocess
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import graph
import kb
import server

TICKET = """---
type: Ticket
title: Connexion
tags: [auth]
state: todo
sprint: s1
generated: { by: human:fab, at: 2026-09-23T00:00:00Z }
---
Lié à : [exigence](../cdc/login.md)
"""
EXIGENCE = "---\ntype: Exigence\ntitle: Login\nstatus: stable\nverified: { by: human:fab, at: 2026-09-24T00:00:00Z }\n---\n## Données\n- email\n"


class AppTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel, text in {
            "tickets/connexion.md": TICKET,
            "cdc/login.md": EXIGENCE,
            "sprints/s1.md": "---\ntype: Sprint\ntitle: Sprint 1\nstate: active\n---\n",
            "project/identity.md": "---\ntype: Project\ntitle: Démo\n---\n## Objectifs mesurables\n- 100 users\n",
            "broken.md": "---\ntype: [oops\n---\n",
            "cdc/log.md": "# Log — kb/cdc\n\n## 2026-09-20\n- human:fab a créé `login`\n",
        }.items():
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text(text, encoding="utf-8")
        self.srv = server.serve(self.root)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_port}"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()

    def call(self, method, path, body=None, ctype="application/json", host=None):
        req = urllib.request.Request(self.base + path, method=method,
                                     data=None if body is None else json.dumps(body).encode())
        if body is not None:
            req.add_header("Content-Type", ctype)
        if host:
            req.add_header("Host", host)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_walk_skips_broken_and_reserved_and_keeps_dates_as_strings(self):
        paths = {c["path"] for c in kb.walk(self.root)}
        self.assertEqual(paths, {"tickets/connexion.md", "cdc/login.md", "sprints/s1.md", "project/identity.md"})
        t = kb.get(self.root, "tickets/connexion.md")
        self.assertEqual(t["frontmatter"]["generated"]["at"], "2026-09-23T00:00:00Z")
        self.assertEqual(t["trustTier"], "unverified")

    def test_patch_state_rewrites_file_and_logs(self):
        status, c = self.call("PATCH", "/api/concepts/tickets/connexion.md", {"frontmatter": {"state": "doing"}})
        self.assertEqual((status, c["frontmatter"]["state"]), (200, "doing"))
        fm, body = kb.parse((self.root / "tickets/connexion.md").read_text(encoding="utf-8"))
        self.assertEqual((fm["state"], fm["generated"]["at"], body), ("doing", "2026-09-23T00:00:00Z", "Lié à : [exigence](../cdc/login.md)\n"))
        log = (self.root / "tickets/log.md").read_text(encoding="utf-8")
        self.assertIn(f"## {date.today().isoformat()}\n- process:hosa-app a modifié `connexion` (state)", log)

    def test_rejects_bad_state_type_change_traversal_and_reserved(self):
        self.assertEqual(self.call("PATCH", "/api/concepts/tickets/connexion.md", {"frontmatter": {"state": "wip"}})[0], 400)
        self.assertEqual(self.call("PUT", "/api/concepts/tickets/connexion.md", {"frontmatter": "type: Sprint", "body": ""})[0], 400)
        self.assertEqual(self.call("GET", "/api/concepts/..%2F..%2Fsecret.md")[0], 400)
        self.assertEqual(self.call("PUT", "/api/concepts/cdc/log.md", {"frontmatter": "type: X", "body": ""})[0], 400)

    def test_csrf_and_rebinding_guards(self):
        self.assertEqual(self.call("PATCH", "/api/concepts/tickets/connexion.md", {"frontmatter": {"state": "done"}}, ctype="text/plain")[0], 400)
        self.assertEqual(self.call("GET", "/api/overview", host="evil.example")[0], 403)

    def test_put_replaces_frontmatter_and_body(self):
        status, c = self.call("PUT", "/api/concepts/cdc/login.md", {"frontmatter": "title: Login v2\nstatus: draft", "body": "# Hé\n<script>x</script>"})
        self.assertEqual(status, 200)
        self.assertEqual(c["frontmatter"], {"type": "Exigence", "title": "Login v2", "status": "draft"})
        self.assertNotIn("<script", c["bodyHtml"])

    def test_create_then_conflict(self):
        status, c = self.call("POST", "/api/concepts", {"bundle": "tickets", "slug": "export", "type": "Ticket", "title": "Export"})
        self.assertEqual((status, c["path"], c["frontmatter"]["state"]), (201, "tickets/export.md", "todo"))
        self.assertEqual(self.call("POST", "/api/concepts", {"bundle": "tickets", "slug": "export", "type": "Ticket", "title": "X"})[0], 409)
        self.assertEqual(self.call("POST", "/api/concepts", {"bundle": "../x", "slug": "a", "type": "T", "title": "X"})[0], 400)

    def test_overview_pipelines_sprints_activity(self):
        status, ov = self.call("GET", "/api/overview")
        self.assertEqual(status, 200)
        stages = {s["skill"]: s["done"] for p in ov["pipelines"] for s in p["stages"]}
        self.assertTrue(stages["hosa"] and stages["contestation"] and stages["donnees"] and stages["backlog"] and stages["git"])
        self.assertFalse(stages["interview"] or stages["fondamentaux"])
        self.assertEqual(ov["next"], "interview")
        self.assertEqual(ov["project"]["objectives"], "- 100 users")
        self.assertEqual((ov["sprints"][0]["total"], ov["sprints"][0]["done"]), (1, 0))
        self.assertEqual(ov["tickets"]["todo"], 1)
        self.assertEqual(ov["activity"][0]["text"], "human:fab a créé `login`")

    def test_spa_fallback(self):
        with urllib.request.urlopen(self.base + "/whatever") as r:
            self.assertIn(b"<title>Hosa", r.read())


class GraphApiTest(unittest.TestCase):
    """KB servie à l'intérieur d'un dépôt git : le graphe est celui de la racine du dépôt."""

    call = AppTest.call

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.checkout = Path(self.tmp.name).resolve()
        for rel, text in {
            ".hosa/kb/tickets/connexion.md": TICKET,
            ".hosa/kb/cdc/login.md": EXIGENCE,
            "src/auth.py": "def login(user):\n    return check(user)\n\ndef check(user):\n    return True\n",
        }.items():
            (self.checkout / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.checkout / rel).write_text(text, encoding="utf-8")
        git = ["git", "-C", str(self.checkout), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(git + ["init", "-q"], check=True)
        subprocess.run(git + ["add", "."], check=True)
        subprocess.run(git + ["commit", "-qm", "feat: login", "-m", "Hosa-Ticket: connexion"], check=True)
        self.srv = server.serve(self.checkout / ".hosa" / "kb")
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_port}"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()

    def test_missing_graph_says_how_to_build_it(self):
        status, body = self.call("GET", "/api/graph/find?q=login")
        self.assertEqual(status, 404)
        self.assertIn("graph.py index", body["error"])

    def test_find_node_and_trace(self):
        graph.refresh(self.checkout)
        status, found = self.call("GET", "/api/graph/find?q=login")
        self.assertEqual(status, 200)
        self.assertEqual([n["id"] for n in found][:2], ["exigence:login", "src/auth.py::login"])
        status, node = self.call("GET", "/api/graph/node?id=src/auth.py::check")
        self.assertEqual(status, 200)
        self.assertIn(("calls", "src/auth.py::login"), {(e["rel"], e["node"]["id"]) for e in node["in"]})
        self.assertEqual([t["id"] for t in node["affected"]["tickets"]], ["ticket:connexion"])
        self.assertEqual(self.call("GET", "/api/graph/node?id=nope")[0], 404)
        status, trace = self.call("GET", "/api/graph/trace")
        self.assertEqual(trace[0]["node"]["id"], "exigence:login")
        self.assertEqual([f["id"] for f in trace[0]["tickets"][0]["files"]], ["src/auth.py"])

    def test_graph_is_fresh_after_an_edit(self):
        graph.refresh(self.checkout)
        auth = self.checkout / "src/auth.py"
        auth.write_text(auth.read_text(encoding="utf-8") + "\ndef logout():\n    pass\n", encoding="utf-8")
        future = time.time() + 5
        os.utime(auth, (future, future))
        self.assertEqual(self.call("GET", "/api/graph/find?q=logout")[1][0]["id"], "src/auth.py::logout")


if __name__ == "__main__":
    unittest.main()
