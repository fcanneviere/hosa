#!/usr/bin/env python3
"""Atelier de design de Hosa : cartes de style, page de comparaison, choix de l'utilisateur, jetons.

  atelier.py cartes   <cartes.json> --out <dossier> [--force]
      Valide les cartes (contraste WCAG AA calculé pour chaque paire de couleurs affichée, avec une couleur proposée
      pour chaque paire refusée), dessine une carte par identité sur le même contenu réel, et la page `comparaison.html`.
  atelier.py comparer <manifest.json> --out <page.html> [--force]
      Assemble des maquettes locales (html, image, adresse locale) en une page de comparaison autonome, sans réseau.
  atelier.py choisir  <kb> <manche> <id> --depuis <cartes.json|manifest.json> --par <utilisateur> [--note "…"]
  atelier.py choisir  <kb> <manche> --conserve --par <utilisateur> [--note "…"]
      Écrit le choix de la manche dans `kb/interface/choix.md` ; pour `styles`, aussi les jetons de la carte.
      `--conserve` : l'utilisateur garde l'existant pour cette manche (interface à compléter, manches d'avant Hosa).
  atelier.py css      <kb> --out <fichier>
      Écrit les jetons de `kb/interface/choix.md` en variables CSS (bloc marqué) et note le fichier dans la KB.
  atelier.py ecart    <kb>
      Contrôle que le fichier CSS du projet porte toujours les jetons de la KB.

Formats d'entrée : `version: 2` ; l'exemple complet est `assets/exemple-cartes.json`.
Sortie : une ligne JSON (succès) ou les manques exacts, un par ligne. Code : 0 réussi, 1 refusé, 2 mauvais appel.
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
from urllib.parse import unquote, urlsplit

ICI = Path(__file__).resolve().parent
SKILL = ICI.parent
TEMPLATE = SKILL / "assets" / "comparaison.html"
MARKER = "/*__ATELIER_DONNEES__*/null"
CSP_MARKER = "__ATELIER_CSP__"
MANCHES = ("styles", "directions", "page")
VERSION = 2


class Refus(ValueError):
    """Une entrée refusée : le message dit exactement quoi corriger."""


def lit_json(chemin: Path, quoi: str) -> dict:
    try:
        brut = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Refus(f"{quoi} illisible {chemin} : {exc}") from None
    if not isinstance(brut, dict):
        raise Refus(f"{quoi} : la racine doit être un objet")
    if brut.get("version") != VERSION:
        ancien = any(k in brut for k in ("schemaVersion", "cards", "candidates"))
        raise Refus(f"{quoi} : `\"version\": {VERSION}` attendu"
                    + (" ; ce fichier suit l'ancien format : réécris-le comme assets/exemple-cartes.json "
                       "(cartes) ou comme le manifest décrit dans agents/ux-designer.md" if ancien else ""))
    return brut


def chaine(obj: dict, cle: str, ou: str, defaut: str | None = None) -> str:
    v = obj.get(cle, defaut)
    if not isinstance(v, str) or not v.strip():
        raise Refus(f"{ou}.{cle} : une chaîne non vide")
    return v.strip()


def chaines(obj: dict, cle: str, ou: str, *, requise: bool = False) -> list[str]:
    v = obj.get(cle)
    if v is None and not requise:
        return []
    if not isinstance(v, list) or (requise and not v) or not all(isinstance(t, str) and t.strip() for t in v):
        raise Refus(f"{ou}.{cle} : une liste {'non vide ' if requise else ''}de chaînes non vides")
    return [t.strip() for t in v]


def objet(obj: dict, cle: str, ou: str) -> dict:
    v = obj.get(cle)
    if not isinstance(v, dict):
        raise Refus(f"{ou}.{cle} : un objet")
    return v


def parmi(obj: dict, cle: str, ou: str, choix, defaut=None) -> str:
    v = obj.get(cle, defaut)
    if v not in choix:
        raise Refus(f"{ou}.{cle} doit valoir : {', '.join(choix)}")
    return v


def entier(obj: dict, cle: str, ou: str, bas: int, haut: int, defaut: int) -> int:
    v = obj.get(cle, defaut)
    if type(v) is not int or not bas <= v <= haut:
        raise Refus(f"{ou}.{cle} : un entier de {bas} à {haut}")
    return v


# ---------------------------------------------------------------- couleurs et contraste (WCAG 2.2)

HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})")
HEX_PALETTE = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})")
COULEURS = {"fond": "Fond", "surface": "Surface", "texte": "Texte", "secondaire": "Texte secondaire",
            "accent": "Accent", "sur_accent": "Texte sur accent", "trait": "Trait", "alerte": "Alerte"}
TEINTE = 0.12  # part de la couleur dans le fond d'une étiquette : `color-mix(in srgb, couleur 12%, surface)`


def canaux(hexa: str) -> tuple[int, int, int]:
    h = hexa.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(a: str, b: str, part_a: float) -> str:
    """Le mélange sRGB que le navigateur calcule pour `color-mix(in srgb, a part_a, b)`."""
    return "#" + "".join(f"{round(x * part_a + y * (1 - part_a)):02x}" for x, y in zip(canaux(a), canaux(b)))


def luminance(hexa: str) -> float:
    lin = [(c / 255) / 12.92 if c <= 10 else (((c / 255) + 0.055) / 1.055) ** 2.4 for c in canaux(hexa)]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contraste(a: str, b: str) -> float:
    clair, sombre = max(luminance(a), luminance(b)), min(luminance(a), luminance(b))
    return (clair + 0.05) / (sombre + 0.05)


def proposition(avant: str, arriere: str, mini: float) -> str | None:
    """La couleur la plus proche de `avant`, même teinte, qui tient `mini` sur `arriere` : poussée vers le noir
    ou le blanc, le premier pas qui passe."""
    for pas in range(1, 51):
        for pole in ("#000000", "#ffffff"):
            essai = mix(pole, avant, pas / 50)
            if contraste(essai, arriere) >= mini:
                return essai.upper()
    return None


def paires(c: dict) -> list[tuple[str, str, str, float]]:
    """Chaque paire de couleurs que la carte et l'interface montrent, avec son minimum WCAG AA :
    4,5:1 pour du texte (1.4.3), 3:1 pour un composant ou un indicateur de focus (1.4.11)."""
    etiquette = mix(c["accent"], c["surface"], TEINTE)
    etiquette_alerte = mix(c["alerte"], c["surface"], TEINTE)
    return [
        ("texte sur fond", c["texte"], c["fond"], 4.5),
        ("texte sur surface", c["texte"], c["surface"], 4.5),
        ("texte secondaire sur fond", c["secondaire"], c["fond"], 4.5),
        ("texte secondaire sur surface (et contour des champs)", c["secondaire"], c["surface"], 4.5),
        ("texte sur accent (bouton principal, menu actif)", c["sur_accent"], c["accent"], 4.5),
        ("accent sur fond (bouton, lien, focus)", c["accent"], c["fond"], 3.0),
        ("accent sur surface (lien, focus dans un cadre)", c["accent"], c["surface"], 3.0),
        ("alerte sur surface", c["alerte"], c["surface"], 4.5),
        ("accent sur son étiquette", c["accent"], etiquette, 4.5),
        ("alerte sur son étiquette", c["alerte"], etiquette_alerte, 4.5),
    ]


def controles(c: dict) -> tuple[list[str], list[str]]:
    """(une ligne par paire avec son rapport, un manque par paire sous son minimum avec une couleur proposée)."""
    lignes, manques = [], []
    for nom, avant, arriere, mini in paires(c):
        r = contraste(avant, arriere)
        lignes.append(f"{nom} {r:.1f}:1 {'✓' if r >= mini else '✗'}".replace(".", ","))
        if r < mini:
            p = proposition(avant, arriere, mini)
            manques.append(f"{nom} : {avant.upper()} sur {arriere.upper()} = {r:.2f}:1, il faut {mini:g}:1"
                           + (f" (proposition : {p})" if p else ""))
    return lignes, manques


# ---------------------------------------------------------------- cartes de style

# rythme : (espace entre blocs, marge verticale, marge horizontale des contrôles, échelle des titres)
RYTHMES = {"serre": (8, 6, 12, 0.94), "normal": (14, 9, 16, 1.0), "ample": (22, 12, 22, 1.06)}
RELIEFS = ("aucun", "trait", "contour", "ombre")
ECRANS = {
    "tableau": "Menu latéral et tableau",
    "liste-detail": "Liste et fiche de détail",
    "tuiles": "Menu haut et tuiles",
    "accueil": "Accueil : titre, actions, aperçus",
    "tableau-de-bord": "Tableau de bord : indicateurs, puis ce qui est à traiter",
}
POLICES = {"titres": "Titres", "texte": "Texte", "chiffres": "Chiffres"}
FAMILLE = re.compile(r"\"[^\"\\]+\"|'[^'\\]+'|[\w -]+")
ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")


def police(pile: str, ou: str) -> None:
    """Des familles installées, séparées par des virgules : rien qui charge une police par le réseau."""
    for famille in pile.split(","):
        famille = famille.strip()
        if not famille or not FAMILLE.fullmatch(famille) or not famille.strip("\"' "):
            raise Refus(f"{ou} : des noms de polices installées, entre guillemets s'ils ont des espaces ; "
                        f"pas de police réseau : {pile}")


def charge_cartes(chemin: Path) -> dict:
    cfg = lit_json(chemin, "cartes")
    for cle, defaut in (("projet", None), ("manche", "Cartes de style"),
                        ("intention", "Comparer couleurs, typographie, contrôles et premier écran sur le même contenu")):
        cfg[cle] = chaine(cfg, cle, "cartes", defaut)
    cfg["langue"] = parmi(cfg, "langue", "cartes", ("fr", "en"), "fr")
    c = objet(cfg, "contenu", "cartes")
    for cle in ("titre", "texte", "chiffre", "legende", "action", "action_secondaire"):
        chaine(c, cle, "contenu")
    chaines(c, "etiquettes", "contenu")
    if "champ" in c:
        champ = objet(c, "champ", "contenu")
        chaine(champ, "libelle", "contenu.champ")
        chaine(champ, "valeur", "contenu.champ")
    ecran = objet(c, "ecran", "contenu")
    chaines(ecran, "menu", "contenu.ecran", requise=True)
    colonnes = chaines(ecran, "colonnes", "contenu.ecran", requise=True)
    lignes = ecran.get("lignes")
    if not isinstance(lignes, list) or not lignes or not all(
            isinstance(r, list) and len(r) == len(colonnes) and all(isinstance(x, str) for x in r) for r in lignes):
        raise Refus(f"contenu.ecran.lignes : une liste de lignes de {len(colonnes)} chaînes, comme `colonnes`")
    if "indicateurs" in c:
        inds = c["indicateurs"]
        if not isinstance(inds, list) or not 2 <= len(inds) <= 4:
            raise Refus("contenu.indicateurs : 2 à 4 indicateurs, ceux du cahier des charges (`INn`)")
        for k, ind in enumerate(inds, 1):
            if not isinstance(ind, dict):
                raise Refus(f"contenu.indicateurs[{k}] : un objet {{libelle, valeur, evolution, serie}}")
            for cle in ("libelle", "valeur"):
                chaine(ind, cle, f"contenu.indicateurs[{k}]")
            if "evolution" in ind:
                chaine(ind, "evolution", f"contenu.indicateurs[{k}]")
            serie = ind.get("serie", [])
            if not isinstance(serie, list) or (serie and (len(serie) < 2 or not all(
                    type(x) in (int, float) for x in serie))):
                raise Refus(f"contenu.indicateurs[{k}].serie : au moins deux nombres, du plus ancien au plus récent")
    cartes = cfg.get("cartes")
    if not isinstance(cartes, list) or not 2 <= len(cartes) <= 6:
        raise Refus(f"cartes : 2 à 6 cartes, il y en a {len(cartes) if isinstance(cartes, list) else 0}")
    vus, manques = set(), []
    for i, carte in enumerate(cartes, 1):
        if not isinstance(carte, dict):
            raise Refus(f"carte {i} : un objet")
        if "contenu" in carte:
            raise Refus(f"carte {i}.contenu : toutes les cartes montrent le même contenu, celui de la racine")
        cid = chaine(carte, "id", f"carte {i}")
        if not ID.fullmatch(cid) or cid in vus:
            raise Refus(f"carte {i} : id invalide ou en double : {cid}")
        vus.add(cid)
        ou = f"carte {cid}"
        chaine(carte, "nom", ou)
        chaine(carte, "intention", ou)
        chaines(carte, "traits", ou)
        col = objet(carte, "couleurs", ou)
        for role in COULEURS:
            v = chaine(col, role, f"{ou}.couleurs")
            if not HEX.fullmatch(v):
                raise Refus(f"{ou}.couleurs.{role} : une couleur hexadécimale #RGB ou #RRGGBB : {v}")
        pol = objet(carte, "polices", ou)
        for role in POLICES:
            police(chaine(pol, role, f"{ou}.polices"), f"{ou}.polices.{role}")
        graisses = carte.setdefault("graisses", {})
        if not isinstance(graisses, dict):
            raise Refus(f"{ou}.graisses : un objet {{titres, chiffres}}")
        for role, defaut in (("titres", 600), ("chiffres", 500)):
            graisses[role] = entier(graisses, role, f"{ou}.graisses", 300, 900, defaut)
        carte["arrondi"] = entier(carte, "arrondi", ou, 0, 24, 6)
        carte["relief"] = parmi(carte, "relief", ou, RELIEFS, "trait")
        carte["rythme"] = parmi(carte, "rythme", ou, tuple(RYTHMES), "normal")
        carte["ecran"] = parmi(carte, "ecran", ou, tuple(ECRANS))
        if carte["ecran"] == "tableau-de-bord" and "indicateurs" not in c:
            raise Refus(f"{ou}.ecran : un tableau de bord montre de vrais indicateurs — ajoute `contenu.indicateurs`")
        manques +=[f"{ou} — {m}" for m in controles(col)[1]]
    if manques:
        raise Refus("contraste WCAG AA insuffisant, corrige ces couleurs :\n" + "\n".join(manques))
    return cfg


def famille(pile: str) -> str:
    return pile.split(",")[0].strip().strip("\"'")


def jetons(carte: dict) -> dict[str, str]:
    """Les jetons de l'identité, nommés comme dans le CSS du projet : la seule définition, de la carte au code."""
    c, p = carte["couleurs"], carte["polices"]
    espace, vy, vx, echelle = RYTHMES[carte.get("rythme", "normal")]
    relief = carte.get("relief", "trait")
    bordure = {"aucun": "0 solid transparent", "trait": f"1px solid {c['trait']}",
               "contour": f"2px solid {c['texte']}", "ombre": "1px solid transparent"}[relief]
    ombre = "0 1px 2px rgb(0 0 0 / .06), 0 4px 16px rgb(0 0 0 / .08)" if relief == "ombre" else "none"
    g = carte.get("graisses", {})
    return {
        "--color-bg": c["fond"], "--color-surface": c["surface"], "--color-text": c["texte"],
        "--color-muted": c["secondaire"], "--color-accent": c["accent"], "--color-on-accent": c["sur_accent"],
        "--color-line": c["trait"], "--color-warn": c["alerte"],
        "--font-display": p["titres"], "--font-body": p["texte"], "--font-number": p["chiffres"],
        "--weight-display": str(g.get("titres", 600)), "--weight-number": str(g.get("chiffres", 500)),
        "--font-size-base": f"{round(15 * echelle)}px", "--radius": f"{carte.get('arrondi', 6)}px",
        "--border": bordure, "--shadow": ombre,
        "--space-gap": f"{espace}px", "--space-y": f"{vy}px", "--space-x": f"{vx}px",
        "--focus-ring": f"2px solid {c['accent']}",
    }


def courbe(serie: list[float]) -> str:
    """L'évolution d'un indicateur en une ligne SVG, à la couleur d'accent ; rien sans série."""
    if len(serie) < 2:
        return ""
    bas, haut = min(serie), max(serie)
    etendue = (haut - bas) or 1
    points = " ".join(f"{round(k * 100 / (len(serie) - 1), 1)},{round(22 - (v - bas) * 20 / etendue, 1)}"
                      for k, v in enumerate(serie))
    return (f'<svg class="e-courbe" viewBox="0 0 100 24" preserveAspectRatio="none" aria-hidden="true">'
            f'<polyline points="{points}" fill="none" stroke="var(--color-accent)" stroke-width="2" '
            f'vector-effect="non-scaling-stroke"/></svg>')


def ecran_html(carte: dict, c: dict) -> str:
    """Le premier écran dans cette identité, avec le vrai menu, les vraies colonnes et les vraies lignes."""
    e = lambda s: html.escape(str(s))
    ec = c["ecran"]
    menu = "".join(f'<li{" class=actif" if i == 0 else ""}>{e(m)}</li>' for i, m in enumerate(ec["menu"]))
    lignes = ec["lignes"][:6]
    bouton = f'<span class="e-btn">{e(c["action"])}</span>'
    if carte["ecran"] == "tableau":
        tete = "".join(f"<th>{e(x)}</th>" for x in ec["colonnes"])
        corps = "".join("<tr>" + "".join(f"<td>{e(x)}</td>" for x in r) + "</tr>" for r in lignes)
        return (f'<div class="e e-cote"><ul class="e-menu">{menu}</ul><div class="e-corps">'
                f'<div class="e-barre"><b>{e(ec["menu"][0])}</b>{bouton}</div>'
                f"<table><thead><tr>{tete}</tr></thead><tbody>{corps}</tbody></table></div></div>")
    if carte["ecran"] == "liste-detail":
        liste = "".join(f'<li{" class=actif" if i == 0 else ""}><b>{e(r[0])}</b><small>{e(" · ".join(r[1:3]))}</small></li>'
                        for i, r in enumerate(lignes))
        fiche = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in zip(ec["colonnes"], lignes[0]))
        return (f'<div class="e e-cote"><ul class="e-liste">{liste}</ul><div class="e-corps">'
                f'<div class="e-barre"><b>{e(lignes[0][0])}</b>{bouton}</div><dl>{fiche}</dl></div></div>')
    if carte["ecran"] == "tableau-de-bord":
        tuiles = "".join(
            f'<div class="e-ind"><small>{e(i["libelle"])}</small><b>{e(i["valeur"])}</b>'
            + (f'<small>{e(i["evolution"])}</small>' if i.get("evolution") else "")
            + courbe(i.get("serie", [])) + "</div>" for i in c["indicateurs"])
        tete = "".join(f"<th>{e(x)}</th>" for x in ec["colonnes"])
        corps = "".join("<tr>" + "".join(f"<td>{e(x)}</td>" for x in r) + "</tr>" for r in lignes[:3])
        return (f'<div class="e e-cote"><ul class="e-menu">{menu}</ul><div class="e-corps">'
                f'<div class="e-inds">{tuiles}</div><div class="e-barre"><b>À traiter</b>{bouton}</div>'
                f"<table><thead><tr>{tete}</tr></thead><tbody>{corps}</tbody></table></div></div>")
    haut = f'<ul class="e-menu e-haut">{menu}</ul>'
    tuile = lambda r: f'<div class="e-tuile"><b>{e(r[0])}</b><small>{e(" · ".join(r[1:]))}</small></div>'
    if carte["ecran"] == "tuiles":
        return f'<div class="e">{haut}<div class="e-corps"><div class="e-tuiles">{"".join(tuile(r) for r in lignes)}</div></div></div>'
    return (f'<div class="e">{haut}<div class="e-corps e-accueil"><b class="e-titre">{e(c["titre"])}</b>'
            f'<span>{e(c["texte"])}</span><div class="e-actions">{bouton}<span class="e-btn e-btn2">'
            f'{e(c["action_secondaire"])}</span></div><div class="e-tuiles">{"".join(tuile(r) for r in lignes[:3])}</div></div></div>')


def carte_html(cfg: dict, carte: dict, lettre: str) -> str:
    e = lambda s: html.escape(str(s))
    c, col, pol = cfg["contenu"], carte["couleurs"], carte["polices"]
    k = RYTHMES[carte["rythme"]][3]
    racine = ";".join(f"{n}:{v}" for n, v in jetons(carte).items())
    lignes, _ = controles(col)
    nuancier = "".join(f'<div class="nuance"><i style="background:{col[r]}"></i><b>{COULEURS[r]}</b><code>{col[r].upper()}</code></div>'
                       for r in ("fond", "surface", "texte", "secondaire", "accent", "sur_accent", "trait", "alerte"))
    polices = "".join(f"<li><b>{n}</b> {e(famille(pol[r]))}</li>" for r, n in POLICES.items())
    etiquettes = "".join(f'<span class="etiquette{" alerte" if i else ""}">{e(t)}</span>'
                         for i, t in enumerate(c.get("etiquettes", [])[:2]))
    champ = (f'<label class="champ">{e(c["champ"]["libelle"])}<span>{e(c["champ"]["valeur"])}</span></label>'
             if c.get("champ") else "")
    traits = "".join(f"<li>{e(t)}</li>" for t in carte.get("traits", []))
    contr = "".join(f"<li>{e(x)}</li>" for x in lignes)
    return f"""<!doctype html>
<html lang="{cfg['langue']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(carte['nom'])}</title><style>
:root{{{racine}}}
*,*::before,*::after{{box-sizing:border-box}}
body{{margin:0;background:var(--color-bg);color:var(--color-text);font:var(--font-size-base)/1.5 var(--font-body)}}
.carte{{max-width:1180px;margin:0 auto;padding:28px 36px 40px;display:grid;gap:calc(var(--space-gap) * 2)}}
.entete{{display:flex;align-items:baseline;gap:16px;border-bottom:1px solid var(--color-line);padding-bottom:12px}}
.entete strong{{font:var(--weight-display) 18px/1.2 var(--font-display)}}
.entete span{{margin-left:auto;color:var(--color-muted);font-size:13px}}
.rub{{margin:0 0 10px;font:600 11px/1 var(--font-body);letter-spacing:.08em;text-transform:uppercase;color:var(--color-muted)}}
.duo{{display:grid;grid-template-columns:3fr 2fr;gap:40px}}
.titre{{margin:0;font:var(--weight-display) {round(36 * k)}px/1.15 var(--font-display);text-wrap:balance}}
.texte{{margin:10px 0 0;max-width:34em;color:var(--color-muted)}}
.chiffre{{margin-top:18px;font:var(--weight-number) {round(50 * k)}px/1 var(--font-number);font-variant-numeric:tabular-nums}}
.legende{{color:var(--color-muted);font-size:13px}}
.nuancier{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
.nuance i{{display:block;height:40px;border-radius:var(--radius);border:1px solid rgb(0 0 0 / .1)}}
.nuance b{{display:block;margin-top:4px;font-size:12px;font-weight:500}}
.nuance code{{font:11px ui-monospace,Menlo,Consolas,monospace;color:var(--color-muted)}}
.polices,.contrastes,.traits{{list-style:none;margin:12px 0 0;padding:0;font-size:12px;color:var(--color-muted)}}
.polices b{{display:inline-block;width:5.5em;color:var(--color-text);font-weight:500}}
.contrastes{{display:grid;grid-template-columns:1fr 1fr;gap:2px 16px}}
.controles{{display:flex;flex-wrap:wrap;align-items:flex-end;gap:var(--space-gap)}}
.btn{{font:500 14px/1 var(--font-body);padding:var(--space-y) var(--space-x);border-radius:var(--radius);border:var(--border);box-shadow:var(--shadow);background:var(--color-surface);color:var(--color-text)}}
.btn-principal{{background:var(--color-accent);border-color:var(--color-accent);color:var(--color-on-accent)}}
.btn-focus{{outline:var(--focus-ring);outline-offset:2px}}
.etiquette{{font-size:12px;padding:3px 10px;border-radius:999px;background:color-mix(in srgb,var(--color-accent) 12%,var(--color-surface));color:var(--color-accent)}}
.etiquette.alerte{{background:color-mix(in srgb,var(--color-warn) 12%,var(--color-surface));color:var(--color-warn)}}
.champ{{display:grid;gap:4px;margin-left:auto;font-size:12px;color:var(--color-muted)}}
.champ span{{min-width:220px;padding:var(--space-y) 12px;border:1px solid var(--color-muted);border-radius:var(--radius);background:var(--color-surface);color:var(--color-text);font-size:14px}}
.intention p{{margin:0;max-width:44em}}
.traits{{display:flex;flex-wrap:wrap;gap:6px}}
.traits li{{padding:2px 9px;border:1px solid var(--color-line);border-radius:999px}}
.cadre{{height:300px;overflow:hidden;border:var(--border);box-shadow:var(--shadow);border-radius:var(--radius);background:var(--color-surface);font-size:13px}}
.e{{height:100%;display:flex;flex-direction:column}} .e-cote{{flex-direction:row}}
.e-menu,.e-liste{{list-style:none;margin:0;padding:10px 8px;display:flex;flex-direction:column;gap:2px;width:24%;background:color-mix(in srgb,var(--color-text) 5%,var(--color-surface))}}
.e-menu li{{padding:5px 9px;border-radius:calc(var(--radius) / 2);color:var(--color-muted)}}
.e-menu li.actif{{background:var(--color-accent);color:var(--color-on-accent)}}
.e-haut{{width:auto;flex-direction:row;padding:8px 12px;border-bottom:1px solid var(--color-line)}}
.e-liste{{width:38%;padding:0;gap:0;background:none;border-right:1px solid var(--color-line)}}
.e-liste li{{display:flex;flex-direction:column;padding:8px 12px;border-bottom:1px solid var(--color-line)}}
.e-liste li.actif{{background:color-mix(in srgb,var(--color-accent) 12%,var(--color-surface))}}
.e-liste small,.e-tuile small{{color:var(--color-muted)}}
.e-corps{{flex:1;min-width:0;padding:12px 14px;display:flex;flex-direction:column;gap:10px}}
.e-barre{{display:flex;align-items:center;justify-content:space-between}}
.e-barre b,.e-titre{{font:var(--weight-display) 16px/1.2 var(--font-display)}}
.e-btn{{align-self:flex-start;padding:5px 11px;border-radius:var(--radius);background:var(--color-accent);color:var(--color-on-accent);font-weight:500}}
.e-btn2{{background:none;color:var(--color-text);border:var(--border)}}
.e-actions{{display:flex;gap:8px}} .e-accueil>span{{color:var(--color-muted)}}
table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}}
th{{text-align:left;font-weight:500;color:var(--color-muted);padding:5px 6px;border-bottom:1px solid var(--color-muted)}}
td{{padding:5px 6px;border-bottom:1px solid var(--color-line);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:130px}}
dl{{margin:0;display:grid;grid-template-columns:auto 1fr;gap:4px 14px}} dt{{color:var(--color-muted)}} dd{{margin:0}}
.e-tuiles{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}
.e-tuile{{display:flex;flex-direction:column;gap:2px;padding:9px;border:var(--border);border-radius:var(--radius);background:var(--color-bg)}}
.e-inds{{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px}}
.e-ind{{display:flex;flex-direction:column;gap:1px;padding:8px 10px;border:var(--border);border-radius:var(--radius);background:var(--color-bg)}}
.e-ind small{{color:var(--color-muted)}} .e-ind b{{font:var(--weight-number) 22px/1.1 var(--font-number);font-variant-numeric:tabular-nums}}
.e-courbe{{width:100%;height:20px;margin-top:4px}}
@media (max-width:760px){{.carte{{padding:20px 16px}}.duo{{grid-template-columns:1fr}}.champ{{margin-left:0}}}}
</style></head><body><main class="carte">
<header class="entete"><strong>{e(cfg['projet'])}</strong><span>{e(lettre)} · {e(carte['nom'])}</span></header>
<section><h2 class="rub">Premier écran · {e(ECRANS[carte['ecran']])}</h2><div class="cadre">{ecran_html(carte, c)}</div></section>
<section class="duo"><div><h2 class="rub">Typographie et chiffres</h2><h1 class="titre">{e(c['titre'])}</h1><p class="texte">{e(c['texte'])}</p>
<div class="chiffre">{e(c['chiffre'])}</div><span class="legende">{e(c['legende'])}</span><ul class="polices">{polices}</ul></div>
<div><h2 class="rub">Couleurs et contrastes</h2><div class="nuancier">{nuancier}</div><ul class="contrastes">{contr}</ul></div></section>
<section><h2 class="rub">Contrôles</h2><div class="controles"><button class="btn btn-principal">{e(c['action'])}</button>
<button class="btn">{e(c['action_secondaire'])}</button><button class="btn btn-focus">Focus clavier</button>{etiquettes}{champ}</div></section>
<section class="intention"><h2 class="rub">Intention</h2><p>{e(carte['intention'])}</p><ul class="traits">{traits}</ul></section>
</main></body></html>
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
    noms = [f"carte-{c['id']}.html" for c in cfg["cartes"]] + ["manifest.json", page.name]
    if cfg_chemin.parent == sortie and cfg_chemin.name in noms:
        raise Refus(f"la configuration serait écrasée par la sortie, renomme-la : {cfg_chemin}")
    for n in noms:
        if (sortie / n).is_symlink() or ((sortie / n).exists() and not (sortie / n).is_file()):
            raise Refus(f"un fichier de sortie ne peut être ni un dossier ni un lien : {sortie / n}")
    options = [{
        "id": carte["id"], "nom": carte["nom"], "intention": carte["intention"],
        "typographie": " · ".join(f"{n} {famille(carte['polices'][r])}" for r, n in POLICES.items()),
        "palette": [carte["couleurs"][r] for r in ("fond", "surface", "texte", "accent", "alerte")],
        "traits": carte.get("traits") or [ECRANS[carte["ecran"]]], "genre": "html",
        "fichier": f"carte-{carte['id']}.html", "controles": controles(carte["couleurs"])[0],
    } for carte in cfg["cartes"]]
    manifest = {"version": VERSION, "langue": cfg["langue"], "projet": cfg["projet"], "intention": cfg["intention"],
                "manche": cfg["manche"], "options": options}
    for cle in ("question", "recommande"):
        if cle in cfg:
            manifest[cle] = cfg[cle]
    lettres = {o["id"]: o.get("lettre", "actuel") for o in ordonne([dict(o) for o in options], cfg.get("recommande"))}
    sortie.mkdir(parents=True, exist_ok=True)
    # Tout naît dans un dossier temporaire, puis remplace la sortie fichier par fichier : un échec la laisse intacte.
    with tempfile.TemporaryDirectory(prefix=".atelier-", dir=sortie) as tmp:
        etape = Path(tmp)
        for carte, o in zip(cfg["cartes"], options):
            (etape / o["fichier"]).write_text(carte_html(cfg, carte, lettres[carte["id"]].upper()), encoding="utf-8")
        (etape / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        comparer(etape / "manifest.json", etape / page.name, force=False)
        for n in noms:
            (etape / n).replace(sortie / n)
    return {"page": str(page), "cartes": len(cfg["cartes"]), "manifest": str(sortie / "manifest.json")}


# ---------------------------------------------------------------- maquettes : un document autonome, sans réseau

INTEGRABLES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
               ".gif": "image/gif", ".avif": "image/avif", ".svg": "image/svg+xml", ".ico": "image/x-icon",
               ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".otf": "font/otf",
               ".mp4": "video/mp4", ".webm": "video/webm", ".vtt": "text/vtt"}
CSP_MAQUETTE = ("default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:; media-src data:; "
                "script-src {scripts}; form-action 'none'; base-uri 'none'; object-src 'none'")
# Une maquette interactive tourne dans un bac à sable sans stockage : `localStorage` y lève une erreur. Ce substitut
# en mémoire répond comme le vrai, y compris l'accès par propriété (`localStorage.jeton = 1`).
STOCKAGE = """<script>(()=>{const memoire=()=>{const m=new Map(),api={get length(){return m.size},
key(i){return[...m.keys()][i]??null},getItem(k){k=String(k);return m.has(k)?m.get(k):null},
setItem(k,v){m.set(String(k),String(v))},removeItem(k){m.delete(String(k))},clear(){m.clear()}};
return new Proxy(api,{get:(t,p)=>p in t?t[p]:typeof p==="string"&&m.has(p)?m.get(p):undefined,
set:(t,p,v)=>{if(p in t)return false;m.set(String(p),String(v));return true},
deleteProperty:(t,p)=>{m.delete(String(p));return true},has:(t,p)=>p in t||m.has(String(p)),
ownKeys:()=>[...m.keys()],getOwnPropertyDescriptor:(t,p)=>m.has(String(p))?
{value:m.get(String(p)),writable:true,enumerable:true,configurable:true}:undefined})};
for(const nom of["localStorage","sessionStorage"]){let ok=false;try{ok=!!window[nom]}catch{}
if(!ok)Object.defineProperty(window,nom,{value:memoire(),configurable:true})}})();</script>""".replace("\n", "")
INTERDITS = {"iframe": "pas de document imbriqué (iframe) : mets son contenu ou une capture",
             "frame": "pas de cadre (frame)", "frameset": "pas de cadres (frameset)",
             "object": "pas d'objet externe (object) : une image ou une capture",
             "embed": "pas d'objet externe (embed) : une image ou une capture",
             "portal": "pas de portail (portal)", "base": "pas de balise base : les chemins restent relatifs à la maquette"}
ATTR_RESSOURCE = {"src", "poster", "data", "background", "xlink:href", "lowsrc", "ping", "manifest", "icon"}
ATTR_SRCSET = {"srcset", "imagesrcset"}
FONCTIONS_IMAGE = {"image-set", "-webkit-image-set", "image", "cross-fade", "-webkit-cross-fade", "src"}


def data_url(fichier: Path) -> str:
    return f"data:{INTEGRABLES[fichier.suffix.lower()]};base64," + base64.b64encode(fichier.read_bytes()).decode("ascii")


class Source:
    """Un fichier de maquette et les règles d'intégration de ses ressources locales."""

    def __init__(self, fichier: Path, racine: Path, lus: set[Path]):
        self.fichier, self.racine, self.lus = fichier, racine, lus

    def local(self, ref: str, depuis: Path) -> Path | None:
        """Le fichier visé par un chemin relatif, s'il existe dans le dossier du manifest ; None sinon."""
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:|^[\\/]{2}", ref):
            return None
        chemin = unquote(ref.split("#", 1)[0].split("?", 1)[0])
        if not chemin:
            return None
        cible = (depuis / chemin).resolve()
        return cible if cible.is_relative_to(self.racine) and cible.is_file() else None

    def integre(self, ref: str, depuis: Path, ou: str, refus) -> str | None:
        """None : la référence reste telle quelle (ancre ou data:). Sinon le data: du fichier local. Refus sinon."""
        r = ref.strip()
        if not r or r.startswith("#") or r[:5].lower() == "data:":
            return None
        cible = self.local(r, depuis)
        if cible is not None and cible.suffix.lower() in INTEGRABLES:
            self.lus.add(cible)
            return data_url(cible)
        if cible is not None:
            refus(f"{ou} : type de fichier non intégrable : {r} (images, polices, vidéos, sous-titres)")
        refus(f"{ou} : ressource non intégrée : {r} — un fichier du dossier du manifest, une ancre # ou un data:")


def _echappement(css: str, i: int) -> tuple[str, int]:
    """Lit un échappement CSS en `css[i] == "\\"` : (caractère, position suivante)."""
    m = re.match(r"\\([0-9a-fA-F]{1,6})(\r\n|[ \t\r\n\f])?", css[i:])
    if m:
        n = int(m[1], 16)
        return (chr(n) if 0 < n <= 0x10FFFF and not 0xD800 <= n <= 0xDFFF else "\ufffd"), i + m.end()
    if i + 1 < len(css):
        return ("" if css[i + 1] in "\r\n\f" else css[i + 1]), i + 2
    return "\ufffd", i + 1


def _chaine_css(css: str, i: int) -> tuple[str, int]:
    """Lit une chaîne CSS ouverte en `css[i]` : (valeur décodée, position après la guillemet fermante)."""
    q, j, val = css[i], i + 1, []
    while j < len(css) and css[j] != q:
        if css[j] == "\\":
            c, j = _echappement(css, j)
            val.append(c)
        elif css[j] == "\n":
            break
        else:
            val.append(css[j])
            j += 1
    return "".join(val), min(j + 1, len(css))


def _debut_ident(css: str, i: int) -> bool:
    c = css[i]
    if c.isalpha() or c == "_" or ord(c) > 127 or c == "\\":
        return True
    return c == "-" and i + 1 < len(css) and (css[i + 1].isalpha() or css[i + 1] in "-_\\" or ord(css[i + 1]) > 127)


def _ident(css: str, i: int) -> tuple[str, int]:
    val = []
    while i < len(css) and (css[i].isalnum() or css[i] in "-_" or ord(css[i]) > 127 or css[i] == "\\"):
        if css[i] == "\\":
            c, i = _echappement(css, i)
            val.append(c)
        else:
            val.append(css[i])
            i += 1
    return "".join(val), i


def reecrit_css(css: str, source: Source, depuis: Path, ou: str, refus) -> str:
    """Une passe sur le CSS : chaque `url()` et chaque chaîne d'`image-set()`/`src()` est un fichier local intégré,
    une ancre ou un data: ; `@import` est refusé. Les échappements CSS sont décodés avant le contrôle."""
    sortie, pile, i, n = [], [], 0, len(css)
    while i < n:
        c = css[i]
        if css.startswith("/*", i):
            fin = css.find("*/", i + 2)
            fin = n if fin < 0 else fin + 2
            sortie.append(css[i:fin])
            i = fin
        elif c in "\"'":
            valeur, fin = _chaine_css(css, i)
            neuf = source.integre(valeur, depuis, ou, refus) if pile and pile[-1] in FONCTIONS_IMAGE else None
            sortie.append(f'"{neuf}"' if neuf else css[i:fin])
            i = fin
        elif c == "@" and i + 1 < n and _debut_ident(css, i + 1):
            mot, fin = _ident(css, i + 1)
            if mot.lower() == "import":
                refus(f"{ou} : pas de @import ; mets la feuille dans une balise style ou un lien vers un fichier local")
            sortie.append(css[i:fin])
            i = fin
        elif _debut_ident(css, i):
            mot, fin = _ident(css, i)
            nom = mot.lower()
            if fin < n and css[fin] == "(" and nom == "url":
                j = fin + 1
                while j < n and css[j] in " \t\r\n\f":
                    j += 1
                if j < n and css[j] in "\"'":
                    valeur, j = _chaine_css(css, j)
                else:
                    brut = []
                    while j < n and css[j] != ")":
                        if css[j] == "\\":
                            car, j = _echappement(css, j)
                            brut.append(car)
                        else:
                            brut.append(css[j])
                            j += 1
                    valeur = "".join(brut)
                while j < n and css[j] != ")":
                    j += 1
                neuf = source.integre(valeur, depuis, ou, refus)
                sortie.append(f'url("{neuf}")' if neuf else css[i:j + 1])
                i = j + 1
            else:
                if fin < n and css[fin] == "(":
                    pile.append(nom)
                    fin += 1
                sortie.append(css[i:fin])
                i = fin
        else:
            if c == "(":
                pile.append("")
            elif c == ")" and pile:
                pile.pop()
            sortie.append(c)
            i += 1
    return "".join(sortie)


def lit_srcset(valeur: str) -> list[tuple[str, str]]:
    """Les candidats d'un srcset : (adresse, descripteur). Une adresse data: garde ses virgules."""
    sortie, i, n = [], 0, len(valeur)
    while i < n:
        while i < n and (valeur[i].isspace() or valeur[i] == ","):
            i += 1
        debut = i
        while i < n and not valeur[i].isspace():
            i += 1
        adresse = valeur[debut:i]
        if not adresse:
            break
        if adresse.endswith(","):
            sortie.append((adresse.rstrip(","), ""))
            continue
        debut = i
        while i < n and valeur[i] != ",":
            i += 1
        sortie.append((adresse, valeur[debut:i].strip()))
    return sortie


class Maquette(HTMLParser):
    """Réécrit une maquette en un document autonome, balise par balise : chaque ressource locale intégrée en data:,
    chaque ressource externe refusée avec sa ligne, la CSP posée en tête, les scripts gardés seulement si la
    maquette est interactive."""

    def __init__(self, fichier: Path, racine: Path, lus: set[Path], interactif: bool):
        super().__init__(convert_charrefs=False)
        self.source = Source(fichier, racine, lus)
        self.fichier, self.interactif = fichier, interactif
        self.morceaux, self.differes = [], []
        self.tete_posee, self.dans = False, None  # dans : "style", "script", "ignore" (script retiré)

    def refus(self, quoi: str):
        raise Refus(f"{self.fichier.name}, ligne {self.getpos()[0]} : {quoi}")

    def pose_tete(self) -> None:
        if not self.tete_posee:
            scripts = "'unsafe-inline' 'unsafe-eval'" if self.interactif else "'none'"
            self.morceaux.append(f'<meta http-equiv="Content-Security-Policy" content="{CSP_MAQUETTE.format(scripts=scripts)}">'
                                 + (STOCKAGE if self.interactif else ""))
            self.tete_posee = True

    def css(self, texte: str, depuis: Path | None = None) -> str:
        return reecrit_css(texte, self.source, depuis or self.fichier.parent, "CSS", self.refus)

    def balise(self, tag: str, attrs: list[tuple[str, str | None]], fermee: bool) -> None:
        if tag in INTERDITS:
            self.refus(INTERDITS[tag])
        a = {k: v for k, v in attrs}
        if tag == "meta" and (a.get("http-equiv") or "").strip().lower() == "refresh":
            self.refus("pas de redirection automatique (meta refresh)")
        if tag not in ("html", "head"):
            self.pose_tete()
        if tag == "link" and "stylesheet" in (a.get("rel") or "").lower().split():
            cible = self.source.local(a.get("href") or "", self.fichier.parent)
            if cible is None:
                self.refus(f"feuille de style non intégrée : {a.get('href')} — un fichier du dossier du manifest")
            self.source.lus.add(cible)
            media = f' media="{html.escape(a["media"])}"' if a.get("media") else ""
            texte = re.sub(r"</(style)", r"<\\/\1", self.css(cible.read_text(encoding="utf-8"), cible.parent), flags=re.I)
            self.morceaux.append(f"<style{media}>{texte}</style>")
            return
        if tag == "script":
            self.script(a)
            return
        change, sortie = False, []
        for nom, val in attrs:
            if val is not None and nom.startswith("on") and not self.interactif:
                change = True  # un gestionnaire d'événement ne sert qu'à une maquette interactive
                continue
            neuf = val
            if val is None:
                pass
            elif nom in ATTR_RESSOURCE or (nom == "href" and tag not in ("a", "area")):
                neuf = self.source.integre(val, self.fichier.parent, f"{tag}.{nom}", self.refus) or val
            elif nom == "href":
                if not val.strip().startswith("#"):
                    self.refus(f"lien hors de la maquette : href=\"{val}\" ; une maquette ne lie qu'à une ancre #…")
            elif nom in ATTR_SRCSET:
                neuf = ", ".join(" ".join(x for x in ((self.source.integre(u, self.fichier.parent, f"{tag}.{nom}",
                                                                           self.refus) or u), d) if x)
                                 for u, d in lit_srcset(val))
            elif nom == "style":
                neuf = self.css(val)
            change |= neuf != val
            sortie.append((nom, neuf))
        if change:
            attributs = "".join(f" {k}" if v is None else f' {k}="{html.escape(v, quote=True)}"' for k, v in sortie)
            self.morceaux.append(f"<{tag}{attributs}{' /' if fermee else ''}>")
        else:
            self.morceaux.append(self.get_starttag_text())
        if tag == "head":
            self.pose_tete()
        if tag == "style" and not fermee:
            self.dans = "style"

    def script(self, a: dict) -> None:
        module = (a.get("type") or "").strip().lower() == "module"
        if "src" not in a:
            if self.interactif:
                self.morceaux.append(self.get_starttag_text())
                self.dans = "script"
            else:
                self.dans = "ignore"
            return
        cible = self.source.local(a.get("src") or "", self.fichier.parent)
        if cible is None or cible.suffix.lower() not in (".js", ".mjs"):
            self.refus(f"script non intégré : {a.get('src')} — un fichier .js du dossier du manifest")
        self.source.lus.add(cible)
        self.dans = "ignore"  # le contenu entre les balises d'un script à src est ignoré par le navigateur
        if not self.interactif:
            return
        code = re.sub("</(script)", r"<\\/\1", cible.read_text(encoding="utf-8"), flags=re.I)
        balise = ('<script type="module">' if module else "<script>") + code + "</script>"
        # un script intégré n'est plus différé : il passe en fin de document, comme `defer` le voulait
        (self.differes if "defer" in a and not module else self.morceaux).append(balise)

    def handle_starttag(self, tag, attrs):
        self.balise(tag, attrs, False)

    def handle_startendtag(self, tag, attrs):
        self.balise(tag, attrs, True)

    def handle_endtag(self, tag):
        if tag == "script" and self.dans == "ignore":
            self.dans = None
            return
        if tag in ("style", "script"):
            self.dans = None
        if tag in ("body", "html") and self.differes:
            self.morceaux += self.differes
            self.differes = []
        self.morceaux.append(f"</{tag}>")

    def handle_data(self, data):
        if self.dans == "ignore":
            return
        if self.dans == "style":
            data = self.css(data)
        elif self.dans is None and data.strip():
            self.pose_tete()
        self.morceaux.append(data)

    def handle_comment(self, data):
        self.morceaux.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.morceaux.append(f"<!{decl}>")

    def handle_pi(self, data):
        self.morceaux.append(f"<?{data}>")

    def unknown_decl(self, data):
        self.morceaux.append(f"<![{data}]>")

    def handle_entityref(self, name):
        self.morceaux.append(f"&{name};")

    def handle_charref(self, name):
        self.morceaux.append(f"&#{name};")

    def resultat(self, texte: str) -> str:
        self.feed(texte)
        self.close()
        if self.dans == "style":
            self.refus("balise style non fermée")
        self.pose_tete()
        return "".join(self.morceaux + self.differes)


def prepare_html(chemin: Path, interactif: bool, racine: Path, lus: set[Path]) -> str:
    try:
        texte = chemin.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise Refus(f"{chemin.name} illisible : {exc}") from None
    return Maquette(chemin, racine, lus, interactif).resultat(texte)


SIGNATURES = ((b"\x89PNG\r\n\x1a\n", "image/png"), (b"\xff\xd8\xff", "image/jpeg"))


def prepare_image(chemin: Path) -> str:
    octets = chemin.read_bytes()
    mime = next((m for sig, m in SIGNATURES if octets.startswith(sig)), None)
    if mime is None and octets[:4] == b"RIFF" and octets[8:12] == b"WEBP":
        mime = "image/webp"
    if mime is None:
        raise Refus(f"{chemin.name} : une capture PNG, JPEG ou WebP")
    return f"data:{mime};base64," + base64.b64encode(octets).decode("ascii")


HOTES_LOCAUX = {"localhost", "127.0.0.1", "::1"}


def adresse_locale(v: str, ou: str) -> str:
    """Une option en direct ne vise qu'un serveur de cette machine, sans identifiants, avec un port valide."""
    try:
        p = urlsplit(v)
        _ = p.port  # lève ValueError pour un port hors limites
    except ValueError:
        p = None
    if p is None or p.scheme not in ("http", "https") or (p.hostname or "").lower() not in HOTES_LOCAUX \
            or p.username or p.password:
        raise Refus(f"{ou} : adresse d'un serveur local valide, par exemple http://localhost:5173/commandes")
    return v


def ordonne(options: list[dict], recommande: str | None) -> list[dict]:
    """L'écran actuel d'abord, sans lettre ; puis la recommandée en a), les autres dans l'ordre du fichier."""
    options.sort(key=lambda o: (not o.get("actuel", False), o["id"] != recommande))
    lettres = iter("abcdefghijklmnopqrstuvwxyz")
    for o in options:
        if not o.get("actuel"):
            o["lettre"] = next(lettres)
    return options


def charge_manifest(chemin: Path) -> tuple[dict, set[Path]]:
    brut = lit_json(chemin, "manifest")
    d = {"version": VERSION, "projet": chaine(brut, "projet", "manifest"),
         "intention": chaine(brut, "intention", "manifest"), "manche": chaine(brut, "manche", "manifest", "01"),
         "langue": parmi(brut, "langue", "manifest", ("fr", "en"), "fr"),
         "question": chaine(brut, "question", "manifest", "Q1")}
    if not re.fullmatch(r"Q\d{1,2}", d["question"]):
        raise Refus("manifest.question : Q1, Q2… comme la question posée à l'utilisateur")
    if "serveur" in brut:
        s = objet(brut, "serveur", "manifest")
        serveur = {"commande": chaine(s, "commande", "manifest.serveur")}
        if "dossier" in s:
            if not Path(chaine(s, "dossier", "manifest.serveur")).is_absolute():
                raise Refus("manifest.serveur.dossier : un chemin absolu")
            serveur["dossier"] = s["dossier"]
        if "adresse" in s:
            serveur["adresse"] = adresse_locale(chaine(s, "adresse", "manifest.serveur"), "manifest.serveur.adresse")
        d["serveur"] = serveur
    brutes = brut.get("options")
    if not isinstance(brutes, list) or not brutes:
        raise Refus("manifest.options : au moins une option")
    racine = chemin.parent.resolve()
    vus, lus, options = set(), {chemin.resolve(), TEMPLATE.resolve()}, []
    for i, o in enumerate(brutes, 1):
        if not isinstance(o, dict):
            raise Refus(f"option {i} : un objet")
        oid = chaine(o, "id", f"option {i}")
        if not ID.fullmatch(oid) or oid in vus:
            raise Refus(f"option {i} : id invalide ou en double : {oid}")
        vus.add(oid)
        genre = parmi(o, "genre", oid, ("html", "image", "adresse"), "html")
        actuel, interactif = o.get("actuel", False), o.get("interactif", False)
        if not isinstance(actuel, bool) or not isinstance(interactif, bool):
            raise Refus(f"{oid} : actuel et interactif valent true ou false")
        if interactif and genre != "html":
            raise Refus(f"{oid} : interactif ne vaut que pour une maquette html")
        if genre == "adresse":
            contenu = adresse_locale(chaine(o, "adresse", oid), oid)
            source = contenu
        else:
            fichier = (racine / chaine(o, "fichier", oid)).resolve()
            if not fichier.is_relative_to(racine) or not fichier.is_file():
                raise Refus(f"{oid}.fichier : un fichier lisible dans le dossier du manifest")
            lus.add(fichier)
            contenu = prepare_html(fichier, interactif, racine, lus) if genre == "html" else prepare_image(fichier)
            source = fichier.name
        palette = chaines(o, "palette", oid, requise=True)
        if not all(HEX_PALETTE.fullmatch(x) for x in palette):
            raise Refus(f"{oid}.palette : des couleurs hexadécimales")
        options.append({"id": oid, "nom": chaine(o, "nom", oid), "intention": chaine(o, "intention", oid),
                        "typographie": chaine(o, "typographie", oid), "palette": palette,
                        "traits": chaines(o, "traits", oid, requise=True), "controles": chaines(o, "controles", oid),
                        "genre": genre, "contenu": contenu, "source": source, "actuel": actuel, "interactif": interactif})
    if sum(o["actuel"] for o in options) > 1:
        raise Refus("un seul écran actuel (actuel: true) au plus")
    if all(o["actuel"] for o in options):
        raise Refus("au moins une option à choisir, en plus de l'écran actuel")
    reco = brut.get("recommande")
    if reco is not None and reco not in {o["id"] for o in options if not o["actuel"]}:
        raise Refus(f"recommande : `{reco}` n'est l'id d'aucune option (l'écran actuel ne se recommande pas)")
    d["recommande"] = reco
    d["options"] = ordonne(options, reco)
    empreinte = json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    d["empreinte"] = hashlib.sha256(empreinte.encode("utf-8")).hexdigest()[:24]
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
    for o in d["options"]:
        if o["genre"] == "adresse":
            p = urlsplit(o["contenu"])
            hote = "localhost" if p.hostname == "::1" else p.hostname.lower()  # une CSP n'accepte pas l'IPv6 littéral
            origines.add(f"{p.scheme}://{hote}" + (f":{p.port}" if p.port else ""))
    permis = " ".join(sorted(origines)) or "'none'"
    csp = f"connect-src {permis}; frame-src {permis}; object-src 'none'; base-uri 'none'; form-action 'none'"
    # Ni `</script>` ni un séparateur de ligne JavaScript ne peuvent sortir du conteneur de données.
    donnees = json.dumps(d, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    page = gabarit.replace(CSP_MARKER, csp).replace(MARKER, donnees)
    if force:
        ecrit_atomique(sortie, page)
    else:
        sortie.parent.mkdir(parents=True, exist_ok=True)
        with sortie.open("x", encoding="utf-8") as h:
            h.write(page)
    if origines and "serveur" not in d:
        print("Rappel : des options visent un serveur local ; ajoute `serveur` au manifest pour pouvoir le relancer.",
              file=sys.stderr)
    return {"page": str(sortie), "options": len(d["options"]), "empreinte": d["empreinte"],
            "lettres": {o["id"]: o.get("lettre", "actuel") for o in d["options"]}}


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
        src = lit_json(depuis, "--depuis")
        options = src.get("cartes") or src.get("options") or []
        trouve = next((o for o in options if isinstance(o, dict) and o.get("id") == option), None)
        if trouve is None:
            ids = ", ".join(str(o.get("id")) for o in options if isinstance(o, dict))
            raise Refus(f"option `{option}` absente de {depuis.name} ; options : {ids}")
        if trouve.get("actuel"):
            raise Refus("l'écran actuel n'est pas une option ; pour garder l'identité : --conserve")
        if manche == "styles":
            if "cartes" not in src:
                raise Refus("manche styles : --depuis le fichier des cartes (cartes.json), qui porte les jetons")
            valide = charge_cartes(depuis)  # la carte retenue passe les mêmes contrôles, contraste compris
            trouve = next(c for c in valide["cartes"] if c["id"] == option)
            etat["jetons"] = jetons(trouve)
        etat["manches"][manche] = (option, str(trouve.get("nom", option)), note or "", maintenant())
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
