---
name: bdd
description: "Use for any database operation on the managed project — migrations, conflicts, an environment's or the test database, reset, backup/restore, slow query — via `hosa-dba`. Triggers: \"applique les migrations\", \"conflit de migrations\", \"restaure la base\", `## Base de données nécessaire`."
---

# Base de données

`hosa-dba` runs the database: `hosa-data-engineer` designs it, `hosa-infra` provisions its server, every other agent uses the commands `hosa-dba` documents in `kb/infra/base-de-donnees.md`. This skill is the direct way in, and the relay for any agent that needs something database-side.

## Flow

```
Détermine le besoin et l'environnement (sprint actif → son
docker_project, sinon la base)
        ↓
Dispatch hosa-dba dans le mode qui convient (Outillage, Tests,
Assistance, Audit)
        ↓ Installation nécessaire → hosa-infra, redispatch
        ↓ changement de conception du schéma → hosa-data-engineer
          (`schema-db`), puis redispatch
        ↓ Documentation à produire → hosa-documentation
Rapporte ce qui a été fait et vérifié
```

## Trigger

Manual: `/bdd [besoin]`. Auto: "applique les migrations", "état des migrations", "conflit de migrations", "réinitialise la base de test", "sauvegarde/restaure la base", "la requête est lente", "verrou sur la base", "documente l'outillage de la base". Relay: any agent output carrying `## Base de données nécessaire`.

---

## Step 1: Scope

Name the need and the environment: an `active` sprint → its `worktree` and `docker_project` (`kb/sprints/`); otherwise the base environment (`kb/infra/environnement-docker.md`). Pick the mode: tooling not set up yet (no `kb/infra/base-de-donnees.md`) → Mode 1 first, whatever was asked.

## Step 2: Dispatch

Dispatch `hosa-dba` (`agents/dba.md`) with the need, the mode and the environment. Relay its returns:
- **`## Installation nécessaire`** → dispatch `hosa-infra` (Mode 2), then redispatch `hosa-dba`.
- **`## Open Questions` asking for a schema design change** → that's `hosa-data-engineer`'s: run `schema-db` for it, then redispatch `hosa-dba` to apply it.
- **`## Documentation à produire`** → dispatch `hosa-documentation` (Mode 1) with it.

## No Commits

You don't commit. Report what changed and let the user decide.

## Output

```
## Base de données
- [Ce qui a été fait, environnement concerné]

## Vérification
- [Migrations, tests, sauvegarde — d'après hosa-dba]

## Suite
[L'étape du flux qui attendait cette opération, ou rien]
```
