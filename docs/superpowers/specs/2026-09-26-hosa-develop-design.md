# Hosa — Implémentation des tickets de sprint (`hosa-tech-lead` / `hosa-developer`)

**Date:** 2026-09-26
**Statut:** approuvé pour implémentation

## Contexte

Une fois un sprint composé (`sprint`) et sa branche/worktree ouverte
(`git` Mode 1), rien de spécifique à Hosa n'implémente encore les tickets.
La spec `hosa-git` renvoie ce travail vers `simflow:build`/`iterate`/
`test`/`debug` — des skills génériques qui ignorent le placement
architecture déjà décidé par `hosa-architect` et les structures de données
déjà écrites par `hosa-data-engineer`. Un ticket peut donc être implémenté
en dehors de la structure que ces deux agents ont fixée, sans aucune garde.

Cette itération ajoute deux agents Hosa dédiés à l'implémentation d'un
ticket de sprint, dans le cadre strict de la structure déjà scaffoldée :
`hosa-tech-lead` (découpe un ticket en tâches courtes et séquentielles) et
`hosa-developer` (implémente une tâche à la fois, en session courte). Ni
l'un ni l'autre ne peut faire évoluer l'architecture ou les structures de
données de sa propre initiative — toute évolution nécessaire est un arrêt
et une remontée, jamais une décision prise sur place.

## Portée : le projet géré, pas Hosa lui-même

Même règle que les autres agents Hosa : `hosa-tech-lead` et
`hosa-developer` opèrent exclusivement sur le dépôt/code du projet
*externe* que Hosa pilote (chemin racine lu depuis `kb/infra/`, ou le
worktree du sprint actif s'il existe), jamais sur `hosa/app` ou `hosa/kb`.

## Positionnement dans le pipeline

`develop` s'insère entre l'ouverture du worktree de sprint et la QA :

```
backlog → sprint → git (Mode 1, ouvre le worktree)
    → develop (par ticket) → qa-plan → qa → git (Mode 2, fusionne)
```

Ce n'est pas une étape numérotée du pipeline de structuration des données
(`stack` → ... → `backlog`) — c'est la suite naturelle, à la granularité du
ticket, une fois qu'un sprint est actif.

## Extension du concept `Ticket`

Aucun nouveau champ. `develop` utilise l'état déjà prévu par
`hosa-product-owner` (`state: todo | doing | done | blocked`) :
il passe le ticket à `state: doing` en démarrant, et le laisse à `doing` à
la fin — c'est `hosa-product-owner` qui décide `done`/`blocked` à la
relecture (sa responsabilité "Deliverable validation", déjà écrite dans
`agents/product-owner.md`, jusqu'ici jamais câblée à un déclencheur).

## Agent `hosa-tech-lead`

`agents/tech-lead.md`, frontmatter :
```yaml
name: hosa-tech-lead
model: claude-opus-4-8
memory: project
```

Guarantor du découpage d'un ticket en tâches d'implémentation — sans
jamais décider lui-même d'étendre l'architecture ou les structures de
données déjà fixées par `hosa-architect`/`hosa-data-engineer`.

### Input

Le slug d'un ticket appartenant à un sprint dont le worktree est ouvert
(`state: active` dans `kb/sprints/<slug-sprint>.md`). Si le sprint n'est
pas `active` ou n'a pas de `worktree`, dit-le et stoppe plutôt que de
travailler sur la branche de base.

### Knowledge Base

| Bundle | Type | Usage |
|---|---|---|
| `kb/tickets/` | `Ticket` | Story, `Note technique (senior dev)`, `Placement architecture (architecte)`, `Placement interface (UX/UI)` |
| `kb/infra/` | `Infra` | Racine du projet géré, chemins de la doc d'architecture/données déjà écrite |
| `kb/sprints/` | `Sprint` | Confirme `state: active` et le chemin du `worktree` |

Ne lit ni n'écrit `kb/stack/`, `kb/cdc/` directement — ce que le ticket
porte déjà dans ses sections suffit ; toute lacune y est déjà signalée par
`backlog`/`sprint`.

**Logging :** aucun — `hosa-tech-lead` ne modifie pas la KB, il retourne un
plan à `develop`, qui logge.

### Process

1. Lit le ticket : story, `Note technique`, `Placement architecture`,
   `Placement interface`. L'une de ces sections tenant encore la ligne de
   repli de `backlog` ("pas encore évalué/déterminé") est un blocage — le
   dit et stoppe, ce ticket n'aurait pas dû passer la porte `sprint`.
2. Lit, dans le projet géré, le code/la documentation réelle pointée par
   le `Placement architecture` (via `Infra`) et les structures de données
   déjà écrites par `hosa-data-engineer` — la frontière réelle, pas
   seulement le texte du placement.
3. Découpe le ticket en tâches courtes, **strictement séquentielles** (pas
   de groupe parallèle) — une tâche par fichier/comportement, dans l'ordre
   d'exécution. Même règle de taille que `simflow-planner` : une tâche
   trop grosse (>5 fichiers à lire, plus d'un livrable) est scindée ; une
   tâche triviale (<5 lignes, une seule valeur de config) est fusionnée à
   la tâche voisine.
4. **Règle de halte (ambiguïté) :** une tâche qui forcerait `hosa-developer`
   à deviner un comportement non écrit dans le ticket → liste la question,
   stoppe, ne produit pas de plan partiel.
5. **Règle de déviation (structure) :** si le ticket, tel qu'écrit, ne
   rentre pas dans les modules/couches ou les entités/champs déjà
   scaffoldés sans les étendre → stoppe et signale la déviation (quoi
   manque, pourquoi ça dépasse la structure actuelle). Ne propose jamais
   lui-même l'extension — ce n'est pas son rôle.

### Output Format

```
## Ambiguïtés (bloquant)
[Si aucune : "Aucune"]
- [question] : [pourquoi ça bloque]

## Déviation structurelle (bloquant)
[Si aucune : "Aucune"]
- [ce que le ticket exige] : [en quoi ça dépasse l'architecture/les
  données déjà scaffoldées]

## Plan de tâches (séquentiel)
- [ ] [Nom de la tâche] — [description, fichiers concernés, contrainte de
  placement à respecter]
- [ ] [Nom de la tâche] — [description]

## Notes
[Conventions existantes à suivre, fichiers à lire en premier]
```

Si `Ambiguïtés` ou `Déviation structurelle` contient une entrée, le plan
de tâches est vide — `develop` s'arrête au rapport, ne dispatche aucune
tâche.

### Project Memory

Sauvegarde : les frontières de modules/entités déjà rencontrées pour ce
projet géré (pour ne pas relire tout le code à chaque ticket). Ne
sauvegarde pas : le plan d'un ticket déjà découpé — non réutilisable d'un
ticket à l'autre.

## Agent `hosa-developer`

`agents/developer.md`, frontmatter :
```yaml
name: hosa-developer
model: claude-sonnet-5
memory: project
```

Implémente une tâche à la fois, dans le cadre strict fixé par
`hosa-tech-lead` — même discipline que `simflow-implementer`, avec une
contrainte en plus : jamais d'extension de l'architecture ou des données
de sa propre initiative.

### Input

Une tâche unique du plan de `hosa-tech-lead` : description, fichiers à
lire, contrainte de placement (module/couche/entité autorisés), chemin du
worktree du sprint.

### Process

1. **Lit avant d'écrire.** Lit tous les fichiers pertinents pour cette
   tâche avant de modifier quoi que ce soit.
2. **Suit les conventions existantes** exactement — nommage, style,
   structure déjà en place dans le projet géré.
3. **Implémente exactement la tâche** — aucun refactor non demandé, aucune
   fonctionnalité non demandée.
4. **Reste dans le placement autorisé.** N'ajoute aucun module, couche,
   entité ou champ hors de ce que `hosa-architect`/`hosa-data-engineer` ont
   déjà scaffoldé. Si la tâche l'exige pour être correcte : n'improvise
   pas de contournement — s'arrête, rapporte la déviation exactement comme
   `hosa-tech-lead` (quoi manque, pourquoi).
5. **Pas de commentaires explicatifs** — uniquement si le pourquoi est non
   évident (contrainte cachée, contournement spécifique).
6. **Pas de faille de sécurité** — même discipline que `simflow-implementer`
   (injection, XSS, secrets en dur, etc.).

### No Commits

Ne commit jamais. `develop` committe une fois, à la fin du ticket.

### Output Format

```
## Tâche réalisée
[1-2 phrases]

## Fichiers modifiés
- `path` — [quoi et pourquoi]

## Déviation structurelle (si applicable)
[Si aucune : "Aucune"]
[ce qui manque à la structure actuelle pour réaliser la tâche]

## À surveiller
[Points d'intégration, hypothèses à valider — si aucun : "Aucun"]
```

### Project Memory

Sauvegarde : conventions de code découvertes pour ce projet géré,
contournements appliqués et pourquoi. Ne sauvegarde pas : la tâche
elle-même ni son résultat — relisible depuis le code.

## Skill `skills/develop/SKILL.md`

**Trigger manuel :** `/develop <slug-ticket>`. **Auto :** "développe le
ticket X", "implémente le ticket X" ; proposé en Suite de `git` Mode 1 et
de `sprint`.

**Flow :**
```
Lit kb/tickets/<slug>.md et son kb/sprints/<slug-sprint>.md
        ↓ sprint pas active / pas de worktree → propose `git` Mode 1
          d'abord, stoppe
Écrit state: doing sur le ticket, log kb/tickets/log.md
        ↓
Dispatch hosa-tech-lead → plan de tâches
        ↓ ambiguïté ou déviation → rapporte à l'utilisateur, propose
          architecture / schema-app / schema-db (ou dispatcher
          hosa-architect / hosa-data-engineer directement) ; stoppe,
          ticket reste state: doing
        ↓ plan clair
Pour chaque tâche, dans l'ordre : dispatch hosa-developer (une tâche par
dispatch — session courte)
        ↓ déviation détectée en cours de tâche → même arrêt/rapport,
          stoppe la boucle
        ↓ toutes les tâches faites
Présente le travail du ticket (fichiers modifiés, décisions clés,
hypothèses) → attend une confirmation explicite (pas de QCM)
        ↓ non / feedback → renvoie la correction à hosa-developer, reprend
        ↓ oui
git add (uniquement les fichiers touchés pour ce ticket)
git commit — identité git de l'utilisateur, jamais de co-auteur
        ↓
Log kb/tickets/log.md
        ↓
Suite : propose hosa-product-owner (validation → state: done/blocked)
et/ou qa-plan
```

### Step 1 — Read the Ticket and Sprint

Lit `kb/tickets/<slug>.md`. Lit son champ `sprint` puis
`kb/sprints/<slug-sprint>.md` : si absent, si `state` n'est pas `active`,
ou si `worktree` est absent, le dit et propose `git` Mode 1 — stoppe, ne
travaille jamais sur la branche de base.

### Step 2 — Mark In Progress

Écrit `state: doing` sur le ticket (idempotent si déjà `doing`). Log
`kb/tickets/log.md`.

### Step 3 — Break Down

Dispatch `hosa-tech-lead` avec le slug du ticket. Si `Ambiguïtés` ou
`Déviation structurelle` contient une entrée : rapporte telle quelle à
l'utilisateur, propose la suite adaptée (combler l'ambiguïté avec
l'utilisateur, ou lancer `architecture`/`schema-app`/`schema-db` /
dispatcher `hosa-architect`/`hosa-data-engineer` pour la déviation) — ne
dispatche aucune tâche, stoppe.

### Step 4 — Implement Sequentially

Pour chaque tâche du plan, dans l'ordre : dispatch `hosa-developer` avec
la tâche, ses contraintes de placement, le chemin du worktree. Une tâche à
la fois — jamais de dispatch concurrent, conformément à "une par une". Si
une tâche revient avec une `Déviation structurelle` non vide : arrête la
boucle immédiatement (les tâches restantes ne sont pas tentées), rapporte
la déviation à l'utilisateur avec la même proposition qu'à l'étape 3, et
stoppe. Le ticket reste `state: doing`, aucun commit n'est fait.

### Step 5 — Present and Confirm

Une fois toutes les tâches faites : présente les fichiers modifiés
(cumulés sur tout le ticket), les décisions clés, les hypothèses. Demande
une confirmation explicite — pas de QCM (le ticket est déjà cadré par sa
story, sa note technique et ses placements ; le garde-fou structurel a
déjà été appliqué tâche par tâche par `hosa-developer`).

Si l'utilisateur rejette ou donne un correctif : renvoie le feedback à
`hosa-developer` pour la tâche concernée, reprend au Step 4 pour cette
tâche seule.

### Step 6 — Commit

```bash
git status
git add <uniquement les fichiers modifiés pour ce ticket>
git commit -m "feat: <description impérative du ticket, ≤72 caractères>"
```

Un seul commit pour tout le ticket (toutes ses tâches regroupées). Aucun
`Co-Authored-By`, aucun auteur additionnel — identité git de l'utilisateur
uniquement, même règle core SimFlow qu'ailleurs.

### Step 7 — Log

Log `kb/tickets/log.md` — chronologique, plus récent en premier, OKF §9.

### Output Format

```
## Ticket <slug> implémenté
- Tâches réalisées : [n]
- Fichiers modifiés : [liste]

## Blocage (si applicable)
[Ambiguïté ou déviation structurelle, et ce qui est proposé pour la lever]

## Suite
Je lance la validation du ticket par hosa-product-owner (state: done) et/ou
qa-plan maintenant ?
```

## Modifications aux fichiers/skills existants

### `agents/git.md` / `docs/superpowers/specs/2026-09-26-hosa-git-design.md`

Mode 1, étape 6 : "le travail des tickets (via `simflow:build`/`iterate`/
`test`/`debug`)" est remplacé par "le travail des tickets (skill `develop`,
un ticket à la fois)".

### `skills/git/SKILL.md`

Mode 1 : rien à changer dans le flow lui-même — seule la phrase de
rapport de `hosa-git` change (voir ci-dessus), pas le skill `git`.

### `skills/sprint/SKILL.md`

Step 6 (Suite), ajoute une proposition : après avoir démarré le sprint (ou
à la place, si l'utilisateur ne veut pas encore ouvrir le worktree),
"Je lance `develop` sur le premier ticket du sprint ?"

### `agents/README.md` et `skills/using-simflow/SKILL.md`

- `hosa-tech-lead` et `hosa-developer` ajoutés à la table "Hosa agents".
- `develop` ajouté à la table des skills, décrit comme le skill qui
  implémente un ticket de sprint (découpage + implémentation) dans le
  cadre de l'architecture/données déjà scaffoldées ; ajouté à la table des
  triggers auto.

## Hors scope (v1)

- Dispatch parallèle de plusieurs tâches d'un même ticket — le découpage
  reste toujours séquentiel, conformément à la demande explicite ("une par
  une"). Pourrait devenir un mode "groupe parallèle" plus tard si demandé,
  sans restructuration (même agents, même garde de déviation).
- Dispatch parallèle de plusieurs tickets d'un même sprint — `develop`
  s'invoque un ticket à la fois ; enchaîner plusieurs tickets reste une
  suite de dispatches manuels ou proposés, pas un mode "sprint entier".
- Auto-résolution d'une déviation structurelle par `hosa-tech-lead`/
  `hosa-developer` — toujours un arrêt et une remontée utilisateur (option
  A), jamais un dispatch agent-à-agent vers `hosa-architect`/
  `hosa-data-engineer`.
- Écriture automatique de `state: done` par `develop` — reste la
  responsabilité exclusive de `hosa-product-owner`.
