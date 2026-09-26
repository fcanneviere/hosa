# Hosa Backlog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `backlog` skill — sixth and last stage of the data-structuring pipeline — that turns every `stable` `kb/cdc/` `Exigence` without a ticket yet into a `Ticket` enriched with three views: the user story (PO), a technical feasibility note (senior dev), and an architecture placement note (architect). No new agents; the skill embeds these three roles inline, same as `stack`/`architecture` already do.

**Architecture:** Markdown prompt-artifact repo (skills in `skills/`) — no application code, no test runner. "Tests" for this plan are structural verifications (frontmatter present, cross-references resolve, required sections exist) run via Grep/Bash, not unit tests.

**Tech Stack:** Markdown (YAML frontmatter + prose), Claude Code skill conventions already established in this repo.

**Spec:** `docs/superpowers/specs/2026-09-25-hosa-backlog-design.md`

## Global Constraints

- No new OKF concept type — `kb/tickets/`/`Ticket.state` is already the Product Backlog and its status.
- No skill in this plan commits — ends with "Report what changed, let the user/orchestrating flow decide" (matches every other Hosa skill).
- `backlog` never overwrites a `Ticket` already linked to an `Exigence` — a rerun only fills gaps, never duplicates or clobbers.
- OKF logging convention: append to the bundle's `log.md` (create if missing), chronological, most recent entry first, per OKF §9.
- Git commits in this plan use the repo's existing convention: plain commit, user's configured `git config user.name`/`user.email` only, no co-author trailer.
- New pipeline order everywhere it's referenced: `stack → donnees → schema-app → schema-db → architecture → backlog`.

## Review Focus

1. `backlog` invoked before `stack` ever ran (no `Stack Decision` in `kb/stack/`) — Task 1 Step 1's technical-note logic must degrade to a one-line note, not block ticket creation.
2. `backlog` invoked before `architecture` ever ran (no doc path in the `Infra` entry) — Task 1 Step 1's placement-note logic must degrade the same way, independently of Review Focus #1.
3. `backlog` re-run after some tickets already exist — Task 1 Step 1's scoping must skip any `Exigence` already linked from an existing `Ticket`, not recreate or duplicate it.
4. `backlog` invoked with zero `stable` `Exigence`s lacking a ticket (fully covered backlog, or no stable Exigences at all) — Task 1 Step 1 must say so and stop, producing no file writes.
5. `architecture`'s output no longer ends the pipeline — Task 2 must remove "Pipeline de structuration des données terminé." from `architecture` entirely (it now belongs only to `backlog`), verified by Task 2 Step 2.

---

### Task 1: `backlog` skill

**Files:**
- Create: `skills/backlog/SKILL.md`

**Interfaces:**
- Consumes: `stable` `Exigence` concepts in `kb/cdc/`, `Stack Decision` concepts in `kb/stack/` (optional), the architecture doc path recorded in the `Infra` entry in `kb/infra/` (optional), existing `Ticket` concepts in `kb/tickets/`
- Produces: `Ticket` concepts in `kb/tickets/`, end of the data-structuring pipeline

- [ ] **Step 1: Write `skills/backlog/SKILL.md`**

```markdown
---
name: backlog
description: Use to turn every stable cahier des charges Exigence without a ticket yet into a Ticket enriched with a user story (PO), a technical feasibility note (senior dev), and an architecture placement note (architect). Sixth and last stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture → backlog).
---

# Backlog

Turns "what the application must do" (the stable cahier des charges) into Product Backlog tickets — each one carrying the business story, its technical feasibility, and where it lands in the architecture, so nothing enters `kb/tickets/` disconnected from the technical reality already decided by `stack` and `architecture`.

## Flow

```
Pour chaque Exigence stable de kb/cdc/ sans Ticket lié :
        ↓
Écrit la story (rôle PO) dans un nouveau Ticket, state: todo
        ↓
Ajoute une note technique (rôle senior dev), ou une ligne
"pas encore évalué" si aucune Stack Decision n'existe
        ↓
Ajoute un placement architecture (rôle architecte), ou une
ligne "pas encore déterminé" si aucune doc d'architecture
n'existe
        ↓
Log kb/tickets/log.md
        ↓
Pipeline de structuration des données terminé
```

## Trigger

Manual: `/backlog`. Auto: immediately after `architecture`, or "crée le product backlog", "génère les tickets à partir du cahier des charges".

---

## Step 1: Scope

Read every `stable` `Exigence` in `kb/cdc/`. For each one, check every existing `Ticket` in `kb/tickets/` for a markdown link pointing back to that `Exigence`'s file — if one already links to it, skip it; a re-run of `backlog` only fills gaps, it never recreates or overwrites a ticket. If every `stable` `Exigence` already has a linked ticket (or there are no `stable` `Exigence`s at all), say so and stop — nothing to write.

## Step 2: Write the Story (PO role)

For each `Exigence` left after Step 1, write a new `Ticket` to `kb/tickets/<slug>.md`, `state: todo`:

```markdown
---
type: Ticket
title: <titre>
description: <description courte>
tags: []
state: todo
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
En tant que [persona],
je veux [besoin],
afin de [valeur].

Lié à : [persona](../personnas/xxx.md), [exigence](../cdc/xxx.md)
```

If the `Exigence` names no clear persona, ask the user which persona it serves before writing the story — same "no guessing" discipline as every other Hosa skill.

## Step 3: Add the Technical Note (senior dev role)

Read `kb/stack/` for `Stack Decision` concepts. If at least one exists, append to the ticket just written:

```markdown
## Note technique (senior dev)
[Faisabilité/complexité au regard de la stack retenue, et pourquoi]
```

If `kb/stack/` has no `Stack Decision` yet (this skill invoked standalone, before `stack` ran), append instead:

```markdown
## Note technique (senior dev)
Stack pas encore choisie — faisabilité non évaluée.
```

Never block ticket creation on a missing `Stack Decision`.

## Step 4: Add the Architecture Placement (architect role)

Read `kb/infra/` for the `Infra` entry's architecture documentation path (written by `architecture`). If one is recorded, read it and append to the ticket:

```markdown
## Placement architecture (architecte)
[Module/couche concerné, et pourquoi]
```

If no architecture documentation path is recorded yet (this skill invoked standalone, before `architecture` ran), append instead:

```markdown
## Placement architecture (architecte)
Architecture pas encore scaffoldée — placement non déterminé.
```

Never block ticket creation on a missing architecture doc.

## Step 5: Log

Log each ticket created to `kb/tickets/log.md` (create if missing) — chronological, most recent date first, per OKF §9.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit.

## Output

```
## Tickets créés
- `kb/tickets/<slug>.md` — [titre] (state: todo)

## Suite
Pipeline de structuration des données terminé.
```
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "^name: backlog$" skills/backlog/SKILL.md` — Expected: `1`
Run: `grep -c "Stack pas encore choisie" skills/backlog/SKILL.md` — Expected: `1`
Run: `grep -c "Architecture pas encore scaffoldée" skills/backlog/SKILL.md` — Expected: `1`
Run: `grep -c "never recreates or overwrites\|only fills gaps" skills/backlog/SKILL.md` — Expected: at least `1`
Run: `grep -c "You don't commit" skills/backlog/SKILL.md` — Expected: `1`

- [ ] **Step 3: Commit**

```bash
git add skills/backlog/SKILL.md
git commit -m "feat: add backlog skill, data-structuring pipeline stage 6"
```

---

### Task 2: Update `architecture` to chain into `backlog` instead of ending the pipeline

**Files:**
- Modify: `skills/architecture/SKILL.md`

**Interfaces:**
- Consumes: `backlog` skill name (Task 1)
- Produces: none new — reuses the existing scaffolding/documentation output, now proposes `backlog` as its next step instead of ending the pipeline.

- [ ] **Step 1: Update the frontmatter description**

Find:

```markdown
description: Use to design and scaffold the software architecture of the project Hosa manages, consistent with the stable cahier des charges, the chosen stack, and the data structures already written by `schema-app`/`schema-db`. Fifth and last stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture).
```

Replace with:

```markdown
description: Use to design and scaffold the software architecture of the project Hosa manages, consistent with the stable cahier des charges, the chosen stack, and the data structures already written by `schema-app`/`schema-db`. Fifth stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture → backlog).
```

- [ ] **Step 2: Update the Output's "Suite" section**

Find:

```markdown
## Output

```
## Architecture conçue
[Couches/modules retenus et pourquoi]

## Structures créées
- `<path>` — [module/dossier scaffoldé]

## Documentation
- `<path>`

## Suite
Pipeline de structuration des données terminé.
```
```

Replace with:

```markdown
## Output

```
## Architecture conçue
[Couches/modules retenus et pourquoi]

## Structures créées
- `<path>` — [module/dossier scaffoldé]

## Documentation
- `<path>`

## Suite
Je lance `backlog` maintenant ?
```
```

- [ ] **Step 3: Verify structure**

Run: `grep -c "Je lance \`backlog\` maintenant" skills/architecture/SKILL.md` — Expected: `1`
Run: `grep -c "Pipeline de structuration des données terminé" skills/architecture/SKILL.md` — Expected: `0`
Run: `grep -c "Fifth stage" skills/architecture/SKILL.md` — Expected: `1`

- [ ] **Step 4: Commit**

```bash
git add skills/architecture/SKILL.md
git commit -m "feat: chain architecture into backlog instead of ending the pipeline"
```

---

### Task 3: Register `backlog` in `using-simflow`

**Files:**
- Modify: `skills/using-simflow/SKILL.md`

**Interfaces:**
- Consumes: skill name `backlog` (Task 1)
- Produces: none new — discoverability wiring only.

- [ ] **Step 1: Add a row to the skills table**

Find:

```markdown
| `architecture` | Design and scaffold the software architecture of the managed project, consistent with the CDC, the stack, and the data structures — data-structuring pipeline stage 5 |
```

Replace with:

```markdown
| `architecture` | Design and scaffold the software architecture of the managed project, consistent with the CDC, the stack, and the data structures — data-structuring pipeline stage 5 |
| `backlog` | Turn every stable cahier des charges Exigence without a ticket yet into a Product Backlog Ticket carrying the story, a technical feasibility note, and an architecture placement note — data-structuring pipeline stage 6 |
```

- [ ] **Step 2: Add a row to the triggers table**

Find:

```markdown
| "Crée l'architecture logicielle", "Génère l'architecture de l'application" | `architecture` |
```

Replace with:

```markdown
| "Crée l'architecture logicielle", "Génère l'architecture de l'application" | `architecture` |
| "Crée le product backlog", "Génère les tickets à partir du cahier des charges" | `backlog` |
```

- [ ] **Step 3: Verify structure**

Run: `grep -c "^| \`backlog\`" skills/using-simflow/SKILL.md` — Expected: `2` (1 row in the skills table + 1 row in the triggers table)

- [ ] **Step 4: Commit**

```bash
git add skills/using-simflow/SKILL.md
git commit -m "docs: register backlog skill in using-simflow"
```

---

### Task 4: Cross-file consistency pass

**Files:**
- None created or modified — read-only verification across Tasks 1-3.

**Interfaces:**
- Consumes: every file touched by Tasks 1-3
- Produces: nothing — this task either passes or sends work back to the relevant earlier task.

- [ ] **Step 1: The pipeline chain is unbroken end to end**

Run: `grep -l "backlog" skills/architecture/SKILL.md`
Expected: `skills/architecture/SKILL.md` listed

Run: `grep -c "Pipeline de structuration des données terminé" skills/backlog/SKILL.md`
Expected: `1` (moved here from `architecture`, not duplicated)

- [ ] **Step 2: `using-simflow` entry matches the actual file name**

Run: `ls skills/ | grep -E "^backlog$"`
Expected: `backlog` listed

- [ ] **Step 3: `backlog` doesn't commit**

Run: `grep -c "You don't commit" skills/backlog/SKILL.md`
Expected: `1`

- [ ] **Step 4: No new OKF concept type introduced**

Run: `grep -c "type: Ticket" skills/backlog/SKILL.md`
Expected: at least `1` (confirms it writes the existing `Ticket` type, not a new one)

If any check in Steps 1-4 fails, fix the specific file it points to (go back to that file's task) rather than patching around it here.

- [ ] **Step 5: No commit needed** — this task is verification-only; nothing changed.

---

## Self-Review Notes

- **Spec coverage:** "Le Product Backlog reste `kb/tickets/`" → no task needed, confirmed as a constraint, not a file change. Skill `skills/backlog/SKILL.md` (Steps 1-4 of the spec) → Task 1. "Modification à `architecture`" → Task 2. "Registre dans `using-simflow`" → Task 3. "Hors scope (v1)" → deliberately no task (no drift-detection, no auto-splitting, no auto-prioritization).
- **Placeholder scan:** no TBD/TODO; `skills/backlog/SKILL.md`'s content above is complete, not a description of content.
- **Type consistency:** `Ticket` frontmatter shape in Task 1 matches the pre-existing shape already used by `hosa-product-owner` and `hosa/kb/tickets/exemple-ticket.md`, unchanged. Skill name `backlog` used identically across all three tasks.
- **Review Focus:** all 5 items map to a specific instruction inside a specific task (see numbered list above) — none left uncovered.
