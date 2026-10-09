---
name: infra
description: "Use to set up the managed project's Docker environment, its stack on pinned versions and its quality tooling (tests, lint, CI), or to handle an agent's `## Installation nécessaire` (`hosa-infra`). Structuration stage 2. Triggers: \"installe la stack\", after `stack`."
---

# Infra

Turns a chosen stack into a real, running, documented Docker environment for the managed project — the environment every later stage (and every day-to-day command against the managed project) runs inside. This skill is the only one that talks to the user or dispatches other agents on `hosa-infra`'s behalf — the actual provisioning is `hosa-infra`'s.

## Flow

```
Dispatch hosa-infra (Mode 1)
        ↓ Open Questions (no project path, no Stack Decision) → relay to user, stop
        ↓ Docker environment written, started, verified
        ↓ outillage qualité : tests, tests navigateur, lint,
        ↓ format, types, CI — installés et lancés une fois
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

Dispatch `hosa-infra` (Mode 1, `agents/infra.md`) to find the managed project, check the recorded `Stack Decision`s, read existing infrastructure and non-functional needs, determine the Docker composition, pin versions, write and start the environment, install the quality tooling (test runner, browser tests, linter, formatter, type checker, CI pipeline) and update `kb/infra/environnement-docker.md` with its `## Outillage qualité` commands. The quality tooling is part of this stage: no sprint starts without it (`git` Mode 1 checks it). Relay its Open Question on the CI host to the user.

If it returns an Open Question (no project path, no `Stack Decision` yet, Docker unavailable) — relay it to the user, get the answer, and only redispatch once you have it. Never guess a path or an installed version yourself.

### Step 2: Dispatch Documentation

Dispatch `hosa-documentation` (Mode 1) with what `hosa-infra` returned under `## Documentation à produire` — it writes the installation documentation into the managed project. Wait for its confirmation before reporting the environment as fully in place.

## Mode 3 — Deployment

Dispatched by `livraison` only (`hosa-infra` Mode 3). Relay its Open Questions on the target, access and rollback to the user.

## Mode 2 — Relay an On-Demand Installation Request

Any other agent, when it needs a server/framework/dependency it can't provision itself, returns that need under its own `## Installation nécessaire` field instead of dispatching `hosa-infra` directly (no agent dispatches another agent). Whichever skill dispatched that agent handles the relay:

1. Dispatch `hosa-infra` (Mode 2, `agents/infra.md`) with the requesting agent's name, what it needs, and why.
2. If it returns an Open Question (conflicting `Stack Decision`, ambiguous mode) — relay it to the user, get the answer, redispatch.
3. Once it confirms the piece is in place, dispatch `hosa-documentation` (Mode 1) with its `## Documentation à produire`.
4. Redispatch the original requesting agent with the confirmation — it resumes the task that needed the installation.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit each.

## Output

```
## Environnement Docker
- Services : <service> (<image>:<version épinglée>)
- Outillage qualité : tests [OK], navigateur [OK / sans objet], lint/format/types [OK], CI `<fichier>`
- Documentation : `<path>`

## Open Questions
[Si rien : "None"]

## Suite
Suite : `donnees`, lancé sans attendre.
```
