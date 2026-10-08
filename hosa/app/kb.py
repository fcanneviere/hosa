"""Lecture/écriture de la KB OKF (.hosa/kb/) — la KB de fichiers est la seule source de vérité."""
import re
from datetime import date, datetime, timezone
from pathlib import Path

import markdown
import nh3
import yaml

RESERVED_FILENAMES = {"index.md", "log.md"}
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


def resolve_kb_root(start=None):
    start = Path(start or Path.cwd()).resolve()
    for d in (start, *start.parents):
        if (d / ".hosa" / "kb").is_dir():
            return d / ".hosa" / "kb"
    return start / ".hosa" / "kb"


def parse(raw):
    """Retourne (frontmatter, body). Lève KbError si le YAML est invalide."""
    raw = raw.lstrip("﻿")
    m = re.match(r"---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", raw, re.S)
    if not m:
        return {}, raw
    try:
        fm = yaml.load(m.group(1), Loader=_Loader) or {}
    except yaml.YAMLError as e:
        raise KbError(f"frontmatter YAML invalide : {e}") from e
    if not isinstance(fm, dict):
        raise KbError("le frontmatter doit être un dictionnaire YAML")
    return fm, raw[m.end():]


def dump_frontmatter(fm):
    return yaml.dump(fm, Dumper=_Dumper, allow_unicode=True, sort_keys=False, default_flow_style=None, width=1000)


def serialize(fm, body):
    return f"---\n{dump_frontmatter(fm)}---\n{body}"


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


def walk(root):
    root = Path(root).resolve()
    out = []
    if not root.is_dir():
        return out
    for p in sorted(root.rglob("*.md")):
        if p.name in RESERVED_FILENAMES:
            continue
        try:
            fm, body = parse(p.read_text(encoding="utf-8"))
        except KbError:
            continue  # YAML cassé : on saute plutôt que de faire tomber la liste
        if not fm.get("type"):
            continue  # OKF §11 : `type` est le seul champ requis
        out.append({"path": _rel(root, p), "frontmatter": fm, "body": body})
    return out


def get(root, rel_path):
    root, target = _safe_target(root, rel_path)
    if not target.is_file():
        return None
    fm, body = parse(target.read_text(encoding="utf-8"))
    return _full(root, target, fm, body)


def _full(root, target, fm, body):
    return {
        "path": _rel(root, target),
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


def update(root, rel_path, frontmatter=None, body=None, merge=True):
    """Met à jour un concept. merge=True fusionne le frontmatter (PATCH), sinon le remplace (édition complète).
    `type` est immuable : un concept ne change pas de nature."""
    root, target = _safe_target(root, rel_path)
    if not target.is_file():
        return None
    fm, old_body = parse(target.read_text(encoding="utf-8"))
    patch = dict(frontmatter or {})
    if "type" in patch and patch["type"] != fm.get("type"):
        raise KbError("`type` est immuable")
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


def activity(root, limit=60):
    root = Path(root).resolve()
    out = []
    for log in root.rglob("log.md"):
        bundle = _rel(root, log.parent) if log.parent != root else ""
        day = None
        for line in log.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                day = line[3:].strip()
            elif line.startswith("- ") and day:
                out.append({"date": day, "bundle": bundle, "text": line[2:]})
    out.sort(key=lambda e: e["date"], reverse=True)  # stable : garde l'ordre intra-jour du fichier
    return out[:limit]


def overview(root):
    cs = walk(root)
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
        sprints.append({
            "path": s["path"], "slug": slug, "title": s["frontmatter"].get("title") or slug,
            "description": s["frontmatter"].get("description", ""),
            "state": s["frontmatter"].get("state", "planned"),
            "branch": s["frontmatter"].get("branch"),
            "total": len(mine), "done": sum(t["frontmatter"].get("state") == "done" for t in mine),
            "tickets": [{"path": t["path"], "title": t["frontmatter"].get("title") or t["path"],
                         "state": t["frontmatter"].get("state", "todo")} for t in mine],
        })
    order = {"active": 0, "planned": 1, "done": 2}
    sprints.sort(key=lambda s: (order.get(s["state"], 3), s["slug"]))

    audits = sorted(_of(cs, "Audit Qualité"), key=_at, reverse=True)
    exigences = _of(cs, "Exigence")
    projects = sorted(_of(cs, "Project"), key=lambda c: c["path"] != "project/identity.md")
    project = projects[0] if projects else None
    return {
        "project": project and {"path": project["path"], "frontmatter": project["frontmatter"],
                                "objectives": _section(project["body"], "Objectifs mesurables")},
        "pipelines": pipelines,
        "next": first_gap,
        "tickets": counts,
        "exigences": {"stable": sum(c["frontmatter"].get("status") == "stable" for c in exigences),
                      "draft": sum(c["frontmatter"].get("status") != "stable" for c in exigences)},
        "sprints": sprints,
        "quality": audits and {"path": audits[0]["path"], "at": _at(audits[0]),
                               "verdict": _section(audits[0]["body"], "Verdict")} or None,
        "activity": activity(root, 12),
    }
