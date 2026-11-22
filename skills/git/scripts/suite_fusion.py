#!/usr/bin/env python3
"""Which tests the merge of a sprint must run (`hosa-git` Mode 2, Step 6).

  suite_fusion.py <kb> <checkout> [--ref <rev>]

Computes the tree of <rev> (default HEAD) without `.hosa/`, then compares it with every tree the KB records as fully
passed: an `Arbre testé : <hash> — suite complète X/X` line in a sprint's `## Suite complète` or in a ticket's
`## Résultats techniques` (a line that leaves the browser tests out does not count). The tree diff is the proof: a
recorded tree whose diff to the tip touches only test files ran the same product code, so only the test files the diff
adds or changes run again (rieki sprint-4: a QA commit swapped one browser test file and the merge reran 1360 tests).

Exit 0: no full suite. Prints `sauter` (same tree) or `ciblé` and, one per line after `lancer :`, the test files to run.
Exit 1: full suite. Prints why (no recorded tree, or the product files changed since the closest one).
Exit 2: bad invocation or git error — run the full suite.
Lint, format and type checks always run: this script decides the suite only. Stdlib only.
"""
from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

NO_WINDOW = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}

TESTED = re.compile(r"Arbre testé\s*:\s*`?([0-9a-f]{40})`?.*?suite complète\s+(\d+)\s*/\s*(\d+)", re.I)
NO_BROWSER = re.compile(r"non[- ]navigateur|navigateur à part|sans (le )?navigateur|hors navigateur", re.I)
TEST_DIRS = {"tests", "test", "__tests__", "spec", "specs", "e2e"}
TEST_NAMES = ("test_*.py", "*_test.py", "*_test.go", "*.test.*", "*.spec.*", "*_spec.rb",
              "*Test.java", "*Tests.java", "*Test.kt", "*Tests.kt", "*Tests.cs", "*Test.cs", "*Test.php")
DOCS = (".md", ".rst")


def git(cwd: Path, *args: str, env: dict | None = None) -> str:
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, **(env or {})}, **NO_WINDOW)
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)} : {r.stderr.strip()}")
    return r.stdout


def tree_without_hosa(checkout: Path, ref: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        env = {"GIT_INDEX_FILE": str(Path(tmp) / "index")}
        git(checkout, "read-tree", ref, env=env)
        git(checkout, "rm", "-rq", "--cached", "--ignore-unmatch", ".hosa", env=env)
        return git(checkout, "write-tree", env=env).strip()


def section(text: str, title: str) -> list[str]:
    """Every `## <title>` section's lines (a ticket's results hold several runs)."""
    out, inside = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line[3:].strip() == title
            continue
        if inside:
            out.append(line)
    return out


def tested_trees(kb: Path) -> list[tuple[str, str]]:
    """(tree, source) of every fully passed run the KB records, in file order."""
    found = []
    sources = [(p, "Suite complète") for p in sorted((kb / "sprints").glob("*.md"))]
    sources += [(p, "Résultats techniques") for p in sorted((kb / "test").glob("*-technique.md"))]
    for path, title in sources:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in section(text, title):
            m = TESTED.search(line)
            if m and m.group(2) == m.group(3) and not NO_BROWSER.search(line):
                found.append((m.group(1), path.name))
    return found


def kind(path: str) -> str:
    """`test` (a test file: run it), `doc` (runs no code) or `code` (anything else: the full suite)."""
    p = PurePosixPath(path)
    in_tests = any(part in TEST_DIRS for part in p.parts[:-1])
    if any(fnmatch.fnmatchcase(p.name, pat) for pat in TEST_NAMES):
        return "test"
    if p.suffix.lower() in DOCS and (len(p.parts) == 1 or p.parts[0] == "docs" or in_tests):
        return "doc"
    return "code"


def changes(checkout: Path, old: str, new: str) -> list[tuple[str, str]]:
    """(status, path) of the diff; a rename gives its new path, a deletion its old one."""
    out = []
    for line in git(checkout, "diff-tree", "-r", "-M", "--name-status", old, new).splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            out.append((parts[0][0], parts[-1]))
    return out


def plan(checkout: Path, tip: str, trees: list[tuple[str, str]]):
    """The best recorded tree: (tree, source, tests to run) when only tests changed, else the reason."""
    best, closest = None, None
    for tree, source in reversed(trees):
        try:
            git(checkout, "cat-file", "-e", f"{tree}^{{tree}}")
            diff = changes(checkout, tree, tip)
        except RuntimeError:
            continue
        code = [p for s, p in diff if kind(p) == "code"]
        tests = sorted({p for s, p in diff if kind(p) == "test" and s != "D"})
        if not code:
            if best is None or len(tests) < len(best[2]):
                best = (tree, source, tests)
        elif closest is None or len(code) < len(closest[2]):
            closest = (tree, source, code)
    return best, closest


def main(argv: list[str]) -> int:
    args = list(argv)
    ref = "HEAD"
    if "--ref" in args:
        i = args.index("--ref")
        if i + 1 >= len(args):
            print(__doc__, file=sys.stderr)
            return 2
        ref = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    kb, checkout = Path(args[0]), Path(args[1])
    try:
        tip = tree_without_hosa(checkout, ref)
    except RuntimeError as exc:
        print(f"✗ {exc} — lance la suite complète", file=sys.stderr)
        return 2
    trees = tested_trees(kb)
    best, closest = plan(checkout, tip, trees)
    if best and not best[2] and best[0] == tip:
        print(f"sauter : arbre {tip} = arbre testé ({best[1]})")
        return 0
    if best:
        tree, source, tests = best
        if not tests:
            print(f"sauter : depuis l'arbre testé {tree} ({source}), seuls des documents ont changé")
            return 0
        print(f"ciblé : depuis l'arbre testé {tree} ({source}), seuls des tests ont changé — arbre {tip}")
        print("lancer :")
        for t in tests:
            print(t)
        return 0
    if closest:
        tree, source, code = closest
        shown = ", ".join(code[:10]) + (f" (+{len(code) - 10})" if len(code) > 10 else "")
        print(f"suite complète : arbre {tip} ; depuis l'arbre testé le plus proche {tree} ({source}), "
              f"{len(code)} fichier(s) hors tests ont changé : {shown}")
    else:
        print(f"suite complète : arbre {tip} ; aucun arbre testé entièrement réussi dans la KB")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
