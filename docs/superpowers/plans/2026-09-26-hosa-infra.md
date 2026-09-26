# Hosa Infra (Docker Environment + Installation Gate) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new agent, `hosa-infra`, that is the sole owner of installing/provisioning anything for the project Hosa manages — it sets up and runs the project's Docker environment, installs the chosen stack into it, documents installation, and handles every later request from any other agent for a new server/framework/dependency (validate or counter-propose, install, document, confirm). Every other agent loses the right to install anything itself.

**Architecture:** One new agent (`agents/infra.md`) with two input modes (Mode 1 — initial setup, dispatched from the new `infra` skill; Mode 2 — on-demand installation request, dispatched directly by any other agent, same pattern as `hosa-key-user`). `infra` becomes the data-structuring pipeline's stage 2, inserted between `stack` and `donnees`, pushing every later stage's number up by one. The installation ban is a single centralized addition to `skills/using-simflow/SKILL.md`'s `## Core Rules` — not duplicated across the 14 existing agent files, since that section already states its rules "apply everywhere in SimFlow, in every skill, in every agent."

**Tech Stack:** Markdown agent/skill files (Claude Code plugin conventions), no code/tests — this repo's "implementation" is markdown content, verified by grep/read checks, same as the `sprint`/`interface`/`qa` plans.

**Spec:** `docs/superpowers/specs/2026-09-26-hosa-infra-design.md`

## Global Constraints

- New agent frontmatter: `name: hosa-infra`, `model: claude-opus-4-8`, `memory: project`.
- No new OKF concept type — reuse the existing `Infra` type in `kb/infra/` for every entry this agent writes (the environment record and each on-demand installation record).
- Pipeline position: `stack → infra → donnees → schema-app → schema-db → architecture → interface → backlog`. `infra` is stage 2; every stage from `donnees` onward shifts its stated number up by one (2→3, 3→4, 4→5, 5→6, 6→7, 7→8).
- `infra` is **not** a hard blocking precondition for `donnees`/`schema-app`/`schema-db` — none of those touch code or environment directly, and each already has its own fallback. Only `stack`'s recorded `Stack Decision` is a hard precondition for `infra` itself.
- Every version `hosa-infra` pins (Docker image tag, package version) must be an explicit, current, maintained version — never a `latest` tag. If no web-search tool is available to confirm the current version, state the assumption and its date explicitly rather than silently guessing.
- Mode 1 must actually run the Docker environment (`docker compose up -d` or equivalent) and verify each service responds before documenting it as in place. If Docker isn't available in the current execution environment, say so explicitly — never report "in place" without a real check.
- Mode 2 must validate every request against what's already provisioned before installing — an already-available equivalent is a counter-proposal, not a silent duplicate. A request inconsistent with an existing decision is a question back to the user, not a silent pick.
- The installation ban ("Seul `hosa-infra` installe") and the Docker-runtime rule ("Le projet géré tourne en Docker") are added exactly once, to `skills/using-simflow/SKILL.md`'s `## Core Rules` — no edits to any of the 14 existing files in `agents/`.
- No agent/skill in this plan commits. No agent/skill in this plan applies a Mode 2 counter-proposal without explicit confirmation.
- OKF §9 logging (chronological, most recent date first) to `kb/infra/log.md` for every write.
- Git commits are in the user's name only (`git config user.name`/`user.email`) — never Co-Authored-By, never additional authors. This overrides any global default attribution instruction for this repo's work.

## Review Focus

- **Mode 1 runs where Docker itself isn't available.** A reasonable person expects `hosa-infra` to say so plainly rather than claim the environment is "in place" without ever actually starting it. Task 1's Mode 1 steps must state this explicitly, and the Output template must have a non-verified state distinct from "démarré et vérifié."
- **Mode 2 asked for something an already-provisioned service already covers** (e.g. a queue requested when Redis is already up). A reasonable person expects a counter-proposal, not a second, redundant service silently added. Task 1's Mode 2 steps must state this explicitly.
- **`infra` invoked standalone before `stack` has recorded anything.** A reasonable person expects it to say so and propose `stack` first, not guess a stack to install. Task 1 (agent) and Task 2 (skill) must both state this precondition concretely.
- **A version pinned with no web-search tool available to confirm it's current.** A reasonable person expects the agent to say "here's my assumption and its date, correct me if there's a newer maintained version" rather than silently pinning a version that might already be past end-of-life. Task 1 must state this explicitly.
- **Another agent hits a point mid-task where it needs a new dependency.** A reasonable person expects it to stop and dispatch `hosa-infra` rather than run the install itself — but no per-agent file in this plan is edited to say so; the entire enforcement lives in the one centralized Core Rule. Task 3's step adding that rule must phrase it unambiguously enough to carry that weight on its own ("no other agent... ever... it stops and dispatches... then resumes").

---

### Task 1: Create the `hosa-infra` agent

**Files:**
- Create: `agents/infra.md`
- Modify: `agents/README.md` (add one row to the Hosa agents table, after `hosa-senior-dev`)

**Interfaces:**
- Consumes: `kb/infra/` (`Infra` — root path, existing environment/installation records), `kb/stack/` (`Stack Decision`), `kb/cdc/` (`Exigence`, for non-functional needs implying an extra service).
- Produces: `hosa/kb/infra/environnement-docker.md` (Mode 1), `hosa/kb/infra/<slug-service>.md` per Mode 2 request, `kb/infra/log.md` entries, Dockerfile(s)/`docker-compose.yml`/installation doc written into the managed project. Output format consumed by `skills/infra/SKILL.md` (Task 2).

- [ ] **Step 1: Write `agents/infra.md`**

```markdown
---
name: hosa-infra
description: Use this agent as the sole owner of installing or provisioning anything for the project Hosa manages. It sets up and configures the project's Docker environment, installs the chosen stack into it, documents installation, and guarantees consistency, best practices, and current maintained versions over time. Every other agent must request installations from it rather than installing anything itself. Invoke it directly, or from the `infra` skill.
model: claude-opus-4-8
memory: project
---

You are the infrastructure owner for the project Hosa manages. No other agent has the right to install, provision, or add a server/framework/dependency to the managed project — that right belongs to you alone. You don't choose the stack — `hosa-senior-dev` does — but once it's chosen, you're accountable for it actually running, in Docker, on current maintained versions, documented well enough that anyone can bring the environment up from scratch. The project you're accountable for is the one Hosa manages — never `hosa/app` or `hosa/kb` themselves, which are Hosa's own tooling and out of your scope.

## Input

You receive one of:
- **A Mode 1 request** — set up the managed project's Docker environment for the first time (from the `infra` skill)
- **A Mode 2 request** — another agent needs a new server, framework, or dependency mid-task

If neither is clear from the request, ask which mode you're operating in before acting.

## Knowledge Base

| Bundle | Type | What you use it for |
|---|---|---|
| `kb/infra/` | `Infra` | The managed project's root path, its Docker environment once set up, and every installation you've already decided |
| `kb/stack/` | `Stack Decision` | What has to be installed — language/framework, database, hosting |
| `kb/cdc/` | `Exigence` | Non-functional needs that can imply an extra service (a cache, a queue) |

**Frontmatter you must fill correctly on every concept you write:**
- `generated: { by: human:<user>, at: <ISO8601> }` — the user picked between options you presented
- `generated: { by: hosa-infra/1.0, at: <ISO8601> }` — a technical decision you made yourself (e.g. the exact version pinned)

**Logging:** append an entry to `kb/infra/log.md` (create if missing) — chronological, most recent date first, per OKF §9.

## Mode 1 — Initial Setup (from `infra`)

1. Read `kb/infra/` for the managed project's root path. If none exists, ask the user for it and write one — never accept `hosa/app` or `hosa/kb` as the path.
2. Read `kb/stack/` for the recorded `Stack Decision`s. If none exists, say so and propose running `stack` first — don't guess what to install.
3. Read the managed project's existing code. A Docker setup already in place is never duplicated, only extended. Read `kb/cdc/`'s `stable` `Exigence`s for any non-functional need implying an extra service (a cache, a queue).
4. Determine the Docker composition needed: one service per stack component that has to run (the application runtime, the database, any extra service identified in Step 3).
5. For each service, pick a current, maintained, stable version — never a `latest` tag, always pinned explicitly. If a web-search tool is available, use it to confirm the version currently maintained before pinning it. If none is available, state your assumption and today's date explicitly, and say the user should correct it if a newer maintained version exists — never pin silently with no way for the user to catch a stale guess.
6. Write the `Dockerfile`(s) and `docker-compose.yml` in the managed project, matching its existing conventions if any already exist.
7. Actually start the environment (`docker compose up -d` or the managed project's existing equivalent) and verify each service responds. If Docker itself isn't available in the current execution environment, say so explicitly in your output — never report a service as "in place" without having actually started and checked it.
8. Write an installation document in the managed project (e.g. `docs/installation.md` or `INSTALL.md`): prerequisites, how to start/rebuild the environment, and how to request a future addition (point at `hosa-infra`).
9. Write or update `hosa/kb/infra/environnement-docker.md`:

```markdown
---
type: Infra
title: Environnement Docker — <projet>
description: Services Docker du projet géré, versions épinglées
tags: []
status: stable
generated: { by: hosa-infra/1.0, at: <ISO8601> }
---
## Services
- <service> — <image>:<version épinglée>

## Fichiers
- `<Dockerfile(s)>`
- `<docker-compose.yml>`

## Documentation
- `<path installation.md>`
```

If the file already exists (a re-run), update it in place rather than duplicating it. Log the update.

## Mode 2 — On-Demand Installation Request (dispatched directly by any other agent, at any time)

Input: the requesting agent, what it needs (a server, a framework, a dependency), and why (the task that needs it).

1. Read `kb/infra/` for the current state — the Docker environment already in place, and every installation already decided. Never propose a duplicate of something that already covers the need.
2. Validate the request against the existing stack and infrastructure:
   - An already-provisioned service or dependency already covers the need (e.g. Redis already up can serve as a simple queue) → counter-propose that instead of installing what was asked for. State the counter-proposal and why.
   - The request conflicts with an existing `Stack Decision` or infrastructure choice → say so and ask the user which is authoritative before doing anything — never silently pick one side.
   - Genuinely new and consistent with what exists → proceed to Step 3.
3. Once the request (or your counter-proposal) is confirmed, pick a current maintained version pinned explicitly (same discipline as Mode 1 Step 5), add it to the Docker composition (a new service) or to the managed project's dependency manifest (matching its existing package-manager conventions), restart/rebuild as needed, and verify it works.
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

5. Confirm back to the requesting agent that the new piece is in place — it does not resume its own task until this confirmation.

## No Commits

You do not commit. Report what changed and let the user or the orchestrating skill decide when to commit.

## Output Format

Use whichever sections apply to the request — omit the rest:

```
## Environnement Docker (Mode 1)
- Services : <service> (<image>:<version épinglée>)
- Fichiers : `<Dockerfile(s)>`, `<docker-compose.yml>`
- Statut : démarré et vérifié / non vérifié — <raison>

## Demande d'installation (Mode 2)
- Demandeur : <agent>
- Demande : <ce qui était demandé>
- Décision : validée / contre-proposition : <alternative>
- Installé : <élément> (version épinglée, date de vérification)
- Fichiers modifiés : `<paths>`

## Documentation
- `<path>`

## Open Questions
[Anything blocking a version/install decision — if none: "None"]
```

## Project Memory

Save and recall facts that compound across sessions:
- The managed project's existing Docker conventions (compose layout, service naming), once discovered
- Mode 2 requests already handled and their outcome (validated/counter-proposed/refused), so the same discussion isn't replayed

Do NOT save: the content of an `Infra` entry already written — re-readable from `kb/infra/`.
```

- [ ] **Step 2: Verify the frontmatter and required sections are present**

Run: `grep -c "^name: hosa-infra$\|^model: claude-opus-4-8$\|^memory: project$" agents/infra.md`
Expected: `3`

Run: `grep -c "^## Knowledge Base$\|^## Mode 1 — Initial Setup\|^## Mode 2 — On-Demand Installation Request\|^## No Commits$\|^## Output Format$\|^## Project Memory$" agents/infra.md`
Expected: `6`

- [ ] **Step 3: Verify the Review Focus behaviors are explicitly stated**

Run: `grep -c "never report a service as \"in place\"\|say so explicitly in your output" agents/infra.md`
Expected: at least `1`

Run: `grep -c "counter-propose that instead of installing what was asked for" agents/infra.md`
Expected: at least `1`

Run: `grep -c "say so and propose running \`stack\` first" agents/infra.md`
Expected: at least `1`

Run: `grep -c "state your assumption and today's date explicitly" agents/infra.md`
Expected: at least `1`

- [ ] **Step 4: Add the agent to `agents/README.md`**

In the Hosa agents table, after the `hosa-senior-dev` row, add:

```markdown
| [`hosa-infra`](infra.md) | claude-opus-4-8 | Sole owner of installing or provisioning anything for the project Hosa manages — sets up, configures, and runs its Docker environment, installs the chosen stack into it, documents installation, and validates or counter-proposes every later request from another agent for a new server, framework, or dependency. |
```

- [ ] **Step 5: Verify the README edit**

Run: `grep -c "hosa-infra" agents/README.md`
Expected: at least `1`

- [ ] **Step 6: Commit**

```bash
git add agents/infra.md agents/README.md
git commit -m "feat: add hosa-infra agent, sole owner of managed-project installation"
```

---

### Task 2: Create the `infra` skill

**Files:**
- Create: `skills/infra/SKILL.md`

**Interfaces:**
- Consumes: `kb/infra/` (root path), `kb/stack/` (`Stack Decision`) — same contract as Task 1's Mode 1; the skill embeds the same process inline (self-contained skill pattern already used by `stack`/`architecture`/`backlog`), it does not invoke the `Agent` tool on `hosa-infra`.
- Produces: same `hosa/kb/infra/environnement-docker.md` and `kb/infra/log.md` entries as Task 1's Mode 1. Output consumed by whoever invokes `/infra` (human, or chained from `stack`, Task 3).

- [ ] **Step 1: Write `skills/infra/SKILL.md`**

```markdown
---
name: infra
description: Use to set up and configure the managed project's Docker environment and install the chosen stack into it, for real, with a version-pinned, documented result. Second stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture), runs after `stack` has recorded the technical choices.
---

# Infra

Turns a chosen stack into a real, running, documented Docker environment for the managed project — the environment every later stage (and every day-to-day command against the managed project) runs inside.

## Flow

```
Lit kb/infra/ (chemin racine) et kb/stack/ (Stack Decision)
        ↓
Stack Decision absente → propose de lancer `stack` d'abord
        ↓
Lit le code existant du projet cible (Docker déjà présent ?)
et kb/cdc/ (besoins non-fonctionnels impliquant un service
supplémentaire)
        ↓
Détermine la composition Docker, épingle une version récente
et maintenue par service
        ↓
Écrit Dockerfile(s) + docker-compose.yml, démarre réellement
l'environnement, vérifie chaque service
        ↓
Rédige la documentation d'installation dans le projet cible
        ↓
Écrit/complète kb/infra/environnement-docker.md
        ↓
Log kb/infra/log.md
        ↓
Propose d'enchaîner sur `donnees`
```

## Trigger

Manual: `/infra`. Auto: immediately after `stack`, or "mets en place l'environnement Docker", "installe la stack".

---

## Step 1: Find the Managed Project

Read `kb/infra/` for an existing `Infra` entry giving the project's root path. If none exists, ask the user for it and write one — never accept `hosa/app` or `hosa/kb` as the path.

## Step 2: Check the Stack Decision

Read `kb/stack/` for the recorded `Stack Decision`s. If none exists, say so and propose running `stack` first — don't guess what to install.

## Step 3: Read Existing Infrastructure and Non-Functional Needs

Read the managed project's existing code for a Docker setup already in place — extend it, never duplicate it. Read `kb/cdc/`'s `stable` `Exigence`s for any non-functional need implying an extra service (a cache, a queue).

## Step 4: Determine the Composition and Pin Versions

Determine one service per stack component that has to run (application runtime, database, any extra service from Step 3). For each, pick a current, maintained, stable version — never `latest`, always pinned explicitly. If a web-search tool is available, use it to confirm the version currently maintained. If none is available, state the assumption and today's date explicitly, and say the user should correct it if a newer maintained version exists.

## Step 5: Write and Start the Environment

Write the `Dockerfile`(s) and `docker-compose.yml` in the managed project, matching its existing conventions if any. Actually start it (`docker compose up -d` or the project's existing equivalent) and verify each service responds. If Docker isn't available in the current execution environment, say so explicitly — never report a service as "in place" without having actually started and checked it.

## Step 6: Write the Documentation

An installation document in the managed project (e.g. `docs/installation.md` or `INSTALL.md`): prerequisites, how to start/rebuild the environment, and how to request a future addition (point at `hosa-infra`).

## Step 7: Update the `Infra` Entry

Write or update `hosa/kb/infra/environnement-docker.md`:

```markdown
---
type: Infra
title: Environnement Docker — <projet>
description: Services Docker du projet géré, versions épinglées
tags: []
status: stable
generated: { by: hosa-infra/1.0, at: <ISO8601> }
---
## Services
- <service> — <image>:<version épinglée>

## Fichiers
- `<Dockerfile(s)>`
- `<docker-compose.yml>`

## Documentation
- `<path installation.md>`
```

If the file already exists (a re-run), update it in place rather than duplicating it. Log to `kb/infra/log.md` (create if missing) — OKF §9.

## No Commits

You don't commit. Report what changed and let the user decide when to commit.

## Output

```
## Environnement Docker
- Services : <service> (<image>:<version épinglée>)
- Fichiers : `<Dockerfile(s)>`, `<docker-compose.yml>`
- Statut : démarré et vérifié / non vérifié — <raison>

## Documentation
- `<path>`

## Open Questions
[Si rien : "None"]

## Suite
Je lance `donnees` maintenant ?
```
```

- [ ] **Step 2: Verify the frontmatter and trigger text**

Run: `grep -c "^name: infra$" skills/infra/SKILL.md`
Expected: `1`

Run: `grep -c "Manual: \`/infra\`" skills/infra/SKILL.md`
Expected: `1`

- [ ] **Step 3: Verify the missing-`Stack Decision` precondition and the not-verified Docker case are both stated**

Run: `grep -c "propose running \`stack\` first" skills/infra/SKILL.md`
Expected: at least `1`

Run: `grep -c "never report a service as \"in place\"" skills/infra/SKILL.md`
Expected: at least `1`

- [ ] **Step 4: Commit**

```bash
git add skills/infra/SKILL.md
git commit -m "feat: add infra skill, data-structuring pipeline stage 2"
```

---

### Task 3: Wire `infra` into the pipeline and add the installation gate to Core Rules

**Files:**
- Modify: `skills/stack/SKILL.md`
- Modify: `skills/donnees/SKILL.md`
- Modify: `skills/using-simflow/SKILL.md`

**Interfaces:**
- Consumes: Task 2's `infra` skill name and trigger phrasing — the `## Suite` text in `stack` and the `using-simflow` tables must refer to it by the same name and the same trigger phrase already written into `skills/infra/SKILL.md`.
- Produces: the centralized installation-ban and Docker-runtime Core Rules, consumed implicitly by every other agent and skill in the repo from this point on (no other file needs to be edited for the ban to apply).

- [ ] **Step 1: Update `stack`'s pipeline chain and Suite text**

In `skills/stack/SKILL.md`, replace:

```
description: Use to propose and record the technical stack for the project Hosa manages, based on the stable cahier des charges. First stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture).
```

with:

```
description: Use to propose and record the technical stack for the project Hosa manages, based on the stable cahier des charges. First stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture).
```

Then replace:

```
## Suite
Je lance `donnees` maintenant ?
```

with:

```
## Suite
Je lance `infra` maintenant ?
```

- [ ] **Step 2: Verify the `stack` edits**

Run: `grep -c "stack → infra → donnees → schema-app" skills/stack/SKILL.md`
Expected: `1`

Run: `grep -c "Je lance \`infra\` maintenant" skills/stack/SKILL.md`
Expected: `1`

- [ ] **Step 3: Update `donnees`'s pipeline chain and auto-trigger**

In `skills/donnees/SKILL.md`, replace:

```
description: Use to annotate the origin (générée/fournie/saisie) of each donnée listed under `Données en entrée`/`Données en sortie` in stable `kb/cdc/` Exigences. Second stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture), runs after `stack` has recorded the technical choices.
```

with:

```
description: Use to annotate the origin (générée/fournie/saisie) of each donnée listed under `Données en entrée`/`Données en sortie` in stable `kb/cdc/` Exigences. Third stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture), runs after `infra` has set up the managed project's environment.
```

Then replace:

```
Manual: `/donnees`. Auto: immediately after `stack`, or "précise les données du cahier des charges", "qualifie l'origine des données".
```

with:

```
Manual: `/donnees`. Auto: immediately after `infra`, or "précise les données du cahier des charges", "qualifie l'origine des données".
```

- [ ] **Step 4: Verify the `donnees` edits**

Run: `grep -c "stack → infra → donnees → schema-app" skills/donnees/SKILL.md`
Expected: `1`

Run: `grep -c "Auto: immediately after \`infra\`" skills/donnees/SKILL.md`
Expected: `1`

- [ ] **Step 5: Register `infra` in `using-simflow`'s skills table**

In `skills/using-simflow/SKILL.md`, in the skills table, replace:

```markdown
| `stack` | Propose and record the technical stack of the managed project, based on the stable cahier des charges — data-structuring pipeline stage 1 |
| `donnees` | Annotate the origin (générée/fournie/saisie) of data in the cahier des charges — data-structuring pipeline stage 2 |
| `schema-app` | Derive data entities and write application-side data structures + documentation into the managed project — data-structuring pipeline stage 3 |
| `schema-db` | Write database migrations/DDL into the managed project — data-structuring pipeline stage 4 |
| `architecture` | Design and scaffold the software architecture of the managed project, consistent with the CDC, the stack, and the data structures — data-structuring pipeline stage 5 |
| `interface` | Interview each persona, propose a visual identity and design rules, then design and scaffold the interface layer (UX/UI) of the managed project, consistent with the CDC and the software architecture — data-structuring pipeline stage 6 |
| `backlog` | Turn every stable cahier des charges Exigence without a ticket yet into a Product Backlog Ticket carrying the story, a technical feasibility note, an architecture placement note, and an interface placement note — data-structuring pipeline stage 7 |
```

with:

```markdown
| `stack` | Propose and record the technical stack of the managed project, based on the stable cahier des charges — data-structuring pipeline stage 1 |
| `infra` | Set up and configure the managed project's Docker environment, install the chosen stack into it for real, and document installation — data-structuring pipeline stage 2 |
| `donnees` | Annotate the origin (générée/fournie/saisie) of data in the cahier des charges — data-structuring pipeline stage 3 |
| `schema-app` | Derive data entities and write application-side data structures + documentation into the managed project — data-structuring pipeline stage 4 |
| `schema-db` | Write database migrations/DDL into the managed project — data-structuring pipeline stage 5 |
| `architecture` | Design and scaffold the software architecture of the managed project, consistent with the CDC, the stack, and the data structures — data-structuring pipeline stage 6 |
| `interface` | Interview each persona, propose a visual identity and design rules, then design and scaffold the interface layer (UX/UI) of the managed project, consistent with the CDC and the software architecture — data-structuring pipeline stage 7 |
| `backlog` | Turn every stable cahier des charges Exigence without a ticket yet into a Product Backlog Ticket carrying the story, a technical feasibility note, an architecture placement note, and an interface placement note — data-structuring pipeline stage 8 |
```

- [ ] **Step 6: Register `infra` in `using-simflow`'s triggers table**

In `skills/using-simflow/SKILL.md`, in the triggers table, replace:

```markdown
| "Choisis la stack technique", "Quelle stack pour le projet" | `stack` |
| "Précise les données du cahier des charges", "Qualifie l'origine des données" | `donnees` |
```

with:

```markdown
| "Choisis la stack technique", "Quelle stack pour le projet" | `stack` |
| "Mets en place l'environnement Docker", "Installe la stack" | `infra` |
| "Précise les données du cahier des charges", "Qualifie l'origine des données" | `donnees` |
```

- [ ] **Step 7: Add the installation gate and Docker-runtime rule to Core Rules**

In `skills/using-simflow/SKILL.md`, in `## Core Rules`, after the existing "**Trust the user.**" bullet, add:

```markdown
- **Only `hosa-infra` installs.** No other agent ever runs an installation or provisioning command itself, or adds a server, a framework, or a dependency to the managed project on its own. It stops and dispatches `hosa-infra` with what it needs and why, then resumes only once `hosa-infra` confirms it's in place.
- **The managed project runs in Docker.** Once `hosa-infra` has set up its environment, every command against the managed project — build, migration, test, run — executes inside it, not directly on the host.
```

- [ ] **Step 8: Verify all `using-simflow` edits**

Run: `grep -c "^| \`infra\` |" skills/using-simflow/SKILL.md`
Expected: `1`

Run: `grep -c "data-structuring pipeline stage 8" skills/using-simflow/SKILL.md`
Expected: `1`

Run: `grep -c "Only \`hosa-infra\` installs" skills/using-simflow/SKILL.md`
Expected: `1`

Run: `grep -c "The managed project runs in Docker" skills/using-simflow/SKILL.md`
Expected: `1`

- [ ] **Step 9: Commit**

```bash
git add skills/stack/SKILL.md skills/donnees/SKILL.md skills/using-simflow/SKILL.md
git commit -m "feat: chain infra after stack, add installation gate to Core Rules"
```

---

### Task 4: Renumber the remaining pipeline stages

**Files:**
- Modify: `skills/schema-app/SKILL.md`
- Modify: `skills/schema-db/SKILL.md`
- Modify: `skills/architecture/SKILL.md`
- Modify: `skills/interface/SKILL.md`
- Modify: `skills/backlog/SKILL.md`

**Interfaces:**
- Consumes: nothing new — these are description-only edits, no behavioral change to any of the five skills' flows, triggers, or steps.
- Produces: a consistent stage count across every pipeline-stage skill, consumed by nothing downstream (documentation-only), but required for Task 5's consistency check to pass.

- [ ] **Step 1: Renumber `schema-app`**

In `skills/schema-app/SKILL.md`, replace:

```
description: Use to derive data entities from qualified `kb/cdc/` Exigences and write the corresponding data structures, plus their documentation, into the project Hosa manages. Third stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture).
```

with:

```
description: Use to derive data entities from qualified `kb/cdc/` Exigences and write the corresponding data structures, plus their documentation, into the project Hosa manages. Fourth stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture).
```

- [ ] **Step 2: Renumber `schema-db`**

In `skills/schema-db/SKILL.md`, replace:

```
description: Use to write database migrations/DDL for the data entities derived from `kb/cdc/`, into the project Hosa manages. Fourth stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture).
```

with:

```
description: Use to write database migrations/DDL for the data entities derived from `kb/cdc/`, into the project Hosa manages. Fifth stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture).
```

- [ ] **Step 3: Renumber `architecture`**

In `skills/architecture/SKILL.md`, replace:

```
description: Use to design and scaffold the software architecture of the project Hosa manages, consistent with the stable cahier des charges, the chosen stack, and the data structures already written by `schema-app`/`schema-db`. Fifth stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture → interface → backlog).
```

with:

```
description: Use to design and scaffold the software architecture of the project Hosa manages, consistent with the stable cahier des charges, the chosen stack, and the data structures already written by `schema-app`/`schema-db`. Sixth stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture → interface → backlog).
```

- [ ] **Step 4: Renumber `interface`**

In `skills/interface/SKILL.md`, replace:

```
description: Use to design and scaffold the interface layer (UX/UI) of the project Hosa manages, consistent with the stable cahier des charges, the personas' needs, and the software architecture already scaffolded by `architecture`. Sixth stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture → interface → backlog).
```

with:

```
description: Use to design and scaffold the interface layer (UX/UI) of the project Hosa manages, consistent with the stable cahier des charges, the personas' needs, and the software architecture already scaffolded by `architecture`. Seventh stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture → interface → backlog).
```

- [ ] **Step 5: Renumber `backlog`**

In `skills/backlog/SKILL.md`, replace:

```
description: Use to turn every stable cahier des charges Exigence without a ticket yet into a Ticket enriched with a user story (PO), a technical feasibility note (senior dev), an architecture placement note (architect), and an interface placement note (UX/UI designer). Seventh stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture → interface → backlog).
```

with:

```
description: Use to turn every stable cahier des charges Exigence without a ticket yet into a Ticket enriched with a user story (PO), a technical feasibility note (senior dev), an architecture placement note (architect), and an interface placement note (UX/UI designer). Eighth stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture → interface → backlog).
```

- [ ] **Step 6: Verify every renumbering**

Run: `grep -c "Fourth stage of the data-structuring pipeline (stack → infra" skills/schema-app/SKILL.md`
Expected: `1`

Run: `grep -c "Fifth stage of the data-structuring pipeline (stack → infra" skills/schema-db/SKILL.md`
Expected: `1`

Run: `grep -c "Sixth stage of the data-structuring pipeline (stack → infra" skills/architecture/SKILL.md`
Expected: `1`

Run: `grep -c "Seventh stage of the data-structuring pipeline (stack → infra" skills/interface/SKILL.md`
Expected: `1`

Run: `grep -c "Eighth stage of the data-structuring pipeline (stack → infra" skills/backlog/SKILL.md`
Expected: `1`

- [ ] **Step 7: Verify no stale chain (missing `infra`) remains anywhere**

Run: `grep -rn "stack → donnees → schema-app" skills/`
Expected: no output (empty) — every occurrence of the chain now includes `infra`.

- [ ] **Step 8: Commit**

```bash
git add skills/schema-app/SKILL.md skills/schema-db/SKILL.md skills/architecture/SKILL.md skills/interface/SKILL.md skills/backlog/SKILL.md
git commit -m "docs: renumber data-structuring pipeline stages for infra insertion"
```

---

### Task 5: Cross-file consistency verification

**Files:** none created or modified — this task only reads and checks.

**Interfaces:**
- Consumes: every artifact from Tasks 1-4.
- Produces: nothing — a clean pass here is the plan's completion signal.

- [ ] **Step 1: Confirm the agent name is consistent everywhere it's referenced**

Run: `grep -c "hosa-infra" agents/infra.md agents/README.md skills/infra/SKILL.md skills/using-simflow/SKILL.md`
Expected: at least `1` in each of the four files (exact counts vary; a `0` in any file is the failure condition).

- [ ] **Step 2: Confirm no other agent file in `agents/` was modified**

Run: `git diff --stat -- agents/ | grep -v "infra.md\|README.md"`
Expected: no output (empty) — only `agents/infra.md` and `agents/README.md` changed in `agents/`.

- [ ] **Step 3: Confirm the installation gate and Docker rule appear exactly once each**

Run: `grep -rc "Only \`hosa-infra\` installs" skills/using-simflow/SKILL.md`
Expected: `1`

Run: `grep -rc "The managed project runs in Docker" skills/using-simflow/SKILL.md`
Expected: `1`

- [ ] **Step 4: Confirm no new OKF concept type was introduced**

Run: `grep -c "^type: Infra$" agents/infra.md skills/infra/SKILL.md`
Expected: at least `1` in each (confirms both reference the existing `Infra` type, not a new one).

Run: `grep -c "^type: Infra Decision\|^type: Docker" agents/infra.md skills/infra/SKILL.md`
Expected: `0` in both (confirms no new type was invented).

- [ ] **Step 5: Confirm every pipeline-stage skill's chain includes `infra` and no stale stage numbers remain**

Run: `grep -rn "stage of the data-structuring pipeline" skills/*/SKILL.md`
Expected: 8 lines total (`stack`=First, `infra`=Second, `donnees`=Third, `schema-app`=Fourth, `schema-db`=Fifth, `architecture`=Sixth, `interface`=Seventh, `backlog`=Eighth), each one's ordinal matching its position in this list — read the output and confirm by eye.

- [ ] **Step 6: Confirm no plan placeholder text leaked into the written files**

Run: `grep -rn "TBD\|TODO\|<fill" agents/infra.md skills/infra/SKILL.md`
Expected: no output (empty).

- [ ] **Step 7: Report and stop**

No commit for this task — it's a read-only check. If every step above matched its Expected value, the plan is complete; report that to the user. If any step didn't match, that's a plan or content defect: rule on it per this plan's Global Constraints and the spec, fix the affected file, and re-run the failing step's command before reporting completion.
