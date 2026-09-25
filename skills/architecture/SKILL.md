---
name: architecture
description: Use to design and scaffold the software architecture of the project Hosa manages, consistent with the stable cahier des charges, the chosen stack, and the data structures already written by `schema-app`/`schema-db`. Fifth and last stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture).
---

# Architecture

Turns the business logic, the chosen stack, and the finished data architecture into a real, scaffolded software architecture in the managed project.

## Flow

```
Lit kb/cdc stable, kb/stack (Stack Decision), la doc de
données + migrations écrites par schema-app/schema-db
        ↓
Si l'une des trois sources manque, le dit et propose de
lancer l'étape manquante d'abord
        ↓
Lit le code existant du projet cible (conventions)
        ↓
Conçoit l'architecture (couches, modules, limites) cohérente
avec stack + données + logique métier
        ↓
Scaffold l'architecture dans le projet cible
        ↓
Rédige la documentation d'architecture dans le projet cible
        ↓
Met à jour l'entrée Infra avec le chemin de la doc
```

## Trigger

Manual: `/architecture`. Auto: immediately after `schema-db`, or "crée l'architecture logicielle", "génère l'architecture de l'application".

---

## Step 1: Gather Inputs

Read `kb/cdc/` for `stable` `Exigence`s, `kb/stack/` for `Stack Decision`s, and the data dictionary + migrations already written by `schema-app`/`schema-db` in the managed project (paths recorded in the `Infra` entry). If any of the three is missing, say so and propose running the missing stage (`stack`, `schema-app`, or `schema-db`) first — don't guess.

## Step 2: Read Existing Conventions

Read the managed project's existing code, if any, to respect conventions already in place — same discipline as `simflow-implementer`.

## Step 3: Design the Architecture

Design the layers, modules, and boundaries that let the business logic (CDC), the chosen stack, and the existing data structures cohere into one buildable codebase. Say what you chose and why.

## Step 4: Scaffold It

Write the architecture for real in the managed project: folders, module skeletons, boilerplate matching the chosen stack. If parts of the architecture already exist (from `schema-app`'s output or otherwise), extend them rather than duplicating.

## Step 5: Write the Documentation

An architecture document in the managed project (e.g. `docs/architecture.md`, or wherever the project's existing docs live) — never in `hosa/kb`. Cover the layers/modules chosen, their boundaries, and how they relate to the data structures and the CDC.

## Step 6: Update the `Infra` Entry

Add the architecture documentation's path to the `Infra` entry, and log the update to `kb/infra/log.md`.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit each.

## Output

```
## Architecture conçue
[Couches/modules retenus et pourquoi]

## Structures créées
- `<path>` — [module/dossier scaffoldé]

## Documentation
- `<path>`

## Suite
Pipeline de structuration des données terminé.
```
