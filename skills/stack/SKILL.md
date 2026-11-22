---
name: stack
description: "Use to propose 2-3 options and record the technical stack from the stable cahier des charges. Triggers: \"choisis la stack technique\", after `contestation`."
---

# Stack

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start stack`; refused → name the missing stage to the user and stop; refused as already done → a re-run only on the user's request: the same `start` with `--rouvre "<their request>"`. Stopped on a user question: `block stack --detail "<question>"`. Once the stage's output is written and committed: `done stack`. Never skip these calls: without them a cut session can't resume (« reprends »), and `budget.js` can't apply the stage's `dispatch` rules (each agent's model, the agents at once) — they hold only while the stage is `en cours`.

**Tâches.** Before each dispatch that writes, `avancement.py task add stack <id> --agent <agent>`; on its return, `task done stack <id> --sortie <the paths it wrote>`: `decision` (`hosa-senior-dev`, Step 4) → `kb/stack/<slug>.md`…; `adr` (`hosa-documentation`, Step 5) → the ADRs. The options pass (Step 2) writes nothing: no task. Stopped on an Open Question → `task block stack <id> --detail "<la question>"`, and `task add` the same id again once answered.

Turns "what the application must do" (the stable cahier des charges) into a chosen technical stack, recorded before any data structure or architecture work begins. This skill is the only one that talks to the user — the actual analysis, proposal, and recording is `hosa-senior-dev`'s.

## Flow

```
Demande Q1 : open source ou SaaS payant (sauf si déjà dans
kb/stack/orientation.md)
        ↓
Dispatch hosa-senior-dev (Stack Process, Steps 1-4: find project,
derive needs, check existing decisions, propose options,
library inventory: Steps 1-4b)
        ↓ Open Questions (no stable Exigence, no project path) → relay to user, stop
        ↓ options returned
Présente les options à l'utilisateur → il choisit
        ↓
Redispatch hosa-senior-dev avec le choix → il écrit la
Stack Decision, retourne "Documentation à produire"
        ↓
Dispatch hosa-documentation (Mode 1) avec les chemins que
hosa-senior-dev rapporte
        ↓
Enchaîne sur `infra`
```

## Trigger

Manual: `/stack`. Auto: immediately after a clean `contestation` sign-off, or "choisis la stack technique", "quelle stack pour le projet".

Reopened by a loop (`back develop stack`, `back schema-db stack`): skip Step 1, dispatch `hosa-senior-dev` with the loop's detail only (the capability missing from `kb/stack/bibliotheques.md`, or the database limit). It proposes for that item alone; the user picks; it writes that line or that decision; then `infra` installs it.

---

## Step 1: Open Source or SaaS

Unless `kb/stack/orientation.md` already records it, ask first — it's a budget and dependency choice the user owns:

```
**Q1 — Pour la stack, tu préfères quel type de services ?** (bloquante)
  a) Open source, auto-hébergeable, sans abonnement (recommandé)
  b) Services SaaS payants — hébergement géré, authentification et base de données en service
  c) Mixte — open source par défaut, SaaS là où ça fait gagner beaucoup de temps
```

Pass the answer to `hosa-senior-dev` with the dispatch below.

## Step 2: Dispatch for Options

Dispatch `hosa-senior-dev` (Stack Process, `agents/senior-dev.md`) with the orientation to find the managed project, derive technical needs from the stable cahier des charges, check `kb/stack/` and the managed project's existing code for decisions already fixed, and propose 2-3 options per still-open category, then the library inventory (Step 4b): one library per technical capability the exigences need, chosen before any code. A « Fait maison » comes with its measurable reason and its cost in lines.

If it returns an Open Question (no `stable` `Exigence` yet, no managed-project path) — relay it to the user, get the answer, and only redispatch once you have it. Never guess a path or proceed against a `draft` CDC yourself.

## Step 3: User Picks

Present the options and trade-offs `hosa-senior-dev` returned, then its `## Bibliothèques proposées`. Wait for the user's choice per category; the inventory is validated as a whole (« Q2 a) l'inventaire tel quel (recommandé) »), the user changing only the lines they name.

## Step 4: Record the Decision

Redispatch `hosa-senior-dev` with the user's choice for each category. It writes the `Stack Decision`(s) to `kb/stack/`, the validated inventory to `kb/stack/bibliotheques.md` (`done stack` refuses the stage without it), and returns `## Documentation à produire`: the path of each `Stack Decision` written (it holds the choice, the justification and the options presented and rejected).

## Step 5: Dispatch Documentation

Dispatch `hosa-documentation` (Mode 1) with the lines `hosa-senior-dev` returned under `## Documentation à produire`, as they are (paths, `retours` §4) — it writes the matching ADR into the managed project. Wait for its confirmation before reporting the decision as fully recorded.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa`, "Git checkpoints".

## Output

```
## Stack proposée
[Options présentées avec compromis, depuis hosa-senior-dev]

## Stack retenue
- `kb/stack/<slug>.md` — [décision]
- `kb/stack/bibliotheques.md` — [N capacités, dont K fait maison]
- ADR : `<path docs/decisions/ADR-...>`

## Open Questions
[Si rien : "None"]

## Suite
Suite : `infra`, lancé sans attendre.
```
