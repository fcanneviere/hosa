---
name: livraison
description: Use to turn a local merge into something actually shipped — scopes the `Ticket`s done since the last release, makes sure a CI pipeline with quality gates and environments exist (via `hosa-infra`), runs the security gate (`securite`, Go/No-Go), writes release notes from those tickets (via `hosa-documentation`), records the release, and optionally pushes/opens a PR (via `hosa-git`, only on explicit confirmation). Follow-on to `git` Mode 4 / `validation` — the step Hosa's pipeline stopped short of before.
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
Porte de sécurité : `securite` (mode Livraison)
    No-Go → corrige d'abord, ou dérogation explicite de l'utilisateur
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

Read `kb/infra/` for an existing CI pipeline / staging-or-prod environment record. Missing → this isn't a fresh install (that's `infra`'s job), it's "make what already runs in dev also run somewhere releasable" — dispatch `hosa-infra` (Mode 2, `## Installation nécessaire`) describing exactly that need. `hosa-infra` remains the only agent that ever installs or provisions anything, per the Hosa core rule — this skill never runs a CI/deploy command itself. The request names what "releasable" means, so `hosa-infra` doesn't have to guess: a pipeline running on every push/PR whose gates block the merge on failure, a staging environment distinct from production, secrets coming from the platform's secret store (never from the repository or the CI file, and CI never holding production secrets), and a way to roll back to the previous version. Once confirmed in place, continue.

## Step 3b: Security Gate

Invoke `securite` in Livraison mode with the version and the previous release's date. **Go** → continue. **No-Go** → `securite` asks the user whether to fix first or ship anyway; fix first → stop here and propose `debug` on the blocking ticket(s); ship anyway → the derogation is recorded by `securite`, continue and mention it in the Output.

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

## Porte de sécurité
[Go / No-Go avec dérogation](../securite/livraison-<version>.md)

## Retour arrière
- Déclencheurs : <taux d'erreur > 2× la normale, parcours critique cassé, faille découverte, intégrité des données>
- Procédure : <redéployer la version précédente — commande ou workflow réel>
- Base de données : <migrations de cette version réversibles : commande vérifiée / non réversibles : comment on s'en sort>

## Vérification après déploiement
- [ ] Health check répond
- [ ] Pas de nouveau type d'erreur dans les logs
- [ ] Parcours critique testé à la main
```

The rollback section is filled before the release, not after an incident: if `hosa-infra` reported no rollback mechanism, or a migration in scope has no verified way back, say so in `## Retour arrière` rather than leaving it blank — a release with no way back is the user's informed choice, not an oversight. The verification checklist is ticked by the user after deploying; leave it unticked.

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
- Sécurité : [Go / No-Go avec dérogation — `kb/securite/livraison-<version>.md`]
- Retour arrière : [procédure prête / absent — <raison>]
- Notes de version : [chemin écrit par hosa-documentation]
- Push/PR : [effectué (remote, branche, PR) / resté local]

## Suite
[Si push/PR fait : rien de plus. Sinon : "Reste local — je pousse quand tu veux."]
```
