#!/usr/bin/env python3
"""Where do the tokens go? Reads Claude Code's local transcripts and reports
token use per agent, per skill and per model, plus the files read the most.

  usage_report.py [project-dir] [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--session ID] [--top N]
  usage_report.py [project-dir] --sprint SLUG [--write]

To measure a change (a model switch), run it on the period before and after:
`## Résultat` gives the cost, the tickets delivered and the review verdicts.
`--sprint` measures one sprint (from its creation to its merge) against the
thresholds below and the earlier sprints, and proposes adjustments; `--write`
records it as `## Mesures` in `kb/sprints/<slug>.md` (`bilan-sprint`).

project-dir: the managed project's root (default: current directory). Its
transcripts live in ~/.claude/projects/<path with / replaced by ->/ (main
sessions as <id>.jsonl, subagents as <id>/subagents/*.jsonl or as sidechain
lines). Read-only, stdlib only, no model involved.

Main-session turns are attributed to the last skill invoked since the user's
last message ("session principale" otherwise) — an approximation, said so in
the output. Subagent turns are attributed to their agent type, exactly.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

FIELDS = ("calls", "input", "cache_write", "cache_read", "output", "thinking", "usd")
# $ per million tokens: input, output, cache read; a cache write is 1.25 × input. First match wins.
# ponytail: list prices of 2026-10, 5-min cache writes, Haiku 5.5's dearer >100k-prompt tier ignored
PRICES = [("fable", 10, 50, 0.25), ("opus-5-5", 4, 20, 0.20), ("opus", 5, 25, 0.50),
          ("sonnet-5", 2, 10, 0.20), ("sonnet", 3, 15, 0.30), ("haiku-5-5", 0.10, 0.50, 0.01), ("haiku", 1, 5, 0.10)]
VERDICT = re.compile(r"\b(PASS-WITH-NOTES|PASS|FAIL)\b")
# Thresholds of `--sprint`. ponytail: set from the pilot and hosa-ui (2026-10), recalibrate on real sprints.
REWRITE = 50_000        # cache tokens written by one call: the context was rewritten whole
MAIN_CTX_MAX = 150_000  # main session context: one session per stage wasn't kept
CAPS = {"hosa-ux-designer": 50}  # tool calls per agent pass — same values as hooks/budget.js
CAP = 150
COST_RISE = 1.5         # cost per ticket vs the median of the earlier sprints


def context(usage: dict) -> int:
    return sum(usage.get(k, 0) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def images(entry: dict) -> int:
    return sum(1 for b in blocks(entry) if b.get("type") == "tool_result" and isinstance(b.get("content"), list)
               for c in b["content"] if isinstance(c, dict) and c.get("type") == "image")


def usd(model: str, usage: dict) -> float:
    price = next((p for p in PRICES if p[0] in model), None)
    if not price:
        return 0.0
    _, inp, out, read = price
    return ((usage.get("input_tokens", 0) or 0) * inp + (usage.get("cache_creation_input_tokens", 0) or 0) * inp * 1.25
            + (usage.get("cache_read_input_tokens", 0) or 0) * read + (usage.get("output_tokens", 0) or 0) * out) / 1e6


def outside(entry: dict, since: str | None, until: str | None) -> bool:
    day = str(entry.get("timestamp", ""))[:10]
    return bool(since and day < since or until and day > until)


def project_dir(root: Path) -> Path:
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(root.resolve()))
    return Path.home() / ".claude" / "projects" / slug


def lines(path: Path):
    with path.open(encoding="utf-8", errors="replace") as f:
        for raw in f:
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                continue


def blocks(entry: dict) -> list:
    content = (entry.get("message") or {}).get("content")
    return content if isinstance(content, list) else []


def usage_once(entry: dict, seen: set) -> dict:
    """The entry's usage, or {} if its message was already counted: Claude Code
    writes one API response over several lines, each repeating the same usage."""
    msg = entry.get("message") or {}
    mid = msg.get("id")
    if mid in seen:
        return {}
    if mid:
        seen.add(mid)
    return msg.get("usage") or {}


def add(table: dict, key: str, usage: dict, model: str) -> None:
    row = table[key]
    row["calls"] += 1
    row["usd"] += usd(model, usage)
    row["input"] += usage.get("input_tokens", 0) or 0
    row["cache_write"] += usage.get("cache_creation_input_tokens", 0) or 0
    row["cache_read"] += usage.get("cache_read_input_tokens", 0) or 0
    row["output"] += usage.get("output_tokens", 0) or 0
    row["thinking"] += ((usage.get("output_tokens_details") or {}).get("thinking_tokens", 0)) or 0


def scan(base: Path, since: str | None, session: str | None, until: str | None = None):
    by_actor: dict = defaultdict(lambda: dict.fromkeys(FIELDS, 0))
    by_model: dict = defaultdict(lambda: dict.fromkeys(FIELDS, 0))
    reads: dict = defaultdict(lambda: [0, 0])          # file -> [times, chars]
    agent_types: dict[str, str] = {}                    # tool_use id -> subagent type
    agent_of: dict[str, str] = {}                       # agentId -> subagent type
    pending_read: dict[str, tuple[str, str]] = {}       # tool_use id -> (actor, file)
    sidechain: list[tuple[Path, list]] = []
    seen: set[str] = set()                              # message ids already counted
    verdicts: dict = defaultdict(int)                   # hosa-reviewer final verdict -> runs
    # main session's largest context and screenshots; whole-context rewrites; each agent pass
    stats = {"main_ctx": 0, "main_images": 0, "rewrites": [0, 0], "passes": {}}

    def measure(usage: dict) -> int:
        if (usage.get("cache_creation_input_tokens", 0) or 0) >= REWRITE:
            stats["rewrites"][0] += 1
            stats["rewrites"][1] += usage["cache_creation_input_tokens"]
        return context(usage)

    files = sorted(base.rglob("*.jsonl")) if base.is_dir() else []
    for path in files:
        entries = list(lines(path))
        if session and not any(e.get("sessionId") == session for e in entries[:50]):
            continue
        if any(e.get("isSidechain") for e in entries[:20]) or "subagents" in path.parts:
            sidechain.append((path, entries))
            continue
        skill = None
        for e in entries:
            if outside(e, since, until):
                continue
            if e.get("isSidechain"):
                sidechain.append((path, [e]))
                continue
            if e.get("type") == "user":
                content = (e.get("message") or {}).get("content")
                if isinstance(content, str) or not any(b.get("type") == "tool_result" for b in blocks(e)):
                    skill = None
                result = e.get("toolUseResult")
                if isinstance(result, dict) and result.get("agentId"):
                    for b in blocks(e):
                        if b.get("type") == "tool_result" and b.get("tool_use_id") in agent_types:
                            agent_of[str(result["agentId"])] = agent_types[b["tool_use_id"]]
                count_reads(e, pending_read, reads)
                stats["main_images"] += images(e)
            elif e.get("type") == "assistant":
                actor = f"skill {skill}" if skill else "session principale"
                usage = usage_once(e, seen)
                if usage:
                    model = (e.get("message") or {}).get("model", "?")
                    add(by_actor, actor, usage, model)
                    add(by_model, model, usage, model)
                    stats["main_ctx"] = max(stats["main_ctx"], measure(usage))
                for b in blocks(e):
                    if b.get("type") != "tool_use":
                        continue
                    inp = b.get("input") or {}
                    if b.get("name") == "Skill" and inp.get("skill"):
                        skill = inp["skill"]
                    elif b.get("name") in ("Agent", "Task") and inp.get("subagent_type"):
                        agent_types[b["id"]] = inp["subagent_type"]
                    elif b.get("name") == "Read" and inp.get("file_path"):
                        pending_read[b["id"]] = (actor, inp["file_path"])

    for path, entries in sidechain:
        agent_id = next((str(e["agentId"]) for e in entries if e.get("agentId")), None) \
            or re.sub(r"^agent-", "", path.stem)
        kind = agent_of.get(agent_id) or meta_type(path) or "agent (type inconnu)"
        actor = f"agent {kind}"
        last_text = None
        run = stats["passes"].setdefault(agent_id, {"kind": kind, "tools": 0, "ctx": 0, "images": 0})
        for e in entries:
            if outside(e, since, until):
                continue
            if e.get("type") == "assistant":
                usage = usage_once(e, seen)
                if usage:
                    model = (e.get("message") or {}).get("model", "?")
                    add(by_actor, actor, usage, model)
                    add(by_model, model, usage, model)
                    run["ctx"] = max(run["ctx"], measure(usage))
                for b in blocks(e):
                    if b.get("type") == "text":
                        last_text = b.get("text", "")
                    if b.get("type") == "tool_use":
                        run["tools"] += 1
                    if b.get("type") == "tool_use" and b.get("name") == "Read" and (b.get("input") or {}).get("file_path"):
                        pending_read[b["id"]] = (actor, b["input"]["file_path"])
            elif e.get("type") == "user":
                count_reads(e, pending_read, reads)
                run["images"] += images(e)
        if kind.endswith("hosa-reviewer") and last_text is not None:
            m = VERDICT.search(last_text)
            verdicts[m.group(1) if m else "sans verdict"] += 1
    stats["passes"] = {k: r for k, r in stats["passes"].items() if r["tools"] or r["ctx"]}  # passes outside the period
    return by_actor, by_model, reads, verdicts, stats


def delivered(project: Path, since: str | None, until: str | None) -> set[str]:
    """Tickets with a commit carrying `Hosa-Ticket: <slug>` (the `develop` gate) in the period."""
    cmd = ["git", "-C", str(project), "log", "--all", "--format=%(trailers:key=Hosa-Ticket,valueonly)"]
    cmd += [f"--since={since} 00:00"] if since else []
    cmd += [f"--until={until} 23:59:59"] if until else []
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return set()
    return {line.strip() for line in (out or "").splitlines() if line.strip()}


def sprint_file(project: Path, slug: str) -> Path:
    return project / ".hosa" / "kb" / "sprints" / f"{slug}.md"


def sprint_period(project: Path, text: str) -> tuple[str | None, str | None, list[str]]:
    """From the sprint's creation day (`generated.at`) to its merge commit's day, and its tickets."""
    tickets = re.findall(r"\(\.\./tickets/([^)]+)\.md\)", text.split("\n## Tickets", 1)[-1].split("\n## ", 1)[0])
    born = re.search(r"^generated:.*?\bat:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
    merge = re.search(r"^merge_commit:\s*([0-9a-fA-F]{7,40})\s*$", text, re.M)  # a SHA only: never a git option
    until = None
    if merge:
        try:
            until = subprocess.run(["git", "-C", str(project), "show", "-s", "--format=%cs", "--end-of-options", merge.group(1)],
                                   capture_output=True, text=True, timeout=10).stdout.strip() or None
        except (OSError, subprocess.SubprocessError):
            pass
    return born and born.group(1), until, tickets


def earlier_costs(project: Path, slug: str) -> list[float]:
    """`Coût par ticket` of the other sprints' `## Mesures`."""
    out = []
    for p in sorted((project / ".hosa" / "kb" / "sprints").glob("*.md")):
        if p.stem != slug:
            m = re.findall(r"^- Coût :.*Coût par ticket : ([\d.]+) \$", p.read_text(encoding="utf-8", errors="replace"), re.M)
            out += [float(m[-1])] if m else []
    return out


def measures(slug, since, until, tickets, sprint_tickets, by_model, verdicts, stats, earlier) -> list[str]:
    """`## Mesures` of a sprint: the figures, then what crossed a threshold, as proposals."""
    total = sum(r["usd"] for r in by_model.values())
    done = len(tickets)
    per = total / done if done else None
    passes = sorted(stats["passes"].values(), key=lambda r: -r["tools"])
    debugger = sum(1 for r in passes if r["kind"].endswith("hosa-debugger"))
    reviews = sum(verdicts.values())
    fails = verdicts.get("FAIL", 0)
    base = sorted(earlier)[len(earlier) // 2] if earlier else None
    out = ["## Mesures", f"{date.today().isoformat()} — `usage_report.py --sprint {slug}`, prix catalogue (estimation)",
           f"- Période : {since or '?'} → {until or 'en cours'}",
           f"- Coût : {total:.2f} $ — tickets livrés : {done}/{len(sprint_tickets)}" + (f" — Coût par ticket : {per:.2f} $" if per else ""),
           f"- Revues : {', '.join(f'{k} {n}' for k, n in sorted(verdicts.items())) or 'aucune'} — passages hosa-debugger : {debugger}",
           f"- Session principale : contexte max {fmt(stats['main_ctx'])} — captures ouvertes : {stats['main_images']}",
           f"- Réécritures complètes du cache (≥ {fmt(REWRITE)}) : {stats['rewrites'][0]} ({fmt(stats['rewrites'][1])})",
           "- Passages d'agent les plus longs : " + (", ".join(f"{r['kind'].split(':')[-1]} {r['tools']} appels ({fmt(r['ctx'])})" for r in passes[:3]) or "aucun"),
           f"- Sprints précédents : " + (f"coût par ticket médian {base:.2f} $ ({len(earlier)} sprint(s))" if base else "aucune mesure"),
           "", "### Propositions"]
    props = []
    if reviews >= 3 and fails / reviews >= 1 / 3 and any("haiku" in m for m in by_model):
        props.append(f"{fails}/{reviews} revues en échec avec des agents sur Haiku : essayer `HOSA_HAIKU=0` au prochain sprint et comparer.")
    if per and base and per > COST_RISE * base:
        props.append(f"Coût par ticket en hausse : {per:.2f} $ contre {base:.2f} $ — regarder les passages les plus longs ci-dessus.")
    if done and debugger * 2 >= done:
        props.append(f"{debugger} passages hosa-debugger pour {done} tickets : les plans du tech-lead ou le développeur ne suffisent pas.")
    if stats["main_ctx"] > MAIN_CTX_MAX:
        props.append(f"Session principale montée à {fmt(stats['main_ctx'])} : une session par étape (`/clear`, puis « reprends »).")
    if stats["main_images"]:
        props.append(f"{stats['main_images']} capture(s) ouverte(s) dans la session principale : donner leur chemin, ne pas les ouvrir.")
    for r in passes:
        cap = CAPS.get(r["kind"].split(":")[-1], CAP)
        if r["tools"] > cap:
            props.append(f"{r['kind'].split(':')[-1]} : un passage de {r['tools']} appels (plafond {cap}) — découper son travail en plusieurs passages.")
    return out + ([f"- {p}" for p in props] or ["- Aucune : rien n'a dépassé les seuils."])


def write_section(path: Path, lines: list[str]) -> None:
    """Replace the file's `## Mesures` section (heading to the next level-2 heading), or append it."""
    text = path.read_text(encoding="utf-8")
    block = "\n".join(lines) + "\n"
    m = re.search(r"^## Mesures\n.*?(?=^## |\Z)", text, re.M | re.S)
    text = text[:m.start()] + block + ("\n" if m.end() < len(text) else "") + text[m.end():] if m else text.rstrip("\n") + "\n\n" + block
    path.write_text(text, encoding="utf-8")


def meta_type(path: Path) -> str | None:
    meta = path.with_suffix(".meta.json")
    try:
        return json.loads(meta.read_text(encoding="utf-8")).get("agentType")
    except (OSError, json.JSONDecodeError, AttributeError):
        return None


def count_reads(entry: dict, pending: dict, reads: dict) -> None:
    for b in blocks(entry):
        if b.get("type") == "tool_result" and b.get("tool_use_id") in pending:
            _, file = pending.pop(b["tool_use_id"])
            content = b.get("content")
            size = len(json.dumps(content, ensure_ascii=False)) if content is not None else 0
            reads[file][0] += 1
            reads[file][1] += size


def fmt(n: int) -> str:
    return f"{n/1_000_000:.2f} M" if n >= 1_000_000 else f"{n/1000:.1f} k" if n >= 1000 else str(n)


def table(title: str, data: dict) -> list[str]:
    total = sum(r["usd"] for r in data.values()) or 1
    out = [f"## {title}", "| | appels | entrée | cache écrit | cache lu | sortie (dont réflexion) | coût | part |", "|---|---|---|---|---|---|---|---|"]
    for key, r in sorted(data.items(), key=lambda kv: -kv[1]["usd"]):
        out.append(f"| {key} | {r['calls']} | {fmt(r['input'])} | {fmt(r['cache_write'])} | {fmt(r['cache_read'])} | "
                   f"{fmt(r['output'])} ({fmt(r['thinking'])}) | {r['usd']:.2f} $ | {100*r['usd']/total:.0f} % |")
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Token use per agent, skill and model, from local transcripts.")
    ap.add_argument("project", nargs="?", type=Path, default=Path.cwd())
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--session")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--sprint")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    base = project_dir(a.project)
    if not base.is_dir():
        print(f"error: pas d'historique Claude Code pour {a.project} ({base})", file=sys.stderr)
        return 2
    if a.sprint:
        path = sprint_file(a.project, a.sprint)
        if not path.is_file():
            print(f"error: pas de sprint {a.sprint} ({path})", file=sys.stderr)
            return 2
        since, until, sprint_tickets = sprint_period(a.project, path.read_text(encoding="utf-8"))
        _, by_model, _, verdicts, stats = scan(base, since, None, until)
        tickets = delivered(a.project, since, until) & set(sprint_tickets)
        out = measures(a.sprint, since, until, tickets, sprint_tickets, by_model, verdicts, stats, earlier_costs(a.project, a.sprint))
        if a.write:
            write_section(path, out)
        print("\n".join(out))
        return 0
    by_actor, by_model, reads, verdicts, _ = scan(base, a.since, a.session, a.until)
    if not by_actor:
        print("Aucun échange trouvé pour ce filtre.")
        return 0
    total = sum(r["usd"] for r in by_model.values())
    tickets = delivered(a.project, a.since, a.until)
    reviews = ", ".join(f"{k} {n}" for k, n in sorted(verdicts.items())) or "aucune"
    out = [f"Historique lu : {base}" + (f" — depuis le {a.since}" if a.since else "") + (f" — jusqu'au {a.until}" if a.until else ""),
           "« coût » : prix catalogue en dollars selon le modèle (estimation, hors abonnement) ; « part » : part de ce coût.",
           "Session principale : attribuée au dernier skill lancé depuis ton dernier message (approximation).", "",
           "## Résultat", f"- Coût total : {total:.2f} $",
           f"- Tickets livrés (commits `Hosa-Ticket:`) : {len(tickets)}" + (f" — {total/len(tickets):.2f} $ par ticket" if tickets else ""),
           f"- Revues `hosa-reviewer` : {reviews}", ""]
    out += table("Par agent et par skill", by_actor) + [""] + table("Par modèle", by_model) + [""]
    out += [f"## Fichiers les plus lus (top {a.top})", "| fichier | lectures | caractères renvoyés |", "|---|---|---|"]
    for f, (n, chars) in sorted(reads.items(), key=lambda kv: -kv[1][1])[: a.top]:
        out.append(f"| `{f}` | {n} | {fmt(chars)} |")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
