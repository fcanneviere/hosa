---
name: infra
description: Use to set up and configure the managed project's Docker environment and install the chosen stack into it, for real, with a version-pinned, documented result. Second stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture), runs after `stack` has recorded the technical choices. Also the entry point for any other agent's mid-task installation need.
---

# Infra

Turns a chosen stack into a real, running, documented Docker environment for the managed project — the environment every later stage (and every day-to-day command against the managed project) runs inside. This skill is the only one that talks to the user or dispatches other agents on `hosa-infra`'s behalf — the actual provisioning is `hosa-infra`'s.

## Flow

```
Dispatch hosa-infra (Mode 1)
        ↓ Open Questions (no project path, no Stack Decision) → relay to user, stop
        ↓ Docker environment written, started, verified
Dispatch hosa-documentation (Mode 1) avec le
"Documentation à produire" retourné
        ↓
Propose d'enchaîner sur `donnees`
```

## Trigger

Manual: `/infra`. Auto: immediately after `stack`, or "mets en place l'environnement Docker", "installe la stack".

**Also triggered mid-task** whenever another agent's output carries an `## Installation nécessaire` field — see Mode 2 below.

---

## Mode 1 — Initial Setup

### Step 1: Dispatch for Setup

Dispatch `hosa-infra` (Mode 1, `agents/infra.md`) to find the managed project, check the recorded `Stack Decision`s, read existing infrastructure and non-functional needs, determine the Docker composition, pin versions, write and start the environment, install the test framework and the database migration tool (mandatory from day one — never offered as an option), and update `kb/infra/environnement-docker.md`.

If it returns an Open Question (no project path, no `Stack Decision` yet, Docker unavailable) — relay it to the user, get the answer, and only redispatch once you have it. Never guess a path or an installed version yourself.

### Step 2: Dispatch Documentation

Dispatch `hosa-documentation` (Mode 1) with what `hosa-infra` returned under `## Documentation à produire` — it writes the installation documentation into the managed project. Wait for its confirmation before reporting the environment as fully in place.

## Mode 2 — Relay an On-Demand Installation Request

Any other agent, when it needs a server/framework/dependency it can't provision itself, returns that need under its own `## Installation nécessaire` field instead of dispatching `hosa-infra` directly (no agent dispatches another agent). Whichever skill dispatched that agent handles the relay:

1. Dispatch `hosa-infra` (Mode 2, `agents/infra.md`) with the requesting agent's name, what it needs, and why.
2. If it returns an Open Question (conflicting `Stack Decision`, ambiguous mode) — relay it to the user, get the answer, redispatch.
3. Once it confirms the piece is in place, dispatch `hosa-documentation` (Mode 1) with its `## Documentation à produire`.
4. Redispatch the original requesting agent with the confirmation — it resumes the task that needed the installation.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa` Core Rules, "Git checkpoints".

## Output

```
## Environnement Docker
- Services : <service> (<image>:<version épinglée>)
- Outillage : tests <framework> (`<commande>`), migrations <outil> (`<commande>`)
- Documentation : `<path>`

## Open Questions
[Si rien : "None"]

## Suite
Je lance `donnees` maintenant ?
```
