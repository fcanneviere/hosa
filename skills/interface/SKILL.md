---
name: interface
description: "Use to design and scaffold a complete, navigable interface: style cards, layout directions and pages on comparison pages, front/back office navigation, lexicon, UX fundamentals, screenshot-verified scaffold with an independent review; also completes an existing one. Structuration stage 8. Triggers: \"conçois l'interface\", \"la navigation manque\"."
---

# Interface

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start interface`; refused → name the missing stage to the user and stop; refused as already done → a re-run only on the user's request: the same `start` with `--rouvre "<their request>"`. Stopped on a user question: `block interface --detail "<question>"`. Once the stage's output is written and committed: `done interface`. Never skip these calls: without them a cut session can't resume (« reprends »), and `budget.js` can't apply the stage's `dispatch` rules (each agent's model, the agents at once) — they hold only while the stage is `en cours`.

**Tâches.** Once Phase 1 (Step 1) has named the personas, list the dispatches in order: `task add interface interview-<persona> --agent hosa-key-user --objet <persona>` (one per persona), then `manche-styles`, `manche-directions`, `manche-page`, `3a`, `3b`, `3c`, `revue` (`--agent hosa-ux-designer`), `documentation` (`--agent hosa-documentation`). Each return → `task done interface <id> --sortie <the paths it wrote>`: an interview → write the persona's answer as is to `<root>/.hosa/design/besoins-<persona>.md` first (Phase 2 needs it after a `/clear`), and give that path; a round → its comparison page; 3a–3c, `revue`, `documentation` → the files they wrote. Identity kept → `task skip interface manche-styles --detail "identité conservée"` and `<hosa> atelier choisir <root>/.hosa/kb styles --conserve --par "<git user.name>"`. A gap redispatch (Step 4b) or a review below 8 re-adds the sub-phase it goes to (`task add` resets it to `à faire`); `3c` and `revue` keep their refusals, so the bound holds across rounds.

Turns the business logic (CDC), what each persona needs to see, and the existing software architecture into a real, scaffolded interface layer in the managed project — plus a visual identity and design rules for the whole project. This skill is the only one that talks to the user or dispatches other agents — the actual interview, proposal, design, and scaffold is `hosa-ux-designer`'s.

## Flow

```
Dispatch hosa-ux-designer (Phase 1: gather inputs, identify
personas to interview)
        ↓ Open Questions (missing Infra/CDC/stack/personas/project) → relay to user, stop
        ↓ Personas à interviewer
Dispatch hosa-key-user (UI-interview), un par persona,
tous dans un seul message
        ↓
Redispatch hosa-ux-designer (Phase 2), trois manches :
styles (cartes de style) → directions (navigation, lexique,
2–3 mises en page) → page (pages complètes front/back)
        ↓ chaque manche : page de comparaison → l'utilisateur choisit
        ↓
Redispatch hosa-ux-designer (Phase 3) avec les choix validés,
en trois passages : 3a KB (identité, règles, navigation,
lexique) → 3b scaffold navigable → 3c vérification (build,
routes, interface_check, captures)
        ↓ Installation nécessaire → hosa-infra, redispatch
        ↓ manques → redispatch avec la liste, jusqu'à complet
Dispatch hosa-ux-designer (Review), sans le raisonnement :
grille Oui/Non → atelier revue calcule la note
        ↓ grille incomplète → même fichier à compléter
        ↓ note < 8 → redispatch Phase 3 avec les R<n>
        ↓
Dispatch hosa-documentation (Mode 1) avec le
"Documentation à produire" retourné
        ↓
Met à jour l'entrée Infra avec le chemin confirmé
        ↓
Enchaîne sur `backlog`
```

## Trigger

Manual: `/interface`. Auto: immediately after `architecture`, or "conçois l'interface", "crée l'identité visuelle", "définis l'UX/UI du projet", "complète l'interface", "la navigation manque", "l'interface n'est pas utilisable".

---

## Completing an Existing Interface

If the interface was already scaffolded (an `Infra` `## Documentation d'interface` heading exists) but `interface_check.py` reports gaps — no `kb/interface/navigation.md`, screens missing, fundamentals not applied — run this same flow as a completion: Step 1 as usual; skip Step 2 and the identity/design-rule part of Step 3 when `## Identité visuelle` and `ux` `Design Rule`s already exist (unless the user wants to revisit them), but always present the navigation structure for validation; then Steps 4 to 6, extending the existing scaffold rather than replacing it. Each round skipped is recorded as kept: `<hosa> atelier choisir <root>/.hosa/kb <round> --conserve --par "<git user.name>" --note "<why>"` — `task done interface 3a` refuses a round with no line, and a project whose rounds predate `choix.md` passes the same way.

A `hosa-ux-designer` report with `## Reprise` (its tool-call budget is spent) → dispatch a fresh one, same phase and round, with that section and the user's choices — not the previous report.

## Step 1: Dispatch for Inputs and Personas

Dispatch `hosa-ux-designer` (Phase 1, `agents/ux-designer.md`) to gather `kb/infra/`, `kb/cdc/`, `kb/personnas/`, `kb/stack/`, and the architecture documentation, and to list every real persona needing a UI-interview.

If it returns an Open Question (no `Infra`/architecture doc, no `stable` `Exigence`, no `Stack Decision`, only the example persona or `Project`) — relay it to the user, propose the missing stage (`architecture`, `contestation`, `stack`, `hosa`), and only redispatch once resolved.

## Step 2: Interview Each Persona

For each persona under `## Personas à interviewer`, dispatch `hosa-key-user` as a UI-interview request: what this persona needs to see, in what order, which information is priority, what usage constraints apply (mobile, accessibility, autonomy...). One dispatch per persona — never two personas in one dispatch — and all the dispatches in one message: the personas are independent.

## Step 3: Dispatch for Proposals, Round by Round

Redispatch `hosa-ux-designer` (Phase 2) three times, with every persona's needs from Step 2 and the user's previous choice. Each round returns a comparison page (`## Pages de comparaison`): give the user its path as a link (`file://<absolute path>`) and tell them to open it in a browser. Ask the choice as one numbered question, the options lettered as on the page: the recommended one is a) on both. The page's « Copier la réponse » button gives the answer to paste (`Q1 b — <their request>`). Mixing two options or asking for a change is an answer too: the request goes in `--note`.

1. **`round: styles`** — 4–6 style cards: the visual identity and the design rules each implies. The user picks one.
2. **`round: directions`** — the navigation structure, the lexicon and 2–3 layout directions of the main screen in that style. The navigation is the part the user will live with every day: show it as a readable tree per role, not a paragraph. Show the lexicon as its table — each term with what it names and the synonyms it rules out — so the user fixes the words now, not screen by screen later. The user validates each item and picks a direction.
3. **`round: page`** — one complete page per space the exigences name, in that direction: the back-office home is the role's queue or dashboard, with its real indicators. The user validates it, or asks for changes (redispatch the same round).

After each answer, record it in the KB, then in the plan:

```bash
<hosa> atelier choisir <root>/.hosa/kb <round> <option id> --depuis <the round's cartes.json or manifest.json> --par "<git user.name>" [--note "<their request, as written>"]
<hosa> avancement <root>/.hosa/kb progress interface --detail "manche <round> : <option id>" --reprise "interface, manche <suivante>"
```

`atelier choisir` writes `kb/interface/choix.md` (then run `<hosa> okf_validate <root>/.hosa/kb`), and for `styles` the chosen card's tokens: the one definition of the identity, which Phase 3 reads and `atelier css` writes into the project's CSS. A card with a `variante` (the other mode) adds its tokens, written under `prefers-color-scheme` and `[data-theme]`. The screenshots are then taken in both modes (`capture --schemes light,dark`). A design tool needs them → `<hosa> atelier dtcg <root>/.hosa/kb --out <folder>` exports them in the W3C DTCG 2025.10 format, a derived file made again on request. A round played again adds its line; the last one counts. `task done interface 3a` refuses while a round has no line (control `choix`). The comparison pages are working files under `<root>/.hosa/design/`, ignored by git; what is chosen goes into the KB in Phase 3. An existing interface whose identity the user keeps → skip `styles`.

## Step 4: Dispatch to Record and Design

Redispatch `hosa-ux-designer` (Phase 3) with the user's validated choices, as three fresh dispatches in a row — one pass ran past its tool-call cap on thirty screens:
1. **3a** — reads the choices in `kb/interface/choix.md`, writes the visual identity to `kb/project/`, each design rule to `kb/rules/design/`, `kb/interface/navigation.md` and `lexique.md`, and applies the UX fundamentals.
2. **3b** — scaffolds the navigable interface from `navigation.md` and the validated pages, the tokens written by `atelier css`. A `## Reprise` → a fresh 3b with it, before 3c.
3. **3c** — verifies it, captures every route of `navigation.md` (`capture --navigation`), and returns `## Vérification` and `## Documentation à produire`.

Each dispatch gets the validated choices and the paths, not the previous report. A gap redispatch (Step 4b) goes to the sub-phase that owns it: KB → 3a, missing screen or route → 3b, then 3c again.

- **`## Installation nécessaire`** → dispatch `hosa-infra` (Mode 2) with it, then redispatch `hosa-ux-designer` (Phase 3) once confirmed.

## Step 4b: Completeness Gate

Run the checker yourself, from the managed project's root:

```bash
<hosa> interface_check .hosa/kb
<hosa> lexique_check .hosa/kb .
```

The loop is bounded by code: `task done interface 3c` runs these same checkers (control `interface` of `pipeline.json`). Refused → its exact lines go to the sub-phase that owns each one (KB, including a missing row of `## Gestion back office` or `## Tableaux de bord` → 3a; screen, route or tokens edited by hand in the project's CSS → 3b), then 3c again: `task add` the sub-phases, `task done` each, then `task done interface 3c` again. The control also reads the line 3c writes under `## Vérification` of `kb/interface/navigation.md`: a failed build or a route that doesn't render is a gap of the same round, counted like the others. Past 2 refusals of one cause the task is `bloqué`: stop, show the user what each round tried, a third round only on their word (`task add … --force`).

A gap on an exigence's missing `espace` isn't the designer's to fix, and the control leaves it out: `back interface fondamentaux --detail "espace manquant : <exigences>"`, then propose `fondamentaux`, where `hosa-product-owner` sets it with the user; `back` names the exigences in the plan, and `done fondamentaux` refuses while one lacks its `espace` or is still signed (it goes back to `draft` without `verified`); `relecture` and `contestation` then run again on them, and `done contestation` waits for the user's signature, then come back (`back` refused → a second round already: show the user the exigences still without `espace` and let them decide).

Then dispatch a **fresh** `hosa-ux-designer` in **Review** mode, with only the screenshot paths from `## Vérification`, the identity, the design rules, each persona's main tasks and a new grid path, `<root>/.hosa/design/revue/grille-<n>.json` — not the Phase 3 report: the review stays independent. The agent answers the grid's closed questions (`pipeline.json`, task `revue`); it never gives the note. On its return, compute and record it yourself:

```bash
<hosa> atelier revue <root>/.hosa/kb <the grid path it returned>
```

A complete grid → it appends `- <date> — note N/10 — grille O/T (k non, b bloquant) — R<n> <où> : <constat> → <correction> ; …` under `## Revue visuelle` of `kb/interface/navigation.md`. The note is the floor of 10 × Oui / (Oui + Non), capped by the lowest `plafond` of the questions answered Non (7 for a blocking one or a default template), and at 7 from the third Non (`trop_de_non` in `pipeline.json`). An incomplete grid (a Oui without the path of an existing capture, a Non without where, finding and fix, a Non applicable the question refuses, an identity with two modes whose Oui cite no capture of one mode) → it writes nothing. Either way, then `task done interface revue --sortie kb/interface/navigation.md <the grid path>`: control `grille` reads the grid with the same code and refuses its exact gaps, a line that isn't this grid's, or a note written by hand; control `score` refuses a note under 8. Each control counts its own refusals against the task's bound: a badly filled grid doesn't spend a design round. Grid gaps → redispatch the review with them and the same grid path, to complete that file; a low note → redispatch Phase 3 with the line's `R<n>` items as they are, then a fresh review on a new grid file. A kept design checked on its own rules → write `- <date> — sans note — <issues>` yourself; no screenshots (no Node or Chrome) → `- <date> — sans captures — T-tests à la place`, and say so; both pass without a grid.

Don't move on to documentation with an incomplete or inconsistently named interface — a forbidden synonym in the code, a screen missing from the lexicon: an exigence with no screen, an orphan screen, a UX fundamental neither done nor justified as not applicable, or tokens edited by hand in the project's CSS (`interface_check` compares them with `kb/interface/choix.md`).

## Step 5: Dispatch Documentation

Dispatch `hosa-documentation` (Mode 1) with the lines `hosa-ux-designer` returned under `## Documentation à produire`, as they are (paths, `retours` §4) — it writes the interface documentation into the managed project. Wait for its confirmation and the path it wrote to.

## Step 6: Update the `Infra` Entry

Add the confirmed interface documentation path to the `Infra` entry under its own `## Documentation d'interface` heading — a fixed heading, not a bare line, so a later reader (`backlog`) can tell it apart from the architecture documentation path `architecture` also records there. If that heading already exists (a re-run), update the path in place rather than duplicating the heading. Log the update to `kb/infra/log.md`.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa`, "Git checkpoints".

## Output

```
## Interviews personas
- <persona> — [besoins surfacés]

## Identité visuelle
[Palette/typo/ton retenus, et où c'est écrit]

## Règles de design
- `kb/rules/design/<slug>.md` — [règle]

## Couche interface conçue
[Écrans/composants retenus et pourquoi]

## Plan de navigation
- `kb/interface/navigation.md` — [N écrans, rôles couverts]

## Structures créées
- `<path>` — [dossier/composant scaffoldé]

## Vérification
- Build : [OK / échec] — routes rendues : [X / Y] — interface_check : [complet / manques]

## Revue visuelle
- Note : [N/10] — [problèmes restants, ou "aucun"] — captures : `<dossier>`

## Documentation
- `<path>`

## Open Questions
[Si rien : "None"]

## Suite
Suite : `backlog`, lancé sans attendre.
```
