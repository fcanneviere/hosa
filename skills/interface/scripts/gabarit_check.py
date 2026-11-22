#!/usr/bin/env python3
"""Cherche dans le code de l'interface les signes d'un gabarit par défaut et les manques que la loi sanctionne.

  gabarit_check.py <kb-dir> <project-root>

Parcourt les dossiers de `## Dossiers analysés` de `kb/interface/lexique.md` (sans cette liste : tout le projet,
hors dépendances et fichiers générés). Chaque signe trouvé donne une ligne `✗ fichier:ligne — signe → correction`.

Trois familles de signes :
- **Ornements et rythme** : dégradé entre deux teintes, texte en dégradé, halo coloré, barre colorée au bord,
  emoji dans l'interface, capitales espacées, graisse 800 ou plus, espacement hors de la grille de 4 px,
  `transition: all`, animation en boucle sans rôle, courbe qui rebondit, animations sans `prefers-reduced-motion`.
- **Rédaction** : point d'exclamation, titre d'accueil familier, mots creux, contenu factice.
- **Loi** : zoom bloqué, focus retiré sans remplacement, `lang` absent, image sans `alt` (WCAG 2.2 AA, repris par
  le RGAA et la norme EN 301 549 de la directive européenne sur l'accessibilité) ; case de consentement
  pré-cochée (RGPD art. 4 et 7) ; bandeau de cookies sans bouton pour refuser (recommandation de la CNIL).

Un choix voulu reste possible : un commentaire `gabarit: assumé — <raison>` sur la ligne, ou sur celle d'avant.
`HOSA_GABARIT=0` coupe le contrôle.

Sortie : 0 aucun signe, 1 signes listés, 2 mauvais appel. Bibliothèque standard seulement.
"""
from __future__ import annotations

import colorsys
import importlib.util
import os
import re
import sys
from pathlib import Path

# Le lexique dit où vit le texte de l'interface : une seule définition, celle de `lexique_check`.
_spec = importlib.util.spec_from_file_location("lexique_check", Path(__file__).with_name("lexique_check.py"))
lexique = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lexique)

STYLES = {".css", ".scss", ".sass", ".less", ".styl"}
BALISAGE = {".html", ".htm", ".vue", ".svelte", ".jsx", ".tsx", ".twig", ".jinja", ".j2", ".erb", ".hbs",
            ".ejs", ".php", ".cshtml", ".razor", ".astro", ".liquid", ".njk"}
SCRIPTS = {".js", ".ts", ".mjs", ".cjs"}
TRADUCTIONS = {".json", ".po", ".strings", ".arb", ".properties", ".yml", ".yaml"}
EXTENSIONS = STYLES | BALISAGE | SCRIPTS | TRADUCTIONS
# Une interface écrite dans le code (NiceGUI, Flutter, SwiftUI…) : lue seulement dans les dossiers du lexique,
# jamais dans tout le projet, où ces fichiers sont surtout le métier.
CODE_INTERFACE = {".py", ".rb", ".dart", ".kt", ".swift"}

ASSUME = re.compile(r"gabarit\s*:\s*assum", re.I)

# ---------------------------------------------------------------- couleurs

# Teinte de chaque famille de couleurs de Tailwind ; les familles grises sont neutres.
TEINTES_TAILWIND = {"red": 0, "orange": 25, "amber": 40, "yellow": 50, "lime": 85, "green": 140, "emerald": 155,
                    "teal": 175, "cyan": 190, "sky": 200, "blue": 220, "indigo": 240, "violet": 260,
                    "purple": 275, "fuchsia": 295, "pink": 330, "rose": 350}
NEUTRES_TAILWIND = {"slate", "gray", "zinc", "neutral", "stone", "white", "black", "transparent", "current",
                    "inherit"}
COULEUR = re.compile(r"#(?:[0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{3,4})\b|rgba?\([^)]*\)|hsla?\([^)]*\)", re.I)


def teinte(couleur: str) -> float | None:
    """La teinte en degrés d'une couleur vive ; `None` pour un gris, un blanc, un noir ou une couleur illisible."""
    c = couleur.strip().lower()
    try:
        if c.startswith("#"):
            h = c[1:]
            if len(h) in (3, 4):
                h = "".join(x * 2 for x in h[:3])
            r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        elif c.startswith("rgb"):
            nombres = re.findall(r"[\d.]+%?", c)[:3]
            r, g, b = (float(n[:-1]) / 100 if n.endswith("%") else float(n) / 255 for n in nombres)
        elif c.startswith("hsl"):
            nombres = re.findall(r"[\d.]+", c)[:3]
            t, s, l = float(nombres[0]), float(nombres[1]) / 100, float(nombres[2]) / 100
            return t % 360 if s >= 0.25 and 0.12 <= l <= 0.9 else None
        else:
            return None
    except (ValueError, IndexError):
        return None
    t, l, s = colorsys.rgb_to_hls(r, g, b)
    return t * 360 if s >= 0.25 and 0.12 <= l <= 0.9 else None


def ecart(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def plusieurs_teintes(teintes: list[float]) -> bool:
    return any(ecart(a, b) >= 30 for i, a in enumerate(teintes) for b in teintes[i + 1:])


def teintes_css(texte: str) -> list[float]:
    return [t for t in (teinte(c) for c in COULEUR.findall(texte)) if t is not None]


def teintes_tailwind(texte: str, prefixes: str) -> list[float]:
    return [TEINTES_TAILWIND[f] for f in re.findall(rf"\b(?:{prefixes})-([a-z]+)-\d{{2,3}}\b", texte)
            if f in TEINTES_TAILWIND]


# ---------------------------------------------------------------- règles par ligne

def regle_degrade(ligne: str) -> str | None:
    for m in re.finditer(r"(?:linear|radial|conic)-gradient\(((?:[^()]|\([^()]*\))*)\)", ligne, re.I):
        if plusieurs_teintes(teintes_css(m[1])):
            return "dégradé entre deux teintes → un fond uni, l'accent seulement là où il a un sens"
    if re.search(r"\bbg-(?:gradient|linear|radial|conic)-", ligne) and plusieurs_teintes(
            teintes_tailwind(ligne, "from|via|to")):
        return "dégradé entre deux teintes → un fond uni, l'accent seulement là où il a un sens"
    return None


def regle_texte_degrade(ligne: str) -> str | None:
    if re.search(r"(?:-webkit-)?background-clip\s*:\s*text|\bbg-clip-text\b", ligne, re.I):
        return "texte en dégradé → la couleur du texte, unie"
    return None


def regle_halo(ligne: str) -> str | None:
    for m in re.finditer(r"(?:box-shadow|text-shadow)\s*:([^;}]*)|drop-shadow\(([^)]*\))", ligne, re.I):
        if teintes_css(m[1] or m[2] or ""):
            return "halo coloré → le relief vient des surfaces et d'un trait fin ; une ombre reste grise"
    if re.search(r"\b(?:shadow|drop-shadow)-(?:" + "|".join(TEINTES_TAILWIND) + r")-\d", ligne) or any(
            teintes_css(x) for x in re.findall(r"\b(?:shadow|drop-shadow)-\[([^\]]*)\]", ligne)):
        return "halo coloré → le relief vient des surfaces et d'un trait fin ; une ombre reste grise"
    return None


def regle_barre_bord(ligne: str) -> str | None:
    m = re.search(r"border-(?:left|inline-start)\s*:\s*(\d+)px\s+solid\s+([^;}]+)", ligne, re.I)
    if m and int(m[1]) >= 3 and teintes_css(m[2]):
        return "barre colorée au bord d'un élément → un statut en mots ou en icône nommée, un trait fin au plus"
    if re.search(r"\bborder-[ls]-(?:[3-9]|\[\d+px\])\b", ligne) and teintes_tailwind(ligne, "border"):
        return "barre colorée au bord d'un élément → un statut en mots ou en icône nommée, un trait fin au plus"
    return None


EMOJI = re.compile("[\U0001F300-\U0001FAFF\U0001F000-\U0001F2FF☀-⛿✀-➿⭐⭕‼⁉]")
SYMBOLES_PERMIS = set("✓✔✗✕✖✳✴❯❮➜➔→←↑↓★☆●○◆◇■□▲▼▶◀☐☑☒✎✏✉☎⚙")  # des signes typographiques, pas des emoji


def regle_emoji(ligne: str) -> str | None:
    trouves = [c for c in EMOJI.findall(ligne) if c not in SYMBOLES_PERMIS]
    if trouves:
        return f"emoji {''.join(dict.fromkeys(trouves))} dans l'interface → une icône d'un seul jeu, ou rien"
    return None


def regle_capitales(ligne: str) -> str | None:
    if re.search(r"(?<![\w-])uppercase(?![\w-])", ligne) and re.search(r"\btracking-(?:wide|wider|widest|\[)", ligne):
        return "capitales espacées → une majuscule au premier mot, sans espacement de lettres"
    return None


def regle_graisse(ligne: str) -> str | None:
    if re.search(r"font-weight\s*:\s*(?:[89]00|bolder)\b|\bfont-(?:extrabold|black)\b", ligne, re.I):
        return "graisse 800 ou plus → 400 à 600 ; la taille et la couleur portent la hiérarchie"
    return None


def hors_grille(px: float) -> bool:
    """La grille de 4 px : 1 px pour un trait, un nombre pair jusqu'à 16 px (les petits contrôles), un multiple de 4
    au-delà."""
    if px != int(px):
        return True
    n = abs(int(px))
    return not (n <= 1 or (n <= 16 and n % 2 == 0) or n % 4 == 0)


def regle_espacement(ligne: str) -> str | None:
    valeurs = []
    for m in re.finditer(r"(?<![\w-])(?:margin|padding|gap|row-gap|column-gap)(?:-[a-z-]+)?\s*:\s*([^;}\"']+)",
                         ligne, re.I):
        valeurs += [float(v) for v in re.findall(r"(-?\d+(?:\.\d+)?)px", m[1])]
    valeurs += [float(v) for v in re.findall(
        r"(?<![\w-])-?(?:p[xytrblse]?|m[xytrblse]?|gap(?:-[xy])?|space-[xy])-\[(-?\d+(?:\.\d+)?)px\]", ligne)]
    faux = sorted({v for v in valeurs if hors_grille(v)})
    if faux:
        return ("espacement hors de la grille de 4 px (" + ", ".join(f"{v:g}px" for v in faux)
                + ") → un nombre pair jusqu'à 16 px, puis un multiple de 4 : 20, 24, 32…")
    return None


def regle_transition(ligne: str) -> str | None:
    if re.search(r"transition(?:-property)?\s*:\s*all\b|(?<![\w-])transition-all(?![\w-])", ligne, re.I):
        return "`transition: all` → nommer ce qui change : couleur, fond, bordure, opacité ou transformation"
    return None


ROLE_BOUCLE = re.compile(r"spin|rotat|tourn|load|charg|skelet|squelet|progress|indetermin", re.I)


def regle_boucle(ligne: str) -> str | None:
    m = re.search(r"animation(?:-iteration-count)?\s*:([^;}]*)\binfinite\b", ligne, re.I)
    if m and not ROLE_BOUCLE.search(m[1]):
        return "animation en boucle sans rôle → une animation en boucle seulement pour un chargement ou un état en direct"
    if re.search(r"(?<![\w-])animate-(?:bounce|ping)(?![\w-])", ligne):
        return "animation en boucle sans rôle → une animation en boucle seulement pour un chargement ou un état en direct"
    return None


def regle_rebond(ligne: str) -> str | None:
    for m in re.finditer(r"cubic-bezier\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)", ligne):
        try:
            y1, y2 = float(m[2]), float(m[4])
        except ValueError:
            continue
        if not (0 <= y1 <= 1 and 0 <= y2 <= 1):
            return "courbe qui rebondit → une seule courbe douce, sans dépassement, pour toute l'interface"
    return None


def regle_zoom(ligne: str) -> str | None:
    if re.search(r"user-scalable\s*=\s*[\"']?(?:no|0)\b|maximum-scale\s*=\s*[\"']?1(?:\.0+)?(?![\d.])", ligne, re.I):
        return "zoom bloqué → retirer `user-scalable=no` et `maximum-scale` (WCAG 1.4.4, exigé par le RGAA)"
    return None


REGLES_LIGNE = (regle_degrade, regle_texte_degrade, regle_halo, regle_barre_bord, regle_emoji, regle_capitales,
                regle_graisse, regle_espacement, regle_transition, regle_boucle, regle_rebond, regle_zoom)

# ---------------------------------------------------------------- rédaction

EXCLAMATION = re.compile(r"[\wÀ-ÿ»);\s  ]!(?![=\w])")
ACCUEIL = re.compile(r"^\s*(?:bienvenue|bonjour|bonsoir|salut|coucou|hello|hi|hey|welcome|ravie? de vous revoir|"
                     r"contente? de vous revoir)\b", re.I)
CREUX = re.compile(r"\b(?:révolutionn\w*|boost\w*|sans effort|magiques?|ultimes?|nouvelle génération|next[- ]gen|"
                   r"débloquez|propulsez|sublimez|game[- ]changer|supercharg\w*|seamless\w*|unlock\w*|empower\w*|"
                   r"cutting[- ]edge|effortless\w*|revolutioni[sz]\w*)\b", re.I)
FACTICE = re.compile(r"\b(?:lorem ipsum|dolor sit amet|john doe|jane doe|john smith|jane smith|acme)\b"
                     r"|\[(?:x|todo|à compléter|placeholder)\]", re.I)


def regles_texte(texte: str, titre: bool) -> list[str]:
    out = []
    if EXCLAMATION.search(" " + texte):
        out.append("point d'exclamation → un énoncé simple")
    if titre and ACCUEIL.search(texte):
        out.append("titre d'accueil familier → le titre nomme le contexte : la page, la période, l'objet")
    m = CREUX.search(texte)
    if m:
        out.append(f"mot creux « {m[0]} » → dire ce que fait la fonction, avec les mots du lexique")
    m = FACTICE.search(texte)
    if m:
        out.append(f"contenu factice « {m[0]} » → des données plausibles, celles du domaine")
    return out


SANS_CODE = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>|<!--.*?-->|\{\{.*?\}\}|\{%.*?%\}|\{[^{}]*\}", re.S | re.I)
NOEUD = re.compile(r"<([A-Za-z][\w.-]*)\b[^<>]*>([^<>]+)(?=</?[A-Za-z])")


def textes_balisage(texte: str) -> list[tuple[int, str, bool]]:
    """Les nœuds de texte d'un gabarit : (position, texte, dans un titre h1-h2). Le code et les expressions
    sont remplacés par des blancs, à la même longueur : les positions restent celles du fichier."""
    propre = SANS_CODE.sub(lambda m: re.sub(r"[^\n]", " ", m[0]), texte)
    return [(m.start(2), m[2], m[1].lower() in ("h1", "h2")) for m in NOEUD.finditer(propre) if m[2].strip()]


def textes_traduction(chemin: Path, texte: str) -> list[tuple[int, str, bool]]:
    if chemin.suffix == ".po":
        motif = re.compile(r'^msgstr\s+"(.*)"\s*$', re.M)
    elif chemin.suffix == ".json" or chemin.suffix == ".arb":
        motif = re.compile(r'"[^"\n]+"\s*:\s*"((?:[^"\\\n]|\\.)*)"')
    elif chemin.suffix == ".strings":
        motif = re.compile(r'=\s*"((?:[^"\\\n]|\\.)*)"\s*;')
    else:  # .properties, .yml : `clé = valeur` ou `clé: valeur`
        motif = re.compile(r"^\s*[\w.-]+\s*[:=]\s*[\"']?([^\"'\n#]+)", re.M)
    return [(m.start(1), m[1], False) for m in motif.finditer(texte) if m[1].strip()]


# ---------------------------------------------------------------- règles sur le fichier entier

CONSENTEMENT = re.compile(r"consent|accept|newsletter|cookie|partenaire|marketing|publicit|prospection|offres|"
                          r"\bcgu\b|\bcgv\b|conditions g[ée]n[ée]rales", re.I)
CASE = re.compile(r"<input\b[^>]*\btype\s*=\s*[\"'{]?checkbox[^>]*>", re.I | re.S)
COCHEE = re.compile(r"(?<![\w-])(?:checked|defaultChecked)(?:\s*=\s*(?:[\"']?(?:true|checked)[\"']?|\{\s*true\s*\}))?"
                    r"(?=[\s/>])|:checked\s*=\s*[\"']true", re.I)


def regles_fichier(chemin: Path, texte: str, noeuds: list[tuple[int, str, bool]]) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    if chemin.suffix in BALISAGE:
        for m in re.finditer(r"<html\b[^>]*>", texte, re.I):
            if not re.search(r"\blang\s*=", m[0]):
                out.append((m.start(), "`<html>` sans `lang` → `lang=\"fr\"` (WCAG 3.1.1 : la langue de la page)"))
        for m in re.finditer(r"<img\b[^>]*>", texte, re.I | re.S):
            if not re.search(r"\balt\s*=", m[0]) and not re.search(r"\{\s*\.\.\.", m[0]):
                out.append((m.start(), "image sans `alt` → un texte de remplacement, ou `alt=\"\"` si elle est "
                                       "décorative (WCAG 1.1.1)"))
        for m in CASE.finditer(texte):
            voisinage = m[0] + texte[m.end():m.end() + 300]
            if COCHEE.search(m[0]) and CONSENTEMENT.search(voisinage):
                out.append((m.start(), "case de consentement pré-cochée → décochée par défaut : un consentement est "
                                       "un acte (RGPD art. 4 et 7)"))
        boutons = " ".join(t for _, t, _ in noeuds).lower()
        if re.search(r"cookie|traceur", texte, re.I) and re.search(r"\b(?:tout )?accepter\b|\baccept(?: all)?\b",
                                                                   boutons):
            if not re.search(r"\brefuser\b|continuer sans accepter|\breject\b|\bdecline\b|\brefuse\b", boutons):
                pos = next(p for p, t, _ in noeuds if re.search(r"accept", t, re.I))
                out.append((pos, "bandeau de cookies sans bouton pour refuser → « Tout refuser » au même niveau et "
                                 "aussi visible que « Tout accepter » (CNIL)"))
    # Le focus retiré sans remplacement : dans le même fichier, rien ne redessine le focus.
    remplace = re.search(r"focus-visible|focus:ring|focus-within:ring|:focus[^{}]*\{[^}]*(?:box-shadow|"
                         r"outline\s*:(?!\s*(?:none|0)\b))", texte, re.I)
    if not remplace:
        m = re.search(r"outline\s*:\s*(?:none|0)\b|(?<![\w-])(?:focus:)?outline-none(?![\w-])", texte, re.I)
        if m:
            out.append((m.start(), "focus retiré sans remplacement → un focus visible au clavier, "
                                   "`:focus-visible` avec un contour (WCAG 2.4.7)"))
    return out


# ---------------------------------------------------------------- parcours

def numero(texte: str, position: int) -> int:
    return texte.count("\n", 0, position) + 1


COMMENTAIRE_SEUL = re.compile(r"^\s*(?:/\*|//|<!--|#|\{#|\{\{!--|\*)")


def assume(lignes: list[str], n: int) -> bool:
    """Le choix est assumé sur la ligne même, ou par un commentaire seul sur la ligne d'avant."""
    meme = 0 <= n - 1 < len(lignes) and ASSUME.search(lignes[n - 1])
    avant = 0 <= n - 2 < len(lignes) and ASSUME.search(lignes[n - 2]) and COMMENTAIRE_SEUL.match(lignes[n - 2])
    return bool(meme or avant)


def examine(chemin: Path, texte: str) -> list[tuple[int, str]]:
    """Les signes d'un fichier : (numéro de ligne, signe → correction), sans ceux qu'un commentaire assume."""
    lignes = texte.splitlines()
    trouves: list[tuple[int, str]] = []
    for n, ligne in enumerate(lignes, 1):
        if len(ligne) > 2000:  # une ligne minifiée : du code généré, pas celui qu'on écrit
            continue
        trouves += [(n, r) for r in (regle(ligne) for regle in REGLES_LIGNE) if r]
    if chemin.suffix in BALISAGE:
        noeuds = textes_balisage(texte)
    elif chemin.suffix in TRADUCTIONS:
        noeuds = textes_traduction(chemin, texte)
    else:
        noeuds = []
    for pos, t, titre in noeuds:
        trouves += [(numero(texte, pos), r) for r in regles_texte(t, titre)]
    trouves += [(numero(texte, pos), r) for pos, r in regles_fichier(chemin, texte, noeuds)]
    return sorted({x for x in trouves if not assume(lignes, x[0])})


ANIME = re.compile(r"@keyframes|(?<![\w-])animate-[a-z]|animation\s*:", re.I)
MOUVEMENT_REDUIT = re.compile(r"prefers-reduced-motion|motion-reduce:|motion-safe:")


def fichiers(racine: Path, dossiers: list[str]):
    lues = EXTENSIONS | CODE_INTERFACE if dossiers else EXTENSIONS
    for base in [racine / d for d in dossiers] or [racine]:
        if base.is_file():
            yield base
            continue
        for d, sous, noms in os.walk(base):
            sous[:] = [x for x in sous if x not in lexique.SKIP]
            for n in noms:
                p = Path(d) / n
                if p.suffix.lower() in lues and ".min." not in n and not n.endswith((".lock", "-lock.json")) \
                        and n not in ("package.json", "tsconfig.json", "composer.json"):
                    yield p


def signes(kb: Path, racine: Path) -> list[str]:
    _, dossiers, _ = lexique.lexicon(kb)
    absents = [d for d in dossiers if not (racine / d).exists()]
    out = [f"dossier analysé introuvable : {d}" for d in absents]
    anime, reduit = None, False
    for f in fichiers(racine, [d for d in dossiers if d not in absents]):
        try:
            texte = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = f.relative_to(racine).as_posix()
        out += [f"{rel}:{n} — {r}" for n, r in examine(f, texte)]
        if anime is None and f.suffix not in TRADUCTIONS:
            m = ANIME.search(texte)
            if m and not assume(texte.splitlines(), numero(texte, m.start())):
                anime = f"{rel}:{numero(texte, m.start())}"
        reduit = reduit or bool(MOUVEMENT_REDUIT.search(texte))
    if anime and not reduit:
        out.append(f"{anime} — animations sans `prefers-reduced-motion` → les couper ou les réduire quand "
                   "l'utilisateur le demande à son système")
    return out


def main(argv: list[str]) -> int:
    if os.environ.get("HOSA_GABARIT") == "0":
        print("gabarit_check désactivé (HOSA_GABARIT=0)")
        return 0
    if len(argv) != 2 or not Path(argv[0]).is_dir() or not Path(argv[1]).is_dir():
        print("usage: gabarit_check.py <kb-dir> <project-root>", file=sys.stderr)
        return 2
    trouves = signes(Path(argv[0]), Path(argv[1]))
    for s in trouves:
        print(f"✗ {s}")
    print("✓ aucun signe de gabarit par défaut" if not trouves else
          f"{len(trouves)} signe(s) — un choix voulu : `gabarit: assumé — <raison>` en commentaire sur la ligne")
    return 1 if trouves else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
