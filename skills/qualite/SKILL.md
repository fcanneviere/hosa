---
name: qualite
description: Use to audit the managed project's source code against a fixed checklist of coding best practices and performance — dispatches `hosa-senior-dev`, classifies findings by severity, and records them in `kb/qualite/`. Companion check usable anytime, not a forced pipeline stage. Security audits are `securite`'s.
---

# Qualité

Senior-dev pass over the managed project's actual source code — not the cahier des charges, not the spec-compliance `review` skill, but "is this code sound and safe to run". Checks a fixed checklist of best practices and performance, classifies anomalies, and routes blocking ones to a fix. Security is a separate audit with its own owner — `securite` (`hosa-security`); a request mixing both runs `qualite` then `securite` on the same scope.

## Flow

```
Détermine le projet géré (kb/infra/)
        ↓
Détermine le scope : fichiers modifiés récemment (session/dernier
ticket), ou codebase entière si demandé explicitement
        ↓
hosa-senior-dev audite : bonnes pratiques + performance (checklist fixe)
        ↓
Classe chaque anomalie : Bloquant / À corriger / Mineur
        ↓
Écrit kb/qualite/<slug>.md (Audit Qualité) + log
        ↓
Bloquant trouvé → propose debug
        ↓
Rapporte le verdict
```

## Trigger

Manual: `/qualite`. Auto: "audite la qualité du code", "vérifie les bonnes pratiques", "le code est-il propre ?". Security phrasing ("revue de sécurité", "check la sécurité") goes to `securite`.

---

## Step 1: Find the Managed Project and Scope

Read `kb/infra/` for the managed project's root path (same as `stack` Step 1 — if missing, stop and say so, this skill has nothing to audit without it).

Scope: if invoked right after a ticket/sprint was implemented, default to the files touched this session. Otherwise ask the user: "Codebase entière ou fichiers récents ?" — don't guess (Core Rule: no guessing).

## Step 2: Audit Checklist

Dispatch `hosa-senior-dev` with the scoped files. Best-practices and performance are its fixed checklist (below) — don't invent extra items, don't drop any without asking first, same discipline as `fondamentaux`. A security issue the agent notices in passing comes back as a pointer to `securite`, not as a classified finding here.

**Bonnes pratiques**
- Lisibilité : nommage clair, fonctions courtes, pas de code mort ou commenté
- Duplication : logique répétée qui devrait être factorisée
- Gestion des erreurs : pas d'exception avalée silencieusement, retours cohérents
- Dépendances : aucune ajoutée hors `hosa-infra`, aucune déclarée mais inutilisée (l'audit de vulnérabilités est celui de `securite`)
- Profondeur des modules : un module passe-plat (interface presque aussi complexe que son implémentation, dont la suppression ne compliquerait rien chez ses appelants) est un constat

**Performance**
- Requêtes N+1 : boucle qui déclenche une requête DB par itération au lieu d'un chargement groupé
- Index manquant sur une colonne filtrée/jointe d'une table qui peut grossir
- Boucle ou récursion sans borne sur une entrée non contrôlée en taille
- Ressource (connexion, fichier, curseur) ouverte sans être systématiquement libérée

Règle d'honnêteté des métriques : sans outil de mesure réel (profiler, APM, benchmark exécuté), ne jamais inventer un chiffre. Formule chaque constat comme un impact potentiel identifié par lecture statique — jamais comme une mesure.

## Step 3: Classify

For each anomaly found: **Bloquant** (bug qui corrompt des données ou casse un parcours), **À corriger** (non-bloquant mais doit être fait), **Mineur** (style, lisibilité).

## Step 4: Write and Log

Write `.hosa/kb/qualite/<slug>.md`:

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

Any **Bloquant** anomaly: dispatch `hosa-product-owner` (Responsibility 2/4) to create a `Ticket` (`state: todo`) linked to `kb/qualite/<slug>.md` and the finding's exact `fichier:ligne`, `generated: { by: hosa-senior-dev/1.0, at: <ISO8601> }` since it's the audit that surfaced it, not the user. Then propose `debug` scoped to that ticket. Don't fix it inline from this skill — `qualite` audits, it doesn't patch. **À corriger**/**Mineur** anomalies stay in the report only — don't create a ticket per minor finding, that's backlog noise.

## No Commits

You don't commit. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa` Core Rules, "Git checkpoints".

## Output

```
## Audit qualité — <scope>
- [Bloquant/À corriger/Mineur] — <fichier:ligne> — <problème>
- [If none: "Aucune anomalie"]

## Verdict
[Propre / N anomalie(s) à corriger]

## Tickets créés
- `kb/tickets/<slug>.md` — [finding] (state: todo)
[Si aucun Bloquant : "Aucun"]

## Suite
[Bloquant présent → "Je lance `debug` sur le ticket <slug> ?" / Sinon → "Rien à signaler."]
```
