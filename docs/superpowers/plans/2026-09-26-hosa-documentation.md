# Hosa Documentation (Technical + Functional Docs Agent) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new agent, `hosa-documentation`, that is the sole owner of writing and maintaining technical documentation (installation, architecture, data dictionary) and functional documentation (per-persona guides derived from the stable cahier des charges) for the project Hosa manages. `hosa-infra`, `hosa-architect`, and `hosa-data-engineer` stop writing their own doc file and dispatch it instead; the `contestation` skill dispatches it once an `Exigence` is validated `stable`. A companion `documentation` skill lets it re-check every tracked section for drift on demand.

**Architecture:** One new agent (`agents/documentation.md`) with two input modes (Mode 1 — hot update, dispatched by a producer the moment something documentable changes; Mode 2 — cold check, dispatched by the new `documentation` skill). A new OKF concept type `Documentation` in a new `kb/documentation/` bundle tracks, per doc section, its path in the managed project and the sources it derives from, so Mode 2 can detect drift by comparing dates. `hosa-documentation` is not a numbered pipeline stage — it's a transversal agent, same status as `hosa-infra`'s Mode 2 or `qualite`/`fondamentaux`.

**Tech Stack:** Markdown agent/skill files (Claude Code plugin conventions), no code/tests — this repo's "implementation" is markdown content, verified by grep/read checks, same as the `infra`/`sprint`/`interface`/`qa` plans.

**Spec:** `docs/superpowers/specs/2026-09-26-hosa-documentation-design.md`

## Global Constraints

- New agent frontmatter: `name: hosa-documentation`, `model: claude-opus-4-8`, `memory: project`.
- New OKF concept type `Documentation`, new bundle `kb/documentation/`. Every entry carries `path` (file in the managed project) and `sources` (list of what it derives from) in its frontmatter, plus the standard `generated: { by, at }`.
- File layout in the managed project: `docs/technique/installation.md`, `docs/technique/architecture.md`, `docs/technique/donnees.md`, `docs/fonctionnel/apercu.md`, `docs/fonctionnel/<persona-slug>.md`. Matching `kb/documentation/` entries are named `technique-installation.md`, `technique-architecture.md`, `technique-donnees.md`, `fonctionnel-apercu.md`, `fonctionnel-<persona-slug>.md`.
- `hosa-documentation` never writes into `hosa/app` or `hosa/kb` themselves — same rule as every other Hosa agent.
- Every one of the four dispatch points (`hosa-infra`, `hosa-architect`, `hosa-data-engineer`, `contestation`) waits for `hosa-documentation`'s confirmation before considering its own task finished — same discipline as the existing relationship with `hosa-infra`.
- `hosa-documentation` never writes an empty doc section when it has nothing to document yet (no `Infra`/`Stack Decision`/`stable` `Exigence`) — it says so instead.
- No agent/skill in this plan commits, except the plan's own commit steps (in the user's name only — `git config user.name`/`user.email`, never Co-Authored-By, never additional authors — this overrides any global default attribution instruction for this repo's work).
- OKF §9 logging (chronological, most recent date first) to `kb/documentation/log.md` for every write `hosa-documentation` makes.
- No renumbering of the data-structuring pipeline — `hosa-documentation` is explicitly not a stage in it.

## Review Focus

- **Mode 2 (cold check) runs before any section has ever been written.** A reasonable person expects it to say "nothing to check yet" rather than error or fabricate a section. Task 1's Mode 2 steps and Task 2's skill flow must both state this explicitly.
- **A producer dispatches Mode 1 for a section that already has a `kb/documentation/` entry.** A reasonable person expects an update in place, never a duplicate file or a second registry entry for the same section. Task 1's Mode 1 steps must state this explicitly.
- **`hosa-infra`'s Mode 2 (on-demand installation) still needs to write `kb/infra/<slug-service>.md`, which is Hosa's own internal registry, separate from the managed-project-facing installation doc it no longer writes itself.** A reasonable person expects both writes to still happen — the internal `Infra` record and the dispatch to `hosa-documentation` — not one replacing the other. Task 3's `hosa-infra` edit must keep the `kb/infra/<slug-service>.md` write intact alongside the new dispatch.
- **`contestation`'s Step 4 validates zero `Exigence`s (user asks for changes instead).** A reasonable person expects no dispatch to `hosa-documentation` in that case — only a validated `stable` transition triggers it. Task 4's `contestation` edit must make the dispatch conditional on at least one `Exigence` actually reaching `stable`.
- **A source recorded in a `Documentation` entry's `sources` list has no readable date** (e.g. a hand-edited file with no log entry). A reasonable person expects the cold check to not silently treat this as "up to date" without saying so. Task 1's Mode 2 and Edge Cases sections must state that undetectable drift outside the two mechanisms is an accepted v1 limit, not silently assumed clean.

---

### Task 1: Create the `hosa-documentation` agent

**Files:**
- Create: `agents/documentation.md`
- Modify: `agents/README.md` (add one row to the Hosa agents table, at the end)

**Interfaces:**
- Consumes: `kb/documentation/` (`Documentation` — sections already written, sources, sync dates), `kb/infra/` (`Infra`), `kb/stack/` (`Stack Decision`), `kb/cdc/` (`Exigence`, `stable` only), `kb/personnas/` (`Persona`). Also reads directly, in the managed project, whatever `hosa-architect`/`hosa-data-engineer` scaffolded/derived, via paths given in the Mode 1 dispatch.
- Produces: `docs/technique/*.md` and `docs/fonctionnel/*.md` in the managed project, `hosa/kb/documentation/<slug>.md` entries, `kb/documentation/log.md` entries. Output format consumed by the four dispatch points (Task 3, Task 4) and by `skills/documentation/SKILL.md` (Task 2).

- [ ] **Step 1: Write `agents/documentation.md`**

```markdown
---
name: hosa-documentation
description: Use this agent as the sole owner of writing and maintaining technical and functional documentation for the project Hosa manages. It writes the documentation `hosa-infra` (installation), `hosa-architect` (architecture), and `hosa-data-engineer` (data dictionary) used to write themselves — they dispatch it instead — and is the sole owner of functional documentation derived from the stable cahier des charges and personas. Kept in sync via hot dispatch from its four producers, and a cold on-demand check via the `documentation` skill. Invoke it directly, or from the `documentation` skill.
model: claude-opus-4-8
memory: project
---

You are the documentation owner for the project Hosa manages. No other agent writes documentation into the managed project directly — `hosa-infra`, `hosa-architect`, and `hosa-data-engineer` dispatch you instead of writing their own doc file, and the cahier des charges pipeline (`contestation`) dispatches you once an `Exigence` is validated `stable`. The project you're accountable for is the one Hosa manages — never `hosa/app` or `hosa/kb` themselves, which are Hosa's own tooling and out of your scope.

## Input

You receive one of:
- **A Mode 1 request (hot update)** — a producer (`hosa-infra`, `hosa-architect`, `hosa-data-engineer`, or the `contestation` skill) just changed something documentable and dispatches you with what changed and the paths concerned
- **A Mode 2 request (cold check)** — the `documentation` skill dispatches you to re-check every section already tracked for drift

If neither is clear from the request, ask which mode you're operating in before acting.

## Knowledge Base

| Bundle | Type | What you use it for |
|---|---|---|
| `kb/documentation/` | `Documentation` | The register of sections already written, their sources, and their last-synced date |
| `kb/infra/` | `Infra` | The managed project's root path; content of the technical installation doc |
| `kb/stack/` | `Stack Decision` | Content of the technical stack doc |
| `kb/cdc/` | `Exigence` | Content of the functional doc — only `stable` Exigences |
| `kb/personnas/` | `Persona` | One functional guide per persona |

You also read directly, in the managed project, what `hosa-architect` scaffolded and what `hosa-data-engineer` derived (paths given in the dispatch, or already recorded in `kb/documentation/`) — you document a decision already made elsewhere, you never re-derive it.

**Frontmatter you must fill correctly on every concept you write:**
- `generated: { by: human:<user>, at: <ISO8601> }` — the user dictated something explicitly (e.g. wording requested for a guide)
- `generated: { by: hosa-documentation/1.0, at: <ISO8601> }` — you wrote it yourself from the sources

**Logging:** append an entry to `kb/documentation/log.md` (create if missing) — chronological, most recent date first, per OKF §9.

## File Layout in the Managed Project

- `docs/technique/installation.md`, `docs/technique/architecture.md`, `docs/technique/donnees.md`
- `docs/fonctionnel/apercu.md` (overview, all personas) + `docs/fonctionnel/<persona-slug>.md` (one guide per persona)

Each file has a matching `kb/documentation/` entry, named `technique-installation.md`, `technique-architecture.md`, `technique-donnees.md`, `fonctionnel-apercu.md`, `fonctionnel-<persona-slug>.md` — same slug as the file it describes, prefixed by its category.

## `Documentation` Entry Template

Every `kb/documentation/<slug>.md` you write or update follows this shape:

```markdown
---
type: Documentation
title: <section> — <projet>
description: <une ligne>
tags: []
status: stable
path: <chemin du fichier dans le projet géré>
sources:
  - <chemin ou slug de la source : entrée kb/infra, kb/stack, kb/cdc, ou code du projet géré>
generated: { by: hosa-documentation/1.0, at: <ISO8601> }
---
## Contenu
<résumé de ce que documente cette section>

## Sources
- <source> (dernière modification connue : <ISO8601 ou référence log>)
```

## Mode 1 — Hot Update (dispatched by a producer)

Input: the producer (`hosa-infra`/`hosa-architect`/`hosa-data-engineer`/`contestation`), what changed, and the paths concerned.

1. Determine which technical or functional section is concerned (installation, architecture, données, or one/several persona guide(s)).
2. Read `kb/documentation/` for that section's existing entry, if any — never a duplicate, always an update in place.
3. Write or update the file in the managed project (`docs/technique/<section>.md` or `docs/fonctionnel/<persona>.md`), matching the style already in place if any.
4. Write or update `kb/documentation/<slug>.md` using the template above (refresh `path`, `sources`, and `generated.at`) and log the update.
5. Confirm back to the producer that the doc is in place — it does not consider its own task finished until this confirmation.

## Mode 2 — Cold Check (dispatched by the `documentation` skill)

1. Read every entry in `kb/documentation/`. None yet → say so; nothing to check until at least one section has been written.
2. For each entry, compare the date of each of its `sources` (the source bundle's latest log entry, or the `generated.at` of the concerned `Exigence`/`Stack Decision`/`Infra`) to the entry's own `generated.at`.
3. A source newer than the entry → refresh the section (same write as Mode 1, Steps 3-4). Source unchanged → nothing to do, list it as up to date.
4. Report, section by section, what was refreshed and what was already current.

## Edge Cases

- Nothing to document yet (no `Infra`/`Stack Decision`/`stable` `Exigence`) → say so, never write an empty section.
- A source changed without ever going through a hot dispatch (e.g. a file edited by hand in the managed project), or a source with no readable date to compare → only the cold check might catch it, and only if the date is readable; you don't guarantee real-time or complete sync outside these two mechanisms — an accepted limit, not a bug. Say so rather than reporting a section as "up to date" when its drift is simply undetectable.

## No Commits

You do not commit. Report what changed and let the user or the orchestrating skill decide when to commit.

## Output Format

```
## Documentation mise à jour (Mode 1)
- Section : technique/installation | technique/architecture | technique/donnees | fonctionnel/<persona>
- Fichier : `<path>`
- Déclenché par : <agent/skill demandeur>

## Vérification (Mode 2)
- À jour : <section>, <section>
- Rafraîchie : <section> (source : <quoi>)
- [If no entry yet: "Rien à vérifier — aucune section écrite pour l'instant"]

## Registre
- `kb/documentation/<slug>.md`

## Open Questions
[Anything blocking a write/refresh decision — if none: "None"]
```

## Project Memory

Save and recall facts that compound across sessions:
- The managed project's existing documentation conventions (`docs/` layout, style), once discovered
- The section → producer mapping already established

Do NOT save: the content of a `Documentation` entry already written — re-readable from `kb/documentation/`.
```

- [ ] **Step 2: Verify the frontmatter and required sections are present**

Run: `grep -c "^name: hosa-documentation$\|^model: claude-opus-4-8$\|^memory: project$" agents/documentation.md`
Expected: `3`

Run: `grep -c "^## Knowledge Base$\|^## File Layout in the Managed Project$\|^## \`Documentation\` Entry Template$\|^## Mode 1 — Hot Update\|^## Mode 2 — Cold Check\|^## Edge Cases$\|^## No Commits$\|^## Output Format$\|^## Project Memory$" agents/documentation.md`
Expected: `9`

- [ ] **Step 3: Verify the Review Focus behaviors are explicitly stated**

Run: `grep -c "nothing to check until at least one section has been written" agents/documentation.md`
Expected: at least `1`

Run: `grep -c "never a duplicate, always an update in place" agents/documentation.md`
Expected: at least `1`

Run: `grep -c "you don't guarantee real-time or complete sync outside these two mechanisms" agents/documentation.md`
Expected: at least `1`

- [ ] **Step 4: Add the agent to `agents/README.md`**

At the end of the Hosa agents table, add:

```markdown
| [`hosa-documentation`](documentation.md) | claude-opus-4-8 | Sole owner of technical and functional documentation for the project Hosa manages — writes and keeps in sync the installation, architecture, and data-dictionary docs on behalf of `hosa-infra`/`hosa-architect`/`hosa-data-engineer`, and owns the functional guides derived from the stable cahier des charges and personas. |
```

- [ ] **Step 5: Verify the README edit**

Run: `grep -c "hosa-documentation" agents/README.md`
Expected: at least `1`

- [ ] **Step 6: Commit**

```bash
git add agents/documentation.md agents/README.md
git commit -m "feat: add hosa-documentation agent, sole owner of managed-project docs"
```

---

### Task 2: Create the `documentation` skill

**Files:**
- Create: `skills/documentation/SKILL.md`

**Interfaces:**
- Consumes: `kb/infra/` (root path) — same contract as `qualite` Step 1. Dispatches `hosa-documentation` (Task 1) in Mode 2 via the `Agent` tool (this skill does not embed the cold-check logic inline, since it's the agent's own responsibility, matching how `qualite` dispatches `hosa-senior-dev` rather than embedding its checklist).
- Produces: nothing of its own — reports `hosa-documentation`'s Mode 2 output.

- [ ] **Step 1: Write `skills/documentation/SKILL.md`**

```markdown
---
name: documentation
description: Use to check whether the managed project's technical and functional documentation is in sync with its sources, and refresh whatever has drifted. Companion check usable anytime, not a forced pipeline stage — dispatches `hosa-documentation` in cold-check mode.
---

# Documentation

Cold-check pass over every documentation section `hosa-documentation` already owns — catches drift the hot-dispatch mechanism might have missed (e.g. a file edited by hand outside the agent flow).

## Flow

```
Lit kb/infra/ (chemin racine du projet géré)
        ↓
Dispatch hosa-documentation en Mode 2 (vérification à froid)
        ↓
Rapporte les sections rafraîchies et celles déjà à jour
```

## Trigger

Manual: `/documentation`. Auto: "vérifie que la documentation est à jour", "génère la documentation du projet", "documente le projet".

---

## Step 1: Find the Managed Project

Read `kb/infra/` for the managed project's root path (same as `stack`/`infra`/`qualite` Step 1). Missing → say so; `hosa-documentation` has nothing to check without a project to point at.

## Step 2: Dispatch the Cold Check

Dispatch `hosa-documentation` in Mode 2. It reads every `kb/documentation/` entry, compares each source's date to its own `generated.at`, and refreshes anything that's drifted. If no `kb/documentation/` entry exists yet, it says so — nothing to check until at least one section has been written by a Mode 1 dispatch.

## No Commits

You don't commit. Report what changed and let the user decide when to commit.

## Output

```
## Documentation
- À jour : <section>, <section>
- Rafraîchie : <section> (source : <quoi>)
- [Si aucune entrée encore : "Rien à vérifier — aucune section écrite pour l'instant"]

## Open Questions
[Si rien : "None"]
```
```

- [ ] **Step 2: Verify the frontmatter and trigger text**

Run: `grep -c "^name: documentation$" skills/documentation/SKILL.md`
Expected: `1`

Run: `grep -c "Manual: \`/documentation\`" skills/documentation/SKILL.md`
Expected: `1`

- [ ] **Step 3: Verify the no-entries-yet case is stated**

Run: `grep -c "nothing to check until at least one section has been written" skills/documentation/SKILL.md`
Expected: at least `1`

- [ ] **Step 4: Commit**

```bash
git add skills/documentation/SKILL.md
git commit -m "feat: add documentation skill, companion drift check"
```

---

### Task 3: Wire hot dispatch into `hosa-infra`, `hosa-architect`, `hosa-data-engineer`

**Files:**
- Modify: `agents/infra.md`
- Modify: `agents/architect.md`
- Modify: `agents/data-engineer.md`

**Interfaces:**
- Consumes: `hosa-documentation`'s Mode 1 contract from Task 1 (dispatched with "what changed and the paths concerned", returns a confirmation before the caller continues).
- Produces: nothing new — these three agents lose their own doc-writing step and gain a dispatch step in its place.

- [ ] **Step 1: Update `hosa-infra`'s Mode 1 (replace Step 8)**

In `agents/infra.md`, replace:

```
8. Write an installation document in the managed project (e.g. `docs/installation.md` or `INSTALL.md`): prerequisites, how to start/rebuild the environment, and how to request a future addition (point at `hosa-infra`).
```

with:

```
8. Dispatch `hosa-documentation` (Mode 1) with what was installed and the paths concerned (Dockerfile(s), compose file, services/versions) — it writes the installation documentation into the managed project. Wait for its confirmation before continuing to Step 9.
```

- [ ] **Step 2: Update `hosa-infra`'s Mode 2 (replace Step 4)**

In `agents/infra.md`, replace:

```
4. Update the managed project's installation document with the new piece, and write `hosa/kb/infra/<slug-service>.md`:

```markdown
---
type: Infra
title: <élément installé> — <projet>
description: <ce qui a été installé et pourquoi>
tags: []
status: stable
generated: { by: hosa-infra/1.0, at: <ISO8601> }
---
## Installé
<élément, version épinglée, date de vérification>

## Justification
<pourquoi, quel agent l'a demandé, quelle tâche en avait besoin>
```

Log the update.
```

with:

```
4. Dispatch `hosa-documentation` (Mode 1) with the new piece and the paths concerned — it updates the managed project's installation documentation. Wait for its confirmation, then write `hosa/kb/infra/<slug-service>.md`:

```markdown
---
type: Infra
title: <élément installé> — <projet>
description: <ce qui a été installé et pourquoi>
tags: []
status: stable
generated: { by: hosa-infra/1.0, at: <ISO8601> }
---
## Installé
<élément, version épinglée, date de vérification>

## Justification
<pourquoi, quel agent l'a demandé, quelle tâche en avait besoin>
```

Log the update.
```

- [ ] **Step 3: Verify the `hosa-infra` edits**

Run: `grep -c "Dispatch \`hosa-documentation\` (Mode 1)" agents/infra.md`
Expected: `2`

Run: `grep -c "Write an installation document in the managed project" agents/infra.md`
Expected: `0`

Run: `grep -c "write \`hosa/kb/infra/<slug-service>.md\`" agents/infra.md`
Expected: `1`

- [ ] **Step 4: Update `hosa-architect`'s process (replace Steps 5-6)**

In `agents/architect.md`, replace:

```
5. Write the architecture documentation in the managed project (never in `hosa/kb`).
6. Update the `Infra` entry with the documentation's path.
```

with:

```
5. Dispatch `hosa-documentation` (Mode 1) with the layers/modules chosen and the paths scaffolded — it writes the architecture documentation into the managed project. Wait for its confirmation before reporting.
```

- [ ] **Step 5: Verify the `hosa-architect` edit**

Run: `grep -c "Dispatch \`hosa-documentation\` (Mode 1)" agents/architect.md`
Expected: `1`

Run: `grep -c "Write the architecture documentation in the managed project" agents/architect.md`
Expected: `0`

- [ ] **Step 6: Update `hosa-data-engineer`'s "Application data structure" responsibility**

In `agents/data-engineer.md`, replace:

```
### 2. Application data structure
Derive data entities from qualified Exigences and personas. Before writing anything, read the managed project's existing code — language, framework, existing models — and match its conventions exactly, same discipline as `hosa-implementer`. Write the structures plus a data dictionary documenting each entity, field, type, origin, and the `Exigence` it traces back to.
```

with:

```
### 2. Application data structure
Derive data entities from qualified Exigences and personas. Before writing anything, read the managed project's existing code — language, framework, existing models — and match its conventions exactly, same discipline as `hosa-implementer`. Write the structures, then dispatch `hosa-documentation` (Mode 1) with each entity's fields, types, origins, and the `Exigence` it traces back to — it writes the data dictionary into the managed project. Wait for its confirmation before reporting.
```

- [ ] **Step 7: Verify the `hosa-data-engineer` edit**

Run: `grep -c "Dispatch \`hosa-documentation\` (Mode 1)" agents/data-engineer.md`
Expected: `1`

Run: `grep -c "Write the structures plus a data dictionary" agents/data-engineer.md`
Expected: `0`

- [ ] **Step 8: Commit**

```bash
git add agents/infra.md agents/architect.md agents/data-engineer.md
git commit -m "feat: hosa-infra/architect/data-engineer dispatch hosa-documentation instead of self-writing docs"
```

---

### Task 4: Wire hot dispatch into `contestation`, register `documentation` in `using-hosa`

**Files:**
- Modify: `skills/contestation/SKILL.md`
- Modify: `skills/using-hosa/SKILL.md`

**Interfaces:**
- Consumes: `hosa-documentation`'s Mode 1 contract (same as Task 3).
- Produces: the `documentation` skill (Task 2) registered and discoverable via `using-hosa`'s tables — consumed by nothing downstream in this plan, but required for the skill to be auto-triggerable per the repo's own convention.

- [ ] **Step 1: Update `contestation`'s Step 4 (Final Sign-Off)**

In `skills/contestation/SKILL.md`, replace:

```
Once Step 1 raised nothing new and `hosa-challenger` reports "Aucune anomalie": list every `Exigence` still at `status: draft` that this audit actually covered (every one Step 2 read — the full bundle, since `hosa-challenger` always receives all of `kb/cdc/`), then ask "Le cahier des charges est propre — tu valides ? (ces N exigences passeront en `stable`)". On yes, set `status: stable` and add `verified: { by: human:<user>, at: <ISO8601> }` on each one listed. Log the change to `kb/cdc/log.md`.

If the user doesn't validate, ask what's still missing and treat it as a new anomaly — route it same as Step 3.

Once at least one `Exigence` has been validated to `stable` in this session, propose the next stage: "Le cahier des charges est stable. Je choisis la stack technique maintenant ? (skill `stack`)". Yes → invoke `stack`. No → finish normally; `stack` stays invocable manually later.
```

with:

```
Once Step 1 raised nothing new and `hosa-challenger` reports "Aucune anomalie": list every `Exigence` still at `status: draft` that this audit actually covered (every one Step 2 read — the full bundle, since `hosa-challenger` always receives all of `kb/cdc/`), then ask "Le cahier des charges est propre — tu valides ? (ces N exigences passeront en `stable`)". On yes, set `status: stable` and add `verified: { by: human:<user>, at: <ISO8601> }` on each one listed. Log the change to `kb/cdc/log.md`. Then dispatch `hosa-documentation` (Mode 1) with the newly-stable Exigence(s) and their linked persona(s) — it writes or updates the functional documentation. Wait for its confirmation before continuing.

If the user doesn't validate, ask what's still missing and treat it as a new anomaly — route it same as Step 3. No dispatch to `hosa-documentation` happens in this case — only an actual `stable` transition triggers it.

Once at least one `Exigence` has been validated to `stable` in this session, propose the next stage: "Le cahier des charges est stable. Je choisis la stack technique maintenant ? (skill `stack`)". Yes → invoke `stack`. No → finish normally; `stack` stays invocable manually later.
```

- [ ] **Step 2: Verify the `contestation` edit**

Run: `grep -c "dispatch \`hosa-documentation\` (Mode 1) with the newly-stable" skills/contestation/SKILL.md`
Expected: `1`

Run: `grep -c "No dispatch to \`hosa-documentation\` happens in this case" skills/contestation/SKILL.md`
Expected: `1`

- [ ] **Step 3: Register `documentation` in `using-hosa`'s skills table**

In `skills/using-hosa/SKILL.md`, in the skills table, after the `qualite` row, add:

```markdown
| `documentation` | Check whether the managed project's technical and functional documentation is in sync with its sources, and refresh whatever has drifted — dispatches `hosa-documentation` in cold-check mode. Companion check usable anytime, not a pipeline stage |
```

- [ ] **Step 4: Register `documentation` in `using-hosa`'s triggers table**

In `skills/using-hosa/SKILL.md`, in the triggers table, after the `qualite` trigger row, add:

```markdown
| "Vérifie que la documentation est à jour", "Génère la documentation du projet", "Documente le projet" | `documentation` |
```

- [ ] **Step 5: Verify the `using-hosa` edits**

Run: `grep -c "^| \`documentation\` |" skills/using-hosa/SKILL.md`
Expected: `1`

Run: `grep -c "Vérifie que la documentation est à jour" skills/using-hosa/SKILL.md`
Expected: `1`

- [ ] **Step 6: Commit**

```bash
git add skills/contestation/SKILL.md skills/using-hosa/SKILL.md
git commit -m "feat: contestation dispatches hosa-documentation, register documentation skill"
```

---

### Task 5: Cross-file consistency verification

**Files:** none created or modified — this task only reads and checks.

**Interfaces:**
- Consumes: every artifact from Tasks 1-4.
- Produces: nothing — a clean pass here is the plan's completion signal.

- [ ] **Step 1: Confirm the agent name is consistent everywhere it's referenced**

Run: `grep -c "hosa-documentation" agents/documentation.md agents/README.md skills/documentation/SKILL.md agents/infra.md agents/architect.md agents/data-engineer.md skills/contestation/SKILL.md skills/using-hosa/SKILL.md`
Expected: at least `1` in each of the eight files (exact counts vary; a `0` in any file is the failure condition).

- [ ] **Step 2: Confirm no other agent file in `agents/` was modified beyond the four expected**

Run: `git diff --stat -- agents/ | grep -v "documentation.md\|README.md\|infra.md\|architect.md\|data-engineer.md"`
Expected: no output (empty).

- [ ] **Step 3: Confirm none of the three producer agents still write a doc file into the managed project directly**

Run: `grep -c "Write an installation document in the managed project\|Write the architecture documentation in the managed project\|Write the structures plus a data dictionary" agents/infra.md agents/architect.md agents/data-engineer.md`
Expected: `0` in each of the three files.

- [ ] **Step 4: Confirm no new pipeline stage numbering was introduced**

Run: `grep -rn "stage of the data-structuring pipeline" skills/*/SKILL.md`
Expected: 8 lines total, unchanged from before this plan (`stack`=First ... `backlog`=Eighth) — `documentation` must not appear in this list; read the output and confirm by eye that no stage was renumbered or added.

- [ ] **Step 5: Confirm the new OKF concept type appears only where intended**

Run: `grep -c "^type: Documentation$\|type: Documentation" agents/documentation.md`
Expected: at least `1`

Run: `grep -rc "^type: Documentation$" agents/*.md skills/*/SKILL.md | grep -v ":0" | grep -v "agents/documentation.md:\|skills/documentation/SKILL.md:"`
Expected: no output (empty) — confirms no other file declares the new type as its own frontmatter.

- [ ] **Step 6: Confirm no plan placeholder text leaked into the written files**

Run: `grep -rn "TBD\|TODO\|<fill" agents/documentation.md skills/documentation/SKILL.md`
Expected: no output (empty).

- [ ] **Step 7: Report and stop**

No commit for this task — it's a read-only check. If every step above matched its Expected value, the plan is complete; report that to the user. If any step didn't match, that's a plan or content defect: rule on it per this plan's Global Constraints and the spec, fix the affected file, and re-run the failing step's command before reporting completion.
