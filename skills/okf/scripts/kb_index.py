#!/usr/bin/env python3
"""Write `.hosa/kb/sommaire.md`: one line per KB concept, so agents read the
summary first and open only the files they need, instead of reading whole
bundles.

  kb_index.py <kb-dir>          (re)write the summary
  kb_index.py <kb-dir> --print  print it instead

Each line: [title](path) — type · status/state · priority · sprint — description.
Generated bundles (`code/`), `log.md`, `index.md` and the summary itself are
left out. Stdlib only; the frontmatter is read with a tolerant line parser.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {"code"}
SKIP_FILES = {"log.md", "index.md", "sommaire.md"}
FIELDS = ("type", "title", "description", "status", "state", "priority", "sprint", "espace")


def frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.S)
    out: dict[str, str] = {}
    if not m:
        return out
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_]+):\s*(.*?)\s*$", line)
        if kv and kv.group(1) in FIELDS:
            out[kv.group(1)] = kv.group(2).strip("'\"")
    return out


def build(kb: Path) -> str:
    bundles: dict[str, list[str]] = {}
    for f in sorted(kb.rglob("*.md")):
        rel = f.relative_to(kb)
        if f.name in SKIP_FILES or (rel.parts and rel.parts[0] in SKIP_DIRS):
            continue
        try:
            fm = frontmatter(f.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue
        meta = " · ".join(x for x in (
            fm.get("type", "?"), fm.get("status") or fm.get("state", ""),
            f"priorité {fm['priority']}" if fm.get("priority") else "",
            f"sprint {fm['sprint']}" if fm.get("sprint") else "",
            f"espace {fm['espace']}" if fm.get("espace") else "") if x)
        desc = fm.get("description", "")
        line = f"- [{fm.get('title') or rel.stem}]({rel.as_posix()}) — {meta}" + (f" — {desc}" if desc else "")
        bundles.setdefault(rel.parts[0] if len(rel.parts) > 1 else ".", []).append(line)
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    out = ["---", "type: Sommaire", "title: Sommaire de la KB",
           "description: Une ligne par concept — lire ceci d'abord, puis seulement les fichiers utiles",
           "tags: [pilotage]", f"generated: {{ by: process:hosa-kb-index, at: {stamp} }}", "---"]
    total = sum(len(v) for v in bundles.values())
    out.append(f"{total} concepts. Extraire une partie précise : `kb_query.py <kb> --type … --where … --sections …`. Code : `graph.py map` (bundle `code/`, non listé ici).\n")
    for name in sorted(bundles, key=lambda b: (b == ".", b)):
        out.append(f"## {name if name != '.' else 'racine'} ({len(bundles[name])})")
        out += bundles[name] + [""]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if not argv or not Path(argv[0]).is_dir():
        print("usage: kb_index.py <kb-dir> [--print]", file=sys.stderr)
        return 2
    kb = Path(argv[0])
    text = build(kb)
    if "--print" in argv[1:]:
        print(text)
    else:
        target = kb / "sommaire.md"
        old = target.read_text(encoding="utf-8") if target.exists() else ""
        strip = lambda t: re.sub(r"^generated:.*$", "", t, flags=re.M)
        if strip(old) != strip(text):  # no rewrite when only the timestamp would change
            target.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
