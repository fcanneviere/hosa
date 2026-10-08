#!/usr/bin/env python3
"""Pull exactly what a task needs out of the KB — no model, no summary.

  kb_query.py <kb-dir> [filters] [what to show]

Filters (combined with AND):
  --type T            concept type (Ticket, Exigence, Persona, …)
  --bundle B          first folder under the KB (tickets, cdc, test, …)
  --where key=v1,v2   frontmatter field equals one of the values (repeatable)
  --where key~text    frontmatter field contains text (lists included: tags~securite)
  --slug S            file name without .md (repeatable)
  --grep TEXT         body contains TEXT (case-insensitive)

What to show (default: one line per concept, like the summary):
  --fields a,b        frontmatter fields
  --sections "A,B"    body sections whose `## ` heading starts with A or B (case-insensitive)
  --full              the whole body
  --count             only the number of matches
  --max-chars N       cap the output (default 15000), with a note of what was cut

Examples:
  kb_query.py .hosa/kb --type Exigence --where status=stable --sections "Données en entrée,Données en sortie"
  kb_query.py .hosa/kb --type Ticket --where sprint=s3 --sections "Note sécurité,Critères"
  kb_query.py .hosa/kb --bundle cdc --where tags~securite --full

Exit: 0 (even with no match — the output says so), 2 bad invocation. Stdlib only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKIP_FILES = {"log.md", "index.md", "sommaire.md"}


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
        elif key and re.match(r"^\s+-\s+", line):  # block list item
            fm[key] = (fm[key] + ", " if fm[key] else "") + re.sub(r"^\s+-\s+", "", line).strip("'\"")
    return fm, m.group(2)


def sections(body: str, wanted: list[str]) -> list[str]:
    out, keep = [], False
    for line in body.splitlines():
        if line.startswith("## "):
            title = line[3:].strip().lower()
            keep = any(title.startswith(w.lower()) for w in wanted)
        if keep:
            out.append(line)
    return out


def matches(fm: dict[str, str], body: str, path: Path, kb: Path, a) -> bool:
    if a.type and fm.get("type") != a.type:
        return False
    if a.bundle and path.relative_to(kb).parts[0] != a.bundle:
        return False
    if a.slug and path.stem not in a.slug:
        return False
    if a.grep and a.grep.lower() not in body.lower():
        return False
    for cond in a.where or []:
        if "~" in cond and ("=" not in cond or cond.index("~") < cond.index("=")):
            k, v = cond.split("~", 1)
            if v.lower() not in fm.get(k, "").lower():
                return False
        elif "=" in cond:
            k, v = cond.split("=", 1)
            if fm.get(k, "") not in [x.strip() for x in v.split(",")]:
                return False
        else:
            raise SystemExit(f"error: --where needs key=value or key~text, got `{cond}`")
    return True


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Extract exactly what you need from the KB.")
    ap.add_argument("kb", type=Path)
    ap.add_argument("--type")
    ap.add_argument("--bundle")
    ap.add_argument("--where", action="append")
    ap.add_argument("--slug", action="append")
    ap.add_argument("--grep")
    ap.add_argument("--fields")
    ap.add_argument("--sections")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--count", action="store_true")
    ap.add_argument("--max-chars", type=int, default=15000)
    a = ap.parse_args(argv)
    if not a.kb.is_dir():
        print(f"error: {a.kb} is not a directory", file=sys.stderr)
        return 2

    hits = []
    for f in sorted(a.kb.rglob("*.md")):
        rel = f.relative_to(a.kb)
        if f.name in SKIP_FILES or (rel.parts and rel.parts[0] == "code"):
            continue
        try:
            fm, body = split(f.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue
        if matches(fm, body, f, a.kb, a):
            hits.append((rel, fm, body))

    if a.count:
        print(len(hits))
        return 0
    if not hits:
        print("Aucun concept ne correspond.")
        return 0

    wanted = [w.strip() for w in a.sections.split(",")] if a.sections else []
    fields = [x.strip() for x in a.fields.split(",")] if a.fields else []
    blocks = []
    for rel, fm, body in hits:
        state = fm.get("status") or fm.get("state", "")
        head = f"### {rel.as_posix()} — {fm.get('title') or rel.stem} ({fm.get('type', '?')}{' · ' + state if state else ''})"
        lines = [head] + [f"- {k}: {fm.get(k, '—')}" for k in fields]
        if a.full:
            lines.append(body.strip())
        elif wanted:
            found = sections(body, wanted)
            lines += found or [f"(aucune section {', '.join(wanted)})"]
        blocks.append("\n".join(lines))

    out, used, shown = [], 0, 0
    for b in blocks:
        if used + len(b) > a.max_chars and shown:
            break
        out.append(b)
        used += len(b) + 2
        shown += 1
    print(f"{len(hits)} concept(s)." + (f" Affichés : {shown} — {len(hits) - shown} coupé(s) par --max-chars ; affine le filtre." if shown < len(hits) else ""))
    print("\n\n".join(out))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
