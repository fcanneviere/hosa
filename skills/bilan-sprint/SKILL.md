---
name: bilan-sprint
description: "Use after a sprint merges: `hosa-product-owner` judges the objective, delivered vs deferred, recurring friction, and writes the Sprint Review and follow-ups. Triggers: \"fais le bilan du sprint X\", \"rétro\", after the merge."
---

# Bilan Sprint

Sprint Review and retro: not just "which tickets closed", but whether the sprint's objective actually landed, and what should change next time.

## Flow

```
Lit kb/sprints/<slug>.md (state: done attendu) et ses tickets
        ↓ pas encore fusionné (state != done) → propose git Mode 2
          d'abord, stoppe
Mesure le sprint : usage_report.py --sprint --write → ## Mesures
Dispatch hosa-product-owner (Responsibility 7)
        ↓
Écrit kb/sprints/<slug>-review.md + tickets de suivi et/ou
Design Rules process
        ↓
Log kb/sprints/log.md et kb/tickets/log.md (si tickets créés)
        ↓
Rapporte le bilan
```

## Trigger

Manual: `/bilan-sprint <slug-sprint>`. Auto: "fais le bilan du sprint X", "rétro du sprint X", "sprint review" ; proposé en Suite de `git` Mode 2.

---

## Step 1: Read the Sprint and Check Preconditions

`avancement.py … start bilan-sprint --sprint <slug>`: refused (not merged yet) → propose `git` Mode 2 and stop — a review before the merge reviews an unfinished sprint. Read `kb/sprints/<slug>.md`, its `## Tickets` list and each linked `kb/tickets/<slug-ticket>.md` for final `state`.

## Step 1b: Measure the Sprint

`<python> "${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/usage_report.py" <root> --sprint <slug> --write` writes `## Mesures` in `kb/sprints/<slug>.md`: cost per ticket, review verdicts, `hosa-debugger` passes, the main session's largest context, the longest agent passes, compared with the earlier sprints — and `### Propositions` for what crossed a threshold (e.g. `HOSA_HAIKU=0` when reviews fail on Haiku). Never apply a proposition yourself.

## Step 2: Dispatch `hosa-product-owner`

Dispatch `hosa-product-owner` (Responsibility 7, `agents/product-owner.md`) with the sprint, its tickets' final states, every `kb/test/` result/recette verdict recorded for those tickets during `qa`, and the `## Mesures` section (cost is a friction like any other). It judges the objective, writes `kb/sprints/<slug>-review.md`, and creates any follow-up `Ticket`/`Design Rule` the review surfaces. Run `backlog`'s Single-Ticket Mode on each follow-up `Ticket` it lists, so the next sprint can plan it as is.

## Step 3: Log

Confirm `kb/sprints/log.md` was updated for the review, and `kb/tickets/log.md`/`kb/rules/design/log.md` for anything created — per `hosa-product-owner`'s own logging.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB.

## Output

```
## Bilan du sprint <slug>
- Objectif : [Atteint / Partiellement atteint / Non atteint]
- Livré : [n tickets]
- Reporté : [n tickets] — [suite proposée]
- Friction récurrente : [résumé, ou "Aucune"]
- Mesures : [coût par ticket, et l'écart aux sprints précédents]

## Créé
- `kb/sprints/<slug>-review.md`
- Tickets de suivi / Design Rules : [liste, ou "Aucun"]

## Suite
**Q1 — Je livre ce qui vient d'être fusionné ? (skill `livraison` : audit qualité, version testée et taguée, déploiement si tu le veux)**
  a) Oui, maintenant. (recommandé si le sprint apporte une version utilisable)
  b) Non, pas cette fois : l'étape est marquée « non applicable » pour ce sprint.
[Si des tickets de suivi ont été créés :]
**Q2 — Je les priorise dans le backlog maintenant ? (skill `sprint` au prochain cycle)**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
[Pour chaque ligne de `### Propositions` autre que « Aucune », une question numérotée :]
**Q3 — <la proposition> : je l'applique pour le prochain sprint ?**
  a) Oui. b) Non, on garde le réglage actuel.
```
