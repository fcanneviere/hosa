---
name: qa
description: "Use to run a sprint's QA: `hosa-tester` per ticket (autonomous, records results, cleans up), `hosa-key-user` recettes, failures routed. Triggers: \"exécute la QA du sprint\", \"teste le sprint\", \"fais la recette du sprint\"."
---

# QA

Runs the QA pass for an implemented sprint (`kb/sprints/<slug>.md`): technical tests via `hosa-tester`, business recette via `hosa-key-user`, one pass per ticket, plus a tooling-health check at the end. This skill is the only one that talks to the user or dispatches other agents — `hosa-tester` runs each ticket's tests on its own and records the results; `hosa-qa-lead` only looks after the tooling at the end.

## Flow

```
Vérifie que chaque ticket a un kb/test/<slug-ticket>-
technique.md
        ↓ manquant
Propose de lancer qa-plan d'abord
        ↓ tous présents
Vérifie l'environnement Docker du sprint et la remise à zéro
documentée du jeu de données
        ↓ manquant → propose qa-plan / git, stop
Pour chaque ticket : dispatch hosa-tester (Exécuter) avec le
slug — il trouve tout, teste, corrige le côté tests, enregistre
ses résultats et fait le ménage
        ↓
Dispatch hosa-key-user pour chaque persona de « Recette
requise », écrit chaque résultat de recette
        ↓
Route les échecs : défaut → `develop <ticket> correction` dans
le sprint ; besoin nouveau → ticket au backlog (hosa-product-owner)
        ↓
Fin de sprint : dispatch hosa-qa-lead (Mode 2) pour la santé
de l'outillage
        ↓
Rapporte le verdict global du sprint
```

## Trigger

Manual: `/qa <slug-sprint> [<slug-ticket>]` — a ticket given re-runs Steps 3-5 for it alone (after a correction). Auto: "exécute la QA du sprint", "teste le sprint", "fais la recette du sprint".

---

## Step 1: Read the Sprint and Check Preconditions

Read `kb/sprints/<slug>.md` for its `## Tickets` list. For each ticket, check that `.hosa/kb/test/<slug-ticket>-technique.md` exists. If any ticket is missing its plan, say so and propose running `qa-plan` first rather than executing tests against a plan that doesn't exist — stop, don't partially execute.

Read the sprint's `docker_project`: missing on an `active` sprint → run `git` Mode 1 (reattach) first, which starts the sprint's own environment. Then `docker_check.py <docker_project> <worktree>` must pass — it guarantees tests and recettes run on this sprint's files, not a previous sprint's; a failure is recreated from the worktree before going on. 

The test dataset must exist with its documented `## Remise à zéro` (prepared by `qa-plan` before the sprint started) — `hosa-tester` and `hosa-key-user` reset to it at the start and end of every pass. No dataset, or no reset command → propose `qa-plan` first and stop: running tests against unknown data proves nothing.

## Step 3: Run Technical Tests Per Ticket

For each ticket, dispatch `hosa-tester` (Exécuter mode) with just the ticket slug — it finds the test plan, the worktree, the `docker_project` and the ticket's changed files itself, runs and completes the tests, fixes test-side problems on its own, appends `## Résultats techniques` (with its `Arbre testé`, which lets `hosa-git` skip re-running a suite already passed on the exact same content at merge time) and resets the environment. Relay `## Installation nécessaire` to `hosa-infra` and `## Open Questions` to the user, then redispatch. `## Tests à faire par toi` → show it to the user as is (T-numbered, `retours` section 3b), with the environment running at its reference state; relay the one-line answer to `hosa-tester`, which records and routes it. Route what it classified: **implementation bug** (wrong output, uncaught exception, business logic error) → the ticket goes back to `doing` and is fixed **in this sprint**: `develop <ticket> correction` with the failing test and its output (it uses `debug` on the sprint's worktree when the cause is unclear), then this QA again for that ticket alone. The failure stays recorded in `## Résultats techniques`, so nothing gets lost. Count the correction cycles per ticket: the same test still failing for the same reason after 2 corrections → stop looping and escalate to the user with what each cycle tried, asking whether the problem is the ticket (`hosa-product-owner`), the structure (`architecture`/`schema-app`/`schema-db`) or the test. A different failure restarts the count; **test infrastructure issue** (bad import path, missing fixture, unconfigured environment) → report directly, no ticket, don't suggest debug.

## Step 4: Run Recette Per Ticket

For each persona under the ticket's `## Recette requise` (in `kb/test/<slug-ticket>-technique.md`): dispatch `hosa-key-user` with a recette request (same contract `recette` already sends) targeting this ticket. If it reads "Aucune...", skip recette for this ticket and say so explicitly in the report — don't omit any mention of it. Any Échoué or Partiel scenario: the ticket's own `## Critères d'acceptation` not met → `develop <ticket> correction` in this sprint, like a bug. The persona wants something the criteria never asked for → dispatch `hosa-product-owner` to create a `Ticket` (`state: todo`, linked to the sprint ticket and the recette result) and run `backlog`'s Single-Ticket Mode on it: a new need goes to the backlog, it doesn't block this sprint.

## Step 5: Record the Recettes

Write each `hosa-key-user` result to `.hosa/kb/test/<slug-ticket>-<slug-persona>.md` in the exact format `recette` uses, and log it to `kb/test/log.md` (and `kb/personnas/log.md` if a persona was enriched). The technical results are already recorded by `hosa-tester` — check its `## Résultats enregistrés` points at the plan; missing → redispatch it rather than writing them yourself.

After each ticket (tests, recettes, results recorded): `avancement.py … progress qa --sprint <slug> --detail "<ticket> : QA faite (k/n)" --reprise "qa <ticket suivant>"`.

## Step 5b: Environment Left Clean

`hosa-tester` and every `hosa-key-user` end their pass with the dataset's reset and verification (their `## Ménage`). Check every report has it: a missing or failed `## Ménage`, or residues named there, means the next ticket would start on polluted data — redispatch `hosa-data-engineer` with `model: sonnet` (Responsibility 4 reload) before the next ticket, and hand the residue to Step 6 as a tooling issue.

## Step 6: Tooling Health

Once every ticket in the sprint has been run through Steps 3-5: dispatch `hosa-qa-lead` (Mode 2 Phase 1) to review whether the same test was flagged flaky or slow across at least two of this session's runs, and every residue reported under `## Ménage` — data a test or a recette leaves that the reset doesn't cover gets a concrete fix (test isolation, or extending the documented reset), not a note. If it returns a proposal, present it to the user; if they confirm, redispatch `hosa-qa-lead` (Mode 2 Phase 2) to apply it. If nothing recurs, report "rien à signaler sur l'outillage".

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit.

## Output

```
## QA du sprint <slug>
- <ticket> — technique : X/Y passés — recette : Réussi/Échoué/Partiel/Non applicable

## Échecs techniques
- <ticket> — [détail] → suggéré : `develop <ticket> correction`
[Si aucun : "Aucun"]

## Recette à corriger
- <ticket>/<persona> — [ce qui a échoué] → `develop <ticket> correction`, ou ticket créé (besoin nouveau) : `kb/tickets/<slug>.md`
[Si aucun : "Aucun"]

## Ménage
[Environnement remis à l'état de référence après chaque passage — ou résidus et action]

## Outillage
[Proposition et justification, ou "Rien à signaler"]

## Suite
[Si tout est propre :] QA propre.
Suite : `validation`, lancé sans attendre.
[Sinon : liste des actions suggérées ci-dessus — pas d'offre de validation tant que le verdict n'est pas propre]
```
