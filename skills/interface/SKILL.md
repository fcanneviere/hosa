---
name: interface
description: "Use to design and scaffold a complete, navigable interface: style cards, layout directions and pages on comparison pages, front/back office navigation, lexicon, UX fundamentals, screenshot-verified scaffold with an independent review; also completes an existing one. Structuration stage 8. Triggers: \"conçois l'interface\", \"la navigation manque\"."
---

# Interface

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start interface`; refused → name the missing stage to the user and stop; refused as already done → a re-run only on the user's request: the same `start` with `--rouvre "<their request>"`. Stopped on a user question: `block interface --detail "<question>"`. Once the stage's output is written and committed: `done interface`. Never skip these calls: without them a cut session can't resume (« reprends »), and `budget.js` can't apply the stage's `dispatch` rules (each agent's model, the agents at once) — they hold only while the stage is `en cours`.

**Tâches.** Once Phase 1 (Step 1) has named the personas, list the dispatches in order: `task add interface interview-<persona> --agent hosa-key-user --objet <persona>` (one per persona), then `manche-styles`, `manche-directions`, `manche-page`, `3a`, `3b`, `3c`, `revue` (`--agent hosa-ux-designer`), `documentation` (`--agent hosa-documentation`). Each return → `task done interface <id> --sortie <the paths it wrote>`: an interview → write the persona's answer as is to `<root>/.hosa/design/besoins-<persona>.md` first (Phase 2 needs it after a `/clear`), and give that path; a round → its comparison page; 3a–3c, `revue`, `documentation` → the files they wrote. Identity kept → `task skip interface manche-styles --detail "identité conservée"`. A gap redispatch (Step 4b) or a review below 8 re-adds the sub-phase it goes to (`task add` resets it to `à faire`); `3c` and `revue` keep their refusals, so the bound holds across rounds.

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
note /10 et problèmes → redispatch Phase 3 si < 8
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

If the interface was already scaffolded (an `Infra` `## Documentation d'interface` heading exists) but `interface_check.py` reports gaps — no `kb/interface/navigation.md`, screens missing, fundamentals not applied — run this same flow as a completion: Step 1 as usual; skip Step 2 and the identity/design-rule part of Step 3 when `## Identité visuelle` and `ux` `Design Rule`s already exist (unless the user wants to revisit them), but always present the navigation structure for validation; then Steps 4 to 6, extending the existing scaffold rather than replacing it.

A `hosa-ux-designer` report with `## Reprise` (its tool-call budget is spent) → dispatch a fresh one, same phase and round, with that section and the user's choices — not the previous report.

## Step 1: Dispatch for Inputs and Personas

Dispatch `hosa-ux-designer` (Phase 1, `agents/ux-designer.md`) to gather `kb/infra/`, `kb/cdc/`, `kb/personnas/`, `kb/stack/`, and the architecture documentation, and to list every real persona needing a UI-interview.

If it returns an Open Question (no `Infra`/architecture doc, no `stable` `Exigence`, no `Stack Decision`, only the example persona or `Project`) — relay it to the user, propose the missing stage (`architecture`, `contestation`, `stack`, `hosa`), and only redispatch once resolved.

## Step 2: Interview Each Persona

For each persona under `## Personas à interviewer`, dispatch `hosa-key-user` as a UI-interview request: what this persona needs to see, in what order, which information is priority, what usage constraints apply (mobile, accessibility, autonomy...). One dispatch per persona — never two personas in one dispatch — and all the dispatches in one message: the personas are independent.

## Step 3: Dispatch for Proposals, Round by Round

Redispatch `hosa-ux-designer` (Phase 2) three times, with every persona's needs from Step 2 and the user's previous choice. Each round returns a comparison page (`## Pages de comparaison`): give the user its path as a link (`file://<absolute path>`) and tell them to open it in a browser. Ask the choice as one numbered question, the options lettered as on the page. Mixing two options or asking for a change is an answer too.

1. **`round: styles`** — 4–6 style cards: the visual identity and the design rules each implies. The user picks one.
2. **`round: directions`** — the navigation structure, the lexicon and 2–3 layout directions of the main screen in that style. The navigation is the part the user will live with every day: show it as a readable tree per role, not a paragraph. Show the lexicon as its table — each term with what it names and the synonyms it rules out — so the user fixes the words now, not screen by screen later. The user validates each item and picks a direction.
3. **`round: page`** — one complete page per space in that direction. The user validates it, or asks for changes (redispatch the same round).

After each answer: `avancement.py … progress interface --detail "manche <round> choisie" --reprise "interface, manche <suivante>"`. The comparison pages are working files under `<root>/.hosa/design/`, ignored by git; what is chosen goes into the KB in Phase 3. An existing interface whose identity the user keeps → skip `styles`.

## Step 4: Dispatch to Record and Design

Redispatch `hosa-ux-designer` (Phase 3) with the user's validated choices, as three fresh dispatches in a row — one pass ran past its tool-call cap on thirty screens:
1. **3a** — writes the visual identity to `kb/project/`, each design rule to `kb/rules/design/`, `kb/interface/navigation.md` and `lexique.md`, and applies the UX fundamentals.
2. **3b** — scaffolds the navigable interface from `navigation.md` and the validated pages. A `## Reprise` → a fresh 3b with it, before 3c.
3. **3c** — verifies it, takes the screenshots and returns `## Vérification` and `## Documentation à produire`.

Each dispatch gets the validated choices and the paths, not the previous report. A gap redispatch (Step 4b) goes to the sub-phase that owns it: KB → 3a, missing screen or route → 3b, then 3c again.

- **`## Installation nécessaire`** → dispatch `hosa-infra` (Mode 2) with it, then redispatch `hosa-ux-designer` (Phase 3) once confirmed.

## Step 4b: Completeness Gate

Run the checker yourself, from the managed project's root:

```bash
<hosa> interface_check .hosa/kb
<hosa> lexique_check .hosa/kb .
```

The loop is bounded by code: `task done interface 3c` runs these same checkers (control `interface` of `pipeline.json`). Refused → its exact lines go to the sub-phase that owns each one (KB → 3a, screen or route → 3b), then 3c again: `task add` the sub-phases, `task done` each, then `task done interface 3c` again. The control also reads the line 3c writes under `## Vérification` of `kb/interface/navigation.md`: a failed build or a route that doesn't render is a gap of the same round, counted like the others. Past 2 refusals of one cause the task is `bloqué`: stop, show the user what each round tried, a third round only on their word (`task add … --force`).

A gap on an exigence's missing `espace` isn't the designer's to fix, and the control leaves it out: `back interface fondamentaux --detail "espace manquant : <exigences>"`, then propose `fondamentaux`, where `hosa-product-owner` sets it with the user; `back` names the exigences in the plan, and `done fondamentaux` refuses while one lacks its `espace` or is still signed (it goes back to `draft` without `verified`); `relecture` and `contestation` then run again on them, and `done contestation` waits for the user's signature, then come back (`back` refused → a second round already: show the user the exigences still without `espace` and let them decide).

Then dispatch a **fresh** `hosa-ux-designer` in **Review** mode, with only the screenshot paths from `## Vérification`, the identity, the design rules and each persona's main tasks — not the Phase 3 report: the review stays independent. Write its verdict as one line under `## Revue visuelle` of `kb/interface/navigation.md` (create the section, append, never rewrite older lines): `- <date> — note N/10 — <issues, numbered>`; a kept design checked on its own rules → `- <date> — sans note — <issues>`; no screenshots (no Node or Chrome) → `- <date> — sans captures — T-tests à la place`, and say so. Then `task done interface revue --sortie kb/interface/navigation.md`: control `score` refuses a note under 8 → redispatch Phase 3 with the numbered issues, then a fresh review, a new line, and `task done` again; same bound.

Don't move on to documentation with an incomplete or inconsistently named interface — a forbidden synonym in the code, a screen missing from the lexicon: an exigence with no screen, an orphan screen, or a UX fundamental neither done nor justified as not applicable.

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
