---
name: backlog
description: "Use to turn every stable Exigence into Product Backlog tickets — vertical slices with `depends_on`, story and criteria (PO), grounded technical, architecture and interface notes, security and legal notes whose abuse cases and legal constraints are criteria; `nfr` exigences become the definition of done; also refines vague `todo` tickets. Structuration stage 9. Triggers: \"crée le product backlog\", after `interface`."
---

# Backlog

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything (Single-Ticket Mode excepted: not a stage, no call): `avancement.py start backlog`; refused → name the missing stage to the user and stop; refused as already done → a re-run only on the user's request: the same `start` with `--rouvre "<their request>"`. Stopped on a user question: `block backlog --detail "<question>"`. Once the stage's output is written and committed: `done backlog`. Never skip these calls: without them a cut session can't resume (« reprends ») and the session stays on the wrong model.

**Tâches.** A lot is **8 tickets at most**, not 8 exigences (rieki: 2 exigences gave 52 tickets, one pass wrote 39 of them up to 273 k tokens of context). `task done stories-<k>` refuses more (`lot`, pipeline.json). An exigence that splits into more: its first pass decides the whole split, writes the first 8 and lists the others under `## Reprise` (slug — scope — `depends_on`, one line each); the next pass is `stories-<k>b` on that list.
A lot is a graph of four tasks, the judge last: `stories-<k>` → `securite-<k>` and `juridique-<k>` → `juge-<k>`. Each is refused at `task add` before the ones it comes after are done or skipped (`after`, pipeline.json).
- `avancement.py task add backlog stories-<k> --agent hosa-product-owner --objet "<exigences, tickets>"`; on its return, `task done backlog stories-<k> --sortie <the ticket paths>`.
- Then `task add` `securite-<k>` (`hosa-security`) and `juridique-<k>` (`hosa-legal`) with `--objet "lot <k>"`, dispatched together; each return → `task done backlog <id> --sortie <the ticket paths it completed>`. A security or legal analysis still missing (fallback line) → `task skip backlog securite-<k> --detail "pas encore d'analyse"`. A `securite` or `juridique` stage the plan marks `non applicable` (the user set it aside) → no agent: `task skip backlog juridique-<k> --detail "étape écartée"`, then `<hosa> ticket_check .hosa/kb --ecartees <the lot's ticket paths>` writes the note `Non applicable — étape … écartée : <the plan's detail>` in each ticket, and the checker accepts it while the plan keeps that status.
- A `## Reprise` report → `task add` a new id (`<id>b`) for what it lists, then `task done` the cut one with what it did write.
- Then `task add backlog juge-<k> --agent hosa-juge --objet "lot <k>"`, dispatch `hosa-juge` with `backlog juge-<k>` and the slugs of the lot's tickets, and `task done backlog juge-<k> --sortie <the verdict path it gives>`. The judge judges each ticket once, complete: story, criteria, security and legal notes. Its report says the extract is too long for one judge → dispatch one `hosa-juge` per group it lists, together, then `task done` once.
- Refused by `juge-Qn` → each Non is already sent back: the refusal lists, per task it reopened (`stories-<k>`, `securite-<k>` or `juridique-<k>`, the `to` of its question), the exact lines. Dispatch a fresh agent of each reopened task on its refused tickets only, with those lines as they are; `task done` its task; then `hosa-juge` on the corrected tickets only (`juge backlog juge-<k> --tickets …`) and `task done backlog juge-<k>` again — never the whole lot: each ticket keeps its newest verdict. A PO correction that makes a security or legal note wrong is caught by the same judgment, and sent on. Refused as `plus ancien que le ticket` → the judge on the slugs it lists. At the bound (2 rounds of one question, or a ticket judged 3 times) it stops: show the user what each round refused.

**Dispatch.** `budget.js` applies pipeline.json's `dispatch` for `backlog`: **2 Hosa agents at once** at most (the judge of lot k beside the PO of lot k+1), and `hosa-security` and `hosa-legal` with `model: "sonnet"` (notes de tickets; their threat model, audits and gates stay on Opus). Four agents at once used up the 5-hour limit in 21 minutes on rieki. An agent cut by a limit or a pause is **not resumed** with `SendMessage`: its cache lasts 5 minutes, and a message writes its whole context again (rieki: 460 k for one agent). Dispatch a fresh one with its `## Reprise` and the files it wrote — refused past 5 minutes and 50 k tokens.

Turns "what the application must do" (the stable cahier des charges) into Product Backlog tickets — each one carrying the business story, its technical feasibility, where it lands in the architecture, and where it lands in the interface, so nothing enters `kb/tickets/` disconnected from the technical reality already decided by `stack`, `architecture`, and `interface`.

## Flow

```
Exigences non fonctionnelles [nfr] → définition de terminé
(kb/rules/design/definition-de-termine.md), vérifiée sur chaque ticket
        ↓
Exigences stables sans ticket lié, et tickets todo à préciser
        ↓
Par lot de 8 tickets au plus, un graphe de 4 tâches :
stories-<k> (hosa-product-owner) : découpe, depends_on, story,
critères, note technique, placements architecture et interface
        ↓
securite-<k> (hosa-security) et juridique-<k> (hosa-legal),
dispatchés ensemble : notes, cas d'abus et contraintes → critères
        ↓
juge-<k> (hosa-juge) : chaque Non rouvre sa tâche, sur ses
seuls tickets, avec les lignes exactes
        ↓
Dernier lot jugé → ticket_check --regles : chaque RGn/CEn
cité par un critère
        ↓
Priorités (l'utilisateur valide l'ordre) et estimations
        ↓
Log kb/tickets/log.md → checkpoint hosa-git : socle encore
non commité, puis KB
        ↓
Enchaîne sur `sprint`
```

## Trigger

Manual: `/backlog`. Auto: immediately after `interface`, or "crée le product backlog", "génère les tickets à partir du cahier des charges".

Single-ticket mode: `/backlog <slug-ticket>`, or chained by any skill that just created a `Ticket` — see **Single-Ticket Mode** below. A ticket is born complete: no skill reports a new ticket before this mode has run on it.

## Ticket complet

A ticket is ready to be planned (`sprint`) and executed (`develop`, `qa-plan`) when it has all of:
- a story (`En tant que … je veux … afin de …`) and a `Lié à :` line — to its `Exigence`, or, for a ticket born outside the cahier des charges (bug, recette gap, audit finding, change impact, sprint follow-up), to the concept that surfaced it;
- `## Critères d'acceptation` with at least one Given/When/Then scenario;
- real `## Note technique (senior dev)`, `## Placement architecture (architecte)`, `## Placement interface (UX/UI)`, `## Note sécurité (expert cybersécurité)` and `## Note juridique (expert conformité)` notes — not the fallback lines below; the security or legal note of a stage the plan marks `non applicable` is the line `ticket_check --ecartees` writes;
- each abuse case of the security note and each legal constraint of the legal note tied to its acceptance criterion (`→ CAn`): security and compliance are built and tested with the ticket, not found at the audit, the recette or the release gate;
- a `priority`, unless the user explicitly answered "pas encore";
- a `depends_on` (when present) naming existing tickets, with no cycle, none ranked after this ticket.

The checker is the source of truth — run it from the managed project's root, with any Python 3.9+:

```bash
<hosa> ticket_check .hosa/kb [.hosa/kb/tickets/<slug>.md ...]
```

No ticket given → every `state: todo` ticket. Exit `0` = all complete, `1` = gaps listed per ticket.

**Rules × criteria.** Once the last lot is judged, before `done backlog`:

```bash
<hosa> ticket_check .hosa/kb --regles
```

It lists each rule (`RGn`) and error case (`CEn`) of an exigence that no criterion of its tickets cites (`- CA1 [RG2] — …`) — the cell the judge can't see, it reads one ticket at a time. Exit `1` → one more `stories-<k>` task for `hosa-product-owner` with those exact lines: a criterion added to the ticket that owns the rule, or a new ticket. `done backlog` refuses while it finds one. An exigence none of whose tickets cites a rule was sliced before the ids existed: it is skipped, never rewritten for this.

---

## Step 1: Scope

List every `stable` `Exigence` (`kb_query.py .hosa/kb --type Exigence --where status=stable`), except those tagged `nfr` (Step 1b). For each one, `kb_query.py .hosa/kb --type Ticket --grep "cdc/<slug>.md"` lists the tickets that link to it — check every existing `Ticket` in `kb/tickets/` for a markdown link pointing back to that `Exigence`'s file — if one already links to it, skip it; a re-run of `backlog` only fills gaps, it never recreates or overwrites a ticket. Also collect every `state: todo` ticket with no `sprint` whose notes miss the Grounding Rule below — free prose instead of the bullets (a security note that only lists rule names), a bullet without a real reference, an abuse case or legal constraint with no `→ CAn`, a missing legal note, or a fallback line whose stage now exists: it is **refined** (those sections rewritten, the criteria they need appended, nothing else). The checker lists them all. Nothing left to create or refine → say so and stop.

## Step 1b: Definition of Done

An `Exigence` tagged `nfr` (performance, availability, data protection, accessibility, compatibility) is a constraint on every ticket, not a feature: it gets no ticket of its own. Write or update `kb/rules/design/definition-de-termine.md` — what every ticket must meet before `validation` accepts it, each item with **how it is checked**:

```markdown
---
type: Design Rule
title: Définition de terminé
description: "Ce que chaque ticket doit respecter avant d'être accepté"
tags: [process, nfr]
status: stable
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
## Pour chaque ticket
- Les tests du plan passent ; la suite complète reste verte — vérifié par `hosa-tester`
- Lint, format et types sans erreur — commandes de `## Outillage qualité`
- Revue de code PASS — `hosa-reviewer`
- Cas d'abus de la note sécurité et contraintes de la note juridique prouvés par leur critère — `hosa-tester`, `hosa-reviewer`
- Textes conformes au lexique — `<hosa> lexique_check .hosa/kb <checkout>` (script de Hosa, pas du projet : rien à installer)
- Documentation utilisateur à jour quand le ticket change ce qu'un utilisateur voit

## Exigences non fonctionnelles
- [<exigence nfr>](../../cdc/<slug>.md) — <cible chiffrée> — vérifié par : <test automatisé, mesure, outil> — s'applique à : <tous les tickets / ceux qui touchent X>
```

A target still "pas encore de chiffre" → the item says so; `qa-plan` then tests nothing for it, and the report says it. An `nfr` exigence that also needs something built (a data export for the right of access, a backup job) → its feature part gets a ticket, like any other exigence. Update this file in place on a re-run; log it to `kb/rules/design/log.md`.

## Steps 2-5c: Write the Tickets

What each ticket holds — the split, the story, the criteria, the Grounding Rule and the five notes — is in `${CLAUDE_PLUGIN_ROOT}/skills/backlog/redaction-tickets.md`, the one file the writing agents read (give them its path, never this skill):
- Steps 2-5, `hosa-product-owner`, one `stories-<k>` pass of 8 tickets at most: split, story and criteria, technical note (senior dev role), architecture placement, interface placement. Each pass gets its exigence paths, the slugs already written (for `depends_on`) and, from the second pass of an exigence on, the `## Reprise` split of the first.
- Step 5b, `hosa-security` (Mode 5 — Notes de tickets), `securite-<k>` with the lot's ticket paths: security note, each abuse case a criterion.
- Step 5c, `hosa-legal` (Mode 3 — Notes de tickets), `juridique-<k>`, same lot: legal note, each legal constraint a criterion.

## Step 6: Priority and Estimate

Once every ticket for this run is written, propose an order and ask the user once: "Je propose cet ordre pour ces N tickets ; je l'applique ? (oui, un autre ordre, ou 'pas encore' pour laisser sans priorité)". The proposal puts every ticket after the tickets in its `depends_on`, and the security and compliance mechanisms (Step 2) right after the first slice that makes them usable — never in a block at the end. An order from the user that ranks a ticket before one of its dependencies → say which, once; the checker reports it until it's fixed. Given an order, write `priority: <rang>` (1 = le plus urgent) into each ticket's frontmatter in that order; tickets left unprioritized keep no `priority` field rather than an invented one — `sprint` treats those as lowest priority, after every explicitly ranked ticket. Then set each ticket's `estimate` yourself, in the senior dev role, from its `Complexité`, in points — the one unit `sprint`, `develop` and the sprint reviews count: `1` (≤ ½ day), `2` (about 1 day) or `3` (2-3 days). Show them in the report; the user can correct any. Bigger than 3 → split it, as in Step 2.

## Step 7: Log and Check

Log each ticket created (and its `priority`/`estimate` once set) to `kb/tickets/log.md` (create if missing) — chronological, most recent date first, per OKF §9. Then run the checker (see **Ticket complet**) on the tickets just written and report any gap it lists.

## Step 8: Checkpoint

Every structuration skill ends with its `hosa-git` checkpoint, so the foundation is already committed. Check anyway `git -C <root> status --porcelain -- . ':(exclude).hosa'`: not empty → dispatch `hosa-git` with `model: haiku` (Mode 3, checkpoint) with those files — `git` Mode 1 refuses to start a sprint on uncommitted source. Then the KB checkpoint for the tickets.

## Single-Ticket Mode

Not a stage: no `start`, no `done` — the `backlog` stage stays as it is. Run on one existing `Ticket` — created by `hosa-product-owner` from `qa`, `recette`, `debug`, `qualite`, `changement`, `bilan-sprint`, by the `hosa` free-form flow, or by hand. Fills only what's missing; never rewrites a section that already meets the Grounding Rule.

1. Run the checker on the ticket. Already complete → say so and stop.
2. Story, `Lié à :` or `## Critères d'acceptation` missing → dispatch `hosa-product-owner` (Responsibility 4) to add them, with the concept that surfaced the ticket. It returns an Open Question instead of guessing a persona or a scenario — ask the user and redispatch.
3. Each of the five notes missing, still on its fallback line or failing the checker → write it as in Steps 3-5c (`hosa-security` and `hosa-legal` for theirs, with the criteria they append). A ticket born from an audit finding keeps the finding's `fichier:ligne` in its technical note, and its security note names the rule the finding broke. If the stage a note depends on still hasn't run (no `Stack Decision`, no architecture or interface doc, no security or legal analysis), keep the fallback line and say which stage is missing — that's the only case where a ticket legitimately stays incomplete.
4. No `priority` → propose a rank in the current backlog — after its `depends_on`, and a security or compliance fix before the tickets that build on the flawed code — and ask the user ("je le place en N, avant <ticket> ?", or "pas encore"). Given a rank, write it and shift every other `todo` ticket at that rank or below by one, so ranks stay unique and whole. Then set its `estimate`, same rules as Step 6.
5. If the ticket was created during an `active` sprint, ask whether it joins that sprint now or waits for the next one; only write `sprint: <slug>` (and add it to the sprint's `## Tickets`) on an explicit yes — `sprint`'s readiness guard is what this mode just satisfied. Then run `qa-plan` for it: a ticket joins a sprint with its tests, like every other.
6. Log every change to `kb/tickets/log.md` (and `kb/sprints/log.md` if Step 5 added it), then rerun the checker and report its line for this ticket.

## Commits

None here but Step 8's `hosa-git` checkpoints (`using-hosa`, Git checkpoints).

## Output

```
## Tickets précisés
- `kb/tickets/<slug>.md` — [titre] (sections réécrites)

## Tickets créés
- `kb/tickets/<slug>.md` — [titre] (state: todo) — [ligne du checker : complet / ce qui manque]

## Suite
Suite : `sprint` (proposition de sprint à valider), lancé sans attendre.
```
