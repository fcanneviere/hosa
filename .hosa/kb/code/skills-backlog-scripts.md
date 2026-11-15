---
type: Module
title: skills/backlog/scripts
description: '!/usr/bin/env python3'
resource: skills/backlog/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-15T12:16:04Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/backlog/scripts/ticket_check.py` | !/usr/bin/env python3 |

## Symboles publics

- `bullet_items` — `skills/backlog/scripts/ticket_check.py:264` — The inline text and the sub-items of the labelled bullet `- **<label>** : …`.
- `cdc` — `skills/backlog/scripts/ticket_check.py:160` — `cdc.py`, the one definition of a rule's id — or None when it can't be loaded (never this check's failure).
- `cited_rules` — `skills/backlog/scripts/ticket_check.py:135`
- `closure` — `skills/backlog/scripts/ticket_check.py:454` — Every ticket `slug` waits for, directly or through another.
- `creators` — `skills/backlog/scripts/ticket_check.py:374` — {path: slug of the ticket whose notes mark it `à créer`}.
- `criteria_ids` — `skills/backlog/scripts/ticket_check.py:259` — The `CAn` of a `## Critères d'acceptation` section, in order, once each.
- `cycle_from` — `skills/backlog/scripts/ticket_check.py:357`
- `data_access` — `skills/backlog/scripts/ticket_check.py:470` — (tables written, tables read) from the architecture placement's `Données` bullet, as `backlog` writes it:
- `depends_on` — `skills/backlog/scripts/ticket_check.py:324`
- `deps_of` — `skills/backlog/scripts/ticket_check.py:352` — {slug: its `depends_on`}, every ticket read once (rieki: 24 886 reads for 122 tickets, 10 s).
- `field` — `skills/backlog/scripts/ticket_check.py:306`
- `gaps` — `skills/backlog/scripts/ticket_check.py:598`
- `grounding` — `skills/backlog/scripts/ticket_check.py:287`
- `hidden_dependencies` — `skills/backlog/scripts/ticket_check.py:509` — The dependencies a ticket's own text states that its `depends_on` misses — the edges `sprint` plans from.
- `in_code` — `skills/backlog/scripts/ticket_check.py:555` — The label as a whole literal: `"Confirmer"`, `>Confirmer<`, `:red[Confirmer]`, « Confirmer » in a comment —
- `indicators_without_value` — `skills/backlog/scripts/ticket_check.py:143` — A criterion that cites an indicator states the value it must show on the test dataset: a wrong number is
- `label_owners` — `skills/backlog/scripts/ticket_check.py:437` — {label: the tickets still to build whose criteria click it} — the tickets that bring it.
- `late_dependencies` — `skills/backlog/scripts/ticket_check.py:659` — A dependency still to build that ranks after this ticket — reported only: the roadmap builds each ticket after
- `linked_exigences` — `skills/backlog/scripts/ticket_check.py:154`
- `main` — `skills/backlog/scripts/ticket_check.py:680`
- `phantom_paths` — `skills/backlog/scripts/ticket_check.py:387` — Paths cited as existing that the project doesn't have: the ticket that creates
- `rank` — `skills/backlog/scripts/ticket_check.py:652`
- `repeated_criteria` — `skills/backlog/scripts/ticket_check.py:229` — Each criterion of a `todo` ticket that another ticket of the same exigence already states: the judge reads one
- `rule_coverage` — `skills/backlog/scripts/ticket_check.py:190` — Each numbered rule and error case of an exigence, cited by a criterion of one of its tickets — the cell
- `rules_of` — `skills/backlog/scripts/ticket_check.py:172` — The `RGn`/`CEn` in force in `kb/cdc/<slug>.md`; None when the fiche or `cdc.py` can't be read.
- `section` — `skills/backlog/scripts/ticket_check.py:311`
- `skipped_note` — `skills/backlog/scripts/ticket_check.py:90`
- `skipped_stages` — `skills/backlog/scripts/ticket_check.py:84` — {stage: detail} of the stages the progress plan marks `non applicable`.
- `source_text` — `skills/backlog/scripts/ticket_check.py:423` — The project's source, read once: a label it holds as a literal already exists.
- `split` — `skills/backlog/scripts/ticket_check.py:301`
- `stamp` — `skills/backlog/scripts/ticket_check.py:338` — What the tickets' files are now: a cache keyed on it is read again once one of them changes.
- `ticket_index` — `skills/backlog/scripts/ticket_check.py:505`
- `unbuilt_labels` — `skills/backlog/scripts/ticket_check.py:561` — A criterion names only what the code, its own ticket or its `depends_on` brings: a button another
- `unknown_rules` — `skills/backlog/scripts/ticket_check.py:180` — A criterion that cites a rule its exigences don't have: a wrong number, or a rule since dropped.
- `untraced` — `skills/backlog/scripts/ticket_check.py:278`
- `words` — `skills/backlog/scripts/ticket_check.py:221` — A criterion's words: code spans kept whole (they tell two screens apart), numbers neutralised, stopwords out.
- `write_skipped` — `skills/backlog/scripts/ticket_check.py:94` — Write the `Non applicable` line of each skipped stage whose note is absent, empty or on its

## Tickets et exigences

Aucun.
