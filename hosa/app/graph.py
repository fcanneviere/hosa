"""Graphe du projet géré : code (tree-sitter) + liens vers la KB, incrémental, requêtes compactes pour les agents."""
import argparse
import fnmatch
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
# Fichiers plus gros que ça (générés, empaquetés, minifiés) : hors du graphe. HOSA_GRAPH_MAX_KB pour changer.
MAX_FILE_BYTES = int(os.environ.get("HOSA_GRAPH_MAX_KB", "512")) * 1024
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
    return sorted({f for f in files if not f.startswith(".hosa/") and gx.lang_of(f) and _indexable(Path(root) / f)})


def _indexable(path):
    try:
        return path.is_file() and path.stat().st_size <= MAX_FILE_BYTES
    except OSError:
        return False


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


def _linked_worktree(root):
    """Dossier git commun si `root` est un worktree lié (celui d'un sprint), sinon None."""
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-dir", "--git-common-dir"],
                             capture_output=True, text=True, check=True).stdout.splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    git_dir, common = (Path(root, d.strip()).resolve() for d in out[:2])
    return common if git_dir != common else None


def _ensure_gitignore(root):
    common = _linked_worktree(root)
    # worktree de sprint : exclusion locale, jamais une modif d'un fichier suivi
    gi = common / "info" / "exclude" if common else Path(root) / ".gitignore"
    gi.parent.mkdir(parents=True, exist_ok=True)
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
                if _indexable(root / rel):
                    current.add(rel)
                else:
                    files.pop(rel, None)
        for rel in sorted(current):
            st = (root / rel).stat()
            entry = files.get(rel)
            if entry and "error" in entry["facts"]:  # extraction en échec : on retente à chaque refresh
                entry = None
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
        if changed and not _linked_worktree(root):  # la KB d'un worktree de sprint reste celle de la base
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

    def find(self, text, limit=20, path=None, kind=None, offset=0):
        tokens = [t for t in re.split(r"[\s/.:_-]+", text.lower()) if t]
        scored = []
        for i, n in self.nodes.items():
            if path and not fnmatch.fnmatch(n.get("file", ""), path):
                continue
            if kind and n["kind"] != kind:
                continue
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
        return [i for *_, i in sorted(scored)[offset:offset + limit]]

    def detail(self, nid):
        return {"node": self.nodes[nid],
                "out": [{**e, "node": self.nodes[e["dst"]]} for e in self.out.get(nid, [])],
                "in": [{**e, "node": self.nodes[e["src"]]} for e in self.inc.get(nid, [])]}

    def affected(self, nid, depth=2):
        """Ce qui dépend de `nid` (parcours inverse calls/imports/inherits) + tickets qui touchent ces fichiers."""
        seeds = [nid]
        for s in seeds:  # tout le contenu, méthodes comprises
            seeds += [e["dst"] for e in self.out.get(s, []) if e["rel"] == "contains"]
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


def status(root):
    """État de l'index, sans le reconstruire : taille, fraîcheur, fichiers à réindexer ou exclus."""
    root = Path(root).resolve()
    gdir = graph_dir(root)
    graph, manifest = _load_json(gdir / "graph.json", {}), _load_json(gdir / "manifest.json", {})
    if not graph:
        return "Pas encore d'index — `graph.py index` le construit (le hook de démarrage aussi)."
    files = manifest.get("files", {})
    stale, missing, langs, errors = [], [], {}, []
    for rel in tracked_files(root):
        entry = files.get(rel)
        if not entry:
            missing.append(rel)
        elif entry["mtime"] != (root / rel).stat().st_mtime:
            stale.append(rel)
        langs[gx.lang_of(rel)] = langs.get(gx.lang_of(rel), 0) + 1
    errors = [r for r, e in files.items() if "error" in e.get("facts", {})]
    big = []
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, check=True).stdout.decode("utf-8", "replace").split("\0")
        big = [f for f in out if f and gx.lang_of(f) and not f.startswith(".hosa/")
               and (root / f).is_file() and (root / f).stat().st_size > MAX_FILE_BYTES]
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass
    kinds = {}
    for n in graph.get("nodes", []):
        kinds[n["kind"]] = kinds.get(n["kind"], 0) + 1
    lines = [f"Index : {gdir / 'graph.json'} — construit le {graph.get('built_at', '?')}",
             f"Fichiers indexés : {len(files)} — " + ", ".join(f"{l} {c}" for l, c in sorted(langs.items(), key=lambda x: -x[1])),
             "Nœuds : " + ", ".join(f"{k} {c}" for k, c in sorted(kinds.items())) + f" — arêtes : {len(graph.get('edges', []))}",
             f"À réindexer : {len(stale)} modifié(s), {len(missing)} nouveau(x)" + (" → `graph.py index`" if stale or missing else " — à jour"),
             f"Exclus (> {MAX_FILE_BYTES // 1024} Ko, HOSA_GRAPH_MAX_KB) : {len(big)}" + (f" — {', '.join(big[:5])}" if big else ""),
             f"Extraction en échec : {len(errors)}" + (f" — {', '.join(errors[:5])}" if errors else "")]
    return "\n".join(lines)


def run(root, cmd, arg=None, depth=2, limit=20, budget=BUDGET, path=None, kind=None, offset=0):
    """Exécute une commande de requête et retourne le texte à afficher."""
    root = Path(root)
    if cmd == "status":
        return status(root)
    if cmd == "map":
        refresh(root)
        index = root / ".hosa" / "kb" / "code" / "index.md"
        return index.read_text(encoding="utf-8") if index.exists() else "Aucune carte (KB absente)."
    g = Index(refresh(root))
    (graph_dir(root) / "last_query").write_text(str(time.time()), encoding="utf-8")
    if cmd == "find":
        return budgeted([fmt(g.nodes[i]) + (f"  — {g.nodes[i]['doc']}" if g.nodes[i].get("doc") else "")
                         for i in g.find(arg, limit, path, kind, offset)] or ["Aucun résultat."], budget)
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
    f = sub.add_parser("find", help="recherche par nom, chemin ou doc")
    f.add_argument("text")
    f.add_argument("--path", help="glob sur le fichier, ex. 'src/api/*'")
    f.add_argument("--kind", choices=sorted(KIND_ORDER), help="type d'élément")
    f.add_argument("--limit", type=int, default=20)
    f.add_argument("--offset", type=int, default=0, help="page suivante : --offset 20")
    sub.add_parser("status", help="état de l'index : taille, fraîcheur, exclus, échecs (sans réindexer)")
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
            print(run(root, args.cmd, arg, depth=getattr(args, "depth", 2), budget=args.budget,
                      limit=getattr(args, "limit", 20), path=getattr(args, "path", None),
                      kind=getattr(args, "kind", None), offset=getattr(args, "offset", 0)))
    except GraphError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # console Windows en cp1252
    sys.exit(main())
