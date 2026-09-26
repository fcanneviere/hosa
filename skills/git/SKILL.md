---
name: git
description: Use to open a dedicated branch/worktree for a sprint when it starts, or to merge it locally back into the managed project once every ticket has a passing QA record. Dispatches `hosa-git`. Companion transversal skill, with dedicated hand-off points in `sprint` (start) and `qa` (finish).
---

# Git

Drives the managed project's git repository lifecycle for one `Sprint` at a time: opening its branch/worktree at the start, merging it locally once its QA is clean.

## Flow

```
Lit kb/sprints/<slug>.md
        ↓
Détermine le mode depuis la requête (démarrage / fusion / ad hoc)
        ↓
Dispatch hosa-git dans ce mode
        ↓
Rapporte le résultat (branche/worktree ouverts, ou fusion/blocage)
```

## Trigger

Manual: `/git demarre <slug>`, `/git termine <slug>`. Auto: "démarre le sprint X", "commence le sprint X" → Mode 1 ; "termine le sprint X", "fusionne le sprint X", "merge le sprint X" → Mode 2.

---

## Step 1: Determine the Mode and Sprint

From the request, determine whether this is a start (Mode 1), a finish (Mode 2), or an ad hoc git request (Mode 3), and which `Sprint` slug it targets. If either is unclear, ask rather than guess.

## Step 2: Dispatch `hosa-git`

Dispatch `hosa-git` in the determined mode with the sprint slug. It reads `kb/sprints/<slug>.md` and the relevant KB, performs the worktree creation or QA-gated merge (or the ad hoc request), and reports back.

## Commits

This skill dispatches the one Hosa agent allowed to commit (`hosa-git`, Mode 2/3 only) — always under the user's own git identity, never a co-author.

## Output

```
[hosa-git's Output Format for whichever mode ran]
```
