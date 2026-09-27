# Hosa — Agent git/GitHub dédié au cycle de vie des sprints

**Date:** 2026-09-26
**Statut:** approuvé pour implémentation

## Contexte

Aujourd'hui, rien dans Hosa ne gère de branche ni de worktree.
`build`/`iterate`/`test`/`debug` committent chacun directement sur
la branche courante, quelle qu'elle soit, au moment de leur étape finale.
Le concept `Sprint` (`kb/sprints/`) existe déjà (`hosa-sprint-planner`,
skill `sprint`) avec un cycle `planned → active → done`, mais rien ne fait
vivre concrètement ce cycle côté dépôt : aucune branche n'est ouverte
quand un sprint démarre, aucune fusion n'a lieu quand il se termine.

Cette itération ajoute `hosa-git`, agent dédié à la gestion du dépôt git du
projet *géré* pour la durée d'un sprint : il ouvre une branche/worktree
dédiée quand un sprint démarre, et la fusionne dans la branche de base une
fois que chaque ticket du sprint a une QA verte enregistrée. Il applique
par ailleurs, pour toute opération git qu'on lui demande, les mêmes règles
de prudence déjà en vigueur ailleurs dans Hosa.

## Portée : le projet géré, pas Hosa lui-même

Même règle que `hosa-infra`/`hosa-documentation` : `hosa-git` opère
exclusivement sur le dépôt git du projet *externe* que Hosa pilote (chemin
racine lu depuis `kb/infra/`), jamais sur `C:\dev\hosa` lui-même. Sa
traçabilité (quel sprint a quelle branche, quand fusionné) vit dans
`kb/sprints/`, comme le reste du cycle de vie du `Sprint`.

**GitHub reste hors scope v1** au sens API/PR : pas de push vers un
remote, pas de Pull Request automatisée. La fusion de fin de sprint est
toujours locale. "GitHub" dans le nom de l'agent couvre l'usage futur
(voir Hors scope) et le vocabulaire — pas un mécanisme livré ici.

## Positionnement : agent transversal, dispatché depuis `sprint` et `qa`

`hosa-git` n'est pas une étape numérotée d'un pipeline — c'est un agent
transversal au même titre que `hosa-documentation`. Il a son propre skill
(`git`) pour un déclenchement direct, et deux points de dispatch à chaud
existants lui proposent la suite naturelle du travail :

| Déclencheur | Moment | Mode appelé |
|---|---|---|
| Skill `sprint`, fin de Step 6 (Suite) | Un `Sprint` vient d'être écrit (`state: planned`) | Mode 1 — Démarrage |
| Skill `qa`, fin de Step 5 (Suite), quand le verdict est "Sprint validé." | Chaque ticket du sprint a une QA verte | Mode 2 — Fusion |
| Skill `git` (`/git`) directement | L'utilisateur le demande explicitement | Mode 1, 2 ou 3 selon la requête |

Chaque point de dispatch propose l'enchaînement — il ne l'impose jamais :
même discipline que le reste de Hosa ("Trust the user").

## Extension du concept `Sprint`

`kb/sprints/<slug>.md` gagne deux champs, écrits uniquement par
`hosa-git` :

```yaml
branch: sprint/<slug>       # ajouté au démarrage (Mode 1)
worktree: <chemin absolu>   # ajouté au démarrage (Mode 1), retiré à la fusion (Mode 2)
```

`state` continue de porter `planned | active | done` — `hosa-git` est
désormais ce qui fait passer `active` puis `done`, à la place d'un
changement manuel.

## Agent `hosa-git`

`agents/git.md`, frontmatter :
```yaml
name: hosa-git
model: claude-opus-4-8
memory: project
```

### Input

Une des trois requêtes ci-dessous, portant toujours le slug d'un sprint.
Si le mode n'est pas clair, demande plutôt que de deviner.

### Knowledge Base

| Bundle | Type | Usage |
|---|---|---|
| `kb/sprints/` | `Sprint` | Lit l'état/tickets, écrit `state`/`branch`/`worktree` |
| `kb/tickets/` | `Ticket` | Liste des tickets du sprint, pour le contrôle QA |
| `kb/test/` | `Test Plan` | `## Résultats techniques` et recette de chaque ticket — porte de qualité avant fusion |
| `kb/infra/` | `Infra` | Racine du projet géré (dépôt git ciblé) |

**Logging :** ajoute une entrée à `kb/sprints/log.md` à chaque changement
d'état/branche — chronologique, plus récent en premier, OKF §9.

### Bonnes pratiques appliquées dans les trois modes

- Jamais de commit direct sur la branche de base pendant qu'un sprint est
  `active` — le sprint vit sur sa propre branche jusqu'à sa fusion.
- Avant tout commit qu'il fait lui-même (uniquement le commit de fusion en
  Mode 2, et tout commit ad hoc explicitement demandé en Mode 3) : vérifie
  `git config user.name`/`user.email`, jamais de `Co-Authored-By`, jamais
  d'auteur additionnel — règle core Hosa appliquée littéralement.
- Jamais de `force-push`, `git reset --hard`, `git clean -f` sans la
  confirmation explicite du mot exact demandé par l'utilisateur — même
  garde-fou que `superpowers:finishing-a-development-branch`.
- Jamais de fusion si les tests échouent sur le résultat fusionné, ou si un
  ticket du sprint n'a pas sa QA au vert (Mode 2, garde ci-dessous).

### Mode 1 — Démarrage de sprint

1. Lit `kb/sprints/<slug>.md`. Si `state` n'est pas `planned`, le dit et
   stoppe (pas de double démarrage) — sauf demande explicite de
   réattachement à un worktree déjà `active`.
2. Lit `kb/infra/` pour la racine du projet géré. Absent → demande.
3. Invoque le skill `superpowers:using-git-worktrees` avec le nom de
   branche `sprint/<slug>`, dans le dépôt du projet géré — il gère le
   placement du worktree (`.worktrees/`), la création de la branche, le
   setup et les tests de baseline. `hosa-git` ne réimplémente pas cette
   mécanique. La demande explicite de démarrage du sprint vaut préférence
   déclarée : son Step 0 (consentement) n'a pas besoin de reposer la
   question.
4. Écrit `state: active`, `branch: sprint/<slug>`, `worktree: <chemin>`
   dans `kb/sprints/<slug>.md`.
5. Log `kb/sprints/log.md`.
6. Rapporte le chemin du worktree et la branche — le travail des tickets
   (via `build`/`iterate`/`test`/`debug`) doit désormais se faire
   dedans.

### Mode 2 — Fusion de fin de sprint

1. Lit `kb/sprints/<slug>.md`. Si `state` n'est pas `active`, ou si
   `branch`/`worktree` sont absents, le dit — rien à fusionner — et stoppe.
2. **Porte QA** : pour chaque ticket listé dans le sprint, lit
   `kb/test/<slug-ticket>-technique.md` (`## Résultats techniques` doit
   être entièrement passé) et son/ses fichier(s) de recette (`Réussi` ou
   "Non applicable"). Un ticket manquant sa QA, ou avec un résultat
   `Échoué`/`Partiel`, bloque la fusion : liste les tickets bloquants et ce
   qu'il leur manque, propose `qa`/`debug`/`hosa-product-owner`
   selon le cas, et stoppe — jamais de fusion partielle.
3. Tout vert → invoque `superpowers:finishing-a-development-branch`, forcé
   sur l'option "Merge locally" (pas de menu proposé — le choix
   local-only a été acté pour ce projet) : tests de la branche fusionnée,
   fusion dans la base branch, nettoyage du worktree, suppression de la
   branche.
4. Échec (tests rouges sur le résultat fusionné, conflit) → stoppe,
   rapporte, laisse worktree/branche en l'état (`kb/sprints` reste
   `active`) — comportement natif du skill réutilisé, rien à committer.
5. Succès → `kb/sprints/<slug>.md` : `state: done`, retire `branch` et
   `worktree` (le sprint n'a plus d'espace de travail actif). Log
   `kb/sprints/log.md`.
6. Rapporte le résultat.

### Mode 3 — Opérations git ad hoc

Requêtes ponctuelles hors cycle de sprint (statut, nettoyage d'un
worktree orphelin, annulation d'un commit...) : traitées directement, avec
les mêmes règles de prudence ci-dessus. Pas d'écriture KB pour ce mode
sauf si l'opération touche un sprint identifié (auquel cas Mode 1/2
s'applique à la place).

### No Commits (exception assumée)

Seul agent Hosa qui commit — uniquement le commit de fusion en Mode 2, et
un commit ad hoc en Mode 3 si explicitement demandé. Jamais en Mode 1.
Toujours sous l'identité git de l'utilisateur, jamais de co-auteur —
même règle core Hosa que partout ailleurs, appliquée ici plutôt que
déférée à l'utilisateur.

### Output Format

```
## Sprint <slug> démarré (Mode 1)
- Branche : sprint/<slug>
- Worktree : <chemin>

## Sprint <slug> fusionné (Mode 2)
- Résultat : fusionné dans <base-branch> / bloqué
- Tickets bloquants (si bloqué) : <ticket> — [ce qui manque]
- [Si fusionné : "Worktree nettoyé, branche supprimée."]

## Opération (Mode 3)
[Résultat de la requête ad hoc]

## Suite
[Selon le mode : rien, ou action suggérée]
```

### Project Memory

Sauvegarde : le chemin racine du projet géré (source de vérité :
`kb/infra/`, juste pour éviter de le redemander en session), la branche de
base du dépôt géré une fois confirmée. Ne sauvegarde pas : l'état courant
d'un sprint — relisible depuis `kb/sprints/`.

## Skill `skills/git/SKILL.md`

**Trigger manuel :** `/git demarre <slug>`, `/git termine <slug>`. **Auto :**
"démarre le sprint X", "commence le sprint X" → Mode 1 ; "termine le
sprint X", "fusionne le sprint X", "merge le sprint X" → Mode 2.

**Flow :**
```
Lit kb/sprints/<slug>.md
        ↓
Détermine le mode (démarrage / fusion / ad hoc) depuis la requête
        ↓
Dispatch hosa-git dans ce mode
        ↓
Rapporte le résultat (branche/worktree ouverts, ou fusion/blocage)
```

**Commits :** ce skill dispatche le seul agent Hosa habilité à committer
(`hosa-git`, Mode 2/3 uniquement) — toujours sous l'identité git de
l'utilisateur, jamais de co-auteur.

Companion transversal usable anytime, comme `qualite`/`documentation` —
mais avec deux points de dispatch à chaud dédiés (`sprint`, `qa`), à la
différence de ces deux-là qui n'en ont pas.

## Modifications aux skills existants

### `sprint`

Step 6 (Suite), ajoute une ligne d'enchaînement : après avoir composé le
sprint, propose "Je démarre le sprint maintenant (ouvre la branche/worktree
dédiée) ?" → dispatch `git` Mode 1 si accepté.

### `qa`

Step 5 (Suite), quand le verdict est "Sprint validé.", ajoute : "Je fusionne
le sprint maintenant ?" → dispatch `git` Mode 2 si accepté. Si le verdict
n'est pas clean, ne propose rien — la porte QA de `hosa-git` referait de
toute façon le même contrôle et bloquerait.

## Registre dans `using-hosa` et `agents/README.md`

- `hosa-git` ajouté à la table "Hosa agents" de `agents/README.md`.
- `git` ajouté à la table des skills de `skills/using-hosa/SKILL.md`,
  décrit comme le skill qui ouvre/fusionne la branche de sprint dédiée du
  projet géré, et à la table des triggers auto.

## Hors scope (v1)

- Push vers un remote / création de Pull Request GitHub — fusion toujours
  locale. Pourrait devenir un Mode 4 plus tard si demandé, sans
  restructuration (même agent, même garde QA).
- Prise en main des commits de `build`/`iterate`/`test`/`debug` —
  ces skills continuent de committer eux-mêmes, simplement désormais dans
  le worktree du sprint actif plutôt que sur une branche arbitraire.
- Résolution de conflits entre sprints concurrents au-delà de ce que git
  worktree empêche déjà nativement (deux sprints touchant les mêmes
  tickets est un problème de process/KB, pas un problème git).
- Règles de protection de branche, intégration CI.
- Rebase/squash d'historique — fusion simple uniquement (`git merge`),
  même choix que `finishing-a-development-branch` Option 1.
