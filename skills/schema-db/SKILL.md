---
name: schema-db
description: "Use to write the database migrations (`hosa-data-engineer`), then apply, validate and document the database tooling (`hosa-dba`). Structuration stage 5. Trigger: \"génère la structure de base de données\", after `schema-app`."
---

# Schema DB

Turns the application-side data structures into real database schema — migrations or DDL, in whatever style the managed project already uses. This skill is the only one that talks to the user — the actual derivation and write is `hosa-data-engineer`'s.

## Flow

```
Dispatch hosa-data-engineer (Responsibility 3)
        ↓ Open Question (no Stack Decision, no project path,
        ↓ unannotated data) → relay to user, stop
        ↓ migrations écrites
Dispatch hosa-dba (Mode 1 Outillage) : applique, prouve
l'aller-retour, commandes, comptes, sauvegardes, documente
        ↓
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

## Step 1b: Database Tooling

Dispatch `hosa-dba` (Mode 1 Outillage, `agents/dba.md`): it applies the new migrations to the base environment, proves they roll back and re-apply, sets up or updates the documented commands (migrer, revenir en arrière, état, vérifier, réinitialiser), the application's least-privilege account and, when an exigence asks, backups with a tested restore — recorded in `kb/infra/base-de-donnees.md`. Relay its `## Installation nécessaire` to `hosa-infra`, its schema-design questions back to `hosa-data-engineer` (Step 1), and its `## Documentation à produire` to `hosa-documentation`. A migration it can't apply or reverse sends the work back to Step 1 — the stage isn't done until both agree.

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
Suite : `architecture`, lancé sans attendre.
```
