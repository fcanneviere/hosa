#!/usr/bin/env python3
"""Hosa dashboard launcher.

  python run.py            from the managed project: serves its .hosa/kb on http://localhost:3000
  python run.py --setup    only (re)builds hosa/app/.venv — the SessionStart hook runs it in the background

The app's dependencies live in hosa/app/.venv, never in the system Python (PEP 668).
They're reinstalled when requirements.txt changes (stamp in the venv).
"""
import hashlib
import os
import subprocess
import sys
import venv
import webbrowser
from pathlib import Path

APP = Path(__file__).resolve().parent / "hosa" / "app"
VENV = APP / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
REQS = APP / "requirements.txt"
STAMP = VENV / "hosa-requirements.sha1"


def setup():
    want = hashlib.sha1(REQS.read_bytes()).hexdigest()
    if PY.exists() and STAMP.exists() and STAMP.read_text() == want:
        return
    if not PY.exists():
        venv.create(VENV, with_pip=True)
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
    port = os.environ.get("PORT", "3000")
    if "--no-browser" not in sys.argv:
        webbrowser.open(f"http://localhost:{port}")
    try:
        subprocess.call([str(PY), str(APP / "server.py")], env={**os.environ, "HOSA_KB_ROOT": str(root), "PORT": port})
    except KeyboardInterrupt:
        pass
