#!/usr/bin/env python3
"""Check that a Docker Compose environment runs the right checkout's files.

  docker_check.py <compose-project> <checkout-dir>
      Every container of <compose-project> must be running, have been started
      from <checkout-dir> (compose's working_dir label) with compose files of
      that checkout only, and bind-mount nothing
      from the managed project other than <checkout-dir> — no other sprint's
      worktree, no base checkout when a sprint is targeted.

  docker_check.py --orphans <project-root> [--clean]
      List what a finished sprint left behind: compose projects started from a
      `.worktrees/` folder of <project-root> that no longer exists, the images
      of a `<projet>-sprint-<slug>` whose worktree is gone and that no container
      uses, and the dangling images of the project's compose projects. Also lists,
      to confirm with the user, the extra compose projects started from the root
      under another name than the base project (`rieki-ux`). `--clean` removes
      the first three (rebuilt by `up --build`), never an extra project.

Exit: 0 OK / no orphan, 1 problems listed, 2 bad invocation or Docker
unreachable. Stdlib only. Paths are compared after normalising Windows,
Docker Desktop and WSL spellings, so it works on any host.
"""
from __future__ import annotations

import json
import re
import os
import subprocess
import sys
from pathlib import Path

NO_WINDOW = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}

PROJECT = "com.docker.compose.project"
WORKDIR = "com.docker.compose.project.working_dir"
CONFIG = "com.docker.compose.project.config_files"


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
        sprint = re.search(r"-sprint-(.+)$", labels.get(PROJECT, ""))
        if sprint and f"/.worktrees/sprint/{sprint.group(1)}" not in norm(checkout):
            # checked against the wrong checkout, the check itself would pass on the wrong files
            return [f"{labels[PROJECT]} est un projet de sprint : son checkout est "
                    f"{root}/.worktrees/sprint/{sprint.group(1)}, pas {checkout}"]
        if not (c.get("State") or {}).get("Running"):
            out.append(f"{name} : arrêté")
        wd = labels.get(WORKDIR)
        if wd and norm(wd) != norm(checkout):
            out.append(f"{name} : démarré depuis {wd}, pas depuis {checkout}")
        for cfg in filter(None, labels.get(CONFIG, "").split(",")):
            if not inside(cfg.strip(), checkout):
                out.append(f"{name} : fichier compose hors du checkout — {cfg.strip()}")
        for m in c.get("Mounts") or []:
            src = m.get("Source", "")
            wrong = not inside(src, checkout) or (
                norm(checkout) == norm(root) and inside(src, str(Path(root) / ".worktrees")))
            if m.get("Type") == "bind" and inside(src, root) and wrong:
                out.append(f"{name} : monte {src} → {m.get('Destination')} (hors de {checkout})")
    return out


def base_project(root: str) -> str:
    """Compose's default project name for the root: its folder name, lowercased, [a-z0-9_-] only."""
    return re.sub(r"[^a-z0-9_-]", "", Path(root.replace("\\", "/").rstrip("/")).name.lower())


def folders(project: dict) -> list[str]:
    return [str(Path(c.strip()).parent) for c in str(project.get("ConfigFiles", "")).split(",") if c.strip()]


def orphans(projects: list[dict], root: str, images: list[dict] | None = None,
            exists=lambda f: Path(f).exists(), base: str | None = None) -> list[dict]:
    """What a finished sprint left behind, as [{"quoi", "nom", "taille", "sur": bool, "cmd": [[docker args]…]}].

    `projects`: `docker compose ls -a --format json`; `images`: `docker image inspect` of the images carrying a
    compose project label. `sur` = rebuilt by `up --build`, removed by `--clean`; else the user confirms first.
    `base`: the base project's name when the KB names it (`-p courses` on hosa-pilote2), else the folder's."""
    base, wt = base or base_project(root), str(Path(root) / ".worktrees")
    out, names = [], {p.get("Name") for p in projects}
    for p in projects:
        name, fs = p.get("Name"), folders(p)
        gone = [f for f in fs if inside(f, wt) and not exists(f)]
        if gone:
            out.append({"quoi": f"environnement sur un dossier disparu ({gone[0]})", "nom": name, "sur": True,
                        "cmd": [["compose", "-p", name, "down", "-v", "--remove-orphans"]]})
        elif fs and all(inside(f, root) and not inside(f, wt) for f in fs) and name != base:
            out.append({"quoi": f"environnement hors plan démarré depuis {root}", "nom": name, "sur": False,
                        "cmd": [["compose", "-p", name, "down", "-v", "--rmi", "local"]]})
    for i in images or []:
        labels = (i.get("Config") or {}).get("Labels") or {}
        proj, tags = labels.get(PROJECT, ""), i.get("RepoTags") or []
        size = f"{(i.get('Size') or 0) / 1e9:.1f} Go"
        sprint = re.fullmatch(rf"{re.escape(base)}-sprint-(.+)", proj)
        if not tags and (proj == base or sprint):
            out.append({"quoi": f"image sans nom de {proj}", "nom": i.get("Id", "?")[7:19], "taille": size,
                        "sur": True, "cmd": [["image", "rm", i.get("Id", "")]]})
        elif sprint and proj not in names and not exists(str(Path(wt) / "sprint" / sprint.group(1))):
            out.append({"quoi": "image d'un sprint fini", "nom": ", ".join(tags), "taille": size, "sur": True,
                        "cmd": [["image", "rm", *tags]]})
    return out


def line(o: dict) -> str:
    cmds = " ; ".join("docker " + " ".join(c) for c in o["cmd"])
    size = f" ({o['taille']})" if o.get("taille") else ""
    return f"{o['nom']}{size} : {o['quoi']} — `{cmds}`" + ("" if o["sur"] else " — à confirmer avec l'utilisateur")


def compose_images() -> list[dict]:
    ids = sorted(set(docker("image", "ls", "-aq", "--filter", f"label={PROJECT}").split()))
    return json.loads(docker("image", "inspect", *ids)) if ids else []


def docker(*args: str) -> str:
    r = subprocess.run(["docker", *args], capture_output=True, text=True, **NO_WINDOW)
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or f"docker {' '.join(args)} failed")
    return r.stdout


def main(argv: list[str]) -> int:
    try:
        if len(argv) in (2, 3) and argv[0] == "--orphans" and argv[2:] in ([], ["--clean"]):
            raw = docker("compose", "ls", "-a", "--format", "json").strip() or "[]"
            left = orphans(json.loads(raw), argv[1], compose_images())
            if argv[2:]:
                for o in [o for o in left if o["sur"]]:
                    try:
                        for c in o["cmd"]:
                            docker(*c)
                        print(f"✓ supprimé : {o['nom']}" + (f" ({o['taille']})" if o.get("taille") else ""))
                    except RuntimeError as exc:  # an image still used: say it, go on with the others
                        print(f"✗ {o['nom']} : {exc}")
                raw = docker("compose", "ls", "-a", "--format", "json").strip() or "[]"
                left = orphans(json.loads(raw), argv[1], compose_images())
            found = [line(o) for o in left]
            ok = "✓ aucun environnement orphelin"
        elif len(argv) == 2:
            ids = docker("ps", "-aq", "--filter", f"label={PROJECT}={argv[0]}").split()
            found = problems(json.loads(docker("inspect", *ids)) if ids else [], argv[1])
            ok = f"✓ {argv[0]} tourne sur {argv[1]}"
        else:
            print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
            print("       docker_check.py --orphans <project-root> [--clean]", file=sys.stderr)
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
