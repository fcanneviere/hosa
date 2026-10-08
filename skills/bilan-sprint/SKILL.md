---
name: bilan-sprint
description: Use to close a sprint after it merges — dispatches `hosa-product-owner` (Responsibility 7) to judge whether its objective was met, list what was delivered vs. deferred, surface recurring friction from its recettes, and write a `Sprint Review` plus follow-up tickets or process Design Rules. Follow-on to `git` Mode 2.
---

# Bilan Sprint

Sprint Review and retro: not just "which tickets closed", but whether the sprint's objective actually landed, and what should change next time.

## Flow

```
Lit kb/sprints/<slug>.md (state: done attendu) et ses tickets
        ↓ pas encore fusionné (state != done) → propose git Mode 2
          d'abord, stoppe
Dispatch hosa-product-owner (Responsibility 7)
        ↓
Écrit kb/sprints/<slug>-review.md + tickets de suivi et/ou
Design Rules process
        ↓
Log kb/sprints/log.md et kb/tickets/log.md (si tickets créés)
        ↓
Rapporte le bilan
```

## Trigger

Manual: `/bilan-sprint <slug-sprint>`. Auto: "fais le bilan du sprint X", "rétro du sprint X", "sprint review" ; proposé en Suite de `git` Mode 2.

---

## Step 1: Read the Sprint and Check Preconditions

Read `kb/sprints/<slug>.md`. If `state` isn't `done` (the sprint hasn't merged yet), say so and propose `git` Mode 2 first — stop, a review before merge is reviewing an unfinished sprint. Read its `## Tickets` list and each linked `kb/tickets/<slug-ticket>.md` for final `state`.

## Step 2: Dispatch `hosa-product-owner`

Dispatch `hosa-product-owner` (Responsibility 7, `agents/product-owner.md`) with the sprint, its tickets' final states, and every `kb/test/` result/recette verdict recorded for those tickets during `qa`. It judges the objective, writes `kb/sprints/<slug>-review.md`, and creates any follow-up `Ticket`/`Design Rule` the review surfaces. Run `backlog`'s Single-Ticket Mode on each follow-up `Ticket` it lists, so the next sprint can plan it as is.

## Step 3: Log

Confirm `kb/sprints/log.md` was updated for the review, and `kb/tickets/log.md`/`kb/rules/design/log.md` for anything created — per `hosa-product-owner`'s own logging.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB.

## Output

```
## Bilan du sprint <slug>
- Objectif : [Atteint / Partiellement atteint / Non atteint]
- Livré : [n tickets]
- Reporté : [n tickets] — [suite proposée]
- Friction récurrente : [résumé, ou "Aucune"]

## Créé
- `kb/sprints/<slug>-review.md`
- Tickets de suivi / Design Rules : [liste, ou "Aucun"]

## Suite
[Si des tickets de suivi ont été créés : "Je les priorise dans le backlog maintenant ? (skill `sprint` au prochain cycle)"]
```
