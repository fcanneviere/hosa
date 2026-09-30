---
name: contestation
description: Use for the final challenge pass on the cahier des charges — `hosa-product-owner` re-questions personas on weak points via `hosa-key-user`, and `hosa-challenger` independently audits the assembled `kb/cdc/` for contradictions, blind spots, and risks. Fourth and last stage of the CDC pipeline; loops back to `redaction`/`interview` until clean, then asks the user for final sign-off.
---

# Contestation

The last line of defense before the cahier des charges is considered done: two independent challenges, not one self-check.

## Flow

```
Passe 1 — PO re-questionne les personas concernés (via
hosa-key-user) sur les points faibles connus
        ↓
Passe 2 — hosa-challenger audite l'ensemble de kb/cdc/ +
kb/personnas/, indépendamment
        ↓
Anomalies (l'une ou l'autre passe) → route vers redaction ou
interview → reboucle relecture → contestation
        ↓
Propre sur les deux passes → demande validation finale
à l'utilisateur
        ↓ oui
PO passe les exigences concernées en status: stable +
verified: human:<user> → log kb/cdc/log.md
```

## Trigger

Manual: `/contestation`. Auto: immediately after a clean `relecture`, or "challenge le cahier des charges".

---

## Step 1: PO → Personas Challenge

The PO always does its own quick pass over `kb/cdc/` first, looking for any need that reads as under-justified — `relecture` checks precision and completeness, not whether a stated need actually holds up, so a clean `relecture` report is not a reason to skip this. If `relecture` just ran, fold its findings in as additional candidates rather than replacing this pass. For each weak point tied to a persona, dispatch `hosa-key-user` (process-interview mode) with the PO's sharper question — "pourquoi ce besoin précisément", "qu'est-ce qui se passe si on ne le fait pas" — until the answer is either solid or the need turns out not to hold. If it doesn't hold, flag the exigence for rewrite in Step 3.

## Step 2: `hosa-challenger` Independent Audit

Dispatch `hosa-challenger` with the full content of `.hosa/kb/cdc/`, `.hosa/kb/personnas/`, and `kb/project/identity.md` if it exists. Take its verdict and findings as-is — don't pre-filter them before showing the user.

## Step 3: Route Anomalies

Combine anything from Step 1 (needs that didn't hold up) and Step 2 (challenger's findings). For each: route to `redaction` (needs rewriting with information already available) or `interview` (genuinely missing information) — except an "exigence hors objectifs" finding, which routes to the user directly: confirm whether it's genuinely out of scope (drop it, or move it to `## Non-objectifs`) or whether an objective is simply missing from `kb/project/identity.md` (add it via `hosa`, then re-check clean). After fixes, re-run `relecture` then `contestation` again — repeat until both passes are clean.

If a second full loop still finds anomalies, stop looping silently and tell the user directly: report what's still failing and ask whether to keep iterating or scope the affected exigence(s) down.

## Step 4: Final Sign-Off

Once Step 1 raised nothing new and `hosa-challenger` reports "Aucune anomalie": list every `Exigence` still at `status: draft` that this audit actually covered (every one Step 2 read — the full bundle, since `hosa-challenger` always receives all of `kb/cdc/`), then ask "Le cahier des charges est propre — tu valides ? (ces N exigences passeront en `stable`)". On yes, set `status: stable` and add `verified: { by: human:<user>, at: <ISO8601> }` on each one listed. Log the change to `kb/cdc/log.md`. Then dispatch `hosa-documentation` (Mode 1) with the newly-stable Exigence(s) and their linked persona(s) — it writes or updates the functional documentation. Wait for its confirmation before continuing.

If the user doesn't validate, ask what's still missing and treat it as a new anomaly — route it same as Step 3. No dispatch to `hosa-documentation` happens in this case — only an actual `stable` transition triggers it.

Once at least one `Exigence` has been validated to `stable` in this session, propose the next stage: "Le cahier des charges est stable. Je choisis la stack technique maintenant ? (skill `stack`)". Yes → invoke `stack`. No → finish normally; `stack` stays invocable manually later.

## No Commits

This skill doesn't commit. Report what changed (including any `status`/`verified` updates, and any persona Pain points/Quick wins `hosa-key-user` appended and logged to `kb/personnas/log.md` during Step 1). The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa` Core Rules, "Git checkpoints".

## Output

```
## Passe PO → Personas
- [Point faible] — [Solide / Ne tient pas → exigence à revoir]
- [If none reviewed: "Aucune — relecture n'avait rien signalé"]

## Passe hosa-challenger
[Its full report]

## Anomalies à router
- [Exigence] → [redaction / interview / utilisateur (hors objectifs)] — [pourquoi]
- [If none: "Aucune"]

## Verdict
[Propre, en attente de validation / N anomalie(s) à corriger / Validé — N exigence(s) passée(s) en stable]
```
