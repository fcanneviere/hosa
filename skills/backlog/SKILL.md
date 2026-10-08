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
Ajoute une note sécurité (rôle expert cybersécurité), ou une
ligne "pas encore faite" si aucune analyse de sécurité n'existe
        ↓
Log kb/tickets/log.md
        ↓
Propose de lancer sprint
```

## Trigger

Manual: `/backlog`. Auto: immediately after `interface`, or "crée le product backlog", "génère les tickets à partir du cahier des charges".

Single-ticket mode: `/backlog <slug-ticket>`, or chained by any skill that just created a `Ticket` — see **Single-Ticket Mode** below. A ticket is born complete: no skill reports a new ticket before this mode has run on it.

## Ticket complet

A ticket is ready to be planned (`sprint`) and executed (`develop`, `qa-plan`) when it has all of:
- a story (`En tant que … je veux … afin de …`) and a `Lié à :` line — to its `Exigence`, or, for a ticket born outside the cahier des charges (bug, recette gap, audit finding, change impact, sprint follow-up), to the concept that surfaced it;
- `## Critères d'acceptation` with at least one Given/When/Then scenario;
- real `## Note technique (senior dev)`, `## Placement architecture (architecte)`, `## Placement interface (UX/UI)` and `## Note sécurité (expert cybersécurité)` notes — not the fallback lines below;
- a `priority`, unless the user explicitly answered "pas encore".

The checker is the source of truth — run it from the managed project's root, with any Python 3.9+:

```bash
<python> "${CLAUDE_PLUGIN_ROOT}/skills/backlog/scripts/ticket_check.py" .hosa/kb [.hosa/kb/tickets/<slug>.md ...]
```

No ticket given → every `state: todo` ticket. Exit `0` = all complete, `1` = gaps listed per ticket.

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

Read `kb/infra/` for the `Infra` entry's `## Documentation d'interface` heading (written by `interface`) — that heading, specifically, not the architecture doc, the data dictionary, or the migrations paths the same `Infra` entry may also record. If it's there, read the documentation it points to and `kb/interface/navigation.md`, and append to the ticket:

```markdown
## Placement interface (UX/UI)
[Écran(s) du plan de navigation, avec leur route, composant(s) concerné(s), et pourquoi — un écran absent du plan est à ajouter via `interface`, pas à inventer ici]
```

If no interface documentation path is recorded yet (this skill invoked standalone, before `interface` ran), append instead:

```markdown
## Placement interface (UX/UI)
Interface pas encore scaffoldée — placement non déterminé.
```

Never block ticket creation on a missing interface doc.

## Step 5b: Add the Security Note (cybersecurity expert role)

Read `kb/cdc/securite.md`, the `Security Rule`s in `kb/rules/security/`, and the linked `Exigence`'s `## Contraintes de sécurité` and security exigences. If the analysis exists, append the constraints this ticket must meet — so they're built in, not retrofitted:

```markdown
## Note sécurité (expert cybersécurité)
[Contraintes applicables à ce ticket — données sensibles touchées, contrôle d'accès attendu, journalisation, règles `kb/rules/security/` concernées — ou "Aucune contrainte propre à ce ticket — règles générales de `kb/rules/security/` applicables." quand c'est le cas]
```

If `kb/cdc/securite.md` doesn't exist yet (`securite` never ran), append instead:

```markdown
## Note sécurité (expert cybersécurité)
Analyse de sécurité pas encore faite — contraintes non déterminées.
```

Never block ticket creation on a missing analysis.

## Step 6: Priority and Estimate

Once every ticket for this run is written, ask the user once: "Dans quel ordre je priorise ces N tickets ? (numéros, ou 'pas encore' pour laisser sans priorité)". If given, write `priority: <rang>` (1 = le plus urgent) into each ticket's frontmatter in that order; tickets left unprioritized keep no `priority` field rather than an invented one — `sprint` treats those as lowest priority, after every explicitly ranked ticket. Then ask, per ticket, for a rough `estimate` (S/M/L or points) using the technical note from Step 3 as basis — "pas encore" is a valid answer and leaves the field absent; never invent one to fill the frontmatter.

## Step 7: Log and Check

Log each ticket created (and its `priority`/`estimate` once set) to `kb/tickets/log.md` (create if missing) — chronological, most recent date first, per OKF §9. Then run the checker (see **Ticket complet**) on the tickets just written and report any gap it lists.

## Single-Ticket Mode

Run on one existing `Ticket` — created by `hosa-product-owner` from `qa`, `recette`, `debug`, `qualite`, `changement`, `bilan-sprint`, by the `hosa` free-form flow, or by hand. Fills only what's missing; never rewrites a section that already holds a real note.

1. Run the checker on the ticket. Already complete → say so and stop.
2. Story, `Lié à :` or `## Critères d'acceptation` missing → dispatch `hosa-product-owner` (Responsibility 4) to add them, with the concept that surfaced the ticket. It returns an Open Question instead of guessing a persona or a scenario — ask the user and redispatch.
3. Each of the four notes missing or still on its fallback line → write it as in Steps 3-5b. If the stage it depends on still hasn't run (no `Stack Decision`, no architecture or interface doc, no security analysis), keep the fallback line and say which stage is missing — that's the only case where a ticket legitimately stays incomplete.
4. No `priority` → ask the user where it goes in the current backlog ("avant/après quel ticket ?", or "pas encore"). Given a rank, write it and shift every other `todo` ticket at that rank or below by one, so ranks stay unique. Then ask for an `estimate`, same rules as Step 6.
5. If the ticket was created during an `active` sprint, ask whether it joins that sprint now or waits for the next one; only write `sprint: <slug>` (and add it to the sprint's `## Tickets`) on an explicit yes — `sprint`'s readiness guard is what this mode just satisfied. Then run `qa-plan` for it: a ticket joins a sprint with its tests, like every other.
6. Log every change to `kb/tickets/log.md` (and `kb/sprints/log.md` if Step 5 added it), then rerun the checker and report its line for this ticket.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit.

## Output

```
## Tickets créés
- `kb/tickets/<slug>.md` — [titre] (state: todo) — [ligne du checker : complet / ce qui manque]

## Suite
Je lance `sprint` maintenant ?
```
