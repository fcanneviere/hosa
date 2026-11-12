"""atelier.py: style cards held to WCAG AA, an offline comparison page, the user's choice and the tokens in the KB."""
import copy
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "interface" / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("atelier", SCRIPTS / "atelier.py")
at = importlib.util.module_from_spec(spec)
spec.loader.exec_module(at)
EXEMPLE = ROOT / "skills" / "interface" / "assets" / "exemple-cartes.json"
OKF = ROOT / "skills" / "okf" / "scripts" / "okf_validate.py"

PAGE = "<!doctype html><html lang=fr><head><title>x</title></head><body>{}</body></html>"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def cfg(self, **change) -> Path:
        data = json.loads(EXEMPLE.read_text(encoding="utf-8"))
        data.update(change)
        p = self.d / "cartes.json"
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return p

    def manifest(self, cands: list[dict], **extra) -> Path:
        m = {"schemaVersion": 1, "project": "P", "brief": "B", "round": "directions", "candidates": cands, **extra}
        p = self.d / "m" / "manifest.json"
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
        return p

    def html(self, name: str, body: str, head: str = "") -> dict:
        (self.d / "m").mkdir(exist_ok=True)
        (self.d / "m" / name).write_text(PAGE.replace("<title>x</title>", "<title>x</title>" + head).replace("{}", body),
                                         encoding="utf-8")
        return {"id": Path(name).stem, "name": name, "concept": "c", "typography": "t", "palette": ["#000000"],
                "traits": ["t"], "kind": "html", "source": name}


class Contraste(unittest.TestCase):
    def test_wcag_ratios_match_the_reference_values(self):
        self.assertAlmostEqual(at.contraste("#000000", "#FFFFFF"), 21.0, places=2)
        self.assertAlmostEqual(at.contraste("#767676", "#FFFFFF"), 4.54, places=2)  # the classic AA limit grey
        self.assertEqual(at.mix("#000000", "#ffffff", 0.5), "#808080")

    def test_every_pair_the_card_shows_is_checked_with_its_own_minimum(self):
        col = dict(bg="#ffffff", surface="#ffffff", text="#000000", muted="#000000", accent="#000000",
                   accent_text="#ffffff", line="#eeeeee", warn="#000000")
        self.assertEqual(at.controles(col)[1], [])
        col["accent"] = "#bbbbbb"  # light accent: white label unreadable, and a button under 3:1 on the page
        gaps = at.controles(col)[1]
        self.assertTrue(any(g.startswith("texte sur accent") and "il faut 4.5:1" in g for g in gaps), gaps)
        self.assertTrue(any(g.startswith("accent sur fond") and "il faut 3.0:1" in g for g in gaps), gaps)


class Cartes(Base):
    def test_the_example_builds_cards_a_manifest_and_one_offline_page(self):
        r = at.cartes(self.cfg(), self.d / "out", False)
        out = self.d / "out"
        self.assertEqual(r["cartes"], 4)
        self.assertEqual(sorted(p.name for p in out.iterdir()),
                         ["carte-gallery.html", "carte-glaze.html", "carte-kiln.html", "carte-zine.html",
                          "comparaison.html", "manifest.json"])
        page = (out / "comparaison.html").read_text(encoding="utf-8")
        self.assertNotIn("__ATELIER_DONNEES__", page)
        self.assertNotRegex(page, r"""(?:src|href)=["']https?://""")
        self.assertLess(len(page.encode()), 150_000)  # no font, no framework: oil-ui's page weighed 284 kB
        m = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(all(c["controles"] for c in m["candidates"]))

    def test_the_recommended_card_is_option_a_as_in_the_question(self):
        at.cartes(self.cfg(recommande="kiln"), self.d / "out", False)
        self.assertIn("A · Cours du soir", (self.d / "out" / "carte-kiln.html").read_text(encoding="utf-8"))
        r = at.comparer(self.d / "out" / "manifest.json", self.d / "p.html")
        self.assertEqual(r["lettres"]["kiln"], "a")

    def test_a_card_under_wcag_aa_is_refused_with_its_exact_pairs_and_nothing_written(self):
        data = json.loads(EXEMPLE.read_text(encoding="utf-8"))
        data["cards"][0]["colors"]["muted"] = "#B0A89F"
        p = self.d / "c.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(at.Refus) as e:
            at.cartes(p, self.d / "out", False)
        msg = str(e.exception)
        self.assertIn("carte glaze — texte secondaire sur fond : #B0A89F sur #EFE7DA", msg)
        self.assertIn("il faut 4.5:1", msg)
        self.assertFalse((self.d / "out").exists())

    def test_bad_configurations_are_refused_before_writing(self):
        data = json.loads(EXEMPLE.read_text(encoding="utf-8"))
        cases = {
            "cards : 2 à 6": lambda d: d.update(cards=d["cards"][:1]),
            "hexadécimale": lambda d: d["cards"][0]["colors"].update(bg="red"),
            "pas de police réseau": lambda d: d["cards"][0]["fonts"].update(body="url(http://x)"),
            "même contenu": lambda d: d["cards"][0].update(content={}),
            "id invalide ou en double": lambda d: d["cards"][1].update(id=d["cards"][0]["id"]),
            "layout doit valoir": lambda d: d["cards"][0].update(layout="carousel"),
            "radius": lambda d: d["cards"][0].update(radius=99),
            "rows": lambda d: d["content"]["screen"]["rows"].append(["trop court"]),
        }
        for want, change in cases.items():
            d = copy.deepcopy(data)
            change(d)
            p = self.d / "c.json"
            p.write_text(json.dumps(d), encoding="utf-8")
            with self.assertRaises(at.Refus, msg=want) as e:
                at.cartes(p, self.d / "out", False)
            self.assertIn(want, str(e.exception))
        self.assertFalse((self.d / "out").exists())

    def test_content_is_escaped_and_the_real_screen_is_drawn(self):
        data = json.loads(EXEMPLE.read_text(encoding="utf-8"))
        data["content"]["title"] = "<script>alert(1)</script>"
        p = self.d / "c.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        at.cartes(p, self.d / "out", False)
        carte = (self.d / "out" / "carte-gallery.html").read_text(encoding="utf-8")
        self.assertNotIn("<script>alert", carte)
        self.assertIn("&lt;script&gt;", carte)
        self.assertIn("<td>Camille Roux</td>", carte)  # the screen's real rows, not grey blocks

    def test_an_existing_page_needs_force_and_hosa_s_folder_is_off_limits(self):
        at.cartes(self.cfg(), self.d / "out", False)
        with self.assertRaises(at.Refus):
            at.cartes(self.cfg(), self.d / "out", False)
        at.cartes(self.cfg(), self.d / "out", True)
        with self.assertRaises(at.Refus):
            at.cartes(self.cfg(), at.SKILL / "tmp-out", True)
        self.assertFalse((at.SKILL / "tmp-out").exists())
        p = self.d / "out" / "manifest.json"
        p.write_text(EXEMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        with self.assertRaises(at.Refus):  # the configuration would be overwritten by the output
            at.cartes(p, self.d / "out", True)


class Comparer(Base):
    def test_a_mockup_s_outside_resources_are_refused(self):
        for body, head in (('<img src="http://x/a.png">', ""), ("<iframe></iframe>", ""), ("<object></object>", ""),
                           ("", '<link rel="stylesheet" href="https://cdn/x.css">'),
                           ("", "<style>@import 'x.css';</style>"),
                           ("", "<style>a{background:url(https://x/y.png)}</style>"),
                           ("", "<style>a{background:\\75rl(https://x/y.png)}</style>"),  # escaped `url`
                           ('<div style="background:url(//x/y.png)"></div>', ""),
                           ("", '<base href="/">'), ("", '<meta http-equiv="refresh" content="0;url=x">')):
            c = self.html("a.html", body, head)
            with self.assertRaises(at.Refus, msg=body + head):
                at.comparer(self.manifest([c]), self.d / "p.html", force=True)

    def test_data_urls_and_text_mentioning_url_are_not_resources(self):
        c = self.html("a.html", "<p>url(http://x) is text</p>", "<style>a{background:url(data:image/png;base64,AA==)}</style>")
        at.comparer(self.manifest([c]), self.d / "p.html")

    def test_local_files_are_embedded_and_files_outside_the_folder_stay_refused(self):
        (self.d / "m").mkdir()
        (self.d / "m" / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\nxx")
        (self.d / "m" / "s.css").write_text("b{color:red}", encoding="utf-8")
        c = self.html("a.html", '<img src="logo.png" alt="l">', '<link rel="stylesheet" href="s.css">')
        at.comparer(self.manifest([c]), self.d / "p.html")
        page = (self.d / "p.html").read_text(encoding="utf-8")
        self.assertIn("data:image/png;base64", page)
        self.assertIn("b{color:red}", page)
        (self.d / "secret.png").write_bytes(b"\x89PNG\r\n\x1a\nxx")
        c = self.html("b.html", '<img src="../secret.png">')
        with self.assertRaises(at.Refus):
            at.comparer(self.manifest([c]), self.d / "q.html")

    def test_scripts_run_only_in_an_interactive_mockup(self):
        (self.d / "m").mkdir()
        (self.d / "m" / "app.js").write_text("window.ok=1", encoding="utf-8")
        c = self.html("a.html", '<script src="app.js"></script>')
        at.comparer(self.manifest([c]), self.d / "p.html")
        self.assertNotIn("window.ok=1", (self.d / "p.html").read_text(encoding="utf-8"))
        c["interactive"] = True
        at.comparer(self.manifest([c]), self.d / "q.html")
        page = (self.d / "q.html").read_text(encoding="utf-8")
        self.assertIn("window.ok=1", page)
        self.assertIn("script-src 'unsafe-inline' 'unsafe-eval'", page)

    def test_the_mockup_s_csp_lands_in_its_real_head_not_in_a_comment(self):
        (self.d / "m").mkdir()
        (self.d / "m" / "a.html").write_text("<!-- <head> --><html><head><title>t</title></head><body>x</body></html>",
                                             encoding="utf-8")
        c = {"id": "a", "name": "a", "concept": "c", "typography": "t", "palette": ["#000"], "traits": ["t"],
             "kind": "html", "source": "a.html"}
        at.comparer(self.manifest([c]), self.d / "p.html")
        data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',
                                    (self.d / "p.html").read_text(encoding="utf-8"), re.S)[1])
        content = data["candidates"][0]["content"]
        self.assertLess(content.index("<head>", 10), content.index("Content-Security-Policy"))

    def test_metadata_cannot_close_the_data_script(self):
        c = self.html("a.html", "x")
        c["name"] = "</script><script>alert(1)</script>"
        at.comparer(self.manifest([c]), self.d / "p.html")
        page = (self.d / "p.html").read_text(encoding="utf-8")
        self.assertNotIn("</script><script>alert", page)

    def test_live_options_point_only_at_a_local_server(self):
        base = {"name": "n", "concept": "c", "typography": "t", "palette": ["#000"], "traits": ["t"], "kind": "url"}
        for url in ("http://example.com", "file:///etc/passwd", "http://user:pw@localhost:3000", "http://localhost:99999"):
            with self.assertRaises(at.Refus, msg=url):
                at.comparer(self.manifest([{**base, "id": "u", "url": url}]), self.d / "p.html", force=True)
        at.comparer(self.manifest([{**base, "id": "u", "url": "http://localhost:5173/x"}]), self.d / "p.html", force=True)
        self.assertIn("frame-src http://localhost:5173", (self.d / "p.html").read_text(encoding="utf-8"))

    def test_baseline_and_recommendation_rules(self):
        a, b = self.html("a.html", "a"), self.html("b.html", "b")
        with self.assertRaises(at.Refus):
            at.comparer(self.manifest([{**a, "baseline": True}, {**b, "baseline": True}]), self.d / "p.html")
        with self.assertRaises(at.Refus):  # nothing to choose but the current screen
            at.comparer(self.manifest([{**a, "baseline": True}]), self.d / "p.html")
        with self.assertRaises(at.Refus):  # the current screen is never recommended
            at.comparer(self.manifest([{**a, "baseline": True}, b], recommande="a"), self.d / "p.html")
        r = at.comparer(self.manifest([b, {**a, "baseline": True}], recommande="b"), self.d / "p.html")
        self.assertEqual(r["lettres"], {"a": "actuel", "b": "a"})

    def test_a_refused_build_keeps_the_previous_page_even_with_force(self):
        at.comparer(self.manifest([self.html("a.html", "a")]), self.d / "p.html")
        before = (self.d / "p.html").read_text(encoding="utf-8")
        with self.assertRaises(at.Refus):
            at.comparer(self.manifest([self.html("a.html", '<img src="http://x">')]), self.d / "p.html", force=True)
        self.assertEqual((self.d / "p.html").read_text(encoding="utf-8"), before)
        with self.assertRaises(at.Refus):  # the output never overwrites an input
            at.comparer(self.manifest([self.html("a.html", "a")]), self.d / "m" / "a.html", force=True)

    def test_the_page_keeps_its_promised_features(self):
        page = at.TEMPLATE.read_text(encoding="utf-8")
        for hook in ('data-layout="single"', 'data-viewport="mobile"', "Taille réelle (100 %)", "Recommandée",
                     "navigator.clipboard", "DATA.question", 'c.kind === "url"', "Le serveur local ne répond pas",
                     "data-copy-serve", "c.baseline", "c.interactive", "DATA.empreinte", "c.controles", "ArrowRight",
                     "prefers-color-scheme:dark", 'id="note"'):
            self.assertIn(hook, page, hook)


class Choix(Base):
    def kb(self) -> Path:
        k = self.d / "proj" / ".hosa" / "kb"
        (k / "interface").mkdir(parents=True)
        return k

    def test_each_round_s_choice_is_written_to_the_kb_with_the_style_s_tokens(self):
        k = self.kb()
        cfg = self.cfg()
        r = at.choisir(k, "styles", "kiln", cfg, "Fabien", None, False)
        self.assertEqual((r["option"], r["jetons"]), ("kiln", len(at.jetons(json.loads(cfg.read_text("utf-8"))["cards"][2]))))
        at.choisir(k, "directions", "kiln", cfg, "Fabien", "la typo de b", False)
        at.choisir(k, "styles", "glaze", cfg, "Fabien", None, False)  # a round played again: its last line wins
        etat = at.lit_choix(k)
        self.assertEqual(etat["manches"]["styles"][0], "glaze")
        self.assertEqual(etat["manches"]["directions"][2], "la typo de b")
        self.assertEqual(etat["jetons"]["--color-bg"], "#EFE7DA")
        text = (k / "interface" / "choix.md").read_text(encoding="utf-8")
        self.assertIn("type: Choix de design", text)
        self.assertIn("generated: { by: human:Fabien", text)
        log = (k / "interface" / "log.md").read_text(encoding="utf-8")
        self.assertEqual(log.count("\n## "), 1)
        self.assertEqual(log.count("human:Fabien a noté la manche"), 3)
        if OKF.is_file():
            import subprocess
            out = subprocess.run([sys.executable, str(OKF), str(k)], capture_output=True, text=True, encoding="utf-8")
            self.assertNotIn("choix.md", "\n".join(l for l in out.stdout.splitlines() if "error" in l.lower()))

    def test_unknown_or_current_options_and_a_kept_identity(self):
        k = self.kb()
        with self.assertRaises(at.Refus):
            at.choisir(k, "styles", "nope", self.cfg(), "u", None, False)
        with self.assertRaises(at.Refus):
            at.choisir(k, "couleurs", "kiln", self.cfg(), "u", None, False)
        m = self.manifest([{**self.html("a.html", "a"), "baseline": True}, self.html("b.html", "b")])
        with self.assertRaises(at.Refus):
            at.choisir(k, "page", "a", m, "u", None, False)
        with self.assertRaises(at.Refus):  # styles needs the cards file: it carries the tokens
            at.choisir(k, "styles", "b", m, "u", None, False)
        at.choisir(k, "page", "b", m, "u", None, False)
        with self.assertRaises(at.Refus):  # keeping what exists names no option
            at.choisir(k, "directions", "b", None, "u", None, True)
        at.choisir(k, "directions", None, None, "u", "navigation actuelle", True)
        self.assertEqual(at.lit_choix(k)["manches"]["directions"][0], "conservée")
        at.choisir(k, "styles", None, None, "u", "charte existante", True)
        etat = at.lit_choix(k)
        self.assertEqual((etat["manches"]["styles"][0], etat["jetons"]), ("conservée", {}))
        self.assertEqual(at.ecarts(k), [])  # a kept identity has no tokens to check

    def test_css_writes_the_tokens_once_and_the_check_catches_a_hand_edit(self):
        k = self.kb()
        at.choisir(k, "styles", "glaze", self.cfg(), "u", None, False)
        self.assertIn("non appliqués", at.ecarts(k)[0])
        css = self.d / "proj" / "src" / "styles.css"
        css.parent.mkdir(parents=True)
        css.write_text("body{margin:0}\n", encoding="utf-8")
        at.css(k, css)
        at.css(k, css)  # idempotent: one block, the rest of the file kept
        text = css.read_text(encoding="utf-8")
        self.assertEqual(text.count(at.DEBUT), 1)
        self.assertIn("body{margin:0}", text)
        self.assertIn("--color-bg: #EFE7DA;", text)
        self.assertEqual(at.lit_choix(k)["css"], "src/styles.css")
        self.assertEqual(at.lit_choix(k)["par"], "human:u")  # the choice stays the user's
        self.assertEqual(at.ecarts(k), [])
        css.write_text(text.replace("#EFE7DA", "#FFFFFF"), encoding="utf-8")
        self.assertIn("édités à la main", at.ecarts(k)[0])
        with self.assertRaises(at.Refus):  # outside the project
            at.css(k, self.d / "ailleurs.css")

    def test_interface_check_reports_the_drift_in_a_real_kb(self):
        spec = importlib.util.spec_from_file_location("interface_check", SCRIPTS / "interface_check.py")
        ic = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ic)
        k = self.kb()
        (k / "interface" / "navigation.md").write_text("---\ntype: Plan de navigation\n---\n## Écrans\n", encoding="utf-8")
        at.choisir(k, "styles", "glaze", self.cfg(), "u", None, False)
        self.assertTrue(any("non appliqués" in g for g in ic.gaps(k)))


class Cli(Base):
    def test_exit_codes_and_one_json_line(self):
        import io
        from contextlib import redirect_stderr, redirect_stdout
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(at.main(["cartes", str(self.cfg()), "--out", str(self.d / "o")]), 0)
            self.assertEqual(at.main(["cartes", str(self.cfg()), "--out", str(self.d / "o")]), 1)
        self.assertIn('"cartes": 4', out.getvalue())
        self.assertIn("--force", err.getvalue())


if __name__ == "__main__":
    unittest.main()
