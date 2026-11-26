---
name: infra
description: "Use to set up the Docker environment, the pinned stack and the quality tooling, or to handle a `## Installation nécessaire`. Triggers: \"installe la stack\", after `stack`."
---

# Infra

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything (Modes 2 and 3 excepted: not a stage, no call): `avancement.py start infra`; refused → name the missing stage to the user and stop; refused as already done → a re-run only on the user's request: the same `start` with `--rouvre "<their request>"`. Stopped on a user question: `block infra --detail "<question>"`. Once the stage's output is written and committed: `done infra`. Never skip these calls: without them a cut session can't resume (« reprends »), and `budget.js` can't apply the stage's `dispatch` rules (each agent's model, the agents at once) — they hold only while the stage is `en cours`.

**Tâches** (Mode 1). Before each dispatch, `avancement.py task add infra <id> --agent <agent>`; on its return, `task done infra <id> --sortie <the paths it wrote>`: `environnement` (`hosa-infra`) → `kb/infra/environnement-docker.md` and the files it wrote; `documentation` (`hosa-documentation`) → the documentation paths. Stopped on an Open Question → `task block infra <id> --detail "<la question>"`, and `task add` the same id again once answered.

Turns a chosen stack into a real, running, documented Docker environment for the managed project — the environment every later stage (and every day-to-day command against the managed project) runs inside. This skill is the only one that talks to the user or dispatches other agents on `hosa-infra`'s behalf — the actual provisioning is `hosa-infra`'s.

## Flow

```
Dispatch hosa-infra (Mode 1)
        ↓ Open Questions (no project path, no Stack Decision) → relay to user, stop
        ↓ Docker environment written, started, verified
        ↓ outillage qualité : tests, tests navigateur, lint,
        ↓ format, types, CI — installés et lancés une fois
Schéma de l'infrastructure validé par l'utilisateur
(`cdc schemas --infra --apercu`, `cdc valide infra`),
puis `cdc assemble` : le schéma entre au cahier des charges
        ↓
Dispatch hosa-documentation (Mode 1) avec le
"Documentation à produire" retourné
        ↓
Enchaîne sur `ia` (`essai-ia`)
```

## Trigger

Manual: `/infra`. Auto: immediately after `stack`, or "mets en place l'environnement Docker", "installe la stack".

**Also triggered mid-task** whenever another agent's output carries an `## Installation nécessaire` field — see Mode 2 below.

---

## Mode 1 — Initial Setup

### Step 1: Dispatch for Setup

Dispatch `hosa-infra` (Mode 1, `agents/infra.md`) to find the managed project, check the recorded `Stack Decision`s, read existing infrastructure and non-functional needs, determine the Docker composition, pin versions, write and start the environment, install the quality tooling (test runner, browser tests, linter, formatter, type checker, CI pipeline) and update `kb/infra/environnement-docker.md` with its `## Outillage qualité` commands and its `## Preuve de sortie`: lint, format, tests, the reload of mounted code and the browser suite, each run in the container with `exit 0` (`done infra` refuses otherwise). The quality tooling is part of this stage: no sprint starts without it (`git` Mode 1 checks it). Relay its Open Question on the CI host to the user.

If it returns an Open Question (no project path, no `Stack Decision` yet, Docker unavailable) — relay it to the user, get the answer, and only redispatch once you have it. Never guess a path or an installed version yourself.

### Step 1a: The User Decides Each Failing Existing Test

Code adopted only (`kb/existant/inventaire.md` exists). `hosa-infra` ran the existing tests once and wrote `## Tests existants` in `kb/infra/environnement-docker.md`: each failure is a new problem `Dn` (`source : tests`) of `kb/existant/diagnostic.md`, set aside so the suite is green. Ask the user one question per `Dn`, as `adoption` does: what the test expects, what the code does, the proposition as `a)`.

**Q1** — D7 : `tests/test_export.py::test_dates` échoue (<ce que le test attend, ce que le code fait>). Que fait-on ?
a) <la proposition de `hosa-infra`>.
b) <les deux autres choix parmi corriger, accepter, plus tard>.

Write each answer under its problem, `  - Décision : corriger | accepter | plus tard — <raison, dite par l'utilisateur>`, a line under `## Révisions`, then `reponse infra --detail "Q1 a"`. A `Dn` to fix becomes a ticket in `backlog` (`diagnostic: [Dn]`), and its test is put back in the suite when that ticket is delivered. `done infra` refuses a failure without its decision (`<hosa> existant_check .hosa/kb infra`).

### Step 1b: The User Validates the Infrastructure Diagram

`hosa-infra` drew the infrastructure in `kb/infra/environnement-docker.md` § `## Schéma de l'infrastructure`. The user validates it before it enters the cahier des charges:

```bash
<hosa> cdc schemas "<root>/.hosa/kb" --infra --apercu
```

It writes `<root>/.hosa/schemas.html` (the diagram drawn) and exits 1 while it is not validated. Give the user the page's path, never the diagram's text, then one question:

**Q1** — Le schéma de l'infrastructure est-il juste ?
a) Oui.
b) Non : <ce qui change>.

« a » → `<hosa> cdc valide "<root>/.hosa/kb" infra`, then `<hosa> cdc assemble "<root>/.hosa/kb"`: the cahier des charges gets it in annex D. « b » → redispatch `hosa-infra` (task `schema-<k>`) with the user's words as given, then the page again. Past 2 rounds, show the user what each round changed and let them decide. `done infra` refuses while the diagram is not validated (`avancement.py check infra`); `HOSA_SCHEMAS=0` turns the check off. A later change of a service (Mode 2) changes the diagram and loses the validation: Mode 2 runs this step again.

### Step 2: Dispatch Documentation

Dispatch `hosa-documentation` (Mode 1) with the lines `hosa-infra` returned under `## Documentation à produire`, as they are (paths, `retours` §4) — it writes the installation documentation into the managed project. Wait for its confirmation before reporting the environment as fully in place.

## Mode 3 — Deployment

Dispatched by `livraison` only (`hosa-infra` Mode 3). Relay its Open Questions on the target, access and rollback to the user.

## Mode 2 — Relay an On-Demand Installation Request

Modes 2 and 3 are not a stage: no `start`, no `done` — the `infra` stage stays as it is.

Any other agent, when it needs a server/framework/dependency it can't provision itself, returns that need under its own `## Installation nécessaire` field instead of dispatching `hosa-infra` directly (no agent dispatches another agent). Whichever skill dispatched that agent handles the relay:

1. Dispatch `hosa-infra` (Mode 2, `agents/infra.md`) with the requesting agent's name, what it needs, and why.
2. If it returns an Open Question (conflicting `Stack Decision`, ambiguous mode) — relay it to the user, get the answer, redispatch.
3. It changed `## Schéma de l'infrastructure` → Step 1b for it, without `start` or `done`.
4. Once it confirms the piece is in place, dispatch `hosa-documentation` (Mode 1) with its `## Documentation à produire` lines, as they are.
5. Redispatch the original requesting agent with the confirmation — it resumes the task that needed the installation.

## Commits

None here: the skill ends with the `hosa-git` checkpoint (`using-hosa`, Git checkpoints).

## Output

```
## Environnement Docker
- Services : <service> (<image>:<version épinglée>)
- Outillage qualité : tests [OK], navigateur [OK / sans objet], lint/format/types [OK], CI `<fichier>`
- Documentation : `<path>`
- Schéma de l'infrastructure : validé par l'utilisateur, au cahier des charges (annexe D)

## Open Questions
[Si rien : "None"]

## Suite
Suite : `ia` (étape `essai-ia`), lancé sans attendre.
```
