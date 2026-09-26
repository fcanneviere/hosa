# Hosa — QA de sprint (tests techniques + recette métier, garant de l'outillage)

**Date:** 2026-09-26
**Statut:** approuvé pour implémentation

## Contexte

`sprint` (`docs/superpowers/specs/2026-09-25-hosa-sprint-design.md`) compose
des sprints à partir du Product Backlog, en garantissant que chaque ticket
dispatché a une note technique, un placement architecture et un placement
interface réels. Une fois un sprint composé puis implémenté, rien ne
garantit aujourd'hui que ses tickets ont été testés techniquement, ni
qu'ils ont été validés du point de vue des personas qu'ils servent — seul
`simflow-tester` (test de code, à la demande, sans lien avec un sprint) et
`hosa-key-user` (recette, un ticket/persona à la fois, à la demande) offrent
des morceaux de cette garantie, jamais à l'échelle d'un sprint entier.

Cette itération ajoute un agent — `hosa-qa-lead` — et deux nouvelles étapes,
`qa-plan` et `qa`, en aval de `sprint`. Elles ne remplacent aucun agent
existant : `hosa-qa-lead` orchestre `simflow-tester` et `hosa-key-user` à
l'échelle du sprint, et prend en plus la responsabilité, propre à lui, de
l'outillage de test (fiabilité, vitesse d'exécution) — une responsabilité
qu'aucun agent ne porte aujourd'hui.

## Portée : le projet géré, pas Hosa lui-même

Même règle que le reste du pipeline : `simflow-tester` s'exécute contre le
projet *externe* que Hosa pilote (chemin lu depuis l'entrée `Infra`), jamais
contre `hosa/app` ou `hosa/kb`. `hosa/kb/` reste la source d'enregistrement
des plans de test et des résultats de recette.

## Positionnement (follow-on, pas une étape du pipeline de structuration)

```
... → backlog → sprint → qa-plan → (implémentation) → qa
```

Même logique de nommage que `sprint` : `qa-plan`/`qa` ne font pas partie du
"pipeline de structuration des données", ce sont les étapes de livraison qui
l'exploitent, une fois un sprint composé puis codé. Invocables seules ;
`sprint` propose `qa-plan` sans l'imposer, `qa-plan` propose `qa` sans
l'imposer — même principe que le reste du pipeline.

## Réutilisation du concept OKF `Test Plan`

Pas de nouveau concept OKF. `kb/test/` (déjà décrit dans `kb/index.md` comme
"Plans de test", pas seulement des recettes) accueille deux natures de
fichiers, distinguées par `tags` :

- `tags: [recette]` — déjà écrit par `hosa-key-user` via `recette`, un
  fichier par session `<slug-target>-<slug-persona>.md`. Inchangé.
- `tags: [technique]` — nouveau, écrit par `hosa-qa-lead` en mode
  Planification, un fichier par ticket `<slug-ticket>-technique.md`.

Aucune modification au concept `Ticket` ni à son frontmatter : `qa-plan`/`qa`
lisent le ticket (story, persona lié) mais n'y écrivent rien — le plan de
test technique et ses résultats vivent entièrement dans `kb/test/`, retrouvés
par nom de fichier (`<slug-ticket>-technique.md`), pas par une section sur le
ticket lui-même.

## Agent `hosa-qa-lead`

`agents/qa-lead.md`, frontmatter :
```yaml
name: hosa-qa-lead
model: claude-opus-4-8
memory: project
```

Rôle : garant qualité du projet géré par Hosa. N'implémente rien et ne
priorise pas le backlog — mais rien ne sort d'un sprint sans avoir été
testé techniquement et validé métier. Trois modes d'entrée, un seul agent
(même principe que `hosa-key-user`, qui a déjà plusieurs modes).

### Input

Un des trois modes ci-dessous. Si le mode n'est pas clair depuis la
requête, demande plutôt que de deviner.

### Mode 1 — Planification (depuis `qa-plan`)

Un ticket à préparer pour les tests.

1. Lit le ticket (`kb/tickets/<slug>.md`) : sa story, le persona lié
   ("Lié à : [persona](...)"), et sa section `## Note technique (senior
   dev)` déjà écrite par `backlog`.
2. Lit `kb/stack/` (`Stack Decision`) pour connaître le cadre technique déjà
   fixé — c'est la base "avec le senior dev" : les décisions déjà tenues par
   `hosa-senior-dev`, pas une nouvelle consultation en direct. Si la note
   technique du ticket ou les `Stack Decision` manquent des éléments
   nécessaires pour définir un cas de test précis, le dit et demande à
   l'utilisateur plutôt que d'inventer un détail technique sans base.
3. Définit les cas de test techniques à couvrir : chemin nominal, cas
   d'erreur, cas limites — dans les mêmes termes que `simflow-tester`
   emploie déjà (Step 3 de `agents/tester.md`), pour qu'il puisse les
   reprendre tels quels à l'exécution.
4. Identifie la recette requise : le(s) persona(s) que ce ticket sert,
   depuis le lien déjà présent dans sa story. Si la story ne lie aucun
   persona, le dit — ne devine pas lequel valider.
5. Écrit `hosa/kb/test/<slug-ticket>-technique.md` :

```markdown
---
type: Test Plan
title: Tests techniques — <titre du ticket>
description: <une ligne : ce qui est couvert>
tags: [technique]
status: stable
generated: { by: hosa-qa-lead/1.0, at: <ISO8601> }
---
## Cas de test
- <cas de test technique, dans les termes de simflow-tester>

## Recette requise
- [<persona>](../personnas/<slug>.md)
[Si aucun persona lié : "Aucune — ticket sans persona identifié dans sa story."]

Lié à : [ticket](../tickets/<slug-ticket>.md)
```

6. Log dans `kb/test/log.md` (créé si absent) — OKF §9.

### Mode 2 — Exécution (depuis `qa`)

Un ticket déjà préparé (`kb/test/<slug-ticket>-technique.md` existe) à
exécuter.

1. Dispatch `simflow-tester` avec les `## Cas de test` du plan comme brief,
   la liste des fichiers récemment modifiés pour ce ticket, et le chemin du
   projet géré. `simflow-tester` exécute la suite existante et écrit les
   tests manquants pour ces cas — même contrat qu'aujourd'hui.
2. Ajoute une section `## Résultats techniques` au fichier `Test Plan` de
   l'étape 1, avec ce que `simflow-tester` a rapporté (passés/échoués,
   nature de chaque échec).
3. Pour chaque persona listée dans `## Recette requise` : dispatch
   `hosa-key-user` en mode recette (même contrat que la requête envoyée par
   le skill `recette` aujourd'hui — rien de nouveau côté `hosa-key-user`),
   avec le ticket comme cible. Écrit le résultat en `hosa/kb/test/<slug-
   ticket>-<slug-persona>.md`, exactement au format déjà défini par
   `recette` (Step 3).
4. Log chaque fichier touché dans `kb/test/log.md` (et `kb/personnas/log.md`
   si un persona a été enrichi) — OKF §9.

### Mode 3 — Outillage (invocable directement, à tout moment)

Une demande d'amélioration de l'outillage de test ("optimise les tests",
"les tests sont trop lents", "les tests sont instables"), ou déclenchée en
fin de Mode 2 pour tout le sprint.

1. Relit sa propre mémoire projet (facteurs de lenteur/instabilité déjà
   observés lors de runs précédents de Mode 2) et les rapports
   `simflow-tester` de la session en cours.
2. Si un problème récurrent ressort (le même test signalé instable ou lent
   sur au moins deux runs), propose une optimisation concrète — isoler le
   test instable, ajuster une configuration d'exécution, paralléliser une
   suite lente — avec la justification.
3. N'applique jamais seul : présente la proposition, applique uniquement si
   l'utilisateur confirme. Si rien de récurrent ne ressort, le dit ("rien à
   signaler sur l'outillage") plutôt que de proposer un changement sans
   base.

### Output

```
## Plan de test (Mode 1)
- `kb/test/<slug-ticket>-technique.md` — [nombre de cas de test]
- Recette requise : [personas], ou "Aucune"

## Résultats (Mode 2)
### Tests techniques
- Passés : X / Y — [détail des échecs, si présents]
### Recette métier
- <persona> — Réussi / Échoué / Partiel

## Outillage (Mode 3)
[Proposition et justification, ou "Rien à signaler"]

## Suite recommandée
[simflow:debug pour un échec technique / hosa-product-owner pour un
Échoué-Partiel de recette / rien si tout est propre]

## Open Questions
[Si rien : "None"]
```

### No Commits

Ne commit jamais — même règle que tous les agents Hosa.

### Project Memory

Sauvegarde : les tests signalés instables/lents par `simflow-tester` à
travers plusieurs sessions, pour détecter la récurrence en Mode 3 ; les
optimisations d'outillage déjà proposées et leur issue (acceptée/refusée),
pour ne pas representer la même proposition refusée. Ne sauvegarde pas : le
contenu d'un plan de test ou d'un résultat de recette déjà écrit —
relisible depuis `kb/test/`.

## Skill `skills/qa-plan/SKILL.md`

**Trigger manuel :** `/qa-plan <slug-sprint>`. **Auto :** immédiatement
après `sprint`, ou "prépare les tests du sprint", "planifie les tests
techniques du sprint".

**Flow :**
```
Lit kb/sprints/<slug>.md pour sa liste de tickets
        ↓
Pour chaque ticket sans kb/test/<slug-ticket>-technique.md existant :
dispatch hosa-qa-lead (Mode 1)
        ↓
Ticket déjà préparé (fichier existe) → passe au suivant, ne
re-génère pas
        ↓
Rapporte les plans écrits et les personas identifiés pour recette
        ↓
Propose de lancer qa une fois le sprint implémenté
```

**Sortie :** un plan par ticket (voir sortie de l'agent, Mode 1), puis :
```
## Suite
Je lance `qa` une fois ce sprint implémenté ?
```

**No Commits** : ne commit jamais.

## Skill `skills/qa/SKILL.md`

**Trigger manuel :** `/qa <slug-sprint>`. **Auto :** "exécute la QA du
sprint", "teste le sprint", "fais la recette du sprint".

**Précondition :** chaque ticket du sprint a un
`kb/test/<slug-ticket>-technique.md`. Si un ticket n'en a pas, le dit et
propose de lancer `qa-plan` d'abord plutôt que d'exécuter des tests sans
plan.

**Flow :**
```
Lit kb/sprints/<slug>.md pour sa liste de tickets
        ↓
Vérifie que chaque ticket a un plan de test technique
        ↓ manquant
Propose de lancer qa-plan d'abord
        ↓ tous présents
Pour chaque ticket : dispatch hosa-qa-lead (Mode 2)
        ↓
Échecs techniques trouvés → classe (bug d'implémentation vs
infrastructure de test), même logique que le skill test
        ↓
Recette Échoué/Partiel → route vers hosa-product-owner
        ↓
Fin de sprint : dispatch hosa-qa-lead (Mode 3) une fois, sur
l'ensemble des runs de ce sprint
        ↓
Rapporte le verdict global du sprint
```

**Sortie :**
```
## QA du sprint <slug>
- <ticket> — technique : X/Y passés — recette : Réussi/Échoué/Partiel

## Échecs techniques
- <ticket> — [détail] → suggéré : simflow:debug

## Recette à corriger
- <ticket>/<persona> — [ce qui a échoué] → suggéré : hosa-product-owner

## Outillage
[Proposition et justification, ou "Rien à signaler"]

## Suite
[Si tout est propre : "Sprint validé."]
[Sinon : liste des actions suggérées ci-dessus]
```

**No Commits** : ne commit jamais.

## Modification à `sprint`

Le `## Suite` actuel se termine par "Je lance un autre sprint pour le reste
du backlog, ou on s'arrête là ?". Une ligne est ajoutée : "Je lance
`qa-plan` pour préparer les tests de ce sprint ?"

## Registre dans `using-simflow` et `agents/README.md`

`qa-plan` et `qa` sont ajoutés à la table des skills et à la table de
triggers auto de `skills/using-simflow/SKILL.md`, décrits comme des étapes
de livraison en aval de `sprint` (même formulation que `sprint` l'est déjà
vis-à-vis de `backlog`). `hosa-qa-lead` est ajouté à la table "Hosa agents"
de `agents/README.md`.

## Hors scope (v1)

- Modification de l'état (`state`) d'un `Ticket` par `qa`/`hosa-qa-lead` —
  la propriété du `state` reste exclusivement à `hosa-product-owner` (Step 5
  de son rôle) ; `qa` rapporte et suggère, il ne change jamais un ticket
  `doing`/`done`/`blocked` lui-même.
- Nouvel état `Sprint` reflétant le résultat de la QA (ex. `qa-passed`) — le
  verdict vit dans `kb/test/`, pas dans le frontmatter du `Sprint` ; pas de
  champ ajouté en v1.
- Ré-exécution automatique après correction (boucle fermée) — `qa` produit
  un rapport et des suggestions ; relancer `qa` sur le même sprint après
  correction reste une action manuelle de l'utilisateur.
- Application automatique des optimisations d'outillage proposées en Mode
  3 — toujours soumise à confirmation, jamais appliquée seule.
- Détection de drift si le plan de test technique change après coup — même
  principe que le reste du pipeline, pas de re-génération automatique.
