#!/usr/bin/env python3
"""The tickets' dependency graph (`depends_on`), computed for planning — a sprint is a computation, not a guess.

  python graphe_tickets.py <kb> pret [--json]
      The ready frontier: `todo` tickets in no sprint, complete (`ticket_check`), every dependency done.
  python graphe_tickets.py <kb> chemin <ticket> [--json]
      Everything <ticket> still waits for, itself included, in build order, with its points and its gaps.
  python graphe_tickets.py <kb> feuille [--jalons a,b,…] [--plafond N] [--demo N] [--tolerance PCT]
                                        [--sprint <slug>] [--ecrire] [--json]
      Every sprint to come: the milestones' paths in their order (list scheduling, whole sub-paths), then the
      complete tickets no milestone needs, by priority. `--ecrire` writes kb/project/feuille-de-route.md, its
      `## Jalons` kept as the user validated them. Exit 1 when a milestone is blocked (an incomplete ticket).
  python graphe_tickets.py <kb> composer [--objectif <ticket>] [--plafond N] [--demo N] [--sprint <slug>]
                                         [--tolerance PCT] [--prolonger] [--remplir] [--json]
      A sprint: the whole path to the objective (default: the first ticket in priority order whose path can be
      built), within N tickets (default 20) and N demo tests (default 15, at least one per ticket with a screen).
      A path at most `--tolerance` % over a bound (default 5, at least one more) is taken whole: no round trip
      to the user for one ticket. Further over → milestones: whole sub-paths of it, the longest first, that fit.
      `--prolonger` takes the objective further on its own way: the furthest ticket waiting for it whose whole
      path still fits (rieki: it made a sprint bigger than its objective; off by default). `--remplir` adds ready tickets (`hors objectif`) up to the bounds. `--sprint <slug>`: recompose that sprint,
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
            remplir: bool = False, apercu: bool = False, tolerance: int = TOLERANCE, prolonger: bool = False) -> dict:
    """The sprint toward `objectif`: its whole path when it fits the bounds; otherwise the milestone — the ticket of
    that path whose own whole path is the longest that fits, never a cut that leaves half-built branches. `remplir`
    adds ready tickets `hors objectif` up to the bounds; by default the sprint is the objective's path alone.
    `prolonger` takes the objective further on its own way while the path still fits (`further`); by default it
    stays as given: the sprint's size comes from the roadmap's milestones, not from filling the bounds."""
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
    if prolonger and not obstacles(graph, chain, missing):
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


def roadmap(graph: dict[str, dict], jalons: list[str], plafond: int = PLAFOND, demo: int = DEMO,
            tolerance: int = TOLERANCE) -> dict:
    """Every sprint to come, computed (list scheduling on the dependency graph):
    1. each milestone in its order brings its whole path — what it still waits for — into the open sprint while it
       fits the bounds (tolerance included); otherwise the sprint closes and the path starts the next one; a path
       over a whole sprint is cut at whole sub-paths (never half a branch);
    2. then the complete tickets no milestone needs, in priority order, each once its dependencies are placed;
    3. an incomplete ticket is placed nowhere: it waits under `a_completer`, and so does every milestone whose path
       holds one. A ticket already in a composed sprint counts as delivered before the roadmap's first sprint.
    Each ticket lands once; each sprint lists its tickets after their dependencies."""
    cap, dmax = with_tolerance(plafond, tolerance), with_tolerance(demo, tolerance)
    placed: set[str] = set()
    sprints: list[dict] = []
    bloques: list[dict] = []

    def open_sprint(kind: str) -> dict:
        sprints.append({"tickets": [], "jalons": [], "nature": kind})
        return sprints[-1]

    def todo_path(s: str) -> list[str]:
        return [x for x in path_to(graph, s, apercu=True)[0] if x not in placed]

    cur = None
    for m in jalons:
        if m not in graph:
            bloques.append({"jalon": m, "obstacles": [f"`{m}` : ticket introuvable"]})
            break
        if graph[m]["state"] == "done" or graph[m]["sprint"] or m in placed:
            continue  # delivered, being delivered, or brought by an earlier milestone
        chain, missing = path_to(graph, m, apercu=True)
        blocked = obstacles(graph, [s for s in chain if s not in placed], missing)
        if blocked:  # the roadmap stops there: no sprint past a milestone that can't be built (rieki: 4 blocked
            # milestones gave a first sprint of 20 tickets « hors parcours », the bag again)
            bloques.append({"jalon": m, "obstacles": blocked})
            bloques += [{"jalon": n, "obstacles": [f"après le jalon bloqué `{m}`"]} for n in jalons[jalons.index(m) + 1:]]
            break
        chain = [s for s in chain if s not in placed]
        while chain:
            if cur is not None and fits(graph, cur["tickets"] + chain, cap, dmax):
                cur["tickets"] += chain
                placed |= set(chain)
                cur["jalons"].append(m)
                chain = []
            elif cur is not None and cur["tickets"]:
                cur = None  # full: the path starts the next sprint
            else:
                cur = cur or open_sprint("parcours")
                if fits(graph, chain, cap, dmax):
                    continue  # taken whole at the next turn
                taken: set[str] = set()  # whole sub-paths, the longest first, while they fit the strict bounds
                for s, sub in sorted(((s, todo_path(s)) for s in chain if s != m),
                                     key=lambda x: (-len(x[1]), order_key(graph[x[0]]))):
                    if s not in taken and fits(graph, list(taken | set(sub)), plafond, demo):
                        taken |= set(sub)
                if not taken:  # one ticket alone over the bounds: it still has to be built
                    taken = {chain[0]}
                part = [s for s in chain if s in taken]
                cur["tickets"] += part
                placed |= taken
                chain = [s for s in chain if s not in taken]
                cur = None
    rest = [] if bloques else sorted((s for s, t in graph.items() if eligible(t) and s not in placed),
                                     key=lambda s: order_key(graph[s]))
    cur = None
    while rest:
        free = [s for s in rest if all(graph.get(d, {}).get("state") == "done" or graph.get(d, {}).get("sprint")
                                       or d in placed for d in graph[s]["depends_on"])]
        if not free:
            break
        s = free[0]
        if cur is None or not fits(graph, cur["tickets"] + [s], plafond, demo):
            cur = open_sprint("hors parcours")
        cur["tickets"].append(s)
        placed.add(s)
        rest.remove(s)
    left = [s for s, t in sorted(graph.items(), key=lambda x: order_key(x[1]))
            if t["state"] == "todo" and not t["sprint"] and s not in placed]
    a_completer = [{"slug": s, "manques": graph[s]["manques"]} for s in left if graph[s]["manques"]]
    en_attente = [s for s in left if not graph[s]["manques"]]  # complete, behind an incomplete one
    for sp in sprints:
        sp["points"] = sum(graph[s]["points"] for s in sp["tickets"])
        sp["demo"] = demo_cost(graph, sp["tickets"])
    return {"sprints": sprints, "bloques": bloques, "a_completer": a_completer, "en_attente": en_attente,
            "plafond": plafond, "demo_max": demo, "tolerance": tolerance}


BORNES = re.compile(r"(\d+) tickets et (\d+) tests de démo par sprint, (\d+) %")


def read_bornes(kb: Path) -> tuple[int, int, int]:
    """The bounds validated with the milestones (`## Bornes`), the defaults otherwise."""
    f = kb / "project" / "feuille-de-route.md"
    m = BORNES.search(f.read_text(encoding="utf-8")) if f.is_file() else None
    return (int(m[1]), int(m[2]), int(m[3])) if m else (PLAFOND, DEMO, TOLERANCE)


def read_jalons(kb: Path) -> list[str] | None:
    """The milestones the user validated, in order: `## Jalons` of `kb/project/feuille-de-route.md`."""
    f = kb / "project" / "feuille-de-route.md"
    if not f.is_file():
        return None
    tc = ticket_check()
    return re.findall(r"\]\((?:\.\./tickets/)?([\w-]+)\.md\)", tc.section(tc.split(f.read_text(encoding="utf-8"))[1], "## Jalons") or "")


def write_roadmap(kb: Path, graph: dict[str, dict], r: dict, at: str, jalons_list: list[str] | None = None) -> Path:
    """Rewrites the computed part of the roadmap. `## Jalons` stays as the user validated it, or is written from
    `jalons_list` (the milestones the user just validated)."""
    f = kb / "project" / "feuille-de-route.md"
    tc = ticket_check()
    link = lambda s: f"[{graph[s]['title']}](../tickets/{s}.md) (`{s}`)" if s in graph else f"`{s}`"  # noqa: E731
    if jalons_list is not None:
        jalons = "\n".join(f"- {link(j)}" for j in jalons_list)
    else:
        jalons = tc.section(tc.split(f.read_text(encoding="utf-8"))[1], "## Jalons") or ""
    f.parent.mkdir(parents=True, exist_ok=True)
    out = ["---", "type: Feuille de route", "title: Feuille de route",
           'description: "Les jalons du parcours, validés une fois, et les sprints calculés depuis le graphe des tickets"',
           "tags: [pilotage]", f"generated: {{ by: process:hosa-graphe-tickets, at: {at} }}", "---",
           "## Jalons", jalons.strip(), "",
           "## Bornes", f"- {r['plafond']} tickets et {r['demo_max']} tests de démo par sprint, {r['tolerance']} % de plus "
           "pour garder un jalon entier.", "", "## Sprints"]
    for i, sp in enumerate(r["sprints"], 1):
        head = ", ".join(f"`{j}`" for j in sp["jalons"]) or ("hors parcours" if sp["nature"] == "hors parcours" else "partie d'un jalon")
        out += [f"### Sprint {i} — {head}", f"{len(sp['tickets'])} tickets, {sp['points']} points, {sp['demo']} tests de démo.", ""]
        out += [f"- {link(s)}" for s in sp["tickets"]] + [""]
    if r["bloques"]:
        out += ["## Jalons bloqués"] + [f"- `{b['jalon']}` — " + " ; ".join(b["obstacles"]) for b in r["bloques"]] + [""]
    if r["a_completer"]:
        out += ["## À compléter"] + [f"- {link(a['slug'])} — " + " ; ".join(a["manques"]) for a in r["a_completer"]] + [""]
    if r["en_attente"]:
        out += ["## En attente d'un ticket à compléter"] + [f"- {link(s)}" for s in r["en_attente"]] + [""]
    f.write_text("\n".join(out), encoding="utf-8")
    return f


def roadmap_report(graph: dict[str, dict], r: dict) -> str:
    lines = [f"{len(r['sprints'])} sprint(s) à venir (bornes : {r['plafond']} tickets, {r['demo_max']} tests de démo, "
             f"+{r['tolerance']} % pour un jalon entier) :"]
    for i, sp in enumerate(r["sprints"], 1):
        head = ", ".join(f"`{j}`" for j in sp["jalons"]) or sp["nature"]
        lines.append(f"- Sprint {i} — {head} : {len(sp['tickets'])} tickets, {sp['points']} points, {sp['demo']} tests de démo")
    lines += [f"Jalon bloqué `{b['jalon']}` : " + " ; ".join(b["obstacles"]) for b in r["bloques"]]
    if r["a_completer"]:
        lines.append(f"À compléter (`/backlog <ticket>`) : {len(r['a_completer'])} ticket(s) — "
                     + ", ".join(f"`{a['slug']}`" for a in r["a_completer"]))
    if r["en_attente"]:
        lines.append(f"En attente d'un ticket à compléter : {len(r['en_attente'])} ticket(s).")
    return "\n".join(lines)


def report(c: dict) -> str:
    lines = []
    if c["obstacles"]:
        lines.append(f"Objectif `{c['objectif']}` inatteignable :")
        lines += [f"- {o}" for o in c["obstacles"]]
        return "\n".join(lines)
    if c.get("etendu"):
        lines.append(f"Objectif demandé `{c['demande']}` : son chemin laisse de la place. Objectif prolongé sur le même "
                     f"chemin jusqu'à `{c['objectif']}`, le plus loin qui tient (`--prolonger`).")
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
    co.add_argument("--prolonger", action="store_true", help="prolonger l'objectif sur son chemin tant qu'il tient")
    co.add_argument("--remplir", action="store_true", help="ajouter des tickets prêts hors objectif jusqu'aux bornes")
    co.add_argument("--json", action="store_true")
    fe = sub.add_parser("feuille")
    fe.add_argument("--jalons", help="jalons séparés par des virgules (sinon ceux de kb/project/feuille-de-route.md)")
    fe.add_argument("--plafond", type=int, help=f"tickets par sprint (sinon `## Bornes`, sinon {PLAFOND})")
    fe.add_argument("--demo", type=int, help=f"tests de démo par sprint (sinon `## Bornes`, sinon {DEMO})")
    fe.add_argument("--tolerance", type=int, help=f"%% pour garder un jalon entier (sinon `## Bornes`, sinon {TOLERANCE})")
    fe.add_argument("--sprint", help="recomposer ce sprint : ses tickets redeviennent libres")
    fe.add_argument("--ecrire", action="store_true", help="écrire kb/project/feuille-de-route.md")
    fe.add_argument("--json", action="store_true")
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
    if a.cmd == "feuille":
        jalons = [j.strip() for j in a.jalons.split(",") if j.strip()] if a.jalons else read_jalons(kb)
        if not jalons:
            print("pas de jalons : `--jalons a,b,…` ou `## Jalons` de kb/project/feuille-de-route.md", file=sys.stderr)
            return 2
        bp, bd, bt = read_bornes(kb)
        r = roadmap(graph, jalons, a.plafond or bp, a.demo or bd, bt if a.tolerance is None else a.tolerance)
        if a.ecrire:
            from datetime import datetime, timezone
            at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            print(f"écrit : {write_roadmap(kb, graph, r, at, jalons if a.jalons else None)}", file=sys.stderr)
        print(json.dumps(r, ensure_ascii=False) if a.json else roadmap_report(graph, r))
        return 1 if r["bloques"] else 0
    c = compose(graph, a.objectif, a.plafond, a.demo, a.remplir, tolerance=a.tolerance, prolonger=a.prolonger)
    print(json.dumps(c, ensure_ascii=False) if a.json else report(c))
    return 1 if c["obstacles"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
