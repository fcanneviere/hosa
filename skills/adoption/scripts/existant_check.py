#!/usr/bin/env python3
"""The proofs of the `adoption` stage: a project whose code exists before Hosa is read, judged, and nothing it
does is lost on the way to the cahier des charges and the backlog.

  existant_check.py <kb> inventaire   `kb/existant/inventaire.md` (`type: Inventaire Existant`): each section
                                      written; at least one process `EXn`, each with its `Code :` paths (they
                                      exist under the project's root, a `:line` within the file), its `Rôles :`
                                      and its `État :` (complet, partiel or cassé, the last two with what is
                                      missing); each stack line with its `source :` path; each role with its
                                      `persona :` (a persona's file, or `aucun`); each documentation file of the
                                      project (Markdown, reStructuredText, AsciiDoc, a README or CHANGELOG, what
                                      `docs/`, `doc/` or `wiki/` hold) listed under `## Documentation constatée`
                                      with its `cible :` in Hosa's layout (or `aucune — <raison>`) and its `état :`
  existant_check.py <kb> diagnostic   `kb/existant/diagnostic.md` (`type: Diagnostic Existant`): `## Sources`
                                      links files that exist; each strength cites its code; each problem `Dn` has
                                      its severity, its code, its source and a `Proposition :`
  existant_check.py <kb> adoption     both, `documentation`, the identity's `## Point de départ` is `Existant`, and each problem
                                      has the user's `Décision :` (a Bloquant accepted names its reason)
  existant_check.py <kb> documentation  each target of `## Documentation constatée` is rebuilt: the file exists,
                                      and its entry in `kb/documentation/` (`technique-installation.md`, for a root
                                      file `racine-readme.md`) cites the source file (`hosa-documentation` Mode 4)
  existant_check.py <kb> stack        each line of `## Stack constatée` is taken over in `kb/stack/existant.md`
                                      (`type: Stack Decision`) `## Stack reprise`, by its `source :` path:
                                      `conservé`, or `remplacé par <x>` with its `raison :` (a `Dn` the user
                                      decided `corriger`, or an exigence's link) and its `migration :` cost
  existant_check.py <kb> infra        the tests of `## Tests constatés` run once in the container: `kb/infra/
                                      environnement-docker.md` `## Tests existants` gives the first run's counts,
                                      and each failing test (its file exists) its problem `Dn` (`source : tests`,
                                      the user's `Décision :`) and how the suite sets it aside (`exclu :`)
  existant_check.py <kb> schema-db    each line of `## Données constatées` is taken over in `kb/infra/schema-base-de-
                                      donnees.md` `## Données reprises`, by its source path: `conservée`; `modifiée`
                                      with its new `migration :` file (it exists) and its `reprise :` (what the rows
                                      already stored become); `supprimée` with its `raison :` (a `Dn` decided
                                      `corriger`, an exigence's link) and its `reprise :`
  existant_check.py <kb> architecture each line of `## Architecture constatée` is taken over in `kb/infra/architecture-
                                      existante.md` (`type: Infra`) `## Architecture reprise`, by its path:
                                      `conservé`, `étendu — <ce qui s'ajoute>`, or `remplacé par <x>` with its
                                      `raison :` (a `Dn` decided `corriger`, an exigence's link) and its `migration :`
  existant_check.py <kb> interface    each screen of `## Interface constatée` is taken over in `kb/interface/
                                      navigation.md` `## Écrans repris`, by its source path: `conservé`; `remplacé
                                      par <écran>` (a screen of `## Écrans`); `supprimé` with its `raison :`
  existant_check.py <kb> fondamentaux each line of `## Fondamentaux constatés` (a basic function the code already
                                      has) is in `kb/cdc/fondamentaux.md` `## Bilan`, by its source path: `Existant :`
                                      with the link of the exigence that describes it (it exists), or `Supprimé` with
                                      its `raison :` (a `Dn` decided `corriger`, an exigence's link)
  existant_check.py <kb> securite     each problem `Dn` of `source : sécurité` is in `kb/cdc/securite.md` `## Failles
                                      existantes` with the user's decision as it is: `corriger` with the link of the
                                      exigence or the rule that fixes it, `accepter` or `plus tard` with its `risque :`
  existant_check.py <kb> menaces      the same `Dn` in `kb/securite/modele-menaces.md` `## Failles existantes`:
                                      `corriger` with its `atténuation :`, `accepter` or `plus tard` with its `résiduel :`
  existant_check.py <kb> interview    each `EXn` is cited by a compte rendu of `kb/cdc/interviews/`
  existant_check.py <kb> cdc          each `EXn` is cited by an exigence's `existant:` field, unless a compte
                                      rendu marks it `abandonné`
  existant_check.py <kb> backlog      each `Dn` decided `corriger` is cited by a ticket's `diagnostic:` field
                                      ; each `EXn` kept (not `abandonné`) complet or partiel has a ticket
                                      `state: done` with `existant: [EXn]`, each criterion of it proved under
                                      `## Preuve` by a test or the code (`- CA1 — tests/test_x.py` in backticks, which
                                      exists); each partiel or cassé one a `todo` ticket for what is missing; a
                                      `todo` ticket citing an `EXn` says what it changes (`## Écart à l'existant`)

No `kb/existant/inventaire.md` → the downstream checks (`fondamentaux` to `backlog`) have nothing to check (a new project).
The project's root is the KB's (`<root>/.hosa/kb`), or `--root`.

  - **EX1** — <ce que le logiciel fait, en mots de métier>
    - Code : `src/commandes/vues.py:40`, `templates/commandes.html`
    - Rôles : <rôle constaté>
    - Données : <objets lus ou écrits>
    - État : complet | partiel — <ce qui manque> | cassé — <la preuve>
  - **D1** — Bloquant | À corriger | Mineur — `src/x.py:12` — <problème> — source : qualité | sécurité | bdd | inventaire
    - Proposition : corriger | accepter | plus tard — <raison>
    - Décision : corriger | accepter | plus tard — <raison, dite par l'utilisateur>
  - `docs/install.md` — installation — cible : `docs/technique/installation.md` — état : périmé — <l'écart au code>
  - `LICENSE.md` — licence — cible : aucune — <pourquoi il reste tel quel>
  - Django 5.1 — source : `requirements.txt:1` — conservé
  - SQLite 3 — source : `settings.py:80` — remplacé par PostgreSQL 16 — raison : D4 — migration : <coût>
  - Premier lancement : `pytest` — 42 tests — 40 passés — 2 en échec
  - `tests/test_export.py::test_dates` — AssertionError — D7 — exclu : `xfail(strict=True, reason="D7")`
  - commande — source : `src/modeles.py:20` — conservée
  - client — source : `src/modeles.py:40` — modifiée — migration : `migrations/0007_client_email.py` — reprise : <ce
    que deviennent les lignes déjà stockées>
  - panier — source : `src/modeles.py:60` — supprimée — raison : D5 — reprise : <archivées, exportées>
  - vues — `src/vues/` — étendu — <ce qui s'ajoute>
  - accès aux données — `src/dao/` — remplacé par l'ORM — raison : D3 — migration : <ce qui bouge, son coût>
  - Liste des commandes — source : `templates/commandes/liste.html` — conservé
  - Export CSV — source : `templates/export.html` — supprimé — raison : D6
  - Socle comptes — Existant : `src/comptes/` — [exigence](connexion.md)
  - **D1** — mots de passe en MD5 — corriger : [exigence](hachage-mots-de-passe.md)
  - **D2** — pas de limite de tentatives — plus tard — risque : <ce qui reste exposé, jusqu'à quand>
  - **D1** — formulaire de connexion — S — corriger — atténuation : <le contrôle, son module>

HOSA_ADOPTION=0 turns the checks off. Exit: 0 complete, 1 gaps (`✗` lines), 2 bad invocation. Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

INVENTAIRE, DIAGNOSTIC, STACK = "existant/inventaire.md", "existant/diagnostic.md", "stack/existant.md"
INFRA = "infra/environnement-docker.md"
SCHEMA = "infra/schema-base-de-donnees.md"
ARCHI, NAVIGATION = "infra/architecture-existante.md", "interface/navigation.md"
FONDA, SECU, MENACES = "cdc/fondamentaux.md", "cdc/securite.md", "securite/modele-menaces.md"
SECTIONS = ("Périmètre lu", "Stack constatée", "Processus constatés", "Rôles constatés", "Données constatées",
            "Architecture constatée", "Interface constatée", "Fondamentaux constatés", "Tests constatés")
STATES = ("complet", "partiel", "cassé")
SEVERITIES = ("Bloquant", "À corriger", "Mineur")
SOURCES = ("qualité", "sécurité", "bdd", "inventaire", "tests")
CHOICES = ("corriger", "accepter", "plus tard")
ITEM = re.compile(r"^-\s+\*\*((?:EX|D)\d+)\*\*\s*—\s*(.*)$")
SUB = re.compile(r"^\s+-\s+(?:\*\*)?([^:*]+?)(?:\*\*)?\s*:\s*(.*)$")
CODE = re.compile(r"`([^`\s]+?)(?::(\d+))?`")
DOC_EXT = {".md", ".markdown", ".rst", ".adoc", ".asciidoc"}
DOC_DIRS = {"docs", "doc", "documentation", "wiki"}
DOC_NAMES = ("readme", "changelog", "contributing", "history", "news", "authors")
SKIP_DIRS = {"node_modules", "vendor", "venv", "env", "dist", "build", "target", "__pycache__", "site-packages",
             "coverage"}
# where a rebuilt document goes (agents/documentation.md, File Layout)
TARGETS = (re.compile(r"^docs/(technique|fonctionnel|decisions)/[\w.-]+\.md$"),
           re.compile(r"^(CHANGELOG|README|CLAUDE)\.md$"))


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


def section(text: str | None, heading: str) -> list[str]:
    out, inside = [], False
    for line in (text or "").splitlines():
        if line.startswith("## "):
            inside = line[3:].strip() == heading
            continue
        if inside:
            out.append(line)
    return out


def has_section(text: str, heading: str) -> bool:
    return any(line.startswith("## ") and line[3:].strip() == heading for line in text.splitlines())


def of_type(text: str, ctype: str) -> bool:
    return bool(re.search(rf"^type:\s*[\"']?{re.escape(ctype)}[\"']?\s*$", text, re.M))


def front(text: str) -> str:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    return m[1] if m else ""


def items(lines: list[str]) -> list[tuple[str, str, dict[str, str]]]:
    """[(EXn or Dn, its first line, {field: value})]."""
    out: list[tuple[str, str, dict[str, str]]] = []
    for line in lines:
        if m := ITEM.match(line):
            out.append((m[1], m[2].strip(), {}))
        elif out and (f := SUB.match(line)):
            out[-1][2][f[1].strip()] = f[2].strip()
    return out


def written(lines: list[str]) -> bool:
    return any(re.match(r"^\s*(-\s+\S|Aucun)", x) for x in lines)


def code_gaps(root: Path, where: str, text: str) -> list[str]:
    """Each `path` or `path:line` cited exists under the project's root."""
    gaps, cited = [], CODE.findall(text)
    if not cited:
        return [f"{where} : aucun chemin de code entre backticks (`chemin:ligne`)"]
    for rel, line in cited:
        f = root / rel
        if not f.exists():
            gaps.append(f"{where} : `{rel}` absent de `{root.as_posix()}` — chemin à corriger")
        elif line and f.is_file():
            n = len((read(f) or "").splitlines())
            if int(line) > n:
                gaps.append(f"{where} : `{rel}:{line}` au-delà de la fin du fichier ({n} lignes)")
    return gaps


def choice(value: str) -> str | None:
    head = value.split("—", 1)[0].strip().lower()
    return head if head in CHOICES else None


def inventaire_gaps(kb: Path, root: Path) -> list[str]:
    text = read(kb / INVENTAIRE)
    if text is None or not of_type(text, "Inventaire Existant"):
        return [f"pas de `kb/{INVENTAIRE}` (`type: Inventaire Existant`) — `hosa-analyst` Mode 1"]
    gaps = [f"`## {h}` vide ou absente (une ligne `- …`, ou « Aucun. »)" for h in SECTIONS
            if not written(section(text, h))]
    processes = [i for i in items(section(text, "Processus constatés")) if i[0].startswith("EX")]
    if not processes:
        gaps.append("aucun processus `- **EX1** — …` sous `## Processus constatés`")
    for ex, _, f in processes:
        gaps += code_gaps(root, f"{ex} `Code :`", f.get("Code", "")) if f.get("Code") else [f"{ex} : pas de `Code :`"]
        if not f.get("Rôles"):
            gaps.append(f"{ex} : pas de `Rôles :` (qui le fait, d'après le code)")
        state = f.get("État", "")
        head = state.split("—", 1)[0].strip().lower()
        if head not in STATES:
            gaps.append(f"{ex} : `État :` doit être complet, partiel ou cassé")
        elif head != "complet" and not state.split("—", 1)[1:]:
            gaps.append(f"{ex} : `État : {head}` sans ce qui manque (`— <ce qui manque ou la preuve>`)")
    for line in section(text, "Stack constatée"):
        if re.match(r"^-\s+\S", line) and not line.lstrip("- ").startswith("Aucun"):
            m = re.search(r"source\s*:\s*(.*)$", line)
            gaps += code_gaps(root, "`## Stack constatée`", m[1]) if m else \
                [f"`## Stack constatée` : « {line.strip()[:60]} » sans `source : \\`fichier:ligne\\``"]
    for heading, what in (("Interface constatée", "gabarit ou composant"), ("Fondamentaux constatés", "fichier:ligne")):
        for line in section(text, heading):
            if re.match(r"^-\s+\S", line) and not line.lstrip("- ").startswith("Aucun"):
                m = re.search(r"source\s*:\s*(.*)$", line)
                gaps += code_gaps(root, f"`## {heading}`", m[1]) if m else \
                    [f"`## {heading}` : « {line.strip()[:60]} » sans `source : \\`{what}\\``"]
    gaps += doc_listing_gaps(kb, root)
    for line in section(text, "Rôles constatés"):
        if re.match(r"^-\s+\S", line) and not line.lstrip("- ").startswith("Aucun"):
            m = re.search(r"persona\s*:\s*(.*)$", line)
            if not m:
                gaps.append(f"`## Rôles constatés` : « {line.strip()[:60]} » sans `persona :` (un persona, ou aucun)")
            elif (link := re.search(r"\]\(([^)]+)\)", m[1])) and not (kb / "existant" / link[1]).resolve().is_file():
                gaps.append(f"`## Rôles constatés` : persona `{link[1]}` absent")
    return gaps


def diagnostic_gaps(kb: Path, root: Path) -> list[str]:
    text = read(kb / DIAGNOSTIC)
    if text is None or not of_type(text, "Diagnostic Existant"):
        return [f"pas de `kb/{DIAGNOSTIC}` (`type: Diagnostic Existant`) — `hosa-analyst` Mode 2"]
    gaps = [f"`## {h}` absente" for h in ("Sources", "Points forts", "Problèmes") if not has_section(text, h)]
    links = re.findall(r"\]\(([^)]+)\)", "\n".join(section(text, "Sources")))
    if not links:
        gaps.append("`## Sources` ne lie aucun audit (`[Audit qualité](../qualite/adoption.md)`)")
    gaps += [f"`## Sources` : `{p}` absent" for p in links if not (kb / "existant" / p).resolve().is_file()]
    for line in section(text, "Points forts"):
        if re.match(r"^-\s+\S", line) and not line.lstrip("- ").startswith("Aucun"):
            gaps += code_gaps(root, f"point fort « {line.strip()[2:40]} »", line)
    for d, first, f in items(section(text, "Problèmes")):
        parts = [p.strip() for p in first.split("—")]
        if not parts or parts[0] not in SEVERITIES:
            gaps.append(f"{d} : gravité Bloquant, À corriger ou Mineur en premier")
        gaps += code_gaps(root, d, first)
        if not re.search(r"source\s*:\s*(" + "|".join(SOURCES) + r")\b", first):
            gaps.append(f"{d} : pas de `source :` ({', '.join(SOURCES)})")
        if not choice(f.get("Proposition", "")):
            gaps.append(f"{d} : `Proposition :` doit être corriger, accepter ou plus tard, avec sa raison")
    return gaps


def doc_files(root: Path) -> list[str]:
    """The project's documentation files, relative to its root, outside hidden, tooling and dependency folders."""
    out = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d.lower() not in SKIP_DIRS and not d.startswith("."))
        rel_dir = Path(dirpath).relative_to(root)
        in_docs = bool({p.lower() for p in rel_dir.parts} & DOC_DIRS)
        for f in sorted(files):
            ext, stem = Path(f).suffix.lower(), Path(f).stem.lower()
            named = stem.startswith(DOC_NAMES) and ext in ("", ".txt")
            if ext in DOC_EXT or named or (in_docs and ext == ".txt"):
                out.append((rel_dir / f).as_posix())
    return out


def doc_lines(kb: Path) -> list[tuple[str, str, str]]:
    """[(source path, target path or `aucune` or "", the line)] of `## Documentation constatée`."""
    out = []
    for line in section(read(kb / INVENTAIRE), "Documentation constatée"):
        if m := re.match(r"^-\s+`([^`]+)`", line):
            c = re.search(r"cible\s*:\s*(?:`([^`]+)`|(aucune))", line)
            out.append((m[1], (c[1] or c[2]) if c else "", line))
    return out


def register_name(target: str) -> str:
    """`docs/technique/installation.md` → `technique-installation.md` (agents/documentation.md, File Layout);
    `README.md` → `racine-readme.md`."""
    m = re.match(r"^docs/(technique|fonctionnel|decisions)/([\w.-]+)\.md$", target)
    return f"{m[1]}-{m[2].lower()}.md" if m else f"racine-{Path(target).stem.lower()}.md"


def doc_listing_gaps(kb: Path, root: Path) -> list[str]:
    listed = {src: (tgt, line) for src, tgt, line in doc_lines(kb)}
    gaps = [f"`{f}` (documentation existante) absent de `## Documentation constatée` — à lister avec sa `cible :`"
            for f in doc_files(root) if f not in listed]
    for src, (tgt, line) in listed.items():
        if not (root / src).is_file():
            gaps.append(f"`## Documentation constatée` : `{src}` absent du projet")
        if not tgt:
            gaps.append(f"`{src}` : pas de `cible :` (un fichier de `docs/technique|fonctionnel|decisions/`, "
                        "`README.md`, `CHANGELOG.md`, `CLAUDE.md`, ou `aucune — <raison>`)")
        elif tgt == "aucune":
            if not re.search(r"cible\s*:\s*aucune\s*—\s*\S", line):
                gaps.append(f"`{src}` : `cible : aucune` sans sa raison")
        else:
            if not any(r.match(tgt) for r in TARGETS):
                gaps.append(f"`{src}` : cible `{tgt}` hors de l'arborescence de Hosa (`docs/technique/`, "
                            "`docs/fonctionnel/`, `docs/decisions/`, `README.md`, `CHANGELOG.md`, `CLAUDE.md`)")
            if not re.search(r"état\s*:\s*(à jour|périmé\s*—\s*\S)", line):
                gaps.append(f"`{src}` : `état :` à jour, ou périmé avec son écart au code")
    return gaps


def documentation_gaps(kb: Path, root: Path) -> list[str]:
    gaps = []
    for src, tgt, _ in doc_lines(kb):
        if not tgt or tgt == "aucune":
            continue
        if not (root / tgt).is_file():
            gaps.append(f"`{src}` → `{tgt}` pas encore reconstruit (`hosa-documentation` Mode 4)")
            continue
        entry = read(kb / "documentation" / register_name(tgt))
        if entry is None:
            gaps.append(f"`{tgt}` sans son entrée `kb/documentation/{register_name(tgt)}` (sources, date de "
                        "synchronisation)")
        elif src not in entry:
            gaps.append(f"`kb/documentation/{register_name(tgt)}` ne cite pas `{src}` dans ses sources : la "
                        "documentation existante n'a pas été reprise")
    return gaps


def problems(kb: Path) -> list[tuple[str, str, dict[str, str]]]:
    return items(section(read(kb / DIAGNOSTIC), "Problèmes"))


def existing(kb: Path) -> bool:
    """The identity's `## Point de départ` says `Existant` (its first line, the template's « Neuf | Existant » aside)."""
    lines = [x.strip() for x in section(read(kb / "project" / "identity.md"), "Point de départ") if x.strip()]
    return bool(lines) and lines[0].lower().startswith("existant")


def adoption_gaps(kb: Path, root: Path) -> list[str]:
    gaps = [] if existing(kb) else ["`kb/project/identity.md` : `## Point de départ` n'est pas `Existant` "
                                    "(projet neuf → `skip adoption`)"]
    gaps += inventaire_gaps(kb, root) + documentation_gaps(kb, root) + diagnostic_gaps(kb, root)
    for d, first, f in problems(kb):
        decided = f.get("Décision", "")
        if not choice(decided):
            gaps.append(f"{d} : pas de `Décision :` de l'utilisateur (corriger, accepter ou plus tard)")
        elif first.startswith("Bloquant") and choice(decided) == "accepter" and not decided.split("—", 1)[1:]:
            gaps.append(f"{d} : Bloquant accepté sans sa raison (`Décision : accepter — <raison>`)")
    return gaps


def stack_gaps(kb: Path) -> list[str]:
    """Nothing of the stack in place is dropped or swapped in silence: each element is kept, or replaced for a reason
    the user decided (a problem to fix, an exigence) at a stated migration cost. Matched by its `source :` path."""
    found = [(x.strip(), CODE.findall(x.split("source", 1)[1])) for x in section(read(kb / INVENTAIRE), "Stack constatée")
             if re.match(r"^-\s+\S", x) and not x.lstrip("- ").startswith("Aucun") and "source" in x]
    if not found:
        return []
    text = read(kb / STACK)
    if text is None or not of_type(text, "Stack Decision"):
        return [f"pas de `kb/{STACK}` (`type: Stack Decision`) : chaque élément de `## Stack constatée`, "
                "conservé ou remplacé, sous `## Stack reprise`"]
    rows = [x.strip() for x in section(text, "Stack reprise") if re.match(r"^-\s+\S", x)]
    gaps = []
    for line, cited in found:
        name = line.lstrip("- ").split(" — ")[0][:60]
        keys = [f"`{rel}:{n}`" if n else f"`{rel}`" for rel, n in cited]
        row = next((r for r in rows if any(k in r for k in keys)), None)
        if row is None:
            gaps.append(f"« {name} » ({', '.join(keys) or 'sans source'}) absent de `## Stack reprise` de "
                        f"`kb/{STACK}` — `conservé`, ou `remplacé par <x> — raison : <Dn|exigence> — migration : <coût>`")
            continue
        verdict = re.search(r"—\s*(conservé|remplacé)\b", row, re.I)
        if not verdict:
            gaps.append(f"« {name} » : ni `conservé` ni `remplacé par <x>` dans `## Stack reprise`")
        elif verdict[1].lower() == "remplacé":
            if reason_gap(kb, row):
                gaps.append(f"« {name} » remplacé sans `raison :` — un problème que l'utilisateur a décidé de "
                            "corriger (`Dn`), ou le lien d'une exigence ; « mieux » ne suffit pas, le code en dépend")
            if not re.search(r"migration\s*:\s*\S", row):
                gaps.append(f"« {name} » remplacé sans `migration :` — ce que la migration coûte (fichiers, données)")
    return gaps


RUN = re.compile(r"(\d+)\s*tests?\b.*?(\d+)\s*pass[ée]s?\b.*?(\d+)\s*en échec", re.I)


def infra_gaps(kb: Path, root: Path) -> list[str]:
    """The existing tests run once in the container before any sprint. Each failure is a problem the user decides,
    set aside under its `Dn`: the suite is green for the first sprint, and no failure is hidden or fixed in silence."""
    found = [x for x in section(read(kb / INVENTAIRE), "Tests constatés")
             if re.match(r"^-\s+\S", x) and not x.lstrip("- ").startswith("Aucun")]
    if not found:
        return []
    text = read(kb / INFRA)
    if text is None or not has_section(text, "Tests existants"):
        return [f"`kb/{INFRA}` sans `## Tests existants` : les tests de `## Tests constatés` lancés une fois dans le "
                "conteneur (`- Premier lancement : <commande> — <n> tests — <p> passés — <f> en échec`)"]
    lines = [x.strip() for x in section(text, "Tests existants") if re.match(r"^-\s+\S", x)]
    first = next((x for x in lines if x.lstrip("- ").lower().startswith("premier lancement")), None)
    run = RUN.search(first) if first else None
    if not run:
        return ["`## Tests existants` : pas de ligne `- Premier lancement : <commande> — <n> tests — <p> passés — "
                "<f> en échec`"]
    total, passed, failed = map(int, run.groups())
    gaps = [] if passed + failed <= total else [f"`Premier lancement` : {passed} passés + {failed} en échec > {total} tests"]
    rows = [x for x in lines if x is not first]
    if len(rows) != failed:
        gaps.append(f"`## Tests existants` : {failed} en échec annoncés, {len(rows)} listés — une ligne par test "
                    "(`- <fichier::test> — <erreur> — Dn — exclu : <comment>`)")
    decided = {d: f for d, _, f in problems(kb)}
    firsts = {d: first for d, first, _ in problems(kb)}
    for row in rows:
        m = re.match(r"^-\s+`([^`]+)`", row)
        if not m:
            gaps.append(f"`## Tests existants` : « {row[:60]} » sans le test entre backticks (`fichier::test`)")
            continue
        test, rel = m[1], re.split(r"::|:(?=\D)| ", m[1])[0]
        if not (root / rel).exists():
            gaps.append(f"`{test}` : `{rel}` absent de `{root.as_posix()}`")
        ds = re.findall(r"\bD\d+\b", row)
        if not ds:
            gaps.append(f"`{test}` en échec sans son problème `Dn` dans `kb/{DIAGNOSTIC}` (`source : tests`)")
        for d in ds:
            if d not in decided:
                gaps.append(f"`{test}` : {d} absent de `## Problèmes` de `kb/{DIAGNOSTIC}`")
            elif not re.search(r"source\s*:\s*tests\b", firsts[d]):
                gaps.append(f"{d} : `source : tests` attendu (le test `{test}` en échec)")
            elif not choice(decided[d].get("Décision", "")):
                gaps.append(f"{d} (`{test}` en échec) : pas de `Décision :` de l'utilisateur (corriger, accepter ou "
                            "plus tard)")
        if not re.search(r"exclu\s*:\s*\S", row):
            gaps.append(f"`{test}` : sans `exclu :` — comment la suite l'écarte sous son {ds[0] if ds else 'Dn'} "
                        "(marqueur d'échec attendu, désélection), pour une suite verte sans le cacher")
    return gaps


def reason_gap(kb: Path, row: str) -> bool:
    """No `raison :` the user decided: a `Dn` decided `corriger`, or the link of an exigence that exists."""
    fix = {d for d, _, f in problems(kb) if choice(f.get("Décision", "")) == "corriger"}
    reason = re.search(r"raison\s*:\s*(.*?)\s*(?:—|$)", row)
    ds = set(re.findall(r"\bD\d+\b", reason[1])) if reason else set()
    link = re.search(r"\]\(\.\./(cdc/[^)]+\.md)\)", reason[1]) if reason else None
    return not (ds & fix or (link and (kb / link[1]).is_file()))


def schema_db_gaps(kb: Path, root: Path) -> list[str]:
    """The data the existing code already stores is not lost: each table or model is kept, changed by a new migration
    that says what the stored rows become, or dropped for a reason the user decided. Matched by its source path."""
    found = [(x.strip(), CODE.findall(x)) for x in section(read(kb / INVENTAIRE), "Données constatées")
             if re.match(r"^-\s+\S", x) and not x.lstrip("- ").startswith("Aucun") and CODE.search(x)]
    if not found:
        return []
    text = read(kb / SCHEMA)
    rows = [x.strip() for x in section(text, "Données reprises") if re.match(r"^-\s+\S", x)] if text else []
    if not rows:
        return [f"`kb/{SCHEMA}` sans `## Données reprises` : chaque ligne de `## Données constatées`, `conservée`, "
                "`modifiée` ou `supprimée`, par son chemin source"]
    gaps = []
    for line, cited in found:
        name = line.lstrip("- ").split(" — ")[0][:60]
        keys = [f"`{rel}:{n}`" if n else f"`{rel}`" for rel, n in cited]
        row = next((r for r in rows if any(k in r for k in keys)), None)
        if row is None:
            gaps.append(f"« {name} » ({', '.join(keys)}) absent de `## Données reprises` de `kb/{SCHEMA}` — "
                        "`conservée`, `modifiée — migration : <fichier> — reprise : <…>` ou `supprimée — raison : "
                        "<Dn|exigence> — reprise : <…>`")
            continue
        verdict = re.search(r"—\s*(conservée|modifiée|supprimée)\b", row, re.I)
        if not verdict:
            gaps.append(f"« {name} » : ni `conservée`, ni `modifiée`, ni `supprimée` dans `## Données reprises`")
            continue
        kind = verdict[1].lower()
        if kind == "conservée":
            continue
        if not re.search(r"reprise\s*:\s*\S", row):
            gaps.append(f"« {name} » {kind} sans `reprise :` — ce que deviennent les lignes déjà stockées")
        if kind == "modifiée":
            mig = re.search(r"migration\s*:\s*`([^`]+)`", row)
            if not mig:
                gaps.append(f"« {name} » modifiée sans `migration :` — la nouvelle migration entre backticks ; "
                            "une migration déjà appliquée ne change jamais")
            elif not (root / mig[1]).is_file():
                gaps.append(f"« {name} » : migration `{mig[1]}` absente de `{root.as_posix()}`")
        elif reason_gap(kb, row):
            gaps.append(f"« {name} » supprimée sans `raison :` — un problème que l'utilisateur a décidé de corriger "
                        "(`Dn`), ou le lien d'une exigence ; les lignes stockées en dépendent")
    return gaps


def found_in(kb: Path, heading: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """The lines of an inventory section that cite code, each with its cited paths (after `source :` when given)."""
    return [(x.strip(), CODE.findall(x.split("source", 1)[-1])) for x in section(read(kb / INVENTAIRE), heading)
            if re.match(r"^-\s+\S", x) and not x.lstrip("- ").startswith("Aucun") and CODE.search(x)]


def matched(line: str, cited: list[tuple[str, str]], rows: list[str]) -> tuple[str, list[str], str | None]:
    name = line.lstrip("- ").split(" — ")[0][:60]
    keys = [f"`{rel}:{n}`" if n else f"`{rel}`" for rel, n in cited]
    return name, keys, next((r for r in rows if any(k in r for k in keys)), None)


def architecture_gaps(kb: Path) -> list[str]:
    """The architecture in place is extended, not redrawn: each layer or module is kept, extended, or replaced for a
    reason the user decided (a problem to fix, an exigence) with what moves. Matched by its path."""
    found = found_in(kb, "Architecture constatée")
    if not found:
        return []
    text = read(kb / ARCHI)
    rows = [x.strip() for x in section(text, "Architecture reprise") if re.match(r"^-\s+\S", x)] if text else []
    if not rows:
        return [f"`kb/{ARCHI}` (`type: Infra`) sans `## Architecture reprise` : chaque ligne de `## Architecture "
                "constatée`, `conservé`, `étendu` ou `remplacé par <x>`, par son chemin"]
    gaps = []
    for line, cited in found:
        name, keys, row = matched(line, cited, rows)
        if row is None:
            gaps.append(f"« {name} » ({', '.join(keys)}) absent de `## Architecture reprise` de `kb/{ARCHI}` — "
                        "`conservé`, `étendu — <ce qui s'ajoute>` ou `remplacé par <x> — raison : <Dn|exigence> — "
                        "migration : <…>`")
            continue
        verdict = re.search(r"—\s*(conservée?|étendue?|remplacée?\s+par)\b", row, re.I)
        if not verdict:
            gaps.append(f"« {name} » : ni `conservé`, ni `étendu`, ni `remplacé par <x>` dans `## Architecture reprise`")
        elif verdict[1].lower().startswith("étendu") and not re.search(r"étendue?\s*—\s*\S", row, re.I):
            gaps.append(f"« {name} » étendu sans ce qui s'ajoute (`étendu — <modules, chemins>`)")
        elif verdict[1].lower().startswith("remplacé"):
            if reason_gap(kb, row):
                gaps.append(f"« {name} » remplacé sans `raison :` — un problème que l'utilisateur a décidé de "
                            "corriger (`Dn`), ou le lien d'une exigence ; « plus propre » ne suffit pas, le code en dépend")
            if not re.search(r"migration\s*:\s*\S", row):
                gaps.append(f"« {name} » remplacé sans `migration :` — ce qui bouge, et son coût")
    return gaps


def ecrans_gaps(kb: Path) -> list[str]:
    """No screen the users already have disappears in silence: each one is kept, replaced by a screen of the new
    navigation, or dropped for a reason the user decided. Matched by its source path."""
    found = found_in(kb, "Interface constatée")
    if not found:
        return []
    text = read(kb / NAVIGATION)
    rows = [x.strip() for x in section(text, "Écrans repris") if re.match(r"^-\s+\S", x)] if text else []
    if not rows:
        return [f"`kb/{NAVIGATION}` sans `## Écrans repris` : chaque écran de `## Interface constatée`, `conservé`, "
                "`remplacé par <écran>` ou `supprimé`, par son chemin source"]
    screens = [x.strip().strip("|").split("|")[0].strip().lower() for x in section(text, "Écrans")
               if x.strip().startswith("|")]
    gaps = []
    for line, cited in found:
        name, keys, row = matched(line, cited, rows)
        if row is None:
            gaps.append(f"« {name} » ({', '.join(keys)}) absent de `## Écrans repris` de `kb/{NAVIGATION}` — "
                        "`conservé`, `remplacé par <écran>` ou `supprimé — raison : <Dn|exigence>`")
            continue
        verdict = re.search(r"—\s*(conservée?|remplacée?\s+par\s+(.+?)|supprimée?)\s*(?:—|$)", row, re.I)
        if not verdict:
            gaps.append(f"« {name} » : ni `conservé`, ni `remplacé par <écran>`, ni `supprimé` dans `## Écrans repris`")
        elif verdict[2]:
            target = verdict[2].strip().strip("«» \"'").strip().lower()
            if target not in screens:
                gaps.append(f"« {name} » remplacé par « {verdict[2].strip()} », absent du tableau `## Écrans` : "
                            "l'écran qui le remplace doit exister")
        elif verdict[1].lower().startswith("supprimé") and reason_gap(kb, row):
            gaps.append(f"« {name} » supprimé sans `raison :` — un problème que l'utilisateur a décidé de corriger "
                        "(`Dn`), ou le lien d'une exigence ; ses utilisateurs s'en servent")
    return gaps


def bullets(text: str | None, heading: str) -> list[str]:
    return [x.strip() for x in section(text, heading) if re.match(r"^-\s+\S", x)] if text else []


def fondamentaux_gaps(kb: Path) -> list[str]:
    """A basic function the code already has (accounts, administration, logs, backup, export) is taken over by an
    exigence, never written again beside it, or dropped for a reason the user decided. Matched by its source path."""
    found = found_in(kb, "Fondamentaux constatés")
    if not found:
        return []
    rows = bullets(read(kb / FONDA), "Bilan")
    if not rows:
        return [f"`kb/{FONDA}` sans `## Bilan` : chaque ligne de `## Fondamentaux constatés`, `Existant : <chemin> — "
                "[exigence](<slug>.md)` ou `Supprimé — raison : <Dn|exigence>`"]
    gaps = []
    for line, cited in found:
        name, keys, row = matched(line, cited, rows)
        if row is None:
            gaps.append(f"« {name} » ({', '.join(keys)}) absent du `## Bilan` de `kb/{FONDA}` — `Existant : "
                        f"{keys[0]} — [exigence](<slug>.md)` ou `Supprimé — raison : <Dn|exigence>`")
            continue
        verdict = re.search(r"—\s*(existant|supprimée?)\b", row, re.I)
        if not verdict:
            gaps.append(f"« {name} » : ni `Existant`, ni `Supprimé` dans le `## Bilan` — le code le fait déjà")
        elif verdict[1].lower() == "existant":
            links = re.findall(r"\]\(([^)/]+\.md)\)", row)
            if not any(of_type(read(kb / "cdc" / p) or "", "Exigence") for p in links):
                gaps.append(f"« {name} » existant sans l'exigence qui décrit ce que le code fait (`[exigence](<slug>.md)`, "
                            "dans `kb/cdc/`) — sans elle, une exigence neuve le refait à côté")
        elif reason_gap(kb, row):
            gaps.append(f"« {name} » supprimé sans `raison :` — un problème que l'utilisateur a décidé de corriger "
                        "(`Dn`), ou le lien d'une exigence ; ses utilisateurs s'en servent")
    return gaps


def failles(kb: Path) -> list[tuple[str, str | None]]:
    """[(Dn, the user's decision)] of the problems the security audit found in the existing code."""
    return [(d, choice(f.get("Décision", ""))) for d, first, f in problems(kb)
            if re.search(r"source\s*:\s*sécurité\b", first)]


def faille_gaps(kb: Path, rel: str, fix: str, rest: str) -> list[str]:
    """Each security flaw of the existing code is in `rel` `## Failles existantes` with the user's decision as it is:
    `corriger` with its `fix`, `accepter` or `plus tard` with what stays exposed (`rest`)."""
    known = failles(kb)
    if not known:
        return []
    rows = bullets(read(kb / rel), "Failles existantes")
    gaps = []
    for d, decided in known:
        row = next((r for r in rows if re.match(rf"^-\s+(?:\*\*)?{d}\b", r)), None)
        if row is None:
            gaps.append(f"{d} (faille du code existant, décision : {decided or '?'}) absent de `## Failles existantes` "
                        f"de `kb/{rel}` — le système en production y est exposé aujourd'hui")
            continue
        said = re.search(r"—\s*(corriger|accepter|plus tard)\b", row)
        if not said:
            gaps.append(f"{d} : ni `corriger`, ni `accepter`, ni `plus tard` dans `kb/{rel}`")
        elif decided and said[1] != decided:
            gaps.append(f"{d} : `{said[1]}` dans `kb/{rel}`, mais l'utilisateur a décidé `{decided}` — seule sa "
                        "décision vaut (`adoption`, Step 4)")
        elif said[1] == "corriger" and fix == "lien":
            links = re.findall(r"\]\(([^)]+\.md)\)", row)
            if not any((kb / "cdc" / p).resolve().is_file() for p in links):
                gaps.append(f"{d} à corriger sans la mesure qui le corrige : le lien d'une exigence ou d'une règle "
                            "de sécurité qui existe (`[exigence](<slug>.md)`, `[règle](../rules/security/<slug>.md)`)")
        elif said[1] == "corriger" and not re.search(rf"{fix}\s*:\s*\S", row):
            gaps.append(f"{d} à corriger sans `{fix} :` — le contrôle qui l'empêche dans l'architecture")
        elif said[1] != "corriger" and not re.search(rf"{rest}\s*:\s*\S", row):
            gaps.append(f"{d} {said[1]} sans `{rest} :` — ce qui reste exposé, et jusqu'à quand")
    return gaps


def processes(kb: Path) -> list[str]:
    return [i[0] for i in items(section(read(kb / INVENTAIRE), "Processus constatés")) if i[0].startswith("EX")]


def interviews(kb: Path) -> str:
    folder = kb / "cdc" / "interviews"
    return "\n".join(read(p) or "" for p in sorted(folder.glob("*.md"))) if folder.is_dir() else ""


def interview_gaps(kb: Path) -> list[str]:
    said = interviews(kb)
    return [f"{ex} (code existant) : aucun compte rendu de `kb/cdc/interviews/` ne le cite — à recueillir, ou "
            f"`({ex}, abandonné)` si l'utilisateur l'abandonne" for ex in processes(kb)
            if not re.search(rf"\b{ex}\b", said)]


def cdc_gaps(kb: Path) -> list[str]:
    said, cited = interviews(kb), set()
    for p in sorted((kb / "cdc").glob("*.md")) if (kb / "cdc").is_dir() else []:
        text = read(p) or ""
        if of_type(text, "Exigence"):
            m = re.search(r"^existant:\s*(.*)$", front(text), re.M)
            cited |= set(re.findall(r"\bEX\d+\b", m[1])) if m else set()
    return [f"{ex} (code existant) : aucune exigence ne le reprend (`existant: [{ex}]`), et aucun compte rendu ne "
            "le dit abandonné" for ex in processes(kb)
            if ex not in cited and not re.search(rf"\b{ex}\b[^\n]*abandonn", said)]


def body_section(text: str, heading: str) -> str | None:
    lines, inside, found = [], False, False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line[3:].strip() == heading
            found = found or inside
            continue
        if inside:
            lines.append(line)
    return "\n".join(lines) if found else None


def tickets(kb: Path) -> list[tuple[str, str, str]]:
    """[(slug, state, text)] of `kb/tickets/`."""
    out = []
    for p in sorted((kb / "tickets").glob("*.md")) if (kb / "tickets").is_dir() else []:
        text = read(p) or ""
        if of_type(text, "Ticket"):
            m = re.search(r"^state:\s*(\w+)", front(text), re.M)
            out.append((p.stem, m[1] if m else "todo", text))
    return out


def ids_of(text: str, key: str, pattern: str) -> set[str]:
    m = re.search(rf"^{key}:\s*(.*)$", front(text), re.M)
    return set(re.findall(pattern, m[1])) if m else set()


def proof_gaps(root: Path, slug: str, text: str) -> list[str]:
    """A delivered ticket of the existing code: each criterion proved by a test or the code, which exist."""
    proof = body_section(text, "Preuve")
    if proof is None:
        return [f"`{slug}` (livré, code existant) : pas de `## Preuve` (par critère : `- CA1 — <chemin du test>`)"]
    gaps = []
    crit = re.findall(r"^-\s+(CA\d+)\b", body_section(text, "Critères d'acceptation") or "", re.M)
    lines = {m[1]: m[2] for m in re.finditer(r"^-\s+(CA\d+)\b(.*)$", proof, re.M)}
    for ca in crit:
        if ca not in lines:
            gaps.append(f"`{slug}` {ca} : absent de `## Preuve` (le test ou le code qui le prouve)")
        else:
            gaps += code_gaps(root, f"`{slug}` {ca} `## Preuve`", lines[ca])
    return gaps


def backlog_gaps(kb: Path, root: Path | None = None) -> list[str]:
    root = root or kb.resolve().parent.parent
    all_tickets = tickets(kb)
    fixed = set().union(*(ids_of(t, "diagnostic", r"\bD\d+\b") for _, _, t in all_tickets)) if all_tickets else set()
    gaps = [f"{d} (décidé « corriger ») : aucun ticket ne le cite (`diagnostic: [{d}]`)" for d, _, f in problems(kb)
            if choice(f.get("Décision", "")) == "corriger" and d not in fixed]
    said = interviews(kb)
    states = {ex: f.get("État", "").split("—", 1)[0].strip().lower()
              for ex, _, f in items(section(read(kb / INVENTAIRE), "Processus constatés")) if ex.startswith("EX")}
    by = {"done": {}, "todo": {}}
    for slug, state, text in all_tickets:
        for ex in ids_of(text, "existant", r"\bEX\d+\b"):
            by["done" if state == "done" else "todo"].setdefault(ex, []).append((slug, text))
    for ex, state in states.items():
        if re.search(rf"\b{ex}\b[^\n]*abandonn", said):
            continue
        if state in ("complet", "partiel") and ex not in by["done"]:
            gaps.append(f"{ex} ({state}) : aucun ticket `state: done` ne reprend ce que le code fait déjà "
                        f"(`existant: [{ex}]`, `## Preuve`)")
        if state in ("partiel", "cassé") and ex not in by["todo"]:
            gaps.append(f"{ex} ({state}) : aucun ticket `todo` pour ce qui manque (`existant: [{ex}]`, "
                        "`## Écart à l'existant`)")
        for slug, text in by["todo"].get(ex, []):
            if not re.search(r"\S", body_section(text, "Écart à l'existant") or ""):
                gaps.append(f"`{slug}` (todo, {ex} {state or '?'}) : pas de `## Écart à l'existant` — ce que le "
                            "ticket change au code ; sans écart, il refait ce qui existe")
    for slug, state, text in all_tickets:
        if state == "done" and ids_of(text, "existant", r"\bEX\d+\b"):
            gaps += proof_gaps(root, slug, text)
    return gaps


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("kb", type=Path)
    downstream = ("fondamentaux", "securite", "stack", "infra", "schema-db", "architecture", "menaces", "interface",
                  "interview", "cdc", "backlog")
    ap.add_argument("action", choices=["inventaire", "diagnostic", "documentation", "adoption", *downstream])
    ap.add_argument("--root", type=Path)
    a = ap.parse_args(argv)
    if not a.kb.is_dir():
        print(f"error: {a.kb} is not a directory", file=sys.stderr)
        return 2
    root = a.root or a.kb.resolve().parent.parent
    if os.environ.get("HOSA_ADOPTION") == "0":
        print("✓ contrôle de l'existant coupé (HOSA_ADOPTION=0)")
        return 0
    if a.action in downstream and not (a.kb / INVENTAIRE).is_file():
        print("✓ pas de code existant adopté")
        return 0
    checks = {"inventaire": lambda: inventaire_gaps(a.kb, root), "diagnostic": lambda: diagnostic_gaps(a.kb, root),
              "documentation": lambda: documentation_gaps(a.kb, root),
              "adoption": lambda: adoption_gaps(a.kb, root), "stack": lambda: stack_gaps(a.kb), "infra": lambda: infra_gaps(a.kb, root),
              "schema-db": lambda: schema_db_gaps(a.kb, root), "architecture": lambda: architecture_gaps(a.kb),
              "interface": lambda: ecrans_gaps(a.kb), "interview": lambda: interview_gaps(a.kb),
              "fondamentaux": lambda: fondamentaux_gaps(a.kb),
              "securite": lambda: faille_gaps(a.kb, SECU, "lien", "risque"),
              "menaces": lambda: faille_gaps(a.kb, MENACES, "atténuation", "résiduel"),
              "cdc": lambda: cdc_gaps(a.kb), "backlog": lambda: backlog_gaps(a.kb, root)}
    gaps = checks[a.action]()
    for g in gaps:
        print(f"✗ {g}")
    print(f"{len(gaps)} manque(s)" if gaps else "✓ complet")
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
