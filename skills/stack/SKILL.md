---
name: stack
description: Use to propose and record the technical stack for the project Hosa manages, based on the stable cahier des charges. First stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture).
---

# Stack

Turns "what the application must do" (the stable cahier des charges) into a chosen technical stack, recorded before any data structure or architecture work begins.

## Flow

```
Détermine le projet cible : kb/infra/ existant, sinon
demande le chemin et l'enregistre
        ↓
Lit les Exigence stable de kb/cdc/ → dérive les besoins
techniques pertinents
        ↓
Vérifie kb/stack/ (décisions déjà enregistrées) et le code
existant du projet cible — une catégorie déjà fixée n'est pas
reproposée
        ↓
Propose 2-3 stacks (langage, framework, BDD, hébergement)
avec compromis, uniquement pour les catégories encore ouvertes
        ↓
Utilisateur choisit
        ↓
Écrit chaque décision comme Stack Decision dans kb/stack/
        ↓
Dispatch hosa-documentation (Mode 1) → ADR dans le projet géré
        ↓
Propose d'enchaîner sur `donnees`
```

## Trigger

Manual: `/stack`. Auto: immediately after a clean `contestation` sign-off, or "choisis la stack technique", "quelle stack pour le projet".

---

## Step 1: Find the Managed Project

Read `kb/infra/` for an existing `Infra` entry giving the project's root path. If none exists, ask the user for it and write one:

```
mkdir -p hosa/kb/infra/
```

Write to `hosa/kb/infra/projet-gere.md`:

```markdown
---
type: Infra
title: Projet géré — chemin racine
description: Racine du projet applicatif géré par Hosa
tags: []
status: stable
generated: { by: human:<user>, at: <ISO8601> }
---
## Chemin racine
<chemin>
```

Log to `kb/infra/log.md` (create if missing) — OKF §9. Never accept `hosa/app` or `hosa/kb` as the path — those are Hosa's own tooling, out of scope; if the user gives one of them, say so and ask again.

## Step 2: Derive Technical Needs

Read every `stable` `Exigence` in `kb/cdc/`. If there are none, say so and stop — a stack choice needs a settled cahier des charges. Derive the needs that bear on a stack choice: data volume and shape, external integrations, deployment constraints, anything else named in the CDC.

## Step 3: Check for Existing Decisions

Before proposing anything, read `kb/stack/` for `Stack Decision`s already recorded for this project, and the managed project's existing code (if any) for a stack already in use. For each category (language/framework, database, hosting):
- Already fixed by existing code, or already recorded as a `Stack Decision` → don't re-propose it. State what's already fixed and why, and skip straight to confirming it still holds — a rerun of `stack` isn't a license to pick something new for a category the project already committed to.
- If the existing code and an existing `Stack Decision` disagree, say so and ask the user which one is authoritative before continuing — don't silently pick one.
- Genuinely undecided → propose for it in Step 4.

## Step 4: Propose Options

Propose 2-3 stack options — language, framework, database, hosting where relevant, but only for categories Step 3 found undecided — each with its trade-offs. Recommend one and say why.

## Step 5: Record the Decision

Once the user picks, write each newly-decided category as a `Stack Decision` in `kb/stack/` — one file per category, e.g. `hosa/kb/stack/langage-framework-projet-gere.md`, `hosa/kb/stack/base-de-donnees-projet-gere.md`, `hosa/kb/stack/hebergement-projet-gere.md`. Never overwrite a category Step 3 found already fixed — a database migration or scaffolded code may already depend on it.

```markdown
---
type: Stack Decision
title: <catégorie> — <projet>
description: <choix technique et sa catégorie>
tags: []
status: stable
generated: { by: human:<user>, at: <ISO8601> }
---
## Décision
<choix>

## Justification
<pourquoi>
```

Log to `kb/stack/log.md` (create if missing) — OKF §9.

## Step 6: ADR

For each newly-recorded `Stack Decision`, dispatch `hosa-documentation` (Mode 1) with the category, the choice, the justification, and the options presented in Step 4 (including the ones not chosen) — it writes the matching ADR into the managed project. Wait for its confirmation before reporting the decision as fully recorded.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit each.

## Output

```
## Stack proposée
[Options présentées avec compromis]

## Stack retenue
- `kb/stack/<slug>.md` — [décision]
- ADR : `<path docs/decisions/ADR-...>`

## Suite
Je lance `infra` maintenant ?
```
