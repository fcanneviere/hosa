---
name: git
description: Use for the managed project's git lifecycle — initialize the repository, commit at pipeline checkpoints, open a sprint's branch/worktree, promote a developed sprint to the `test` branch for QA, and merge `test` into the main branch once every ticket has a passing QA record. Dispatches `hosa-git`. Companion transversal skill, with hand-off points in `hosa` (init), every skill's end (checkpoint), `sprint` (start), `develop` (promote) and `validation` (release).
---

# Git

Drives the managed project's git repository from its first file: `sprint/<slug>` for development, `test` for QA in Docker, the main branch for what's validated. See `agents/git.md` "Branch Model".

## Flow

```
Détermine le mode depuis la requête
  0 init · 1 démarrage · 2 passage en test · 3 checkpoint/ad hoc · 4 fusion
        ↓
Sprint identifié (Mode 1/2/4) ou requête libre (Mode 0/3)
        ↓
Dispatch hosa-git dans ce mode
        ↓
Rapporte le résultat
```

## Trigger

Manual: `/git demarre <slug>`, `/git test <slug>`, `/git termine <slug>`, or any other git request against the managed project (`/git <requête libre>`) for Mode 3. Auto: "démarre le sprint X" → Mode 1 ; "pousse le sprint X en test" → Mode 2 ; "termine le sprint X", "fusionne le sprint X", "merge le sprint X" → Mode 4 ; any other git request against the managed project's repo (statut, nettoyage d'un worktree orphelin, annuler un commit...) → Mode 3. Modes 0 and 3-checkpoint are dispatched by other skills, not by the user.

---

## Step 1: Determine the Mode and Target

From the request, determine the mode. Modes 1, 2 and 4 need a `Sprint` slug — if it's unclear which one, ask rather than guess.

## Step 2: Dispatch `hosa-git`

Dispatch `hosa-git` in the determined mode — with the sprint slug for Mode 1/2/4, or with the request as given for Mode 0/3.

If it returns:
- **`## Installation nécessaire`** — dispatch `hosa-infra` (Mode 2) with it, then redispatch `hosa-git` once confirmed.
- **`## Open Questions`** with a mode ambiguity — ask the user and redispatch.
- **`## Open Questions`** with a ticket `Accepté avec réserves` — present the reservations and ask the user (or `hosa-product-owner`) to explicitly accept the risk; only redispatch `hosa-git` to proceed with the merge once they do.

## Step 3: Hand-off

- Mode 2 succeeded → invoke `qa` on the sprint right away. Tests are mandatory, never offered as an option.
- Mode 4 succeeded → propose `bilan-sprint`.

## Commits

This skill dispatches the one Hosa agent allowed to commit outside `develop`/`debug` (`hosa-git`) — always under the user's own git identity, never a co-author.

## Output

```
[hosa-git's Output Format for whichever mode ran]
```
