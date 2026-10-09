---
name: validation
description: "Use to accept or reject an implemented, tested ticket against its criteria, test results and recettes (`hosa-product-owner`), then run the sprint demo with the user. Required before the sprint merge. Triggers: \"valide le ticket X\", after `qa`."
---

# Validation

Closes the loop `develop` opens: a ticket doesn't become `done` just because it was implemented and merged tests passed — `hosa-product-owner` checks it against its own `## Critères d'acceptation`, the technical results, and the recette verdict, then accepts or bounces it.

## Flow

```
Lit kb/tickets/<slug>.md et kb/test/<slug>-technique.md
        ↓ résultats techniques absents ou recette requise non
          exécutée → propose qa d'abord, stoppe
        ↓ tout présent
Dispatch hosa-product-owner (Responsibility 5)
        ↓ Accepté → state: done + verified (machine-confirmed)
        ↓ Rejeté → reste doing/blocked, motif renvoyé à develop/
          debug/qa selon la nature du manque
Log kb/tickets/log.md
        ↓ tous les tickets du sprint acceptés
Démo : hosa-qa-lead (Mode 3) écrit les tests T1… → l'utilisateur
les fait → résultat écrit dans le sprint (## Démo)
        ↓ KO → develop <ticket> correction → qa → validation
        ↓ tout OK
Suite : propose git Mode 2
```

## Trigger

Manual: `/validation <slug-ticket>`. Auto: "valide le ticket X", "accepte le ticket X" ; proposé en Suite de `develop` et de `qa` une fois le verdict propre.

---

## Step 1: Read and Check Preconditions

Read `kb/tickets/<slug>.md`. If it has no `## Critères d'acceptation` (written before `backlog` carried this field, or written standalone), say so and ask the user to confirm the ticket informally instead — don't invent criteria. Read `kb/test/<slug>-technique.md`: if it doesn't exist, or its most recent `## Résultats techniques` is missing, propose running `qa-plan`/`qa` first and stop. If `## Recette requise` names a persona with no matching verdict file yet, propose `qa` and stop.

## Step 2: Dispatch `hosa-product-owner`

Dispatch `hosa-product-owner` (Responsibility 5, `agents/product-owner.md`) with the ticket, its acceptance criteria, its technical results, and its recette verdict(s). It returns Accept or Reject with a reason.

## Step 3: Apply the Verdict

- **Accept:** `hosa-product-owner` writes `state: done` and `verified: { by: hosa-product-owner/1.0, at: <ISO8601> }` on the ticket directly (it already owns `kb/tickets/` writes) — confirm it did.
- **Reject:** ticket stays `doing`/`blocked`. Relay the missing criterion/result to the user, and suggest the right next skill: `develop <ticket> correction` (an implementation gap or a bug, fixed in this sprint), or `qa` (a recette or a test to re-run after a fix).

## Step 3b: Sprint Demo

Once every ticket of the sprint is `done`, the user checks the sprint working, in its environment — the agents' recettes simulate personas; the demo is a person. Dispatch `hosa-qa-lead` (Mode 3) and show its T-tests as is, with the sprint's environment running at the dataset's reference state. The user answers in one line ("T1 OK, T2 KO : …").
- All OK → write `## Démo` in `kb/sprints/<slug>.md`: the date, each T-test and `OK`. Log to `kb/sprints/log.md`.
- A KO → record it the same way, then `develop <ticket> correction` with the user's words as the defect report; after its `qa` and `validation`, redo only the failed T-tests.
- The user says the demo isn't needed this time → write `## Démo` with "Non faite — choix de l'utilisateur" and the date. `hosa-git` refuses the merge with no `## Démo` at all.

## Step 4: Log

Confirm `kb/tickets/log.md` was updated (per `hosa-product-owner`'s own logging) — chronological, most recent date first, per OKF §9.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB.

## Output

```
## Ticket <slug> — Validation
Verdict : Accepté (state: done) / Rejeté — [ce qui manque]

## Suite
[Si Rejeté : suggéré : `develop <ticket> correction` / qa]
[Si Accepté et tous les tickets du sprint sont désormais done :] Sprint <slug-sprint> entièrement validé. Démo : [T-tests ci-dessous / faite : tout OK].
[T1, T2… de `hosa-qa-lead` Mode 3, tant que la démo n'est pas faite]
[Démo faite et OK :]
**Q1 — Je fusionne le sprint maintenant ? (skill `git`, Mode 2)**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
[Si Accepté mais d'autres tickets du sprint restent en cours : "Ticket validé. Tickets restants du sprint : [liste]"]
```
