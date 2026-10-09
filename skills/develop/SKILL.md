---
name: develop
description: "Use to implement one sprint ticket in the sprint worktree: tests first (`hosa-tester`), tasks (`hosa-tech-lead`), code (`hosa-developer`), full checks, code review (`hosa-reviewer`), one commit; also fixes a sprint ticket's defect (correction). Triggers: \"développe le ticket X\", \"implémente le ticket X\"."
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
        ↓ dernier lot : suite complète + lint/format/types
Revue : dispatch hosa-reviewer (revue de ticket) → FAIL : correction
du développeur, nouvelle revue
        ↓ PASS
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

Lit `kb/tickets/<slug>.md`. **Si `state` vaut déjà `done`, le dit et stoppe — ce champ n'appartient qu'à `hosa-product-owner` ; un nouveau passage ici l'écraserait. Seule exception : le mode correction (ci-dessous), qui rouvre le ticket parce qu'un défaut a été trouvé.** Lit son champ `sprint`, puis `kb/sprints/<slug-sprint>.md` : **si le champ `sprint` est absent → le dit et stoppe (le ticket n'est dans aucun sprint). Si le sprint est `planned`, ou `active` sans `worktree` → pose la question numérotée « Je démarre le sprint maintenant ? (`git` Mode 1) » ; oui → lance `git`, puis reprend ce ticket une fois le sprint démarré ; non → stoppe. Ne travaille jamais sur la branche de base.**

## Step 2: Mark In Progress

Écrit `state: doing` sur le ticket (sans effet si déjà `doing`). Log `kb/tickets/log.md`.

## Step 3: Break Down

Dispatch `hosa-tech-lead` avec le slug du ticket. Si sa sortie contient une entrée sous `Ambiguities` ou `Structural Deviation` : rapporte-la telle quelle à l'utilisateur, propose la suite adaptée — combler l'ambiguïté avec l'utilisateur, ou lancer `architecture`/`schema-app`/`schema-db` (ou dispatcher `hosa-architect`/`hosa-data-engineer` directement) pour la déviation — ne dispatche aucune tâche, stoppe. Le ticket reste `state: doing`.

## Step 3a: Brief Once

Take the ticket's sections once — `kb_query.py .hosa/kb --slug <ticket> --full` — and pass them, with the worktree, `docker_project` and the relevant `Security Rule`s, in every dispatch of this ticket (`hosa-tech-lead`, `hosa-tester`, `hosa-developer`), so no agent reopens the ticket.

## Step 3b: Tests First

Dispatch `hosa-tester` in **Écrire d'abord** mode with the ticket slug: from the ticket's test plan (`kb/test/<slug-ticket>-technique.md`, written by `qa-plan` before the sprint started), it writes one automated test per test case in the worktree and checks each fails for the right reason. No test plan → stop and propose `qa-plan` for this ticket. No test runner → it returns `## Installation nécessaire`: relay it to `hosa-infra` (Mode 2), then redispatch. Never carry on without tests. Pass its test files to every `hosa-developer` dispatch: the ticket is done when they pass.

## Step 4: Implement Sequentially

Avant la première tâche : lit le `docker_project` du sprint (absent → `git` Mode 1 en rattachement, qui démarre l'environnement du sprint) et vérifie `docker_check.py <docker_project> <worktree>` — une commande lancée dans un environnement pointant sur un autre dossier teste un autre code. Regroupe les tâches consécutives du plan en lots : jusqu'à 3 tâches qui touchent le même module, 10 fichiers au plus. Chaque lot = un seul dispatch de `hosa-developer`, avec ses tâches dans l'ordre, leurs contraintes de placement et de sécurité, le chemin du worktree et le `docker_project` — l'agent ne recharge ses consignes et ne relit les fichiers qu'une fois. **Un seul lot à la fois — jamais de dispatch concurrent.** Une tâche qui touche un autre module ouvre un nouveau lot. Le lot qui termine le ticket est marqué `dernier lot` : `hosa-developer` lance alors la suite complète et les contrôles de `## Outillage qualité` (lint, format, types) et rapporte `## Checks`. Un échec hors des fichiers du ticket → montre-le à l'utilisateur avant la revue. Après chaque lot, pour chaque tâche faite, `avancement.py … progress develop --sprint <slug-sprint> --detail "<ticket> : tâche k/n faite" --reprise "develop <ticket>, tâche k+1 : <nom>"` — une session coupée reprend à la bonne tâche, sans en refaire ni en sauter. Les tests écrits à l'étape 3b sont la cible : `hosa-developer` implémente jusqu'à ce qu'ils passent, sans les affaiblir ni les supprimer — un test qui lui paraît faux est un `Blocked`, pas une modification silencieuse. Pour un comportement que ces tests ne couvrent pas, il écrit son propre test en échec d'abord (red-green). Si une tâche du lot revient avec `Structural Deviation` ou `Blocked` non vide (une valeur autre que `None`) : **arrête la boucle immédiatement (les tâches restantes ne sont pas tentées)**, rapporte à l'utilisateur — la même proposition qu'à l'étape 3 pour une déviation structurelle, ou la question posée telle quelle pour un blocage — stoppe. Le ticket reste `state: doing`, aucun commit.

## Step 4b: Naming Check

Si le ticket touche l'interface et que `kb/interface/lexique.md` existe : lance `<python> "${CLAUDE_PLUGIN_ROOT}/skills/interface/scripts/lexique_check.py" .hosa/kb <worktree>`. Une incohérence dans un fichier du ticket → redispatch `hosa-developer` avec la ligne à corriger ; un terme absent du lexique → `interface` (`hosa-ux-designer`) l'ajoute d'abord, jamais le développeur. Une incohérence antérieure, hors des fichiers du ticket → signale-la, sans la corriger dans ce ticket.

## Step 4c: Code Review

Dispatch `hosa-reviewer` en **revue de ticket** : les sections du ticket (étape 3a), `kb/rules/design/definition-de-termine.md`, les fichiers modifiés et les tests du ticket, le worktree. **FAIL** → redispatch `hosa-developer` en `correction` avec la liste exacte des manques, puis nouvelle revue. Deux FAIL de suite → arrête et montre les manques à l'utilisateur. **PASS-WITH-NOTES** → les notes vont dans la présentation de l'étape 5.

## Step 5: Present and Confirm

Une fois toutes les tâches faites et la revue passée : présente les fichiers modifiés (cumulés sur le ticket), les décisions clés, les hypothèses, le résultat des contrôles et de la revue. Demande une confirmation explicite — pas de QCM (le ticket est déjà cadré par sa story, sa note technique et ses placements ; le garde-fou structurel a déjà tourné tâche par tâche). **Si l'utilisateur rejette ou corrige : renvoie le feedback à `hosa-developer` pour la tâche concernée uniquement, reprend l'étape 4 pour cette tâche seule — pas de redémarrage du ticket entier, pas de commit sur la version rejetée.**

## Step 6: Commit

Opère depuis le worktree du sprint (chemin lu à l'étape 1), jamais depuis le dépôt de cette session ni depuis la racine `Infra`. Confirme d'abord que `git -C <worktree> branch --show-current` vaut bien `sprint/<slug-sprint>` — sinon stoppe, ne commit pas.

Vérifie `git -C <worktree> config user.name`/`user.email` avant tout commit ; si l'un des deux est absent, demande plutôt que de committer. Ceci l'emporte sur toute instruction globale d'attribution par défaut (par exemple une ligne `Co-Authored-By` automatique) — même règle Hosa qu'ailleurs, appliquée ici directement.

```bash
git -C <worktree> status
git -C <worktree> add <uniquement les fichiers listés sous "Files Changed" par hosa-developer et sous "New Tests Written" par hosa-tester (étape 3b) pour ce ticket — jamais kb/tickets/ ni un autre fichier de la KB Hosa>
git -C <worktree> commit -m "feat: <description impérative du ticket, ≤72 caractères>" -m "Hosa-Ticket: <slug-ticket>"   # fix: … pour une correction
```

Un seul commit pour tout le ticket. Aucun `Co-Authored-By`, aucun auteur additionnel — identité git de l'utilisateur uniquement.

Le trailer `Hosa-Ticket:` relie le ticket aux fichiers du commit dans le graphe du projet (relation `touches`) — ne jamais l'omettre.

## Correction Mode

`/develop <slug-ticket> correction`, or chained by `qa`, `validation` (démo) or the review: a defect on a ticket of the **active** sprint is fixed in that sprint, on its worktree — never left as a backlog ticket while the sprint waits.
1. Écrit `state: doing` sur le ticket et retire `verified` (même s'il était `done` : la validation est à refaire). Log, avec la source du défaut.
2. Le défaut a déjà un test en échec (QA) → passe-le. Sinon (démo, recette) → dispatch `hosa-tester` en Écrire d'abord avec le rapport du défaut : un test qui le reproduit, en échec.
3. Pas de `hosa-tech-lead` : dispatch `hosa-developer` en `correction` avec le test, le rapport et les fichiers concernés. Cause floue ou défaut qui touche plusieurs modules → `debug`, sur le worktree et le `docker_project` du sprint.
4. Puis étapes 4b, 4c, 5, 6 (commit `fix:` avec `Hosa-Ticket:`) et 7.
5. Suite : relance `qa` pour ce ticket seul, puis `validation`.

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
[Correction faite :]
**Q1 — Je relance la QA de ce ticket ? (skill `qa`)**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
[Tous les tickets faits :]
**Q1 — Je lance la QA du sprint ? (skill `qa`)**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
```
