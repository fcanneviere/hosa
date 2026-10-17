---
type: Module
title: skills/kb-commit/scripts
description: '!/usr/bin/env python3'
resource: skills/kb-commit/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-10-17T17:02:29Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/kb-commit/scripts/kb_branch.py` | !/usr/bin/env python3 |

## Symboles publics

- `commit` — `skills/kb-commit/scripts/kb_branch.py:243`
- `ensure` — `skills/kb-commit/scripts/kb_branch.py:221`
- `git` — `skills/kb-commit/scripts/kb_branch.py:36`
- `has_branch` — `skills/kb-commit/scripts/kb_branch.py:44`
- `identity` — `skills/kb-commit/scripts/kb_branch.py:112`
- `ignore_hosa` — `skills/kb-commit/scripts/kb_branch.py:65` — Make the code branch's .gitignore cover `.hosa/` and the agents' local memory. True if it changed.
- `init` — `skills/kb-commit/scripts/kb_branch.py:152`
- `is_kb_worktree` — `skills/kb-commit/scripts/kb_branch.py:48`
- `main` — `skills/kb-commit/scripts/kb_branch.py:259`
- `memoire` — `skills/kb-commit/scripts/kb_branch.py:77` — Move agent memories written under the old `project` scope to the `local` one.
- `migrate` — `skills/kb-commit/scripts/kb_branch.py:173`
- `orphan_commit_from` — `skills/kb-commit/scripts/kb_branch.py:140` — Commit `folder`'s content (as the tree root) as a parentless commit, without touching any index.
- `same_tree` — `skills/kb-commit/scripts/kb_branch.py:117`
- `status` — `skills/kb-commit/scripts/kb_branch.py:124`
- `tracked_kb` — `skills/kb-commit/scripts/kb_branch.py:54`

## Tickets et exigences

Aucun.
