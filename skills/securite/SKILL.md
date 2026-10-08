---
name: securite
description: "Use to build security into the cahier des charges: `hosa-security` analyses data sensitivity and threats, writes security exigences and `Security Rule`s. CDC stage 4, mandatory. Triggers: \"sécurité dès la conception\", after `fondamentaux`."
---

# Sécurité

Security by design: the cybersecurity expert gives its constraints while the cahier des charges is being written, so they flow into the stack choice, the architecture, every ticket and every developer task. The end-of-project audit (`qualite`) stays — to catch what nobody could foresee, not what should have been required from the start.

## Flow

```
Dispatch hosa-security (Mode 1 Phase 1) : données et
sensibilité, acteurs, menaces par exigence → propositions
        ↓
Présente l'analyse et les propositions → l'utilisateur
valide, ajuste, ou accepte un risque explicitement
        ↓
Redispatch hosa-security (Phase 2) : écrit exigences [securite],
contraintes dans les exigences existantes, Security Rules,
kb/cdc/securite.md
        ↓
Enchaîne sur `relecture`
```

## Trigger

Manual: `/securite`. Auto: immediately after `fondamentaux`, or "analyse la sécurité du cahier des charges", "quelles sont les contraintes de sécurité ?", "sécurité dès la conception". `contestation` invokes it itself if `kb/cdc/securite.md` is missing or out of date.

---

## Step 1: Analyse

Dispatch `hosa-security` (Mode 1 Phase 1, `agents/security.md`). Relay its `## Open Questions` to the user (data classification, regulatory scope) and redispatch with the answers until it returns a complete analysis.

## Step 2: Validate

Present the analysis: the data and their sensitivity, then per exigence the threats and the proposed measure, then the proposed security exigences, constraints and rules. The user validates, adjusts, or drops a measure — a dropped measure on a real threat is an **accepted risk**: ask for the reason and keep it, it's recorded rather than forgotten.

## Step 3: Write

Redispatch `hosa-security` (Mode 1 Phase 2) with the validated choices and the accepted risks. It seeds and writes `kb/rules/security/`, writes the security exigences (`status: draft`, `tags: [securite]`), adds `## Contraintes de sécurité` to the existing exigences concerned, and writes `kb/cdc/securite.md`.

## No Commits

You don't commit. Report what changed in the KB and let the user decide.

## Output

```
## Analyse de sécurité
- Données sensibles : [liste et classification]
- Menaces traitées : N — risques acceptés : N

## Écrit
- `kb/cdc/<slug>.md` — [exigence de sécurité, ou contrainte ajoutée]
- `kb/rules/security/<slug>.md` — [règle]
- `kb/cdc/securite.md`

## Suite
**Q1 — Je lance `relecture` maintenant ?**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
```
