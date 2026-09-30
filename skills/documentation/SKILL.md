---
name: documentation
description: Use to check whether the managed project's technical and functional documentation is in sync with its sources, and refresh whatever has drifted. Companion check usable anytime, not a forced pipeline stage — dispatches `hosa-documentation` in cold-check mode.
---

# Documentation

Cold-check pass over every documentation section `hosa-documentation` already owns — catches drift the hot-dispatch mechanism might have missed (e.g. a file edited by hand outside the agent flow).

## Flow

```
Lit kb/infra/ (chemin racine du projet géré)
        ↓
Dispatch hosa-documentation en Mode 2 (vérification à froid)
        ↓
Rapporte les sections rafraîchies et celles déjà à jour
```

## Trigger

Manual: `/documentation`. Auto: "vérifie que la documentation est à jour".

---

## Step 1: Find the Managed Project

Read `kb/infra/` for the managed project's root path (same as `stack`/`infra`/`qualite` Step 1). Missing → say so; `hosa-documentation` has nothing to check without a project to point at.

## Step 2: Dispatch the Cold Check

Dispatch `hosa-documentation` in Mode 2. It reads every `kb/documentation/` entry, compares each source's date to its own `generated.at`, and refreshes anything that's drifted. A source with no readable date is reported as non vérifiable, never silently treated as up to date. If no `kb/documentation/` entry exists yet, it says so — nothing to check until at least one section has been written by a Mode 1 dispatch.

## No Commits

You don't commit. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa` Core Rules, "Git checkpoints".

## Output

```
## Documentation
- À jour : <section>, <section>
- Rafraîchie : <section> (source : <quoi>)
- Non vérifiable : <section> (source sans date : <quoi>)
- [Si aucune entrée encore : "Rien à vérifier — aucune section écrite pour l'instant"]

## Open Questions
[Si rien : "None"]
```
