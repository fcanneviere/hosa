---
type: Module
title: skills/infra/scripts
description: '!/usr/bin/env python3'
resource: skills/infra/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-10-24T15:18:04Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/infra/scripts/docker_check.py` | !/usr/bin/env python3 |

## Symboles publics

- `docker` — `skills/infra/scripts/docker_check.py:95`
- `inside` — `skills/infra/scripts/docker_check.py:42`
- `main` — `skills/infra/scripts/docker_check.py:102`
- `norm` — `skills/infra/scripts/docker_check.py:35`
- `orphans` — `skills/infra/scripts/docker_check.py:84` — `projects`: [{"Name":…, "ConfigFiles":…}] as `docker compose ls -a --format json` gives.
- `problems` — `skills/infra/scripts/docker_check.py:53` — Pure check on `docker inspect` output, so it can be tested without Docker.
- `root_of` — `skills/infra/scripts/docker_check.py:47`

## Tickets et exigences

Aucun.
