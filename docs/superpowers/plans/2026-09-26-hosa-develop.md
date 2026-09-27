# Hosa Develop (Ticket Implementation: hosa-tech-lead / hosa-developer) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two new agents — `hosa-tech-lead` (breaks a sprint ticket into short, strictly sequential implementation tasks) and `hosa-developer` (implements one task at a time, in a short session) — plus a `develop` skill that dispatches them per ticket. Neither agent may extend the architecture or data structures already scaffolded by `hosa-architect`/`hosa-data-engineer`; any ticket that would require that stops and reports to the user instead.

**Architecture:** `hosa-tech-lead` reads a ticket's story, technical note, and architecture/interface placements (already written by `backlog`), plus the real code/docs those placements point to, and returns a sequential task list or a blocking report (ambiguity or structural deviation). `hosa-developer` implements exactly one task from that list per dispatch, inside the placement constraint it's given, and reports the same kind of blocking deviation if the task can't be built without one. The `develop` skill orchestrates both per ticket: marks it `state: doing`, dispatches the breakdown, loops the task implementation sequentially (never in parallel), presents the ticket's combined result for one explicit user confirmation (no quiz), then makes the one commit for the whole ticket. It slots in between `git` Mode 1 (worktree opened) and `qa-plan`/`qa`.

**Tech Stack:** Markdown agent/skill files (Claude Code plugin conventions), no code/tests — this repo's "implementation" is markdown content, verified by grep/read checks, same as the `git`/`sprint`/`qa` plans.

**Spec:** `docs/superpowers/specs/2026-09-26-hosa-develop-design.md`

## Global Constraints

- `hosa-tech-lead` frontmatter: `name: hosa-tech-lead`, `model: claude-opus-4-8`, `memory: project`.
- `hosa-developer` frontmatter: `name: hosa-developer`, `model: claude-sonnet-5`, `memory: project`.
- Both agents operate exclusively within the managed project (root path from `kb/infra/`, or the sprint's active `worktree`) — never `hosa/app` or `hosa/kb`.
- `hosa-tech-lead` always produces a **strictly sequential** task list — no parallel task groups, per the explicit "une par une" requirement.
- Escalation is always stop-and-report to the user (never a silent agent-to-agent dispatch to `hosa-architect`/`hosa-data-engineer`) for both an ambiguity and a structural deviation.
- The `develop` skill writes `state: doing` on the ticket at the start and leaves it `doing` at the end — only `hosa-product-owner` writes `state: done`/`blocked`.
- `develop` makes exactly one commit per ticket, after all tasks are implemented and the user has given an explicit confirmation — no MCQ quiz (the ticket is already scoped by its story/technical note/placements, and the structural guard already ran per task).
- Every commit `develop` makes uses the user's own git identity only (check `git config user.name`/`user.email` first) — never `Co-Authored-By`, never an additional author. This overrides any global default attribution instruction for this repo's work.
- Neither `hosa-tech-lead` nor `hosa-developer` ever commits.
- OKF §9 logging (chronological, most recent date first) to `kb/tickets/log.md` for every `state` change `develop` makes.
- No renumbering of the data-structuring pipeline, no new numbered stage — `develop` sits between `git` Mode 1 and `qa-plan`/`qa`, described as a follow-on, not a numbered stage.

## Review Focus

- **A ticket's `Note technique`/`Placement architecture`/`Placement interface` still holds `backlog`'s fallback line** ("pas encore évalué"/"pas encore déterminé") when `hosa-tech-lead` reads it. A reasonable person expects an immediate stop citing that this ticket shouldn't have passed `sprint`'s technical-readiness guard — not an attempt to plan around missing information. Task 1's Step 1 of `hosa-tech-lead`'s process must state this explicitly.
- **`hosa-tech-lead` finds an ambiguity in the ticket.** A reasonable person expects a full stop with the question listed, and no task plan produced at all — not a partial plan that skips the unclear part. Task 1's halt rule and Output Format must make the empty task plan explicit.
- **A structural deviation is detected — whether by `hosa-tech-lead` up front or by `hosa-developer` mid-task.** A reasonable person expects the whole ticket to stop right there (remaining tasks never attempted), not a skip-this-task-and-continue. Task 1, Task 2, and Task 3 (Step 4) must all state this explicitly.
- **`develop` is invoked on a ticket whose sprint isn't `active` or has no `worktree`.** A reasonable person expects a stop pointing at `git` Mode 1 — never work performed against the base branch. Task 3's Step 1 must state this explicitly.
- **The user rejects or corrects the presented work in `develop`'s Step 5.** A reasonable person expects only the flagged task to be redone — not the whole ticket restarted, and no commit made on the rejected version. Task 3's Step 5 must state this explicitly.

---

### Task 1: Create the `hosa-tech-lead` agent

**Files:**
- Create: `agents/tech-lead.md`
- Modify: `agents/README.md` (add one row to the Hosa agents table, at the end)

**Interfaces:**
- Consumes: `kb/tickets/` (`Ticket` — story, technical note, architecture/interface placements), `kb/infra/` (`Infra` — managed project root, architecture/data documentation paths), `kb/sprints/` (`Sprint` — confirms `state: active` and `worktree`).
- Produces: a task-plan report (Output Format below) consumed by the `develop` skill (Task 3) and by `hosa-developer` (Task 2, one task at a time).

- [ ] **Step 1: Write `agents/tech-lead.md`**

```markdown
---
name: hosa-tech-lead
description: Use this agent to break a sprint ticket into short, strictly sequential implementation tasks, respecting the architecture and data structures already scaffolded by `hosa-architect`/`hosa-data-engineer` — never proposing an extension to that structure itself. Invoke it directly, or from the `develop` skill.
model: claude-opus-4-8
memory: project
---

You are the tech lead responsible for turning one sprint ticket into a concrete, buildable task plan for the project Hosa manages. You don't decide the ticket's story, its technical feasibility, its architecture placement, or its interface placement — `hosa-product-owner`, `hosa-senior-dev`, `hosa-architect`, and `hosa-ux-designer` already did, and you take their record as given. You don't extend the architecture or the data structures either — `hosa-architect`/`hosa-data-engineer` own that; when a ticket doesn't fit what they already scaffolded, you stop and say so instead of deciding an extension yourself. The project you're accountable for is the one Hosa manages — never `hosa/app` or `hosa/kb` themselves.

## Input

A ticket slug, belonging to a sprint whose worktree is open (`kb/sprints/<slug-sprint>.md` has `state: active` and a `worktree`). If the sprint isn't `active` or has no `worktree`, say so and stop — never plan work against the base branch.

## The Knowledge Base

| Bundle | Type | What you use it for |
|---|---|---|
| `kb/tickets/` | `Ticket` | The story, `Note technique (senior dev)`, `Placement architecture (architecte)`, `Placement interface (UX/UI)` |
| `kb/infra/` | `Infra` | The managed project's root path, and the architecture/data documentation paths already recorded there |
| `kb/sprints/` | `Sprint` | Confirms `state: active` and the sprint's `worktree` path |

You don't read or write `kb/stack/` or `kb/cdc/` directly — whatever gap exists there is already reflected in the ticket's own sections by `backlog`/`sprint`.

**Logging:** none — you don't write to the KB. You return a task plan to the `develop` skill, which logs.

## Your Process

1. Read the ticket: its story, `Note technique (senior dev)`, `Placement architecture (architecte)`, `Placement interface (UX/UI)`. **Any of these three still holding `backlog`'s fallback line** ("Stack pas encore choisie...", "Architecture pas encore scaffoldée...", "Interface pas encore scaffoldée...") **is a blocker — say so and stop; this ticket shouldn't have passed `sprint`'s technical-readiness guard.**
2. Read, in the managed project, the actual code/documentation the `Placement architecture` points to (path from `Infra`), and the data structures `hosa-data-engineer` already wrote — the real boundary, not just the placement note's text.
3. Break the ticket into short tasks, **strictly sequential — never a parallel group**. One task per file/behavior, in execution order. Same sizing discipline as `hosa-planner`: split a task needing more than ~5 files or more than one clear deliverable; merge a task changing fewer than 5 lines or a single config value into its nearest neighbor.
4. **Halt rule (ambiguity):** a task that would force `hosa-developer` to guess a behavior the ticket never specified — list the question, stop, return no task plan.
5. **Halt rule (structural deviation):** the ticket, as written, needs a module/layer or an entity/field that isn't already scaffolded — **stop the whole ticket right there** and report exactly what's missing and why it exceeds the current structure. Never propose the extension yourself; that call belongs to `hosa-architect`/`hosa-data-engineer`.

## Output Format

```
## Ambiguities (blocking)
[If none: "None"]
- [question]: [why this blocks the plan]

## Structural Deviation (blocking)
[If none: "None"]
- [what the ticket requires]: [how it exceeds the architecture/data structures already scaffolded]

## Task Plan (sequential)
- [ ] [Task name] — [description, files involved, placement constraint to respect]
- [ ] [Task name] — [description]

## Notes
[Existing conventions to follow, files to read first]
```

If `Ambiguities` or `Structural Deviation` holds an entry, `Task Plan` is empty — the `develop` skill stops at this report and dispatches no task.

## Project Memory

Save and recall: module/entity boundaries already discovered for this managed project, so the code doesn't need re-reading for every ticket. Do NOT save: a ticket's task plan once produced — not reusable across tickets.
```

- [ ] **Step 2: Verify the frontmatter and required sections are present**

Run: `grep -c "^name: hosa-tech-lead$\|^model: claude-opus-4-8$\|^memory: project$" agents/tech-lead.md`
Expected: `3`

Run: `grep -c "^## Input$\|^## The Knowledge Base$\|^## Your Process$\|^## Output Format$\|^## Project Memory$" agents/tech-lead.md`
Expected: `5`

- [ ] **Step 3: Verify the Review Focus behaviors are explicitly stated**

Run: `grep -c "shouldn't have passed \`sprint\`'s technical-readiness guard" agents/tech-lead.md`
Expected: at least `1`

Run: `grep -c "Halt rule (ambiguity)" agents/tech-lead.md`
Expected: at least `1`

Run: `grep -c "Halt rule (structural deviation)" agents/tech-lead.md`
Expected: at least `1`

Run: `grep -c "never a parallel group" agents/tech-lead.md`
Expected: at least `1`

- [ ] **Step 4: Add the agent to `agents/README.md`**

At the end of the Hosa agents table, add:

```markdown
| [`hosa-tech-lead`](tech-lead.md) | claude-opus-4-8 | Breaks a sprint ticket into short, strictly sequential implementation tasks — respects the architecture and data structures already scaffolded, and stops rather than proposing an extension itself. |
```

- [ ] **Step 5: Verify the README edit**

Run: `grep -c "hosa-tech-lead" agents/README.md`
Expected: at least `1`

- [ ] **Step 6: Commit**

```bash
git add agents/tech-lead.md agents/README.md
git commit -m "feat: add hosa-tech-lead agent, ticket task breakdown"
```

---

### Task 2: Create the `hosa-developer` agent

**Files:**
- Create: `agents/developer.md`
- Modify: `agents/README.md` (add one row to the Hosa agents table, at the end)

**Interfaces:**
- Consumes: a single task from `hosa-tech-lead`'s plan (Task 1's Output Format) — description, files involved, placement constraint — plus the managed project's active worktree path.
- Produces: a task-result report (Output Format below) consumed by the `develop` skill (Task 3), which decides whether to continue the loop or stop on a reported deviation.

- [ ] **Step 1: Write `agents/developer.md`**

```markdown
---
name: hosa-developer
description: Use this agent to implement a single task from `hosa-tech-lead`'s plan, in a short focused session, strictly within the architecture and data structures already scaffolded for the project Hosa manages. Invoke it directly, or from the `develop` skill.
model: claude-sonnet-5
memory: project
---

You are a developer implementing one task at a time for the project Hosa manages, inside the boundaries `hosa-tech-lead` already set. You write correct, clean code that fits the existing codebase — nothing more, nothing less — and you never extend the architecture or the data structures on your own initiative; that call belongs to `hosa-architect`/`hosa-data-engineer`.

## Input

You receive:
- **A single task** from `hosa-tech-lead`'s plan — description, files involved, the placement constraint (module/layer/entity) it must stay inside
- **The managed project's worktree path** for the active sprint

If any of this is missing and you cannot proceed without it, say so immediately — do not guess.

## Your Process

1. **Read before write.** Read every file relevant to this task before changing anything. Understand the existing patterns, naming conventions, and architecture already in place.
2. **Follow conventions exactly.** Match the style, structure, and patterns of the surrounding code — same discipline as `hosa-implementer`.
3. **Implement exactly the task.** Build what the task describes. No unrelated refactor, no unrequested feature.
4. **Stay inside the placement you were given.** Never add a module, layer, entity, or field outside what `hosa-architect`/`hosa-data-engineer` already scaffolded. **If the task genuinely needs one to be correct — don't improvise a workaround: stop this task and report the deviation** exactly like `hosa-tech-lead` does (what's missing, why).
5. **No comments explaining what code does.** Only add one when the WHY is non-obvious: a hidden constraint, a specific workaround.
6. **No security vulnerabilities.** Never introduce SQL injection, XSS, command injection, path traversal, or other OWASP top-10 issues.

## No Commits

You never commit. The `develop` skill commits once, at the end of the ticket, after every task is done and the user has confirmed.

## Output Format

```
## Task Completed
[1-2 sentences]

## Files Changed
- `path` — [what changed and why]

## Structural Deviation
[If none: "None"]
[What's missing from the current structure to complete this task]

## Watch Out For
[Integration points, assumptions to validate — if none: "None"]
```

## Project Memory

Save and recall: code conventions discovered for this managed project, workarounds applied and why. Do NOT save: the task itself or its result — re-readable from the code.
```

- [ ] **Step 2: Verify the frontmatter and required sections are present**

Run: `grep -c "^name: hosa-developer$\|^model: claude-sonnet-5$\|^memory: project$" agents/developer.md`
Expected: `3`

Run: `grep -c "^## Input$\|^## Your Process$\|^## No Commits$\|^## Output Format$\|^## Project Memory$" agents/developer.md`
Expected: `5`

- [ ] **Step 3: Verify the Review Focus behavior is explicitly stated**

Run: `grep -c "don't improvise a workaround: stop this task and report the deviation" agents/developer.md`
Expected: at least `1`

- [ ] **Step 4: Add the agent to `agents/README.md`**

At the end of the Hosa agents table (after the `hosa-tech-lead` row added in Task 1), add:

```markdown
| [`hosa-developer`](developer.md) | claude-sonnet-5 | Implements a single task from `hosa-tech-lead`'s plan, in a short focused session — stays inside the architecture/data structures already scaffolded, and stops rather than improvising a workaround if a task needs one extended. |
```

- [ ] **Step 5: Verify the README edit**

Run: `grep -c "hosa-developer" agents/README.md`
Expected: at least `1`

- [ ] **Step 6: Commit**

```bash
git add agents/developer.md agents/README.md
git commit -m "feat: add hosa-developer agent, per-task ticket implementation"
```

---

### Task 3: Create the `develop` skill

**Files:**
- Create: `skills/develop/SKILL.md`

**Interfaces:**
- Consumes: `hosa-tech-lead`'s task-plan contract (Task 1) and `hosa-developer`'s task-result contract (Task 2), both via the `Agent` tool. Reads `kb/tickets/` and `kb/sprints/` directly for its own preconditions and logging.
- Produces: nothing new for other components to consume — this is the pipeline's terminal ticket-implementation step before `qa-plan`/`qa`.

- [ ] **Step 1: Write `skills/develop/SKILL.md`**

```markdown
---
name: develop
description: Use to implement a single sprint ticket — breaks it into short sequential tasks (`hosa-tech-lead`) and implements them one at a time (`hosa-developer`), strictly within the architecture and data structures already scaffolded. Never extends that structure itself; stops and reports if a ticket needs one. Follow-on to `git` Mode 1, precondition for `qa-plan`/`qa`.
---

# Develop

Implémente un ticket de sprint (`kb/tickets/<slug>.md`) dans le worktree déjà ouvert par `git` Mode 1 : découpage en tâches courtes et séquentielles (`hosa-tech-lead`), puis implémentation une tâche à la fois (`hosa-developer`) — jamais de déviation de la structure déjà scaffoldée par `hosa-architect`/`hosa-data-engineer` sans arrêt et remontée.

## Flow

```
Lit kb/tickets/<slug>.md et son kb/sprints/<slug-sprint>.md
        ↓ sprint pas active / pas de worktree → propose `git` Mode 1
          d'abord, stoppe
Écrit state: doing sur le ticket, log kb/tickets/log.md
        ↓
Dispatch hosa-tech-lead → plan de tâches séquentiel
        ↓ ambiguïté ou déviation → rapporte, propose de combler le
          manque (utilisateur, `architecture`/`schema-app`/`schema-db`,
          ou hosa-architect/hosa-data-engineer directement), stoppe
        ↓ plan clair
Pour chaque tâche, dans l'ordre : dispatch hosa-developer (une à la fois)
        ↓ déviation détectée en cours de tâche → même arrêt/rapport,
          stoppe la boucle
        ↓ toutes les tâches faites
Présente le travail cumulé du ticket → confirmation explicite (pas de QCM)
        ↓ oui
git add (fichiers du ticket) + commit unique, identité utilisateur
        ↓
Log kb/tickets/log.md
        ↓
Suite : propose hosa-product-owner (validation) et/ou qa-plan
```

## Trigger

Manual: `/develop <slug-ticket>`. Auto: "développe le ticket X", "implémente le ticket X" ; proposé en Suite de `git` Mode 1 et de `sprint`.

---

## Step 1: Read the Ticket and Sprint

Lit `kb/tickets/<slug>.md`. Lit son champ `sprint`, puis `kb/sprints/<slug-sprint>.md` : **si le champ `sprint` est absent, si `state` n'est pas `active`, ou si `worktree` est absent, le dit et propose `git` Mode 1 — stoppe, ne travaille jamais sur la branche de base.**

## Step 2: Mark In Progress

Écrit `state: doing` sur le ticket (sans effet si déjà `doing`). Log `kb/tickets/log.md`.

## Step 3: Break Down

Dispatch `hosa-tech-lead` avec le slug du ticket. Si sa sortie contient une entrée sous `Ambiguities` ou `Structural Deviation` : rapporte-la telle quelle à l'utilisateur, propose la suite adaptée — combler l'ambiguïté avec l'utilisateur, ou lancer `architecture`/`schema-app`/`schema-db` (ou dispatcher `hosa-architect`/`hosa-data-engineer` directement) pour la déviation — ne dispatche aucune tâche, stoppe. Le ticket reste `state: doing`.

## Step 4: Implement Sequentially

Pour chaque tâche du plan, dans l'ordre : dispatch `hosa-developer` avec la tâche, sa contrainte de placement, le chemin du worktree. **Une seule tâche à la fois — jamais de dispatch concurrent.** Si une tâche revient avec `Structural Deviation` non vide : **arrête la boucle immédiatement (les tâches restantes ne sont pas tentées)**, rapporte à l'utilisateur avec la même proposition qu'à l'étape 3, stoppe. Le ticket reste `state: doing`, aucun commit.

## Step 5: Present and Confirm

Une fois toutes les tâches faites : présente les fichiers modifiés (cumulés sur le ticket), les décisions clés, les hypothèses. Demande une confirmation explicite — pas de QCM (le ticket est déjà cadré par sa story, sa note technique et ses placements ; le garde-fou structurel a déjà tourné tâche par tâche). **Si l'utilisateur rejette ou corrige : renvoie le feedback à `hosa-developer` pour la tâche concernée uniquement, reprend l'étape 4 pour cette tâche seule — pas de redémarrage du ticket entier, pas de commit sur la version rejetée.**

## Step 6: Commit

```bash
git status
git add <uniquement les fichiers modifiés pour ce ticket>
git commit -m "feat: <description impérative du ticket, ≤72 caractères>"
```

Un seul commit pour tout le ticket. Aucun `Co-Authored-By`, aucun auteur additionnel — identité git de l'utilisateur uniquement.

## Step 7: Log

Log `kb/tickets/log.md` — chronologique, plus récent en premier, OKF §9.

## Commits

Ce skill est le seul point qui committe pour ce flow — jamais `hosa-tech-lead`/`hosa-developer` eux-mêmes — toujours sous l'identité git de l'utilisateur, jamais de co-auteur.

## Output

```
## Ticket <slug> implémenté
- Tâches réalisées : [n]
- Fichiers modifiés : [liste]

## Blocage (si applicable)
[Ambiguïté ou déviation structurelle, et ce qui est proposé pour la lever]

## Suite
Je lance la validation du ticket par hosa-product-owner (state: done) et/ou qa-plan maintenant ?
```
```

- [ ] **Step 2: Verify the frontmatter and trigger text**

Run: `grep -c "^name: develop$" skills/develop/SKILL.md`
Expected: `1`

Run: `grep -c "Manual: \`/develop <slug-ticket>\`" skills/develop/SKILL.md`
Expected: `1`

- [ ] **Step 3: Verify the skill dispatches rather than embeds logic**

Run: `grep -c "Dispatch \`hosa-tech-lead\`" skills/develop/SKILL.md`
Expected: at least `1`

Run: `grep -c "dispatch \`hosa-developer\`" skills/develop/SKILL.md`
Expected: at least `1`

- [ ] **Step 4: Verify the Review Focus behaviors are explicitly stated**

Run: `grep -c "stoppe, ne travaille jamais sur la branche de base" skills/develop/SKILL.md`
Expected: at least `1`

Run: `grep -c "les tâches restantes ne sont pas tentées" skills/develop/SKILL.md`
Expected: at least `1`

Run: `grep -c "pas de redémarrage du ticket entier, pas de commit sur la version rejetée" skills/develop/SKILL.md`
Expected: at least `1`

- [ ] **Step 5: Commit**

```bash
git add skills/develop/SKILL.md
git commit -m "feat: add develop skill, per-ticket task breakdown and implementation"
```

---

### Task 4: Wire hand-off into `git`/`sprint`, register `develop` in `using-hosa`

**Files:**
- Modify: `agents/git.md`
- Modify: `skills/sprint/SKILL.md`
- Modify: `skills/using-hosa/SKILL.md`

**Interfaces:**
- Consumes: the `develop` skill's identity and purpose (Task 3).
- Produces: `develop` discoverable via `using-hosa`'s tables, `git` Mode 1's report and `sprint`'s Suite each pointing at it as the natural next step.

- [ ] **Step 1: Point `hosa-git` Mode 1's report at `develop`**

In `agents/git.md`, replace:

```
6. Report the branch and worktree path — ticket work (via `build`/`iterate`/`test`/`debug`) should now happen inside it.
```

with:

```
6. Report the branch and worktree path — ticket work should now happen inside it, one ticket at a time, via the `develop` skill.
```

- [ ] **Step 2: Verify the `agents/git.md` edit**

Run: `grep -c "via the \`develop\` skill" agents/git.md`
Expected: `1`

Run: `grep -c "build\`/\`iterate\`/\`test\`/\`debug\`" agents/git.md`
Expected: `0`

- [ ] **Step 3: Add the hand-off line to `sprint`'s Suite**

In `skills/sprint/SKILL.md`, in the Output block's `## Suite` section, replace:

```
Sprint prêt. Je démarre le sprint maintenant (ouvre la branche/worktree dédiée — skill `git`) ? Sinon, je lance un autre sprint pour le reste du backlog, je lance `qa-plan` pour préparer les tests de ce sprint, ou on s'arrête là ?
```

with:

```
Sprint prêt. Je démarre le sprint maintenant (ouvre la branche/worktree dédiée — skill `git`) ? Une fois démarré, je peux lancer `develop` sur son premier ticket. Sinon, je lance un autre sprint pour le reste du backlog, je lance `qa-plan` pour préparer les tests de ce sprint, ou on s'arrête là ?
```

- [ ] **Step 4: Verify the `sprint` edit**

Run: `grep -c "je peux lancer \`develop\` sur son premier ticket" skills/sprint/SKILL.md`
Expected: `1`

- [ ] **Step 5: Register `develop` in `using-hosa`'s skills table**

In `skills/using-hosa/SKILL.md`, in the skills table, after the `git` row, add:

```markdown
| `develop` | Implement a single sprint ticket — break it into short sequential tasks (`hosa-tech-lead`) and implement them one at a time (`hosa-developer`), strictly within the architecture and data structures already scaffolded. Follow-on to `git` Mode 1, precondition for `qa-plan`/`qa` |
```

- [ ] **Step 6: Register `develop` in `using-hosa`'s triggers table**

In `skills/using-hosa/SKILL.md`, in the triggers table, after the `git` (Mode 2) trigger row, add:

```markdown
| "Développe le ticket X", "Implémente le ticket X" | `develop` |
```

- [ ] **Step 7: Verify the `using-hosa` edits**

Run: `grep -c "^| \`develop\` |" skills/using-hosa/SKILL.md`
Expected: `1`

Run: `grep -c "\`develop\`$" skills/using-hosa/SKILL.md`
Expected: at least `1`

- [ ] **Step 8: Commit**

```bash
git add agents/git.md skills/sprint/SKILL.md skills/using-hosa/SKILL.md
git commit -m "feat: sprint/git dispatch develop, register develop skill"
```

---

### Task 5: Cross-file consistency verification

**Files:** none created or modified — this task only reads and checks.

**Interfaces:**
- Consumes: every artifact from Tasks 1-4.
- Produces: nothing — a clean pass here is the plan's completion signal.

- [ ] **Step 1: Confirm each new agent name is consistent everywhere it's referenced**

Run: `grep -c "hosa-tech-lead" agents/tech-lead.md agents/README.md skills/develop/SKILL.md`
Expected: at least `1` in each of the three files.

Run: `grep -c "hosa-developer" agents/developer.md agents/README.md skills/develop/SKILL.md`
Expected: at least `1` in each of the three files.

- [ ] **Step 2: Confirm no other agent file was modified beyond the three expected**

Run: `git diff --stat -- agents/ | grep -v "tech-lead.md\|developer.md\|git.md\|README.md"`
Expected: no output (empty).

- [ ] **Step 3: Confirm no other skill file was modified beyond the three expected**

Run: `git diff --stat -- skills/ | grep -v "develop/SKILL.md\|sprint/SKILL.md\|using-hosa/SKILL.md"`
Expected: no output (empty).

- [ ] **Step 4: Confirm no new pipeline stage numbering was introduced**

Run: `grep -rn "stage of the data-structuring pipeline" skills/*/SKILL.md`
Expected: unchanged from before this plan (`stack`=stage 1 ... `backlog`=stage 8) — `develop` must not appear in this list.

- [ ] **Step 5: Confirm the escalation path is stop-and-report everywhere, never a silent agent-to-agent dispatch**

Run: `grep -n "dispatche lui-même\|dispatches hosa-architect\|dispatches hosa-data-engineer" agents/tech-lead.md agents/developer.md skills/develop/SKILL.md`
Expected: no output (empty) — confirms neither agent nor the skill self-dispatches the architecture/data roles; escalation always names the user/skill options instead.

- [ ] **Step 6: Confirm `develop` never writes `state: done`**

Run: `grep -n "state: done" skills/develop/SKILL.md`
Expected: no output (empty).

- [ ] **Step 7: Confirm no plan placeholder text leaked into the written files**

Run: `grep -rn "TBD\|TODO\|<fill" agents/tech-lead.md agents/developer.md skills/develop/SKILL.md`
Expected: no output (empty).

- [ ] **Step 8: Report and stop**

No commit for this task — it's a read-only check. If every step above matched its Expected value, the plan is complete; report that to the user. If any step didn't match, that's a plan or content defect: rule on it per this plan's Global Constraints and the spec, fix the affected file, and re-run the failing step's command before reporting completion.
