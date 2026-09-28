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
