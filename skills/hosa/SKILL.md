---
name: hosa
description: "Use to set up or update the managed project's identity and personas, to note an out-of-band concept (exigence, ticket, rule), or to answer \"qui a demandé X ?\" from the KB. Triggers: \"initialise le projet\", \"crée un persona\"."
---

# Hosa

Initializes or updates the managed project's identity and personas in `.hosa/kb/`, creates any other OKF concept a natural-language request implies (when no more specific pipeline skill already owns it), and answers provenance questions by reading `generated`/`sources` straight from the KB.

## Flow

```
Check kb/project/identity.md
        ↓ missing                          ↓ exists
   Init flow                          Update flow
        ↓                                   ↓
Crée .hosa/kb/index.md +              Show current values → ask which
git init si besoin (hosa-git Mode 0)
        ↓
Brief fourni ? → en extrait les
réponses, ne demande que le reste
        ↓
Ask: nom → objectif → descriptif →
public cible → objectifs mesurables   field(s) to change → confirm each
(KPI/OKR) → non-objectifs →                  ↓
contraintes → point de départ →       Apply confirmed changes
échéances/budget → langue →
niveau dev → niveau infra
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
        ↓
hosa-git Mode 3 : commit de la KB initiale
```

## Trigger

Manual: `/hosa [chemin/vers/brief.md]`. Auto: "initialise le projet", "configure hosa", "crée le projet Hosa", or anything asking to set up or change the project's identity or personas.

---

## Init flow (`kb/project/identity.md` doesn't exist)

### Bootstrap

Before any question, dispatch `hosa-git` (Mode 0, `agents/git.md`) on the project root: it initializes the repository if there's none, sets up the ignore rules, and creates the KB on its own branch `hosa-kb` (`kb_branch.py init`). Everything this skill and the ones after it write is versioned from the start. `kb_branch.py init` seeds `.hosa/kb/index.md`, the OKF root index (`okf` skill) without which the KB is invalid; if it is missing anyway, create it:

```markdown
---
okf_version: "0.2"
---
# KB Hosa
```

### Brief

If the user gave a brief file (`/hosa brief.md`, or pasted/named one): read it first and extract every answer it already gives to the questions below, plus any personas it describes. Show what was extracted as a numbered list and ask the user to confirm or correct it in one go; then ask only the questions the brief left unanswered. Never invent an answer the brief doesn't support — a missing answer is asked, not guessed. Copy the brief to `.hosa/kb/project/brief.md` (`type: Brief`, `generated: { by: human:<user>, at: <ISO8601> }`) and link it from `identity.md` so every later answer stays traceable to it.

### Questions

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
11. Ton niveau en développement : débutant / intermédiaire / expert
12. Ton niveau en infrastructure (serveurs, Docker, déploiement) : débutant / intermédiaire / expert
13. Taille du projet : petit (quelques écrans, un ou deux personas, un usage principal) / standard — propose "petit" when the description says so ("minuscule", "simple", "perso")

Then ask for personas one at a time: "Un persona à ajouter ? (nom + description, ou 'terminé' pour finir)". Repeat until the user says done. Zero personas is fine for now — don't force one if the user has none ready yet; but the cahier des charges (`interview`) can't start without one, so say so.

### Writing `kb/project/identity.md`

The KB is on its branch (`using-hosa`, KB location): on a first run, `hosa-git` Mode 0 (Bootstrap) has created it with `kb_branch.py init`; otherwise `status` must say it's in place. Then:

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

## Niveau de l'utilisateur
- Développement : débutant | intermédiaire | expert
- Infrastructure : débutant | intermédiaire | expert

## Taille
petit | standard
```

`contestation` later checks every `Exigence` against `## Objectifs mesurables` — an Exigence that serves none of them is a candidate for the "hors périmètre" route, cross-checked against `## Non-objectifs`. `hosa-senior-dev` reads `## Point de départ` and `## Échéances et budget` when proposing a stack; `hosa-documentation` writes in the `## Langue` documentation language. Every skill reads `## Niveau de l'utilisateur` before asking a technical question (see `using-hosa` Core Rules).

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
target). It writes back whatever of Identité / Objectifs / Besoins /
Attentes / Pain points / Quick wins it can derive to
`kb/personnas/<slug>.md`, and returns the rest under `## Open Questions` —
it can't ask the user itself. Ask those questions yourself, one at a time,
then redispatch it with the answers; repeat until it returns "None". Do this
one persona at a time — don't batch the interrogation across personas.

Once every persona in this session has been enriched, chain to `interview`
without asking ("Personas prêts. Je lance l'interview du cahier des charges.").
If zero personas exist, don't chain: say that `interview` needs at least one
persona, and ask whether to create one now.

### Logging

Append an entry to `kb/project/log.md` and `kb/personnas/log.md` (create if missing) — OKF §9 format: chronological, most recent date first, grouped by date.

Then dispatch `hosa-git` (Mode 3, checkpoint) to commit the initial KB on `hosa-kb` — the identity, the brief if any, the personas — before chaining to `interview`.

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
3. Log to the bundle's `log.md`. For a `Ticket`, then run `backlog`'s Single-Ticket Mode on it — it asks for whatever the request didn't give, instead of padding it.
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
