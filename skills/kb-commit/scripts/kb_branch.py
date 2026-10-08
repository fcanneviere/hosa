#!/usr/bin/env python3
"""Keep the Hosa KB on its own orphan branch, checked out at `<root>/.hosa/kb`.

The KB then never appears in the code's branches: sprint worktrees carry no
stale copy, sprint merges never touch it, and KB commits never mix with code
commits. Each KB commit records the code commit it was made against
(`Hosa-Code-Commit:` trailer), so "which KB went with which code" stays
answerable.

  kb_branch.py status  <root>                   where the KB lives now
  kb_branch.py init    <root>                   new project: create the branch and its worktree
  kb_branch.py migrate <root> [--yes]           move a KB tracked in the code branches to the branch
  kb_branch.py ensure  <root>                   check out the branch at .hosa/kb if it isn't (new clone)
  kb_branch.py commit  <root> -m <message>      commit every KB change on the branch
  kb_branch.py memoire <root> [--yes]           move agent memories from the old `project` scope to `local`

`migrate` without --yes only says what it would do. It keeps the KB's current
content, uncommitted changes included, and checks the result byte for byte
before removing anything. Exit: 0 done, 1 refused (reason printed), 2 bad
invocation. Stdlib only; needs git.
"""
from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BRANCH = "hosa-kb"


def git(root: Path, *args: str, env: dict | None = None, check: bool = True) -> str:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                       env={**os.environ, **(env or {})})
    if check and r.returncode:
        raise SystemExit(f"✗ git {' '.join(args)} : {r.stderr.strip()}")
    return r.stdout.strip()


def has_branch(root: Path, name: str) -> bool:
    return subprocess.run(["git", "-C", str(root), "show-ref", "--verify", "--quiet", name]).returncode == 0


def is_kb_worktree(kb: Path) -> bool:
    if not (kb / ".git").exists():
        return False
    return git(kb, "rev-parse", "--abbrev-ref", "HEAD", check=False) == BRANCH


def tracked_kb(root: Path) -> bool:
    return bool(git(root, "ls-files", "--", ".hosa/kb", check=False))


IGNORED = {".hosa/": "# Hosa : KB sur la branche hosa-kb, graphe régénéré",
           ".claude/agent-memory-local/": "# Hosa : mémoire des agents, propre à cette machine"}
KEEP_MEMORY = {"hosa-tester", "hosa-debugger", "hosa-challenger", "hosa-reviewer", "hosa-key-user",
               "hosa-product-owner", "hosa-qa-lead", "hosa-dba", "hosa-tech-lead", "hosa-developer",
               "hosa-implementer", "hosa-planner"}


def ignore_hosa(root: Path) -> bool:
    """Make the code branch's .gitignore cover `.hosa/` and the agents' local memory. True if it changed."""
    gi = root / ".gitignore"
    lines = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    have = {l.strip().strip("/") for l in lines}
    add = [x for e, c in IGNORED.items() if e.strip("/") not in have for x in (c, e)]
    if not add:
        return False
    gi.write_text("\n".join(lines + add) + "\n", encoding="utf-8")
    return True


def memoire(root: Path, yes: bool) -> int:
    """Move agent memories written under the old `project` scope to the `local` one."""
    old = root / ".claude" / "agent-memory"
    new = root / ".claude" / "agent-memory-local"
    dirs = sorted(d for d in old.iterdir() if d.is_dir()) if old.is_dir() else []
    if not dirs:
        changed = ignore_hosa(root)
        print("✓ rien à déplacer" + (" — .gitignore complété (à committer)" if changed else ""))
        return 0
    plan = [f"- {d.name} → " + (f".claude/agent-memory-local/{d.name}" if d.name in KEEP_MEMORY
            else f".claude/agent-memory-local/_archive/{d.name} (agent sans mémoire désormais : ses faits sont dans la KB)") for d in dirs]
    tracked = bool(git(root, "ls-files", "--", ".claude/agent-memory", check=False))
    if not yes:
        print("Déplacement prévu (relance avec --yes pour l'exécuter, rien n'est supprimé) :\n" + "\n".join(plan)
              + ("\n- .claude/agent-memory retiré du suivi git, .gitignore complété, dans un commit à ton nom" if tracked else "\n- .gitignore complété"))
        return 0
    for d in dirs:
        target = new / d.name if d.name in KEEP_MEMORY else new / "_archive" / d.name
        if target.exists():
            print(f"✗ {target} existe déjà — fusionne-le à la main avec {d}, puis relance")
            return 1
        target.parent.mkdir(parents=True, exist_ok=True)
        d.rename(target)
    ignore_hosa(root)
    if tracked:
        identity(root)
        git(root, "rm", "-r", "--cached", "--quiet", ".claude/agent-memory")
        git(root, "add", ".gitignore")
        git(root, "commit", "-m", "chore: mémoire des agents Hosa locale, hors du suivi git")
    if old.is_dir() and not any(old.iterdir()):
        old.rmdir()
    print(f"✓ {len(dirs)} mémoire(s) déplacée(s) vers .claude/agent-memory-local/")
    return 0


def identity(root: Path) -> None:
    if not git(root, "config", "user.name", check=False) or not git(root, "config", "user.email", check=False):
        raise SystemExit("✗ git user.name/user.email non configurés — à régler avant tout commit (jamais d'autre identité).")


def same_tree(a: Path, b: Path) -> bool:
    cmp = filecmp.dircmp(a, b, ignore=[".git"])
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    return all(same_tree(a / d, b / d) for d in cmp.common_dirs)


def status(root: Path) -> int:
    kb = root / ".hosa" / "kb"
    local, remote = has_branch(root, f"refs/heads/{BRANCH}"), has_branch(root, f"refs/remotes/origin/{BRANCH}")
    if is_kb_worktree(kb):
        print(f"✓ KB sur la branche {BRANCH}, extraite dans .hosa/kb")
    elif tracked_kb(root):
        print(f"! KB suivie dans les branches du code — à migrer : kb_branch.py migrate {root}")
    elif local or remote:
        print(f"! Branche {BRANCH} présente mais pas extraite — kb_branch.py ensure {root}")
    elif kb.exists():
        print(f"! .hosa/kb existe sans branche ni suivi git — kb_branch.py migrate {root}")
    else:
        print(f"! Pas de KB — kb_branch.py init {root}")
    return 0


def orphan_commit_from(root: Path, folder: Path, message: str) -> str:
    """Commit `folder`'s content (as the tree root) as a parentless commit, without touching any index."""
    with tempfile.TemporaryDirectory() as tmp:
        env = {"GIT_INDEX_FILE": str(Path(tmp) / "index"), "GIT_WORK_TREE": str(folder)}
        r = subprocess.run(["git", "-C", str(root), "--work-tree", str(folder), "add", "-A", "."],
                           capture_output=True, text=True, env={**os.environ, **env}, cwd=folder)
        if r.returncode:
            raise SystemExit(f"✗ git add (KB) : {r.stderr.strip()}")
        tree = git(root, "write-tree", env=env)
    return git(root, "commit-tree", tree, "-m", message)


def init(root: Path) -> int:
    kb = root / ".hosa" / "kb"
    if is_kb_worktree(kb):
        print("✓ déjà en place")
        return 0
    if kb.exists() or tracked_kb(root) or has_branch(root, f"refs/heads/{BRANCH}"):
        print("✗ une KB existe déjà — utilise `migrate` ou `ensure`")
        return 1
    identity(root)
    with tempfile.TemporaryDirectory() as tmp:
        seed = Path(tmp) / "kb"
        seed.mkdir()
        (seed / "index.md").write_text('---\nokf_version: "0.2"\n---\n# KB Hosa\n', encoding="utf-8")
        sha = orphan_commit_from(root, seed, "chore(kb): initialise la KB Hosa")
    git(root, "update-ref", f"refs/heads/{BRANCH}", sha)
    changed = ignore_hosa(root)
    git(root, "worktree", "add", str(kb), BRANCH)
    print(f"✓ branche {BRANCH} créée et extraite dans .hosa/kb" + (" — .hosa/ ajouté au .gitignore (à committer)" if changed else ""))
    return 0


def migrate(root: Path, yes: bool) -> int:
    kb = root / ".hosa" / "kb"
    if is_kb_worktree(kb):
        print("✓ déjà migrée")
        return 0
    if not kb.is_dir():
        print("✗ pas de dossier .hosa/kb à migrer — utilise `init`")
        return 1
    if has_branch(root, f"refs/heads/{BRANCH}"):
        print(f"✗ la branche {BRANCH} existe déjà : la KB a sans doute été migrée ailleurs — utilise `ensure`, ne migre pas deux fois")
        return 1
    if git(root, "worktree", "list", "--porcelain").count("worktree ") > 1:
        print("✗ des worktrees de sprint sont ouverts — termine ou ferme les sprints actifs avant de migrer")
        return 1
    tracked = tracked_kb(root)
    plan = [f"1. créer la branche orpheline {BRANCH} avec le contenu actuel de .hosa/kb (modifications non committées comprises)",
            "2. " + ("retirer .hosa/kb du suivi de la branche courante et " if tracked else "") + "ajouter .hosa/ au .gitignore, dans un commit à ton nom",
            "3. remplacer le dossier .hosa/kb par l'extraction de la branche, après vérification octet par octet"]
    if not yes:
        print("Migration prévue (relance avec --yes pour l'exécuter) :\n" + "\n".join(plan))
        return 0
    identity(root)
    sha = orphan_commit_from(root, kb, f"chore(kb): migre la KB Hosa sur sa branche\n\nHosa-Code-Commit: {git(root, 'rev-parse', 'HEAD', check=False) or 'aucun'}")
    git(root, "update-ref", f"refs/heads/{BRANCH}", sha)
    backup = root / ".hosa" / "kb.avant-migration"
    if backup.exists():
        print(f"✗ {backup} existe déjà — supprime-le ou renomme-le, puis relance")
        return 1
    kb.rename(backup)
    try:
        if tracked:
            git(root, "rm", "-r", "--cached", "--quiet", ".hosa/kb")
        ignore_hosa(root)
        git(root, "add", ".gitignore")
        if git(root, "diff", "--cached", "--name-only"):
            git(root, "commit", "-m", f"chore: déplace la KB Hosa sur la branche {BRANCH}", "--", ".gitignore", *([".hosa/kb"] if tracked else []))
        git(root, "worktree", "add", str(kb), BRANCH)
        if not same_tree(backup, kb):
            raise SystemExit(f"✗ le contenu extrait diffère de l'original — rien n'est supprimé : l'original est dans {backup}")
    except SystemExit:
        if not kb.exists():
            backup.rename(kb)
        raise
    shutil.rmtree(backup)
    print(f"✓ KB migrée sur la branche {BRANCH}, extraite dans .hosa/kb, contenu identique vérifié")
    return 0


def ensure(root: Path) -> int:
    kb = root / ".hosa" / "kb"
    if is_kb_worktree(kb):
        print("✓ en place")
        return 0
    if not has_branch(root, f"refs/heads/{BRANCH}"):
        if has_branch(root, f"refs/remotes/origin/{BRANCH}"):
            git(root, "branch", BRANCH, f"origin/{BRANCH}")
        else:
            print(f"✗ pas de branche {BRANCH} (ni locale ni origin) — `init` ou `migrate`")
            return 1
    if kb.exists() and any(kb.iterdir()):
        print(f"✗ .hosa/kb existe déjà et n'est pas l'extraction de {BRANCH} — `migrate`, ou déplace-le")
        return 1
    if kb.exists():
        kb.rmdir()
    git(root, "worktree", "prune")
    git(root, "worktree", "add", str(kb), BRANCH)
    print(f"✓ branche {BRANCH} extraite dans .hosa/kb")
    return 0


def commit(root: Path, message: str) -> int:
    kb = root / ".hosa" / "kb"
    if not is_kb_worktree(kb):
        print(f"✗ .hosa/kb n'est pas l'extraction de {BRANCH} — `status` pour voir quoi faire")
        return 1
    identity(kb)
    git(kb, "add", "-A")
    if not git(kb, "diff", "--cached", "--name-only"):
        print("✓ rien à committer")
        return 0
    code = git(root, "rev-parse", "HEAD", check=False) or "aucun"
    git(kb, "commit", "-q", "-m", message, "-m", f"Hosa-Code-Commit: {code}")
    print(f"✓ {git(kb, 'rev-parse', '--short', 'HEAD')} sur {BRANCH} (code : {code[:12]})")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["status", "init", "migrate", "ensure", "commit", "memoire"])
    ap.add_argument("root", type=Path)
    ap.add_argument("-m", "--message")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args(argv)
    root = a.root.resolve()
    if not (root / ".git").exists():
        print(f"error: {root} n'est pas la racine d'un dépôt git", file=sys.stderr)
        return 2
    if a.action == "commit" and not a.message:
        print("error: commit needs -m", file=sys.stderr)
        return 2
    return {"status": lambda: status(root), "init": lambda: init(root), "ensure": lambda: ensure(root),
            "migrate": lambda: migrate(root, a.yes), "commit": lambda: commit(root, a.message),
            "memoire": lambda: memoire(root, a.yes)}[a.action]()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
