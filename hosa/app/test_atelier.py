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
        m = {"version": 2, "projet": "P", "intention": "B", "manche": "directions", "options": cands, **extra}
        p = self.d / "m" / "manifest.json"
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
        return p

    def html(self, name: str, body: str, head: str = "") -> dict:
        (self.d / "m").mkdir(exist_ok=True)
        (self.d / "m" / name).write_text(PAGE.replace("<title>x</title>", "<title>x</title>" + head).replace("{}", body),
                                         encoding="utf-8")
        return {"id": Path(name).stem, "nom": name, "intention": "c", "typographie": "t", "palette": ["#000000"],
                "traits": ["t"], "genre": "html", "fichier": name}


class Contraste(unittest.TestCase):
    def test_wcag_ratios_match_the_reference_values(self):
        self.assertAlmostEqual(at.contraste("#000000", "#FFFFFF"), 21.0, places=2)
        self.assertAlmostEqual(at.contraste("#767676", "#FFFFFF"), 4.54, places=2)  # the classic AA limit grey
        self.assertEqual(at.mix("#000000", "#ffffff", 0.5), "#808080")

    def test_every_pair_the_card_shows_is_checked_with_its_own_minimum(self):
        col = dict(fond="#ffffff", surface="#ffffff", texte="#000000", secondaire="#000000", accent="#000000",
                   sur_accent="#ffffff", trait="#eeeeee", alerte="#000000")
        self.assertEqual(at.controles(col)[1], [])
        col["accent"] = "#bbbbbb"  # light accent: white label unreadable, and a button under 3:1 on the page
        gaps = at.controles(col)[1]
        self.assertTrue(any(g.startswith("texte sur accent") and "il faut 4.5:1" in g for g in gaps), gaps)
        self.assertTrue(any(g.startswith("accent sur fond") and "il faut 3:1" in g for g in gaps), gaps)


class Cartes(Base):
    def test_the_example_builds_cards_a_manifest_and_one_offline_page(self):
        r = at.cartes(self.cfg(), self.d / "out", False)
        out = self.d / "out"
        self.assertEqual(r["cartes"], 4)
        self.assertEqual(sorted(p.name for p in out.iterdir()),
                         ["carte-email.html", "carte-four.html", "carte-galerie.html", "carte-journal.html",
                          "comparaison.html", "manifest.json"])
        page = (out / "comparaison.html").read_text(encoding="utf-8")
        self.assertNotIn("__ATELIER_DONNEES__", page)
        self.assertNotRegex(page, r"""(?:src|href)=["']https?://""")
        self.assertLess(len(page.encode()), 150_000)  # no font, no framework: it opens offline at once
        m = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(all(o["controles"] for o in m["options"]))

    def test_the_recommended_card_is_option_a_as_in_the_question(self):
        at.cartes(self.cfg(recommande="four"), self.d / "out", False)
        self.assertIn("A · Cours du soir", (self.d / "out" / "carte-four.html").read_text(encoding="utf-8"))
        r = at.comparer(self.d / "out" / "manifest.json", self.d / "p.html")
        self.assertEqual(r["lettres"]["four"], "a")

    def test_a_card_under_wcag_aa_is_refused_with_its_exact_pairs_and_nothing_written(self):
        data = json.loads(EXEMPLE.read_text(encoding="utf-8"))
        data["cartes"][0]["couleurs"]["secondaire"] = "#B0A89F"
        p = self.d / "c.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(at.Refus) as e:
            at.cartes(p, self.d / "out", False)
        msg = str(e.exception)
        self.assertIn("carte email — texte secondaire sur fond : #B0A89F sur #EFE7DA", msg)
        self.assertIn("il faut 4.5:1", msg)
        proposee = re.search(r"texte secondaire sur fond : .*?proposition : (#[0-9A-F]{6})", msg)[1]
        self.assertGreaterEqual(at.contraste(proposee, "#EFE7DA"), 4.5)  # the proposed colour passes
        self.assertLess(at.contraste(proposee, "#B0A89F"), 2.5)  # and stays close to the chosen one
        self.assertFalse((self.d / "out").exists())

    def test_bad_configurations_are_refused_before_writing(self):
        data = json.loads(EXEMPLE.read_text(encoding="utf-8"))
        cases = {
            "cartes : 2 à 6": lambda d: d.update(cartes=d["cartes"][:1]),
            "hexadécimale": lambda d: d["cartes"][0]["couleurs"].update(fond="red"),
            "pas de police réseau": lambda d: d["cartes"][0]["polices"].update(texte="url(http://x)"),
            "même contenu": lambda d: d["cartes"][0].update(contenu={}),
            "id invalide ou en double": lambda d: d["cartes"][1].update(id=d["cartes"][0]["id"]),
            "ecran doit valoir": lambda d: d["cartes"][0].update(ecran="carrousel"),
            "arrondi": lambda d: d["cartes"][0].update(arrondi=99),
            "lignes": lambda d: d["contenu"]["ecran"]["lignes"].append(["trop court"]),
            "ancien format": lambda d: d.update(version=None, cards=[]),
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

    def test_a_dashboard_card_shows_real_indicators_and_their_trend(self):
        at.cartes(self.cfg(), self.d / "out", False)
        carte = (self.d / "out" / "carte-galerie.html").read_text(encoding="utf-8")
        self.assertIn("Places vendues cette semaine", carte)
        self.assertIn("<b>38 / 48</b>", carte)
        self.assertEqual(carte.count("<polyline"), 3)
        self.assertIn("À traiter", carte)
        data = json.loads(EXEMPLE.read_text(encoding="utf-8"))
        del data["contenu"]["indicateurs"]
        p = self.d / "c.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(at.Refus) as e:
            at.cartes(p, self.d / "o2", False)
        self.assertIn("contenu.indicateurs", str(e.exception))
        self.assertEqual(at.courbe([5]), "")

    def test_content_is_escaped_and_the_real_screen_is_drawn(self):
        data = json.loads(EXEMPLE.read_text(encoding="utf-8"))
        data["contenu"]["titre"] = "<script>alert(1)</script>"
        p = self.d / "c.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        at.cartes(p, self.d / "out", False)
        carte = (self.d / "out" / "carte-galerie.html").read_text(encoding="utf-8")
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
        c["interactif"] = True
        at.comparer(self.manifest([c]), self.d / "q.html")
        page = (self.d / "q.html").read_text(encoding="utf-8")
        self.assertIn("window.ok=1", page)
        self.assertIn("script-src 'unsafe-inline' 'unsafe-eval'", page)

    def test_the_mockup_s_csp_lands_in_its_real_head_not_in_a_comment(self):
        (self.d / "m").mkdir()
        (self.d / "m" / "a.html").write_text("<!-- <head> --><html><head><title>t</title></head><body>x</body></html>",
                                             encoding="utf-8")
        c = {"id": "a", "nom": "a", "intention": "c", "typographie": "t", "palette": ["#000"], "traits": ["t"],
             "genre": "html", "fichier": "a.html"}
        at.comparer(self.manifest([c]), self.d / "p.html")
        data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',
                                    (self.d / "p.html").read_text(encoding="utf-8"), re.S)[1])
        content = data["options"][0]["contenu"]
        self.assertNotIn("<!--", content)  # the comment is dropped: only the real head remains
        self.assertLess(content.index("<head>"), content.index("Content-Security-Policy"))

    def test_metadata_cannot_close_the_data_script(self):
        c = self.html("a.html", "x")
        c["nom"] = "</script><script>alert(1)</script>"
        at.comparer(self.manifest([c]), self.d / "p.html")
        page = (self.d / "p.html").read_text(encoding="utf-8")
        self.assertNotIn("</script><script>alert", page)

    def test_live_options_point_only_at_a_local_server(self):
        base = {"nom": "n", "intention": "c", "typographie": "t", "palette": ["#000"], "traits": ["t"], "genre": "adresse"}
        for url in ("http://example.com", "file:///etc/passwd", "http://user:pw@localhost:3000", "http://localhost:99999"):
            with self.assertRaises(at.Refus, msg=url):
                at.comparer(self.manifest([{**base, "id": "u", "adresse": url}]), self.d / "p.html", force=True)
        at.comparer(self.manifest([{**base, "id": "u", "adresse": "http://localhost:5173/x"}]), self.d / "p.html", force=True)
        self.assertIn("frame-src http://localhost:5173", (self.d / "p.html").read_text(encoding="utf-8"))

    def test_baseline_and_recommendation_rules(self):
        a, b = self.html("a.html", "a"), self.html("b.html", "b")
        with self.assertRaises(at.Refus):
            at.comparer(self.manifest([{**a, "actuel": True}, {**b, "actuel": True}]), self.d / "p.html")
        with self.assertRaises(at.Refus):  # nothing to choose but the current screen
            at.comparer(self.manifest([{**a, "actuel": True}]), self.d / "p.html")
        with self.assertRaises(at.Refus):  # the current screen is never recommended
            at.comparer(self.manifest([{**a, "actuel": True}, b], recommande="a"), self.d / "p.html")
        r = at.comparer(self.manifest([b, {**a, "actuel": True}], recommande="b"), self.d / "p.html")
        self.assertEqual(r["lettres"], {"a": "actuel", "b": "a"})

    def test_a_refused_build_keeps_the_previous_page_even_with_force(self):
        at.comparer(self.manifest([self.html("a.html", "a")]), self.d / "p.html")
        before = (self.d / "p.html").read_text(encoding="utf-8")
        with self.assertRaises(at.Refus):
            at.comparer(self.manifest([self.html("a.html", '<img src="http://x">')]), self.d / "p.html", force=True)
        self.assertEqual((self.d / "p.html").read_text(encoding="utf-8"), before)
        with self.assertRaises(at.Refus):  # the output never overwrites an input
            at.comparer(self.manifest([self.html("a.html", "a")]), self.d / "m" / "a.html", force=True)

    def test_markup_the_browser_and_the_check_would_read_differently_is_refused_or_dropped(self):
        for body in ('<svg><style><img src="http://x/a.png"></style></svg>',
                     '<math><script>x</script></math>',
                     '<xmp><a title="</xmp><img src=http://x>">x</a></xmp>',
                     '<noscript><a title="</noscript><img src=http://x>">x</a></noscript>',
                     '<!-- a --!><img src="http://x/a.png"> -->'):  # the comment ends at --!>, as in the browser
            with self.assertRaises(at.Refus, msg=body):
                at.comparer(self.manifest([self.html("a.html", body)]), self.d / "p.html", force=True)
        c = self.html("a.html", '<!-- <img src="http://x/a.png"> --><p>ok</p><![CDATA[<img src=http://y>]]>'
                                '<svg><title>Logo</title></svg><textarea>texte</textarea>')
        at.comparer(self.manifest([c]), self.d / "p.html", force=True)
        data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',
                                    (self.d / "p.html").read_text(encoding="utf-8"), re.S)[1])
        contenu = data["options"][0]["contenu"]
        self.assertNotIn("<!--", contenu)
        self.assertNotIn("http://", contenu)
        self.assertIn("<p>ok</p>", contenu)

    def test_a_refusal_names_the_file_and_line(self):
        c = self.html("a.html", '<p>ok</p>\n<p>ok</p>\n<img alt="" src="https://cdn/x.png">')
        with self.assertRaises(at.Refus) as e:
            at.comparer(self.manifest([c]), self.d / "p.html")
        self.assertIn("a.html, ligne 3", str(e.exception))
        self.assertIn("https://cdn/x.png", str(e.exception))

    def test_srcset_candidates_are_embedded_one_by_one(self):
        (self.d / "m").mkdir()
        (self.d / "m" / "a1.png").write_bytes(b"\x89PNG\r\n\x1a\n1")
        (self.d / "m" / "a2.png").write_bytes(b"\x89PNG\r\n\x1a\n2")
        c = self.html("a.html", '<img alt="" src="a1.png" srcset="a1.png 1x, a2.png 2x, data:image/png;base64,AA== 3x">')
        at.comparer(self.manifest([c]), self.d / "p.html")
        data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',
                                    (self.d / "p.html").read_text(encoding="utf-8"), re.S)[1])
        srcset = re.search(r'srcset="([^"]+)"', data["options"][0]["contenu"])[1]
        self.assertEqual(srcset.count("data:image/png;base64,"), 3)
        self.assertNotIn("a2.png", srcset)
        c = self.html("b.html", '<img alt="" srcset="a1.png 1x, https://cdn/a2.png 2x">')
        with self.assertRaises(at.Refus):
            at.comparer(self.manifest([c]), self.d / "q.html")

    def test_a_static_mockup_carries_no_script_and_a_headless_one_gets_its_csp_first(self):
        c = self.html("a.html", '<button onclick="go()">Go</button><script>window.ko=1</script>')
        at.comparer(self.manifest([c]), self.d / "p.html")
        data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',
                                    (self.d / "p.html").read_text(encoding="utf-8"), re.S)[1])
        self.assertNotIn("window.ko=1", data["options"][0]["contenu"])
        self.assertNotIn("onclick", data["options"][0]["contenu"])
        self.assertIn("<button>Go</button>", data["options"][0]["contenu"])
        (self.d / "m" / "b.html").write_text("<p>Sans en-tête</p>", encoding="utf-8")
        c = {**self.html("a.html", "a"), "id": "b", "fichier": "b.html"}
        at.comparer(self.manifest([c]), self.d / "q.html")
        data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',
                                    (self.d / "q.html").read_text(encoding="utf-8"), re.S)[1])
        contenu = data["options"][0]["contenu"]
        self.assertLess(contenu.index("Content-Security-Policy"), contenu.index("<p>"))

    @unittest.skipUnless(__import__("shutil").which("node"), "Node requis")
    def test_the_storage_stand_in_answers_like_the_real_one(self):
        import subprocess
        shim = re.search(r"<script>(.*)</script>", at.STOCKAGE, re.S)[1]
        js = ("const window = globalThis; Object.defineProperty(globalThis, 'localStorage', {configurable: true, "
              "get() { throw new Error('bac à sable'); }});" + shim +
              "localStorage.jeton = 1; localStorage.setItem('b', 2);"
              "console.log([localStorage.getItem('jeton'), localStorage.b, localStorage.length, 'b' in localStorage,"
              "Object.keys(localStorage).join('+'), (delete localStorage.b, localStorage.getItem('b'))].join('|'))")
        out = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=30)
        self.assertEqual(out.stdout.strip(), "1|2|2|true|jeton+b|", out.stderr)

    def test_the_page_keeps_its_promised_features(self):
        page = at.TEMPLATE.read_text(encoding="utf-8")
        for hook in ('data-layout="single"', 'data-viewport="mobile"', "Taille réelle (100 %)", "Recommandée",
                     "navigator.clipboard", "DATA.question", 'c.genre === "adresse"', "Le serveur local ne répond pas",
                     "data-copy-serve", "c.actuel", "c.interactif", "DATA.empreinte", "c.controles", "ArrowRight",
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
        r = at.choisir(k, "styles", "four", cfg, "Fabien", None, False)
        self.assertEqual((r["option"], r["jetons"]), ("four", len(at.jetons(at.charge_cartes(cfg)["cartes"][2]))))
        at.choisir(k, "directions", "four", cfg, "Fabien", "la typo de b", False)
        at.choisir(k, "styles", "email", cfg, "Fabien", None, False)  # a round played again: its last line wins
        etat = at.lit_choix(k)
        self.assertEqual(etat["manches"]["styles"][0], "email")
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
            at.choisir(k, "couleurs", "four", self.cfg(), "u", None, False)
        m = self.manifest([{**self.html("a.html", "a"), "actuel": True}, self.html("b.html", "b")])
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
        at.choisir(k, "styles", "email", self.cfg(), "u", None, False)
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

    NUIT = {"fond": "#1E1B18", "surface": "#2A2622", "texte": "#F2EBE3", "secondaire": "#BFB4A8",
            "accent": "#7FB3AB", "sur_accent": "#10201E", "trait": "#3E3832", "alerte": "#E8A37C"}
    JOUR = {"fond": "#F6F1EA", "surface": "#FFFFFF", "texte": "#2A2522", "secondaire": "#5E554E",
            "accent": "#9A4A16", "sur_accent": "#FFFFFF", "trait": "#E3DACF", "alerte": "#8A5A00"}

    def test_a_dark_card_s_light_variant_goes_the_other_way(self):
        data = json.loads(EXEMPLE.read_text(encoding="utf-8"))
        data["cartes"][2]["variante"] = self.JOUR  # `four`, a dark card with relief contour
        cfg = self.d / "jour.json"
        cfg.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        k = self.kb()
        self.assertEqual(at.choisir(k, "styles", "four", cfg, "u", None, False)["mode"], "clair")
        self.assertIn("## Jetons du mode clair", (k / "interface" / "choix.md").read_text(encoding="utf-8"))
        css = self.d / "proj" / "src" / "styles.css"
        at.css(k, css)
        text = css.read_text(encoding="utf-8")
        for want in ("color-scheme: dark;", "@media (prefers-color-scheme: light) {", ':root:not([data-theme="dark"]) {',
                     ':root[data-theme="light"] {', "  --border: 2px solid #2A2522;"):
            self.assertIn(want, text)
        self.assertEqual(at.ecarts(k), [])

    def avec_nuit(self, **change) -> Path:
        data = json.loads(EXEMPLE.read_text(encoding="utf-8"))
        data["cartes"][0]["variante"] = {**self.NUIT, **change}  # `email`, a light card with relief ombre
        p = self.d / "nuit.json"
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return p

    def test_a_card_without_a_variant_keeps_its_css_block_to_the_character(self):
        import hashlib  # pinned before the modes: a project's CSS must not look "edited by hand" after an upgrade
        avant = {"email": "b9098d0f0f0685db082bf1533a7c4bd2357ab34abeaa165586a52bc24878faf0",
                 "galerie": "f253eca07c79b3df870461327f1713988f7b0db6e7c864a2a21552df2d05cdf8",
                 "four": "63f59c7c59545d6a2e1cdea2fef07f522ecb9f845b0f44e22c27964fe895c73b",
                 "journal": "6f0c5f725c59db60c68a571fddf20ef8a56e7918a775988ccea3bb1dc82f9fb6"}
        for c in at.charge_cartes(EXEMPLE)["cartes"]:
            self.assertEqual(hashlib.sha256(at.bloc_css(at.jetons(c)).encode()).hexdigest(), avant[c["id"]], c["id"])

    def test_a_variant_is_the_other_mode_and_holds_the_same_contrasts(self):
        with self.assertRaises(at.Refus) as e:
            at.charge_cartes(self.avec_nuit(fond="#FAFAFA"))
        self.assertIn("le mode opposé à la carte (sombre)", str(e.exception))
        with self.assertRaises(at.Refus) as e:
            at.charge_cartes(self.avec_nuit(secondaire="#4A4540"))
        self.assertIn("carte email — mode sombre — texte secondaire sur fond", str(e.exception))
        carte = at.charge_cartes(self.avec_nuit())["cartes"][0]
        self.assertEqual(at.jetons_variante(carte)["--border"], "1px solid #3E3832")  # no shadow seen on dark: a line
        with self.assertRaises(at.Refus) as e:  # the mode asked for is not lost with the card chosen
            at.cartes(self.avec_nuit(), self.d / "o", False)
        self.assertIn("`variante` dans email, pas dans galerie, four, journal", str(e.exception))
        data = json.loads(self.avec_nuit().read_text(encoding="utf-8"))
        for c in data["cartes"][1:]:
            c["variante"] = self.NUIT if at.mode(c["couleurs"]) == "clair" else self.JOUR
        (self.d / "nuit.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        r = at.cartes(self.d / "nuit.json", self.d / "o", False)
        page = (self.d / "o" / "carte-email.html").read_text(encoding="utf-8")
        self.assertIn("Mode sombre · premier écran", page)
        m = json.loads(Path(r["manifest"]).read_text(encoding="utf-8"))
        self.assertTrue(any(x.startswith("mode sombre : ") for x in m["options"][0]["controles"]))

    def test_the_variant_survives_every_rewrite_and_its_css_is_checked(self):
        k = self.kb()
        r = at.choisir(k, "styles", "email", self.avec_nuit(), "u", None, False)
        self.assertEqual(r["mode"], "sombre")
        at.choisir(k, "directions", "four", self.cfg(), "u", None, False)  # rewrites choix.md
        css = self.d / "proj" / "src" / "styles.css"
        at.css(k, css)  # rewrites it again, with the CSS path
        etat = at.lit_choix(k)
        self.assertEqual((etat["variante"]["mode"], etat["variante"]["jetons"]["--color-bg"]), ("sombre", "#1E1B18"))
        text = css.read_text(encoding="utf-8")
        for want in ("color-scheme: light;", "@media (prefers-color-scheme: dark) {",
                     ':root:not([data-theme="light"]) {', ':root[data-theme="dark"] {', "    --color-bg: #1E1B18;"):
            self.assertIn(want, text)
        self.assertEqual(at.ecarts(k), [])
        css.write_text(text.replace("#1E1B18", "#000000"), encoding="utf-8")
        self.assertIn("édités à la main", at.ecarts(k)[0])
        if OKF.is_file():
            import subprocess
            out = subprocess.run([sys.executable, str(OKF), str(k)], capture_output=True, text=True, encoding="utf-8")
            self.assertNotIn("choix.md", "\n".join(l for l in out.stdout.splitlines() if "error" in l.lower()))
        at.choisir(k, "styles", None, None, "u", "charte existante", True)
        self.assertNotIn("## Jetons du mode", (k / "interface" / "choix.md").read_text(encoding="utf-8"))
        self.assertIsNone(at.lit_choix(k)["variante"])

    def test_dtcg_export_reads_every_relief_and_refuses_an_unknown_form(self):
        data = json.loads(EXEMPLE.read_text(encoding="utf-8"))
        data["cartes"][1]["relief"] = "aucun"  # galerie: the four reliefs are ombre, aucun, contour, trait
        data["cartes"][0]["variante"] = self.NUIT
        cfg = self.d / "reliefs.json"
        cfg.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        attendu = {"email": (1, "transparent"), "galerie": (0, "transparent"), "four": (2, None), "journal": (1, None)}
        for carte, (largeur, couleur) in attendu.items():
            k = self.d / carte / ".hosa" / "kb"
            (k / "interface").mkdir(parents=True)
            at.choisir(k, "styles", carte, cfg, "u", None, False)
            r = at.dtcg(k, self.d / carte / "jetons")
            t = json.loads(Path(r["dtcg"][0]).read_text(encoding="utf-8"))
            self.assertEqual(t["color"]["bg"]["$type"], "color")
            self.assertEqual(set(t["color"]["bg"]["$value"]), {"colorSpace", "components", "hex"})
            self.assertTrue(all(0 <= x <= 1 for x in t["color"]["bg"]["$value"]["components"]))
            b = t["border"]["default"]["$value"]
            self.assertEqual((b["width"], b["style"]), ({"value": largeur, "unit": "px"}, "solid"))
            if couleur:
                self.assertEqual(b["color"]["alpha"], 0)
            self.assertIsInstance(t["font"]["family"]["body"]["$value"], list)
            self.assertIsInstance(t["font"]["weight"]["display"]["$value"], int)
            self.assertEqual(t["radius"]["$type"], "dimension")
            if carte == "email":
                self.assertEqual([s["color"]["alpha"] for s in t["shadow"]["$value"]], [0.06, 0.08])
                nuit = json.loads(Path(r["dtcg"][1]).read_text(encoding="utf-8"))
                self.assertTrue(r["dtcg"][1].endswith("identite.sombre.tokens.json"))
                self.assertEqual(nuit["color"]["bg"]["$value"]["hex"], "#1e1b18")
                self.assertNotIn("font", nuit)  # only what changes
            else:
                self.assertNotIn("shadow", t)  # no shadow: DTCG has no "none"
                self.assertEqual(len(r["dtcg"]), 1)
        f = self.d / "email" / ".hosa" / "kb" / "interface" / "choix.md"
        f.write_text(f.read_text(encoding="utf-8").replace("`--radius` | `14px`", "`--radius` | `calc(1rem + 2px)`"),
                     encoding="utf-8")
        with self.assertRaises(at.Refus) as e:
            at.dtcg(f.parents[1], self.d / "x")
        self.assertIn("`--radius` : la valeur `calc(1rem + 2px)`", str(e.exception))

    def test_interface_check_reports_the_drift_in_a_real_kb(self):
        spec = importlib.util.spec_from_file_location("interface_check", SCRIPTS / "interface_check.py")
        ic = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ic)
        k = self.kb()
        (k / "interface" / "navigation.md").write_text("---\ntype: Plan de navigation\n---\n## Écrans\n", encoding="utf-8")
        at.choisir(k, "styles", "email", self.cfg(), "u", None, False)
        self.assertTrue(any("non appliqués" in g for g in ic.gaps(k)))


class Diversite(Base):
    def jumelles(self) -> Path:
        data = json.loads(EXEMPLE.read_text(encoding="utf-8"))
        jumelle = copy.deepcopy(data["cartes"][0])
        jumelle.update(id="jumelle", nom="Jumelle", ecran="tuiles")  # another screen is content, not style
        jumelle["couleurs"]["fond"] = "#F2EADD"
        return self.cfg(cartes=data["cartes"][:3] + [jumelle])

    def test_cards_that_differ_by_a_shade_are_refused_with_their_axes(self):
        with self.assertRaises(at.Refus) as e:
            at.cartes(self.jumelles(), self.d / "o", False)
        self.assertIn("email et jumelle : 0 axe(s) différent(s)", str(e.exception))
        self.assertFalse((self.d / "o" / "comparaison.html").exists())
        self.assertEqual(at.cartes_proches(at.charge_cartes(self.cfg())["cartes"]), [])  # the example passes

    def test_default_choices_of_a_generated_interface_are_refused_unless_assumed(self):
        data = json.loads(EXEMPLE.read_text(encoding="utf-8"))
        data["cartes"][0]["polices"]["titres"] = "Inter, system-ui, sans-serif"
        data["cartes"][3]["couleurs"]["accent"] = "#6D28D9"  # violet-700, readable on its paper
        with self.assertRaises(at.Refus) as e:
            at.cartes(self.cfg(cartes=data["cartes"]), self.d / "o", False)
        msg = str(e.exception)
        self.assertIn("carte email — polices.titres : Inter", msg)
        self.assertIn("carte journal — couleurs.accent : #6D28D9", msg)
        self.assertFalse((self.d / "o" / "comparaison.html").exists())
        data["cartes"][0]["assume"] = ""
        with self.assertRaises(at.Refus):  # an empty reason is no reason
            at.charge_cartes(self.cfg(cartes=data["cartes"]))
        for i in (0, 3):
            data["cartes"][i]["assume"] = "la charte de la marque impose cette police et ce violet"
        self.assertEqual(len(at.charge_cartes(self.cfg(cartes=data["cartes"]))["cartes"]), 4)
        self.assertEqual([at.cliches(c) for c in at.charge_cartes(self.cfg())["cartes"]], [[]] * 4)  # the example
        self.assertEqual(at.cliches({"polices": {"titres": "Georgia, serif"}, "couleurs": {"accent": "#2563EB"}}), [])

    def test_a_refinement_round_and_the_user_s_choice_are_not_refused(self):
        p = self.jumelles()
        k = self.d / ".hosa" / "kb"
        (k / "interface").mkdir(parents=True)
        self.assertEqual(at.choisir(k, "styles", "jumelle", p, "Fabien", None, False)["option"], "jumelle")
        data = json.loads(p.read_text(encoding="utf-8"))
        data["affinage"] = "a avec le fond de d"
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(at.cartes(p, self.d / "o", False)["affinage"], "a avec le fond de d")  # the skill sees it


class Revue(Base):
    NAV = "---\ntype: Plan de navigation\ntitle: N\ndescription: d\ntags: [ux]\n---\n## Écrans\n- a\n\n## Fondamentaux UX\n- x\n"
    SHOT = ".hosa/design/shots/routes-admin/accueil-1280x900.png"

    def kb(self) -> Path:
        k = self.d / ".hosa" / "kb"
        (k / "interface").mkdir(parents=True)
        (k / "interface" / "navigation.md").write_text(self.NAV, encoding="utf-8")
        (self.d / self.SHOT).parent.mkdir(parents=True)
        (self.d / self.SHOT).write_bytes(b"png")
        return k

    def remplie(self, **change) -> Path:
        g = {"version": 2, "questions": [{"id": q["id"], "reponse": "oui", "preuve": self.SHOT}
                                         for q in at.questions_grille()]}
        for qid, rep in change.items():
            next(r for r in g["questions"] if r["id"] == qid).update(rep)
        p = self.d / f"grille-{len(list(self.d.glob('grille-*')))}.json"
        p.write_text(json.dumps(g, ensure_ascii=False), encoding="utf-8")
        return p

    def test_an_identity_with_two_modes_is_reviewed_on_captures_of_both(self):
        k = self.kb()
        sans = at.revue(k, self.remplie())  # one mode: a single capture is enough
        self.assertEqual(sans["note"], 10)
        data = json.loads(EXEMPLE.read_text(encoding="utf-8"))
        data["cartes"][0]["variante"] = Choix.NUIT
        cfg = self.d / "nuit.json"
        cfg.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        at.choisir(k, "styles", "email", cfg, "u", None, False)
        clair, sombre = self.SHOT.replace(".png", "-light.png"), self.SHOT.replace(".png", "-dark-marque.png")
        for s in (clair, sombre):
            (self.d / s).write_bytes(b"png")
        with self.assertRaises(at.Refus) as e:
            at.revue(k, self.remplie(R3={"preuve": clair}))
        self.assertIn("aucune preuve capturée en mode sombre", str(e.exception))
        self.assertNotIn("mode clair", str(e.exception))
        with self.assertRaises(at.Refus) as e:  # a Non's capture proves nothing: only the Oui count
            at.revue(k, self.remplie(R3={"preuve": clair}, R4={"reponse": "non", "preuve": sombre, "ou": "a",
                                                                "constat": "b", "correction": "c"}))
        self.assertIn("mode sombre", str(e.exception))
        self.assertEqual(at.revue(k, self.remplie(R3={"preuve": clair}, R5={"preuve": f"{self.SHOT}, {sombre}"}))["note"], 10)

    def test_the_grid_comes_from_the_pipeline_and_its_template_is_written_once(self):
        qs = at.questions_grille()
        self.assertEqual((qs[0]["id"], at.plafond(qs[0]), at.plafond(qs[3])), ("R1", 7, 10))
        out = self.d / ".hosa" / "design" / "revue" / "grille-1.json"  # its folder does not exist yet
        self.assertEqual(at.grille(out)["questions"], len(qs))
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["questions"][1]["reponse"], "")
        with self.assertRaises(at.Refus):
            at.grille(out)

    def test_the_note_is_computed_and_a_capped_no_holds_it_at_7(self):
        k = self.kb()
        non = {"ou": "Accueil", "constat": "deux boutons principaux", "correction": "un seul"}
        r = at.revue(k, self.remplie(R4={"reponse": "non", **non}, R13={"reponse": "na", "constat": "pas de back office"}))
        self.assertEqual((r["note"], r["grille"]), (9, "14/15"))
        self.assertEqual(at.revue(k, self.remplie(R8={"reponse": "non", **non}))["note"], 7)  # a default template
        self.assertEqual(at.revue(k, self.remplie(R16={"reponse": "non", **non}))["note"], 7)  # default ornaments
        deux = {f"R{i}": {"reponse": "non", **non} for i in (6, 7)}
        self.assertEqual(at.revue(k, self.remplie(**deux))["note"], 8)  # 14/16
        self.assertEqual(at.revue(k, self.remplie(**deux, R10={"reponse": "non", **non}))["note"], 7)  # 13/16 = 8, a 3rd non
        r = at.revue(k, self.remplie(R1={"reponse": "non", **non}))
        self.assertEqual(r["note"], 7)
        nav = (k / "interface" / "navigation.md").read_text(encoding="utf-8")
        lignes = [l for l in nav.split("## Revue visuelle")[1].splitlines() if l.startswith("- ")]
        self.assertEqual(len(lignes), 6)  # appended, never rewritten
        self.assertRegex(lignes[5], r"— note 7/10 — grille 15/16 \(1 non, 1 bloquant\) — R1 Accueil : deux boutons")
        self.assertIn("## Fondamentaux UX", nav)
        sys.path.insert(0, str(ROOT / "skills" / "status" / "scripts"))
        import avancement as av
        m = av.REVIEW_LINE.match(lignes[4])
        self.assertEqual((m[1], bool(av.GRID_MARK.search(m[3]))), ("7", True))  # the control reads what it writes

    def test_an_unproven_or_incomplete_grid_writes_nothing(self):
        k = self.kb()
        (self.d / ".hosa" / "design" / "shots" / "notes.txt").write_text("x", encoding="utf-8")
        avant = (k / "interface" / "navigation.md").read_text(encoding="utf-8")
        for change, attendu in (({"R3": {"preuve": "absente.png"}}, "R3 : oui sans preuve"),
                                ({"R3": {"preuve": "accueil-1280x900.png"}}, "R3 : oui sans preuve"),  # a bare name
                                ({"R3": {"preuve": "*.png"}}, "R3 : oui sans preuve"),
                                ({"R3": {"preuve": ".hosa/design/shots"}}, "R3 : oui sans preuve"),
                                ({"R3": {"preuve": ".hosa/design/shots/notes.txt"}}, "R3 : oui sans preuve"),
                                ({"R3": {"preuve": "."}}, "R3 : oui sans preuve"),
                                ({"R5": {"reponse": "non", "ou": "Menu"}}, "R5 : non sans constat, correction"),
                                ({"R2": {"reponse": "na", "constat": "x"}}, "R2 : ne peut pas être non applicable"),
                                ({"R9": {"reponse": "na", "constat": "x"}}, "R9 : ne peut pas être non applicable"),
                                ({"R6": {"reponse": "peut-être"}}, "R6 : `reponse` vaut oui, non ou na"),
                                ({"R14": {"reponse": "na"}}, "R14 : non applicable sans raison")):
            with self.assertRaises(at.Refus) as e:
                at.revue(k, self.remplie(**change))
            self.assertIn(attendu, str(e.exception))
        self.assertEqual((k / "interface" / "navigation.md").read_text(encoding="utf-8"), avant)


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
