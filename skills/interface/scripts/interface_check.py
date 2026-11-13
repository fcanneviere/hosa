#!/usr/bin/env python3
"""Check that the interface design is complete — `kb/interface/navigation.md`.

  - every functional `stable` Exigence (not tagged `nfr`, not `hors-application`)
    is served by a screen listed in `## Écrans`, in each space (front-office /
    back-office) its `espace` names;
  - every screen has a route, an entry point ("Accès depuis") so none is
    orphaned, and a space; each space the exigences name has screens (an
    application with no front office needs none);
  - back office: every object of `kb/cdc/modele-metier.md` has its row in
    `## Gestion back office` — a list and a record screen of the back office,
    a history, the actions — or `Non applicable : <raison>`;
  - dashboards: every indicator `INn` in force in a `stable` exigence has its
    row in `## Tableaux de bord` — the screen that shows it and the detail screen
    it leads to (the records behind the number);
  - every item of the UX fundamentals checklist (read from the `## UX
    Fundamentals` section of `agents/ux-designer.md`, the single source) is
    marked "Fait" or "Non applicable : <raison>" in `## Fondamentaux UX`;
  - in a real `<root>/.hosa/kb`, the project's CSS file carries the tokens of
    `kb/interface/choix.md`, unedited (`atelier.py ecart`).

Run:  python interface_check.py <kb-dir>
Exit: 0 complete, 1 gaps listed, 2 bad invocation. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SPACES = re.compile(r"\b(front-office|back-office)\b")
AGENT = Path(__file__).resolve().parents[3] / "agents" / "ux-designer.md"
NON_APPLICABLE = re.compile(r"^Non applicable\s*:\s*\S", re.I)
INDICATOR = re.compile(r"^-\s+\*\*(IN\d+)\*\*(.*)$", re.M)


def split(text: str) -> tuple[str, str]:
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    return (m.group(1), m.group(2)) if m else ("", text)


def field(front: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.*?)\s*$", front, re.M)
    return m.group(1).strip("'\"") if m else ""


def section(body: str, heading: str) -> str | None:
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1) if m else None


def table(text: str, width: int) -> list[list[str]]:
    """The rows of the first markdown table in `text`, header dropped, each padded to `width` cells."""
    rows = [r for r in text.splitlines() if r.strip().startswith("|") and not re.match(r"^\s*\|[\s|:-]+\|\s*$", r)][1:]
    out = []
    for r in rows:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        out.append(cells + [""] * (width - len(cells)))
    return out


def plain(cell: str) -> str:
    """A cell without its markdown: `[Commandes](…)` → Commandes, `` `/admin` `` → /admin."""
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cell).replace("`", "").replace("*", "").strip()


def checklist() -> list[str]:
    fundamentals = section(AGENT.read_text(encoding="utf-8"), "UX Fundamentals") or ""
    return re.findall(r"^- \*\*(.+?)\*\*", fundamentals, re.M)


def stable_exigences(kb: Path) -> list[tuple[str, str, str]]:
    """(slug, frontmatter, body) of each `stable` Exigence."""
    out = []
    for ex in sorted((kb / "cdc").glob("*.md")) if (kb / "cdc").is_dir() else []:
        f, b = split(ex.read_text(encoding="utf-8"))
        if field(f, "type") == "Exigence" and field(f, "status") == "stable":
            out.append((ex.stem, f, b))
    return out


def objects(kb: Path) -> list[str]:
    """The business objects of `kb/cdc/modele-metier.md`: each `## <Objet>` but the notifications."""
    f = kb / "cdc" / "modele-metier.md"
    if not f.is_file():
        return []
    _, body = split(f.read_text(encoding="utf-8"))
    return [h.strip() for h in re.findall(r"^## (.+)$", body, re.M) if not h.strip().lower().startswith("notifications")]


def indicators(body: str) -> list[str]:
    """The `INn` in force under `## Indicateurs` (a retired one keeps its line: `- **IN2** — retiré : …`)."""
    return [i for i, rest in INDICATOR.findall(section(body, "Indicateurs") or "")
            if not re.match(r"\s*—\s*retirée?\b", rest, re.I)]


def back_office_gaps(body: str, kb: Path, screens: dict[str, set[str]]) -> list[str]:
    wanted = objects(kb)
    if not wanted:
        return []
    text = section(body, "Gestion back office")
    if text is None:
        return [f"section `## Gestion back office` absente : une ligne par objet du modèle métier ({', '.join(wanted)})"]
    out, rows = [], {plain(r[0]).lower(): r for r in table(text, 5)}
    for obj in wanted:
        row = rows.get(obj.lower())
        if row is None:
            out.append(f"objet « {obj} » sans ligne dans `## Gestion back office` (liste, fiche, historique, actions)")
            continue
        for col, name in ((1, "liste"), (2, "fiche"), (3, "historique")):
            cell = plain(row[col])
            if NON_APPLICABLE.match(cell):
                continue
            if not cell:
                out.append(f"objet « {obj} » : {name} vide — un écran du back office ou « Non applicable : <raison> »")
            elif cell not in screens:
                out.append(f"objet « {obj} » : {name} « {cell} » absent de `## Écrans`")
            elif col < 3 and "back-office" not in screens[cell]:
                out.append(f"objet « {obj} » : {name} « {cell} » n'est pas un écran du back office")
        if not plain(row[4]):
            out.append(f"objet « {obj} » : actions vides — ce que le back office fait sur lui (créer, corriger, archiver…)")
    return out


def dashboard_gaps(body: str, exigences: list[tuple[str, str, str]], screens: dict[str, set[str]],
                   routes: set[str]) -> list[str]:
    wanted = [(slug, i) for slug, _, b in exigences for i in indicators(b)]
    if not wanted:
        return []
    text = section(body, "Tableaux de bord")
    if text is None:
        return [f"section `## Tableaux de bord` absente : {len(wanted)} indicateur(s) à placer"]
    placed: dict[tuple[str, str], list[str]] = {}
    for row in table(text, 4):
        for slug in re.findall(r"cdc/([^)\s]+)\.md", row[1]):
            for i in re.findall(r"\bIN\d+\b", row[0]):
                placed[(slug, i)] = row
    out = []
    for slug, i in wanted:
        row = placed.get((slug, i))
        if row is None:
            out.append(f"indicateur {i} de `{slug}` placé sur aucun écran (`## Tableaux de bord`)")
            continue
        ecran, detail = plain(row[2]), plain(row[3])
        if ecran not in screens:
            out.append(f"indicateur {i} de `{slug}` : écran « {ecran or '—'} » absent de `## Écrans`")
        if not detail:
            out.append(f"indicateur {i} de `{slug}` : pas d'écran de détail — les données derrière le chiffre, "
                       "ou « Non applicable : <raison> »")
        elif not NON_APPLICABLE.match(detail) and detail not in screens and detail.split("?")[0] not in routes:
            out.append(f"indicateur {i} de `{slug}` : détail « {detail} » absent de `## Écrans`")
    return out


def gaps(kb: Path) -> list[str]:
    nav = kb / "interface" / "navigation.md"
    if not nav.is_file():
        return ["`interface/navigation.md` absent — pas de plan de navigation"]
    front, body = split(nav.read_text(encoding="utf-8"))
    out = []
    if field(front, "type") != "Plan de navigation":
        out.append("`interface/navigation.md` n'est pas un `Plan de navigation`")

    text = section(body, "Écrans")
    if text is None:
        out.append("section `## Écrans` absente")
        text = ""
    rows = table(text, 6)
    if not rows:
        out.append("aucun écran listé dans `## Écrans`")
    served: dict[str, set[str]] = {}
    screens: dict[str, set[str]] = {}
    routes: set[str] = set()
    for cells in rows:
        name = plain(cells[0]) or "?"
        space = set(SPACES.findall(cells[5]))
        screens.setdefault(name, set()).update(space)
        routes.add(plain(cells[1]))
        if not cells[1]:
            out.append(f"écran « {name} » sans route")
        if not cells[4]:
            out.append(f"écran « {name} » orphelin — rien n'y mène (« Accès depuis » vide)")
        if not space:
            out.append(f"écran « {name} » sans espace (front-office / back-office)")
        for t in re.findall(r"\]\(([^)\s]*cdc/[^)\s]+\.md)\)", cells[3]):
            served.setdefault(Path(t).stem, set()).update(space)

    exigences = stable_exigences(kb)
    named = {sp for _, f, _ in exigences for sp in SPACES.findall(field(f, "espace"))}
    for needed in sorted(named or {"front-office", "back-office"}):
        if rows and needed not in set(SPACES.findall(text)):
            out.append(f"aucun écran {needed} — des exigences le demandent")
    for slug, f, _ in exigences:
        if re.search(r"^tags:.*\bnfr\b", f, re.M) or re.search(r"^\s*-\s*nfr\s*$", f, re.M):
            continue
        if "hors-application" in field(f, "espace"):  # a job, a script, a procedure: no screen to draw
            continue
        wanted = set(SPACES.findall(field(f, "espace")))
        if not wanted:
            out.append(f"exigence `{slug}` sans `espace` (front-office / back-office) — à préciser par le PO")
        if slug not in served:
            out.append(f"exigence `{slug}` servie par aucun écran")
        else:
            for sp in sorted(wanted - served[slug]):
                out.append(f"exigence `{slug}` sans écran {sp}")

    out += back_office_gaps(body, kb, screens)
    out += dashboard_gaps(body, exigences, screens, routes)

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
    if kb.resolve().parent.name == ".hosa":  # the project's CSS carries the identity's tokens, unedited
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import atelier
        out += atelier.ecarts(kb)
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
