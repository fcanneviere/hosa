---
name: develop
description: "Use to implement sprint tickets in the sprint worktree: tests first (`hosa-tester`), tasks (`hosa-tech-lead`), code (`hosa-developer`), full checks, code review (`hosa-reviewer`), commit — by lot of small same-module tickets (default) or one ticket; also fixes a sprint ticket's defect (correction). Triggers: \"développe le ticket X\", \"développe le sprint\", \"développe le lot\"."
---

# Develop

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start develop --sprint <slug>`; refused → name the missing stage to the user and stop; refused as already done → a re-run only on the user's request: the same `start` with `--rouvre "<their request>"`. Stopped on a user question: `block develop --sprint <slug> --detail "<question>"`. Once the stage's output is written and committed: `done develop --sprint <slug>`. Never skip these calls: without them a cut session can't resume (« reprends ») and the session stays on the wrong model.

**Tâches.** Per ticket, ids prefixed by its slug: at Step 2, `avancement.py task add develop <ticket>.plan --sprint <slug> --agent hosa-tech-lead --objet <ticket>` and `<ticket>.tests` (`hosa-tester`); once the plan is written (Step 3), one `<ticket>.lot-<k>` per lot of Step 4 (`hosa-developer`, `--objet "tâches i-j"`: the lines of `## Plan de tâches`, not a copy) and `<ticket>.revue` (`hosa-reviewer`). Each return → `task done develop <id> --sprint <slug> --sortie <paths> --reprise "<the next action>"` (one call: the task and the resume point, never a separate `progress` for it): `plan` and `revue` → `kb/tickets/<ticket>.md`, `tests` → the test files, a lot → the files it changed. A lot stopped on `Blocked` or `Structural Deviation` → `task block … --detail "<la question>"`. A FAIL review → `task add <ticket>.correction-<n>` (`hosa-developer`) and `task add <ticket>.revue` again. A correction (Correction Mode) adds its own `<ticket>.correction-<n>` and `<ticket>.revue`.

**Reprise** (`args: "reprise"`). The resume card is the start-up: go to the step its `Action` and its tasks name (a `<ticket>.plan` done → Step 3 is done; a `.lot-<k>` to do → Step 4; a `.revue` to do → Step 4c; all done → Step 5), with the sprint's `worktree` and `docker_project` it gives. Skip Steps 1-2 for the tickets whose tasks exist; read no ticket again but for Brief Once (3a).

Implements a sprint ticket (`kb/tickets/<slug>.md`) in the worktree `git` Mode 1 already opened: a breakdown into short sequential tasks (`hosa-tech-lead`), then one task at a time (`hosa-developer`) — never a deviation from the structure `hosa-architect`/`hosa-data-engineer` scaffolded without stopping and escalating.

## Trigger

Manual: `/develop <slug-ticket>`, `/develop lot` (next lot of the sprint) or `/develop lot <slug> <slug>…`. Auto: "développe le ticket X", "implémente le ticket X"; chained by `git` Mode 1 and `sprint`.

---

## Step 1: Read the Ticket and Sprint

Read `kb/tickets/<slug>.md`. **If its `state` is already `done`, say so and stop — that field belongs to `hosa-product-owner` only; another pass here would overwrite it. Sole exception: Correction Mode (below), which reopens the ticket because a defect was found.** Read its `sprint` field, then `kb/sprints/<slug-sprint>.md`: **no `sprint` field → say so and stop (the ticket is in no sprint). The sprint is `planned`, or `active` without `worktree` → ask the numbered question « Je démarre le sprint maintenant ? (`git` Mode 1) »; yes → run `git`, then resume this ticket once the sprint has started; no → stop. Never work on the base branch.**

## Step 2: Mark In Progress

Write `state: doing` on the ticket (no effect if already `doing`). Log `kb/tickets/log.md`.

## Step 3: Break Down

Dispatch `hosa-tech-lead` with the ticket's slug. An entry under `Ambiguities` or `Structural Deviation` → dispatch no task, the ticket stays `state: doing`: read `${CLAUDE_PLUGIN_ROOT}/skills/develop/blocages.md` § Plan and follow it.

Clear plan: write `hosa-tech-lead`'s `Task Plan` and `Notes` as they are in the ticket, under `## Plan de tâches (tech lead)` at the end of the file (replace the section after a block). It is what a human developer reads to review or take over the ticket; don't summarize it. Each task done without a block: tick its line (`- [x]`).

## Step 3a: Brief Once

Take the ticket's sections once — `kb_query.py .hosa/kb --slug <ticket> --full` — and pass them, with the worktree, `docker_project` and the relevant `Security Rule`s, in every dispatch of this ticket (`hosa-tech-lead`, `hosa-tester`, `hosa-developer`), so no agent reopens the ticket.

## Step 3b: Tests First

Dispatch `hosa-tester` in **Écrire d'abord** mode with the ticket slug: from the ticket's test plan (`kb/test/<slug-ticket>-technique.md`, written by `qa-plan` before the sprint started), it writes one automated test per test case in the worktree and checks each fails for the right reason. No test plan → stop and propose `qa-plan` for this ticket. No test runner → it returns `## Installation nécessaire`: relay it to `hosa-infra` (Mode 2), then redispatch. Never carry on without tests. Pass its test files to every `hosa-developer` dispatch: the ticket is done when they pass.

## Step 4: Implement Sequentially

Before the first task: read the sprint's `docker_project` (missing → `git` Mode 1 in reattach mode, which starts the sprint's environment) and check `docker_check.py <docker_project> <worktree>` — a command run in an environment pointing at another folder tests other code. Group the plan's consecutive tasks into lots: up to 3 tasks touching the same module, 10 files at most. Each lot = one `hosa-developer` dispatch, with its tasks in order, their placement and security constraints, the worktree path and the `docker_project` — the agent loads its instructions and reads the files only once. **One lot at a time — never concurrent dispatches.** Dispatch with `model: sonnet` when the ticket's security note cites a `Security Rule`, and for every correction: on Haiku a call costs less, but a FAIL review costs a whole loop (pilot2: 2 FAILs out of 6, both on a security rule). A task that touches another module opens a new lot. The lot that finishes the ticket is marked `dernier lot`: `hosa-developer` then runs the full suite and the `## Outillage qualité` checks (lint, format, types) and reports `## Checks`. A failure outside the ticket's files → show it to the user before the review. After each lot, one call: `task done develop <ticket>.lot-<k> --sprint <slug-sprint> --sortie <the lot's files> --reprise "develop <ticket>, tâche k+1 : <nom>"` — `--reprise` writes the resume point in the same call: a cut session resumes at the right task, without redoing or skipping one. The tests written at Step 3b are the target: `hosa-developer` implements until they pass, without weakening or deleting them — a test it thinks wrong is a `Blocked`, not a silent change. For behaviour those tests don't cover, it writes its own failing test first (red-green). A task of the lot returns `Structural Deviation` or a `Blocked` other than `None` → **stop the loop at once** (the remaining tasks are not attempted), no commit, the ticket stays `state: doing`: `blocages.md` § Lot.

## Step 4b: Naming Check

If the ticket touches the interface and `kb/interface/lexique.md` exists: run `<hosa> lexique_check .hosa/kb <worktree>`. An inconsistency in one of the ticket's files → redispatch `hosa-developer` with the line to fix; a term missing from the lexicon → `interface` (`hosa-ux-designer`) adds it first, never the developer. An older inconsistency, outside the ticket's files → report it, without fixing it in this ticket.

## Step 4c: Code Review

Dispatch `hosa-reviewer` in **ticket review**: the ticket's sections (Step 3a), `kb/rules/design/definition-de-termine.md`, the ticket's changed files and tests, the worktree. After each review, add a line under the ticket's `## Revue` (root KB): `- <AAAA-MM-JJTHH:MMZ> — PASS | PASS-WITH-NOTES | FAIL — <manques ou notes>` (UTC time from `date -u +%Y-%m-%dT%H:%MZ`: after a `back … develop` loop, `done develop` needs a review dated after it). The `gate.js` hook refuses the ticket's commit while the last line is not PASS or PASS-WITH-NOTES. **FAIL** → redispatch `hosa-developer` in `correction` with the exact list of gaps: it shows each one by a failing test before fixing it (`prouvé`), or returns it `non reproduit`. Write the `## Corrections` line (`correction.md`, point 4). Then a **correction review**: `hosa-reviewer` gets the previous gaps, the developer's `## Constats` and the correction's diff — nothing else, it doesn't re-read the whole ticket. Two FAILs in a row → stop and show the gaps to the user. The `gate.js` hook enforces this bound: it refuses any `hosa-developer` dispatch on a ticket whose last two `## Revue` lines are FAIL. The user's answer is written under `## Revue`: `- <date> — DÉCISION — <son choix>`, without the words PASS or FAIL. The count then restarts from zero. **PASS-WITH-NOTES** → the notes go into Step 5's presentation.

## Step 5: Present and Confirm

Once every task is done and the review passed: present the changed files (accumulated over the ticket), the key decisions, the assumptions, the result of the checks and of the review. Ask for an explicit confirmation — no quiz (the ticket is already framed by its story, its technical note and its placements; the structural guard already ran task by task). **If the user rejects or corrects: send the feedback to `hosa-developer` for the task concerned only, and redo Step 4 for that task alone — no restart of the whole ticket, no commit of the rejected version.**

## Step 6: Commit

Work from the sprint's worktree (path read at Step 1), never from this session's repository nor from the `Infra` root. First confirm that `git -C <worktree> branch --show-current` is `sprint/<slug-sprint>` — otherwise stop, don't commit.

Check `git -C <worktree> config user.name`/`user.email` before any commit; if either is missing, ask rather than commit. This overrides any global default attribution instruction (for instance an automatic `Co-Authored-By` line) — the same Hosa rule as elsewhere, applied here directly.

```bash
git -C <worktree> status
git -C <worktree> add <only the files listed under "Files Changed" by hosa-developer and under "New Tests Written" by hosa-tester (Step 3b) for this ticket — never kb/tickets/ nor any other Hosa KB file>
git -C <worktree> commit -m "feat: <imperative description of the ticket, ≤72 characters>" --trailer "Hosa-Ticket: <slug-ticket>"   # fix: … for a correction
```

One commit for the whole ticket. No `Co-Authored-By`, no additional author — the user's git identity only.

The `Hosa-Ticket:` trailer links the ticket to the commit's files in the project graph (relation `touches`) — never omit it.

## Lot Mode

The default when the sprint has several tickets to do: a ticket alone pays each time for starting four agents, re-reading the same files and one confirmation; a lot pays them once. Measured on hosa-ui's sprint 1 (8 tickets, one by one): 60 % of the cost in the orchestrating session, 37 dispatches.

**Compose the lot.** Take the sprint's `todo`/`doing` tickets in priority order and group the consecutive ones that touch the same module (`## Placement architecture`): at most 4 tickets and 8 points, no ticket above 3 points (a big ticket stays alone, normal flow), no dependency (`depends_on`) on a ticket outside the lot or later in the lot. Announce the lot (slugs, points) and launch it, without a quiz.

**Run it.** The steps of the normal flow, once for the lot:
1. Steps 1-2 for each ticket (`state: doing`), then Brief Once (3a) for all: one read of the sections, passed to every dispatch.
2. Step 3: **one** `hosa-tech-lead` dispatch with every slug → one plan per ticket; each is written in its ticket. A blocked ticket leaves the lot (it stays `doing`, its block is reported); the others go on.
3. Step 3b: **one** `hosa-tester` dispatch (Écrire d'abord) with every slug.
4. Step 4: the task lots follow the tickets' order; the `dernier lot` of tasks is the last ticket's: the full suite and the checks run only once.
5. Step 4b once on the lot's files; Step 4c: **one** lot review (`hosa-reviewer`, a verdict per ticket), one `## Revue` line written in each ticket. FAIL on a ticket → correction of that ticket alone, then review of that ticket alone.
6. Step 5: **one** presentation and **one** confirmation for the lot, ticket by ticket.
7. Step 6: one commit per ticket when their files are disjoint; otherwise one commit for the lot, with one `--trailer "Hosa-Ticket: <slug>"` per ticket — never one `-m` per trailer, which splits them into paragraphs (the `gate.js` hook checks each one's review; the graph links the files to each ticket). Then 6b and 7.

After each committed ticket: `avancement.py progress develop --sprint <slug-sprint> --detail "<lot> : ticket k/n commité" --reprise "develop lot <slugs restants>"` — the commit is not a task, it alone needs this `progress`.

## Session

The orchestrating session only orchestrates, and it costs the most: its context is re-read on every call. It reads neither the code nor the screenshots (the agents do); from each agent report it keeps the sections it must relay, not the rest. **One lot (or one big ticket) per session**: at the end of a lot, the `develop` stage stays `en cours` with its `--reprise`, and the Suite proposes `/clear` then « reprends » (the session hook re-reads the resume point). Never chain two lots in the same session.

## Correction Mode

`/develop <slug-ticket> correction`, or chained by `qa`, `validation` (démo), the sprint audit or a FAIL review: a defect on a ticket of the **active** sprint is fixed in that sprint, on its worktree. Read `${CLAUDE_PLUGIN_ROOT}/skills/develop/correction.md` first and follow it — only then: a normal lot never needs it.

## Step 6b: Clean Worktree

After the commit: `git -C <worktree> status --porcelain -- . ':(exclude).hosa'`. Any output = ticket work that `Files Changed` left out: list those files to the user. They belong to the ticket → add them to the commit (`git commit --amend`, the sprint branch is not published). To discard → only with their explicit confirmation. Never move on to the next ticket with an unclean worktree.

## Step 7: Log

Log `kb/tickets/log.md` — chronological, most recent first, OKF §9.

## Commits

This skill is the only point that commits in this flow — never `hosa-tech-lead`/`hosa-developer` themselves — always under the user's git identity, never a co-author.

## Output

```
## Ticket <slug> implémenté
- Tâches réalisées : [n]
- Fichiers modifiés : [liste]

## Blocage (si applicable)
[Ambiguïté ou déviation structurelle, et ce qui est proposé pour la lever]

## Suite
[Tickets restants :]
Suite : `/clear`, puis « reprends » — prochain lot : <slugs> (une session neuve par lot).
[Correction faite :]
Suite : `qa <sprint> <ticket> technique` (correction technique : recettes conservées) ou `qa <sprint> <ticket>` (fonctionnelle : CAn…), lancé sans attendre.
[Aucun constat reproduit :]
Rien corrigé : <constats non reproduits, avec leur test> — renvoyés à <source>.
[Tous les tickets faits :]
Suite : audit du sprint (`qualite`, étape `audit`), lancé sans attendre — puis `qa`.
```
