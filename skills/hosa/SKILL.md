---
name: hosa
description: Use when initializing or updating the Hosa project's identity (name, objective, description, target audience) and its personas in the KB. First slice of the `hosa` skill described in the pilotage spec — scoped to project init for now. Manual trigger `/hosa`.
---

# Hosa

Initializes or updates the Hosa project's identity and personas in `hosa/kb/`. This is the first slice of the `hosa` skill from `docs/simflow/specs/2026-09-23-hosa-pilotage-design.md` — broader responsibilities (creating arbitrary `Exigence`/`Ticket`/`Stack Decision` concepts from natural language, answering provenance questions) are a later increment, not covered here.

## Flow

```
Check kb/project/identity.md
        ↓ missing                          ↓ exists
   Init flow                          Update flow
        ↓                                   ↓
Ask: nom → objectif → descriptif →    Show current values → ask which
public cible (one at a time)          field(s) to change → confirm each
        ↓                                   ↓
Ask personas one at a time            Apply confirmed changes
(nom + description) until
user says "terminé"
        ↓
Write kb/project/identity.md +
kb/personnas/<slug>.md per persona
        ↓
Log to kb/project/log.md and
kb/personnas/log.md
```

## Trigger

Manual: `/hosa`. Auto: "initialise le projet", "configure hosa", "crée le projet Hosa", or anything asking to set up or change the project's identity or personas.

---

## Init flow (`kb/project/identity.md` doesn't exist)

Ask one question at a time, in order, waiting for an answer before moving on:
1. Nom du projet
2. Objectif (une phrase)
3. Descriptif (texte libre, plus long)
4. Public cible

Then ask for personas one at a time: "Un persona à ajouter ? (nom + description, ou 'terminé' pour finir)". Repeat until the user says done. Zero personas is fine — don't force one if the user has none ready yet.

### Writing `kb/project/identity.md`

```
mkdir -p hosa/kb/project/
```

```markdown
---
type: Project
title: <nom>
description: <objectif>
tags: []
status: stable
generated: { by: human:<user>, at: <ISO8601> }
---
## Description
<descriptif>

## Public cible
<public cible>
```

### Writing personas

One file per persona in `hosa/kb/personnas/<slug>.md` (slug = kebab-case of the persona name):

```markdown
---
type: Persona
title: <nom du persona>
description: <description>
tags: []
status: stable
generated: { by: human:<user>, at: <ISO8601> }
---
<description>
```

### Logging

Append an entry to `kb/project/log.md` and `kb/personnas/log.md` (create if missing) — OKF §9 format: chronological, most recent date first, grouped by date.

---

## Update flow (`kb/project/identity.md` exists)

Read the current values and show them to the user. Ask which field(s) to change. Confirm each new value (echo it back, wait for yes) before writing — overwrite only the confirmed fields, leave the rest untouched. Log the update to `kb/project/log.md`.

Personas already in `kb/personnas/` are not touched by the update flow — adding a new persona later is a separate request ("ajoute un persona pour...").

---

## App

The app (`hosa/app/`) reads this data through the existing `GET /api/concepts?type=Project` and `GET /api/concepts?type=Persona` endpoints — this skill never touches app code. The home and personas pages already exist; running this skill just populates what they render.
