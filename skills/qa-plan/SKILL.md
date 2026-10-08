---
name: qa-plan
description: "Use to add the tests to a sprint before it starts: one test plan per ticket (`hosa-qa-lead`) and the test dataset with its reset (`hosa-data-engineer`). Chained by `sprint`. Triggers: \"prépare les tests du sprint\"."
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

## Step 3b: Test Database

If `kb/infra/base-de-donnees.md` has no `## Tests` section yet (or doesn't exist), dispatch `hosa-dba` (Mode 2 Tests, `agents/dba.md`) first: the isolated test database, the isolation between tests, and the *réinitialiser la base de test* command the dataset's reset will call. No database in the project → skip.

## Step 4: Dispatch for the Test Dataset

Once every ticket of the sprint has its plan, dispatch `hosa-data-engineer` **with `model: sonnet`** — building a dataset from written test plans needs no design judgment, unlike its other responsibilities (Responsibility 4 create/update, `agents/data-engineer.md`) with the sprint slug. It builds or extends the dataset covering every test case and recette, documents it and loads it. If it returns an Open Question (architecture not done yet, tool missing for `hosa-infra`) — relay it to the user and only redispatch once resolved.

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
Les tests sont dans le sprint.

**Q1 — Je démarre le sprint maintenant ? (skill `git`)**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
```
