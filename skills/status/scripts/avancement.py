#!/usr/bin/env python3
"""Hosa progress plan — `.hosa/kb/project/avancement.md`.

Keeps every pipeline stage with its status, and a resume point, so an
interrupted session (limit reached, crash, new day) picks up exactly where
the work stopped, in the right order.

  avancement.py <kb> show
  avancement.py <kb> start    <stage> [--sprint S] [--detail D] [--reprise R] [--force]
  avancement.py <kb> progress <stage> [--sprint S]  --detail D  [--reprise R]
  avancement.py <kb> done     <stage> [--sprint S] [--detail D]
  avancement.py <kb> block    <stage> [--sprint S]  --detail D
  avancement.py <kb> skip     <stage> [--sprint S]  --detail D   (non applicable)
  avancement.py <kb> reprise  "<next action>"                     (outside the pipeline)

`start` refuses (exit 1) while an earlier stage of the same pipeline isn't
done or skipped — `--force` only once the user has confirmed going out of
order. Sprint stages need `--sprint`. Exit 2 = bad invocation. Stdlib only.
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


def next_open(sections: dict) -> str:
    for title, rows in sections.items():
        if title.startswith("Sprint ") and all(r[1] in CLOSED for r in rows):
            continue
        for r in rows:
            if r[1] not in CLOSED:
                return f"`{r[0]}` ({title}) — {r[1]}"
    return "toutes les étapes connues sont faites — composer un nouveau sprint (`sprint`)"


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
    ap.add_argument("action", choices=["show", "start", "progress", "done", "block", "skip", "reprise"])
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
