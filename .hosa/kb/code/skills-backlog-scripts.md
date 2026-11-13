---
type: Module
title: skills/backlog/scripts
description: '!/usr/bin/env python3'
resource: skills/backlog/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-12T23:50:36Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/backlog/scripts/ticket_check.py` | !/usr/bin/env python3 |

## Symboles publics

- `bullet_items` — `skills/backlog/scripts/ticket_check.py:210` — The inline text and the sub-items of the labelled bullet `- **<label>** : …`.
- `cdc` — `skills/backlog/scripts/ticket_check.py:154` — `cdc.py`, the one definition of a rule's id — or None when it can't be loaded (never this check's failure).
- `cited_rules` — `skills/backlog/scripts/ticket_check.py:129`
- `creators` — `skills/backlog/scripts/ticket_check.py:301` — {path: slug of the ticket whose notes mark it `à créer`}.
- `criteria_ids` — `skills/backlog/scripts/ticket_check.py:205` — The `CAn` of a `## Critères d'acceptation` section, in order, once each.
- `cycle_from` — `skills/backlog/scripts/ticket_check.py:284`
- `depends_on` — `skills/backlog/scripts/ticket_check.py:270`
- `field` — `skills/backlog/scripts/ticket_check.py:252`
- `gaps` — `skills/backlog/scripts/ticket_check.py:339`
- `grounding` — `skills/backlog/scripts/ticket_check.py:233`
- `indicators_without_value` — `skills/backlog/scripts/ticket_check.py:137` — A criterion that cites an indicator states the value it must show on the test dataset: a wrong number is
- `late_dependencies` — `skills/backlog/scripts/ticket_check.py:398` — A dependency still to build that ranks after this ticket: `sprint` can't plan this one
- `linked_exigences` — `skills/backlog/scripts/ticket_check.py:148`
- `main` — `skills/backlog/scripts/ticket_check.py:418`
- `phantom_paths` — `skills/backlog/scripts/ticket_check.py:314` — Paths cited as existing that the project doesn't have: the ticket that creates
- `rank` — `skills/backlog/scripts/ticket_check.py:391`
- `rule_coverage` — `skills/backlog/scripts/ticket_check.py:184` — Each numbered rule and error case of an exigence, cited by a criterion of one of its tickets — the cell
- `rules_of` — `skills/backlog/scripts/ticket_check.py:166` — The `RGn`/`CEn` in force in `kb/cdc/<slug>.md`; None when the fiche or `cdc.py` can't be read.
- `section` — `skills/backlog/scripts/ticket_check.py:257`
- `skipped_note` — `skills/backlog/scripts/ticket_check.py:84`
- `skipped_stages` — `skills/backlog/scripts/ticket_check.py:78` — {stage: detail} of the stages the progress plan marks `non applicable`.
- `split` — `skills/backlog/scripts/ticket_check.py:247`
- `unknown_rules` — `skills/backlog/scripts/ticket_check.py:174` — A criterion that cites a rule its exigences don't have: a wrong number, or a rule since dropped.
- `untraced` — `skills/backlog/scripts/ticket_check.py:224`
- `write_skipped` — `skills/backlog/scripts/ticket_check.py:88` — Write the `Non applicable` line of each skipped stage whose note is absent, empty or on its

## Tickets et exigences

Aucun.
