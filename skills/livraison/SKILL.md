---
name: livraison
description: "Use to ship merged work: scope done tickets, quality gate (`qualite`), security and legal gates (`securite`, `juridique`), release notes and user docs (`hosa-documentation`), tested tag (`hosa-git`), optional deployment on a test target or in production (backup and every gate; `hosa-dba`, `hosa-infra`), promotion from test, optional push. Triggers: \"livre le projet\", \"prépare la release\", \"déploie\"."
---

# Livraison

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start livraison --sprint <slug>`; refused → name the missing stage to the user and stop. Stopped on a user question: `block livraison --sprint <slug> --detail "<question>"`. Once the stage's output is written and committed: `done livraison --sprint <slug>`. Never skip these calls: without them a cut session can't resume (« reprends ») and the session stays on the wrong model.

`git` Mode 2 merges a sprint locally; nothing after that checks the whole, versions it, deploys it, or tells anyone what shipped. This skill closes that gap: scope what's new, pass the quality gate, write it down, tag a tested version, deploy it if asked, record the release, and push only if asked.

## Flow

```
Demande la cible : test, production ou aucune (tag seul)
        ↓ production d'une version déjà livrée en test, base
          inchangée → promotion : saute aux parties production
Lit le dernier enregistrement de ce type (derniere-livraison.md
ou derniere-livraison-test.md ; absent : tous les tickets done)
        ↓
Scope = tickets state: done depuis cette dernière livraison
        ↓ aucun → rien à livrer, stoppe
Demande la version (semver) à l'utilisateur — jamais devinée
        ↓
Barrière qualité : audits des sprints repris, `qualite` sur le
seul code changé depuis le dernier commit audité → aucun
Bloquant ouvert ; prérequis de livraison bloquants en production
        ↓
Porte de sécurité : `securite` (Livraison, avec la cible) → Go,
ou No-Go : corrige d'abord, ou dérogation de l'utilisateur
        ↓
Porte juridique (production seulement) : `juridique` (Livraison)
→ Go, ou No-Go : corrige d'abord, ou dérogation de l'utilisateur
        ↓
hosa-documentation (Mode 3) : notes de version + documentation
utilisateur
        ↓
hosa-git (Mode 3, release) : commit des docs, suite complète
(sautée si seule la doc a changé depuis la fusion) et
contrôles sur la branche de base, tag v<version>
        ↓
Déployer maintenant sur la cible ? (question)
    Oui → hosa-dba (production : sauvegarde + migrations ;
          test : migrations seules) → hosa-infra (Mode 3 :
          déploie le tag, vérifie, revient en arrière si échec)
    Non → passe
        ↓
Écrit kb/infra/derniere-livraison.md (production) ou
derniere-livraison-test.md (test)
        ↓
Push + PR ? (question) → hosa-git (Mode 3) sur demande explicite
        ↓
Log kb/infra/log.md
```

## Trigger

Manual: `/livraison [version]`. Auto: "livre le projet", "déploie", "prépare la release", "livre en test" (target test), "passe en prod" (production, promotion when the version was tried in test) ; proposé en Suite de `bilan-sprint`. Progress-plan stage `livraison` (`--sprint <slug>` of the sprint just reviewed); `skip` it with the user's reason when this sprint ships nothing.

---

## Step 1: Target

One numbered question: where does this version go? The targets and their type are in `kb/infra/deploiement.md` `## Cible` (none yet → `hosa-infra` asks at Step 6).
- **test** — no real user, no real data: recette, staging, client demo. It serves to try the version.
- **production** — real users or real data. A test target loaded with a copy of production data counts as production: it holds data to lose and to protect.
- **aucune** — the tested tag only, no deployment; gated as test.

The type sets what blocks — a test target has nothing to lose, so production's safeguards would only slow it:

| | test / aucune | production |
|---|---|---|
| Quality gate (Bloquant), suite, tag | blocking | blocking |
| `prérequis-de-livraison` tickets (accounts, backups, production configuration) | listed | blocking |
| Security gate | code checks, and no real data or production secret on the target | complete, production configuration included |
| Legal gate | not applicable: no real user, no real data | blocking |
| Database backup before migrating | none: the test dataset reloads it | required, checked restorable |

**Promotion** — production of a version already delivered to test (`kb/infra/derniere-livraison-test.md`), with the base unchanged since its tag except documentation (`git diff --name-only v<version> HEAD`): its quality gate, release notes and tag stand, nothing is redone. Run only what production adds — the `prérequis-de-livraison` (Step 3), the security gate's production part (Step 3b), the legal gate (Step 3c) — then deploy the same tag (Step 6) and record it (Step 7). Scope and notes are the test delivery's.

## Step 1b: Scope the Release

Read the last record of the target's type: `kb/infra/derniere-livraison.md` (production) or `kb/infra/derniere-livraison-test.md` (test, aucune). A test delivery never moves the production record: the next production release still ships everything since the last production one. If it doesn't exist, this is the first release of that type — scope is every `Ticket` with `state: done`. If it exists, read its `## Tickets inclus` and `## Date`, and scope to every `Ticket` with `state: done` and a `verified.at` timestamp after that date, not already listed. Empty scope either way → report "Rien de nouveau à livrer depuis <dernière version ou 'le début'>." and stop.

No sprint may be `active` with unmerged work the user expects in this release: list any `active` sprint and ask whether it waits.

## Step 2: Version

Ask the user for the version number (semver or the managed project's own scheme) — never guess a bump type (major/minor/patch) from ticket content alone; if the tickets suggest one, say so as a suggestion, not a default.

## Step 3: Quality Gate

**Reuse the sprint audits first.** Each sprint merged since the last release has a `## Audit` (`qualite`, stage `audit`) naming its reports and the commit it audited. Take them as the evidence for the files they covered: never audit the same tree again (pilot2: the user stopped a full re-audit of a sprint audited the day before). Run `qualite` only on the files changed after the last audited commit (`git diff --name-only <audited commit>..HEAD`, and on a first release add any code file no sprint audit covered); empty list → no new audit, say so. An open Bloquant in a reused report counts as one found here. Any **Bloquant** → stop the release: each becomes a ticket fixed in a sprint, then come back. **À corriger** findings are shown; the user decides whether they wait.

**Prérequis de livraison** (open tickets tagged `prérequis-de-livraison`: database account, backups, production configuration) never block the tested tag, nor a test target: list them here and go on. **Production** with one open → blocking: no production deployment while it is open. One numbered question: go on with a test target or the tag only (recommended — the tag is ready when the ticket is fixed, and a later promotion reuses it), or stop.

## Step 3b: Security Gate

Invoke `securite` in Livraison mode with the version, the target's type, the previous release's date (same type) and the security audit reports reused in Step 3 with their audited commits. Test: the code checks, and the target holds no real data and no production secret; the production configuration is checked at production. Promotion: the production part only. **Go** → continue. **No-Go** → `securite` asks the user: fix first (stop here; each blocking finding is a ticket fixed in a sprint), or ship anyway (the derogation is recorded by `securite`; continue and say so in the Output).

## Step 3c: Legal Gate

**Production only.** Test or aucune → not run: no real user and no real personal data, so no obligation applies yet; write « Non applicable (cible de test) » in the record. The gate runs when the version goes to production, promotion included.

Invoke `juridique` in Livraison mode with the version, the planned release date and the previous production release's date. **Go** → continue. **No-Go** → `juridique` asks the user: fix first (stop here; each missing constraint is a ticket fixed in a sprint), or ship anyway (the derogation is recorded by `juridique`; continue and say so in the Output).

## Step 4: Release Notes and User Documentation

Dispatch `hosa-documentation` (Mode 3) with the version and the scoped tickets (title, description, linked Exigence). It prepends a dated section to `CHANGELOG.md` (or the project's existing changelog) and updates the user documentation the tickets change. Never write either from this skill: documentation in the managed project is `hosa-documentation`'s alone.

## Step 5: Tested Tag

Dispatch `hosa-git` (Mode 3, « release ») with the version, the files `hosa-documentation` wrote and the last merged sprint's `merge_commit`. It commits them, runs the full suite and the `## Outillage qualité` checks on the base branch, and tags `v<version>` only if all pass. Nothing but those files changed since that merge → the suite is skipped (the merge tested that tree), the checks still run. Red → stop: the base has a problem no sprint caught; report it and propose `develop <ticket> correction` or a fix ticket.

## Step 6: Deployment (Optional)

Target `aucune` → skip. Otherwise ask one numbered question: deploy `v<version>` on `<target>` now? Production with an open `prérequis-de-livraison` never gets here (Step 3). Yes:
1. With a database, dispatch `hosa-dba` (Mode 3, « release ») with the target and its type. Production: a backup checked restorable, then the migrations; a failure restores the backup and stops here. Test: the migrations only, no backup — a failure reloads the test dataset (`## Remise à zéro`) and stops here.
2. Dispatch `hosa-infra` (Mode 3) with the target: it deploys the tag, verifies it, and rolls back on failure. No `kb/infra/deploiement.md` yet → relay its Open Questions (targets and their type, access, secrets location, rollback) to the user first.
`hosa-infra` and `hosa-dba` stay the only agents that provision or touch a database; this skill never runs a deploy command itself.

## Step 7: Record the Release

Write `.hosa/kb/infra/derniere-livraison.md` (production, promotion included) or `.hosa/kb/infra/derniere-livraison-test.md` (test, aucune):

```markdown
---
type: Infra
title: Dernière livraison — <version> (<test | production>)
description: "<une ligne>"
tags: [livraison, <test | production>]
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

## Porte juridique
[Go / No-Go avec dérogation](../juridique/livraison-<version>.md) — test : Non applicable (cible de test)

## Prérequis de livraison
<tickets ouverts, ou "Aucun" — production : toujours "Aucun">

## Retour arrière
- Déclencheurs : <taux d'erreur > 2× la normale, parcours critique cassé, faille découverte, intégrité des données>
- Procédure : <redéployer la version précédente — commande réelle de `kb/infra/deploiement.md`>
- Base de données : <production : migrations réversibles, commande vérifiée / non réversibles : comment on s'en sort ; sauvegarde <emplacement, date> — test : rechargement du jeu de test>

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

Overwrite the previous version of this file — it's a pointer to "the last release" of its type, not a history; the history is the changelog, the tags, and this file's own git history.

## Step 8: Push / PR (Optional)

Ask the user explicitly, as numbered questions: "Je pousse (branche et tag) et j'ouvre une PR maintenant, ou ça reste local ?" and, when pushing, "Je pousse aussi la branche de la KB (`hosa-kb`) ?" Never assume yes because a release was just cut. On yes, dispatch `hosa-git` Mode 3 with that exact request (remote, branch, tag, PR title/body drawn from the release notes) — `hosa-git` confirms the remote/branch back before pushing, per its own Mode 3 discipline.

## Step 9: Log

Append to `kb/infra/log.md` (create if missing) — OKF §9 format.

## Commits

This skill commits nothing itself: the release commit and the tag are `hosa-git`'s (Mode 3), in the user's name only.

## Output

```
## Livraison <version> — <test | production (promotion) | tag seul>
- Tickets inclus : [liste]
- Qualité : [audit, Bloquant : 0] — Sécurité : [Go / No-Go avec dérogation] — Juridique : [Go / No-Go avec dérogation / non applicable (test)]
- Prérequis de livraison : [aucun / ouverts : <tickets> — listés (test), bloquants (production)]
- Retour arrière : [procédure prête / absente — <raison>]
- Notes de version : [chemin] — documentation utilisateur : [sections mises à jour]
- Tag : `v<version>` sur `<commit>` — suite complète X/Y (ou sautée : seule la doc a changé depuis <merge_commit>), contrôles OK
- Déploiement : [cible, vérifié / non déployé]
- Push/PR : [effectué (remote, branche, PR) / resté local]

## Suite
[Si push/PR fait : rien de plus. Sinon :] Reste local. Pour publier, demande « pousse et ouvre une PR ».
```
