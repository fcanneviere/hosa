---
name: livraison
description: Use to turn a local merge into something actually shipped — scopes the `Ticket`s done since the last release, makes sure a CI pipeline and environments exist (via `hosa-infra`), writes release notes from those tickets (via `hosa-documentation`), records the release, and optionally pushes/opens a PR (via `hosa-git`, only on explicit confirmation). Follow-on to `git` Mode 4 / `validation` — the step Hosa's pipeline stopped short of before.
---

# Livraison

`git` Mode 4 merges a sprint locally; nothing after that builds it, versions it, or tells anyone what shipped. This skill closes that gap: scope what's actually new, make sure it can run somewhere real, write it down, record the release, and push only if asked.

## Flow

```
Lit kb/infra/derniere-livraison.md (si absent : première livraison,
scope = tous les tickets state: done)
        ↓
Scope = tickets state: done depuis cette dernière livraison
        ↓ aucun → rien à livrer, stoppe
Demande la version (semver) à l'utilisateur — jamais devinée
        ↓
CI/environnements déjà en place (kb/infra/) ?
    Non → dispatch hosa-infra (## Installation nécessaire)
    Oui → passe
        ↓
Dispatch hosa-documentation : notes de version depuis les
tickets scopés
        ↓
Écrit/actualise kb/infra/derniere-livraison.md (version, date,
tickets inclus)
        ↓
Demande : push + PR maintenant ?
    Oui → dispatch hosa-git (Mode 3, demande explicite)
    Non → passe, reste local
        ↓
Log kb/infra/log.md
```

## Trigger

Manual: `/livraison [version]`. Auto: "livre le projet", "déploie", "prépare la release" ; proposé en Suite de `git` Mode 4 et de `bilan-sprint` une fois le sprint bouclé.

---

## Step 1: Scope the Release

Read `kb/infra/derniere-livraison.md`. If it doesn't exist, this is the first release — scope is every `Ticket` with `state: done`. If it exists, read its `## Tickets inclus` and `## Date`, and scope to every `Ticket` with `state: done` and a `verified.at` timestamp after that date, not already listed. Empty scope either way → report "Rien de nouveau à livrer depuis <dernière version ou 'le début'>." and stop.

## Step 2: Version

Ask the user for the version number (semver or the managed project's own scheme) — never guess a bump type (major/minor/patch) from ticket content alone; if the tickets suggest one, say so as a suggestion, not a default.

## Step 3: CI and Environments

Read `kb/infra/` for an existing CI pipeline / staging-or-prod environment record. Missing → this isn't a fresh install (that's `infra`'s job), it's "make what already runs in dev also run somewhere releasable" — dispatch `hosa-infra` (Mode 2, `## Installation nécessaire`) describing exactly that need. `hosa-infra` remains the only agent that ever installs or provisions anything, per the Hosa core rule — this skill never runs a CI/deploy command itself. Once confirmed in place, continue.

## Step 4: Release Notes

Dispatch `hosa-documentation` (Mode 3) with the version and the scoped tickets (title, description, linked Exigence) — it prepends a dated section to `CHANGELOG.md` at the managed project's root (or the project's existing changelog file, if different). Never write release notes from this skill directly — documentation in the managed project is `hosa-documentation`'s sole responsibility.

## Step 5: Record the Release

Write `.hosa/kb/infra/derniere-livraison.md`:

```markdown
---
type: Infra
title: Dernière livraison — <version>
description: <une ligne>
tags: [livraison]
status: stable
generated: { by: human:<user>, at: <ISO8601> }
---
## Version
<version>

## Date
<ISO8601>

## Tickets inclus
- [<titre>](../tickets/<slug>.md)
```

Overwrite the previous version of this file — it's a pointer to "the last release", not a history; the history is the release notes `hosa-documentation` wrote into the managed project, and this file's own git history if `kb-commit` runs.

## Step 6: Push / PR (Optional)

Ask the user explicitly: "Je pousse et j'ouvre une PR maintenant, ou ça reste local ?" Never assume yes because a release was just cut. On yes, dispatch `hosa-git` Mode 3 with that exact request (remote, branch, PR title/body drawn from the release notes) — `hosa-git` confirms the remote/branch back before pushing, per its own Mode 3 discipline.

## Step 7: Log

Append to `kb/infra/log.md` (create if missing) — OKF §9 format.

## No Commits

You don't commit — neither in the managed project (that's `hosa-git`'s call, only in Mode 3 on explicit request) nor in Hosa's own KB.

## Output

```
## Livraison <version>
- Tickets inclus : [liste]
- CI/environnements : [déjà en place / mis en place via hosa-infra]
- Notes de version : [chemin écrit par hosa-documentation]
- Push/PR : [effectué (remote, branche, PR) / resté local]

## Suite
[Si push/PR fait : rien de plus. Sinon : "Reste local — je pousse quand tu veux."]
```
