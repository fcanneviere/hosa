---
name: architecture
description: Use to design and scaffold the software architecture of the project Hosa manages, consistent with the stable cahier des charges, the chosen stack, and the data structures already written by `schema-app`/`schema-db`. Sixth stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture → interface → backlog).
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
Dispatch hosa-documentation (Mode 1) pour la documentation
d'architecture
        ↓
Met à jour l'entrée Infra avec le chemin confirmé
```

## Trigger

Manual: `/architecture`. Auto: immediately after `schema-db`, or "crée l'architecture logicielle", "génère l'architecture de l'application".

---

## Step 1: Gather Inputs

Read `kb/infra/` for the `Infra` entry giving the managed project's root path — the scaffold target is always that path, never `hosa/app` or `hosa/kb` (Hosa's own tooling). If there's no `Infra` entry yet, say so and propose running `stack` or `schema-app` first (either writes one); don't guess a path.

Read `kb/cdc/` for `stable` `Exigence`s, `kb/stack/` for `Stack Decision`s, and the data dictionary + migrations already written by `schema-app`/`schema-db` in the managed project (paths recorded in the `Infra` entry). If any of the three is missing, say so and propose running the missing stage (`stack`, `schema-app`, or `schema-db`) first — don't guess.

## Step 2: Read Existing Conventions

Read the managed project's existing code, if any, to respect conventions already in place — same discipline as `hosa-implementer`.

## Step 3: Design the Architecture

Design the layers, modules, and boundaries that let the business logic (CDC), the chosen stack, and the existing data structures cohere into one buildable codebase. Say what you chose and why.

## Step 4: Scaffold It

Write the architecture for real in the managed project: folders, module skeletons, boilerplate matching the chosen stack. If parts of the architecture already exist (from `schema-app`'s output or otherwise), extend them rather than duplicating.

## Step 5: Dispatch `hosa-documentation` (Mode 1)

Dispatch `hosa-documentation` (Mode 1) with the layers/modules chosen and the paths scaffolded — it writes the architecture documentation into the managed project. Wait for its confirmation and the path it wrote to.

## Step 6: Update the `Infra` Entry

Add the confirmed architecture documentation path to the `Infra` entry under its own `## Documentation d'architecture` heading — a fixed heading, not a bare line, so a later reader (e.g. `backlog`) can tell it apart from the data dictionary or migrations paths `schema-app`/`schema-db` also record there. Log the update to `kb/infra/log.md`.

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
Je lance `interface` maintenant ?
```
