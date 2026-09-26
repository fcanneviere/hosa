---
name: interface
description: Use to design and scaffold the interface layer (UX/UI) of the project Hosa manages, consistent with the stable cahier des charges, the personas' needs, and the software architecture already scaffolded by `architecture`. Seventh stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture → interface → backlog).
---

# Interface

Turns the business logic (CDC), what each persona needs to see, and the existing software architecture into a real, scaffolded interface layer in the managed project — plus a visual identity and design rules for the whole project.

## Flow

```
Lit kb/cdc stable, kb/personnas, kb/stack, et la doc
d'architecture (Infra → ## Documentation d'architecture)
        ↓
Si l'une des sources manque, le dit et propose de lancer
l'étape manquante d'abord
        ↓
Pour chaque persona : dispatch hosa-key-user (UI-interview) —
un persona à la fois
        ↓
Propose une identité visuelle → kb/project/ (## Identité
visuelle)
        ↓
Propose des règles de design → Design Rule dans kb/rules/design/
        ↓
Conçoit la couche interface (écrans, composants, navigation)
cohérente avec l'architecture
        ↓
Scaffold l'interface dans le projet cible
        ↓
Rédige la documentation d'interface dans le projet cible
        ↓
Met à jour l'entrée Infra avec le chemin de la doc
        ↓
Propose de lancer `backlog`
```

## Trigger

Manual: `/interface`. Auto: immediately after `architecture`, or "conçois l'interface", "crée l'identité visuelle", "définis l'UX/UI du projet".

---

## Step 1: Gather Inputs

Read `kb/infra/` for the `Infra` entry giving the managed project's root path — the scaffold target is always that path, never `hosa/app` or `hosa/kb`. If there's no `Infra` entry, or no `## Documentation d'architecture` heading recorded on it yet, say so and propose running `architecture` first; don't guess a path or a layer to build on.

Read `kb/cdc/` for `stable` `Exigence`s, `kb/personnas/` for every persona, `kb/stack/` for `Stack Decision`s, and the architecture documentation itself (path from the `Infra` entry). If none of `kb/cdc/`'s `Exigence`s is `stable`, say so and propose running `contestation` first. If `kb/stack/` has no `Stack Decision` yet, say so and propose running `stack` first. If `kb/personnas/` only holds the example persona (no real one), say so and propose sharpening it (via `hosa-key-user`) or running `hosa` first — don't interview a placeholder. If `kb/project/` only holds the example `Project` concept (no real one), say so and propose running `hosa` first, before any persona is interviewed — writing a visual identity into a placeholder happens in Step 3, but knowing there's nowhere to write it is a precondition, not something to discover after N interviews.

## Step 2: Interview Each Persona

For each persona in `kb/personnas/`, dispatch `hosa-key-user` as a UI-interview request: what this persona needs to see, in what order, which information is priority, what usage constraints apply. One persona at a time.

## Step 3: Propose the Visual Identity

Propose a visual identity (color palette, typography, tone) for the project. Once the user validates or adjusts it, write it into `kb/project/`'s existing `Project` concept, under a `## Identité visuelle` heading — if that heading already exists (a re-run), update it in place rather than duplicating it. Log the update to `kb/project/log.md` (create if missing) — OKF §9.

## Step 4: Propose Design Rules

Propose design rules (information density, reusable components, interaction conventions). For each one the user validates or adjusts, write it to `kb/rules/design/<slug>.md` — tagged `ux` to distinguish it from a process/methodology `Design Rule` `hosa-product-owner` might record in the same bundle. If a file already exists at that slug, update it in place rather than creating a duplicate.

```markdown
---
type: Design Rule
title: <titre court>
description: <résumé une ligne>
tags: [ux]
status: stable
generated: { by: human:<user>, at: <ISO8601> }
---
## Règle
<contenu>

## Justification
<pourquoi>
```

Log each one to `kb/rules/design/log.md` (create if missing) — OKF §9.

## Step 5: Design the Interface Layer

Design the screens, components, and navigation that let the business logic (CDC), what each persona needs to see, and the existing software architecture cohere into one usable interface. Say what you chose and why.

## Step 6: Scaffold It

Write the interface layer for real in the managed project: folders, base components, style/theme tokens matching the chosen stack and the visual identity from Step 3. If parts of the interface already exist, extend them rather than duplicating.

## Step 7: Write the Documentation

An interface document in the managed project (e.g. `docs/interface.md`, or wherever the project's existing docs live) — never in `hosa/kb`. Cover the screens/components chosen, their relationship to the architecture, and the visual identity/design rules they follow.

## Step 8: Update the `Infra` Entry

Add the interface documentation's path to the `Infra` entry under its own `## Documentation d'interface` heading — a fixed heading, not a bare line, so a later reader (`backlog`) can tell it apart from the architecture documentation path `architecture` also records there. If that heading already exists (a re-run), update the path in place rather than duplicating the heading. Log the update to `kb/infra/log.md`.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit each.

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

## Structures créées
- `<path>` — [dossier/composant scaffoldé]

## Documentation
- `<path>`

## Suite
Je lance `backlog` maintenant ?
```
