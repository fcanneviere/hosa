---
type: Module
title: skills/infra/scripts
description: '!/usr/bin/env python3'
resource: skills/infra/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-10-17T17:02:29Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/infra/scripts/docker_check.py` | !/usr/bin/env python3 |

## Symboles publics

- `docker` — `skills/infra/scripts/docker_check.py:82`
- `inside` — `skills/infra/scripts/docker_check.py:37`
- `main` — `skills/infra/scripts/docker_check.py:89`
- `norm` — `skills/infra/scripts/docker_check.py:30`
- `orphans` — `skills/infra/scripts/docker_check.py:71` — `projects`: [{"Name":…, "ConfigFiles":…}] as `docker compose ls -a --format json` gives.
- `problems` — `skills/infra/scripts/docker_check.py:48` — Pure check on `docker inspect` output, so it can be tested without Docker.
- `root_of` — `skills/infra/scripts/docker_check.py:42`

## Tickets et exigences

Aucun.
