---
name: validation
description: "Use to accept or reject an implemented, tested ticket against its criteria, test results and recettes (`hosa-product-owner`). Required before the sprint merge. Triggers: \"valide le ticket X\", after `qa`."
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
        ↓
Suite : si tous les tickets du sprint sont validés, propose git Mode 2
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
- **Reject:** ticket stays `doing`/`blocked`. Relay the missing criterion/result to the user, and suggest the right next skill: `develop` (implementation gap), `debug` (technical bug), or `qa` (recette to re-run after a fix).

## Step 4: Log

Confirm `kb/tickets/log.md` was updated (per `hosa-product-owner`'s own logging) — chronological, most recent date first, per OKF §9.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB.

## Output

```
## Ticket <slug> — Validation
Verdict : Accepté (state: done) / Rejeté — [ce qui manque]

## Suite
[Si Rejeté : suggéré : develop / debug / qa]
[Si Accepté et tous les tickets du sprint sont désormais done :] Sprint <slug-sprint> entièrement validé.
**Q1 — Je fusionne le sprint maintenant ? (skill `git`, Mode 2)**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
[Si Accepté mais d'autres tickets du sprint restent en cours : "Ticket validé. Tickets restants du sprint : [liste]"]
```
