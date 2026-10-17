import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import graph
import kb
import server
from fixtures import jeu

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

    def test_patch_state_changes_only_the_state_line(self):
        raw = '---\ntype: Ticket\ntitle: "Recherche"\n# note\nstate: todo\ngenerated: { by: hosa-product-owner/1.0, at: 2026-09-23T00:00:00Z }\n---\nCorps\n'
        for eol in ("\n", "\r\n"):
            with self.subTest(eol=repr(eol)):
                path = self.root / "tickets/quote.md"
                path.write_bytes(raw.replace("\n", eol).encode("utf-8"))
                self.assertEqual(self.call("PATCH", "/api/concepts/tickets/quote.md", {"frontmatter": {"state": "doing"}})[0], 200)
                self.assertEqual(path.read_bytes(), raw.replace("state: todo", "state: doing").replace("\n", eol).encode("utf-8"))

    def test_rejects_bad_state_type_change_traversal_and_reserved(self):
        self.assertEqual(self.call("PATCH", "/api/concepts/tickets/connexion.md", {"frontmatter": {"state": "wip"}})[0], 400)
        self.assertEqual(self.call("PUT", "/api/concepts/tickets/connexion.md", {"frontmatter": "type: Sprint", "body": ""})[0], 400)
        self.assertEqual(self.call("GET", "/api/concepts/..%2F..%2Fsecret.md")[0], 400)
        self.assertEqual(self.call("PUT", "/api/concepts/cdc/log.md", {"frontmatter": "type: X", "body": ""})[0], 400)

    def test_csrf_and_rebinding_guards(self):
        self.assertEqual(self.call("PATCH", "/api/concepts/tickets/connexion.md", {"frontmatter": {"state": "done"}}, ctype="text/plain")[0], 400)
        self.assertEqual(self.call("GET", "/api/overview", host="evil.example")[0], 403)

    def _ticket_file(self):
        return (self.root / "tickets/connexion.md").read_text(encoding="utf-8")

    def test_patch_each_state_and_board_column(self):
        for state in ("todo", "doing", "blocked", "done"):
            status, c = self.call("PATCH", "/api/concepts/tickets/connexion.md", {"frontmatter": {"state": state}})
            self.assertEqual((status, c["frontmatter"]["state"]), (200, state))
            self.assertEqual(kb.parse(self._ticket_file())[0]["state"], state)
            board = self.call("GET", "/api/overview")[1]["board"]
            self.assertEqual([r["state"] for r in board if r["slug"] == "connexion"], [state])

    def test_patch_bad_state_values(self):
        before = self._ticket_file()
        for bad in ("", None, 3, ["doing"], "doing\nowner: x"):
            status, r = self.call("PATCH", "/api/concepts/tickets/connexion.md", {"frontmatter": {"state": bad}})
            self.assertEqual(status, 400, bad)
            self.assertIn("state doit valoir : todo, doing, blocked, done", r["error"])
            self.assertEqual(self._ticket_file(), before)
            self.assertNotIn("owner", self._ticket_file())
        self.assertFalse((self.root / "tickets/log.md").exists())

    def test_patch_type_is_immutable(self):
        before = self._ticket_file()
        self.assertEqual(self.call("PATCH", "/api/concepts/tickets/connexion.md", {"frontmatter": {"type": "Sprint"}})[0], 400)
        self.assertEqual(self._ticket_file(), before)

    def test_patch_missing_ticket_is_404(self):
        files = sorted(p.name for p in (self.root / "tickets").iterdir())
        self.assertEqual(self.call("PATCH", "/api/concepts/tickets/absent.md", {"frontmatter": {"state": "doing"}})[0], 404)
        self.assertEqual(sorted(p.name for p in (self.root / "tickets").iterdir()), files)

    def test_patch_broken_yaml_is_400(self):
        (self.root / "tickets/casse.md").write_text("---\ntype: Ticket\ntitle: [oops\nstate: todo\n---\n", encoding="utf-8")
        before = (self.root / "tickets/casse.md").read_text(encoding="utf-8")
        status, r = self.call("PATCH", "/api/concepts/tickets/casse.md", {"frontmatter": {"state": "doing"}})
        self.assertEqual(status, 400)
        self.assertNotIn("Traceback", r["error"])
        self.assertNotIn(str(self.root), r["error"])
        self.assertEqual((self.root / "tickets/casse.md").read_text(encoding="utf-8"), before)
        self.assertFalse((self.root / "tickets/log.md").exists())

    def test_patch_hostile_paths_are_400(self):
        (self.root / "tickets/log.md").write_text("# Log\n", encoding="utf-8")
        (self.root / "index.md").write_text("# Index\n", encoding="utf-8")
        for p in ("tickets/log.md", "tickets/index.md", "tickets/../index.md", "tickets/../../x.md"):
            status, _ = self.call("PATCH", "/api/concepts/" + p, {"frontmatter": {"state": "doing"}})
            self.assertEqual(status, 400, p)
        self.assertEqual((self.root / "tickets/log.md").read_text(encoding="utf-8"), "# Log\n")
        self.assertEqual((self.root / "index.md").read_text(encoding="utf-8"), "# Index\n")

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
        self.assertFalse(stages["interview"] or stages["fondamentaux"] or stages["juridique"] or stages["securite"])
        self.assertEqual(ov["next"], "interview")
        self.assertEqual(ov["project"]["objectives"], "- 100 users")
        self.assertEqual((ov["sprints"][0]["total"], ov["sprints"][0]["done"]), (1, 0))
        self.assertEqual(ov["tickets"]["todo"], 1)
        self.assertEqual(ov["activity"][0]["text"], "human:fab a créé `login`")

    def test_overview_plan_follows_avancement(self):
        self.assertIsNone(self.call("GET", "/api/overview")[1]["plan"])  # pas de plan : l'app retombe sur l'heuristique
        with contextlib.redirect_stdout(io.StringIO()):
            for stage in kb.av.PIPELINES[0][1] + kb.av.PIPELINES[1][1]:
                kb.av.main([str(self.root), "done", stage])
            kb.av.main([str(self.root), "skip", "menaces", "--detail", "pas d'API"])
            kb.av.main([str(self.root), "start", "sprint", "--sprint", "s1", "--detail", "composition"])
        plan = self.call("GET", "/api/overview")[1]["plan"]
        self.assertEqual((plan["next"]["stage"], plan["next"]["skill"], plan["next"]["section"]), ("sprint", "sprint", "Sprint s1"))
        self.assertIn("`## Tickets` ne liste aucun ticket", plan["next"]["gaps"])
        self.assertEqual([s["title"] for s in plan["sections"]], ["Cahier des charges", "Structuration", "Sprint s1"])
        menaces = next(s for s in plan["sections"][1]["stages"] if s["stage"] == "menaces")
        self.assertEqual((menaces["status"], menaces["detail"]), ("non applicable", "pas d'API"))
        self.assertTrue(plan["resume"][0].startswith("En cours : `sprint` (sprint s1)"))

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

    def gjson(self):
        return graph.graph_dir(self.checkout) / "graph.json"

    def test_trace_builds_the_index_when_absent(self):  # CA1
        self.assertFalse(self.gjson().exists())
        status, trace = self.call("GET", "/api/graph/trace")
        self.assertEqual(status, 200)
        self.assertEqual(trace[0]["node"]["id"], "exigence:login")
        self.assertTrue(self.gjson().exists())
        self.assertEqual(self.call("GET", "/api/graph/trace"), (status, trace))

    def test_find_without_index_builds_it(self):  # CA1
        self.assertFalse(self.gjson().exists())
        status, found = self.call("GET", "/api/graph/find?q=login")
        self.assertEqual(status, 200)
        self.assertEqual(found[0]["id"], "exigence:login")

    def test_node_without_index_builds_it(self):  # CA1
        self.assertFalse(self.gjson().exists())
        self.assertEqual(self.call("GET", "/api/graph/node?id=src/auth.py::check")[0], 200)

    def test_first_build_writes_only_graph_dir_gitignore_and_code_map(self):  # sécurité
        self.call("GET", "/api/graph/trace")
        out = subprocess.run(["git", "-C", str(self.checkout), "status", "--porcelain", "-uall"],
                             capture_output=True, text=True, check=True).stdout
        changed = [l[3:].strip() for l in out.splitlines()]
        self.assertTrue(all(c.startswith((".hosa/graph/", ".hosa/kb/code/")) or c == ".gitignore" for c in changed), changed)
        ignored = subprocess.run(["git", "-C", str(self.checkout), "check-ignore", ".hosa/graph/graph.json"],
                                 capture_output=True)
        self.assertEqual(ignored.returncode, 0)

    def test_foreign_host_is_refused_and_builds_nothing(self):  # sécurité
        status, _ = self.call("GET", "/api/graph/trace", host="evil.example")
        self.assertNotEqual(status, 200)
        self.assertFalse(self.gjson().exists())

    def test_no_git_project_says_graph_is_built_at_session_open(self):  # CA3
        with tempfile.TemporaryDirectory() as d:
            d = Path(d).resolve()
            probe = subprocess.run(["git", "-C", str(d), "rev-parse", "--show-toplevel"], capture_output=True)
            if probe.returncode == 0:
                self.skipTest(f"le dossier temporaire est dans un dépôt git : {probe.stdout.decode().strip()}")
            (d / "src").mkdir()
            (d / "src/x.py").write_text("def f(): pass", encoding="utf-8")
            (d / ".hosa" / "kb").mkdir(parents=True)
            srv = server.serve(d / ".hosa" / "kb")
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            self.addCleanup(srv.server_close)
            self.addCleanup(srv.shutdown)
            self.base = f"http://127.0.0.1:{srv.server_port}"
            status, body = self.call("GET", "/api/graph/trace")
            self.assertEqual(status, 404)
            self.assertEqual(body["error"], "Graphe absent : il se construit à l'ouverture d'une session Claude Code dans le projet")
            for bad in ("git", "Traceback", ".py", str(d)):
                self.assertNotIn(bad, body["error"])
            self.assertFalse((d / ".hosa" / "graph").exists())

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
        self.assertEqual(self.call("GET", "/api/graph/trace")[0], 200)  # CA2
        self.assertEqual(self.call("GET", "/api/graph/find?q=logout")[1][0]["id"], "src/auth.py::logout")

GIT = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]


class KbStatusTest(unittest.TestCase):
    call = AppTest.call

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.srv = None

    def tearDown(self):
        if self.srv:
            self.srv.shutdown()
            self.srv.server_close()
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(GIT + list(args), cwd=self.root, capture_output=True, text=True, check=True).stdout

    def repo(self):
        self.git("init", "-q")
        (self.root / "a.md").write_text("a", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")

    def serve(self):
        self.srv = server.serve(self.root)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_port}"

    def status(self):
        return self.call("GET", "/api/kb-status")

    def test_clean_repo(self):
        self.repo(); self.serve()
        self.assertEqual(self.status(), (200, {"git": True, "changed": 0, "files": []}))

    def test_three_changes_and_ca4_commit_without_restart(self):
        self.repo(); self.serve()
        for n in "bcd":
            (self.root / f"{n}.md").write_text(n, encoding="utf-8")
        self.assertEqual(self.status()[1]["changed"], 3)
        self.git("add", "-A"); self.git("commit", "-q", "-m", "x")
        self.assertEqual(self.status(), (200, {"git": True, "changed": 0, "files": []}))

    def test_code_map_is_not_counted(self):  # etat-kb-bandeau-fichiers CA1, CA2
        self.repo(); self.serve()
        (self.root / "code").mkdir()
        (self.root / "code" / "x.md").write_text("carte", encoding="utf-8")
        self.assertEqual(self.status()[1], {"git": True, "changed": 0, "files": []})
        (self.root / "a.md").write_text("changed", encoding="utf-8")
        for n in "bc":
            (self.root / f"{n}.md").write_text(n, encoding="utf-8")
        self.assertEqual(self.status()[1]["changed"], 3)

    def test_files_and_their_state(self):  # etat-kb-bandeau-fichiers CA3
        self.repo()
        (self.root / "z.md").write_text("z", encoding="utf-8")
        self.git("add", "-A"); self.git("commit", "-q", "-m", "z")
        self.serve()
        (self.root / "a.md").write_text("changed", encoding="utf-8")
        (self.root / "z.md").unlink()
        (self.root / "é t.md").write_text("n", encoding="utf-8")
        files = sorted(self.status()[1]["files"], key=lambda f: f["path"])
        self.assertEqual(files, [{"path": "a.md", "state": "modifié"}, {"path": "z.md", "state": "supprimé"},
                                 {"path": "é t.md", "state": "nouveau"}])

    def test_non_git_dir(self):
        self.serve()
        self.assertEqual(self.status(), (200, {"git": False, "changed": 0, "files": []}))

    def test_counting_limits(self):
        self.repo(); self.serve()
        (self.root / "a.md").write_text("changed", encoding="utf-8")
        self.assertEqual(self.status()[1]["changed"], 1)
        self.git("checkout", "-q", "--", "a.md")
        (self.root / "new.md").write_text("n", encoding="utf-8")
        self.assertEqual(self.status()[1]["changed"], 1)
        (self.root / "new.md").unlink()
        (self.root / "dir").mkdir()
        for n in "xy":
            (self.root / "dir" / f"{n}.md").write_text(n, encoding="utf-8")
        self.assertEqual(self.status()[1]["changed"], 1)

    def test_git_absent_is_500_without_path(self):
        self.repo(); self.serve()
        with patch("kb.subprocess.run", side_effect=FileNotFoundError):
            status, body = self.status()
        self.assertEqual(status, 500)
        self.assertIn("error", body)
        self.assertNotIn(str(self.root), json.dumps(body))

    def test_timeout_is_500_without_path(self):
        self.repo(); self.serve()
        with patch("kb.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 10)):
            status, body = self.status()
        self.assertEqual(status, 500)
        self.assertNotIn(str(self.root), json.dumps(body))

    def test_status_failure_is_500_without_path(self):
        self.repo(); self.serve()
        ok = subprocess.CompletedProcess([], 0, "true" + chr(10), "")
        ko = subprocess.CompletedProcess([], 128, "", f"fatal: {self.root}")
        with patch("kb.subprocess.run", side_effect=[ok, ko]):
            status, body = self.status()
        self.assertEqual(status, 500)
        self.assertIn("error", body)
        self.assertNotIn(str(self.root), json.dumps(body))

    def test_call_does_not_modify_worktree(self):
        self.repo(); self.serve()
        (self.root / "u.md").write_text("u", encoding="utf-8")
        before = self.git("status", "--short")
        self.status()
        self.assertEqual(self.git("status", "--short"), before)

    def test_post_not_allowed(self):
        self.repo(); self.serve()
        self.assertNotEqual(self.call("POST", "/api/kb-status", {})[0], 200)


NO_DATA = "Aucune donnée de consommation trouvée pour ce projet"


class UsageApiTest(unittest.TestCase):
    """GET /api/usage : lit les transcripts factices via kb.ur.project_dir patché (jamais ~/.claude)."""

    call = AppTest.call

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.checkout = Path(self.tmp.name).resolve()
        self.tr = self.checkout.parent / (self.checkout.name + "-transcripts")
        self.tr.mkdir()
        kbroot = self.checkout / ".hosa" / "kb"
        (kbroot / "project").mkdir(parents=True)
        (kbroot / "project" / "identity.md").write_text("---\ntype: Project\ntitle: Demo\n---\n", encoding="utf-8")
        self.srv = server.serve(kbroot)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_port}"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()
        shutil.rmtree(self.tr, ignore_errors=True)

    def ur(self):
        """Patch de project_dir ; échoue (sans erreur d'import) tant que kb.ur n'existe pas."""
        ur = getattr(kb, "ur", None)
        if ur is None:
            self.fail("kb.ur absent : usage_report.py n'est pas chargé par kb.py")
        return ur

    def patched(self, target=None):
        return patch.object(self.ur(), "project_dir", lambda root: target or self.tr)

    def get(self, qs=""):
        with self.patched():
            return self.call("GET", "/api/usage" + qs)

    def model(self, body, name="claude-opus-5-5"):
        return next(m for m in body["models"] if m["name"] == name)

    def test_values_match_scan_and_cost(self):  # CA1
        jeu.transcripts(self.tr)
        status, body = self.get("?days=7")
        self.assertEqual(status, 200)
        ur = self.ur()
        by_actor, by_model, *_ = ur.scan(self.tr, (date.today() - timedelta(days=7)).isoformat(), None)
        for key, table in (("agents", by_actor), ("models", by_model)):
            rows = body[key]
            self.assertEqual({r["name"] for r in rows}, set(table))
            total = sum(r["usd"] for r in table.values())
            self.assertEqual([r["name"] for r in rows],
                             sorted(table, key=lambda n: -table[n]["usd"]))
            for r in rows:
                for f in ur.FIELDS:
                    self.assertEqual(r[f], table[r["name"]][f], (r["name"], f))
                self.assertAlmostEqual(r["part"], 100 * table[r["name"]]["usd"] / total)

    def test_window_boundaries(self):  # CA1
        jeu.transcripts(self.tr)
        _, b7 = self.get("?days=7")
        o = self.model(b7)
        self.assertEqual((o["calls"], o["input"]), (2, 170))  # aujourd'hui 100 + d(7) 70 ; d(8), d(40) exclus
        self.assertEqual(self.model(b7, "claude-sonnet-4-5")["input"], 40)  # d(20) exclu
        _, b30 = self.get("?days=30")
        self.assertEqual((self.model(b30)["calls"], self.model(b30)["input"]), (3, 250))  # + d(8), d(40) exclu
        self.assertEqual(self.model(b30, "claude-sonnet-4-5")["input"], 240)  # + d(20)

    def test_default_is_7_days(self):  # CA2
        jeu.transcripts(self.tr)
        s1, b1 = self.get()
        s2, b2 = self.get("?days=7")
        self.assertEqual((s1, b1), (s2, b2))
        self.assertEqual(s1, 200)

    def test_since_is_the_date_given_to_scan(self):  # consommation-source-date CA5
        jeu.transcripts(self.tr)
        for days in (7, 30):
            self.assertEqual(self.get(f"?days={days}")[1]["since"], (date.today() - timedelta(days=days)).isoformat())

    def test_no_data_is_404(self):  # CA3
        for label, setup in (
            ("dossier absent", lambda: shutil.rmtree(self.tr)),
            ("dossier vide", lambda: None),
            ("transcripts trop anciens", lambda: jeu.transcripts(self.tr, today=date.today() - timedelta(days=100))),
        ):
            with self.subTest(label):
                shutil.rmtree(self.tr, ignore_errors=True)
                self.tr.mkdir()
                setup()
                status, body = self.get()
                self.assertEqual(status, 404)
                self.assertEqual(body["error"], NO_DATA)

    def test_script_failure_is_500_with_message(self):  # CA4
        jeu.transcripts(self.tr)
        with self.patched(), patch.object(self.ur(), "scan", side_effect=RuntimeError("boom")):
            status, body = self.call("GET", "/api/usage")
        self.assertEqual(status, 500)
        self.assertIn("boom", body["error"])

    def test_invalid_days_is_400(self):  # CA5
        jeu.transcripts(self.tr)
        with self.patched(), patch.object(self.ur(), "scan") as scan:
            for raw in ("abc", "0", "-3", "1.5", "1%3Bls", "..%2F..%2Fx", "%00", "99999999999999999999", "3651", ""):
                with self.subTest(days=raw):
                    status, body = self.call("GET", f"/api/usage?days={raw}")
                    self.assertEqual(status, 400)
                    self.assertTrue(body["error"])
            scan.assert_not_called()

    def test_spawns_no_process(self):
        jeu.transcripts(self.tr)
        with self.patched(), patch("subprocess.run") as run, patch("subprocess.Popen") as popen:
            status, _ = self.call("GET", "/api/usage")
        self.assertEqual(status, 200)
        run.assert_not_called()
        popen.assert_not_called()

    def test_read_only(self):
        jeu.transcripts(self.tr)
        snap = lambda: {str(f): (f.stat().st_size, f.stat().st_mtime_ns) for f in self.tr.rglob("*")}
        before = snap()
        self.assertEqual(self.get("?days=30")[0], 200)
        self.assertEqual(snap(), before)


class CouvertureTest(unittest.TestCase):
    """GET /api/couverture et kb.coverage_of (ticket qualite-couverture-criteres-api).
    Cas 15 à 19 (navigateur, app.js, lexique, documentation) : recette, pas de test automatisé ici."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = jeu.ecrire(Path(self.tmp.name))
        self.srv = server.serve(self.root)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_port}"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()

    call = AppTest.call

    def test_route_gives_dataset_values(self):  # cas 9
        status, body = self.call("GET", "/api/couverture")
        self.assertEqual(status, 200)
        tickets = {c["path"] for c in kb.walk(self.root) if c["frontmatter"].get("type") == "Ticket"}
        self.assertEqual(set(body), tickets)
        for v in body.values():
            self.assertEqual(set(v), {"criteres", "couverts", "total", "plan"})
        self.assertEqual(body["tickets/connexion.md"],
                         {"criteres": ["CA1", "CA2", "CA3"], "couverts": ["CA1", "CA2"], "total": 3, "plan": True})
        self.assertEqual(body["tickets/export-csv.md"]["couverts"], ["CA1", "CA3"])
        self.assertEqual(body["tickets/annuaire.md"],
                         {"criteres": ["CA1", "CA2"], "couverts": ["CA1"], "total": 2, "plan": False})
        self.assertEqual(body["tickets/recherche.md"], {"criteres": [], "couverts": [], "total": 0, "plan": False})

    def test_route_equals_avancement_coverage(self):  # cas 10
        status, body = self.call("GET", "/api/couverture")
        self.assertEqual(status, 200)
        self.assertTrue(body)
        for path, v in body.items():
            self.assertEqual(v, kb.av.coverage(self.root, Path(path).stem), path)

    def test_unreadable_recette_is_ignored(self):  # cas 11 et 14 : un fichier non UTF-8 est ignoré
        before = self.call("GET", "/api/couverture")[1]["tickets/recherche.md"]
        jeu.ecrire(self.root, jeu.NON_UTF8)
        status, body = self.call("GET", "/api/couverture")
        self.assertEqual(status, 200)
        self.assertEqual(body["tickets/recherche.md"], before)
        self.assertEqual(body["tickets/recherche.md"]["total"], 0)
        self.assertNotIn("Traceback", json.dumps(body))

    def test_coverage_of_refuses_paths_outside_tickets(self):  # cas 12
        if not hasattr(kb, "coverage_of"):
            self.fail("kb.coverage_of n'existe pas")
        for bad in ("../x.md", str(self.root / "tickets" / "connexion.md"), "/etc/passwd", "cdc/login.md"):
            with self.assertRaises(kb.KbError, msg=bad):
                kb.coverage_of(self.root, bad)

    def test_hostile_criterion_does_not_break_patterns(self):  # cas 13
        status, body = self.call("GET", "/api/couverture")
        self.assertEqual(status, 200)
        self.assertEqual(body["tickets/titre-hostile.md"]["criteres"], ["CA1", "CA2"])


class BoardTest(unittest.TestCase):
    """GET /api/overview -> board et kb.points (ticket tickets-tableau-colonnes).
    Cas navigateur (colonnes, carte, total affiché, texte vide, titre en texte brut, 390/1280 px, lexique) : recette.
    Cas chemin `../` : déjà couvert par test_app.py (/api/concepts/..%2F..%2Fsecret.md -> 400)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = jeu.ecrire(Path(self.tmp.name))
        self.srv = server.serve(self.root)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_port}"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()

    call = AppTest.call

    def board(self):
        status, body = self.call("GET", "/api/overview")
        self.assertEqual(status, 200)
        self.assertIn("board", body)
        return body["board"]

    def col(self, state):
        return [t["slug"] for t in self.board() if t["state"] == state]

    def by_slug(self):
        return {t["slug"]: t for t in self.board()}

    def test_each_ticket_in_its_column_only(self):  # CA1
        b = self.board()
        slugs = [t["slug"] for t in b]
        self.assertEqual(len(slugs), len(set(slugs)))
        expected = {"connexion": "doing", "export-csv": "doing", "annuaire": "doing", "recherche": "todo",
                    "titre-hostile": "blocked", "inscription": "done"}
        got = {t["slug"]: t["state"] for t in b}
        for slug, state in expected.items():
            self.assertEqual(got.get(slug), state, slug)

    def test_unknown_or_missing_state_is_todo(self):  # CA1
        got = self.by_slug()
        self.assertEqual(got["etat-inconnu"]["state"], "todo")
        self.assertEqual(got["sans-etat"]["state"], "todo")

    def test_sorted_by_priority_then_title(self):  # CA2
        self.assertEqual(self.col("doing"), ["annuaire", "export-csv", "connexion"])

    def test_no_priority_last(self):  # CA2
        self.assertEqual(self.col("todo"), ["recherche", "etat-inconnu", "sans-etat"])
        self.assertIsNone(self.by_slug()["sans-etat"]["priority"])

    def test_entry_keys(self):  # CA3
        for t in self.board():
            self.assertLessEqual({"slug", "title", "priority", "estimate", "sprint", "origine", "validation"}, set(t))
        self.assertEqual(self.by_slug()["connexion"]["title"], "Connexion")

    def test_origine_and_validation(self):  # CA3
        got = self.by_slug()
        pick = lambda s: (got[s]["origine"], got[s]["validation"])
        self.assertEqual(pick("connexion"), ("humain", "humain"))
        self.assertEqual(pick("export-csv"), ("agent", "machine"))
        self.assertEqual(pick("annuaire"), ("agent", "aucune"))
        self.assertEqual(got["sans-etat"]["origine"], "agent")

    def test_points_totals(self):  # CA4
        got = self.by_slug()
        self.assertEqual(sum(got[s]["points"] for s in self.col("doing")), 11)
        self.assertEqual([got[s]["points"] for s in ("recherche", "titre-hostile", "inscription", "etat-inconnu")],
                         [1, 2, 1, 0])

    def test_points_function(self):  # CA4
        self.assertTrue(hasattr(kb, "points"), "kb.points manquant")
        cases = [("S", 1), ("M", 3), ("L", 5), ("m", 3), (2, 2), ("2", 2), (None, 0), ("à voir", 0), (True, 0), (-1, 0)]
        for value, want in cases:
            self.assertEqual(kb.points(value), want, repr(value))

    def test_empty_kb_gives_empty_board(self):  # CA5
        with tempfile.TemporaryDirectory() as d:
            srv = server.serve(jeu.ecrire(Path(d), {"README.md": "# vide"}))
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            try:
                self.base = f"http://127.0.0.1:{srv.server_port}"
                status, body = self.call("GET", "/api/overview")
            finally:
                srv.shutdown()
                srv.server_close()
        self.assertEqual(status, 200)
        self.assertEqual(body.get("board"), [])

    def test_hostile_title_returned_as_is(self):  # sécurité
        self.assertEqual(self.by_slug()["titre-hostile"]["title"], "<img src=x onerror=alert(1)>")


class ValidationProvenanceTest(unittest.TestCase):
    """Ticket validation-provenance-liste : couche serveur (le reste est en recette)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = jeu.ecrire(Path(self.tmp.name))
        self.srv = server.serve(self.root)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_port}"
        self.f = self.root / "cdc/export.md"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()

    call = AppTest.call

    def test_trust_tier_values(self):
        for path, tier in (("cdc/export.md", "unverified"), ("cdc/obsolete-lint.md", "machine-confirmed"),
                           ("cdc/login.md", "human-reviewed")):
            self.assertEqual(self.call("GET", "/api/concepts/" + path)[1]["trustTier"], tier, path)

    def test_patch_verified_writes_file_and_logs_without_content(self):
        at = "2026-10-12T10:00:00Z"
        status, _ = self.call("PATCH", "/api/concepts/cdc/export.md",
                              {"frontmatter": {"verified": {"by": "human:fabien", "at": at}}})
        self.assertEqual(status, 200)
        self.assertEqual(kb.get(self.root, "cdc/export.md")["frontmatter"]["verified"], {"by": "human:fabien", "at": at})
        log = (self.root / "cdc/log.md").read_text(encoding="utf-8")
        self.assertIn("process:hosa-app a modifié `export` (verified)", log)
        self.assertNotIn(at, log)

    def test_patch_plain_text_refused_file_unchanged(self):
        before = self.f.read_bytes()
        status, _ = self.call("PATCH", "/api/concepts/cdc/export.md",
                              {"frontmatter": {"verified": {"by": "human:x", "at": "2026-10-12T00:00:00Z"}}},
                              ctype="text/plain")
        self.assertEqual(status, 400)
        self.assertEqual(self.f.read_bytes(), before)

    def test_patch_null_verified_cancels_validation(self):
        path = "/api/concepts/cdc/login.md"
        self.assertEqual(self.call("PATCH", path, {"frontmatter": {"verified": {"by": None, "at": None}}})[0], 200)
        # le serveur fusionne : verified devient {by: None, at: None}, le niveau retombe à unverified
        self.assertEqual(kb.get(self.root, "cdc/login.md")["frontmatter"]["verified"], {"by": None, "at": None})
        self.assertEqual(self.call("GET", path)[1]["trustTier"], "unverified")


class RecettesTest(unittest.TestCase):
    """`recettes` de GET /api/overview (ticket qualite-recettes-api). Cas navigateur : recette (T1-T4)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = jeu.ecrire(Path(self.tmp.name))
        self.srv = server.serve(self.root)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_port}"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()

    call = AppTest.call

    def recettes(self):
        status, body = self.call("GET", "/api/overview")
        self.assertEqual(status, 200)
        self.assertIn("recettes", body)
        return body["recettes"]

    def by_path(self, path):
        found = [r for r in self.recettes() if r.get("path") == path]
        self.assertEqual(len(found), 1, path)
        return found[0]

    def add(self, name, verdict, title=None):
        jeu.ecrire(self.root, {f"test/{name}.md": jeu.recette("zz", name, verdict, title=title)})

    def test_entry_shape_and_pass(self):  # CA1
        r = self.by_path("test/connexion-martine.md")
        self.assertEqual({k: r.get(k) for k in ("ticket", "titre", "persona", "at", "verdict")},
                         {"ticket": "tickets/connexion.md", "titre": "Connexion", "persona": "martine",
                          "at": "2026-10-08T10:00:00Z", "verdict": "PASS"})

    def test_pass_with_notes_and_fail_as_is(self):  # CA1
        self.assertEqual(self.by_path("test/annuaire-camille.md").get("verdict"), "PASS-WITH-NOTES")
        self.assertEqual(self.by_path("test/export-csv-karim.md").get("verdict"), "FAIL")

    def test_no_verdict_section_is_null_but_listed(self):  # CA1
        self.assertIsNone(self.by_path("test/inscription-martine.md").get("verdict", "absent"))

    def test_fail_first_then_date_desc(self):  # CA2
        mine = ["test/export-csv-karim.md", "test/connexion-martine.md", "test/annuaire-camille.md",
                "test/inscription-martine.md", "test/recherche-karim.md"]
        rs = self.recettes()
        self.assertEqual([r.get("path") for r in rs if r.get("path") in mine], mine)
        self.assertEqual(rs[0].get("verdict"), "FAIL")

    def test_ties_ordered_by_path(self):  # CA2
        self.add("zz-b", "## Verdict\nPASS\n")
        self.add("zz-a", "## Verdict\nPASS\n")
        paths = [r.get("path") for r in self.recettes() if r.get("path", "").startswith("test/zz-")]
        self.assertEqual(paths, ["test/zz-a.md", "test/zz-b.md"])

    def test_technique_plans_excluded(self):  # CA3
        paths = [r.get("path") for r in self.recettes()]
        self.assertFalse([p for p in paths if p.endswith("-technique.md")])
        self.assertIn("test/export-csv-karim.md", paths)

    def test_empty_or_missing_test_dir_gives_empty_list(self):  # CA4
        shutil.rmtree(self.root / "test")
        self.assertEqual(self.recettes(), [])
        (self.root / "test").mkdir()
        self.assertEqual(self.recettes(), [])

    def test_kb_without_test_folder_gives_empty_list(self):  # CA4
        with tempfile.TemporaryDirectory() as d:
            jeu.ecrire(Path(d), {})
            self.assertEqual(kb.overview(Path(d)).get("recettes"), [])

    def test_hostile_title_returned_as_is(self):  # sécurité
        hostile = "<img src=x onerror=alert(1)>"
        self.add("orphelin-karim", "## Verdict\nPASS\n", hostile)
        self.assertEqual(self.by_path("test/orphelin-karim.md").get("titre"), hostile)

    def test_hostile_verdict_never_raw(self):  # sécurité
        self.assertEqual(self.by_path("test/recherche-karim.md").get("verdict"), "PASS")  # PASS<script>
        self.add("zz-inconnu", "## Verdict\nPASSED\n")
        self.add("zz-js", "## Verdict\n<script>alert(1)</script>\n")
        self.assertIsNone(self.by_path("test/zz-inconnu.md").get("verdict", "absent"))
        self.assertIsNone(self.by_path("test/zz-js.md").get("verdict", "absent"))
        for r in self.recettes():
            self.assertIn(r.get("verdict", "absent"), ("PASS", "PASS-WITH-NOTES", "FAIL", None), r)

    def test_non_utf8_file_ignored_without_trace(self):  # sécurité
        jeu.ecrire(self.root, jeu.NON_UTF8)
        status, body = self.call("GET", "/api/overview")
        self.assertEqual(status, 200)
        self.assertNotIn("test/recherche-martine.md", [r.get("path") for r in body["recettes"]])
        text = json.dumps(body)
        self.assertNotIn("Traceback", text)
        self.assertNotIn(self.tmp.name.replace("\\", "/"), text.replace("\\\\", "/"))

    def test_non_utf8_log_does_not_break_overview(self):  # sécurité (kb.activity)
        (self.root / "test" / "log.md").write_bytes("# Log\n\n## 2026-10-01\n- caf\xe9\n".encode("latin-1"))
        status, body = self.call("GET", "/api/overview")
        self.assertEqual(status, 200)
        self.assertNotIn("Traceback", json.dumps(body))

    def test_non_utf8_file_keeps_concepts_list(self):  # sécurité (tâche 1)
        avant = sorted(c["path"] for c in kb.walk(self.root))
        jeu.ecrire(self.root, jeu.NON_UTF8)
        self.assertEqual(sorted(c["path"] for c in kb.walk(self.root)), avant)
        status, body = self.call("GET", "/api/concepts")
        self.assertEqual(status, 200)
        self.assertNotIn("Traceback", json.dumps(body))

    def test_non_utf8_concept_is_clean_400(self):  # sécurité (kb.get)
        jeu.ecrire(self.root, jeu.NON_UTF8)
        status, body = self.call("GET", "/api/concepts/test/recherche-martine.md")
        self.assertEqual(status, 400)
        text = json.dumps(body)
        self.assertNotIn("Traceback", text)
        self.assertNotIn(self.tmp.name.replace("\\", "/"), text.replace("\\\\", "/"))

    def test_non_utf8_avancement_does_not_break_overview(self):  # sécurité (av.load)
        (self.root / "project").mkdir(exist_ok=True)
        (self.root / "project" / "avancement.md").write_bytes(("# Avancement\n\n## caf\xe9\n").encode("latin-1"))
        status, body = self.call("GET", "/api/overview")
        self.assertEqual(status, 200)
        self.assertNotIn("Traceback", json.dumps(body))

    def test_read_only_and_relative_paths(self):  # sécurité
        def snap():
            return {str(f): f.read_bytes() for f in (self.root / "test").rglob("*") if f.is_file()}
        before = snap()
        rs = self.recettes()
        self.recettes()
        self.assertEqual(snap(), before)
        self.assertTrue(rs)
        for r in rs:
            self.assertNotIn("..", r.get("path", ".."))
            self.assertFalse(r.get("path", "/").startswith("/"))
        self.assertIn(self.call("POST", "/api/overview", {})[0], range(400, 500))


class BacklogApiTest(unittest.TestCase):
    """Tickets du backlog après le sprint 1 : un test par critère vérifiable côté serveur."""
    setUp, tearDown, call = AppTest.setUp, AppTest.tearDown, AppTest.call

    def put(self, rel, text):
        (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.root / rel).write_text(text, encoding="utf-8")

    def ov(self):
        return self.call("GET", "/api/overview")[1]

    # qualite-audits-sprint-demo
    def test_audits_security_bloquants_and_demo(self):
        self.assertIsNone(self.ov()["security"])  # CA3
        self.put("qualite/audit.md", "---\ntype: Audit Qualité\ngenerated: { by: x, at: 2026-10-01T00:00:00Z }\n---\n## Verdict\nPASS-WITH-NOTES — 2 remarques\n")
        self.put("securite/audit-2026-10-02-app.md", "---\ntype: Audit\ngenerated: { by: x, at: 2026-10-02T00:00:00Z }\n---\n## Verdict\nFAIL\n")
        self.put("sprints/s1.md", "---\ntype: Sprint\ntitle: Sprint 1\nstate: active\n---\n## Audit\nBloquant : 5\nBloquant : 2\n## Démo\n- T1 recherche — OK\n- T2 export — KO\n"
                 "## Mesures\n2026-10-20 — x\n- Coût : 4.00 $\n\n### Propositions\n- Aucune : rien n'a dépassé les seuils.\n")
        ov = self.ov()
        self.assertEqual((ov["quality"]["at"], ov["quality"]["verdict"]), ("2026-10-01T00:00:00Z", "PASS-WITH-NOTES"))  # CA1
        self.assertEqual((ov["security"]["at"], ov["security"]["verdict"]), ("2026-10-02T00:00:00Z", "FAIL"))  # CA2
        s1 = ov["sprints"][0]
        self.assertEqual(s1["audit"], {"bloquants": 2})  # CA4
        self.assertEqual(s1["demo"], [{"t": "T1", "ok": True}, {"t": "T2", "ok": False}])  # CA5
        self.assertEqual(s1["mesures"], ["Coût : 4.00 $", "Aucune : rien n'a dépassé les seuils."])

    # sprints-points-velocite
    def test_points_velocity_and_remaining_sprints(self):
        t = "---\ntype: Ticket\ntitle: {0}\nstate: {1}\nsprint: {2}\nestimate: {3}\n---\n"
        self.put("sprints/s0.md", "---\ntype: Sprint\ntitle: S0\nstate: done\n---\n")
        self.put("sprints/s2.md", "---\ntype: Sprint\ntitle: S2\nstate: done\n---\n")
        self.put("tickets/connexion.md", t.format("Connexion", "todo", "s1", 5))
        self.put("tickets/a.md", t.format("A", "done", "s0", 8))
        self.put("tickets/b.md", t.format("B", "done", "s2", 12))
        self.put("tickets/c.md", t.format("C", "todo", "s1", "à voir"))
        self.put("tickets/d.md", t.format("D", "done", "s1", 3))
        self.put("tickets/e.md", "---\ntype: Ticket\ntitle: E\nstate: todo\nestimate: 30\n---\n")
        ov = self.ov()
        s1 = next(s for s in ov["sprints"] if s["slug"] == "s1")
        self.assertEqual((s1["engages"], s1["faits"], s1["restants"]), (8, 3, 5))  # CA1
        self.assertEqual(ov["velocite"], {"moyenne": 10, "ouverts": 35, "restants": 3.5})  # CA2, CA3

    def test_no_done_sprint_no_velocity(self):  # sprints-points-velocite CA4
        self.assertEqual(self.ov()["velocite"]["moyenne"], None)
        self.assertEqual(self.ov()["velocite"]["restants"], None)

    # tickets-fichiers-illisibles + exigences-liste-filtres-compteur CA5
    def test_unreadable_files_listed_with_plain_cause(self):
        self.put("tickets/casse.md", "---\ntype: Ticket\ntitle: Casse\nstate: [oops\n---\n")
        (self.root / "cdc/latin.md").write_bytes("---\ntype: Exigence\ntitle: Été\n---\n".encode("latin-1"))
        ill = {i["path"]: i["cause"] for i in self.ov()["illisibles"]}
        self.assertEqual(ill["tickets/casse.md"], "l'en-tête est mal écrit (ligne 4)")  # CA1 (ligne du fichier)
        self.assertEqual(ill["cdc/latin.md"], "le fichier n'est pas en UTF-8")  # CA3
        self.assertIn("broken.md", ill)
        self.assertNotIn("tickets/casse.md", {c["path"] for c in self.call("GET", "/api/concepts")[1]})

    def test_patch_broken_ticket_says_why_without_yaml_words(self):  # tickets-fichiers-illisibles CA4
        self.put("tickets/casse.md", "---\ntype: Ticket\ntitle: Casse\nstate: [oops\n---\n")
        before = (self.root / "tickets/casse.md").read_bytes()
        status, r = self.call("PATCH", "/api/concepts/tickets/casse.md", {"frontmatter": {"state": "doing"}})
        self.assertEqual((status, r["error"]), (400, "Le fichier est illisible : l'en-tête est mal écrit (ligne 4)"))
        for word in ("YAML", "scanning", "<unicode string>"):
            self.assertNotIn(word, r["error"])
        self.assertEqual((self.root / "tickets/casse.md").read_bytes(), before)

    def test_no_unreadable_file(self):  # tickets-fichiers-illisibles CA2
        (self.root / "broken.md").unlink()
        self.assertEqual(self.ov()["illisibles"], [])

    # concepts-edition-garde-fous
    def test_put_with_baseline_and_conflict(self):
        c = self.call("GET", "/api/concepts/cdc/login.md")[1]
        status, c2 = self.call("PUT", "/api/concepts/cdc/login.md", {"frontmatter": c["frontmatterYaml"], "body": "v2\n", "baseline": c["version"]})
        self.assertEqual((status, c2["body"]), (200, "v2\n"))  # CA1
        self.assertIn("`login` (corps)", (self.root / "cdc/log.md").read_text(encoding="utf-8").split("\n")[3])  # plus récente en tête
        self.put("cdc/login.md", (self.root / "cdc/login.md").read_text(encoding="utf-8") + "agent\n")  # un agent écrit
        before = (self.root / "cdc/login.md").read_text(encoding="utf-8")
        status, r = self.call("PUT", "/api/concepts/cdc/login.md", {"frontmatter": c["frontmatterYaml"], "body": "v3\n", "baseline": c2["version"]})
        self.assertEqual(status, 409)  # CA5
        self.assertIn("modifié entre-temps", r["error"])
        self.assertEqual((self.root / "cdc/login.md").read_text(encoding="utf-8"), before)

    def test_put_invalid_yaml_points_at_the_field(self):  # concepts-edition-garde-fous CA3
        before = (self.root / "cdc/login.md").read_text(encoding="utf-8")
        status, r = self.call("PUT", "/api/concepts/cdc/login.md", {"frontmatter": "type: Exigence\ntitle: [oops", "body": "x"})
        self.assertEqual((status, r["champ"], r["error"]), (400, "frontmatter", "l'en-tête est mal écrit (ligne 2)"))
        self.assertEqual((self.root / "cdc/login.md").read_text(encoding="utf-8"), before)

    # concepts-creation
    def test_create_refusals(self):
        for body in ({"bundle": "tickets", "slug": "Été 2", "type": "Ticket", "title": "X"},  # CA3
                     {"bundle": "tickets", "slug": "ok", "type": "", "title": "X"},  # CA4
                     {"bundle": "tickets", "slug": "ok", "type": "Ticket", "title": ""},
                     {"bundle": "../..", "slug": "ok", "type": "Ticket", "title": "X"}):  # CA5
            self.assertEqual(self.call("POST", "/api/concepts", body)[0], 400, body)
        self.assertFalse((self.root / "tickets/ok.md").exists())
        self.call("POST", "/api/concepts", {"bundle": "tickets", "slug": "neuf", "type": "Ticket", "title": "Neuf"})
        self.assertIn("a créé `neuf` (Ticket)", (self.root / "tickets/log.md").read_text(encoding="utf-8"))  # CA1

    # concepts-lecture-liens-historique
    def test_concept_links_and_history(self):
        c = self.call("GET", "/api/concepts/cdc/login.md")[1]
        self.assertEqual(c["liens"]["entrants"], [{"path": "tickets/connexion.md", "title": "Connexion"}])  # CA3
        self.assertEqual(self.call("GET", "/api/concepts/tickets/connexion.md")[1]["liens"]["sortants"], [{"path": "cdc/login.md", "title": "Login"}])
        self.assertEqual(c["historique"], [{"date": "2026-09-20", "acteur": "human:fab", "texte": "human:fab a créé `login`"}])  # CA4
        for bad in ("cdc/log.md", "index.md", "..%2Fx.md"):
            self.assertEqual(self.call("GET", "/api/concepts/" + bad)[0], 400, bad)  # CA5

    # journal-groupe-filtres
    def test_activity_actor_and_link(self):
        self.put("tickets/log.md", "# Log\n\n## 2026-09-21\n- hosa-tester/1.0 a testé `connexion`\n- process:hosa-app a modifié `inconnu`\n")
        act = {a["text"]: a for a in self.call("GET", "/api/activity")[1]}
        self.assertEqual((act["human:fab a créé `login`"]["acteur"], act["human:fab a créé `login`"]["lien"]), ("humain", "cdc/login.md"))  # CA2, CA5
        self.assertEqual((act["hosa-tester/1.0 a testé `connexion`"]["acteur"], act["hosa-tester/1.0 a testé `connexion`"]["lien"]), ("agent", "tickets/connexion.md"))
        self.assertEqual((act["process:hosa-app a modifié `inconnu`"]["acteur"], act["process:hosa-app a modifié `inconnu`"]["lien"]), ("processus", None))

    # graphe-recherche-impact CA4 : message sans identifiant brut
    def test_unknown_graph_node_message(self):
        with patch("server._in_git", return_value=True), patch("graph.refresh", return_value={"nodes": {}, "edges": []}), \
                patch("graph.Index") as idx:
            idx.return_value.nodes = {}
            status, r = self.call("GET", "/api/graph/node?id=src%2Fx.py")
        self.assertEqual((status, r["error"]), (404, "Élément introuvable"))


if __name__ == "__main__":
    unittest.main()
