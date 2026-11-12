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
Rétro : une question à l'utilisateur (ce qui l'a gêné ou aidé)
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

**Tâches.** Before Step 2, `avancement.py task add bilan-sprint revue --sprint <slug> --agent hosa-product-owner`; on its return, `task done bilan-sprint revue --sprint <slug> --sortie kb/sprints/<slug>-review.md` plus the tickets and rules it created. Stopped on an Open Question → `task block bilan-sprint revue --sprint <slug> --detail "<la question>"`, and `task add` it again once answered.

## Step 1b: Measure the Sprint

`<hosa> usage_report <root> --sprint <slug> --write` writes `## Mesures` in `kb/sprints/<slug>.md`: cost per ticket, review verdicts, the corrections by type with their findings proved or not reproduced (the relevance of reviews, audits and recettes), `hosa-debugger` passes, the main session's largest context, the longest agent passes, compared with the earlier sprints — and `### Propositions` for what crossed a threshold (e.g. `HOSA_HAIKU=0` when reviews fail on Haiku). Never apply a proposition yourself. Then `avancement.py … reponse --sprint <slug>` gives the questions' measure of the sprint (recommendations followed per stage and asker, from `kb/questions/log.md`): pass it to `hosa-product-owner` with `## Mesures` and show it in the report — a group marked « candidate à la décision par défaut » is a stop that decided nothing.

## Step 1c: The User's Retro

The measures say what cost; only the user says what got in their way. Before the dispatch, ask one question — the merge was just their decision, they are here:

**Q1 — Qu'est-ce qui t'a gêné ou aidé pendant ce sprint ?** Une ligne, ou « rien ».

It has no recommended option: never log it with `reponse`, which measures the recommendations followed. Pass it to `hosa-product-owner` as is, with the measures: its review keeps it under `## Points de friction récurrents` or `## Leçons`, in the user's words. A problem with Hosa itself goes to `kb/retours-hosa/journal.md` too (`using-hosa`, Auto-audit). « rien » is a normal answer.

## Step 2: Dispatch `hosa-product-owner`

Dispatch `hosa-product-owner` (Responsibility 7, `agents/product-owner.md`) with the sprint, its tickets' final states, every `kb/test/` result/recette verdict recorded for those tickets during `qa`, the `## Mesures` section (cost is a friction like any other), and the user's retro answer (Step 1c), in their words. It judges the objective, writes `kb/sprints/<slug>-review.md`, and creates any follow-up `Ticket`/`Design Rule` the review surfaces. Run `backlog`'s Single-Ticket Mode on each follow-up `Ticket` it lists, so the next sprint can plan it as is.

## Step 3: Log

Confirm `kb/sprints/log.md` was updated for the review, and `kb/tickets/log.md`/`kb/rules/design/log.md` for anything created — per `hosa-product-owner`'s own logging. Then the checkpoint (Commits below) and `avancement.py … done bilan-sprint --sprint <slug>` (it refuses without `kb/sprints/<slug>-review.md`), before the questions of the report.

## Commits

None here: the skill ends with the `hosa-git` checkpoint (`using-hosa`, Git checkpoints).

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
[Puis chaque question de `## Open Questions` de `hosa-product-owner`, toutes, à la suite — une leçon du bilan reste sans effet si sa question se perd.]
```
