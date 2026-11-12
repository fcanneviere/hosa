---
type: Module
title: skills/backlog/scripts
description: '!/usr/bin/env python3'
resource: skills/backlog/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-12T07:10:14Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/backlog/scripts/ticket_check.py` | !/usr/bin/env python3 |

## Symboles publics

- `bullet_items` — `skills/backlog/scripts/ticket_check.py:194` — The inline text and the sub-items of the labelled bullet `- **<label>** : …`.
- `cdc` — `skills/backlog/scripts/ticket_check.py:138` — `cdc.py`, the one definition of a rule's id — or None when it can't be loaded (never this check's failure).
- `cited_rules` — `skills/backlog/scripts/ticket_check.py:128`
- `creators` — `skills/backlog/scripts/ticket_check.py:285` — {path: slug of the ticket whose notes mark it `à créer`}.
- `criteria_ids` — `skills/backlog/scripts/ticket_check.py:189` — The `CAn` of a `## Critères d'acceptation` section, in order, once each.
- `cycle_from` — `skills/backlog/scripts/ticket_check.py:268`
- `depends_on` — `skills/backlog/scripts/ticket_check.py:254`
- `field` — `skills/backlog/scripts/ticket_check.py:236`
- `gaps` — `skills/backlog/scripts/ticket_check.py:323`
- `grounding` — `skills/backlog/scripts/ticket_check.py:217`
- `late_dependencies` — `skills/backlog/scripts/ticket_check.py:381` — A dependency still to build that ranks after this ticket: `sprint` can't plan this one
- `linked_exigences` — `skills/backlog/scripts/ticket_check.py:132`
- `main` — `skills/backlog/scripts/ticket_check.py:401`
- `phantom_paths` — `skills/backlog/scripts/ticket_check.py:298` — Paths cited as existing that the project doesn't have: the ticket that creates
- `rank` — `skills/backlog/scripts/ticket_check.py:374`
- `rule_coverage` — `skills/backlog/scripts/ticket_check.py:168` — Each numbered rule and error case of an exigence, cited by a criterion of one of its tickets — the cell
- `rules_of` — `skills/backlog/scripts/ticket_check.py:150` — The `RGn`/`CEn` in force in `kb/cdc/<slug>.md`; None when the fiche or `cdc.py` can't be read.
- `section` — `skills/backlog/scripts/ticket_check.py:241`
- `skipped_note` — `skills/backlog/scripts/ticket_check.py:83`
- `skipped_stages` — `skills/backlog/scripts/ticket_check.py:77` — {stage: detail} of the stages the progress plan marks `non applicable`.
- `split` — `skills/backlog/scripts/ticket_check.py:231`
- `unknown_rules` — `skills/backlog/scripts/ticket_check.py:158` — A criterion that cites a rule its exigences don't have: a wrong number, or a rule since dropped.
- `untraced` — `skills/backlog/scripts/ticket_check.py:208`
- `write_skipped` — `skills/backlog/scripts/ticket_check.py:87` — Write the `Non applicable` line of each skipped stage whose note is absent, empty or on its

## Tickets et exigences

Aucun.
