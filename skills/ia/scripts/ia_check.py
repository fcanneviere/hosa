#!/usr/bin/env python3
"""The proofs of the AI stages: each AI function framed, measured on real data, and measured again when it changes.

  ia_check.py <kb> cadrage                    `kb/cdc/ia.md`: each function `IAn` has its exigence, its form (a
                                              single call, RAG, MCP, agent), its baseline without AI, its metric,
                                              threshold, longest duration, place (local or cloud), data, limits,
                                              behaviour on a wrong answer, and the fields of its form; the target
                                              machine and the budget are written, and the user's answers kept
                                              under `## Choix validés`
  ia_check.py <kb> spec                       `kb/stack/essai-ia.md`: each function's technical specification, by
                                              form, and what must be installed (`## Besoins d'installation`)
  ia_check.py <kb> besoins                    each need pinned, with its verification command run (`exit 0`)
  ia_check.py <kb> essai                      `spec` and `besoins`, and each function's last result line is a PASS
                                              from the evaluation script (`exit 0`), with its measures
  ia_check.py <kb> rejeu     [--root <dir>]   the files each function tracks, in <dir>, are the ones its last PASS
                                              measured (same fingerprint): else the evaluation is run again
  ia_check.py <kb> empreinte [--root <dir>]   each function's fingerprint, to write on its result line

<dir>: the project's checkout (a sprint's worktree); by default the KB's project root (`<root>/.hosa/kb`).
A result line, one per run, appended (the last one of a function is the retained model's):

  - 2026-01-31T14:00Z — IA1 — PASS — modèle : <nom@révision> — exécution : local — mesuré : <valeur> —
    référence : <valeur sans IA> — durée : <s> — mémoire : <Go> — coût : <€> — commande : `<cmd>` — exit 0 —
    empreinte : <12 hex>                                                             (on one line)

A RAG function's line also has `recherche : <the right passage found>`. A need, one line each:

  - <nom> — version : <épinglée> — <rôle> — vérification : `<cmd>` — exit 0 — <date>      (or `- aucun — <raison>`)

HOSA_IA=0 turns the checks off. Exit: 0 complete, 1 gaps (`✗` lines), 2 bad invocation. Stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from fnmatch import fnmatchcase
from pathlib import Path

CADRAGE, ESSAI = "cdc/ia.md", "stack/essai-ia.md"
FIELDS = ("Forme", "Référence sans IA", "Métrique", "Seuil", "Durée max", "Exécution", "Données", "Limites",
          "Erreur du modèle")
NUMBERED = ("Seuil", "Durée max", "Limites", "Seuil de recherche", "Bornes")  # a number, or the measure to come
# what the user owns, asked at the framing, by form (a function may have several: « agent, MCP »)
FORMS = {
    "appel simple": (),
    "RAG": ("Corpus", "Mise à jour", "Droits d'accès", "Sources citées", "Seuil de recherche"),
    "MCP": ("Rôle MCP", "Serveurs", "Outils", "Authentification", "Actions confirmées"),
    "agent": ("Outils", "Actions confirmées", "Bornes"),
}
# what the AI expert decides once the stack is chosen: every function, then by form
SPEC = {
    "": ("Sortie", "Suivi"),
    "RAG": ("Découpage", "Embeddings", "Base vectorielle", "Filtre d'accès"),
    "MCP": ("Transport", "Versions épinglées", "Droits des outils"),
    "agent": ("Orchestration", "Droits des outils"),
}
NEEDS = "Besoins d'installation"
SECRET = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|hf_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,})"
                    r"|(?:API_KEY|TOKEN|SECRET|PASSWORD)\s*=\s*[\"']?[A-Za-z0-9_-]{12,}")
CONSTRAINTS = ("Machine cible", "Budget")
CHOICES = "Choix validés"  # the user's answers, written by the skill: the agent's rewrite never drops them
PLACES = ("local", "cloud", "à comparer")
RESULT_FIELDS = ("modèle", "exécution", "mesuré", "référence", "durée", "mémoire", "coût", "commande", "empreinte")
FUNCTION = re.compile(r"^-\s+\*\*(IA\d+)\*\*(?:\s*—\s*(.*))?$")
RESULT = re.compile(r"^-\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})\S*\s+—\s+\**(IA\d+)\**\s+—\s+(PASS|FAIL)\b(.*)$")
STAMP = re.compile(r"^-\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})")
SKIPPED_DIRS = {".git", ".hosa", ".worktrees", "node_modules", "__pycache__", ".venv", "venv"}


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


def section(text: str, heading: str) -> list[str]:
    out, inside = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line[3:].strip() == heading
        elif inside:
            out.append(line)
    return out


def of_type(text: str, ctype: str) -> bool:
    return bool(re.search(rf"^type:\s*[\"']?{re.escape(ctype)}[\"']?\s*$", text, re.M))


def functions(text: str, heading: str = "Fonctions IA") -> list[tuple[str, str, dict[str, str]]]:
    """[(IAn, its first line, {field: value})] of `## <heading>`."""
    out: list[tuple[str, str, dict[str, str]]] = []
    for line in section(text, heading):
        if m := FUNCTION.match(line):
            out.append((m[1], m[2] or "", {}))
        elif out and (f := re.match(r"^\s+-\s+(?:\*\*)?([^:*]+?)(?:\*\*)?\s*:\s*(.*)$", line)):
            out[-1][2][f[1].strip().replace("’", "'")] = f[2].strip()
    return out


def forms(value: str) -> tuple[list[str], list[str]]:
    """(the known forms, the unknown words) of a `Forme :` value."""
    known, unknown = [], []
    for word in (w.strip() for w in re.split(r"[,+]", value) if w.strip()):
        form = next((f for f in FORMS if word.lower().startswith(f.lower())), None)
        (known if form else unknown).append(form or word)
    return known, unknown


def secrets(kb: Path) -> list[str]:
    return [f"`kb/{rel}` contient la valeur d'un secret : retire-la (la clé vit dans le fichier d'environnement non "
            "suivi), et change cette clé" for rel in (CADRAGE, ESSAI) if SECRET.search(read(kb / rel) or "")]


def cadrage_gaps(kb: Path) -> list[str]:
    text = read(kb / CADRAGE)
    if text is None or not of_type(text, "Cadrage IA"):
        return [f"pas de `kb/{CADRAGE}` (`type: Cadrage IA`) — sans fonction d'IA : `skip cadrage-ia` et "
                "`skip essai-ia`"]
    found, gaps = functions(text), []
    if not found:
        return [f"`kb/{CADRAGE}` `## Fonctions IA` sans ligne `- **IA1** — …` — sans fonction d'IA : "
                "`skip cadrage-ia` et `skip essai-ia`"]
    ids = [i for i, _, _ in found]
    gaps += [f"{i} en double" for i in sorted({i for i in ids if ids.count(i) > 1})]
    for i, head, fields in found:
        links = re.findall(r"\]\(([\w./-]+\.md)\)", head)
        if not any((kb / "cdc" / x).is_file() for x in links):
            gaps.append(f"{i} : sa ligne ne lie aucune exigence existante (`[exigence](<slug>.md)`)")
        known, unknown = forms(fields.get("Forme", ""))
        gaps += [f"{i} : forme « {w} » inconnue — `Forme :` vaut {' | '.join(FORMS)} (plusieurs : « agent, MCP »)"
                 for w in unknown]
        asked = dict.fromkeys(FIELDS + tuple(f for form in known for f in FORMS[form]))
        gaps += [f"{i} : `{f} :` absent ou vide" for f in asked if not fields.get(f)]
        gaps += [f"{i} : `{f} :` sans chiffre — une valeur, ou `[à mesurer Mn : … — étape essai-ia]`"
                 for f in asked if f in NUMBERED and fields.get(f) and not re.search(r"\d", fields[f])]
        role = fields.get("Rôle MCP", "").lower()
        if "MCP" in known and role and not role.startswith(("client", "serveur", "les deux")):
            gaps.append(f"{i} : `Rôle MCP :` vaut client | serveur | les deux")
        place = fields.get("Exécution", "")
        if place and not place.lower().startswith(PLACES):
            gaps.append(f"{i} : `Exécution :` vaut {' | '.join(PLACES)}")
    constraints = "\n".join(section(text, "Contraintes"))
    gaps += [f"`## Contraintes` : ligne `- {c} :` absente ou vide" for c in CONSTRAINTS
             if not re.search(rf"^-\s+(?:\*\*)?{c}(?:\*\*)?\s*:[ \t]*\S", constraints, re.M)]
    if not any(re.match(r"^-\s+\S", x) for x in section(text, CHOICES)):
        gaps.append(f"`## {CHOICES}` vide : les réponses de l'utilisateur (`- <date> — human:<user> — <réponse>`), "
                    "écrites par le skill, gardées par `hosa-ia`")
    return gaps + secrets(kb)


def results(text: str) -> dict[str, list[dict[str, str]]]:
    """{IAn: its result lines in order, each {at, verdict, line, field: value}}."""
    out: dict[str, list[dict[str, str]]] = {}
    for line in section(text, "Résultats"):
        if m := RESULT.match(line.strip()):
            row = {"at": m[1], "verdict": m[3], "line": m[4]}
            for part in re.split(r"\s+—\s+", m[4]):
                key, sep, value = part.partition(" : ")
                if sep:
                    row[key.strip().strip("*").lower()] = value.strip()
            out.setdefault(m[2], []).append(row)
    return out


def tracked(text: str) -> dict[str, list[str]]:
    """{IAn: the paths and globs of `## Fichiers suivis`}."""
    out: dict[str, list[str]] = {}
    for line in section(text, "Fichiers suivis"):
        if m := re.match(r"^-\s+\**(IA\d+)\**\s*—\s*(.+)$", line):
            out.setdefault(m[1], []).extend(p.strip().strip("`") for p in m[2].split(",") if p.strip().strip("`"))
    return out


def trial(kb: Path) -> tuple[str | None, str | None, list[str]]:
    """(cadrage, essai, the gap of a missing essai). No cadrage: no AI function, nothing to check."""
    framed, text = read(kb / CADRAGE), read(kb / ESSAI)
    if framed is not None and (text is None or not of_type(text, "Essai IA")):
        return framed, None, [f"pas de `kb/{ESSAI}` (`type: Essai IA`) : l'essai mesuré sur des données réelles"]
    return framed, text, []


def spec_gaps(kb: Path) -> list[str]:
    framed, text, gaps = trial(kb)
    if framed is None or gaps:
        return gaps
    written = {i: fields for i, _, fields in functions(text, "Spécification technique")}
    for i, _, fields in functions(framed):
        asked = dict.fromkeys(f for form in ["", *forms(fields.get("Forme", ""))[0]] for f in SPEC.get(form, ()))
        missing = [f for f in asked if not written.get(i, {}).get(f)]
        if missing:
            gaps.append(f"{i} : `## Spécification technique` (`- **{i}**`, un champ par sous-ligne) sans "
                        f"{', '.join(f'`{f} :`' for f in missing)}")
    if not [x for x in section(text, NEEDS) if x.startswith("- ")]:
        gaps.append(f"`## {NEEDS}` vide : une ligne par élément à installer (modèle, serveur, base vectorielle, serveur "
                    "MCP, GPU, clé d'API), ou `- aucun — <raison>`")
    return gaps + secrets(kb)


def needs_gaps(kb: Path) -> list[str]:
    """Each need pinned, and verified in the project's environment by whoever installed it."""
    framed, text, gaps = trial(kb)
    if framed is None or gaps:
        return gaps
    lines = [x[2:].strip() for x in section(text, NEEDS) if x.startswith("- ")]
    if not lines:
        return [f"`## {NEEDS}` vide : une ligne par élément, ou `- aucun — <raison>`"]
    for line in lines:
        if re.match(r"aucun\s+—\s+\S", line, re.I):
            continue
        name = line.split(" — ")[0]
        version = re.search(r"—\s*version\s*:\s*([^—]+)", line)
        if not version or re.search(r"\blatest\b", version[1], re.I):
            gaps.append(f"besoin « {name} » sans `version :` épinglée (jamais `latest` ; une clé : `sans objet`)")
        if not re.search(r"vérification\s*:\s*`[^`]+`", line):
            gaps.append(f"besoin « {name} » sans `vérification : `<commande>``")
        elif not re.search(r"—\s*exit 0\b", line):
            gaps.append(f"besoin « {name} » pas vérifié (`— exit 0`) : `hosa-infra` l'installe, lance sa commande dans "
                        "le conteneur et écrit le code de sortie")
    return gaps + secrets(kb)


def essai_gaps(kb: Path) -> list[str]:
    framed, text, gaps = trial(kb)
    if framed is None or gaps:
        return gaps  # no AI function: nothing to try
    gaps = list(dict.fromkeys(spec_gaps(kb) + needs_gaps(kb)))
    if not any(re.match(r"^-\s+(?:\*\*)?Source(?:\*\*)?\s*:\s*\S", x) for x in section(text, "Données d'essai")):
        gaps.append("`## Données d'essai` sans ligne `- Source :` (les données réelles : origine, volume, période)")
    revised = max((m[1] for x in section(framed, "Révisions") if (m := STAMP.match(x))), default="")
    found, paths = results(text), tracked(text)
    for i, _, fields in functions(framed):
        runs = found.get(i, [])
        if not runs:
            gaps.append(f"{i} : aucune ligne sous `## Résultats` (`- <date>Z — {i} — PASS|FAIL — modèle : …`)")
            continue
        last = runs[-1]
        if last["verdict"] != "PASS":
            gaps.append(f"{i} : dernier résultat FAIL ({last.get('modèle', 'modèle non nommé')}, mesuré : "
                        f"{last.get('mesuré', '?')}) — autre modèle : `back essai-ia stack` ; seuil ou fonction à "
                        "revoir : `back essai-ia cadrage-ia` ; l'utilisateur décide")
            continue
        rag = ("recherche",) if "RAG" in forms(fields.get("Forme", ""))[0] else ()
        missing = [f for f in RESULT_FIELDS + rag if not last.get(f)]
        if missing:
            gaps.append(f"{i} : ligne PASS sans {', '.join(f'`{f} :`' for f in missing)}")
        if not re.search(r"\bexit 0\b", last["line"]):
            gaps.append(f"{i} : PASS sans `exit 0` — le verdict est celui du script d'évaluation")
        if last["at"] < revised:
            gaps.append(f"{i} : résultat du {last['at']}Z, antérieur au cadrage révisé le {revised}Z — relance "
                        "l'évaluation")
        asked = fields.get("Exécution", "").lower()
        ran = {r.get("exécution", "").lower().split(" ")[0] for r in runs}
        if asked.startswith("à comparer") and not {"local", "cloud"} <= ran:
            gaps.append(f"{i} : cadré « à comparer » — il faut un résultat `exécution : local` et un `exécution : cloud`")
        for place in ("local", "cloud"):
            if asked.startswith(place) and last.get("exécution") and not last["exécution"].lower().startswith(place):
                gaps.append(f"{i} : cadré `{place}`, retenu `{last['exécution']}`")
        if not paths.get(i):
            gaps.append(f"{i} : aucune ligne `- {i} — <script d'évaluation>, <code, prompts>` sous `## Fichiers suivis`")
    return gaps


def files_of(root: Path, patterns: list[str]) -> list[str]:
    """The files of <root> the patterns name (a path, a folder, or a glob where `*` crosses `/`), sorted."""
    out: set[str] = set()
    for raw in patterns:
        pattern = raw.replace("\\", "/").removeprefix("./").rstrip("/")
        literal = []  # walk from the pattern's fixed folders only, never the whole project
        for part in pattern.split("/"):
            if any(c in part for c in "*?["):
                break
            literal.append(part)
        if ".." in literal or pattern.startswith("/") or ":" in pattern:
            continue
        start = root.joinpath(*literal)
        if start.is_file():
            out.add("/".join(literal))
            continue
        for folder, dirs, names in os.walk(start):
            dirs[:] = [d for d in dirs if d not in SKIPPED_DIRS]
            for name in names:
                rel = (Path(folder) / name).relative_to(root).as_posix()
                if fnmatchcase(rel, pattern) or rel.startswith(pattern + "/"):
                    out.add(rel)
    return sorted(out)


def fingerprint(root: Path, files: list[str]) -> str:
    h = hashlib.sha256()
    for rel in files:  # the same files give the same print on Windows (CRLF) and in a container
        h.update(rel.encode() + b"\0" + (root / rel).read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return h.hexdigest()[:12]


def rejeu_gaps(kb: Path, root: Path) -> list[str]:
    framed = read(kb / CADRAGE)
    if framed is None:
        return []
    text = read(kb / ESSAI) or ""
    found, paths = results(text), tracked(text)
    gaps = needs_gaps(kb) if text else []  # a need added since the trial is installed and verified too
    for i, _, _ in functions(framed):
        runs = found.get(i, [])
        if not paths.get(i) or not runs:
            gaps.append(f"{i} : jamais essayée (`kb/{ESSAI}` : ni résultat ni fichiers suivis) — `ia`, étape `essai-ia`")
            continue
        files = files_of(root, paths[i])
        if not files:
            gaps.append(f"{i} : aucun fichier suivi dans `{root.as_posix()}` ({', '.join(paths[i])}) — corrige "
                        "`## Fichiers suivis`")
            continue
        now, last = fingerprint(root, files), runs[-1]
        if last["verdict"] != "PASS" or not re.search(r"\bexit 0\b", last["line"]):
            gaps.append(f"{i} : dernière évaluation sans PASS (`exit 0`) — le seuil ne tient pas : défaut à corriger")
        elif last.get("empreinte", "").strip("`") != now:
            gaps.append(f"{i} : ses fichiers suivis ont changé depuis la dernière évaluation (empreinte {now}, mesurée "
                        f"{last.get('empreinte') or 'absente'}) — `hosa-ia` Mode 3 relance l'évaluation et ajoute sa ligne")
    return gaps


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("kb", type=Path)
    ap.add_argument("action", choices=["cadrage", "spec", "besoins", "essai", "rejeu", "empreinte"])
    ap.add_argument("--root", type=Path)
    a = ap.parse_args(argv)
    if not a.kb.is_dir():
        print(f"error: {a.kb} is not a directory", file=sys.stderr)
        return 2
    root = a.root or a.kb.resolve().parent.parent
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    if a.action == "empreinte":
        for i, patterns in tracked(read(a.kb / ESSAI) or "").items():
            files = files_of(root, patterns)
            print(f"{i} {fingerprint(root, files) if files else 'aucun fichier'} ({len(files)} fichier(s))")
        return 0
    if os.environ.get("HOSA_IA") == "0":
        print("✓ contrôle IA coupé (HOSA_IA=0)")
        return 0
    checks = {"cadrage": cadrage_gaps, "spec": spec_gaps, "besoins": needs_gaps, "essai": essai_gaps}
    gaps = checks.get(a.action, lambda k: rejeu_gaps(k, root))(a.kb)
    for g in gaps:
        print(f"✗ {g}")
    print(f"{len(gaps)} manque(s)" if gaps else "✓ complet")
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
