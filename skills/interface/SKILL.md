---
name: interface
description: Use to design and scaffold a complete, working and usable interface layer (UX/UI) for the project Hosa manages — screen inventory and navigation per role covering every stable Exigence (basic functions included), UX fundamentals (states, forms, lists, errors, accessibility, responsive…), a verified navigable scaffold — consistent with the stable cahier des charges, the personas' needs, and the software architecture already scaffolded by `architecture`. Also completes an interface scaffolded earlier. Seventh stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture → interface → backlog).
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
surfacés → propose identité visuelle + règles de design +
structure de navigation par rôle
        ↓
Présente les propositions à l'utilisateur → il valide/ajuste
        ↓
Redispatch hosa-ux-designer (Phase 3) avec les choix validés
→ plan de navigation, fondamentaux UX, scaffold navigable,
vérification (build, routes, interface_check)
        ↓ Installation nécessaire → hosa-infra, redispatch
        ↓ manques → redispatch avec la liste, jusqu'à complet
        ↓
Dispatch hosa-documentation (Mode 1) avec le
"Documentation à produire" retourné
        ↓
Met à jour l'entrée Infra avec le chemin confirmé
        ↓
Propose de lancer `backlog`
```

## Trigger

Manual: `/interface`. Auto: immediately after `architecture`, or "conçois l'interface", "crée l'identité visuelle", "définis l'UX/UI du projet", "complète l'interface", "la navigation manque", "l'interface n'est pas utilisable".

---

## Completing an Existing Interface

If the interface was already scaffolded (an `Infra` `## Documentation d'interface` heading exists) but `interface_check.py` reports gaps — no `kb/interface/navigation.md`, screens missing, fundamentals not applied — run this same flow as a completion: Step 1 as usual; skip Step 2 and the identity/design-rule part of Step 3 when `## Identité visuelle` and `ux` `Design Rule`s already exist (unless the user wants to revisit them), but always present the navigation structure for validation; then Steps 4 to 6, extending the existing scaffold rather than replacing it.

## Step 1: Dispatch for Inputs and Personas

Dispatch `hosa-ux-designer` (Phase 1, `agents/ux-designer.md`) to gather `kb/infra/`, `kb/cdc/`, `kb/personnas/`, `kb/stack/`, and the architecture documentation, and to list every real persona needing a UI-interview.

If it returns an Open Question (no `Infra`/architecture doc, no `stable` `Exigence`, no `Stack Decision`, only the example persona or `Project`) — relay it to the user, propose the missing stage (`architecture`, `contestation`, `stack`, `hosa`), and only redispatch once resolved.

## Step 2: Interview Each Persona

For each persona under `## Personas à interviewer`, dispatch `hosa-key-user` as a UI-interview request: what this persona needs to see, in what order, which information is priority, what usage constraints apply (mobile, accessibility, autonomy...). One persona at a time — don't batch multiple personas into a single dispatch.

## Step 3: Dispatch for Proposals

Redispatch `hosa-ux-designer` (Phase 2) with every persona's needs surfaced in Step 2. It returns a proposed visual identity, design rules, and the navigation structure (screens per role, each role's home screen and main menu, every functional `stable` `Exigence` placed on a screen) — present all three to the user and wait for their validation or adjustments per item. The navigation is the part the user will live with every day: show it as a readable tree per role, not a paragraph. Show the lexicon as its table — each term with what it names and the synonyms it rules out — so the user fixes the words now, not screen by screen later.

## Step 4: Dispatch to Record and Design

Redispatch `hosa-ux-designer` (Phase 3) with the user's validated choices. It writes the visual identity to `kb/project/` and each design rule to `kb/rules/design/`, writes `kb/interface/navigation.md`, applies the UX fundamentals, scaffolds a navigable interface, verifies it, and returns a `## Documentation à produire` field.

- **`## Installation nécessaire`** → dispatch `hosa-infra` (Mode 2) with it, then redispatch `hosa-ux-designer` (Phase 3) once confirmed.

## Step 4b: Completeness Gate

Run the checker yourself, from the managed project's root:

```bash
<python> "${CLAUDE_PLUGIN_ROOT}/skills/interface/scripts/interface_check.py" .hosa/kb
<python> "${CLAUDE_PLUGIN_ROOT}/skills/interface/scripts/lexique_check.py" .hosa/kb .
```

Exit `1`, or a `## Vérification` reporting a failed build or routes that don't render → redispatch `hosa-ux-designer` (Phase 3) with the exact gaps, and repeat. A gap on an exigence's missing `espace` isn't the designer's to fix: propose `fondamentaux`, where `hosa-product-owner` sets it with the user, then come back. After two rounds that still leave gaps, stop and show the user what's left rather than looping. Don't move on to documentation with an incomplete or inconsistently named interface — a forbidden synonym in the code, a screen missing from the lexicon: an exigence with no screen, an orphan screen, or a UX fundamental neither done nor justified as not applicable.

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

## Plan de navigation
- `kb/interface/navigation.md` — [N écrans, rôles couverts]

## Structures créées
- `<path>` — [dossier/composant scaffoldé]

## Vérification
- Build : [OK / échec] — routes rendues : [X / Y] — interface_check : [complet / manques]

## Documentation
- `<path>`

## Open Questions
[Si rien : "None"]

## Suite
**Q1 — Je lance `backlog` maintenant ?**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
```
