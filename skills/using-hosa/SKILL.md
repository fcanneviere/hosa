---
name: using-hosa
description: Bootstrap skill — always loaded at session start. Explains what Hosa is, what skills exist, and when to trigger them automatically.
---

# Hosa

You have a lightweight full dev lifecycle skill set for Claude Code and Codex — generic skills and agents to understand, build, test, review, and debug software without ceremony, plus Hosa's own project-specific pipeline (cahier des charges, backlog, sprints, QA).

## Skills

Use the `Skill` tool to invoke any of these. The skill loads its full instructions — follow them exactly.

| Skill | What it does |
|---|---|
| `understand` | Brainstorm + grill an idea → write spec → quiz user → commit |
| `build` | Read spec or description → plan → implement task by task → quiz → commit |
| `iterate` | Change or extend existing code → light grill → targeted plan → quiz → commit |
| `dispatch` | Fan out independent tasks to agents in parallel |
| `test` | Run tests, identify gaps, write new tests, commit them |
| `review` | Check implementation against spec → fix gaps → loop until clean |
| `debug` | Systematic root cause analysis → confirm with user → fix → commit |
| `status` | Snapshot of project state — spec, progress, tests, next step |
| `hosa` | Initialize/update the Hosa project's identity and personas in the KB (`.hosa/kb/`) |
| `recette` | Business/functional acceptance testing of a feature or ticket, from a specific persona's point of view |
| `interview` | Gather cahier des charges input from processes, personas, and the user — CDC pipeline stage 1 |
| `redaction` | Turn interview notes into structured `Exigence` concepts in `kb/cdc/` — CDC pipeline stage 2 |
| `relecture` | Check the cahier des charges for precision, completeness, and consistency — CDC pipeline stage 3 |
| `contestation` | Final independent challenge pass on the cahier des charges — CDC pipeline stage 4 |
| `fondamentaux` | Check the cahier des charges against a standard checklist of cross-cutting essentials (admin, login, rights, settings, import/export, backup, audit, notifications) and write missing ones — companion check to the CDC pipeline, usable anytime |
| `stack` | Propose and record the technical stack of the managed project, based on the stable cahier des charges — data-structuring pipeline stage 1 |
| `infra` | Set up and configure the managed project's Docker environment, install the chosen stack into it for real, and document installation — data-structuring pipeline stage 2 |
| `donnees` | Annotate the origin (générée/fournie/saisie) of data in the cahier des charges — data-structuring pipeline stage 3 |
| `schema-app` | Derive data entities and write application-side data structures + documentation into the managed project — data-structuring pipeline stage 4 |
| `schema-db` | Write database migrations/DDL into the managed project — data-structuring pipeline stage 5 |
| `architecture` | Design and scaffold the software architecture of the managed project, consistent with the CDC, the stack, and the data structures — data-structuring pipeline stage 6 |
| `interface` | Interview each persona, propose a visual identity and design rules, then design and scaffold the interface layer (UX/UI) of the managed project, consistent with the CDC and the software architecture — data-structuring pipeline stage 7 |
| `backlog` | Turn every stable cahier des charges Exigence without a ticket yet into a Product Backlog Ticket carrying the story, a technical feasibility note, an architecture placement note, and an interface placement note — data-structuring pipeline stage 8 |
| `sprint` | Compose a sprint from the Product Backlog — dispatch tickets in priority order up to a given capacity, guarding against dispatching one whose technical feasibility, architecture placement, or interface placement was never actually evaluated — follow-on to the data-structuring pipeline |
| `qa-plan` | Prepare a sprint's technical test plan — one `Test Plan` per ticket in `kb/test/`, grounded in the senior dev's recorded stack decisions, identifying which persona(s) must validate it via recette — follow-on to `sprint` |
| `qa` | Run a sprint's QA — dispatch `hosa-tester` for each ticket's technical test plan and `hosa-key-user` for its required recette, then route failures to the right owner — follow-on to `qa-plan` |
| `git` | Open a dedicated branch/worktree for a sprint when it starts, or merge it locally back into the managed project once every ticket has a passing QA record — dispatches `hosa-git`. Companion transversal skill, with dedicated hand-off points in `sprint` (start) and `validation` (finish) |
| `develop` | Implement a single sprint ticket — break it into short sequential tasks (`hosa-tech-lead`) and implement them one at a time (`hosa-developer`), strictly within the architecture and data structures already scaffolded. Follow-on to `git` Mode 1, precondition for `qa-plan`/`qa` |
| `validation` | Close a ticket's cycle once implemented and tested — dispatches `hosa-product-owner` to check it against its own acceptance criteria, technical results, and recette verdict, then sets it `done`+`verified` or bounces it back. Follow-on to `qa`, precondition for `git` Mode 2 |
| `bilan-sprint` | Sprint Review and retro once a sprint merges — dispatches `hosa-product-owner` to judge whether the objective was met, list delivered/deferred tickets, surface recurring friction, and write follow-up tickets or process Design Rules. Follow-on to `git` Mode 2 |
| `qualite` | Audit the managed project's source code against a fixed checklist of coding best practices and security rules — dispatches `hosa-senior-dev`, classifies findings by severity, records them in `kb/qualite/` — companion check usable anytime |
| `documentation` | Check whether the managed project's technical and functional documentation is in sync with its sources, and refresh whatever has drifted — dispatches `hosa-documentation` in cold-check mode. Companion check usable anytime, not a pipeline stage |
| `changement` | Handle a change to a `stable` Exigence — impact analysis (tickets/entities/migrations/screens/docs affected), revert to `draft`, a mini relecture/contestation loop, then follow-up tickets. Companion to the CDC pipeline, usable anytime after `contestation` has run once |
| `livraison` | Release/deploy the managed project — CI pipeline and environments (via `hosa-infra`), release notes drawn from `done` tickets since the last release, optional push/PR (via `hosa-git`). Turns a local merge into something actually shipped. Follow-on to `git` Mode 2 / `validation` |
| `kb-commit` | Commit whatever's accumulated under `.hosa/kb/` as a dedicated commit in the managed project's own git history, separate from the rest of that project's commits and from Hosa's own tooling commits. Companion skill, usable anytime |

## Triggering Rules

**Auto-trigger** the matching skill immediately via the `Skill` tool — without asking for permission — when the user's message clearly matches a skill's purpose:

| User says something like... | Trigger |
|---|---|
| "I have an idea for...", "I want to build...", "Let's plan..." | `understand` |
| "Implement this", "Build it", "Add this feature", "Write the code" | `build` |
| "Change how X works", "Refactor this", "Update this", "Add X to existing Y" | `iterate` |
| "Run these in parallel", "Fan out", "Do these simultaneously" | `dispatch` |
| "Test this", "Run tests", "Check if it works" | `test` |
| "Does this match the spec?", "Check requirements", "Is everything implemented?" | `review` |
| "It's broken", "This isn't working", "I'm getting an error", "There's a bug" | `debug` |
| "Where are we?", "What's done?", "Catch me up", "What's left?" | `status` |
| "Initialise le projet", "Configure hosa", "Crée un persona pour..." | `hosa` |
| "Fais une recette de...", "Valide ça avec [persona]", "Est-ce que ça répond au besoin de..." | `recette` |
| "Rédige le cahier des charges", "Interview les personas", "Démarre le cahier des charges" | `interview` |
| "Rédige les exigences", "Écris le cahier des charges" (avec notes fournies) | `redaction` |
| "Relis le cahier des charges" | `relecture` |
| "Challenge le cahier des charges" | `contestation` |
| "Vérifie les fondamentaux du cahier des charges", "Le cahier des charges couvre-t-il les basiques (admin, login, import/export...)" | `fondamentaux` |
| "Choisis la stack technique", "Quelle stack pour le projet" | `stack` |
| "Mets en place l'environnement Docker", "Installe la stack" | `infra` |
| "Précise les données du cahier des charges", "Qualifie l'origine des données" | `donnees` |
| "Génère la structure de données de l'application" | `schema-app` |
| "Génère la structure de base de données" | `schema-db` |
| "Crée l'architecture logicielle", "Génère l'architecture de l'application" | `architecture` |
| "Conçois l'interface", "Crée l'identité visuelle", "Définis l'UX/UI du projet" | `interface` |
| "Crée le product backlog", "Génère les tickets à partir du cahier des charges" | `backlog` |
| "Planifie un sprint", "Compose le prochain sprint" | `sprint` |
| "Prépare les tests du sprint", "Planifie les tests techniques du sprint" | `qa-plan` |
| "Exécute la QA du sprint", "Teste le sprint", "Fais la recette du sprint" | `qa` |
| "Démarre le sprint X", "Commence le sprint X" | `git` (Mode 1) |
| "Termine le sprint X", "Fusionne le sprint X", "Merge le sprint X" | `git` (Mode 2) |
| "Développe le ticket X", "Implémente le ticket X" | `develop` |
| "Valide le ticket X", "Accepte le ticket X" | `validation` |
| "Fais le bilan du sprint X", "Rétro du sprint X" | `bilan-sprint` |
| "Audite la qualité du code", "Vérifie les bonnes pratiques", "Fais une revue de sécurité du code" | `qualite` |
| "Vérifie que la documentation est à jour" | `documentation` |
| "Cette exigence a changé", "Modifie le cahier des charges sur X (déjà stable)" | `changement` |
| "Livre le projet", "Déploie", "Prépare la release" | `livraison` |
| "Committe la KB", "Sauvegarde les changements de la KB" | `kb-commit` |

**Manual trigger**: the user can always invoke a skill directly by naming it or typing `/skill-name`.

**When ambiguous**: if the message could match two skills, pick the one with the stronger signal and invoke it. If you genuinely cannot tell, ask one clarifying question first.

**Generic vs. Hosa variant**: several triggers overlap in shape between a generic lifecycle skill and a Hosa-pipeline skill — "teste le sprint" (`qa`) vs. "test this" (`test`), "implémente le ticket X" (`develop`) vs. "implement this" (`build`), "fais une recette de X" (`recette`) vs. "fais la recette du sprint" (`qa`). Before firing the Hosa variant, check that `.hosa/kb/` actually exists and is populated beyond its example files, and that the sprint/ticket named actually resolves to a file in `kb/sprints/`/`kb/tickets/`. No KB, or nothing resolves → use the generic variant, don't guess a Hosa context that isn't there. Both present and the message still names no sprint/ticket → ask which one.

**For standalone `dispatch`**: the user should provide a list of specific independent tasks. If they say "run in parallel" with vague tasks, ask: "What are the specific tasks you want to run in parallel, and for each — what's the goal and which files are involved?"

## Core Rules

These apply everywhere in Hosa, in every skill, in every agent:

- **KB location.** The KB lives inside the managed project itself, at `.hosa/kb/` — never inside Hosa's own plugin checkout. Resolve it once per session: walk up from the current working directory the same way `.git` is discovered, until a `.hosa/kb/` directory is found. None found anywhere up the tree → this is that project's first run: confirm the project root with the user (default: current working directory; never Hosa's own plugin checkout), then create `.hosa/kb/` there. Every `kb/<bundle>/` reference anywhere in this skill set is relative to that resolved root. This is what lets more than one project be managed, each with its own `.hosa/kb/` versioned alongside it — instead of one KB hardcoded inside Hosa's own repository.
- **Git commits are always in the user's name only.** Check `git config user.name` and `git config user.email` before committing. Never add Co-Authored-By. Never add any additional author. Zero exceptions.
- **No forced entry point.** Any skill can start the session. Skills auto-detect prior outputs like spec files.
- **No guessing.** If you need information to proceed, ask. Don't invent requirements, file paths, or behaviors.
- **Trust the user.** Don't add steps, gates, or checks they haven't asked for — this doesn't override a hard gate elsewhere in this file (the quiz policy below) or in a skill's own flow (e.g. `sprint`'s technical-readiness guard, `git`'s QA gate): those exist because a specific failure mode was worth blocking, not because a step needed padding.
- **Skills orchestrate, agents execute.** Every Hosa agent is a subagent: it returns exactly one final report and cannot hold a dialogue or dispatch another agent itself. Every pipeline skill dispatches its matching agent for the actual proposal/design/scaffold/write work instead of re-implementing that agent's process itself. When a dispatched agent needs a user decision, a persona's answer, or an installation it can't perform itself, it returns that need in its own Output (`## Open Questions`, `## Documentation à produire`, `## Installation nécessaire`, `## Persona question`, as fits) instead of asking or dispatching directly — the orchestrating skill reads that field, gets the answer (from the user directly, or by dispatching `hosa-key-user`/`hosa-infra`), and redispatches the original agent with it.
- **Only `hosa-infra` installs.** No other agent ever runs an installation or provisioning command itself, or adds a server, a framework, or a dependency to the managed project on its own. It returns what it needs and why under `## Installation nécessaire` instead; the orchestrating skill dispatches `hosa-infra` (Mode 2) with that, then redispatches the requesting agent once `hosa-infra` confirms it's in place.
- **The managed project runs in Docker.** Once `hosa-infra` has set up its environment, every command against the managed project — build, migration, test, run — executes inside it, not directly on the host.
