---
name: stack
description: Use to propose and record the technical stack for the project Hosa manages, based on the stable cahier des charges. First stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture).
---

# Stack

Turns "what the application must do" (the stable cahier des charges) into a chosen technical stack, recorded before any data structure or architecture work begins. This skill is the only one that talks to the user — the actual analysis, proposal, and recording is `hosa-senior-dev`'s.

## Flow

```
Dispatch hosa-senior-dev (Stack Process, Steps 1-4: find project,
derive needs, check existing decisions, propose options)
        ↓ Open Questions (no stable Exigence, no project path) → relay to user, stop
        ↓ options returned
Présente les options à l'utilisateur → il choisit
        ↓
Redispatch hosa-senior-dev avec le choix → il écrit la
Stack Decision, retourne "Documentation à produire"
        ↓
Dispatch hosa-documentation (Mode 1) avec ce que hosa-senior-dev
rapporte
        ↓
Propose d'enchaîner sur `infra`
```

## Trigger

Manual: `/stack`. Auto: immediately after a clean `contestation` sign-off, or "choisis la stack technique", "quelle stack pour le projet".

---

## Step 1: Dispatch for Options

Dispatch `hosa-senior-dev` (Stack Process, `agents/senior-dev.md`) to find the managed project, derive technical needs from the stable cahier des charges, check `kb/stack/` and the managed project's existing code for decisions already fixed, and propose 2-3 options per still-open category.

If it returns an Open Question (no `stable` `Exigence` yet, no managed-project path) — relay it to the user, get the answer, and only redispatch once you have it. Never guess a path or proceed against a `draft` CDC yourself.

## Step 2: User Picks

Present the options and trade-offs `hosa-senior-dev` returned. Wait for the user's choice per category.

## Step 3: Record the Decision

Redispatch `hosa-senior-dev` with the user's choice for each category. It writes the `Stack Decision`(s) to `kb/stack/` and returns a `## Documentation à produire` field (category, choice, justification, options presented and rejected).

## Step 4: Dispatch Documentation

Dispatch `hosa-documentation` (Mode 1) with what `hosa-senior-dev` returned under `## Documentation à produire` — it writes the matching ADR into the managed project. Wait for its confirmation before reporting the decision as fully recorded.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit each.

## Output

```
## Stack proposée
[Options présentées avec compromis, depuis hosa-senior-dev]

## Stack retenue
- `kb/stack/<slug>.md` — [décision]
- ADR : `<path docs/decisions/ADR-...>`

## Open Questions
[Si rien : "None"]

## Suite
**Q1 — Je lance `infra` maintenant ?**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
```
