---
type: Module
title: skills/backlog/scripts
description: '!/usr/bin/env python3'
resource: skills/backlog/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-17T18:14:03Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/backlog/scripts/ticket_check.py` | !/usr/bin/env python3 |

## Symboles publics

- `bullet_items` — `skills/backlog/scripts/ticket_check.py:279` — The inline text and the sub-items of the labelled bullet `- **<label>** : …`.
- `cdc` — `skills/backlog/scripts/ticket_check.py:175` — `cdc.py`, the one definition of a rule's id — or None when it can't be loaded (never this check's failure).
- `cited_rules` — `skills/backlog/scripts/ticket_check.py:150`
- `closure` — `skills/backlog/scripts/ticket_check.py:505` — Every ticket `slug` waits for, directly or through another.
- `creators` — `skills/backlog/scripts/ticket_check.py:425` — {path: slug of the ticket whose notes mark it `à créer`}.
- `criteria_ids` — `skills/backlog/scripts/ticket_check.py:274` — The `CAn` of a `## Critères d'acceptation` section, in order, once each.
- `cycle_from` — `skills/backlog/scripts/ticket_check.py:408`
- `data_access` — `skills/backlog/scripts/ticket_check.py:521` — (tables written, tables read) from the architecture placement's `Données` bullet, as `backlog` writes it:
- `deferred_cases` — `skills/backlog/scripts/ticket_check.py:325` — Every abuse case deferred for exploratory use, done tickets included: what real use must build first.
- `depends_on` — `skills/backlog/scripts/ticket_check.py:375`
- `deps_of` — `skills/backlog/scripts/ticket_check.py:403` — {slug: its `depends_on`}, every ticket read once (rieki: 24 886 reads for 122 tickets, 10 s).
- `field` — `skills/backlog/scripts/ticket_check.py:357`
- `gaps` — `skills/backlog/scripts/ticket_check.py:672`
- `grounding` — `skills/backlog/scripts/ticket_check.py:338`
- `hidden_dependencies` — `skills/backlog/scripts/ticket_check.py:560` — The dependencies a ticket's own text states that its `depends_on` misses — the edges `sprint` plans from.
- `in_code` — `skills/backlog/scripts/ticket_check.py:606` — The label as a whole literal: `"Confirmer"`, `>Confirmer<`, `:red[Confirmer]`, « Confirmer » in a comment —
- `indicators_without_value` — `skills/backlog/scripts/ticket_check.py:158` — A criterion that cites an indicator states the value it must show on the test dataset: a wrong number is
- `label_owners` — `skills/backlog/scripts/ticket_check.py:488` — {label: the tickets still to build whose criteria click it} — the tickets that bring it.
- `late_dependencies` — `skills/backlog/scripts/ticket_check.py:738` — A dependency still to build that ranks after this ticket — reported only: the roadmap builds each ticket after
- `linked_exigences` — `skills/backlog/scripts/ticket_check.py:169`
- `main` — `skills/backlog/scripts/ticket_check.py:759`
- `one_fix` — `skills/backlog/scripts/ticket_check.py:655` — A checker line that is its own decision: `hosa-product-owner` applies it (Graph fixes), nobody is asked.
- `phantom_paths` — `skills/backlog/scripts/ticket_check.py:438` — Paths cited as existing that the project doesn't have: the ticket that creates
- `rank` — `skills/backlog/scripts/ticket_check.py:731`
- `repeated_criteria` — `skills/backlog/scripts/ticket_check.py:244` — Each criterion of a `todo` ticket that another ticket of the same exigence already states: the judge reads one
- `rule_coverage` — `skills/backlog/scripts/ticket_check.py:205` — Each numbered rule and error case of an exigence, cited by a criterion of one of its tickets — the cell
- `rules_of` — `skills/backlog/scripts/ticket_check.py:187` — The `RGn`/`CEn` in force in `kb/cdc/<slug>.md`; None when the fiche or `cdc.py` can't be read.
- `section` — `skills/backlog/scripts/ticket_check.py:362`
- `single_fixes` — `skills/backlog/scripts/ticket_check.py:661` — Every `todo` ticket's one-fix lines, verbatim (rieki 0.1.107: 16 tickets left « à compléter » while the
- `skipped_note` — `skills/backlog/scripts/ticket_check.py:105`
- `skipped_stages` — `skills/backlog/scripts/ticket_check.py:99` — {stage: detail} of the stages the progress plan marks `non applicable`.
- `source_text` — `skills/backlog/scripts/ticket_check.py:474` — The project's source, read once: a label it holds as a literal already exists.
- `split` — `skills/backlog/scripts/ticket_check.py:352`
- `stamp` — `skills/backlog/scripts/ticket_check.py:389` — What the tickets' files are now: a cache keyed on it is read again once one of them changes.
- `ticket_index` — `skills/backlog/scripts/ticket_check.py:556`
- `unbuilt_labels` — `skills/backlog/scripts/ticket_check.py:612` — A criterion names only what the code, its own ticket or its `depends_on` brings: a button another
- `unknown_rules` — `skills/backlog/scripts/ticket_check.py:195` — A criterion that cites a rule its exigences don't have: a wrong number, or a rule since dropped.
- `untraced` — `skills/backlog/scripts/ticket_check.py:308`
- `usage` — `skills/backlog/scripts/ticket_check.py:300` — The project's `## Usage` (kb/project/identity.md): `exploratoire` or `réel`. Absent → `réel`: full security.
- `words` — `skills/backlog/scripts/ticket_check.py:236` — A criterion's words: code spans kept whole (they tell two screens apart), numbers neutralised, stopwords out.
- `write_skipped` — `skills/backlog/scripts/ticket_check.py:109` — Write the `Non applicable` line of each skipped stage whose note is absent, empty or on its

## Tickets et exigences

Aucun.
