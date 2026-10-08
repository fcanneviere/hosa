---
name: status
description: Use when the user wants to know where they are in a project. On a Hosa-managed project (`.hosa/kb/` exists), reads the KB directly — identity/objectives, CDC state, backlog by state, the active sprint and its QA, open qualite anomalies, documentation drift, and the next pipeline step. Otherwise falls back to reading the spec, git log, and test results.
---

# Status

Gives you a fast, accurate snapshot of where the project stands right now. Useful at the start of any session, after time away, or whenever you need to reorient.

## Flow

```
kb/ existe ? ────────────────┐
        ↓ oui                ↓ non
Lit la KB Hosa          Lit docs/specs/, git log, tests
(identité, CDC, backlog,       ↓
sprint actif, qualité,   Snapshot générique (mode historique)
documentation, pipeline)
        ↓
Snapshot KB Hosa
        ↓
Suggère la prochaine étape logique
```

---

## Mode Hosa (`.hosa/kb/` exists)

Read directly — no agent dispatch, this is a read-only snapshot:

**Identité et objectifs:** `kb/project/identity.md` — nom, objectif, `## Objectifs mesurables`. Missing → say so, suggest `hosa`.

**Cahier des charges:** count every `Exigence` in `kb/cdc/` by `status` (`draft`/`stable`). No `kb/cdc/` at all → say so, this project hasn't started the CDC pipeline.

**Backlog:** count every `Ticket` in `kb/tickets/` by `state` (`todo`/`doing`/`done`/`blocked`).

**Sprint actif:** find the `Sprint` in `kb/sprints/` with `state: active` (there's at most one at a time by convention). List its tickets and each one's current `state`. For each ticket, check `kb/test/<slug>-technique.md` — read its most recent `## Résultats techniques` if present ("non testé" if the file doesn't exist yet). No active sprint → say so; note the most recently `done` sprint instead if one exists.

**Qualité:** the most recent `kb/qualite/log.md` entry's file — read its `## Verdict`. No `kb/qualite/` yet → "jamais audité".

**Documentation:** the most recent `kb/documentation/log.md` entry's date, if it exists. Don't re-check drift here (that's `documentation`'s job, and requires a dispatch) — just report when it was last verified, and suggest running `documentation` if that's more than a few sessions old or absent entirely.

**Prochaine étape du pipeline:** walk the three Hosa pipelines in order and report the first gap found — the same precondition each stage's own Step 1 already checks, just read here instead of enforced:
1. CDC: `hosa` (identity) → `interview` → `redaction` → `fondamentaux` → `securite` → `relecture` → `contestation` (needs ≥1 `stable` Exigence to move on)
2. Data-structuring (needs a stable CDC): `stack` → `infra` → `donnees` → `schema-app` → `schema-db` → `architecture` → `interface` → `backlog`
3. Delivery cycle (needs a non-empty backlog): `sprint` → `git` (M1) → `develop` → `qa-plan` → `qa` → `validation` → `git` (M2) → `bilan-sprint`

If a pipeline hasn't started yet because an earlier one isn't done (e.g. no stable CDC yet, so data-structuring can't start), say so explicitly rather than reporting a false gap further down.

### Output Format (Mode Hosa)

```
## Statut Hosa

### Identité
- Projet : <nom> — <objectif>
- Objectifs mesurables : <liste, ou "Aucun encore défini">

### Cahier des charges
- Exigences : X stable(s), Y draft

### Backlog
- Tickets : X todo, Y doing, Z done, W blocked

### Sprint actif
- <slug> — objectif : <objectif>
- Tickets : <ticket> (state, résultats techniques, recette)
[Si aucun sprint actif : "Aucun sprint actif." + dernier sprint done s'il y en a un]

### Qualité
- Dernier audit : <Propre / N anomalie(s)> (<date>)
[Si jamais audité : "Jamais audité."]

### Documentation
- Dernière vérification : <date>
[Si jamais vérifiée : "Jamais vérifiée."]

### Prochaine étape
[La première étape manquante du pipeline concerné, et le skill à lancer]
```

---

## Mode Générique (no `.hosa/kb/`)

**Spec:** check `docs/specs/` for all spec files. Note each one's date, topic, and any open questions listed inside.

**Git log:** run `git log --oneline -20` to see recent commits. Identify:
- Which tasks have been committed (look for `feat:`, `fix:`, `test:` prefixes)
- When the last commit happened
- Whether there's uncommitted work in the working tree (`git status`)

**Tests:** check if a test runner exists and run it if possible. If tests were run recently, note the last known result. If you can't run them, say so — don't guess.

**Open questions:** re-read the spec's "Open Questions" section if it exists. Flag any that are still unresolved.

### Output Format (Mode Générique)

```
## Project Status

### Spec
- File: docs/specs/<filename>
- Topic: <what's being built>
- Written: <date>
- Open questions: <N unresolved / none>

### Implementation Progress
- Tasks committed: [list from git log, e.g. "auth middleware (2d ago)", "user endpoint (2d ago)"]
- Tasks outstanding: [what the spec describes that hasn't been committed yet]
- Uncommitted changes: [yes — describe / no]

### Tests
- Last run: <date / unknown>
- Result: <X passed, Y failed / not yet run / could not determine>

### Last Activity
- <timestamp> — <what was last committed>

### Suggested Next Step
[One sentence: the most logical thing to do next based on the above state]
```

If there is no spec file: say so and suggest `understand` to create one.

If the git repo has no commits yet: say so and suggest `understand` or `build`.

Keep either output scannable. No paragraphs — just the facts.
