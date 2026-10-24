#!/usr/bin/env python3
"""Check that the interface names each thing one way — `kb/interface/lexique.md`.

  lexique_check.py <kb-dir> <project-root>

Reads the `## Termes` table of the lexicon (Terme | Désigne | Où | Synonymes
interdits) and the optional `## Dossiers analysés` list, then scans the
interface's text files for every forbidden synonym (whole word, any case).
Also checks every screen of `kb/interface/navigation.md` is a lexicon term.

Exit: 0 consistent, 1 problems listed (file:line), 2 bad invocation. Stdlib only.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

EXTENSIONS = {".html", ".htm", ".vue", ".svelte", ".jsx", ".tsx", ".js", ".ts", ".mjs",
              ".json", ".yml", ".yaml", ".po", ".properties", ".xml", ".twig", ".jinja",
              ".j2", ".erb", ".hbs", ".ejs", ".php", ".cshtml", ".razor", ".dart", ".kt",
              ".swift", ".py", ".rb", ".md", ".txt", ".strings", ".arb"}
SKIP = {"node_modules", ".git", ".hosa", ".worktrees", "dist", "build", "vendor", "coverage",
        "migrations", "__pycache__", ".venv", "venv", ".next", ".nuxt", "target",
        "docs", ".claude", "staticfiles", ".mypy_cache", ".pytest_cache", ".ruff_cache"}


def section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def lexicon(kb: Path) -> tuple[dict[str, list[str]], list[str], list[str]]:
    """{term: [forbidden synonyms]}, folders to scan, problems."""
    path = kb / "interface" / "lexique.md"
    if not path.is_file():
        return {}, [], ["`interface/lexique.md` absent — pas de lexique de l'interface"]
    text = path.read_text(encoding="utf-8")
    rows = [r for r in section(text, "Termes").splitlines()
            if r.strip().startswith("|") and not re.match(r"^\s*\|[\s|:-]+\|\s*$", r)][1:]
    terms: dict[str, list[str]] = {}
    for r in rows:
        c = cells(r) + ["", "", "", ""]
        if c[0]:
            terms[c[0]] = [s.strip() for s in re.split(r"[,;]", c[3]) if s.strip() and s.strip() not in ("—", "-")]
    # the path only: the backticked part, else the first word — a comment after it is not part of it
    folders = [a or b for a, b in re.findall(r"^- (?:`([^`]+)`|(\S+))", section(text, "Dossiers analysés"), re.M)]
    return terms, folders, ([] if terms else ["`## Termes` vide — aucun terme défini"])


def screens(kb: Path) -> list[str]:
    nav = kb / "interface" / "navigation.md"
    if not nav.is_file():
        return []
    rows = [r for r in section(nav.read_text(encoding="utf-8"), "Écrans").splitlines()
            if r.strip().startswith("|") and not re.match(r"^\s*\|[\s|:-]+\|\s*$", r)][1:]
    return [cells(r)[0] for r in rows if cells(r)[0]]


def files(root: Path, base: Path):
    if base.is_file():
        yield base
        return
    for d, dirs, names in os.walk(base):
        dirs[:] = [x for x in dirs if x not in SKIP]  # never walk into them: .venv alone took minutes
        for n in names:
            if Path(n).suffix.lower() in EXTENSIONS and ".min." not in n:
                yield Path(d) / n


def scan(root: Path, folders: list[str], terms: dict[str, list[str]]) -> list[str]:
    out = []
    pairs = [(re.compile(rf"(?<![\w-]){re.escape(s)}(?![\w-])", re.I), s, t) for t, syns in terms.items() for s in syns]
    for base in [root / f for f in folders] or [root]:
        for f in files(root, base):
            try:
                lines = f.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            for n, line in enumerate(lines, 1):
                for pattern, synonym, term in pairs:
                    if pattern.search(line):
                        out.append(f"{f.relative_to(root)}:{n} — « {synonym} » au lieu de « {term} »")
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not Path(argv[0]).is_dir() or not Path(argv[1]).is_dir():
        print("usage: lexique_check.py <kb-dir> <project-root>", file=sys.stderr)
        return 2
    kb, root = Path(argv[0]), Path(argv[1])
    terms, folders, found = lexicon(kb)
    lowered = {t.lower() for t in terms}
    found += [f"écran « {s} » absent du lexique" for s in screens(kb) if terms and s.lower() not in lowered]
    missing = [f for f in folders if not (root / f).exists()]
    found += [f"dossier analysé introuvable : {f}" for f in missing]
    found += scan(root, [f for f in folders if f not in missing], terms)
    for g in found:
        print(f"✗ {g}")
    print("✓ nommage cohérent" if not found else f"{len(found)} incohérence(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
