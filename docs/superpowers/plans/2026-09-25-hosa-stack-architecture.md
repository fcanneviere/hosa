# Hosa Stack & Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `hosa-senior-dev` and `hosa-architect` agents, plus the `stack` and `architecture` skills, that bookend the existing data-structuring pipeline — choosing the technical stack before `donnees` runs, and designing/scaffolding the software architecture once `schema-db` is done.

**Architecture:** Markdown prompt-artifact repo (agents in `agents/`, skills in `skills/`) — no application code, no test runner. "Tests" for this plan are structural verifications (frontmatter present, cross-references resolve, required sections exist) run via Grep/Bash, not unit tests.

**Tech Stack:** Markdown (YAML frontmatter + prose), Claude Code agent/skill conventions already established in this repo.

**Spec:** `docs/superpowers/specs/2026-09-24-hosa-stack-architecture-design.md`

## Global Constraints

- Agent files: frontmatter `name`, `description`, `model`, `memory: project` — matches every existing agent in `agents/`.
- Skill files: frontmatter `name`, `description` only — matches every existing skill in `skills/`.
- No skill in this plan commits to git — each ends with "Report what changed, let the user/orchestrating flow decide" (matches every other Hosa skill).
- `hosa-senior-dev` and `hosa-architect` never write to `hosa/kb/` except the concepts their own skills name explicitly (`Stack Decision`, `Infra`) — same "write only what your skill says" discipline as every other Hosa agent.
- `stack` and `architecture` never treat `hosa/app` or `hosa/kb` as their "managed project" target — only the project path recorded in the `Infra` concept.
- OKF logging convention: append to the bundle's `log.md` (create if missing), chronological, most recent entry first, grouped by date.
- Git commits in this plan use the repo's existing convention: plain commit, user's configured `git config user.name`/`user.email` only, no co-author trailer (matches this repo's existing commit history and `skills/using-hosa/SKILL.md`'s Core Rules).
- New pipeline order everywhere it's referenced: `stack → donnees → schema-app → schema-db → architecture`, chained after `contestation`.

## Review Focus

1. `architecture` invoked before `stack`/`schema-app`/`schema-db` have produced their output — Task 4 Step 1 requires stopping and proposing the missing stage instead of guessing.
2. `schema-db` invoked standalone with no prior `stack` run in this project — Task 5's modified Step 1 must fall back to asking the user for the database engine, not assume a `Stack Decision` already exists.
3. `stack` invoked with no `stable` Exigence yet (CDC still entirely `draft`) — Task 2 Step 2 requires stopping, a stack choice needs a settled cahier des charges.
4. `donnees` invoked after `stack` ran in a separate session from `contestation` (no "just validated" Exigences in the current session) — Task 7's modified Step 1 must fall back to reading every `stable` Exigence in `kb/cdc/`, not assume a just-validated subset exists.
5. `architecture` invoked when the managed project already has partial scaffolding from `schema-app` — Task 4 Step 4 requires extending what's there rather than duplicating it.

---

### Task 1: `hosa-senior-dev` agent

**Files:**
- Create: `agents/senior-dev.md`

**Interfaces:**
- Consumes: none (new agent, no dependency on other tasks in this plan)
- Produces: agent name `hosa-senior-dev`, invocable by `stack` (Task 2) to propose and record the managed project's technical stack.

- [ ] **Step 1: Write `agents/senior-dev.md`**

```markdown
---
name: hosa-senior-dev
description: Use this agent to choose the technical stack for the project Hosa manages. It reads the stable cahier des charges to understand what the application must do, proposes 2-3 stack options (language, framework, database, hosting where relevant) with trade-offs, and records the user's choice as `Stack Decision` concepts. Invoke it directly, or from the `stack` skill.
model: claude-opus-4-8
memory: project
---

You are the senior developer for the project Hosa manages, accountable for its technical stack. You don't own the cahier des charges — `hosa-product-owner` does — but every stack choice you make has to trace back to what it says the application needs to do. The project you're accountable for is the one Hosa manages — never `hosa/app` or `hosa/kb` themselves, which are Hosa's own tooling and out of your scope.

## Input

A request to choose the technical stack for the managed project. If `kb/cdc/` has no `stable` Exigence yet, say so and stop — a stack choice needs to know what the application does, and a cahier des charges still in `draft` hasn't settled that yet.

## The Knowledge Base

You read from Hosa's KB (`hosa/kb/`) but every decision you write also belongs there — `Stack Decision` concepts are Hosa's own record of the managed project's technical choices, unlike the code and documentation `hosa-data-engineer`/`hosa-architect` write into the managed project itself.

| Bundle | Type | What you use it for |
|---|---|---|
| `kb/cdc/` | `Exigence` | What the application must do — the basis for every stack trade-off |
| `kb/infra/` | `Infra` | The managed project's root path, once recorded |
| `kb/stack/` | `Stack Decision` | Where you write each stack choice |

**Frontmatter you must fill correctly on every concept you write:**
- `generated: { by: human:<user>, at: <ISO8601> }` — the user asked for this explicitly (e.g. dictated the target project path)
- `generated: { by: hosa-senior-dev/1.0, at: <ISO8601> }` — you derived or decided it yourself (e.g. a trade-off analysis)

**Logging:** append an entry to the touched bundle's `log.md` (create if missing) — chronological, most recent date first, per OKF §9.

## Your Process

1. Determine the managed project: read `kb/infra/` for an existing `Infra` entry giving its root path. If none exists, ask the user for it and write one — never accept `hosa/app` or `hosa/kb` as the path.
2. Read every `stable` `Exigence` in `kb/cdc/` and derive the functional and non-functional needs that bear on a stack choice (data volume, integrations, deployment constraints named in the CDC).
3. Propose 2-3 stack options — language, framework, database, hosting where relevant — each with its trade-offs, and recommend one.
4. Once the user picks, write each decision as a `Stack Decision` in `kb/stack/` (one file per category: language/framework, database, hosting where applicable).

## No Commits

You do not commit. Report what you changed and let the user or the orchestrating skill decide when to commit, per the Hosa core rule that commits are always in the user's name only.

## Output Format

```
## Stack proposée
[Options presented with trade-offs]

## Stack retenue
- `kb/stack/<slug>.md` — [decision]

## Suite
Je lance `donnees` maintenant ?
```

## Project Memory

Save and recall facts that compound across sessions:
- The managed project's root path, once discovered (the `Infra` KB entry is the source of truth — this is just to avoid re-asking within a session)
- Trade-offs already explained to the user for this project, so the same pedagogy isn't repeated next time

Do NOT save: the content of `Stack Decision`s already written — re-readable from `kb/stack/`.
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "^name: hosa-senior-dev$" agents/senior-dev.md` — Expected: `1`
Run: `grep -c "^## " agents/senior-dev.md` — Expected: at least `4` (Input, The Knowledge Base, Your Process, No Commits, Output Format, Project Memory)

- [ ] **Step 3: Commit**

```bash
git add agents/senior-dev.md
git commit -m "feat: add hosa-senior-dev agent"
```

---

### Task 2: `stack` skill

**Files:**
- Create: `skills/stack/SKILL.md`

**Interfaces:**
- Consumes: `Infra` concept in `kb/infra/` (created if absent), `stable` `Exigence` concepts in `kb/cdc/`
- Produces: `Stack Decision` concepts in `kb/stack/`, consumed by `schema-app` (Task 6), `schema-db` (Task 5), and `architecture` (Task 4)

- [ ] **Step 1: Write `skills/stack/SKILL.md`**

```markdown
---
name: stack
description: Use to propose and record the technical stack for the project Hosa manages, based on the stable cahier des charges. First stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture).
---

# Stack

Turns "what the application must do" (the stable cahier des charges) into a chosen technical stack, recorded before any data structure or architecture work begins.

## Flow

```
Détermine le projet cible : kb/infra/ existant, sinon
demande le chemin et l'enregistre
        ↓
Lit les Exigence stable de kb/cdc/ → dérive les besoins
techniques pertinents
        ↓
Propose 2-3 stacks (langage, framework, BDD, hébergement)
avec compromis
        ↓
Utilisateur choisit
        ↓
Écrit chaque décision comme Stack Decision dans kb/stack/
        ↓
Propose d'enchaîner sur `donnees`
```

## Trigger

Manual: `/stack`. Auto: immediately after a clean `contestation` sign-off, or "choisis la stack technique", "quelle stack pour le projet".

---

## Step 1: Find the Managed Project

Read `kb/infra/` for an existing `Infra` entry giving the project's root path. If none exists, ask the user for it and write one:

```
mkdir -p hosa/kb/infra/
```

Write to `hosa/kb/infra/projet-gere.md`:

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

Log to `kb/infra/log.md` (create if missing) — OKF §9. Never accept `hosa/app` or `hosa/kb` as the path — those are Hosa's own tooling, out of scope; if the user gives one of them, say so and ask again.

## Step 2: Derive Technical Needs

Read every `stable` `Exigence` in `kb/cdc/`. If there are none, say so and stop — a stack choice needs a settled cahier des charges. Derive the needs that bear on a stack choice: data volume and shape, external integrations, deployment constraints, anything else named in the CDC.

## Step 3: Propose Options

Propose 2-3 stack options — language, framework, database, hosting where relevant — each with its trade-offs. Recommend one and say why.

## Step 4: Record the Decision

Once the user picks, write each decision as a `Stack Decision` in `kb/stack/` — one file per category, e.g. `hosa/kb/stack/langage-framework-projet-gere.md`, `hosa/kb/stack/base-de-donnees-projet-gere.md`, `hosa/kb/stack/hebergement-projet-gere.md`:

```markdown
---
type: Stack Decision
title: <catégorie> — <projet>
description: <choix technique et sa catégorie>
tags: []
status: stable
generated: { by: human:<user>, at: <ISO8601> }
---
## Décision
<choix>

## Justification
<pourquoi>
```

Log to `kb/stack/log.md` (create if missing) — OKF §9.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit each.

## Output

```
## Stack proposée
[Options présentées avec compromis]

## Stack retenue
- `kb/stack/<slug>.md` — [décision]

## Suite
Je lance `donnees` maintenant ?
```
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "type: Stack Decision" skills/stack/SKILL.md` — Expected: at least `1`
Run: `grep -c "a settled cahier des charges" skills/stack/SKILL.md` — Expected: at least `1`

- [ ] **Step 3: Commit**

```bash
git add skills/stack/SKILL.md
git commit -m "feat: add stack skill, data-structuring pipeline stage 1"
```

---

### Task 3: `hosa-architect` agent

**Files:**
- Create: `agents/architect.md`

**Interfaces:**
- Consumes: none (new agent, no dependency on other tasks in this plan)
- Produces: agent name `hosa-architect`, invocable by `architecture` (Task 4) for software architecture design and scaffolding.

- [ ] **Step 1: Write `agents/architect.md`**

```markdown
---
name: hosa-architect
description: Use this agent as the guarantor of software architecture for the project Hosa manages. Once the cahier des charges is stable, the stack is chosen, and the application/database data structures are written by `hosa-data-engineer`, it designs a software architecture (layers, modules, boundaries) consistent with all three, then scaffolds it for real in the managed project's own codebase, along with its documentation. Invoke it directly, or from the `architecture` skill.
model: claude-opus-4-8
memory: project
---

You are the software architect for the project Hosa manages. You don't own the cahier des charges, the stack, or the data structures — `hosa-product-owner`, `hosa-senior-dev`, and `hosa-data-engineer` do — but you're accountable for how they fit together: the layers, modules, and boundaries that make the business logic, the chosen stack, and the data architecture cohere into one buildable codebase. The project you're accountable for is the one Hosa manages — never `hosa/app` or `hosa/kb` themselves, which are Hosa's own tooling and out of your scope.

## Input

A request to design and scaffold the software architecture. If the stack or the data structures aren't in place yet, say so and propose running `stack`/`schema-app`/`schema-db` first rather than guessing.

## The Knowledge Base

You read from Hosa's KB (`hosa/kb/`) but write your implementation output into the *managed project* — the same one `hosa-data-engineer` already wrote its structures into.

| Bundle | Type | What you use it for |
|---|---|---|
| `kb/cdc/` | `Exigence` | The business logic your architecture has to serve |
| `kb/stack/` | `Stack Decision` | The chosen language, framework, database, hosting |
| `kb/infra/` | `Infra` | The managed project's root path and where its documentation lives |

You also read the data dictionary and migrations `hosa-data-engineer` already wrote into the managed project (paths recorded in the `Infra` entry) — your architecture has to fit the data structures that already exist, not redesign them.

**Frontmatter you must fill correctly on every concept you write:**
- `generated: { by: human:<user>, at: <ISO8601> }` — the user asked for this explicitly
- `generated: { by: hosa-architect/1.0, at: <ISO8601> }` — you derived or decided it yourself

**Logging:** append an entry to the touched bundle's `log.md` (create if missing) — chronological, most recent date first, per OKF §9.

## Your Process

1. Read `kb/cdc/` (`stable` `Exigence`), `kb/stack/` (`Stack Decision`), and the data dictionary + migrations already written by `hosa-data-engineer` in the managed project.
2. Read the managed project's existing code, if any, to respect conventions already in place — same discipline as `hosa-implementer`.
3. Design the architecture — layers, modules, boundaries, patterns — consistent with the stack and the data structures. Say what you chose and why.
4. Scaffold it for real in the managed project: folders, module skeletons, boilerplate matching the chosen stack. Extend anything that already exists rather than duplicating it.
5. Write the architecture documentation in the managed project (never in `hosa/kb`).
6. Update the `Infra` entry with the documentation's path.

## No Commits

You do not commit. Report what you changed and let the user or the orchestrating skill decide when to commit, per the Hosa core rule that commits are always in the user's name only.

## Output Format

```
## Architecture conçue
[Layers/modules chosen and why]

## Structures créées
- `<path>` — [module/dossier scaffoldé]

## Documentation
- `<path>`

## Open Questions
[Anything blocking a design decision — if none: "None"]
```

## Project Memory

Save and recall facts that compound across sessions:
- The managed project's root path, once discovered
- Recurring architecture conventions of the managed project (folder structure, patterns already in place)

Do NOT save: the content of an architecture already scaffolded — re-readable from the managed project's own code.
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "^name: hosa-architect$" agents/architect.md` — Expected: `1`
Run: `grep -c "hosa-data-engineer" agents/architect.md` — Expected: at least `2`

- [ ] **Step 3: Commit**

```bash
git add agents/architect.md
git commit -m "feat: add hosa-architect agent"
```

---

### Task 4: `architecture` skill

**Files:**
- Create: `skills/architecture/SKILL.md`

**Interfaces:**
- Consumes: `Stack Decision` concepts (Task 2's output), data dictionary + migrations written by `schema-app`/`schema-db` in the managed project, `Infra` entry
- Produces: scaffolded architecture files and documentation in the managed project; updates the `Infra` entry with the architecture doc's path

- [ ] **Step 1: Write `skills/architecture/SKILL.md`**

```markdown
---
name: architecture
description: Use to design and scaffold the software architecture of the project Hosa manages, consistent with the stable cahier des charges, the chosen stack, and the data structures already written by `schema-app`/`schema-db`. Fifth and last stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture).
---

# Architecture

Turns the business logic, the chosen stack, and the finished data architecture into a real, scaffolded software architecture in the managed project.

## Flow

```
Lit kb/cdc stable, kb/stack (Stack Decision), la doc de
données + migrations écrites par schema-app/schema-db
        ↓
Si l'une des trois sources manque, le dit et propose de
lancer l'étape manquante d'abord
        ↓
Lit le code existant du projet cible (conventions)
        ↓
Conçoit l'architecture (couches, modules, limites) cohérente
avec stack + données + logique métier
        ↓
Scaffold l'architecture dans le projet cible
        ↓
Rédige la documentation d'architecture dans le projet cible
        ↓
Met à jour l'entrée Infra avec le chemin de la doc
```

## Trigger

Manual: `/architecture`. Auto: immediately after `schema-db`, or "crée l'architecture logicielle", "génère l'architecture de l'application".

---

## Step 1: Gather Inputs

Read `kb/cdc/` for `stable` `Exigence`s, `kb/stack/` for `Stack Decision`s, and the data dictionary + migrations already written by `schema-app`/`schema-db` in the managed project (paths recorded in the `Infra` entry). If any of the three is missing, say so and propose running the missing stage (`stack`, `schema-app`, or `schema-db`) first — don't guess.

## Step 2: Read Existing Conventions

Read the managed project's existing code, if any, to respect conventions already in place — same discipline as `hosa-implementer`.

## Step 3: Design the Architecture

Design the layers, modules, and boundaries that let the business logic (CDC), the chosen stack, and the existing data structures cohere into one buildable codebase. Say what you chose and why.

## Step 4: Scaffold It

Write the architecture for real in the managed project: folders, module skeletons, boilerplate matching the chosen stack. If parts of the architecture already exist (from `schema-app`'s output or otherwise), extend them rather than duplicating.

## Step 5: Write the Documentation

An architecture document in the managed project (e.g. `docs/architecture.md`, or wherever the project's existing docs live) — never in `hosa/kb`. Cover the layers/modules chosen, their boundaries, and how they relate to the data structures and the CDC.

## Step 6: Update the `Infra` Entry

Add the architecture documentation's path to the `Infra` entry, and log the update to `kb/infra/log.md`.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit each.

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

- [ ] **Step 2: Verify structure**

Run: `grep -c "don't guess" skills/architecture/SKILL.md` — Expected: at least `1`
Run: `grep -c "extend them rather than duplicating\|extend anything that already exists" skills/architecture/SKILL.md` — Expected: at least `1`

- [ ] **Step 3: Commit**

```bash
git add skills/architecture/SKILL.md
git commit -m "feat: add architecture skill, data-structuring pipeline stage 5"
```

---

### Task 5: Update `schema-db` to consume the `stack` skill's output

**Files:**
- Modify: `skills/schema-db/SKILL.md`

**Interfaces:**
- Consumes: `Stack Decision` concept normally already written by `stack` (Task 2)
- Produces: none new — reuses the existing `Infra`/migration output, now proposes `architecture` (Task 4) as its next step instead of ending the pipeline.

- [ ] **Step 1: Update the frontmatter description and Flow diagram**

Find:

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
Détermine le projet cible : kb/infra/ existant, sinon
demande le chemin et l'enregistre
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
```

Replace with:

```markdown
---
name: schema-db
description: Use to write database migrations/DDL for the data entities derived from `kb/cdc/`, into the project Hosa manages. Fourth stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture).
---

# Schema DB

Turns the application-side data structures into real database schema — migrations or DDL, in whatever style the managed project already uses.

## Flow

```
Lit la Stack Decision base de données (écrite par `stack`,
ou demandée ici en fallback si absente)
        ↓
Détermine le projet cible : kb/infra/ existant, sinon
demande le chemin et l'enregistre
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
        ↓
Propose d'enchaîner sur `architecture`
```
```

- [ ] **Step 2: Update Step 1's opening sentence**

Find:

```markdown
## Step 1: Determine the Database Engine

Read `kb/stack/` for an existing `Stack Decision` covering the managed project's database. If none exists, ask the user and write one:
```

Replace with:

```markdown
## Step 1: Determine the Database Engine

Read `kb/stack/` for the `Stack Decision` covering the managed project's database — normally already written by the `stack` skill before this pipeline reaches `schema-db`. If none exists (this skill invoked standalone, without `stack` having run), fall back to asking the user and writing one:
```

- [ ] **Step 3: Update the Output's "Suite" section**

Find:

```markdown
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

Replace with:

```markdown
## Output

```
## Choix base de données
[Décision utilisée ou nouvellement enregistrée]

## Structures créées
- `<path>` — <entité>

## Suite
Je lance `architecture` maintenant ?
```
```

- [ ] **Step 4: Verify structure**

Run: `grep -c "normally already written by the \`stack\` skill" skills/schema-db/SKILL.md` — Expected: `1`
Run: `grep -c "Je lance \`architecture\` maintenant" skills/schema-db/SKILL.md` — Expected: `1`
Run: `grep -c "Pipeline de structuration des données terminé" skills/schema-db/SKILL.md` — Expected: `0`

- [ ] **Step 5: Commit**

```bash
git add skills/schema-db/SKILL.md
git commit -m "feat: chain schema-db to stack's Stack Decision and to architecture"
```

---

### Task 6: Update `schema-app` to prefer the `stack` skill's output on greenfield projects

**Files:**
- Modify: `skills/schema-app/SKILL.md`

**Interfaces:**
- Consumes: `Stack Decision` concept normally already written by `stack` (Task 2)
- Produces: none new — Step 3's convention-detection logic gains a fallback source.

- [ ] **Step 1: Update the frontmatter description**

Find:

```markdown
description: Use to derive data entities from qualified `kb/cdc/` Exigences and write the corresponding data structures, plus their documentation, into the project Hosa manages. Second stage of the data-structuring pipeline (donnees → schema-app → schema-db).
```

Replace with:

```markdown
description: Use to derive data entities from qualified `kb/cdc/` Exigences and write the corresponding data structures, plus their documentation, into the project Hosa manages. Third stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture).
```

- [ ] **Step 2: Update Step 3 to prefer the recorded stack on greenfield projects**

Find:

```markdown
## Step 3: Read Existing Conventions

Before writing anything, read the managed project's existing code: language, framework, any existing models/types/schemas, naming style. Match it exactly — same discipline as `hosa-implementer`. If the project has no existing data-structure code yet, pick conventions consistent with its language/framework and say what you chose and why.
```

Replace with:

```markdown
## Step 3: Read Existing Conventions

Before writing anything, read the managed project's existing code: language, framework, any existing models/types/schemas, naming style. Match it exactly — same discipline as `hosa-implementer`. If the project has no existing data-structure code yet, use the language/framework `Stack Decision` in `kb/stack/` (written by the `stack` skill) rather than guessing; if that's also missing, pick conventions consistent with whatever's available and say what you chose and why.
```

- [ ] **Step 3: Verify structure**

Run: `grep -c "stage 3" skills/schema-app/SKILL.md` — Expected: at least `1`
Run: `grep -c "written by the \`stack\` skill" skills/schema-app/SKILL.md` — Expected: `1`

- [ ] **Step 4: Commit**

```bash
git add skills/schema-app/SKILL.md
git commit -m "feat: prefer stack's Stack Decision on greenfield schema-app runs"
```

---

### Task 7: Update `donnees` to chain from `stack` instead of directly from `contestation`

**Files:**
- Modify: `skills/donnees/SKILL.md`

**Interfaces:**
- Consumes: `stack` skill name (Task 2)
- Produces: none new — trigger wiring and scoping logic only.

- [ ] **Step 1: Update the frontmatter description, Flow diagram, and Trigger**

Find:

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
```

Replace with:

```markdown
---
name: donnees
description: Use to annotate the origin (générée/fournie/saisie) of each donnée listed under `Données en entrée`/`Données en sortie` in stable `kb/cdc/` Exigences. Second stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture), runs after `stack` has recorded the technical choices.
---

# Données

Qualifies where each piece of data in the cahier des charges actually comes from — a prerequisite before any real data structure can be derived from it.

## Flow

```
Pour chaque Exigence stable de kb/cdc/ (ou celles validées
par contestation dans cette session, si enchaîné depuis
contestation/stack) :
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

Manual: `/donnees`. Auto: immediately after `stack`, or "précise les données du cahier des charges", "qualifie l'origine des données".
```

- [ ] **Step 2: Update Step 1's scoping condition**

Find:

```markdown
## Step 1: Scope

If invoked right after `contestation`, work on the `Exigence`s that just moved to `stable` in this session. Otherwise, read every `stable` `Exigence` in `kb/cdc/`. Skip anything still `draft` — data qualification works from a settled cahier des charges, not one still being contested. If there are no `stable` Exigences at all, say so and stop.
```

Replace with:

```markdown
## Step 1: Scope

If `contestation` validated one or more `Exigence`s to `stable` earlier in this same session (whether or not `stack` ran in between), work on those just-validated `Exigence`s. Otherwise, read every `stable` `Exigence` in `kb/cdc/`. Skip anything still `draft` — data qualification works from a settled cahier des charges, not one still being contested. If there are no `stable` Exigences at all, say so and stop.
```

- [ ] **Step 3: Verify structure**

Run: `grep -c "stage 2" skills/donnees/SKILL.md` — Expected: at least `1`
Run: `grep -c "Auto: immediately after \`stack\`" skills/donnees/SKILL.md` — Expected: `1`
Run: `grep -c "whether or not \`stack\` ran in between" skills/donnees/SKILL.md` — Expected: `1`

- [ ] **Step 4: Commit**

```bash
git add skills/donnees/SKILL.md
git commit -m "feat: chain donnees from stack instead of directly from contestation"
```

---

### Task 8: Chain `stack` from `contestation`'s sign-off

**Files:**
- Modify: `skills/contestation/SKILL.md`

**Interfaces:**
- Consumes: `stack` skill name (Task 2)
- Produces: none new — trigger wiring only.

- [ ] **Step 1: Replace the proposal after final sign-off**

Find:

```markdown
Once at least one `Exigence` has been validated to `stable` in this session, propose the next stage: "Le cahier des charges est stable. Je lance la qualification des données maintenant ? (skill `donnees`)". Yes → invoke `donnees`. No → finish normally; `donnees` stays invocable manually later.
```

Replace with:

```markdown
Once at least one `Exigence` has been validated to `stable` in this session, propose the next stage: "Le cahier des charges est stable. Je choisis la stack technique maintenant ? (skill `stack`)". Yes → invoke `stack`. No → finish normally; `stack` stays invocable manually later.
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "skill \`stack\`" skills/contestation/SKILL.md` — Expected: `1`
Run: `grep -c "skill \`donnees\`" skills/contestation/SKILL.md` — Expected: `0`

- [ ] **Step 3: Commit**

```bash
git add skills/contestation/SKILL.md
git commit -m "feat: chain stack skill after contestation sign-off"
```

---

### Task 9: Register `stack` and `architecture` in `using-hosa`

**Files:**
- Modify: `skills/using-hosa/SKILL.md`

**Interfaces:**
- Consumes: skill names `stack`, `architecture` (Tasks 2, 4)
- Produces: none new — discoverability wiring only.

- [ ] **Step 1: Replace the data-structuring pipeline rows in the skills table**

Find:

```markdown
| `donnees` | Annotate the origin (générée/fournie/saisie) of data in the cahier des charges — data-structuring pipeline stage 1 |
| `schema-app` | Derive data entities and write application-side data structures + documentation into the managed project — data-structuring pipeline stage 2 |
| `schema-db` | Write database migrations/DDL into the managed project — data-structuring pipeline stage 3 |
```

Replace with:

```markdown
| `stack` | Propose and record the technical stack of the managed project, based on the stable cahier des charges — data-structuring pipeline stage 1 |
| `donnees` | Annotate the origin (générée/fournie/saisie) of data in the cahier des charges — data-structuring pipeline stage 2 |
| `schema-app` | Derive data entities and write application-side data structures + documentation into the managed project — data-structuring pipeline stage 3 |
| `schema-db` | Write database migrations/DDL into the managed project — data-structuring pipeline stage 4 |
| `architecture` | Design and scaffold the software architecture of the managed project, consistent with the CDC, the stack, and the data structures — data-structuring pipeline stage 5 |
```

- [ ] **Step 2: Add rows to the triggers table**

Find:

```markdown
| "Précise les données du cahier des charges", "Qualifie l'origine des données" | `donnees` |
| "Génère la structure de données de l'application" | `schema-app` |
| "Génère la structure de base de données" | `schema-db` |
```

Replace with:

```markdown
| "Choisis la stack technique", "Quelle stack pour le projet" | `stack` |
| "Précise les données du cahier des charges", "Qualifie l'origine des données" | `donnees` |
| "Génère la structure de données de l'application" | `schema-app` |
| "Génère la structure de base de données" | `schema-db` |
| "Crée l'architecture logicielle", "Génère l'architecture de l'application" | `architecture` |
```

- [ ] **Step 3: Verify structure**

Run: `grep -c "^| \`stack\`\|^| \`donnees\`\|^| \`schema-app\`\|^| \`schema-db\`\|^| \`architecture\`" skills/using-hosa/SKILL.md` — Expected: `10` (5 rows in the skills table + 5 rows in the triggers table)

- [ ] **Step 4: Commit**

```bash
git add skills/using-hosa/SKILL.md
git commit -m "docs: register stack and architecture skills in using-hosa"
```

---

### Task 10: Register the 2 new agents in `agents/README.md`

**Files:**
- Modify: `agents/README.md`

**Interfaces:**
- Consumes: agent names `hosa-senior-dev` (Task 1), `hosa-architect` (Task 3)
- Produces: none new — discoverability wiring only.

- [ ] **Step 1: Add rows to the Hosa agents table**

Find:

```markdown
| [`hosa-challenger`](challenger.md) | claude-opus-4-8 | Audits the assembled cahier des charges (`hosa/kb/cdc/`) for contradictions, blind spots, unstated assumptions, and risks — an independent read, never a self-check. |
| [`hosa-data-engineer`](data-engineer.md) | claude-opus-4-8 | Data engineer and guarantor of data for the managed project — qualifies where each piece of data comes from (générée/fournie/saisie), derives and writes the resulting app- and DB-side data structures plus their documentation. |
```

Replace with:

```markdown
| [`hosa-challenger`](challenger.md) | claude-opus-4-8 | Audits the assembled cahier des charges (`hosa/kb/cdc/`) for contradictions, blind spots, unstated assumptions, and risks — an independent read, never a self-check. |
| [`hosa-senior-dev`](senior-dev.md) | claude-opus-4-8 | Chooses the technical stack for the managed project — proposes stack options based on the stable cahier des charges, with trade-offs, and records the choice. |
| [`hosa-data-engineer`](data-engineer.md) | claude-opus-4-8 | Data engineer and guarantor of data for the managed project — qualifies where each piece of data comes from (générée/fournie/saisie), derives and writes the resulting app- and DB-side data structures plus their documentation. |
| [`hosa-architect`](architect.md) | claude-opus-4-8 | Guarantor of software architecture for the managed project — designs and scaffolds an architecture consistent with the business logic, the chosen stack, and the finished data structures. |
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "hosa-senior-dev\|hosa-architect" agents/README.md` — Expected: `2`

- [ ] **Step 3: Commit**

```bash
git add agents/README.md
git commit -m "docs: register hosa-senior-dev and hosa-architect in agents README"
```

---

### Task 11: Cross-file consistency pass

**Files:**
- None created or modified — read-only verification across Tasks 1-10.

**Interfaces:**
- Consumes: every file touched by Tasks 1-10
- Produces: nothing — this task either passes or sends work back to the relevant earlier task.

- [ ] **Step 1: Every referenced agent/skill name actually exists**

Run: `grep -l "hosa-senior-dev" agents/*.md skills/*/SKILL.md`
Expected: includes `agents/senior-dev.md`, `skills/stack/SKILL.md`

Run: `grep -l "hosa-architect" agents/*.md skills/*/SKILL.md`
Expected: includes `agents/architect.md`, `skills/architecture/SKILL.md`

- [ ] **Step 2: The pipeline chain is unbroken end to end**

Run: `grep -l "stack" skills/contestation/SKILL.md skills/donnees/SKILL.md`
Expected: both files listed

Run: `grep -l "architecture" skills/schema-db/SKILL.md`
Expected: `skills/schema-db/SKILL.md` listed

Run: `grep -l "schema-db" skills/architecture/SKILL.md`
Expected: `skills/architecture/SKILL.md` listed

- [ ] **Step 3: `using-hosa` and `agents/README.md` entries match actual file names**

Run: `ls skills/ | grep -E "^(stack|architecture)$"`
Expected: both names listed, matching the rows added in Task 9

Run: `ls agents/ | grep -E "^(senior-dev|architect)\.md$"`
Expected: both files listed, matching the rows added in Task 10

- [ ] **Step 4: No skill in this plan commits**

Run: `grep -L "You don't commit\|You do not commit" skills/stack/SKILL.md skills/architecture/SKILL.md agents/senior-dev.md agents/architect.md`
Expected: empty output (every file contains one of the two phrases)

If any check in Steps 1-4 fails, fix the specific file it points to (go back to that file's task) rather than patching around it here.

- [ ] **Step 5: No commit needed** — this task is verification-only; nothing changed.

---

## Self-Review Notes

- **Spec coverage:** §1 `hosa-senior-dev` → Task 1. §2 `stack` skill → Task 2. §3 `hosa-architect` → Task 3. §4 `architecture` skill → Task 4. §5 `schema-db`/`schema-app` modifications → Tasks 5-6. Pipeline renumbering (§5) → Tasks 5-9. §6 `using-hosa` registry → Task 9. Chaining from `contestation` (implicit in "Pipeline mis à jour") → Task 8; `donnees`'s own chain adjustment → Task 7. Agent discoverability (matches existing `agents/README.md` convention, not explicitly in spec but required for consistency) → Task 10.
- **Placeholder scan:** no TBD/TODO; every agent/skill file above is complete content, not a description of content.
- **Type consistency:** agent names `hosa-senior-dev`/`hosa-architect` used identically across all tasks; skill names `stack`/`architecture` used identically everywhere cross-referenced; `Stack Decision` frontmatter shape matches exactly between Task 2's `stack` skill and the pre-existing shape in `schema-db` (Task 5), unchanged.
- **Review Focus:** all 5 items map to a specific instruction inside a specific task (see numbered list above) — none left uncovered.
