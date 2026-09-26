---
name: schema-db
description: Use to write database migrations/DDL for the data entities derived from `kb/cdc/`, into the project Hosa manages. Fifth stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture).
---

# Schema DB

Turns the application-side data structures into real database schema — migrations or DDL, in whatever style the managed project already uses.

## Flow

```
Lit la Stack Decision base de données (écrite par `stack`,
ou demandée ici en fallback si absente)
        ↓
Détermine le projet cible : kb/infra/ existant, sinon
demande le chemin et l'enregistre
        ↓
Reprend les entités de schema-app (ou les redérive si besoin)
        ↓
Lit les conventions de migration déjà en place dans le
projet cible
        ↓
Écrit les fichiers de migration/DDL dans le style déjà en place
        ↓
Met à jour l'entrée Infra si le chemin des migrations n'y
figure pas encore
        ↓
Propose d'enchaîner sur `architecture`
```

## Trigger

Manual: `/schema-db`. Auto: immediately after `schema-app`, or "génère la structure de base de données".

---

## Step 1: Determine the Database Engine

Read `kb/stack/` for the `Stack Decision` covering the managed project's database — normally already written by the `stack` skill before this pipeline reaches `schema-db`. If none exists (this skill invoked standalone, without `stack` having run), fall back to asking the user and writing one:

```
mkdir -p hosa/kb/stack/
```

Write to `hosa/kb/stack/base-de-donnees-projet-gere.md`:

```markdown
---
type: Stack Decision
title: Base de données — <projet>
description: Choix du moteur de base de données pour le projet géré
tags: []
status: stable
generated: { by: human:<user>, at: <ISO8601> }
---
## Décision
<moteur choisi>

## Justification
<pourquoi>
```

Log to `kb/stack/log.md` (create if missing) — OKF §9.

## Step 2: Find the Managed Project

Same as `schema-app` Step 1: read `kb/infra/` for the `Infra` entry giving the project's root path. If none exists, ask the user for it and write one there. Never accept `hosa/app` or `hosa/kb` as the path — those are Hosa's own tooling, out of scope; if the user gives one of them, say so and ask again.

## Step 3: Get the Entities

If `schema-app` just ran in this session, reuse its entities. Otherwise, re-derive them the same way (`donnees`-qualified `Exigence`s + `Persona`s), same rule as `schema-app` Step 2 — stop and ask for `donnees` to run first if any item lacks an origin annotation.

## Step 4: Read Existing Migration Conventions

Before writing anything, read the managed project's existing migration/DDL setup — which tool it uses (if any), naming style, directory layout. Match it exactly. If none exists yet, pick conventions consistent with the chosen database engine and the project's existing stack, and say what you chose and why.

## Step 5: Write the Migrations

One migration/DDL file per entity (or grouped, if the project's existing convention groups them), in the managed project, in its existing style. Never edit an existing migration that may already be applied — write a new one for any change to an entity already covered.

## Step 6: Update the `Infra` Entry

If the migrations' path isn't already recorded in the `Infra` entry (`schema-app`'s Step 1), add it and log the update to `kb/infra/log.md`.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit each.

## Output

```
## Choix base de données
[Décision utilisée ou nouvellement enregistrée]

## Structures créées
- `<path>` — <entité>

## Suite
Je lance `architecture` maintenant ?
```
