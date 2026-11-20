#!/usr/bin/env python3
"""Lit une partie d'un fichier, lignes numérotées, sous un plafond — à la place de `cat`, `sed -n` ou `head`.

  <hosa> lire <cible> [<cible>…] [--max-chars N]

Une cible :
  chemin               le fichier entier s'il tient sous le plafond, sinon son plan (titres ou définitions, numérotés)
  chemin:120-180       les lignes 120 à 180 (aussi chemin:120:60 = 60 lignes depuis 120, chemin:120 = jusqu'à la fin)
  chemin#Titre         la section Markdown de ce titre, jusqu'au titre suivant de même niveau ou plus haut

Plusieurs cibles partagent le plafond (12 000 caractères par défaut, environ 3 k tokens) : au-delà, les cibles
restantes donnent leur plan. Un chemin introuvable donne les noms proches. Idées reprises de qmd (MIT,
github.com/tobi/qmd) : `get chemin:début:nombre`, `multi-get --max-bytes`, numéros de ligne, suggestions.
Code de sortie : 0, ou 1 si une cible est introuvable.
"""
import argparse
import difflib
import re
import sys
from pathlib import Path

MAX_CHARS = 12000
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
DEF = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:def|class|function|func|fn|pub\s+fn|interface|type|enum|struct|impl)\b"
                 r"|^\s*(?:export\s+)?const\s+\w+\s*=\s*(?:async\s*)?(?:\(|function)"
                 r"|^\s*(?:public|private|protected)\s+[\w<>\[\], ]+\s+\w+\s*\(")
TARGET = re.compile(r"^(?P<path>.+?)(?::(?P<a>\d+)(?:(?P<sep>[-:])(?P<b>\d+))?)?$")


def parse(target):
    """(path, first line, last line or None, section title or None) — lines 1-based, inclusive."""
    if "#" in target:
        p, _, title = target.partition("#")
        if p and title:
            return p, None, None, title
    m = TARGET.match(target)
    a = m.group("a")
    if a is None:
        return target, None, None, None
    a, b = int(a), m.group("b")
    if b is None:
        return m.group("path"), a, None, None
    b = int(b)
    return m.group("path"), a, (a + b - 1 if m.group("sep") == ":" else b), None


def numbered(lines, start):
    width = len(str(start + len(lines) - 1))
    return "".join(f"{i:>{width}}\t{l}\n" for i, l in enumerate(lines, start))


def outline(lines, path):
    if path.suffix.lower() in (".md", ".markdown"):
        return [f"{i + 1:>6}\t{lines[i].rstrip()[:120]}" for i, _, _ in headings(lines)]
    return [f"{i:>6}\t{l.rstrip()[:120]}" for i, l in enumerate(lines, 1) if DEF.match(l)]


def headings(lines):
    """(index, level, text) of each Markdown heading outside a code fence."""
    out, fence = [], False
    for i, l in enumerate(lines):
        if l.lstrip().startswith("```"):
            fence = not fence
        elif not fence and (m := HEADING.match(l)):
            out.append((i, len(m.group(1)), m.group(2)))
    return out


def section(lines, title):
    want = title.strip().lstrip("#").strip().lower()
    heads = headings(lines)
    for exact in (True, False):
        for k, (i, level, text) in enumerate(heads):
            t = text.lower()
            if t == want if exact else t.startswith(want) or want in t:
                end = next((j for j, lv, _ in heads[k + 1:] if lv <= level), len(lines))
                return i + 1, end
    return None


def suggest(path):
    parent = path.parent
    while not parent.is_dir() and parent != parent.parent:
        parent = parent.parent
    try:
        names = [p.name for p in parent.iterdir()]
    except OSError:
        return []
    return [str(parent / n) for n in difflib.get_close_matches(path.name, names, n=5, cutoff=0.5)]


def render(target, budget):
    """(text, ok): the excerpt, or the file's outline when it doesn't fit `budget`."""
    raw, a, b, title = parse(target)
    path = Path(raw)
    if not path.is_file():
        near = suggest(path)
        return f"== {raw} : introuvable." + (" Noms proches :\n" + "\n".join(f"  {n}" for n in near) if near else "") + "\n", False
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    total = len(lines)
    if title is not None:
        found = section(lines, title)
        if not found:
            heads = outline(lines, path) if path.suffix.lower() in (".md", ".markdown") else []
            return f"== {raw} : pas de section « {title} ». Titres :\n" + "\n".join(heads) + "\n", False
        a, b = found
    a = max(1, a or 1)
    b = min(total, b or total)
    body = numbered(lines[a - 1:b], a) if a <= b else ""
    head = f"== {raw} — lignes {a}-{b} sur {total}\n" if (a, b) != (1, total) else f"== {raw} — {total} lignes\n"
    if len(body) <= budget:
        return head + body, True
    plan = outline(lines, path)
    return (f"== {raw} — lignes {a}-{b} sur {total} : {len(body):,} caractères, au-delà du plafond ({budget:,}). "
            f"Lis une plage (`{raw}:<début>-<fin>`) ou une section (`{raw}#<titre>`).\n"
            + ("Plan :\n" + "\n".join(plan[:80]) + ("\n  …" if len(plan) > 80 else "") + "\n" if plan else "")), True


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lire", description=__doc__.split("\n\n")[0])
    ap.add_argument("cibles", nargs="+")
    ap.add_argument("--max-chars", type=int, default=MAX_CHARS)
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    left, ok = args.max_chars, True
    for t in args.cibles:
        text, found = render(t, max(left, 0))
        ok &= found
        sys.stdout.write(text)
        left -= len(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
