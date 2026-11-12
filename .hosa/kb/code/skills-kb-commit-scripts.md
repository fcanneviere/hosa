---
type: Module
title: skills/kb-commit/scripts
description: '!/usr/bin/env python3'
resource: skills/kb-commit/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-10-19T17:10:14Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/kb-commit/scripts/kb_branch.py` | !/usr/bin/env python3 |

## Symboles publics

- `commit` — `skills/kb-commit/scripts/kb_branch.py:245`
- `ensure` — `skills/kb-commit/scripts/kb_branch.py:223`
- `git` — `skills/kb-commit/scripts/kb_branch.py:38`
- `has_branch` — `skills/kb-commit/scripts/kb_branch.py:46`
- `identity` — `skills/kb-commit/scripts/kb_branch.py:114`
- `ignore_hosa` — `skills/kb-commit/scripts/kb_branch.py:67` — Make the code branch's .gitignore cover `.hosa/` and the agents' local memory. True if it changed.
- `init` — `skills/kb-commit/scripts/kb_branch.py:154`
- `is_kb_worktree` — `skills/kb-commit/scripts/kb_branch.py:50`
- `main` — `skills/kb-commit/scripts/kb_branch.py:261`
- `memoire` — `skills/kb-commit/scripts/kb_branch.py:79` — Move agent memories written under the old `project` scope to the `local` one.
- `migrate` — `skills/kb-commit/scripts/kb_branch.py:175`
- `orphan_commit_from` — `skills/kb-commit/scripts/kb_branch.py:142` — Commit `folder`'s content (as the tree root) as a parentless commit, without touching any index.
- `same_tree` — `skills/kb-commit/scripts/kb_branch.py:119`
- `status` — `skills/kb-commit/scripts/kb_branch.py:126`
- `tracked_kb` — `skills/kb-commit/scripts/kb_branch.py:56`

## Tickets et exigences

Aucun.
