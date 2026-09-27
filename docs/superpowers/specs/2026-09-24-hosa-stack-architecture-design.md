# Hosa — choix de stack et architecture logicielle

**Date:** 2026-09-24
**Statut:** approuvé pour implémentation

## Contexte

Le pipeline de structuration des données (`docs/superpowers/specs/2026-09-24-hosa-data-engineer-design.md`)
qualifie l'origine des données du CDC puis dérive les structures
applicatives et base de données. Il manque deux choses en amont et en aval :
avant, rien ne choisit la stack technique du projet géré — `schema-db`
demande le moteur de base de données au fil de l'eau, sans vue d'ensemble ;
après, rien n'assemble la logique métier (CDC), la stack retenue et
l'architecture de données en une architecture logicielle cohérente.

Cette itération ajoute deux agents — `hosa-senior-dev` et `hosa-architect` —
et deux skills qui encadrent le pipeline existant.

## Portée : le projet géré, pas Hosa lui-même

Même règle que le reste du pipeline de structuration : `hosa/kb/` reste la
source de spécification, `hosa/app/` et `hosa/kb/` ne sont jamais la cible
d'écriture. Les deux nouveaux skills écrivent dans le projet *externe* que
Hosa pilote — chemin découvert/enregistré via l'entrée `Infra`, jamais
supposé être `hosa/app`.

## Pipeline mis à jour

```
interview → redaction → relecture → contestation →
stack → donnees → schema-app → schema-db → architecture
```

`stack` devient la première étape du pipeline de structuration des données ;
`architecture` en devient la dernière. Chaque étape reste invocable seule ;
chaque étape propose la suivante sans l'imposer (même logique que le reste
du pipeline).

## 1. Agent `hosa-senior-dev`

`agents/senior-dev.md`, frontmatter :
```yaml
name: hosa-senior-dev
model: claude-opus-4-8
memory: project
```

Rôle : garant du choix technique du projet géré par Hosa. Lit les `Exigence`
`stable` de `kb/cdc/` pour comprendre ce que l'application doit faire,
propose 2-3 options de stack technique (langage, framework, base de
données, hébergement si pertinent) avec leurs compromis, laisse
l'utilisateur trancher, puis écrit chaque choix comme `Stack Decision` dans
`kb/stack/`.

### Input

Une demande de choix de stack technique. Si le CDC n'a pas encore
d'`Exigence` `stable`, le dit et s'arrête — le choix de stack dépend de
savoir ce que l'application doit faire.

### Output

```
## Stack proposée
[Options présentées avec compromis]

## Stack retenue
- `kb/stack/<slug>.md` — [décision]

## Suite
Je lance `donnees` maintenant ?
```

### Project Memory

Sauvegarde : les compromis déjà expliqués à l'utilisateur pour ce projet
(pour ne pas répéter la même pédagogie). Ne sauvegarde pas : le contenu des
`Stack Decision` déjà écrites — relisibles depuis `kb/stack/`.

## 2. Skill `skills/stack/SKILL.md`

**Trigger manuel :** `/stack`. **Auto :** immédiatement après une
`contestation` propre (CDC passé en `stable`), ou "choisis la stack
technique", "quelle stack pour le projet".

**Flow :**
1. Détermine le projet cible : lit `kb/infra/` pour une entrée `Infra`
   existante ; sinon demande le chemin à l'utilisateur et l'enregistre
   (même convention que `schema-app` Step 1). Refuse `hosa/app`/`hosa/kb`.
2. Lit les `Exigence` `stable` de `kb/cdc/`, en dérive les besoins
   fonctionnels et non-fonctionnels pertinents pour le choix de stack.
3. Propose 2-3 stacks techniques (langage, framework, base de données,
   hébergement le cas échéant) avec compromis ; recommande une option.
4. L'utilisateur choisit. Écrit chaque décision comme `Stack Decision` dans
   `kb/stack/` (même format que celui déjà utilisé par `schema-db` pour la
   base de données) :
```markdown
---
type: Stack Decision
title: <catégorie> — <projet>
description: <choix technique et sa catégorie>
tags: []
status: stable
generated: { by: human:<user>, at: <ISO8601> }
---
## Décision
<choix>

## Justification
<pourquoi>
```
5. Log dans `kb/stack/log.md` (OKF §9).

**Sortie :** voir format agent ci-dessus.

## 3. Agent `hosa-architect`

`agents/architect.md`, frontmatter :
```yaml
name: hosa-architect
model: claude-opus-4-8
memory: project
```

Rôle : garant de l'architecture logicielle du projet géré. Intervient une
fois le CDC stable, la stack choisie et les structures de données (app +
DB) écrites par `hosa-data-engineer`. Conçoit une architecture logicielle
(couches, modules, limites) cohérente à la fois avec la logique métier
(CDC), la stack retenue et l'architecture de données existante, puis la
scaffold réellement dans le projet cible.

### Input

Une demande de génération de l'architecture logicielle. Si la stack ou les
structures de données ne sont pas encore en place, le dit et propose de
lancer `stack`/`schema-app`/`schema-db` d'abord plutôt que de deviner.

### Process

1. Lit `kb/cdc/` (`Exigence` `stable`), `kb/stack/` (`Stack Decision`), et
   le dictionnaire de données + migrations déjà écrits par
   `hosa-data-engineer` dans le projet cible.
2. Lit le code existant du projet cible, si présent, pour respecter les
   conventions déjà en place — même discipline que `hosa-implementer`.
3. Conçoit l'architecture (couches, modules, limites, patterns) cohérente
   avec la stack et les données ; dit ce qu'il choisit et pourquoi.
4. Scaffold l'architecture dans le projet cible : dossiers, squelettes de
   modules, boilerplate correspondant à la stack retenue.
5. Rédige la documentation d'architecture dans le projet cible (jamais dans
   `hosa/kb`) — ex. `docs/architecture.md`, ou l'emplacement de doc déjà en
   place dans le projet.
6. Met à jour l'entrée `Infra` avec le chemin du document d'architecture.

### Output

```
## Architecture conçue
[Couches/modules retenus et pourquoi]

## Structures créées
- `<path>` — [module/dossier scaffoldé]

## Documentation
- `<path>`

## Open Questions
[Si rien : "None"]
```

### No Commits

Ne commit jamais — même règle que tous les agents Hosa.

### Project Memory

Sauvegarde : les conventions d'architecture récurrentes du projet cible
(structure de dossiers, patterns déjà en place). Ne sauvegarde pas : le
contenu d'une architecture déjà scaffoldée — relisible depuis le code.

## 4. Skill `skills/architecture/SKILL.md`

**Trigger manuel :** `/architecture`. **Auto :** immédiatement après
`schema-db`, ou "crée l'architecture logicielle", "génère l'architecture de
l'application".

**Flow :**
1. Lit `kb/cdc/` stable, `kb/stack/` (`Stack Decision`), la documentation de
   données et les migrations écrites par `schema-app`/`schema-db`. Si l'une
   de ces trois sources manque, le dit et propose de lancer l'étape
   manquante d'abord.
2. Lit le code existant du projet cible (conventions).
3. Conçoit l'architecture logicielle cohérente avec stack + données +
   logique métier.
4. Scaffold l'architecture dans le projet cible.
5. Rédige la documentation d'architecture dans le projet cible.
6. Met à jour l'entrée `Infra` avec le chemin du document.

**Sortie :** voir format agent ci-dessus, plus :
```
## Suite
Pipeline de structuration des données terminé.
```

## 5. Modifications aux skills existants

### `schema-db`

Le Step 1 actuel ("Determine the Database Engine" — demande le moteur à
l'utilisateur et écrit la `Stack Decision`) est retiré. À la place : lit la
`Stack Decision` base de données déjà écrite par `stack` dans `kb/stack/`.
Si absente (le skill est invoqué seul, sans que `stack` ait tourné), retombe
sur l'ancien comportement — demande à l'utilisateur et écrit la décision —
conformément à la règle Hosa "no forced entry point".

### `schema-app`

Le Step 3 ("Read Existing Conventions") privilégie la `Stack Decision`
langage/framework quand le projet cible n'a pas encore de code existant
(cas greenfield), plutôt que de deviner sans base.

### Renumérotation des étapes

Les descriptions de `donnees`, `schema-app`, `schema-db` ("stage 1/2/3 du
pipeline de structuration des données") deviennent stage 2/3/4 ; `stack` est
stage 1, `architecture` est stage 5.

## 6. Registre dans `using-hosa`

`stack` et `architecture` sont ajoutés à la table des skills et à la table
de triggers auto de `skills/using-hosa/SKILL.md`, même format que les
entrées existantes. Les descriptions de `donnees`/`schema-app`/`schema-db`
sont mises à jour pour refléter la nouvelle numérotation.

## Hors scope (v1)

- Nouveau type OKF `Architecture Decision` dans `hosa/kb` — l'architecture
  vit dans le code et la documentation du projet cible, même principe que
  les structures de données (`hors scope` de la spec data-engineer).
- Régénération/migration d'une architecture déjà scaffoldée si la stack ou
  les données changent après coup (pas de detection de drift, même
  principe que le reste du pipeline).
- Choix de stack pour des besoins non couverts par le CDC (ex. exigences
  non-fonctionnelles hors périmètre du CDC actuel — performance, conformité
  spécifique) — reste une question ouverte posée à l'utilisateur au cas par
  cas par `hosa-senior-dev`, pas un processus formalisé.
