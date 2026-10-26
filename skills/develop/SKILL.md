---
name: develop
description: "Use to implement sprint tickets in the sprint worktree: tests first (`hosa-tester`), tasks (`hosa-tech-lead`), code (`hosa-developer`), full checks, code review (`hosa-reviewer`), commit — by lot of small same-module tickets (default) or one ticket; also fixes a sprint ticket's defect (correction). Triggers: \"développe le ticket X\", \"développe le sprint\", \"développe le lot\"."
---

# Develop

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start develop --sprint <slug>`; refused → name the missing stage to the user and stop. Stopped on a user question: `block develop --sprint <slug> --detail "<question>"`. Once the stage's output is written and committed: `done develop --sprint <slug>`. Never skip these calls: without them a cut session can't resume (« reprends ») and the session stays on the wrong model.

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
Suite : ticket suivant du sprint, ou l'audit du sprint
(`qualite`, étape `audit`) quand tous sont faits, puis `qa`
```

## Trigger

Manual: `/develop <slug-ticket>`, `/develop lot` (next lot of the sprint) or `/develop lot <slug> <slug>…`. Auto: "développe le ticket X", "implémente le ticket X" ; proposé en Suite de `git` Mode 1 et de `sprint`.

---

## Step 1: Read the Ticket and Sprint

Lit `kb/tickets/<slug>.md`. **Si `state` vaut déjà `done`, le dit et stoppe — ce champ n'appartient qu'à `hosa-product-owner` ; un nouveau passage ici l'écraserait. Seule exception : le mode correction (ci-dessous), qui rouvre le ticket parce qu'un défaut a été trouvé.** Lit son champ `sprint`, puis `kb/sprints/<slug-sprint>.md` : **si le champ `sprint` est absent → le dit et stoppe (le ticket n'est dans aucun sprint). Si le sprint est `planned`, ou `active` sans `worktree` → pose la question numérotée « Je démarre le sprint maintenant ? (`git` Mode 1) » ; oui → lance `git`, puis reprend ce ticket une fois le sprint démarré ; non → stoppe. Ne travaille jamais sur la branche de base.**

## Step 2: Mark In Progress

Écrit `state: doing` sur le ticket (sans effet si déjà `doing`). Log `kb/tickets/log.md`.

## Step 3: Break Down

Dispatch `hosa-tech-lead` avec le slug du ticket. Si sa sortie contient une entrée sous `Ambiguities` ou `Structural Deviation` : rapporte-la telle quelle à l'utilisateur, propose la suite adaptée — combler l'ambiguïté avec l'utilisateur, ou, pour la déviation, la router vers le propriétaire qu'elle nomme : `architecture`/`hosa-architect` (module, couche), `schema-app`/`schema-db`/`hosa-data-engineer` (entité, champ), `hosa-ux-designer` (écran, composant, interaction) — ne dispatche aucune tâche, stoppe. Le ticket reste `state: doing`. Un fichier absent qu'un autre ticket crée (ambiguïté, pas déviation) : une seule question Q1 — A. créer le fichier dans ce ticket, avec le contrat de la `Note technique` du ticket créateur (recommandé quand le fichier est petit) — ce ticket le note `à créer`, le ticket créateur le note « existe, à étendre » ; B. sortir ce ticket du lot et ajouter le `depends_on` sur le ticket créateur. Puis relance le tech lead. **Tout ce qui touche l'interface (écran, parcours, composant, libellé visible) passe par `hosa-ux-designer`** en dispatch « Ticket gap » (slug, worktree, manque) : il complète l'écran dans le worktree et réécrit `## Placement interface (UX/UI)` ; puis relance cette étape.

Plan clair : écrit le `Task Plan` et les `Notes` de `hosa-tech-lead` tels quels dans le ticket, sous `## Plan de tâches (tech lead)` en fin de fichier (remplace la section après un blocage). C'est ce qu'un développeur humain lit pour relire ou reprendre le ticket ; ne le résume pas. Chaque tâche faite sans blocage : coche sa ligne (`- [x]`).

## Step 3a: Brief Once

Take the ticket's sections once — `kb_query.py .hosa/kb --slug <ticket> --full` — and pass them, with the worktree, `docker_project` and the relevant `Security Rule`s, in every dispatch of this ticket (`hosa-tech-lead`, `hosa-tester`, `hosa-developer`), so no agent reopens the ticket.

## Step 3b: Tests First

Dispatch `hosa-tester` in **Écrire d'abord** mode with the ticket slug: from the ticket's test plan (`kb/test/<slug-ticket>-technique.md`, written by `qa-plan` before the sprint started), it writes one automated test per test case in the worktree and checks each fails for the right reason. No test plan → stop and propose `qa-plan` for this ticket. No test runner → it returns `## Installation nécessaire`: relay it to `hosa-infra` (Mode 2), then redispatch. Never carry on without tests. Pass its test files to every `hosa-developer` dispatch: the ticket is done when they pass.

## Step 4: Implement Sequentially

Avant la première tâche : lit le `docker_project` du sprint (absent → `git` Mode 1 en rattachement, qui démarre l'environnement du sprint) et vérifie `docker_check.py <docker_project> <worktree>` — une commande lancée dans un environnement pointant sur un autre dossier teste un autre code. Regroupe les tâches consécutives du plan en lots : jusqu'à 3 tâches qui touchent le même module, 10 fichiers au plus. Chaque lot = un seul dispatch de `hosa-developer`, avec ses tâches dans l'ordre, leurs contraintes de placement et de sécurité, le chemin du worktree et le `docker_project` — l'agent ne recharge ses consignes et ne relit les fichiers qu'une fois. **Un seul lot à la fois — jamais de dispatch concurrent.** Dispatch avec `model: sonnet` quand la note sécurité du ticket cite une `Security Rule`, et pour toute correction : sur Haiku, un appel coûte moins, mais une revue FAIL coûte une boucle entière (pilot2 : 2 FAIL sur 6, toutes deux sur une règle de sécurité). Une tâche qui touche un autre module ouvre un nouveau lot. Le lot qui termine le ticket est marqué `dernier lot` : `hosa-developer` lance alors la suite complète et les contrôles de `## Outillage qualité` (lint, format, types) et rapporte `## Checks`. Un échec hors des fichiers du ticket → montre-le à l'utilisateur avant la revue. Après chaque lot, pour chaque tâche faite, `avancement.py … progress develop --sprint <slug-sprint> --detail "<ticket> : tâche k/n faite" --reprise "develop <ticket>, tâche k+1 : <nom>"` — une session coupée reprend à la bonne tâche, sans en refaire ni en sauter. Les tests écrits à l'étape 3b sont la cible : `hosa-developer` implémente jusqu'à ce qu'ils passent, sans les affaiblir ni les supprimer — un test qui lui paraît faux est un `Blocked`, pas une modification silencieuse. Pour un comportement que ces tests ne couvrent pas, il écrit son propre test en échec d'abord (red-green). Si une tâche du lot revient avec `Structural Deviation` ou `Blocked` non vide (une valeur autre que `None`) : **arrête la boucle immédiatement (les tâches restantes ne sont pas tentées)**, rapporte à l'utilisateur — la même proposition qu'à l'étape 3 pour une déviation structurelle, ou la question posée telle quelle pour un blocage (un `Installation nécessaire` va à `hosa-infra`, Mode 2, puis redispatch du lot) — stoppe. Le ticket reste `state: doing`, aucun commit.

## Step 4b: Naming Check

Si le ticket touche l'interface et que `kb/interface/lexique.md` existe : lance `<hosa> lexique_check .hosa/kb <worktree>`. Une incohérence dans un fichier du ticket → redispatch `hosa-developer` avec la ligne à corriger ; un terme absent du lexique → `interface` (`hosa-ux-designer`) l'ajoute d'abord, jamais le développeur. Une incohérence antérieure, hors des fichiers du ticket → signale-la, sans la corriger dans ce ticket.

## Step 4c: Code Review

Dispatch `hosa-reviewer` en **revue de ticket** : les sections du ticket (étape 3a), `kb/rules/design/definition-de-termine.md`, les fichiers modifiés et les tests du ticket, le worktree. Après chaque revue, ajoute une ligne sous `## Revue` du ticket (KB de la racine) : `- <date> — PASS | PASS-WITH-NOTES | FAIL — <manques ou notes>`. Le hook `gate.js` refuse le commit du ticket tant que la dernière ligne n'est pas PASS ou PASS-WITH-NOTES. **FAIL** → redispatch `hosa-developer` en `correction` avec la liste exacte des manques : il montre chacun par un test en échec avant de le corriger (`prouvé`), ou le rend `non reproduit`. Écrit la ligne `## Corrections` (Correction Mode, point 4). Puis **revue de correction** : `hosa-reviewer` reçoit les manques précédents, les `## Constats` du développeur et le diff de la correction — rien d'autre, il ne relit pas le ticket entier. Deux FAIL de suite → arrête et montre les manques à l'utilisateur. **PASS-WITH-NOTES** → les notes vont dans la présentation de l'étape 5.

## Step 5: Present and Confirm

Une fois toutes les tâches faites et la revue passée : présente les fichiers modifiés (cumulés sur le ticket), les décisions clés, les hypothèses, le résultat des contrôles et de la revue. Demande une confirmation explicite — pas de QCM (le ticket est déjà cadré par sa story, sa note technique et ses placements ; le garde-fou structurel a déjà tourné tâche par tâche). **Si l'utilisateur rejette ou corrige : renvoie le feedback à `hosa-developer` pour la tâche concernée uniquement, reprend l'étape 4 pour cette tâche seule — pas de redémarrage du ticket entier, pas de commit sur la version rejetée.**

## Step 6: Commit

Opère depuis le worktree du sprint (chemin lu à l'étape 1), jamais depuis le dépôt de cette session ni depuis la racine `Infra`. Confirme d'abord que `git -C <worktree> branch --show-current` vaut bien `sprint/<slug-sprint>` — sinon stoppe, ne commit pas.

Vérifie `git -C <worktree> config user.name`/`user.email` avant tout commit ; si l'un des deux est absent, demande plutôt que de committer. Ceci l'emporte sur toute instruction globale d'attribution par défaut (par exemple une ligne `Co-Authored-By` automatique) — même règle Hosa qu'ailleurs, appliquée ici directement.

```bash
git -C <worktree> status
git -C <worktree> add <uniquement les fichiers listés sous "Files Changed" par hosa-developer et sous "New Tests Written" par hosa-tester (étape 3b) pour ce ticket — jamais kb/tickets/ ni un autre fichier de la KB Hosa>
git -C <worktree> commit -m "feat: <description impérative du ticket, ≤72 caractères>" --trailer "Hosa-Ticket: <slug-ticket>"   # fix: … pour une correction
```

Un seul commit pour tout le ticket. Aucun `Co-Authored-By`, aucun auteur additionnel — identité git de l'utilisateur uniquement.

Le trailer `Hosa-Ticket:` relie le ticket aux fichiers du commit dans le graphe du projet (relation `touches`) — ne jamais l'omettre.

## Lot Mode

Le mode par défaut quand le sprint a plusieurs tickets à faire : un ticket seul paie à chaque fois le démarrage de quatre agents, la relecture des mêmes fichiers et une confirmation ; un lot les paie une fois. Mesure du sprint 1 de hosa-ui (8 tickets, un par un) : 60 % du coût dans la session qui orchestre, 37 dispatches.

**Composer le lot.** Prend les tickets `todo`/`doing` du sprint dans l'ordre de priorité et regroupe les consécutifs qui touchent le même module (`## Placement architecture`) : au plus 4 tickets et 8 points, aucun ticket au-delà de 3 points (un gros ticket reste seul, flow normal), aucune dépendance (`depends_on`) vers un ticket hors du lot ou plus loin dans le lot. Annonce le lot (slugs, points) et lance-le, sans QCM.

**Dérouler.** Les étapes du flow normal, une fois pour le lot :
1. Étapes 1-2 pour chaque ticket (`state: doing`), puis Brief Once (3a) pour tous : une seule lecture des sections, passée à chaque dispatch.
2. Étape 3 : **un** dispatch `hosa-tech-lead` avec tous les slugs → un plan par ticket ; chacun est écrit dans son ticket. Un ticket bloqué sort du lot (il reste `doing`, son blocage est rapporté) ; les autres continuent.
3. Étape 3b : **un** dispatch `hosa-tester` (Écrire d'abord) avec tous les slugs.
4. Étape 4 : les lots de tâches suivent l'ordre des tickets ; le `dernier lot` de tâches est celui du dernier ticket : la suite complète et les contrôles ne tournent qu'une fois.
5. Étape 4b une fois sur les fichiers du lot ; étape 4c : **une** revue de lot (`hosa-reviewer`, verdict par ticket), une ligne `## Revue` écrite dans chaque ticket. FAIL sur un ticket → correction de ce ticket seul, puis revue de ce ticket seul.
6. Étape 5 : **une** présentation et **une** confirmation pour le lot, ticket par ticket.
7. Étape 6 : un commit par ticket quand leurs fichiers sont disjoints ; sinon un commit pour le lot, avec un `--trailer "Hosa-Ticket: <slug>"` par ticket — jamais un `-m` par trailer, qui les sépare en paragraphes (le hook `gate.js` vérifie la revue de chacun ; le graphe rattache les fichiers à chaque ticket). Puis 6b et 7.

`avancement.py progress develop --detail "<lot> : ticket k/n fait" --reprise "develop lot <slugs restants>"` après chaque ticket commité.

## Session

La session qui orchestre ne fait qu'orchestrer, c'est elle qui coûte le plus : son contexte est relu à chaque appel. Elle ne lit ni le code ni les captures (les agents le font) ; elle garde de chaque rapport d'agent les sections qu'elle doit relayer, pas le reste. **Un lot (ou un gros ticket) par session** : à la fin d'un lot, l'étape `develop` reste `en cours` avec sa `--reprise`, et la Suite propose `/clear` puis « reprends » (le hook de session relit le point de reprise). Ne chaîne jamais deux lots dans la même session.

## Correction Mode

`/develop <slug-ticket> correction`, or chained by `qa`, `validation` (démo) or the review: a defect on a ticket of the **active** sprint is fixed in that sprint, on its worktree — never left as a backlog ticket while the sprint waits.
1. **Montre d'abord.** Le défaut a déjà un test en échec (QA) → passe-le. Démo, recette → dispatch `hosa-tester` en Écrire d'abord avec le rapport du défaut : un test qui le reproduit, en échec. Revue, audit → `hosa-developer` écrit ce test lui-même (point 3, son étape 11). Aucun constat reproduit → aucun code, aucun commit, le ticket garde son état ; écrit quand même la ligne `## Corrections` (point 4 : `0 prouvé(s)`, commit `aucun`), qu'elle soit mesurée ; rapporte les `non reproduit` (test et sortie) à la source — l'utilisateur pour une démo, la revue de correction, ou le ré-audit (`qualite`, audit du sprint), qui les juge sur ce test.
2. Au moins un constat prouvé → écrit `state: doing` sur le ticket et retire `verified` (même s'il était `done`). Log, avec la source du défaut.
3. Pas de `hosa-tech-lead` : dispatch `hosa-developer` en `correction`, `model: sonnet`, avec le test, le rapport et les fichiers concernés. Cause floue ou défaut qui touche plusieurs modules → `debug` en mode auto, sur le worktree et le `docker_project` du sprint.
4. **Type de la correction**, d'après son diff :
   - **technique** — le diff ne touche ni un écran, un gabarit, un libellé ou un message visible du `## Placement interface` du ticket, ni un `CAn`. Cas courant d'une revue, d'un audit ou d'un test en échec.
   - **fonctionnelle** — sinon, et toujours pour un défaut de recette ou de démo. Nomme les `CAn` touchés.
   Ajoute une ligne sous `## Corrections` du ticket (KB de la racine) : `- <date> — <source : revue | audit | qa | recette <persona> | démo> — <technique | fonctionnelle : CAn…> — <P> prouvé(s), <N> non reproduit(s) — <commit>`. `usage_report` en tire la pertinence des retours du sprint.
5. Puis étapes 4b, 4c (revue de correction), 5, 6 (commit `fix:` avec `Hosa-Ticket:`) et 7.
6. Suite. Correction d'un Bloquant de l'audit du sprint, avant la QA → ré-audit seulement : aucun test du sprint, aucune recette, aucune validation n'a encore tourné. Sinon, selon le type — une correction technique ne change rien de ce qu'un persona voit, la rejouer chez lui ne prouve rien de plus :
   - **technique** → `qa <sprint> <ticket> technique` : les tests seuls, les recettes restent valables ; puis `validation` en reconfirmation.
   - **fonctionnelle** → `qa <sprint> <ticket>` : les tests, puis la recette des seuls `CAn` touchés, chez les seuls personas qui les recettent ; puis `validation`.

## Step 6b: Clean Worktree

Après le commit : `git -C <worktree> status --porcelain -- . ':(exclude).hosa'`. Une sortie = du travail du ticket que `Files Changed` a omis : liste ces fichiers à l'utilisateur. Ils appartiennent au ticket → ajoute-les au commit (`git commit --amend`, la branche du sprint n'est pas publiée). À jeter → seulement avec sa confirmation explicite. Ne passe jamais au ticket suivant avec un worktree non propre.

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
Suite : `/clear`, puis « reprends » — prochain lot : <slugs> (une session neuve par lot).
[Correction faite :]
Suite : `qa <sprint> <ticket> technique` (correction technique : recettes conservées) ou `qa <sprint> <ticket>` (fonctionnelle : CAn…), lancé sans attendre.
[Aucun constat reproduit :]
Rien corrigé : <constats non reproduits, avec leur test> — renvoyés à <source>.
[Tous les tickets faits :]
Suite : audit du sprint (`qualite`, étape `audit`), lancé sans attendre — puis `qa`.
```
