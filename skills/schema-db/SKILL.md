---
name: schema-db
description: Use to write database migrations/DDL for the data entities derived from `kb/cdc/`, into the project Hosa manages. Fifth stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture).
---

# Schema DB

Turns the application-side data structures into real database schema — migrations or DDL, in whatever style the managed project already uses. This skill is the only one that talks to the user — the actual derivation and write is `hosa-data-engineer`'s.

## Flow

```
Dispatch hosa-data-engineer (Responsibility 3)
        ↓ Open Question (no Stack Decision, no project path,
        ↓ unannotated data) → relay to user, stop
        ↓ migrations écrites
Met à jour l'entrée Infra avec le chemin des migrations
        ↓
Propose d'enchaîner sur `architecture`
```

## Trigger

Manual: `/schema-db`. Auto: immediately after `schema-app`, or "génère la structure de base de données".

---

## Step 1: Dispatch for the Migrations

Dispatch `hosa-data-engineer` (Responsibility 3, `agents/data-engineer.md`) to determine the database engine, find the managed project, reuse or re-derive the entities, read existing migration conventions, and write the migrations/DDL.

If it returns an Open Question:
- **No `Stack Decision` for the database** — ask the user which engine to use, redispatch with the answer (the agent records the `Stack Decision` itself once it has it).
- **No `Infra` entry** — ask the user for the managed project's root path, redispatch with the answer (the agent writes the `Infra` entry itself once it has it).
- **An item still missing an origin annotation** — relay it and propose running `donnees` first; don't guess an origin yourself.

## Step 2: Update the `Infra` Entry

If the migrations' path isn't already recorded in the `Infra` entry, add it and log the update to `kb/infra/log.md`.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa` Core Rules, "Git checkpoints".

## Output

```
## Choix base de données
[Décision utilisée ou nouvellement enregistrée]

## Structures créées
- `<path>` — <entité>

## Open Questions
[Si rien : "None"]

## Suite
Je lance `architecture` maintenant ?
```
