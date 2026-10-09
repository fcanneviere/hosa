---
name: architecture
description: "Use to design and scaffold the managed project's software architecture (layers, modules, observability baseline) from the stable CDC, the stack and the data structures. Structuration stage 6. Triggers: \"crée l'architecture logicielle\", after `schema-db`."
---

# Architecture

Turns the business logic, the chosen stack, and the finished data architecture into a real, scaffolded software architecture in the managed project — including the minimal observability baseline every later module builds on. This skill is the only one that talks to the user — the actual design and scaffold is `hosa-architect`'s.

## Flow

```
Dispatch hosa-architect (design + scaffold, incl. observability
baseline)
        ↓ Open Questions (missing Infra/CDC/Stack/data structures) → relay to user, stop
        ↓ architecture scaffolded
Dispatch hosa-documentation (Mode 1) avec le
"Documentation à produire" retourné
        ↓
Met à jour l'entrée Infra avec le chemin confirmé
        ↓
Enchaîne sur `securite` (mode Menaces) sans demander,
puis `interface`
```

## Trigger

Manual: `/architecture`. Auto: immediately after `schema-db`, or "crée l'architecture logicielle", "génère l'architecture de l'application".

---

## Step 1: Dispatch for Design and Scaffold

Dispatch `hosa-architect` (`agents/architect.md`) to gather the inputs (`Infra` entry, `stable` `Exigence`s, `Stack Decision`s, data dictionary + migrations), read existing conventions, design the architecture — layers, modules, boundaries, and the observability baseline (correlation-id propagation, structured logging convention, alertable failure symptoms) — and scaffold it for real in the managed project.

If it returns an Open Question (no `Infra` entry, missing CDC/stack/data structures) — relay it to the user, propose running the missing stage (`stack`, `schema-app`, `schema-db`), and only redispatch once resolved. Never guess a path or a design decision yourself.

## Step 2: Dispatch Documentation

Dispatch `hosa-documentation` (Mode 1) with what `hosa-architect` returned under `## Documentation à produire` (layers/modules chosen, observability baseline, paths scaffolded) — it writes the architecture documentation into the managed project. Wait for its confirmation and the path it wrote to.

## Step 3: Update the `Infra` Entry

Add the confirmed architecture documentation path to the `Infra` entry under its own `## Documentation d'architecture` heading — a fixed heading, not a bare line, so a later reader (e.g. `backlog`) can tell it apart from the data dictionary or migrations paths `schema-app`/`schema-db` also record there. Log the update to `kb/infra/log.md`.

## Step 4: Threat Model

Invoke `securite` in Menaces mode without asking — the trust boundaries of an application only exist once its layers do, and every control added after the code is written costs more than one designed in now. It's the progress-plan stage `menaces`; `securite` then chains to `interface`.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa` Core Rules, "Git checkpoints".

## Output

```
## Architecture conçue
[Couches/modules retenus et pourquoi]
[Socle observabilité : correlation-id, convention de logs, symptômes alertables]

## Structures créées
- `<path>` — [module/dossier scaffoldé]

## Documentation
- `<path>`

## Open Questions
[Si rien : "None"]

## Suite
Suite : `securite` (Menaces), puis `interface`, lancé sans attendre.
```
