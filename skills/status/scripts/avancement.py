#!/usr/bin/env python3
"""Hosa progress plan — `.hosa/kb/project/avancement.md`.

Keeps every pipeline stage with its status, and a resume point, so an
interrupted session (limit reached, crash, new day) picks up exactly where
the work stopped, in the right order.

  avancement.py <kb> show
  avancement.py <kb> init                                         (no plan yet: built from the KB's proofs)
  avancement.py <kb> next                                        (stage to run, its skill, what it still lacks)
  avancement.py <kb> check    <stage> [--sprint S]                (exit 1 + gaps when its proof is missing)
  avancement.py <kb> start    <stage> [--sprint S] [--detail D] [--reprise R] [--force]
  avancement.py <kb> progress <stage> [--sprint S]  --detail D  [--reprise R]
  avancement.py <kb> done     <stage> [--sprint S] [--detail D] [--force]
  avancement.py <kb> block    <stage> [--sprint S]  --detail D   (D: the questions in full, one line each)
  avancement.py <kb> skip     <stage> [--sprint S]  --detail D   (non applicable)
  avancement.py <kb> reprise  "<next action>"                     (outside the pipeline)
  avancement.py <kb> back     <from> <to> [--sprint S] [--ticket T] [--cause C] --detail D [--reprise R] [--force]
                                                                  (a loop: <from> sends work back to <to>)
  avancement.py <kb> task add   <stage> <id> [--sprint S] --agent A [--objet O] [--detail D]
  avancement.py <kb> task done  <stage> <id> [--sprint S] --sortie P[,P…] [--detail D] [--force]
  avancement.py <kb> task block <stage> <id> [--sprint S] --detail D
  avancement.py <kb> task skip  <stage> <id> [--sprint S] --detail D
                                                                  (the agents' tasks of a stage, under `## Tâches`)

`start` refuses (exit 1) while an earlier stage of the same pipeline isn't
done or skipped — `--force` only once the user has confirmed going out of
order. `done` refuses (exit 1) while `check` finds a gap — same `--force`
rule. `back` follows a loop of pipeline.json: it reopens <to> (and the
stages the loop re-runs after it) and <from>, and counts the round under
`## Boucles`; past the loop's `max` rounds it refuses (exit 1) — `--force`
once the user chose to go on. A different `--cause` restarts the count;
`done <from>` closes its loops. `task add` lists one agent dispatch of an
open stage; `task done` refuses (exit 1) without `--sortie`, the paths the
agent wrote, each one existing; `done <stage>` refuses while one of its tasks
is `à faire` or `bloqué`, and clears them once done. Sprint stages need
`--sprint`. Exit 2 = bad invocation. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# the stage graph lives in pipeline.json, shared with hooks/budget.js
GRAPH = json.loads(Path(__file__).with_name("pipeline.json").read_text(encoding="utf-8"))
PIPELINES = [(p["title"], p["stages"]) for p in GRAPH["pipelines"]]
SPRINT = GRAPH["sprint"]
SKILL = GRAPH["skill"]
LOOPS = GRAPH["loops"]
OPEN, SHUT = "ouverte", "fermée"
LOOP_ROW = re.compile(r"^\|\s*`([\w-]+)`\s*→\s*`([\w-]+)`(?:\s*\(([^)]*)\))?\s*\|\s*(\d+)/\d+\s*\|"
                      r"\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$")
# `| id | `stage` (sprint) | agent | objet | statut | mis à jour | sortie | détail |` — never a stage row
TASK_ROW = re.compile(r"^\|\s*([\w.-]+)\s*\|\s*`([\w-]+)`(?:\s*\(([^)]*)\))?\s*\|" + r"\s*([^|]*?)\s*\|" * 6 + r"\s*$")
TASK_ID = re.compile(r"^[\w.-]+$")
TODO, DOING, DONE, BLOCKED, SKIPPED = "à faire", "en cours", "fait", "bloqué", "non applicable"
CLOSED = {DONE, SKIPPED}
# a sprint begun before the `audit` stage existed had its audit inside `validation`
AFTER_AUDIT = {"validation", "git-fusion", "bilan-sprint", "livraison"}
ROW = re.compile(r"^\|\s*`?([\w-]+)`?\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load(path: Path) -> tuple[dict[str, list[list[str]]], str]:
    """{section title: [[stage, status, updated, detail], …]}, resume point."""
    sections = {title: [[s, TODO, "", ""] for s in stages] for title, stages in PIPELINES}
    resume = ""
    text = read(path)
    if text is None:
        return sections, resume
    current = None
    body = text.split("\n---\n", 1)[-1]
    for line in body.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            if current.startswith("Sprint ") and current not in sections:
                sections[current] = []
            continue
        if current == "Point de reprise" and line.strip():
            resume += line + "\n"
            continue
        m = ROW.match(line)
        if m and current in sections and m.group(1) not in ("Étape", "Etape") and m.group(1).strip("-"):
            rows = sections[current]
            row = next((r for r in rows if r[0] == m.group(1)), None)
            if row is None:
                row = [m.group(1), TODO, "", ""]
                rows.append(row)
            row[1:] = [m.group(2), m.group(3), m.group(4)]
    for title, rows in sections.items():
        if title.startswith("Sprint "):
            known = {r[0] for r in rows}
            if "audit" not in known and any(r[0] in AFTER_AUDIT and r[1] in CLOSED for r in rows):
                rows.append(["audit", SKIPPED, "", "audit dans `validation` (ordre d'avant 0.1.59)"])
                known.add("audit")
            rows[:] = [next((r for r in rows if r[0] == s), [s, TODO, "", ""]) for s in SPRINT] + \
                      [r for r in rows if r[0] not in SPRINT and r[0] in known]
    return sections, resume.strip()


def edge(frm: str, to: str) -> dict | None:
    """The loop of pipeline.json by which <frm> sends work back to <to>."""
    return next((e for e in LOOPS if e["from"] == frm and to in e["to"]), None)


def load_loops(path: Path) -> list[dict]:
    """The rounds of each loop, from `## Boucles`."""
    out = []
    for line in (section(read(path), "Boucles") or "").splitlines():
        m = LOOP_ROW.match(line)
        if m:
            out.append({"from": m[1], "to": m[2], "scope": m[3] or "", "tours": int(m[4]), "etat": m[5],
                        "at": m[6], "cause": m[7], "detail": m[8]})
    return out


def loop_name(lp: dict) -> str:
    return f"`{lp['from']}` → `{lp['to']}`" + (f" ({lp['scope']})" if lp["scope"] else "")


def loop_max(lp: dict) -> int:
    e = edge(lp["from"], lp["to"])
    return e["max"] if e else 2


def load_tasks(path: Path) -> list[dict]:
    """The agents' tasks of the open stages, from `## Tâches`."""
    out = []
    for line in (section(read(path), "Tâches") or "").splitlines():
        m = TASK_ROW.match(line)
        if m:
            out.append({"id": m[1], "stage": m[2], "scope": m[3] or "", "agent": m[4], "objet": m[5],
                        "statut": m[6], "at": m[7], "sortie": m[8], "detail": m[9]})
    return out


def cell(s: str) -> str:
    return s.replace("|", "/").replace("\n", " ").strip()


def task_where(t: dict) -> str:
    return f"`{t['stage']}`" + (f" (sprint {t['scope']})" if t["scope"] else "")


def task_name(t: dict) -> str:
    return f"`{t['id']}` {t['agent']}" + (f" → {t['objet']}" if t["objet"] else "")


def save(path: Path, sections: dict, resume: str, loops: list[dict] | None = None,
         tasks: list[dict] | None = None) -> None:
    loops = load_loops(path) if loops is None else loops
    tasks = load_tasks(path) if tasks is None else tasks
    out = ["---", "type: Plan d'avancement", "title: Plan d'avancement",
           "description: Étapes du projet, leur statut et le point de reprise",
           "tags: [pilotage]", f"generated: {{ by: process:hosa-avancement, at: {now()} }}", "---",
           "## Point de reprise", resume or "- Rien en cours.", ""]
    if loops:
        out += ["## Boucles", "| Boucle | Tours | État | Mis à jour | Cause | Détail |", "|---|---|---|---|---|---|"]
        out += [f"| {loop_name(lp)} | {lp['tours']}/{loop_max(lp)} | {lp['etat']} | {lp['at']} | "
                f"{lp['cause'].replace('|', '/')} | {lp['detail'].replace('|', '/')} |" for lp in loops]
        out.append("")
    if tasks:
        out += ["## Tâches", "| Tâche | Étape | Agent | Objet | Statut | Mis à jour | Sortie | Détail |",
                "|---|---|---|---|---|---|---|---|"]
        out += [f"| {t['id']} | `{t['stage']}`" + (f" ({t['scope']})" if t["scope"] else "")
                + f" | {cell(t['agent'])} | {cell(t['objet'])} | {t['statut']} | {t['at']} | {cell(t['sortie'])} | "
                f"{cell(t['detail'])} |" for t in tasks]
        out.append("")
    for title, rows in sections.items():
        out += [f"## {title}", "| Étape | Statut | Mis à jour | Détail |", "|---|---|---|---|"]
        out += [f"| `{r[0]}` | {r[1]} | {r[2]} | {r[3].replace('|', '/')} |" for r in rows]
        out.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out), encoding="utf-8")


def locate(sections: dict, stage: str, sprint: str | None) -> tuple[str, list[list[str]]]:
    if stage in SPRINT:
        if not sprint:
            raise SystemExit(f"error: `{stage}` is a sprint stage — pass --sprint <slug>")
        title = f"Sprint {sprint}"
        sections.setdefault(title, [[s, TODO, "", ""] for s in SPRINT])
        return title, sections[title]
    for title, stages in PIPELINES:
        if stage in stages:
            return title, sections[title]
    raise SystemExit(f"error: unknown stage `{stage}` — use `reprise` for work outside the pipeline")


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def section(text: str | None, heading: str) -> str | None:
    """Body of the last `## <heading>` (up to the next level-2 heading)."""
    lines, start = (text or "").splitlines(), None
    for i, line in enumerate(lines):
        if line.strip() == f"## {heading}":
            start = i
    if start is None:
        return None
    out = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        out.append(line)
    return "\n".join(out)


def field(text: str | None, name: str) -> str | None:
    m = re.search(rf"^{name}:\s*(.+)$", text or "", re.M)
    return m and m.group(1).strip()


def criteria(text: str | None) -> list[str]:
    ids = re.findall(r"^-\s*(CA\d+)\b", section(text, "Critères d'acceptation") or "", re.M)
    return list(dict.fromkeys(ids))


def coverage(kb: Path, ticket: str) -> dict:
    """Criteria of a ticket proved by its technical plan (`[CAn]`) or a recette (`CAn — Oui`)."""
    crit = criteria(read(kb / "tickets" / f"{ticket}.md"))
    plan = read(kb / "test" / f"{ticket}-technique.md")
    proofs = plan or ""
    if (kb / "test").is_dir():
        for p in sorted((kb / "test").iterdir()):
            if p.name.startswith(f"{ticket}-") and p.suffix == ".md" and p.name != f"{ticket}-technique.md":
                proofs += "\n" + (read(p) or "")
    done = [ca for ca in crit if re.search(rf"\[{re.escape(ca)}\]|^-\s*{re.escape(ca)}\s*—\s*Oui\b", proofs, re.M)]
    return {"criteres": crit, "couverts": done, "total": len(crit), "plan": plan is not None}


def front(text: str | None) -> str:
    m = re.match(r"---\s*\n(.*?)\n---", text or "", re.S)
    return m.group(1) if m else ""


def concepts(kb: Path, folder: str, ctype: str) -> list[tuple[Path, str]]:
    """The `.md` files of `kb/<folder>/` whose `type:` is <ctype>, with their text."""
    out = []
    for p in sorted((kb / folder).glob("*.md")) if (kb / folder).is_dir() else []:
        text = read(p)
        if text and (field(front(text), "type") or "").strip("\"'") == ctype:
            out.append((p, text))
    return out


def concept(kb: Path, rel: str, ctype: str, heading: str | None = None) -> str | None:
    """Gap of one expected file: missing, wrong type, or without its `## <heading>`."""
    text = read(kb / rel)
    if text is None or (field(front(text), "type") or "").strip("\"'") != ctype:
        return f"pas de `kb/{rel}` (`type: {ctype}`)"
    if heading and not re.search(rf"^## {re.escape(heading)}", text, re.M):
        return f"`kb/{rel}` n'a pas sa section `## {heading}`"
    return None


def infra_with(kb: Path, heading: str) -> str | None:
    if any(re.search(rf"^## {re.escape(heading)}", t, re.M) for _, t in concepts(kb, "infra", "Infra")):
        return None
    return f"aucune entrée `Infra` de `kb/infra/` n'a de section `## {heading}`"


SCRIPTS = Path(__file__).resolve().parents[2]


def script(rel: str, *args) -> list[str]:
    """Gaps a Hosa checker reports (exit 1). Any other failure is not the stage's: fail-open."""
    import os
    import subprocess
    try:
        r = subprocess.run([sys.executable, str(SCRIPTS / rel), *map(str, args)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        return []
    if r.returncode != 1:
        return []
    lines = [x.strip() for x in r.stdout.splitlines() if x.strip()]
    more = f" (+{len(lines) - 5})" if len(lines) > 5 else ""
    return [f"`{Path(rel).stem}` : " + " ; ".join(lines[:5]) + more]


def upstream_check(kb: Path, stage: str) -> list[str]:
    """What the KB lacks to prove a stage of the cahier des charges or the structuration done:
    the files each stage's skill writes, and the checkers its skill must pass."""
    gaps: list[str | None] = []
    exigences = concepts(kb, "cdc", "Exigence")
    stable = [(p, t) for p, t in exigences if field(front(t), "status") == "stable"]
    if stage == "hosa":
        gaps.append(concept(kb, "project/identity.md", "Project"))
        if not [p for p, _ in concepts(kb, "personnas", "Persona") if p.name != "exemple-persona.md"]:
            gaps.append("aucun persona dans `kb/personnas/` (hors exemple)")
    elif stage == "interview":
        if not concepts(kb, "cdc/interviews", "Compte Rendu"):
            gaps.append("aucun compte rendu dans `kb/cdc/interviews/`")
    elif stage == "redaction":
        if not exigences:
            gaps.append("aucune `Exigence` dans `kb/cdc/`")
        gaps.append(concept(kb, "project/cahier-des-charges.md", "Cahier des charges"))
        gaps += script("redaction/scripts/cdc.py", "revue", kb, "--route", "redaction")
    elif stage == "fondamentaux":
        gaps.append(concept(kb, "cdc/fondamentaux.md", "Revue Fondamentaux"))
    elif stage == "juridique":
        gaps.append(concept(kb, "cdc/juridique.md", "Analyse juridique", "Contraintes retenues"))
    elif stage == "securite":
        gaps.append(concept(kb, "cdc/securite.md", "Analyse de sécurité", "Menaces et mesures"))
    elif stage == "relecture":
        gaps.append(concept(kb, "cdc/relecture.md", "Revue Relecture"))
        gaps += script("redaction/scripts/cdc.py", "revue", kb)
    elif stage == "contestation":
        draft = [p.stem for p, t in exigences if field(front(t), "status") != "stable"]
        unsigned = [p.stem for p, t in stable if not field(front(t), "verified")]
        if draft:
            gaps.append(f"exigences pas `stable` : {', '.join(draft)}")
        if unsigned:
            gaps.append(f"exigences sans `verified` (signature de l'utilisateur) : {', '.join(unsigned)}")
        gaps += script("redaction/scripts/cdc.py", "check", kb)
    elif stage == "stack":
        if not concepts(kb, "stack", "Stack Decision"):
            gaps.append("aucune `Stack Decision` dans `kb/stack/`")
    elif stage == "infra":
        gaps.append(infra_with(kb, "Outillage qualité"))
    elif stage == "donnees":
        for p, t in stable:
            lines = [x for h in ("Données en entrée", "Données en sortie")
                     for x in (section(t, h) or "").splitlines() if re.match(r"-\s", x)]
            bare = [x for x in lines if "origine" not in x]
            if bare:
                gaps.append(f"`{p.stem}` : {len(bare)} donnée(s) sans `origine :`")
    elif stage == "schema-app":
        gaps.append(infra_with(kb, "Structures de données"))
    elif stage == "schema-db":
        gaps.append(concept(kb, "infra/base-de-donnees.md", "Infra", "Commandes"))
    elif stage == "architecture":
        gaps.append(infra_with(kb, "Documentation d'architecture"))
    elif stage == "menaces":
        gaps.append(concept(kb, "securite/modele-menaces.md", "Modèle de Menaces"))
    elif stage == "interface":
        gaps.append(infra_with(kb, "Documentation d'interface"))
        gaps.append(concept(kb, "interface/navigation.md", "Plan de navigation"))
        gaps.append(concept(kb, "interface/lexique.md", "Lexique interface"))
        gaps += script("interface/scripts/interface_check.py", kb)
        if kb.parent.name == ".hosa":  # it scans the project's files: only from a real `<root>/.hosa/kb`
            gaps += script("interface/scripts/lexique_check.py", kb, kb.parent.parent)
    elif stage == "backlog":
        if not concepts(kb, "tickets", "Ticket"):
            gaps.append("aucun `Ticket` dans `kb/tickets/`")
        gaps.append(concept(kb, "rules/design/definition-de-termine.md", "Design Rule"))
        gaps += script("backlog/scripts/ticket_check.py", kb)
    return [g for g in gaps if g]


def open_tasks(tasks: list[dict], stage: str, sprint: str | None) -> list[dict]:
    return [t for t in tasks if t["stage"] == stage and t["scope"] == (sprint or "") and t["statut"] not in CLOSED]


def check(kb: Path, stage: str, sprint: str | None) -> list[str]:
    """What the KB lacks to prove a stage done: its proofs, then its agents' tasks still open.
    `hooks/gate.js` runs `check validation` before a sprint lands."""
    tasks = open_tasks(load_tasks(kb / "project" / "avancement.md"), stage, sprint)
    return proofs(kb, stage, sprint) + [f"tâche {task_name(t)} : {t['statut']}"
                                        + (f" — {t['detail']}" if t["detail"] else "") for t in tasks]


def proofs(kb: Path, stage: str, sprint: str | None) -> list[str]:
    """The files and checkers that prove a stage done."""
    if stage not in SPRINT:
        return upstream_check(kb, stage)
    if not sprint:
        return []
    s = read(kb / "sprints" / f"{sprint}.md")
    if s is None:
        return [f"sprint `{sprint}` absent de kb/sprints/"]
    tickets = re.findall(r"\(\.\./tickets/([^)]+)\.md\)", section(s, "Tickets") or "")
    gaps = [] if tickets else ["`## Tickets` ne liste aucun ticket"]
    # the merge (`git` Mode 2) removes `worktree`: a `merge_commit` proves the start too
    if stage == "git-demarrage" and not field(s, "worktree") and not field(s, "merge_commit"):
        gaps.append("le sprint n'a pas de `worktree` (`git` Mode 1)")
    if stage == "git-fusion" and not field(s, "merge_commit"):
        gaps.append("le sprint n'a pas de `merge_commit` (`git` Mode 2)")
    if stage == "bilan-sprint" and read(kb / "sprints" / f"{sprint}-review.md") is None:
        gaps.append(f"pas de `kb/sprints/{sprint}-review.md` (`bilan-sprint`)")
    tests = sorted(p.name for p in (kb / "test").glob("*.md")) if (kb / "test").is_dir() else []
    for t in tickets:
        text = read(kb / "tickets" / f"{t}.md")
        plan = read(kb / "test" / f"{t}-technique.md")
        crit = criteria(text)
        if stage == "qa-plan":
            if plan is None:
                gaps.append(f"{t} : pas de plan `kb/test/{t}-technique.md` (`qa-plan`)")
            missing = [ca for ca in crit if f"[{ca}]" not in (plan or "")]
            if missing:
                gaps.append(f"{t} : {', '.join(missing)} sans cas de test [CAn] (`qa-plan`)")
        if stage == "develop":
            verdicts = re.findall(r"\b(PASS-WITH-NOTES|PASS|FAIL)\b", section(text, "Revue") or "")
            if not verdicts or verdicts[-1] == "FAIL":
                gaps.append(f"{t} : dernière `## Revue` {verdicts[-1] if verdicts else 'absente'} (`develop`)")
        if stage in ("qa", "validation") and section(plan, "Résultats techniques") is None:
            gaps.append(f"{t} : pas de `## Résultats techniques` (`qa`)")
        if stage in ("qa", "validation"):
            for p in re.findall(r"\(\.\./personnas/([^)]+)\.md\)", section(plan, "Recette requise") or ""):
                if f"{t}-{p}.md" not in tests:
                    gaps.append(f"{t} : recette de {p} absente (`kb/test/{t}-{p}.md`, `qa`)")
        if stage == "validation":
            if field(text, "state") != "done" or not field(text, "verified"):
                gaps.append(f"{t} : pas `done` et `verified` (`validation`)")
            for f in (x for x in tests if x.startswith(f"{t}-") and x != f"{t}-technique.md"):
                r = read(kb / "test" / f) or ""
                if re.search(r"^\s*Refusé", section(r, "Verdict") or "", re.M):
                    gaps.append(f"{f} : recette Refusé")
                if re.search(r"^-\s*CA\d+\s*—\s*Non\s*—", r, re.M):
                    gaps.append(f"{f} : un critère répondu Non")
            cov = coverage(kb, t)
            unproved = [ca for ca in cov["criteres"] if ca not in cov["couverts"]]
            if unproved:
                gaps.append(f"{t} : {', '.join(unproved)} prouvé(s) par aucun cas [CAn] ni recette Oui (`qa-plan`)")
    if stage in ("audit", "validation"):
        bloquants = re.findall(r"Bloquant\s*:\s*(\d+)", section(s, "Audit") or "")
        if not bloquants:
            gaps.append("pas de `## Audit` avec sa ligne `Bloquant : N` (`qualite`, étape `audit`)")
        elif bloquants[-1] != "0":
            gaps.append(f"`## Audit` : Bloquant : {bloquants[-1]}")
    if stage == "validation":
        demo = section(s, "Démo")
        if demo is None:
            gaps.append("pas de `## Démo` (`validation` étape 3b)")
        else:
            status = dict(re.findall(r"\b(T\d+)\b[^\n]*?\b(OK|KO)\b", demo))
            ko = [k for k, v in status.items() if v == "KO"]
            if ko:
                gaps.append(f"`## Démo` : {', '.join(ko)} encore KO")
    return gaps


def first_open(sections: dict) -> tuple[str, list[str]] | None:
    for title, rows in sections.items():
        if title.startswith("Sprint ") and all(r[1] in CLOSED for r in rows):
            continue
        for r in rows:
            if r[1] not in CLOSED:
                return title, r
    return None


def next_open(sections: dict) -> str:
    found = first_open(sections)
    if not found:
        return "toutes les étapes connues sont faites — composer un nouveau sprint (`sprint`)"
    title, r = found
    return f"`{r[0]}` ({title}) — {r[1]}"


def open_loops(loops: list[dict]) -> list[str]:
    return [f"- Boucle ouverte : {loop_name(lp)} — tour {lp['tours']}/{loop_max(lp)} — {lp['detail']}"
            for lp in loops if lp["etat"] == OPEN]


def task_lines(tasks: list[dict]) -> list[str]:
    """Per stage: tasks done out of all, the next one to dispatch; each blocked task in full."""
    out = []
    for where in dict.fromkeys(task_where(t) for t in tasks):
        mine = [t for t in tasks if task_where(t) == where]
        done = sum(t["statut"] in CLOSED for t in mine)
        todo = next((t for t in mine if t["statut"] == TODO), None)
        out.append(f"- Tâches {where} : {done}/{len(mine)} faites"
                   + (f" — prochaine : {task_name(todo)}" + (f" ({todo['detail']})" if todo["detail"] else "")
                      if todo else ""))
        out += [f"- Tâche bloquée : {task_name(t)} ({where}) — {t['detail']}" for t in mine if t["statut"] == BLOCKED]
    return out


def show(sections: dict, resume: str, loops: list[dict] = (), tasks: list[dict] = ()) -> str:
    lines = ["## Point de reprise", resume or "- Rien en cours.",
             f"- Prochaine étape du plan : {next_open(sections)}"]
    for title, rows in sections.items():
        doing = [f"`{r[0]}` {r[1]}" + (f" — {r[3]}" if r[3] else "") for r in rows if r[1] in (DOING, BLOCKED)]
        if doing:
            lines.append(f"- {title} : " + " ; ".join(doing))
    return "\n".join(lines + [x for x in open_loops(loops) if x not in (resume or "")] + task_lines(tasks))


def exists(kb: Path, p: str, sprint: str = "") -> bool:
    """An output path as an agent gives it: absolute, `kb/…`, `.hosa/kb/…`, from the project root
    or from the sprint's worktree."""
    p = p.strip().strip("`")
    if not p:
        return False
    worktree = field(read(kb / "sprints" / f"{sprint}.md"), "worktree") if sprint else None
    roots = [Path.cwd(), kb] + ([kb.parent.parent] if kb.parent.name == ".hosa" else []) + \
        ([Path(worktree.strip("\"'"))] if worktree else [])
    candidates = [Path(p)] + [r / p for r in roots] + ([kb / p[3:]] if p.startswith("kb/") else [])
    return any(c.exists() for c in candidates)


def task(kb: Path, sections: dict, tasks: list[dict], a) -> tuple[int, str]:
    """`task add|done|block|skip <stage> <id>`. (exit code, message)"""
    op, stage, tid = a.stage, a.to, a.item
    if op not in ("add", "done", "block", "skip") or not stage or not tid:
        return 2, "error: task add|done|block|skip <stage> <id>"
    if not TASK_ID.match(tid):
        return 2, f"error: task id `{tid}` — letters, digits, `.`, `_`, `-` only"
    title, rows = locate(sections, stage, a.sprint)
    row = next(r for r in rows if r[0] == stage)
    scope = a.sprint if stage in SPRINT else ""
    t = next((x for x in tasks if (x["id"], x["stage"], x["scope"]) == (tid, stage, scope)), None)
    where = f"`{stage}`" + (f" (sprint {scope})" if scope else "")
    if op == "add":
        if not a.agent:
            return 2, "error: task add needs --agent"
        if row[1] not in (DOING, BLOCKED):
            return 1, f"✗ {where} est {row[1]} : `start` l'étape d'abord, puis liste ses tâches."
        if t is None:
            t = {"id": tid, "stage": stage, "scope": scope}
            tasks.append(t)
        t.update(agent=a.agent, objet=a.objet, statut=TODO, at=now(), sortie="", detail=a.detail)
        return 0, ""
    if t is None:
        known = ", ".join(f"`{x['id']}`" for x in tasks if (x["stage"], x["scope"]) == (stage, scope)) or "aucune"
        return 2, f"error: {where} n'a pas de tâche `{tid}` — tâches : {known}"
    if op in ("block", "skip") and not a.detail:
        return 2, f"error: task {op} needs --detail"
    if op == "done":
        paths = [p.strip() for p in a.sortie.split(",") if p.strip()]
        missing = [p for p in paths if not exists(kb, p, scope)]
        if (not paths or missing) and not a.force:
            return 1, (f"✗ tâche `{tid}` ({where}) pas faite : "
                       + ("aucune sortie (--sortie : les chemins que l'agent a écrits)" if not paths
                          else "sortie(s) absente(s) — " + ", ".join(missing))
                       + ". Relance l'agent, ou --force si l'utilisateur accepte.")
        t.update(statut=DONE, at=now(), sortie=", ".join(paths), detail=a.detail or t["detail"])
    else:
        t.update(statut=BLOCKED if op == "block" else SKIPPED, at=now(), detail=a.detail.strip().splitlines()[0])
    return 0, ""


def back(sections: dict, loops: list[dict], a) -> tuple[int, str]:
    """`back <from> <to>`: one more round of a loop. (exit code, message or new resume point)"""
    e = edge(a.stage, a.to or "")
    if not e:
        known = " ; ".join(f"`{x['from']}` → " + "/".join(f"`{t}`" for t in x["to"]) for x in LOOPS)
        return 2, f"error: pipeline.json has no loop `{a.stage}` → `{a.to}` — known: {known}"
    if not a.detail:
        return 2, "error: back needs --detail (what goes back, and why)"
    scope = ", ".join(x for x in (a.sprint, a.ticket) if x)
    lp = next((x for x in loops if (x["from"], x["to"], x["scope"]) == (a.stage, a.to, scope)), None)
    same = lp is not None and lp["etat"] == OPEN and (not a.cause or a.cause == lp["cause"])
    n = lp["tours"] + 1 if same else 1
    name = loop_name({"from": a.stage, "to": a.to, "scope": scope})
    if n > e["max"] and not a.force:
        return 1, (f"✗ boucle {name} : déjà {e['max']} tour(s) sans sortie propre — {lp['detail']}\n"
                   "Arrête la boucle : montre à l'utilisateur ce qui reste et ce que chaque tour a essayé, "
                   "et demande s'il faut un tour de plus (relance avec --force) ou changer d'approche.")
    if lp is None:
        lp = {"from": a.stage, "to": a.to, "scope": scope}
        loops.append(lp)
    first = a.detail.strip().splitlines()[0]
    lp.update(tours=n, etat=OPEN, at=now(), cause=a.cause or (lp.get("cause", "") if same else ""), detail=first)
    tour = f"tour {n}/{e['max']}"
    reruns = [a.to] + e.get("then", [])
    for s in reruns:
        r = next(x for x in locate(sections, s, a.sprint)[1] if x[0] == s)
        r[1:] = [TODO, now(), f"rouvert par `{a.stage}` ({tour}) : {first}"]
    r = next(x for x in locate(sections, a.stage, a.sprint)[1] if x[0] == a.stage)
    r[1:] = [TODO, now(), f"retour vers `{a.to}` ({tour})"]
    order = ", puis ".join(f"`{SKILL.get(s, s)}`" for s in reruns + [a.stage])
    rest = "".join(f"\n  {x}" for x in a.detail.strip().splitlines()[1:])
    return 0, (f"- Boucle ouverte : {name} — {tour} — {first}{rest}\n"
               f"- Prochaine action : {a.reprise or order}")


def init(kb: Path) -> tuple[dict, list[str]]:
    """A plan for a project begun before it: each stage done while its proof holds, in order,
    up to the first gap of each section. `livraison` is never inferred: a tag isn't in the KB."""
    sections, _ = load(kb / "project" / "avancement.md")
    report = []

    def walk(title, rows, sprint=None) -> bool:
        for r in rows:
            gaps = check(kb, r[0], sprint)
            if gaps or r[0] == "livraison":
                report.append(f"- {title} : arrêt à `{r[0]}` — " + ("; ".join(gaps) if gaps else "à confirmer"))
                return False
            r[1:] = [DONE, now(), "repris de la KB (`init`)"]
        return True

    ok = True
    for title, _ in PIPELINES:  # a later pipeline starts only once the earlier one is proved
        ok = ok and walk(title, sections[title])
    for p, _ in concepts(kb, "sprints", "Sprint"):
        title = f"Sprint {p.stem}"
        sections[title] = [[s, TODO, "", ""] for s in SPRINT]
        walk(title, sections[title], p.stem)
    return sections, report


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("kb", type=Path)
    ap.add_argument("action", choices=["show", "next", "check", "start", "progress", "done", "block", "skip", "reprise",
                                       "back", "init", "task"])
    ap.add_argument("stage", nargs="?")
    ap.add_argument("to", nargs="?")
    ap.add_argument("item", nargs="?")
    ap.add_argument("--sprint")
    ap.add_argument("--ticket", default="")
    ap.add_argument("--cause", default="")
    ap.add_argument("--detail", default="")
    ap.add_argument("--reprise", default="")
    ap.add_argument("--agent", default="")
    ap.add_argument("--objet", default="")
    ap.add_argument("--sortie", default="")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    if not a.kb.is_dir():
        print(f"error: {a.kb} is not a directory", file=sys.stderr)
        return 2
    path = a.kb / "project" / "avancement.md"
    sections, resume = load(path)
    loops = load_loops(path)
    tasks = load_tasks(path)

    if a.action == "show":
        print(show(sections, resume, loops, tasks))
        return 0
    if a.action == "task":
        code, out = task(a.kb, sections, tasks, a)
        if code:
            print(out, file=sys.stderr if code == 2 else sys.stdout)
            return code
        save(path, sections, resume, loops, tasks)
        print(show(*load(path), loops, tasks))
        return 0
    if a.action == "init":
        if path.exists():
            print(f"✗ le plan existe déjà : {path} — `show` le lit", file=sys.stderr)
            return 1
        sections, report = init(a.kb)
        save(path, sections, "- Plan créé depuis la KB (`init`) : confirmer les arrêts ci-dessous avec l'utilisateur.", [])
        print("\n".join(report) or "- Toutes les étapes prouvées.")
        print(show(*load(path)))
        return 0
    if a.action == "next":
        if not path.exists():
            print("Pas de plan d'avancement : le skill `status` le crée depuis l'état de la KB.")
            return 0
        found = first_open(sections)
        if not found:
            print(f"Prochaine étape : {next_open(sections)}")
            return 0
        title, r = found
        sprint = title[len("Sprint "):] if title.startswith("Sprint ") else None
        print(f"Prochaine étape : `{r[0]}` ({title}, {r[1]}) → skill `{SKILL.get(r[0], r[0])}`"
              + (f" — {r[3]}" if r[3] else ""))
        if r[1] == DOING:
            gaps = check(a.kb, r[0], sprint)
            print("Reste à prouver :" if gaps else "Preuves : complètes — `done` possible.")
            print("\n".join(f"- {g}" for g in gaps))
        if resume:
            print(resume)
        print("\n".join(x for x in open_loops(loops) if x not in resume))
        return 0
    if a.action == "check":
        if not a.stage:
            print("error: check needs a stage", file=sys.stderr)
            return 2
        gaps = check(a.kb, a.stage, a.sprint)
        print("\n".join(f"- {g}" for g in gaps) if gaps else f"✓ `{a.stage}` : preuves complètes")
        return 1 if gaps else 0
    if a.action == "reprise":
        if not a.stage:
            print("error: reprise needs the next action as text", file=sys.stderr)
            return 2
        save(path, sections, f"- Prochaine action : {a.stage} ({now()})")
        print(show(*load(path), loops, tasks))
        return 0
    if a.action == "back":
        code, out = back(sections, loops, a)
        if code:
            print(out, file=sys.stderr if code == 2 else sys.stdout)
            return code
        save(path, sections, out, loops)
        print(show(*load(path), loops, tasks))
        return 0
    if not a.stage:
        print(f"error: {a.action} needs a stage", file=sys.stderr)
        return 2
    if a.action in ("progress", "block", "skip") and not a.detail:
        print(f"error: {a.action} needs --detail", file=sys.stderr)
        return 2

    title, rows = locate(sections, a.stage, a.sprint)
    row = next(r for r in rows if r[0] == a.stage)
    where = f"`{a.stage}`" + (f" (sprint {a.sprint})" if a.sprint else "")
    if a.action == "start":
        before = rows[: rows.index(row)]
        if title != "Cahier des charges" or a.stage != "hosa":
            prev_pipe = [t for t, _ in PIPELINES]
            if title in prev_pipe:
                for t in prev_pipe[: prev_pipe.index(title)]:
                    before = sections[t] + before
        pending = [r[0] for r in before if r[1] not in CLOSED]
        if pending and not a.force:
            print(f"✗ {where} ne peut pas démarrer : étape(s) précédente(s) pas faite(s) — "
                  + ", ".join(f"`{p}`" for p in pending)
                  + ". Fais-les d'abord, ou relance avec --force si l'utilisateur confirme.")
            return 1
        row[1:] = [DOING, now(), a.detail or row[3]]
        resume = f"- En cours : {where}" + (f" — {a.detail}" if a.detail else "") + \
                 (f"\n- Prochaine action : {a.reprise}" if a.reprise else "")
    elif a.action == "progress":
        row[1:] = [DOING, now(), a.detail]
        resume = f"- En cours : {where} — {a.detail}" + (f"\n- Prochaine action : {a.reprise}" if a.reprise else "")
    elif a.action == "done":
        gaps = check(a.kb, a.stage, a.sprint)
        if gaps and not a.force:
            print(f"✗ {where} ne peut pas être fait : preuve(s) manquante(s)\n"
                  + "\n".join(f"- {g}" for g in gaps)
                  + "\nComplète-les, ou relance avec --force si l'utilisateur accepte.")
            return 1
        row[1:] = [DONE, now(), a.detail]
        resume = ""
        scope = a.sprint if a.stage in SPRINT else ""
        tasks = [t for t in tasks if (t["stage"], t["scope"]) != (a.stage, scope)]  # their outputs are in the KB
        for lp in loops:  # the stage came out clean: its loops are over
            if lp["from"] == a.stage and lp["etat"] == OPEN and (lp["scope"].split(", ")[0] or None) == a.sprint:
                lp.update(etat=SHUT, at=now())
    elif a.action == "block":
        # the questions in full survive a /clear in the resume point; the table keeps their first line
        row[1:] = [BLOCKED, now(), a.detail.strip().splitlines()[0]]
        resume = f"- Bloqué : {where} — {a.detail.strip()}"
    elif a.action == "skip":
        row[1:] = [SKIPPED, now(), a.detail]
    save(path, sections, resume, loops, tasks)
    print(show(*load(path), loops, tasks))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
