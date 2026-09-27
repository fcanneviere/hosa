# Hosa — Documentation technique et fonctionnelle (agent dédié)

**Date:** 2026-09-26
**Statut:** approuvé pour implémentation

## Contexte

Aujourd'hui, trois agents écrivent chacun leur propre documentation
technique dans le projet géré, au fil de leur travail : `hosa-infra` un
document d'installation, `hosa-architect` une documentation
d'architecture, `hosa-data-engineer` un dictionnaire de données. Chacun le
fait une fois, au moment de son intervention, sans garantie que le document
reste juste si l'état sous-jacent change ensuite. Aucune documentation
fonctionnelle (ce que l'application fait, pour qui, par persona) n'existe
nulle part — `kb/cdc/` est le cahier des charges interne de Hosa, pas un
livrable déposé dans le projet géré.

Cette itération ajoute `hosa-documentation`, seul agent habilité à écrire
la documentation technique et fonctionnelle du projet géré. Il reprend
l'écriture des trois documents techniques cités ci-dessus (leurs agents
producteurs le dispatchent désormais au lieu d'écrire eux-mêmes), et crée la
documentation fonctionnelle à partir du cahier des charges stable et des
personas. Il garantit dans le temps que ces documents restent synchronisés
avec leur source, via deux mécanismes complémentaires : une mise à jour à
chaud dispatchée par le producteur au moment où l'état change, et une
vérification à froid invocable à tout moment qui rattrape toute dérive
passée entre les mailles.

## Portée : le projet géré, pas Hosa lui-même

Même règle que le reste du pipeline : `hosa-documentation` écrit dans le
projet *externe* que Hosa pilote (chemin lu depuis l'entrée `Infra`), jamais
dans `hosa/app` ou `hosa/kb`. Sa propre traçabilité (§ suivante) vit dans
`hosa/kb/documentation/`, comme tout autre registre Hosa.

## Positionnement : agent transversal, pas une étape figée du pipeline

`hosa-documentation` n'est **pas** une étape numérotée du pipeline de
structuration des données (`stack → infra → donnees → schema-app →
schema-db → architecture → interface → backlog`). Il est dispatché à chaud
depuis quatre points existants, et invocable à froid à tout moment via son
propre skill — même principe que `hosa-infra` en Mode 2 ou que
`qualite`/`fondamentaux` : un agent transversal, jamais un blocage dans une
chaîne séquentielle.

### Points de dispatch à chaud

| Producteur | Moment | Contenu du dispatch |
|---|---|---|
| `hosa-infra` (Mode 1 et Mode 2) | Fin de mise en place / installation ponctuelle | Services/éléments installés, chemins Docker |
| `hosa-architect` | Fin du scaffolding d'architecture | Layers/modules choisis, chemins scaffoldés |
| `hosa-data-engineer` | Fin de la dérivation des structures applicatives | Entités, champs, origine, chemins écrits |
| `contestation` (skill, Étape 4) | Exigence(s) passée(s) en `status: stable` | Exigences validées + personas liées |

Les trois premiers alimentent la documentation **technique**
(`docs/technique/`) ; `contestation` alimente la documentation
**fonctionnelle** (`docs/fonctionnel/`). Chaque point de dispatch attend la
confirmation de `hosa-documentation` avant de considérer sa propre tâche
terminée (même discipline que la relation existante avec `hosa-infra`).

### Vérification à froid

Le skill `documentation` (`/documentation`), invocable à tout moment,
dispatche `hosa-documentation` en mode vérification : relit chaque entrée
de `kb/documentation/`, compare la date de ses sources à sa propre date de
synchronisation, et rafraîchit toute section qui a dérivé. Filet de
sécurité pour ce que la mise à jour à chaud aurait manqué (ex. un fichier
modifié à la main dans le projet géré, hors du flux des agents).

## Fichiers dans le projet géré

- `docs/technique/installation.md`, `docs/technique/architecture.md`,
  `docs/technique/donnees.md`
- `docs/fonctionnel/apercu.md` (vue d'ensemble, toutes personas) +
  `docs/fonctionnel/<persona-slug>.md` (un guide par persona)

Chaque fichier a une entrée `kb/documentation/` correspondante, nommée
`technique-installation.md`, `technique-architecture.md`,
`technique-donnees.md`, `fonctionnel-apercu.md`,
`fonctionnel-<persona-slug>.md` — même slug que le fichier qu'elle décrit,
préfixé par sa catégorie.

## Nouveau concept OKF `Documentation`

`kb/documentation/` (nouveau bundle) reçoit un fichier par section de
documentation que l'agent possède :

```markdown
---
type: Documentation
title: <section> — <projet>
description: <une ligne>
tags: []
status: stable
path: <chemin dans le projet géré>
sources:
  - <chemin ou slug de la source : entrée kb/infra, kb/stack, kb/cdc, code du projet géré>
generated: { by: hosa-documentation/1.0, at: <ISO8601> }
---
## Contenu
<résumé de ce que documente cette section>

## Sources
- <source> (dernière modification connue : <ISO8601 ou référence log>)
```

`sources` est la liste que la vérification à froid relit pour détecter une
dérive : si l'une d'elles a une date de log/`generated.at` postérieure à
celle de cette entrée, la section est considérée périmée et rafraîchie.

## Agent `hosa-documentation`

`agents/documentation.md`, frontmatter :
```yaml
name: hosa-documentation
model: claude-opus-4-8
memory: project
```

Rôle : seul agent habilité à écrire la documentation technique et
fonctionnelle du projet géré. Deux modes d'entrée, un seul agent (même
principe que `hosa-infra`, `hosa-qa-lead`).

### Input

Un des deux modes ci-dessous. Si le mode n'est pas clair depuis la requête,
demande plutôt que de deviner.

### Knowledge Base

| Bundle | Type | Usage |
|---|---|---|
| `kb/documentation/` | `Documentation` | Registre des sections déjà écrites, leurs sources, leur date de synchronisation |
| `kb/infra/` | `Infra` | Chemin racine du projet géré ; contenu de la doc d'installation (technique) |
| `kb/stack/` | `Stack Decision` | Contenu de la doc technique (stack retenue) |
| `kb/cdc/` | `Exigence` | Contenu de la doc fonctionnelle (besoins validés `stable`) |
| `kb/personnas/` | `Persona` | Un guide fonctionnel par persona |

Elle lit aussi directement, dans le projet géré, ce que `hosa-architect` a
scaffoldé et ce que `hosa-data-engineer` a dérivé (chemins reçus dans le
dispatch, ou déjà enregistrés dans `kb/documentation/`) — elle ne redérive
jamais une décision déjà prise ailleurs, elle la documente.

**Frontmatter à remplir correctement sur chaque concept écrit :**
- `generated: { by: human:<user>, at: <ISO8601> }` — l'utilisateur a
  tranché explicitement (ex. formulation demandée pour un guide)
- `generated: { by: hosa-documentation/1.0, at: <ISO8601> }` — rédaction
  propre à partir des sources

**Logging :** ajoute une entrée à `kb/documentation/log.md` (créé si
absent) — chronologique, plus récent en premier, OKF §9.

### Mode 1 — Mise à jour à chaud (dispatché par un autre agent/skill)

Input : le producteur (`hosa-infra`/`hosa-architect`/`hosa-data-engineer`/
`contestation`), ce qui a changé, et les chemins concernés.

1. Détermine la section technique ou fonctionnelle concernée (installation,
   architecture, données, ou le guide d'une/plusieurs persona(s)).
2. Lit `kb/documentation/` pour l'entrée existante de cette section, s'il y
   en a une — jamais de doublon, toujours une mise à jour en place.
3. Rédige ou met à jour le fichier dans le projet géré
   (`docs/technique/<section>.md` ou `docs/fonctionnel/<persona>.md`),
   dans un style cohérent avec ce qui existe déjà.
4. Écrit/met à jour `kb/documentation/<slug>.md` (`sources` et
   `generated.at` rafraîchis) et logue.
5. Confirme au producteur que la doc est en place — celui-ci ne termine sa
   propre tâche qu'après cette confirmation.

### Mode 2 — Vérification à froid (dispatché par le skill `documentation`)

1. Lit chaque entrée de `kb/documentation/`. Aucune entrée → le dit ; rien
   à vérifier tant qu'aucune section n'a jamais été écrite.
2. Pour chaque entrée, compare la date de chacune de ses `sources` (dernière
   entrée de log du bundle source, ou `generated.at` de l'`Exigence`/
   `Stack Decision`/`Infra` concernée) à `generated.at` de l'entrée elle-même.
3. Source plus récente → rafraîchit la section (même écriture qu'en Mode 1,
   étapes 3-4). Source inchangée → rien à faire, listée comme "à jour".
4. Rapporte, section par section, ce qui a été rafraîchi et ce qui était
   déjà à jour.

### Cas limites

- Rien à documenter encore (aucune `Infra`/`Stack Decision`/`Exigence`
  stable) → le dit, ne crée jamais de section vide.
- Une source a changé sans jamais passer par un dispatch à chaud (ex.
  fichier modifié à la main dans le projet géré) → seule la vérification à
  froid la rattrape ; l'agent ne garantit pas une synchronisation temps
  réel hors de ces deux mécanismes — limite assumée, voir "Hors scope".

### No Commits

Ne commit jamais — même règle que tous les agents Hosa.

### Output

```
## Documentation mise à jour (Mode 1)
- Section : technique/installation | technique/architecture | technique/donnees | fonctionnel/<persona>
- Fichier : `<path>`
- Déclenché par : <agent/skill demandeur>

## Vérification (Mode 2)
- À jour : <section>, <section>
- Rafraîchie : <section> (source : <quoi>)
- [Si aucune entrée encore : "Rien à vérifier — aucune section écrite pour l'instant"]

## Registre
- `kb/documentation/<slug>.md`

## Open Questions
[Si rien : "None"]
```

### Project Memory

Sauvegarde : les conventions de documentation déjà en place dans le projet
géré (structure de `docs/`, style), le mapping section → producteur déjà
établi. Ne sauvegarde pas : le contenu d'une entrée `Documentation` déjà
écrite — relisible depuis `kb/documentation/`.

## Skill `skills/documentation/SKILL.md`

**Trigger manuel :** `/documentation`. **Auto :** "vérifie que la
documentation est à jour", "génère la documentation du projet", "documente
le projet".

**Flow :**
```
Lit kb/infra/ (chemin racine)
        ↓
Dispatch hosa-documentation en Mode 2 (vérification à froid)
        ↓
Rapporte les sections rafraîchies et celles déjà à jour
```

**Sortie :** celle de l'agent (Mode 2).

**No Commits** : ne commit jamais.

Companion check usable anytime — pas une étape figée du pipeline, même
statut que `qualite`/`fondamentaux`.

## Modifications aux agents existants

### `hosa-infra`

Retire, en Mode 1 (Étape 8) et en Mode 2 (Étape 4), l'écriture directe de
la doc d'installation dans le projet géré. À la place : dispatche
`hosa-documentation` (Mode 1) avec ce qui a été installé et les chemins
concernés, attend sa confirmation avant de considérer sa propre tâche
terminée. `kb/infra/environnement-docker.md`/`<slug-service>.md`
(registre interne de Hosa) restent inchangés — seul le document destiné au
projet géré change de propriétaire.

### `hosa-architect`

Retire l'Étape 5 ("Write the architecture documentation in the managed
project"). À la place : une fois le scaffolding fait, dispatche
`hosa-documentation` avec les layers/modules choisis et les chemins
scaffoldés, attend sa confirmation.

### `hosa-data-engineer`

Dans la Responsabilité "Application data structure", retire l'écriture du
dictionnaire de données dans le projet géré. À la place : une fois les
entités dérivées et écrites, dispatche `hosa-documentation` avec les
entités, champs, origines et chemins.

### `contestation` (skill)

À l'Étape 4 (Sign-Off), après le passage en `stable` d'au moins une
`Exigence` : dispatche `hosa-documentation` (Mode 1) avec les exigences
validées et leurs personas liées, avant de proposer l'étape suivante
(`stack`).

## Registre dans `using-hosa` et `agents/README.md`

- `hosa-documentation` ajouté à la table "Hosa agents" de
  `agents/README.md`.
- `documentation` ajouté à la table des skills de
  `skills/using-hosa/SKILL.md`, décrit comme "companion check usable
  anytime — like `qualite`/`fondamentaux`", et à la table des triggers
  auto.

## Hors scope (v1)

- Synchronisation temps réel indépendante des deux mécanismes définis
  (aucun watcher de fichiers, aucune tâche planifiée) — seules la mise à
  jour à chaud (dispatch) et la vérification à froid (sur demande)
  détectent une dérive.
- Documentation générée pour `hosa/app`/`hosa/kb` eux-mêmes — hors
  périmètre, comme pour tout autre agent Hosa.
- Versionnage/historique des documents au-delà du `log.md` OKF standard
  (pas de changelog par document, pas de diff affiché).
- Formats de sortie autres que Markdown (pas de PDF, pas de site généré).
- Détection de dérive sur une source qui ne loggue pas dans un bundle OKF
  (ex. un fichier de code modifié à la main sans passer par
  `hosa-data-engineer`) — seule une source enregistrée dans `sources` avec
  une date lisible est comparée ; un changement de code totalement hors
  flux agent n'est pas détecté par la vérification à froid en v1.
