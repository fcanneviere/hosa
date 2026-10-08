---
name: fondamentaux
description: Use to make sure the cahier des charges contains every basic function of a software product that personas never think to ask for (administration, user management, rights, logs, error log, change history, backup, import/export, settings, notifications…) plus the core non-functional requirements. `hosa-product-owner` checks coverage against a standard checklist, includes every missing item by default, and the user only strikes out what the project genuinely doesn't need. CDC pipeline stage 3 (interview → redaction → fondamentaux → securite → relecture → contestation) — mandatory: `contestation` won't sign off without it. Also usable anytime.
---

# Fondamentaux

Personas describe what they need to *do*; they never ask for the plumbing that makes an application usable, operable and safe — an admin panel, user management, error logs, a change history, backups, exports. Making sure those are in the cahier des charges is the Product Owner's job, not the personas'. This stage checks `kb/cdc/` against a standard checklist and writes every missing basic as an `Exigence` — included by default, never silently dropped.

## Flow

```
Dispatch hosa-product-owner (Responsabilité 8) : checklist ×
kb/cdc/ → Couvert / Manquant, avec une recommandation et un
exemple concret pour ce projet par item manquant
        ↓
Présente TOUS les manquants d'un coup, inclus par défaut —
l'utilisateur ne raye que ce dont le projet n'a pas besoin
        ↓
Questions ciblées sur ce qui manque pour rédiger les items
retenus (chiffres NFR compris — "pas encore" est valide)
        ↓
Redispatch hosa-product-owner : écrit une Exigence (draft)
par item retenu + kb/cdc/fondamentaux.md (le bilan, item
par item)
        ↓
Log kb/cdc/log.md → enchaîne sur `securite`
```

## Trigger

Manual: `/fondamentaux`. Auto: immediately after `redaction` (every time it writes new exigences), or "vérifie les fondamentaux du cahier des charges", "le cahier des charges couvre-t-il les basiques (admin, utilisateurs, logs, sauvegarde, import/export...)", "assure-toi qu'on n'a pas oublié l'administration/la sauvegarde/les exports". `contestation` also invokes it itself if `kb/cdc/fondamentaux.md` is missing.

---

## Step 1: The Checklist

The standard list `hosa-product-owner` checks against — pass it as is. Don't drop an item without the user striking it out; an item this list doesn't name can be added by the PO when the project's domain clearly calls for it (it says why).

**Fonctionnel — administration et exploitation**
- **Front office et back office** : deux espaces distincts — celui des utilisateurs finaux et celui de l'équipe qui exploite l'application — avec leurs accès, leurs rôles et leur point d'entrée
- **Gestion back-office de chaque donnée du front** : pour tout ce que le front office affiche ou collecte, qui le crée, le valide/modère, le corrige, le supprime et le suit, depuis le back office
- **Interface d'administration** : back-office pour gérer contenus, données de référence, paramètres
- **Gestion des utilisateurs** : création/invitation, modification, désactivation et suppression de comptes, profil utilisateur
- **Authentification** : connexion, déconnexion, gestion et expiration de session
- **Récupération de compte** : mot de passe oublié, réinitialisation
- **Gestion des droits et rôles** : qui peut voir/faire quoi, attribution des rôles
- **Paramétrage / configuration** : réglages modifiables sans redéploiement
- **Notifications** : email/in-app sur les événements clés, préférences de notification

**Fonctionnel — données**
- **Import de données** : formats, contrôle et rapport d'erreurs d'import
- **Export de données** : formats, périmètre, qui peut exporter
- **Sauvegarde et restauration** : fréquence, rétention, procédure de restauration testée
- **Archivage et purge** : ce qui est archivé/supprimé, quand, par qui
- **Recherche, filtres, tri et pagination** des listes

**Fonctionnel — traçabilité**
- **Journal d'audit** : qui a fait quelle action sensible, quand (connexions, droits, suppressions, exports)
- **Historique des modifications** : pour chaque donnée métier modifiable, qui l'a changée, quand, valeur avant/après, consultable
- **Journal des erreurs** : erreurs applicatives tracées avec contexte, consultables par un administrateur
- **Supervision et alertes** : état de santé de l'application, alerte en cas de panne ou d'erreurs répétées

**Fonctionnel — utilisateur final**
- **Messages d'erreur compréhensibles** : l'utilisateur sait ce qui s'est passé et quoi faire
- **Aide et documentation utilisateur** : aide en ligne, guide, contact support

**Non fonctionnel (NFR)** — contraintes chiffrées, `tags: [nfr]` (la sécurité a sa propre étape juste après : `securite`) :
- **Performance** : temps de réponse cible, volumétrie attendue
- **Disponibilité** : SLA visé, tolérance à l'indisponibilité, objectifs de reprise (RPO/RTO)
- **Protection des données (RGPD ou équivalent)** : base légale, durée de rétention, droit d'accès et à l'effacement
- **Accessibilité** : niveau visé (RGAA/WCAG), publics concernés
- **Compatibilité** : navigateurs, appareils, OS à supporter

## Step 2: Coverage Check (PO)

Dispatch `hosa-product-owner` (Responsibility 8, `agents/product-owner.md`) with the checklist above, every `Exigence` in `kb/cdc/`, `kb/personnas/`, `kb/project/identity.md`, and the existing `kb/cdc/fondamentaux.md` if one exists (items already confirmed out of scope there aren't re-asked). It returns, per item: **Couvert** (citing the exigence that actually covers it — judged on content, not keywords) or **Manquant**, with a one-line example of what it means for *this* project, and its recommendation.

## Step 3: Confirm Once, Included by Default

Show the user every **Manquant** item at once, as one list: "Voici les fonctions de base absentes du cahier des charges. Je les ajoute toutes, sauf celles que tu rayes :" — each with the PO's project-specific example. One answer, not one question per item. An item struck out needs a one-line reason ("pas de données externes", "application mono-utilisateur"…), recorded as is. Silence on an item means it stays in.

With the same list, show the `espace` the PO proposes for any functional exigence that doesn't have one yet — confirmed together, corrected if wrong.

Then ask, grouped, only what's needed to write the items kept: the actor or rule the PO couldn't derive, and the concrete target for each NFR (number, level, threshold — "pas encore de chiffre" is a valid answer, never invented).

## Step 4: Write (PO)

Redispatch `hosa-product-owner` with the kept items and the user's answers. It writes:
- one `Exigence` per kept item, `status: draft`, in `redaction`'s structure — `espace` set (most basics are `back-office`; login, account recovery, notifications or user help are usually `front-office` too), `tags: [nfr]` for an NFR — linking a matching persona if one exists (e.g. an "Administrateur" for admin items), otherwise `Aucun — exigence transverse.` under `## Besoin(s) persona répondu(s)` — expected for most of this list, not a gap;
- `kb/cdc/fondamentaux.md`, the record `contestation` checks for:

```markdown
---
type: Revue Fondamentaux
title: Fonctions de base du logiciel
description: Couverture du cahier des charges sur la checklist des fondamentaux
tags: [fondamentaux]
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
## Bilan
- <item> — Couvert : [exigence](<slug>.md)
- <item> — Ajouté : [exigence](<slug>.md)
- <item> — Hors périmètre (confirmé par l'utilisateur) : <raison>
```

On a re-run, update this file in place — it always reflects the latest pass.

## Step 5: Log

`hosa-product-owner` appends every file written to `kb/cdc/log.md` — OKF §9.

## No Commits

You don't commit. Report what changed in the KB and let the user or the orchestrating flow decide when to commit.

## Output

```
## Fondamentaux
- [Item] — [Couvert : <exigence> / Ajouté : <exigence> / Hors périmètre : <raison>]

## Exigences écrites
- `kb/cdc/<slug>.md` — <titre> (status: draft)
- [If none: "Aucune — tout était déjà couvert ou hors périmètre"]

## Suite
J'analyse la sécurité du cahier des charges maintenant ? (skill `securite`)
```
