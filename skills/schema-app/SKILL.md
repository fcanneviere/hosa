---
name: schema-app
description: "Use to derive entities from qualified exigences and write the application data structures and their documentation. Structuration stage 4. Trigger: \"génère la structure de données de l'application\", after `donnees`."
---

# Schema App

Turns qualified cahier des charges data into real application-side data structures — and documents them — in the managed project, never in `hosa/app`. This skill is the only one that talks to the user — the actual derivation, scaffold, and write is `hosa-data-engineer`'s.

## Flow

```
Dispatch hosa-data-engineer (Responsibility 2)
        ↓ Open Question (no project path, unannotated data) → relay to user, stop
        ↓ structures written
Dispatch hosa-documentation (Mode 1) avec le
"Documentation à produire" retourné
        ↓
Met à jour l'entrée Infra avec le chemin confirmé
        ↓
Propose d'enchaîner sur `schema-db`
```

## Trigger

Manual: `/schema-app`. Auto: immediately after `donnees`, or "génère la structure de données de l'application".

---

## Step 1: Dispatch for the Structures

Dispatch `hosa-data-engineer` (Responsibility 2, `agents/data-engineer.md`) to determine the managed project, derive data entities from `stable`, origin-annotated `Exigence`s and their `Persona`s, read the managed project's existing conventions, and write the data structures.

If it returns an Open Question:
- **No `Infra` entry** — ask the user for the managed project's root path, redispatch with the answer (the agent writes the `Infra` entry itself once it has it).
- **An item still missing an origin annotation** — relay it and propose running `donnees` first; don't guess an origin yourself.

## Step 2: Dispatch Documentation

Dispatch `hosa-documentation` (Mode 1) with what `hosa-data-engineer` returned under `## Documentation à produire` (each entity's fields, types, origins, and the `Exigence` it traces back to) — it writes the data dictionary into the managed project. Wait for its confirmation and the path it wrote to.

## Step 3: Update the `Infra` Entry

Add the confirmed documentation path to the `Infra` entry, and log the update to `kb/infra/log.md`.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa` Core Rules, "Git checkpoints".

## Output

```
## Structures créées
- `<path>` — <entité> (<n> champs)

## Documentation
- `<path>`

## Open Questions
[Si rien : "None"]

## Suite
Suite : `schema-db`, lancé sans attendre.
```
