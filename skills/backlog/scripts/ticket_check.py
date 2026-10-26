#!/usr/bin/env python3
"""Check that Hosa tickets are complete — ready to be planned and executed.

A ticket is complete when it has, in its body:
  - a user story ("En tant que ...") and a "Lié à :" line,
  - a "## Critères d'acceptation" section with at least one scenario,
  - "## Note technique (senior dev)", "## Placement architecture (architecte)",
    "## Placement interface (UX/UI)", "## Note sécurité (expert
    cybersécurité)" and "## Note juridique (expert conformité)" sections
    holding a real note, not `backlog`'s "pas encore …" fallback line,
  - a `depends_on` (if any) naming existing tickets, without a cycle, none
    ranked after this ticket (`priority`),
  - grounded notes (`backlog`'s Grounding Rule): every note carries its
    labelled bullets, none still `inconnu — …` and none a structural gap
    `à créer — owner: …`,
  - each abuse case of the security note and each legal constraint of the
    legal note tied to an acceptance criterion (`→ CAn`), and every `→ CAn`
    naming a criterion the ticket has,
  - every `dir/file.ext` its technical and architecture notes cite as existing
    (no `à créer` on the line) present in the project — or created by a ticket
    it `depends_on`.

Run:  python ticket_check.py <kb-dir> [ticket.md ...]
      No ticket given → every `state: todo` ticket in <kb-dir>/tickets/.
Exit: 0 all complete, 1 at least one incomplete, 2 bad invocation.
Stdlib only, so any Python 3.9+ runs it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SECTIONS = {
    "## Critères d'acceptation": None,
    "## Note technique (senior dev)": "Stack pas encore choisie",
    "## Placement architecture (architecte)": "Architecture pas encore scaffoldée",
    "## Placement interface (UX/UI)": "Interface pas encore scaffoldée",
    "## Note sécurité (expert cybersécurité)": "Analyse de sécurité pas encore faite",
    "## Note juridique (expert conformité)": "Analyse juridique pas encore faite",
}


BULLETS = {
    "## Note technique (senior dev)": ("Contrat", "Règles et validations", "Tests à écrire", "Complexité"),
    "## Placement architecture (architecte)": ("Module/couche", "Fichiers touchés", "Données"),
    "## Placement interface (UX/UI)": ("Écran / route", "Composants", "États"),
    "## Note sécurité (expert cybersécurité)": ("Règles", "Cas d'abus", "Contrôle d'accès", "Journalisation", "Données sensibles"),
    "## Note juridique (expert conformité)": ("Contraintes", "Données personnelles", "Hors logiciel"),
}

# Bullets whose every item is built and tested as an acceptance criterion, not left to the audit or the recette.
TRACED = {
    "## Note sécurité (expert cybersécurité)": "Cas d'abus",
    "## Note juridique (expert conformité)": "Contraintes",
}
CA_REF = re.compile(r"(?:→|->)\s*CA(\d+)")
TOO_MANY_CRITERIA = 10  # pilot2: 16 criteria and two variants in one ticket estimated "simple"


def bullet_items(content: str, label: str) -> list[str]:
    """The inline text and the sub-items of the labelled bullet `- **<label>** : …`."""
    m = re.search(rf"^\s*[-*]\s+\*\*{re.escape(label)}\*\*\s*:[ \t]*(.*)$", content, re.M)
    if not m:
        return []
    items = [m.group(1).strip()] if m.group(1).strip() else []
    for line in content[m.end():].splitlines()[1:]:
        if re.match(r"^[-*]\s", line) or re.match(r"^#{1,2} ", line):
            break
        if re.match(r"^\s+[-*]\s+\S", line):
            items.append(line.strip()[2:].strip())
    return items


def untraced(heading: str, content: str) -> list[str]:
    label = TRACED.get(heading)
    if not label:
        return []
    return [f"`{heading[3:]}` : « {item[:60]} » sans critère (`→ CAn`)"
            for item in bullet_items(content, label)
            if not re.match(r"aucun", item, re.I) and not CA_REF.search(item)]


def grounding(heading: str, content: str) -> list[str]:
    out = []
    for label in BULLETS.get(heading, ()):
        if not re.search(rf"^\s*[-*]\s+\*\*{re.escape(label)}\*\*\s*:", content, re.M):
            out.append(f"`{heading[3:]}` : puce « {label} » absente")
    out += untraced(heading, content)
    for line in content.splitlines():
        if re.search(r"\binconnu\s+—", line):
            out.append(f"`{heading[3:]}` : « {line.strip()[:60]} » encore inconnu")
        elif re.search(r"à créer\s+—\s+owner\s*:", line):
            out.append(f"`{heading[3:]}` : manque structurel « {line.strip()[:60]} »")
    return out


def split(text: str) -> tuple[str, str]:
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    return (m.group(1), m.group(2)) if m else ("", text)


def field(front: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.*?)\s*$", front, re.M)
    return m.group(1).strip("'\"") if m else ""


def section(body: str, heading: str) -> str | None:
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == heading:
            out = []
            for nxt in lines[i + 1:]:
                if re.match(r"^#{1,2} ", nxt):
                    break
                out.append(nxt)
            return "\n".join(out).strip()
    return None


def depends_on(front: str) -> list[str]:
    m = re.search(r"^depends_on:[ \t]*(.*)$", front, re.M)
    if not m:
        return []
    value = m.group(1).strip()
    if value.startswith("["):
        items = value.strip("[]").split(",")
    elif value:
        items = [value]
    else:  # block list
        items = re.findall(r"^\s+-\s+(.+)$", re.split(r"\n(?=\S)", front[m.end():], maxsplit=1)[0], re.M)
    return [i.strip().strip("'\"").removesuffix(".md").split("/")[-1] for i in items if i.strip()]


def cycle_from(slug: str, tickets: Path, seen: tuple = ()) -> list[str] | None:
    if slug in seen:
        return list(seen[seen.index(slug):]) + [slug]
    f = tickets / f"{slug}.md"
    if not f.is_file():
        return None
    for dep in depends_on(split(f.read_text(encoding="utf-8"))[0]):
        found = cycle_from(dep, tickets, seen + (slug,))
        if found:
            return found
    return None


PATH = re.compile(r"`([\w.-]+(?:/[\w.-]+)+\.\w+)(?::[\w.]+)?`")  # `dir/file.ext` or `dir/file.ext:symbol`
CITED = ("## Note technique (senior dev)", "## Placement architecture (architecte)")


def creators(tickets: Path) -> dict[str, str]:
    """{path: slug of the ticket whose notes mark it `à créer`}."""
    out = {}
    for f in sorted(tickets.glob("*.md")):
        body = split(f.read_text(encoding="utf-8"))[1]
        for heading in CITED:
            for line in (section(body, heading) or "").splitlines():
                if "à créer" in line:
                    for p in PATH.findall(line):
                        out.setdefault(p, f.stem)
    return out


def phantom_paths(path: Path, front: str, body: str) -> list[str]:
    """Paths cited as existing that the project doesn't have: the ticket that creates
    them must be a `depends_on`, or the sprint takes this ticket without its creator."""
    kb = path.parent.parent
    if kb.name != "kb" or kb.parent.name != ".hosa":
        return []
    root, deps, made, out = kb.parent.parent, set(depends_on(front)), None, []
    for heading in CITED:
        for line in (section(body, heading) or "").splitlines():
            if "à créer" in line:
                continue
            for p in PATH.findall(line):
                if (root / p).exists() or p.startswith(("kb/", ".hosa/")):  # KB paths aren't project files
                    continue
                made = creators(path.parent) if made is None else made
                by = made.get(p)
                if by == path.stem or by in deps:
                    continue
                gap = (f"`{p}` cité comme existant, créé par `{by}` → ajouter `depends_on: [{by}]`" if by
                       else f"`{p}` cité comme existant, absent du projet → `à créer` ou chemin à corriger")
                if gap not in out:
                    out.append(gap)
    return out


def gaps(path: Path) -> list[str]:
    front, body = split(path.read_text(encoding="utf-8"))
    if field(front, "type") != "Ticket":
        return ["pas un `Ticket` (type manquant ou différent)"]
    missing = []
    if not re.search(r"^En tant que\b", body, re.M):
        missing.append("story « En tant que … » absente")
    if not re.search(r"^Lié à\s*:", body, re.M):
        missing.append("ligne « Lié à : » absente")
    for heading, fallback in SECTIONS.items():
        content = section(body, heading)
        if content is None:
            missing.append(f"section `{heading}` absente")
        elif not content:
            missing.append(f"section `{heading}` vide")
        elif fallback and content.startswith(fallback):
            missing.append(f"section `{heading}` encore au texte d'attente")
        elif fallback is None and not re.search(r"^\s*[-*] \S", content, re.M):
            missing.append(f"section `{heading}` sans aucun scénario")
        else:
            missing += grounding(heading, content)
    criteria = set(re.findall(r"^\s*[-*]\s+CA(\d+)\b", section(body, "## Critères d'acceptation") or "", re.M))
    for heading in list(SECTIONS)[1:]:
        cited = (n for tail in re.findall(r"(?:→|->)(.*)", section(body, heading) or "")
                 for n in re.findall(r"\bCA(\d+)", tail))
        for n in dict.fromkeys(cited):
            if n not in criteria:
                missing.append(f"`{heading[3:]}` cite `CA{n}`, absent des critères d'acceptation")
    for dep in depends_on(front):
        if not (path.parent / f"{dep}.md").is_file():
            missing.append(f"`depends_on` cite `{dep}`, ticket introuvable")
    missing += phantom_paths(path, front, body)
    missing += late_dependencies(path, front)
    loop = cycle_from(path.stem, path.parent)
    if loop:
        missing.append("dépendances en boucle : " + " → ".join(loop))
    if not field(front, "priority"):
        missing.append("(info) pas de `priority` — passera après les tickets priorisés")
    if len(criteria) > TOO_MANY_CRITERIA:
        missing.append(f"(info) {len(criteria)} critères — plusieurs variantes ou règles : à découper ?")
    return missing


def rank(front: str) -> float | None:
    try:
        return float(field(front, "priority"))
    except ValueError:
        return None


def late_dependencies(path: Path, front: str) -> list[str]:
    """A dependency still to build that ranks after this ticket: `sprint` can't plan this one
    until it gets there (pilot2: the security log at 43, used by tickets at 7 to 17)."""
    own, out = rank(front), []
    if own is None:
        return out
    for dep in depends_on(front):
        f = path.parent / f"{dep}.md"
        if not f.is_file():
            continue
        dep_front = split(f.read_text(encoding="utf-8"))[0]
        if field(dep_front, "state") == "done":
            continue
        theirs = rank(dep_front)
        if theirs is None or theirs > own:
            where = f"priorité {field(dep_front, 'priority')}" if theirs is not None else "sans priorité"
            out.append(f"dépend de `{dep}` ({where}), classé après lui → remonter `{dep}` avant {field(front, 'priority')}")
    return out


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        print("usage: ticket_check.py <kb-dir> [ticket.md ...]", file=sys.stderr)
        return 2
    kb = Path(argv[0])
    if not kb.is_dir():
        print(f"error: {kb} is not a directory", file=sys.stderr)
        return 2
    if argv[1:]:
        paths = [Path(p) for p in argv[1:]]
    else:
        paths = [p for p in sorted((kb / "tickets").glob("*.md"))
                 if p.name not in ("index.md", "log.md")
                 and field(split(p.read_text(encoding="utf-8"))[0], "state") == "todo"]
    incomplete = 0
    for p in paths:
        if not p.is_file():
            print(f"✗ {p} — fichier introuvable")
            incomplete += 1
            continue
        found = gaps(p)
        blocking = [g for g in found if not g.startswith("(info)")]
        if blocking:
            incomplete += 1
            print(f"✗ {p.name} — incomplet : " + " ; ".join(found))
        else:
            print(f"✓ {p.name} — complet" + (f" ({found[0]})" if found else ""))
    print(f"{len(paths) - incomplete}/{len(paths)} ticket(s) complet(s)")
    return 1 if incomplete else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
