---
name: livraison
description: "Use to ship merged work: scope done tickets, quality gate (`qualite`), release notes and user docs (`hosa-documentation`), tested tag (`hosa-git`), optional deployment with database backup (`hosa-dba`, `hosa-infra`), optional push. Triggers: \"livre le projet\", \"prépare la release\", \"déploie\"."
---

# Livraison

`git` Mode 2 merges a sprint locally; nothing after that checks the whole, versions it, deploys it, or tells anyone what shipped. This skill closes that gap: scope what's new, pass the quality gate, write it down, tag a tested version, deploy it if asked, record the release, and push only if asked.

## Flow

```
Lit kb/infra/derniere-livraison.md (si absent : première livraison,
scope = tous les tickets state: done)
        ↓
Scope = tickets state: done depuis cette dernière livraison
        ↓ aucun → rien à livrer, stoppe
Demande la version (semver) à l'utilisateur — jamais devinée
        ↓
Barrière qualité : `qualite` sur le code changé depuis la
dernière livraison → aucun Bloquant ouvert
        ↓
Porte de sécurité : `securite` (Livraison) → Go, ou No-Go :
corrige d'abord, ou dérogation explicite de l'utilisateur
        ↓
hosa-documentation (Mode 3) : notes de version + documentation
utilisateur
        ↓
hosa-git (Mode 3, release) : commit des docs, suite complète et
contrôles sur la branche de base, tag v<version>
        ↓
Déployer maintenant ? (question)
    Oui → hosa-dba (sauvegarde + migrations de la cible) →
          hosa-infra (Mode 3 : déploie le tag, vérifie,
          revient en arrière si échec)
    Non → passe
        ↓
Écrit kb/infra/derniere-livraison.md
        ↓
Push + PR ? (question) → hosa-git (Mode 3) sur demande explicite
        ↓
Log kb/infra/log.md
```

## Trigger

Manual: `/livraison [version]`. Auto: "livre le projet", "déploie", "prépare la release" ; proposé en Suite de `bilan-sprint`. Progress-plan stage `livraison` (`--sprint <slug>` of the sprint just reviewed); `skip` it with the user's reason when this sprint ships nothing.

---

## Step 1: Scope the Release

Read `kb/infra/derniere-livraison.md`. If it doesn't exist, this is the first release — scope is every `Ticket` with `state: done`. If it exists, read its `## Tickets inclus` and `## Date`, and scope to every `Ticket` with `state: done` and a `verified.at` timestamp after that date, not already listed. Empty scope either way → report "Rien de nouveau à livrer depuis <dernière version ou 'le début'>." and stop.

No sprint may be `active` with unmerged work the user expects in this release: list any `active` sprint and ask whether it waits.

## Step 2: Version

Ask the user for the version number (semver or the managed project's own scheme) — never guess a bump type (major/minor/patch) from ticket content alone; if the tickets suggest one, say so as a suggestion, not a default.

## Step 3: Quality Gate

Run `qualite` on the code changed since the last release (`git diff --name-only <last tag or derniere-livraison's commit>..HEAD`; first release → the whole codebase). It audits best practices, performance and security. Any **Bloquant** → stop the release: each becomes a ticket fixed in a sprint, then come back. **À corriger** findings are shown; the user decides whether they wait.

## Step 3b: Security Gate

Invoke `securite` in Livraison mode with the version and the previous release's date. **Go** → continue. **No-Go** → `securite` asks the user: fix first (stop here; each blocking finding is a ticket fixed in a sprint), or ship anyway (the derogation is recorded by `securite`; continue and say so in the Output).

## Step 4: Release Notes and User Documentation

Dispatch `hosa-documentation` (Mode 3) with the version and the scoped tickets (title, description, linked Exigence). It prepends a dated section to `CHANGELOG.md` (or the project's existing changelog) and updates the user documentation the tickets change. Never write either from this skill: documentation in the managed project is `hosa-documentation`'s alone.

## Step 5: Tested Tag

Dispatch `hosa-git` (Mode 3, « release ») with the version and the files `hosa-documentation` wrote. It commits them, runs the full suite and the `## Outillage qualité` checks on the base branch, and tags `v<version>` only if all pass. Red → stop: the base has a problem no sprint caught; report it and propose `develop <ticket> correction` or a fix ticket.

## Step 6: Deployment (Optional)

Ask one numbered question: deploy `v<version>` now? Yes:
1. With a database, dispatch `hosa-dba` (Mode 3, « release ») on the target: a backup checked restorable, then the migrations. A failure restores the backup and stops here.
2. Dispatch `hosa-infra` (Mode 3): it deploys the tag, verifies it, and rolls back on failure. No `kb/infra/deploiement.md` yet → relay its Open Questions (target, access, secrets location, rollback) to the user first.
`hosa-infra` and `hosa-dba` stay the only agents that provision or touch a database; this skill never runs a deploy command itself.

## Step 7: Record the Release

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
<version> — tag `v<version>` sur `<commit>`

## Date
<ISO8601>

## Qualité
<audit `kb/qualite/<slug>.md` — Bloquant : 0 — À corriger : N, reportés ou corrigés>

## Porte de sécurité
[Go / No-Go avec dérogation](../securite/livraison-<version>.md)

## Retour arrière
- Déclencheurs : <taux d'erreur > 2× la normale, parcours critique cassé, faille découverte, intégrité des données>
- Procédure : <redéployer la version précédente — commande réelle de `kb/infra/deploiement.md`>
- Base de données : <migrations de cette version réversibles : commande vérifiée / non réversibles : comment on s'en sort>

## Déploiement
<cible, date, vérification OK — ou "Non déployé">

## Vérification après déploiement
- [ ] Health check répond
- [ ] Pas de nouveau type d'erreur dans les logs
- [ ] Parcours critique testé à la main

## Tickets inclus
- [<titre>](../tickets/<slug>.md)
```

`## Retour arrière` is filled before the release, not after an incident: no rollback mechanism, or a migration with no verified way back → say so there; a release with no way back is the user's informed choice. The user ticks `## Vérification après déploiement` after deploying.

Overwrite the previous version of this file — it's a pointer to "the last release", not a history; the history is the changelog, the tags, and this file's own git history.

## Step 8: Push / PR (Optional)

Ask the user explicitly, as numbered questions: "Je pousse (branche et tag) et j'ouvre une PR maintenant, ou ça reste local ?" and, when pushing, "Je pousse aussi la branche de la KB (`hosa-kb`) ?" Never assume yes because a release was just cut. On yes, dispatch `hosa-git` Mode 3 with that exact request (remote, branch, tag, PR title/body drawn from the release notes) — `hosa-git` confirms the remote/branch back before pushing, per its own Mode 3 discipline.

## Step 9: Log

Append to `kb/infra/log.md` (create if missing) — OKF §9 format.

## Commits

This skill commits nothing itself: the release commit and the tag are `hosa-git`'s (Mode 3), in the user's name only.

## Output

```
## Livraison <version>
- Tickets inclus : [liste]
- Qualité : [audit, Bloquant : 0] — Sécurité : [Go / No-Go avec dérogation]
- Retour arrière : [procédure prête / absente — <raison>]
- Notes de version : [chemin] — documentation utilisateur : [sections mises à jour]
- Tag : `v<version>` sur `<commit>` — suite complète X/Y, contrôles OK
- Déploiement : [cible, vérifié / non déployé]
- Push/PR : [effectué (remote, branche, PR) / resté local]

## Suite
[Si push/PR fait : rien de plus. Sinon :] Reste local. Pour publier, demande « pousse et ouvre une PR ».
```
