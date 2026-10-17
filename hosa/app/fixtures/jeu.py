"""Jeu de données de test du sprint 1 : une KB de référence, un dépôt git, des transcripts.

Tests : `from fixtures import jeu` puis `jeu.ecrire(self.root)` (même boucle que setUp de test_app.py).
Recette : `python fixtures/jeu.py [dest] [--changes N]` remet `dest` à zéro ; `--check` vérifie.
Chaque fichier sert un cas des plans `kb/test/*-technique.md` : voir README.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

DEST = Path(tempfile.gettempdir()) / "hosa-ui-recette"


def ticket(title, state=None, priority=None, estimate=None, by=None, at=None, verified=None, criteres=(), extra=""):
    fm = ["type: Ticket", f'title: "{title}"']
    fm += [f"state: {state}"] if state else []
    fm += [f"priority: {priority}"] if priority is not None else []
    fm += [f"estimate: {estimate}"] if estimate is not None else []
    fm += ["sprint: s1"]
    fm += [f"generated: {{ by: {by}, at: '{at}' }}"] if by else []
    fm += [f"verified: {{ by: {verified}, at: '2026-10-05T09:00:00Z' }}"] if verified else []
    body = "Lié à : [exigence](../cdc/login.md)\n"
    if criteres:
        body += "\n## Critères d'acceptation\n" + "".join(f"- {c}\n" for c in criteres)
    return "---\n" + "\n".join(fm) + "\n---\n" + body + extra


def recette(ticket_slug, persona, verdict_section, at="2026-10-08T10:00:00Z", title=None):
    return (f"---\ntype: Test Plan\ntitle: \"{title or f'Recette — {ticket_slug} ({persona})'}\"\n"
            f"tags: [recette]\nstatus: stable\ngenerated: {{ by: hosa-key-user/1.0, at: '{at}' }}\n---\n"
            f"{verdict_section}\nLié à : [ticket](../tickets/{ticket_slug}.md)\n")


CA3 = ("CA1 — a", "CA2 — b", "CA3 — c")

# KB de référence : chemin relatif -> contenu. Tout fichier sert un cas (README.md).
KB: dict[str, str] = {
    # Tableau (tickets-tableau-colonnes) : colonne doing = Annuaire L p1, Export CSV M p1, Connexion M p2 -> 11 points
    "tickets/connexion.md": ticket("Connexion", "doing", 2, "M", "human:fabien", "2026-09-23T00:00:00Z",
                                   "human:fabien", CA3),
    "tickets/export-csv.md": ticket("Export CSV", "doing", 1, "M", "hosa-product-owner/1.0", "2026-09-25T00:00:00Z",
                                    "hosa-lint", CA3),
    "tickets/annuaire.md": ticket("Annuaire", "doing", 1, "L", "hosa-product-owner/1.0", "2026-10-10T00:00:00Z",
                                  None, ("CA1 — a", "CA2 — b")),
    "tickets/recherche.md": ticket("Recherche", "todo", 3, "S", "hosa-product-owner/1.0", "2026-10-01T00:00:00Z"),
    "tickets/etat-inconnu.md": ticket("État inconnu", "foo", 4, "à voir"),
    "tickets/sans-etat.md": ticket("Sans état"),
    "tickets/titre-hostile.md": ticket("<img src=x onerror=alert(1)>", "blocked", 1, 2, "hosa-product-owner/1.0",
                                       "2026-10-02T00:00:00Z", None, ("CA1)( — motif hostile", "CA2 — b")),
    "tickets/inscription.md": ticket("Inscription", "done", 1, "S", "human:fabien", "2026-09-10T00:00:00Z",
                                     "human:fabien", tuple(f"CA{i} — c{i}" for i in range(1, 12))),
    "tickets/casse.md": "---\ntype: Ticket\ntitle: [oops\nstate: todo\n---\n",
    "tickets/index.md": "# Index — tickets (réservé, ne doit pas bouger)\n",
    "tickets/log.md": "# Log — kb/tickets\n\n## 2026-09-20\n- human:fabien a créé `connexion`\n",
    # Sprints
    "sprints/s1.md": ("---\ntype: Sprint\ntitle: Sprint 1\nstate: active\n"
                      "generated: { by: hosa-sprint-planner/1.0, at: '2026-10-03T00:00:00Z' }\n---\n## Tickets\n"
                      + "".join(f"- [{s}](../tickets/{s}.md)\n" for s in
                                ("connexion", "export-csv", "annuaire", "recherche", "titre-hostile", "inscription"))),
    "sprints/s0.md": "---\ntype: Sprint\ntitle: Sprint 0\nstate: done\n---\n## Tickets\n",
    # Exigences et personas (validation-provenance-liste)
    "cdc/login.md": ("---\ntype: Exigence\ntitle: Login\nstatus: stable\n"
                     "generated: { by: hosa-product-owner/1.0, at: '2026-09-15T00:00:00Z' }\n"
                     "verified: { by: human:fabien, at: '2026-09-24T00:00:00Z' }\n---\n## Données en entrée\n- email\n"),
    "cdc/export.md": ("---\ntype: Exigence\ntitle: Export\nstatus: stable\n"
                      "generated: { by: hosa-product-owner/1.0, at: '2026-09-01T00:00:00Z' }\n---\n"),
    "cdc/ancienne.md": ("---\ntype: Exigence\ntitle: Ancienne\nstatus: deprecated\n"
                        "generated: { by: hosa-product-owner/1.0, at: '2026-08-01T00:00:00Z' }\n---\n"),
    "cdc/obsolete-lint.md": ("---\ntype: Exigence\ntitle: Obsolète lint\nstatus: deprecated\n"
                             "generated: { by: hosa-product-owner/1.0, at: '2026-08-02T00:00:00Z' }\n"
                             "verified: { by: hosa-lint, at: '2026-08-03T00:00:00Z' }\n---\n"),
    "cdc/obsolete-humain.md": ("---\ntype: Exigence\ntitle: Obsolète humain\nstatus: deprecated\n"
                               "generated: { by: hosa-product-owner/1.0, at: '2026-08-04T00:00:00Z' }\n"
                               "verified: { by: human:fabien, at: '2026-08-05T00:00:00Z' }\n---\n"),
    "cdc/log.md": "# Log — kb/cdc\n\n## 2026-09-20\n- human:fabien a créé `login`\n",
    "personnas/martine.md": ("---\ntype: Persona\ntitle: Martine\nstatus: stable\n"
                             "generated: { by: hosa-product-owner/1.0, at: '2026-09-20T00:00:00Z' }\n---\n"),
    "personnas/karim.md": ("---\ntype: Persona\ntitle: Karim\nstatus: stable\n"
                           "generated: { by: hosa-product-owner/1.0, at: '2026-09-21T00:00:00Z' }\n"
                           "verified: { by: human:martine, at: '2026-09-22T00:00:00Z' }\n---\n"),
    "project/identity.md": "---\ntype: Project\ntitle: Démo\n---\n## Objectifs mesurables\n- 100 users\n",
    "broken.md": "---\ntype: [oops\n---\n",
    # Plans techniques (couverture) et recettes (qualite-recettes-api)
    "test/connexion-technique.md": "---\ntype: Test Plan\ntitle: Tech connexion\n---\n## Cas de test\n- [CA1] x\n",
    "test/export-csv-technique.md": "---\ntype: Test Plan\ntitle: Tech export\n---\n## Cas de test\n- [CA1] x\n- [CA3] y\n",
    "test/inscription-technique.md": ("---\ntype: Test Plan\ntitle: Tech inscription\n---\n## Cas de test\n"
                                      "- [CA10] x\n- [CA11] y\n- ACA1 n'est pas CA1\n"),
    "test/connexion-martine.md": recette("connexion", "martine",
                                         "FAIL cité avant le titre.\n### Critères\n- CA2 — Oui — capture\n"
                                         "## Verdict\nPASS\n\nUn FAIL cité plus bas ne compte pas.\n"),
    "test/export-csv-karim.md": recette("export-csv", "karim", "### Critères\n- CA2 — Non\n## Verdict\nFAIL\n",
                                        "2026-10-09T10:00:00Z"),
    "test/annuaire-camille.md": recette("annuaire", "camille", "### Critères\n- CA1 — Oui\n## Verdict\nPASS-WITH-NOTES\n",
                                        "2026-10-07T10:00:00Z"),
    "test/inscription-martine.md": recette("inscription", "martine", "Pas de section verdict.\n", "2026-10-06T10:00:00Z"),
    "test/recherche-karim.md": recette("recherche", "karim", "## Verdict\nPASS<script>\n", "2026-10-05T10:00:00Z",
                                       "<script>alert(1)</script>"),
    "test/recherche-camille.md": "",
    "test/annuaire-martine.md": "---\ntype: [oops\n---\n## Verdict\nPASS\n",
    "test/log.md": "# Log — kb/test\n",
}

# Hors KB de référence : ignoré par kb.walk (fichier non UTF-8). À fusionner dans un test.
NON_UTF8 = {"test/recherche-martine.md": "---\ntitle: caf\xe9\n---\n## Verdict\nPASS\n".encode("latin-1")}

SRC = {"src/auth.py": "def login(user):\n    return check(user)\n\ndef check(user):\n    return True\n"}

# Changements non sauvegardés : 1 modifié, 1 non suivi, 1 dossier non suivi de 2 fichiers = 3 lignes de `git status --short`
CHANGES = [
    ("tickets/recherche.md", None),
    ("cdc/brouillon.md", "---\ntype: Exigence\ntitle: Brouillon\n---\n"),
    ("brouillons/", None),
]


def ecrire(root: Path, files: dict | None = None) -> Path:
    for rel, text in (KB if files is None else files).items():
        p = Path(root) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text) if isinstance(text, bytes) else p.write_text(text, encoding="utf-8")
    return Path(root)


def _git(root, *args):
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


def depot(checkout: Path, changes: int = 0) -> Path:
    """Projet git : KB sous .hosa/kb, code sous src/, un commit Hosa-Ticket: connexion. Renvoie la racine KB."""
    root = ecrire(Path(checkout) / ".hosa" / "kb")
    ecrire(checkout, SRC)
    _git(checkout, "init", "-q")
    _git(checkout, "add", ".")
    _git(checkout, "commit", "-qm", "feat: login", "-m", "Hosa-Ticket: connexion")
    for rel, text in CHANGES[:changes]:
        p = root / rel
        if rel == "tickets/recherche.md":
            p.write_text(p.read_text(encoding="utf-8").replace("priority: 3", "priority: 2"), encoding="utf-8")
        elif rel.endswith("/"):
            ecrire(p, {"a.md": "a\n", "b.md": "b\n"})
        else:
            ecrire(root, {rel: text})
    return root


def _entry(kind, day, **kw):
    return {"type": kind, "timestamp": f"{day.isoformat()}T12:00:00Z", "sessionId": "s1", **kw}


def _assistant(day, model, n, tools=()):
    return _entry("assistant", day, message={
        "model": model, "content": list(tools),
        "usage": {"input_tokens": n, "cache_creation_input_tokens": 2 * n, "cache_read_input_tokens": 10 * n,
                  "output_tokens": n // 2, "output_tokens_details": {"thinking_tokens": n // 10}}})


def transcripts(base: Path, today: date | None = None) -> Path:
    """Transcripts Claude Code factices dans `base` (= usage_report.project_dir patché)."""
    t = today or date.today()
    d = lambda n: t - timedelta(days=n)
    main = [
        _entry("user", t, message={"content": "lance qa-plan"}),
        _assistant(t, "claude-opus-5-5", 100, [
            {"type": "tool_use", "id": "sk1", "name": "Skill", "input": {"skill": "qa-plan"}},
            {"type": "tool_use", "id": "tu1", "name": "Agent", "input": {"subagent_type": "hosa-data-engineer"}}]),
        _entry("user", t, toolUseResult={"agentId": "a1"},
               message={"content": [{"type": "tool_result", "tool_use_id": "tu1", "content": "ok"}]}),
        _assistant(t, "claude-sonnet-4-5", 40),
        _entry("user", d(7), message={"content": "borne"}),
        _assistant(d(7), "claude-opus-5-5", 70),     # = since à 7 jours : inclus
        _assistant(d(8), "claude-opus-5-5", 80),     # exclu à 7 jours, inclus à 30
        _assistant(d(20), "claude-sonnet-4-5", 200),  # inclus à 30 seulement
        _assistant(d(40), "claude-opus-5-5", 999),    # toujours exclu
    ]
    side = [{**_assistant(t, "claude-haiku-4-5", 30), "isSidechain": True, "agentId": "a1"}]
    base = Path(base)
    (base / "s1" / "subagents").mkdir(parents=True, exist_ok=True)
    (base / "s1.jsonl").write_text("".join(json.dumps(e) + "\n" for e in main) + "{ligne cassée\n", encoding="utf-8")
    (base / "s1" / "subagents" / "agent-a1.jsonl").write_text(json.dumps(side[0]) + "\n", encoding="utf-8")
    return base


def project_dir(checkout: Path) -> Path:  # même règle que usage_report.project_dir
    return Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(Path(checkout).resolve()))


def _rmtree(p: Path):
    if p.exists():  # .git contient des fichiers en lecture seule sous Windows
        shutil.rmtree(p, onerror=lambda f, path, _: (os.chmod(path, stat.S_IWRITE), f(path)))


def reset(dest: Path, changes: int) -> Path:
    _rmtree(dest)
    _rmtree(project_dir(dest))
    root = depot(dest, changes)
    transcripts(project_dir(dest))
    return root


def check(dest: Path, changes: int) -> list[str]:
    root, errs = dest / ".hosa" / "kb", []
    for rel in KB:
        if not (root / rel).is_file():
            errs.append(f"manque {rel}")
    extra = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} - set(KB)
    allowed = {"cdc/brouillon.md", "brouillons/a.md", "brouillons/b.md"}
    if extra - allowed:
        errs.append(f"fichiers en trop : {sorted(extra - allowed)}")
    st = subprocess.run(["git", "-C", str(root), "status", "--short"], capture_output=True, text=True)
    n = len(st.stdout.splitlines())
    if st.returncode or n != changes:
        errs.append(f"git status : {n} changement(s), attendu {changes}")
    if (dest / ".hosa" / "graph").exists():
        errs.append(".hosa/graph existe (graphe à reconstruire à la volée)")
    if not (project_dir(dest) / "s1.jsonl").is_file():
        errs.append("transcripts absents")
    return errs


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dest", nargs="?", type=Path, default=DEST)
    ap.add_argument("--changes", type=int, default=3, choices=range(len(CHANGES) + 1))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    dest = a.dest.resolve()
    if not a.check:
        print(f"HOSA_KB_ROOT={reset(dest, a.changes)}")
    errs = check(dest, a.changes)
    print("\n".join(errs) or "OK : état de référence")
    sys.exit(1 if errs else 0)
