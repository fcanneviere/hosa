"""gabarit_check.py : les signes d'un gabarit par défaut et les manques que la loi sanctionne, lus dans le code."""
import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
import unittest.mock
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "interface" / "scripts" / "gabarit_check.py"
spec = importlib.util.spec_from_file_location("gabarit_check", SCRIPT)
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)


def signes(nom: str, texte: str) -> list[str]:
    """Les signes d'un seul fichier, sans le numéro de ligne."""
    return [s for _, s in gc.examine(Path(nom), texte)]


def un(nom: str, texte: str, debut: str) -> bool:
    return any(s.startswith(debut) for s in signes(nom, texte))


class Ornements(unittest.TestCase):
    def test_a_gradient_between_two_hues_but_not_a_shade_of_one_neutral(self):
        self.assertTrue(un("a.css", ".a { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) }", "dégradé"))
        self.assertTrue(un("a.html", '<div class="bg-gradient-to-r from-indigo-500 to-pink-500">x</div>', "dégradé"))
        self.assertFalse(un("a.css", ".a { background: linear-gradient(#2b2b2b, #1f1f1f) }", "dégradé"))
        self.assertFalse(un("a.css", ".a { background: linear-gradient(#3F6560, #355650) }", "dégradé"))  # one hue
        self.assertFalse(un("a.html", '<div class="bg-gradient-to-b from-zinc-800 to-zinc-900">x</div>', "dégradé"))

    def test_gradient_text_a_coloured_glow_and_a_coloured_side_bar(self):
        self.assertTrue(un("a.css", "h1 { -webkit-background-clip: text }", "texte en dégradé"))
        self.assertTrue(un("a.css", ".c { box-shadow: 0 0 20px rgba(139,92,246,.5) }", "halo"))
        self.assertTrue(un("a.html", '<b class="shadow-lg shadow-violet-500/50">x</b>', "halo"))
        self.assertFalse(un("a.css", ".c { box-shadow: 0 1px 2px rgba(0,0,0,.05) }", "halo"))
        self.assertTrue(un("a.css", ".n { border-left: 4px solid #2563eb }", "barre colorée"))
        self.assertTrue(un("a.html", '<div class="border-l-4 border-blue-500">x</div>', "barre colorée"))
        self.assertFalse(un("a.css", ".n { border-left: 1px solid #e5e5e5 }", "barre colorée"))

    def test_emoji_but_not_typographic_signs(self):
        self.assertTrue(un("a.html", "<li>🏠 Accueil</li>", "emoji 🏠"))
        self.assertTrue(un("fr.json", '{"nouveau": "Nouveau ✨"}', "emoji ✨"))
        self.assertFalse(un("a.html", "<li>✓ Payée</li><li>→ Suite</li>", "emoji"))

    def test_spaced_capitals_heavy_weights_and_the_4px_grid(self):
        self.assertTrue(un("a.html", '<h2 class="uppercase tracking-widest">x</h2>', "capitales espacées"))
        self.assertFalse(un("a.html", '<abbr class="uppercase">tva</abbr>', "capitales espacées"))
        self.assertTrue(un("a.css", "h1 { font-weight: 900 }", "graisse"))
        self.assertTrue(un("a.html", '<h1 class="font-extrabold">x</h1>', "graisse"))
        self.assertFalse(un("a.css", "h1 { font-weight: 600 }", "graisse"))
        self.assertEqual(signes("a.css", ".a { padding: 13px 16px; margin: 7px }"),
                         ["espacement hors de la grille de 4 px (7px, 13px) → un nombre pair jusqu'à 16 px, "
                          "puis un multiple de 4 : 20, 24, 32…"])
        self.assertTrue(un("a.html", '<div class="p-[13px]">x</div>', "espacement"))
        self.assertTrue(un("a.css", ".a { gap: 18px }", "espacement"))
        self.assertEqual(signes("a.css", ".a { padding: 1px 6px 10px 24px; gap: 0; margin: -8px }"), [])

    def test_motion_that_loops_bounces_or_moves_everything(self):
        self.assertTrue(un("a.css", ".a { transition: all .2s }", "`transition: all`"))
        self.assertTrue(un("a.html", '<b class="transition-all">x</b>', "`transition: all`"))
        self.assertFalse(un("a.css", ".a { transition: background-color .15s }", "`transition"))
        self.assertTrue(un("a.css", ".a { animation: pulse 2s infinite }", "animation en boucle"))
        self.assertTrue(un("a.html", '<b class="animate-bounce">x</b>', "animation en boucle"))
        self.assertFalse(un("a.css", ".a { animation: spin 1s linear infinite }", "animation en boucle"))  # a loader
        self.assertTrue(un("a.css", ".a { transition-timing-function: cubic-bezier(.68,-0.55,.27,1.55) }", "courbe"))
        self.assertFalse(un("a.css", ".a { transition-timing-function: cubic-bezier(0.22, 1, 0.36, 1) }", "courbe"))


class Redaction(unittest.TestCase):
    def test_exclamation_greeting_hollow_words_and_fake_content_in_text_only(self):
        page = ("<h1>Bonjour Camille</h1><p>Boostez vos ventes !</p><p>Lorem ipsum</p>"
                "<script>if (!ok && a !== b) {}</script><p>{!vide && total}</p>")
        trouves = signes("a.html", page)
        self.assertEqual(sorted(s.split(" →")[0] for s in trouves),
                         ["contenu factice « Lorem ipsum »", "mot creux « Boostez »", "point d'exclamation",
                          "titre d'accueil familier"])
        self.assertEqual(signes("a.html", "<p>Bonjour, voici vos 3 réservations</p>"), [])  # a greeting off a title
        self.assertTrue(un("fr.json", '{"ok": "Enregistré !"}', "point d'exclamation"))
        self.assertTrue(un("fr.po", 'msgid "Saved"\nmsgstr "Enregistré !"\n', "point d'exclamation"))
        self.assertEqual(signes("a.ts", "if (!ok) { throw new Error('Unlock') }"), [])  # code, not interface text

    def test_a_tsx_text_node_is_read_but_not_the_expression_around_it(self):
        self.assertEqual(signes("a.tsx", "return <p className='x'>{!open && <b>Fermé</b>}</p>"), [])
        self.assertTrue(un("a.tsx", "return <Button>Débloquez tout</Button>", "mot creux"))


class Loi(unittest.TestCase):
    def test_blocked_zoom_missing_lang_and_image_without_alt(self):
        self.assertTrue(un("a.html", '<meta name="viewport" content="width=device-width, user-scalable=no">', "zoom"))
        self.assertTrue(un("a.html", '<meta name="viewport" content="initial-scale=1, maximum-scale=1">', "zoom"))
        self.assertFalse(un("a.html", '<meta name="viewport" content="width=device-width, initial-scale=1">', "zoom"))
        self.assertTrue(un("a.html", "<html><body></body></html>", "`<html>` sans `lang`"))
        self.assertFalse(un("a.html", '<html lang="fr"><body></body></html>', "`<html>`"))
        self.assertTrue(un("a.html", '<img src="a.png">', "image sans `alt`"))
        self.assertFalse(un("a.html", '<img src="a.png" alt="">', "image"))
        self.assertFalse(un("a.tsx", "<img {...props} />", "image"))

    def test_focus_removed_without_a_replacement(self):
        self.assertTrue(un("a.css", ".b:focus { outline: none }", "focus retiré"))
        self.assertTrue(un("a.html", '<input class="focus:outline-none">', "focus retiré"))
        self.assertFalse(un("a.css", ".b:focus { outline: none } .b:focus-visible { outline: 2px solid #000 }", "focus"))
        self.assertFalse(un("a.html", '<input class="focus:outline-none focus:ring-2">', "focus"))
        self.assertFalse(un("a.css", ".b:focus { outline: none; box-shadow: 0 0 0 3px #000 }", "focus"))

    def test_a_pre_ticked_consent_box_but_not_a_pre_ticked_preference(self):
        self.assertTrue(un("a.html", '<label><input type="checkbox" name="newsletter" checked> Newsletter</label>',
                           "case de consentement pré-cochée"))
        self.assertTrue(un("a.tsx", "<input type='checkbox' defaultChecked /> J'accepte les CGU", "case de consentement"))
        self.assertFalse(un("a.html", '<input type="checkbox" name="newsletter"> Newsletter', "case"))
        self.assertFalse(un("a.html", '<input type="checkbox" name="compact" checked> Vue compacte', "case"))

    def test_a_cookie_banner_must_offer_to_refuse(self):
        self.assertTrue(un("a.html", "<div>Nous utilisons des cookies <button>Tout accepter</button></div>",
                           "bandeau de cookies"))
        self.assertFalse(un("a.html", "<div>Cookies <button>Tout refuser</button><button>Tout accepter</button></div>",
                            "bandeau"))


class Parcours(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.kb = self.root / ".hosa" / "kb"
        (self.kb / "interface").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def ecrit(self, rel: str, texte: str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texte, encoding="utf-8")

    def lexique(self, *dossiers: str) -> None:
        self.ecrit(".hosa/kb/interface/lexique.md", "## Termes\n| Terme | Désigne | Où | Synonymes interdits |\n"
                   "|---|---|---|---|\n| Cours | c | p | — |\n\n## Dossiers analysés\n"
                   + "".join(f"- `{d}`\n" for d in dossiers))

    def test_a_deliberate_choice_is_kept_with_its_reason(self):
        self.ecrit("src/a.css", "/* gabarit: assumé — la marque impose ce dégradé */\n"
                                ".a { background: linear-gradient(#e11d48, #2563eb) }\n"
                                ".b { font-weight: 900 } /* gabarit: assumé — le logo */\n.c { font-weight: 900 }\n")
        self.assertEqual(gc.signes(self.kb, self.root), ["src/a.css:4 — graisse 800 ou plus → 400 à 600 ; la taille "
                                                         "et la couleur portent la hiérarchie"])

    def test_only_the_lexicon_s_folders_and_code_only_there(self):
        self.ecrit("app/ui.py", "ui.label('Bonjour 👋').classes('font-black')\n")
        self.ecrit("back/metier.py", "log('✨ fait')\n")
        self.ecrit("node_modules/x/a.css", ".a { font-weight: 900 }\n")
        self.assertEqual(gc.signes(self.kb, self.root), [])  # no list: markup and styles only, never dependencies
        self.lexique("app", "absent")
        trouves = gc.signes(self.kb, self.root)
        self.assertIn("dossier analysé introuvable : absent", trouves)
        self.assertEqual(sorted(s.split(" — ")[1].split(" ")[0] for s in trouves if s.startswith("app/")),
                         ["emoji", "graisse"])
        self.assertFalse(any(s.startswith("back/") for s in trouves))

    def test_animations_need_reduced_motion_somewhere_in_the_interface(self):
        self.ecrit("src/a.css", "@keyframes entree { from { opacity: 0 } }\n")
        self.assertEqual(gc.signes(self.kb, self.root)[-1].split(" → ")[0],
                         "src/a.css:1 — animations sans `prefers-reduced-motion`")
        self.ecrit("src/b.css", "@media (prefers-reduced-motion: reduce) { * { animation: none } }\n")
        self.assertEqual(gc.signes(self.kb, self.root), [])

    def test_exit_codes_and_the_switch(self):
        def code(*args: str) -> int:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return gc.main(list(args))
        self.ecrit("src/a.css", ".a { transition: all .2s }\n")
        self.assertEqual(code(str(self.kb), str(self.root)), 1)
        with unittest.mock.patch.dict(os.environ, {"HOSA_GABARIT": "0"}):
            self.assertEqual(code(str(self.kb), str(self.root)), 0)
        self.assertEqual(code(str(self.kb)), 2)
        (self.root / "src" / "a.css").write_text(".a { transition: opacity .2s }\n", encoding="utf-8")
        self.assertEqual(code(str(self.kb), str(self.root)), 0)


if __name__ == "__main__":
    unittest.main()
