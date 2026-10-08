# Agents

Agents invoked via the `Agent` tool (agent type `<name>` in Claude Code) or dispatched from a skill. Full details, including the `## Input` contract, are in each agent's file.

## Generic agents

Generic dev lifecycle agents, usable on any project.

| Agent | Model | Role |
|---|---|---|
| [`hosa-planner`](planner.md) | opus | Breaks a spec or feature description into a concrete, executable task plan — assigns tasks to agents, identifies parallel vs sequential execution, flags blocking ambiguities. |
| [`hosa-implementer`](implementer.md) | sonnet | Executes a specific implementation task — writes code following existing patterns, reports what it built, never commits. |
| [`hosa-tester`](tester.md) | sonnet | Autonomous tester — from a ticket slug, finds its plan, worktree and Docker environment, writes the tests before the code or runs them, fixes the test side itself, records results and cleans the environment. |
| [`hosa-reviewer`](reviewer.md) | opus | Checks whether an implementation satisfies every requirement in the spec — returns PASS / PASS-WITH-NOTES / FAIL with a precise gap list. |
| [`hosa-debugger`](debugger.md) | sonnet | Investigates a specific bug or failure — finds the root cause through systematic investigation, never guesses, applies a targeted fix. |

## Hosa agents

Project-specific agents for the Hosa cahier-des-charges and data-structuring pipelines.

| Agent | Model | Role |
|---|---|---|
| [`hosa-product-owner`](product-owner.md) | sonnet | Acts as Product Owner for Hosa — carries the product vision, manages the Product Backlog (`.hosa/kb/tickets/`), writes user stories from persona needs, validates deliverables. |
| [`hosa-key-user`](key-user.md) | sonnet | Embodies a specific persona from `.hosa/kb/personnas/` — sharpens thin persona entries, runs functional/business acceptance testing ("recette métier") from that persona's point of view. |
| [`hosa-challenger`](challenger.md) | opus | Audits the assembled cahier des charges (`.hosa/kb/cdc/`) for contradictions, blind spots, unstated assumptions, and risks — an independent read, never a self-check. |
| [`hosa-senior-dev`](senior-dev.md) | opus | Chooses the technical stack for the managed project — proposes stack options based on the stable cahier des charges (security constraints included), with trade-offs, and records the choice. Also audits the managed project's source code for best practices and performance. |
| [`hosa-security`](security.md) | opus | Cybersecurity expert, security by design — analyses data sensitivity and threats during the cahier des charges and writes security exigences and the project's `Security Rule`s; at the end, audits the code for conformity and for the holes nobody could foresee. |
| [`hosa-infra`](infra.md) | sonnet | Sole owner of installing or provisioning anything for the project Hosa manages — sets up, configures, and runs its Docker environment, installs the chosen stack into it, documents installation, and validates or counter-proposes every later request from another agent for a new server, framework, or dependency. |
| [`hosa-data-engineer`](data-engineer.md) | opus | Data engineer and guarantor of data for the managed project — qualifies where each piece of data comes from (générée/fournie/saisie), derives and writes the resulting app- and DB-side data structures plus their documentation, and builds, documents and (re)loads the test dataset once architecture and test plans are known. |
| [`hosa-dba`](dba.md) | sonnet | Database administrator — migration tooling and discipline across sprint branches, each environment's database, the isolated test database and its reset, accounts, backups with tested restores, database audits; documents it all in `kb/infra/base-de-donnees.md` and assists every other agent through `bdd`. |
| [`hosa-architect`](architect.md) | opus | Guarantor of software architecture for the managed project — designs and scaffolds an architecture consistent with the business logic, the chosen stack, and the finished data structures. |
| [`hosa-ux-designer`](ux-designer.md) | sonnet | Guarantor of the interface layer (UX/UI) for the managed project — interviews each persona, proposes a visual identity and design rules, then designs and scaffolds an interface consistent with the business logic and the software architecture. |
| [`hosa-sprint-planner`](sprint-planner.md) | haiku | Composes each sprint from the Product Backlog — dispatches tickets in `hosa-product-owner`'s priority order up to a given capacity, guarding against dispatching a ticket whose technical feasibility, architecture placement, or interface placement was never actually evaluated. |
| [`hosa-qa-lead`](qa-lead.md) | sonnet | Defines each ticket's technical test plan when the sprint is composed, before it starts, and keeps the test tooling reliable, fast and clean. |
| [`hosa-documentation`](documentation.md) | sonnet | Sole owner of technical and functional documentation for the project Hosa manages — writes and keeps in sync the installation, architecture, and data-dictionary docs on behalf of `hosa-infra`/`hosa-architect`/`hosa-data-engineer`, and owns the functional guides derived from the stable cahier des charges and personas. |
| [`hosa-git`](git.md) | sonnet | Sole owner of the managed project's git repository lifecycle for a sprint — opens a dedicated branch/worktree when it starts, and merges it locally once every ticket has a passing QA record. |
| [`hosa-tech-lead`](tech-lead.md) | sonnet | Breaks a sprint ticket into short, strictly sequential implementation tasks — respects the architecture and data structures already scaffolded, and stops rather than proposing an extension itself. |
| [`hosa-developer`](developer.md) | sonnet | Implements a single task from `hosa-tech-lead`'s plan, in a short focused session — stays inside the architecture/data structures already scaffolded, and stops rather than improvising a workaround if a task needs one extended. |
