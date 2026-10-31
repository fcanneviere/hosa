---
name: fondamentaux
description: "Use to put every basic software function (administration, users, rights, logs, history, backup, import/export…), front/back office coverage and core NFRs in the cahier des charges, included by default. CDC stage 3, mandatory. Triggers: \"vérifie les fondamentaux\", after `redaction`."
---

# Fondamentaux

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start fondamentaux`; refused → name the missing stage to the user and stop. Stopped on a user question: `block fondamentaux --detail "<question>"`. Once the stage's output is written and committed: `done fondamentaux`. Never skip these calls: without them a cut session can't resume (« reprends ») and the session stays on the wrong model.

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
Log kb/cdc/log.md → enchaîne sur `juridique`
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
- **Socle comptes** : invitation ou inscription, connexion avec limitation des tentatives et double authentification, session et déconnexion, mot de passe et mot de passe oublié, changement d'email, administration des comptes, rôles et droits, suppression, journal de sécurité — exigences standard déjà rédigées dans `${CLAUDE_PLUGIN_ROOT}/skills/fondamentaux/socle-comptes.md`, jamais réécrites projet par projet (voir Step 1b)
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

**Non fonctionnel (NFR)** — contraintes chiffrées, `tags: [nfr]` (le juridique et la sécurité ont leur propre étape juste après : `juridique`, puis `securite`) :
- **Performance** : temps de réponse cible, volumétrie attendue
- **Disponibilité** : SLA visé, tolérance à l'indisponibilité, objectifs de reprise (RPO/RTO)
- **Protection des données (RGPD ou équivalent)** : base légale, durée de rétention, droit d'accès et à l'effacement
- **Accessibilité** : niveau visé (RGAA/WCAG), publics concernés
- **Compatibilité** : navigateurs, appareils, OS à supporter

## Step 1b: Socle comptes

Accounts are the same in every application, so they are not drafted here: `socle-comptes.md` holds the exigences, their security controls, their abuse cases and their ticket split. This stage only fills in what the project decides — 3 variants and a block of parameters with defaults — plus the project's matrice des rôles. Struck out only for an application with no accounts at all (a public site with no login), with that reason.

## Step 2: Coverage Check (PO)

Dispatch `hosa-product-owner` **with `model: opus`** — judging what the cahier des charges is missing is the PO's hardest call (Responsibility 8, `agents/product-owner.md`) with the checklist above, every `Exigence` in `kb/cdc/`, `kb/personnas/`, `kb/project/identity.md`, and the existing `kb/cdc/fondamentaux.md` if one exists (items already confirmed out of scope there aren't re-asked). It returns, per item: **Couvert** (citing the exigence that actually covers it — judged on content, not keywords) or **Manquant**, with a one-line example of what it means for *this* project, and its recommendation. For **Socle comptes**, it also returns the project exigences that already cover one of its processes (they get merged, not duplicated), the variants it recommends from the identity and personas, and the project's roles.

## Step 3: Confirm Once, Included by Default

Show the user every **Manquant** item at once, as one list: "Voici les fonctions de base absentes du cahier des charges. Je les ajoute toutes, sauf celles que tu rayes :" — each with the PO's project-specific example. One answer, not one question per item. An item struck out needs a one-line reason ("pas de données externes", "application mono-utilisateur"…), recorded as is. Silence on an item means it stays in.

With the same list, show the `espace` the PO proposes for any functional exigence that doesn't have one yet — confirmed together, corrected if wrong.

Then ask, grouped, only what's needed to write the items kept: the actor or rule the PO couldn't derive, the concrete target for each NFR (number, level, threshold — "pas encore de chiffre" is a valid answer, never invented) and how it is measured, and the priority and lot of each kept item as one proposed table (`redaction`, frontmatter: a basic function is usually `indispensable`, in the lot of the first process that needs it).

For the socle comptes, in the same round: the 3 variants (`socle-comptes.md` § Variantes, the PO's recommendation as option a) and the whole parameter table with its defaults filled in — "je garde les valeurs par défaut" is one answer — then the matrice des rôles (roles × espace × what each sees and does), drafted by the PO from the personas for the user to correct. MFA, session lengths and the attempt limits are settled here: `securite` doesn't ask them again.

In the same round, ask the context `juridique` and `securite` will need, so the user is questioned once for the three stages: country or countries of use, B2B or B2C, sector, planned release date, AI vendor if any, data sensitivity and the risks the user is ready to accept. Record the answers in `kb/cdc/fondamentaux.md` under `## Contexte`.

## Step 4: Write (PO)

Redispatch `hosa-product-owner` with the kept items and the user's answers. It writes:
- one `Exigence` per kept item, `status: draft`, in `redaction`'s structure — `espace`, `domaine`, `priorite` and `lot` set (most basics are `back-office`; login, account recovery, notifications or user help are usually `front-office` too), `tags: [nfr]` and the non-functional template (`## Exigence`, `## Mesure`…) for an NFR — linking a matching persona if one exists (e.g. an "Administrateur" for admin items), otherwise `Aucun — exigence transverse.` under `## Besoin(s) persona répondu(s)` — expected for most of this list, not a gap;
- for the socle comptes, every exigence the variants keep, copied from `socle-comptes.md` as its Rules of use say: text unchanged, parameters replaced by the chosen values, roles renamed, matrice des rôles filled in, `tags: [socle-comptes]`; a project exigence on the same process is merged, not duplicated;
- `kb/cdc/fondamentaux.md`, the record `contestation` checks for:

```markdown
---
type: Revue Fondamentaux
title: Fonctions de base du logiciel
description: "Couverture du cahier des charges sur la checklist des fondamentaux"
tags: [fondamentaux]
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
## Contexte
- <pays / B2B-B2C / secteur / date de mise en production / fournisseur d'IA / sensibilité des données / risques acceptés> : <réponse>
## Socle comptes
- Version : socle-comptes/1.0
- Variantes : V1 <mot-de-passe / sso / lien-magique> · V2 <invitation / auto-inscription> · V3 <mono / multi-organisation>
- <paramètre> : <valeur> (défaut | choisi par l'utilisateur)
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
Suite : `juridique`, lancé sans attendre.
```
