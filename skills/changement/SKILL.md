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
        ↓ anomalie → `back changement changement --objet <slug>`
          (2 tours par cause, puis l'utilisateur décide) → reboucle
        ↓ propre → confirmation finale utilisateur → PO repasse
status: stable + verified: human:<user> → `done changement --objet <slug>`
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

Read every `Ticket` in `kb/tickets/` with a markdown link back to this Exigence, at any `state`. List them, split `state: todo` (nothing built yet: no impact analysis, but their story and criteria still carry the old wording — Step 7 rewrites them; `backlog` never does, it skips an exigence that already has tickets) from `doing`/`done`/`blocked` (something may already exist against the old wording).

A ticket `doing` in the `active` sprint → one numbered question, asked with Step 4: a) fix it in this sprint once the loop is clean — `develop <ticket> correction` with the new wording as the defect (recommended: it isn't merged yet); b) finish it on the old wording, and a follow-up ticket (Step 7) reworks it.

## Step 3: Impact — What's Already Built

First, for each of those tickets, run the project graph (command line under `## Project graph` in your context): `graph.py ticket <slug>` for its files and symbols, then `graph.py affected <file-or-symbol>` on each. Hand that output to every agent dispatched below as its starting point — they read those files, not the whole tree.

For each ticket from Step 2 that isn't `state: todo`, dispatch the agent(s) whose layer that ticket actually touched (read its `Note technique`/`Placement architecture`/`Placement interface` sections to know which):
- `hosa-data-engineer` — does the change alter what data is needed, its origin, or its shape? Scope it to this Exigence and the entities it already derived from it.
- `hosa-architect` — does the change move a module boundary or invalidate an assumption the architecture made?
- `hosa-ux-designer` — does the change alter a screen/flow already scaffolded?
- `hosa-documentation` — which docs reference this Exigence or the entities/screens above and would need a refresh?

Each returns whether it's impacted and how, in its normal Output format — no agent writes anything yet at this step, this is read-only impact reporting.

**Feasibility first.** The new wording relies on a platform capability (notifications, Web Push, camera, offline, background work, a browser or OS API) → dispatch `hosa-senior-dev` (Verification mode) on the platforms the CDC imposes, even when no ticket is built yet. A capability a platform lacks goes into Step 4 before anything is rewritten — relecture and contestation check the wording, not whether it can run (pilot2: two rounds refined a rule that doesn't work on iPhone).

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

Then edit the affected sections of the Exigence body itself with the new content — same structure `redaction` uses, frontmatter (`priorite`, `lot`, `objectifs`) included when the change moves them. Add the decision to `kb/cdc/decisions.md` § Décisions (date, who, what, why), and update `kb/cdc/modele-metier.md` when the change adds or moves a state, a right or a notification. The mini relecture regenerates `kb/project/cahier-des-charges.md`.

## Step 6: Mini Relecture/Contestation Loop

Invoke `relecture` with its scope given explicitly: this Exigence's path (it is back to `draft`, Step 5). Then invoke `contestation`. Neither calls `avancement.py` for its own stage inside this loop (`start`, `done`, or `back` from `relecture`/`contestation`): their stages are done, and a `start` would reopen them and move the resume point off the stage in progress. Scope both passes to this Exigence plus the personas/tickets found in Step 2 — not the whole `kb/cdc/`, that's what makes this loop "mini" rather than a full pipeline re-run.

The loop is `changement`'s own, declared in `pipeline.json` and counted by the plan:

- **Its exit is a checker.** A round is clean when `<hosa> cdc revue "<root>/.hosa/kb"` exits 0 (no `bloquante` still `ouverte`) and `contestation`'s challenger returns no `bloquante` on the scope.
- **A round that isn't clean** → `avancement.py back changement changement --objet <slug> --detail "<the open anomalies, one per line: A<n> — what is wrong>"` (`--cause <A<n>>` when the same anomaly comes back), then Step 5 with those exact lines — never a summary of them. The round and its gaps survive a `/clear`.
- **The bound is the script's.** `back` refuses (exit 1) past 2 rounds of one cause: stop, show the user what each round tried and what still fails, and ask whether to run one more round (`--force`, on their word only) or keep the old wording.
- **Clean** → ask the user for final sign-off, same as `contestation`'s own last step; on yes, dispatch `hosa-product-owner` to set `status: stable` + `verified: { by: human:<user>, at: <ISO8601> }`, then `avancement.py done changement --objet <slug>`: it refuses while the Exigence isn't `stable` and signed, or `cdc revue` still finds an open `bloquante`.

## Step 7: Follow-Up Tickets

Dispatch `hosa-product-owner` to create one `Ticket` per confirmed impact from Step 3 (`state: todo`, tagged `changement`, linked to the Exigence and to whichever ticket/entity/screen/doc it reworks) — don't leave a confirmed impact as only a line in this session's report. Then run `backlog`'s Single-Ticket Mode on each, so they're complete before you report them.

**The `todo` tickets of Step 2** carry the old wording: in the same dispatch, `hosa-product-owner` rewrites their story and criteria to the new one (Responsibility 2, « A changed exigence »). Then dispatch together `hosa-security` (Mode 5) and `hosa-legal` (Mode 3, notes de tickets), `model: sonnet`, on those tickets only, each told to update its existing note and the criteria it linked (`→ CAn`), never to add a second note. Then run `<hosa> ticket_check .hosa/kb <their paths>` and `<hosa> ticket_check .hosa/kb --regles`: a gap goes back to the agent that owns it, with its exact lines.

## Step 8: Log

Confirm `kb/cdc/log.md` was updated for the Exigence rewrite and re-stabilization, and `kb/tickets/log.md` for the follow-up tickets — per each dispatched agent's own logging.

## Commits

You don't commit yourself. End by dispatching `hosa-git` (Mode 3, `model: haiku`) with the files written and a one-line summary — `using-hosa`, "Git checkpoints". Never a question.

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
