---
name: redaction
description: Use to turn cahier des charges interview notes into structured `Exigence` concepts in `.hosa/kb/cdc/`. Second stage of the CDC pipeline (interview → redaction → relecture → contestation). Works from `interview`'s notes in the same session, or from notes/answers the user pastes inline.
---

# Redaction

Writes one `Exigence` concept per business process into `.hosa/kb/cdc/`, using the structured body from the pipeline design (Objectif du processus / Données en entrée / Données en sortie / Qui fait quoi / Responsable / Besoin(s) persona répondu(s)).

## Flow

```
Source des notes : sortie de `interview` (même session) ou
notes inline de l'utilisateur
        ↓
Pour chaque processus : écrit une Exigence structurée
(status: draft) dans kb/cdc/
        ↓
Log kb/cdc/log.md
        ↓
Propose d'enchaîner sur `relecture`
```

## Trigger

Manual: `/redaction`. Auto: immediately after `interview` finishes, or "rédige les exigences" / "écris le cahier des charges" with notes provided inline.

---

## Step 1: Get the Notes

If `interview` just ran in this session, use its notes directly. Otherwise ask: "Quelles sont les notes à rédiger ?" — accept whatever structure the user provides; you don't require `interview`'s exact format.

## Step 2: Write One `Exigence` Per Process

```
mkdir -p .hosa/kb/cdc/
```

For each process, `.hosa/kb/cdc/<slug-processus>.md` (slug = kebab-case of the process name):

```markdown
---
type: Exigence
title: <nom du processus>
description: <une ligne : ce que ce processus accomplit>
tags: []
status: draft
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
## Objectif du processus
<une à deux phrases concrètes>

## Données en entrée
- <donnée nécessaire>

## Données en sortie
- <donnée produite>

## Qui fait quoi
- <rôle/persona> : <action concrète>

## Responsable
<rôle ou persona responsable>

## Besoin(s) persona répondu(s)
- [<persona>](../personnas/<slug>.md) : <besoin précis>
```

Use `generated: { by: human:<user>, at: <ISO8601> }` instead if the user dictated the content verbatim rather than you synthesizing it from interview notes.

If a process serves no specific persona (purely transverse — e.g. a compliance step), write `Aucun — exigence transverse.` under `## Besoin(s) persona répondu(s)` instead of a persona link. Every other section is still required — "transverse" doesn't excuse vagueness.

Every section must be filled with the specific content gathered — a section with no matching information from the notes means you're missing input, not that you should write a placeholder. If information is missing, ask the user rather than writing something generic.

## Step 3: Log

Append to `kb/cdc/log.md` (create if missing) — OKF §9: chronological, most recent date first, grouped by date.

## No Commits

You don't commit. Report what changed in the KB and let the user or the orchestrating flow decide when to commit.

## Output

```
## Exigences écrites
- `kb/cdc/<slug>.md` — <titre> (status: draft)

## Suite
Je lance `relecture` maintenant ?
```
