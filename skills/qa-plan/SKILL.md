---
name: qa-plan
description: Use to add the tests to a sprint before it starts — for each ticket of a composed sprint, defines the technical test cases (grounded in the senior dev's recorded stack decisions) and the persona(s) who must validate it via recette, then has the test dataset built with its reset command. Chained by `sprint` right after composing it; precondition for starting the sprint (`git` Mode 1), for `develop`'s tests-first step and for `qa`.
---

# QA Plan

Turns a composed sprint (`kb/sprints/<slug>.md`) into one technical `Test Plan` per ticket in `kb/test/`, before the sprint starts — so `develop` can write each ticket's tests before its code, and `qa` has something concrete to execute. This skill is the only one that talks to the user — the actual test-case definition is `hosa-qa-lead`'s.

## Flow

```
Lit kb/sprints/<slug>.md pour sa liste de tickets
        ↓
Pour chaque ticket sans kb/test/<slug-ticket>-technique.md
existant : dispatch hosa-qa-lead (Mode 1)
        ↓ Open Question (note technique/stack incomplète) → relay to user, stop
        ↓ plan écrit
Ticket déjà préparé (fichier existe) → passe au suivant,
ne re-génère pas
        ↓ tous les plans écrits
Dispatch hosa-data-engineer (Responsabilité 4) : crée/étend,
documente et charge le jeu de données de test
        ↓
Propose de démarrer le sprint (git Mode 1)
```

## Trigger

Manual: `/qa-plan <slug-sprint>`. Auto: immediately after `sprint` (part of composing it), and for any ticket added to a sprint later, or "prépare les tests du sprint", "planifie les tests techniques du sprint".

---

## Step 1: Read the Sprint

Read `kb/sprints/<slug>.md` for its `## Tickets` list. If the sprint file doesn't exist, ask the user for the correct slug rather than guessing.

## Step 2: Scope — Skip Already-Prepared Tickets

For each ticket in the sprint, check whether `.hosa/kb/test/<slug-ticket>-technique.md` already exists. If it does, skip it — a re-run of `qa-plan` only prepares the gaps, it never regenerates or duplicates a plan already written for a ticket. If every ticket already has a plan, say so and report nothing to do.

## Step 3: Dispatch for Each Missing Plan

For each ticket without a plan yet, dispatch `hosa-qa-lead` (Mode 1, `agents/qa-lead.md`) with the ticket's slug. It reads the ticket's story, persona link, and technical note, reads the recorded `Stack Decision`s, defines the technical test cases, identifies the recette required, and writes `kb/test/<slug-ticket>-technique.md`.

If it returns an Open Question (the technical note or the stack decisions are missing something needed) — relay it to the user, get the answer, and only redispatch once you have it.

## Step 4: Dispatch for the Test Dataset

Once every ticket of the sprint has its plan, dispatch `hosa-data-engineer` (Responsibility 4 create/update, `agents/data-engineer.md`) with the sprint slug. It builds or extends the dataset covering every test case and recette, documents it and loads it. If it returns an Open Question (architecture not done yet, tool missing for `hosa-infra`) — relay it to the user and only redispatch once resolved.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit.

## Output

```
## Plans de test écrits
- `kb/test/<slug-ticket>-technique.md` — [nombre de cas de test] — Recette requise : [personas / "Aucune"]

## Tickets déjà préparés (ignorés)
- `kb/tickets/<slug-ticket>.md` — plan déjà existant
[Si aucun : "Aucun"]

## Jeu de données de test
- `<path>` — [créé | mis à jour] — doc : `<path>/README.md`

## Open Questions
[Si rien : "None"]

## Suite
Les tests sont dans le sprint. Je le démarre maintenant ? (skill `git`)
```
