---
name: schema-app
description: Use to derive data entities from qualified `kb/cdc/` Exigences and write the corresponding data structures, plus their documentation, into the project Hosa manages. Second stage of the data-structuring pipeline (donnees → schema-app → schema-db).
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
Rédige la documentation (dictionnaire de données) dans le
projet cible
        ↓
Met à jour l'entrée Infra avec le chemin de la doc
        ↓
Propose d'enchaîner sur `schema-db`
```

## Trigger

Manual: `/schema-app`. Auto: immediately after `donnees`, or "génère la structure de données de l'application".

---

## Step 1: Find the Managed Project

Read `kb/infra/` for an existing `Infra` entry giving the project's root path. If none exists, ask the user for it and write one:

```
mkdir -p hosa/kb/infra/
```

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

Read every `stable` `Exigence` in `kb/cdc/` annotated by `donnees`, and the `Persona`s they reference. Group `Données en entrée`/`sortie` items into coherent entities — items that describe the same real-world thing (a client, a commande, a facture...) belong to the same entity, regardless of which Exigence mentions them.

If an item has no origin annotation yet, stop and say so — run `donnees` first, don't guess an origin here.

## Step 3: Read Existing Conventions

Before writing anything, read the managed project's existing code: language, framework, any existing models/types/schemas, naming style. Match it exactly — same discipline as `simflow-implementer`. If the project has no existing data-structure code yet, pick conventions consistent with its language/framework and say what you chose and why.

## Step 4: Write the Structures

One data structure (type/model/schema, whatever the project's stack calls for) per entity, in the managed project, in its existing style.

## Step 5: Write the Documentation

A data dictionary in the managed project (e.g. `docs/data-model.md`, or wherever the project's existing docs live), one section per entity:

```markdown
## <Entité>
| Champ | Type | Origine | Exigence |
|---|---|---|---|
| <champ> | <type> | <générée/fournie/saisie> | [<exigence>](<chemin kb/cdc>) |
```

## Step 6: Update the `Infra` Entry

Add the documentation file's path to the `Infra` entry from Step 1, and log the update to `kb/infra/log.md`.

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
