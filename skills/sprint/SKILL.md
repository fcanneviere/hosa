---
name: sprint
description: Use to compose a sprint from the Product Backlog — dispatches tickets in `hosa-product-owner`'s priority order, with a name, objective and capacity proposed by `hosa-sprint-planner` for the user to validate, guarding against dispatching a ticket whose technical feasibility, architecture placement, or interface placement was never actually evaluated. Follows the data-structuring pipeline's last stage (`backlog`), but is itself delivery planning, not data structuring.
---

# Sprint

Turns the Product Backlog (`kb/tickets/`) into a concrete sprint — a bounded set of tickets whose technical feasibility, architecture placement, and interface placement have all been actually evaluated, not left on `backlog`'s fallback line. This skill is the only one that talks to the user — the actual scoping, classification, and write is `hosa-sprint-planner`'s.

## Flow

```
Vérifie kb/infra/environnement-docker.md ## Outillage (tests +
migrations)
        ↓ absent → `infra` d'abord, stoppe
Dispatch hosa-sprint-planner (Phase 1: scope, priority order,
classify tickets prêts/écartés, propose nom/objectif/capacité)
        ↓ Open Questions (empty backlog, no priority order) → relay to user, stop
        ↓ Proposition + Tickets prêts / Tickets écartés
Présente la proposition à l'utilisateur pour validation — propose
de combler les tickets écartés (stack/architecture/interface) ou
de continuer sans eux
        ↓
Redispatch hosa-sprint-planner (Phase 2) avec le nom/objectif et
les tickets confirmés → écrit le Sprint
        ↓
Log kb/sprints/log.md et kb/tickets/log.md
        ↓
qa-plan (tests du sprint écrits avant de démarrer) → git Mode 1
```

## Trigger

Manual: `/sprint [capacité]`. Auto: immediately after `backlog`, or "planifie un sprint", "compose le prochain sprint".

---

## Step 1: Dispatch to Scope and Classify

Read `kb/infra/environnement-docker.md`: no `## Outillage` naming both a test command and a migration command (or "Aucune base de données") → the project isn't ready for a sprint. Say so, invoke `infra` to install them, and stop.

Dispatch `hosa-sprint-planner` (Phase 1, `agents/sprint-planner.md`) with the capacity if one came with the trigger — otherwise let it propose one, don't ask.

If it returns an Open Question (empty backlog, no priority order) — relay it to the user, propose `backlog` if the backlog itself looks empty, and only redispatch once resolved.

## Step 2: Review with the User

Present `## Tickets prêts` and `## Tickets écartés`. For each ticket écarté, offer to fill the gap now (`stack`/`architecture`/`interface`, or a direct opinion from `hosa-senior-dev`/`hosa-architect`/`hosa-ux-designer`) — if the user does, redispatch Phase 1 fresh afterward so the reclassification reflects the fix, rather than patching the old result by hand. Otherwise present `## Proposition de sprint` (name, objective, capacity) with the tickets as one numbered block for the user to validate or amend in one answer (e.g. "Q1 ok, Q2 retire le ticket 3") — they may drop a ticket to wait for a fuller backlog.

If `## Tickets prêts` is empty and the user has no gap to fill, stop here — report the tickets écartés and their Open Questions, don't write a `Sprint`.

## Step 3: Dispatch to Write

Redispatch `hosa-sprint-planner` (Phase 2) with the validated name/objective and the confirmed ticket list. If it returns an Open Question (slug already taken) — let it propose the next free name and redispatch.

## Step 4: Prepare and Start

Without asking: invoke `qa-plan` on the sprint so every ticket has its test plan before any code is written, then invoke `git` (Mode 1) to open the sprint's branch and worktree, then `develop` on its first ticket.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa` Core Rules, "Git checkpoints".

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
Sprint composé — plan de tests en cours (skill `qa-plan`), puis démarrage (skill `git`, Mode 1) et développement du premier ticket (skill `develop`).
```
