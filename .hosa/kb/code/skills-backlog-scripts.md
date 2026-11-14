---
type: Module
title: skills/backlog/scripts
description: '!/usr/bin/env python3'
resource: skills/backlog/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-13T16:54:52Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/backlog/scripts/ticket_check.py` | !/usr/bin/env python3 |

## Symboles publics

- `bullet_items` — `skills/backlog/scripts/ticket_check.py:261` — The inline text and the sub-items of the labelled bullet `- **<label>** : …`.
- `cdc` — `skills/backlog/scripts/ticket_check.py:157` — `cdc.py`, the one definition of a rule's id — or None when it can't be loaded (never this check's failure).
- `cited_rules` — `skills/backlog/scripts/ticket_check.py:132`
- `creators` — `skills/backlog/scripts/ticket_check.py:352` — {path: slug of the ticket whose notes mark it `à créer`}.
- `criteria_ids` — `skills/backlog/scripts/ticket_check.py:256` — The `CAn` of a `## Critères d'acceptation` section, in order, once each.
- `cycle_from` — `skills/backlog/scripts/ticket_check.py:335`
- `depends_on` — `skills/backlog/scripts/ticket_check.py:321`
- `field` — `skills/backlog/scripts/ticket_check.py:303`
- `gaps` — `skills/backlog/scripts/ticket_check.py:390`
- `grounding` — `skills/backlog/scripts/ticket_check.py:284`
- `indicators_without_value` — `skills/backlog/scripts/ticket_check.py:140` — A criterion that cites an indicator states the value it must show on the test dataset: a wrong number is
- `late_dependencies` — `skills/backlog/scripts/ticket_check.py:449` — A dependency still to build that ranks after this ticket: `sprint` can't plan this one
- `linked_exigences` — `skills/backlog/scripts/ticket_check.py:151`
- `main` — `skills/backlog/scripts/ticket_check.py:469`
- `phantom_paths` — `skills/backlog/scripts/ticket_check.py:365` — Paths cited as existing that the project doesn't have: the ticket that creates
- `rank` — `skills/backlog/scripts/ticket_check.py:442`
- `repeated_criteria` — `skills/backlog/scripts/ticket_check.py:226` — Each criterion of a `todo` ticket that another ticket of the same exigence already states: the judge reads one
- `rule_coverage` — `skills/backlog/scripts/ticket_check.py:187` — Each numbered rule and error case of an exigence, cited by a criterion of one of its tickets — the cell
- `rules_of` — `skills/backlog/scripts/ticket_check.py:169` — The `RGn`/`CEn` in force in `kb/cdc/<slug>.md`; None when the fiche or `cdc.py` can't be read.
- `section` — `skills/backlog/scripts/ticket_check.py:308`
- `skipped_note` — `skills/backlog/scripts/ticket_check.py:87`
- `skipped_stages` — `skills/backlog/scripts/ticket_check.py:81` — {stage: detail} of the stages the progress plan marks `non applicable`.
- `split` — `skills/backlog/scripts/ticket_check.py:298`
- `unknown_rules` — `skills/backlog/scripts/ticket_check.py:177` — A criterion that cites a rule its exigences don't have: a wrong number, or a rule since dropped.
- `untraced` — `skills/backlog/scripts/ticket_check.py:275`
- `words` — `skills/backlog/scripts/ticket_check.py:218` — A criterion's words: code spans kept whole (they tell two screens apart), numbers neutralised, stopwords out.
- `write_skipped` — `skills/backlog/scripts/ticket_check.py:91` — Write the `Non applicable` line of each skipped stage whose note is absent, empty or on its

## Tickets et exigences

Aucun.
