---
type: Module
title: skills/sprint/scripts
description: '!/usr/bin/env python3'
resource: skills/sprint/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-15T14:36:13Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/sprint/scripts/graphe_tickets.py` | !/usr/bin/env python3 |

## Symboles publics

- `build_order` — `skills/sprint/scripts/graphe_tickets.py:83` — Topological order of `slugs`, each after its dependencies, the higher priority first among the free ones.
- `compose` — `skills/sprint/scripts/graphe_tickets.py:169` — The sprint toward `objectif`: its whole path when it fits the bounds; otherwise the milestone — the ticket of
- `demo_cost` — `skills/sprint/scripts/graphe_tickets.py:138`
- `eligible` — `skills/sprint/scripts/graphe_tickets.py:115`
- `fits` — `skills/sprint/scripts/graphe_tickets.py:142`
- `further` — `skills/sprint/scripts/graphe_tickets.py:151` — The furthest ticket on the way past `objectif` — one that waits for it, directly or not — whose whole path
- `has_screen` — `skills/sprint/scripts/graphe_tickets.py:56` — A ticket the user plays at the demo: its interface placement names a screen (`Écran / route`, not `aucun`).
- `load` — `skills/sprint/scripts/graphe_tickets.py:63` — Every ticket; those of the sprint `recompose` are free again (loop `qa-plan` → `sprint`).
- `main` — `skills/sprint/scripts/graphe_tickets.py:421`
- `obstacles` — `skills/sprint/scripts/graphe_tickets.py:125`
- `order_key` — `skills/sprint/scripts/graphe_tickets.py:79`
- `path_to` — `skills/sprint/scripts/graphe_tickets.py:96` — (the tickets still to build for `slug`, in build order; the dependencies no ticket file holds).
- `points` — `skills/sprint/scripts/graphe_tickets.py:51` — Points as `backlog` writes them; an older S/M/L counts 1/2/3, none 2 (`sprint-planner`).
- `read_bornes` — `skills/sprint/scripts/graphe_tickets.py:318` — The bounds validated with the milestones (`## Bornes`), the defaults otherwise.
- `read_jalons` — `skills/sprint/scripts/graphe_tickets.py:325` — The milestones the user validated, in order: `## Jalons` of `kb/project/feuille-de-route.md`.
- `ready` — `skills/sprint/scripts/graphe_tickets.py:119`
- `report` — `skills/sprint/scripts/graphe_tickets.py:391`
- `roadmap` — `skills/sprint/scripts/graphe_tickets.py:229` — Every sprint to come, computed (list scheduling on the dependency graph):
- `roadmap.open_sprint` — `skills/sprint/scripts/graphe_tickets.py:244`
- `roadmap.todo_path` — `skills/sprint/scripts/graphe_tickets.py:248`
- `roadmap_report` — `skills/sprint/scripts/graphe_tickets.py:371`
- `single_fixes` — `skills/sprint/scripts/graphe_tickets.py:365` — The checker lines of the tickets to complete that are their own decision, verbatim.
- `ticket_check` — `skills/sprint/scripts/graphe_tickets.py:43`
- `with_tolerance` — `skills/sprint/scripts/graphe_tickets.py:146` — A bound widened by `tolerance` %, at least one more as soon as the tolerance isn't 0: 20 → 21, 15 → 16.
- `write_roadmap` — `skills/sprint/scripts/graphe_tickets.py:334` — Rewrites the computed part of the roadmap. `## Jalons` stays as the user validated it, or is written from

## Tickets et exigences

Aucun.
