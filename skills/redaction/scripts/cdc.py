#!/usr/bin/env python3
"""The cahier des charges as one document, and the proof that nothing is missing.

  cdc.py check <kb-dir> [--json]   list the holes; exit 1 if there is any
  cdc.py assemble <kb-dir>         write kb/project/cahier-des-charges.md, holes included
  cdc.py revue <kb-dir> [--route R] the anomalies of kb/cdc/relecture.md: exit 1 on a badly
                                   tagged one or a `bloquante` still `ouverte` (routed → R when given)
  cdc.py mesure <kb-dir>           the anomalies counted by pass, gravity and origin
  cdc.py numerote <kb-dir>         give each rule and error case without an id its `RGn` / `CEn`

The fiches stay the source (kb/cdc/, kb/project/identity.md, kb/personnas/):
the document is regenerated from them, never edited by hand. A hole is a cell of
a completeness matrix left empty — an objective no exigence serves, an exigence
with no priority or lot, a state with no way out, a right nobody decided, an open
question, a persona need nobody judged, a line still `[à confirmer]` (deduced, never
confirmed by the user), a rule or an error case without its id. `contestation` signs
nothing while `check` finds one.

A rule is `- **RG2** — …` under `## Règles de gestion`, an error case `- **CE1** — …`
under `## Cas d'erreur`, a dashboard's indicator `- **IN1** — <nom> : <calcul> — source : … —
période : … — cible ou seuil : … — action : …` under `## Indicateurs` (a missing part is a hole).
The id is what a ticket's criterion cites (`- CA1 [RG2] — …`, `- CA2 [IN1] — … affiche 12`,
checked by `ticket_check.py`): `numerote` adds the missing ones and never moves one.

An anomaly line is `- A12 [p2, bloquante, correction] — … — → redaction — ouverte`:
its pass (`p<n>` relecture, `c<n>` contestation), its gravity (only a `bloquante`
holds a stage and sends work back) and its origin (`texte` was there at the first
read, `correction` came with a fix, `regle-hosa` is Hosa's rule, not the project's).

Exit: 0 complete (or document written), 1 holes (check, revue), 2 bad invocation. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PRIORITES = ["indispensable", "important", "souhaitable"]
NATURES = {"processus", "nfr", "contrainte"}
TRANSVERSE = "aucun — exigence transverse"
CONTRAINTE_TAGS = {"juridique", "securite", "rgpd"}
# `objectifs: [obligation]`: imposed by the law, security or the basics of software, not by a business objective
OBLIGATION = "obligation"
OBLIGATION_TAGS = CONTRAINTE_TAGS | {"fondamentaux", "socle-comptes"}
ESPACES = {"front-office", "back-office", "hors-application"}
GRAVITES = ("bloquante", "mineure")
ORIGINES = ("texte", "correction", "regle-hosa")
ROUTES = ("redaction", "interview", "utilisateur")
# a line the persona agent deduced and the user never confirmed (`interview`, `redaction`): never a fact
A_CONFIRMER = "[à confirmer]"
# a rule and an error case carry an id (`- **RG2** — …`, `- **CE1** — …`) that a ticket's criterion cites
# (`- CA1 [RG2] — …`): never renumbered, never reused — a rule dropped keeps its line, `- **RG2** — retirée : <raison>`
# An indicator of a dashboard (`## Indicateurs`, `- **IN1** — …`) is numbered and cited the same way: a ticket that
# shows it proves its value on the test dataset (`- CA2 [IN1] — … affiche 12`).
RULES = {"règles de gestion": "RG", "cas d'erreur": "CE", "indicateurs": "IN"}
RULE_ID = re.compile(r"^-\s+\*\*((?:RG|CE|IN)\d+)\*\*")
RETIRED = re.compile(r"^-\s+\*\*(?:RG|CE|IN)\d+\*\*\s*—\s*retirée?\b", re.I)
# what an indicator line says besides its name and calculation — without one, nobody can build, test or act on it
INDICATEUR_CHAMPS = ("source", "période", "cible ou seuil", "action")
OUT = "project/cahier-des-charges.md"
LINK = re.compile(r"\]\(([^)#\s:]+\.md)(#[^)]*)?\)")


# --- reading -----------------------------------------------------------------

def split(text: str) -> tuple[dict[str, str], str]:
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*(?:\n|$)(.*)$", text, re.S)
    if not m:
        return {}, text
    fm: dict[str, str] = {}
    key = None
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$", line)
        if kv:
            key = kv.group(1)
            fm[key] = kv.group(2).strip("'\"")
        elif key and re.match(r"^\s+-\s+", line):
            fm[key] = (fm[key] + ", " if fm[key] else "") + re.sub(r"^\s+-\s+", "", line).strip("'\"")
    return fm, m.group(2)


def as_list(value: str) -> list[str]:
    return [x.strip().strip("'\"") for x in value.strip("[]").split(",") if x.strip()]


def section_map(body: str, level: int = 2) -> dict[str, str]:
    """`## Title` → its text, in order; the text before the first heading under ''."""
    mark = "#" * level + " "
    out: dict[str, list[str]] = {"": []}
    cur = ""
    for line in body.splitlines():
        if line.startswith(mark):
            cur = line[len(mark):].strip()
            out[cur] = []
        else:
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def get(secs: dict[str, str], prefix: str) -> str:
    for k, v in secs.items():
        if k.lower().startswith(prefix.lower()):
            return v
    return ""


def empty(text: str) -> bool:
    t = text.strip().lower().rstrip(".")
    return not t or t in {"aucun", "aucune", "aucun encore défini", "aucune encore définie", "à compléter", "?"}


class Concept:
    def __init__(self, path: Path, kb: Path):
        self.path, self.slug = path, path.stem
        self.rel = path.relative_to(kb).as_posix()
        self.fm, self.body = split(path.read_text(encoding="utf-8"))
        self.secs = section_map(self.body)
        self.title = self.fm.get("title") or self.slug
        self.tags = set(as_list(self.fm.get("tags", "")))

    @property
    def transverse(self) -> bool:
        return get(self.secs, "Besoin").strip().lower().rstrip(".") == TRANSVERSE

    @property
    def nature(self) -> str:
        if self.fm.get("nature") in NATURES:
            return self.fm["nature"]
        if "nfr" in self.tags:
            return "nfr"
        if self.transverse and self.tags & CONTRAINTE_TAGS:
            return "contrainte"
        return "processus"


def load(kb: Path) -> dict:
    cdc = kb / "cdc"
    def concepts(folder: Path, type_: str) -> list[Concept]:
        out = []
        for f in sorted(folder.glob("*.md")) if folder.is_dir() else []:
            if f.name in {"log.md", "index.md"}:
                continue
            c = Concept(f, kb)
            if c.fm.get("type") == type_ and c.fm.get("status") != "deprecated":
                out.append(c)
        return out
    def one(rel: str) -> Concept | None:
        p = kb / rel
        return Concept(p, kb) if p.is_file() else None
    return {
        "identity": one("project/identity.md"),
        "personas": [p for p in concepts(kb / "personnas", "Persona") if p.slug != "exemple-persona"],
        "exigences": [e for e in concepts(cdc, "Exigence") if e.slug != "exemple-exigence"],
        "glossaire": one("cdc/glossaire.md"),
        "modele": one("cdc/modele-metier.md"),
        "decisions": one("cdc/decisions.md"),
        "relecture": one("cdc/relecture.md"),
        "annexes": [c for c in (one(f"cdc/{n}.md") for n in ("juridique", "securite", "fondamentaux", "relecture")) if c],
        "interviews": [Concept(f, kb) for f in sorted((cdc / "interviews").glob("*.md")) if f.name != "log.md"]
        if (cdc / "interviews").is_dir() else [],
    }


# --- matrices ----------------------------------------------------------------

def objectives(identity: Concept | None) -> list[dict[str, str]]:
    """Rows of the `## Objectifs mesurables` table: Id | Objectif | Indicateur | Cible | Mesure."""
    if not identity:
        return []
    rows = []
    for line in get(identity.secs, "Objectifs mesurables").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.strip().startswith("|") and re.fullmatch(r"O\d+", cells[0] if cells else ""):
            cells += [""] * (5 - len(cells))
            rows.append(dict(zip(["id", "objectif", "indicateur", "cible", "mesure"], cells[:5])))
    return rows


def transitions(text: str) -> list[tuple[str, str, str]]:
    """`- a → b : comment — [exigence](x.md)` lines of a `### Cycle de vie`."""
    out = []
    for line in text.splitlines():
        m = re.match(r"^\s*-\s+(.+?)\s+→\s+(.+?)\s*:\s*(.+)$", line)
        if m:
            out.append((m.group(1).strip().lower(), m.group(2).strip().lower(), m.group(3)))
    return out


def bullets(text: str) -> list[str]:
    """Top-level `- ` lines that say something."""
    return [l for l in text.splitlines() if re.match(r"^-\s+\S", l) and not empty(l[1:])]


def rule_lines(text: str) -> list[tuple[int, str, str]]:
    """(line index, `RG` or `CE`, its id or '') of each rule and error case of a fiche:
    the top-level bullets of `## Règles de gestion` and `## Cas d'erreur`."""
    out, prefix = [], ""
    for i, line in enumerate(text.splitlines()):
        if line.startswith("## "):
            prefix = RULES.get(line[3:].strip().lower(), "")
        elif prefix and re.match(r"^-\s+\S", line) and not re.match(r"^-\s+aucun", line, re.I):
            m = RULE_ID.match(line)
            out.append((i, prefix, m.group(1) if m else ""))
    return out


def rule_ids(text: str) -> list[str]:
    """The ids a ticket can cite: every numbered rule and error case still in force, in the fiche's order."""
    lines = text.splitlines()
    return [rid for i, _, rid in rule_lines(text) if rid and not RETIRED.match(lines[i])]


def indicateurs(text: str) -> list[dict[str, str]]:
    """Each indicator in force of `## Indicateurs`: {id, texte} — its whole line, sub-bullets included."""
    lines, out = text.splitlines(), []
    for i, prefix, rid in rule_lines(text):
        if prefix != "IN" or RETIRED.match(lines[i]):
            continue
        texte = [lines[i]]
        for nxt in lines[i + 1:]:
            if not re.match(r"^\s+\S", nxt):
                break
            texte.append(nxt)
        out.append({"id": rid, "texte": " ".join(texte)})
    return out


def numerote(path: Path) -> int:
    """Give each rule and error case without an id the next free one. An id already there never moves."""
    with path.open(encoding="utf-8", newline="") as f:  # the file's own line ends are kept
        text = f.read()
    lines, found = text.splitlines(keepends=True), rule_lines(text)
    last = {p: max([int(rid[2:]) for _, _, rid in found if rid.startswith(p)] or [0]) for p in RULES.values()}
    added = 0
    for i, prefix, rid in found:
        if not rid:
            last[prefix] += 1
            lines[i] = re.sub(r"^-\s+", f"- **{prefix}{last[prefix]}** — ", lines[i], count=1)
            added += 1
    if added:
        with path.open("w", encoding="utf-8", newline="") as f:
            f.write("".join(lines))
    return added


def table_rows(text: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        if line.strip().startswith("|") and not re.fullmatch(r"\|?[\s:|-]+\|?", line.strip()):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows[1:]  # header dropped


def holes(d: dict, kb: Path) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    def hole(matrix: str, where: str, what: str) -> None:
        found.append({"matrice": matrix, "où": where, "trou": what})

    ident = d["identity"]
    exigences = d["exigences"]
    slugs = {e.slug for e in exigences}

    # Cadrage
    if not ident:
        hole("cadrage", "project/identity.md", "fiche projet absente")
    else:
        if empty(get(ident.secs, "Contexte et enjeux")):
            hole("cadrage", "project/identity.md", "`## Contexte et enjeux` vide : situation actuelle et problèmes constatés")
        if empty(get(ident.secs, "Hypothèses")):
            hole("cadrage", "project/identity.md", "`## Hypothèses, dépendances et risques` vide")
    objs = objectives(ident)
    if not objs:
        hole("objectifs", "project/identity.md", "aucun objectif mesurable au format `| O1 | objectif | indicateur | cible | mesure |`")
    for o in objs:
        for col in ("indicateur", "cible", "mesure"):
            if empty(o[col]):
                hole("objectifs", o["id"], f"{col} non renseigné(e)")

    # Exigences : priorité, lot, domaine, objectif, déclencheur
    served = {o["id"]: [] for o in objs}
    for e in exigences:
        where = e.rel
        if e.fm.get("priorite") not in PRIORITES:
            hole("priorités", where, f"`priorite` absente ou hors {'/'.join(PRIORITES)}")
        if not e.fm.get("lot"):
            hole("périmètre", where, "`lot` absent")
        if not e.fm.get("domaine"):
            hole("cartographie", where, "`domaine` absent")
        if e.nature == "processus":
            if empty(get(e.secs, "Déclencheur")):
                hole("chaîne des processus", where, "`## Déclencheur` absent ou vide")
            for target in LINK.findall(get(e.secs, "Déclencheur")):
                if not (e.path.parent / target[0]).is_file():
                    hole("chaîne des processus", where, f"déclencheur vers une fiche absente : {target[0]}")
            espace = set(as_list(e.fm.get("espace", "")))
            if not espace or not espace <= ESPACES or ("hors-application" in espace and len(espace) > 1):
                hole("espaces", where, "`espace` absent ou invalide : front-office et/ou back-office, ou hors-application seul")
            cited = as_list(e.fm.get("objectifs", ""))
            if not e.transverse and not cited:
                hole("traçabilité", where, "ne sert aucun objectif (`objectifs` vide)")
            for oid in cited:
                if oid == OBLIGATION:
                    if not e.tags & OBLIGATION_TAGS:
                        hole("traçabilité", where, "`obligation` sans tag juridique, securite, rgpd ou fondamentaux : citer l'objectif servi")
                elif oid in served:
                    served[oid].append(e.slug)
                elif objs:
                    hole("traçabilité", where, f"objectif inconnu : {oid}")
        if e.nature == "nfr":
            for s in ("Exigence", "Mesure"):
                if empty(get(e.secs, s)):
                    hole("exigences non fonctionnelles", where, f"`## {s}` absent ou vide : cible chiffrée et façon de la vérifier")
    for oid, serving in served.items():
        if not serving:
            hole("traçabilité", oid, "aucune exigence ne sert cet objectif")

    # Personas : la matrice de couverture tenue par la relecture
    rel = d["relecture"]
    cover = get(rel.secs, "Couverture des personas") if rel else ""
    if d["personas"] and not cover:
        hole("couverture des personas", "cdc/relecture.md", "`## Couverture des personas` absente (relecture à lancer)")
    rows = table_rows(cover)
    for row in rows:
        if len(row) >= 3 and (empty(row[2]) or row[2].lower().startswith("non couvert")):
            hole("couverture des personas", row[0], f"non couvert : {row[1]}")
    for p in d["personas"]:
        needs = len(bullets(get(p.secs, "Besoins"))) + len(bullets(get(p.secs, "Pain points")))
        if not bullets(get(p.secs, "Besoins")):
            hole("couverture des personas", p.rel, "persona sans `## Besoins` : rien à couvrir, rien de prouvé")
        if not cover:
            continue
        judged = sum(1 for row in rows if row and (plain(row[0]).strip().lower() == p.title.lower() or f"{p.slug}.md" in row[0]))
        if judged < needs:
            hole("couverture des personas", p.title, f"{needs} besoin(s) et irritant(s), {judged} ligne(s) dans la couverture")

    # Recueil : ce que l'agent persona a déduit et que l'utilisateur n'a pas confirmé
    for c in [*exigences, *(x for x in (d["modele"], d["glossaire"]) if x)]:
        n = sum(1 for line in c.body.splitlines() if A_CONFIRMER in line.lower())
        if n:
            hole("recueil", c.rel, f"{n} ligne(s) `{A_CONFIRMER}` : déduite(s), jamais confirmée(s) par l'utilisateur")

    # Règles : chaque règle et chaque cas d'erreur a son identifiant, celui que les critères des tickets citent
    for e in exigences:
        ids = [rid for _, _, rid in rule_lines(e.body)]
        if "" in ids:
            hole("règles", e.rel, f"{ids.count('')} règle(s) ou cas d'erreur sans identifiant `RGn`/`CEn` : "
                                  "`cdc numerote` les numérote")
        twice = sorted({rid for rid in ids if rid and ids.count(rid) > 1})
        if twice:
            hole("règles", e.rel, f"identifiant en double : {', '.join(twice)}")
        for ind in indicateurs(e.body):
            manque = [c for c in INDICATEUR_CHAMPS if not re.search(rf"\b{c}\s*:\s*\S", ind["texte"], re.I)]
            if manque:
                hole("indicateurs", e.rel, f"{ind['id'] or 'indicateur'} sans {', '.join(manque)} "
                                           "(`— source : … — période : … — cible ou seuil : … — action : …`)")

    # Modèle métier : cycles de vie, droits, notifications
    model = d["modele"]
    if not model:
        hole("objets métier", "cdc/modele-metier.md", "modèle métier absent : objets, cycles de vie, droits, notifications")
    else:
        for name, text in section_map(model.body).items():
            if not name or name.lower().startswith("notifications"):
                continue
            sub = section_map(text, 3)
            trans = transitions(get(sub, "Cycle de vie"))
            if not trans:
                hole("cycles de vie", name, "aucune transition `- état → état : … — [exigence](…)`")
            sources = {a for a, _, _ in trans}
            targets = {b for _, b, _ in trans}
            for state in sorted(targets - sources - {"(fin)"}):
                hole("cycles de vie", name, f"état « {state} » sans sortie (ni transition, ni `(fin)`)")
            for state in sorted(sources - targets - {"(début)"}):
                hole("cycles de vie", name, f"état « {state} » jamais atteint")
            for a, b, comment in trans:
                links = LINK.findall(comment)
                if not links:
                    hole("cycles de vie", name, f"{a} → {b} : aucune exigence ne porte cette transition")
                for target, _ in links:
                    if not (model.path.parent / target).is_file():
                        hole("cycles de vie", name, f"{a} → {b} : fiche absente {target}")
            rights = table_rows(get(sub, "Droits"))
            if not rights:
                hole("droits (CRUD)", name, "table `### Droits` absente")
            for row in rights:
                for cell in row[1:]:
                    if empty(cell):
                        hole("droits (CRUD)", name, f"droit non décidé pour « {row[0]} »")
                        break
        for row in table_rows(get(model.secs, "Notifications")):
            if any(empty(c) for c in row[:4]):
                hole("notifications", row[0] if row else "?", "destinataire, canal ou moment non décidé")

    # Décisions
    dec = d["decisions"]
    if not dec:
        hole("décisions", "cdc/decisions.md", "journal des décisions absent")
    else:
        for line in get(dec.secs, "Questions ouvertes").splitlines():
            m = re.match(r"^\s*-\s+\*\*(Q\d+)\*\*\s*(.*)$", line)
            if m:
                hole("questions ouvertes", m.group(1), m.group(2).lstrip("—: ")[:140])
    return found


# --- review anomalies ----------------------------------------------------------

def anomalies(d: dict) -> list[dict]:
    """The `- A<n> [passe, gravité, origine] — …` lines of `kb/cdc/relecture.md` § Anomalies."""
    rel = d["relecture"]
    out = []
    for line in (get(rel.secs, "Anomalies") if rel else "").splitlines():
        m = re.match(r"^\s*-\s*(A\d+)\b\s*(?:\[([^\]]*)\])?(.*)$", line)
        if not m:
            continue
        tag = [x.strip() for x in m.group(2).split(",")] if m.group(2) is not None else []
        valid = (len(tag) == 3 and re.fullmatch(r"[pc]\d+", tag[0]) is not None
                 and tag[1] in GRAVITES and tag[2] in ORIGINES)
        rest = m.group(3)
        out.append({"id": m.group(1), "passe": tag[0] if valid else "", "gravite": tag[1] if valid else "",
                    "origine": tag[2] if valid else "", "tagged": bool(tag), "valid": valid,
                    "ouverte": re.search(r"—\s*ouverte\s*$", rest) is not None,
                    "route": next((r for r in ROUTES if f"→ {r}" in rest), "")})
    return out


def revue(found: list[dict], route: str | None = None) -> list[str]:
    """What holds the stage: a tag missing or wrong, a rule of gravity broken, a `bloquante` still open.
    An untagged open anomaly counts as `bloquante`; an untagged closed one is history, left alone."""
    blocking = [a["id"] for a in found if a["ouverte"] and a["gravite"] != "mineure"
                and (route is None or a["route"] == route)]
    if route is not None:
        return [f"anomalies bloquantes → {route} encore `ouverte` : {', '.join(blocking)}"] if blocking else []
    gaps = []
    for a in found:
        if (a["ouverte"] or a["tagged"]) and not a["valid"]:
            gaps.append(f"{a['id']} : sans `[passe, gravité, origine]` valide (ex. `[p1, bloquante, texte]`)")
        elif a["gravite"] == "mineure" and a["route"] != "redaction":
            gaps.append(f"{a['id']} : une `mineure` va → redaction ; s'il manque une information ou une décision, elle est `bloquante`")
        elif a["gravite"] == "mineure" and a["origine"] == "texte" and int(a["passe"][1:]) > 1:
            gaps.append(f"{a['id']} : passe de reprise {a['passe']} : un passage déjà relu (`texte`) ne donne qu'une `bloquante`")
    if blocking:
        gaps.append(f"anomalies bloquantes encore `ouverte` : {', '.join(blocking)}")
    return gaps


def mesure(found: list[dict]) -> str:
    """One row per pass: how many anomalies, how grave, where they came from — the loop above the loop."""
    rows: dict[str, dict[str, int]] = {}
    for a in found:
        r = rows.setdefault(a["passe"] or "non classées", {})
        for k in ("total", a["gravite"], a["origine"], "ouverte" if a["ouverte"] else ""):
            if k:
                r[k] = r.get(k, 0) + 1
    order = sorted(rows, key=lambda k: (k == "non classées", k[:1] != "p", int(k[1:]) if k[1:].isdigit() else 0))
    cols = ["total", *GRAVITES, *ORIGINES, "ouverte"]
    out = ["| Passe | Anomalies | Bloquantes | Mineures | Texte | Correction | Règle Hosa | Ouvertes |",
           "|---|---|---|---|---|---|---|---|"]
    out += [f"| {k} | " + " | ".join(str(rows[k].get(c, 0)) for c in cols) + " |" for k in order]
    out.append("| **Total** | " + " | ".join(str(sum(r.get(c, 0) for r in rows.values())) for c in cols) + " |")
    return "\n".join(out)


# --- assembling --------------------------------------------------------------

def relink(text: str, src: Path, dest: Path) -> str:
    """Rewrite relative .md links written from `src`'s folder so they work from `dest`'s."""
    def sub(m: re.Match) -> str:
        target = (src.parent / m.group(1)).resolve()
        return f"]({Path(os.path.relpath(target, dest.parent)).as_posix()}{m.group(2) or ''})"
    return LINK.sub(sub, text)


def demote(text: str, by: int) -> str:
    return re.sub(r"^(#+) ", lambda m: "#" * (len(m.group(1)) + by) + " ", text, flags=re.M)


def link(c: Concept, dest: Path) -> str:
    return f"[{c.title}]({Path(os.path.relpath(c.path, dest.parent)).as_posix()})"


def plain(text: str) -> str:
    """Links reduced to their label, for table cells."""
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)


def first_line(text: str) -> str:
    for line in text.splitlines():
        line = plain(line.strip().lstrip("-").strip())
        if line:
            return line.replace("|", "/")
    return "—"


def lot_key(e: Concept) -> tuple:
    lot = e.fm.get("lot", "")
    return (int(lot) if lot.isdigit() else 99, PRIORITES.index(e.fm["priorite"]) if e.fm.get("priorite") in PRIORITES else 9)


def ordered(group: list[Concept]) -> list[Concept]:
    """A process comes after the ones its `## Déclencheur` links to."""
    by_slug = {e.slug: e for e in group}
    after = {e.slug: {Path(t).stem for t, _ in LINK.findall(get(e.secs, "Déclencheur"))} & by_slug.keys() for e in group}
    out, seen = [], set()
    def visit(s: str, stack: tuple = ()) -> None:
        if s in seen or s in stack:
            return
        for p in sorted(after[s], key=lambda x: lot_key(by_slug[x])):
            visit(p, stack + (s,))
        seen.add(s)
        out.append(by_slug[s])
    for e in sorted(group, key=lambda e: (lot_key(e), e.title)):
        visit(e.slug)
    return out


def fiche(e: Concept, dest: Path, level: int) -> str:
    meta = " · ".join(x for x in (
        f"priorité **{e.fm.get('priorite', '?')}**", f"lot {e.fm.get('lot', '?')}",
        f"espace {e.fm.get('espace', '?').strip('[]')}", e.fm.get("status", ""),
        ("objectifs " + ", ".join(as_list(e.fm["objectifs"]))) if e.fm.get("objectifs") else "") if x)
    parts = [f"{'#' * level} {e.title}", f"*{e.fm.get('description', '')}*", f"{meta} — fiche : {link(e, dest)}"]
    skipped = []
    for name, text in e.secs.items():
        if not name:
            continue
        if name.lower().startswith("contraintes"):
            skipped.append(f"{name.lower()} : {sum(1 for l in text.splitlines() if l.strip().startswith('-'))}")
            continue
        parts.append(f"{'#' * (level + 1)} {name}\n{relink(demote(text, level - 1), e.path, dest)}")
    if skipped:
        parts.append(f"> Détail technique en annexe ({', '.join(skipped)}) : voir la fiche.")
    return "\n\n".join(parts) + "\n"


def assemble(d: dict, kb: Path, found: list[dict[str, str]]) -> str:
    dest = kb / OUT
    ident = d["identity"]
    ex = d["exigences"]
    procs = [e for e in ex if e.nature == "processus"]
    nfrs = [e for e in ex if e.nature == "nfr"]
    contraintes = [e for e in ex if e.nature == "contrainte"]
    stable = sum(1 for e in ex if e.fm.get("status") == "stable")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    status = "stable" if ex and stable == len(ex) and not found else "draft"
    name = ident.title if ident else "projet"
    def isec(prefix: str) -> str:
        return relink(demote(get(ident.secs, prefix), 1), ident.path, dest) if ident and not empty(get(ident.secs, prefix)) else "_À compléter._"

    signed = sorted({f"{m.group(1)}, {m.group(2)}" for e in ex
                     if (m := re.search(r"by:\s*\"?(human:[^,\"}]+)\"?\s*,\s*at:\s*\"?(\d{4}-\d\d-\d\d)", e.fm.get("verified", "")))})
    out = [f"""---
type: Cahier des charges
title: "Cahier des charges — {name}"
description: "Le cahier des charges en un document, assemblé depuis les fiches de kb/cdc : {len(ex)} exigences, {len(found)} trou(s)"
tags: [cdc]
status: {status}
generated: {{ by: process:hosa-cdc, at: {now} }}
---
> Document généré par `cdc.py assemble` depuis les fiches. Ne le corrige pas ici : corrige la fiche, puis régénère.

## 0. Fiche du document
| | |
|---|---|
| Projet | {name} |
| Généré le | {now[:10]} |
| Statut | {status} |
| Exigences | {len(ex)} ({stable} stables, {len(ex) - stable} en brouillon) |
| Complétude | {"complet" if not found else f"{len(found)} trou(s), voir § 12"} |
| Validé par | {"; ".join(signed) if signed else "pas encore signé"} |
| Historique | [journal du cahier des charges](../cdc/log.md) |

## 1. Contexte et enjeux
{isec("Contexte et enjeux")}

{isec("Description")}

## 2. Objectifs et indicateurs"""]
    objs = objectives(ident)
    if objs:
        out.append("| Id | Objectif | Indicateur | Cible | Mesure | Exigences |\n|---|---|---|---|---|---|")
        for o in objs:
            serving = [link(e, dest) for e in procs if o["id"] in as_list(e.fm.get("objectifs", ""))]
            out.append(f"| {o['id']} | {o['objectif']} | {o['indicateur']} | {o['cible']} | {o['mesure']} | {', '.join(serving) or '**aucune**'} |")
    else:
        out.append("_Aucun objectif mesurable : le projet ne peut pas prouver sa réussite._")

    out.append("\n## 3. Périmètre\n### Lots")
    kind = {"processus": "processus", "nfr": "non fonctionnelle", "contrainte": "contrainte"}
    out.append("| Lot | Priorité | Exigence | Nature |\n|---|---|---|---|")
    for e in sorted(ex, key=lambda e: (lot_key(e), list(kind).index(e.nature), e.title)):
        out.append(f"| {e.fm.get('lot') or '**non affecté**'} | {e.fm.get('priorite') or '**aucune**'} | {link(e, dest)} | {kind[e.nature]} |")
    out += ["\n### Hors périmètre", isec("Non-objectifs"), "\n### Contraintes du projet", isec("Contraintes"),
            "\n### Échéances et budget", isec("Échéances")]

    out.append("\n## 4. Acteurs\n| Persona | Qui c'est |\n|---|---|")
    out += [f"| {link(p, dest)} | {p.fm.get('description', '')} |" for p in d["personas"]]
    out.append("\nCe que chaque rôle fait sur chaque objet : § 6, tables « Droits ».")

    out.append("\n## 5. Processus métier\n### 5.1 Cartographie")
    domaines: dict[str, list[Concept]] = {}
    for e in procs:
        domaines.setdefault(e.fm.get("domaine") or "Sans domaine", []).append(e)
    order = sorted(domaines, key=lambda k: (k == "Sans domaine", min(lot_key(e) for e in domaines[k]), -len(domaines[k])))
    for dom in order:
        out.append(f"\n**{dom}**\n\n| # | Processus | Déclencheur | Responsable | Priorité | Lot | Statut |\n|---|---|---|---|---|---|---|")
        for i, e in enumerate(ordered(domaines[dom]), 1):
            out.append(f"| {i} | {link(e, dest)} | {first_line(get(e.secs, 'Déclencheur'))} | {first_line(get(e.secs, 'Responsable'))} "
                       f"| {e.fm.get('priorite', '—')} | {e.fm.get('lot', '—')} | {e.fm.get('status', '')} |")
    for n, dom in enumerate(order, 2):
        out.append(f"\n### 5.{n} {dom}")
        out += [fiche(e, dest, 4) for e in ordered(domaines[dom])]

    out.append("\n## 6. Objets métier")
    model = d["modele"]
    out.append(relink(demote(model.body.strip(), 1), model.path, dest) if model else "_Modèle métier absent (`kb/cdc/modele-metier.md`)._")
    if d["glossaire"]:
        out += ["\n### Glossaire", relink(demote(get(d["glossaire"].secs, "Termes"), 2), d["glossaire"].path, dest)]

    out.append("\n## 7. Exigences non fonctionnelles")
    out += [fiche(e, dest, 3) for e in sorted(nfrs, key=lot_key)] or ["_Aucune._"]

    out.append("\n## 8. Contraintes juridiques et de sécurité\nCe que la loi et la sécurité imposent au produit. Le détail est dans les fiches et les analyses (annexes).\n")
    out.append("| Contrainte | Ce qu'elle impose | Priorité | Lot |\n|---|---|---|---|")
    out += [f"| {link(e, dest)} | {e.fm.get('description', '')} | {e.fm.get('priorite', '—')} | {e.fm.get('lot', '—')} |" for e in contraintes]
    per_proc = [(e, [n for n in e.secs if n.lower().startswith("contraintes")]) for e in procs]
    out.append("\nDans les processus du § 5 : " + ("; ".join(
        f"{link(e, dest)} ({', '.join(n.lower() for n in names)})" for e, names in per_proc if names) or "aucune."))

    out += ["\n## 9. Hypothèses, dépendances et risques", isec("Hypothèses")]

    out.append("\n## 10. Critères de recette globaux")
    if objs:
        out += [f"- **{o['id']} — {o['objectif']}.** Indicateur : {o['indicateur']}. Cible : {o['cible']}. Mesure : {o['mesure']}." for o in objs]
    else:
        out.append("_Sans objectif mesurable, pas de critère global._")
    out.append("- Chaque exigence est recettée par les critères d'acceptation de ses tickets (`backlog`).")

    out.append("\n## 11. Décisions et questions ouvertes")
    dec = d["decisions"]
    out.append(relink(demote(dec.body.strip(), 1), dec.path, dest) if dec else "_Journal absent (`kb/cdc/decisions.md`)._")

    out.append("\n## 12. Contrôle de complétude")
    if found:
        out.append(f"**{len(found)} trou(s).** Le cahier des charges ne se signe pas tant qu'il en reste.\n\n| Matrice | Où | Trou |\n|---|---|---|")
        out += [f"| {h['matrice']} | {h['où']} | {plain(h['trou'])} |" for h in found]
    else:
        out.append("Complet : chaque matrice est remplie.")

    out.append("\n## Annexes\n### A. Fiches des contraintes")
    out += [f"- {link(e, dest)} — {e.fm.get('description', '')}" for e in contraintes] or ["- Aucune."]
    out.append("\n### B. Analyses et revues")
    out += [f"- {link(c, dest)} — {c.fm.get('description', '')}" for c in d["annexes"]] or ["- Aucune."]
    out.append("\n### C. Comptes rendus d'interview")
    out += [f"- {link(c, dest)} — {c.fm.get('description', '')}" for c in d["interviews"]] or ["- Aucun."]
    return "\n".join(out).rstrip() + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Assemble the cahier des charges and check its completeness.")
    ap.add_argument("command", choices=["check", "assemble", "revue", "mesure", "numerote"])
    ap.add_argument("kb", type=Path)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--route", choices=ROUTES)
    a = ap.parse_args(argv)
    kb = a.kb.resolve()
    if not (kb / "cdc").is_dir():
        print(f"error: {a.kb} has no cdc/ bundle", file=sys.stderr)
        return 2
    d = load(kb)
    if a.command == "revue":
        gaps = revue(anomalies(d), a.route)
        print("\n".join(gaps) if gaps else "Revue conforme : aucune anomalie bloquante ouverte.")
        return 1 if gaps else 0
    if a.command == "mesure":
        print(mesure(anomalies(d)))
        return 0
    if a.command == "numerote":
        done = [(e.rel, n) for e in d["exigences"] if (n := numerote(e.path))]
        print(f"{sum(n for _, n in done)} règle(s) et cas d'erreur numéroté(s) dans {len(done)} fiche(s)"
              + "".join(f"\n- {rel} : {n}" for rel, n in done))
        return 0
    found = holes(d, kb)
    if a.command == "assemble":
        (kb / OUT).write_text(assemble(d, kb, found), encoding="utf-8")
        print(f"Écrit : {OUT} — {len(d['exigences'])} exigences, {len(found)} trou(s).")
        return 0
    if a.json:
        print(json.dumps(found, ensure_ascii=False, indent=1))
    elif not found:
        print("Complet : aucun trou.")
    else:
        print(f"{len(found)} trou(s) :")
        by: dict[str, list[dict]] = {}
        for h in found:
            by.setdefault(h["matrice"], []).append(h)
        for m, hs in by.items():
            print(f"\n## {m} ({len(hs)})")
            print("\n".join(f"- {h['où']} — {h['trou']}" for h in hs))
    return 1 if found else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
