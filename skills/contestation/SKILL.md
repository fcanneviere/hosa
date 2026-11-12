---
name: contestation
description: "Use for the final challenge of the cahier des charges (PO re-questions personas, `hosa-challenger` audits) and the user's sign-off. CDC stage 7; requires fondamentaux, juridique, securite, relecture. Triggers: \"challenge le cahier des charges\", after a clean relecture."
---

# Contestation

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start contestation`; refused → name the missing stage to the user and stop. Stopped on a user question: `block contestation --detail "<question>"`. Once the stage's output is written and committed: `done contestation`. Never skip these calls: without them a cut session can't resume (« reprends ») and the session stays on the wrong model.

The last line of defense before the cahier des charges is considered done: two independent challenges, not one self-check.

## Flow

```
Passe 1 — PO re-questionne les personas concernés (via
hosa-key-user) sur les points faibles connus
        ↓
Passe 2 — hosa-challenger audite l'ensemble de kb/cdc/ +
kb/personnas/, indépendamment
        ↓
Anomalies (l'une ou l'autre passe) → kb/cdc/relecture.md,
tour c<n>, avec gravité et origine
        ↓
Bloquantes → route vers redaction ou interview → reboucle
relecture → contestation
Mineures seules → redaction les corrige en une fois, sans boucle
        ↓
Aucune bloquante sur les deux passes → demande validation finale
à l'utilisateur
        ↓ oui
PO passe les exigences concernées en status: stable +
verified: human:<user> → log kb/cdc/log.md
```

## Trigger

Manual: `/contestation`. Auto: immediately after a clean `relecture`, or "challenge le cahier des charges".

---

## Step 0: Fondamentaux Gate

Run this gate once per session, at the first entry: coming back from Step 3 after `relecture`, skip it — a fix to an exigence is already re-checked by `relecture`, and re-running `fondamentaux` for it restarts the whole chain.

`kb/cdc/fondamentaux.md` must exist, and be at least as recent (`generated.at`) as the newest `Exigence` in `kb/cdc/` that is not tagged `fondamentaux`, `juridique` or `securite` (those stages write their own exigences after it, so counting them makes the gate fail on every normal pass) — otherwise the basics haven't been checked against what the cahier des charges now says. Missing or older → say so, `back contestation fondamentaux --detail "<why>"` (it reopens `fondamentaux`, then `relecture`, then `contestation`), and run `fondamentaux`. Same for `kb/cdc/juridique.md` (`Analyse juridique`) → `back contestation juridique`, and for `kb/cdc/securite.md` (`Analyse de sécurité`) → `back contestation securite`, each followed by `relecture`. A cahier des charges is never signed off without its basic functions, its legal constraints and its security constraints in it.

## Step 1: PO → Personas Challenge

The PO always does its own quick pass over `kb/cdc/` first, looking for any need that reads as under-justified — `relecture` checks precision and completeness, not whether a stated need actually holds up, so a clean `relecture` report is not a reason to skip this. If `relecture` just ran, fold its findings in as additional candidates rather than replacing this pass. For the weak points tied to a persona, dispatch `hosa-key-user` (process-interview mode) once per persona, with all that persona's questions in the one dispatch (a dispatch per question reloads the persona each time), each with the PO's sharper question — "pourquoi ce besoin précisément", "qu'est-ce qui se passe si on ne le fait pas" — until the answer is either solid or the need turns out not to hold. An answer the agent marks `[à confirmer]` is its deduction, not the persona's word (`interview`, « Who knows what »): it settles nothing until the user confirms it — ask it as a numbered question. If the need doesn't hold, flag the exigence for rewrite in Step 3.

## Step 2: `hosa-challenger` Independent Audit

Dispatch `hosa-challenger` with the full content of `.hosa/kb/cdc/` (`fondamentaux.md`, `juridique.md`, `securite.md`, `modele-metier.md`, `decisions.md` and `relecture.md` included — what `relecture` found is not found again), `.hosa/kb/personnas/`, and `kb/project/identity.md` if it exists — never `kb/project/cahier-des-charges.md`, which repeats the fiches. On a loop coming back from Step 3, give it only the exigences changed since its last report (files of `kb/cdc/` modified after its `generated.at`, plus `git log` on `hosa-kb`) and that report: it re-audits those and the exigences linked to them, and says what it did not re-read. Take its verdict and findings as-is — don't pre-filter them before showing the user.

## Step 3: Route Anomalies

Combine anything from Step 1 (needs that didn't hold up) and Step 2 (challenger's findings). For each: route to `redaction` (needs rewriting with information already available) or `interview` (genuinely missing information) — except an "exigence hors objectifs" finding, which routes to the user directly: confirm whether it's genuinely out of scope (drop it, or move it to `## Non-objectifs`) or whether an objective is simply missing from `kb/project/identity.md` (add it via `hosa`, then re-check clean).

Write each one into `kb/cdc/relecture.md` § Anomalies, after the last number, in its format: `- A<n> [c<k>, <gravité>, <origine>] — …` — `c1` for this skill's first round, `c2` for the next. The gravity and the origin are the challenger's (the PO's for Step 1, with `relecture` Step 4's definitions); on `c2` and later, a new finding in a passage no fix touched is recorded only if `bloquante`. A `regle-hosa` finding also gets its line in `kb/retours-hosa/journal.md`. Then run `<hosa> cdc revue "<root>/.hosa/kb"` and fix the lines it refuses. The findings now survive a cut session, and `redaction` works from that list.

Route by gravity — only a `bloquante` makes a loop. `bloquante` findings open → record the round in the plan: `back contestation interview --detail "<A-numbers> : <one line>"` when one needs information never gathered (it reopens `interview`, `redaction`, `relecture`), otherwise `back contestation redaction --detail "…"` (it reopens `redaction`, `relecture`); `redaction` fixes the open `mineure` ones in the same pass. After fixes, re-run `relecture` then `contestation` again — repeat until neither pass finds a `bloquante`. Only `mineure` findings → no `back`, no new `relecture`: run `redaction` in its « Fixing a relecture » mode on them, without its `avancement.py` calls, then go to Step 4.

`back` refused (exit 1: a second full loop already found anomalies) → stop looping and tell the user directly: report what's still failing and ask whether to keep iterating (`back … --force`) or scope the affected exigence(s) down.

## Step 4: Final Sign-Off

Once Step 1 raised nothing new and `hosa-challenger` reports no `bloquante` (its `mineure` ones fixed, Step 3), prove completeness:

```bash
<hosa> cdc check "<root>/.hosa/kb"
```

Exit 1 → the cahier des charges is not signed: every hole (an objective no exigence serves, a priority or a lot not chosen, a state with no way out, a right nobody decided, an open question of `kb/cdc/decisions.md`, a persona need nobody judged, a line still `[à confirmer]`) is an anomaly, routed as in `relecture` Step 3b. The open questions go to the user now, numbered Q1… with their proposed answer; `redaction` records the answers. Then back to `relecture`: `back contestation relecture --detail "cdc check : <N> trous"` (or `back contestation redaction` when `redaction` must record answers first).

Exit 0 → `<hosa> cdc assemble "<root>/.hosa/kb"`. List every `Exigence` still at `status: draft` that this audit actually covered (every one Step 2 read — the full bundle, since `hosa-challenger` always receives all of `kb/cdc/`), then ask "Le cahier des charges est propre et complet : `kb/project/cahier-des-charges.md`. Tu le valides ? (ces N exigences passeront en `stable`)". The user signs the document, not a list of files. On yes, set `status: stable` and add `verified: { by: human:<user>, at: <ISO8601> }` on each one listed. Log the change to `kb/cdc/log.md`, then run `cdc assemble` again: the document turns `stable` and names its signatory. Then dispatch `hosa-documentation` (Mode 1) with the newly-stable Exigence(s) and their linked persona(s) — it writes or updates the functional documentation. Wait for its confirmation before continuing.

If the user doesn't validate, ask what's still missing and treat it as a new anomaly — route it same as Step 3, with its `back`. `done contestation` refuses while an `Exigence` is not `stable` with its `verified`, or `cdc check` finds a hole. No dispatch to `hosa-documentation` happens in this case — only an actual `stable` transition triggers it.

Once at least one `Exigence` has been validated to `stable` in this session, chain to `stack` without asking (the user just signed the cahier des charges off): say "Le cahier des charges est stable. Je lance le choix de la stack." and invoke it.

## No Commits

This skill doesn't commit. Report what changed (including any `status`/`verified` updates, and any persona Pain points/Quick wins `hosa-key-user` appended and logged to `kb/personnas/log.md` during Step 1). The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa`, "Git checkpoints".

## Output

```
## Passe PO → Personas
- [Point faible] — [Solide / Ne tient pas → exigence à revoir]
- [If none reviewed: "Aucune — relecture n'avait rien signalé"]

## Passe hosa-challenger
[Its full report]

## Anomalies à router
- [A-number] [c<k>, gravité, origine] [Exigence] → [redaction / interview / utilisateur (hors objectifs)] — [pourquoi]
- [If none: "Aucune"]

## Complétude
`cdc check` : [complet / N trou(s) — par matrice]

## Mesure
[the table of `<hosa> cdc mesure "<root>/.hosa/kb"`, relecture and contestation passes together]

## Verdict
[Propre, en attente de validation de `kb/project/cahier-des-charges.md` / N anomalie(s) ou trou(s) à corriger / Validé — N exigence(s) passée(s) en stable]
```
