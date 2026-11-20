---
name: schema-db
description: "Use to draw the database diagram the user validates (tables, relations, data formats), write its migrations (`hosa-data-engineer`), then apply, validate and document the database tooling (`hosa-dba`). Structuration stage 5. Trigger: \"génère la structure de base de données\", after `schema-app`."
---

# Schema DB

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start schema-db`; refused → name the missing stage to the user and stop; refused as already done → a re-run only on the user's request: the same `start` with `--rouvre "<their request>"`. Stopped on a user question: `block schema-db --detail "<question>"`. Once the stage's output is written and committed: `done schema-db`. Never skip these calls: without them a cut session can't resume (« reprends »), and `budget.js` can't apply the stage's `dispatch` rules (each agent's model, the agents at once) — they hold only while the stage is `en cours`.

**Tâches.** Before each dispatch, `avancement.py task add schema-db <id> --agent <agent>`; on its return, `task done schema-db <id> --sortie <the paths it wrote>`: `schema` (`hosa-data-engineer`, Step 1) → `kb/infra/schema-base-de-donnees.md`; `migrations` (`hosa-data-engineer`, Step 1b) → the migrations; `outillage` (`hosa-dba`, Step 1c) → `kb/infra/base-de-donnees.md`; `documentation` (`hosa-documentation`) → the documentation paths. A round back to Step 1 or 1b → `task add schema-db schema` or `migrations` again (it resets the task to `à faire`). Stopped on an Open Question → `task block schema-db <id> --detail "<la question>"`, and `task add` the same id again once answered.

Turns the application-side data structures into real database schema — migrations or DDL, in whatever style the managed project already uses. **No migration is written before the user validates the database diagram**: tables, relations, each column's type and format, keys and constraints. This skill is the only one that talks to the user — the actual derivation and write is `hosa-data-engineer`'s.

## Flow

```
Dispatch hosa-data-engineer (Responsibility 3, schéma)
        ↓ Open Question (no Stack Decision, no project path,
        ↓ unannotated data) → relay to user, stop
        ↓ schéma de la base écrit
Schéma validé par l'utilisateur : tables, relations,
format des données (`cdc schemas --db --apercu`, `cdc valide db`)
        ↓
Dispatch hosa-data-engineer (Responsibility 3, migrations)
        ↓ migrations conformes au schéma validé
Dispatch hosa-dba (Mode 1 Outillage) : applique, prouve
l'aller-retour, commandes, comptes, sauvegardes, documente
        ↓
Met à jour l'entrée Infra avec le chemin des migrations
        ↓
Enchaîne sur `architecture`
```

## Trigger

Manual: `/schema-db`. Auto: immediately after `schema-app`, or "génère la structure de base de données".

---

## Step 1: Dispatch for the Database Diagram

Dispatch `hosa-data-engineer` (Responsibility 3, `agents/data-engineer.md`, part **schéma**) to determine the database engine, find the managed project, reuse or re-derive the entities, and write `kb/infra/schema-base-de-donnees.md` (`type: Infra`) with its `## Schéma de la base de données`: one ```mermaid `erDiagram` — every table, every relation with its cardinality, every column with its type, its keys (`PK`, `FK`, `UK`) and, in its comment, its format (length, unit, allowed values, null or not, default). No migration yet.

If it returns an Open Question:
- **No `Stack Decision` for the database** — ask the user which engine to use, redispatch with the answer (the agent records the `Stack Decision` itself once it has it).
- **No `Infra` entry** — ask the user for the managed project's root path, redispatch with the answer (the agent writes the `Infra` entry itself once it has it).
- **An item still missing an origin annotation** — relay it, `back schema-db donnees --detail "<exigences>"` (it reopens `donnees`, then `schema-app`, then `schema-db`), and run `donnees` first; don't guess an origin yourself.

## Step 1a: The User Validates the Database Diagram

```bash
<hosa> cdc schemas "<root>/.hosa/kb" --db --apercu
```

It writes `<root>/.hosa/schemas.html` (the diagram drawn) and exits 1 while the diagram is incomplete (no `erDiagram`, a table without columns, tables without relations, a column without its type or format) or not validated. Incomplete → redispatch `hosa-data-engineer` (task `schema`) with the exact gaps, never a summary. Complete → give the user the page's path, never the diagram's text, then one question:

**Q1** — Le schéma de la base de données est-il juste : tables, relations, format de chaque donnée ?
a) Oui.
b) Non : <ce qui change>.

« a » → `<hosa> cdc valide "<root>/.hosa/kb" db`. « b » → `block schema-db --detail` while waiting, then redispatch `hosa-data-engineer` (task `schema`) with the user's words as given, then the page again. Past 2 rounds, show the user what each round changed and let them decide. `done schema-db` refuses while the diagram is not validated, or changed since (`avancement.py check schema-db`); `HOSA_SCHEMAS=0` turns the check off. A later change of the schema (a loop from `develop`, a `changement`) changes the diagram and loses the validation: this step runs again before any new migration.

## Step 1b: Dispatch for the Migrations

Dispatch `hosa-data-engineer` (Responsibility 3, part **migrations**) to read the existing migration conventions and write the migrations/DDL of the validated diagram, exactly: no table, column, type, format or relation the diagram doesn't hold. A gap it finds in the diagram while writing comes back as an Open Question: the diagram changes first (Step 1, then Step 1a), never the migration alone.

## Step 1c: Database Tooling

Dispatch `hosa-dba` (Mode 1 Outillage, `agents/dba.md`): it applies the new migrations to the base environment, proves they roll back and re-apply, sets up or updates the documented commands (migrer, revenir en arrière, état, vérifier, réinitialiser), the application's least-privilege account and, when an exigence asks, backups with a tested restore — recorded in `kb/infra/base-de-donnees.md`. Relay its `## Installation nécessaire` to `hosa-infra`, its schema-design questions back to `hosa-data-engineer` (Step 1: a change of the diagram is validated again in Step 1a), and its `## Documentation à produire` lines, as they are (paths), to `hosa-documentation`. A migration it can't apply or reverse sends the work back to Step 1b, with its exact error, never a summary. Two rounds on the same migration still failing → stop: show the user both errors and what each round changed, and let them decide. The stage isn't done until both agree.

## Step 2: Update the `Infra` Entry

If the migrations' path isn't already recorded in the `Infra` entry, add it and log the update to `kb/infra/log.md`.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa`, "Git checkpoints".

## Output

```
## Choix base de données
[Décision utilisée ou nouvellement enregistrée]

## Schéma validé
`kb/infra/schema-base-de-donnees.md` — validé le <date>

## Structures créées
- `<path>` — <entité>

## Open Questions
[Si rien : "None"]

## Suite
Suite : `architecture`, lancé sans attendre.
```
