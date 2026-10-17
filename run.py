#!/usr/bin/env python3
"""Hosa dashboard launcher.

  python run.py            from the managed project: serves its .hosa/kb on http://127.0.0.1:3000
  python run.py --setup    only (re)builds the venv — the SessionStart hook runs it in the background

The app's dependencies live in a venv, never in the system Python (PEP 668): ${CLAUDE_PLUGIN_DATA}/venv once
installed (kept across plugin updates, the plugin root is replaced at each one), hosa/app/.venv from the repo.
They're reinstalled when requirements.txt changes (stamp in the venv), with uv when it's on the PATH, pip otherwise.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

APP = Path(__file__).resolve().parent / "hosa" / "app"
VENV = Path(os.environ["CLAUDE_PLUGIN_DATA"]) / "venv" if os.environ.get("CLAUDE_PLUGIN_DATA") else APP / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
REQS = APP / "requirements.txt"
STAMP = VENV / "hosa-requirements.sha1"


def setup():
    want = hashlib.sha1(REQS.read_bytes()).hexdigest()
    if PY.exists() and STAMP.exists() and STAMP.read_text() == want:
        return
    uv = shutil.which("uv")  # much faster when present; --seed keeps pip in the venv should uv go away later
    if not PY.exists():
        if uv:
            subprocess.check_call([uv, "venv", "-q", "--seed", "--python", sys.executable, str(VENV)])
        else:
            venv.create(VENV, with_pip=True)
    if uv:
        subprocess.check_call([uv, "pip", "install", "-q", "--python", str(PY), "-r", str(REQS)])
    else:
        subprocess.check_call([str(PY), "-m", "pip", "install", "-q", "--disable-pip-version-check", "-r", str(REQS)])
    STAMP.write_text(want)


def kb_root(start):
    # Like hooks/graph.js findKbRoot: a sprint worktree's copy of .hosa/kb is stale, keep walking up.
    for d in (start, *start.parents):
        if (d / ".hosa" / "kb").is_dir() and ".worktrees" not in d.parts:
            return d / ".hosa" / "kb"
    return None


if __name__ == "__main__":
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
        raise SystemExit(subprocess.call([str(PY), str(APP / "server.py")], env=env))
    except KeyboardInterrupt:
        pass
