---
type: Module
title: skills/sprint/scripts
description: '!/usr/bin/env python3'
resource: skills/sprint/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-17T18:15:17Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/sprint/scripts/graphe_tickets.py` | !/usr/bin/env python3 |

## Symboles publics

- `build_order` — `skills/sprint/scripts/graphe_tickets.py:93` — Topological order of `slugs`, each after its dependencies, the higher priority first among the free ones.
- `compose` — `skills/sprint/scripts/graphe_tickets.py:179` — The sprint toward `objectif`: its whole path when it fits the bounds; otherwise the milestone — the ticket of
- `demo_cost` — `skills/sprint/scripts/graphe_tickets.py:148`
- `eligible` — `skills/sprint/scripts/graphe_tickets.py:125`
- `fits` — `skills/sprint/scripts/graphe_tickets.py:152`
- `further` — `skills/sprint/scripts/graphe_tickets.py:161` — The furthest ticket on the way past `objectif` — one that waits for it, directly or not — whose whole path
- `has_screen` — `skills/sprint/scripts/graphe_tickets.py:59` — A ticket the user plays at the demo: its interface placement names a screen (`Écran / route`, not `aucun`).
- `load` — `skills/sprint/scripts/graphe_tickets.py:70` — Every ticket; those of the sprint `recompose` are free again (loop `qa-plan` → `sprint`).
- `main` — `skills/sprint/scripts/graphe_tickets.py:453`
- `objectives` — `skills/sprint/scripts/graphe_tickets.py:331` — The ids of the measurable objectives (`## Objectifs mesurables` of kb/project/identity.md): O1, O2…
- `obstacles` — `skills/sprint/scripts/graphe_tickets.py:135`
- `order_key` — `skills/sprint/scripts/graphe_tickets.py:89`
- `path_to` — `skills/sprint/scripts/graphe_tickets.py:106` — (the tickets still to build for `slug`, in build order; the dependencies no ticket file holds).
- `points` — `skills/sprint/scripts/graphe_tickets.py:54` — Points as `backlog` writes them; an older S/M/L counts 1/2/3, none 2 (`sprint-planner`).
- `read_bornes` — `skills/sprint/scripts/graphe_tickets.py:342` — The bounds validated with the milestones (`## Bornes`), the defaults otherwise.
- `read_jalons` — `skills/sprint/scripts/graphe_tickets.py:349` — The milestones the user validated, in order: `## Jalons` of `kb/project/feuille-de-route.md`.
- `ready` — `skills/sprint/scripts/graphe_tickets.py:129`
- `report` — `skills/sprint/scripts/graphe_tickets.py:423`
- `roadmap` — `skills/sprint/scripts/graphe_tickets.py:239` — Every sprint to come, computed (list scheduling on the dependency graph):
- `roadmap.open_sprint` — `skills/sprint/scripts/graphe_tickets.py:254`
- `roadmap.todo_path` — `skills/sprint/scripts/graphe_tickets.py:258`
- `roadmap_report` — `skills/sprint/scripts/graphe_tickets.py:399`
- `single_fixes` — `skills/sprint/scripts/graphe_tickets.py:393` — The checker lines of the tickets to complete that are their own decision, verbatim.
- `ticket_check` — `skills/sprint/scripts/graphe_tickets.py:46`
- `with_tolerance` — `skills/sprint/scripts/graphe_tickets.py:156` — A bound widened by `tolerance` %, at least one more as soon as the tolerance isn't 0: 20 → 21, 15 → 16.
- `write_roadmap` — `skills/sprint/scripts/graphe_tickets.py:358` — Rewrites the computed part of the roadmap. `## Jalons` stays as the user validated it, or is written from

## Tickets et exigences

Aucun.
