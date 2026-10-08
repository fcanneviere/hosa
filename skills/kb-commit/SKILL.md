---
name: kb-commit
description: "Use to commit the KB's pending changes on its own `hosa-kb` branch (linked to the code commit), or to migrate a KB still tracked in the code branches. Triggers: `/kb-commit`, `/kb-commit migrer`; proposed after KB writes."
---

# KB Commit

Commits whatever has piled up under `.hosa/kb/` since the last KB commit — inside the managed project's own repository (the KB lives there, per `using-hosa`'s KB Location rule), but as its own dedicated commit, kept separate from the rest of that repo's commits (`hosa-git`'s job) and from Hosa's own plugin development commits. One commit, KB paths only.

## Repository Targeting

Runs on the managed project's root — the parent of the resolved `.hosa/` — never on Hosa's own plugin checkout. The KB lives on its own orphan branch `hosa-kb`, checked out at `<root>/.hosa/kb` (`using-hosa`, KB location): its commits never land on a code branch.

## Flow

```
kb_branch.py status <root>
        ↓ KB encore suivie dans les branches du code → Migration
          (plan montré, --yes sur accord de l'utilisateur)
        ↓ branche présente mais pas extraite → ensure
        ↓ en place
Résume les bundles touchés (git -C .hosa/kb status --short)
        ↓ rien → "Rien à committer dans la KB."
kb_branch.py commit <root> -m "kb: <bundles touchés>"
(identité de l'utilisateur seule, + Hosa-Code-Commit)
```

## Trigger

Manual: `/kb-commit`, `/kb-commit migrer`. Auto: never on natural language alone ("commit" is too ambiguous). Proposed as a Suite step by pipeline skills once a bundle write lands (`hosa`, `backlog`, `sprint`, `validation`, `bilan-sprint`, `qa`, `qualite`, `changement`) — run only when the user confirms.

---

## Step 1: Where the KB Lives

```bash
<python> "${CLAUDE_PLUGIN_ROOT}/skills/kb-commit/scripts/kb_branch.py" status <root>
```

- **In place** → Step 2.
- **Branch present, not checked out** (a fresh clone) → `ensure <root>`, then Step 2.
- **Still tracked in the code branches** (a project started before this layout) → **Migration** below, then Step 2.

## Step 2: Commit

`git -C <root>/.hosa/kb status --short` → nothing → "Rien à committer dans la KB." Otherwise summarize the bundles touched, then:

```bash
<python> "${CLAUDE_PLUGIN_ROOT}/skills/kb-commit/scripts/kb_branch.py" commit <root> -m "kb: <résumé des bundles touchés, ex: update tickets, sprints>"
```

It checks `user.name`/`user.email` first and commits under the user's identity only — never `Co-Authored-By`, never another author. It adds `Hosa-Code-Commit: <sha>`, the code commit the KB was written against. One commit for the whole pending diff unless the user asks for finer grain.

## Migration (once per project)

Run `migrate <root>` without `--yes` and show the user its plan: create `hosa-kb` with the KB's current content (uncommitted changes included), untrack `.hosa/kb` and ignore `.hosa/` in the current code branch (one commit, the user's identity), replace the folder by the branch's checkout after a byte-for-byte check. It refuses while a sprint worktree is open — finish the sprint first. On the user's yes, run it with `--yes`. Nothing is deleted before the check passes; on any failure the original folder is restored.

## Agent Memories (once per project)

Agents used to keep their memory under `.claude/agent-memory/`, inside the code repository. `kb_branch.py memoire <root>` shows the plan, then with `--yes` moves the 12 agents that keep a memory to `.claude/agent-memory-local/` (ignored by git), archives the others' under `_archive/` (their facts are in the KB), and untracks the old folder if it was committed. Nothing is deleted.

## No Other Commits

This skill only commits on `hosa-kb`, plus the migration's single `.gitignore`/untrack commit. Code commits are `develop`'s and `hosa-git`'s; Hosa's own tooling is committed separately.

## Output

```
## KB committée
- Bundles touchés : [liste] — Commit : <sha court> sur hosa-kb (code : <sha>)
[Ou : "Rien à committer dans la KB." / "KB migrée sur la branche hosa-kb, contenu vérifié."]
```
