# Hosa Interface (UX/UI) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `hosa-ux-designer` agent and the `interface` skill — sixth stage of the data-structuring pipeline, inserted between `architecture` and `backlog` — that interviews each persona, proposes a visual identity and design rules for the project, then designs and scaffolds the interface layer in the managed project. Extend `backlog` with a third ticket note (interface placement) and `sprint`'s technical-readiness guard to match.

**Architecture:** Markdown prompt-artifact repo (agents in `agents/`, skills in `skills/`) — no application code, no test runner. "Tests" for this plan are structural verifications (frontmatter present, cross-references resolve, required sections exist) run via Grep/Bash, not unit tests.

**Tech Stack:** Markdown (YAML frontmatter + prose), Claude Code agent/skill conventions already established in this repo.

**Spec:** `docs/superpowers/specs/2026-09-26-hosa-interface-design.md`

## Global Constraints

- Agent files: frontmatter `name`, `description`, `model`, `memory: project` — matches every existing agent in `agents/`.
- Skill files: frontmatter `name`, `description` only — matches every existing skill in `skills/`.
- No skill or agent in this plan commits to git — each ends with "Report what changed, let the user/orchestrating flow decide" (matches every other Hosa skill/agent).
- `hosa-ux-designer` never writes to `hosa/kb/` except the concepts its own skill names explicitly (`Project`'s `## Identité visuelle` section, `Design Rule`, `Infra`'s `## Documentation d'interface` heading) — same "write only what your skill says" discipline as every other Hosa agent.
- `interface` never treats `hosa/app` or `hosa/kb` as its "managed project" target — only the project path recorded in the `Infra` concept.
- OKF logging convention: append to the bundle's `log.md` (create if missing), chronological, most recent entry first, grouped by date.
- Git commits in this plan use the repo's existing convention: plain commit, user's configured `git config user.name`/`user.email` only, no co-author trailer (matches this repo's existing commit history and `skills/using-hosa/SKILL.md`'s Core Rules).
- New pipeline order everywhere it's referenced: `stack → donnees → schema-app → schema-db → architecture → interface → backlog → sprint`.

## Review Focus

1. `interface` invoked before `architecture` ever ran (no `## Documentation d'architecture` heading on the `Infra` entry) — Task 2 Step 1 must say so and propose `architecture` first, not guess a layer to build the interface on.
2. `interface` invoked when `kb/project/` only holds the example `Project` concept — Task 2 Step 3 must say so and propose `hosa` first, rather than writing a visual identity into a placeholder entry.
3. `backlog` invoked before `interface` ever ran (no `## Documentation d'interface` heading on the `Infra` entry) — Task 5's new step must degrade to a one-line fallback note, not block ticket creation.
4. `sprint` invoked against a ticket written directly by `hosa-product-owner` (no `backlog` pass at all — none of the three notes present) — Task 6's guard must treat that the same as a fallback line, not a pass, across all three notes.
5. `hosa-key-user` answering a UI-interview request must not touch the persona's `Besoins`/`Attentes` sections — Task 3 must restate the same restriction already in place for the process-interview mode, only `Pain points`/`Quick wins` may be appended.

---

### Task 1: `hosa-ux-designer` agent

**Files:**
- Create: `agents/ux-designer.md`

**Interfaces:**
- Consumes: none (new agent, no dependency on other tasks in this plan)
- Produces: agent name `hosa-ux-designer`, invocable by `interface` (Task 2) for interviewing personas and designing/scaffolding the interface layer.

- [ ] **Step 1: Write `agents/ux-designer.md`**

```markdown
---
name: hosa-ux-designer
description: Use this agent as the guarantor of the interface layer (UX/UI) for the project Hosa manages. Once the cahier des charges is stable and the software architecture is scaffolded, it interviews each persona (via `hosa-key-user`) about what they need to see, proposes a visual identity and design rules for the project, then designs and scaffolds an interface layer (screens, components, navigation) consistent with the architecture, along with its documentation. Invoke it directly, or from the `interface` skill.
model: claude-opus-4-8
memory: project
---

You are the UX/UI designer for the project Hosa manages. You don't own the cahier des charges, the personas, or the software architecture — `hosa-product-owner`, `hosa-key-user`, and `hosa-architect` do — but you're accountable for what the end user actually sees and interacts with: the visual identity, the design rules, and the screens/components that turn each persona's need into a usable interface. The project you're accountable for is the one Hosa manages — never `hosa/app` or `hosa/kb` themselves, which are Hosa's own tooling and out of your scope.

## Input

A request to design and scaffold the interface layer. If the cahier des charges has no `stable` `Exigence` yet, or the software architecture isn't scaffolded yet, say so and propose running `contestation`/`architecture` first rather than guessing.

## The Knowledge Base

You read from Hosa's KB (`hosa/kb/`) but write your implementation output into the *managed project* — the same one `hosa-architect` already wrote its architecture into.

| Bundle | Type | What you use it for |
|---|---|---|
| `kb/cdc/` | `Exigence` | The business logic the interface has to serve |
| `kb/personnas/` | `Persona` | Who the interface is for — interviewed one at a time via `hosa-key-user` |
| `kb/stack/` | `Stack Decision` | The chosen language/framework, which constrains what the interface layer can be built with |
| `kb/infra/` | `Infra` | The managed project's root path and where its documentation lives |
| `kb/project/` | `Project` | The project's identity — you add its `## Identité visuelle` section |
| `kb/rules/design/` | `Design Rule` | Where you write each design rule you propose and the user validates |

You also read the architecture documentation `hosa-architect` already wrote into the managed project (path recorded in the `Infra` entry) — your interface has to fit the layers/modules that already exist, not redesign them.

**Frontmatter you must fill correctly on every concept you write:**
- `generated: { by: human:<user>, at: <ISO8601> }` — the user asked for this explicitly
- `generated: { by: hosa-ux-designer/1.0, at: <ISO8601> }` — you derived or decided it yourself

**Logging:** append an entry to the touched bundle's `log.md` (create if missing) — chronological, most recent date first, per OKF §9.

## Your Process

1. Read `kb/infra/` for the `Infra` entry giving the managed project's root path — never `hosa/app` or `hosa/kb`. No `Infra` entry, or no `## Documentation d'architecture` heading recorded on it yet → say so and propose `architecture` first. Then read `kb/cdc/` (`stable` `Exigence`), `kb/personnas/`, `kb/stack/` (`Stack Decision`), and the architecture documentation itself.
2. For each persona in `kb/personnas/`, dispatch `hosa-key-user` as a UI-interview request (see `agents/key-user.md`): what this persona needs to see, in what order, which information is priority, what usage constraints apply (mobile, accessibility, autonomy...). One persona at a time — don't batch multiple personas into a single dispatch.
3. Propose a visual identity (color palette, typography, tone) for the project. Once the user validates or adjusts it, write it to `kb/project/`'s existing `Project` concept, under a `## Identité visuelle` heading. If `kb/project/` has no real `Project` concept yet (only the example entry), say so and propose running `hosa` first rather than writing into a placeholder.
4. Propose design rules (information density, reusable components, interaction conventions). Once the user validates or adjusts each one, write it as a `Design Rule` in `kb/rules/design/<slug>.md`.
5. Design the interface layer — screens, components, navigation — consistent with the architecture already scaffolded. Say what you chose and why.
6. Scaffold it for real in the managed project: folders, base components, style/theme tokens matching the chosen stack and the visual identity from step 3. Extend anything that already exists rather than duplicating it.
7. Write the interface documentation in the managed project (never in `hosa/kb`).
8. Update the `Infra` entry with the documentation's path, under its own `## Documentation d'interface` heading.

## No Commits

You do not commit. Report what you changed and let the user or the orchestrating skill decide when to commit, per the Hosa core rule that commits are always in the user's name only.

## Output Format

```
## Interviews personas
- <persona> — [needs surfaced]

## Identité visuelle
[Palette/typography/tone chosen, and where it's written]

## Règles de design
- `kb/rules/design/<slug>.md` — [rule]

## Couche interface conçue
[Screens/components chosen and why]

## Structures créées
- `<path>` — [folder/component scaffolded]

## Documentation
- `<path>`

## Open Questions
[Anything blocking a design decision — if none: "None"]
```

## Project Memory

Save and recall facts that compound across sessions:
- The visual identity already validated by the user for this project, so it isn't reproposed from scratch every session
- Recurring interface conventions of the managed project (folder structure, component patterns already in place)

Do NOT save: the content of an interface already scaffolded — re-readable from the managed project's own code, nor individual UI-interview answers — already reported in session output.
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "^name: hosa-ux-designer$" agents/ux-designer.md` — Expected: `1`
Run: `grep -c "hosa-key-user" agents/ux-designer.md` — Expected: at least `2`
Run: `grep -c "## Identité visuelle" agents/ux-designer.md` — Expected: at least `2`
Run: `grep -c "You do not commit" agents/ux-designer.md` — Expected: `1`

- [ ] **Step 3: Commit**

```bash
git add agents/ux-designer.md
git commit -m "feat: add hosa-ux-designer agent"
```

---

### Task 2: `interface` skill

**Files:**
- Create: `skills/interface/SKILL.md`

**Interfaces:**
- Consumes: `Infra` entry with `## Documentation d'architecture` heading (Task 4's chain from `architecture`), `stable` `Exigence` concepts in `kb/cdc/`, `Persona` concepts in `kb/personnas/`, `Stack Decision` concepts in `kb/stack/`
- Produces: `## Identité visuelle` section on `kb/project/`'s `Project` concept, `Design Rule` concepts in `kb/rules/design/`, scaffolded interface files and documentation in the managed project, `## Documentation d'interface` heading on the `Infra` entry — consumed by `backlog` (Task 5)

- [ ] **Step 1: Write `skills/interface/SKILL.md`**

```markdown
---
name: interface
description: Use to design and scaffold the interface layer (UX/UI) of the project Hosa manages, consistent with the stable cahier des charges, the personas' needs, and the software architecture already scaffolded by `architecture`. Sixth stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture → interface → backlog).
---

# Interface

Turns the business logic (CDC), what each persona needs to see, and the existing software architecture into a real, scaffolded interface layer in the managed project — plus a visual identity and design rules for the whole project.

## Flow

```
Lit kb/cdc stable, kb/personnas, kb/stack, et la doc
d'architecture (Infra → ## Documentation d'architecture)
        ↓
Si l'une des sources manque, le dit et propose de lancer
l'étape manquante d'abord
        ↓
Pour chaque persona : dispatch hosa-key-user (UI-interview) —
un persona à la fois
        ↓
Propose une identité visuelle → kb/project/ (## Identité
visuelle)
        ↓
Propose des règles de design → Design Rule dans kb/rules/design/
        ↓
Conçoit la couche interface (écrans, composants, navigation)
cohérente avec l'architecture
        ↓
Scaffold l'interface dans le projet cible
        ↓
Rédige la documentation d'interface dans le projet cible
        ↓
Met à jour l'entrée Infra avec le chemin de la doc
        ↓
Propose de lancer `backlog`
```

## Trigger

Manual: `/interface`. Auto: immediately after `architecture`, or "conçois l'interface", "crée l'identité visuelle", "définis l'UX/UI du projet".

---

## Step 1: Gather Inputs

Read `kb/infra/` for the `Infra` entry giving the managed project's root path — the scaffold target is always that path, never `hosa/app` or `hosa/kb`. If there's no `Infra` entry, or no `## Documentation d'architecture` heading recorded on it yet, say so and propose running `architecture` first; don't guess a path or a layer to build on.

Read `kb/cdc/` for `stable` `Exigence`s, `kb/personnas/` for every persona, `kb/stack/` for `Stack Decision`s, and the architecture documentation itself (path from the `Infra` entry).

## Step 2: Interview Each Persona

For each persona in `kb/personnas/`, dispatch `hosa-key-user` as a UI-interview request: what this persona needs to see, in what order, which information is priority, what usage constraints apply. One persona at a time.

## Step 3: Propose the Visual Identity

Propose a visual identity (color palette, typography, tone) for the project. Once the user validates or adjusts it, write it into `kb/project/`'s existing `Project` concept, under a `## Identité visuelle` heading. If `kb/project/` has no real `Project` concept yet (only the example entry), say so and propose running `hosa` first rather than writing into a placeholder.

## Step 4: Propose Design Rules

Propose design rules (information density, reusable components, interaction conventions). For each one the user validates or adjusts, write it to `kb/rules/design/<slug>.md`:

```markdown
---
type: Design Rule
title: <titre court>
description: <résumé une ligne>
tags: []
status: stable
generated: { by: human:<user>, at: <ISO8601> }
---
## Règle
<contenu>

## Justification
<pourquoi>
```

Log each one to `kb/rules/design/log.md` (create if missing) — OKF §9.

## Step 5: Design the Interface Layer

Design the screens, components, and navigation that let the business logic (CDC), what each persona needs to see, and the existing software architecture cohere into one usable interface. Say what you chose and why.

## Step 6: Scaffold It

Write the interface layer for real in the managed project: folders, base components, style/theme tokens matching the chosen stack and the visual identity from Step 3. If parts of the interface already exist, extend them rather than duplicating.

## Step 7: Write the Documentation

An interface document in the managed project (e.g. `docs/interface.md`, or wherever the project's existing docs live) — never in `hosa/kb`. Cover the screens/components chosen, their relationship to the architecture, and the visual identity/design rules they follow.

## Step 8: Update the `Infra` Entry

Add the interface documentation's path to the `Infra` entry under its own `## Documentation d'interface` heading — a fixed heading, not a bare line, so a later reader (`backlog`) can tell it apart from the architecture documentation path `architecture` also records there. Log the update to `kb/infra/log.md`.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit each.

## Output

```
## Interviews personas
- <persona> — [besoins surfacés]

## Identité visuelle
[Palette/typo/ton retenus, et où c'est écrit]

## Règles de design
- `kb/rules/design/<slug>.md` — [règle]

## Couche interface conçue
[Écrans/composants retenus et pourquoi]

## Structures créées
- `<path>` — [dossier/composant scaffoldé]

## Documentation
- `<path>`

## Suite
Je lance `backlog` maintenant ?
```
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "^name: interface$" skills/interface/SKILL.md` — Expected: `1`
Run: `grep -c "type: Design Rule" skills/interface/SKILL.md` — Expected: at least `1`
Run: `grep -c "## Documentation d'interface" skills/interface/SKILL.md` — Expected: at least `1`
Run: `grep -c "propose running \`architecture\` first\|propose running .architecture. first" skills/interface/SKILL.md` — Expected: at least `1`
Run: `grep -c "propose running \`hosa\` first" skills/interface/SKILL.md` — Expected: `1`

- [ ] **Step 3: Commit**

```bash
git add skills/interface/SKILL.md
git commit -m "feat: add interface skill, data-structuring pipeline stage 6"
```

---

### Task 3: Update `hosa-key-user` to answer a UI-interview request

**Files:**
- Modify: `agents/key-user.md`

**Interfaces:**
- Consumes: `hosa-ux-designer` agent name (Task 1)
- Produces: none new — adds a third dispatch mode alongside identification/recette and process-interview.

- [ ] **Step 1: Add the UI-interview request to the Input list**

Find:

```markdown
- **A process-interview request** — from `hosa-product-owner` (via `interview`/`contestation`) or `hosa-data-engineer` (via `donnees`), targeted questions about one business process or one specific donnée (its objective for this persona, données en entrée/sortie, what they concretely do) — answer in character
- **Both** — a recette where the persona's KB entry is too thin to embody convincingly, so you enrich it first
```

Replace with:

```markdown
- **A process-interview request** — from `hosa-product-owner` (via `interview`/`contestation`) or `hosa-data-engineer` (via `donnees`), targeted questions about one business process or one specific donnée (its objective for this persona, données en entrée/sortie, what they concretely do) — answer in character
- **A UI-interview request** — from `hosa-ux-designer` (via `interface`), targeted questions about what this persona needs to see: which information is priority, in what order, what usage constraints apply (mobile, accessibility, autonomy...) — answer in character
- **Both** — a recette where the persona's KB entry is too thin to embody convincingly, so you enrich it first
```

- [ ] **Step 2: Add the UI-interview answer step**

Find:

```markdown
## Step 2 (alternate): Answer a process-interview request

Only for a process-interview request from `hosa-product-owner` or `hosa-data-engineer`, not a recette.

1. Answer each question in character: what this persona needs before they can act in this process (données en entrée), what they produce or hand off (données en sortie), what they concretely do, what they're trying to accomplish here.
2. If an answer reveals a pain point or quick win not already on file, append it to the persona's `Pain points` / `Quick wins` sections in `kb/personnas/<slug>.md` — same convention as during recette — and append an entry to `kb/personnas/log.md` (OKF §9). Don't touch `Besoins`/`Attentes` here — those are Step 1's responsibility.
3. If you genuinely don't know how this persona would answer — the question needs a fact that isn't in their KB entry and isn't derivable from it — say so. Don't invent a specific process detail with no basis.

Answer inline, in the persona's voice, structured by whichever questions were asked — the Output template below is for identification and recette runs, not this mode.

## No Commits
```

Replace with:

```markdown
## Step 2 (alternate): Answer a process-interview request

Only for a process-interview request from `hosa-product-owner` or `hosa-data-engineer`, not a recette.

1. Answer each question in character: what this persona needs before they can act in this process (données en entrée), what they produce or hand off (données en sortie), what they concretely do, what they're trying to accomplish here.
2. If an answer reveals a pain point or quick win not already on file, append it to the persona's `Pain points` / `Quick wins` sections in `kb/personnas/<slug>.md` — same convention as during recette — and append an entry to `kb/personnas/log.md` (OKF §9). Don't touch `Besoins`/`Attentes` here — those are Step 1's responsibility.
3. If you genuinely don't know how this persona would answer — the question needs a fact that isn't in their KB entry and isn't derivable from it — say so. Don't invent a specific process detail with no basis.

Answer inline, in the persona's voice, structured by whichever questions were asked — the Output template below is for identification and recette runs, not this mode.

## Step 2 (alternate 2): Answer a UI-interview request

Only for a UI-interview request from `hosa-ux-designer`, not a recette or a process-interview.

1. Answer each question in character: what this persona needs to see, in what order, which information is priority, what usage constraints they have (mobile, accessibility, autonomy...).
2. If an answer reveals a pain point or quick win not already on file, append it to the persona's `Pain points` / `Quick wins` sections in `kb/personnas/<slug>.md` — same convention as during recette or a process-interview — and append an entry to `kb/personnas/log.md` (OKF §9). Don't touch `Besoins`/`Attentes` here — those are Step 1's responsibility.
3. If you genuinely don't know how this persona would answer — the question needs a fact that isn't in their KB entry and isn't derivable from it — say so. Don't invent a specific screen detail with no basis.

Answer inline, in the persona's voice, structured by whichever questions were asked — the Output template below is for identification and recette runs, not this mode.

## No Commits
```

- [ ] **Step 3: Verify structure**

Run: `grep -c "hosa-ux-designer" agents/key-user.md` — Expected: at least `2`
Run: `grep -c "## Step 2 (alternate 2)" agents/key-user.md` — Expected: `1`
Run: `grep -c "Don't touch \`Besoins\`/\`Attentes\` here" agents/key-user.md` — Expected: `2`

- [ ] **Step 4: Commit**

```bash
git add agents/key-user.md
git commit -m "feat: add UI-interview request mode to hosa-key-user"
```

---

### Task 4: Update `architecture` to chain into `interface` instead of `backlog`

**Files:**
- Modify: `skills/architecture/SKILL.md`

**Interfaces:**
- Consumes: `interface` skill name (Task 2)
- Produces: none new — reuses the existing scaffolding/documentation output, now proposes `interface` as its next step instead of `backlog`.

- [ ] **Step 1: Update the frontmatter description**

Find:

```markdown
description: Use to design and scaffold the software architecture of the project Hosa manages, consistent with the stable cahier des charges, the chosen stack, and the data structures already written by `schema-app`/`schema-db`. Fifth stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture → backlog).
```

Replace with:

```markdown
description: Use to design and scaffold the software architecture of the project Hosa manages, consistent with the stable cahier des charges, the chosen stack, and the data structures already written by `schema-app`/`schema-db`. Fifth stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture → interface → backlog).
```

- [ ] **Step 2: Update the Output's "Suite" section**

Find:

```markdown
## Documentation
- `<path>`

## Suite
Je lance `backlog` maintenant ?
```
```

Replace with:

```markdown
## Documentation
- `<path>`

## Suite
Je lance `interface` maintenant ?
```
```

- [ ] **Step 3: Verify structure**

Run: `grep -c "Je lance \`interface\` maintenant" skills/architecture/SKILL.md` — Expected: `1`
Run: `grep -c "Je lance \`backlog\` maintenant" skills/architecture/SKILL.md` — Expected: `0`
Run: `grep -c "architecture → interface → backlog" skills/architecture/SKILL.md` — Expected: `1`

- [ ] **Step 4: Commit**

```bash
git add skills/architecture/SKILL.md
git commit -m "feat: chain architecture into interface instead of backlog"
```

---

### Task 5: Update `backlog` to add the Interface Placement note

**Files:**
- Modify: `skills/backlog/SKILL.md`

**Interfaces:**
- Consumes: `## Documentation d'interface` heading on the `Infra` entry, normally already written by `interface` (Task 2)
- Produces: `## Placement interface (UX/UI)` section on every `Ticket` it writes — consumed by `sprint`'s guard (Task 6)

- [ ] **Step 1: Update the frontmatter description**

Find:

```markdown
description: Use to turn every stable cahier des charges Exigence without a ticket yet into a Ticket enriched with a user story (PO), a technical feasibility note (senior dev), and an architecture placement note (architect). Sixth and last stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture → backlog).
```

Replace with:

```markdown
description: Use to turn every stable cahier des charges Exigence without a ticket yet into a Ticket enriched with a user story (PO), a technical feasibility note (senior dev), an architecture placement note (architect), and an interface placement note (UX/UI designer). Seventh stage of the data-structuring pipeline (stack → donnees → schema-app → schema-db → architecture → interface → backlog).
```

- [ ] **Step 2: Update the intro paragraph, Flow diagram, and Trigger**

Find:

```markdown
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
Propose de lancer sprint
```

## Trigger

Manual: `/backlog`. Auto: immediately after `architecture`, or "crée le product backlog", "génère les tickets à partir du cahier des charges".
```

Replace with:

```markdown
Turns "what the application must do" (the stable cahier des charges) into Product Backlog tickets — each one carrying the business story, its technical feasibility, where it lands in the architecture, and where it lands in the interface, so nothing enters `kb/tickets/` disconnected from the technical reality already decided by `stack`, `architecture`, and `interface`.

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
Ajoute un placement interface (rôle UX/UI designer), ou une
ligne "pas encore déterminé" si aucune doc d'interface n'existe
        ↓
Log kb/tickets/log.md
        ↓
Propose de lancer sprint
```

## Trigger

Manual: `/backlog`. Auto: immediately after `interface`, or "crée le product backlog", "génère les tickets à partir du cahier des charges".
```

- [ ] **Step 3: Insert the new step between the existing Step 4 and Step 5, and renumber Log**

Find:

```markdown
Never block ticket creation on a missing architecture doc.

### Step 5 : Log

Log each ticket created to `kb/tickets/log.md` (create if missing) — chronological, most recent date first, per OKF §9.
```

Replace with:

```markdown
Never block ticket creation on a missing architecture doc.

### Step 5 : Placement interface (rôle UX/UI designer)

Lit `kb/infra/` pour l'en-tête `## Documentation d'interface` de l'entrée `Infra` (écrit par `interface`) — cet en-tête, spécifiquement, distinct de la doc d'architecture, du dictionnaire de données ou des migrations que la même entrée `Infra` peut aussi porter. S'il est présent, lit la documentation qu'il référence et ajoute au ticket :

```markdown
## Placement interface (UX/UI)
[Écran/composant concerné et pourquoi]
```

Si aucun chemin de documentation d'interface n'est encore enregistré (`interface` n'a pas encore tourné), ajoute à la place :

```markdown
## Placement interface (UX/UI)
Interface pas encore scaffoldée — placement non déterminé.
```

Ne bloque jamais la création du ticket sur une doc d'interface manquante.

### Step 6 : Log

Log each ticket created to `kb/tickets/log.md` (create if missing) — chronological, most recent date first, per OKF §9.
```

- [ ] **Step 4: Verify structure**

Run: `grep -c "^name: backlog$" skills/backlog/SKILL.md` — Expected: `1`
Run: `grep -c "Interface pas encore scaffoldée" skills/backlog/SKILL.md` — Expected: `1`
Run: `grep -c "### Step 5 : Placement interface" skills/backlog/SKILL.md` — Expected: `1`
Run: `grep -c "### Step 6 : Log" skills/backlog/SKILL.md` — Expected: `1`
Run: `grep -c "Auto: immediately after \`interface\`" skills/backlog/SKILL.md` — Expected: `1`
Run: `grep -c "Seventh stage" skills/backlog/SKILL.md` — Expected: `1`

- [ ] **Step 5: Commit**

```bash
git add skills/backlog/SKILL.md
git commit -m "feat: add interface placement note to backlog, data-structuring pipeline stage 7"
```

---

### Task 6: Update `sprint`'s technical-readiness guard for the third note

**Files:**
- Modify: `skills/sprint/SKILL.md`

**Interfaces:**
- Consumes: `## Placement interface (UX/UI)` section on `Ticket` concepts, written by `backlog` (Task 5)
- Produces: none new — extends the existing guard logic to a third section.

- [ ] **Step 1: Update the frontmatter description and intro paragraph**

Find:

```markdown
description: Use to compose a sprint from the Product Backlog — dispatches tickets in `hosa-product-owner`'s priority order, up to a given capacity, guarding against dispatching a ticket whose technical feasibility or architecture placement was never actually evaluated. Follows the data-structuring pipeline's last stage (`backlog`), but is itself delivery planning, not data structuring.
---

# Sprint

Turns the Product Backlog (`kb/tickets/`) into a concrete sprint — a bounded set of tickets whose technical feasibility and architecture placement have both been actually evaluated, not left on `backlog`'s fallback line.
```

Replace with:

```markdown
description: Use to compose a sprint from the Product Backlog — dispatches tickets in `hosa-product-owner`'s priority order, up to a given capacity, guarding against dispatching a ticket whose technical feasibility, architecture placement, or interface placement was never actually evaluated. Follows the data-structuring pipeline's last stage (`backlog`), but is itself delivery planning, not data structuring.
---

# Sprint

Turns the Product Backlog (`kb/tickets/`) into a concrete sprint — a bounded set of tickets whose technical feasibility, architecture placement, and interface placement have all been actually evaluated, not left on `backlog`'s fallback line.
```

- [ ] **Step 2: Update the Step 4 guard**

Find:

```markdown
## Step 4: Dispatch Up to Capacity (technical-readiness guard)

Walk the tickets in that order, up to the capacity from Step 1:

- Read the ticket's `## Note technique (senior dev)` and `## Placement architecture (architecte)` sections.
- If either section is missing entirely, or still holds `backlog`'s fallback line ("Stack pas encore choisie — faisabilité non évaluée." or "Architecture pas encore scaffoldée — placement non déterminé."), treat it the same way: say so and propose filling the gap now — running `stack`/`architecture`, or getting a real opinion from the senior-dev/architect roles — rather than dispatching the ticket without knowing whether it's actually buildable. A ticket written directly by `hosa-product-owner` without going through `backlog` has no such sections at all — that's the same gap, not a pass.
- If the user fills the gap, re-read the updated note and re-evaluate this ticket against it. If the gap stays unfilled, this ticket does not enter this sprint — it stays in the backlog, and capacity is not spent on it.
- Otherwise (both notes are real), dispatch it: write `sprint: <slug>` into the ticket's frontmatter, add it to the sprint's ticket list.
- If capacity is reached before the ticket list runs out, stop — the rest stay in the backlog for a future sprint. If fewer eligible tickets exist than the requested capacity, dispatch every eligible one and say so — not an error.
```

Replace with:

```markdown
## Step 4: Dispatch Up to Capacity (technical-readiness guard)

Walk the tickets in that order, up to the capacity from Step 1:

- Read the ticket's `## Note technique (senior dev)`, `## Placement architecture (architecte)`, and `## Placement interface (UX/UI)` sections.
- If any of the three sections is missing entirely, or still holds `backlog`'s fallback line ("Stack pas encore choisie — faisabilité non évaluée.", "Architecture pas encore scaffoldée — placement non déterminé.", or "Interface pas encore scaffoldée — placement non déterminé."), treat it the same way: say so and propose filling the gap now — running `stack`/`architecture`/`interface`, or getting a real opinion from the senior-dev/architect/UX-UI-designer roles — rather than dispatching the ticket without knowing whether it's actually buildable. A ticket written directly by `hosa-product-owner` without going through `backlog` has no such sections at all — that's the same gap, not a pass.
- If the user fills the gap, re-read the updated note and re-evaluate this ticket against it. If the gap stays unfilled, this ticket does not enter this sprint — it stays in the backlog, and capacity is not spent on it.
- Otherwise (all three notes are real), dispatch it: write `sprint: <slug>` into the ticket's frontmatter, add it to the sprint's ticket list.
- If capacity is reached before the ticket list runs out, stop — the rest stay in the backlog for a future sprint. If fewer eligible tickets exist than the requested capacity, dispatch every eligible one and say so — not an error.
```

- [ ] **Step 3: Verify structure**

Run: `grep -c "Placement interface (UX/UI)" skills/sprint/SKILL.md` — Expected: at least `2`
Run: `grep -c "Interface pas encore scaffoldée" skills/sprint/SKILL.md` — Expected: `1`
Run: `grep -c "all three notes are real" skills/sprint/SKILL.md` — Expected: `1`

- [ ] **Step 4: Commit**

```bash
git add skills/sprint/SKILL.md
git commit -m "feat: extend sprint's technical-readiness guard to interface placement"
```

---

### Task 7: Register `interface` in `using-hosa`, renumber `backlog`/`sprint`

**Files:**
- Modify: `skills/using-hosa/SKILL.md`

**Interfaces:**
- Consumes: skill name `interface` (Task 2)
- Produces: none new — discoverability wiring only.

- [ ] **Step 1: Update the data-structuring pipeline rows in the skills table**

Find:

```markdown
| `architecture` | Design and scaffold the software architecture of the managed project, consistent with the CDC, the stack, and the data structures — data-structuring pipeline stage 5 |
| `backlog` | Turn every stable cahier des charges Exigence without a ticket yet into a Product Backlog Ticket carrying the story, a technical feasibility note, and an architecture placement note — data-structuring pipeline stage 6 |
| `sprint` | Compose a sprint from the Product Backlog — dispatch tickets in priority order up to a given capacity, guarding against dispatching one whose technical feasibility or architecture placement was never actually evaluated — follow-on to the data-structuring pipeline |
```

Replace with:

```markdown
| `architecture` | Design and scaffold the software architecture of the managed project, consistent with the CDC, the stack, and the data structures — data-structuring pipeline stage 5 |
| `interface` | Interview each persona, propose a visual identity and design rules, then design and scaffold the interface layer (UX/UI) of the managed project, consistent with the CDC and the software architecture — data-structuring pipeline stage 6 |
| `backlog` | Turn every stable cahier des charges Exigence without a ticket yet into a Product Backlog Ticket carrying the story, a technical feasibility note, an architecture placement note, and an interface placement note — data-structuring pipeline stage 7 |
| `sprint` | Compose a sprint from the Product Backlog — dispatch tickets in priority order up to a given capacity, guarding against dispatching one whose technical feasibility, architecture placement, or interface placement was never actually evaluated — follow-on to the data-structuring pipeline |
```

- [ ] **Step 2: Add a row to the triggers table**

Find:

```markdown
| "Crée l'architecture logicielle", "Génère l'architecture de l'application" | `architecture` |
| "Crée le product backlog", "Génère les tickets à partir du cahier des charges" | `backlog` |
```

Replace with:

```markdown
| "Crée l'architecture logicielle", "Génère l'architecture de l'application" | `architecture` |
| "Conçois l'interface", "Crée l'identité visuelle", "Définis l'UX/UI du projet" | `interface` |
| "Crée le product backlog", "Génère les tickets à partir du cahier des charges" | `backlog` |
```

- [ ] **Step 3: Verify structure**

Run: `grep -c "^| \`interface\`" skills/using-hosa/SKILL.md` — Expected: `2` (1 row in the skills table + 1 row in the triggers table)
Run: `grep -c "data-structuring pipeline stage 7" skills/using-hosa/SKILL.md` — Expected: `1`

- [ ] **Step 4: Commit**

```bash
git add skills/using-hosa/SKILL.md
git commit -m "docs: register interface skill in using-hosa, renumber backlog/sprint"
```

---

### Task 8: Register `hosa-ux-designer` in `agents/README.md`

**Files:**
- Modify: `agents/README.md`

**Interfaces:**
- Consumes: agent name `hosa-ux-designer` (Task 1)
- Produces: none new — discoverability wiring only.

- [ ] **Step 1: Add a row to the Hosa agents table**

Find:

```markdown
| [`hosa-architect`](architect.md) | claude-opus-4-8 | Guarantor of software architecture for the managed project — designs and scaffolds an architecture consistent with the business logic, the chosen stack, and the finished data structures. |
| [`hosa-sprint-planner`](sprint-planner.md) | claude-opus-4-8 | Composes each sprint from the Product Backlog — dispatches tickets in `hosa-product-owner`'s priority order up to a given capacity, guarding against dispatching a ticket whose technical feasibility or architecture placement was never actually evaluated. |
```

Replace with:

```markdown
| [`hosa-architect`](architect.md) | claude-opus-4-8 | Guarantor of software architecture for the managed project — designs and scaffolds an architecture consistent with the business logic, the chosen stack, and the finished data structures. |
| [`hosa-ux-designer`](ux-designer.md) | claude-opus-4-8 | Guarantor of the interface layer (UX/UI) for the managed project — interviews each persona, proposes a visual identity and design rules, then designs and scaffolds an interface consistent with the business logic and the software architecture. |
| [`hosa-sprint-planner`](sprint-planner.md) | claude-opus-4-8 | Composes each sprint from the Product Backlog — dispatches tickets in `hosa-product-owner`'s priority order up to a given capacity, guarding against dispatching a ticket whose technical feasibility, architecture placement, or interface placement was never actually evaluated. |
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "hosa-ux-designer" agents/README.md` — Expected: at least `1`
Run: `grep -c "interface placement was never actually evaluated" agents/README.md` — Expected: `1`

- [ ] **Step 3: Commit**

```bash
git add agents/README.md
git commit -m "docs: register hosa-ux-designer in agents README"
```

---

### Task 9: Cross-file consistency pass

**Files:**
- None created or modified — read-only verification across Tasks 1-8.

**Interfaces:**
- Consumes: every file touched by Tasks 1-8
- Produces: nothing — this task either passes or sends work back to the relevant earlier task.

- [ ] **Step 1: Every referenced agent/skill name actually exists**

Run: `grep -l "hosa-ux-designer" agents/*.md skills/*/SKILL.md`
Expected: includes `agents/ux-designer.md`, `agents/key-user.md`, `skills/interface/SKILL.md`, `agents/README.md`

Run: `grep -l "\`interface\`" skills/architecture/SKILL.md skills/backlog/SKILL.md skills/using-hosa/SKILL.md`
Expected: all three files listed

- [ ] **Step 2: The pipeline chain is unbroken end to end**

Run: `grep -c "Je lance \`interface\` maintenant" skills/architecture/SKILL.md`
Expected: `1`

Run: `grep -c "Auto: immediately after \`interface\`" skills/backlog/SKILL.md`
Expected: `1`

Run: `grep -c "Propose de lancer \`backlog\`" skills/interface/SKILL.md`
Expected: at least `1`

- [ ] **Step 3: `using-hosa` and `agents/README.md` entries match actual file names**

Run: `ls skills/ | grep -E "^interface$"`
Expected: `interface` listed

Run: `ls agents/ | grep -E "^ux-designer\.md$"`
Expected: `ux-designer.md` listed

- [ ] **Step 4: No skill or agent in this plan commits**

Run: `grep -L "You don't commit\|You do not commit" skills/interface/SKILL.md agents/ux-designer.md`
Expected: empty output (both files contain one of the two phrases)

- [ ] **Step 5: The three-note guard is consistent everywhere it's checked**

Run: `grep -c "Placement interface (UX/UI)" skills/backlog/SKILL.md skills/sprint/SKILL.md`
Expected: `skills/backlog/SKILL.md` at least `1`, `skills/sprint/SKILL.md` at least `2`

If any check in Steps 1-5 fails, fix the specific file it points to (go back to that file's task) rather than patching around it here.

- [ ] **Step 6: No commit needed** — this task is verification-only; nothing changed.

---

## Self-Review Notes

- **Spec coverage:** §1 `hosa-ux-designer` agent → Task 1. §2 `interface` skill → Task 2. §3 `hosa-key-user` UI-interview mode → Task 3. §4 `architecture` chaining change → Task 4. §5 `backlog` Placement interface step → Task 5. §6 `sprint` guard extension → Task 6. §7 `using-hosa` registry → Task 7. Agent discoverability in `agents/README.md` (matches existing convention, implicit in every prior iteration's registry step) → Task 8. §Hors scope (v1) → deliberately no task (no new OKF type, no wireframe/image generation, no drift detection, no automated a11y testing).
- **Placeholder scan:** no TBD/TODO; every agent/skill file content and Find/Replace block above is complete, not a description of content.
- **Type consistency:** agent name `hosa-ux-designer` used identically across Tasks 1, 3, 8. Skill name `interface` used identically across Tasks 2, 4, 5, 7. `Design Rule` frontmatter shape in Task 2 matches the shape given in the spec. Section heading `## Placement interface (UX/UI)` used identically in Task 5 (written by `backlog`) and Task 6 (read by `sprint`'s guard) — same string, so the guard's grep actually matches what gets written.
- **Review Focus:** all 5 items map to a specific instruction inside a specific task (see numbered list above) — none left uncovered.
