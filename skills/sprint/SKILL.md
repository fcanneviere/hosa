---
name: sprint
description: "Use to compose the next sprint: the next one of the roadmap computed from the tickets' dependency graph (milestones validated once, the first measuring an objective; up to 20 tickets and 15 demo tests), gaps with one fix applied, its tickets' notes written and judged, then chain `qa-plan`. Triggers: \"planifie un sprint\", \"compose le prochain sprint\"."
---

# Sprint

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start sprint --sprint <slug>`; refused → name the missing stage to the user and stop; refused as already done → a re-run only on the user's request: the same `start` with `--rouvre "<their request>"`. Stopped on a user question: `block sprint --sprint <slug> --detail "<question>"`. Once the stage's output is written and committed: `done sprint --sprint <slug>`. Never skip these calls: without them a cut session can't resume (« reprends »), and `budget.js` can't apply the stage's `dispatch` rules (each agent's model, the agents at once) — they hold only while the stage is `en cours`.

**Tâches.** Before Step 3 (not on a `qa-plan` round that keeps every ticket: `ordonner`, Step 1), `avancement.py task add sprint ecriture --sprint <slug> --agent hosa-sprint-planner`; on its return, `task done sprint ecriture --sprint <slug> --sortie kb/sprints/<slug>.md`. Phase 1 writes nothing: no task. A gap with one fix (Step 1) → `task add sprint graphe-<ticket> --sprint <slug> --agent hosa-product-owner` before the dispatch, `task done … --sortie kb/tickets/<the tickets it changed>.md` on its return; a moved criterion whose ticket has a plan → `task add sprint cas-<ticket> --agent hosa-qa-lead` for its case. Stopped on an Open Question → `task block sprint ecriture --sprint <slug> --detail "<la question>"`, and `task add` it again once answered. The notes of the sprint's tickets (Step 2b) are lots of four tasks, the judge last: `notes-<k>` → `securite-<k>` and `juridique-<k>` → `juge-<k>`, each refused at `task add` before the ones it comes after are done or skipped (`after`, pipeline.json).

Turns the Product Backlog (`kb/tickets/`) into a concrete sprint — a bounded set of tickets whose technical feasibility, architecture placement, interface placement, security and legal notes are written now, against the code as it is, for these tickets only (`backlog` planned every ticket on its story, criteria and graph). This skill is the only one that talks to the user — the actual scoping, classification, and write is `hosa-sprint-planner`'s.

## Flow

```
Dispatch hosa-sprint-planner (Phase 1) : feuille de route
recalculée (graphe_tickets feuille), son Sprint 1
        ↓ pas encore de jalons → les jalons proposés, une question, une fois
        ↓ écart à une correction → hosa-product-owner l'applique
          (backlog, Single-Ticket Mode), puis recalcul — sans question
        ↓ étape manquante (stack/architecture/interface) → proposée
Annonce le sprint (jalons, taille) — pas de question tant
qu'il suit la feuille de route validée
        ↓
Détaille ses tickets « à détailler », par lot de 8 :
notes-<k> (hosa-product-owner : technique, architecture,
interface) → securite-<k> (hosa-security) et juridique-<k>
(hosa-legal) → juge-<k> (hosa-juge) ; puis recalcul
        ↓
Redispatch hosa-sprint-planner (Phase 2) → écrit le Sprint
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

Dispatch `hosa-sprint-planner` (Phase 1, `agents/sprint-planner.md`). **The sprint is the next one of the roadmap** (`kb/project/feuille-de-route.md`, its milestones validated once by the user): the planner recomputes it from the graph (`<hosa> graphe_tickets … feuille --ecrire`) and takes its first sprint — the milestones' paths in build order, up to 20 tickets and 15 demo tests (5 % over to keep a milestone whole). No roadmap yet (a backlog made before it), or a roadmap whose first milestone measures no objective of the identity (`done sprint` refuses it) → the planner proposes the milestones (first the shortest path to what an objective measures, then the steps of the main persona journey, in order) and the bounds: one question to the user, once; then the roadmap is written with `--mesure <On>`. A sprint is sized by its milestones, not by a developer's week.

Reopened by `qa-plan` (loop `qa-plan` → `sprint`, an `Écart de composition`). **The fix changes only criteria or a `depends_on`, every ticket stays** (a criterion moved, a dependency already in the sprint): no planner, no `ecriture` task. The fix goes through `graphe-<ticket>` (`hosa-product-owner`), then `<hosa> graphe_tickets <root>/.hosa/kb ordonner --sprint <slug> --ecrire` puts `## Tickets` in build order and recounts « Taille : N tickets, P points » — `check sprint` refuses a size the tickets don't make. Then `done sprint` and `qa-plan` again. **A ticket enters or leaves:** give the planner the loop's exact lines; it recomputes the roadmap with that sprint's tickets free again (`feuille --sprint <slug> --ecrire`), and Phase 2 rewrites the sprint (`ecriture`). The user validates only what changes.

**A gap with one fix is applied, never offered.** A ticket the checker sets aside for a missing `depends_on`, a criterion to move to the ticket that brings what it tests, or one behaviour in two tickets → `backlog` Single-Ticket Mode on it at once (`hosa-product-owner` applies the checker's line), then recompute. The lines are the `Corrections uniques` that `feuille` prints, every one, copied as they are: never a list you write yourself, never only the sprint's. `done sprint` refuses while one is left in the backlog (`avancement.py check sprint`). rieki sprint-3: three such gaps came to the user as questions whose answer was written in the gap itself; then the product owner got four hand-written points, 16 one-fix tickets stayed « à compléter », and the sprint closed on « aucun écart ». Only a missing stage (`stack`, `architecture`, `interface`, `securite`, `juridique`) or a product choice goes to the user.

If it returns an Open Question (empty backlog, no priority order) — relay it to the user, propose `backlog` if the backlog itself looks empty, and only redispatch once resolved.

## Step 2: Review with the User

Present `## Tickets prêts`, in the build order of the roadmap, and `## Tickets écartés` with what was already fixed (above). A ticket set aside for a missing stage → offer that stage (`stack`/`architecture`/`interface`, or a direct opinion from `hosa-senior-dev`/`hosa-architect`/`hosa-ux-designer`), then redispatch Phase 1 fresh. **The roadmap's milestones validated, the sprint is announced, not asked** (`## Proposition de sprint`: name, milestones, size), and Step 3 runs in the same turn; the user can still say « retire le ticket 3 ». A question only when the sprint differs from the validated roadmap's next sprint by a milestone (blocked, moved): « Q1 a » validates, « Q1 b, … » amends.

If `## Tickets prêts` is empty and the user has no gap to fill, stop here — report the tickets écartés and their Open Questions, don't write a `Sprint`.

## Step 2b: Detail the Sprint's Tickets

`feuille` lists `À détailler avant le Sprint 1`: the sprint's tickets planned on their story, criteria and graph, whose five notes `backlog` left to this moment. Write them now, by lots of 8 tickets at most, with `${CLAUDE_PLUGIN_ROOT}/skills/backlog/redaction-tickets.md` (give its path to each agent, never this skill):
- `task add sprint notes-<k> --sprint <slug> --agent hosa-product-owner --objet "<tickets>"`: Steps 3-5 (technical note, architecture and interface placements), with the Grounding Rule; `task done … --sortie <the ticket paths>`.
- Then `securite-<k>` (`hosa-security`, Mode 5) and `juridique-<k>` (`hosa-legal`, Mode 3), dispatched together, on the same lot; `task done … --sortie <the ticket paths>`. A security or legal analysis still missing (fallback line) → `task skip sprint securite-<k> --sprint <slug> --detail "pas encore d'analyse"`. A stage the plan marks `non applicable` → no agent: `task skip sprint juridique-<k> --sprint <slug> --detail "étape écartée"`; the checker needs no note then.
- Then `task add sprint juge-<k> --sprint <slug> --agent hosa-juge --objet "lot <k>"`, dispatch `hosa-juge` with `sprint juge-<k> --sprint <slug>` and the lot's slugs, and `task done sprint juge-<k> --sprint <slug> --sortie <the verdict path>`. Refused by `juge-Qn` → each Non reopens its task (`notes-<k>`, `securite-<k>` or `juridique-<k>`) with its exact lines: a fresh agent of that task on its refused tickets only, then the judge on them only. At the bound (2 rounds of one question, or a ticket judged 3 times) stop and show the user what each round refused.

`budget.js` applies pipeline.json's `dispatch` for `sprint`: 2 Hosa agents at once, `hosa-security` and `hosa-legal` on `model: "sonnet"`. Then recompute (`feuille --ecrire`): the notes can add a `depends_on` (a `Corrections uniques` line) or split a ticket over 10 criteria. A ticket that enters `Sprint 1` gets its notes in one more lot; one that leaves it keeps them. `done sprint` refuses a sprint ticket still `(à détailler)` (`avancement.py check sprint`).

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
Sprint prêt, tickets détaillés et tests compris. Une fois démarré, je lance `develop lot` sur son premier lot de tickets.

Suite : `qa-plan`, puis démarrage du sprint (`git` Mode 1), lancé sans attendre.
```
