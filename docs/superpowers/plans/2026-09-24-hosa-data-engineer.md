# Hosa Data Engineer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `hosa-data-engineer` agent and the three-skill data-structuring pipeline (`donnees` → `schema-app` → `schema-db`) that qualifies data origin in the cahier des charges and turns it into real application and database structures in the project Hosa manages.

**Architecture:** Markdown prompt-artifact repo (agents in `agents/`, skills in `skills/`) — no application code, no test runner. "Tests" for this plan are structural verifications (frontmatter present, cross-references resolve, required sections exist) run via Grep/Bash, not unit tests.

**Tech Stack:** Markdown (YAML frontmatter + prose), Claude Code agent/skill conventions already established in this repo.

**Spec:** `docs/superpowers/specs/2026-09-24-hosa-data-engineer-design.md`

## Global Constraints

- Agent files: frontmatter `name`, `description`, `model`, `memory: project` — matches every existing agent in `agents/`.
- Skill files: frontmatter `name`, `description` only — matches every existing skill in `skills/`.
- No skill in this plan commits to git — each ends with "Report what changed, let the user/orchestrating flow decide" (matches `hosa`, `recette`, `redaction`, `relecture`, `contestation`).
- `hosa-data-engineer` never writes to `hosa/kb/` except the concepts its own skills name explicitly (Exigence origin annotations, `Infra`, `Stack Decision`) — same "write only what your skill says" discipline as every other Hosa agent.
- `Exigence` frontmatter and its six existing body sections are unchanged — `donnees` only appends `— origine : ...` to existing `Données en entrée`/`Données en sortie` list items, never rewrites a section.
- OKF logging convention: append to the bundle's `log.md` (create if missing), chronological, most recent entry first, grouped by date.
- Git commits in this plan use the repo's existing convention: plain commit, user's configured `git config user.name`/`user.email` only, no co-author trailer (matches this repo's existing commit history and `skills/using-simflow/SKILL.md`'s Core Rules).
- `schema-app` and `schema-db` never treat `hosa/app` or `hosa/kb` as their "managed project" target — only the project path recorded in the `Infra` concept.

## Review Focus

1. `schema-app`/`schema-db` invoked on an `Exigence` item with no origin annotation yet — Task 3 Step 2 and Task 4 Step 2 both require stopping and asking for `donnees` to run first, never guessing an origin.
2. `schema-db` invoked standalone with no prior `schema-app` in-session — Task 4 Step 2 requires re-deriving entities the same way, not assuming `schema-app`'s output exists.
3. `donnees` invoked when `kb/cdc/` has no `stable` Exigences yet (all still `draft`) — Task 2 Step 1 requires skipping those, qualification works from a settled cahier des charges only.
4. First-ever invocation with no `kb/infra/` entry and no `kb/stack/` database `Stack Decision` — Task 3 Step 1 and Task 4 Step 1 both require asking the user and recording one, never defaulting silently.
5. A data item with no persona attached (purely technical, e.g. a system timestamp) — Task 2 Step 2 requires asking the user directly rather than forcing a `hosa-key-user` dispatch.

---

### Task 1: `hosa-data-engineer` agent

**Files:**
- Create: `agents/data-engineer.md`

**Interfaces:**
- Consumes: none (new agent, no dependency on other tasks in this plan)
- Produces: agent name `hosa-data-engineer`, invocable by `donnees` (Task 2) for data-origin qualification, by `schema-app`/`schema-db` (Tasks 3-4) for structure derivation; consumes `hosa-key-user`'s existing process-interview mode.

- [ ] **Step 1: Write `agents/data-engineer.md`**

```markdown
---
name: hosa-data-engineer
description: Use this agent as the data engineer and guarantor of data for the project Hosa manages. It qualifies where each piece of data in `hosa/kb/cdc/` Exigences comes from (générée/fournie/saisie), then derives and writes the resulting data structures — application-side and database-side — into the managed project's own codebase, along with their documentation. Invoke it directly, or from the `donnees`/`schema-app`/`schema-db` skills.
model: claude-opus-4-8
memory: project
---

You are the data engineer for the project Hosa manages. You don't own the cahier des charges or the personas — `hosa-product-owner` does — but you're accountable for what happens to data once it's named there: where it comes from, what shape it takes in the application, and how it's stored. The project you're accountable for is the one Hosa manages — never `hosa/app` or `hosa/kb` themselves, which are Hosa's own tooling and out of your scope.

## Input

You receive one of:
- **A data qualification request** — annotate the origin (générée/fournie/saisie) of data listed in `kb/cdc/` Exigences
- **An application structure request** — derive data entities from qualified Exigences and write them into the managed project's codebase, with documentation
- **A database structure request** — derive or reuse those entities and write migrations/DDL into the managed project's database

If none of these is clear from the request, ask which mode you're operating in before acting.

## The Knowledge Base

You read from Hosa's KB (`hosa/kb/`) but write your implementation output into the *managed project* — a separate codebase whose location you discover or record, never assumed to be `hosa/app`.

| Bundle | Type | What you use it for |
|---|---|---|
| `kb/cdc/` | `Exigence` | Source of the data your work is grounded in — `Données en entrée`/`Données en sortie` per process, annotated with origin |
| `kb/personnas/` | `Persona` | Who provides or enters data — needed to resolve ambiguous origins |
| `kb/infra/` | `Infra` | The managed project's root path and where its data documentation lives, once recorded |
| `kb/stack/` | `Stack Decision` | Technical choices, including the managed project's database engine |

**Frontmatter you must fill correctly on every concept you write:**
- `generated: { by: human:<user>, at: <ISO8601> }` — the user asked for this explicitly (e.g. dictated the target project path)
- `generated: { by: hosa-data-engineer/1.0, at: <ISO8601> }` — you derived or decided it yourself (e.g. an origin annotation inferred from context)

**Logging:** append an entry to the touched bundle's `log.md` (create if missing) — chronological, most recent date first, per OKF §9.

## Your Responsibilities

### 1. Data origin qualification
Annotate `Données en entrée`/`Données en sortie` items in `kb/cdc/` Exigences with their origin: générée (produced by the system/process), fournie (external source), or saisie (entered by a user). Resolve ambiguity by dispatching `hosa-key-user` in process-interview mode for anything persona-dependent; ask the user directly for anything purely technical.

### 2. Application data structure
Derive data entities from qualified Exigences and personas. Before writing anything, read the managed project's existing code — language, framework, existing models — and match its conventions exactly, same discipline as `simflow-implementer`. Write the structures plus a data dictionary documenting each entity, field, type, origin, and the `Exigence` it traces back to.

### 3. Database structure
Determine the managed project's database engine — from an existing `Stack Decision` in `kb/stack/`, or by asking the user and recording one. Write migrations/DDL matching the project's existing migration conventions.

### 4. Guarantor of data
You're accountable for data staying traceable end to end — every field in the managed project's schema should trace back to a `Données en entrée`/`sortie` item, and every such item should either be implemented or explicitly still pending. If you find a gap either direction, say so rather than filling it silently.

## No Commits

You do not commit. Report what you changed and let the user or the orchestrating skill decide when to commit, per the SimFlow core rule that commits are always in the user's name only.

## Output Format

Use whichever sections apply to the request — omit the rest:

```
## Données qualifiées
- `kb/cdc/<slug>.md` — [n] items annotated

## Structures applicatives créées
- `<path>` — [entité] ([n] champs)

## Documentation
- `<path>`

## Structures base de données créées
- `<path>` — [entité]

## Open Questions
[Anything blocking a qualification or structure decision — if none: "None"]
```

## Project Memory

Save and recall facts that compound across sessions:
- The managed project's root path, once discovered (the `Infra` KB entry is the source of truth — this is just to avoid re-asking within a session)
- Recurring data-structure conventions of the managed project (naming, ORM/framework, migration style)
- Origin qualifications that were ambiguous and how they got resolved, so the same question isn't re-asked next time

Do NOT save: the content of a specific Exigence, or a one-off structure already written into the managed project — both are re-readable from the KB or the code itself.
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "^name: hosa-data-engineer$" agents/data-engineer.md` — Expected: `1`
Run: `grep -c "^## " agents/data-engineer.md` — Expected: at least `4` (Input, The Knowledge Base, Your Responsibilities, No Commits, Output Format, Project Memory)

- [ ] **Step 3: Commit**

```bash
git add agents/data-engineer.md
git commit -m "feat: add hosa-data-engineer agent"
```

---

### Task 2: `donnees` skill

**Files:**
- Create: `skills/donnees/SKILL.md`

**Interfaces:**
- Consumes: `hosa-key-user`'s existing process-interview mode (`agents/key-user.md`), `stable` `Exigence` concepts in `kb/cdc/`
- Produces: annotated `Données en entrée`/`Données en sortie` items (`— origine : générée | fournie | saisie (par <persona ou système>)`), consumed by `schema-app` (Task 3) and `schema-db` (Task 4)

- [ ] **Step 1: Write `skills/donnees/SKILL.md`**

```markdown
---
name: donnees
description: Use to annotate the origin (générée/fournie/saisie) of each donnée listed under `Données en entrée`/`Données en sortie` in stable `kb/cdc/` Exigences. First stage of the data-structuring pipeline (donnees → schema-app → schema-db), runs after `contestation` has made the CDC stable.
---

# Données

Qualifies where each piece of data in the cahier des charges actually comes from — a prerequisite before any real data structure can be derived from it.

## Flow

```
Pour chaque Exigence stable de kb/cdc/ (ou celles touchées
dans cette session si enchaîné depuis contestation) :
        ↓
Pour chaque item de Données en entrée/sortie déjà annoté : passe
        ↓
Pour chaque item non annoté ou ambigu :
  dépend d'un persona ? → hosa-key-user (mode interview processus)
  purement technique ?  → demande à l'utilisateur
        ↓
Écrit l'annotation en place, préserve le reste du contenu
        ↓
Log kb/cdc/log.md
        ↓
Propose d'enchaîner sur `schema-app`
```

## Trigger

Manual: `/donnees`. Auto: immediately after a clean `contestation` sign-off, or "précise les données du cahier des charges", "qualifie l'origine des données".

---

## Step 1: Scope

If invoked right after `contestation`, work on the `Exigence`s that just moved to `stable` in this session. Otherwise, read every `stable` `Exigence` in `kb/cdc/`. Skip anything still `draft` — data qualification works from a settled cahier des charges, not one still being contested. If there are no `stable` Exigences at all, say so and stop.

## Step 2: Per Item — Qualify Origin

For each item under `Données en entrée`/`Données en sortie`:
- Already annotated (`— origine : ...`) → skip.
- Origin depends on a persona's point of view (who enters it, who hands it off) → dispatch `hosa-key-user` in process-interview mode (`agents/key-user.md`) with the exigence's process and the specific item: does this persona enter it (saisie), receive it from elsewhere (fournie), or does the process generate it (générée)?
- Purely technical, no persona involved (e.g. a system timestamp, a computed total) → ask the user directly, never force a `hosa-key-user` dispatch for data no persona owns.

One item at a time — don't batch multiple ambiguous items into a single question.

## Step 3: Write the Annotation

In place, preserving every other line of the `Exigence`:

```markdown
- <donnée> — origine : générée | fournie | saisie (par <persona ou système>)
```

`générée` and `fournie` name the system/process or the external source in the parenthesis; `saisie` names the persona.

## Step 4: Log

Append to `kb/cdc/log.md` (create if missing) — OKF §9: chronological, most recent date first, grouped by date.

## No Commits

You don't commit. Report what changed in the KB and let the user or the orchestrating flow decide when to commit.

## Output

```
## Exigences qualifiées
- `kb/cdc/<slug>.md` — <n> items annotés

## Suite
Je lance `schema-app` maintenant ?
```
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "hosa-key-user" skills/donnees/SKILL.md` — Expected: at least `2`
Run: `grep -c "origine : générée | fournie | saisie" skills/donnees/SKILL.md` — Expected: at least `1`

- [ ] **Step 3: Commit**

```bash
git add skills/donnees/SKILL.md
git commit -m "feat: add donnees skill, data-structuring pipeline stage 1"
```

---

### Task 3: `schema-app` skill

**Files:**
- Create: `skills/schema-app/SKILL.md`

**Interfaces:**
- Consumes: origin-annotated `Exigence` concepts (Task 2's output), `Persona` concepts in `kb/personnas/`, `Infra` concept in `kb/infra/` (created if absent)
- Produces: data structure files and a data dictionary in the managed project; an `Infra` entry recording the managed project's root path and documentation path, consumed by `schema-db` (Task 4)

- [ ] **Step 1: Write `skills/schema-app/SKILL.md`**

```markdown
---
name: schema-app
description: Use to derive data entities from qualified `kb/cdc/` Exigences and write the corresponding data structures, plus their documentation, into the project Hosa manages. Second stage of the data-structuring pipeline (donnees → schema-app → schema-db).
---

# Schema App

Turns qualified cahier des charges data into real application-side data structures — and documents them — in the managed project, never in `hosa/app`.

## Flow

```
Détermine le projet cible : kb/infra/ existant, sinon
demande le chemin et l'enregistre
        ↓
Lit les Exigence stable annotées + Persona liés → dérive
les entités de données
        ↓
Lit le code existant du projet cible (langage, framework,
conventions) avant d'écrire
        ↓
Écrit les structures de données dans le style déjà en place
        ↓
Rédige la documentation (dictionnaire de données) dans le
projet cible
        ↓
Met à jour l'entrée Infra avec le chemin de la doc
        ↓
Propose d'enchaîner sur `schema-db`
```

## Trigger

Manual: `/schema-app`. Auto: immediately after `donnees`, or "génère la structure de données de l'application".

---

## Step 1: Find the Managed Project

Read `kb/infra/` for an existing `Infra` entry giving the project's root path. If none exists, ask the user for it and write one:

```
mkdir -p hosa/kb/infra/
```

```markdown
---
type: Infra
title: Projet géré — chemin racine
description: Racine du projet applicatif géré par Hosa
tags: []
status: stable
generated: { by: human:<user>, at: <ISO8601> }
---
## Chemin racine
<chemin>
```

Log to `kb/infra/log.md` (create if missing) — OKF §9.

## Step 2: Derive Data Entities

Read every `stable` `Exigence` in `kb/cdc/` annotated by `donnees`, and the `Persona`s they reference. Group `Données en entrée`/`sortie` items into coherent entities — items that describe the same real-world thing (a client, a commande, a facture...) belong to the same entity, regardless of which Exigence mentions them.

If an item has no origin annotation yet, stop and say so — run `donnees` first, don't guess an origin here.

## Step 3: Read Existing Conventions

Before writing anything, read the managed project's existing code: language, framework, any existing models/types/schemas, naming style. Match it exactly — same discipline as `simflow-implementer`. If the project has no existing data-structure code yet, pick conventions consistent with its language/framework and say what you chose and why.

## Step 4: Write the Structures

One data structure (type/model/schema, whatever the project's stack calls for) per entity, in the managed project, in its existing style.

## Step 5: Write the Documentation

A data dictionary in the managed project (e.g. `docs/data-model.md`, or wherever the project's existing docs live), one section per entity:

```markdown
## <Entité>
| Champ | Type | Origine | Exigence |
|---|---|---|---|
| <champ> | <type> | <générée/fournie/saisie> | [<exigence>](<chemin kb/cdc>) |
```

## Step 6: Update the `Infra` Entry

Add the documentation file's path to the `Infra` entry from Step 1, and log the update to `kb/infra/log.md`.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit each.

## Output

```
## Structures créées
- `<path>` — <entité> (<n> champs)

## Documentation
- `<path>`

## Suite
Je lance `schema-db` maintenant ?
```
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "type: Infra" skills/schema-app/SKILL.md` — Expected: at least `1`
Run: `grep -c "run \`donnees\` first" skills/schema-app/SKILL.md` — Expected: at least `1`

- [ ] **Step 3: Commit**

```bash
git add skills/schema-app/SKILL.md
git commit -m "feat: add schema-app skill, data-structuring pipeline stage 2"
```

---

### Task 4: `schema-db` skill

**Files:**
- Create: `skills/schema-db/SKILL.md`

**Interfaces:**
- Consumes: data entities derived in `schema-app` (Task 3), or re-derived the same way if run standalone; `Stack Decision` concept in `kb/stack/` (created if absent); `Infra` entry from Task 3
- Produces: migration/DDL files in the managed project; updates the `Infra` entry with the migrations path

- [ ] **Step 1: Write `skills/schema-db/SKILL.md`**

```markdown
---
name: schema-db
description: Use to write database migrations/DDL for the data entities derived from `kb/cdc/`, into the project Hosa manages. Third and last stage of the data-structuring pipeline (donnees → schema-app → schema-db).
---

# Schema DB

Turns the application-side data structures into real database schema — migrations or DDL, in whatever style the managed project already uses.

## Flow

```
Cherche une Stack Decision base de données existante dans
kb/stack/ ; absente → demande à l'utilisateur, l'enregistre
        ↓
Reprend les entités de schema-app (ou les redérive si besoin)
        ↓
Lit les conventions de migration déjà en place dans le
projet cible
        ↓
Écrit les fichiers de migration/DDL dans le style déjà en place
        ↓
Met à jour l'entrée Infra si le chemin des migrations n'y
figure pas encore
```

## Trigger

Manual: `/schema-db`. Auto: immediately after `schema-app`, or "génère la structure de base de données".

---

## Step 1: Determine the Database Engine

Read `kb/stack/` for an existing `Stack Decision` covering the managed project's database. If none exists, ask the user and write one:

```
mkdir -p hosa/kb/stack/
```

```markdown
---
type: Stack Decision
title: Base de données — <projet>
description: Choix du moteur de base de données pour le projet géré
tags: []
status: stable
generated: { by: human:<user>, at: <ISO8601> }
---
## Décision
<moteur choisi>

## Justification
<pourquoi>
```

Log to `kb/stack/log.md` (create if missing) — OKF §9.

## Step 2: Get the Entities

If `schema-app` just ran in this session, reuse its entities. Otherwise, re-derive them the same way (`donnees`-qualified `Exigence`s + `Persona`s), same rule as `schema-app` Step 2 — stop and ask for `donnees` to run first if any item lacks an origin annotation.

## Step 3: Read Existing Migration Conventions

Before writing anything, read the managed project's existing migration/DDL setup — which tool it uses (if any), naming style, directory layout. Match it exactly. If none exists yet, pick conventions consistent with the chosen database engine and the project's existing stack, and say what you chose and why.

## Step 4: Write the Migrations

One migration/DDL file per entity (or grouped, if the project's existing convention groups them), in the managed project, in its existing style.

## Step 5: Update the `Infra` Entry

If the migrations' path isn't already recorded in the `Infra` entry (`schema-app`'s Step 1), add it and log the update to `kb/infra/log.md`.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit each.

## Output

```
## Choix base de données
[Décision utilisée ou nouvellement enregistrée]

## Structures créées
- `<path>` — <entité>

## Suite
Pipeline de structuration des données terminé.
```
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "type: Stack Decision" skills/schema-db/SKILL.md` — Expected: at least `1`
Run: `grep -c "re-derive them the same way" skills/schema-db/SKILL.md` — Expected: at least `1`

- [ ] **Step 3: Commit**

```bash
git add skills/schema-db/SKILL.md
git commit -m "feat: add schema-db skill, data-structuring pipeline stage 3"
```

---

### Task 5: Chain `donnees` from `contestation`'s sign-off

**Files:**
- Modify: `skills/contestation/SKILL.md`

**Interfaces:**
- Consumes: `donnees` skill name (Task 2)
- Produces: none new — trigger wiring only, same pattern as `hosa` proposing `interview`.

- [ ] **Step 1: Add the proposal after final sign-off**

In `skills/contestation/SKILL.md`, find:

```markdown
## Step 4: Final Sign-Off

Once Step 1 raised nothing new and `hosa-challenger` reports "Aucune anomalie": list every `Exigence` still at `status: draft` that this audit actually covered (every one Step 2 read — the full bundle, since `hosa-challenger` always receives all of `kb/cdc/`), then ask "Le cahier des charges est propre — tu valides ? (ces N exigences passeront en `stable`)". On yes, set `status: stable` and add `verified: { by: human:<user>, at: <ISO8601> }` on each one listed. Log the change to `kb/cdc/log.md`.

If the user doesn't validate, ask what's still missing and treat it as a new anomaly — route it same as Step 3.
```

Replace with:

```markdown
## Step 4: Final Sign-Off

Once Step 1 raised nothing new and `hosa-challenger` reports "Aucune anomalie": list every `Exigence` still at `status: draft` that this audit actually covered (every one Step 2 read — the full bundle, since `hosa-challenger` always receives all of `kb/cdc/`), then ask "Le cahier des charges est propre — tu valides ? (ces N exigences passeront en `stable`)". On yes, set `status: stable` and add `verified: { by: human:<user>, at: <ISO8601> }` on each one listed. Log the change to `kb/cdc/log.md`.

If the user doesn't validate, ask what's still missing and treat it as a new anomaly — route it same as Step 3.

Once at least one `Exigence` has been validated to `stable` in this session, propose the next stage: "Le cahier des charges est stable. Je lance la qualification des données maintenant ? (skill `donnees`)". Yes → invoke `donnees`. No → finish normally; `donnees` stays invocable manually later.
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "skill \`donnees\`" skills/contestation/SKILL.md` — Expected: `1`
Run: `grep -c "Once at least one" skills/contestation/SKILL.md` — Expected: `1`

- [ ] **Step 3: Commit**

```bash
git add skills/contestation/SKILL.md
git commit -m "feat: chain donnees skill after contestation sign-off"
```

---

### Task 6: Register the 3 new skills in `using-simflow`

**Files:**
- Modify: `skills/using-simflow/SKILL.md`

**Interfaces:**
- Consumes: skill names `donnees`, `schema-app`, `schema-db` (Tasks 2-4)
- Produces: none new — discoverability wiring only.

- [ ] **Step 1: Add rows to the skills table**

Find:

```markdown
| `contestation` | Final independent challenge pass on the cahier des charges — CDC pipeline stage 4 |
```

Replace with:

```markdown
| `contestation` | Final independent challenge pass on the cahier des charges — CDC pipeline stage 4 |
| `donnees` | Annotate the origin (générée/fournie/saisie) of data in the cahier des charges — data-structuring pipeline stage 1 |
| `schema-app` | Derive data entities and write application-side data structures + documentation into the managed project — data-structuring pipeline stage 2 |
| `schema-db` | Write database migrations/DDL into the managed project — data-structuring pipeline stage 3 |
```

- [ ] **Step 2: Add rows to the triggers table**

Find:

```markdown
| "Challenge le cahier des charges" | `contestation` |
```

Replace with:

```markdown
| "Challenge le cahier des charges" | `contestation` |
| "Précise les données du cahier des charges", "Qualifie l'origine des données" | `donnees` |
| "Génère la structure de données de l'application" | `schema-app` |
| "Génère la structure de base de données" | `schema-db` |
```

- [ ] **Step 3: Verify structure**

Run: `grep -c "^| \`donnees\`\|^| \`schema-app\`\|^| \`schema-db\`" skills/using-simflow/SKILL.md` — Expected: `6` (3 rows in the skills table + 3 rows in the triggers table)

- [ ] **Step 4: Commit**

```bash
git add skills/using-simflow/SKILL.md
git commit -m "docs: register data-structuring pipeline skills in using-simflow"
```

---

### Task 7: Cross-file consistency pass

**Files:**
- None created or modified — read-only verification across Tasks 1-6.

**Interfaces:**
- Consumes: every file touched by Tasks 1-6
- Produces: nothing — this task either passes or sends work back to the relevant earlier task.

- [ ] **Step 1: Every referenced agent/skill name actually exists**

Run: `grep -l "hosa-data-engineer" agents/*.md skills/*/SKILL.md`
Expected: includes `agents/data-engineer.md`, `skills/donnees/SKILL.md`

Run: `grep -l "hosa-key-user" skills/donnees/SKILL.md`
Expected: `skills/donnees/SKILL.md` listed

- [ ] **Step 2: The pipeline chain is unbroken**

Run: `grep -l "schema-app" skills/donnees/SKILL.md skills/schema-db/SKILL.md`
Expected: both files listed (each references `schema-app` as next step or prior stage)

Run: `grep -l "donnees" skills/contestation/SKILL.md skills/schema-app/SKILL.md skills/schema-db/SKILL.md`
Expected: all three files listed

- [ ] **Step 3: `using-simflow` table entries match actual skill directory names**

Run: `ls skills/ | grep -E "^(donnees|schema-app|schema-db)$"`
Expected: all 3 names listed, matching the rows added in Task 6

- [ ] **Step 4: Origin annotation format is consistent everywhere it's referenced**

Run: `grep -h "origine : générée | fournie | saisie" skills/donnees/SKILL.md skills/schema-app/SKILL.md`
Expected: at least 1 match in `skills/donnees/SKILL.md` (`skills/schema-app/SKILL.md` isn't required to restate the literal format — only that it reads/consumes annotated items, checked in Step 1's grep for its "run donnees first" guard)

If any check in Steps 1-3 fails, fix the specific file it points to (go back to that file's task) rather than patching around it here.

- [ ] **Step 5: No commit needed** — this task is verification-only; nothing changed.

---

## Self-Review Notes

- **Spec coverage:** §1 agent → Task 1. §2 Exigence origin annotation → Task 2 Step 3. §3.1 `donnees` → Task 2. §3.2 `schema-app` → Task 3. §3.3 `schema-db` → Task 4. §4 (implicit) chaining from `contestation` → Task 5. §4 registry → Task 6.
- **Placeholder scan:** no TBD/TODO; every agent/skill file above is complete content, not a description of content.
- **Type consistency:** agent name `hosa-data-engineer` used identically across Tasks 1-3; skill names `donnees`/`schema-app`/`schema-db` used identically everywhere cross-referenced; origin annotation literal (`— origine : générée | fournie | saisie (par <persona ou système>)`) matches exactly between the spec, Task 2 Step 3, and the Global Constraints entry.
- **Review Focus:** all 5 items map to a specific instruction inside a specific task (see numbered list above) — none left uncovered.
