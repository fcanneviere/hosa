---
name: interface
description: Use to design and scaffold the interface layer (UX/UI) of the project Hosa manages, consistent with the stable cahier des charges, the personas' needs, and the software architecture already scaffolded by `architecture`. Seventh stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture → interface → backlog).
---

# Interface

Turns the business logic (CDC), what each persona needs to see, and the existing software architecture into a real, scaffolded interface layer in the managed project — plus a visual identity and design rules for the whole project. This skill is the only one that talks to the user or dispatches other agents — the actual interview, proposal, design, and scaffold is `hosa-ux-designer`'s.

## Flow

```
Dispatch hosa-ux-designer (Phase 1: gather inputs, identify
personas to interview)
        ↓ Open Questions (missing Infra/CDC/stack/personas/project) → relay to user, stop
        ↓ Personas à interviewer
Dispatch hosa-key-user (UI-interview) pour chaque persona,
un à la fois
        ↓
Redispatch hosa-ux-designer (Phase 2) avec les besoins
surfacés → propose identité visuelle + règles de design
        ↓
Présente les propositions à l'utilisateur → il valide/ajuste
        ↓
Redispatch hosa-ux-designer (Phase 3) avec les choix validés
→ enregistre, conçoit et scaffold la couche interface
        ↓
Dispatch hosa-documentation (Mode 1) avec le
"Documentation à produire" retourné
        ↓
Met à jour l'entrée Infra avec le chemin confirmé
        ↓
Propose de lancer `backlog`
```

## Trigger

Manual: `/interface`. Auto: immediately after `architecture`, or "conçois l'interface", "crée l'identité visuelle", "définis l'UX/UI du projet".

---

## Step 1: Dispatch for Inputs and Personas

Dispatch `hosa-ux-designer` (Phase 1, `agents/ux-designer.md`) to gather `kb/infra/`, `kb/cdc/`, `kb/personnas/`, `kb/stack/`, and the architecture documentation, and to list every real persona needing a UI-interview.

If it returns an Open Question (no `Infra`/architecture doc, no `stable` `Exigence`, no `Stack Decision`, only the example persona or `Project`) — relay it to the user, propose the missing stage (`architecture`, `contestation`, `stack`, `hosa`), and only redispatch once resolved.

## Step 2: Interview Each Persona

For each persona under `## Personas à interviewer`, dispatch `hosa-key-user` as a UI-interview request: what this persona needs to see, in what order, which information is priority, what usage constraints apply (mobile, accessibility, autonomy...). One persona at a time — don't batch multiple personas into a single dispatch.

## Step 3: Dispatch for Proposals

Redispatch `hosa-ux-designer` (Phase 2) with every persona's needs surfaced in Step 2. It returns a proposed visual identity and design rules — present them to the user and wait for their validation or adjustments per item.

## Step 4: Dispatch to Record and Design

Redispatch `hosa-ux-designer` (Phase 3) with the user's validated choices. It writes the visual identity to `kb/project/` and each design rule to `kb/rules/design/`, then designs and scaffolds the interface layer, and returns a `## Documentation à produire` field.

## Step 5: Dispatch Documentation

Dispatch `hosa-documentation` (Mode 1) with what `hosa-ux-designer` returned under `## Documentation à produire` — it writes the interface documentation into the managed project. Wait for its confirmation and the path it wrote to.

## Step 6: Update the `Infra` Entry

Add the confirmed interface documentation path to the `Infra` entry under its own `## Documentation d'interface` heading — a fixed heading, not a bare line, so a later reader (`backlog`) can tell it apart from the architecture documentation path `architecture` also records there. If that heading already exists (a re-run), update the path in place rather than duplicating the heading. Log the update to `kb/infra/log.md`.

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

## Open Questions
[Si rien : "None"]

## Suite
Je lance `backlog` maintenant ?
```
