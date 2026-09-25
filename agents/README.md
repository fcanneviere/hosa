# Agents

Agents invoked via the `Agent` tool (`select:<name>` in Claude Code) or dispatched from a skill. Full details, including the `## Input` contract, are in each agent's file.

## SimFlow agents

Generic dev lifecycle agents, usable on any project.

| Agent | Model | Role |
|---|---|---|
| [`simflow-planner`](planner.md) | claude-opus-4-8 | Breaks a spec or feature description into a concrete, executable task plan — assigns tasks to agents, identifies parallel vs sequential execution, flags blocking ambiguities. |
| [`simflow-implementer`](implementer.md) | claude-sonnet-5 | Executes a specific implementation task — writes code following existing patterns, reports what it built, never commits. |
| [`simflow-tester`](tester.md) | claude-sonnet-5 | Runs and writes tests — reads existing tests to match conventions, runs the suite, identifies coverage gaps, writes new tests. |
| [`simflow-reviewer`](reviewer.md) | claude-opus-4-8 | Checks whether an implementation satisfies every requirement in the spec — returns PASS / PASS-WITH-NOTES / FAIL with a precise gap list. |
| [`simflow-debugger`](debugger.md) | claude-sonnet-5 | Investigates a specific bug or failure — finds the root cause through systematic investigation, never guesses, applies a targeted fix. |

## Hosa agents

Project-specific agents for the Hosa cahier-des-charges and data-structuring pipelines.

| Agent | Model | Role |
|---|---|---|
| [`hosa-product-owner`](product-owner.md) | claude-opus-4-8 | Acts as Product Owner for Hosa — carries the product vision, manages the Product Backlog (`hosa/kb/tickets/`), writes user stories from persona needs, validates deliverables. |
| [`hosa-key-user`](key-user.md) | claude-opus-4-8 | Embodies a specific persona from `hosa/kb/personnas/` — sharpens thin persona entries, runs functional/business acceptance testing ("recette métier") from that persona's point of view. |
| [`hosa-challenger`](challenger.md) | claude-opus-4-8 | Audits the assembled cahier des charges (`hosa/kb/cdc/`) for contradictions, blind spots, unstated assumptions, and risks — an independent read, never a self-check. |
| [`hosa-senior-dev`](senior-dev.md) | claude-opus-4-8 | Chooses the technical stack for the managed project — proposes stack options based on the stable cahier des charges, with trade-offs, and records the choice. |
| [`hosa-data-engineer`](data-engineer.md) | claude-opus-4-8 | Data engineer and guarantor of data for the managed project — qualifies where each piece of data comes from (générée/fournie/saisie), derives and writes the resulting app- and DB-side data structures plus their documentation. |
| [`hosa-architect`](architect.md) | claude-opus-4-8 | Guarantor of software architecture for the managed project — designs and scaffolds an architecture consistent with the business logic, the chosen stack, and the finished data structures. |
