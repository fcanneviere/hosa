#!/usr/bin/env python3
"""Captures et contrôles machine des écrans : lance `capture.mjs` (Node 22+, Chrome/Chromium/Edge local).

  capture.py <adresse|fichier> [options de capture.mjs]
  capture.py <adresse de base> --navigation <kb>/interface/navigation.md --role <rôle>
             [--connexion "goto /connexion; type #email …; click …"] [--valeurs id=42,slug=essai] [options]

`--navigation` lit les routes de `## Écrans` du plan de navigation ; `--role` garde celles de ce rôle (colonne
`Rôles`) : un passage par rôle, connecté comme lui, car une route d'un autre rôle rend un 403 ou une redirection.
La 3c additionne les lignes « Routes rendues : X / Y » de ses passages et écrit le total sous `## Vérification`. Une route à paramètre
(`:id`, `{id}`, `[id]`) prend sa valeur dans `--valeurs` ; sans valeur, la capture est refusée et le dit.
Code : 0 sans problème, 1 problèmes trouvés, 2 mauvais appel, 3 Node ou navigateur absent.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MJS = HERE / "capture.mjs"
NO_WINDOW = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
PARAM = re.compile(r":(\w+)|\{(\w+)\}|\[(\w+)\]")


def roles_du_plan(nav: Path) -> list[str]:
    """Les rôles de la colonne `Rôles`, dans l'ordre : un passage de capture chacun."""
    vus = []
    for cells in lignes_ecrans(nav):
        for r in re.split(r"[,;/]", cells[2] if len(cells) > 2 else ""):
            if r.strip() and r.strip().lower() not in (v.lower() for v in vus):
                vus.append(r.strip())
    return vus


def lignes_ecrans(nav: Path) -> list[list[str]]:
    texte = nav.read_text(encoding="utf-8")
    m = re.search(r"^## Écrans\s*$(.*?)(?=^## |\Z)", texte, re.M | re.S)
    lignes = [r for r in (m.group(1) if m else "").splitlines()
              if r.strip().startswith("|") and not re.match(r"^\s*\|[\s|:-]+\|\s*$", r)][1:]
    return [[c.strip() for c in r.strip().strip("|").split("|")] for r in lignes]


def routes_du_plan(nav: Path, role: str | None = None) -> list[str]:
    """Les routes de la colonne `Route` de `## Écrans`, dans l'ordre, sans doublon ; avec `role`, celles de ce rôle."""
    vues = []
    for cells in lignes_ecrans(nav):
        route = cells[1].strip("` ") if len(cells) > 1 else ""
        roles = {r.strip().lower() for r in re.split(r"[,;/]", cells[2] if len(cells) > 2 else "")}
        if route.startswith("/") and route not in vues and (role is None or role.strip().lower() in roles):
            vues.append(route)
    return vues


def remplit(routes: list[str], valeurs: dict[str, str]) -> tuple[list[str], list[str]]:
    pleines, manques = [], []
    for r in routes:
        noms = [a or b or c for a, b, c in PARAM.findall(r)]
        absents = [n for n in noms if n not in valeurs]
        if absents:
            manques.append(f"route {r} : donne une valeur à {', '.join(absents)} (--valeurs {absents[0]}=…)")
        else:
            pleines.append(PARAM.sub(lambda m: valeurs[m.group(1) or m.group(2) or m.group(3)], r))
    return pleines, manques


def node() -> str | None:
    n = shutil.which("node")
    if not n:
        return None
    try:
        v = subprocess.run([n, "--version"], capture_output=True, text=True, timeout=20, **NO_WINDOW).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.match(r"v(\d+)", v.strip())
    return n if m and int(m.group(1)) >= 22 else None


def main(argv: list[str]) -> int:
    args, nav, valeurs, role = [], None, {}, None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--navigation", "--valeurs", "--role"):
            if i + 1 >= len(argv):
                print(f"capture : {a} attend une valeur", file=sys.stderr)
                return 2
            if a == "--navigation":
                nav = Path(argv[i + 1])
            elif a == "--role":
                role = argv[i + 1]
            else:
                for paire in argv[i + 1].split(","):
                    k, _, v = paire.partition("=")
                    if not k.strip() or not v.strip():
                        print(f"capture : --valeurs attend nom=valeur, séparés par des virgules : {paire}", file=sys.stderr)
                        return 2
                    valeurs[k.strip()] = v.strip()
            i += 2
            continue
        args.append(a)
        i += 1
    if role is not None and nav is None:
        print("capture : --role va avec --navigation", file=sys.stderr)
        return 2
    if nav is not None:
        if "--routes" in args:
            print("capture : --navigation ou --routes, pas les deux", file=sys.stderr)
            return 2
        if not nav.is_file():
            print(f"capture : plan de navigation introuvable : {nav}", file=sys.stderr)
            return 2
        roles = roles_du_plan(nav)
        if len(roles) > 1 and role is None:
            print(f"capture : le plan a plusieurs rôles ({', '.join(roles)}) : un passage par rôle, "
                  "--role <rôle> et --connexion pour se connecter comme lui", file=sys.stderr)
            return 2
        if role is not None and role.strip().lower() not in (r.lower() for r in roles):
            print(f"capture : rôle « {role} » absent de la colonne Rôles ; rôles : {', '.join(roles)}", file=sys.stderr)
            return 2
        routes, manques = remplit(routes_du_plan(nav, role), valeurs)
        if manques:
            print("capture refusée — routes à paramètre sans valeur :\n" + "\n".join(manques), file=sys.stderr)
            return 2
        if not routes:
            print(f"capture : aucune route dans `## Écrans` de {nav}", file=sys.stderr)
            return 2
        args += ["--routes", ",".join(routes)]
    n = node()
    if n is None:
        print("capture : Node 22 ou plus récent introuvable. Ne l'installe pas toi-même : "
              "demande-le en `## Installation nécessaire`, ou mets les écrans en tests T.", file=sys.stderr)
        return 3
    r = subprocess.run([n, str(MJS), *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       **NO_WINDOW)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    return r.returncode


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
