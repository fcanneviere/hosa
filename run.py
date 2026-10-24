#!/usr/bin/env python3
"""Hosa launcher — the one entry point of every Hosa script.

  python run.py <script> [args]   runs a Hosa script by name (`avancement`, `kb_query`, `docker_check`, `graph`…),
                                  from any folder, with Hosa's own Python — never its path under the plugin cache
  python run.py --list            the script names
  python run.py                   from the managed project: serves its .hosa/kb on http://127.0.0.1:3000
  python run.py --setup           only (re)builds the venv — the SessionStart hook runs it in the background

Sessions call it through `<hosa>`, a shim in ${CLAUDE_PLUGIN_DATA} that survives plugin updates (hooks/graph.js).

The app's dependencies live in a venv, never in the system Python (PEP 668): ${CLAUDE_PLUGIN_DATA}/venv once
installed (kept across plugin updates, the plugin root is replaced at each one), hosa/app/.venv from the repo.
They're reinstalled when requirements.txt changes (stamp in the venv), with uv when it's on the PATH, pip otherwise.
"""
import hashlib
import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent / "hosa" / "app"
VENV = Path(os.environ["CLAUDE_PLUGIN_DATA"]) / "venv" if os.environ.get("CLAUDE_PLUGIN_DATA") else APP / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
REQS = APP / "requirements.txt"
STAMP = VENV / "hosa-requirements.sha1"
# Launched detached by the SessionStart hook: on Windows each console child would open its own window.
# A hidden console for each direct child; theirs (uv's python, ensurepip) inherit it.
NO_WINDOW = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}


def setup():
    want = hashlib.sha1(REQS.read_bytes()).hexdigest()
    if PY.exists() and STAMP.exists() and STAMP.read_text() == want:
        return
    uv = shutil.which("uv")  # much faster when present; --seed keeps pip in the venv should uv go away later
    if not PY.exists():
        if uv:
            subprocess.check_call([uv, "venv", "-q", "--seed", "--python", sys.executable, str(VENV)], **NO_WINDOW)
        else:
            subprocess.check_call([sys.executable, "-m", "venv", str(VENV)], **NO_WINDOW)
    if uv:
        subprocess.check_call([uv, "pip", "install", "-q", "--python", str(PY), "-r", str(REQS)], **NO_WINDOW)
    else:
        subprocess.check_call([str(PY), "-m", "pip", "install", "-q", "--disable-pip-version-check", "-r", str(REQS)],
                              **NO_WINDOW)
    STAMP.write_text(want)


def scripts():
    root = Path(__file__).resolve().parent
    found = {p.stem: p for p in sorted(root.glob("skills/*/scripts/*.py")) + sorted(root.glob("skills/*/vendor/*/scripts/*.py"))}
    found["graph"] = APP / "graph.py"
    return found


def run_script(name, args):
    table = scripts()
    path = table.get(name.removesuffix(".py"))
    if path is None:
        print(f"Script Hosa inconnu : {name}. Scripts : {', '.join(sorted(table))}", file=sys.stderr)
        return 2
    try:
        setup()
        py = PY
    except Exception as exc:  # no network to build the venv: a stdlib script still runs, say why a yaml one fails
        print(f"[hosa] venv indisponible ({exc}) — script lancé avec {sys.executable}", file=sys.stderr)
        py = Path(sys.executable)
    sys.argv = [str(path), *args]
    if Path(sys.executable).resolve() == py.resolve():  # already Hosa's Python: no child process, no window
        sys.path.insert(0, str(path.parent))
        runpy.run_path(str(path), run_name="__main__")
        return 0
    # No NO_WINDOW here: the child shares our console, and with it the venv's python.exe redirector
    # loses the inherited stdout (tested on Windows, 2026-10-24).
    return subprocess.call([str(py), str(path), *args])


def kb_root(start):
    # Like hooks/graph.js findKbRoot: a sprint worktree's copy of .hosa/kb is stale, keep walking up.
    for d in (start, *start.parents):
        if (d / ".hosa" / "kb").is_dir() and ".worktrees" not in d.parts:
            return d / ".hosa" / "kb"
    return None


if __name__ == "__main__":
    if sys.argv[1:2] == ["--list"]:
        print("\n".join(sorted(scripts())))
        raise SystemExit(0)
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        raise SystemExit(run_script(sys.argv[1], sys.argv[2:]))
    setup()
    if "--setup" in sys.argv:
        raise SystemExit(0)
    root = os.environ.get("HOSA_KB_ROOT") or kb_root(Path.cwd().resolve())
    if not root:
        raise SystemExit("Pas de .hosa/kb ici ni au-dessus : lance run.py depuis le projet géré par Hosa.")
    env = {**os.environ, "HOSA_KB_ROOT": str(root), "PYTHONUTF8": "1"}
    if "--no-browser" not in sys.argv:
        env["HOSA_OPEN_BROWSER"] = "1"  # server.py opens it once the port is its own, never on another project's server
    try:
        raise SystemExit(subprocess.call([str(PY), str(APP / "server.py")], env=env, **NO_WINDOW))
    except KeyboardInterrupt:
        pass
