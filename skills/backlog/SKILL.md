---
name: backlog
description: "Use to turn every stable exigence into planned backlog tickets (story, criteria, `depends_on`, estimate) and the roadmap, or to complete one ticket. Triggers: \"crée le product backlog\", after `interface`."
---

# Backlog

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything (Single-Ticket Mode excepted: not a stage, no call): `avancement.py start backlog`; refused → name the missing stage to the user and stop; refused as already done → a re-run only on the user's request: the same `start` with `--rouvre "<their request>"`. Stopped on a user question: `block backlog --detail "<question>"`. Once the stage's output is written and committed: `done backlog`. Never skip these calls: without them a cut session can't resume (« reprends »), and `budget.js` can't apply the stage's `dispatch` rules (each agent's model, the agents at once) — they hold only while the stage is `en cours`.

**Plan everything, detail just in time.** This stage writes every ticket's story, criteria, `depends_on` and `estimate`, then the roadmap: what the graph needs, and the cheap part. The five notes are `sprint`'s, for the tickets of the next sprint only (`notes-<k>` → `securite-<k>`, `juridique-<k>` → `juge-<k>`). rieki wrote the notes of 128 tickets up front: about 61 $, 27 % of the project, and 22 of them used after three sprints; the others went stale (« classe existe sans méthode ») or out of the plan. `ticket_check --planifiable` is this stage's proof: an absent note is an `(à détailler)` line, not a gap here.

**Tâches.** A lot is **8 tickets at most**, not 8 exigences (rieki: 2 exigences gave 52 tickets, one pass wrote 39 of them up to 273 k tokens of context). `task done stories-<k>` refuses more (`lot`, pipeline.json). An exigence that splits into more: its first pass decides the whole split, writes the first 8 and lists the others under `## Reprise` (slug — scope — `depends_on`, one line each); the next pass is `stories-<k>b` on that list.
A lot is two tasks, the judge last: `stories-<k>` → `juge-<k>`. The judge's task is refused at `task add` before its stories are done (`after`, pipeline.json).
- `avancement.py task add backlog stories-<k> --agent hosa-product-owner --objet "<exigences, tickets>"`; on its return, `task done backlog stories-<k> --sortie <the ticket paths>`.
- A `## Reprise` report → `task add` a new id (`<id>b`) for what it lists, then `task done` the cut one with what it did write.
- Then `task add backlog juge-<k> --agent hosa-juge --objet "lot <k>"`, dispatch `hosa-juge` with `backlog juge-<k>` and the slugs of the lot's tickets, and `task done backlog juge-<k> --sortie <the verdict path it gives>`. The judge asks the story and criteria questions only. Its report says the extract is too long for one judge → dispatch one `hosa-juge` per group it lists, together, then `task done` once.
- Refused by `juge-Qn` → each Non is already sent back: the refusal lists the exact lines per ticket and reopens `stories-<k>`. Dispatch a fresh `hosa-product-owner` on its refused tickets only, with those lines as they are; `task done` its task; then `hosa-juge` on the corrected tickets only (`juge backlog juge-<k> --tickets …`) and `task done backlog juge-<k>` again — never the whole lot: each ticket keeps its newest verdict. Refused as `plus ancien que le ticket` → the judge on the slugs it lists. At the bound (2 rounds of one question, or a ticket judged 3 times) it stops: show the user what each round refused.

**Dispatch.** `budget.js` applies pipeline.json's `dispatch` for `backlog`: **2 Hosa agents at once** at most (the judge of lot k beside the PO of lot k+1). Four agents at once used up the 5-hour limit in 21 minutes on rieki. An agent cut by a limit or a pause is **not resumed** with `SendMessage`: its cache lasts 5 minutes, and a message writes its whole context again (rieki: 460 k for one agent). Dispatch a fresh one with its `## Reprise` and the files it wrote — refused past 5 minutes and 50 k tokens.

Turns "what the application must do" (the stable cahier des charges) into Product Backlog tickets — each one a vertical slice with its story, its criteria, its dependencies and its size, so the whole roadmap is computed from the graph before the first sprint. Each ticket gets its technical feasibility, its place in the architecture and the interface, and its security and legal notes when it enters a sprint, against the code as it is then.

## Flow

```
Exigences non fonctionnelles [nfr] → définition de terminé
(kb/rules/design/definition-de-termine.md), vérifiée sur chaque ticket
        ↓
Exigences stables sans ticket lié
        ↓
Par lot de 8 tickets au plus :
stories-<k> (hosa-product-owner) : découpe, depends_on, story,
critères, estimation — aucune note
        ↓
juge-<k> (hosa-juge) : story et critères ; chaque Non rouvre
stories-<k>, sur ses seuls tickets, avec les lignes exactes
        ↓
Dernier lot jugé → ticket_check --regles : chaque RGn/CEn
cité par un critère ; ticket_check --repetes : chaque
comportement porté par un seul ticket
        ↓
Priorités et jalons (l'utilisateur valide les deux en une
réponse) : le premier jalon mesure un objectif de l'identité
(--mesure On) ; feuille de route calculée
        ↓
Log kb/tickets/log.md → checkpoint hosa-git : socle encore
non commité, puis KB
        ↓
Enchaîne sur `sprint` : il détaille les tickets de son sprint
```

## Trigger

Manual: `/backlog`. Auto: immediately after `interface`, or "crée le product backlog", "génère les tickets à partir du cahier des charges".

Single-ticket mode: `/backlog <slug-ticket>`, or chained by any skill that just created a `Ticket` — see **Single-Ticket Mode** below. A ticket is born complete: no skill reports a new ticket before this mode has run on it.

## Ticket planifiable, ticket complet

A ticket is **planifiable** — the roadmap places it, this stage closes on it — when it has:
- a story (`En tant que … je veux … afin de …`) and a `Lié à :` line — to its `Exigence`, or, for a ticket born outside the cahier des charges (bug, recette gap, audit finding, change impact, sprint follow-up), to the concept that surfaced it;
- `## Critères d'acceptation` with at least one Given/When/Then scenario;
- an `estimate` and a `priority`, unless the user explicitly answered "pas encore";
- a `depends_on` (when present) naming existing tickets, with no cycle (a dependency ranked after it is only reported: the roadmap builds from the graph, `priority` breaks ties);
- no criterion testing a button another ticket brings (`clique sur « … »` in its criteria) unless that ticket is in its `depends_on` or the code has the button, and none conditional (« dès qu'il existe ») — `HOSA_LIBELLES=0` turns this check off.

`ticket_check` also refuses, each with its switch: a dependency the ticket's own text states that `depends_on` misses (a criterion citing another ticket, a table read that no earlier ticket writes — `HOSA_DEPENDANCES=0`); a `CAn`, ticket or KB file cited that doesn't exist (`HOSA_RENVOIS=0`); a criterion observing a state that no ticket of `depends_on` brings (`HOSA_ETATS=0`); a quoted label that is a forbidden synonym of `kb/interface/lexique.md` (`HOSA_LEXIQUE=0`).

A ticket is **complete** — ready to be built (`develop`, `qa-plan`) — when it also has:
- real `## Note technique (senior dev)`, `## Placement architecture (architecte)`, `## Placement interface (UX/UI)`, `## Note sécurité (expert cybersécurité)` and `## Note juridique (expert conformité)` notes — not the fallback lines below; a stage the plan marks `non applicable` needs no note at all;
- each abuse case of the security note and each legal constraint of the legal note tied to its acceptance criterion (`→ CAn`): security and compliance are built and tested with the ticket, not found at the audit, the recette or the release gate. While `## Usage` of `kb/project/identity.md` is `exploratoire`, an abuse case may say `— différé : usage exploratoire` instead (`hosa-security` Mode 5); `livraison` refuses real use while one is left (`ticket_check --differes`).

`sprint` makes the tickets of its sprint complete; Single-Ticket Mode makes one ticket complete.

The checker is the source of truth — run it from the managed project's root, with any Python 3.9+:

```bash
<hosa> ticket_check .hosa/kb [--planifiable] [.hosa/kb/tickets/<slug>.md ...]
```

No ticket given → every `state: todo` ticket. Exit `0` = all complete (planifiable with `--planifiable`), `1` = gaps listed per ticket.

**Rules × criteria.** Once the last lot is judged, before `done backlog`:

```bash
<hosa> ticket_check .hosa/kb --regles
```

It lists each rule (`RGn`) and error case (`CEn`) of an exigence that no criterion of its tickets cites (`- CA1 [RG2] — …`) — the cell the judge can't see, it reads one ticket at a time. Exit `1` → one more `stories-<k>` task for `hosa-product-owner` with those exact lines: a criterion added to the ticket that owns the rule, or a new ticket. `done backlog` refuses while it finds one. An exigence whose rules have no id yet (a cahier des charges signed before them) is refused: `<hosa> cdc numerote <kb>` numbers them, text and signature unchanged, then its tickets cite them. An exigence none of whose tickets cites a rule was sliced before the ids existed: shown `(info)`, not refused; its tickets cite them when they are next refined.

**One behaviour, one ticket.** Then, before `done backlog`:

```bash
<hosa> ticket_check .hosa/kb --repetes
```

It lists each criterion of a `todo` ticket that another ticket of the same exigence states too (70 % of their words in common) — the judge can't see it either. Exit `1` → one more `stories-<k>` task for `hosa-product-owner` with those exact lines: the criterion stays in one ticket (« Say it once », `redaction-tickets.md`), the other drops it or names that ticket in `depends_on`. `done backlog` refuses while it finds one; `HOSA_REPETES=0` turns this check off.

---

## Step 1: Scope

List every `stable` `Exigence` (`kb_query.py .hosa/kb --type Exigence --where status=stable`), except those tagged `nfr` (Step 1b). For each one, `kb_query.py .hosa/kb --type Ticket --grep "cdc/<slug>.md"` lists the tickets that link to it — check every existing `Ticket` in `kb/tickets/` for a markdown link pointing back to that `Exigence`'s file — if one already links to it, skip it; a re-run of `backlog` only fills gaps, it never recreates or overwrites a ticket. A `state: todo` ticket whose story or criteria the checker refuses (`--planifiable`) is **refined**: those parts rewritten, nothing else. Its notes are `sprint`'s. Nothing left to create or refine → say so and stop.

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

## Step 2: Write the Tickets

What each ticket holds is in `${CLAUDE_PLUGIN_ROOT}/skills/backlog/redaction-tickets.md`, the one file the writing agents read (give them its path, never this skill). Here, `hosa-product-owner` runs its Step 2 only, one `stories-<k>` pass of 8 tickets at most: the split, the story, the criteria, `depends_on` and `estimate`. Each pass gets its exigence paths, the slugs already written (for `depends_on`), the architecture's module map (`kb/infra/` `## Documentation d'architecture`: a ticket that needs another one's table, module or screen depends on it) and, from the second pass of an exigence on, the `## Reprise` split of the first. Steps 3-5c (the five notes) run in `sprint`, and in Single-Ticket Mode below.

## Step 6: Priority and Estimate

**Split shown first.** Before proposing the order, run `<hosa> ticket_check .hosa/kb --decoupage` and put its `(info)` lines in the same question: each exigence cut into more tickets than its rules and error cases. The user confirms the split or asks to merge; never merge on your own. rieki: 7 rules gave 22 tickets, and each extra ticket brought about 7 criteria and their cross-references.

Once every ticket for this run is written, propose an order and ask the user once: "Je propose cet ordre pour ces N tickets ; je l'applique ? (oui, un autre ordre, ou 'pas encore' pour laisser sans priorité)". The proposal puts the main persona journey first, end to end, one thin ticket per step (rieki: after three sprints, import → nettoyage → run → résultats had no run yet, while polish of the Résultats screen ranked 9). Variants, polish and secondary screens come after the journey step they improve. It puts every ticket after the tickets in its `depends_on`, and the security and compliance mechanisms (Step 2) right after the first slice that makes them usable — never in a block at the end. An order from the user that ranks a ticket before one of its dependencies is harmless: the roadmap builds from the graph, the rank only breaks ties. Given an order, write `priority: <rang>` (1 = le plus urgent) into each ticket's frontmatter in that order; tickets left unprioritized keep no `priority` field rather than an invented one — `sprint` treats those as lowest priority, after every explicitly ranked ticket. The `stories-<k>` pass wrote each ticket's `estimate` (`redaction-tickets.md`) — no judgment of yours —, in points — the one unit `sprint`, `develop` and the sprint reviews count: `1` (≤ ½ day), `2` (about 1 day) or `3` (2-3 days). Show them in the report; the user can correct any. Bigger than 3 → split it, as in Step 2.

**Milestones and roadmap.** In the same question, propose the milestones. **The first one measures an objective** of `## Objectifs mesurables` (`kb/project/identity.md`): the ticket whose demo shows that objective's indicator, reached by the shortest path — the thinnest ticket of each step before it, no variant, no polish, no hardening the path doesn't need. rieki, « exploratoire : tester Timestral », O1 « Timestral bat la méthode simple sur 70 % des séries »: after 221 $ and three sprints its three milestones were all in Importer, and no forecast had run; the first milestone was « le WAPE de Timestral face à la référence, à l'écran ». The next ones are the tickets that end each step of the main persona journey, in order (rieki: import des ventes → nettoyage → run → graphique de prévision), each a result a persona sees at a demo. A ticket that must come by a given step (a security fix, a legal page) is a milestone too, placed there. Once the user validated them, compute every sprint:

```bash
<hosa> graphe_tickets .hosa/kb feuille --jalons <slug>,<slug>,… --mesure <On> --ecrire
```

`--mesure` names the objective the first milestone measures; `feuille` refuses `--jalons` without it while the identity has objectives, and `done sprint` refuses a roadmap whose first milestone measures none.

It writes `kb/project/feuille-de-route.md`: `## Jalons` as validated, then each sprint computed from the graph (each milestone's whole path in order, cut at whole sub-paths over the bounds, then the tickets no milestone needs by priority), the blocked milestones and the tickets to complete. `sprint` takes the next one, recomputes it and details its tickets; the user validates the milestones once, not each sprint. A blocked milestone or a ticket to complete → the refinement of Step 1, at once.

## Step 7: Log and Check

Log each ticket created (and its `priority`/`estimate` once set) to `kb/tickets/log.md` (create if missing) — chronological, most recent date first, per OKF §9. Then run the checker with `--planifiable` on the tickets just written and report any gap it lists.

## Step 8: Checkpoint

Every structuration skill ends with its `hosa-git` checkpoint, so the foundation is already committed. Check anyway `git -C <root> status --porcelain -- . ':(exclude).hosa'`: not empty → dispatch `hosa-git` with `model: haiku` (Mode 3, checkpoint) with those files — `git` Mode 1 refuses to start a sprint on uncommitted source. Then the KB checkpoint for the tickets.

## Single-Ticket Mode

Not a stage: no `start`, no `done` — the `backlog` stage stays as it is. Run on one existing `Ticket` — created by `hosa-product-owner` from `qa`, `recette`, `debug`, `qualite`, `changement`, `bilan-sprint`, by the `hosa` free-form flow, or by hand. Fills only what's missing; never rewrites a section that already meets the Grounding Rule. It makes the ticket complete, notes included: a ticket born from a finding is usually built next.

1. Run the checker on the ticket. Already complete → say so and stop.
2. Story, `Lié à :` or `## Critères d'acceptation` missing → dispatch `hosa-product-owner` (Responsibility 4) to add them, with the concept that surfaced the ticket. It returns an Open Question instead of guessing a persona or a scenario — ask the user and redispatch.
2b. A checker line with one fix — a `depends_on` to add, a criterion to move to the ticket it names, one behaviour in two tickets, a table's first writer — → dispatch `hosa-product-owner` (Responsibility 4, Graph fixes) with those exact lines, on every ticket they name. No question: the line is the decision. Then `graphe_tickets … feuille --ecrire` recomputes the roadmap.
3. Each of the five notes missing, still on its fallback line or failing the checker → write it as in `redaction-tickets.md` Steps 3-5c (`hosa-product-owner` for the first three, `hosa-security` and `hosa-legal` for theirs, with the criteria they append; none for a stage the plan marks `non applicable`). A ticket born from an audit finding keeps the finding's `fichier:ligne` in its technical note, and its security note names the rule the finding broke. If the stage a note depends on still hasn't run (no `Stack Decision`, no architecture or interface doc, no security or legal analysis), keep the fallback line and say which stage is missing — that's the only case where a ticket legitimately stays incomplete.
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
Suite : `sprint` (le premier sprint de la feuille de route), lancé sans attendre.
```
