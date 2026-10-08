#!/usr/bin/env python3
"""Check that Hosa tickets are complete — ready to be planned and executed.

A ticket is complete when it has, in its body:
  - a user story ("En tant que ...") and a "Lié à :" line,
  - a "## Critères d'acceptation" section with at least one scenario,
  - "## Note technique (senior dev)", "## Placement architecture (architecte)",
    "## Placement interface (UX/UI)" and "## Note sécurité (expert
    cybersécurité)" sections holding a real note, not
    `backlog`'s "pas encore évalué/déterminé" fallback line.

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
}


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
    if not field(front, "priority"):
        missing.append("(info) pas de `priority` — passera après les tickets priorisés")
    return missing


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
