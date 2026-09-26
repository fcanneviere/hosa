---
name: qualite
description: Use to audit the managed project's source code against a fixed checklist of coding best practices and security rules — dispatches `hosa-senior-dev`, classifies findings by severity, and records them in `kb/qualite/`. Companion check usable anytime, not a forced pipeline stage.
---

# Qualité

Senior-dev pass over the managed project's actual source code — not the cahier des charges, not the spec-compliance `review` skill, but "is this code sound and safe to run". Checks a fixed checklist of best practices and security rules, classifies anomalies, and routes blocking ones to a fix.

## Flow

```
Détermine le projet géré (kb/infra/)
        ↓
Détermine le scope : fichiers modifiés récemment (session/dernier
ticket), ou codebase entière si demandé explicitement
        ↓
hosa-senior-dev audite : bonnes pratiques + sécurité (checklist fixe)
        ↓
Classe chaque anomalie : Bloquant / À corriger / Mineur
        ↓
Écrit kb/qualite/<slug>.md (Audit Qualité) + log
        ↓
Bloquant trouvé → propose simflow:debug
        ↓
Rapporte le verdict
```

## Trigger

Manual: `/qualite`. Auto: "audite la qualité du code", "vérifie les bonnes pratiques", "fais une revue de sécurité du code", "check la sécurité du projet".

---

## Step 1: Find the Managed Project and Scope

Read `kb/infra/` for the managed project's root path (same as `stack` Step 1 — if missing, stop and say so, this skill has nothing to audit without it).

Scope: if invoked right after a ticket/sprint was implemented, default to the files touched this session. Otherwise ask the user: "Codebase entière ou fichiers récents ?" — don't guess (Core Rule: no guessing).

## Step 2: Audit Checklist

Dispatch `hosa-senior-dev` with the scoped files and this fixed checklist. Don't invent extra items, don't drop any without asking first — same discipline as `fondamentaux`.

**Bonnes pratiques**
- Lisibilité : nommage clair, fonctions courtes, pas de code mort ou commenté
- Duplication : logique répétée qui devrait être factorisée
- Gestion des erreurs : pas d'exception avalée silencieusement, retours cohérents
- Dépendances : pas de version connue pour être vulnérable, aucune ajoutée hors `hosa-infra`

**Sécurité (OWASP)**
- Injection : requêtes SQL paramétrées, aucune commande shell construite par concaténation d'une entrée utilisateur
- Validation des entrées aux frontières (API publique, formulaires) — jamais côté client seul
- Authentification/autorisation : contrôle d'accès sur chaque route sensible
- Secrets : aucune clé, mot de passe ou token en dur dans le code
- Données sensibles : pas de PII en log

## Step 3: Classify

For each anomaly found: **Bloquant** (faille de sécurité exploitable, bug qui corrompt des données), **À corriger** (non-bloquant mais doit être fait), **Mineur** (style, lisibilité).

## Step 4: Write and Log

Write `hosa/kb/qualite/<slug>.md`:

```markdown
---
type: Audit Qualité
title: Audit qualité — <scope>
description: <une ligne>
tags: []
status: stable
generated: { by: hosa-senior-dev/1.0, at: <ISO8601> }
---
## Anomalies
- [Bloquant/À corriger/Mineur] — <fichier:ligne> — <problème précis>

## Verdict
<Propre / N anomalie(s)>
```

Log to `kb/qualite/log.md` (create if missing) — OKF §9: chronological, most recent date first.

## Step 5: Route Blocking Findings

Any **Bloquant** anomaly: propose `simflow:debug` scoped to that finding. Don't fix it inline from this skill — `qualite` audits, it doesn't patch.

## No Commits

You don't commit. Report what changed in the KB and let the user decide.

## Output

```
## Audit qualité — <scope>
- [Bloquant/À corriger/Mineur] — <fichier:ligne> — <problème>
- [If none: "Aucune anomalie"]

## Verdict
[Propre / N anomalie(s) à corriger]

## Suite
[Bloquant présent → "Je lance `simflow:debug` sur <finding> ?" / Sinon → "Rien à signaler."]
```
