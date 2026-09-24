# Hosa — pilotage de projet (KB OKF + app + skill)

**Date:** 2026-09-23
**Statut:** approuvé pour implémentation

## Contexte

`C:\dev\hosa` héberge SimFlow, un plugin Claude Code (agents + skills de cycle de dev).
`C:\dev\hosa\hosa` est le projet cible : une couche de pilotage par-dessus SimFlow,
inspirée (très librement) de [paperclip](https://github.com/paperclipai/paperclip) —
mais réduite à l'usage d'un seul développeur en local, sans org chart, budgets,
auth ni multi-tenant.

Trois livrables, à construire dans cet ordre car chacun dépend du précédent :

1. Format et structure de la base de connaissance (KB) — `hosa/kb/`
2. Skill `hosa` qui lit/écrit la KB avec traçabilité
3. App de visualisation (lecture seule) — `hosa/app/`

### Phasage

SimFlow (agents/skills existants dans `C:\dev\hosa\skills` et `agents/`) sert de
base et n'est pas modifié dans cette itération. Le travail sur les skills
(section 2 : le skill `hosa`) est repoussé à une phase ultérieure dédiée.

**Périmètre de cette itération : sections 1 (KB) et 3 (app) uniquement.**
Comme le skill `hosa` n'existe pas encore, la KB de départ est peuplée
manuellement (ou par toi, directement) — l'app doit donc fonctionner sur une
KB créée à la main, sans dépendre du skill.

## 1. Format de la KB : OKF v0.2

Référence : [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).

Résumé opérationnel : chaque concept est un fichier `.md` avec un bloc
frontmatter YAML (seul champ obligatoire : `type`) suivi d'un corps markdown
libre. Un dossier peut contenir un `index.md` (listing, sans frontmatter sauf
`okf_version` à la racine) et un `log.md` (historique daté).

### 1.1 Bundles et types

Chaque sous-dossier de `hosa/kb/` est un bundle OKF avec un type de concept dédié :

| Dossier | `type` | Contenu |
|---|---|---|
| `kb/project/` | `Project` | Identité du projet (singleton) : nom, objectif, descriptif, public cible |
| `kb/cdc/` | `Exigence` | Une exigence/besoin par fichier, extrait du cahier des charges |
| `kb/personnas/` | `Persona` | Un persona (PO, utilisateur...) par fichier |
| `kb/rules/design/` | `Design Rule` | Règles de conception |
| `kb/rules/security/` | `Security Rule` | Règles de sécurité |
| `kb/stack/` | `Stack Decision` | Choix techniques (façon ADR) |
| `kb/infra/` | `Infra` | Notes d'infrastructure |
| `kb/test/` | `Test Plan` | Plans/stratégies de test |
| `kb/tickets/` (nouveau dossier) | `Ticket` | Tickets créés par l'agent, suivis par l'utilisateur |

`kb/index.md` liste les bundles à la racine (progressive disclosure, §8 OKF),
avec `okf_version: "0.2"` en frontmatter.

### 1.2 Frontmatter commun (traçabilité)

Tous les concepts, quel que soit leur type, portent les familles OKF de
provenance/trust quand l'info est connue :

```yaml
type: <Exigence|Persona|Design Rule|Security Rule|Stack Decision|Infra|Test Plan|Ticket>
title: <nom court>
description: <résumé une ligne>
tags: [<tag>, ...]
status: draft | stable | deprecated      # défaut: stable
generated: { by: <acteur>, at: <ISO8601> }   # qui a écrit/demandé ce concept
verified: { by: <acteur>, at: <ISO8601> }    # optionnel, qui a validé
sources:                                      # optionnel, d'où ça vient
  - { id: <clé>, resource: <path|url>, title: <libellé> }
```

Convention d'acteur (§7 OKF), reprise telle quelle :
- `human:<id>` — une personne (ex: `human:fcanneviere`)
- `<producteur>/<version>` — un agent (ex: `claude-code/sonnet-5`)
- `process:<id>` — un automatisme

`verified.by` avec préfixe `human:` ⇒ trust tier "human-reviewed" ; sinon
"machine-confirmed" ; absent ⇒ "unverified" (§5.3 OKF). Cette info répond
directement au besoin "qui a demandé quoi, qui a validé quoi".

### 1.3 Concept `Ticket`

Le seul type avec un champ additionnel producteur-défini, `state` — distinct
du `status` OKF (qui décrit le cycle de vie du *document*, pas l'avancement
de la *tâche*) :

```yaml
type: Ticket
title: <titre court>
description: <une ligne>
tags: [<tag>, ...]
state: todo | doing | done | blocked
generated: { by: <acteur qui a créé/demandé le ticket>, at: <ISO8601> }
verified: { by: <acteur qui a clos/confirmé>, at: <ISO8601> }   # ajouté au passage en "done"
---
<corps: description libre, liens markdown vers les concepts liés (exigence, persona...)>
```

### 1.4 Journalisation

Chaque dossier de bundle modifié reçoit une entrée dans son `log.md` (§9 OKF)
à chaque création/modification de concept par le skill — format standard OKF,
liste chronologique groupée par date, entrée la plus récente en tête.

## 2. Skill `hosa`

**Statut (2026-09-24) :** une première tranche est implémentée — initialisation/mise
à jour de l'identité du projet (`kb/project/`) et des personas. Les autres
responsabilités listées ci-dessous restent à construire.

Nouveau dossier `C:\dev\hosa\skills\hosa\SKILL.md`, suivant les conventions
existantes des skills SimFlow (frontmatter `name`/`description`, diagramme de
flux, sections pas-à-pas). Référencé dans le tableau de
`skills/using-simflow/SKILL.md` au même titre que `build`/`iterate`/`status`/etc.

### Responsabilités

- Créer/mettre à jour des concepts OKF dans `hosa/kb/` (`Exigence`, `Persona`,
  `Stack Decision`, `Ticket`, etc.) à partir d'une demande en langage naturel.
- Renseigner correctement `generated.by` : `human:<user>` si l'utilisateur
  demande explicitement la création, `<agent>/<version>` si l'agent décide
  seul (ex: crée un ticket pour un besoin secondaire découvert en cours de
  route).
- Ajouter une entrée `log.md` dans le bundle concerné à chaque changement.
- Répondre aux questions de traçabilité ("qui a demandé X ?", "d'où vient
  cette règle ?") en lisant `generated`/`sources` dans la KB.
- Peut être invoqué depuis une autre session SimFlow (ex: pendant
  `simflow:build`, si un besoin hors scope apparaît → créer un `Ticket` au
  lieu de dévier la tâche en cours).

### Triggers auto

| L'utilisateur dit... | Action |
|---|---|
| "Ajoute cette exigence...", "Note dans le cahier des charges..." | Créer un concept `Exigence` dans `kb/cdc/` |
| "Crée un persona pour...", "Le PO veut..." | Créer un concept `Persona` dans `kb/personnas/` |
| "Crée un ticket pour...", "Note ça pour plus tard" | Créer un `Ticket` dans `kb/tickets/` |
| "On a décidé d'utiliser X pour...", "Choix technique :" | Créer une `Stack Decision` dans `kb/stack/` |
| "Qui a demandé X ?", "D'où vient cette règle ?" | Chercher dans la KB, répondre avec `generated`/`sources` |

Invocation manuelle : `/hosa`.

## 3. App de pilotage (lecture seule)

Dossier `hosa/app/`. Objectif : visualiser la KB et les tickets, sans écrire
dans les fichiers (l'écriture reste la responsabilité du skill). Architecture
choisie pour permettre un passage ultérieur en lecture/écriture sans refonte.

### Architecture

- **Backend** : Node + Express, pas de base de données — la KB de fichiers
  *est* la source de vérité. À chaque requête, parcourt `hosa/kb/`, parse le
  frontmatter (`gray-matter`), sert du JSON.
- **API** (lecture seule) :
  - `GET /api/concepts?type=<Type>` — liste des concepts d'un type, avec
    frontmatter et chemin
  - `GET /api/concepts/*path` — un concept complet (frontmatter + corps rendu)
  - `GET /api/tickets` — raccourci équivalent à `?type=Ticket`, groupé par `state`
- **Frontend** : HTML/CSS/JS vanilla, pas de framework. Deux vues :
  - **Kanban tickets** — colonnes todo/doing/done/blocked, lecture seule
  - **Explorateur KB** — liste par type/tag avec recherche simple
  - Pas de live-reload au départ : bouton "rafraîchir" manuel.

### Chemin d'évolution vers l'écriture

L'API et le stockage fichier étant déjà séparés du frontend, ajouter l'écriture
plus tard = ajouter des routes `PATCH`/`POST` qui réécrivent le frontmatter
(en préservant le corps) et loggent dans `log.md` — pas de restructuration du
backend ni du frontend nécessaire.

## Hors scope (v1)

- Authentification, multi-utilisateur, multi-organisation
- Org chart, budgets/coûts, heartbeats/scheduling d'agents
- Écriture depuis l'app (voir chemin d'évolution ci-dessus)
- Live-reload / websocket
- Attestation de calculs OKF (§10 de la spec) — non pertinent pour ce cas d'usage
