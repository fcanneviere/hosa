#!/usr/bin/env python3
"""Check that the interface design is complete — `kb/interface/navigation.md`.

  - every functional `stable` Exigence (not tagged `nfr`) is served by a screen
    listed in `## Écrans`, in each space (front-office / back-office) its
    `espace` names;
  - every screen has a route, an entry point ("Accès depuis") so none is
    orphaned, and a space; both spaces exist;
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

SPACES = re.compile(r"\b(front-office|back-office)\b")
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
    served: dict[str, set[str]] = {}
    for r in rows:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        cells += [""] * (6 - len(cells))
        name = cells[0] or "?"
        space = set(SPACES.findall(cells[5]))
        if not cells[1]:
            out.append(f"écran « {name} » sans route")
        if not cells[4]:
            out.append(f"écran « {name} » orphelin — rien n'y mène (« Accès depuis » vide)")
        if not space:
            out.append(f"écran « {name} » sans espace (front-office / back-office)")
        for t in re.findall(r"\]\(([^)\s]*cdc/[^)\s]+\.md)\)", cells[3]):
            served.setdefault(Path(t).stem, set()).update(space)
    all_spaces = set(SPACES.findall(screens))
    for needed in ("front-office", "back-office"):
        if rows and needed not in all_spaces:
            out.append(f"aucun écran {needed} — les deux espaces sont attendus")
    for ex in sorted((kb / "cdc").glob("*.md")):
        f, _ = split(ex.read_text(encoding="utf-8"))
        if field(f, "type") != "Exigence" or field(f, "status") != "stable":
            continue
        if re.search(r"^tags:.*\bnfr\b", f, re.M) or re.search(r"^\s*-\s*nfr\s*$", f, re.M):
            continue
        wanted = set(SPACES.findall(field(f, "espace")))
        if not wanted:
            out.append(f"exigence `{ex.stem}` sans `espace` (front-office / back-office) — à préciser par le PO")
        if ex.stem not in served:
            out.append(f"exigence `{ex.stem}` servie par aucun écran")
        else:
            for sp in sorted(wanted - served[ex.stem]):
                out.append(f"exigence `{ex.stem}` sans écran {sp}")

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
