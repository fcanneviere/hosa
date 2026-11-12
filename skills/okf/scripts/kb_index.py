#!/usr/bin/env python3
"""Write `.hosa/kb/sommaire.md`: one line per KB concept, so agents read the
summary first and open only the files they need, instead of reading whole
bundles.

  kb_index.py <kb-dir>          (re)write the summary
  kb_index.py <kb-dir> --print  print it instead

Each line: [title](path) — type · status/state · priority · sprint — description,
cut at DESC_MAX characters: the summary is read first by every agent. Generated bundles (`code/`), `log.md`, `index.md` and the summary itself are
left out, and so is anything under a hidden folder. Past BUDGET bytes, closed concepts (`done`,
`deprecated`) become one count line per bundle, then the bundles with the most description text lose
their descriptions; each cut line names the `kb_query` command that gives it back. Stdlib only; the
frontmatter is read with kb_query's tolerant line parser.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kb_query import concept_files, split, text_of  # noqa: E402 — one frontmatter reader for both scripts

DESC_MAX = 160
# The summary is read whole by every agent (read-guard lets it through): past this size, closed concepts
# become one count line, then the biggest bundles lose their descriptions — each time with the kb_query
# command that gives them back. ~13 k tokens, half of what one Read takes. A bundle whose descriptions weigh
# under a twentieth of it keeps them: cutting them saves little and loses the most useful lines (cdc, rules).
# Still over: the bundle with the most line text becomes one count line per state, until it fits.
BUDGET = 48_000
CLOSED = {"done", "deprecated"}
ACTIVE = {"doing", "blocked"}  # a folded bundle still lists them: the sprint in progress


def frontmatter(text: str) -> dict:
    return split(text)[0]


def _entries(kb: Path) -> dict[str, list[dict]]:
    bundles: dict[str, list[dict]] = {}
    for f, rel in concept_files(kb):
        try:
            fm = {k: text_of(v) for k, v in frontmatter(f.read_text(encoding="utf-8")).items()}
        except (UnicodeDecodeError, OSError):
            continue
        state = fm.get("status") or fm.get("state", "")
        meta = " · ".join(x for x in (
            fm.get("type", "?"), state,
            f"priorité {fm['priority']}" if fm.get("priority") else "",
            f"sprint {fm['sprint']}" if fm.get("sprint") else "",
            f"espace {fm['espace']}" if fm.get("espace") else "") if x)
        desc = fm.get("description", "")
        if len(desc) > DESC_MAX:
            desc = desc[:DESC_MAX - 1].rstrip() + "…"
        bundles.setdefault(rel.parts[0] if len(rel.parts) > 1 else ".", []).append(
            {"head": f"- [{fm.get('title') or rel.stem}]({rel.as_posix()}) — {meta}", "desc": desc,
             "closed": state in CLOSED, "state": state, "field": "status" if fm.get("status") else "state"})
    return bundles


def _counts(items, sel) -> list[str]:
    """One line per state for these concepts, with the kb_query command that lists them."""
    counts: dict[tuple[str, str], int] = {}
    for e in items:
        counts[(e["field"], e["state"])] = counts.get((e["field"], e["state"]), 0) + 1
    return [f"- {n} concept(s) `{s}` non listés : `kb_query <kb> {sel} --where {f}={s}`" if s
            else f"- {n} concept(s) sans état non listés : `kb_query <kb> {sel}`" for (f, s), n in sorted(counts.items())]


def _render(bundles, collapse=False, bare=(), folded=()) -> list[str]:
    out = []
    for name in sorted(bundles, key=lambda b: (b == ".", b)):
        items, sel = bundles[name], f"--bundle {name}" if name != "." else ""
        note = f" — descriptions : `kb_query <kb> {sel} --fields description`" if name in bare and name not in folded else ""
        out.append(f"## {name if name != '.' else 'racine'} ({len(items)}){note}")
        if name in folded:
            out += [e["head"] for e in items if e["state"] in ACTIVE]
            out += _counts([e for e in items if e["state"] not in ACTIVE], sel)
        else:
            shown = [e for e in items if not (collapse and e["closed"])]
            out += [e["head"] + (f" — {e['desc']}" if e["desc"] and name not in bare else "") for e in shown]
            if collapse:
                out += _counts([e for e in items if e["closed"]], sel)
        out.append("")
    return out


def build(kb: Path, budget: int = BUDGET) -> str:
    bundles = _entries(kb)
    total = sum(len(v) for v in bundles.values())
    collapse, bare, folded = False, [], []
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    head = ["---", "type: Sommaire", "title: Sommaire de la KB",
            "description: Une ligne par concept — lire ceci d'abord, puis seulement les fichiers utiles",
            "tags: [pilotage]", f"generated: {{ by: process:hosa-kb-index, at: {stamp} }}", "---",
            f"{total} concepts. Extraire une partie précise : `kb_query.py <kb> --type … --where … --sections …`. "
            "Code : `graph.py map` (bundle `code/`, non listé ici).\n"]
    body = _render(bundles)
    size = lambda lines: len("\n".join(head + lines).encode("utf-8"))
    if size(body) > budget:
        collapse = True
        body = _render(bundles, collapse)
    while size(body) > budget:
        weight = {b: sum(len(e["desc"].encode("utf-8")) for e in bundles[b]) for b in bundles if b not in bare}
        left = [b for b, w in weight.items() if w >= budget // 20]
        if not left:
            break
        bare.append(max(left, key=weight.get))
        body = _render(bundles, collapse, bare)
    while size(body) > budget:  # last tier, always fits: the biggest bundle becomes its count lines
        weight = {b: sum(len(e["head"].encode("utf-8")) for e in bundles[b]) for b in bundles if b not in folded}
        if not weight:
            break
        folded.append(max(weight, key=weight.get))
        body = _render(bundles, collapse, bare, folded)
    return "\n".join(head + body)


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
