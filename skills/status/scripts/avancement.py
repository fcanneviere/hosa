#!/usr/bin/env python3
"""Hosa progress plan — `.hosa/kb/project/avancement.md`.

Keeps every pipeline stage with its status, and a resume point, so an
interrupted session (limit reached, crash, new day) picks up exactly where
the work stopped, in the right order.

  avancement.py <kb> show
  avancement.py <kb> next                                         (stage to run, its skill, what it still lacks)
  avancement.py <kb> check    <stage> [--sprint S]                (exit 1 + gaps when its proof is missing)
  avancement.py <kb> start    <stage> [--sprint S] [--detail D] [--reprise R] [--force]
  avancement.py <kb> progress <stage> [--sprint S]  --detail D  [--reprise R]
  avancement.py <kb> done     <stage> [--sprint S] [--detail D] [--force]
  avancement.py <kb> block    <stage> [--sprint S]  --detail D
  avancement.py <kb> skip     <stage> [--sprint S]  --detail D   (non applicable)
  avancement.py <kb> reprise  "<next action>"                     (outside the pipeline)

`start` refuses (exit 1) while an earlier stage of the same pipeline isn't
done or skipped — `--force` only once the user has confirmed going out of
order. `done` on a sprint stage refuses (exit 1) while `check` finds a gap —
same `--force` rule. Sprint stages need `--sprint`. Exit 2 = bad invocation.
Stdlib only.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PIPELINES = [
    ("Cahier des charges", ["hosa", "interview", "redaction", "fondamentaux", "securite",
                            "relecture", "contestation"]),
    ("Structuration", ["stack", "infra", "donnees", "schema-app", "schema-db",
                       "architecture", "menaces", "interface", "backlog"]),
]
SPRINT = ["sprint", "qa-plan", "git-demarrage", "develop", "qa", "validation",
          "git-fusion", "bilan-sprint", "livraison"]
TODO, DOING, DONE, BLOCKED, SKIPPED = "à faire", "en cours", "fait", "bloqué", "non applicable"
CLOSED = {DONE, SKIPPED}
ROW = re.compile(r"^\|\s*`?([\w-]+)`?\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load(path: Path) -> tuple[dict[str, list[list[str]]], str]:
    """{section title: [[stage, status, updated, detail], …]}, resume point."""
    sections = {title: [[s, TODO, "", ""] for s in stages] for title, stages in PIPELINES}
    resume = ""
    if not path.exists():
        return sections, resume
    current = None
    body = path.read_text(encoding="utf-8").split("\n---\n", 1)[-1]
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
            rows[:] = [next((r for r in rows if r[0] == s), [s, TODO, "", ""]) for s in SPRINT] + \
                      [r for r in rows if r[0] not in SPRINT and r[0] in known]
    return sections, resume.strip()


def save(path: Path, sections: dict, resume: str) -> None:
    out = ["---", "type: Plan d'avancement", "title: Plan d'avancement",
           "description: Étapes du projet, leur statut et le point de reprise",
           "tags: [pilotage]", f"generated: {{ by: process:hosa-avancement, at: {now()} }}", "---",
           "## Point de reprise", resume or "- Rien en cours.", ""]
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


SKILL = {"git-demarrage": "git", "git-fusion": "git", "menaces": "securite"}


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
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


def check(kb: Path, stage: str, sprint: str | None) -> list[str]:
    """What the KB lacks to prove a sprint stage done. `hooks/gate.js` runs
    `check validation` before a sprint lands."""
    if stage not in SPRINT or not sprint:
        return []
    s = read(kb / "sprints" / f"{sprint}.md")
    if s is None:
        return [f"sprint `{sprint}` absent de kb/sprints/"]
    tickets = re.findall(r"\(\.\./tickets/([^)]+)\.md\)", section(s, "Tickets") or "")
    gaps = [] if tickets else ["`## Tickets` ne liste aucun ticket"]
    if stage == "git-demarrage" and not field(s, "worktree"):
        gaps.append("le sprint n'a pas de `worktree` (`git` Mode 1)")
    if stage == "git-fusion" and not field(s, "merge_commit"):
        gaps.append("le sprint n'a pas de `merge_commit` (`git` Mode 2)")
    if stage == "bilan-sprint" and read(kb / "sprints" / f"{sprint}-review.md") is None:
        gaps.append(f"pas de `kb/sprints/{sprint}-review.md` (`bilan-sprint`)")
    tests = sorted(p.name for p in (kb / "test").glob("*.md")) if (kb / "test").is_dir() else []
    for t in tickets:
        text = read(kb / "tickets" / f"{t}.md")
        plan = read(kb / "test" / f"{t}-technique.md")
        criteria = re.findall(r"^-\s*(CA\d+)\b", section(text, "Critères d'acceptation") or "", re.M)
        if stage == "qa-plan":
            if plan is None:
                gaps.append(f"{t} : pas de plan `kb/test/{t}-technique.md` (`qa-plan`)")
            missing = [ca for ca in criteria if f"[{ca}]" not in (plan or "")]
            if missing:
                gaps.append(f"{t} : {', '.join(missing)} sans cas de test [CAn] (`qa-plan`)")
        if stage == "develop":
            verdicts = re.findall(r"\b(PASS-WITH-NOTES|PASS|FAIL)\b", section(text, "Revue") or "")
            if not verdicts or verdicts[-1] == "FAIL":
                gaps.append(f"{t} : dernière `## Revue` {verdicts[-1] if verdicts else 'absente'} (`develop`)")
        if stage in ("qa", "validation") and section(plan, "Résultats techniques") is None:
            gaps.append(f"{t} : pas de `## Résultats techniques` (`qa`)")
        if stage == "validation":
            if field(text, "state") != "done" or not field(text, "verified"):
                gaps.append(f"{t} : pas `done` et `verified` (`validation`)")
            proofs = plan or ""
            for f in (x for x in tests if x.startswith(f"{t}-") and x != f"{t}-technique.md"):
                r = read(kb / "test" / f) or ""
                if re.search(r"^\s*Refusé", section(r, "Verdict") or "", re.M):
                    gaps.append(f"{f} : recette Refusé")
                if re.search(r"^-\s*CA\d+\s*—\s*Non\s*—", r, re.M):
                    gaps.append(f"{f} : un critère répondu Non")
                proofs += "\n" + r
            unproved = [ca for ca in criteria
                        if not re.search(rf"\[{ca}\]|^-\s*{ca}\s*—\s*Oui\b", proofs, re.M)]
            if unproved:
                gaps.append(f"{t} : {', '.join(unproved)} prouvé(s) par aucun cas [CAn] ni recette Oui (`qa-plan`)")
    if stage == "validation":
        bloquants = re.findall(r"Bloquant\s*:\s*(\d+)", section(s, "Audit") or "")
        if not bloquants:
            gaps.append("pas de `## Audit` avec sa ligne `Bloquant : N` (`validation` étape 3a)")
        elif bloquants[-1] != "0":
            gaps.append(f"`## Audit` : Bloquant : {bloquants[-1]}")
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


def show(sections: dict, resume: str) -> str:
    lines = ["## Point de reprise", resume or "- Rien en cours.",
             f"- Prochaine étape du plan : {next_open(sections)}"]
    for title, rows in sections.items():
        doing = [f"`{r[0]}` {r[1]}" + (f" — {r[3]}" if r[3] else "") for r in rows if r[1] in (DOING, BLOCKED)]
        if doing:
            lines.append(f"- {title} : " + " ; ".join(doing))
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("kb", type=Path)
    ap.add_argument("action", choices=["show", "next", "check", "start", "progress", "done", "block", "skip", "reprise"])
    ap.add_argument("stage", nargs="?")
    ap.add_argument("--sprint")
    ap.add_argument("--detail", default="")
    ap.add_argument("--reprise", default="")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    if not a.kb.is_dir():
        print(f"error: {a.kb} is not a directory", file=sys.stderr)
        return 2
    path = a.kb / "project" / "avancement.md"
    sections, resume = load(path)

    if a.action == "show":
        print(show(sections, resume))
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
        print(show(*load(path)))
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
    elif a.action == "block":
        row[1:] = [BLOCKED, now(), a.detail]
        resume = f"- Bloqué : {where} — {a.detail}"
    elif a.action == "skip":
        row[1:] = [SKIPPED, now(), a.detail]
    save(path, sections, resume)
    print(show(*load(path)))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
