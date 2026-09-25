---
name: using-simflow
description: Bootstrap skill — always loaded at session start. Explains what SimFlow is, what skills exist, and when to trigger them automatically.
---

# SimFlow

You have SimFlow — a lightweight full dev lifecycle plugin for Claude Code and Codex. SimFlow gives you skills and agents to understand, build, test, review, and debug software without ceremony.

## Skills

Use the `Skill` tool to invoke any of these. The skill loads its full instructions — follow them exactly.

| Skill | What it does |
|---|---|
| `simflow:understand` | Brainstorm + grill an idea → write spec → quiz user → commit |
| `simflow:build` | Read spec or description → plan → implement task by task → quiz → commit |
| `simflow:iterate` | Change or extend existing code → light grill → targeted plan → quiz → commit |
| `simflow:dispatch` | Fan out independent tasks to agents in parallel |
| `simflow:test` | Run tests, identify gaps, write new tests, commit them |
| `simflow:review` | Check implementation against spec → fix gaps → loop until clean |
| `simflow:debug` | Systematic root cause analysis → confirm with user → fix → commit |
| `simflow:status` | Snapshot of project state — spec, progress, tests, next step |
| `hosa` | Initialize/update the Hosa project's identity and personas in the KB (`hosa/kb/`) |
| `recette` | Business/functional acceptance testing of a feature or ticket, from a specific persona's point of view |
| `interview` | Gather cahier des charges input from processes, personas, and the user — CDC pipeline stage 1 |
| `redaction` | Turn interview notes into structured `Exigence` concepts in `kb/cdc/` — CDC pipeline stage 2 |
| `relecture` | Check the cahier des charges for precision, completeness, and consistency — CDC pipeline stage 3 |
| `contestation` | Final independent challenge pass on the cahier des charges — CDC pipeline stage 4 |
| `stack` | Propose and record the technical stack of the managed project, based on the stable cahier des charges — data-structuring pipeline stage 1 |
| `donnees` | Annotate the origin (générée/fournie/saisie) of data in the cahier des charges — data-structuring pipeline stage 2 |
| `schema-app` | Derive data entities and write application-side data structures + documentation into the managed project — data-structuring pipeline stage 3 |
| `schema-db` | Write database migrations/DDL into the managed project — data-structuring pipeline stage 4 |
| `architecture` | Design and scaffold the software architecture of the managed project, consistent with the CDC, the stack, and the data structures — data-structuring pipeline stage 5 |
| `backlog` | Turn every stable cahier des charges Exigence without a ticket yet into a Product Backlog Ticket carrying the story, a technical feasibility note, and an architecture placement note — data-structuring pipeline stage 6 |

## Triggering Rules

**Auto-trigger** the matching skill immediately via the `Skill` tool — without asking for permission — when the user's message clearly matches a skill's purpose:

| User says something like... | Trigger |
|---|---|
| "I have an idea for...", "I want to build...", "Let's plan..." | `simflow:understand` |
| "Implement this", "Build it", "Add this feature", "Write the code" | `simflow:build` |
| "Change how X works", "Refactor this", "Update this", "Add X to existing Y" | `simflow:iterate` |
| "Run these in parallel", "Fan out", "Do these simultaneously" | `simflow:dispatch` |
| "Test this", "Run tests", "Check if it works" | `simflow:test` |
| "Does this match the spec?", "Check requirements", "Is everything implemented?" | `simflow:review` |
| "It's broken", "This isn't working", "I'm getting an error", "There's a bug" | `simflow:debug` |
| "Where are we?", "What's done?", "Catch me up", "What's left?" | `simflow:status` |
| "Initialise le projet", "Configure hosa", "Crée un persona pour..." | `hosa` |
| "Fais une recette de...", "Valide ça avec [persona]", "Est-ce que ça répond au besoin de..." | `recette` |
| "Rédige le cahier des charges", "Interview les personas", "Démarre le cahier des charges" | `interview` |
| "Rédige les exigences", "Écris le cahier des charges" (avec notes fournies) | `redaction` |
| "Relis le cahier des charges" | `relecture` |
| "Challenge le cahier des charges" | `contestation` |
| "Choisis la stack technique", "Quelle stack pour le projet" | `stack` |
| "Précise les données du cahier des charges", "Qualifie l'origine des données" | `donnees` |
| "Génère la structure de données de l'application" | `schema-app` |
| "Génère la structure de base de données" | `schema-db` |
| "Crée l'architecture logicielle", "Génère l'architecture de l'application" | `architecture` |
| "Crée le product backlog", "Génère les tickets à partir du cahier des charges" | `backlog` |

**Manual trigger**: the user can always invoke a skill directly by naming it or typing `/simflow:skill-name`.

**When ambiguous**: if the message could match two skills, pick the one with the stronger signal and invoke it. If you genuinely cannot tell, ask one clarifying question first.

**For standalone `simflow:dispatch`**: the user should provide a list of specific independent tasks. If they say "run in parallel" with vague tasks, ask: "What are the specific tasks you want to run in parallel, and for each — what's the goal and which files are involved?"

## Core Rules

These apply everywhere in SimFlow, in every skill, in every agent:

- **Git commits are always in the user's name only.** Check `git config user.name` and `git config user.email` before committing. Never add Co-Authored-By. Never add any additional author. Zero exceptions.
- **No forced entry point.** Any skill can start the session. Skills auto-detect prior outputs like spec files.
- **No guessing.** If you need information to proceed, ask. Don't invent requirements, file paths, or behaviors.
- **Trust the user.** Don't add steps, gates, or checks they haven't asked for.
