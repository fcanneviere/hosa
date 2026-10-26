---
name: qualite
description: "Use to audit the managed project's code: best practices and performance (`hosa-senior-dev`), security (`hosa-security`), database (`hosa-dba`); blocking findings become tickets. Also the sprint audit (stage `audit`, after `develop`, before `qa`). Triggers: \"audite la qualité du code\", \"revue de sécurité du code\", \"audite le sprint\"."
---

# Qualité

Senior-dev and cybersecurity pass over the managed project's actual source code — not the cahier des charges, not the spec-compliance `review` skill, but "is this code sound and safe to run". Checks a fixed checklist of best practices and security rules, classifies anomalies, and routes blocking ones to a fix.

## Flow

```
Détermine le projet géré (kb/infra/)
        ↓
Détermine le scope : fichiers modifiés récemment (session/dernier
ticket), ou codebase entière si demandé explicitement
        ↓
hosa-senior-dev audite bonnes pratiques + performance, et
hosa-security audite la sécurité (règles de conception + imprévus)
        ↓
Classe chaque anomalie : Bloquant / À corriger / Mineur
        ↓
Écrit kb/qualite/<slug>.md (Audit Qualité) + log
        ↓
Bloquant trouvé → propose debug (audit de sprint :
`develop <ticket> correction`, puis ré-audit, puis `qa`)
        ↓
Rapporte le verdict
```

## Trigger

Manual: `/qualite`, `/qualite sprint <slug>` (the sprint's `audit` stage, chained by `develop`). Auto: "audite la qualité du code", "vérifie les bonnes pratiques", "fais une revue de sécurité du code", "check la sécurité du projet".

---

## Step 1: Find the Managed Project and Scope

Read `kb/infra/` for the managed project's root path (same as `stack` Step 1 — if missing, stop and say so, this skill has nothing to audit without it).

Scope: from `livraison`, the file list it gives (the code changed since the last release); this audit is then the release gate, and a Bloquant stops it. From the sprint's `audit` stage (Sprint Audit below), the files the sprint changed; a Bloquant stops the QA and the merge. Even on a scoped audit, `hosa-senior-dev` checks **Duplication** against the whole codebase: code a ticket copied from an existing file is only visible from outside the diff. If invoked right after a ticket/sprint was implemented, default to the files touched this session. Otherwise ask the user: "Codebase entière ou fichiers récents ?" — don't guess (Core Rule: no guessing).

## Step 2: Audit Checklist

Dispatch, on the same scope and in parallel, `hosa-senior-dev` (best practices and performance — its fixed checklist below; don't invent extra items, don't drop any without asking first) and — when the project has a database (`kb/infra/base-de-donnees.md`) — `hosa-dba` (Mode 4 Audit, `agents/dba.md`: migrations reversible and conflict-free, indexes against the queries actually run, least-privilege account, backups and their last restore test), and `hosa-security` (Mode 2, `agents/security.md`): conformity to the `Security Rule`s and security exigences set during the cahier des charges, then the unforeseen holes. Security constraints were designed in from the start (`securite`, then its threat model); this audit is the safety net for what nobody could foresee, and it also covers the supply chain and the secrets in the git history. If `kb/rules/security/` is empty because `securite` never ran, say so — the audit still runs on the baseline rules, but propose `securite` so the next features are built with them.

**Bonnes pratiques**
- Lisibilité : nommage clair, fonctions courtes, pas de code mort ou commenté
- Duplication : logique répétée qui devrait être factorisée
- Gestion des erreurs : pas d'exception avalée silencieusement, retours cohérents
- Dépendances : aucune ajoutée hors `hosa-infra`, aucune déclarée mais inutilisée (l'audit de vulnérabilités est celui de `hosa-security`)
- Profondeur des modules : un module passe-plat (interface presque aussi complexe que son implémentation, dont la suppression ne compliquerait rien chez ses appelants) est un constat

**Performance**
- Requêtes N+1 : boucle qui déclenche une requête DB par itération au lieu d'un chargement groupé
- Index manquant sur une colonne filtrée/jointe d'une table qui peut grossir
- Boucle ou récursion sans borne sur une entrée non contrôlée en taille
- Ressource (connexion, fichier, curseur) ouverte sans être systématiquement libérée

Règle d'honnêteté des métriques : sans outil de mesure réel (profiler, APM, benchmark exécuté), ne jamais inventer un chiffre. Formule chaque constat comme un impact potentiel identifié par lecture statique — jamais comme une mesure.

## Step 3: Classify

For each anomaly found: **Bloquant** (faille de sécurité exploitable, bug qui corrompt des données), **À corriger** (non-bloquant mais doit être fait), **Mineur** (style, lisibilité). **Pertinence** — each anomaly cites the rule, exigence or checklist item it breaks, or its concrete consequence; none → drop it. A Bloquant carries its proof: the test, request or input that shows the effect (a secret readable in the repository is its own proof); a Bloquant read statically with no input to show it is À corriger. An audit with no anomaly is a normal result — never a Mineur to fill the report. **Re-audit** after a correction (Sprint Audit below): verify each previous Bloquant and the lines the correction changed — no new audit of the rest. On a sprint audit, a Bloquant about production setup that the sprint's files don't touch (database account rights, backups, restore test, production configuration) is a **Prérequis de livraison**: it blocks a production deployment, not the merge nor a test deployment (Sprint Audit below). Already ticketed with the tag `prérequis-de-livraison` → cite the ticket, create none.

## Step 4: Write and Log

`hosa-senior-dev` writes `.hosa/kb/qualite/<slug>.md`, `hosa-dba` writes `.hosa/kb/qualite/<slug>-bdd.md`, `hosa-security` writes `.hosa/kb/securite/audit-<date>-<scope>.md` (its own structure: constats, dépendances, verdict; each finding marked prévisible/imprévisible) — this skill links it from its report. The senior dev and DBA audits use this structure:

```markdown
---
type: Audit Qualité
title: Audit qualité — <scope>
description: "<une ligne>"
tags: []
status: stable
generated: { by: hosa-senior-dev/1.0, at: <ISO8601> }
---
## Anomalies
- [Bloquant/Prérequis de livraison/À corriger/Mineur] — <fichier:ligne> — <problème précis>

## Verdict
<Propre / N anomalie(s)>
```

Log to `kb/qualite/log.md` (create if missing) — OKF §9: chronological, most recent date first.

## Step 5: Route Blocking Findings

On a sprint audit, a **Bloquant** in the code of a sprint ticket is fixed by `develop <ticket> correction` (Sprint Audit below), with no new ticket. Any other **Bloquant** anomaly, from either audit: dispatch `hosa-product-owner` (Responsibility 2/4) to create a `Ticket` (`state: todo`) linked to `kb/qualite/<slug>.md` and the finding's exact `fichier:ligne`, `generated: { by: <hosa-senior-dev or hosa-security>/1.0, at: <ISO8601> }` — whichever audit surfaced it, not the user. Run `backlog`'s Single-Ticket Mode on it so it's complete, then propose `debug` scoped to that ticket. Don't fix it inline from this skill — `qualite` audits, it doesn't patch. **À corriger** anomalies from a sprint audit: one `Ticket` per fix, grouped by cause (all missing indexes = one ticket), so they reach a sprint instead of piling up until the release — each one through `backlog`'s Single-Ticket Mode too, which writes its five notes, its rank and its estimate (pilot2: 13 audit tickets left with a story and criteria only, no rank, none plannable). Otherwise **À corriger**/**Mineur** anomalies stay in the report only — don't create a ticket per minor finding, that's backlog noise. Each new `Security Rule` `hosa-security` proposes from an unforeseen finding: ask the user, and on yes it's written to `kb/rules/security/` so the next tickets are built with it.

## Sprint Audit (stage `audit`)

`avancement.py … start audit --sprint <slug>` once `develop` is done — every ticket of the sprint reviewed and committed, before `qa`. Audit the files `git diff --name-only <base>...<branch>` lists (from `kb/sprints/<slug>.md`). Found here, before QA, a flaw costs one correction and its review: no test run, recette or validation to redo, since none has run yet (pilot2: an audit after validation reopened a `done` ticket and replayed QA, validation and the audit). Found at release, it costs a sprint. Write `## Audit` in `kb/sprints/<slug>.md`: the date, the audit files, the commit audited (`livraison` reuses the audit up to that commit), and the line `Bloquant : N — À corriger : N — Mineur : N`. A new audit appends a new line; the last one counts. The `gate.js` hook refuses the merge unless it reads `Bloquant : 0`. A re-audit after a correction covers only the files changed since the last audited commit, and **verifies the correction — it doesn't audit again**: each previous Bloquant is closed or not (a `non reproduit` is judged on the developer's test: closed unless the auditor shows the failing input); new findings only on the lines the correction changed. A flaw the first audit missed elsewhere goes to the backlog (À corriger), unless it is a proved Bloquant. Pilot2: the re-audit of sprint 1 added 5 new findings; at that rate a sprint never closes.
- **Pertinence** — a Bloquant carries its proof (Step 3). One the developer couldn't reproduce costs a correction for nothing: it stays counted under `## Corrections` (`non reproduit`) and in `## Mesures`.
- **Prérequis de livraison** — a blocking finding on production setup the sprint's diff doesn't touch (database account rights, backups and their restore test, production configuration) doesn't block the merge: it gets one ticket tagged `prérequis-de-livraison` (none if one already exists) and is counted by `livraison` before deploying to production, not in this line — a test target has no real data to lose. Write `Prérequis de livraison : N` next to it (pilot2: B1-B3 of the database audit stopped the merge twice and needed the user's acceptance each time).
- **Bloquant** → `develop <ticket> correction` on the ticket that introduced it — the QA hasn't run yet, so nothing else to replay — then this audit again, as a re-audit. `Bloquant : 0` → `done audit --sprint <slug>`, then `qa`, launched without waiting.
- **À corriger** → Step 5: `hosa-product-owner` creates the tickets; they go to the backlog, not this sprint.
- **Mineur** → stays in the audit.

## No Commits

You don't commit. Report what changed in the KB and let the user decide.

## Output

```
## Audit qualité — <scope>
- [Bloquant/À corriger/Mineur] — <fichier:ligne> — <problème>
- [If none: "Aucune anomalie"]

## Audit sécurité — <scope>
- [Bloquant/À corriger/Mineur] — <fichier:ligne> — <problème> — [prévisible : <règle> / imprévisible]
- Règles proposées : [nouvelle Security Rule, ou "Aucune"]

## Verdict
[Propre / N anomalie(s) à corriger]

## Tickets créés
- `kb/tickets/<slug>.md` — [finding] (state: todo)
[Si aucun Bloquant : "Aucun"]

## Suite
[Bloquant présent :]
**Q1 — Je lance `debug` sur le ticket <slug> ?**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
[Sinon :] Rien à signaler.
```
