---
type: Module
title: skills/redaction/scripts
description: '!/usr/bin/env python3'
resource: skills/redaction/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-12T23:50:47Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/redaction/scripts/cdc.py` | !/usr/bin/env python3 |

## Symboles publics

- `Concept` — `skills/redaction/scripts/cdc.py:116`
- `anomalies` — `skills/redaction/scripts/cdc.py:412` — The `- A<n> [passe, gravité, origine] — …` lines of `kb/cdc/relecture.md` § Anomalies.
- `as_list` — `skills/redaction/scripts/cdc.py:86`
- `assemble` — `skills/redaction/scripts/cdc.py:540`
- `assemble.isec` — `skills/redaction/scripts/cdc.py:551`
- `bullets` — `skills/redaction/scripts/cdc.py:193` — Top-level `- ` lines that say something.
- `demote` — `skills/redaction/scripts/cdc.py:478`
- `empty` — `skills/redaction/scripts/cdc.py:111`
- `fiche` — `skills/redaction/scripts/cdc.py:521`
- `first_line` — `skills/redaction/scripts/cdc.py:491`
- `get` — `skills/redaction/scripts/cdc.py:104`
- `holes` — `skills/redaction/scripts/cdc.py:258`
- `holes.hole` — `skills/redaction/scripts/cdc.py:260`
- `indicateurs` — `skills/redaction/scripts/cdc.py:217` — Each indicator in force of `## Indicateurs`: {id, texte} — its whole line, sub-bullets included.
- `link` — `skills/redaction/scripts/cdc.py:482`
- `load` — `skills/redaction/scripts/cdc.py:140`
- `load.concepts` — `skills/redaction/scripts/cdc.py:142`
- `load.one` — `skills/redaction/scripts/cdc.py:151`
- `lot_key` — `skills/redaction/scripts/cdc.py:499`
- `main` — `skills/redaction/scripts/cdc.py:663`
- `mesure` — `skills/redaction/scripts/cdc.py:451` — One row per pass: how many anomalies, how grave, where they came from — the loop above the loop.
- `numerote` — `skills/redaction/scripts/cdc.py:232` — Give each rule and error case without an id the next free one. An id already there never moves.
- `objectives` — `skills/redaction/scripts/cdc.py:170` — Rows of the `## Objectifs mesurables` table: Id \| Objectif \| Indicateur \| Cible \| Mesure.
- `ordered` — `skills/redaction/scripts/cdc.py:504` — A process comes after the ones its `## Déclencheur` links to.
- `ordered.visit` — `skills/redaction/scripts/cdc.py:509`
- `plain` — `skills/redaction/scripts/cdc.py:486` — Links reduced to their label, for table cells.
- `relink` — `skills/redaction/scripts/cdc.py:470` — Rewrite relative .md links written from `src`'s folder so they work from `dest`'s.
- `relink.sub` — `skills/redaction/scripts/cdc.py:472`
- `revue` — `skills/redaction/scripts/cdc.py:431` — What holds the stage: a tag missing or wrong, a rule of gravity broken, a `bloquante` still open.
- `rule_ids` — `skills/redaction/scripts/cdc.py:211` — The ids a ticket can cite: every numbered rule and error case still in force, in the fiche's order.
- `rule_lines` — `skills/redaction/scripts/cdc.py:198` — (line index, `RG` or `CE`, its id or '') of each rule and error case of a fiche:
- `section_map` — `skills/redaction/scripts/cdc.py:90` — `## Title` → its text, in order; the text before the first heading under ''.
- `split` — `skills/redaction/scripts/cdc.py:70`
- `table_rows` — `skills/redaction/scripts/cdc.py:250`
- `transitions` — `skills/redaction/scripts/cdc.py:183` — `- a → b : comment — exigence` lines of a `### Cycle de vie`.

## Tickets et exigences

Aucun.
