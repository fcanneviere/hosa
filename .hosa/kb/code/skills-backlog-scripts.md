---
type: Module
title: skills/backlog/scripts
description: '!/usr/bin/env python3'
resource: skills/backlog/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-15T09:36:25Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/backlog/scripts/ticket_check.py` | !/usr/bin/env python3 |

## Symboles publics

- `bullet_items` — `skills/backlog/scripts/ticket_check.py:265` — The inline text and the sub-items of the labelled bullet `- **<label>** : …`.
- `cdc` — `skills/backlog/scripts/ticket_check.py:161` — `cdc.py`, the one definition of a rule's id — or None when it can't be loaded (never this check's failure).
- `cited_rules` — `skills/backlog/scripts/ticket_check.py:136`
- `closure` — `skills/backlog/scripts/ticket_check.py:455` — Every ticket `slug` waits for, directly or through another.
- `creators` — `skills/backlog/scripts/ticket_check.py:375` — {path: slug of the ticket whose notes mark it `à créer`}.
- `criteria_ids` — `skills/backlog/scripts/ticket_check.py:260` — The `CAn` of a `## Critères d'acceptation` section, in order, once each.
- `cycle_from` — `skills/backlog/scripts/ticket_check.py:358`
- `depends_on` — `skills/backlog/scripts/ticket_check.py:325`
- `deps_of` — `skills/backlog/scripts/ticket_check.py:353` — {slug: its `depends_on`}, every ticket read once (rieki: 24 886 reads for 122 tickets, 10 s).
- `field` — `skills/backlog/scripts/ticket_check.py:307`
- `gaps` — `skills/backlog/scripts/ticket_check.py:509`
- `grounding` — `skills/backlog/scripts/ticket_check.py:288`
- `in_code` — `skills/backlog/scripts/ticket_check.py:466` — The label as a whole literal: `"Confirmer"`, `>Confirmer<`, `:red[Confirmer]`, « Confirmer » in a comment —
- `indicators_without_value` — `skills/backlog/scripts/ticket_check.py:144` — A criterion that cites an indicator states the value it must show on the test dataset: a wrong number is
- `label_owners` — `skills/backlog/scripts/ticket_check.py:438` — {label: the tickets still to build whose criteria click it} — the tickets that bring it.
- `late_dependencies` — `skills/backlog/scripts/ticket_check.py:569` — A dependency still to build that ranks after this ticket: `sprint` can't plan this one
- `linked_exigences` — `skills/backlog/scripts/ticket_check.py:155`
- `main` — `skills/backlog/scripts/ticket_check.py:589`
- `phantom_paths` — `skills/backlog/scripts/ticket_check.py:388` — Paths cited as existing that the project doesn't have: the ticket that creates
- `rank` — `skills/backlog/scripts/ticket_check.py:562`
- `repeated_criteria` — `skills/backlog/scripts/ticket_check.py:230` — Each criterion of a `todo` ticket that another ticket of the same exigence already states: the judge reads one
- `rule_coverage` — `skills/backlog/scripts/ticket_check.py:191` — Each numbered rule and error case of an exigence, cited by a criterion of one of its tickets — the cell
- `rules_of` — `skills/backlog/scripts/ticket_check.py:173` — The `RGn`/`CEn` in force in `kb/cdc/<slug>.md`; None when the fiche or `cdc.py` can't be read.
- `section` — `skills/backlog/scripts/ticket_check.py:312`
- `skipped_note` — `skills/backlog/scripts/ticket_check.py:91`
- `skipped_stages` — `skills/backlog/scripts/ticket_check.py:85` — {stage: detail} of the stages the progress plan marks `non applicable`.
- `source_text` — `skills/backlog/scripts/ticket_check.py:424` — The project's source, read once: a label it holds as a literal already exists.
- `split` — `skills/backlog/scripts/ticket_check.py:302`
- `stamp` — `skills/backlog/scripts/ticket_check.py:339` — What the tickets' files are now: a cache keyed on it is read again once one of them changes.
- `unbuilt_labels` — `skills/backlog/scripts/ticket_check.py:472` — A criterion names only what the code, its own ticket or its `depends_on` brings: a button another
- `unknown_rules` — `skills/backlog/scripts/ticket_check.py:181` — A criterion that cites a rule its exigences don't have: a wrong number, or a rule since dropped.
- `untraced` — `skills/backlog/scripts/ticket_check.py:279`
- `words` — `skills/backlog/scripts/ticket_check.py:222` — A criterion's words: code spans kept whole (they tell two screens apart), numbers neutralised, stopwords out.
- `write_skipped` — `skills/backlog/scripts/ticket_check.py:95` — Write the `Non applicable` line of each skipped stage whose note is absent, empty or on its

## Tickets et exigences

Aucun.
