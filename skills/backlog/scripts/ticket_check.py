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
  - a `depends_on` (if any) naming existing tickets, without a cycle,
  - grounded notes (`backlog`'s Grounding Rule): every note carries its
    labelled bullets, none still `inconnu — …` and none a structural gap
    `à créer — owner: …`,
  - each abuse case of the security note and each legal constraint of the
    legal note tied to an acceptance criterion (`→ CAn`), and every `→ CAn`
    naming a criterion the ticket has,
  - every `dir/file.ext` its technical and architecture notes cite as existing
    (no `à créer` on the line) present in the project — or created by a ticket
    it `depends_on`,
  - every « label » a criterion cites present in the code, or brought by this
    ticket or one of its `depends_on` (the tickets whose criteria click it),
    and no criterion conditional on another ticket (« dès qu'il existe »),
  - every `CAn` of another ticket its criteria and notes cite (`CA11 de <ticket>`,
    `[t](t.md) CA5`) a criterion that ticket has, every KB file its notes link
    present, and no decision cited from an agent's report (« Q2 du rapport »),
  - every rule, error case or indicator a criterion cites (`- CA1 [RG2, CE1] — …`,
    `- CA2 [IN1] — …`) in force in an exigence of its `Lié à :` line, and a
    criterion citing an indicator stating its expected value (a number).

A ticket whose notes are all still absent is *planifiable*: `backlog` writes the story, the criteria,
`depends_on` and `estimate` of every ticket, and `sprint` writes the notes of the tickets it takes. The
absent notes come back as `(à détailler)` lines; a stage the plan marks `non applicable` needs no note.
An abuse case of the security note may say `— différé : usage exploratoire` instead of `→ CAn` while
kb/project/identity.md says `## Usage` : exploratoire.

Run:  python ticket_check.py <kb-dir> [--planifiable] [ticket ...]
      <kb-dir> is `<root>/.hosa/kb`. Each ticket is a slug (`lancer-un-run`), a path to its `.md`, or the
      `tickets/` folder (its `todo` tickets). No ticket given → every `state: todo` ticket in <kb-dir>/tickets/.
      `--planifiable`: the `(à détailler)` lines don't count (`backlog`'s proof, the roadmap).
      python ticket_check.py <kb-dir> --differes
      Every deferred abuse case, done tickets included; exit 1 when `## Usage` is no longer exploratoire.
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
import os
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


# The five notes: written when the ticket enters a sprint (`sprint`, tasks `notes-<k>` → `securite-<k>`,
# `juridique-<k>` → `juge-<k>`), not by `backlog`. A ticket without them is planned (`--planifiable`), not built:
# rieki wrote 128 tickets' notes up front (≈ 61 $, 27 % of the project) and used 22 of them after 3 sprints.
NOTES = tuple(list(SECTIONS)[1:])
TO_DETAIL = "(à détailler)"

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


def measure_dependencies(path: Path, front: str, body: str) -> list[str]:
    """A criterion citing a rule that waits for a measure (`[à mesurer M1 : …]` in the exigence) can't be tested
    before the measure: the ticket that makes it (`mesure: M1` in its frontmatter) comes first, unless
    `decisions.md` already records M1 (rieki: CA12 « repli de taille », on a time nobody had measured)."""
    kb = path.parent.parent
    if cdc() is None or path.parent.name != "tickets":
        return []
    done, out = cdc().measured(kb), []
    waits = {}
    for slug in linked_exigences(body):
        f = kb / "cdc" / f"{slug}.md"
        if f.is_file():
            waits.update(cdc().rule_measures(f.read_text(encoding="utf-8")))
    if not waits:
        return out
    makers = {}
    for f in path.parent.glob("*.md"):
        m = re.search(r"^mesure:\s*\[?([\w, ]+)\]?\s*$", split(f.read_text(encoding="utf-8"))[0], re.M)
        for mid in re.findall(r"M\d+", m[1]) if m else []:
            makers.setdefault(mid, f.stem)
    mine = set(re.findall(r"M\d+", (re.search(r"^mesure:.*$", front, re.M) or [""])[0]))
    deps = closure(path.stem, path.parent)
    for line in (section(body, "## Critères d'acceptation") or "").splitlines():
        m = re.match(r"\s*[-*]\s+(CA\d+)\s*\[([^\]]*)\]", line)
        if not m:
            continue
        for rid in re.findall(r"\b(?:RG|CE)\d+\b", m[2]):
            for mid in waits.get(rid, []):
                if mid in done or mid in mine:
                    continue
                by = makers.get(mid)
                if by and by in deps:
                    continue
                out.append(f"{m[1]} cite {rid}, qui attend la mesure {mid} → `depends_on: [{by}]`" if by else
                           f"{m[1]} cite {rid}, qui attend la mesure {mid} : aucun ticket ne la fait → créer le "
                           f"ticket qui la mesure (`mesure: {mid}`), ou porter ce critère dans un ticket après lui")
    return list(dict.fromkeys(out))


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


# An abuse case set aside while the project is only explored (`## Usage` : exploratoire, kb/project/identity.md): no
# criterion yet, built before real use. rieki, a local single-user test of a forecasting model: 6 of its first 26
# tickets hardened the import, and after 3 sprints no forecast had run.
DEFERRED = re.compile(r"—\s*différé\s*:\s*usage exploratoire", re.I)
EXPLORATORY = "exploratoire"


def usage(kb: Path) -> str:
    """The project's `## Usage` (kb/project/identity.md): `exploratoire` or `réel`. Absent → `réel`: full security."""
    ident = kb / "project" / "identity.md"
    content = section(split(ident.read_text(encoding="utf-8"))[1], "## Usage") if ident.is_file() else None
    first = next((x.strip().strip("*").strip().lower() for x in (content or "").splitlines() if x.strip()), "")
    return EXPLORATORY if first.startswith(EXPLORATORY) else "réel"


def untraced(heading: str, content: str, exploratory: bool = False) -> list[str]:
    label = TRACED.get(heading)
    if not label:
        return []
    out = []
    for item in bullet_items(content, label):
        if re.match(r"aucun", item, re.I) or CA_REF.search(item):
            continue
        if DEFERRED.search(item) and heading == "## Note sécurité (expert cybersécurité)":
            if not exploratory:
                out.append(f"`{heading[3:]}` : « {item[:60]} » différé alors que l'usage est réel (`## Usage`, "
                           "identity.md) : son critère (`→ CAn`)")
            continue
        out.append(f"`{heading[3:]}` : « {item[:60]} » sans critère (`→ CAn`)")
    return out


def deferred_cases(kb: Path) -> list[str]:
    """Every abuse case deferred for exploratory use, done tickets included: what real use must build first."""
    out = []
    for f in sorted((kb / "tickets").glob("*.md")) if (kb / "tickets").is_dir() else []:
        front, body = split(f.read_text(encoding="utf-8"))
        if field(front, "type") != "Ticket":
            continue
        note = section(body, "## Note sécurité (expert cybersécurité)") or ""
        out += [f"{f.stem} ({field(front, 'state') or 'todo'}) : {item}"
                for item in bullet_items(note, "Cas d'abus") if DEFERRED.search(item)]
    return out


def grounding(heading: str, content: str, exploratory: bool = False) -> list[str]:
    out = []
    for label in BULLETS.get(heading, ()):
        if not re.search(rf"^\s*[-*]\s+\*\*{re.escape(label)}\*\*\s*:", content, re.M):
            out.append(f"`{heading[3:]}` : puce « {label} » absente")
    out += untraced(heading, content, exploratory)
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


def stamp(tickets: Path) -> tuple:
    """What the tickets' files are now: a cache keyed on it is read again once one of them changes."""
    try:  # a DirEntry's stat comes with the listing on Windows: one call, not one per file
        with os.scandir(tickets) as it:
            return tuple(sorted((e.name, e.stat().st_mtime_ns, e.stat().st_size) for e in it if e.name.endswith(".md")))
    except OSError:
        return ()


@functools.lru_cache(maxsize=8)
def _all_deps(tickets: str, _stamp: tuple) -> dict[str, list[str]]:
    return {f.stem: depends_on(split(f.read_text(encoding="utf-8"))[0]) for f in Path(tickets).glob("*.md")}


def deps_of(tickets: Path) -> dict[str, list[str]]:
    """{slug: its `depends_on`}, every ticket read once (rieki: 24 886 reads for 122 tickets, 10 s)."""
    return _all_deps(str(tickets), stamp(tickets))


def cycle_from(slug: str, tickets: Path, seen: tuple = (), graph: dict | None = None) -> list[str] | None:
    if slug in seen:
        return list(seen[seen.index(slug):]) + [slug]
    graph = deps_of(tickets) if graph is None else graph
    if slug not in graph:
        return None
    for dep in graph[slug]:
        found = cycle_from(dep, tickets, seen + (slug,), graph)
        if found:
            return found
    return None


PATH = re.compile(r"`([\w.-]+(?:/[\w.-]+)+\.\w+)(?::[\w.]+)?`")  # `dir/file.ext` or `dir/file.ext:symbol`
CITED = ("## Note technique (senior dev)", "## Placement architecture (architecte)")


def creators(tickets: Path) -> dict[str, str]:
    """{path: slug of the ticket whose notes mark it `à créer`}, every ticket read once while none changes
    (rieki: the whole backlog read again for each of 28 tickets, 2.2 s of the dashboard's 3.9 s)."""
    return _creators(str(tickets), stamp(tickets))


@functools.lru_cache(maxsize=8)
def _creators(tickets: str, _stamp: tuple) -> dict[str, str]:
    out = {}
    for f in sorted(Path(tickets).glob("*.md")):
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


SOURCE_EXT = {".py", ".js", ".mjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte", ".html", ".php", ".rb", ".java",
              ".kt", ".cs", ".go", ".rs", ".dart", ".swift", ".erb", ".twig", ".json", ".toml", ".yaml", ".yml"}
SOURCE_SKIP = {".hosa", ".git", ".worktrees", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", "vendor"}
# A button another ticket brings; a choice (« choisit « Semaine » ») is a value, often a column name too (rieki)
ACTION = re.compile(r"(?:clique|cliquer|appuie|appuyer)\s+sur\s+« ([^»]+?) »")
QUOTED = re.compile(r"« ([^»]+?) »")
CONDITIONAL = re.compile(r"dès qu['’](?:il|elle)s? existen?t?|s['’]ils? existen?t? déjà|quand (?:il|elle)s? exister(?:a|ont)"
                         r"|une fois (?:livrée?s?|créée?s?)", re.I)


@functools.lru_cache(maxsize=8)
def source_text(root: str) -> str:
    """The project's source, read once: a label it holds as a literal already exists."""
    out = []
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SOURCE_SKIP]
        for name in files:
            if os.path.splitext(name)[1] in SOURCE_EXT:
                try:
                    out.append(Path(folder, name).read_text(encoding="utf-8", errors="ignore"))
                except OSError:
                    pass
    return "\n".join(out)


def label_owners(tickets: Path) -> dict[str, frozenset[str]]:
    """{label: the tickets still to build whose criteria click it} — the tickets that bring it."""
    return _label_owners(str(tickets), stamp(tickets))


@functools.lru_cache(maxsize=8)
def _label_owners(tickets: str, _stamp: tuple) -> dict[str, frozenset[str]]:
    out: dict[str, set[str]] = {}
    for f in Path(tickets).glob("*.md"):
        front, body = split(f.read_text(encoding="utf-8"))
        if field(front, "type") != "Ticket" or field(front, "state") == "done":
            continue
        for label in ACTION.findall(section(body, "## Critères d'acceptation") or ""):
            out.setdefault(label, set()).add(f.stem)
    return {k: frozenset(v) for k, v in out.items()}


def closure(slug: str, tickets: Path) -> set[str]:
    """Every ticket `slug` waits for, directly or through another."""
    graph, seen, todo = deps_of(tickets), set(), [slug]
    while todo:
        for dep in graph.get(todo.pop(), []):
            if dep not in seen:
                seen.add(dep)
                todo.append(dep)
    return seen


TICKET_LINK = re.compile(r"\]\((?:\.\./tickets/)?([\w-]+)\.md\)")
WRITE = re.compile(r"\bécrite?s?\b|\binsérée?s?\b|\bcréée?s?\b")
READ = re.compile(r"\blue?s?\b")


def data_access(body: str) -> tuple[set[str], set[str]]:
    """(tables written, tables read) from the architecture placement's `Données` bullet, as `backlog` writes it:
    « `ventes`.`date`, … écrits ; `imports`.`date_export` … écrits » — a verb closes the segments before it."""
    m = re.search(r"\*\*Données\*\*\s*:\s*(.*)", section(body, "## Placement architecture (architecte)") or "")
    written, read, pending = set(), set(), set()
    for seg in (m[1].split(";") if m else []):
        seg = seg.strip()
        pending |= set(re.findall(r"`(\w+)`\.`", seg)) | set(re.findall(r"^`(\w+)`(?!\.)", seg))
        w, r = WRITE.search(seg), READ.search(seg)
        if w:
            written |= pending
        if r:
            read |= pending
        if w or r or "supprim" in seg:
            pending = set()
    return written, read - written


@functools.lru_cache(maxsize=8)
def _ticket_index(tickets: str, _stamp: tuple) -> dict[str, dict]:
    out = {}
    for f in Path(tickets).glob("*.md"):
        front, body = split(f.read_text(encoding="utf-8"))
        if field(front, "type") != "Ticket":
            continue
        links = {}
        for line in (section(body, "## Critères d'acceptation") or "").splitlines():
            m = re.match(r"\s*[-*]\s*(CA\d+)", line)
            if m:
                links[m[1]] = [x for x in dict.fromkeys(TICKET_LINK.findall(line)) if x != f.stem]
        written, read = data_access(body)
        out[f.stem] = {"done": field(front, "state") == "done", "links": links, "writes": written, "reads": read}
    return out


def ticket_index(tickets: Path) -> dict[str, dict]:
    return _ticket_index(str(tickets), stamp(tickets))


def room(index: dict, slug: str) -> str:
    """The receiving ticket's free room: a moved criterion must not take it past the bound (rieki sprint-4:
    supprimer-un-article and supprimer-un-run would have reached 11)."""
    n = len(index.get(slug, {}).get("links", {}))
    full = " — plein : découper le ticket d'abord" if n >= TOO_MANY_CRITERIA else ""
    return f" (`{slug}` : {n}/{TOO_MANY_CRITERIA} critères{full})"


def hidden_dependencies(path: Path, front: str, body: str) -> list[str]:
    """The dependencies a ticket's own text states that its `depends_on` misses — the edges `sprint` plans from.
    - A criterion that cites another ticket still to build: it can't be tested without it (rieki: « consulter les
      articles » CA5, an article deleted by `supprimer-un-article`). Both citing each other: one behaviour in two
      tickets (rieki: the `op-…` message of a failed sales import, in the import's CA7 and in the guard's CA9).
    - A table its `Données` read that no ticket done or among its dependencies writes (rieki: the cleaning read
      `ventes`, whose import came 3 sprints later) — unless every writer comes after it: it shows the empty state.
    `HOSA_DEPENDANCES=0`: off."""
    if os.environ.get("HOSA_DEPENDANCES") == "0" or path.parent.name != "tickets":
        return []
    index, me, out = ticket_index(path.parent), path.stem, []
    deps = closure(me, path.parent)
    todo = lambda s: s in index and not index[s]["done"]  # noqa: E731
    for ca, cited in (index.get(me) or {"links": {}})["links"].items():
        for x in cited:
            if not todo(x) or x in deps:
                continue
            back = [c for c, ls in index[x]["links"].items() if me in ls]
            if back:
                out.append(f"{ca} et `{x}` {', '.join(back)} portent le même comportement (chacun cite l'autre) : un "
                           "seul des deux le garde, l'autre le retire")
            elif me in closure(x, path.parent):  # x waits for this one: the criterion is x's
                out.append(f"{ca} cite `{x}`, qui vient après ce ticket (il en dépend) → porter ce critère dans `{x}`"
                           + room(index, x))
            else:
                out.append(f"{ca} cite `{x}` (à faire), hors de ses dépendances → `depends_on: [{x}]`, ou porter ce "
                           f"critère dans `{x}`" + room(index, x))
    written, read = data_access(body)
    for table in sorted(read):
        writers = {s for s, t in index.items() if table in t["writes"] and s != me}
        if not writers or any(not todo(w) for w in writers) or writers & deps:
            continue
        before = {w for w in writers if me not in closure(w, path.parent)}  # one coming after would make a cycle
        if not before:  # every writer comes after: the reader shows the empty state
            continue
        # the first to write it: no other writer before it (rieki `ventes`: the sales import, not the code check
        # that rewrites two of its columns)
        first = sorted(w for w in before if not (closure(w, path.parent) & (before - {w})))
        if len(first) == 1:
            out.append(f"lit `{table}`, qu'aucun ticket fait ni de ses dépendances n'écrit → `depends_on: [{first[0]}]` "
                       f"(le premier à l'écrire)")
        else:
            out.append(f"lit `{table}`, qu'aucun ticket fait ni de ses dépendances n'écrit — l'écrivent d'abord (à faire) : "
                       + ", ".join(f"`{w}`" for w in first) + " → mettre celui qui la remplit dans `depends_on`")
    return out


CA_LIST = r"CA\d+(?:\s*(?:,|et|à|-)\s*CA\d+)*"
# `[x](x.md) CA5`, `[x](../tickets/x.md) (CA1, CA2)`, `x (CA5)` with a slug of 3 words at least
REF_AFTER = re.compile(r"(?:\[[^\]]*\]\((?:\.\./tickets/)?([\w-]+)\.md\)|`?\b([a-z0-9]+(?:-[a-z0-9]+){2,})\b`?)"
                       r"\s*\(?\s*(" + CA_LIST + r")\b")
# `CA11 de lancer-un-nettoyage`, `CA9 de [lister](lister.md)`
REF_BEFORE = re.compile(r"\b(" + CA_LIST + r")\s+(?:de|du ticket)\s+(?:\[[^\]]*\]\((?:\.\./tickets/)?([\w-]+)\.md\)"
                        r"|`?([a-z0-9]+(?:-[a-z0-9]+)+)`?)")
KB_LINK = re.compile(r"\]\(((?!https?:)[\w./-]+\.md)(?:#[^)]*)?\)")
REPORT = re.compile(r"\bQ\d+(?:\s*/\s*Q\d+)*\s+du rapport\b[^)\];,.]*")


def resolve_ticket(name: str, tickets: Path) -> str | None:
    """A slug, or the unique ticket whose slug starts with it (« lancer-un-nettoyage » for
    `lancer-un-nettoyage-et-enregistrer-une-version`)."""
    if (tickets / f"{name}.md").is_file():
        return name
    found = [f.stem for f in tickets.glob(f"{name}-*.md")]
    return found[0] if len(found) == 1 else None


def cross_references(path: Path, body: str) -> list[str]:
    """What a ticket's criteria and notes cite elsewhere exists: the other ticket has that `CAn`, the KB file is there,
    a decision is a KB file, never an agent's report (rieki sprint-4: « CA11 de lancer-un-nettoyage » and « CA9 de
    lister » that didn't exist, « Q2/Q3 du rapport de sécurité » found nowhere — each seen only at qa-plan).
    `HOSA_RENVOIS=0`: off."""
    if os.environ.get("HOSA_RENVOIS") == "0" or path.parent.name != "tickets":
        return []
    out = []
    for heading in SECTIONS:
        text = section(body, heading) or ""
        name = heading[3:]
        refs = [(m[3], m[1] or m[2]) for m in REF_AFTER.finditer(text)]
        refs += [(m[1], m[2] or m[3]) for m in REF_BEFORE.finditer(text)]
        for cas, target in refs:
            slug = resolve_ticket(target, path.parent)
            if not slug or slug == path.stem:
                continue
            theirs = ticket_index(path.parent).get(slug, {}).get("links", {})
            for ca in dict.fromkeys(re.findall(r"CA\d+", cas)):
                if ca not in theirs:
                    gap = f"`{name}` cite {ca} de `{slug}`, qui n'a pas ce critère → corriger le renvoi"
                    if gap not in out:
                        out.append(gap)
        if heading == "## Critères d'acceptation":
            continue
        for link in dict.fromkeys(KB_LINK.findall(text)):
            if not (path.parent / link).resolve().is_file():
                out.append(f"`{name}` cite `{link}`, absent de la KB → lien à corriger")
        for cite in dict.fromkeys(REPORT.findall(text)):
            out.append(f"`{name}` cite « {cite.strip()} », introuvable dans la KB → citer le fichier de la KB "
                       "qui porte la décision")
    return out


def note_tickets(path: Path, body: str) -> list[str]:
    """The tickets still to build that a note cites, outside its `Hors périmètre` bullet, and that neither come before
    this one (`depends_on`) nor after it (they depend on it): what the note uses from them doesn't exist when this
    ticket is built — unless the sprint holds them (`avancement.py check sprint`)."""
    if path.parent.name != "tickets":
        return []
    index, me = ticket_index(path.parent), path.stem
    before, out = closure(me, path.parent), []
    for heading in list(SECTIONS)[1:]:
        for line in (section(body, heading) or "").splitlines():
            if "Hors périmètre" in line:
                continue
            for x in TICKET_LINK.findall(line):
                if x == me or x in out or x in before or x not in index or index[x]["done"]:
                    continue
                if me in closure(x, path.parent):
                    continue
                out.append(x)
    return out


def in_code(label: str, code: str) -> bool:
    """The label as a whole literal: `"Confirmer"`, `>Confirmer<`, `:red[Confirmer]`, « Confirmer » in a comment —
    never a word of a sentence (« Supprimer une version supprime ses filles »)."""
    return re.search(r"(?:[\"'`>\[]|«\s?)" + re.escape(label) + r"(?:[\"'`<\]]|\s?»)", code) is not None


def unbuilt_labels(path: Path, front: str, body: str) -> list[str]:
    """A criterion names only what the code, its own ticket or its `depends_on` brings: a button another
    ticket still to build adds can't be tested here (rieki: « Supprimer » of Résultats, cited at priority 9
    by the button hierarchy, brought by `supprimer-un-run` at 124, many sprints away). `HOSA_LIBELLES=0`: off."""
    if os.environ.get("HOSA_LIBELLES") == "0":
        return []
    crit = section(body, "## Critères d'acceptation") or ""
    out = []
    for line in crit.splitlines():
        m = re.match(r"\s*[-*]\s*(CA\d+)", line)
        if m and CONDITIONAL.search(line):
            out.append(f"{m[1]} conditionnel (« {CONDITIONAL.search(line)[0]} ») : un critère se teste à la fin de "
                       "son ticket → `depends_on` le ticket qui livre l'élément, ou porter le critère dans ce ticket-là")
    kb = path.parent.parent
    if kb.name != "kb" or kb.parent.name != ".hosa":
        return out
    owners, deps, code = label_owners(path.parent), None, None
    for line in crit.splitlines():
        m = re.match(r"\s*[-*]\s*(CA\d+)", line)
        if not m:
            continue
        for label in dict.fromkeys(QUOTED.findall(line)):
            by = owners.get(label)
            if not by or path.stem in by:
                continue
            deps = closure(path.stem, path.parent) if deps is None else deps
            if by & deps:
                continue
            code = source_text(str(kb.parent.parent)) if code is None else code
            if in_code(label, code):
                continue
            names = ", ".join(f"`{s}`" for s in sorted(by))
            out.append(f"{m[1]} cite « {label} », absent du code et livré par {names} (à faire) → ajouter le bon "
                       "à `depends_on`, ou porter ce critère dans ce ticket-là")
    return out


ONE_FIX = re.compile(r"→ (?:ajouter )?`depends_on: \[[\w-]+\]`"  # one ticket to add
                     r"|→ porter ce critère dans `[\w-]+`(?: \(`[\w-]+` : \d+/\d+ critères\))?$"  # one criterion to move
                     r"|portent le même comportement"  # one behaviour in two tickets: the mechanism's keeps it
                     r"|livré par `[\w-]+` \(à faire\)")  # one ticket brings the label


def one_fix(gap: str) -> bool:
    """A checker line that is its own decision: `hosa-product-owner` applies it (Graph fixes), nobody is asked.
    Several writers, several owners, a conditional with no ticket named, a missing note: not one fix."""
    return ONE_FIX.search(gap) is not None


def single_fixes(tickets: Path) -> list[tuple[str, str]]:
    """Every `todo` ticket's one-fix lines, verbatim (rieki 0.1.107: 16 tickets left « à compléter » while the
    product owner got a hand-written list of four other points, and the sprint closed)."""
    out = []
    for f in sorted(tickets.glob("*.md")):
        front, _ = split(f.read_text(encoding="utf-8"))
        if field(front, "type") == "Ticket" and (field(front, "state") or "todo") == "todo":
            out += [(f.stem, g) for g in gaps(f) if one_fix(g)]
    return out


def gaps(path: Path) -> list[str]:
    front, body = split(path.read_text(encoding="utf-8"))
    if field(front, "type") != "Ticket":
        return ["pas un `Ticket` (type manquant ou différent)"]
    missing, skipped = [], skipped_stages(path.parent.parent)
    exploratory = usage(path.parent.parent) == EXPLORATORY
    if not re.search(r"^En tant qu(?:e\b|['’])", body, re.M):  # « En tant qu'administrateur » is a story too (rieki)
        missing.append("story « En tant que … » absente")
    if not re.search(r"^Lié à\s*:", body, re.M):
        missing.append("ligne « Lié à : » absente")
    for heading, fallback in SECTIONS.items():
        content = section(body, heading)
        if content is None and STAGE.get(heading) in skipped:
            continue  # a stage the user set aside needs no note at all (rieki: 44 KB of « Non applicable » lines)
        if content is None and heading in NOTES:
            missing.append(f"{TO_DETAIL} section `{heading}` absente")
        elif content is None:
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
            missing += grounding(heading, content, exploratory)
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
    missing += unbuilt_labels(path, front, body)
    missing += hidden_dependencies(path, front, body)
    missing += cross_references(path, body)
    missing += measure_dependencies(path, front, body)
    missing += [f"(info) une note cite `{x}` (à faire), ni dans `depends_on` ni après ce ticket : le sprint doit "
                "le prendre avant lui" for x in note_tickets(path, body)]
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
    """A dependency still to build that ranks after this ticket — reported only: the roadmap builds each ticket after
    its dependencies whatever their rank; `priority` breaks ties (pilot2 had to re-rank by hand: the security log at
    43, used by tickets at 7 to 17)."""
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
            out.append(f"(info) dépend de `{dep}` ({where}), classé après lui : le graphe le construit avant quand même")
    return out


def todo_tickets(folder: Path) -> list[Path]:
    return [p for p in sorted(folder.glob("*.md")) if p.name not in ("index.md", "log.md")
            and field(split(p.read_text(encoding="utf-8"))[0], "state") == "todo"]


def ticket_paths(kb: Path, args: list[str]) -> list[Path]:
    """Each argument a ticket's path, its slug (`lancer-un-run`) or the `tickets/` folder (its `todo` tickets):
    rieki sprint-4, three agents tried a slug or the folder and got « is not a directory »."""
    out = []
    for a in args:
        p = Path(a)
        if p.is_dir():
            out += todo_tickets(p)
        elif p.is_file() or a.endswith(".md") or "/" in a or "\\" in a:
            out.append(p)
        else:
            out.append(kb / "tickets" / f"{a}.md")
    return out


def main(argv: list[str]) -> int:
    if argv[:1] in (["-h"], ["--help"]):
        print(__doc__.strip())
        return 0
    if not argv:
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        print("usage: ticket_check.py <kb-dir> [--ecartees] [--planifiable] [ticket.md ...] | <kb-dir> --regles"
              " | <kb-dir> --repetes | <kb-dir> --differes",
              file=sys.stderr)
        return 2
    fill = "--ecartees" in argv
    plannable = "--planifiable" in argv
    argv = [a for a in argv if a not in ("--ecartees", "--planifiable")]
    kb = Path(argv[0])
    if not kb.is_dir():
        print(f"error: {kb} is not a directory — the first argument is the KB (`<root>/.hosa/kb`), then tickets "
              "(slug, path or the `tickets/` folder): `ticket_check <root>/.hosa/kb lancer-un-run`", file=sys.stderr)
        return 2
    if "--regles" in argv:
        lacking = rule_coverage(kb)
        print("\n".join(lacking) if lacking else "Règles : chaque règle numérotée d'une exigence découpée est citée par un critère.")
        return 1 if lacking else 0
    if "--differes" in argv:
        found = deferred_cases(kb)
        print("\n".join(f"✗ {x}" for x in found) if found else "Différés : aucun cas d'abus différé.")
        print(f"Usage : {usage(kb)} — {len(found)} cas d'abus différé(s)")
        # real use with a deferred case left: each one is built before the release (`livraison`, security gate)
        return 1 if found and usage(kb) != EXPLORATORY else 0
    if "--repetes" in argv:
        repeated = repeated_criteria(kb)
        print("\n".join(repeated) if repeated else "Répétitions : aucun critère d'un ticket `todo` ne répète un autre ticket de son exigence.")
        return 1 if repeated else 0
    paths = ticket_paths(kb, argv[1:]) if argv[1:] else todo_tickets(kb / "tickets")
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
        blocking = [g for g in found if not g.startswith("(info)") and not (plannable and g.startswith(TO_DETAIL))]
        if blocking:
            incomplete += 1
            print(f"✗ {p.name} — incomplet : " + " ; ".join(found))
        elif plannable and any(g.startswith(TO_DETAIL) for g in found):
            print(f"✓ {p.name} — planifiable, notes à détailler au sprint")
        else:
            print(f"✓ {p.name} — complet" + (f" ({found[0]})" if found else ""))
    print(f"{len(paths) - incomplete}/{len(paths)} ticket(s) " + ("planifiable(s)" if plannable else "complet(s)"))
    return 1 if incomplete else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
