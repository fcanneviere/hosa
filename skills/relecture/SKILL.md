---
name: relecture
description: "Use to check every exigence for precision, completeness and consistency, routing gaps to `redaction` or `interview`. CDC stage 5. Triggers: \"relis le cahier des charges\", after `securite`."
---

# Relecture

Reads the cahier des charges as written and checks it holds up — not a rewrite, a precision check.

## Flow

```
Scope : exigences écrites ou modifiées dans cette session
(redaction, fondamentaux, securite), ou l'ensemble de kb/cdc/
si appelé seul
        ↓
Pour chaque exigence : les 8 sections sont-elles remplies,
précises, sans généralité ?
        ↓
Cohérence entre exigences : sorties/entrées qui s'enchaînent,
responsables non contradictoires
        ↓
Anomalies trouvées → route vers redaction (à corriger) ou
interview (info manquante)
        ↓
Propre → propose d'enchaîner sur `contestation`
```

## Trigger

Manual: `/relecture`. Auto: immediately after `securite`, or "relis le cahier des charges".

---

## Step 1: Scope

In the pipeline, `relecture` runs after `securite`: check every `Exigence` written or changed in this session by `redaction`, `fondamentaux` and `securite`. Invoked alone, read every `Exigence` in `.hosa/kb/cdc/`.

## Step 2: Precision and Completeness Check

For each exigence, check every section against these standards — mark **OK** or **Anomalie** with the exact problem:
- `Objectif du processus`: concrete and specific, not a restatement of the title
- `Données en entrée` / `Données en sortie`: named data, not "les infos nécessaires" or other placeholders
- `Qui fait quoi`: names an actual persona/rôle for every action listed, not "l'utilisateur" generically when a specific persona applies
- `Règles de gestion`: each rule testable — a condition, a threshold, a calculation or a status change with an example; not "selon les règles en vigueur". "Aucune règle propre" only for pure entry or consultation
- `Cas d'erreur`: at least one, each with the expected reaction; not "gérer les erreurs"
- `Responsable`: exactly one clear owner, not "l'équipe" or left implicit
- `espace` (frontmatter, functional exigences — not `nfr`): `front-office`, `back-office` or both, consistent with the roles in `Qui fait quoi`
- `Besoin(s) persona répondu(s)`: a real link to a `kb/personnas/` file, or an explicit "Aucun — exigence transverse"

## Step 3: Cross-Exigence Consistency

Check pairs of exigences that plausibly connect (one's output feeds another's input, or they share a responsable):
- Does a claimed `Données en entrée` actually get produced somewhere as `Données en sortie`, or is it assumed from nowhere?
- Do two exigences assign the same responsibility to different responsables?

## Step 4: Report and Route

For each anomaly: which exigence, the exact problem, and whether it needs a **rewrite** (route to `redaction`) or is missing **information that was never gathered** (route to `interview`).

If no anomalies: report "Propre" and propose `contestation` as the next step.

## No Commits

This skill only reads and reports — it doesn't edit `kb/cdc/` itself. Fixes happen in `redaction`.

## Output

```
## Anomalies
- [Exigence] — [OK / Anomalie: <problème précis>] — [si anomalie: → redaction | → interview]
- [If none: "Aucune"]

## Verdict
[Propre / N anomalie(s) à corriger]

## Suite
[Propre :]
**Q1 — Je lance `contestation` maintenant ?**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
[Sinon :] liste des exigences à renvoyer et vers quel skill.
```
