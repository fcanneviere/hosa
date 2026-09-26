# Hosa — agent data engineer et pipeline de structuration des données

**Date:** 2026-09-24
**Statut:** approuvé pour implémentation

## Contexte

Le pipeline CDC (`docs/simflow/specs/2026-09-24-hosa-cdc-pipeline-design.md`)
produit des `Exigence` stables dans `kb/cdc/`, chacune avec ses `Données en
entrée`/`Données en sortie`. Rien, aujourd'hui, ne précise l'origine de ces
données (générée par le système, fournie par une source externe, saisie par
un utilisateur), et rien ne transforme cette spécification en structure de
données réelle — ni côté application, ni côté base de données.

Cette itération ajoute un agent `hosa-data-engineer`, garant de la donnée, et
trois skills qui complètent le cahier des charges puis implémentent la
structure de données correspondante.

## Portée : le projet géré, pas Hosa lui-même

`hosa/kb/` (CDC, personas) reste la source de spécification. `hosa/app/` et
sa décision "pas de base de données" (§3 de
`docs/simflow/specs/2026-09-23-hosa-pilotage-design.md`) ne sont **pas**
concernés et restent inchangés. Les skills 2 et 3 écrivent dans le projet
*externe* que Hosa pilote — chemin découvert/demandé à l'exécution, jamais
supposé être `hosa/app`. Même logique que `simflow-implementer` : lire les
conventions existantes du projet cible avant d'écrire.

## 1. Agent `hosa-data-engineer`

`agents/data-engineer.md`, frontmatter :
```yaml
name: hosa-data-engineer
model: claude-opus-4-8
memory: project
```

Rôle : garant de la donnée du projet géré par Hosa. Lit `kb/cdc/`,
`kb/personnas/`, `kb/stack/`, `kb/infra/`. N'écrit dans `hosa/kb/` que les
concepts propres à ses skills (annotations d'origine sur les `Exigence`,
entrée `Infra`, `Stack Decision` DB — voir sections skills). Ne commit
jamais — même règle que tous les agents Hosa/SimFlow, le commit reste à
l'utilisateur ou au flow orchestrateur.

### Input

Reçoit une des trois demandes correspondant à ses skills : qualification des
données du CDC, génération de la structure applicative, génération de la
structure base de données. Si l'intention n'est pas claire, demande laquelle
avant d'agir (même règle que `hosa-product-owner`).

### Output

Chaque skill définit son propre format de sortie (voir sections 3.1-3.3) ;
l'agent ne restitue pas de format générique en dehors des skills.

### Project Memory

Sauvegarde ce qui compte au-delà d'une session :
- Le chemin du projet cible une fois découvert (complète, ne remplace pas,
  l'entrée `Infra` qui reste la source de vérité écrite)
- Conventions de structuration de données récurrentes du projet cible
  (naming, ORM/framework utilisé, style de migration)
- Décisions d'origine de données ambiguës déjà tranchées, pour ne pas
  reposer la même question au persona à chaque passage

Ne sauvegarde pas : le contenu d'une `Exigence` donnée, une structure de
données ponctuelle déjà écrite dans le projet cible — relisible depuis le
code ou la KB.

## 2. Schéma `Exigence` — annotation d'origine

Le frontmatter et les six sections existantes (§2 du pipeline CDC) restent
inchangés. Seuls les items sous `Données en entrée`/`Données en sortie`
gagnent une annotation d'origine, ajoutée en place :

```markdown
## Données en entrée
- <donnée> — origine : générée | fournie | saisie (par <persona ou système>)

## Données en sortie
- <donnée> — origine : générée | fournie | saisie (par <persona ou système>)
```

- **générée** : produite par le système/processus lui-même (par <système ou
  processus>).
- **fournie** : vient d'une source externe déjà existante (par <source>).
- **saisie** : entrée manuellement par un utilisateur (par <persona>).

Un item sans annotation signifie que la qualification n'a pas encore eu
lieu — c'est précisément ce que le skill `donnees` corrige.

## 3. Les trois skills

Nouveau dossier par skill, mêmes conventions que l'existant (frontmatter
`name`/`description`, diagramme de flux, sections pas-à-pas, pas de commit).
Placement dans le pipeline : `interview → redaction → relecture →
contestation → donnees → schema-app → schema-db`. Chacun reste invocable
seul ; chaque étape propose la suivante sans l'imposer (même logique que le
pipeline CDC).

### 3.1 `skills/donnees/SKILL.md`

**Trigger manuel :** `/donnees`. **Auto :** immédiatement après une
`contestation` propre (CDC passé en `stable`), ou "précise les données du
cahier des charges".

**Flow :**
1. Pour chaque `Exigence` `stable` de `kb/cdc/` (ou seulement celles
   touchées dans cette session si enchaîné depuis `contestation`), relit
   `Données en entrée`/`Données en sortie`.
2. Pour chaque item déjà annoté, passe. Pour chaque item non annoté ou dont
   l'origine est ambiguë : si l'origine dépend du point de vue d'un persona
   (qui saisit quoi), dispatch `hosa-key-user` en mode **interview
   processus** existant (`agents/key-user.md` §"process-interview
   request") — pas de nouveau mode à créer. Pour tout ce qui ne dépend
   d'aucun persona (donnée technique générée par un composant système),
   interroge l'utilisateur directement.
3. Écrit l'annotation en place dans l'`Exigence` (préserve tout le reste du
   contenu).
4. Log dans `kb/cdc/log.md` (OKF §9).

**Sortie :**
```
## Exigences qualifiées
- `kb/cdc/<slug>.md` — <n> items annotés

## Suite
Je lance `schema-app` maintenant ?
```

### 3.2 `skills/schema-app/SKILL.md`

**Trigger manuel :** `/schema-app`. **Auto :** immédiatement après
`donnees`, ou "génère la structure de données de l'application".

**Flow :**
1. Détermine le projet cible : lit `kb/infra/` pour une entrée `Infra`
   existante donnant le chemin racine du projet ; sinon demande le chemin à
   l'utilisateur et l'enregistre (`type: Infra`, `kb/infra/<slug>.md`,
   `generated: { by: human:<user>, ... }`).
2. Lit les `Exigence` `stable` annotées de `kb/cdc/` et les `Persona`
   concernés ; dérive les entités de données impliquées (une entité par
   regroupement cohérent de données en entrée/sortie).
3. Lit le code existant du projet cible (conventions, langage, framework,
   ORM éventuel) avant d'écrire quoi que ce soit — même règle que
   `simflow-implementer`.
4. Écrit les structures de données (types/modèles/schémas) dans le projet
   cible, dans le style déjà en place.
5. Rédige la documentation de la structure de données (dictionnaire de
   données : entité, champ, type, origine reprise du CDC, exigence liée)
   dans le projet cible.
6. Met à jour l'entrée `Infra` avec le chemin du fichier de documentation
   écrit, pour que les prochaines exécutions le retrouvent.

**Sortie :**
```
## Structures créées
- `<path>` — <entité> (<n> champs)

## Documentation
- `<path>`

## Suite
Je lance `schema-db` maintenant ?
```

### 3.3 `skills/schema-db/SKILL.md`

**Trigger manuel :** `/schema-db`. **Auto :** immédiatement après
`schema-app`, ou "génère la structure de base de données".

**Flow :**
1. Cherche une `Stack Decision` existante dans `kb/stack/` couvrant le choix
   de base de données du projet cible. Absente → demande à l'utilisateur,
   écrit la décision (`type: Stack Decision`, `kb/stack/<slug>.md`).
2. Reprend les entités dérivées en 3.2 (ou les redérive si `schema-app` n'a
   pas tourné dans cette session).
3. Lit les conventions de migration/DDL déjà en place dans le projet cible
   (outil de migration, style de nommage) avant d'écrire.
4. Écrit les fichiers de migration/DDL dans le projet cible, dans le style
   déjà en place.
5. Log l'entrée `Infra` si le chemin des migrations n'y figure pas encore.

**Sortie :**
```
## Choix base de données
[Décision utilisée ou nouvellement enregistrée]

## Structures créées
- `<path>` — <entité>

## Suite
Pipeline de structuration des données terminé.
```

## 4. Registre dans `using-simflow`

Les trois skills sont ajoutés à la table de `skills/using-simflow/SKILL.md`
et à la table de triggers auto, même format que les entrées existantes
(`interview`, `redaction`, `relecture`, `contestation`).

## Hors scope (v1)

- Modification de `hosa-challenger` pour vérifier la cohérence des
  annotations d'origine — reste un audit CDC pur, pas un audit de
  structure de données.
- Nouveau type OKF pour la structure de données elle-même — elle vit dans
  le code et la documentation du projet cible, pas dans `hosa/kb/`.
- Synchronisation automatique si le schéma du projet cible dérive de la KB
  après coup (pas de detection de drift).
- Multi-projet simultané (une seule entrée `Infra` "projet cible" à la
  fois, cohérent avec le principe mono-projet/local de Hosa).
