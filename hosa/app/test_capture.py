"""capture.py / capture.mjs: screenshots whose verdict a machine reads — rendering, accessibility, routes rendered."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "interface" / "scripts"
spec = importlib.util.spec_from_file_location("capture", SCRIPTS / "capture.py")
cap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cap)

NAV = """---
type: Plan de navigation
---
## Écrans
| Écran | Route | Rôles | Exigences servies | Accès depuis | Espace |
|---|---|---|---|---|---|
| Accueil | `/` | client | — | connexion | front-office |
| Commande | `/commandes/:id` | client | — | Commandes | front-office |
| Fiche | `/clients/{slug}/notes/[n]` | admin | — | Clients | back-office |
| Accueil bis | `/` | client | — | menu | front-office |
## Vérification
| pas | `/ici` |
"""


def chrome() -> bool:
    if os.environ.get("CHROME_PATH"):
        return True
    for c in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if Path(c).exists():
            return True
    return any(shutil.which(n) for n in ("google-chrome", "chromium", "chromium-browser"))


class Routes(unittest.TestCase):
    def test_routes_come_from_the_screens_table_once_each(self):
        with tempfile.TemporaryDirectory() as d:
            nav = Path(d) / "navigation.md"
            nav.write_text(NAV, encoding="utf-8")
            self.assertEqual(cap.routes_du_plan(nav), ["/", "/commandes/:id", "/clients/{slug}/notes/[n]"])

    def test_one_pass_per_role_keeps_that_role_s_routes(self):
        with tempfile.TemporaryDirectory() as d:
            nav = Path(d) / "navigation.md"
            nav.write_text(NAV, encoding="utf-8")
            self.assertEqual(cap.roles_du_plan(nav), ["client", "admin"])
            self.assertEqual(cap.routes_du_plan(nav, "Admin"), ["/clients/{slug}/notes/[n]"])
            self.assertEqual(cap.routes_du_plan(nav, "client"), ["/", "/commandes/:id"])
            self.assertEqual(cap.main(["http://localhost:1", "--navigation", str(nav), "--valeurs", "id=1,slug=a,n=1"]), 2)
            self.assertEqual(cap.main(["http://localhost:1", "--navigation", str(nav), "--role", "stagiaire"]), 2)
            self.assertEqual(cap.main(["http://localhost:1", "--role", "client"]), 2)

    def test_a_parameter_without_a_value_is_named_never_guessed(self):
        routes = ["/", "/commandes/:id", "/clients/{slug}/notes/[n]"]
        full, gaps = cap.remplit(routes, {"id": "42"})
        self.assertEqual(full, ["/", "/commandes/42"])
        self.assertEqual(gaps, ["route /clients/{slug}/notes/[n] : donne une valeur à slug, n (--valeurs slug=…)"])
        self.assertEqual(cap.remplit(routes, {"id": "42", "slug": "dupont", "n": "3"})[0][-1], "/clients/dupont/notes/3")

    def test_bad_calls_exit_2_and_a_missing_node_exits_3(self):
        with tempfile.TemporaryDirectory() as d:
            nav = Path(d) / "navigation.md"
            nav.write_text(NAV, encoding="utf-8")
            self.assertEqual(cap.main(["http://localhost:1", "--navigation", str(nav), "--role", "client"]), 2)  # :id
            self.assertEqual(cap.main(["x", "--navigation", str(nav), "--routes", "/"]), 2)
            self.assertEqual(cap.main(["x", "--valeurs", "id"]), 2)
            with unittest.mock.patch.object(cap, "node", return_value=None):
                self.assertEqual(cap.main(["page.html"]), 3)


@unittest.skipUnless(cap.node() and chrome(), "Node 22+ et Chrome/Edge requis")
class Navigateur(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_capture(self, *args):
        r = subprocess.run([sys.executable, str(SCRIPTS / "capture.py"), *args, "--out", str(self.d / "out")],
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
        report = json.loads((self.d / "out" / "report.json").read_text(encoding="utf-8")) \
            if (self.d / "out" / "report.json").exists() else None
        return r.returncode, r.stdout + r.stderr, report

    def test_a_clean_page_passes_and_a_flawed_one_lists_each_issue(self):
        ok = self.d / "ok.html"
        ok.write_text('<!doctype html><html lang="fr"><head><title>T</title></head><body><main><h1>Commandes</h1>'
                      '<label for="q">Recherche</label><input id="q"><button>Exporter</button></main></body></html>',
                      encoding="utf-8")
        code, out, _ = self.run_capture(str(ok), "--size", "1280x900")
        self.assertEqual(code, 0, out)
        envoi = self.d / "envoi.html"  # a small submit button is no text field: no zoom on it
        envoi.write_text('<!doctype html><html lang="fr"><head><title>T</title></head><body><h1>Envoi</h1>'
                         '<input type="submit" value="Envoyer" style="font-size:13px;min-height:44px"></body></html>',
                         encoding="utf-8")
        code, out, _ = self.run_capture(str(envoi), "--size", "390x844")
        self.assertEqual(code, 0, out)
        self.assertIn("Verdict : OK", out)
        ko = self.d / "ko.html"
        ko.write_text('<!doctype html><html><head><meta name="viewport" content="width=device-width, maximum-scale=1"></head><body style="background:#fff"><h2>Section</h2><h4>Sous-section</h4><p style="color:#bbb">Gris pâle</p><label>Ville <input style="font-size:13px"></label>'
                      '<img src="data:image/gif;base64,R0lGODlhAQABAAAAACw="><input name="nom"><button></button>'
                      '<a href="#x" style="display:inline-block;width:10px;height:10px;background:#000"></a>'
                      '<div style="width:3000px">large</div><script>throw new Error("boum")</script></body></html>',
                      encoding="utf-8")
        code, out, report = self.run_capture(str(ko), "--size", "390x844")
        self.assertEqual(code, 1, out)
        issues = " | ".join(report["captures"][0]["issues"])
        for want in ("langue de la page absente", "contraste", "image sans alt", "champ sans libellé : input [name=nom]",
                     "bouton sans nom accessible", "cible tactile", "débordement horizontal", "erreur de script",
                     "titre de page absent", "zoom bloqué", "aucun titre h1 visible",
                     "niveau de titre sauté : h4 après un h2", "champ en 13 px < 16 px sur mobile"):
            self.assertIn(want, issues)
        self.assertRegex(out, r"Verdict : \d+ problème")

    def test_routes_rendered_are_counted_like_the_verification_line(self):
        page = '<!doctype html><html lang="fr"><head><title>T</title></head><body><h1>{}</h1></body></html>'
        (self.d / "a.html").write_text(page.format("A"), encoding="utf-8")
        (self.d / "vide.html").write_text('<!doctype html><html lang="fr"><head><title>T</title></head><body></body></html>', encoding="utf-8")
        (self.d / "sans-titre.html").write_text('<!doctype html><html lang="fr"><body><h1>B</h1></body></html>', encoding="utf-8")
        code, out, report = self.run_capture(str(self.d / "a.html"), "--routes",
                                             "/a.html,/absente.html,/vide.html,/sans-titre.html", "--size", "1280x900")
        self.assertEqual(code, 1, out)
        # an accessibility issue is fixed in 3c, but the route rendered: it is not a gap of the verification line
        self.assertIn("Routes rendues : 2 / 4", out)
        self.assertEqual(report["routes"]["rendues"], 2)
        self.assertIn("titre de page absent", " ".join(c["issues"][0] for c in report["captures"] if c["issues"]))
        self.assertIn("HTTP 404", report["routes"]["echecs"]["/absente.html"])
        self.assertIn("page vide", report["routes"]["echecs"]["/vide.html"])

    def test_a_login_played_once_lets_the_role_s_routes_render(self):
        (self.d / "login.html").write_text('<!doctype html><html lang="fr"><head><title>T</title></head><body><h1>Connexion</h1>'
                                           '<button id="go" onclick="localStorage.ok=1">Se connecter</button></body></html>',
                                           encoding="utf-8")
        (self.d / "admin.html").write_text('<!doctype html><html lang="fr"><head><title>T</title></head><body><h1>Administration</h1><script>'
                                           'if(!localStorage.ok)location.replace("/login.html")</script></body></html>',
                                           encoding="utf-8")
        code, out, _ = self.run_capture(str(self.d / "login.html"), "--routes", "/admin.html", "--size", "1280x900")
        self.assertIn("redirigé vers /login.html", out)
        self.assertIn("Routes rendues : 0 / 1", out)
        code, out, _ = self.run_capture(str(self.d / "login.html"), "--routes", "/admin.html", "--size", "1280x900",
                                        "--connexion", "goto /login.html; click #go; wait 100")
        self.assertEqual(code, 0, out)
        self.assertIn("Routes rendues : 1 / 1", out)

    def test_states_sheet_and_marks(self):
        (self.d / "s.html").write_text('<!doctype html><html lang="fr"><head><title>T</title></head><body><h1 id="t">x</h1><script>'
                                       'document.getElementById("t").textContent=new URLSearchParams(location.search).get("state")'
                                       '</script></body></html>', encoding="utf-8")
        code, out, _ = self.run_capture(str(self.d / "s.html"), "--states", "vide,erreur", "--sheet",
                                        "--mark", "1=#t", "--size", "800x600")
        self.assertEqual(code, 0, out)
        names = sorted(p.name for p in (self.d / "out").glob("*.png"))
        self.assertEqual(names, ["erreur-800x600-marque.png", "erreur-800x600.png", "planche-800x600.png",
                                 "vide-800x600-marque.png", "vide-800x600.png"])

    def test_a_click_that_changes_page_waits_for_it_and_wait_takes_a_selector(self):
        (self.d / "login.html").write_text('<!doctype html><html lang="fr"><head><title>T</title></head><body><h1>Connexion</h1>'
                                           '<a id="go" href="/fini.html" onclick="localStorage.ok=1">Se connecter</a></body></html>',
                                           encoding="utf-8")
        (self.d / "fini.html").write_text('<!doctype html><html lang="fr"><head><title>T</title></head><body><h1>Fini</h1><script>'
                                          'setTimeout(()=>document.body.insertAdjacentHTML("beforeend","<p id=tard>tard</p>"),300)'
                                          '</script></body></html>', encoding="utf-8")
        (self.d / "admin.html").write_text('<!doctype html><html lang="fr"><head><title>T</title></head><body><h1>Admin</h1><script>'
                                           'if(!localStorage.ok)location.replace("/login.html")</script></body></html>',
                                           encoding="utf-8")
        # no "wait" after the click: the next page is awaited, then the late element
        code, out, _ = self.run_capture(str(self.d / "login.html"), "--routes", "/admin.html", "--size", "800x600",
                                        "--connexion", "click #go; wait #tard")
        self.assertEqual(code, 0, out)
        self.assertIn("Routes rendues : 1 / 1", out)
        code, out, report = self.run_capture(str(self.d / "login.html"), "--size", "800x600", "--steps", "wait #jamais")
        self.assertIn("élément absent", " ".join(report["captures"][0]["issues"]))

    def test_mask_turns_text_into_bars_and_the_sheet_wraps_four_per_row(self):
        (self.d / "s.html").write_text('<!doctype html><html lang="fr"><head><title>T</title></head><body><h1>Titre</h1><p>Texte</p></body></html>',
                                       encoding="utf-8")
        code, out, _ = self.run_capture(str(self.d / "s.html"), "--states", "a,b,c,d,e", "--sheet", "--mask",
                                        "--size", "400x300")
        self.assertEqual(code, 0, out)
        names = {p.name for p in (self.d / "out").glob("*.png")}
        self.assertIn("a-400x300-masque.png", names)
        self.assertIn("planche-400x300-masque.png", names)
        png = (self.d / "out" / "planche-400x300.png").read_bytes()
        width, height = int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big")
        self.assertEqual(width, 4 * 400 + 3 * 20 + 56)  # five states: four on the first row
        self.assertGreater(height, 2 * 300)

    def test_a_folder_serves_its_index(self):
        (self.d / "index.html").write_text('<!doctype html><html lang="fr"><head><title>T</title></head><body><p>Accueil</p></body></html>',
                                           encoding="utf-8")
        code, out, _ = self.run_capture(str(self.d), "--size", "800x600")
        self.assertEqual(code, 0, out)

    def test_the_local_server_serves_nothing_outside_the_page_s_folder(self):
        sub = self.d / "site"
        sub.mkdir()
        (self.d / "secret.html").write_text("<p>secret</p>", encoding="utf-8")
        (sub / ".env.html").write_text("<p>secret</p>", encoding="utf-8")
        (sub / "i.html").write_text('<!doctype html><html lang="fr"><head><title>T</title></head><body><p>i</p></body></html>', encoding="utf-8")
        _, out, report = self.run_capture(str(sub / "i.html"), "--routes", "/../secret.html,/.env.html,/ENV~1.HTM,/i.html",
                                          "--size", "800x600", "--sans-a11y")
        self.assertEqual(report["routes"]["rendues"], 1, out)


import unittest.mock  # noqa: E402

if __name__ == "__main__":
    unittest.main()
