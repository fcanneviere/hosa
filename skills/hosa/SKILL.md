---
name: hosa
description: Use when initializing or updating the identity (name, objective, description, target audience) of the project Hosa manages and its personas, when creating an arbitrary OKF concept from a natural-language request that doesn't fit a more specific pipeline skill, or when answering a traceability question ("who asked for X?", "where does this rule come from?") against the KB. Manual trigger `/hosa`.
---

# Hosa

Initializes or updates the managed project's identity and personas in `.hosa/kb/`, creates any other OKF concept a natural-language request implies (when no more specific pipeline skill already owns it), and answers provenance questions by reading `generated`/`sources` straight from the KB. Full scope of the `hosa` skill from `docs/specs/2026-09-23-hosa-pilotage-design.md` §2.

## Flow

```
Check kb/project/identity.md
        ↓ missing                          ↓ exists
   Init flow                          Update flow
        ↓                                   ↓
Ask: nom → objectif → descriptif →    Show current values → ask which
public cible → objectifs mesurables   field(s) to change → confirm each
(KPI/OKR) → non-objectifs →                  ↓
contraintes → point de départ →       Apply confirmed changes
échéances/budget → langue
(one at a time)
        ↓
Ask personas one at a time
(nom + description) until
user says "terminé"
        ↓
Write kb/project/identity.md +
kb/personnas/<slug>.md per persona
        ↓
Dispatch hosa-key-user per persona: interroge
l'utilisateur → enrichit Identité/Objectifs/Besoins/
Attentes/Pain points/Quick wins
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
5. Objectifs mesurables (KPI/OKR — au moins un ; "aucun encore" accepté si l'utilisateur n'en a pas)
6. Non-objectifs (ce que ce projet ne cherche pas à faire — pour cadrer le périmètre)
7. Contraintes (techniques, réglementaires, business — "aucune" accepté)
8. Point de départ : projet neuf, ou code existant ? Si existant : ce qui doit être conservé tel quel (stack, conventions, modules) — "rien de particulier" accepté
9. Échéances et budget (date de livraison visée, jalons, enveloppe — "aucun" accepté)
10. Langue : de la documentation, et du code (identifiants, commentaires) — "français / anglais" par exemple

Then ask for personas one at a time: "Un persona à ajouter ? (nom + description, ou 'terminé' pour finir)". Repeat until the user says done. Zero personas is fine — don't force one if the user has none ready yet.

### Writing `kb/project/identity.md`

```
mkdir -p .hosa/kb/project/
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

## Objectifs mesurables
- <KPI/OKR>
[Ou "Aucun encore défini." si l'utilisateur n'en a pas]

## Non-objectifs
- <ce que ce projet ne cherche pas à faire>
[Ou "Aucun encore défini."]

## Contraintes
- <contrainte technique, réglementaire ou business>
[Ou "Aucune."]

## Point de départ
Neuf | Existant
- <ce qui doit être conservé tel quel>
[Ou "Rien de particulier."]

## Échéances et budget
- <échéance, jalon ou enveloppe>
[Ou "Aucun."]

## Langue
- Documentation : <langue>
- Code : <langue>
```

`contestation` later checks every `Exigence` against `## Objectifs mesurables` — an Exigence that serves none of them is a candidate for the "hors périmètre" route, cross-checked against `## Non-objectifs`. `hosa-senior-dev` reads `## Point de départ` and `## Échéances et budget` when proposing a stack; `hosa-documentation` writes in the `## Langue` documentation language.

### Writing personas

One file per persona in `.hosa/kb/personnas/<slug>.md` (slug = kebab-case of the persona name):

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

### Enriching personas

This flow only captures nom + description — not enough to embody the
persona for recette métier. Once all personas for this session are written
(the user has said "terminé"), for each persona just created dispatch
`hosa-key-user` in identification mode (persona file path, no recette
target) so it interrogates the user directly and writes back Identité /
Objectifs / Besoins / Attentes / Pain points / Quick wins to
`kb/personnas/<slug>.md`, per its own process. Do this one persona at a time
— don't batch the interrogation across personas.

Once every persona in this session has been enriched, propose the next
stage: "Personas prêts. Lancer l'interview du cahier des charges
maintenant ? (skill `interview`)". Yes → invoke the `interview` skill. No →
finish normally; `interview` stays invocable manually later. Skip this
proposal entirely if zero personas were created or enriched this session —
there's nothing yet to interview about.

### Logging

Append an entry to `kb/project/log.md` and `kb/personnas/log.md` (create if missing) — OKF §9 format: chronological, most recent date first, grouped by date.

---

## Update flow (`kb/project/identity.md` exists)

Read the current values and show them to the user. Ask which field(s) to change. Confirm each new value (echo it back, wait for yes) before writing — overwrite only the confirmed fields, leave the rest untouched. Log the update to `kb/project/log.md`.

Personas already in `kb/personnas/` are not touched by the update flow — adding a new persona later is a separate request ("ajoute un persona pour..."), following the same "Writing personas" + "Enriching personas" steps as the init flow.

---

## App

The app (`hosa/app/`) reads this data through the existing `GET /api/concepts?type=Project` and `GET /api/concepts?type=Persona` endpoints — this skill never touches app code. The home and personas pages already exist; running this skill just populates what they render.

---

## Free-form concept creation

Use this when a request names a concept type this skill doesn't already have a dedicated flow for above, and no more specific pipeline skill owns it either — a one-off `Exigence`, `Stack Decision`, `Ticket`, `Design Rule`, or `Security Rule` mentioned in passing that would otherwise be lost. **Don't use this to shortcut a pipeline stage**: an `Exigence` that should go through `interview`/`redaction` for a whole feature, a `Ticket` that `backlog` would normally derive from one, or a `Stack Decision` `stack` would normally justify with trade-offs — those still go through their own skill. This flow is for the isolated, out-of-band case: a need surfacing mid-conversation, in another skill's session, or the user just wants to note something down.

| L'utilisateur dit... | Action |
|---|---|
| "Ajoute cette exigence...", "Note dans le cahier des charges..." | Créer un concept `Exigence` dans `kb/cdc/`, `status: draft` |
| "Crée un ticket pour...", "Note ça pour plus tard" | Créer un `Ticket` dans `kb/tickets/`, `state: todo` |
| "On a décidé d'utiliser X pour...", "Choix technique :" | Créer une `Stack Decision` dans `kb/stack/` |
| "Retiens cette règle...", "À partir de maintenant on fait toujours X" | Créer une `Design Rule` dans `kb/rules/design/` |

Steps:
1. Identify the concept type and bundle from the table above (or ask if the request is genuinely ambiguous between two).
2. Write the minimal valid frontmatter for that type (`type`, `title`, `description`, `tags`, `status`/`state` as the type requires) plus whatever body content the request actually gave — never pad it with invented detail. `generated: { by: human:<user>, at: <ISO8601> }` when the user asked directly; `{ by: hosa/1.0, at: <ISO8601> }` only if you're the one deciding to capture something the user just mentioned in passing, without them asking for a concept to be written.
3. Log to the bundle's `log.md`.
4. If invoked from inside another skill's session (e.g. `build` hits an out-of-scope need mid-task) rather than the user directly: report the new `Ticket`/concept back to that skill instead of switching to Hosa mid-task — the calling skill decides whether to pause or continue.

## Traceability questions

"Qui a demandé X ?", "D'où vient cette règle ?", "Sur quelle base cette décision a été prise ?" — never guess, always answer straight from the KB:

1. Locate the concept(s) the question refers to (search `kb/` by title/content if the user doesn't name the file directly).
2. Read its `generated` field (who wrote/asked for it, and when) and `sources` if present (what it was derived from — another concept, an external document).
3. Answer in plain language, citing the file path and the actor exactly as recorded — `human:<user>` reads as "demandé par <user>", `<agent>/<version>` reads as "décidé par l'agent <agent>, pas explicitement demandé".
4. Concept not found, or `generated` missing (shouldn't happen — it's the one required OKF provenance field Hosa always fills) → say so plainly rather than guessing an answer.

## Output

```
## Identité / Personas
[Si Init/Update flow : résumé des changements]

## Concept créé
[Si Free-form creation : `kb/<bundle>/<slug>.md` — type, titre]

## Réponse
[Si question de traçabilité : la réponse, avec le chemin du fichier cité]

## Suite
[Comme applicable à la branche exécutée]
```
