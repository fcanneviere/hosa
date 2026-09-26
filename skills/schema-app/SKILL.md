---
name: schema-app
description: Use to derive data entities from qualified `kb/cdc/` Exigences and write the corresponding data structures, plus their documentation, into the project Hosa manages. Fourth stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture).
---

# Schema App

Turns qualified cahier des charges data into real application-side data structures — and documents them — in the managed project, never in `hosa/app`.

## Flow

```
Détermine le projet cible : kb/infra/ existant, sinon
demande le chemin et l'enregistre
        ↓
Lit les Exigence stable annotées + Persona liés → dérive
les entités de données
        ↓
Lit le code existant du projet cible (langage, framework,
conventions) avant d'écrire
        ↓
Écrit les structures de données dans le style déjà en place
        ↓
Dispatch hosa-documentation (Mode 1) pour le dictionnaire de
données
        ↓
Met à jour l'entrée Infra avec le chemin confirmé
        ↓
Propose d'enchaîner sur `schema-db`
```

## Trigger

Manual: `/schema-app`. Auto: immediately after `donnees`, or "génère la structure de données de l'application".

---

## Step 1: Find the Managed Project

Read `kb/infra/` for an existing `Infra` entry giving the project's root path. If none exists, ask the user for it and write one. Never accept `hosa/app` or `hosa/kb` as the path — those are Hosa's own tooling, out of scope; if the user gives one of them, say so and ask again.

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

Log to `kb/infra/log.md` (create if missing) — OKF §9.

## Step 2: Derive Data Entities

Read every `stable` `Exigence` in `kb/cdc/`, and the `Persona`s they reference. If any `Données en entrée`/`sortie` item has no origin annotation (`— origine : ...`) yet, stop and say so — run `donnees` first, don't guess an origin here.

Once every item is annotated, group them into coherent entities — items that describe the same real-world thing (a client, a commande, a facture...) belong to the same entity, regardless of which Exigence mentions them.

## Step 3: Read Existing Conventions

Before writing anything, read the managed project's existing code: language, framework, any existing models/types/schemas, naming style. Match it exactly — same discipline as `simflow-implementer`. If the project has no existing data-structure code yet, use the language/framework `Stack Decision` in `kb/stack/` (written by the `stack` skill) rather than guessing; if that's also missing, pick conventions consistent with whatever's available and say what you chose and why.

## Step 4: Write the Structures

One data structure (type/model/schema, whatever the project's stack calls for) per entity, in the managed project, in its existing style. If a structure for that entity already exists, extend it to match the current entity definition rather than creating a duplicate.

## Step 5: Dispatch `hosa-documentation` (Mode 1)

Dispatch `hosa-documentation` (Mode 1) with each entity's fields, types, origins, and the `Exigence` it traces back to — it writes the data dictionary into the managed project. Wait for its confirmation and the path it wrote to.

## Step 6: Update the `Infra` Entry

Add the confirmed documentation path to the `Infra` entry from Step 1, and log the update to `kb/infra/log.md`.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit each.

## Output

```
## Structures créées
- `<path>` — <entité> (<n> champs)

## Documentation
- `<path>`

## Suite
Je lance `schema-db` maintenant ?
```
