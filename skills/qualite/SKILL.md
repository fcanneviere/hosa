---
name: qualite
description: Use to audit the managed project's source code — `hosa-senior-dev` for best practices and performance, `hosa-security` for security (conformity to the rules set at design time, plus the holes nobody could foresee) — classifies findings by severity and records them in `kb/qualite/`. Companion check usable anytime, and before a release.
---

# Qualité

Senior-dev and cybersecurity pass over the managed project's actual source code — not the cahier des charges, not the spec-compliance `review` skill, but "is this code sound and safe to run". Checks a fixed checklist of best practices and security rules, classifies anomalies, and routes blocking ones to a fix.

## Flow

```
Détermine le projet géré (kb/infra/)
        ↓
Détermine le scope : fichiers modifiés récemment (session/dernier
ticket), ou codebase entière si demandé explicitement
        ↓
hosa-senior-dev audite bonnes pratiques + performance, et
hosa-security audite la sécurité (règles de conception + imprévus)
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

Manual: `/qualite`. Auto: "audite la qualité du code", "vérifie les bonnes pratiques", "fais une revue de sécurité du code", "check la sécurité du projet".

---

## Step 1: Find the Managed Project and Scope

Read `kb/infra/` for the managed project's root path (same as `stack` Step 1 — if missing, stop and say so, this skill has nothing to audit without it).

Scope: if invoked right after a ticket/sprint was implemented, default to the files touched this session. Otherwise ask the user: "Codebase entière ou fichiers récents ?" — don't guess (Core Rule: no guessing).

## Step 2: Audit Checklist

Dispatch, on the same scope and in parallel, `hosa-senior-dev` (best practices and performance — its fixed checklist below; don't invent extra items, don't drop any without asking first) and — when the project has a database (`kb/infra/base-de-donnees.md`) — `hosa-dba` (Mode 4 Audit, `agents/dba.md`: migrations reversible and conflict-free, indexes against the queries actually run, least-privilege account, backups and their last restore test), and `hosa-security` (Mode 2, `agents/security.md`): conformity to the `Security Rule`s and security exigences set during the cahier des charges, then the unforeseen holes. Security constraints were designed in from the start (`securite`); this audit is the safety net for what nobody could foresee. If `kb/rules/security/` is empty because `securite` never ran, say so — the audit still runs on the baseline rules, but propose `securite` so the next features are built with them.

**Bonnes pratiques**
- Lisibilité : nommage clair, fonctions courtes, pas de code mort ou commenté
- Duplication : logique répétée qui devrait être factorisée
- Gestion des erreurs : pas d'exception avalée silencieusement, retours cohérents
- Dépendances : audit natif du gestionnaire de paquets sur le lockfile committé (aucune vulnérabilité critique/haute non mitigée), aucune ajoutée hors `hosa-infra`

**Performance**
- Requêtes N+1 : boucle qui déclenche une requête DB par itération au lieu d'un chargement groupé
- Index manquant sur une colonne filtrée/jointe d'une table qui peut grossir
- Boucle ou récursion sans borne sur une entrée non contrôlée en taille
- Ressource (connexion, fichier, curseur) ouverte sans être systématiquement libérée

Règle d'honnêteté des métriques : sans outil de mesure réel (profiler, APM, benchmark exécuté), ne jamais inventer un chiffre. Formule chaque constat comme un impact potentiel identifié par lecture statique — jamais comme une mesure.

## Step 3: Classify

For each anomaly found: **Bloquant** (faille de sécurité exploitable, bug qui corrompt des données), **À corriger** (non-bloquant mais doit être fait), **Mineur** (style, lisibilité).

## Step 4: Write and Log

`hosa-senior-dev` writes `.hosa/kb/qualite/<slug>.md`, `hosa-dba` writes `.hosa/kb/qualite/<slug>-bdd.md`, `hosa-security` writes `.hosa/kb/qualite/<slug>-securite.md` (same structure, `tags: [securite]`, each finding marked prévisible/imprévisible):

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

Any **Bloquant** anomaly, from either audit: dispatch `hosa-product-owner` (Responsibility 2/4) to create a `Ticket` (`state: todo`) linked to `kb/qualite/<slug>.md` and the finding's exact `fichier:ligne`, `generated: { by: <hosa-senior-dev or hosa-security>/1.0, at: <ISO8601> }` — whichever audit surfaced it, not the user. Run `backlog`'s Single-Ticket Mode on it so it's complete, then propose `debug` scoped to that ticket. Don't fix it inline from this skill — `qualite` audits, it doesn't patch. **À corriger**/**Mineur** anomalies stay in the report only — don't create a ticket per minor finding, that's backlog noise. Each new `Security Rule` `hosa-security` proposes from an unforeseen finding: ask the user, and on yes it's written to `kb/rules/security/` so the next tickets are built with it.

## No Commits

You don't commit. Report what changed in the KB and let the user decide.

## Output

```
## Audit qualité — <scope>
- [Bloquant/À corriger/Mineur] — <fichier:ligne> — <problème>
- [If none: "Aucune anomalie"]

## Audit sécurité — <scope>
- [Bloquant/À corriger/Mineur] — <fichier:ligne> — <problème> — [prévisible : <règle> / imprévisible]
- Règles proposées : [nouvelle Security Rule, ou "Aucune"]

## Verdict
[Propre / N anomalie(s) à corriger]

## Tickets créés
- `kb/tickets/<slug>.md` — [finding] (state: todo)
[Si aucun Bloquant : "Aucun"]

## Suite
[Bloquant présent → "Je lance `debug` sur le ticket <slug> ?" / Sinon → "Rien à signaler."]
```
