---
name: changement
description: "Use when a stable exigence must change: impact analysis (tickets, data, architecture, interface, docs), back to draft, mini relecture/contestation, follow-up tickets. Triggers: \"cette exigence a changé\", \"le besoin a évolué sur…\"."
---

# Changement

A `stable` Exigence isn't supposed to move casually — `contestation` already vetted it and tickets, data structures, architecture, and screens may already be built against it. This skill is what makes changing one deliberate instead of a silent edit: know what breaks before you break it.

## Flow

```
Identifie l'Exigence stable concernée + la nature du changement
        ↓ pas stable → dis-le, c'est une simple redaction/relecture, stoppe
Impact : tickets liés (kb/tickets/) à tout état
        ↓ pour chaque ticket déjà construit (state != todo)
Dispatch hosa-data-engineer / hosa-architect / hosa-ux-designer /
hosa-documentation, scope = uniquement cette Exigence — chacun
répond si et comment sa couche est touchée
        ↓
Présente l'impact à l'utilisateur, confirme qu'on procède
        ↓
Repasse l'Exigence en status: draft, ajoute ## Changement
(quoi, pourquoi, par qui)
        ↓
Mini boucle : relecture (scope auto = cette Exigence, vient
d'être modifiée) → contestation (Passe 1+2 scopées à cette
Exigence + personas/tickets liés, pas tout le CDC)
        ↓ anomalie → reboucle
        ↓ propre → confirmation finale utilisateur → PO repasse
status: stable + verified: human:<user>
Dispatch hosa-product-owner : crée un Ticket par impact confirmé
(rework data/architecture/interface/doc)
        ↓
Log kb/cdc/log.md, kb/tickets/log.md
```

## Trigger

Manual: `/changement <slug-exigence>`. Auto: "cette exigence a changé", "il faut modifier X (déjà stable)", "le besoin a évolué sur..." — when the target Exigence is `stable`. A `draft` Exigence just needs `redaction`/`relecture` directly, not this skill.

---

## Step 1: Identify and Check Preconditions

Read `kb/cdc/<slug>.md`. If `status` isn't `stable`, say so and redirect to `redaction`/`relecture` — those already handle a `draft` Exigence, this skill exists specifically for the higher cost of changing a vetted one. Ask the user, in their own words, what's changing and why — don't infer it from a diff, the *why* is what the mini contestation pass will need.

## Step 2: Impact — Backlog

Read every `Ticket` in `kb/tickets/` with a markdown link back to this Exigence, at any `state`. List them, split `state: todo` (nothing built yet, no further impact analysis needed — it'll just be re-derived) from `doing`/`done`/`blocked` (something may already exist against the old wording).

## Step 3: Impact — What's Already Built

First, for each of those tickets, run the project graph (command line under `## Project graph` in your context): `graph.py ticket <slug>` for its files and symbols, then `graph.py affected <file-or-symbol>` on each. Hand that output to every agent dispatched below as its starting point — they read those files, not the whole tree.

For each ticket from Step 2 that isn't `state: todo`, dispatch the agent(s) whose layer that ticket actually touched (read its `Note technique`/`Placement architecture`/`Placement interface` sections to know which):
- `hosa-data-engineer` — does the change alter what data is needed, its origin, or its shape? Scope it to this Exigence and the entities it already derived from it.
- `hosa-architect` — does the change move a module boundary or invalidate an assumption the architecture made?
- `hosa-ux-designer` — does the change alter a screen/flow already scaffolded?
- `hosa-documentation` — which docs reference this Exigence or the entities/screens above and would need a refresh?

Each returns whether it's impacted and how, in its normal Output format — no agent writes anything yet at this step, this is read-only impact reporting.

## Step 4: Confirm With the User

Present the full impact (tickets, data, architecture, interface, docs) before touching anything. If the impact is large enough that the user wants to reconsider the change itself, stop here — nothing has been modified yet.

## Step 5: Revert to Draft

Rewrite `kb/cdc/<slug>.md`: `status: draft`, append (don't replace the existing body):

```markdown
## Changement (<date>)
Quoi : <ce qui change>
Pourquoi : <raison>
Demandé par : <human:user ou origine>
Impact identifié : tickets [liste], data/architecture/interface/doc [résumé Step 3]
```

Then edit the affected sections of the Exigence body itself with the new content — same six-section structure `redaction` uses.

## Step 6: Mini Relecture/Contestation Loop

Invoke `relecture` — its own Step 1 already scopes to "exigences modifiées dans cette session", which is just this one. Then invoke `contestation`, but scope both passes to this Exigence plus the personas/tickets found in Step 2 — not the whole `kb/cdc/`, that's what makes this loop "mini" rather than a full pipeline re-run. Anomaly in either pass → back to Step 5. Clean on both → ask the user for final sign-off, same as `contestation`'s own last step; on yes, dispatch `hosa-product-owner` to set `status: stable` + `verified: { by: human:<user>, at: <ISO8601> }`.

## Step 7: Follow-Up Tickets

Dispatch `hosa-product-owner` to create one `Ticket` per confirmed impact from Step 3 (`state: todo`, tagged `changement`, linked to the Exigence and to whichever ticket/entity/screen/doc it reworks) — don't leave a confirmed impact as only a line in this session's report. Then run `backlog`'s Single-Ticket Mode on each, so they're complete before you report them.

## Step 8: Log

Confirm `kb/cdc/log.md` was updated for the Exigence rewrite and re-stabilization, and `kb/tickets/log.md` for the follow-up tickets — per each dispatched agent's own logging.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa` Core Rules, "Git checkpoints".

## Output

```
## Exigence modifiée
`kb/cdc/<slug>.md` — <titre> (stable → draft → stable une fois la boucle propre)

## Impact
- Tickets : [liste, avec state]
- Data / Architecture / Interface / Documentation : [résumé Step 3, ou "Rien de construit encore — impact nul"]

## Tickets de suivi créés
- `kb/tickets/<slug>.md` — [ce qu'il rattrape]
[Si aucun : "Aucun — rien n'était encore construit contre cette Exigence"]

## Suite
**Q1 — Je lance `sprint` pour prioriser ces tickets de rattrapage ?**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
```
