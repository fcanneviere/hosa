---
name: backlog
description: Use to turn every stable cahier des charges Exigence without a ticket yet into a Ticket enriched with a user story and Given/When/Then acceptance criteria (PO), a technical feasibility note (senior dev), an architecture placement note (architect), and an interface placement note (UX/UI designer). Eighth stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture → interface → backlog).
---

# Backlog

Turns "what the application must do" (the stable cahier des charges) into Product Backlog tickets — each one carrying the business story, its technical feasibility, where it lands in the architecture, and where it lands in the interface, so nothing enters `kb/tickets/` disconnected from the technical reality already decided by `stack`, `architecture`, and `interface`.

## Flow

```
Pour chaque Exigence stable de kb/cdc/ sans Ticket lié :
        ↓
Écrit la story et les critères d'acceptation Given/When/
Then (rôle PO) dans un nouveau Ticket, state: todo
        ↓
Ajoute une note technique (rôle senior dev), ou une ligne
"pas encore évalué" si aucune Stack Decision n'existe
        ↓
Ajoute un placement architecture (rôle architecte), ou une
ligne "pas encore déterminé" si aucune doc d'architecture
n'existe
        ↓
Ajoute un placement interface (rôle UX/UI designer), ou une
ligne "pas encore déterminé" si aucune doc d'interface n'existe
        ↓
Log kb/tickets/log.md
        ↓
Propose de lancer sprint
```

## Trigger

Manual: `/backlog`. Auto: immediately after `interface`, or "crée le product backlog", "génère les tickets à partir du cahier des charges".

---

## Step 1: Scope

Read every `stable` `Exigence` in `kb/cdc/`. For each one, check every existing `Ticket` in `kb/tickets/` for a markdown link pointing back to that `Exigence`'s file — if one already links to it, skip it; a re-run of `backlog` only fills gaps, it never recreates or overwrites a ticket. If every `stable` `Exigence` already has a linked ticket (or there are no `stable` `Exigence`s at all), say so and stop — nothing to write.

## Step 2: Write the Story (PO role)

For each `Exigence` left after Step 1, write a new `Ticket` to `kb/tickets/<slug>.md`, `state: todo`:

```markdown
---
type: Ticket
title: <titre>
description: <description courte>
tags: []
state: todo
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
En tant que [persona],
je veux [besoin],
afin de [valeur].

Lié à : [persona](../personnas/xxx.md), [exigence](../cdc/xxx.md)
```

If the `Exigence` names no clear persona, ask the user which persona it serves before writing the story — same "no guessing" discipline as every other Hosa skill.

Then append acceptance criteria derived from the `Exigence`'s own text — at least one scenario, more if the `Exigence` describes distinct cases (happy path, error case, edge case):

```markdown
## Critères d'acceptation
- Étant donné [contexte], quand [action], alors [résultat attendu]
```

**Vertical slices.** A ticket delivers something a persona can actually exercise end to end — a thin path through every layer it needs (data, logic, interface), not one layer of many features ("toutes les tables", "toute l'API"). An `Exigence` too big for one such slice becomes several tickets, the first one the thinnest path that works (the tracer bullet), the next ones widening it.

**Blocking edges.** Once every ticket of this run is written, add to each ticket that can't start before another one is `done`:

```markdown
## Bloqué par
- [<titre>](<slug>.md) — <ce qu'il attend de lui>
```

Only a real dependency (needs its data, its screen, its endpoint) — never "plus logique après". No such section = can start anytime. A cycle between tickets means the split is wrong: re-slice rather than write it.

If the `Exigence` doesn't say enough to derive a concrete scenario, ask the user rather than inventing one. These criteria are what `qa-plan` grounds its technical test cases in, and what `recette`/`validation` check the delivered ticket against — never leave a ticket without at least one.

## Step 3: Add the Technical Note (senior dev role)

Read `kb/stack/` for `Stack Decision` concepts. If at least one exists, append to the ticket just written:

```markdown
## Note technique (senior dev)
[Faisabilité/complexité au regard de la stack retenue, et pourquoi]
```

If `kb/stack/` has no `Stack Decision` yet (this skill invoked standalone, before `stack` ran), append instead:

```markdown
## Note technique (senior dev)
Stack pas encore choisie — faisabilité non évaluée.
```

Never block ticket creation on a missing `Stack Decision`.

## Step 4: Add the Architecture Placement (architect role)

Read `kb/infra/` for the `Infra` entry's `## Documentation d'architecture` heading (written by `architecture`) — that heading, specifically, not the data dictionary or migrations paths `schema-app`/`schema-db` also record in the same `Infra` entry. If it's there, read the documentation it points to and append to the ticket:

```markdown
## Placement architecture (architecte)
[Module/couche concerné, et pourquoi]
```

If no architecture documentation path is recorded yet (this skill invoked standalone, before `architecture` ran), append instead:

```markdown
## Placement architecture (architecte)
Architecture pas encore scaffoldée — placement non déterminé.
```

Never block ticket creation on a missing architecture doc.

## Step 5: Add the Interface Placement (UX/UI designer role)

Read `kb/infra/` for the `Infra` entry's `## Documentation d'interface` heading (written by `interface`) — that heading, specifically, not the architecture doc, the data dictionary, or the migrations paths the same `Infra` entry may also record. If it's there, read the documentation it points to and append to the ticket:

```markdown
## Placement interface (UX/UI)
[Écran/composant concerné et pourquoi]
```

If no interface documentation path is recorded yet (this skill invoked standalone, before `interface` ran), append instead:

```markdown
## Placement interface (UX/UI)
Interface pas encore scaffoldée — placement non déterminé.
```

Never block ticket creation on a missing interface doc.

## Step 6: Priority and Estimate

Once every ticket for this run is written, ask the user once: "Dans quel ordre je priorise ces N tickets ? (numéros, ou 'pas encore' pour laisser sans priorité)". If given, write `priority: <rang>` (1 = le plus urgent) into each ticket's frontmatter in that order; tickets left unprioritized keep no `priority` field rather than an invented one — `sprint` treats those as lowest priority, after every explicitly ranked ticket. Then set each ticket's `estimate` yourself, in the senior dev role: `1` (small, ≤ ½ day), `2` (medium, ≈ 1 day) or `3` (large, 2-3 days) points, from the technical note of Step 3 — the complexity estimate is the senior dev's call, not the user's. A ticket whose note still says "Stack pas encore choisie" gets no `estimate` rather than a guess; anything larger than 3 is a sign the ticket should be split into vertical slices (Step 2) — say so in the report.

## Step 7: Log

Log each ticket created (and its `priority`/`estimate` once set) to `kb/tickets/log.md` (create if missing) — chronological, most recent date first, per OKF §9.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa` Core Rules, "Git checkpoints".

## Output

```
## Tickets créés
- `kb/tickets/<slug>.md` — [titre] (state: todo)

## Suite
Je lance `sprint` maintenant ?
```
