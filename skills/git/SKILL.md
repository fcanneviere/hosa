---
name: git
description: Use to open a dedicated branch/worktree for a sprint when it starts, or to merge it locally back into the managed project once every ticket has a passing QA record. Dispatches `hosa-git`. Companion transversal skill, with dedicated hand-off points in `sprint` (start) and `validation` (finish).
---

# Git

Drives the managed project's git repository lifecycle for one `Sprint` at a time: opening its branch/worktree at the start, merging it locally once its QA is clean.

## Flow

```
Détermine le mode depuis la requête (démarrage / fusion / ad hoc)
        ↓
Sprint identifié (Mode 1/2) ou requête libre (Mode 3)
        ↓
Dispatch hosa-git dans ce mode
        ↓
Rapporte le résultat (branche/worktree ouverts, fusion/blocage,
ou résultat de la requête ad hoc)
```

## Trigger

Manual: `/git demarre <slug>`, `/git termine <slug>`, or any other git request against the managed project (`/git <requête libre>`) for Mode 3. Auto: "démarre le sprint X", "commence le sprint X" → Mode 1 ; "termine le sprint X", "fusionne le sprint X", "merge le sprint X" → Mode 2 ; any other git request against the managed project's repo (statut, nettoyage d'un worktree orphelin, annuler un commit...) → Mode 3.

---

## Step 1: Determine the Mode and Target

From the request, determine whether this is a start (Mode 1), a finish (Mode 2), or an ad hoc git request (Mode 3). Modes 1 and 2 need a `Sprint` slug — if it's unclear which one, ask rather than guess. Mode 3 doesn't require one; it can be any other git request against the managed project's repo.

## Step 2: Dispatch `hosa-git`

Dispatch `hosa-git` in the determined mode — with the sprint slug for Mode 1/2, or with the request as given for Mode 3. It reads `kb/sprints/<slug>.md` and the relevant KB when a sprint is involved, performs the worktree creation or QA-gated merge (or handles the ad hoc request directly), and reports back.

If it returns:
- **`## Installation nécessaire`** — dispatch `hosa-infra` (Mode 2) with it, then redispatch `hosa-git` once confirmed.
- **`## Open Questions`** with a mode ambiguity — ask the user and redispatch.
- **`## Open Questions`** with a ticket `Accepté avec réserves` — present the reservations and ask the user (or `hosa-product-owner`) to explicitly accept the risk; only redispatch `hosa-git` to proceed with the merge once they do.

## Commits

This skill dispatches the one Hosa agent allowed to commit (`hosa-git`, Mode 2/3 only) — always under the user's own git identity, never a co-author.

## Output

```
[hosa-git's Output Format for whichever mode ran]
```
