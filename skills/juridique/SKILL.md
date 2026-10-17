---
name: juridique
description: "Use to put every legal constraint (RGPD, AI Act, cookies, LCEN, consumer law, accessibility, sector rules) in the cahier des charges before the stack — legal exigences, `## Contraintes juridiques`, processing register. CDC stage 4, mandatory; legal Go/No-Go inside `livraison`. Dispatches `hosa-legal`. Triggers: \"conformité RGPD\", \"AI Act\", \"contraintes juridiques\", after `fondamentaux`."
---

# Juridique

Compliance by design. `hosa-legal` reads the cahier des charges right after the basics are in, says which regulations apply, and turns each obligation into a testable exigence. A consent screen, a retention period or a human review of an AI decision is then in the backlog from day one — not a surprise at the recette. It runs before `securite`: `hosa-security` reads the legal decisions (retention, data location, vendors) and designs the technical measures on top of them. Before each release, a gate checks that every legal constraint was delivered and that nothing new — a tracker, a vendor, an AI feature — slipped in behind the register's back.

## Modes

| Mode | When | Agent mode | Writes |
|---|---|---|---|
| **Analyse** | CDC stage 4, right after `fondamentaux` (default inside the CDC pipeline) | Mode 1 | `kb/cdc/juridique.md`, legal exigences, `## Contraintes juridiques` |
| **Livraison** | Inside `livraison`, after the security gate | Mode 2 | `kb/juridique/livraison-<version>.md` |

## Flow (Analyse)

```
hosa-legal Mode 1 Phase 1 : contexte, qualification des réglementations,
registre des traitements, systèmes d'IA, propositions
        ↓ Open Questions → Q1, Q2… à l'utilisateur, redispatch
Présente les obligations, incluses par défaut — l'utilisateur
ne retire qu'avec une raison ; tranche les choix ouverts
        ↓
hosa-legal Mode 1 Phase 2 : exigences juridiques (draft),
## Contraintes juridiques, kb/cdc/juridique.md
        ↓
Checkpoint hosa-git (Mode 3), puis enchaîne : securite (Analyse)
```

## Trigger

Manual: `/juridique [analyse|livraison]`. Auto: immediately after `fondamentaux`; "vérifie la conformité RGPD", "est-ce que l'AI Act s'applique ?", "quelles contraintes juridiques ?", "conformité dès la conception". `contestation` invokes Analyse itself if `kb/cdc/juridique.md` is missing or out of date; `livraison` invokes Livraison. Progress-plan stage: `juridique` (CDC pipeline).

---

## Step 1: Analyse

Dispatch `hosa-legal` (Mode 1 Phase 1). Relay its `## Open Questions` (country, B2B/B2C, sector, release date, AI vendor) and redispatch with the answers until the analysis is complete.

## Step 2: Confirm

Show the user, in this order:
1. the regulations that apply, and those ruled out, each with its reason;
2. the AI features and their AI Act classification;
3. the proposed legal exigences and the constraints added to existing exigences — **included by default**;
4. the open choices (legal basis, retention period, vendor outside the EU…), as numbered questions with the recommended answer;
5. the documents to produce outside the software (DPA, AIPD, privacy policy, CGU…).

A legal obligation is dropped only with the user's reason, recorded in `kb/cdc/juridique.md` — never silently. Tell the user once that this analysis prepares the design and doesn't replace a lawyer or a DPO; the points marked « à valider » need one.

## Step 3: Write

Redispatch `hosa-legal` (Mode 1 Phase 2) with the validated choices and the reasons for what was dropped. It writes the legal exigences (`status: draft`, `tags: [juridique]`), adds `## Contraintes juridiques` to the exigences concerned, and writes `kb/cdc/juridique.md`.

## Livraison (Mode 2)

Dispatch `hosa-legal` (Mode 2) with the version, the planned release date and the previous release's date. Relay its Open Questions (a required document still `à faire`: done or not?) and redispatch with the answers; a document the user confirms done is updated in `kb/cdc/juridique.md` (`état : fait le <date>`). Return the verdict to `livraison`.

**No-Go** → one numbered question: fix first (recommended — a missing constraint becomes a ticket via `hosa-product-owner`, `priority: 1`, then `backlog`'s Single-Ticket Mode; a new vendor or AI feature reruns Analyse), or ship anyway knowingly. Shipping anyway is written in `kb/juridique/livraison-<version>.md` under `## Dérogation` with the user's reason and `generated.by: human:<user>` — the user's decision, written down, never implied. Say once that a derogation doesn't remove the legal risk.

## Commits

None here: the skill ends with the `hosa-git` checkpoint (`using-hosa`, Git checkpoints).

## Output

```
## Juridique — <mode>
- [Livraison] `kb/juridique/livraison-<version>.md` — Go / No-Go [avec dérogation] — points KO : N — tickets créés : […]
- [Analyse] Réglementations applicables : [liste] — non applicables : N — incertaines : N
- Systèmes d'IA : [exigence — classification] / Aucun
- Écrit : `kb/cdc/juridique.md`, N exigences juridiques, N contraintes ajoutées
- Écartées par l'utilisateur : N — documents hors logiciel : [liste]

## Suite
[Analyse → `securite` (Analyse), lancé sans attendre. Livraison → retour à `livraison`.]
```
