---
name: sprint
description: Use to compose a sprint from the Product Backlog — dispatches tickets in `hosa-product-owner`'s priority order, up to a given capacity, guarding against dispatching a ticket whose technical feasibility, architecture placement, or interface placement was never actually evaluated. Follows the data-structuring pipeline's last stage (`backlog`), but is itself delivery planning, not data structuring.
---

# Sprint

Turns the Product Backlog (`kb/tickets/`) into a concrete sprint — a bounded set of tickets whose technical feasibility, architecture placement, and interface placement have all been actually evaluated, not left on `backlog`'s fallback line. This skill is the only one that talks to the user — the actual scoping, classification, and write is `hosa-sprint-planner`'s.

## Flow

```
Dispatch hosa-sprint-planner (Phase 1: scope, priority order,
classify tickets prêts/écartés)
        ↓ Open Questions (no capacity, empty backlog, no priority order) → relay to user, stop
        ↓ Tickets prêts / Tickets écartés
Présente le résultat à l'utilisateur — propose de combler les
tickets écartés (stack/architecture/interface) ou de continuer
sans eux ; demande le nom/objectif du sprint
        ↓
Redispatch hosa-sprint-planner (Phase 2) avec le nom/objectif et
les tickets confirmés → écrit le Sprint
        ↓
Log kb/sprints/log.md et kb/tickets/log.md
        ↓
Enchaîne sur `qa-plan` : plan de test de chaque ticket + jeu de
données — les tests font partie du sprint avant son démarrage
```

## Trigger

Manual: `/sprint [capacité]`. Auto: immediately after `backlog`, or "planifie un sprint", "compose le prochain sprint".

---

## Step 1: Dispatch to Scope and Classify

Dispatch `hosa-sprint-planner` (Phase 1, `agents/sprint-planner.md`) with the capacity (ask the user for one first if not given with the trigger — capacity stays a ticket count even when tickets carry an `estimate`, a capacity below 1 means there's nothing to plan).

If it returns an Open Question (empty backlog, no priority order) — relay it to the user, propose `backlog` if the backlog itself looks empty, and only redispatch once resolved.

## Step 2: Review with the User

Present `## Tickets prêts` and `## Tickets écartés`. For each ticket écarté, offer to fill the gap now (`stack`/`architecture`/`interface`, or a direct opinion from `hosa-senior-dev`/`hosa-architect`/`hosa-ux-designer`) — if the user does, redispatch Phase 1 fresh afterward so the reclassification reflects the fix, rather than patching the old result by hand. Otherwise confirm which of `## Tickets prêts` to actually include (the user may drop one to wait for a fuller backlog), and ask for the sprint's name and objective/period if not already given — never invent them.

If `## Tickets prêts` is empty and the user has no gap to fill, stop here — report the tickets écartés and their Open Questions, don't write a `Sprint`.

## Step 3: Dispatch to Write

Redispatch `hosa-sprint-planner` (Phase 2) with the sprint's name/objective and the confirmed ticket list. If it returns an Open Question (slug already taken) — ask the user for a different name and redispatch.

## Step 4: Add the Tests to the Sprint

A sprint isn't ready to start until its tests are part of it. Run `qa-plan` on the sprint now: one technical test plan per ticket (`hosa-qa-lead`) and the test dataset with its reset command (`hosa-data-engineer`). `git` Mode 1 refuses to start a sprint whose tickets don't all have their plan.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit.

## Output

```
## Sprint composé
- `kb/sprints/<slug>.md` — [nom] (capacité: N, state: planned)

## Tickets inclus
- `kb/tickets/<slug>.md` — [titre]

## Tests du sprint
- [N plans de test écrits par `qa-plan`, jeu de données : <path>]

## Tickets écartés (manque technique)
- `kb/tickets/<slug>.md` — [ce qui manque, proposé et décliné/différé]

## Open Questions
[Si rien : "None"]

## Suite
Sprint prêt, tests compris. Une fois démarré, je lance `develop` sur son premier ticket.

**Q1 — Je démarre le sprint maintenant ? (skill `git` : branche, worktree et environnement du sprint)**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
```
