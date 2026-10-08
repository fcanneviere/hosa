#!/usr/bin/env python3
"""Check that the interface design is complete — `kb/interface/navigation.md`.

  - every functional `stable` Exigence (not tagged `nfr`) is served by a screen
    listed in `## Écrans`;
  - every screen has a route and an entry point ("Accès depuis"), so none is
    orphaned;
  - every item of the UX fundamentals checklist (read from the `## UX
    Fundamentals` section of `agents/ux-designer.md`, the single source) is
    marked "Fait" or "Non applicable : <raison>" in `## Fondamentaux UX`.

Run:  python interface_check.py <kb-dir>
Exit: 0 complete, 1 gaps listed, 2 bad invocation. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

AGENT = Path(__file__).resolve().parents[3] / "agents" / "ux-designer.md"


def split(text: str) -> tuple[str, str]:
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    return (m.group(1), m.group(2)) if m else ("", text)


def field(front: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.*?)\s*$", front, re.M)
    return m.group(1).strip("'\"") if m else ""


def section(body: str, heading: str) -> str | None:
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1) if m else None


def checklist() -> list[str]:
    fundamentals = section(AGENT.read_text(encoding="utf-8"), "UX Fundamentals") or ""
    return re.findall(r"^- \*\*(.+?)\*\*", fundamentals, re.M)


def gaps(kb: Path) -> list[str]:
    nav = kb / "interface" / "navigation.md"
    if not nav.is_file():
        return ["`interface/navigation.md` absent — pas de plan de navigation"]
    front, body = split(nav.read_text(encoding="utf-8"))
    out = []
    if field(front, "type") != "Plan de navigation":
        out.append("`interface/navigation.md` n'est pas un `Plan de navigation`")

    screens = section(body, "Écrans")
    if screens is None:
        out.append("section `## Écrans` absente")
        screens = ""
    rows = [r for r in screens.splitlines()
            if r.strip().startswith("|") and not re.match(r"^\s*\|[\s|:-]+\|\s*$", r)][1:]
    if not rows:
        out.append("aucun écran listé dans `## Écrans`")
    for r in rows:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        name = cells[0] if cells else "?"
        if len(cells) < 5 or not cells[1]:
            out.append(f"écran « {name} » sans route")
        elif not cells[4]:
            out.append(f"écran « {name} » orphelin — rien n'y mène (« Accès depuis » vide)")
    linked = {Path(t).stem for t in re.findall(r"\]\(([^)\s]*cdc/[^)\s]+\.md)\)", screens)}
    for ex in sorted((kb / "cdc").glob("*.md")):
        f, _ = split(ex.read_text(encoding="utf-8"))
        if field(f, "type") != "Exigence" or field(f, "status") != "stable":
            continue
        if re.search(r"^tags:.*\bnfr\b", f, re.M) or re.search(r"^\s*-\s*nfr\s*$", f, re.M):
            continue
        if ex.stem not in linked:
            out.append(f"exigence `{ex.stem}` servie par aucun écran")

    review = section(body, "Fondamentaux UX")
    if review is None:
        out.append("section `## Fondamentaux UX` absente")
        review = ""
    for item in checklist():
        m = re.search(rf"^- \*\*{re.escape(item)}\*\*\s*[—–-]\s*(.*)$", review, re.M)
        if not m:
            out.append(f"fondamental UX « {item} » non traité")
        elif not re.match(r"(Fait|Non applicable)\s*:\s*\S", m.group(1)):
            out.append(f"fondamental UX « {item} » ni Fait ni Non applicable justifié")
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 1 or not Path(argv[0]).is_dir():
        print("usage: interface_check.py <kb-dir>", file=sys.stderr)
        return 2
    if not checklist():
        print(f"error: no UX fundamentals found in {AGENT}", file=sys.stderr)
        return 2
    found = gaps(Path(argv[0]))
    for g in found:
        print(f"✗ {g}")
    print("✓ interface complète" if not found else f"{len(found)} manque(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
