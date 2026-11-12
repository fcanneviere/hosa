---
type: Module
title: skills/redaction/scripts
description: '!/usr/bin/env python3'
resource: skills/redaction/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-12T18:14:13Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/redaction/scripts/cdc.py` | !/usr/bin/env python3 |

## Symboles publics

- `Concept` — `skills/redaction/scripts/cdc.py:110`
- `anomalies` — `skills/redaction/scripts/cdc.py:386` — The `- A<n> [passe, gravité, origine] — …` lines of `kb/cdc/relecture.md` § Anomalies.
- `as_list` — `skills/redaction/scripts/cdc.py:80`
- `assemble` — `skills/redaction/scripts/cdc.py:514`
- `assemble.isec` — `skills/redaction/scripts/cdc.py:525`
- `bullets` — `skills/redaction/scripts/cdc.py:187` — Top-level `- ` lines that say something.
- `demote` — `skills/redaction/scripts/cdc.py:452`
- `empty` — `skills/redaction/scripts/cdc.py:105`
- `fiche` — `skills/redaction/scripts/cdc.py:495`
- `first_line` — `skills/redaction/scripts/cdc.py:465`
- `get` — `skills/redaction/scripts/cdc.py:98`
- `holes` — `skills/redaction/scripts/cdc.py:237`
- `holes.hole` — `skills/redaction/scripts/cdc.py:239`
- `link` — `skills/redaction/scripts/cdc.py:456`
- `load` — `skills/redaction/scripts/cdc.py:134`
- `load.concepts` — `skills/redaction/scripts/cdc.py:136`
- `load.one` — `skills/redaction/scripts/cdc.py:145`
- `lot_key` — `skills/redaction/scripts/cdc.py:473`
- `main` — `skills/redaction/scripts/cdc.py:637`
- `mesure` — `skills/redaction/scripts/cdc.py:425` — One row per pass: how many anomalies, how grave, where they came from — the loop above the loop.
- `numerote` — `skills/redaction/scripts/cdc.py:211` — Give each rule and error case without an id the next free one. An id already there never moves.
- `objectives` — `skills/redaction/scripts/cdc.py:164` — Rows of the `## Objectifs mesurables` table: Id \| Objectif \| Indicateur \| Cible \| Mesure.
- `ordered` — `skills/redaction/scripts/cdc.py:478` — A process comes after the ones its `## Déclencheur` links to.
- `ordered.visit` — `skills/redaction/scripts/cdc.py:483`
- `plain` — `skills/redaction/scripts/cdc.py:460` — Links reduced to their label, for table cells.
- `relink` — `skills/redaction/scripts/cdc.py:444` — Rewrite relative .md links written from `src`'s folder so they work from `dest`'s.
- `relink.sub` — `skills/redaction/scripts/cdc.py:446`
- `revue` — `skills/redaction/scripts/cdc.py:405` — What holds the stage: a tag missing or wrong, a rule of gravity broken, a `bloquante` still open.
- `rule_ids` — `skills/redaction/scripts/cdc.py:205` — The ids a ticket can cite: every numbered rule and error case still in force, in the fiche's order.
- `rule_lines` — `skills/redaction/scripts/cdc.py:192` — (line index, `RG` or `CE`, its id or '') of each rule and error case of a fiche:
- `section_map` — `skills/redaction/scripts/cdc.py:84` — `## Title` → its text, in order; the text before the first heading under ''.
- `split` — `skills/redaction/scripts/cdc.py:64`
- `table_rows` — `skills/redaction/scripts/cdc.py:229`
- `transitions` — `skills/redaction/scripts/cdc.py:177` — `- a → b : comment — exigence` lines of a `### Cycle de vie`.

## Tickets et exigences

Aucun.
