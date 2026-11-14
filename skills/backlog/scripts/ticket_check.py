#!/usr/bin/env python3
"""Check that Hosa tickets are complete — ready to be planned and executed.

A ticket is complete when it has, in its body:
  - a user story ("En tant que ...") and a "Lié à :" line,
  - a "## Critères d'acceptation" section with at least one scenario and
    10 at most (more: two variants or rules in one ticket — split it),
  - "## Note technique (senior dev)", "## Placement architecture (architecte)",
    "## Placement interface (UX/UI)", "## Note sécurité (expert
    cybersécurité)" and "## Note juridique (expert conformité)" sections
    holding a real note, not `backlog`'s "pas encore …" fallback line — or,
    for the security and the legal note, the line `Non applicable — étape …`
    when the progress plan marks that stage `non applicable`,
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
    it `depends_on`,
  - every rule, error case or indicator a criterion cites (`- CA1 [RG2, CE1] — …`,
    `- CA2 [IN1] — …`) in force in an exigence of its `Lié à :` line, and a
    criterion citing an indicator stating its expected value (a number).

Run:  python ticket_check.py <kb-dir> [ticket.md ...]
      No ticket given → every `state: todo` ticket in <kb-dir>/tickets/.
      python ticket_check.py <kb-dir> --ecartees [ticket.md ...]
      First writes that `Non applicable` line in the tickets whose security or
      legal note is absent, empty or on its fallback line while the plan marks
      the stage `non applicable` — no agent needed — then checks.
      python ticket_check.py <kb-dir> --regles
      The rules × criteria matrix, over every ticket: each `RGn`/`CEn`/`INn` of an
      exigence is cited by a criterion of one of its tickets (exit 1 otherwise).
      An exigence whose tickets cite no rule at all predates the ids: skipped.
      python ticket_check.py <kb-dir> --repetes
      The criteria a `todo` ticket restates from another ticket of the same exigence
      (70 % of their words in common): one ticket owns a behaviour (exit 1 otherwise).
Exit: 0 all complete, 1 at least one incomplete, 2 bad invocation.
Stdlib only, so any Python 3.9+ runs it.
"""
from __future__ import annotations

import functools
import importlib.util
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

# The stage each note waits for. Set aside by the user (`avancement.py skip`), its note is one line read from the plan:
# rieki skipped `juridique` and 107 tickets stayed refused until a 3-bullet note was written by hand in each.
STAGE = {
    "## Note sécurité (expert cybersécurité)": "securite",
    "## Note juridique (expert conformité)": "juridique",
}
SKIPPED_NOTE = "Non applicable"
SKIPPED_ROW = re.compile(r"^\|\s*`?([\w-]+)`?\s*\|\s*non applicable\s*\|[^|]*\|\s*(.*?)\s*\|\s*$", re.M)


def skipped_stages(kb: Path) -> dict[str, str]:
    """{stage: detail} of the stages the progress plan marks `non applicable`."""
    plan = kb / "project" / "avancement.md"
    return dict(SKIPPED_ROW.findall(plan.read_text(encoding="utf-8"))) if plan.is_file() else {}


def skipped_note(stage: str, detail: str) -> str:
    return f"{SKIPPED_NOTE} — étape `{stage}` écartée" + (f" : {detail}" if detail else "")


def write_skipped(path: Path, skipped: dict[str, str]) -> list[str]:
    """Write the `Non applicable` line of each skipped stage whose note is absent, empty or on its
    fallback line. Returns the headings written. A real note is never touched."""
    text = path.read_text(encoding="utf-8")
    body = split(text)[1]
    head, written = text[:len(text) - len(body)], []
    for heading, stage in STAGE.items():
        if stage not in skipped:
            continue
        content, note = section(body, heading), skipped_note(stage, skipped[stage])
        if content is None:
            body = body.rstrip("\n") + f"\n\n{heading}\n{note}\n"
        elif not content or content.startswith(SECTIONS[heading]):
            lines = body.splitlines()
            i = next(k for k, line in enumerate(lines) if line.strip() == heading)
            j = next((k for k in range(i + 1, len(lines)) if re.match(r"^#{1,2} ", lines[k])), len(lines))
            body = "\n".join(lines[:i + 1] + [note] + ([""] if j < len(lines) else []) + lines[j:]) + "\n"
        else:
            continue
        written.append(heading)
    if written:
        path.write_text(head + body, encoding="utf-8", newline="\n")
    return written


# Bullets whose every item is built and tested as an acceptance criterion, not left to the audit or the recette.
TRACED = {
    "## Note sécurité (expert cybersécurité)": "Cas d'abus",
    "## Note juridique (expert conformité)": "Contraintes",
}
CA_REF = re.compile(r"(?:→|->)\s*CA(\d+)")
# what a criterion is, for every Hosa script: avancement.py reads it from here, so qa-plan counts the same ones
CRITERION = re.compile(r"^\s*[-*]\s+(CA\d+)\b", re.M)
TOO_MANY_CRITERIA = 10  # pilot2: 16 criteria and two variants in one ticket estimated "simple"


# `- CA1 [RG2, CE1] — …`: the rules and error cases of the linked exigence this criterion proves
RULE_REF = re.compile(r"^\s*[-*]\s+CA\d+\s*\[([^\]]*)\]", re.M)
EXIGENCE_LINK = re.compile(r"\(\.\./cdc/([^)#\s]+)\.md")


def cited_rules(content: str | None) -> set[str]:
    return {r for inside in RULE_REF.findall(content or "") for r in re.findall(r"\b(?:RG|CE|IN)\d+\b", inside)}


# `- CA2 [IN1] — Étant donné le jeu de test, le tableau de bord affiche 12 commandes en retard`
INDICATOR_CRITERION = re.compile(r"^\s*[-*]\s+(CA\d+)\s*\[([^\]]*\bIN\d+\b[^\]]*)\](.*)$", re.M)


def indicators_without_value(body: str) -> list[str]:
    """A criterion that cites an indicator states the value it must show on the test dataset: a wrong number is
    how a dashboard fails, and only an expected value catches it."""
    out = []
    for ca, refs, text in INDICATOR_CRITERION.findall(section(body, "## Critères d'acceptation") or ""):
        if not re.search(r"\d", text):
            ids = ", ".join(re.findall(r"\bIN\d+\b", refs))
            out.append(f"{ca} cite {ids} sans la valeur attendue sur le jeu de test (un nombre)")
    return out


def linked_exigences(body: str) -> list[str]:
    m = re.search(r"^Lié à\s*:(.*)$", body, re.M)
    return EXIGENCE_LINK.findall(m.group(1)) if m else []


@functools.cache
def cdc():
    """`cdc.py`, the one definition of a rule's id — or None when it can't be loaded (never this check's failure)."""
    try:
        path = Path(__file__).resolve().parents[2] / "redaction" / "scripts" / "cdc.py"
        spec = importlib.util.spec_from_file_location("cdc", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


def rules_of(kb: Path, slug: str) -> list[str] | None:
    """The `RGn`/`CEn` in force in `kb/cdc/<slug>.md`; None when the fiche or `cdc.py` can't be read."""
    f = kb / "cdc" / f"{slug}.md"
    if cdc() is None or not f.is_file():
        return None
    return cdc().rule_ids(f.read_text(encoding="utf-8"))


def unknown_rules(kb: Path, body: str) -> list[str]:
    """A criterion that cites a rule its exigences don't have: a wrong number, or a rule since dropped."""
    cited = cited_rules(section(body, "## Critères d'acceptation"))
    known = [rules_of(kb, slug) for slug in linked_exigences(body)]
    if not cited or not known or None in known:
        return []
    return [f"un critère cite `{r}`, absent de l'exigence liée (ou retiré)"
            for r in sorted(cited - {r for ids in known for r in ids})]


def rule_coverage(kb: Path) -> list[str]:
    """Each numbered rule and error case of an exigence, cited by a criterion of one of its tickets — the cell
    the judge can't see: it reads one ticket at a time, and a rule no ticket took is in none of them.
    An exigence none of whose tickets cites a rule was sliced before the ids: left alone."""
    cited: dict[str, set[str]] = {}
    for f in sorted((kb / "tickets").glob("*.md")) if (kb / "tickets").is_dir() else []:
        front, body = split(f.read_text(encoding="utf-8"))
        if field(front, "type") != "Ticket":
            continue
        for slug in linked_exigences(body):
            cited.setdefault(slug, set()).update(cited_rules(section(body, "## Critères d'acceptation")))
    out = []
    for slug, got in sorted(cited.items()):
        ids = rules_of(kb, slug) or []
        lacking = [r for r in ids if r not in got]
        if lacking and got & set(ids):
            out.append(f"✗ cdc/{slug}.md — {', '.join(lacking)} : aucun critère de ses tickets ne les cite "
                       f"(`- CAn [{lacking[0]}] — …`)")
    return out


# One behaviour, one ticket. Rieki: about 7 criteria per ticket whatever it covered, and 54 criteria of 34 `todo` tickets
# restated another ticket's — « Annuler » n'enregistre rien, the same escaping, one abuse case copied on 3 style tickets.
# Pilot2, sliced 5 times coarser: 4. 70 %: every pair sampled on rieki at that level was a real repeat.
REPEATED = 0.7
REPEATED_MIN_WORDS = 6  # « CA3 — refus » shares its few words with any other refusal
CRITERION_TEXT = re.compile(r"^\s*[-*]\s+(CA\d+)\b[^\n—]*—\s*(.+)$", re.M)
STOPWORDS = frozenset("le la les l un une des de du d et à au aux en est sont il elle ils quand alors étant donné "
                      "dans sur par pour que qui ne n pas son sa ses ce cette ces avec se s y ou".split())


def words(text: str) -> frozenset[str]:
    """A criterion's words: code spans kept whole (they tell two screens apart), numbers neutralised, stopwords out."""
    text = text.lower()
    code = {"`" + c for c in re.findall(r"`([^`]+)`", text)}
    text = re.sub(r"\d+(?:[.,]\d+)*", "0", re.sub(r"`[^`]+`", " ", text))
    return frozenset(w for w in re.findall(r"[0-9a-zàâçéèêëîïôûùüÿœæ_]+", text) if w not in STOPWORDS) | code


def repeated_criteria(kb: Path) -> list[str]:
    """Each criterion of a `todo` ticket that another ticket of the same exigence already states: the judge reads one
    ticket at a time and can't see it. A `done` ticket counts as the owner, never as the one to fix. A `depends_on`
    between the two names the owner: the other keeps only the criterion that checks its screen uses it."""
    by: dict[str, list[tuple[str, str, bool, frozenset[str]]]] = {}
    deps: dict[str, set[str]] = {}
    for f in sorted((kb / "tickets").glob("*.md")) if (kb / "tickets").is_dir() else []:
        front, body = split(f.read_text(encoding="utf-8"))
        if field(front, "type") != "Ticket":
            continue
        todo, deps[f.stem] = field(front, "state") == "todo", set(depends_on(front))
        for slug in linked_exigences(body):
            by.setdefault(slug, []).extend((f.stem, ca, todo, words(text)) for ca, text in
                                           CRITERION_TEXT.findall(section(body, "## Critères d'acceptation") or ""))
    out, seen = [], set()
    for slug, items in sorted(by.items()):
        for i, (a, ca, todo_a, wa) in enumerate(items):
            for b, cb, todo_b, wb in items[i + 1:]:
                if (a == b or not (todo_a or todo_b) or min(len(wa), len(wb)) < REPEATED_MIN_WORDS
                        or b in deps.get(a, ()) or a in deps.get(b, ())):
                    continue
                share = len(wa & wb) / len(wa | wb)
                if share >= REPEATED and (pair := frozenset({(a, ca), (b, cb)})) not in seen:  # a ticket of 2 exigences: once
                    seen.add(pair)
                    out.append(f"✗ cdc/{slug}.md — `{a}` {ca} ≈ `{b}` {cb} ({share:.0%} de mots communs) : un seul "
                               "ticket porte ce comportement ; l'autre le retire, ou le met en `depends_on` et ne garde "
                               "que son branchement (ou la définition de terminé, si chaque écran le doit)")
    return out


def criteria_ids(content: str | None) -> list[str]:
    """The `CAn` of a `## Critères d'acceptation` section, in order, once each."""
    return list(dict.fromkeys(CRITERION.findall(content or "")))


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
    missing, skipped = [], skipped_stages(path.parent.parent)
    if not re.search(r"^En tant qu(?:e\b|['’])", body, re.M):  # « En tant qu'administrateur » is a story too (rieki)
        missing.append("story « En tant que … » absente")
    if not re.search(r"^Lié à\s*:", body, re.M):
        missing.append("ligne « Lié à : » absente")
    for heading, fallback in SECTIONS.items():
        content = section(body, heading)
        if content is None:
            missing.append(f"section `{heading}` absente")
        elif not content:
            missing.append(f"section `{heading}` vide")
        elif heading in STAGE and content.startswith(SKIPPED_NOTE):
            if STAGE[heading] not in skipped:
                missing.append(f"section `{heading}` « {SKIPPED_NOTE} » alors que le plan d'avancement "
                               f"n'écarte pas l'étape `{STAGE[heading]}`")
        elif fallback and content.startswith(fallback):
            missing.append(f"section `{heading}` encore au texte d'attente" + (
                f" — étape `{STAGE[heading]}` écartée : `ticket_check <kb> --ecartees` écrit la note"
                if STAGE.get(heading) in skipped else ""))
        elif fallback is None and not re.search(r"^\s*[-*] \S", content, re.M):
            missing.append(f"section `{heading}` sans aucun scénario")
        else:
            missing += grounding(heading, content)
    criteria = {c[2:] for c in criteria_ids(section(body, "## Critères d'acceptation"))}
    for heading in list(SECTIONS)[1:]:
        cited = (n for tail in re.findall(r"(?:→|->)(.*)", section(body, heading) or "")
                 for n in re.findall(r"\bCA(\d+)", tail))
        for n in dict.fromkeys(cited):
            if n not in criteria:
                missing.append(f"`{heading[3:]}` cite `CA{n}`, absent des critères d'acceptation")
    for dep in depends_on(front):
        if not (path.parent / f"{dep}.md").is_file():
            missing.append(f"`depends_on` cite `{dep}`, ticket introuvable")
    missing += unknown_rules(path.parent.parent, body)
    missing += indicators_without_value(body)
    missing += phantom_paths(path, front, body)
    missing += late_dependencies(path, front)
    loop = cycle_from(path.stem, path.parent)
    if loop:
        missing.append("dépendances en boucle : " + " → ".join(loop))
    if not field(front, "priority"):
        missing.append("(info) pas de `priority` — passera après les tickets priorisés")
    if len(criteria) > TOO_MANY_CRITERIA:
        missing.append(f"{len(criteria)} critères, {TOO_MANY_CRITERIA} au plus — plusieurs variantes ou règles : "
                       "découper le ticket")
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
        print("usage: ticket_check.py <kb-dir> [--ecartees] [ticket.md ...] | <kb-dir> --regles | <kb-dir> --repetes",
              file=sys.stderr)
        return 2
    fill = "--ecartees" in argv
    argv = [a for a in argv if a != "--ecartees"]
    kb = Path(argv[0])
    if not kb.is_dir():
        print(f"error: {kb} is not a directory", file=sys.stderr)
        return 2
    if "--regles" in argv:
        lacking = rule_coverage(kb)
        print("\n".join(lacking) if lacking else "Règles : chaque règle numérotée d'une exigence découpée est citée par un critère.")
        return 1 if lacking else 0
    if "--repetes" in argv:
        repeated = repeated_criteria(kb)
        print("\n".join(repeated) if repeated else "Répétitions : aucun critère d'un ticket `todo` ne répète un autre ticket de son exigence.")
        return 1 if repeated else 0
    if argv[1:]:
        paths = [Path(p) for p in argv[1:]]
    else:
        paths = [p for p in sorted((kb / "tickets").glob("*.md"))
                 if p.name not in ("index.md", "log.md")
                 and field(split(p.read_text(encoding="utf-8"))[0], "state") == "todo"]
    if fill:
        skipped = skipped_stages(kb)
        filled = [p.name for p in paths if p.is_file() and write_skipped(p, skipped)]
        print(f"{len(filled)} ticket(s) : note « {SKIPPED_NOTE} » écrite"
              + (f" (étapes écartées : {', '.join(s for s in STAGE.values() if s in skipped)})" if filled else ""))
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
