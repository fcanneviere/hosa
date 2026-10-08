---
name: develop
description: "Use to implement one sprint ticket in the sprint worktree: tests first (`hosa-tester`), tasks (`hosa-tech-lead`), code (`hosa-developer`), one commit. Triggers: \"développe le ticket X\", \"implémente le ticket X\"."
---

# Develop

Implémente un ticket de sprint (`kb/tickets/<slug>.md`) dans le worktree déjà ouvert par `git` Mode 1 : découpage en tâches courtes et séquentielles (`hosa-tech-lead`), puis implémentation une tâche à la fois (`hosa-developer`) — jamais de déviation de la structure déjà scaffoldée par `hosa-architect`/`hosa-data-engineer` sans arrêt et remontée.

## Flow

```
Lit kb/tickets/<slug>.md et son kb/sprints/<slug-sprint>.md
        ↓ sprint pas active / pas de worktree → Q : je démarre le
          sprint maintenant (`git` Mode 1) ? oui → le démarre, puis
          reprend ce ticket ; non → stoppe
Écrit state: doing sur le ticket, log kb/tickets/log.md
        ↓
Dispatch hosa-tech-lead → plan de tâches séquentiel
        ↓ ambiguïté ou déviation → rapporte, propose de combler le
          manque (utilisateur, `architecture`/`schema-app`/`schema-db`,
          ou hosa-architect/hosa-data-engineer directement), stoppe
        ↓ plan clair
Tests d'abord : dispatch hosa-tester (Écrire d'abord) avec le
slug — un test automatisé par cas du plan, en échec
        ↓
Pour chaque tâche, dans l'ordre : dispatch hosa-developer (une à la fois)
jusqu'à ce que ces tests passent
        ↓ déviation détectée en cours de tâche → même arrêt/rapport,
          stoppe la boucle
        ↓ toutes les tâches faites
Présente le travail cumulé du ticket → confirmation explicite (pas de QCM)
        ↓ oui
git add (fichiers du ticket) + commit unique, identité utilisateur
        ↓
Log kb/tickets/log.md
        ↓
Suite : ticket suivant du sprint, ou `qa` quand tous sont faits
```

## Trigger

Manual: `/develop <slug-ticket>`. Auto: "développe le ticket X", "implémente le ticket X" ; proposé en Suite de `git` Mode 1 et de `sprint`.

---

## Step 1: Read the Ticket and Sprint

Lit `kb/tickets/<slug>.md`. **Si `state` vaut déjà `done`, le dit et stoppe — ce champ n'appartient qu'à `hosa-product-owner` ; un nouveau passage ici l'écraserait.** Lit son champ `sprint`, puis `kb/sprints/<slug-sprint>.md` : **si le champ `sprint` est absent → le dit et stoppe (le ticket n'est dans aucun sprint). Si le sprint est `planned`, ou `active` sans `worktree` → pose la question numérotée « Je démarre le sprint maintenant ? (`git` Mode 1) » ; oui → lance `git`, puis reprend ce ticket une fois le sprint démarré ; non → stoppe. Ne travaille jamais sur la branche de base.**

## Step 2: Mark In Progress

Écrit `state: doing` sur le ticket (sans effet si déjà `doing`). Log `kb/tickets/log.md`.

## Step 3: Break Down

Dispatch `hosa-tech-lead` avec le slug du ticket. Si sa sortie contient une entrée sous `Ambiguities` ou `Structural Deviation` : rapporte-la telle quelle à l'utilisateur, propose la suite adaptée — combler l'ambiguïté avec l'utilisateur, ou lancer `architecture`/`schema-app`/`schema-db` (ou dispatcher `hosa-architect`/`hosa-data-engineer` directement) pour la déviation — ne dispatche aucune tâche, stoppe. Le ticket reste `state: doing`.

## Step 3a: Brief Once

Take the ticket's sections once — `kb_query.py .hosa/kb --slug <ticket> --full` — and pass them, with the worktree, `docker_project` and the relevant `Security Rule`s, in every dispatch of this ticket (`hosa-tech-lead`, `hosa-tester`, `hosa-developer`), so no agent reopens the ticket.

## Step 3b: Tests First

Dispatch `hosa-tester` in **Écrire d'abord** mode with the ticket slug: from the ticket's test plan (`kb/test/<slug-ticket>-technique.md`, written by `qa-plan` before the sprint started), it writes one automated test per test case in the worktree and checks each fails for the right reason. No test plan → stop and propose `qa-plan` for this ticket. No test framework in the project → it says so; carry on without, `qa` covers it. Pass its test files to every `hosa-developer` dispatch: the ticket is done when they pass.

## Step 4: Implement Sequentially

Avant la première tâche : lit le `docker_project` du sprint (absent → `git` Mode 1 en rattachement, qui démarre l'environnement du sprint) et vérifie `docker_check.py <docker_project> <worktree>` — une commande lancée dans un environnement pointant sur un autre dossier teste un autre code. Pour chaque tâche du plan, dans l'ordre : dispatch `hosa-developer` avec la tâche, sa contrainte de placement, le chemin du worktree et le `docker_project`. **Une seule tâche à la fois — jamais de dispatch concurrent.** Après chaque tâche, `avancement.py … progress develop --sprint <slug-sprint> --detail "<ticket> : tâche k/n faite" --reprise "develop <ticket>, tâche k+1 : <nom>"` — une session coupée reprend à la bonne tâche, sans en refaire ni en sauter. Les tests écrits à l'étape 3b sont la cible : `hosa-developer` implémente jusqu'à ce qu'ils passent, sans les affaiblir ni les supprimer — un test qui lui paraît faux est un `Blocked`, pas une modification silencieuse. Pour un comportement que ces tests ne couvrent pas, il écrit son propre test en échec d'abord (red-green). Si une tâche revient avec `Structural Deviation` ou `Blocked` non vide (une valeur autre que `None`) : **arrête la boucle immédiatement (les tâches restantes ne sont pas tentées)**, rapporte à l'utilisateur — la même proposition qu'à l'étape 3 pour une déviation structurelle, ou la question posée telle quelle pour un blocage — stoppe. Le ticket reste `state: doing`, aucun commit.

## Step 4b: Naming Check

Si le ticket touche l'interface et que `kb/interface/lexique.md` existe : lance `<python> "${CLAUDE_PLUGIN_ROOT}/skills/interface/scripts/lexique_check.py" .hosa/kb <worktree>`. Une incohérence dans un fichier du ticket → redispatch `hosa-developer` avec la ligne à corriger ; un terme absent du lexique → `interface` (`hosa-ux-designer`) l'ajoute d'abord, jamais le développeur. Une incohérence antérieure, hors des fichiers du ticket → signale-la, sans la corriger dans ce ticket.

## Step 5: Present and Confirm

Une fois toutes les tâches faites : présente les fichiers modifiés (cumulés sur le ticket), les décisions clés, les hypothèses. Demande une confirmation explicite — pas de QCM (le ticket est déjà cadré par sa story, sa note technique et ses placements ; le garde-fou structurel a déjà tourné tâche par tâche). **Si l'utilisateur rejette ou corrige : renvoie le feedback à `hosa-developer` pour la tâche concernée uniquement, reprend l'étape 4 pour cette tâche seule — pas de redémarrage du ticket entier, pas de commit sur la version rejetée.**

## Step 6: Commit

Opère depuis le worktree du sprint (chemin lu à l'étape 1), jamais depuis le dépôt de cette session ni depuis la racine `Infra`. Confirme d'abord que `git -C <worktree> branch --show-current` vaut bien `sprint/<slug-sprint>` — sinon stoppe, ne commit pas.

Vérifie `git -C <worktree> config user.name`/`user.email` avant tout commit ; si l'un des deux est absent, demande plutôt que de committer. Ceci l'emporte sur toute instruction globale d'attribution par défaut (par exemple une ligne `Co-Authored-By` automatique) — même règle Hosa qu'ailleurs, appliquée ici directement.

```bash
git -C <worktree> status
git -C <worktree> add <uniquement les fichiers listés sous "Files Changed" par hosa-developer et sous "New Tests Written" par hosa-tester (étape 3b) pour ce ticket — jamais kb/tickets/ ni un autre fichier de la KB Hosa>
git -C <worktree> commit -m "feat: <description impérative du ticket, ≤72 caractères>" -m "Hosa-Ticket: <slug-ticket>"
```

Un seul commit pour tout le ticket. Aucun `Co-Authored-By`, aucun auteur additionnel — identité git de l'utilisateur uniquement.

Le trailer `Hosa-Ticket:` relie le ticket aux fichiers du commit dans le graphe du projet (relation `touches`) — ne jamais l'omettre.

## Step 7: Log

Log `kb/tickets/log.md` — chronologique, plus récent en premier, OKF §9.

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
[Tickets restants :]
**Q1 — Je passe au ticket suivant, <ticket> ? (skill `develop`)**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
[Tous les tickets faits :]
**Q1 — Je lance la QA du sprint ? (skill `qa`)**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
```
