#!/usr/bin/env python3
"""Atelier de design de Hosa : cartes de style, page de comparaison, choix de l'utilisateur, jetons.

  atelier.py cartes   <cartes.json> --out <dossier> [--force]
      Valide les cartes (contraste WCAG AA calculé pour chaque paire de couleurs utilisée), dessine une carte
      par identité, sur le même contenu réel, et la page de comparaison `comparaison.html`.
  atelier.py comparer <manifest.json> --out <page.html> [--force]
      Assemble des maquettes locales (html, image, url locale) en une page de comparaison autonome, sans réseau.
  atelier.py choisir  <kb> <manche> <id> --depuis <cartes.json|manifest.json> --par <utilisateur> [--note "…"]
  atelier.py choisir  <kb> <manche> --conserve --par <utilisateur> [--note "…"]
      Écrit le choix de la manche dans `kb/interface/choix.md` ; pour `styles`, aussi les jetons de la carte.
      `--conserve` : l'utilisateur garde l'existant pour cette manche (interface à compléter, manches d'avant Hosa).
  atelier.py css      <kb> --out <fichier>
      Écrit les jetons de `kb/interface/choix.md` en variables CSS (bloc marqué) et note le fichier dans la KB.
  atelier.py ecart    <kb>
      Contrôle que le fichier CSS du projet porte toujours les jetons de la KB.

Sortie : une ligne JSON (succès) ou les manques exacts, un par ligne. Code : 0 réussi, 1 refusé, 2 mauvais appel.
Le contrôle des ressources des maquettes est adapté d'oil-ui (https://github.com/oil-oil/oil-ui,
licence MIT, © 2026 oil-oil, voir ../NOTICE-oil-ui.md) ; le reste est de Hosa.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
TEMPLATE = SKILL / "assets" / "comparaison.html"
MARKER = "/*__ATELIER_DONNEES__*/null"
CSP_MARKER = "__ATELIER_CSP__"
MANCHES = ("styles", "directions", "page")


class Refus(ValueError):
    """Une entrée refusée : le message dit exactement quoi corriger."""


# ---------------------------------------------------------------- couleurs et contraste (WCAG 2.2)

HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})")
HEX_PALETTE = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})")
ROLES = ("bg", "surface", "text", "muted", "accent", "accent_text", "line", "warn")
ROLE_NOMS = {"bg": "fond", "surface": "surface", "text": "texte", "muted": "texte secondaire", "accent": "accent",
             "accent_text": "texte sur accent", "line": "trait", "warn": "alerte"}


def rgb(hexa: str) -> tuple[float, float, float]:
    h = hexa.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def mix(a: str, b: str, part_a: float) -> str:
    """`color-mix(in srgb, a part_a, b)` — ce que la carte affiche pour les étiquettes teintées."""
    ca, cb = rgb(a), rgb(b)
    return "#" + "".join(f"{round((x * part_a + y * (1 - part_a)) * 255):02x}" for x, y in zip(ca, cb))


def luminance(hexa: str) -> float:
    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb(hexa))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def paires(col: dict) -> list[tuple[str, str, str, float]]:
    """Chaque paire de couleurs que la carte et l'interface affichent, avec le minimum WCAG AA qu'elle doit tenir :
    4,5:1 pour du texte, 3:1 pour un composant d'interface (1.4.11)."""
    tag_accent = mix(col["accent"], col["surface"], 0.14)
    tag_warn = mix(col["warn"], col["surface"], 0.14)
    return [
        ("texte sur fond", col["text"], col["bg"], 4.5),
        ("texte sur surface", col["text"], col["surface"], 4.5),
        ("texte secondaire sur fond", col["muted"], col["bg"], 4.5),
        ("texte secondaire sur surface", col["muted"], col["surface"], 4.5),
        ("texte sur accent (bouton principal)", col["accent_text"], col["accent"], 4.5),
        ("accent sur fond (bouton, lien, focus)", col["accent"], col["bg"], 3.0),
        ("accent sur étiquette teintée", col["accent"], tag_accent, 4.5),
        ("alerte sur étiquette teintée", col["warn"], tag_warn, 4.5),
    ]


def controles(col: dict) -> tuple[list[str], list[str]]:
    """(lignes lisibles, manques) : chaque paire avec son rapport ; un manque par paire sous le minimum."""
    lignes, manques = [], []
    for nom, avant, arriere, mini in paires(col):
        r = contraste(avant, arriere)
        ok = r >= mini
        lignes.append(f"{nom} {r:.1f}:1 {'✓' if ok else '✗'}".replace(".", ","))
        if not ok:
            manques.append(f"{nom} : {avant.upper()} sur {arriere.upper()} = {r:.2f}:1, il faut {mini}:1")
    return lignes, manques


# ---------------------------------------------------------------- cartes de style

DENSITE = {"compact": (12, 6, 12, 0.92), "regular": (18, 9, 16, 1.0), "airy": (26, 12, 20, 1.08)}
LAYOUTS = {
    "sidebar-table": "Barre latérale et tableau",
    "topbar-cards": "Barre du haut et grille de cartes",
    "queue-detail": "Liste à gauche, détail à droite",
    "hero-center": "Titre centré et aperçu du produit",
    "hero-split": "Texte à gauche, visuel à droite",
    "editorial": "Gros titres et colonnes",
    "fullbleed": "Visuel pleine page, texte par-dessus",
}
FONT = re.compile(r"[\w \t\"',.-]+")
ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")


def exige(obj: dict, cle: str, ou: str, genre=str):
    if not isinstance(obj, dict) or cle not in obj:
        raise Refus(f"{ou} : `{cle}` manquant")
    v = obj[cle]
    if not isinstance(v, genre) or (genre is str and not v.strip()):
        attendu = {str: "une chaîne non vide", dict: "un objet", list: "une liste"}[genre]
        raise Refus(f"{ou}.{cle} doit être {attendu}")
    return v


def liste_texte(obj: dict, cle: str, ou: str, *, requise: bool = False) -> list[str]:
    v = obj.get(cle, [] if not requise else None)
    if not isinstance(v, list) or (requise and not v) or any(not isinstance(t, str) or not t.strip() for t in v):
        raise Refus(f"{ou}.{cle} doit être une liste {'non vide ' if requise else ''}de chaînes non vides")
    return [t.strip() for t in v]


def police(valeur: str, ou: str) -> None:
    if not FONT.fullmatch(valeur):
        raise Refus(f"{ou} : noms de police système seulement, pas de police réseau : {valeur}")
    for part in (p.strip() for p in valeur.split(",")):
        if not part:
            raise Refus(f"{ou} : un nom de police vide")
        if part[0] in "\"'":
            ok = len(part) > 2 and part[-1] == part[0] and part[0] not in part[1:-1] and part[1:-1].strip()
        else:
            ok = not any(q in part for q in "\"'")
        if not ok:
            raise Refus(f"{ou} : guillemets de police non appariés ou nom vide : {valeur}")


def charge_cartes(chemin: Path) -> dict:
    try:
        cfg = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Refus(f"configuration illisible {chemin} : {exc}") from None
    if not isinstance(cfg, dict):
        raise Refus("la racine de la configuration doit être un objet")
    for cle, defaut in (("project", "Cartes de style"), ("round", "Cartes de style"),
                        ("brief", "Comparer couleurs, typographie, contrôles et mise en page sur le même contenu")):
        cfg.setdefault(cle, defaut)
        exige(cfg, cle, "configuration")
    if cfg.setdefault("lang", "fr") not in ("fr", "en"):
        raise Refus('lang doit valoir "fr" ou "en"')
    c = exige(cfg, "content", "configuration", dict)
    for cle in ("title", "body", "number", "number_label", "primary", "secondary"):
        exige(c, cle, "content")
    for cle in ("input_label", "input_value"):
        if cle in c:
            exige(c, cle, "content")
    liste_texte(c, "tags", "content")
    if "screen" in c:
        ecran = exige(c, "screen", "content", dict)
        liste_texte(ecran, "nav", "content.screen", requise=True)
        cols = liste_texte(ecran, "columns", "content.screen", requise=True)
        lignes = exige(ecran, "rows", "content.screen", list)
        if not lignes or any(not isinstance(r, list) or len(r) != len(cols) or any(not isinstance(x, str) for x in r)
                             for r in lignes):
            raise Refus(f"content.screen.rows : une liste de lignes de {len(cols)} chaînes, comme `columns`")
    cartes = exige(cfg, "cards", "configuration", list)
    if not 2 <= len(cartes) <= 6:
        raise Refus(f"cards : 2 à 6 cartes, il y en a {len(cartes)}")
    vus, manques = set(), []
    for i, carte in enumerate(cartes, 1):
        ou = f"carte {i}"
        if not isinstance(carte, dict):
            raise Refus(f"{ou} doit être un objet")
        if "content" in carte:
            raise Refus(f"{ou}.content : toutes les cartes montrent le même contenu, celui de la racine")
        cid = exige(carte, "id", ou)
        if not ID.fullmatch(cid) or cid in vus:
            raise Refus(f"{ou} : id invalide ou en double : {cid}")
        vus.add(cid)
        ou = f"carte {cid}"
        exige(carte, "name", ou)
        exige(carte, "concept", ou)
        liste_texte(carte, "traits", ou)
        col = exige(carte, "colors", ou, dict)
        for role in ROLES:
            v = exige(col, role, f"{ou}.colors")
            if not HEX.fullmatch(v):
                raise Refus(f"{ou}.colors.{role} : une couleur hexadécimale #RGB ou #RRGGBB : {v}")
        polices = exige(carte, "fonts", ou, dict)
        for role in ("display", "body", "number"):
            police(exige(polices, role, f"{ou}.fonts"), f"{ou}.fonts.{role}")
        for cle, options, defaut in (("layout", LAYOUTS, None), ("density", DENSITE, "regular"),
                                     ("border", ("none", "hairline", "solid"), "hairline"),
                                     ("shadow", ("none", "soft"), "none"), ("texture", ("none", "paper"), "none")):
            v = carte.get(cle, defaut)
            if not isinstance(v, str) or v not in options:
                raise Refus(f"{ou}.{cle} doit valoir : {', '.join(options)}")
        rayon = carte.get("radius", 6)
        if type(rayon) not in (int, float) or not 0 <= rayon <= 28:
            raise Refus(f"{ou}.radius : un nombre de 0 à 28")
        for cle, defaut in (("display_weight", 500), ("number_weight", 400)):
            poids = carte.get(cle, defaut)
            if type(poids) is not int or not 300 <= poids <= 900:
                raise Refus(f"{ou}.{cle} : un entier de 300 à 900")
        manques += [f"{ou} — {m}" for m in controles(col)[1]]
    if manques:
        raise Refus("contraste WCAG AA insuffisant, corrige ces couleurs :\n" + "\n".join(manques))
    return cfg


def premiere_police(pile: str) -> str:
    return pile.split(",")[0].strip().strip("\"'")


def jetons(carte: dict) -> dict[str, str]:
    """Les jetons de l'identité, nommés comme dans le CSS du projet : la seule définition, de la carte au code."""
    col, f = carte["colors"], carte["fonts"]
    gap, py, px, echelle = DENSITE[carte.get("density", "regular")]
    bordure = {"none": "0 solid transparent", "hairline": f"1px solid {col['line']}",
               "solid": f"1.5px solid {col['text']}"}[carte.get("border", "hairline")]
    ombre = "0 1px 2px rgb(0 0 0 / .05), 0 10px 28px rgb(0 0 0 / .07)" if carte.get("shadow") == "soft" else "none"
    return {
        "--color-bg": col["bg"], "--color-surface": col["surface"], "--color-text": col["text"],
        "--color-muted": col["muted"], "--color-accent": col["accent"], "--color-on-accent": col["accent_text"],
        "--color-line": col["line"], "--color-warn": col["warn"],
        "--font-display": f["display"], "--font-body": f["body"], "--font-number": f["number"],
        "--weight-display": str(carte.get("display_weight", 500)), "--weight-number": str(carte.get("number_weight", 400)),
        "--font-size-base": f"{round(15 * echelle)}px", "--radius": f"{carte.get('radius', 6)}px",
        "--border": bordure, "--shadow": ombre, "--space-gap": f"{gap}px", "--space-y": f"{py}px", "--space-x": f"{px}px",
        "--focus-ring": f"2px solid {col['accent']}",
    }


def apercu(carte: dict, c: dict) -> str:
    """Le premier écran dans cette identité : avec `content.screen`, le vrai menu et les vraies lignes ;
    sinon une esquisse en aplats."""
    e = lambda s: html.escape(str(s))
    lay = carte["layout"]
    ecran = c.get("screen")
    if ecran:
        nav = "".join(f'<li{" class=on" if i == 0 else ""}>{e(n)}</li>' for i, n in enumerate(ecran["nav"]))
        tete = "".join(f"<th>{e(x)}</th>" for x in ecran["columns"])
        corps = "".join("<tr>" + "".join(f"<td>{e(x)}</td>" for x in r) + "</tr>" for r in ecran["rows"][:5])
        table = f'<table><thead><tr>{tete}</tr></thead><tbody>{corps}</tbody></table>'
        barre = f'<div class="pbar"><b>{e(ecran["nav"][0])}</b><span class="pbtn">{e(c["primary"])}</span></div>'
        if lay == "sidebar-table":
            return f'<div class="pv pv-side"><ul class="pnav">{nav}</ul><div class="pmain">{barre}{table}</div></div>'
        if lay == "queue-detail":
            items = "".join(f'<li{" class=on" if i == 0 else ""}><b>{e(r[0])}</b><small>{e(" · ".join(r[1:3]))}</small></li>'
                            for i, r in enumerate(ecran["rows"][:5]))
            premier = ecran["rows"][0]
            detail = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in zip(ecran["columns"], premier))
            return (f'<div class="pv pv-queue"><ul class="pq">{items}</ul><div class="pdet"><h4>{e(premier[0])}</h4>'
                    f'<dl>{detail}</dl><span class="pbtn">{e(c["primary"])}</span></div></div>')
        if lay == "topbar-cards":
            tuiles = "".join(f'<div class="ptile"><b>{e(r[0])}</b><small>{e(" · ".join(r[1:]))}</small></div>'
                             for r in ecran["rows"][:6])
            return f'<div class="pv pv-top"><ul class="pnav row">{nav}</ul><div class="pgrid">{tuiles}</div></div>'
        return (f'<div class="pv pv-top"><ul class="pnav row">{nav}</ul><h4 class="phero">{e(c["title"])}</h4>'
                f'<span class="pbtn">{e(c["primary"])}</span>{table}</div>')
    b = lambda cls: f'<i class="{cls}"></i>'
    if lay == "sidebar-table":
        return f'<div class="sk sk-side">{b("side")}<div class="main">{b("bar")}{"".join(b("rw") for _ in range(5))}</div></div>'
    if lay == "topbar-cards":
        return f'<div class="sk">{b("nav")}<div class="grid">{b("tile") * 6}</div></div>'
    if lay == "queue-detail":
        return f'<div class="sk sk-side"><div class="list">{b("item on")}{b("item") * 4}</div><div class="main">{b("h1")}{b("p") * 4}{b("cta")}</div></div>'
    if lay == "editorial":
        return f'<div class="sk">{b("nav")}{b("mega")}<div class="cols">{b("p") * 9}</div></div>'
    if lay == "fullbleed":
        return f'<div class="sk sk-full">{b("nav")}{b("h1")}{b("p")}{b("cta")}</div>'
    return f'<div class="sk">{b("nav")}{b("h1")}{b("p")}{b("cta")}<div class="grid">{b("tile") * 3}</div></div>'


def carte_html(cfg: dict, carte: dict, lettre: str) -> str:
    e = lambda s: html.escape(str(s))
    c, col, f = cfg["content"], carte["colors"], carte["fonts"]
    j = jetons(carte)
    echelle = DENSITE[carte.get("density", "regular")][3]
    racine = ";".join(f"{k}:{v}" for k, v in j.items())
    papier = ("background-image:url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'>"
              "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' stitchTiles='stitch'/>"
              "<feColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .05 0'/></filter>"
              "<rect width='100%' height='100%' filter='url(%23n)'/></svg>\");") if carte.get("texture") == "paper" else ""
    lignes, _ = controles(col)
    nuancier = "".join(f'<div class="sw"><span style="background:{col[r]}"></span><b>{e(ROLE_NOMS[r].capitalize())}</b>'
                       f'<em>{col[r].upper()}</em></div>' for r in ("bg", "surface", "text", "muted", "accent", "warn"))
    polices = "".join(f"<li><b>{n}</b>{e(premiere_police(f[k]))}</li>"
                      for k, n in (("display", "Titres"), ("body", "Texte"), ("number", "Chiffres")))
    etiquettes = "".join(f'<span class="tag{" warn" if i else ""}">{e(t)}</span>' for i, t in enumerate(c.get("tags", [])[:2]))
    champ = (f'<label class="field"><small>{e(c["input_label"])}</small><span>{e(c["input_value"])}</span></label>'
             if c.get("input_value") else "")
    traits = "".join(f"<span>{e(t)}</span>" for t in carte.get("traits", []))
    contr = "".join(f"<li>{e(x)}</li>" for x in lignes)
    return f"""<!doctype html>
<html lang="{cfg['lang']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(carte['name'])}</title><style>
:root{{{racine}}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--color-bg);{papier}color:var(--color-text);font:var(--font-size-base)/1.55 var(--font-body);padding:40px 52px;display:flex;flex-direction:column;gap:calc(var(--space-gap)*1.5)}}
.top{{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid var(--color-line);padding-bottom:12px}}
.brand{{font:var(--weight-display) 20px/1 var(--font-display)}}
.top small,.k{{font-size:12px;color:var(--color-muted);letter-spacing:.02em}}
.k{{display:block;margin-bottom:calc(var(--space-gap)*.6)}}
.row{{display:grid;grid-template-columns:1.15fr 1fr;gap:48px}}
h1{{font:var(--weight-display) {round(38 * echelle)}px/1.18 var(--font-display);letter-spacing:-.01em;text-wrap:balance}}
.body{{color:var(--color-muted);margin-top:8px;max-width:32em;text-wrap:pretty}}
.num{{font:var(--weight-number) {round(56 * echelle)}px/1.05 var(--font-number);font-variant-numeric:tabular-nums;margin-top:calc(var(--space-gap)*1.1)}}
.num+small{{color:var(--color-muted);font-size:13px}}
.sws{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}}
.sw span{{display:block;aspect-ratio:1;border-radius:var(--radius);border:1px solid rgb(0 0 0 / .08)}}
.sw b{{display:block;font-weight:500;font-size:11px;margin-top:5px}}.sw em{{font-style:normal;font-size:11px;color:var(--color-muted);font-family:Menlo,Consolas,monospace}}
.fonts,.ctl{{list-style:none;margin-top:calc(var(--space-gap)*.9);font-size:12px;color:var(--color-muted)}}.fonts b{{display:inline-block;width:5.5em;color:var(--color-text);font-weight:500}}
.ctl{{columns:2;column-gap:16px}}
.controls{{display:flex;align-items:center;gap:var(--space-gap);flex-wrap:wrap;border-top:1px solid var(--color-line);padding-top:calc(var(--space-gap)*1.1)}}
.btn{{font:500 14px/1 var(--font-body);padding:var(--space-y) var(--space-x);border-radius:var(--radius);border:var(--border);background:var(--color-surface);color:var(--color-text);box-shadow:var(--shadow)}}
.btn.primary{{background:var(--color-accent);color:var(--color-on-accent);border-color:var(--color-accent)}}
.btn.focus{{outline:var(--focus-ring);outline-offset:2px}}
.tag{{font-size:12px;padding:3px 10px;border-radius:calc(var(--radius) + 4px);background:color-mix(in srgb,var(--color-accent) 14%,var(--color-surface));color:var(--color-accent)}}
.tag.warn{{background:color-mix(in srgb,var(--color-warn) 14%,var(--color-surface));color:var(--color-warn)}}
.field{{margin-left:auto;display:flex;gap:10px;align-items:center;min-width:240px;padding:var(--space-y) 12px;border-radius:var(--radius);border:var(--border);background:var(--color-surface);box-shadow:var(--shadow)}}
.field small{{color:var(--color-muted);font-size:12px}}
.bottom{{display:grid;grid-template-columns:1.4fr 1fr;gap:40px;border-top:1px solid var(--color-line);padding-top:calc(var(--space-gap)*1.1);flex:1}}
.frame{{height:250px;border-radius:var(--radius);border:var(--border);background:var(--color-surface);box-shadow:var(--shadow);overflow:hidden;font-size:12px}}
.pv{{height:100%;display:flex}} .pv-top{{flex-direction:column;padding:10px 12px;gap:8px}}
.pnav{{list-style:none;width:26%;background:color-mix(in srgb,var(--color-text) 6%,var(--color-surface));padding:10px 8px;display:flex;flex-direction:column;gap:2px}}
.pnav li{{padding:5px 8px;border-radius:calc(var(--radius)/2);color:var(--color-muted)}} .pnav li.on{{background:var(--color-accent);color:var(--color-on-accent)}}
.pnav.row{{width:auto;flex-direction:row;background:none;padding:0;border-bottom:1px solid var(--color-line);padding-bottom:6px}}
.pmain{{flex:1;padding:10px 12px;display:flex;flex-direction:column;gap:8px;min-width:0}}
.pbar{{display:flex;justify-content:space-between;align-items:center}} .pbar b{{font:var(--weight-display) 15px/1.2 var(--font-display)}}
.pbtn{{align-self:flex-start;background:var(--color-accent);color:var(--color-on-accent);padding:4px 10px;border-radius:var(--radius);font-weight:500}}
table{{border-collapse:collapse;width:100%}} th{{text-align:left;font-weight:500;color:var(--color-muted);border-bottom:var(--border);padding:4px 6px}}
td{{padding:4px 6px;border-bottom:1px solid var(--color-line);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:120px;font-variant-numeric:tabular-nums}}
.pq{{list-style:none;width:40%;border-right:1px solid var(--color-line)}} .pq li{{padding:8px 10px;border-bottom:1px solid var(--color-line);display:flex;flex-direction:column}}
.pq li.on{{background:color-mix(in srgb,var(--color-accent) 12%,var(--color-surface))}} .pq small{{color:var(--color-muted)}}
.pdet{{flex:1;padding:10px 14px;display:flex;flex-direction:column;gap:8px}} .pdet h4,.phero{{font:var(--weight-display) 16px/1.2 var(--font-display)}}
dl{{display:grid;grid-template-columns:auto 1fr;gap:3px 12px}} dt{{color:var(--color-muted)}}
.pgrid{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;flex:1}} .ptile{{border:var(--border);border-radius:var(--radius);padding:8px;display:flex;flex-direction:column;gap:2px;background:var(--color-bg)}} .ptile small{{color:var(--color-muted)}}
.sk{{height:100%;padding:12px;display:flex;flex-direction:column;gap:8px}} .sk i{{display:block;min-height:8px;background:color-mix(in srgb,var(--color-text) 10%,transparent);border-radius:calc(var(--radius)/2)}}
.sk-side{{flex-direction:row}} .sk .side{{width:18%;background:color-mix(in srgb,var(--color-text) 80%,transparent)}} .sk .main,.sk .list{{flex:1;display:flex;flex-direction:column;gap:6px}} .sk .list{{flex:.6}}
.sk .rw,.sk .item{{flex:1}} .sk .on{{background:color-mix(in srgb,var(--color-accent) 35%,transparent)}} .sk .h1{{height:20px;width:60%}} .sk .mega{{height:32px}}
.sk .cta{{height:14px;width:22%;background:var(--color-accent)}} .sk .grid,.sk .cols{{flex:1;display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}
.sk-full{{background:color-mix(in srgb,var(--color-accent) 70%,var(--color-text));justify-content:center}} .sk-full i{{background:color-mix(in srgb,var(--color-on-accent) 55%,transparent)}}
.style h2{{font:var(--weight-display) 22px/1.3 var(--font-display)}} .style p{{color:var(--color-muted);margin-top:6px}}
.traits{{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}} .traits span{{font-size:12px;padding:2px 9px;border-radius:999px;border:1px solid var(--color-line);color:var(--color-muted)}}
</style></head><body>
<header class="top"><span class="brand">{e(cfg['project'])}</span><small>{lettre} · {e(carte['name'])}</small></header>
<section class="row"><div><span class="k">Typographie et chiffres</span><h1>{e(c['title'])}</h1><p class="body">{e(c['body'])}</p><div class="num">{e(c['number'])}</div><small>{e(c['number_label'])}</small></div>
<div><span class="k">Couleurs</span><div class="sws">{nuancier}</div><ul class="fonts">{polices}</ul><ul class="ctl">{contr}</ul></div></section>
<section class="controls"><span class="k" style="margin:0 6px 0 0">Contrôles</span><button class="btn primary">{e(c['primary'])}</button><button class="btn">{e(c['secondary'])}</button><button class="btn focus">Focus clavier</button>{etiquettes}{champ}</section>
<section class="bottom"><div><span class="k">Premier écran · {e(LAYOUTS[carte['layout']])}</span><div class="frame">{apercu(carte, c)}</div></div>
<div class="style"><span class="k">Intention</span><h2>{e(carte['name'])}</h2><p>{e(carte['concept'])}</p><div class="traits">{traits}</div></div></section>
</body></html>
"""


def ecrit_atomique(cible: Path, texte: str) -> None:
    cible.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=cible.parent, delete=False, suffix=".tmp") as h:
        tmp = Path(h.name)
        h.write(texte)
    try:
        tmp.replace(cible)
    finally:
        if tmp.exists():
            tmp.unlink()


def cartes(cfg_chemin: Path, sortie: Path, force: bool) -> dict:
    cfg_chemin, sortie = cfg_chemin.resolve(), sortie.resolve()
    if sortie.is_relative_to(SKILL):
        raise Refus(f"la sortie ne peut pas être dans le dossier de Hosa : {sortie}")
    if sortie.exists() and not sortie.is_dir():
        raise Refus(f"la sortie doit être un dossier : {sortie}")
    cfg = charge_cartes(cfg_chemin)
    page = sortie / "comparaison.html"
    if page.exists() and not force:
        raise Refus(f"la page existe déjà : {page} ; --force pour la refaire")
    noms = [f"carte-{c['id']}.html" for c in cfg["cards"]] + ["manifest.json", page.name]
    if cfg_chemin.parent == sortie and cfg_chemin.name in noms:
        raise Refus(f"la configuration serait écrasée par la sortie, renomme-la : {cfg_chemin}")
    for n in noms:
        if (sortie / n).is_symlink() or ((sortie / n).exists() and not (sortie / n).is_file()):
            raise Refus(f"un fichier de sortie ne peut être ni un dossier ni un lien : {sortie / n}")
    candidats = []
    for i, carte in enumerate(cfg["cards"]):
        f = carte["fonts"]
        candidats.append({
            "id": carte["id"], "name": carte["name"], "concept": carte["concept"],
            "typography": " · ".join(f"{n} {premiere_police(f[k])}" for k, n in
                                     (("display", "Titres"), ("body", "Texte"), ("number", "Chiffres"))),
            "palette": [carte["colors"][r] for r in ("bg", "surface", "text", "accent", "warn")],
            "traits": carte.get("traits") or [LAYOUTS[carte["layout"]]], "kind": "html",
            "source": f"carte-{carte['id']}.html", "controles": controles(carte["colors"])[0],
        })
    manifest = {"schemaVersion": 1, "lang": cfg["lang"], "project": cfg["project"], "brief": cfg["brief"],
                "round": cfg["round"], "candidates": candidats}
    for cle in ("question", "recommande"):
        if cle in cfg:
            manifest[cle] = cfg[cle]
    sortie.mkdir(parents=True, exist_ok=True)
    # Tout naît dans un dossier temporaire, puis remplace la sortie fichier par fichier : un échec la laisse intacte.
    with tempfile.TemporaryDirectory(prefix=".atelier-", dir=sortie) as tmp:
        etape = Path(tmp)
        for i, (carte, cand) in enumerate(zip(cfg["cards"], candidats)):
            (etape / cand["source"]).write_text(carte_html(cfg, carte, lettre_de(manifest, carte["id"])), encoding="utf-8")
        (etape / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        comparer(etape / "manifest.json", etape / page.name, force=False)
        for n in noms:
            (etape / n).replace(sortie / n)
    return {"page": str(page), "cartes": len(cfg["cards"]), "manifest": str(sortie / "manifest.json")}


# ---------------------------------------------------------------- page de comparaison

def lettre_de(manifest: dict, cid: str) -> str:
    """La lettre d'une option, comme dans la question posée : la recommandée est a), la référence actuelle n'en a pas."""
    ordre = ordonne([dict(c) for c in manifest["candidates"]], manifest.get("recommande"))
    for c in ordre:
        if c["id"] == cid:
            return c.get("lettre", "Actuel").upper()
    return "?"


def ordonne(cands: list[dict], recommande: str | None) -> list[dict]:
    cands.sort(key=lambda c: (not c.get("baseline", False), c["id"] != recommande))
    n = 0
    for c in cands:
        if not c.get("baseline"):
            c["lettre"] = "abcdefghijklmnopqrstuvwxyz"[n]
            n += 1
    return cands


class Ressources(HTMLParser):
    """Refuse toute dépendance hors de la page : la comparaison s'ouvre sans réseau, et rien ne fuit."""

    def __init__(self):
        super().__init__()
        self.styles, self.dans_style, self.head = [], False, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "head" and self.head is None:
            self.head = (self.getpos(), self.get_starttag_text())
        if tag in ("iframe", "frame", "object", "embed"):
            raise Refus("maquette : pas de document imbriqué (iframe, object, embed) ; mets le contenu ou une capture")
        if tag == "base":
            raise Refus("maquette : pas de balise base")
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "refresh":
            raise Refus("maquette : pas de redirection automatique")
        if tag == "style":
            self.dans_style = True
        if a.get("style"):
            self.styles.append(a["style"])
        for cle in ("src", "poster", "data", "href", "xlink:href"):
            v = a.get(cle) or ""
            if v and not v.startswith(("#", "data:")):
                raise Refus(f"maquette : ressource non intégrée {tag}.{cle} : {v}")
        if a.get("srcset"):
            raise Refus("maquette : un src intégré plutôt qu'un srcset")

    def handle_endtag(self, tag):
        if tag == "style":
            self.dans_style = False

    def handle_data(self, data):
        if self.dans_style:
            self.styles.append(data)


CSS_JETON = re.compile(
    r"(?P<comment>/\*.*?\*/)|(?P<string>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')"
    r"|(?P<ident>(?:[-_a-zA-Z]|\\(?:[0-9a-fA-F]{1,6}\s?|[^\r\n]))(?:[-_a-zA-Z0-9]|\\(?:[0-9a-fA-F]{1,6}\s?|[^\r\n]))*)"
    r"|(?P<space>\s+)|(?P<symbol>.)", re.S)


def css_brut(v: str) -> str:
    def rep(m):
        if m.group(1):
            n = int(m.group(1), 16)
            return chr(n) if 0 < n <= 0x10FFFF else "\ufffd"
        return m.group(2)
    return re.sub(r"\\([0-9a-fA-F]{1,6})(?:\s)?|\\([^\r\n])", rep, v)


def verifie_css(css: str, nom: str) -> None:
    """`url()`, `image-set()`, `src()` et `@import` ne pointent que vers `data:` ou `#` — échappements CSS compris."""
    jet = [(m.lastgroup, m.group()) for m in CSS_JETON.finditer(css) if m.lastgroup not in ("comment", "space")]

    def ressource(v: str):
        if not css_brut(v).strip().lower().startswith(("data:", "#")):
            raise Refus(f"{nom} : le CSS charge une ressource non intégrée")

    for i, (genre, v) in enumerate(jet):
        if v == "@" and i + 1 < len(jet) and jet[i + 1][0] == "ident" and css_brut(jet[i + 1][1]).lower() == "import":
            raise Refus(f"{nom} : intègre le CSS, sans @import")
        nomf = css_brut(v).lower() if genre == "ident" else ""
        if nomf not in ("url", "image-set", "-webkit-image-set", "image", "src") or i + 1 >= len(jet) or jet[i + 1][1] != "(":
            continue
        prof, corps = 1, []
        for g2, v2 in jet[i + 2:]:
            if g2 == "symbol" and v2 == "(":
                prof += 1
            elif g2 == "symbol" and v2 == ")":
                prof -= 1
                if prof == 0:
                    break
            if nomf == "url":
                corps.append(v2[1:-1] if g2 == "string" else v2)
            elif prof == 1 and g2 == "string":
                ressource(v2[1:-1])
        if nomf == "url":
            ressource("".join(corps))


INTEGRABLES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
               ".gif": "image/gif", ".avif": "image/avif", ".svg": "image/svg+xml", ".woff2": "font/woff2",
               ".woff": "font/woff", ".ttf": "font/ttf", ".otf": "font/otf", ".mp4": "video/mp4", ".webm": "video/webm"}
REF_ATTR = re.compile(r"""(?P<lead>\b(?:src|poster|href|xlink:href)\s*=\s*)(?P<q>["'])(?P<ref>[^"'#][^"']*)(?P=q)""")
REF_CSS = re.compile(r"""url\(\s*(?P<q>["']?)(?P<ref>[^"')\s][^"')]*)(?P=q)\s*\)""")
SCRIPT_SRC = re.compile(r"""<script\b(?P<attrs>[^>]*?)\bsrc\s*=\s*(?P<q>["'])(?P<ref>[^"']+)(?P=q)(?P<rest>[^>]*)>\s*</script>""", re.I)
LINK = re.compile(r"<link\b[^>]*>", re.I)
LINK_ATTR = re.compile(r"""\b(?P<name>rel|href)\s*=\s*(?P<q>["'])(?P<value>[^"']*)(?P=q)""", re.I)
SCHEMA = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:|^//")


def fichier_local(ref: str, base: Path, racine: Path) -> Path | None:
    if SCHEMA.match(ref):
        return None
    cible = (base / ref.split("?")[0].split("#")[0]).resolve()
    return cible if cible.is_file() and cible.is_relative_to(racine) else None


def integre_fichiers(texte: str, base: Path, racine: Path, lus: set[Path]) -> str:
    """Images, polices et vidéos en chemin relatif, dans le dossier du manifest : intégrées en `data:`."""
    def url(ref: str) -> str | None:
        cible = fichier_local(ref, base, racine)
        mime = INTEGRABLES.get(cible.suffix.lower()) if cible else None
        if not mime:
            return None
        lus.add(cible)
        return f"data:{mime};base64," + base64.b64encode(cible.read_bytes()).decode("ascii")

    def attr(m):
        u = url(m["ref"])
        return m.group(0) if u is None else f'{m["lead"]}{m["q"]}{u}{m["q"]}'

    def css(m):
        u = url(m["ref"])
        return m.group(0) if u is None else f'url("{u}")'

    return REF_CSS.sub(css, REF_ATTR.sub(attr, texte))


def integre_code(texte: str, base: Path, racine: Path, lus: set[Path], interactif: bool) -> str:
    """Feuilles de style locales intégrées ; scripts locaux intégrés pour une maquette interactive, retirés sinon."""
    def link(m):
        a = {x["name"].lower(): x["value"] for x in LINK_ATTR.finditer(m.group(0))}
        cible = fichier_local(a.get("href", ""), base, racine) if "stylesheet" in a.get("rel", "").lower() else None
        if cible is None:
            return m.group(0)
        lus.add(cible)
        css = integre_fichiers(cible.read_text(encoding="utf-8"), cible.parent, racine, lus)
        return "<style>" + css.replace("</style", "<\\/style") + "</style>"

    differes = []

    def script(m):
        cible = fichier_local(m["ref"], base, racine)
        if cible is None:
            return m.group(0)
        lus.add(cible)
        if not interactif:
            return ""
        attrs = f'{m["attrs"]} {m["rest"]}'
        code = cible.read_text(encoding="utf-8").replace("</script", "<\\/script")
        module = re.search(r"""type\s*=\s*["']module["']""", attrs, re.I)
        balise = ('<script type="module">' if module else "<script>") + code + "</script>"
        if re.search(r"\bdefer\b", attrs, re.I) and not module:  # un script intégré ignore defer : il passe en fin de body
            differes.append(balise)
            return ""
        return balise

    texte = SCRIPT_SRC.sub(script, LINK.sub(link, texte))
    if differes:
        fin = texte.lower().rfind("</body>")
        texte = texte + "".join(differes) if fin < 0 else texte[:fin] + "".join(differes) + texte[fin:]
    return texte


CSP_MAQUETTE = ("default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:; media-src data:; "
                "script-src 'none'; form-action 'none'; base-uri 'none'; object-src 'none'")
# Une maquette interactive n'a pas de stockage dans son bac à sable : un substitut en mémoire garde ses scripts en vie.
STOCKAGE = ("<script>(()=>{const mem=()=>{const m=new Map();return{get length(){return m.size},"
            "key:i=>[...m.keys()][i]??null,getItem:k=>m.has(String(k))?m.get(String(k)):null,"
            "setItem:(k,v)=>{m.set(String(k),String(v))},removeItem:k=>{m.delete(String(k))},clear:()=>m.clear()}};"
            "for(const n of['localStorage','sessionStorage']){try{window[n].length}catch{"
            "Object.defineProperty(window,n,{value:mem(),configurable:true})}}})();</script>")


def prepare_html(chemin: Path, interactif: bool, racine: Path, lus: set[Path]) -> str:
    texte = chemin.read_text(encoding="utf-8")
    texte = integre_fichiers(integre_code(texte, chemin.parent, racine, lus, interactif), chemin.parent, racine, lus)
    p = Ressources()
    p.feed(texte)
    for s in p.styles:
        verifie_css(s, chemin.name)
    if p.head is None:
        raise Refus(f"{chemin.name} : la maquette doit avoir un élément head")
    (ligne, colonne), balise = p.head
    fin_head = sum(len(x) + 1 for x in texte.split("\n")[:ligne - 1]) + colonne + len(balise)
    csp = CSP_MAQUETTE.replace("script-src 'none'", "script-src 'unsafe-inline' 'unsafe-eval'") if interactif else CSP_MAQUETTE
    return texte[:fin_head] + f'<meta http-equiv="Content-Security-Policy" content="{csp}">' + \
        (STOCKAGE if interactif else "") + texte[fin_head:]


def prepare_image(chemin: Path) -> str:
    d = chemin.read_bytes()
    mime = ("image/png" if d.startswith(b"\x89PNG\r\n\x1a\n") else "image/jpeg" if d.startswith(b"\xff\xd8\xff")
            else "image/webp" if d.startswith(b"RIFF") and d[8:12] == b"WEBP" else None)
    if not mime:
        raise Refus(f"{chemin.name} : une capture PNG, JPEG ou WebP")
    return f"data:{mime};base64," + base64.b64encode(d).decode("ascii")


LOCAL = {"localhost", "127.0.0.1", "::1"}


def url_locale(v: str, ident: str) -> str:
    try:
        p = urlsplit(v)
        p.port  # un port mal formé est refusé avant d'entrer dans la CSP
    except ValueError:
        raise Refus(f"{ident} : url doit être une adresse http(s) locale valide") from None
    if p.scheme not in ("http", "https") or (p.hostname or "").lower() not in LOCAL or p.username or p.password:
        raise Refus(f"{ident} : url ne vise qu'un serveur local, par exemple http://localhost:5173/commandes")
    return v


def texte(obj: dict, cle: str, defaut: str | None = None) -> str:
    v = obj.get(cle, defaut)
    if not isinstance(v, str) or not v.strip():
        raise Refus(f"{cle} doit être une chaîne non vide")
    return v.strip()


def charge_manifest(chemin: Path) -> tuple[dict, set[Path]]:
    try:
        brut = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Refus(f"manifest illisible {chemin} : {exc}") from None
    if not isinstance(brut, dict) or brut.get("schemaVersion") != 1:
        raise Refus("manifest.schemaVersion doit valoir 1")
    d = {"schemaVersion": 1, "project": texte(brut, "project"), "brief": texte(brut, "brief"),
         "round": texte(brut, "round", "01"), "lang": brut.get("lang", "fr"),
         "question": texte(brut, "question", "Q1")}
    if d["lang"] not in ("fr", "en"):
        raise Refus('manifest.lang doit valoir "fr" ou "en"')
    if not re.fullmatch(r"Q\d{1,2}", d["question"]):
        raise Refus("question : Q1, Q2… comme la question posée à l'utilisateur")
    if "serve" in brut:
        s = brut["serve"]
        if not isinstance(s, dict) or not isinstance(s.get("command"), str) or not s["command"].strip():
            raise Refus("serve.command doit être une chaîne non vide")
        if "cwd" in s and (not isinstance(s["cwd"], str) or not Path(s["cwd"]).is_absolute()):
            raise Refus("serve.cwd doit être un chemin absolu")
        if "url" in s:
            url_locale(texte(s, "url"), "serve")
        d["serve"] = s
    cands = brut.get("candidates")
    if not isinstance(cands, list) or not cands:
        raise Refus("candidates doit contenir au moins une option")
    vus, lus, sortie = set(), {chemin.resolve(), TEMPLATE.resolve()}, []
    racine = chemin.parent.resolve()
    for c in cands:
        if not isinstance(c, dict):
            raise Refus("chaque option doit être un objet")
        ident = texte(c, "id")
        if not ID.fullmatch(ident) or ident in vus:
            raise Refus(f"id d'option invalide ou en double : {ident}")
        vus.add(ident)
        genre, base, inter = c.get("kind", "html"), c.get("baseline", False), c.get("interactive", False)
        if genre not in ("html", "image", "url"):
            raise Refus(f"{ident} : kind inconnu : {genre}")
        if not isinstance(base, bool) or not isinstance(inter, bool):
            raise Refus(f"{ident} : baseline et interactive valent true ou false")
        if inter and genre != "html":
            raise Refus(f"{ident} : interactive ne vaut que pour une maquette html")
        if genre == "url":
            source, contenu = None, url_locale(texte(c, "url"), ident)
        else:
            source = (racine / texte(c, "source")).resolve()
            if not source.is_relative_to(racine) or not source.is_file():
                raise Refus(f"{ident} : source doit être un fichier lisible dans le dossier du manifest")
            lus.add(source)
            contenu = prepare_html(source, inter, racine, lus) if genre == "html" else prepare_image(source)
        palette = liste_texte(c, "palette", ident, requise=True)
        if any(not HEX_PALETTE.fullmatch(x) for x in palette):
            raise Refus(f"{ident} : palette attend des couleurs hexadécimales")
        sortie.append({"id": ident, **{k: texte(c, k) for k in ("name", "concept", "typography")},
                       "palette": palette, "traits": liste_texte(c, "traits", ident, requise=True),
                       "controles": liste_texte(c, "controles", ident), "kind": genre, "content": contenu,
                       "sourceLabel": contenu if genre == "url" else source.name, "baseline": base, "interactive": inter})
    if sum(c["baseline"] for c in sortie) > 1:
        raise Refus("une seule référence actuelle (baseline) au plus")
    reco = brut.get("recommande")
    if reco is not None and reco not in {c["id"] for c in sortie if not c["baseline"]}:
        raise Refus(f"recommande : `{reco}` n'est l'id d'aucune option (la référence actuelle ne se recommande pas)")
    if not any(not c["baseline"] for c in sortie):
        raise Refus("au moins une option à choisir, en plus de la référence actuelle")
    d["recommande"] = reco
    d["candidates"] = ordonne(sortie, reco)
    canon = json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    d["empreinte"] = hashlib.sha256(canon.encode("utf-8")).hexdigest()[:24]
    return d, lus


def comparer(manifest: Path, sortie: Path, *, force: bool = False) -> dict:
    manifest, sortie = manifest.resolve(), sortie.resolve()
    d, lus = charge_manifest(manifest)
    if sortie in lus or sortie.is_relative_to(SKILL):
        raise Refus("la sortie ne peut ni écraser une entrée ni être dans le dossier de Hosa")
    if sortie.exists() and not force:
        raise Refus(f"la page existe déjà : {sortie} ; --force pour la refaire")
    gabarit = TEMPLATE.read_text(encoding="utf-8")
    if gabarit.count(MARKER) != 1 or gabarit.count(CSP_MARKER) != 1:
        raise Refus("gabarit de comparaison abîmé : point d'entrée des données ou de la CSP absent ou en double")
    origines = set()
    for c in d["candidates"]:
        if c["kind"] == "url":
            p = urlsplit(c["content"])
            hote = "localhost" if p.hostname == "::1" else p.hostname.lower()  # pas d'IPv6 littéral dans une CSP
            origines.add(f"{p.scheme}://{hote}" + (f":{p.port}" if p.port else ""))
    src = " ".join(sorted(origines)) if origines else "'none'"
    csp = f"connect-src {src}; frame-src {src}; object-src 'none'; base-uri 'none'; form-action 'none'"
    # Une balise </script> dans les métadonnées ou une maquette ne peut pas sortir du conteneur de données.
    donnees = json.dumps(d, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    page = gabarit.replace(CSP_MARKER, csp).replace(MARKER, donnees)
    if force:
        ecrit_atomique(sortie, page)
    else:
        sortie.parent.mkdir(parents=True, exist_ok=True)
        with sortie.open("x", encoding="utf-8") as h:
            h.write(page)
    if origines and "serve" not in d:
        print("Rappel : des options pointent vers un serveur local ; ajoute `serve` au manifest pour pouvoir le relancer.",
              file=sys.stderr)
    return {"page": str(sortie), "options": len(d["candidates"]), "empreinte": d["empreinte"],
            "lettres": {c["id"]: c.get("lettre", "actuel") for c in d["candidates"]}}


# ---------------------------------------------------------------- choix et jetons dans la KB

CHOIX = Path("interface") / "choix.md"
LIGNE_CHOIX = re.compile(r"^\|\s*(styles|directions|page)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$", re.M)
JETON = re.compile(r"^\|\s*`(--[\w-]+)`\s*\|\s*`([^`]*)`\s*\|\s*$", re.M)
DEBUT, FIN = "/* hosa:jetons:debut — généré depuis .hosa/kb/interface/choix.md par `atelier css`, ne pas éditer */", \
    "/* hosa:jetons:fin */"


def maintenant() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def section(corps: str, titre: str) -> str | None:
    m = re.search(rf"^## {re.escape(titre)}\s*$(.*?)(?=^## |\Z)", corps, re.M | re.S)
    return m.group(1) if m else None


def lit_choix(kb: Path) -> dict:
    """{manches: {manche: (option, nom, demande, date)}, jetons: {nom: valeur}, css: chemin|None} — la dernière
    ligne d'une manche l'emporte (une manche refaite ajoute sa ligne)."""
    f = kb / CHOIX
    t = f.read_text(encoding="utf-8") if f.is_file() else ""
    manches = {}
    for m in LIGNE_CHOIX.finditer(section(t, "Manches") or ""):
        manches[m[1]] = (m[2], m[3], m[4], m[5])
    jet = dict(JETON.findall(section(t, "Jetons") or ""))
    css = re.search(r"`([^`]+)`", section(t, "Fichier CSS") or "")
    par = re.search(r"^generated:\s*\{\s*by:\s*([^,}]+)", t, re.M)
    return {"manches": manches, "jetons": jet, "css": css[1] if css else None, "existe": f.is_file(),
            "par": par[1].strip() if par else None}


def ecrit_choix(kb: Path, etat: dict, par: str) -> Path:
    cell = lambda s: (s or "—").replace("|", "/").replace("\n", " ").strip() or "—"
    lignes = [f"| {m} | {cell(o)} | {cell(n)} | {cell(d)} | {cell(t)} |"
              for m in MANCHES if m in etat["manches"] for o, n, d, t in [etat["manches"][m]]]
    jet = "\n".join(f"| `{k}` | `{v}` |" for k, v in etat["jetons"].items())
    corps = (f"---\ntype: Choix de design\ntitle: Choix de design\n"
             f'description: "L\'option retenue par l\'utilisateur à chaque manche de l\'interface, et les jetons de l\'identité"\n'
             f"tags: [ux]\ngenerated: {{ by: {par}, at: {maintenant()} }}\n---\n"
             "## Manches\n| Manche | Option | Nom | Demande de l'utilisateur | Date |\n|---|---|---|---|---|\n"
             + "\n".join(lignes) + "\n")
    if jet:
        corps += ("\n## Jetons\nLa seule définition de l'identité : `atelier css` les écrit dans le CSS du projet.\n\n"
                  "| Jeton | Valeur |\n|---|---|\n" + jet + "\n")
    if etat["css"]:
        corps += f"\n## Fichier CSS\n`{etat['css']}`\n"
    f = kb / CHOIX
    ecrit_atomique(f, corps)
    return f


def journal(kb: Path, acteur: str, verbe: str) -> None:
    """Une ligne dans `kb/interface/log.md`, sous la date du jour (OKF §9)."""
    log = kb / "interface" / "log.md"
    jour = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    t = log.read_text(encoding="utf-8") if log.is_file() else "# Log — kb/interface\n"
    ligne = f"- {acteur} a {verbe} `choix`"
    if f"\n## {jour}\n" in t:
        t = t.replace(f"\n## {jour}\n", f"\n## {jour}\n{ligne}\n", 1)
    else:  # le jour le plus récent en premier, juste sous le titre
        tete, _, reste = t.partition("\n")
        reste = reste.strip("\n")
        t = f"{tete}\n\n## {jour}\n{ligne}\n" + (f"\n{reste}\n" if reste else "")
    ecrit_atomique(log, t)


def acteur(par: str) -> str:
    par = par.strip()
    if not par:
        raise Refus("--par : le nom de l'utilisateur (git config user.name)")
    return par if par.startswith(("human:", "process:")) else "human:" + re.sub(r"\s+", "-", par)


def choisir(kb: Path, manche: str, option: str | None, depuis: Path | None, par: str, note: str | None,
            conserve: bool) -> dict:
    if not kb.is_dir():
        raise Refus(f"KB introuvable : {kb}")
    if manche not in MANCHES:
        raise Refus(f"manche : {', '.join(MANCHES)}")
    qui = acteur(par)
    etat = lit_choix(kb)
    if conserve:
        if option:
            raise Refus("--conserve garde l'existant : pas d'option à nommer")
        etat["manches"][manche] = ("conservée", "existant gardé", note or "", maintenant())
        if manche == "styles":  # l'identité existante n'a pas de jetons Hosa : rien à comparer au CSS
            etat["jetons"] = {}
    else:
        if not option or depuis is None:
            raise Refus("il faut l'id de l'option et --depuis <cartes.json|manifest.json> de la manche")
        try:
            src = json.loads(depuis.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise Refus(f"--depuis illisible : {exc}") from None
        options = src.get("cards") or src.get("candidates") or []
        trouve = next((o for o in options if isinstance(o, dict) and o.get("id") == option), None)
        if trouve is None:
            ids = ", ".join(str(o.get("id")) for o in options if isinstance(o, dict))
            raise Refus(f"option `{option}` absente de {depuis.name} ; options : {ids}")
        if trouve.get("baseline"):
            raise Refus("la référence actuelle n'est pas une option ; pour garder l'identité : --conserve")
        if manche == "styles":
            if "cards" not in src:
                raise Refus("manche styles : --depuis le fichier des cartes (cartes.json), qui porte les jetons")
            charge_cartes(depuis)  # la carte retenue passe les mêmes contrôles, contraste compris
            etat["jetons"] = jetons(trouve)
        etat["manches"][manche] = (option, str(trouve.get("name", option)), note or "", maintenant())
    f = ecrit_choix(kb, etat, qui)
    journal(kb, qui, f"noté la manche {manche} dans")
    return {"choix": str(f), "manche": manche, "option": etat["manches"][manche][0], "jetons": len(etat["jetons"])}


def bloc_css(jet: dict[str, str]) -> str:
    return DEBUT + "\n:root {\n" + "".join(f"  {k}: {v};\n" for k, v in jet.items()) + "}\n" + FIN


def racine_de(kb: Path) -> Path:
    return kb.resolve().parent.parent  # <racine>/.hosa/kb


def css(kb: Path, sortie: Path) -> dict:
    etat = lit_choix(kb)
    if not etat["jetons"]:
        raise Refus("pas de `## Jetons` dans kb/interface/choix.md : la manche styles n'a pas été choisie "
                    "(atelier choisir … styles), ou l'identité est conservée")
    racine, sortie = racine_de(kb), sortie.resolve()
    if not sortie.is_relative_to(racine):
        raise Refus(f"le fichier CSS doit être dans le projet : {racine}")
    bloc = bloc_css(etat["jetons"])
    actuel = sortie.read_text(encoding="utf-8") if sortie.is_file() else ""
    if DEBUT in actuel and FIN in actuel:
        avant, reste = actuel.split(DEBUT, 1)
        nouveau = avant + bloc + reste.split(FIN, 1)[1]
    else:
        nouveau = bloc + ("\n\n" + actuel if actuel.strip() else "\n")
    ecrit_atomique(sortie, nouveau)
    rel = sortie.relative_to(racine).as_posix()
    if etat["css"] != rel:
        etat["css"] = rel
        ecrit_choix(kb, etat, etat["par"] or "process:hosa-atelier")  # le choix reste celui de l'utilisateur
        journal(kb, "process:hosa-atelier", "noté le fichier CSS dans")
    return {"css": str(sortie), "jetons": len(etat["jetons"])}


def ecarts(kb: Path) -> list[str]:
    """Les jetons de la KB sont-ils ceux du CSS du projet ? Rien à contrôler sans jetons (identité conservée)."""
    etat = lit_choix(kb)
    if not etat["jetons"]:
        return []
    if not etat["css"]:
        return ["jetons de l'identité non appliqués : lance `<hosa> atelier css .hosa/kb --out <fichier CSS du projet>`"]
    f = racine_de(kb) / etat["css"]
    t = f.read_text(encoding="utf-8", errors="replace") if f.is_file() else ""
    if DEBUT not in t or FIN not in t:
        return [f"`{etat['css']}` ne porte plus le bloc des jetons : relance `<hosa> atelier css`"]
    present = DEBUT + t.split(DEBUT, 1)[1].split(FIN, 1)[0] + FIN
    if present != bloc_css(etat["jetons"]):
        return [f"`{etat['css']}` : les jetons ont été édités à la main ; change l'identité dans la KB "
                "(atelier choisir), puis relance `<hosa> atelier css`"]
    return []


# ---------------------------------------------------------------- ligne de commande

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="atelier", description="Atelier de design de Hosa")
    sous = p.add_subparsers(dest="cmd", required=True)
    a = sous.add_parser("cartes", help="cartes de style et page de comparaison")
    a.add_argument("config", type=Path)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--force", action="store_true")
    a = sous.add_parser("comparer", help="page de comparaison d'un manifest")
    a.add_argument("manifest", type=Path)
    a.add_argument("--out", "--output", dest="out", type=Path, required=True)
    a.add_argument("--force", action="store_true")
    a = sous.add_parser("choisir", help="noter le choix d'une manche dans la KB")
    a.add_argument("kb", type=Path)
    a.add_argument("manche")
    a.add_argument("option", nargs="?")
    a.add_argument("--depuis", type=Path)
    a.add_argument("--par", required=True)
    a.add_argument("--note")
    a.add_argument("--conserve", action="store_true")
    a = sous.add_parser("css", help="écrire les jetons dans le CSS du projet")
    a.add_argument("kb", type=Path)
    a.add_argument("--out", type=Path, required=True)
    a = sous.add_parser("ecart", help="le CSS du projet porte-t-il les jetons de la KB ?")
    a.add_argument("kb", type=Path)
    x = p.parse_args(argv)
    try:
        if x.cmd == "cartes":
            r = cartes(x.config, x.out, x.force)
        elif x.cmd == "comparer":
            r = comparer(x.manifest, x.out, force=x.force)
        elif x.cmd == "choisir":
            r = choisir(x.kb, x.manche, x.option, x.depuis, x.par, x.note, x.conserve)
        elif x.cmd == "css":
            r = css(x.kb, x.out)
        else:
            manques = ecarts(x.kb)
            for m in manques:
                print(f"✗ {m}")
            print("✓ le CSS porte les jetons de la KB" if not manques else f"{len(manques)} écart(s)")
            return 1 if manques else 0
    except (Refus, OSError) as exc:
        print(f"atelier {x.cmd} refusé : {exc}", file=sys.stderr)
        return 1
    print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    # UTF-8 quelle que soit la page de code de la console (Windows : cp1252).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
