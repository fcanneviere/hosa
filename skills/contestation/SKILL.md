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

Source the weak points from `relecture`'s report if it just ran; otherwise the PO does a quick pass itself first to identify anything that reads as under-justified. For each weak point tied to a persona, dispatch `hosa-key-user` (process-interview mode) with the PO's sharper question — "pourquoi ce besoin précisément", "qu'est-ce qui se passe si on ne le fait pas" — until the answer is either solid or the need turns out not to hold. If it doesn't hold, flag the exigence for rewrite in Step 3.

## Step 2: `hosa-challenger` Independent Audit

Dispatch `hosa-challenger` with the full content of `hosa/kb/cdc/` and `hosa/kb/personnas/`. Take its verdict and findings as-is — don't pre-filter them before showing the user.

## Step 3: Route Anomalies

Combine anything from Step 1 (needs that didn't hold up) and Step 2 (challenger's findings). For each: route to `redaction` (needs rewriting with information already available) or `interview` (genuinely missing information). After fixes, re-run `relecture` then `contestation` again — repeat until both passes are clean.

If a second full loop still finds anomalies, stop looping silently and tell the user directly: report what's still failing and ask whether to keep iterating or scope the affected exigence(s) down.

## Step 4: Final Sign-Off

Once Step 1 raised nothing new and `hosa-challenger` reports "Aucune anomalie": ask the user "Le cahier des charges est propre — tu valides ? (les exigences passeront en `stable`)". On yes, for every `Exigence` touched in this cycle, set `status: stable` and add `verified: { by: human:<user>, at: <ISO8601> }`. Log the change to `kb/cdc/log.md`.

If the user doesn't validate, ask what's still missing and treat it as a new anomaly — route it same as Step 3.

## No Commits

This skill doesn't commit. Report what changed (including any `status`/`verified` updates) and let the user or the orchestrating flow decide when to commit.

## Output

```
## Passe PO → Personas
- [Point faible] — [Solide / Ne tient pas → exigence à revoir]
- [If none reviewed: "Aucune — relecture n'avait rien signalé"]

## Passe hosa-challenger
[Its full report]

## Anomalies à router
- [Exigence] → [redaction / interview] — [pourquoi]
- [If none: "Aucune"]

## Verdict
[Propre, en attente de validation / N anomalie(s) à corriger / Validé — N exigence(s) passée(s) en stable]
```
