---
name: develop
description: Use to implement a single sprint ticket — breaks it into short sequential tasks (`hosa-tech-lead`) and implements them one at a time (`hosa-developer`), strictly within the architecture and data structures already scaffolded. Never extends that structure itself; stops and reports if a ticket needs one. Follow-on to `git` Mode 1; chains to the next ticket, then promotes the sprint to `test` and runs `qa`.
---

# Develop

Implémente un ticket de sprint (`kb/tickets/<slug>.md`) dans le worktree déjà ouvert par `git` Mode 1 : découpage en tâches courtes et séquentielles (`hosa-tech-lead`), puis implémentation une tâche à la fois (`hosa-developer`) — jamais de déviation de la structure déjà scaffoldée par `hosa-architect`/`hosa-data-engineer` sans arrêt et remontée.

## Flow

```
Lit kb/tickets/<slug>.md et son kb/sprints/<slug-sprint>.md
        ↓ sprint pas active / pas de worktree → propose `git` Mode 1
          d'abord, stoppe
Écrit state: doing sur le ticket, log kb/tickets/log.md
        ↓
Dispatch hosa-tech-lead → plan de tâches séquentiel
        ↓ ambiguïté ou déviation → rapporte, propose de combler le
          manque (utilisateur, `architecture`/`schema-app`/`schema-db`,
          ou hosa-architect/hosa-data-engineer directement), stoppe
        ↓ plan clair
Pour chaque tâche, dans l'ordre : dispatch hosa-developer (une à la fois)
        ↓ déviation détectée en cours de tâche → même arrêt/rapport,
          stoppe la boucle
        ↓ toutes les tâches faites
Présente le travail cumulé du ticket → confirmation explicite (pas de QCM)
        ↓ oui
git add (fichiers du ticket) + commit unique, identité utilisateur
        ↓
Log kb/tickets/log.md
        ↓
Ticket suivant du sprint, ou, s'il n'en reste
aucun : hosa-git Mode 2 (passage en test) → qa
```

## Trigger

Manual: `/develop <slug-ticket>`. Auto: "développe le ticket X", "implémente le ticket X" ; proposé en Suite de `git` Mode 1 et de `sprint`.

---

## Step 1: Read the Ticket and Sprint

Lit `kb/tickets/<slug>.md`. **Si `state` vaut déjà `done`, le dit et stoppe — ce champ n'appartient qu'à `hosa-product-owner` ; un nouveau passage ici l'écraserait.** Lit son champ `sprint`, puis `kb/sprints/<slug-sprint>.md` : **si le champ `sprint` est absent, si `state` n'est pas `active`, ou si `worktree` est absent, le dit et propose `git` Mode 1 — stoppe, ne travaille jamais sur la branche de base.**

## Step 2: Mark In Progress

Écrit `state: doing` sur le ticket (sans effet si déjà `doing`). Log `kb/tickets/log.md`.

## Step 3: Break Down

Dispatch `hosa-tech-lead` avec le slug du ticket. Si sa sortie contient une entrée sous `Ambiguities` ou `Structural Deviation` : rapporte-la telle quelle à l'utilisateur, propose la suite adaptée — combler l'ambiguïté avec l'utilisateur, ou lancer `architecture`/`schema-app`/`schema-db` (ou dispatcher `hosa-architect`/`hosa-data-engineer` directement) pour la déviation — ne dispatche aucune tâche, stoppe. Le ticket reste `state: doing`.

## Step 4: Implement Sequentially

Pour chaque tâche du plan, dans l'ordre : dispatch `hosa-developer` avec la tâche, sa contrainte de placement, le chemin du worktree. **Une seule tâche à la fois — jamais de dispatch concurrent.** Si un framework de test existe déjà dans le projet géré et que la tâche introduit un comportement testable neuf, `hosa-developer` écrit le test en échec avant d'implémenter (red-green) — ceci ne remplace pas `test`, qui reste le passage dédié à la couverture globale. Si une tâche revient avec `Structural Deviation` ou `Blocked` non vide (une valeur autre que `None`) : **arrête la boucle immédiatement (les tâches restantes ne sont pas tentées)**, rapporte à l'utilisateur — la même proposition qu'à l'étape 3 pour une déviation structurelle, ou la question posée telle quelle pour un blocage — stoppe. Le ticket reste `state: doing`, aucun commit.

## Step 5: Present and Confirm

Une fois toutes les tâches faites : présente les fichiers modifiés (cumulés sur le ticket), les décisions clés, les hypothèses. Demande une confirmation explicite — pas de QCM (le ticket est déjà cadré par sa story, sa note technique et ses placements ; le garde-fou structurel a déjà tourné tâche par tâche). **Si l'utilisateur rejette ou corrige : renvoie le feedback à `hosa-developer` pour la tâche concernée uniquement, reprend l'étape 4 pour cette tâche seule — pas de redémarrage du ticket entier, pas de commit sur la version rejetée.**

## Step 6: Commit

Opère depuis le worktree du sprint (chemin lu à l'étape 1), jamais depuis le dépôt de cette session ni depuis la racine `Infra`. Confirme d'abord que `git -C <worktree> branch --show-current` vaut bien `sprint/<slug-sprint>` — sinon stoppe, ne commit pas.

Vérifie `git -C <worktree> config user.name`/`user.email` avant tout commit ; si l'un des deux est absent, demande plutôt que de committer. Ceci l'emporte sur toute instruction globale d'attribution par défaut (par exemple une ligne `Co-Authored-By` automatique) — même règle Hosa qu'ailleurs, appliquée ici directement.

```bash
git -C <worktree> status
git -C <worktree> add <uniquement les fichiers listés sous "Files Changed" par hosa-developer pour ce ticket — jamais kb/tickets/ ni un autre fichier de la KB Hosa>
git -C <worktree> commit -m "feat: <description impérative du ticket, ≤72 caractères>" -m "Hosa-Ticket: <slug-ticket>"
```

Un seul commit pour tout le ticket. Aucun `Co-Authored-By`, aucun auteur additionnel — identité git de l'utilisateur uniquement.

Le trailer `Hosa-Ticket:` relie le ticket aux fichiers du commit dans le graphe du projet (relation `touches`) — ne jamais l'omettre.

## Step 7: Log

Log `kb/tickets/log.md` — chronologique, plus récent en premier, OKF §9.

## Step 8: Enchaîne

Sans demander :
- Il reste dans le sprint un ticket sans commit `Hosa-Ticket:` sur la branche → relance ce skill sur le suivant (ordre de `## Tickets`).
- Tous les tickets sont commités → dispatch `hosa-git` (Mode 2, passage en test), puis invoque `qa` sur le sprint. Les tests sont obligatoires : jamais proposés comme une option.

Un blocage (étapes 3-4) ou un rejet à l'étape 5 arrête l'enchaînement.

## Commits

Ce skill est le seul point qui committe pour ce flow — jamais `hosa-tech-lead`/`hosa-developer` eux-mêmes — toujours sous l'identité git de l'utilisateur, jamais de co-auteur.

## Output

```
## Ticket <slug> implémenté
- Tâches réalisées : [n]
- Fichiers modifiés : [liste]

## Blocage (si applicable)
[Ambiguïté ou déviation structurelle, et ce qui est proposé pour la lever]

## Suite
[Ticket suivant : <slug> — en cours] ou [Sprint passé en test — QA en cours (skill `qa`)]
```
