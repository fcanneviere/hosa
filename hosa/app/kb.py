"""Lecture/écriture de la KB OKF (.hosa/kb/) — la KB de fichiers est la seule source de vérité."""
import hashlib
import importlib.util
import posixpath
import re
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import markdown
import nh3
import yaml

RESERVED_FILENAMES = {"index.md", "log.md"}
UNREADABLE = "Le fichier est illisible : "
NOT_UTF8 = "le fichier n'est pas en UTF-8"
TICKET_STATES = ("todo", "doing", "blocked", "done")
ACTOR = "process:hosa-app"


class _Loader(yaml.SafeLoader):
    """SafeLoader qui garde les dates ISO en chaînes, pour un aller-retour fichier -> JSON -> fichier sans perte."""


class _Dumper(yaml.SafeDumper):
    """Symétrique de _Loader : écrit les dates ISO sans guillemets, comme les skills les rédigent."""


_Loader.yaml_implicit_resolvers = _Dumper.yaml_implicit_resolvers = {
    k: [(tag, rx) for tag, rx in v if tag != "tag:yaml.org,2002:timestamp"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


class KbError(ValueError):
    pass


class GitError(Exception):
    pass


class ConflictError(Exception):
    pass


class UsageError(Exception):
    pass


class UsageFailed(Exception):
    pass


def resolve_kb_root(start=None):
    start = Path(start or Path.cwd()).resolve()
    for d in (start, *start.parents):
        if (d / ".hosa" / "kb").is_dir():
            return d / ".hosa" / "kb"
    return start / ".hosa" / "kb"


def load_frontmatter(text, first_line=1):
    """Le frontmatter en dict, ou KbError avec une cause lisible : jamais le message de PyYAML, qui cite le contenu.
    `first_line` : numéro, pour l'utilisateur, de la première ligne YAML."""
    try:
        fm = yaml.load(text, Loader=_Loader) or {}
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        raise KbError(f"l'en-tête est mal écrit (ligne {mark.line + first_line})" if mark else "l'en-tête est mal écrit") from None
    if not isinstance(fm, dict):
        raise KbError("l'en-tête doit être une liste de champs")
    return fm


def parse(raw):
    """Retourne (frontmatter, body). Lève KbError « Le fichier est illisible : <cause> » si le YAML est invalide."""
    raw = raw.lstrip("﻿")
    m = re.match(r"---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", raw, re.S)
    if not m:
        return {}, raw
    try:
        return load_frontmatter(m.group(1), first_line=2), raw[m.end():]
    except KbError as e:
        raise KbError(UNREADABLE + str(e)) from None


def dump_frontmatter(fm):
    return yaml.dump(fm, Dumper=_Dumper, allow_unicode=True, sort_keys=False, default_flow_style=None, width=1000)


def serialize(fm, body):
    return f"---\n{dump_frontmatter(fm)}---\n{body}"


def _patch_in_place(raw, patch):
    """Réécrit seulement les lignes `clé: valeur` modifiées du frontmatter, le reste du fichier reste identique.
    Retourne None si une clé n'est pas un scalaire déjà présent sur une seule ligne (repli : réécriture complète)."""
    bare = raw.lstrip("﻿")
    m = re.match(r"---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", bare, re.S)
    if not m:
        return None
    out = m.group(1)
    for k, v in patch.items():
        if isinstance(v, (dict, list, set, tuple)):
            return None
        lines = yaml.dump({k: v}, Dumper=_Dumper, allow_unicode=True, sort_keys=False, default_flow_style=False, width=1000).splitlines()
        hits = list(re.finditer(rf"(?m)^{re.escape(str(k))}:[ \t]*[^\r\n]*", out))
        if len(lines) != 1 or len(hits) != 1:
            return None
        out = out[:hits[0].start()] + lines[0] + out[hits[0].end():]
    i, j = m.span(1)
    cut = len(raw) - len(bare)
    return raw[:cut + i] + out + raw[cut + j:]


def render(body):
    return nh3.clean(markdown.markdown(body, extensions=["tables", "fenced_code", "sane_lists"]))


def trust_tier(verified):
    by = verified.get("by") if isinstance(verified, dict) else None
    if not by:
        return "unverified"
    return "human-reviewed" if str(by).startswith("human:") else "machine-confirmed"


def _rel(root, p):
    return p.relative_to(root).as_posix()


def _safe_target(root, rel_path):
    """Chemin absolu d'un concept dans la KB, ou KbError (traversée, nom réservé, extension)."""
    root = Path(root).resolve()
    target = (root / rel_path).resolve()
    if root not in target.parents:
        raise KbError("chemin hors de la KB")
    if target.suffix != ".md" or target.name in RESERVED_FILENAMES:
        raise KbError("seuls les concepts .md (hors index.md/log.md) sont accessibles")
    return root, target


def _read(p):
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None  # fichier illisible : on saute


def walk(root, unreadable=None):
    """Concepts de la KB. Un fichier illisible est sauté (la liste n'échoue jamais) et,
    si `unreadable` est une liste, y est ajouté avec sa cause."""
    root = Path(root).resolve()
    out = []
    if not root.is_dir():
        return out
    for p in sorted(root.rglob("*.md")):
        if p.name in RESERVED_FILENAMES:
            continue
        text = _read(p)
        try:
            if text is None:
                raise KbError(UNREADABLE + NOT_UTF8)
            fm, body = parse(text)
        except KbError as e:
            if unreadable is not None:
                unreadable.append({"path": _rel(root, p), "cause": str(e).removeprefix(UNREADABLE)})
            continue
        if not fm.get("type"):
            continue  # OKF §11 : `type` est le seul champ requis
        out.append({"path": _rel(root, p), "frontmatter": fm, "body": body})
    return out


def get(root, rel_path):
    root, target = _safe_target(root, rel_path)
    if not target.is_file():
        return None
    text = _read(target)
    if text is None:
        raise KbError(UNREADABLE + NOT_UTF8)
    fm, body = parse(text)
    rel = _rel(root, target)
    cs = walk(root)
    titles = {c["path"]: c["frontmatter"].get("title") or c["path"] for c in cs}
    cited, bundle = f"`{target.stem}`", rel.rpartition("/")[0]
    return {**_full(root, target, fm, body),
            "liens": {"sortants": [{"path": p, "title": titles[p]} for p in _links(rel, body) if p in titles],
                      "entrants": [{"path": c["path"], "title": titles[c["path"]]} for c in cs
                                   if c["path"] != rel and rel in _links(c["path"], c["body"])]},
            "historique": [{"date": e["date"], "acteur": e["acteurNom"], "texte": e["text"]}
                           for e in activity(root, None, cs) if e["bundle"] == bundle and cited in e["text"]]}


LINK = re.compile(r"\]\(([^)\s#]+\.md)(?:#[^)]*)?\)")


def _links(rel, body):
    """Chemins KB des liens Markdown `(…/x.md)` du corps d'un concept, sans doublon."""
    base = posixpath.dirname(rel)
    return list(dict.fromkeys(posixpath.normpath(posixpath.join(base, h)) for h in LINK.findall(body)))


def version(target):
    """Empreinte du fichier sur disque : un PUT qui la renvoie n'écrase pas l'écriture d'un agent."""
    return hashlib.sha256(Path(target).read_bytes()).hexdigest()[:16]


def _full(root, target, fm, body):
    return {
        "path": _rel(root, target),
        "version": version(target),
        "frontmatter": fm,
        "frontmatterYaml": dump_frontmatter(fm),
        "body": body,
        "bodyHtml": render(body),
        "trustTier": trust_tier(fm.get("verified")),
    }


def append_log(root, bundle_dir, line, today=None):
    """Entrée OKF §9 dans le log.md du bundle : groupée par date, plus récente en tête."""
    log = bundle_dir / "log.md"
    day = f"## {(today or date.today()).isoformat()}"
    label = f"kb/{_rel(root, bundle_dir)}" if bundle_dir != root else "kb"
    text = log.read_text(encoding="utf-8") if log.exists() else f"# Log — {label}\n"
    if not text.startswith("#"):
        text = f"# Log — {label}\n{text}"
    if day in text:
        text = text.replace(day, f"{day}\n- {line}", 1)
    else:
        head, _, rest = text.partition("\n")
        text = f"{head}\n\n{day}\n- {line}\n{rest}"
    log.write_text(text, encoding="utf-8")


def update(root, rel_path, frontmatter=None, body=None, merge=True, baseline=None):
    """Met à jour un concept. merge=True fusionne le frontmatter (PATCH), sinon le remplace (édition complète).
    `type` est immuable : un concept ne change pas de nature. `baseline` : la `version` lue avant l'édition ;
    si le fichier a changé depuis (un agent a écrit), ConflictError et rien n'est écrit."""
    root, target = _safe_target(root, rel_path)
    if not target.is_file():
        return None
    text = _read(target)
    if text is None:
        raise KbError(UNREADABLE + NOT_UTF8)
    if baseline and baseline != version(target):
        raise ConflictError("Le fichier a été modifié entre-temps : rechargez-le avant d'enregistrer")
    fm, old_body = parse(text)
    patch = dict(frontmatter or {})
    if "type" in patch and patch["type"] != fm.get("type"):
        raise KbError("le type d'un concept ne change jamais")
    if patch.get("state", "todo") not in TICKET_STATES and fm.get("type") == "Ticket":
        raise KbError(f"state doit valoir : {', '.join(TICKET_STATES)}")
    if merge:
        changed = [k for k in patch if fm.get(k) != patch[k]]
        new_fm = {**fm, **patch}
    else:
        new_fm = {"type": fm["type"], **{k: v for k, v in patch.items() if k != "type"}}
        changed = sorted({k for k in fm.keys() | new_fm.keys() if fm.get(k) != new_fm.get(k)})
    new_body = old_body if body is None else body
    if new_body != old_body:
        changed.append("corps")
    if changed:
        text = None
        if merge and new_body == old_body and "corps" not in changed:
            with open(target, encoding="utf-8", newline="") as f:
                text = _patch_in_place(f.read(), {k: patch[k] for k in changed})
        if text is not None:
            with open(target, "w", encoding="utf-8", newline="") as f:
                f.write(text)
        else:
            target.write_text(serialize(new_fm, new_body), encoding="utf-8")
        append_log(root, target.parent, f"{ACTOR} a modifié `{target.stem}` ({', '.join(changed)})")
    return _full(root, target, new_fm, new_body)


def create(root, bundle, slug, ctype, title):
    root = Path(root).resolve()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug or ""):
        raise KbError("slug : minuscules, chiffres et tirets uniquement")
    if not ctype or not title:
        raise KbError("type et titre sont requis")
    _, target = _safe_target(root, f"{bundle.strip('/')}/{slug}.md")
    if target.exists():
        raise FileExistsError(_rel(root, target))
    target.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fm = {"type": ctype, "title": title, "description": "", "tags": [], "status": "draft",
          "generated": {"by": ACTOR, "at": now}}
    if ctype == "Ticket":
        fm["state"] = "todo"
    target.write_text(serialize(fm, "\n"), encoding="utf-8")
    append_log(root, target.parent, f"{ACTOR} a créé `{slug}` ({ctype})")
    return _full(root, target, fm, "\n")


# --- Pilotage -------------------------------------------------------------

def _of(cs, t):
    return [c for c in cs if c["frontmatter"].get("type") == t]


def _any_body(cs, t, pattern):
    return any(re.search(pattern, c["body"], re.I | re.M) for c in _of(cs, t))


# ponytail: chaque étape est "faite" si l'artefact qu'elle laisse dans la KB existe — heuristique
# alignée sur le skill `status` ; relecture/contestation n'écrivent pas de concept dédié, on lit `stable`.
PIPELINES = [
    ("cdc", "Cahier des charges", [
        ("hosa", "Identité du projet", lambda cs: bool(_of(cs, "Project"))),
        ("interview", "Interviews", lambda cs: bool(_of(cs, "Compte Rendu"))),
        ("redaction", "Rédaction", lambda cs: bool(_of(cs, "Exigence"))),
        ("fondamentaux", "Fondamentaux", lambda cs: bool(_of(cs, "Revue Fondamentaux"))),
        ("securite", "Sécurité", lambda cs: bool(_of(cs, "Analyse de sécurité"))),
        ("relecture", "Relecture", lambda cs: any(c["frontmatter"].get("status") == "stable" for c in _of(cs, "Exigence"))),
        ("contestation", "Contestation", lambda cs: any((c["frontmatter"].get("status") == "stable" and c["frontmatter"].get("verified")) for c in _of(cs, "Exigence"))),
    ]),
    ("data", "Structuration", [
        ("stack", "Stack", lambda cs: bool(_of(cs, "Stack Decision"))),
        ("infra", "Infra", lambda cs: bool(_of(cs, "Infra"))),
        ("donnees", "Données", lambda cs: _any_body(cs, "Exigence", r"^## Données")),
        ("schema-app", "Schéma app", lambda cs: _any_body(cs, "Infra", r"dictionnaire")),
        ("schema-db", "Schéma BDD", lambda cs: _any_body(cs, "Infra", r"migration")),
        ("architecture", "Architecture", lambda cs: _any_body(cs, "Infra", r"^## Documentation d'architecture")),
        ("menaces", "Menaces", lambda cs: bool(_of(cs, "Modèle de Menaces"))),
        ("interface", "Interface", lambda cs: _any_body(cs, "Infra", r"^## Documentation d'interface")),
        ("backlog", "Backlog", lambda cs: bool(_of(cs, "Ticket"))),
    ]),
    ("delivery", "Livraison", [
        ("sprint", "Sprint", lambda cs: bool(_of(cs, "Sprint"))),
        ("qa-plan", "Plan de test", lambda cs: bool(_of(cs, "Test Plan"))),
        ("git", "Branche", lambda cs: any(c["frontmatter"].get("branch") or c["frontmatter"].get("state") in ("active", "done") for c in _of(cs, "Sprint"))),
        ("develop", "Développement", lambda cs: any(c["frontmatter"].get("state") in ("doing", "done") for c in _of(cs, "Ticket"))),
        ("qa", "QA", lambda cs: _any_body(cs, "Test Plan", r"^## Résultats techniques")),
        ("validation", "Validation", lambda cs: any(c["frontmatter"].get("state") == "done" for c in _of(cs, "Ticket"))),
        ("bilan-sprint", "Bilan", lambda cs: bool(_of(cs, "Sprint Review"))),
    ]),
]


def _section(body, heading):
    m = re.search(rf"^## {heading}\s*\n+(.+)", body, re.M)
    return m.group(1).strip() if m else None


def _at(c, key="generated"):
    v = c["frontmatter"].get(key)
    return str(v.get("at", "")) if isinstance(v, dict) else ""


def _actor(text):
    name = text.split(" ", 1)[0]
    return ("humain" if name.startswith("human:") else "processus" if name.startswith("process:") else "agent"), name


def activity(root, limit=60, cs=None):
    """Entrées des `log.md` : jour, dossier, texte, acteur (humain|processus|agent), et `lien` vers le
    premier concept cité entre accents graves qui existe dans la KB (même dossier d'abord)."""
    root = Path(root).resolve()
    by_stem = {}
    for c in sorted(walk(root) if cs is None else cs, key=lambda c: c["path"]):
        by_stem.setdefault(Path(c["path"]).stem, []).append(c["path"])
    out = []
    for log in root.rglob("log.md"):
        bundle = _rel(root, log.parent) if log.parent != root else ""
        day = None
        for line in (_read(log) or "").splitlines():
            if line.startswith("## "):
                day = line[3:].strip()
            elif line.startswith("- ") and day:
                text = line[2:]
                acteur, nom = _actor(text)
                found = [p for s in re.findall(r"`([^`\s]+)`", text) for p in by_stem.get(s, [])]
                lien = next((p for p in found if p.rpartition("/")[0] == bundle), found[0] if found else None)
                out.append({"date": day, "bundle": bundle, "text": text, "acteur": acteur, "acteurNom": nom, "lien": lien})
    out.sort(key=lambda e: e["date"], reverse=True)  # stable : garde l'ordre intra-jour du fichier
    return out[:limit]


def _avancement():
    path = Path(__file__).resolve().parents[2] / "skills" / "status" / "scripts" / "avancement.py"
    spec = importlib.util.spec_from_file_location("avancement", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


av = _avancement()


def _usage_report():
    path = Path(__file__).resolve().parents[2] / "skills" / "status" / "scripts" / "usage_report.py"
    spec = importlib.util.spec_from_file_location("usage_report", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ur = _usage_report()


def usage(checkout, days):
    """Consommation par agent et par modèle sur les `days` derniers jours, via `usage_report.scan`."""
    try:
        days = int(days)
    except (TypeError, ValueError) as e:
        raise KbError("days doit être un entier ≥ 1") from e
    if days < 1 or days > 3650:
        raise KbError("days doit être un entier ≥ 1")
    since = (date.today() - timedelta(days=days)).isoformat()
    try:
        by_actor, by_model, *_ = ur.scan(ur.project_dir(Path(checkout)), since, None)
    except Exception as e:
        raise UsageFailed(str(e)) from e
    if not by_actor:
        raise UsageError("Aucune donnée de consommation trouvée pour ce projet")

    def rows(table):
        total = sum(r["usd"] for r in table.values()) or 1
        return [{"name": k, **{f: r[f] for f in ur.FIELDS}, "part": 100 * r["usd"] / total}
                for k, r in sorted(table.items(), key=lambda kv: -kv[1]["usd"])]

    return {"agents": rows(by_actor), "models": rows(by_model), "since": since}


def coverage_of(root, ticket_path):
    """Couverture des critères d'un ticket de `tickets/` (`av.coverage`)."""
    root, target = _safe_target(root, ticket_path)
    if Path(ticket_path).is_absolute() or target.parent != root / "tickets":
        raise KbError("seuls les tickets sont accessibles")
    return av.coverage(root, target.stem)


def coverage(root):
    """Couverture des critères de chaque ticket, par chemin de concept."""
    try:
        return {c["path"]: coverage_of(root, c["path"]) for c in walk(root)
                if c["frontmatter"].get("type") == "Ticket" and Path(c["path"]).parent.as_posix() == "tickets"}
    except (OSError, UnicodeDecodeError):
        raise KbError("KB illisible") from None


def plan(root):
    """Le plan d'avancement tenu par les skills (`project/avancement.md`), ou None s'il n'existe pas encore.
    Mêmes règles que `avancement.py next` : étape à reprendre, son skill, ce qu'il lui manque."""
    root = Path(root).resolve()
    path = root / "project" / "avancement.md"
    if not path.exists():
        return None
    sections, resume = av.load(path)
    found = av.first_open(sections)
    nxt = None
    if found:
        title, r = found
        sprint = title[len("Sprint "):] if title.startswith("Sprint ") else None
        nxt = {"stage": r[0], "section": title, "status": r[1], "detail": r[3],
               "skill": av.SKILL.get(r[0], r[0]),
               "gaps": av.check(root, r[0], sprint) if r[1] == av.DOING else []}
    return {
        "resume": [line[2:] if line.startswith("- ") else line for line in resume.splitlines()],
        "sections": [{"title": t, "stages": [{"stage": s, "status": st, "at": at, "detail": d} for s, st, at, d in rows]}
                     for t, rows in sections.items()],
        "next": nxt,
    }


def points(estimate):
    if isinstance(estimate, str):
        estimate = estimate.strip()
        e = {"S": 1, "M": 3, "L": 5}.get(estimate.upper())
        return e if e is not None else int(estimate) if estimate.isdecimal() else 0
    return estimate if isinstance(estimate, int) and not isinstance(estimate, bool) and estimate > 0 else 0


def board(cs):
    """Tickets à plat, triés par priorité (sans priorité en dernier) puis titre."""
    tier = {"human-reviewed": "humain", "machine-confirmed": "machine", "unverified": "aucune"}
    rows = []
    for t in _of(cs, "Ticket"):
        fm = t["frontmatter"]
        slug = Path(t["path"]).stem
        prio = fm.get("priority")
        gen = fm.get("generated")
        by = gen.get("by") if isinstance(gen, dict) else None
        rows.append({
            "path": t["path"], "slug": slug, "title": fm.get("title") or slug,
            "state": fm.get("state") if fm.get("state") in TICKET_STATES else "todo",
            "priority": prio if isinstance(prio, int) and not isinstance(prio, bool) else None,
            "estimate": fm.get("estimate"), "points": points(fm.get("estimate")), "sprint": fm.get("sprint"),
            "origine": "humain" if str(by).startswith("human:") else "agent",
            "validation": tier[trust_tier(fm.get("verified"))],
        })
    rows.sort(key=lambda r: (r["priority"] is None, r["priority"] or 0, str(r["title"]).casefold()))
    return rows


def recettes(cs):
    """Concepts de `test/` hors `*-technique.md`, FAIL d'abord puis du plus récent au plus ancien."""
    tickets = sorted(((Path(t["path"]).stem, t) for t in _of(cs, "Ticket")), key=lambda x: -len(x[0]))
    out = []
    for c in cs:
        p = Path(c["path"])
        if p.parent.as_posix() != "test" or p.stem.endswith("-technique"):
            continue
        stem, t = next(((s, t) for s, t in tickets if p.stem.startswith(s + "-")), (None, None))
        persona = p.stem[len(stem) + 1:] if stem else None
        titre = t["frontmatter"].get("title") if t else None
        m = re.search(r"^## Verdict\s*$(.*?)(?=^## |\Z)", c["body"], re.M | re.S)
        v = re.search(r"\b(PASS-WITH-NOTES|PASS|FAIL)\b", m.group(1)) if m else None
        out.append({"path": c["path"], "ticket": t["path"] if t else None, "persona": persona,
                    "titre": titre or c["frontmatter"].get("title") or c["path"],
                    "at": _at(c), "verdict": v.group(1) if v else None})
    out.sort(key=lambda r: r["path"])
    out.sort(key=lambda r: r["at"], reverse=True)
    out.sort(key=lambda r: r["verdict"] != "FAIL")
    return out


def _verdict(body):
    """PASS / PASS-WITH-NOTES / FAIL de `## Verdict`, sinon sa première ligne telle quelle."""
    sec = av.section(body, "Verdict") or ""
    m = re.search(r"\b(PASS-WITH-NOTES|PASS|FAIL)\b", sec)
    return m.group(1) if m else _section(body, "Verdict")


def _audit(c):
    return c and {"path": c["path"], "at": _at(c), "verdict": _verdict(c["body"])}


def overview(root):
    illisibles = []
    cs = walk(root, illisibles)
    first_gap = None
    pipelines = []
    for key, label, stages in PIPELINES:
        rows = []
        for skill, name, done in stages:
            ok = done(cs)
            if not ok and first_gap is None:
                first_gap = skill
            rows.append({"skill": skill, "label": name, "done": ok})
        pipelines.append({"key": key, "label": label, "stages": rows})

    tickets = _of(cs, "Ticket")
    counts = {s: 0 for s in TICKET_STATES}
    for t in tickets:
        counts[t["frontmatter"].get("state") if t["frontmatter"].get("state") in counts else "todo"] += 1

    sprints = []
    for s in _of(cs, "Sprint"):
        slug = Path(s["path"]).stem
        mine = [t for t in tickets if t["frontmatter"].get("sprint") == slug]
        engages = sum(points(t["frontmatter"].get("estimate")) for t in mine)
        faits = sum(points(t["frontmatter"].get("estimate")) for t in mine if t["frontmatter"].get("state") == "done")
        # mêmes règles que `avancement.check validation` : dernier « Bloquant : N », dernière mention OK/KO par Tn
        bloquants = re.findall(r"Bloquant\s*:\s*(\d+)", av.section(s["body"], "Audit") or "")
        demo = dict(re.findall(r"\b(T\d+)\b[^\n]*?\b(OK|KO)\b", av.section(s["body"], "Démo") or ""))
        sprints.append({
            "path": s["path"], "slug": slug, "title": s["frontmatter"].get("title") or slug,
            "description": s["frontmatter"].get("description", ""),
            "state": s["frontmatter"].get("state", "planned"),
            "branch": s["frontmatter"].get("branch"),
            "total": len(mine), "done": sum(t["frontmatter"].get("state") == "done" for t in mine),
            "engages": engages, "faits": faits, "restants": engages - faits,
            "audit": {"bloquants": int(bloquants[-1]) if bloquants else None},
            "demo": [{"t": k, "ok": v == "OK"} for k, v in demo.items()],
            "tickets": [{"path": t["path"], "title": t["frontmatter"].get("title") or t["path"],
                         "state": t["frontmatter"].get("state", "todo")} for t in mine],
        })
    order = {"active": 0, "planned": 1, "done": 2}
    sprints.sort(key=lambda s: (order.get(s["state"], 3), s["slug"]))

    audits = sorted(_of(cs, "Audit Qualité"), key=_at, reverse=True)
    security = sorted((c for c in cs if re.fullmatch(r"securite/audit-[^/]+\.md", c["path"])),
                      key=lambda c: (_at(c), c["path"]), reverse=True)
    done = [s["faits"] for s in sprints if s["state"] == "done"]
    moyenne = sum(done) / len(done) if done else None
    ouverts = sum(points(t["frontmatter"].get("estimate")) for t in tickets if t["frontmatter"].get("state") != "done")
    exigences = _of(cs, "Exigence")
    projects = sorted(_of(cs, "Project"), key=lambda c: c["path"] != "project/identity.md")
    project = projects[0] if projects else None
    return {
        "project": project and {"path": project["path"], "frontmatter": project["frontmatter"],
                                "objectives": _section(project["body"], "Objectifs mesurables")},
        "plan": plan(root),
        "pipelines": pipelines,
        "next": first_gap,
        "tickets": counts,
        "board": board(cs),
        "exigences": {"stable": sum(c["frontmatter"].get("status") == "stable" for c in exigences),
                      "draft": sum(c["frontmatter"].get("status") != "stable" for c in exigences)},
        "sprints": sprints,
        "quality": _audit(audits[0] if audits else None),
        "security": _audit(security[0] if security else None),
        "velocite": {"moyenne": moyenne, "ouverts": ouverts,
                     "restants": round(ouverts / moyenne, 1) if moyenne else None},
        "illisibles": illisibles,
        "activity": activity(root, 12, cs),
        "recettes": recettes(cs),
    }


GIT_STATE = {"?": "nouveau", "A": "nouveau", "D": "supprimé"}


def kb_status(root):
    """État git de la KB (lecture seule) : dépôt ou non, fichiers de `git status --short`. Le dossier `code/`
    (carte du code régénérée par le graphe) est exclu par pathspec : ouvrir un écran ne change pas le compte."""
    try:
        inside = subprocess.run(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
                                capture_output=True, text=True, timeout=10)
        if inside.returncode != 0:
            return {"git": False, "changed": 0, "files": []}
        st = subprocess.run(["git", "-c", "core.quotePath=false", "-C", str(root), "status", "--short", "--", ".", ":(exclude)code"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise GitError("état de la KB illisible") from e
    if st.returncode != 0:
        raise GitError("état de la KB illisible")
    files = [{"path": line[3:].split(" -> ")[-1].strip('"'),
              "state": next((GIT_STATE[x] for x in line[:2] if x in GIT_STATE), "modifié")}
             for line in st.stdout.splitlines() if line.strip()]
    return {"git": True, "changed": len(files), "files": files}
