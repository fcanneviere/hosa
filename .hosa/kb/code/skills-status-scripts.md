---
type: Module
title: skills/status/scripts
description: '!/usr/bin/env python3'
resource: skills/status/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-10-17T12:13:03Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/status/scripts/avancement.py` | !/usr/bin/env python3 |
| `skills/status/scripts/usage_report.py` | !/usr/bin/env python3 |

## Symboles publics

- `check` — `skills/status/scripts/avancement.py:158` — What the KB lacks to prove a sprint stage done. `hooks/gate.js` runs
- `coverage` — `skills/status/scripts/avancement.py:145` — Criteria of a ticket proved by its technical plan (`[CAn]`) or a recette (`CAn — Oui`).
- `criteria` — `skills/status/scripts/avancement.py:140`
- `field` — `skills/status/scripts/avancement.py:135`
- `first_open` — `skills/status/scripts/avancement.py:225`
- `load` — `skills/status/scripts/avancement.py:49` — {section title: [[stage, status, updated, detail], …]}, resume point.
- `locate` — `skills/status/scripts/avancement.py:96`
- `main` — `skills/status/scripts/avancement.py:253`
- `next_open` — `skills/status/scripts/avancement.py:235`
- `now` — `skills/status/scripts/avancement.py:45`
- `read` — `skills/status/scripts/avancement.py:112`
- `save` — `skills/status/scripts/avancement.py:83`
- `section` — `skills/status/scripts/avancement.py:119` — Body of the last `## <heading>` (up to the next level-2 heading).
- `show` — `skills/status/scripts/avancement.py:243`
- `add` — `skills/status/scripts/usage_report.py:102`
- `blocks` — `skills/status/scripts/usage_report.py:85`
- `context` — `skills/status/scripts/usage_report.py:48`
- `count_reads` — `skills/status/scripts/usage_report.py:306`
- `delivered` — `skills/status/scripts/usage_report.py:211` — Tickets with a commit carrying `Hosa-Ticket: <slug>` (the `develop` gate) in the period.
- `earlier_costs` — `skills/status/scripts/usage_report.py:242` — `Coût par ticket` of the other sprints' `## Mesures`.
- `fmt` — `skills/status/scripts/usage_report.py:316`
- `images` — `skills/status/scripts/usage_report.py:52`
- `lines` — `skills/status/scripts/usage_report.py:76`
- `main` — `skills/status/scripts/usage_report.py:329`
- `measures` — `skills/status/scripts/usage_report.py:252` — `## Mesures` of a sprint: the figures, then what crossed a threshold, as proposals.
- `meta_type` — `skills/status/scripts/usage_report.py:298`
- `outside` — `skills/status/scripts/usage_report.py:66`
- `project_dir` — `skills/status/scripts/usage_report.py:71`
- `scan` — `skills/status/scripts/usage_report.py:113`
- `scan.measure` — `skills/status/scripts/usage_report.py:126`
- `sprint_file` — `skills/status/scripts/usage_report.py:223`
- `sprint_period` — `skills/status/scripts/usage_report.py:227` — From the sprint's creation day (`generated.at`) to its merge commit's day, and its tickets.
- `table` — `skills/status/scripts/usage_report.py:320`
- `usage_once` — `skills/status/scripts/usage_report.py:90` — The entry's usage, or {} if its message was already counted: Claude Code
- `usd` — `skills/status/scripts/usage_report.py:57`
- `write_section` — `skills/status/scripts/usage_report.py:289` — Replace the file's `## Mesures` section (heading to the next level-2 heading), or append it.

## Tickets et exigences

Aucun.
