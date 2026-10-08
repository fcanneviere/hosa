---
name: qa
description: Use to run a sprint's QA once it's implemented — dispatches `hosa-tester` against each ticket's technical test plan and `hosa-key-user` for its required recette, classifies failures, and routes them to the right owner (`debug` for technical bugs, `hosa-product-owner` for business gaps). Follow-on to `qa-plan`.
---

# QA

Runs the QA pass for an implemented sprint (`kb/sprints/<slug>.md`): technical tests via `hosa-tester`, business recette via `hosa-key-user`, one pass per ticket, plus a tooling-health check at the end. This skill is the only one that talks to the user or dispatches other agents — the actual briefing, classification, and routing is `hosa-qa-lead`'s.

## Flow

```
Vérifie que chaque ticket a un kb/test/<slug-ticket>-
technique.md
        ↓ manquant
Propose de lancer qa-plan d'abord
        ↓ tous présents
Dispatch hosa-data-engineer : recharge le jeu de données de test
        ↓ échec → rapporte, stop
Pour chaque ticket : dispatch hosa-qa-lead (Mode 2 Phase 1)
→ brief
        ↓
Dispatch hosa-tester avec le brief, puis hosa-key-user pour
chaque persona listée
        ↓
Redispatch hosa-qa-lead (Mode 2 Phase 2) avec les résultats
→ classe, route
        ↓
Fin de sprint : dispatch hosa-qa-lead (Mode 3) pour la santé
de l'outillage
        ↓
Rapporte le verdict global du sprint
```

## Trigger

Manual: `/qa <slug-sprint>`. Auto: "exécute la QA du sprint", "teste le sprint", "fais la recette du sprint".

---

## Step 1: Read the Sprint and Check Preconditions

Read `kb/sprints/<slug>.md` for its `## Tickets` list. For each ticket, check that `.hosa/kb/test/<slug-ticket>-technique.md` exists. If any ticket is missing its plan, say so and propose running `qa-plan` first rather than executing tests against a plan that doesn't exist — stop, don't partially execute.

Then dispatch `hosa-data-engineer` (Responsibility 4 reload, `agents/data-engineer.md`) so tests and recettes start from the documented dataset. No dataset yet → propose `qa-plan` first and stop. Reload fails → report it as a test infrastructure issue and stop — running tests against unknown data proves nothing.

## Step 2: Brief Per Ticket

For each ticket, dispatch `hosa-qa-lead` (Mode 2 Phase 1, `agents/qa-lead.md`). It returns the brief for `hosa-tester` (`## Cas de test`, recently changed files, the managed project's root path — the sprint's `worktree` path from `kb/sprints/<slug>.md` if it's still `active`, otherwise the root path from `Infra`) and, for each persona under `## Recette requise`, the brief for `hosa-key-user`.

## Step 3: Run Technical Tests Per Ticket

Dispatch `hosa-tester` with the brief from Step 2. Classify any failure the same way the `test` skill already does: **implementation bug** (wrong output, uncaught exception, business logic error) → dispatch `hosa-product-owner` to create a `Ticket` (`state: todo`, linked to the sprint ticket and the failing test) so it doesn't get lost as a mention in a report, then flag it for `debug`; **test infrastructure issue** (bad import path, missing fixture, unconfigured environment) → report directly, no ticket, don't suggest debug.

## Step 4: Run Recette Per Ticket

For each persona under `## Recette requise` from Step 2: dispatch `hosa-key-user` with a recette request (same contract `recette` already sends) targeting this ticket. If it reads "Aucune...", skip recette for this ticket and say so explicitly in the report — don't omit any mention of it. Any Échoué or Partiel scenario: dispatch `hosa-product-owner` to create a `Ticket` (`state: todo`, linked to the sprint ticket and the recette result) capturing exactly what the persona rejected — the ticket itself needs rework, not a code fix.

## Step 5: Dispatch to Record

Redispatch `hosa-qa-lead` (Mode 2 Phase 2) with `hosa-tester`'s report and every `hosa-key-user` recette result from Steps 3-4. It appends `## Résultats techniques` (with `hosa-tester`'s `Arbre testé` fingerprint, which lets `hosa-git` skip re-running a suite already passed on the exact same content at merge time), records each recette result, refreshes the `Test Plan`'s `generated` frontmatter to this write's timestamp, and logs to `kb/test/log.md` (and `kb/personnas/log.md` if a persona was enriched).

## Step 6: Tooling Health

Once every ticket in the sprint has been run through Steps 2-5: dispatch `hosa-qa-lead` (Mode 3 Phase 1) to review whether the same test was flagged flaky or slow across at least two of this session's runs. If it returns a proposal, present it to the user; if they confirm, redispatch `hosa-qa-lead` (Mode 3 Phase 2) to apply it. If nothing recurs, report "rien à signaler sur l'outillage".

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit.

## Output

```
## QA du sprint <slug>
- <ticket> — technique : X/Y passés — recette : Réussi/Échoué/Partiel/Non applicable

## Échecs techniques
- <ticket> — [détail] → ticket créé : `kb/tickets/<slug>.md` → suggéré : debug
[Si aucun : "Aucun"]

## Recette à corriger
- <ticket>/<persona> — [ce qui a échoué] → ticket créé : `kb/tickets/<slug>.md`
[Si aucun : "Aucun"]

## Outillage
[Proposition et justification, ou "Rien à signaler"]

## Suite
[Si tout est propre : "QA propre. Je lance la validation des tickets maintenant ? (skill `validation`)"]
[Sinon : liste des actions suggérées ci-dessus — pas d'offre de validation tant que le verdict n'est pas propre]
```
