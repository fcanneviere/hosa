---
name: qa-plan
description: Use to prepare a sprint's technical test plan — for each ticket in a composed sprint, defines the technical test cases (grounded in the senior dev's recorded stack decisions) and identifies which persona(s) must validate it via recette. Follow-on to `sprint`, precondition for `qa`.
---

# QA Plan

Turns a composed sprint (`kb/sprints/<slug>.md`) into one technical `Test Plan` per ticket in `kb/test/`, so `qa` has something concrete to execute once the sprint is implemented.

## Flow

```
Lit kb/sprints/<slug>.md pour sa liste de tickets
        ↓
Pour chaque ticket sans kb/test/<slug-ticket>-technique.md
existant : lit sa Note technique (senior dev) + kb/stack/,
définit les cas de test, identifie le(s) persona(s) à
consulter en recette
        ↓
Ticket déjà préparé (fichier existe) → passe au suivant,
ne re-génère pas
        ↓
Écrit kb/test/<slug-ticket>-technique.md
        ↓
Log kb/test/log.md
        ↓
Propose de lancer qa une fois le sprint implémenté
```

## Trigger

Manual: `/qa-plan <slug-sprint>`. Auto: immediately after `sprint`, or "prépare les tests du sprint", "planifie les tests techniques du sprint".

---

## Step 1: Read the Sprint

Read `kb/sprints/<slug>.md` for its `## Tickets` list. If the sprint file doesn't exist, say so and ask for the correct slug rather than guessing.

## Step 2: Scope — Skip Already-Prepared Tickets

For each ticket in the sprint, check whether `hosa/kb/test/<slug-ticket>-technique.md` already exists. If it does, skip it — a re-run of `qa-plan` only prepares the gaps, it never regenerates or duplicates a plan already written for a ticket. If every ticket already has a plan, say so and report nothing to do.

## Step 3: Define Each Missing Plan

For each ticket without a plan yet:

1. Read the ticket (`kb/tickets/<slug-ticket>.md`): its story, the persona it links, and its `## Note technique (senior dev)` section.
2. Read `kb/stack/` for the recorded `Stack Decision`s — your "with the senior dev" basis, not a live consultation. If the technical note or the stack decisions are missing something needed to define a precise test case, say so and ask the user rather than inventing a technical detail with no basis.
3. Define the technical test cases: happy path, error cases, edge cases — in the same terms `hosa-tester` already uses.
4. Identify the recette required: the persona(s) linked in the ticket's story. If none is linked, write "Aucune — ticket sans persona identifié dans sa story." — never guess.
5. Write `hosa/kb/test/<slug-ticket>-technique.md`:

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
- <cas de test technique, dans les termes de hosa-tester>

## Recette requise
- [<persona>](../personnas/<slug>.md)

Lié à : [ticket](../tickets/<slug-ticket>.md)
```

## Step 4: Log

Append an entry to `kb/test/log.md` (create if missing) for each plan written — chronological, most recent date first, per OKF §9.

## No Commits

This skill does not commit. Report what changed in the KB and let the user decide when to commit.

## Output

```
## Plans de test écrits
- `kb/test/<slug-ticket>-technique.md` — [nombre de cas de test] — Recette requise : [personas / "Aucune"]

## Tickets déjà préparés (ignorés)
- `kb/tickets/<slug-ticket>.md` — plan déjà existant
[Si aucun : "Aucun"]

## Open Questions
[Si rien : "None"]

## Suite
Je lance `qa` une fois ce sprint implémenté ?
```
