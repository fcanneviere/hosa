# Sprint Planning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a seventh stage, `sprint`, that composes sprints from the Product Backlog (`kb/tickets/`), guarding against dispatching a ticket whose technical feasibility or architecture placement was never really evaluated.

**Architecture:** New OKF concept `Sprint` in `kb/sprints/`, a new agent `hosa-sprint-planner` that owns the sprint-composition process, and a self-contained skill `skills/sprint/SKILL.md` that embeds that same process inline (same pattern as `stack`/`architecture`/`backlog`). `backlog`'s `## Suite` output is updated to offer chaining into `sprint`, and `sprint` is registered in `using-simflow` and `agents/README.md`.

**Tech Stack:** Markdown agent/skill files (Claude Code plugin conventions), no code/tests — this repo's "implementation" is markdown content, verified by grep/read checks, same as the `backlog` plan.

**Spec:** `docs/superpowers/specs/2026-09-25-hosa-sprint-design.md`

## Global Constraints

- Pipeline order: `interview → redaction → relecture → contestation → stack → donnees → schema-app → schema-db → architecture → backlog → sprint`.
- `sprint` is NOT described as part of the "data-structuring pipeline" — it's the delivery-planning stage that follows it. Its description and skill docs must say so explicitly, not just omit the phrase.
- New agent frontmatter: `name: hosa-sprint-planner`, `model: claude-opus-4-8`, `memory: project`.
- `Sprint` concept lives in `kb/sprints/`, frontmatter `type: Sprint`, `state: planned | active | done`, body is a `## Tickets` list of markdown links to `kb/tickets/<slug>.md`.
- `Ticket` frontmatter gains an optional field `sprint: <slug>` — present only once a ticket is actually dispatched into a sprint; absent while it sits in the unplanned backlog.
- Sprint capacity is always user-given (a ticket count) — no auto-estimation, no new complexity field on `Ticket` in v1.
- Priority order is never invented by `sprint` — it's read from the order `hosa-product-owner` already holds; if that order isn't explicit, ask rather than guess.
- Technical-readiness guard: a ticket whose `Note technique (senior dev)` or `Placement architecture (architecte)` is still the fallback line ("Stack pas encore choisie — faisabilité non évaluée." / "Architecture pas encore scaffoldée — placement non déterminé.") is never silently dispatched into a sprint. The behavior is to say what's missing and propose filling it now (running `stack`/`architecture`, or getting a real opinion) — never just skip-and-flag-blocked.
- If the gap gets filled, re-evaluate that ticket against the updated note before deciding; if it stays unfilled, the ticket stays in the backlog, capacity unchanged (not spent on a rejected slot).
- Every agent/skill in this codebase: no commits (report and let the user decide), OKF §9 logging (chronological, most recent date first) to the bundle's own `log.md`.
- Git commits are in the user's name only (`git config user.name`/`user.email`) — never Co-Authored-By, never additional authors. This overrides any global default attribution instruction for this repo's work.

## Review Focus

- **Capacity given as 0 or negative, or larger than the number of eligible tickets.** A reasonable person expects `sprint` to compose whatever fits (0 → empty sprint, or say there's nothing to plan; more requested than available → take all eligible tickets, don't error). No task's steps currently exercise this — Task 2 must state the expected behavior explicitly in the skill and agent text.
- **All eligible tickets fail the readiness guard.** A reasonable person expects `sprint` to still report clearly (an empty "Tickets inclus" list, a full "Tickets écartés" list, and a real Open Question or proposal) rather than silently producing a `Sprint` file with zero tickets and no explanation. Task 2 must cover this in the Output section.
- **A ticket already has a `sprint:` field from a previous run.** Re-running `sprint` must not re-dispatch or duplicate it — same "no guessing / no overwrite" discipline as `backlog`'s re-run safety. Task 2's Step 1 (scope) must state this explicitly, mirroring `backlog` Step 1's dedup logic.
- **No `hosa-product-owner` priority order exists at all (fresh KB, no prior backlog session).** The spec says "ask the user or `hosa-product-owner`" — Task 2 must make this a concrete, first-class branch in both the agent and skill, not an afterthought.
- **`sprint` invoked standalone before `backlog` ever ran (empty `kb/tickets/`).** A reasonable person expects the same graceful "nothing to do yet, run `backlog` first" message `architecture`/`backlog` already give for their own missing prerequisites — Task 2 must state this explicitly rather than let the process silently produce an empty `Sprint`.

---

### Task 1: Create the `hosa-sprint-planner` agent

**Files:**
- Create: `agents/sprint-planner.md`
- Modify: `agents/README.md` (add one row to the Hosa agents table)

**Interfaces:**
- Consumes: `kb/tickets/` `Ticket` concepts with `state: todo`, `Note technique (senior dev)` and `Placement architecture (architecte)` sections written by `backlog`; `hosa-product-owner`'s current priority order (read live, not stored).
- Produces: `kb/sprints/<slug>.md` (`Sprint` concept, `state: planned`), `sprint: <slug>` written into dispatched tickets' frontmatter, `kb/sprints/log.md` and `kb/tickets/log.md` entries. Output format consumed by `skills/sprint/SKILL.md` (Task 2) and by any human/skill invoking this agent directly.

- [ ] **Step 1: Write `agents/sprint-planner.md`**

```markdown
---
name: hosa-sprint-planner
description: Use to compose a sprint from the Product Backlog (`hosa/kb/tickets/`) — dispatches tickets in the priority order already held by `hosa-product-owner`, up to a given capacity, and guards against dispatching a ticket whose technical feasibility or architecture placement was never actually evaluated. Invoke directly, or from the `sprint` skill.
model: claude-opus-4-8
memory: project
---

You compose sprints from Hosa's Product Backlog. You don't prioritize the backlog yourself — `hosa-product-owner` does — but you're the guarantor that nothing enters a sprint without its technical feasibility and its architecture placement having been actually evaluated, not just left on `backlog`'s fallback line.

## Input

A request to compose a sprint, with a capacity (a ticket count). If no capacity is given, ask the user rather than guessing — no complexity-estimation field exists on `Ticket` today, so there's no way to derive one automatically.

## Knowledge Base

You read from and write to Hosa's KB (`hosa/kb/`):

| Bundle | Type | What you use it for |
|---|---|---|
| `kb/tickets/` | `Ticket` | The Product Backlog. You read `state: todo` tickets without a `sprint` field yet, and their `Note technique (senior dev)` / `Placement architecture (architecte)` sections. You write `sprint: <slug>` into the ones you dispatch. |
| `kb/sprints/` | `Sprint` | New bundle you write into: `state: planned \| active \| done`. |

**Frontmatter you write on `Sprint`:** `generated: { by: hosa-sprint-planner/1.0, at: <ISO8601> }`.

**Logging:** append an entry to `kb/sprints/log.md` and to `kb/tickets/log.md` (create if missing) — chronological, most recent date first, per OKF §9.

## Process

1. Read `kb/tickets/` for `Ticket`s with `state: todo` and no `sprint` field already filled. If there are none — either `kb/tickets/` is empty or every `todo` ticket is already in a sprint — say so and propose running `backlog` first if the backlog itself looks empty; stop, don't produce an empty `Sprint`.
2. Read the priority order `hosa-product-owner` currently holds for these tickets. If it isn't explicit anywhere reachable (no prior backlog session, no stated order), ask the user for the order rather than inventing one.
3. Walk the tickets in that order, up to capacity:
   - Read the ticket's `Note technique (senior dev)` and `Placement architecture (architecte)` sections.
   - If either is still `backlog`'s fallback line ("Stack pas encore choisie — faisabilité non évaluée." or "Architecture pas encore scaffoldée — placement non déterminé."), say so and propose filling the gap now — running `stack`/`architecture`, or getting a real opinion from `hosa-senior-dev`/`hosa-architect` — rather than dispatching the ticket without knowing whether it's actually buildable.
   - If the user fills the gap, re-read the updated note and re-evaluate this ticket against it. If the gap stays unfilled, this ticket does not enter this sprint — it stays in the backlog, and capacity is not spent on it.
   - Otherwise (both notes are real), dispatch it: write `sprint: <slug>` into the ticket's frontmatter, add it to the `Sprint`'s ticket list.
   - If capacity is reached before the ticket list runs out, stop — the remaining tickets stay in the backlog for a future sprint. If fewer eligible tickets exist than the requested capacity, dispatch every eligible one and say so — this is not an error.
4. Write the `Sprint` to `kb/sprints/<slug>.md`, `state: planned`, body a `## Tickets` list of markdown links to the dispatched tickets:

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

5. Log the new `Sprint` to `kb/sprints/log.md`, and each ticket's frontmatter change to `kb/tickets/log.md` — OKF §9.

## No Commits

You do not commit. Report what you changed and let the user or orchestrating skill decide when to commit, per SimFlow's core rule that commits are always in the user's name only.

## Output Format

```
## Sprint composé
- `kb/sprints/<slug>.md` — [nom] (capacité: N, state: planned)

## Tickets inclus
- `kb/tickets/<slug>.md` — [titre]

## Tickets écartés (manque technique)
- `kb/tickets/<slug>.md` — [ce qui manque, proposé et décliné/différé]

## Open Questions
[Si rien : "None"]
```

## Project Memory

Save and recall: the sprint cadence already agreed with the user (duration, usual capacity), so it isn't asked again every time. Do NOT save: the content of a sprint already written — re-readable from `kb/sprints/`.
```

- [ ] **Step 2: Verify the frontmatter and required sections are present**

Run: `grep -c "^name: hosa-sprint-planner$\|^model: claude-opus-4-8$\|^memory: project$" agents/sprint-planner.md`
Expected: `3`

Run: `grep -c "^## Input$\|^## Knowledge Base$\|^## Process$\|^## No Commits$\|^## Output Format$\|^## Project Memory$" agents/sprint-planner.md`
Expected: `6` (one match per top-level section; this pattern deliberately excludes the `## Tickets`, `## Sprint composé`, etc. headings that also appear inside the file's fenced code-block templates, so it isn't thrown off by them)

- [ ] **Step 3: Add the agent to `agents/README.md`**

In the Hosa agents table (after the `hosa-architect` row), add:

```markdown
| [`hosa-sprint-planner`](sprint-planner.md) | claude-opus-4-8 | Composes each sprint from the Product Backlog — dispatches tickets in `hosa-product-owner`'s priority order up to a given capacity, guarding against dispatching a ticket whose technical feasibility or architecture placement was never actually evaluated. |
```

- [ ] **Step 4: Verify the README edit**

Run: `grep -c "hosa-sprint-planner" agents/README.md`
Expected: `1`

- [ ] **Step 5: Commit**

```bash
git add agents/sprint-planner.md agents/README.md
git commit -m "feat: add hosa-sprint-planner agent"
```

---

### Task 2: Create the `sprint` skill

**Files:**
- Create: `skills/sprint/SKILL.md`

**Interfaces:**
- Consumes: same `kb/tickets/`/`kb/sprints/` contract as Task 1's agent — the skill embeds the same process inline (self-contained skill pattern already used by `stack`/`architecture`/`backlog`), it does not invoke the `Agent` tool on `hosa-sprint-planner`.
- Produces: same `kb/sprints/<slug>.md`, ticket frontmatter updates, and log entries as Task 1. Output format consumed by whoever invokes `/sprint` (human or chained from `backlog`, Task 3).

- [ ] **Step 1: Write `skills/sprint/SKILL.md`**

```markdown
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

If a capacity (ticket count) wasn't given with the trigger, ask the user for one — no complexity-estimation field exists on `Ticket` today, so there's no way to derive a default automatically.

## Step 2: Scope

Read `kb/tickets/` for `Ticket`s with `state: todo` and no `sprint` field already filled — a re-run of `sprint` only dispatches gaps, it never re-dispatches a ticket that already carries a `sprint` field. If there are none, say so. If `kb/tickets/` has no `todo` tickets at all, propose running `backlog` first rather than producing an empty sprint.

## Step 3: Get the Priority Order

Read the priority order `hosa-product-owner` currently holds for these tickets (the live state of the backlog, not a stored snapshot). If it isn't explicit — no prior backlog session, no stated order — ask the user for the order rather than inventing one.

## Step 4: Dispatch Up to Capacity (technical-readiness guard)

Walk the tickets in that order, up to the capacity from Step 1:

- Read the ticket's `## Note technique (senior dev)` and `## Placement architecture (architecte)` sections.
- If either is still `backlog`'s fallback line ("Stack pas encore choisie — faisabilité non évaluée." or "Architecture pas encore scaffoldée — placement non déterminé."), say so and propose filling the gap now — running `stack`/`architecture`, or getting a real opinion from the senior-dev/architect roles — rather than dispatching the ticket without knowing whether it's actually buildable.
- If the user fills the gap, re-read the updated note and re-evaluate this ticket against it. If the gap stays unfilled, this ticket does not enter this sprint — it stays in the backlog, and capacity is not spent on it.
- Otherwise (both notes are real), dispatch it: write `sprint: <slug>` into the ticket's frontmatter, add it to the sprint's ticket list.
- If capacity is reached before the ticket list runs out, stop — the rest stay in the backlog for a future sprint. If fewer eligible tickets exist than the requested capacity, dispatch every eligible one and say so — not an error.

## Step 5: Write the Sprint

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
```

- [ ] **Step 2: Verify the frontmatter and trigger text**

Run: `grep -c "^name: sprint$" skills/sprint/SKILL.md`
Expected: `1`

Run: `grep -c "Manual: \`/sprint \[capacité\]\`" skills/sprint/SKILL.md`
Expected: `1`

- [ ] **Step 3: Verify the readiness guard and re-run safety are both stated**

Run: `grep -c "no \`sprint\` field already filled" skills/sprint/SKILL.md`
Expected: `1`

Run: `grep -c "propose filling the gap now" skills/sprint/SKILL.md`
Expected: `1`

- [ ] **Step 4: Commit**

```bash
git add skills/sprint/SKILL.md
git commit -m "feat: add sprint skill, data-structuring pipeline follow-on stage"
```

---

### Task 3: Chain `backlog` into `sprint`, register in `using-simflow`

**Files:**
- Modify: `skills/backlog/SKILL.md`
- Modify: `skills/using-simflow/SKILL.md`

**Interfaces:**
- Consumes: Task 2's `sprint` skill name and trigger phrasing (the `## Suite` text in `backlog` and the `using-simflow` tables must refer to it by the same name, `sprint`, and the same trigger phrases already written into `skills/sprint/SKILL.md`'s Trigger section).
- Produces: nothing new consumed by later tasks — this task only wires existing pieces together.

- [ ] **Step 1: Update `backlog`'s Flow diagram and Output**

In `skills/backlog/SKILL.md`, replace:

```
        ↓
Log kb/tickets/log.md
        ↓
Pipeline de structuration des données terminé
```

with:

```
        ↓
Log kb/tickets/log.md
        ↓
Propose de lancer sprint
```

Then replace:

```
## Suite
Pipeline de structuration des données terminé.
```

with:

```
## Suite
Je lance `sprint` maintenant ?
```

- [ ] **Step 2: Verify the `backlog` edit**

Run: `grep -c "Pipeline de structuration des données terminé" skills/backlog/SKILL.md`
Expected: `0`

Run: `grep -c "Je lance \`sprint\` maintenant ?" skills/backlog/SKILL.md`
Expected: `1`

- [ ] **Step 3: Register `sprint` in `using-simflow`'s skills table**

In `skills/using-simflow/SKILL.md`, after the `backlog` row in the skills table, add:

```markdown
| `sprint` | Compose a sprint from the Product Backlog — dispatch tickets in priority order up to a given capacity, guarding against dispatching one whose technical feasibility or architecture placement was never actually evaluated — follow-on to the data-structuring pipeline |
```

- [ ] **Step 4: Register `sprint` in `using-simflow`'s triggers table**

In `skills/using-simflow/SKILL.md`, after the `backlog` row in the triggers table, add:

```markdown
| "Planifie un sprint", "Compose le prochain sprint" | `sprint` |
```

- [ ] **Step 5: Verify both `using-simflow` edits**

Run: `grep -c "^| \`sprint\` |" skills/using-simflow/SKILL.md`
Expected: `1`

Run: `grep -c "Planifie un sprint" skills/using-simflow/SKILL.md`
Expected: `1`

- [ ] **Step 6: Commit**

```bash
git add skills/backlog/SKILL.md skills/using-simflow/SKILL.md
git commit -m "feat: chain sprint after backlog, register it in using-simflow"
```

---

### Task 4: Cross-file consistency verification

**Files:** none created or modified — this task only reads and checks.

**Interfaces:**
- Consumes: every artifact from Tasks 1-3.
- Produces: nothing — a clean pass here is the plan's completion signal.

- [ ] **Step 1: Confirm the agent name is consistent everywhere it's referenced**

Run: `grep -rc "hosa-sprint-planner" agents/sprint-planner.md agents/README.md skills/sprint/SKILL.md`
Expected: at least `1` in each of the three files (exact counts vary; a `0` in any file is the failure condition).

- [ ] **Step 2: Confirm the pipeline diagram phrasing in the spec matches what the skill/agent files imply**

Run: `grep -n "interview → redaction → relecture → contestation" docs/superpowers/specs/2026-09-25-hosa-sprint-design.md`
Expected: one match, ending in `...architecture → backlog → sprint`. Read the matched line to confirm — this step checks the spec is still internally consistent with what Tasks 1-3 built, not that any plan file repeats the whole diagram verbatim.

- [ ] **Step 3: Confirm `sprint` is never described as one of the data-structuring pipeline's own stages**

Run: `grep -c "stage of the data-structuring pipeline\|stage.*pipeline (stack" skills/sprint/SKILL.md agents/sprint-planner.md`
Expected: `0` in both files. This distinguishes the forbidden framing (the numbered-stage phrasing every actual pipeline-stage skill uses, e.g. "Sixth and last stage of the data-structuring pipeline (stack → ... → backlog)") from the allowed one (`sprint`'s own description may still say it follows that pipeline, per the spec's wording — it just can't claim to be one of its stages).

- [ ] **Step 4: Confirm no plan placeholder text leaked into the written files**

Run: `grep -rn "TBD\|TODO\|<fill" agents/sprint-planner.md skills/sprint/SKILL.md`
Expected: no output (empty).

- [ ] **Step 5: Report and stop**

No commit for this task — it's a read-only check. If every step above matched its Expected value, the plan is complete; report that to the user. If any step didn't match, that's a plan or content defect: rule on it per this plan's Global Constraints and the spec, fix the affected file, and re-run the failing step's command before reporting completion.
