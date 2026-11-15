---
name: sprint
description: "Use to compose the next sprint: the next one of the roadmap computed from the tickets' dependency graph (milestones validated once by the user, up to 20 tickets and 15 demo tests), complete tickets only, gaps with one fix applied, then chain `qa-plan`. Triggers: \"planifie un sprint\", \"compose le prochain sprint\"."
---

# Sprint

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start sprint --sprint <slug>`; refused → name the missing stage to the user and stop; refused as already done → a re-run only on the user's request: the same `start` with `--rouvre "<their request>"`. Stopped on a user question: `block sprint --sprint <slug> --detail "<question>"`. Once the stage's output is written and committed: `done sprint --sprint <slug>`. Never skip these calls: without them a cut session can't resume (« reprends »), and `budget.js` can't apply the stage's `dispatch` rules (each agent's model, the agents at once) — they hold only while the stage is `en cours`.

**Tâches.** Before Step 3, `avancement.py task add sprint ecriture --sprint <slug> --agent hosa-sprint-planner`; on its return, `task done sprint ecriture --sprint <slug> --sortie kb/sprints/<slug>.md`. Phase 1 writes nothing: no task. Stopped on an Open Question → `task block sprint ecriture --sprint <slug> --detail "<la question>"`, and `task add` it again once answered.

Turns the Product Backlog (`kb/tickets/`) into a concrete sprint — a bounded set of tickets whose technical feasibility, architecture placement, and interface placement have all been actually evaluated, not left on `backlog`'s fallback line. This skill is the only one that talks to the user — the actual scoping, classification, and write is `hosa-sprint-planner`'s.

## Flow

```
Dispatch hosa-sprint-planner (Phase 1: scope, priority order,
classify tickets prêts/écartés)
        ↓ Open Questions (empty backlog, no priority order, objective unreachable) → relay to user, stop
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

Manual: `/sprint [nombre de tickets au plus]`. Auto: immediately after `backlog`, or "planifie un sprint", "compose le prochain sprint".

---

## Step 1: Dispatch to Scope and Classify

First, `kb/infra/environnement-docker.md` must have `## Outillage qualité` with a test command (and the migration command, or "Aucune base de données"): otherwise the project isn't ready for a sprint — say so, invoke `infra` to install them, and stop. Same for security: `kb/securite/modele-menaces.md` must exist once the architecture is documented — otherwise run `securite` (Menaces) first. Its abuse cases become the `[sécurité]` tests of every ticket; written after the code, they only find what must be redone.

Dispatch `hosa-sprint-planner` (Phase 1, `agents/sprint-planner.md`). **The sprint is the next one of the roadmap** (`kb/project/feuille-de-route.md`, its milestones validated once by the user): the planner recomputes it from the graph (`<hosa> graphe_tickets … feuille --ecrire`) and takes its first sprint — the milestones' paths in build order, up to 20 tickets and 15 demo tests (5 % over to keep a milestone whole). No roadmap yet (a backlog made before it) → the planner proposes the milestones (the steps of the main persona journey, in order) and the bounds: one question to the user, once; then the roadmap is written. A sprint is sized by its milestones, not by a developer's week.

Reopened by `qa-plan` (loop `qa-plan` → `sprint`, an `Écart de composition`): give the planner the loop's exact lines; it recomposes from the current sprint (`composer --sprint <slug>`). The user validates only what changes.

**A gap with one fix is applied, never offered.** A ticket the checker sets aside for a missing `depends_on`, a criterion to move to the ticket that brings what it tests, or one behaviour in two tickets → `backlog` Single-Ticket Mode on it at once (`hosa-product-owner` applies the checker's line), then recompute. rieki sprint-3: three such gaps came to the user as questions whose answer was written in the gap itself. Only a missing stage (`stack`, `architecture`, `interface`, `securite`, `juridique`) or a product choice goes to the user.

If it returns an Open Question (empty backlog, no priority order) — relay it to the user, propose `backlog` if the backlog itself looks empty, and only redispatch once resolved.

## Step 2: Review with the User

Present `## Tickets prêts`, in the build order of the roadmap, and `## Tickets écartés` with what was already fixed (above). A ticket set aside for a missing stage → offer that stage (`stack`/`architecture`/`interface`, or a direct opinion from `hosa-senior-dev`/`hosa-architect`/`hosa-ux-designer`), then redispatch Phase 1 fresh. **The roadmap's milestones validated, the sprint is announced, not asked** (`## Proposition de sprint`: name, milestones, size), and Step 3 runs in the same turn; the user can still say « retire le ticket 3 ». A question only when the sprint differs from the validated roadmap's next sprint by a milestone (blocked, moved): « Q1 a » validates, « Q1 b, … » amends.

If `## Tickets prêts` is empty and the user has no gap to fill, stop here — report the tickets écartés and their Open Questions, don't write a `Sprint`.

## Step 3: Dispatch to Write

Redispatch `hosa-sprint-planner` (Phase 2) with the sprint's name/objective and the confirmed ticket list. If it returns an Open Question (slug already taken) — let it propose the next free name, and redispatch.

## Step 4: Add the Tests to the Sprint

A sprint isn't ready to start until its tests are part of it. Run `qa-plan` on the sprint now: one technical test plan per ticket (`hosa-qa-lead`) and the test dataset with its reset command (`hosa-data-engineer`). `git` Mode 1 refuses to start a sprint whose tickets don't all have their plan. Then, without asking: `git` (Mode 1) opens the sprint's branch, worktree and environment, and `develop` starts on the first ticket of `## Tickets`.

## Commits

None here: the skill ends with the `hosa-git` checkpoint (`using-hosa`, Git checkpoints), before chaining on `qa-plan`.

## Output

```
## Sprint composé
- `kb/sprints/<slug>.md` — [nom] (N tickets, state: planned)

## Tickets inclus
- `kb/tickets/<slug>.md` — [titre]

## Tests du sprint
- [N plans de test écrits par `qa-plan`, jeu de données : <path>]

## Tickets écartés (manque technique)
- `kb/tickets/<slug>.md` — [ce qui manque, proposé et décliné/différé]

## Open Questions
[Si rien : "None"]

## Suite
Sprint prêt, tests compris. Une fois démarré, je lance `develop lot` sur son premier lot de tickets.

Suite : `qa-plan`, puis démarrage du sprint (`git` Mode 1), lancé sans attendre.
```
