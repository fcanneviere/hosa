---
name: sprint
description: Use to compose a sprint from the Product Backlog — dispatches tickets in `hosa-product-owner`'s priority order, up to a given capacity, guarding against dispatching a ticket whose technical feasibility or architecture placement was never actually evaluated. Follows the data-structuring pipeline's last stage (`backlog`), but is itself delivery planning, not data structuring.
---

# Sprint

Turns the Product Backlog (`kb/tickets/`) into a concrete sprint — a bounded set of tickets whose technical feasibility and architecture placement have both been actually evaluated, not left on `backlog`'s fallback line.

## Flow

```
Lit kb/tickets/ pour les Ticket state: todo sans champ
sprint déjà rempli
        ↓
Si aucun, propose de lancer backlog d'abord
        ↓
Reprend l'ordre de priorité tenu par hosa-product-owner
(demande si pas explicite)
        ↓
Pour chaque ticket dans cet ordre, jusqu'à capacité :
vérifie Note technique + Placement architecture ; si ligne
de repli, propose de combler le manque plutôt que
d'engager sans savoir
        ↓
Écrit kb/sprints/<slug>.md, state: planned
        ↓
Log kb/sprints/log.md et kb/tickets/log.md
```

## Trigger

Manual: `/sprint [capacité]`. Auto: immediately after `backlog`, or "planifie un sprint", "compose le prochain sprint".

---

## Step 1: Get the Capacity

If a capacity (ticket count) wasn't given with the trigger, ask the user for one — no complexity-estimation field exists on `Ticket` today, so there's no way to derive a default automatically. A capacity below 1 means there's nothing to plan — say so and ask for a real number rather than composing an empty sprint.

## Step 2: Scope

Read `kb/tickets/` for `Ticket`s with `state: todo` and no `sprint` field already filled — a re-run of `sprint` only dispatches gaps, it never re-dispatches a ticket that already carries a `sprint` field. If there are none, say so. If `kb/tickets/` has no `todo` tickets at all, propose running `backlog` first rather than producing an empty sprint.

## Step 3: Get the Priority Order

Read the priority order `hosa-product-owner` currently holds for these tickets (the live state of the backlog, not a stored snapshot). If it isn't explicit — no prior backlog session, no stated order — ask the user for the order rather than inventing one.

## Step 4: Dispatch Up to Capacity (technical-readiness guard)

Walk the tickets in that order, up to the capacity from Step 1:

- Read the ticket's `## Note technique (senior dev)` and `## Placement architecture (architecte)` sections.
- If either section is missing entirely, or still holds `backlog`'s fallback line ("Stack pas encore choisie — faisabilité non évaluée." or "Architecture pas encore scaffoldée — placement non déterminé."), treat it the same way: say so and propose filling the gap now — running `stack`/`architecture`, or getting a real opinion from the senior-dev/architect roles — rather than dispatching the ticket without knowing whether it's actually buildable. A ticket written directly by `hosa-product-owner` without going through `backlog` has no such sections at all — that's the same gap, not a pass.
- If the user fills the gap, re-read the updated note and re-evaluate this ticket against it. If the gap stays unfilled, this ticket does not enter this sprint — it stays in the backlog, and capacity is not spent on it.
- Otherwise (both notes are real), dispatch it: write `sprint: <slug>` into the ticket's frontmatter, add it to the sprint's ticket list.
- If capacity is reached before the ticket list runs out, stop — the rest stay in the backlog for a future sprint. If fewer eligible tickets exist than the requested capacity, dispatch every eligible one and say so — not an error.

## Step 5: Write the Sprint

If no ticket was dispatched in Step 4 (every eligible ticket hit the guard and the gap stayed unfilled), don't write a `Sprint` at all — report every ticket under "Tickets écartés" and put what's needed to unblock them under "Open Questions", then stop. Otherwise, ask the user for the sprint's name and objective/period if not already given — never invent them — then check `kb/sprints/` for a file with that slug; if one already exists, ask for a different name rather than overwriting it (an existing `Sprint`'s tickets still point back to it).

Write to `kb/sprints/<slug>.md`:

```markdown
---
type: Sprint
title: <nom du sprint>
description: <objectif ou période>
tags: []
state: planned
generated: { by: hosa-sprint-planner/1.0, at: <ISO8601> }
---
## Tickets
- [<titre>](../tickets/<slug>.md)
- [<titre>](../tickets/<slug>.md)
```

## Step 6: Log

Log the new `Sprint` to `kb/sprints/log.md` (create if missing), and each dispatched ticket's frontmatter change to `kb/tickets/log.md` — chronological, most recent date first, per OKF §9.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit.

## Output

```
## Sprint composé
- `kb/sprints/<slug>.md` — [nom] (capacité: N, state: planned)

## Tickets inclus
- `kb/tickets/<slug>.md` — [titre]

## Tickets écartés (manque technique)
- `kb/tickets/<slug>.md` — [ce qui manque, proposé et décliné/différé]

## Open Questions
[Si rien : "None"]

## Suite
Sprint prêt. Je lance un autre sprint pour le reste du backlog, ou on s'arrête là ?
```
