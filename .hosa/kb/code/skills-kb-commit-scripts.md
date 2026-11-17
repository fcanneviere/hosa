---
type: Module
title: skills/kb-commit/scripts
description: '!/usr/bin/env python3'
resource: skills/kb-commit/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-17T05:33:18Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/kb-commit/scripts/kb_branch.py` | !/usr/bin/env python3 |

## Symboles publics

- `commit` — `skills/kb-commit/scripts/kb_branch.py:246`
- `ensure` — `skills/kb-commit/scripts/kb_branch.py:224`
- `git` — `skills/kb-commit/scripts/kb_branch.py:39`
- `has_branch` — `skills/kb-commit/scripts/kb_branch.py:47`
- `identity` — `skills/kb-commit/scripts/kb_branch.py:115`
- `ignore_hosa` — `skills/kb-commit/scripts/kb_branch.py:68` — Make the code branch's .gitignore cover `.hosa/` and the agents' local memory. True if it changed.
- `init` — `skills/kb-commit/scripts/kb_branch.py:155`
- `is_kb_worktree` — `skills/kb-commit/scripts/kb_branch.py:51`
- `main` — `skills/kb-commit/scripts/kb_branch.py:267`
- `memoire` — `skills/kb-commit/scripts/kb_branch.py:80` — Move agent memories written under the old `project` scope to the `local` one.
- `migrate` — `skills/kb-commit/scripts/kb_branch.py:176`
- `orphan_commit_from` — `skills/kb-commit/scripts/kb_branch.py:143` — Commit `folder`'s content (as the tree root) as a parentless commit, without touching any index.
- `same_tree` — `skills/kb-commit/scripts/kb_branch.py:120`
- `status` — `skills/kb-commit/scripts/kb_branch.py:127`
- `tracked_kb` — `skills/kb-commit/scripts/kb_branch.py:57`

## Tickets et exigences

Aucun.
