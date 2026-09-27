---
name: qa
description: Use to run a sprint's QA once it's implemented — dispatches `hosa-tester` against each ticket's technical test plan and `hosa-key-user` for its required recette, classifies failures, and routes them to the right owner (`debug` for technical bugs, `hosa-product-owner` for business gaps). Follow-on to `qa-plan`.
---

# QA

Runs the QA pass for an implemented sprint (`kb/sprints/<slug>.md`): technical tests via `hosa-tester`, business recette via `hosa-key-user`, one pass per ticket, plus a tooling-health check at the end.

## Flow

```
Lit kb/sprints/<slug>.md pour sa liste de tickets
        ↓
Vérifie que chaque ticket a un kb/test/<slug-ticket>-
technique.md
        ↓ manquant
Propose de lancer qa-plan d'abord
        ↓ tous présents
Pour chaque ticket : exécute les tests techniques
(hosa-tester), puis la recette (hosa-key-user) pour
chaque persona listée
        ↓
Échecs techniques trouvés → classe (bug d'implémentation
vs infrastructure de test), même logique que le skill test
        ↓
Recette Échoué/Partiel → route vers hosa-product-owner
        ↓
Fin de sprint : vérifie la santé de l'outillage (tests
flaky/lents récurrents) une fois, sur l'ensemble des runs
        ↓
Rapporte le verdict global du sprint
```

## Trigger

Manual: `/qa <slug-sprint>`. Auto: "exécute la QA du sprint", "teste le sprint", "fais la recette du sprint".

---

## Step 1: Read the Sprint and Check Preconditions

Read `kb/sprints/<slug>.md` for its `## Tickets` list. For each ticket, check that `hosa/kb/test/<slug-ticket>-technique.md` exists. If any ticket is missing its plan, say so and propose running `qa-plan` first rather than executing tests against a plan that doesn't exist — stop, don't partially execute.

## Step 2: Run Technical Tests Per Ticket

For each ticket:

1. Dispatch `hosa-tester` with the plan's `## Cas de test` as the brief, the recently changed files for this ticket, and the managed project's root path — the sprint's `worktree` path from `kb/sprints/<slug>.md` if it's still `active`, otherwise the root path from `Infra`.
2. Append a `## Résultats techniques` section to `kb/test/<slug-ticket>-technique.md` with the pass/fail detail, and refresh its `generated: { by: hosa-qa-lead/1.0, at: <ISO8601> }` frontmatter to this write's timestamp — the same attribution convention `hosa-qa-lead` uses whenever it creates or extends a `Test Plan`.
3. Classify any failure the same way the `test` skill already does: **implementation bug** (wrong output, uncaught exception, business logic error) → flag for `debug`; **test infrastructure issue** (bad import path, missing fixture, unconfigured environment) → report directly, don't suggest debug.

## Step 3: Run Recette Per Ticket

For each ticket, read `## Recette requise` from its `Test Plan`:

- If it lists persona(s): for each one, dispatch `hosa-key-user` with a recette request (same contract `recette` already sends) targeting this ticket. Write the result to `hosa/kb/test/<slug-ticket>-<slug-persona>.md`, in the format `recette` already uses (Step 3 of that skill). If the persona was enriched, log to `kb/personnas/log.md` too.
- If it reads "Aucune...": skip recette for this ticket and say so explicitly in the report — don't omit any mention of it.
- Any Échoué or Partiel scenario: flag this ticket for `hosa-product-owner` — the ticket itself needs rework, not a code fix.

## Step 4: Log

Append an entry to `kb/test/log.md` for every file touched in Steps 2-3 — chronological, most recent date first, per OKF §9.

## Step 5: Tooling Health

Once every ticket in the sprint has been run through Steps 2-3: review whether the same test was flagged flaky or slow across at least two of this session's runs (or against what's already known from prior sessions). If so, propose one concrete optimization and its reasoning — apply only if the user confirms. If nothing recurs, report "rien à signaler sur l'outillage" instead of inventing a proposal.

## No Commits

This skill does not commit. Report what changed in the KB and let the user decide when to commit.

## Output

```
## QA du sprint <slug>
- <ticket> — technique : X/Y passés — recette : Réussi/Échoué/Partiel/Non applicable

## Échecs techniques
- <ticket> — [détail] → suggéré : debug
[Si aucun : "Aucun"]

## Recette à corriger
- <ticket>/<persona> — [ce qui a échoué] → suggéré : hosa-product-owner
[Si aucun : "Aucun"]

## Outillage
[Proposition et justification, ou "Rien à signaler"]

## Suite
[Si tout est propre : "Sprint validé. Je fusionne le sprint maintenant (skill `git`) ?"]
[Sinon : liste des actions suggérées ci-dessus — pas d'offre de fusion tant que le verdict n'est pas propre]
```
