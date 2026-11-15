---
type: Module
title: skills/sprint/scripts
description: '!/usr/bin/env python3'
resource: skills/sprint/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-15T10:11:12Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/sprint/scripts/graphe_tickets.py` | !/usr/bin/env python3 |

## Symboles publics

- `build_order` — `skills/sprint/scripts/graphe_tickets.py:74` — Topological order of `slugs`, each after its dependencies, the higher priority first among the free ones.
- `compose` — `skills/sprint/scripts/graphe_tickets.py:137` — The sprint toward `objectif`: its whole path when it fits the bounds; otherwise the milestone — the ticket of
- `demo_cost` — `skills/sprint/scripts/graphe_tickets.py:129`
- `eligible` — `skills/sprint/scripts/graphe_tickets.py:106`
- `fits` — `skills/sprint/scripts/graphe_tickets.py:133`
- `has_screen` — `skills/sprint/scripts/graphe_tickets.py:47` — A ticket the user plays at the demo: its interface placement names a screen (`Écran / route`, not `aucun`).
- `load` — `skills/sprint/scripts/graphe_tickets.py:54` — Every ticket; those of the sprint `recompose` are free again (loop `qa-plan` → `sprint`).
- `main` — `skills/sprint/scripts/graphe_tickets.py:205`
- `obstacles` — `skills/sprint/scripts/graphe_tickets.py:116`
- `order_key` — `skills/sprint/scripts/graphe_tickets.py:70`
- `path_to` — `skills/sprint/scripts/graphe_tickets.py:87` — (the tickets still to build for `slug`, in build order; the dependencies no ticket file holds).
- `points` — `skills/sprint/scripts/graphe_tickets.py:42` — Points as `backlog` writes them; an older S/M/L counts 1/2/3, none 2 (`sprint-planner`).
- `ready` — `skills/sprint/scripts/graphe_tickets.py:110`
- `report` — `skills/sprint/scripts/graphe_tickets.py:183`
- `ticket_check` — `skills/sprint/scripts/graphe_tickets.py:34`

## Tickets et exigences

Aucun.
