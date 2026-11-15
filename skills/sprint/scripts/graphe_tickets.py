#!/usr/bin/env python3
"""The tickets' dependency graph (`depends_on`), computed for planning — a sprint is a computation, not a guess.

  python graphe_tickets.py <kb> pret [--json]
      The ready frontier: `todo` tickets in no sprint, complete (`ticket_check`), every dependency done.
  python graphe_tickets.py <kb> chemin <ticket> [--json]
      Everything <ticket> still waits for, itself included, in build order, with its points and its gaps.
  python graphe_tickets.py <kb> composer [--objectif <ticket>] [--plafond N] [--demo N] [--sprint <slug>]
                                         [--tolerance PCT] [--exact] [--remplir] [--json]
      A sprint: the whole path to the objective (default: the first ticket in priority order whose path can be
      built), within N tickets (default 20) and N demo tests (default 15, at least one per ticket with a screen).
      A path at most `--tolerance` % over a bound (default 5, at least one more) is taken whole: no round trip
      to the user for one ticket. Further over → milestones: whole sub-paths of it, the longest first, that fit.
      The objective goes further on its own way: the furthest ticket waiting for it whose whole path still fits
      (`--exact` keeps it as given). `--remplir` adds ready tickets (`hors objectif`) up to the bounds. `--sprint <slug>`: recompose that sprint,
      its tickets free again. The incomplete tickets come back as `ecartes`, with their gaps. Exit 1 when the
      objective can't be reached (a ticket of its path incomplete, missing or in another sprint).

Rieki sprint-3: the planner walked the priorities and took a ticket testing « Supprimer » of Résultats, a button
many sprints away. Stdlib only.
"""
from __future__ import annotations

import argparse
import functools
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

PLAFOND, DEMO = 20, 15
TOLERANCE = 5  # % over the bounds the whole path to the objective may go: no round trip for one ticket


@functools.cache
def ticket_check():
    path = Path(__file__).resolve().parents[2] / "backlog" / "scripts" / "ticket_check.py"
    spec = importlib.util.spec_from_file_location("ticket_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def points(value: str) -> int:
    """Points as `backlog` writes them; an older S/M/L counts 1/2/3, none 2 (`sprint-planner`)."""
    return {"S": 1, "M": 2, "L": 3}.get(value, int(value) if value.isdigit() else 2)


def has_screen(body: str) -> bool:
    """A ticket the user plays at the demo: its interface placement names a screen (`Écran / route`, not `aucun`)."""
    tc = ticket_check()
    m = re.search(r"\*\*Écran / route\*\*\s*:\s*(.*)", tc.section(body, "## Placement interface (UX/UI)") or "")
    return bool(m) and not m[1].strip().lower().startswith(("aucun", "non applicable", "—"))


def load(kb: Path, recompose: str | None = None) -> dict[str, dict]:
    """Every ticket; those of the sprint `recompose` are free again (loop `qa-plan` → `sprint`)."""
    tc, out = ticket_check(), {}
    for f in sorted((kb / "tickets").glob("*.md")):
        front, body = tc.split(f.read_text(encoding="utf-8"))
        if tc.field(front, "type") != "Ticket":
            continue
        state = tc.field(front, "state") or "todo"
        out[f.stem] = {
            "slug": f.stem, "title": (tc.field(front, "title") or f.stem).strip("'\""), "state": state,
            "sprint": None if tc.field(front, "sprint") in (None, "", recompose) else tc.field(front, "sprint"), "priority": tc.rank(front), "points": points(tc.field(front, "estimate")),
            "depends_on": tc.depends_on(front), "ecran": has_screen(body),
            "manques": [] if state == "done" else [g for g in tc.gaps(f) if not g.startswith("(info)")]}
    return out


def order_key(t: dict):
    return (t["priority"] is None, t["priority"] or 0, t["slug"])


def build_order(graph: dict[str, dict], slugs: set[str]) -> list[str]:
    """Topological order of `slugs`, each after its dependencies, the higher priority first among the free ones."""
    left, out = set(slugs), []
    while left:
        free = [s for s in left if not set(graph[s]["depends_on"]) & left]
        if not free:  # a cycle: ticket_check names it; keep the rest in priority order
            free = list(left)
        nxt = min(free, key=lambda s: order_key(graph[s]))
        out.append(nxt)
        left.remove(nxt)
    return out


def path_to(graph: dict[str, dict], slug: str, apercu: bool = False) -> tuple[list[str], list[str]]:
    """(the tickets still to build for `slug`, in build order; the dependencies no ticket file holds).
    `apercu` (the dashboard's preview): a dependency in a sprint already composed counts as brought by it. A real
    composition never assumes it: the sprint's worktree starts from `main`, without that code (`done sprint`)."""
    seen, missing, todo = set(), [], [slug]
    while todo:
        s = todo.pop()
        if s in seen:
            continue
        if s not in graph:
            missing.append(s)
            continue
        if graph[s]["state"] == "done" or (apercu and s != slug and graph[s]["sprint"]):
            continue
        seen.add(s)
        todo += graph[s]["depends_on"]
    return build_order(graph, seen), sorted(set(missing))


def eligible(t: dict) -> bool:
    return t["state"] == "todo" and not t["sprint"] and not t["manques"]


def ready(graph: dict[str, dict]) -> list[str]:
    return sorted((s for s, t in graph.items() if eligible(t)
                   and all(graph.get(d, {}).get("state") == "done" for d in t["depends_on"])),
                  key=lambda s: order_key(graph[s]))


def obstacles(graph: dict[str, dict], chain: list[str], missing: list[str]) -> list[str]:
    out = [f"`{m}` : ticket introuvable (cité dans un `depends_on`)" for m in missing]
    for s in chain:
        t = graph[s]
        if t["state"] != "todo":
            out.append(f"`{s}` : état `{t['state']}`")
        elif t["sprint"]:
            out.append(f"`{s}` : déjà dans le sprint `{t['sprint']}`")
        elif t["manques"]:
            out.append(f"`{s}` : incomplet → `/backlog {s}` — " + " ; ".join(t["manques"]))
    return out


def demo_cost(graph: dict[str, dict], slugs) -> int:
    return sum(1 for s in slugs if graph[s]["ecran"])


def fits(graph: dict[str, dict], chain: list[str], plafond: int, demo: int) -> bool:
    return len(chain) <= plafond and demo_cost(graph, chain) <= demo


def with_tolerance(bound: int, tolerance: int) -> int:
    """A bound widened by `tolerance` %, at least one more as soon as the tolerance isn't 0: 20 → 21, 15 → 16."""
    return bound + (math.ceil(bound * tolerance / 100) if tolerance > 0 else 0)


def further(graph: dict[str, dict], objectif: str, plafond: int, demo: int, tolerance: int, apercu: bool) -> str:
    """The furthest ticket on the way past `objectif` — one that waits for it, directly or not — whose whole path
    can be built and fits the bounds (tolerance included): the longest such path, the higher priority on a tie.
    rieki sprint-3: « importer un fichier de ventes » gave 9 tickets; « lancer un run », 21 tickets on, fitted."""
    best, best_len = objectif, None
    cap, dmax = with_tolerance(plafond, tolerance), with_tolerance(demo, tolerance)
    for s in sorted(graph, key=lambda x: order_key(graph[x])):
        t = graph[s]
        if s == objectif or t["state"] != "todo" or t["sprint"] or t["manques"]:
            continue
        chain, missing = path_to(graph, s, apercu)
        if objectif not in chain or missing or obstacles(graph, chain, missing) or not fits(graph, chain, cap, dmax):
            continue
        if best_len is None or len(chain) > best_len:
            best, best_len = s, len(chain)
    return best


def compose(graph: dict[str, dict], objectif: str | None, plafond: int, demo: int,
            remplir: bool = False, apercu: bool = False, tolerance: int = TOLERANCE, exact: bool = False) -> dict:
    """The sprint toward `objectif`: its whole path when it fits the bounds; otherwise the milestone — the ticket of
    that path whose own whole path is the longest that fits, never a cut that leaves half-built branches. `remplir`
    adds ready tickets `hors objectif` up to the bounds; by default the sprint is the objective's path alone.
    The objective goes further on its own way while the path still fits (`further`); `exact` keeps it as given."""
    todo = sorted((s for s, t in graph.items() if t["state"] == "todo" and not t["sprint"]), key=lambda s: order_key(graph[s]))
    ecartes = [{"slug": s, "manques": graph[s]["manques"]} for s in todo if graph[s]["manques"]]
    base = {"objectif": objectif, "tickets": [], "jalon": None, "ecartes": ecartes, "plafond": plafond, "demo_max": demo}
    if objectif is None:  # the first ticket in priority order whose whole path can be built now
        objectif = next((s for s in todo if not obstacles(graph, *path_to(graph, s, apercu))), None)
        if objectif is None:
            return dict(base, obstacles=["aucun ticket `todo` hors sprint dont le chemin est complet (`graphe_tickets pret`)"])
    if objectif not in graph:
        return dict(base, objectif=objectif, obstacles=[f"`{objectif}` : ticket introuvable"])
    demande, etendu = objectif, False
    chain, missing = path_to(graph, objectif, apercu)
    if not exact and not obstacles(graph, chain, missing):
        objectif = further(graph, objectif, plafond, demo, tolerance, apercu)
        etendu = objectif != demande
        chain, missing = path_to(graph, objectif, apercu)
    blocked = obstacles(graph, chain, missing)
    picked, jalon, tolere = [], None, False
    if not blocked:
        if fits(graph, chain, plafond, demo):
            picked = chain
        elif fits(graph, chain, with_tolerance(plafond, tolerance), with_tolerance(demo, tolerance)):
            picked, tolere = chain, True  # a little over: the whole objective, never a sprint left one ticket short
        else:  # milestones: whole sub-paths, the longest first, joined while they fit — never half a branch
            subs = sorted(((s, path_to(graph, s, apercu)[0]) for s in chain if s != objectif),
                          key=lambda x: (-len(x[1]), order_key(graph[x[0]])))
            taken, jalons = set(), []
            for s, sub in subs:
                if s in taken:
                    continue
                union = taken | set(sub)
                if fits(graph, list(union), plafond, demo):
                    taken, jalons = union, jalons + [s]
            picked = [s for s in chain if s in taken]
            jalon = [s for s in jalons if not any(s in path_to(graph, j, apercu)[0] and s != j for j in jalons)] or None
    rows = [dict(graph[s], objectif=True) for s in picked]
    if remplir and picked:  # ready tickets, each one's dependencies done or taken
        taken = set(picked)
        while len(rows) < plafond:
            free = [s for s in todo if s not in taken and eligible(graph[s])
                    and all(d in taken or graph.get(d, {}).get("state") == "done"
                            or (apercu and graph.get(d, {}).get("sprint")) for d in graph[s]["depends_on"])
                    and demo_cost(graph, list(taken) + [s]) <= demo]
            if not free:
                break
            taken.add(free[0])
            rows.append(dict(graph[free[0]], objectif=False))
    return dict(base, objectif=objectif, chemin=len(chain), chemin_points=sum(graph[s]["points"] for s in chain), chemin_demo=demo_cost(graph, chain),
                atteint=bool(picked) and picked[-1] == objectif and not jalon, jalon=jalon, obstacles=blocked,
                tickets=rows, points=sum(r["points"] for r in rows), demo=demo_cost(graph, [r["slug"] for r in rows]),
                reste=len(chain) - len(picked), tolere=tolere, tolerance=tolerance,
                demande=demande, etendu=etendu)


def report(c: dict) -> str:
    lines = []
    if c["obstacles"]:
        lines.append(f"Objectif `{c['objectif']}` inatteignable :")
        lines += [f"- {o}" for o in c["obstacles"]]
        return "\n".join(lines)
    if c.get("etendu"):
        lines.append(f"Objectif demandé `{c['demande']}` : son chemin laisse de la place. Objectif prolongé sur le même "
                     f"chemin jusqu'à `{c['objectif']}`, le plus loin qui tient (`--exact` pour garder le premier).")
    lines.append(f"Objectif `{c['objectif']}` : chemin de {c['chemin']} ticket(s), {c['chemin_points']} point(s), "
                 f"{c['chemin_demo']} test(s) de démo.")
    if c["jalon"]:
        lines.append(f"Trop loin pour un sprint (plafond {c['plafond']} tickets, {c['demo_max']} tests de démo) : "
                     f"jalon(s) {', '.join(f'`{j}`' for j in c['jalon'])}, chacun avec son chemin entier ; "
                     f"il restera {c['reste']} ticket(s) vers l'objectif.")
    elif c["tolere"]:
        lines.append(f"Au-dessus des bornes (plafond {c['plafond']} tickets, {c['demo_max']} tests de démo) de "
                     f"{c['tolerance']} % au plus : l'objectif entier est pris.")
    elif c["obstacles"] is not None and not c["tickets"]:
        lines.append(f"Aucun jalon ne tient dans les bornes (plafond {c['plafond']}, {c['demo_max']} tests de démo).")
    lines.append(f"Sprint : {len(c['tickets'])} ticket(s), {c['points']} point(s), {c['demo']} test(s) de démo, "
                 "dans l'ordre de construction :")
    lines += [f"{i}. `{t['slug']}` — {t['points']} pt{'' if t['objectif'] else ' (hors objectif)'}"
              for i, t in enumerate(c["tickets"], 1)]
    if c["ecartes"]:
        lines.append("Écartés, incomplets (`/backlog <ticket>`) :")
        lines += [f"- `{e['slug']}` — " + " ; ".join(e["manques"]) for e in c["ecartes"]]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Graphe des dépendances entre tickets, pour planifier un sprint.")
    ap.add_argument("kb")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pret").add_argument("--json", action="store_true")
    ch = sub.add_parser("chemin")
    ch.add_argument("ticket")
    ch.add_argument("--json", action="store_true")
    co = sub.add_parser("composer")
    co.add_argument("--objectif")
    co.add_argument("--plafond", type=int, default=PLAFOND)
    co.add_argument("--demo", type=int, default=DEMO)
    co.add_argument("--tolerance", type=int, default=TOLERANCE, help="%% au-dessus des bornes accepté pour l'objectif entier")
    co.add_argument("--sprint", help="recomposer ce sprint : ses tickets redeviennent libres")
    co.add_argument("--exact", action="store_true", help="garder l'objectif donné, sans le prolonger")
    co.add_argument("--remplir", action="store_true", help="ajouter des tickets prêts hors objectif jusqu'aux bornes")
    co.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    kb = Path(a.kb)
    if not (kb / "tickets").is_dir():
        print(f"pas de dossier `tickets/` dans {kb}", file=sys.stderr)
        return 2
    graph = load(kb, getattr(a, "sprint", None))
    if a.cmd == "pret":
        rows = [graph[s] for s in ready(graph)]
        print(json.dumps(rows, ensure_ascii=False) if a.json else
              "\n".join(f"- `{t['slug']}` — priorité {t['priority']}, {t['points']} pt" for t in rows) or "Aucun ticket prêt.")
        return 0
    if a.cmd == "chemin":
        if a.ticket not in graph:
            print(f"`{a.ticket}` : ticket introuvable", file=sys.stderr)
            return 2
        chain, missing = path_to(graph, a.ticket)
        blocked = obstacles(graph, chain, missing)
        if a.json:
            print(json.dumps({"tickets": [graph[s] for s in chain], "obstacles": blocked}, ensure_ascii=False))
        else:
            print(f"`{a.ticket}` : {len(chain)} ticket(s) à construire, {sum(graph[s]['points'] for s in chain)} point(s).")
            print("\n".join(f"{i}. `{s}`{' — incomplet' if graph[s]['manques'] else ''}" for i, s in enumerate(chain, 1)))
            print("\n".join(f"- {o}" for o in blocked))
        return 0
    c = compose(graph, a.objectif, a.plafond, a.demo, a.remplir, tolerance=a.tolerance, exact=a.exact)
    print(json.dumps(c, ensure_ascii=False) if a.json else report(c))
    return 1 if c["obstacles"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
