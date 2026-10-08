#!/usr/bin/env python3
"""Check that a Docker Compose environment runs the right checkout's files.

  docker_check.py <compose-project> <checkout-dir>
      Every container of <compose-project> must be running, have been started
      from <checkout-dir> (compose's working_dir label), and bind-mount nothing
      from the managed project other than <checkout-dir> — no other sprint's
      worktree, no base checkout when a sprint is targeted.

  docker_check.py --orphans <project-root>
      List compose projects started from a `.worktrees/` folder of
      <project-root> that no longer exists (a finished or deleted sprint).

Exit: 0 OK / no orphan, 1 problems listed, 2 bad invocation or Docker
unreachable. Stdlib only. Paths are compared after normalising Windows,
Docker Desktop and WSL spellings, so it works on any host.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT = "com.docker.compose.project"
WORKDIR = "com.docker.compose.project.working_dir"


def norm(path: str) -> str:
    p = path.replace("\\", "/").rstrip("/").lower()
    p = re.sub(r"^/(?:run/desktop/mnt/host|host_mnt|mnt)/([a-z])(?=/|$)", r"/\1", p)
    p = re.sub(r"^([a-z]):(?=/|$)", r"/\1", p)
    return p


def inside(path: str, folder: str) -> bool:
    p, f = norm(path), norm(folder)
    return p == f or p.startswith(f + "/")


def root_of(checkout: str) -> str:
    n = checkout.replace("\\", "/")
    i = n.find("/.worktrees/")
    return checkout[:i] if i >= 0 else checkout


def problems(containers: list[dict], checkout: str) -> list[str]:
    """Pure check on `docker inspect` output, so it can be tested without Docker."""
    if not containers:
        return ["aucun conteneur pour ce projet compose — environnement non démarré"]
    root = root_of(checkout)
    out = []
    for c in containers:
        name = c.get("Name", "?").lstrip("/")
        labels = (c.get("Config") or {}).get("Labels") or {}
        if not (c.get("State") or {}).get("Running"):
            out.append(f"{name} : arrêté")
        wd = labels.get(WORKDIR)
        if wd and norm(wd) != norm(checkout):
            out.append(f"{name} : démarré depuis {wd}, pas depuis {checkout}")
        for m in c.get("Mounts") or []:
            src = m.get("Source", "")
            wrong = not inside(src, checkout) or (
                norm(checkout) == norm(root) and inside(src, str(Path(root) / ".worktrees")))
            if m.get("Type") == "bind" and inside(src, root) and wrong:
                out.append(f"{name} : monte {src} → {m.get('Destination')} (hors de {checkout})")
    return out


def orphans(projects: list[dict], root: str) -> list[str]:
    """`projects`: [{"Name":…, "ConfigFiles":…}] as `docker compose ls -a --format json` gives."""
    out = []
    for p in projects:
        for cfg in str(p.get("ConfigFiles", "")).split(","):
            folder = str(Path(cfg.strip()).parent) if cfg.strip() else ""
            if folder and inside(folder, str(Path(root) / ".worktrees")) and not Path(folder).exists():
                out.append(f"{p.get('Name')} : dossier {folder} disparu — `docker compose -p {p.get('Name')} down`")
    return out


def docker(*args: str) -> str:
    r = subprocess.run(["docker", *args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or f"docker {' '.join(args)} failed")
    return r.stdout


def main(argv: list[str]) -> int:
    try:
        if len(argv) == 2 and argv[0] == "--orphans":
            raw = docker("compose", "ls", "-a", "--format", "json").strip() or "[]"
            found = orphans(json.loads(raw), argv[1])
            ok = "✓ aucun environnement orphelin"
        elif len(argv) == 2:
            ids = docker("ps", "-aq", "--filter", f"label={PROJECT}={argv[0]}").split()
            found = problems(json.loads(docker("inspect", *ids)) if ids else [], argv[1])
            ok = f"✓ {argv[0]} tourne sur {argv[1]}"
        else:
            print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
            print("       docker_check.py --orphans <project-root>", file=sys.stderr)
            return 2
    except (RuntimeError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"error: Docker injoignable ou réponse illisible — {exc}", file=sys.stderr)
        return 2
    for f in found:
        print(f"✗ {f}")
    print(ok if not found else f"{len(found)} problème(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
