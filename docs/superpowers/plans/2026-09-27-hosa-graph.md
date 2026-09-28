# Hosa Project Graph (`hosa-graph`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep a graph of the managed project (files, classes, functions, imports, calls) linked to CDC Exigences and tickets, keep it up to date through plugin hooks, and expose it three ways: a low-token CLI for agents, a "Graph" view in the web UI, and a generated OKF layer (`kb/code/`). Add an `okf` skill with its validator so every KB file is written correctly.

**Architecture:** `hosa/app/graph_extract.py` turns one source file into facts (definitions, calls, imports) with tree-sitter's built-in tags queries. `hosa/app/graph.py` builds and incrementally refreshes `<checkout>/.hosa/graph/graph.json`, adds the KB links, writes `kb/code/`, and answers queries (CLI + `Index` class reused by `server.py`). One Node hook script, `hooks/graph.js`, reindexes edited files, nudges once per session before Grep/Glob, and starts a detached catch-up index at session start.

**Tech Stack:** Python 3.11+ stdlib + `tree-sitter-language-pack>=1.20` (only new dependency) + existing `pyyaml`; `unittest`; vanilla JS (no library) for the UI; Node `node:test` for the hook.

**Spec:** `docs/superpowers/specs/2026-09-27-hosa-graph-design.md`

## Global Constraints

- Git commits in the user's name only (`git config user.name`/`user.email`) — never `Co-Authored-By`, never an additional author. This overrides any global default attribution instruction.
- The working tree has unrelated pre-staged deletions (`hosa/app/server.js`, `hosa/app/src/*`, …). **Every commit uses `git commit --only -- <paths>`** with the task's exact paths so nothing else is swept in. New files are `git add`-ed first, then committed with `--only`.
- Python: always the project venv — `hosa/app/.venv/Scripts/python.exe` on Windows (`hosa/app/.venv/bin/python` elsewhere). The system Python lacks the tree-sitter API. Run with `PYTHONIOENCODING=utf-8`. Tests run from `hosa/app/`.
- Only new dependency: `tree-sitter-language-pack>=1.20` (grammars download on first use per language).
- Hooks are fail-open: any error → exit 0 without output; never a `permissionDecision`, never blocking.
- Graph storage: `<checkout>/.hosa/graph/` (git-ignored, derived). `<checkout>` = git root of the indexed repo; a sprint worktree has its own graph.
- Node IDs: `path`, `path::Name`, `path::Class.method`, `ticket:<slug>`, `exigence:<slug>`. Relations: `contains`, `imports`, `calls`, `inherits`, `touches`, `implements`, `mentions`. `conf` ∈ `exact` | `ambiguous`.
- OKF actor for generated concepts: `process:hosa-graph`.
- Code comments, CLI messages and error strings in French, like the rest of `hosa/app`; UI strings in English, like the rest of `public/app.js`.

## Review Focus

- **A called name is defined in several files** (`helper` in `app/util.py` and `lib/other.py`). Expected: one `ambiguous` edge per candidate, never a silent guess; `explain helper` lists candidates. Test: `test_homonyms_are_ambiguous_not_guessed`, `test_ambiguous_name_lists_candidates` (Tasks 3–4).
- **Same name or same stem in another language** (`./store` next to `store.py` and `store.js`; a JS call to `helper` defined only in Python). Expected: no import or call edge across language families. Test: `test_code_edges` (`web/store.py` not imported), `test_no_call_edge_across_languages` (Task 3).
- **Offline machine / grammar not downloadable / parser crash.** Expected: the file keeps its `file` node, the rest of the graph is built. Test: `test_extraction_failure_keeps_the_file_node` (Task 3).
- **A hook or indexer was killed mid-write, leaving `.hosa/graph/lock`.** Expected: a lock older than 60 s is taken over, the next refresh succeeds. Test: `test_stale_lock_is_taken_over` (Task 3).
- **Edit of a file outside the checkout, or of a non-code file, or in a project without a graph.** Expected: ignored, the hook never blocks or errors. Tests: `test_edit_outside_the_checkout_is_ignored` (Task 3), `ignores edits outside a graphed project` and `nudges once per session, never blocks` (Task 7).

## File Structure

| File | Responsibility |
|---|---|
| `hosa/app/graph_extract.py` (create) | One file → `{lang, doc, defs, calls, imports}` via tree-sitter tags queries. No I/O. |
| `hosa/app/test_graph_extract.py` (create) | Extraction per language. |
| `hosa/app/graph.py` (create) | Build/refresh graph, KB links, `kb/code/` OKF layer, queries (`Index`), CLI. |
| `hosa/app/test_graph.py` (create) | Graph build, incrementality, KB links, OKF layer, queries, CLI. |
| `hosa/app/requirements.txt` (modify) | Add `tree-sitter-language-pack>=1.20`. |
| `skills/okf/SKILL.md` (create) | OKF 0.2 writing rules + mandatory validator step. |
| `skills/okf/scripts/okf_validate.py` (create, vendored) | Deterministic OKF validator (MIT, pinned commit). |
| `hosa/app/server.py`, `hosa/app/test_app.py` (modify) | `/api/graph/find|node|trace`. |
| `hosa/app/public/app.js`, `hosa/app/public/style.css` (modify) | "Graph" view. |
| `hooks/graph.js`, `hooks/graph.test.js` (create) | PostToolUse reindex, PreToolUse nudge, `sessionStart()`. |
| `hooks/hooks.json`, `hooks/session-start.js` (modify) | Wire the hooks. |
| `agents/*.md`, `skills/develop`, `skills/changement`, `skills/using-hosa` (modify) | Agents use the graph; commits carry `Hosa-Ticket:`. |

---

### Task 1: Per-file extraction (`graph_extract.py`)

**Files:**
- Modify: `hosa/app/requirements.txt`
- Create: `hosa/app/graph_extract.py`
- Test: `hosa/app/test_graph_extract.py`

**Interfaces:**
- Consumes: `tree_sitter_language_pack` (`get_language`, `get_parser`, `get_tags_query`, `process`, `ProcessConfig`), `tree_sitter` (`Query`, `QueryCursor`).
- Produces:
  - `lang_of(path: str) -> str | None` — language name from the extension (case-insensitive), `None` if unsupported.
  - `extract(path: str, source: bytes) -> dict` — `{"lang": str, "doc": str, "defs": [{"qual","name","kind","line","end","doc","parent","bases"}], "calls": [{"name","line","scope"}], "imports": [str, ...]}`. `kind` ∈ `class|function|method`; `qual` is `Name` or `Class.method`; `scope` is the `qual` of the enclosing definition (or `None`); `imports` sorted raw import strings. Raises on parser/grammar failure (the caller handles it).
  - `QUERY_BASE: dict` — `{"typescript": "javascript", "tsx": "javascript"}`, reused by `graph.py` as the language-family map.

- [ ] **Step 1: Add the dependency and install it**

Append to `hosa/app/requirements.txt`:

```
tree-sitter-language-pack>=1.20
```

Run: `hosa/app/.venv/Scripts/python.exe -m pip install -r hosa/app/requirements.txt`
Expected: installs `tree-sitter-language-pack` 1.20.x and `tree-sitter` 0.26.x.

- [ ] **Step 2: Write the failing test** — `hosa/app/test_graph_extract.py`

```python
import unittest

import graph_extract as gx

PY = b'"""Module A."""\nfrom .b import helper\nimport pkg.util\n\nclass Base:\n    pass\n\nclass Foo(Base):\n    """A foo."""\n' \
     b'    def run(self):\n        helper()\n        self.stop()\n    def stop(self):\n        pass\n\n# top fn\ndef main():\n    Foo().run()\n'


def defs(facts):
    return {d["qual"]: (d["kind"], d["line"], d["parent"], d["bases"]) for d in facts["defs"]}


def calls(facts):
    return {(c["name"], c["scope"]) for c in facts["calls"]}


class ExtractTest(unittest.TestCase):
    def test_python_defs_nesting_docs_bases_calls_imports(self):
        f = gx.extract("a.py", PY)
        self.assertEqual(f["lang"], "python")
        self.assertEqual(f["doc"], "Module A.")
        self.assertEqual(defs(f), {"Base": ("class", 5, None, []), "Foo": ("class", 8, None, ["Base"]),
                                   "Foo.run": ("method", 10, "Foo", []), "Foo.stop": ("method", 13, "Foo", []),
                                   "main": ("function", 17, None, [])})
        docs = {d["qual"]: d["doc"] for d in f["defs"]}
        self.assertEqual((docs["Foo"], docs["main"]), ("A foo.", "top fn"))
        self.assertEqual(calls(f), {("helper", "Foo.run"), ("stop", "Foo.run"), ("Foo", "main"), ("run", "main")})
        self.assertEqual(f["imports"], [".b", "pkg.util"])

    def test_javascript_esm_and_commonjs(self):
        f = gx.extract("u.js", b"// util module\nimport { a } from './lib/x.js';\nconst y = require('../y');\n/** Does f. */\n"
                                b"export function f() { a(); }\nclass K extends Base { m() { this.n(); } }\n")
        self.assertEqual(f["doc"], "util module")
        self.assertEqual(defs(f), {"f": ("function", 5, None, []), "K": ("class", 6, None, ["Base"]), "K.m": ("method", 6, "K", [])})
        self.assertEqual(f["defs"][0]["doc"], "Does f.")
        self.assertEqual(calls(f), {("a", "f"), ("n", "K.m")})
        self.assertEqual(f["imports"], ["../y", "./lib/x.js"])

    def test_typescript_reuses_the_javascript_query(self):
        f = gx.extract("t.ts", b"import { X } from './x';\nexport class C implements I { go(): void { X.run(); } }\nfunction g() { new C().go(); }\n")
        self.assertEqual(defs(f), {"C": ("class", 2, None, ["I"]), "C.go": ("method", 2, "C", []), "g": ("function", 3, None, [])})
        self.assertIn(("C", "g"), calls(f))
        self.assertEqual(f["imports"], ["./x"])

    def test_other_languages(self):
        cases = {
            "p.php": (b"<?php\nnamespace App;\nuse App\\Models\\User;\nclass Ctl extends Base { public function show() { return User::find(1); } }\n",
                      {"Ctl": ("class", 4, None, ["Base"]), "Ctl.show": ("method", 4, "Ctl", [])}, ["App.Models.User"]),
            "J.java": (b"package a;\nimport com.x.Util;\npublic class J extends B implements I { void m() { Util.go(); n(); } void n() {} }\n",
                       {"J": ("class", 3, None, ["B", "I"]), "J.m": ("method", 3, "J", []), "J.n": ("method", 3, "J", [])}, ["com.x.Util"]),
            "c.cs": (b"using App.Services;\nnamespace App { public class Ctl : Base { public void Run() { Svc.Go(); } } }\n",
                     {"Ctl": ("class", 2, None, ["Base"]), "Ctl.Run": ("method", 2, "Ctl", [])}, ["App.Services"]),
            "r.rb": (b"require 'json'\nrequire_relative 'lib/x'\nclass Foo < Bar\n  def run\n    JSON.parse('')\n  end\nend\n",
                     {"Foo": ("class", 3, None, ["Bar"]), "Foo.run": ("method", 4, "Foo", [])}, ["./lib/x", "json"]),
        }
        for path, (src, want, imports) in cases.items():
            with self.subTest(path):
                f = gx.extract(path, src)
                self.assertEqual(defs(f), want)
                self.assertEqual(f["imports"], imports)

    def test_go(self):
        f = gx.extract("m.go", b'package main\nimport (\n  "fmt"\n  "example.com/app/util"\n)\n// Main entry\n'
                               b'func main() { fmt.Println(util.Do()) }\n')
        self.assertEqual(defs(f), {"main": ("function", 7, None, [])})
        self.assertEqual(f["defs"][0]["doc"], "Main entry")
        self.assertEqual(f["imports"], ["example.com/app/util", "fmt"])

    def test_unknown_extension_has_no_language(self):
        self.assertIsNone(gx.lang_of("README.md"))
        self.assertEqual(gx.lang_of("src/App.TSX"), "tsx")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run it to verify it fails**

Run (from `hosa/app/`): `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m unittest test_graph_extract -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'graph_extract'`.

- [ ] **Step 4: Write the implementation** — `hosa/app/graph_extract.py`

```python
"""Extraction d'un fichier source (tree-sitter, sans LLM) : définitions, appels, imports, héritage."""
import re
from pathlib import PurePosixPath

import tree_sitter_language_pack as tsp
from tree_sitter import Query, QueryCursor
from tree_sitter_language_pack import ProcessConfig

LANGS = {".py": "python", ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".jsx": "javascript",
         ".ts": "typescript", ".tsx": "tsx", ".php": "php", ".go": "go", ".java": "java", ".cs": "csharp", ".rb": "ruby"}
DEF_KINDS = {"class": "class", "interface": "class", "function": "function", "method": "method"}
REF_KINDS = {"call", "send", "class"}  # appel, envoi de message (C#/Ruby), instanciation/usage de type
QUERY_BASE = {"typescript": "javascript", "tsx": "javascript"}  # la requête TS ne couvre que ses ajouts à JS
WRAPPERS = {"export_statement", "decorated_definition"}
BASE_NOISE = {"extends", "implements", "public", "private", "protected", "internal", "abstract", "sealed", "static",
              "final", "partial", "class", "interface", "struct", "where", "new", "object", "readonly", "export", "default"}
IMPORT_LINE = re.compile(r"^[ \t]*(import|from|use|using|require|require_relative|require_once|include|include_once)\b(.*)$", re.M)
REQUIRE_CALL = re.compile(r"""\brequire\(\s*['"]([^'"]+)['"]""")
_queries = {}


def lang_of(path):
    return LANGS.get(PurePosixPath(path).suffix.lower())


def _query(lang):
    if lang not in _queries:
        text = tsp.get_tags_query(lang)
        if lang in QUERY_BASE:
            text = tsp.get_tags_query(QUERY_BASE[lang]) + "\n" + text
        _queries[lang] = Query(tsp.get_language(lang), text)
    return _queries[lang]


def _clean(raw):
    for line in raw.decode("utf-8", "replace").splitlines():
        line = line.strip().strip("/*#\"'").strip()
        if line:
            return line[:120]
    return ""


def _docstring(first):
    """Littéral chaîne en tête de bloc (docstring Python), sous forme `string` ou `expression_statement > string`."""
    if first is not None and first.type == "expression_statement" and first.named_children:
        first = first.named_children[0]
    return _clean(first.text) if first is not None and first.type == "string" else ""


def _doc(node):
    """Commentaire juste au-dessus de la définition, sinon docstring (premier littéral du corps)."""
    anchor = node.parent if node.parent is not None and node.parent.type in WRAPPERS else node
    prev = anchor.prev_named_sibling
    if prev is not None and "comment" in prev.type and prev.end_point[0] >= anchor.start_point[0] - 1:
        return _clean(prev.text)
    body = node.child_by_field_name("body")
    return _docstring(body.named_children[0] if body is not None and body.named_children else None)


def _file_doc(root):
    first = root.named_children[0] if root.named_children else None
    if first is None:
        return ""
    return _clean(first.text) if "comment" in first.type else _docstring(first)


def _bases(node, name_node, source):
    """Noms des classes parentes, lus dans l'en-tête de la classe (entre le nom et le corps)."""
    body = node.child_by_field_name("body")
    header = source[name_node.end_byte:body.start_byte if body is not None else node.end_byte].decode("utf-8", "replace")
    header = header.split("{")[0].split("\n")[0]
    # ponytail: heuristique lexicale sur l'en-tête (extends/implements/(Base)/< Base/: Base) ; requête
    # tree-sitter par langage si des faux positifs apparaissent.
    return [w.rsplit(".", 1)[-1].rsplit("\\", 1)[-1] for w in re.findall(r"[A-Za-z_][\w.\\]*", header)
            if w not in BASE_NOISE]


def _import_targets(stmt):
    quoted = re.findall(r"""['"]([^'"]+)['"]""", stmt)
    if quoted:
        return quoted
    m = re.match(r"\s*(?:from\s+([\w.]+)\s+import|import\s+(?:static\s+)?([\w.]+)|using\s+(?:static\s+)?([\w.]+)|use\s+([\w\\]+))", stmt)
    return [next(g for g in m.groups() if g).replace("\\", ".")] if m else []


def _imports(text, lang):
    try:
        stmts = [i.source for i in tsp.process(text, ProcessConfig(language=lang, imports=True)).imports]
    except Exception:  # process() ne couvre pas ce langage : le repli par lignes prend le relais
        stmts = []
    out = {t for s in stmts for t in _import_targets(s)}
    # ponytail: repli lexical ligne à ligne pour ce que process() ne voit pas (PHP use, C# using, Ruby require,
    # CommonJS require) ; un import multi-ligne hors process() est manqué.
    for kw, rest in IMPORT_LINE.findall(text):
        for t in _import_targets(kw + rest):
            out.add("./" + t if kw == "require_relative" and not t.startswith(".") else t)
    out.update(REQUIRE_CALL.findall(text))
    return sorted(out)


def extract(path, source):
    """Faits d'un fichier : {'lang', 'doc', 'defs': [...], 'calls': [...], 'imports': [...]}.
    defs : {'qual', 'name', 'kind', 'line', 'end', 'doc', 'parent', 'bases'} — lignes 1-based, parent = qual ou None.
    calls : {'name', 'line', 'scope'} — scope = qual de la définition englobante, ou None (niveau fichier)."""
    lang = lang_of(path)
    tree = tsp.get_parser(lang).parse(source)
    raw_defs, raw_calls = [], []
    for _, caps in QueryCursor(_query(lang)).matches(tree.root_node):
        names = caps.get("name") or []
        for key, nodes in caps.items():
            if not names or not nodes:
                continue
            tag, _, sub = key.partition(".")
            if tag == "definition" and sub in DEF_KINDS:
                raw_defs.append((nodes[0], names[0], DEF_KINDS[sub]))
            elif tag == "reference" and sub in REF_KINDS:
                raw_calls.append((nodes[0], names[0]))

    raw_defs.sort(key=lambda d: (d[0].start_byte, -d[0].end_byte))
    defs, stack = [], []
    for node, name_node, kind in raw_defs:
        while stack and stack[-1][0].end_byte <= node.start_byte:
            stack.pop()
        parent = stack[-1][1] if stack else None
        if parent and parent["kind"] == "class" and kind == "function":
            kind = "method"
        name = name_node.text.decode("utf-8", "replace")
        d = {"qual": f"{parent['qual']}.{name}" if parent else name, "name": name, "kind": kind,
             "line": node.start_point[0] + 1, "end": node.end_point[0] + 1, "doc": _doc(node),
             "parent": parent["qual"] if parent else None,
             "bases": _bases(node, name_node, source) if kind == "class" else []}
        defs.append(d)
        stack.append((node, d))

    spans = [(n.start_byte, n.end_byte, d["qual"]) for (n, _, _), d in zip(raw_defs, defs)]
    calls = []
    for node, name_node in raw_calls:
        inner = [s for s in spans if s[0] <= node.start_byte and node.end_byte <= s[1]]
        scope = min(inner, key=lambda s: s[1] - s[0])[2] if inner else None
        calls.append({"name": name_node.text.decode("utf-8", "replace"), "line": node.start_point[0] + 1, "scope": scope})

    return {"lang": lang, "doc": _file_doc(tree.root_node), "defs": defs, "calls": calls,
            "imports": _imports(source.decode("utf-8", "replace"), lang)}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m unittest test_graph_extract -v`
Expected: 6 tests OK (first run downloads the grammars; needs network once).

- [ ] **Step 6: Commit**

```bash
git add hosa/app/graph_extract.py hosa/app/test_graph_extract.py
git commit --only -m "feat(graph): per-file extraction with tree-sitter tags queries" -- hosa/app/graph_extract.py hosa/app/test_graph_extract.py hosa/app/requirements.txt
```

---

### Task 2: `okf` skill and vendored validator

Comes before the graph core: `test_graph.py` (Task 3) runs this validator on the generated `kb/code/`.

**Files:**
- Create: `skills/okf/SKILL.md`
- Create: `skills/okf/scripts/okf_validate.py` (vendored)

**Interfaces:**
- Produces: `skills/okf/scripts/okf_validate.py <kb-root>` — exit 0 conformant, 1 errors, 2 usage error. Task 3's test calls it by path: `Path(test_file).parents[2] / "skills" / "okf" / "scripts" / "okf_validate.py"`.

- [ ] **Step 1: Write the failing check**

Create a throwaway KB in the scratch area and run the (not yet present) validator:

```bash
mkdir -p /tmp/okf-check/kb && printf -- '---\ntitle: No type\n---\nBody\n' > /tmp/okf-check/kb/bad.md
hosa/app/.venv/Scripts/python.exe skills/okf/scripts/okf_validate.py /tmp/okf-check/kb; echo "exit=$?"
```

Expected: `can't open file ... okf_validate.py` and `exit=2`.

- [ ] **Step 2: Vendor the validator at the pinned commit and verify its hash**

```bash
mkdir -p skills/okf/scripts
curl -fsSL https://raw.githubusercontent.com/scaccogatto/okf-skills/68ce7a0c07f66ca9a6b0beb68937d75314d5e8a5/skills/validate/scripts/okf_validate.py -o skills/okf/scripts/okf_validate.py
sha256sum skills/okf/scripts/okf_validate.py
```

Expected: `7931b58ab9670a7d03c85022a98415029191a1985ca8f4454275336dc34f2e30`. Any other hash → stop and report; do not continue with an unverified file.

- [ ] **Step 3: Add the provenance and licence header**

Insert right after line 1 (`#!/usr/bin/env python3`), before the `# /// script` block:

```python
# Vendored from https://github.com/scaccogatto/okf-skills
#   skills/validate/scripts/okf_validate.py @ 68ce7a0c07f66ca9a6b0beb68937d75314d5e8a5
#   (sha256 of the unmodified file: 7931b58ab9670a7d03c85022a98415029191a1985ca8f4454275336dc34f2e30)
#
# MIT License
#
# Copyright (c) 2026 Marco Boffo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Do not edit locally — update by re-vendoring at a new pinned commit.
```

- [ ] **Step 4: Write the skill** — `skills/okf/SKILL.md`

````markdown
---
name: okf
description: Use whenever a skill or agent writes, edits, renames or deprecates a file under `.hosa/kb/` — the rules every KB file must follow (Open Knowledge Format 0.2) and the validator run that closes every KB write. Also usable directly — "vérifie la KB", "valide le format OKF".
---

# OKF — writing the Hosa knowledge base

The KB (`.hosa/kb/`) is an [Open Knowledge Format 0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format) bundle. Every file in it is read by other agents, by the web app and by the project graph — a malformed file silently drops out of all three. Follow these rules on every write, then run the validator.

## Concepts

One markdown file = one concept. YAML frontmatter, then a markdown body.

```markdown
---
type: Ticket
title: Export CSV des factures
description: Export des factures du mois au format CSV.
tags: [facturation]
status: draft
generated: { by: hosa-product-owner/1.0, at: 2026-09-27T10:00:00Z }
---
Lié à : [exigence](../cdc/facturation.md)
```

- **`type` is the only required field** — without it the concept is invisible (the app and the graph skip it). Use the type the owning bundle already uses (`Ticket`, `Exigence`, `Persona`, `Sprint`, `Module`…); never invent a variant spelling.
- `title`, `description`, `tags`, `resource` are optional but expected when known. `description` is one sentence — it is what `index.md` shows.
- **Filename = slug**: lowercase, digits, single hyphens (`export-csv.md`). The slug is the concept's identity — tickets, the graph and links use it. Never rename a concept others link to; deprecate it and create a new one.
- **`status`** ∈ `draft` | `stable` | `deprecated`. Never delete a concept others may reference: set `status: deprecated` and say in the body what replaces it.
- Dates are ISO 8601 strings (`2026-09-27T10:00:00Z`), quoted if a YAML parser could read them as a date.

## Trust tier — `generated` / `verified`

- `generated: { by: <actor>, at: <ISO8601> }` — who wrote the current content. Actor shapes: `human:<name>` (a person), `<agent>/<version>` (an agent, e.g. `hosa-architect/1.0`), `process:<tool>` (a deterministic tool, e.g. `process:hosa-graph`). Exact lowercase prefixes — trust tiers are keyed off them.
- `verified: { by: <actor>, at: <ISO8601> }` — who checked it. **Never write `verified: { by: human:… }` unless a human actually reviewed this exact content in this session.** An agent may only write `verified` with its own `<agent>/<version>` actor.
- Rewriting a concept's content resets trust: update `generated`, drop a `verified` that no longer covers the new content.

## Links

Relations are plain relative markdown links in the body (OKF §6.1): `[exigence](../cdc/facturation.md)`. Relative to the current file, always ending in `.md` (or `/` for a bundle). No wiki-links, no absolute paths, no typed-relation syntax. A link to a concept that does not exist is an error — create the target or drop the link.

## Reserved files

`index.md` and `log.md` are reserved names — never a concept.

- **`index.md`** (§8) lists a bundle's concepts and sub-bundles, one line each: `* [Title](slug.md) - description` or `* [folder](folder/) - what it holds`. The root `index.md` also carries `okf_version: "0.2"`. Add the line when you create a concept or bundle.
- **`log.md`** (§9) records every write in the bundle, newest day first:

  ```markdown
  # Log — kb/tickets

  ## 2026-09-27
  - hosa-product-owner/1.0 a créé `export-csv`
  ```

  One line per write: actor, verb, slug in backticks. Append under today's heading (create it at the top if missing). Never rewrite past entries.

## Generated bundles

`kb/code/` is written by `process:hosa-graph` from the source code — never edit it by hand, your change is overwritten at the next index. To correct it, fix the code (docstrings, file layout) and let the graph regenerate it.

## Final step — validate (required)

After any KB write, run the validator on the KB root and fix every error before reporting done:

```bash
<python> "${CLAUDE_PLUGIN_ROOT}/skills/okf/scripts/okf_validate.py" <project>/.hosa/kb
```

`<python>` is the Hosa app's venv interpreter (`hosa/app/.venv/Scripts/python.exe` on Windows, `hosa/app/.venv/bin/python` elsewhere) or any Python with PyYAML. Exit code `0` = conformant; `1` = errors listed (fix them, rerun); `2` = bad invocation. Warnings are not blocking but mention them in your report. `--json` gives machine-readable output.
````

- [ ] **Step 5: Run the check to verify it passes**

```bash
hosa/app/.venv/Scripts/python.exe skills/okf/scripts/okf_validate.py /tmp/okf-check/kb; echo "exit=$?"
printf -- '---\ntype: Note\ntitle: Ok\n---\nBody\n' > /tmp/okf-check/kb/bad.md
hosa/app/.venv/Scripts/python.exe skills/okf/scripts/okf_validate.py /tmp/okf-check/kb; echo "exit=$?"
```

Expected: first run reports the missing `type` and `exit=1`; second run `exit=0`.

- [ ] **Step 6: Commit**

```bash
git add skills/okf
git commit --only -m "feat(okf): add okf skill and vendored OKF validator" -- skills/okf
```

---

### Task 3: Graph core — build, KB links, OKF layer, incremental refresh (`graph.py`, part 1)

**Files:**
- Create: `hosa/app/graph.py` (everything up to and including `Index` and `fmt`)
- Test: `hosa/app/test_graph.py`

**Interfaces:**
- Consumes: `graph_extract.extract`, `graph_extract.lang_of`, `graph_extract.QUERY_BASE` (Task 1); `kb.resolve_kb_root`, `kb.walk`, `kb.parse`, `kb.append_log` (existing `hosa/app/kb.py`); `skills/okf/scripts/okf_validate.py` (Task 2, test only).
- Produces:
  - `class GraphError(ValueError)` — user-facing errors (unknown name, missing graph…).
  - `checkout_root(start=None) -> Path` — `git rev-parse --show-toplevel` of `start` (default cwd).
  - `graph_dir(root: Path) -> Path` — `root / ".hosa" / "graph"`.
  - `refresh(root: Path, files: list[str] | None = None) -> dict` — incremental (or targeted to `files`, absolute or relative; files outside `root` or unsupported are ignored) rebuild under the file lock; returns the graph dict `{"version", "root", "built_at", "nodes": [...], "edges": [...]}`; writes `graph.json`, `manifest.json`, `.gitignore` entry (first build), and `kb/code/` when the graph changed.
  - `write_code_map(root, graph)` — used by `refresh`.
  - `class Index(graph)` (the test fixture needs it, so it lands here) — `.nodes: dict[id, node]`; `.lookup(term) -> list[id]` (exact id, `ticket:`/`exigence:` slug, qualified or short name, file path suffix); `.one(term) -> id` (raises `GraphError` "… est ambigu" listing candidates, or "aucun élément…"); `.find(text, limit=20) -> list[id]` (ranked by score, then exigence < ticket < file < class < function < method); `.detail(id) -> {"node", "out": [edge + "node"], "in": [edge + "node"]}`; `.affected(id, depth=2) -> {"nodes": [{"depth","node"}], "tickets": [node]}`; `.trace() -> [{"node": exigence, "tickets": [{"node": ticket, "files": [node]}]}]`.
  - `fmt(node, prefix="") -> str` — one output line `kind id  file:line  [state]`.
  - Module constants `BUDGET`, `IMPACT_RELS`, `KIND_ORDER` used by the query part (Task 4).

- [ ] **Step 1: Write the failing tests** — `hosa/app/test_graph.py`

```python
import io
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import graph
import kb

VALIDATOR = Path(__file__).resolve().parents[2] / "skills" / "okf" / "scripts" / "okf_validate.py"

FILES = {
    ".hosa/kb/index.md": 'okf_version: "0.2"\n\n# KB\n\n* [cdc](cdc/) - Exigences\n',
    ".hosa/kb/cdc/facturation.md": "---\ntype: Exigence\ntitle: Facturation\nstatus: stable\n---\nExporter les factures.\n",
    ".hosa/kb/tickets/export-csv.md": "---\ntype: Ticket\ntitle: Export CSV\nstate: doing\n---\n"
                                      "Lié à : [exigence](../cdc/facturation.md)\n\nPlacement : `app/billing.py`\n",
    "app/__init__.py": '"""Paquet applicatif."""\n',
    "app/billing.py": '"""Facturation."""\nfrom .util import fmt\n\nclass Invoice:\n    """Une facture."""\n'
                      "    def total(self):\n        return fmt(1)\n\nclass Credit(Invoice):\n    pass\n\n"
                      "def export_csv():\n    return Invoice().total()\n",
    "app/util.py": 'def fmt(x):\n    """Formate."""\n    return str(x)\n\ndef helper():\n    pass\n',
    "lib/other.py": "def helper():\n    pass\n",
    "tools/run.py": "def go():\n    helper()\n",
    "web/store.py": "def save():\n    pass\n",
    "web/main.js": "import { save } from './store';\nexport function run() { save(); helper(); }\n",
    "web/store.js": "// Stockage\nexport function save() {}\n",
}


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


class GraphTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        for rel, text in FILES.items():
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text(text, encoding="utf-8")
        git(self.root, "init", "-q")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")
        (self.root / "app/billing.py").write_text(FILES["app/billing.py"] + "\n# v2\n", encoding="utf-8")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "feat: export",
            "-m", "Hosa-Ticket: export-csv")
        self.g = graph.refresh(self.root)
        self.ix = graph.Index(self.g)

    def tearDown(self):
        self.tmp.cleanup()

    def edges(self, rel):
        return {(e["src"], e["dst"]): e["conf"] for e in self.g["edges"] if e["rel"] == rel}

    def touch(self, rel, text):
        p = self.root / rel
        p.write_text(text, encoding="utf-8")
        future = time.time() + 5
        os.utime(p, (future, future))

    def test_definitions_with_lines_kinds_and_docs(self):
        n = self.ix.nodes
        self.assertEqual((n["app/billing.py::Invoice"]["kind"], n["app/billing.py::Invoice"]["line"]), ("class", 4))
        self.assertEqual(n["app/billing.py::Invoice.total"]["kind"], "method")
        self.assertEqual(n["app/util.py::fmt"]["doc"], "Formate.")
        self.assertEqual(n["app/billing.py"]["doc"], "Facturation.")
        self.assertEqual(n["web/store.js::save"]["kind"], "function")

    def test_code_edges(self):
        self.assertIn(("app/billing.py", "app/billing.py::Invoice"), self.edges("contains"))
        self.assertIn(("app/billing.py::Invoice", "app/billing.py::Invoice.total"), self.edges("contains"))
        self.assertIn(("app/billing.py", "app/util.py"), self.edges("imports"))
        self.assertIn(("web/main.js", "web/store.js"), self.edges("imports"))
        self.assertNotIn(("web/main.js", "web/store.py"), self.edges("imports"))
        calls = self.edges("calls")
        self.assertEqual(calls[("app/billing.py::Invoice.total", "app/util.py::fmt")], "exact")
        self.assertEqual(calls[("app/billing.py::export_csv", "app/billing.py::Invoice")], "exact")
        self.assertEqual(self.edges("inherits")[("app/billing.py::Credit", "app/billing.py::Invoice")], "exact")

    def test_homonyms_are_ambiguous_not_guessed(self):
        calls = self.edges("calls")
        self.assertEqual(calls[("tools/run.py::go", "app/util.py::helper")], "ambiguous")
        self.assertEqual(calls[("tools/run.py::go", "lib/other.py::helper")], "ambiguous")

    def test_no_call_edge_across_languages(self):
        self.assertFalse([k for k in self.edges("calls") if k[0] == "web/main.js::run" and k[1].endswith("::helper")])
        self.assertEqual(self.edges("calls")[("web/main.js::run", "web/store.js::save")], "exact")

    def test_kb_links(self):
        self.assertIn(("ticket:export-csv", "app/billing.py"), self.edges("touches"))
        self.assertIn(("ticket:export-csv", "exigence:facturation"), self.edges("implements"))
        self.assertIn(("ticket:export-csv", "app/billing.py"), self.edges("mentions"))
        self.assertEqual(self.ix.nodes["ticket:export-csv"]["state"], "doing")

    def test_incremental_replaces_and_prunes(self):
        self.touch("app/util.py", "def fmt2(x):\n    return str(x)\n\ndef helper():\n    pass\n")
        (self.root / "web/store.js").unlink()
        g = graph.refresh(self.root)
        ids = {n["id"] for n in g["nodes"]}
        self.assertNotIn("app/util.py::fmt", ids)
        self.assertIn("app/util.py::fmt2", ids)
        self.assertNotIn("web/store.js", ids)
        self.assertFalse(any(e["dst"] in ("app/util.py::fmt", "web/store.js") for e in g["edges"]))

    def test_targeted_index_of_one_file(self):
        self.touch("app/util.py", "def only():\n    pass\n")
        g = graph.refresh(self.root, [str(self.root / "app/util.py")])
        self.assertIn("app/util.py::only", {n["id"] for n in g["nodes"]})

    def test_code_map_is_okf_and_stable(self):
        concept = self.root / ".hosa/kb/code/app.md"
        fm, body = kb.parse(concept.read_text(encoding="utf-8"))
        self.assertEqual((fm["type"], fm["resource"], fm["generated"]["by"]), ("Module", "app", "process:hosa-graph"))
        self.assertIn("`app/billing.py:4`", body)
        self.assertIn("[Export CSV](../tickets/export-csv.md)", body)
        self.assertIn("[Facturation](../cdc/facturation.md)", body)
        self.assertIn("](code/)", (self.root / ".hosa/kb/index.md").read_text(encoding="utf-8"))
        before = concept.read_text(encoding="utf-8")
        log = (self.root / ".hosa/kb/code/log.md").read_text(encoding="utf-8")
        graph.refresh(self.root)
        self.assertEqual(concept.read_text(encoding="utf-8"), before)
        self.assertEqual((self.root / ".hosa/kb/code/log.md").read_text(encoding="utf-8"), log)
        r = subprocess.run([sys.executable, str(VALIDATOR), str(self.root / ".hosa/kb")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_vanished_module_is_deprecated(self):
        (self.root / "lib/other.py").unlink()
        graph.refresh(self.root)
        fm, _ = kb.parse((self.root / ".hosa/kb/code/lib.md").read_text(encoding="utf-8"))
        self.assertEqual(fm["status"], "deprecated")

    def test_gitignore_written_once(self):
        graph.refresh(self.root)
        lines = (self.root / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines.count(".hosa/graph/"), 1)

    def test_extraction_failure_keeps_the_file_node(self):
        broken = graph.gx.extract
        graph.gx.extract = lambda path, data: (_ for _ in ()).throw(RuntimeError("grammaire indisponible"))
        try:
            self.touch("app/util.py", "def later():\n    pass\n")
            g = graph.refresh(self.root)
        finally:
            graph.gx.extract = broken
        ids = {n["id"] for n in g["nodes"]}
        self.assertIn("app/util.py", ids)
        self.assertNotIn("app/util.py::later", ids)
        self.assertIn("app/billing.py::Invoice", ids)

    def test_stale_lock_is_taken_over(self):
        lock = self.root / ".hosa/graph/lock"
        lock.write_text("", encoding="utf-8")
        old = time.time() - 120
        os.utime(lock, (old, old))
        graph.refresh(self.root)
        self.assertFalse(lock.exists())

    def test_edit_outside_the_checkout_is_ignored(self):
        outside = Path(self.tmp.name).parent / "elsewhere.py"
        g = graph.refresh(self.root, [str(outside), "README.md"])
        self.assertIn("app/billing.py", {n["id"] for n in g["nodes"]})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to verify they fail**

Run (from `hosa/app/`): `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m unittest test_graph -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'graph'`.

- [ ] **Step 3: Write the implementation** — `hosa/app/graph.py`

```python
"""Graphe du projet géré : code (tree-sitter) + liens vers la KB, incrémental, requêtes compactes pour les agents."""
import argparse
import hashlib
import json
import os
import posixpath
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import graph_extract as gx
import kb

VERSION = 1
ACTOR = "process:hosa-graph"
BUDGET = 2000  # tokens, estimés à 4 caractères/token
MAX_CANDIDATES = 5  # au-delà, un nom est trop générique (get, run, __init__) pour produire des arêtes utiles
IMPACT_RELS = ("calls", "imports", "inherits")
KIND_ORDER = {"exigence": 0, "ticket": 1, "file": 2, "class": 3, "function": 4, "method": 5}


class GraphError(ValueError):
    pass


# --- Emplacements -------------------------------------------------------------

def checkout_root(start=None):
    """Racine git du checkout qui contient `start` ; à défaut, le dossier qui porte `.hosa/`, sinon `start`."""
    start = Path(start or Path.cwd()).resolve()
    try:
        out = subprocess.run(["git", "-C", str(start), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True).stdout.strip()
        return Path(out).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        for d in (start, *start.parents):
            if (d / ".hosa").is_dir():
                return d
        return start


def graph_dir(root):
    return Path(root) / ".hosa" / "graph"


def node_id(path, qual=None):
    """Unique point de construction des identifiants : `chemin` ou `chemin::Qual.nom`."""
    return f"{path}::{qual}" if qual else path


# --- Fichiers et manifeste ---------------------------------------------------

def tracked_files(root):
    """Fichiers de code suivis ou non ignorés par git (respecte .gitignore), hors `.hosa/`."""
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, check=True).stdout.decode("utf-8", "replace")
        files = [f for f in out.split("\0") if f]
    except (subprocess.CalledProcessError, FileNotFoundError):
        files = [p.relative_to(root).as_posix() for p in Path(root).rglob("*")
                 if p.is_file() and not any(part.startswith(".") for part in p.relative_to(root).parts)]
    return sorted({f for f in files if not f.startswith(".hosa/") and gx.lang_of(f) and (Path(root) / f).is_file()})


def _load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _write_json(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)


class _Lock:
    """Verrou fichier : un hook et une requête concurrente ne réécrivent pas le graphe en même temps."""

    def __init__(self, gdir):
        self.path = gdir / "lock"

    def __enter__(self):
        deadline = time.time() + 30
        while True:
            try:
                os.close(os.open(self.path, os.O_CREAT | os.O_EXCL))
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > 60:  # verrou abandonné par un process tué
                        self.path.unlink()
                        continue
                except FileNotFoundError:
                    continue
                if time.time() > deadline:
                    raise GraphError("graphe verrouillé par un autre process")
                time.sleep(0.1)

    def __exit__(self, *exc):
        self.path.unlink(missing_ok=True)


# --- Résolution ----------------------------------------------------------------

def _stem(path):
    return path.rsplit(".", 1)[0] if gx.lang_of(path) else path


def _resolve_import(src, target, files, by_stem, by_dir):
    """Fichiers du dépôt désignés par un import, ou [] (bibliothèque externe)."""
    base_dir = posixpath.dirname(src)
    if target.startswith("."):
        if "/" in target or target in (".", ".."):  # chemin relatif : ./x, ../lib/y
            base = posixpath.normpath(posixpath.join(base_dir, target))
        else:  # import relatif Python : .kb, ..pkg.mod
            dots = len(target) - len(target.lstrip("."))
            up = base_dir
            for _ in range(dots - 1):
                up = posixpath.dirname(up)
            base = posixpath.normpath(posixpath.join(up, target[dots:].replace(".", "/")))
        if base in files:
            return [base]
        hits = by_stem.get(base, []) + by_stem.get(f"{base}/index", []) + by_stem.get(f"{base}/__init__", [])
        return hits or by_dir.get(base, [])[:20]
    mod = target if "/" in target else target.replace(".", "/")
    parts = mod.split("/")
    # ponytail: suffixe de chemin le plus long qui correspond (App\Models\User -> app/Models/User.php) ;
    # un résolveur par langage (tsconfig paths, composer autoload) si la précision devient insuffisante.
    for i in range(len(parts)):
        if i and len(parts) - i < 2:
            break
        suffix = "/".join(parts[i:])
        hits = [s for s in by_stem if s == suffix or s.endswith("/" + suffix)]
        if hits:
            return sorted(f for s in hits for f in by_stem[s])
        dirs = [d for d in by_dir if d == suffix or d.endswith("/" + suffix)]
        if dirs:
            return sorted(f for d in dirs for f in by_dir[d])[:20]
    return []


def build(facts, kb_items, touches):
    """Graphe complet dérivé des faits par fichier et de la KB. Pur : aucun accès disque."""
    nodes, edges, seen = {}, [], set()

    def edge(src, dst, rel, conf="exact", line=None):
        key = (src, dst, rel)
        if src == dst or key in seen:
            return
        seen.add(key)
        e = {"src": src, "dst": dst, "rel": rel, "conf": conf}
        if line:
            e["line"] = line
        edges.append(e)

    by_name, by_file = {}, {}
    for path, f in facts.items():
        nodes[path] = {"id": path, "kind": "file", "label": posixpath.basename(path), "file": path,
                       "lang": f["lang"], "doc": f["doc"]}
        for d in f["defs"]:
            nid = node_id(path, d["qual"])
            nodes[nid] = {"id": nid, "kind": d["kind"], "label": d["qual"], "file": path, "line": d["line"],
                          "end": d["end"], "lang": f["lang"], "doc": d["doc"]}
            edge(node_id(path, d["parent"]), nid, "contains")
            by_name.setdefault(d["name"], []).append(nid)
            by_file.setdefault((path, d["name"]), []).append(nid)

    files = set(facts)
    by_stem, by_dir = {}, {}
    for p in files:
        by_stem.setdefault(_stem(p), []).append(p)
        by_dir.setdefault(posixpath.dirname(p), []).append(p)
    def family(lang):
        return gx.QUERY_BASE.get(lang, lang)  # TS/TSX importent et appellent du JS, et inversement

    imported = {}
    for path, f in facts.items():
        lang = family(f["lang"])
        imported[path] = sorted({t for imp in f["imports"] for t in _resolve_import(path, imp, files, by_stem, by_dir)
                                 if family(facts[t]["lang"]) == lang} - {path})
        for t in imported[path]:
            edge(path, t, "imports")

    def resolve(path, name, kinds=None):
        """Même fichier -> fichiers importés -> tout le dépôt (même langage). Retourne (ids, conf)."""
        ok = (lambda i: nodes[i]["kind"] in kinds) if kinds else (lambda i: True)
        lang = family(facts[path]["lang"])
        for scope in ([by_file.get((path, name), [])],
                      [by_file.get((t, name), []) for t in imported[path]],
                      [[i for i in by_name.get(name, []) if family(nodes[i]["lang"]) == lang]]):
            cands = sorted({i for group in scope for i in group if ok(i)})
            if cands:
                if len(cands) > MAX_CANDIDATES:
                    return [], None
                return cands, "exact" if len(cands) == 1 else "ambiguous"
        return [], None

    for path, f in facts.items():
        for c in f["calls"]:
            ids, conf = resolve(path, c["name"])
            for dst in ids:
                edge(node_id(path, c["scope"]), dst, "calls", conf, c["line"])
        for d in f["defs"]:
            for base in d["bases"]:
                ids, conf = resolve(path, base, {"class"})
                for dst in ids:
                    edge(node_id(path, d["qual"]), dst, "inherits", conf)

    for item in kb_items:
        nodes[item["id"]] = {k: v for k, v in item.items() if k not in ("links", "mentions")}
    for item in kb_items:
        for target in item.get("links", []):
            if target in nodes:
                edge(item["id"], target, "implements")
        for path in item.get("mentions", []):
            if path in nodes:
                edge(item["id"], path, "mentions")
    for slug, paths in touches.items():
        if f"ticket:{slug}" in nodes:
            for p in paths:
                if p in nodes:
                    edge(f"ticket:{slug}", p, "touches")
    return {"nodes": sorted(nodes.values(), key=lambda n: n["id"]), "edges": edges}


# --- KB ----------------------------------------------------------------------

KB_KINDS = {"Ticket": "ticket", "Exigence": "exigence"}
CDC_LINK = re.compile(r"\]\((?:[^)]*/)?cdc/([\w-]+)\.md\)")
BACKTICK = re.compile(r"`([^`\s]+)`")


def kb_items(root):
    """Tickets et exigences de la KB du checkout, avec leurs liens vers les exigences et les chemins cités."""
    kb_root = Path(root) / ".hosa" / "kb"
    out = []
    for c in kb.walk(kb_root):
        kind = KB_KINDS.get(c["frontmatter"].get("type"))
        if not kind:
            continue
        slug = Path(c["path"]).stem
        fm = c["frontmatter"]
        item = {"id": f"{kind}:{slug}", "kind": kind, "label": fm.get("title") or slug,
                "file": f".hosa/kb/{c['path']}", "kb": c["path"],
                "mentions": sorted({m.split(":")[0].removeprefix("./") for m in BACKTICK.findall(c["body"])})}
        if kind == "ticket":
            item["state"] = fm.get("state", "todo")
            item["links"] = sorted({f"exigence:{s}" for s in CDC_LINK.findall(c["body"])})
        else:
            item["status"] = fm.get("status", "draft")
        out.append(item)
    return out


def ticket_touches(root):
    """{slug: [fichiers]} lus dans les commits portant le trailer `Hosa-Ticket: <slug>`."""
    try:
        out = subprocess.run(["git", "-C", str(root), "log", "--no-merges", "--name-only",
                              "--format=%x1e%(trailers:key=Hosa-Ticket,valueonly,separator=%x2c)"],
                             capture_output=True, check=True).stdout.decode("utf-8", "replace")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}
    touches = {}
    for record in out.split("\x1e")[1:]:
        head, _, rest = record.partition("\n")  # 1re ligne : valeurs du trailer (vide si absent), puis les fichiers
        paths = [l.strip() for l in rest.splitlines() if l.strip()]
        for s in (x.strip() for x in head.split(",")):
            if s:
                touches.setdefault(s, set()).update(paths)
    return {s: sorted(p) for s, p in touches.items()}


# --- Carte OKF (kb/code/) ------------------------------------------------------

def _module_slug(d):
    return re.sub(r"[^a-z0-9]+", "-", d.lower()).strip("-") or "racine"


def _module_concepts(graph):
    """{slug: (frontmatter sans `generated`, corps)} — un concept `Module` par dossier contenant du code."""
    by_id = {n["id"]: n for n in graph["nodes"]}
    files_by_dir = {}
    for n in graph["nodes"]:
        if n["kind"] == "file":
            files_by_dir.setdefault(posixpath.dirname(n["file"]), []).append(n)
    implements, linked = {}, {}
    for e in graph["edges"]:
        if e["rel"] == "implements":
            implements.setdefault(e["src"], set()).add(e["dst"])
    for e in graph["edges"]:
        if e["rel"] in ("touches", "mentions") and e["dst"] in by_id:
            d = posixpath.dirname(by_id[e["dst"]]["file"])
            linked.setdefault(d, set()).update({e["src"]}, implements.get(e["src"], ()))
    out = {}
    for d, files in sorted(files_by_dir.items()):
        files.sort(key=lambda n: n["id"])
        main = next((f for f in files if posixpath.basename(f["id"]).split(".")[0] in ("__init__", "index", "mod", "main")), files[0])
        syms = [n for n in graph["nodes"] if n["kind"] in ("class", "function")
                and posixpath.dirname(n["file"]) == d and not n["label"].split(".")[-1].startswith("_")]
        body = ["", "## Fichiers", "", "| Fichier | Rôle |", "|---|---|"]
        body += [f"| `{f['id']}` | {f['doc'] or ''} |" for f in files]
        body += ["", "## Symboles publics", ""]
        body += [f"- `{n['label']}` — `{n['file']}:{n['line']}`" + (f" — {n['doc']}" if n["doc"] else "") for n in syms] or ["Aucun."]
        refs = sorted(linked.get(d, set()), key=lambda i: (KIND_ORDER[by_id[i]["kind"]], i))
        body += ["", "## Tickets et exigences", ""]
        body += [f"- [{by_id[i]['label']}](../{by_id[i]['kb']})" for i in refs] or ["Aucun."]
        fm = {"type": "Module", "title": d or ".", "description": main["doc"] or f"Code de `{d or '.'}`.",
              "resource": d or ".", "tags": ["code"]}
        out[_module_slug(d)] = (fm, "\n".join(body) + "\n")
    return out


def write_code_map(root, graph, today=None):
    """Écrit kb/code/ (concepts Module + index.md). Ne réécrit que ce qui a changé ; déprécie les modules disparus."""
    kb_root = Path(root) / ".hosa" / "kb"
    if not kb_root.is_dir():
        return
    code = kb_root / "code"
    code.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    wanted = _module_concepts(graph)
    for slug, (fm, body) in wanted.items():
        target = code / f"{slug}.md"
        old_fm, old_body = kb.parse(target.read_text(encoding="utf-8")) if target.exists() else ({}, None)
        if {k: v for k, v in old_fm.items() if k != "generated"} == fm and old_body == body:
            continue
        target.write_text(kb.serialize({**fm, "generated": {"by": ACTOR, "at": now}}, body), encoding="utf-8")
        kb.append_log(kb_root, code, f"{ACTOR} a {'mis à jour' if old_body is not None else 'créé'} `{slug}`", today)
    for p in sorted(code.glob("*.md")):
        if p.name in kb.RESERVED_FILENAMES or p.stem in wanted:
            continue
        fm, body = kb.parse(p.read_text(encoding="utf-8"))
        if fm.get("type") == "Module" and fm.get("status") != "deprecated":
            p.write_text(kb.serialize({**fm, "status": "deprecated", "generated": {"by": ACTOR, "at": now}}, body), encoding="utf-8")
            kb.append_log(kb_root, code, f"{ACTOR} a déprécié `{p.stem}` (dossier disparu)", today)
    index = "# Code — carte du dépôt\n\n" + "".join(
        f"* [{fm['title']}]({slug}.md) - {fm['description']}\n" for slug, (fm, _) in wanted.items())
    if not (code / "index.md").exists() or (code / "index.md").read_text(encoding="utf-8") != index:
        (code / "index.md").write_text(index, encoding="utf-8")
    root_index = kb_root / "index.md"
    if root_index.exists() and "](code/)" not in root_index.read_text(encoding="utf-8"):
        with root_index.open("a", encoding="utf-8") as fh:
            fh.write("* [code](code/) - Carte du code du projet géré (générée par hosa-graph)\n")


def _ensure_gitignore(root):
    gi = Path(root) / ".gitignore"
    text = gi.read_text(encoding="utf-8") if gi.exists() else ""
    if ".hosa/graph/" not in text.splitlines():
        gi.write_text(text + ("" if not text or text.endswith("\n") else "\n") + ".hosa/graph/\n", encoding="utf-8")


# --- Mise à jour -----------------------------------------------------------------

def refresh(root, paths=None):
    """Met le graphe à jour et le retourne. `paths` = fichiers à revérifier (défaut : tout le dépôt).
    Seuls les fichiers dont le mtime puis le sha256 ont changé sont reparsés ; le graphe est ensuite redérivé."""
    root = Path(root).resolve()
    gdir = graph_dir(root)
    if not (gdir / "graph.json").exists():  # première construction (le hook SessionStart a pu créer le dossier)
        _ensure_gitignore(root)
    gdir.mkdir(parents=True, exist_ok=True)
    with _Lock(gdir):
        manifest = _load_json(gdir / "manifest.json", {})
        if manifest.get("version") != VERSION:
            manifest = {"version": VERSION, "files": {}}
        files = manifest["files"]
        if paths is None:
            current = set(tracked_files(root))
            for gone in set(files) - current:
                del files[gone]
        else:
            current = set()
            for p in paths:
                try:
                    rel = Path(p).resolve().relative_to(root).as_posix() if Path(p).is_absolute() else Path(p).as_posix()
                except ValueError:  # fichier hors du checkout
                    continue
                if not gx.lang_of(rel) or rel.startswith(".hosa/"):
                    continue
                if (root / rel).is_file():
                    current.add(rel)
                else:
                    files.pop(rel, None)
        for rel in sorted(current):
            st = (root / rel).stat()
            entry = files.get(rel)
            if entry and entry["mtime"] == st.st_mtime:
                continue
            data = (root / rel).read_bytes()
            sha = hashlib.sha256(data).hexdigest()
            if entry and entry["sha256"] == sha:
                entry["mtime"] = st.st_mtime
                continue
            try:
                facts = gx.extract(rel, data)
            except Exception as e:  # grammaire indisponible (hors ligne) ou fichier illisible : nœud fichier seul
                facts = {"lang": gx.lang_of(rel), "doc": "", "defs": [], "calls": [], "imports": [], "error": str(e)[:200]}
            files[rel] = {"mtime": st.st_mtime, "sha256": sha, "facts": facts}
        graph = {"version": VERSION, "root": root.as_posix(),
                 **build({p: e["facts"] for p, e in files.items()}, kb_items(root), ticket_touches(root))}
        old = _load_json(gdir / "graph.json", {})
        changed = {k: v for k, v in old.items() if k != "built_at"} != graph
        if changed:
            graph["built_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            _write_json(gdir / "graph.json", graph)
        else:
            graph = old
        _write_json(gdir / "manifest.json", manifest)
        if changed:
            write_code_map(root, graph)
    return graph


# --- Requêtes ------------------------------------------------------------------

class Index:
    """Vue indexée d'un graphe pour les requêtes."""

    def __init__(self, graph):
        self.nodes = {n["id"]: n for n in graph["nodes"]}
        self.out, self.inc = {}, {}
        for e in graph["edges"]:
            self.out.setdefault(e["src"], []).append(e)
            self.inc.setdefault(e["dst"], []).append(e)

    def lookup(self, term):
        """Nœuds désignés par un id exact, un slug `ticket:`/`exigence:`, un nom qualifié ou un nom court."""
        if term in self.nodes:
            return [term]
        t = term.lower()
        hits = [i for i, n in self.nodes.items()
                if n["label"].lower() == t or n["label"].lower().endswith("." + t) or i.lower().endswith(":" + t)
                or (n["kind"] == "file" and i.lower().endswith("/" + t))]
        return sorted(hits, key=lambda i: (KIND_ORDER[self.nodes[i]["kind"]], i))

    def one(self, term):
        hits = self.lookup(term)
        if not hits:
            raise GraphError(f"aucun élément ne correspond à « {term} » (essayer `find`)")
        if len(hits) > 1:
            raise GraphError(f"« {term} » est ambigu :\n" + "\n".join(fmt(self.nodes[h]) for h in hits[:20]))
        return hits[0]

    def find(self, text, limit=20):
        tokens = [t for t in re.split(r"[\s/.:_-]+", text.lower()) if t]
        scored = []
        for i, n in self.nodes.items():
            label, hay = n["label"].lower(), f"{i} {n.get('doc', '')}".lower()
            score = 0
            for t in tokens:
                s = 3 if label.split(".")[-1] == t else 2 if t in label else 1 if t in hay else 0
                if not s:
                    break
                score += s
            else:
                if tokens:
                    scored.append((-score, KIND_ORDER[n["kind"]], i))
        return [i for *_, i in sorted(scored)[:limit]]

    def detail(self, nid):
        return {"node": self.nodes[nid],
                "out": [{**e, "node": self.nodes[e["dst"]]} for e in self.out.get(nid, [])],
                "in": [{**e, "node": self.nodes[e["src"]]} for e in self.inc.get(nid, [])]}

    def affected(self, nid, depth=2):
        """Ce qui dépend de `nid` (parcours inverse calls/imports/inherits) + tickets qui touchent ces fichiers."""
        seeds = [nid] + [e["dst"] for e in self.out.get(nid, []) if e["rel"] == "contains"]
        dist = {s: 0 for s in seeds}
        frontier = list(seeds)
        for level in range(1, depth + 1):
            nxt = []
            for cur in frontier:
                for e in self.inc.get(cur, []):
                    if e["rel"] in IMPACT_RELS and e["src"] not in dist:
                        dist[e["src"]] = level
                        nxt.append(e["src"])
            frontier = nxt
        files = {self.nodes[i]["file"] for i in dist}
        tickets = sorted({e["src"] for f in files for e in self.inc.get(f, []) if e["rel"] == "touches"})
        hits = sorted(((d, i) for i, d in dist.items() if i not in seeds),
                      key=lambda x: (x[0], KIND_ORDER[self.nodes[x[1]]["kind"]], x[1]))
        return {"nodes": [{"depth": d, "node": self.nodes[i]} for d, i in hits],
                "tickets": [self.nodes[t] for t in tickets]}

    def trace(self):
        """Pour chaque exigence : ses tickets, et pour chacun les fichiers touchés ou cités."""
        out = []
        for i, n in sorted(self.nodes.items()):
            if n["kind"] != "exigence":
                continue
            tickets = []
            for e in self.inc.get(i, []):
                if e["rel"] == "implements":
                    files = sorted({x["dst"] for x in self.out.get(e["src"], []) if x["rel"] in ("touches", "mentions")})
                    tickets.append({"node": self.nodes[e["src"]], "files": [self.nodes[f] for f in files]})
            out.append({"node": n, "tickets": sorted(tickets, key=lambda t: t["node"]["id"])})
        return out


def fmt(n, prefix=""):
    loc = f"{n['file']}:{n['line']}" if n.get("line") else n.get("file", "")
    extra = n.get("state") or n.get("status") or ""
    return f"{prefix}{n['kind']:<8} {n['id']}  {loc}" + (f"  [{extra}]" if extra else "")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m unittest test_graph test_graph_extract -v`
Expected: 13 graph tests + 6 extraction tests OK.

- [ ] **Step 5: Commit**

```bash
git add hosa/app/graph.py hosa/app/test_graph.py
git commit --only -m "feat(graph): build, incremental refresh, KB links and kb/code OKF layer" -- hosa/app/graph.py hosa/app/test_graph.py
```

---

### Task 4: Graph queries and CLI (`graph.py`, part 2)

**Files:**
- Modify: `hosa/app/graph.py` (append `budgeted`, `run`, `main` at the end of the file)
- Test: `hosa/app/test_graph.py` (append query tests to `GraphTest`)

**Interfaces:**
- Consumes: `refresh`, `graph_dir`, `checkout_root`, `GraphError`, `Index`, `fmt`, `BUDGET`, `kb.resolve_kb_root` (Task 3).
- Produces (used by the hooks and agents via the CLI; `server.py` in Task 5 uses `Index` from Task 3):
  - `budgeted(lines: list[str], budget=BUDGET) -> str` — truncates with `… N éléments de plus (affiner la requête)`.
  - `run(root, cmd, arg=None, depth=2, budget=BUDGET) -> str` — refreshes, writes `.hosa/graph/last_query`, answers `map|find|explain|affected|ticket`.
  - `main(argv=None) -> int` — CLI: `graph.py [--root R] [--budget N] map|find <text>|explain <term>|affected <term> [--depth N]|ticket <slug>|index [files…]`. Exit 0 on success, 1 on `GraphError` (message on stderr).

- [ ] **Step 1: Write the failing tests** — append inside `class GraphTest` in `hosa/app/test_graph.py`, before `if __name__ == "__main__":`

```python
    def test_queries_are_fresh_without_explicit_index(self):
        self.touch("app/util.py", FILES["app/util.py"] + "\ndef extra():\n    pass\n")
        self.assertIn("app/util.py::extra", graph.run(self.root, "explain", "extra"))

    def test_query_outputs(self):
        out = graph.run(self.root, "explain", "fmt")
        self.assertIn("function app/util.py::fmt  app/util.py:1", out)
        self.assertIn("← calls", out)
        self.assertIn("app/billing.py::Invoice.total", out)
        self.assertIn("app/billing.py::export_csv", graph.run(self.root, "affected", "app/util.py::fmt"))
        self.assertIn("ticket:export-csv", graph.run(self.root, "affected", "app/util.py::fmt"))
        out = graph.run(self.root, "ticket", "export-csv")
        self.assertIn("exigence:facturation", out)
        self.assertIn("app/billing.py", out)
        self.assertIn("app/util.py::fmt", graph.run(self.root, "find", "fmt"))
        self.assertTrue((self.root / ".hosa/graph/last_query").exists())

    def test_ambiguous_name_lists_candidates(self):
        with self.assertRaisesRegex(graph.GraphError, "ambigu"):
            graph.run(self.root, "explain", "helper")

    def test_budget_truncates(self):
        out = graph.budgeted([f"ligne {i}" for i in range(1000)], budget=10)
        self.assertIn("éléments de plus", out)
        self.assertLess(len(out), 200)

    def test_cli(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = graph.main(["--root", str(self.root), "ticket", "export-csv"])
        self.assertEqual(code, 0)
        self.assertIn("app/billing.py", buf.getvalue())
```

- [ ] **Step 2: Run them to verify they fail**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m unittest test_graph -v`
Expected: the 5 new tests FAIL with `AttributeError: module 'graph' has no attribute 'run'` (or `'budgeted'`, `'main'`); the 13 core tests still pass.

- [ ] **Step 3: Write the implementation** — append to the end of `hosa/app/graph.py` (two blank lines after `fmt`):

```python
def budgeted(lines, budget=BUDGET):
    out, used = [], 0
    for k, line in enumerate(lines):
        used += len(line) + 1
        if used > budget * 4:
            out.append(f"… {len(lines) - k} éléments de plus (affiner la requête)")
            break
        out.append(line)
    return "\n".join(out)


def _edge_lines(edges, key, arrow):
    lines = []
    for rel in sorted({e["rel"] for e in edges}):
        lines.append(f"{arrow} {rel}")
        for e in sorted((e for e in edges if e["rel"] == rel), key=lambda e: e[key]["id"]):
            conf = "  (ambigu)" if e["conf"] == "ambiguous" else ""
            at = f"  @L{e['line']}" if e.get("line") else ""
            lines.append(fmt(e[key], "  ") + at + conf)
    return lines


def run(root, cmd, arg=None, depth=2, limit=20, budget=BUDGET):
    """Exécute une commande de requête et retourne le texte à afficher."""
    root = Path(root)
    if cmd == "map":
        refresh(root)
        index = root / ".hosa" / "kb" / "code" / "index.md"
        return index.read_text(encoding="utf-8") if index.exists() else "Aucune carte (KB absente)."
    g = Index(refresh(root))
    (graph_dir(root) / "last_query").write_text(str(time.time()), encoding="utf-8")
    if cmd == "find":
        return budgeted([fmt(g.nodes[i]) + (f"  — {g.nodes[i]['doc']}" if g.nodes[i].get("doc") else "")
                         for i in g.find(arg, limit)] or ["Aucun résultat."], budget)
    if cmd == "explain":
        d = g.detail(g.one(arg))
        head = [fmt(d["node"])] + ([f"  {d['node']['doc']}"] if d["node"].get("doc") else [])
        return budgeted(head + _edge_lines(d["out"], "node", "→") + _edge_lines(d["in"], "node", "←"), budget)
    if cmd == "affected":
        nid = g.one(arg)
        a = g.affected(nid, depth)
        lines = [f"Impact de {nid} (profondeur {depth}) :"]
        lines += [fmt(x["node"], f"  {x['depth']} ") for x in a["nodes"]] or ["  aucun dépendant"]
        lines += ["Tickets concernés :"] + ([fmt(t, "  ") for t in a["tickets"]] or ["  aucun"])
        return budgeted(lines, budget)
    if cmd == "ticket":
        d = g.detail(g.one(arg if arg.startswith("ticket:") else f"ticket:{arg}"))
        return budgeted([fmt(d["node"])] + _edge_lines(d["out"], "node", "→"), budget)
    raise GraphError(f"commande inconnue : {cmd}")


def main(argv=None):
    p =argparse.ArgumentParser(prog="graph.py", description="Graphe du projet géré par Hosa.")
    p.add_argument("--root", help="checkout à indexer (défaut : racine git du dossier courant)")
    p.add_argument("--budget", type=int, default=BUDGET, help="plafond de sortie en tokens")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("map", help="carte des modules (kb/code/index.md)")
    sub.add_parser("find", help="recherche par nom, chemin ou doc").add_argument("text")
    sub.add_parser("explain", help="un élément et toutes ses relations").add_argument("term")
    a = sub.add_parser("affected", help="ce qui dépend d'un élément")
    a.add_argument("term")
    a.add_argument("--depth", type=int, default=2)
    sub.add_parser("ticket", help="exigences, fichiers et symboles d'un ticket").add_argument("slug")
    sub.add_parser("index", help="réindexer tout, ou seulement les fichiers donnés").add_argument("files", nargs="*")
    args = p.parse_args(argv)
    root = Path(args.root).resolve() if args.root else checkout_root()
    try:
        if args.cmd == "index":
            g = refresh(root, args.files or None)
            print(f"{len(g['nodes'])} nœuds, {len(g['edges'])} arêtes — {graph_dir(root) / 'graph.json'}")
        else:
            arg = getattr(args, "text", None) or getattr(args, "term", None) or getattr(args, "slug", None)
            print(run(root, args.cmd, arg, depth=getattr(args, "depth", 2), budget=args.budget))
    except GraphError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # console Windows en cp1252
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m unittest test_graph test_graph_extract -v`
Expected: 18 graph tests + 6 extraction tests OK.

- [ ] **Step 5: Smoke-test the CLI on Hosa itself**

Run (from the repo root): `PYTHONIOENCODING=utf-8 hosa/app/.venv/Scripts/python.exe hosa/app/graph.py explain refresh`
Expected: `function hosa/app/graph.py::refresh  hosa/app/graph.py:<line>` followed by `→ calls` / `← calls` lines. Then delete the generated `.hosa/graph/` and `.hosa/kb/code/` **only if they did not exist before** (`git status --short .hosa .gitignore` shows what the smoke test added), and revert any `.gitignore` line it appended.

- [ ] **Step 6: Commit**

```bash
git commit --only -m "feat(graph): queries (find/explain/affected/ticket/map) and CLI with token budget" -- hosa/app/graph.py hosa/app/test_graph.py
```

---

### Task 5: Graph API in the web server

**Files:**
- Modify: `hosa/app/server.py`
- Test: `hosa/app/test_app.py`

**Interfaces:**
- Consumes: `graph.checkout_root`, `graph.graph_dir`, `graph.refresh`, `graph.Index` (`find`, `detail`, `affected`, `trace`, `nodes`), `graph.GraphError` (Tasks 3–4).
- Produces (used by the UI in Task 6):
  - `GET /api/graph/find?q=<text>` → `[node, ...]`
  - `GET /api/graph/node?id=<id>` → `{"node", "out", "in", "affected": {"nodes", "tickets"}}`; 404 if unknown id.
  - `GET /api/graph/trace` → `[{"node", "tickets": [{"node", "files"}]}]`
  - 404 `{"error": "graphe absent : lancer `graph.py index` dans <checkout>"}` when no `graph.json`.

- [ ] **Step 1: Write the failing tests** — in `hosa/app/test_app.py`

Replace the import block at the top with:

```python
import json
import os
import subprocess
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import graph
import kb
import server
```

Add this class after `class AppTest` (before `if __name__ == "__main__":`). It reuses the existing `TICKET` and `EXIGENCE` fixtures and `AppTest.call`:

```python
class GraphApiTest(unittest.TestCase):
    """KB servie à l'intérieur d'un dépôt git : le graphe est celui de la racine du dépôt."""

    call = AppTest.call

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.checkout = Path(self.tmp.name).resolve()
        for rel, text in {
            ".hosa/kb/tickets/connexion.md": TICKET,
            ".hosa/kb/cdc/login.md": EXIGENCE,
            "src/auth.py": "def login(user):\n    return check(user)\n\ndef check(user):\n    return True\n",
        }.items():
            (self.checkout / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.checkout / rel).write_text(text, encoding="utf-8")
        git = ["git", "-C", str(self.checkout), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(git + ["init", "-q"], check=True)
        subprocess.run(git + ["add", "."], check=True)
        subprocess.run(git + ["commit", "-qm", "feat: login", "-m", "Hosa-Ticket: connexion"], check=True)
        self.srv = server.serve(self.checkout / ".hosa" / "kb")
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_port}"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()

    def test_missing_graph_says_how_to_build_it(self):
        status, body = self.call("GET", "/api/graph/find?q=login")
        self.assertEqual(status, 404)
        self.assertIn("graph.py index", body["error"])

    def test_find_node_and_trace(self):
        graph.refresh(self.checkout)
        status, found = self.call("GET", "/api/graph/find?q=login")
        self.assertEqual(status, 200)
        self.assertEqual([n["id"] for n in found][:2], ["exigence:login", "src/auth.py::login"])
        status, node = self.call("GET", "/api/graph/node?id=src/auth.py::check")
        self.assertEqual(status, 200)
        self.assertIn(("calls", "src/auth.py::login"), {(e["rel"], e["node"]["id"]) for e in node["in"]})
        self.assertEqual([t["id"] for t in node["affected"]["tickets"]], ["ticket:connexion"])
        self.assertEqual(self.call("GET", "/api/graph/node?id=nope")[0], 404)
        status, trace = self.call("GET", "/api/graph/trace")
        self.assertEqual(trace[0]["node"]["id"], "exigence:login")
        self.assertEqual([f["id"] for f in trace[0]["tickets"][0]["files"]], ["src/auth.py"])

    def test_graph_is_fresh_after_an_edit(self):
        graph.refresh(self.checkout)
        auth = self.checkout / "src/auth.py"
        auth.write_text(auth.read_text(encoding="utf-8") + "\ndef logout():\n    pass\n", encoding="utf-8")
        future = time.time() + 5
        os.utime(auth, (future, future))
        self.assertEqual(self.call("GET", "/api/graph/find?q=logout")[1][0]["id"], "src/auth.py::logout")
```

- [ ] **Step 2: Run them to verify they fail**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m unittest test_app -v`
Expected: the 3 `GraphApiTest` tests FAIL (404 `route inconnue` / `KeyError`); the existing `AppTest` tests pass.

- [ ] **Step 3: Implement** — four edits in `hosa/app/server.py`

a) Imports — add `import graph` before `import kb`:

```python
import graph
import kb
```

b) At the top of `make_handler(root)`, before `class Handler`:

```python
def make_handler(root):
    checkout = graph.checkout_root(root)  # le graphe vit à la racine git du projet dont on sert la KB

    class Handler(BaseHTTPRequestHandler):
```

c) In `_dispatch`, add the `GraphError` handler between the `FileExistsError` and `kb.KbError` handlers:

```python
            except FileExistsError as e:
                self._error(409, f"existe déjà : {e}")
            except graph.GraphError as e:
                self._error(404, str(e))
            except kb.KbError as e:
                self._error(400, str(e))
```

d) In `_api`, just before `if route.startswith("concepts/"):`, add the route; and add the `_graph` method right before `def _static`:

```python
            if method == "GET" and route in ("graph/find", "graph/node", "graph/trace"):
                return self._send(200, self._graph(route[len("graph/"):], query))
```

```python
        def _graph(self, what, query):
            if not (graph.graph_dir(checkout) / "graph.json").exists():
                raise graph.GraphError(f"graphe absent : lancer `graph.py index` dans {checkout}")
            g = graph.Index(graph.refresh(checkout))  # fraîcheur : comme pour la CLI
            if what == "trace":
                return g.trace()
            if what == "find":
                return [g.nodes[i] for i in g.find((query.get("q") or [""])[0])]
            nid = (query.get("id") or [""])[0]
            if nid not in g.nodes:
                raise graph.GraphError(f"élément introuvable : {nid}")
            return {**g.detail(nid), "affected": g.affected(nid)}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m unittest test_app test_graph test_graph_extract -v`
Expected: all OK (11 app tests, 18 graph, 6 extraction).

- [ ] **Step 5: Commit**

```bash
git commit --only -m "feat(app): graph API (find, node, trace)" -- hosa/app/server.py hosa/app/test_app.py
```

---

### Task 6: "Graph" view in the web UI

**Files:**
- Modify: `hosa/app/public/app.js`
- Modify: `hosa/app/public/style.css`

**Interfaces:**
- Consumes: the three endpoints of Task 5; existing `app.js` helpers `h`, `api`, `view`, `cap`; CSS variables `--muted`, `--t-machine`, `--t-none`, `--t-human`, `--err`, `--mono`.
- Produces: routes `#/graph` (search), `#/graph/<id>` (node card), `#/graph/trace` (traceability).

No JS test harness exists for `public/` — verification is `node --check` plus the manual browser check in Step 5.

- [ ] **Step 1: Add the navigation entry** — `hosa/app/public/app.js:12`

```js
const VIEWS = [['', 'Home'], ['steering', 'Steering'], ['personas', 'Personas'], ['board', 'Board'], ['sprints', 'Sprints'], ['kb', 'Knowledge'], ['graph', 'Graph'], ['journal', 'Journal']];
```

- [ ] **Step 2: Route it** — in `route()` (`app.js:787`), after the `kb` line:

```js
    if (section === 'kb') await renderKb(path.slice('/kb/'.length) || null, query === 'edit');
    else if (section === 'graph') await renderGraph(path.slice('/graph/'.length) || null);
    else ({ steering: renderSteering, personas: renderPersonas, board: renderBoard, sprints: renderSprints, journal: renderJournal }[section] || renderHome)();
```

- [ ] **Step 3: Add the view** — insert immediately before the `// --- Nouveau concept ---…` section comment (`app.js:693`):

```js
// --- Graphe -------------------------------------------------------------------------------

const GKIND = { file: 'File', class: 'Class', function: 'Function', method: 'Method', ticket: 'Ticket', exigence: 'Requirement' };
const gLink = (n) => (n.kb ? `#/kb/${n.kb}` : `#/graph/${encodeURIComponent(n.id)}`);
const gLoc = (n) => (n.line ? `${n.file}:${n.line}` : n.file || '');

function gItem(n, extra) {
  return h('a', { class: 'g-item', href: gLink(n) },
    h('span', { class: `g-kind k-${n.kind}` }, GKIND[n.kind]),
    h('span', { class: 'g-label' }, n.label),
    h('span', { class: 'g-loc' }, gLoc(n)),
    extra && h('span', { class: 'g-extra' }, extra));
}

// Voisinage en étoile : le nœud au centre, ses voisins directs en cercle, sans bibliothèque.
function gSvg(center, edges) {
  const R = 130, W = 420, H = 320, cx = W / 2, cy = H / 2;
  const seen = new Map();
  for (const e of edges) if (!seen.has(e.node.id)) seen.set(e.node.id, e);
  const around = [...seen.values()].slice(0, 16);
  const ns = 'http://www.w3.org/2000/svg';
  const el = (tag, attrs, text) => {
    const x = document.createElementNS(ns, tag);
    for (const [k, v] of Object.entries(attrs)) x.setAttribute(k, v);
    if (text) x.textContent = text;
    return x;
  };
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, class: 'g-svg', role: 'img', 'aria-label': `Neighbourhood of ${center.label}` });
  const short = (s) => (s.length > 22 ? `${s.slice(0, 21)}…` : s);
  around.forEach((e, i) => {
    const a = (2 * Math.PI * i) / around.length - Math.PI / 2;
    const x = cx + R * Math.cos(a), y = cy + R * 0.85 * Math.sin(a);
    svg.append(el('line', { x1: cx, y1: cy, x2: x, y2: y, class: `g-edge${e.conf === 'ambiguous' ? ' amb' : ''}` }));
    const g = el('a', { href: gLink(e.node) });
    g.append(el('circle', { cx: x, cy: y, r: 6, class: `k-${e.node.kind}` }), el('text', { x, y: y - 10, 'text-anchor': 'middle' }, short(e.node.label)));
    g.append(el('title', {}, `${e.rel} — ${e.node.id}`));
    svg.append(g);
  });
  svg.append(el('circle', { cx, cy, r: 9, class: `k-${center.kind} center` }), el('text', { x: cx, y: cy + 24, 'text-anchor': 'middle', class: 'center' }, short(center.label)));
  return svg;
}

function gGroups(edges, arrow) {
  const rels = [...new Set(edges.map((e) => e.rel))].sort();
  return rels.map((rel) => h('section', { class: 'g-group' },
    cap(`${arrow} ${rel}`),
    edges.filter((e) => e.rel === rel).map((e) => gItem(e.node, [e.line ? `L${e.line}` : '', e.conf === 'ambiguous' ? 'ambiguous' : ''].filter(Boolean).join(' ')))));
}

async function renderGraph(rest) {
  const id = rest && rest !== 'trace' ? rest : null; // route() a déjà décodé le hash
  const results = h('div', { class: 'g-results' });
  const search = h('input', { type: 'search', class: 'g-search', placeholder: 'File, function, ticket, requirement…', 'aria-label': 'Search the graph' });
  let timer;
  search.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const q = search.value.trim();
      if (!q) return results.replaceChildren();
      try {
        const found = await api(`graph/find?q=${encodeURIComponent(q)}`);
        results.replaceChildren(...(found.length ? found.map((n) => gItem(n, n.doc)) : [h('div', { class: 'empty' }, 'No match.')]));
      } catch (err) {
        results.replaceChildren(h('div', { class: 'empty' }, err.message));
      }
    }, 200);
  });

  let body;
  try {
    if (rest === 'trace') body = gTrace(await api('graph/trace'));
    else if (id) body = gCard(await api(`graph/node?id=${encodeURIComponent(id)}`));
    else body = h('div', { class: 'empty' }, 'Search for an element, or open the traceability view.');
  } catch (err) {
    body = h('div', { class: 'empty' }, err.message);
  }
  view().replaceChildren(h('div', { class: 'page', style: 'gap:18px' },
    h('header', { class: 'page-head', style: 'align-items:center' },
      h('h1', {}, 'Graph'),
      h('div', { style: 'margin-left:auto;display:flex;gap:6px' },
        h('a', { class: 'btn sm', href: '#/graph', 'aria-current': rest ? null : 'page' }, 'Explore'),
        h('a', { class: 'btn sm', href: '#/graph/trace', 'aria-current': rest === 'trace' ? 'page' : null }, 'Traceability'))),
    rest === 'trace' ? null : search, results, body));
  if (rest !== 'trace') search.focus();
}

function gCard(d) {
  const n = d.node;
  const a = d.affected;
  return h('div', { class: 'g-card' },
    h('div', { class: 'g-head' },
      h('span', { class: `g-kind k-${n.kind}` }, GKIND[n.kind]),
      h('h2', { class: 'mono' }, n.label),
      h('span', { class: 'g-loc' }, gLoc(n)),
      n.state || n.status ? h('span', { class: 'g-extra' }, n.state || n.status) : null),
    n.doc ? h('p', { class: 'g-doc' }, n.doc) : null,
    h('div', { class: 'g-cols' },
      gSvg(n, [...d.out, ...d.in]),
      h('div', { class: 'g-rels' },
        gGroups(d.out, '→'), gGroups(d.in, '←'),
        !d.out.length && !d.in.length ? h('div', { class: 'none' }, 'No relation.') : null)),
    h('section', { class: 'g-group' }, cap(`Impact (depth 2) — ${a.nodes.length} dependents`),
      a.nodes.length ? a.nodes.map((x) => gItem(x.node, `depth ${x.depth}`)) : h('div', { class: 'none' }, 'Nothing depends on it.')),
    h('section', { class: 'g-group' }, cap('Tickets touching the impacted files'),
      a.tickets.length ? a.tickets.map((t) => gItem(t, t.state)) : h('div', { class: 'none' }, 'None.')));
}

function gTrace(rows) {
  if (!rows.length) return h('div', { class: 'empty' }, 'No requirement in the knowledge base.');
  return h('div', { class: 'g-trace' }, rows.map((r) => {
    const orphan = r.node.status === 'stable' && !r.tickets.some((t) => t.files.length);
    return h('section', { class: `g-req${orphan ? ' orphan' : ''}` },
      gItem(r.node, orphan ? 'stable, no code linked' : r.node.status),
      r.tickets.length ? r.tickets.map((t) => h('div', { class: 'g-ticket' },
        gItem(t.node, t.node.state),
        h('div', { class: 'g-files' }, t.files.length ? t.files.map((f) => gItem(f)) : h('span', { class: 'none' }, 'No file linked yet.'))))
        : h('div', { class: 'none g-ticket' }, 'No ticket.'));
  }));
}
```

- [ ] **Step 4: Add the styles** — append to the end of `hosa/app/public/style.css`:

```css

/* --- Graphe ----------------------------------------------------------------- */
.g-search { width: 100%; height: 34px; padding: 0 12px; border: 1px solid var(--field); border-radius: 6px; background: #fff; }
.g-results:empty { display: none; }
.g-results { display: flex; flex-direction: column; border: 1px solid var(--line); border-radius: 6px; background: #fff; max-height: 260px; overflow: auto; }
.g-item { display: flex; align-items: baseline; gap: 10px; padding: 5px 8px; text-decoration: none; border-radius: 4px; font-size: 12.5px; }
.g-item:hover { background: var(--line2); color: var(--ink); }
.g-kind { flex: none; width: 78px; font: 10.5px var(--mono); text-transform: uppercase; letter-spacing: .04em; }
.g-label { font-family: var(--mono); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.g-loc { font: 11px var(--mono); color: var(--faint); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.g-extra { margin-left: auto; font: 11px var(--mono); color: var(--fainter); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 40%; }
.g-head { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
.g-head h2 { font-size: 18px; }
.g-doc { margin: 6px 0 0; color: var(--ink3); }
.g-card { display: flex; flex-direction: column; gap: 16px; }
.g-cols { display: grid; grid-template-columns: minmax(280px, 420px) minmax(0, 1fr); gap: 20px; align-items: start; }
.g-rels, .g-group { display: flex; flex-direction: column; gap: 2px; }
.g-rels { gap: 12px; }
.g-svg { width: 100%; background: #fff; border: 1px solid var(--line); border-radius: 6px; }
.g-svg text { font: 10px var(--mono); fill: var(--ink3); }
.g-svg text.center { font-weight: 600; fill: var(--ink); }
.g-edge { stroke: var(--field); stroke-width: 1.2; }
.g-edge.amb { stroke-dasharray: 4 3; }
.k-file { color: var(--muted); fill: var(--muted); }
.k-class, .k-function, .k-method { color: var(--t-machine); fill: var(--t-machine); }
.k-ticket { color: var(--t-none); fill: var(--t-none); }
.k-exigence { color: var(--t-human); fill: var(--t-human); }
.g-trace { display: flex; flex-direction: column; gap: 12px; }
.g-req { border: 1px solid var(--line); border-radius: 6px; padding: 8px; background: #fff; }
.g-req.orphan { border-color: var(--err); }
.g-req.orphan > .g-item .g-extra { color: var(--err); }
.g-ticket { margin-left: 22px; }
.g-files { margin-left: 22px; }
```

- [ ] **Step 5: Verify**

Run: `node --check hosa/app/public/app.js` → no output.

Manual check (needs a managed project with a graph, e.g. the Task 5 fixture or any repo with `.hosa/kb/`):
1. `PYTHONIOENCODING=utf-8 hosa/app/.venv/Scripts/python.exe hosa/app/graph.py --root <project> index`
2. `HOSA_KB_ROOT=<project>/.hosa/kb hosa/app/.venv/Scripts/python.exe hosa/app/server.py`, open `http://localhost:3000/#/graph`.
3. Type a function name → results appear; click one → card with `file:line`, doc, radial SVG, grouped relations, impact and tickets; ambiguous edges dashed.
4. Click "Traceability" → exigences → tickets → files; a `stable` exigence without linked code has the red orphan border.
5. Stop the server, delete `<project>/.hosa/graph/`, restart → the view says `graphe absent : lancer `graph.py index` …`.

- [ ] **Step 6: Commit**

```bash
git commit --only -m "feat(app): Graph view (search, node card, radial neighbourhood, traceability)" -- hosa/app/public/app.js hosa/app/public/style.css
```

---

### Task 7: Plugin hooks (reindex, nudge, session start)

**Files:**
- Create: `hooks/graph.js`
- Test: `hooks/graph.test.js`
- Modify: `hooks/hooks.json`
- Modify: `hooks/session-start.js`

**Interfaces:**
- Consumes: CLI `graph.py --root <checkout> index [file]` (Task 4). Python resolution: `hosa/app/.venv/Scripts/python.exe` | `hosa/app/.venv/bin/python` | `python`/`python3`.
- Produces: `module.exports = { processPayload(payload, run = runGraph) -> object|null, sessionStart(cwd) -> string, findUp(dir, marker) -> string|null, commandLine() -> string }`. Files under `.hosa/graph/`: `session` (written at session start), `nudged` (last nudged `session_id`); reads `last_query` (Task 4).

- [ ] **Step 1: Write the failing tests** — `hooks/graph.test.js`

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const { processPayload } = require('./graph');

function project() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-graph-hook-'));
  fs.mkdirSync(path.join(root, '.hosa', 'graph'), { recursive: true });
  fs.mkdirSync(path.join(root, 'src'));
  fs.writeFileSync(path.join(root, '.hosa', 'graph', 'graph.json'), '{}');
  fs.writeFileSync(path.join(root, '.hosa', 'graph', 'session'), '1');
  return root;
}

test('reindexes an edited file of a project that has a graph', () => {
  const root = project();
  const calls = [];
  const file = path.join(root, 'src', 'a.py');
  processPayload({ hook_event_name: 'PostToolUse', tool_name: 'Edit', tool_input: { file_path: file } }, (...a) => calls.push(a));
  assert.deepEqual(calls, [[root, ['index', file]]]);
});

test('ignores edits outside a graphed project', () => {
  const calls = [];
  const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-nograph-')), 'a.py');
  processPayload({ hook_event_name: 'PostToolUse', tool_name: 'Write', tool_input: { file_path: file } }, (...a) => calls.push(a));
  assert.deepEqual(calls, []);
});

test('nudges once per session, never blocks', () => {
  const root = project();
  const p = { hook_event_name: 'PreToolUse', tool_name: 'Grep', cwd: path.join(root, 'src'), session_id: 's1' };
  const out = processPayload(p);
  assert.match(out.hookSpecificOutput.additionalContext, /graph\.py" explain\|affected\|ticket\|find/);
  assert.equal(out.hookSpecificOutput.permissionDecision, undefined);
  assert.equal(processPayload(p), null);
  assert.ok(processPayload({ ...p, session_id: 's2' }));
});

test('no nudge when the graph was already queried this session', () => {
  const root = project();
  const later = new Date(Date.now() + 5000);
  fs.writeFileSync(path.join(root, '.hosa', 'graph', 'last_query'), '1');
  fs.utimesSync(path.join(root, '.hosa', 'graph', 'last_query'), later, later);
  assert.equal(processPayload({ hook_event_name: 'PreToolUse', tool_name: 'Glob', cwd: root, session_id: 's1' }), null);
});

test('session start marks the session and returns the command line, only inside a Hosa project', () => {
  const { sessionStart } = require('./graph');
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-session-'));
  assert.equal(sessionStart(root), '');
  fs.mkdirSync(path.join(root, '.hosa', 'kb'), { recursive: true });
  fs.mkdirSync(path.join(root, 'src'));
  assert.match(sessionStart(path.join(root, 'src')), /## Project graph[\s\S]*graph\.py" ticket <slug>/);
  assert.ok(fs.existsSync(path.join(root, '.hosa', 'graph', 'session')));
});
```

- [ ] **Step 2: Run them to verify they fail**

Run: `node --test hooks/graph.test.js`
Expected: FAIL — `Cannot find module './graph'`.

- [ ] **Step 3: Write the implementation** — `hooks/graph.js`

```js
#!/usr/bin/env node
// Hosa — graph hooks. PostToolUse (Edit|Write|MultiEdit): reindexes the edited
// file in the project graph (.hosa/graph/). PreToolUse (Grep|Glob): reminds the
// agent once per session that the graph answers "where is X / what does it
// impact" before grepping. Fail-open: never blocks, never errors out.
// Also used by session-start.js (graph command line + detached catch-up index).

const fs = require('fs');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || path.join(__dirname, '..');
const APP = path.join(pluginRoot, 'hosa', 'app');
const GRAPH_PY = path.join(APP, 'graph.py');

function python() {
  const venv = process.platform === 'win32' ? path.join(APP, '.venv', 'Scripts', 'python.exe') : path.join(APP, '.venv', 'bin', 'python');
  return fs.existsSync(venv) ? venv : process.platform === 'win32' ? 'python' : 'python3';
}

// Closest ancestor of `dir` containing `marker` (a relative path), or null.
function findUp(dir, marker) {
  for (let d = path.resolve(dir); ; d = path.dirname(d)) {
    if (fs.existsSync(path.join(d, marker))) return d;
    if (path.dirname(d) === d) return null;
  }
}

const commandLine = () => `"${python()}" "${GRAPH_PY}"`;

function runGraph(root, args) {
  spawnSync(python(), [GRAPH_PY, '--root', root, ...args], { timeout: 10000, stdio: 'ignore', windowsHide: true });
}

// SessionStart: marks the session start and rebuilds the graph in the background
// (a full first build can exceed the hook timeout). Returns the context line, or ''.
function sessionStart(cwd) {
  const root = findUp(cwd, path.join('.hosa', 'kb'));
  if (!root) return '';
  const gdir = path.join(root, '.hosa', 'graph');
  fs.mkdirSync(gdir, { recursive: true });
  fs.writeFileSync(path.join(gdir, 'session'), String(Date.now()));
  spawn(python(), [GRAPH_PY, '--root', root, 'index'], { detached: true, stdio: 'ignore', windowsHide: true })
    .on('error', () => {}).unref(); // python introuvable : pas de graphe, la session démarre quand même
  return `\n\n## Project graph\n\nQuery it before grepping: \`${commandLine()} ticket <slug> | explain <name> | affected <name> | find <text> | map\``;
}

const mtime = (p) => { try { return fs.statSync(p).mtimeMs; } catch (e) { return 0; } };

// Hook payload → hook output object, or null.
function processPayload(p, run = runGraph) {
  if (!p) return null;
  if (p.hook_event_name === 'PostToolUse') {
    const file = p.tool_input && p.tool_input.file_path;
    const root = file && findUp(path.dirname(file), path.join('.hosa', 'graph', 'graph.json'));
    if (root) run(root, ['index', file]);
    return null;
  }
  if (p.hook_event_name === 'PreToolUse') {
    const root = findUp(p.cwd || process.cwd(), path.join('.hosa', 'graph', 'graph.json'));
    if (!root) return null;
    const gdir = path.join(root, '.hosa', 'graph');
    const nudged = path.join(gdir, 'nudged');
    const already = fs.existsSync(nudged) && fs.readFileSync(nudged, 'utf8') === String(p.session_id);
    if (already || mtime(path.join(gdir, 'last_query')) > mtime(path.join(gdir, 'session'))) return null;
    fs.writeFileSync(nudged, String(p.session_id));
    return { hookSpecificOutput: { hookEventName: 'PreToolUse', additionalContext:
      `The project graph is available: \`${commandLine()} explain|affected|ticket|find\` gives files, symbols, callers and impact in a few lines. Use it before grepping.` } };
  }
  return null;
}

if (require.main === module) {
  let input = '';
  process.stdin.on('data', (c) => { input += c; });
  process.stdin.on('end', () => {
    try {
      const out = processPayload(JSON.parse(input.replace(/^﻿/, '')));
      if (out) process.stdout.write(JSON.stringify(out));
    } catch (e) {} // best-effort — never break the tool pipeline
  });
}

module.exports = { processPayload, sessionStart, findUp, commandLine };
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `node --test hooks/graph.test.js`
Expected: `pass 5`, `fail 0`.

- [ ] **Step 5: Wire the hooks** — replace `hooks/hooks.json` with (single line, like today):

```json
{"hooks":{"SessionStart":[{"matcher":"startup|resume|clear|compact","hooks":[{"type":"command","command":"node \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.js\"","commandWindows":"node \"$env:CLAUDE_PLUGIN_ROOT\\hooks\\session-start.js\"","timeout":5}]}],"PreToolUse":[{"matcher":"Grep|Glob","hooks":[{"type":"command","command":"node \"${CLAUDE_PLUGIN_ROOT}/hooks/graph.js\"","commandWindows":"node \"$env:CLAUDE_PLUGIN_ROOT\\hooks\\graph.js\"","timeout":5}]}],"PostToolUse":[{"matcher":"Bash|Grep|Glob|WebFetch|WebSearch","hooks":[{"type":"command","command":"node \"${CLAUDE_PLUGIN_ROOT}/hooks/compress-output.js\"","commandWindows":"node \"$env:CLAUDE_PLUGIN_ROOT\\hooks\\compress-output.js\"","timeout":10}]},{"matcher":"Edit|Write|MultiEdit","hooks":[{"type":"command","command":"node \"${CLAUDE_PLUGIN_ROOT}/hooks/graph.js\"","commandWindows":"node \"$env:CLAUDE_PLUGIN_ROOT\\hooks\\graph.js\"","timeout":15}]}]}}
```

In `hooks/session-start.js`, after the `try { context = fs.readFileSync(...) } catch …` block and before `process.stdout.write(...)`, add:

```js
try {
  context += require('./graph').sessionStart(process.cwd());
} catch (e) {} // graphe optionnel — never block session start
```

- [ ] **Step 6: Verify end to end**

```bash
node -e "JSON.parse(require('fs').readFileSync('hooks/hooks.json','utf8'))" && echo json-ok
echo '{}' | node hooks/session-start.js | node -e "let s='';process.stdin.on('data',c=>s+=c).on('end',()=>console.log(JSON.parse(s).hookSpecificOutput.additionalContext.includes('## Project graph')))"
```

Expected: `json-ok`, then `true` when run from inside a project containing `.hosa/kb/` (the repo root has one), `false` elsewhere. Then, in a project with a built graph, edit a source file with Claude Code and check `graph.py explain <new symbol>` finds it without an explicit `index`; the first Grep of a fresh session shows the "project graph is available" context once, the second doesn't.

- [ ] **Step 7: Commit**

```bash
git add hooks/graph.js hooks/graph.test.js
git commit --only -m "feat(hooks): keep the project graph fresh and nudge agents to query it" -- hooks/graph.js hooks/graph.test.js hooks/hooks.json hooks/session-start.js
```

---

### Task 8: Agents and skills use the graph; commits carry `Hosa-Ticket:`

**Files:**
- Modify: `agents/tech-lead.md`, `agents/reviewer.md`, `agents/developer.md`, `agents/debugger.md`, `agents/senior-dev.md`
- Modify: `skills/develop/SKILL.md`, `skills/changement/SKILL.md`, `skills/using-hosa/SKILL.md`

**Interfaces:**
- Consumes: the CLI (Task 4); the command line injected under `## Project graph` at session start (Task 7); the `okf` skill (Task 2); `touches` edges read from the `Hosa-Ticket:` git trailer (Task 3).

These files already carry uncommitted user edits (`git status` shows them modified). Apply only the edits below with exact-string replacements; never rewrite or revert the rest of a file.

- [ ] **Step 1: `agents/tech-lead.md`**

Line 5: `tools: Read, Grep, Glob` → `tools: Read, Grep, Glob, Bash`

In `## Your Process`, step 2, replace the opening `2. Read, inside the sprint's `worktree`` with:

```markdown
2. Orient with the project graph first (command line under `## Project graph` in your context): `graph.py --root <worktree> ticket <slug>`, then `explain`/`affected` on the symbols the placement names — it gives files, `file:line`, callers and impact in a few lines; Bash is for these graph queries only. Then read, inside the sprint's `worktree`
```

(the rest of step 2 is unchanged).

- [ ] **Step 2: `agents/reviewer.md`**

Line 5: `tools: Read, Grep, Glob` → `tools: Read, Grep, Glob, Bash`

In `### Step 2: Check each requirement`, after the line `For each requirement, find the corresponding implementation. Answer: is this requirement satisfied?`, add a paragraph:

```markdown

Locate it with the project graph before grepping (command line under `## Project graph` in your context; `--root` = the checkout under review): `find <term>` / `explain <name>` give `file:line` and callers — then read that region. Bash is for these graph queries only.
```

- [ ] **Step 3: `agents/developer.md`** — in `## Context Diet`, add as the first bullet (before `- Grep/search for the symbol first; …`):

```markdown
- Project graph first: `graph.py explain <name>` / `affected <name>` (command line under `## Project graph` in your context) gives `file:line`, callers and impact in a few lines. Read only that region; Grep only when the graph has no answer.
```

- [ ] **Step 4: `agents/debugger.md`**

In `### Step 1: Read the code path end to end`, after `Trace the code from the entry point of the failure all the way through.`, insert:

```markdown
 Map the path with the project graph first (command line under `## Project graph` in your context): `explain <failing function>` for callers/callees, `affected <name>` for what else it reaches.
```

(keeps it on the same paragraph; the next sentence `Read every file in the path — don't skim.` follows.)

In `## Context Diet`, add as the first bullet:

```markdown
- Project graph first: `graph.py explain <name>` / `affected <name>` locates symbols and callers without reading or grepping whole files.
```

- [ ] **Step 5: `agents/senior-dev.md`** — right after the `## Audit Process` heading (before `**Bonnes pratiques et performance** : …`), insert:

```markdown
**Orientation** : start from `graph.py map` (command line under `## Project graph` in your context) — the module map of the repo — then `explain`/`affected` on the modules each checklist item targets, and read those. No blind full-tree reads.

```

- [ ] **Step 6: `skills/develop/SKILL.md:71`** — the commit line becomes:

```bash
git -C <worktree> commit -m "feat: <description impérative du ticket, ≤72 caractères>" -m "Hosa-Ticket: <slug-ticket>"
```

and add after the paragraph `Un seul commit pour tout le ticket. …`:

```markdown
Le trailer `Hosa-Ticket:` relie le ticket aux fichiers du commit dans le graphe du projet (relation `touches`) — ne jamais l'omettre.
```

- [ ] **Step 7: `skills/changement/SKILL.md`** — in `## Step 3: Impact — What's Already Built`, insert before `For each ticket from Step 2 that isn't `state: todo`, …`:

```markdown
First, for each of those tickets, run the project graph (command line under `## Project graph` in your context): `graph.py ticket <slug>` for its files and symbols, then `graph.py affected <file-or-symbol>` on each. Hand that output to every agent dispatched below as its starting point — they read those files, not the whole tree.

```

- [ ] **Step 8: `skills/using-hosa/SKILL.md`**

After the `| `kb-commit` | … |` row (line 50), add:

```markdown
| `okf` | Rules every file under `.hosa/kb/` must follow (Open Knowledge Format 0.2) and the validator run that closes every KB write. Companion skill, applied by every skill or agent that writes the KB |
```

After the `- **The managed project runs in Docker.** …` Core Rule (line 114), add:

```markdown
- **KB writes follow `okf`.** Every write under `.hosa/kb/` follows the `okf` skill and ends with its validator run; any error is fixed before reporting. `kb/code/` is generated by the project graph — never edit it by hand.
- **Project graph before Grep.** In a project with `.hosa/graph/`, locate code with the graph command injected at session start (`ticket`, `explain`, `affected`, `find`, `map`) and read only the regions it points to; Grep only when the graph has no answer.
```

- [ ] **Step 9: Verify**

```bash
grep -c "graph.py" agents/tech-lead.md agents/reviewer.md agents/developer.md agents/debugger.md agents/senior-dev.md skills/changement/SKILL.md
grep -n "Hosa-Ticket" skills/develop/SKILL.md
grep -n "\`okf\`" skills/using-hosa/SKILL.md
grep -n "^tools:" agents/tech-lead.md agents/reviewer.md
```

Expected: every agent/skill file ≥ 1; the develop commit line and its note; the `okf` row and Core Rule; both `tools:` lines end with `Bash`. Also run `git diff --stat -- agents skills` and confirm only these files changed, by a handful of lines each.

- [ ] **Step 10: Commit**

```bash
git commit --only -m "feat: agents query the project graph; develop commits carry Hosa-Ticket trailer" -- agents/tech-lead.md agents/reviewer.md agents/developer.md agents/debugger.md agents/senior-dev.md skills/develop/SKILL.md skills/changement/SKILL.md skills/using-hosa/SKILL.md
```

Note: `--only` commits the whole current content of each listed file, including the user's pre-existing uncommitted edits in those files. Before this step, show the user `git diff -- <those files>` and ask whether to commit them together or to stash their own edits first.

---

## Known limits (accepted)

- Go methods are not nested under their struct (flat `function` nodes).
- Ruby `require` of gems stays unresolved (no edge) — only `require_relative` resolves.
- Grammars download on first use per language; offline, those files keep only their `file` node.
- Names with more than 5 candidates repo-wide (`get`, `run`, `__init__`) produce no call edge (`MAX_CANDIDATES`).
