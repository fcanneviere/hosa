---
name: fondamentaux
description: Use to check the cahier des charges against a standard checklist of cross-cutting essentials (admin interface, login, rights, settings, import/export, backup, audit log, notifications) that personas rarely think to ask for, and write missing ones as new `Exigence`. Mandatory CDC stage owned by `hosa-product-owner`, between `redaction` and `relecture` — also usable anytime after.
---

# Fondamentaux

Personas describe what they need to *do*; they rarely ask for the plumbing that makes an application usable and safe to operate — an admin panel, a login page, a way to back up or import/export data. This skill checks `kb/cdc/` against a fixed checklist of those basics and fills the gaps.

## Flow

```
Lit kb/cdc/ existant
        ↓
Pour chaque item de la checklist standard : couvert par une
Exigence existante, ou manquant ?
        ↓
Pour les items manquants : une seule série Q1, Q2…, réponse
recommandée par le PO selon le projet
        ↓ oui                              ↓ non
Écrit une Exigence (kb/cdc/, status: draft)   Noté "hors périmètre" dans le rapport
        ↓
Log kb/cdc/log.md
        ↓
Enchaîne sur `relecture`
```

## Trigger

Manual: `/fondamentaux`. Auto: "Vérifie les fondamentaux du cahier des charges", "Le cahier des charges couvre-t-il les basiques (admin, login, import/export...)", "Assure-toi qu'on n'a pas oublié l'administration/la sauvegarde/les exports".

---

## Step 1: The Checklist

Fixed list — don't invent extra items and don't drop any without asking the user first:

- **Interface d'administration** : back-office pour gérer contenus/utilisateurs/données de référence
- **Gestion des utilisateurs** : création/invitation, profil, désactivation, suppression d'un compte
- **Authentification (connexion)** : page de login, gestion de session
- **Gestion des droits et rôles** : qui peut faire quoi
- **Récupération de compte** : mot de passe oublié, réinitialisation
- **Paramétrage / configuration** : réglages de l'application modifiables sans redéploiement
- **Import de données**
- **Export de données**
- **Sauvegarde et restauration**
- **Journalisation / audit des actions sensibles** : qui a fait quoi, quand
- **Notifications utilisateur** : email/in-app sur les événements clés

**Exigences non fonctionnelles (NFR)** — même logique, checklist distincte car ce sont des contraintes chiffrées, pas des fonctionnalités :
- **Performance** : temps de réponse cible, volumétrie attendue
- **Disponibilité** : SLA visé, tolérance à l'indisponibilité
- **Protection des données (RGPD ou équivalent)** : base légale, durée de rétention, droit à l'effacement
- **Sécurité** : sensibilité des données manipulées (personnelles, financières, de santé…), exigences d'authentification (MFA, durée de session), obligations réglementaires ou contractuelles — le socle dont `hosa-security` part pour son modèle de menaces
- **Supervision** : qui doit être alerté de quoi quand l'application tombe ou se dégrade, et dans quel délai
- **Accessibilité** : niveau visé (ex: RGAA/WCAG), publics concernés
- **Compatibilité** : navigateurs/appareils/OS à supporter

## Step 2: Coverage Check

Read every `Exigence` in `kb/cdc/`. For each checklist item, judge — don't pattern-match on keywords alone, read what the exigence actually covers — whether an existing exigence already addresses it. Mark **Couvert** (cite the exigence) or **Manquant**.

## Step 3: Confirm and Write Missing Items

Act as `hosa-product-owner`: the essentials are the PO's responsibility, not something the user must think of. For each **Manquant** item, decide the recommended answer from the project (`kb/project/identity.md`, personas, existing exigences) — e.g. any app with more than one user needs user management, authentication and rights. Then ask all the Manquant items at once, as one numbered block (`using-hosa` Core Rules, "Question format"): "Q1. <item> — <exemple concret pour ce projet> : oui (recommandé) / non". Don't assume every item applies — a project with no external data source has no real need for import, for instance, and its recommended answer is "non".

- **Non** → note "Hors périmètre (confirmé par l'utilisateur)" in the report, don't write anything.
- **Oui, item fonctionnel** → ask only what's missing to fill the six sections (objectif, données en entrée/sortie, qui fait quoi, responsable) — a couple of targeted questions, not a full `interview` pass. Then write `kb/cdc/<slug-item>.md` using the same structure as `redaction`:
- **Oui, item NFR** → ask for the concrete target (chiffre, niveau, seuil — "aucun chiffre encore" est une réponse valide, ne l'invente pas), and write the same structure below with `tags: [nfr]` so `hosa-senior-dev`/`hosa-infra` can find every NFR at once instead of re-reading the whole cahier des charges.

```markdown
---
type: Exigence
title: <nom de l'item>
description: <une ligne>
tags: []            # [nfr] pour une exigence non fonctionnelle
status: draft
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
## Objectif du processus
<une à deux phrases concrètes>

## Données en entrée
- <donnée nécessaire>

## Données en sortie
- <donnée produite>

## Qui fait quoi
- <rôle/persona> : <action concrète>

## Responsable
<rôle ou persona responsable>

## Besoin(s) persona répondu(s)
- [<persona>](../personnas/<slug>.md) : <besoin précis>
```

Check `kb/personnas/` for a persona matching the item (e.g. an "Administrateur" persona for admin-interface or rights items). Link it if one exists; otherwise write `Aucun — exigence transverse.` under `## Besoin(s) persona répondu(s)` — most of this checklist is transverse rather than persona-driven, and that's expected, not a gap to force-fix.

## Step 4: Log

Append to `kb/cdc/log.md` (create if missing) — OKF §9: chronological, most recent date first, grouped by date.

## No Commits

You don't commit. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa` Core Rules, "Git checkpoints".

## Output

```
## Checklist
- [Item] — [Couvert: <exigence> / Manquant → écrit / Hors périmètre (confirmé)]

## Exigences écrites
- `kb/cdc/<slug>.md` — <titre> (status: draft)
- [If none: "Aucune — tout était déjà couvert ou hors périmètre"]

## Suite
Fondamentaux couverts — relecture en cours (skill `relecture`).
```
