---
name: sprint
description: "Use to compose a sprint from the backlog in priority order, up to a capacity, with complete tickets only, then chain `qa-plan`. Triggers: \"planifie un sprint\", \"compose le prochain sprint\"."
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

First, `kb/infra/environnement-docker.md` must have `## Outillage qualité` with a test command (and the migration command, or "Aucune base de données"): otherwise the project isn't ready for a sprint — say so, invoke `infra` to install them, and stop.

Dispatch `hosa-sprint-planner` (Phase 1, `agents/sprint-planner.md`) with the capacity if one came with the trigger; otherwise it proposes one — don't ask.

If it returns an Open Question (empty backlog, no priority order) — relay it to the user, propose `backlog` if the backlog itself looks empty, and only redispatch once resolved.

## Step 2: Review with the User

Present `## Tickets prêts`, in the build order the planner set from `depends_on`, and `## Tickets écartés` (incomplete, or waiting on a dependency). For each ticket écarté, offer to fill the gap now (`stack`/`architecture`/`interface`, `backlog` to refine a vague ticket, or a direct opinion from `hosa-senior-dev`/`hosa-architect`/`hosa-ux-designer`) — if the user does, redispatch Phase 1 fresh afterward so the reclassification reflects the fix, rather than patching the old result by hand. Otherwise present `## Proposition de sprint` (name, objective, capacity) with the tickets as one numbered question for the user to validate or amend in one answer ("Q1 a", or "Q1 b, retire le ticket 3") — they may drop a ticket to wait for a fuller backlog.

If `## Tickets prêts` is empty and the user has no gap to fill, stop here — report the tickets écartés and their Open Questions, don't write a `Sprint`.

## Step 3: Dispatch to Write

Redispatch `hosa-sprint-planner` (Phase 2) with the sprint's name/objective and the confirmed ticket list. If it returns an Open Question (slug already taken) — let it propose the next free name, and redispatch.

## Step 4: Add the Tests to the Sprint

A sprint isn't ready to start until its tests are part of it. Run `qa-plan` on the sprint now: one technical test plan per ticket (`hosa-qa-lead`) and the test dataset with its reset command (`hosa-data-engineer`). `git` Mode 1 refuses to start a sprint whose tickets don't all have their plan. Then, without asking: `git` (Mode 1) opens the sprint's branch, worktree and environment, and `develop` starts on the first ticket of `## Tickets`.

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

Suite : `qa-plan`, puis démarrage du sprint (`git` Mode 1), lancé sans attendre.
```
