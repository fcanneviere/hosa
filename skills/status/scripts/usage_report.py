#!/usr/bin/env python3
"""Where do the tokens go? Reads Claude Code's local transcripts and reports
token use per agent, per skill and per model, plus the files read the most.

  usage_report.py [project-dir] [--since YYYY-MM-DD] [--session ID] [--top N]

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
import sys
from collections import defaultdict
from pathlib import Path

FIELDS = ("calls", "input", "cache_write", "cache_read", "output", "thinking")
# Relative cost of each token type, input = 1 (Anthropic pricing structure). Model price differences are not included.
WEIGHT = {"input": 1.0, "cache_write": 1.25, "cache_read": 0.1, "output": 5.0}


def weight(r: dict) -> float:
    return sum(r[k] * w for k, w in WEIGHT.items())


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


def add(table: dict, key: str, usage: dict) -> None:
    row = table[key]
    row["calls"] += 1
    row["input"] += usage.get("input_tokens", 0) or 0
    row["cache_write"] += usage.get("cache_creation_input_tokens", 0) or 0
    row["cache_read"] += usage.get("cache_read_input_tokens", 0) or 0
    row["output"] += usage.get("output_tokens", 0) or 0
    row["thinking"] += ((usage.get("output_tokens_details") or {}).get("thinking_tokens", 0)) or 0


def scan(base: Path, since: str | None, session: str | None):
    by_actor: dict = defaultdict(lambda: dict.fromkeys(FIELDS, 0))
    by_model: dict = defaultdict(lambda: dict.fromkeys(FIELDS, 0))
    reads: dict = defaultdict(lambda: [0, 0])          # file -> [times, chars]
    agent_types: dict[str, str] = {}                    # tool_use id -> subagent type
    agent_of: dict[str, str] = {}                       # agentId -> subagent type
    pending_read: dict[str, tuple[str, str]] = {}       # tool_use id -> (actor, file)
    sidechain: list[tuple[Path, list]] = []

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
            if since and str(e.get("timestamp", ""))[:10] < since:
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
            elif e.get("type") == "assistant":
                actor = f"skill {skill}" if skill else "session principale"
                usage = (e.get("message") or {}).get("usage") or {}
                if usage:
                    add(by_actor, actor, usage)
                    add(by_model, (e.get("message") or {}).get("model", "?"), usage)
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
        for e in entries:
            if since and str(e.get("timestamp", ""))[:10] < since:
                continue
            if e.get("type") == "assistant":
                usage = (e.get("message") or {}).get("usage") or {}
                if usage:
                    add(by_actor, actor, usage)
                    add(by_model, (e.get("message") or {}).get("model", "?"), usage)
                for b in blocks(e):
                    if b.get("type") == "tool_use" and b.get("name") == "Read" and (b.get("input") or {}).get("file_path"):
                        pending_read[b["id"]] = (actor, b["input"]["file_path"])
            elif e.get("type") == "user":
                count_reads(e, pending_read, reads)
    return by_actor, by_model, reads


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
    total = sum(weight(r) for r in data.values()) or 1
    out = [f"## {title}", "| | appels | entrée | cache écrit | cache lu | sortie (dont réflexion) | part |", "|---|---|---|---|---|---|---|"]
    for key, r in sorted(data.items(), key=lambda kv: -weight(kv[1])):
        out.append(f"| {key} | {r['calls']} | {fmt(r['input'])} | {fmt(r['cache_write'])} | {fmt(r['cache_read'])} | "
                   f"{fmt(r['output'])} ({fmt(r['thinking'])}) | {100*weight(r)/total:.0f} % |")
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Token use per agent, skill and model, from local transcripts.")
    ap.add_argument("project", nargs="?", type=Path, default=Path.cwd())
    ap.add_argument("--since")
    ap.add_argument("--session")
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args(argv)
    base = project_dir(a.project)
    if not base.is_dir():
        print(f"error: pas d'historique Claude Code pour {a.project} ({base})", file=sys.stderr)
        return 2
    by_actor, by_model, reads = scan(base, a.since, a.session)
    if not by_actor:
        print("Aucun échange trouvé pour ce filtre.")
        return 0
    out = [f"Historique lu : {base}" + (f" — depuis le {a.since}" if a.since else ""),
           "« part » : coût relatif par type de token (entrée 1, cache écrit 1,25, cache lu 0,1, sortie 5), sans la différence de prix entre modèles — voir le tableau par modèle.",
           "Session principale : attribuée au dernier skill lancé depuis ton dernier message (approximation).", ""]
    out += table("Par agent et par skill", by_actor) + [""] + table("Par modèle", by_model) + [""]
    out += [f"## Fichiers les plus lus (top {a.top})", "| fichier | lectures | caractères renvoyés |", "|---|---|---|"]
    for f, (n, chars) in sorted(reads.items(), key=lambda kv: -kv[1][1])[: a.top]:
        out.append(f"| `{f}` | {n} | {fmt(chars)} |")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
