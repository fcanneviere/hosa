---
name: recette
description: "Use for a business acceptance test (recette) of a feature or ticket from one persona's point of view (`hosa-key-user`) — not code tests. Triggers: \"fais une recette de…\", \"valide ça avec [persona]\"."
---

# Recette

Runs a business acceptance pass on a feature/ticket using `hosa-key-user`, which embodies one persona from `.hosa/kb/personnas/`. Distinct from `test`: that skill checks the code works; this skill checks it serves the person it's for.

## Flow

```
Identify persona (ask if ambiguous) + target (ticket/spec/feature, ask if missing)
        ↓
hosa-key-user: load persona → enrich if thin → embody → run recette
        ↓
Persona enriched?
    Yes → show the user what it added to kb/personnas/<slug>.md
    No  → skip
        ↓
Write recette result as a Test Plan concept in kb/test/
        ↓
Log to kb/test/log.md (and kb/personnas/log.md if enriched)
        ↓
Report: verdict, scénarios, pain points, quick wins
        ↓ Échoué scenarios found
Active sprint ticket → develop <ticket> correction ; otherwise a
ticket (hosa-product-owner), then debug or rework
```

## Trigger

Manual: `/recette`. Auto: "fais une recette de...", "valide ça avec [persona]", "est-ce que ça répond au besoin de...", "teste ça du point de vue de l'utilisateur/PO/[persona]".

---

## Step 1: Identify Persona and Target

**Persona:** if named, use it. If not and `kb/personnas/` has exactly one non-example persona, use that. Otherwise list the personas found and ask which one.

**Target:** a ticket (`kb/tickets/`), a spec (`docs/specs/`), or an inline feature description. If none given, ask: "Qu'est-ce que je fais valider, et à quel persona ?"

## Step 2: Run `hosa-key-user`

Dispatch with the persona file path and the target content. Let it enrich the persona first if its entry is too thin to embody — that's the agent's job, not this skill's.

If the agent enriched the persona, show the user what it added to `kb/personnas/<slug>.md`, in the report. The agent already wrote it: the user corrects it if needed, through `hosa` (persona update). The recette goes on without waiting.

## Step 3: Write the Test Plan

```
mkdir -p "<root>/.hosa/kb/test/"
```

One file per recette session, `.hosa/kb/test/<slug-target>-<slug-persona>.md`:

```markdown
---
type: Test Plan
title: Recette — <target> (<persona>)
description: "<one line: what was validated, for whom>"
tags: [recette]
status: stable
generated: { by: hosa-key-user/1.0, at: <ISO8601> }
---
<the agent's `## Recette` and `## Verdict` as they are: each scenario Réussi / Échoué / Partiel / Différé, and each `CAn` of the ticket answered `Oui` / `Non` / `Non observé` (`agents/key-user.md`, Output) — the format `qa` writes and `validation` reads; then pain points and quick wins>

Lié à : [persona](../personnas/<slug>.md), [ticket/spec](<path>)
```

## Step 4: Log

Append to `kb/test/log.md` (create if missing, OKF §9 format). If the persona was enriched, also append to `kb/personnas/log.md`.

## Step 5: Report and Route

Report the agent's verdict, scénarios, pain points, and quick wins in plain language, and its `## Ménage` — a recette that couldn't reset the environment leaves data the next one would trip on: say so, and propose `qa-plan` to have `hosa-data-engineer` add or fix the dataset's `## Remise à zéro`.

- **A ticket of the `active` sprint** → no new ticket: route as `qa` Step 4 does. A `CAn` answered `Non` is a defect fixed in the sprint: `develop <ticket> correction`, then `qa <sprint> <ticket>`. A need the criteria never asked for → the backlog, as below.
- **Otherwise, Échoué scenarios that look like implementation bugs** → dispatch `hosa-product-owner` to create a `Ticket` (`state: todo`, linked to the recette `Test Plan` and the target) with the exact gap, then suggest `debug` on it.
- **Échoué/Partiel scenarios that look like the ticket itself was wrong or incomplete** → dispatch `hosa-product-owner` to create a `Ticket` capturing what's missing, then suggest routing it back for rework.
- **Quick wins surfaced by the persona** (small, clearly out of this recette's scope) → dispatch `hosa-product-owner` to create one `Ticket` per quick win, `state: todo`, tagged so they're easy to spot in the backlog later.
- **Every ticket created above** → run `backlog`'s Single-Ticket Mode on it before reporting, so it's complete.
- **Différé** (the software couldn't be run) → say so plainly: nothing was judged. Never report it as Accepté.
- **Accepté with no quick win** → nothing further.

## No Commits

This skill does not commit. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa`, "Git checkpoints".
