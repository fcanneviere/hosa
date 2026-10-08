---
name: interface
description: "Use to design and scaffold a complete, navigable interface: style cards, layout directions and pages on comparison pages, front/back office navigation, lexicon, UX fundamentals, screenshot-verified scaffold with an independent review; also completes an existing one. Structuration stage 7. Triggers: \"conçois l'interface\", \"la navigation manque\"."
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
Redispatch hosa-ux-designer (Phase 2), trois manches :
styles (cartes de style) → directions (navigation, lexique,
2–3 mises en page) → page (pages complètes front/back)
        ↓ chaque manche : page de comparaison → l'utilisateur choisit
        ↓
Redispatch hosa-ux-designer (Phase 3) avec les choix validés
→ plan de navigation, fondamentaux UX, scaffold navigable,
vérification (build, routes, interface_check, captures)
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

## Step 3: Dispatch for Proposals, Round by Round

Redispatch `hosa-ux-designer` (Phase 2) three times, with every persona's needs from Step 2 and the user's previous choice. Each round returns a comparison page (`## Pages de comparaison`): give the user its path as a link (`file://<absolute path>`) and tell them to open it in a browser. Ask the choice as one numbered question, the options lettered as on the page. Mixing two options or asking for a change is an answer too.

1. **`round: styles`** — 4–6 style cards: the visual identity and the design rules each implies. The user picks one.
2. **`round: directions`** — the navigation structure, the lexicon and 2–3 layout directions of the main screen in that style. The navigation is the part the user will live with every day: show it as a readable tree per role, not a paragraph. Show the lexicon as its table — each term with what it names and the synonyms it rules out — so the user fixes the words now, not screen by screen later. The user validates each item and picks a direction.
3. **`round: page`** — one complete page per space in that direction. The user validates it, or asks for changes (redispatch the same round).

After each answer: `avancement.py … progress interface --detail "manche <round> choisie" --reprise "interface, manche <suivante>"`. The comparison pages are working files under `<root>/.hosa/design/`, ignored by git; what is chosen goes into the KB in Phase 3. An existing interface whose identity the user keeps → skip `styles`.

## Step 4: Dispatch to Record and Design

Redispatch `hosa-ux-designer` (Phase 3) with the user's validated choices. It writes the visual identity to `kb/project/` and each design rule to `kb/rules/design/`, writes `kb/interface/navigation.md`, applies the UX fundamentals, scaffolds a navigable interface, verifies it, and returns a `## Documentation à produire` field.

- **`## Installation nécessaire`** → dispatch `hosa-infra` (Mode 2) with it, then redispatch `hosa-ux-designer` (Phase 3) once confirmed.

## Step 4b: Completeness Gate

Run the checker yourself, from the managed project's root:

```bash
<python> "${CLAUDE_PLUGIN_ROOT}/skills/interface/scripts/interface_check.py" .hosa/kb
<python> "${CLAUDE_PLUGIN_ROOT}/skills/interface/scripts/lexique_check.py" .hosa/kb .
```

Exit `1`, or a `## Vérification` reporting a failed build or routes that don't render → redispatch `hosa-ux-designer` (Phase 3) with the exact gaps, and repeat. A gap on an exigence's missing `espace` isn't the designer's to fix: propose `fondamentaux`, where `hosa-product-owner` sets it with the user, then come back. After two rounds that still leave gaps, stop and show the user what's left rather than looping. Then dispatch a **fresh** `hosa-ux-designer` in **Review** mode, with only the screenshot paths from `## Vérification`, the identity, the design rules and each persona's main tasks — not the Phase 3 report: the review stays independent. A score under 8, or any issue that blocks a task, → redispatch Phase 3 with the numbered issues, then review again. After two review rounds, show the user the score and the remaining issues, and let them decide. No screenshots (no Node or Chrome) → the T-tests replace the review; say so.

Don't move on to documentation with an incomplete or inconsistently named interface — a forbidden synonym in the code, a screen missing from the lexicon: an exigence with no screen, an orphan screen, or a UX fundamental neither done nor justified as not applicable.

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

## Revue visuelle
- Note : [N/10] — [problèmes restants, ou "aucun"] — captures : `<dossier>`

## Documentation
- `<path>`

## Open Questions
[Si rien : "None"]

## Suite
**Q1 — Je lance `backlog` maintenant ?**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
```
