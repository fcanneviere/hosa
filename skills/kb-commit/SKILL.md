---
name: kb-commit
description: Use to commit accumulated `.hosa/kb/` changes into a dedicated commit, scoped to just that subtree, inside the managed project's own git history. Every Hosa pipeline skill writes the KB but never commits it ("No Commits" is a per-skill rule, not a statement that the KB stays uncommitted forever) — without running this, the OKF traceability (`generated`/`verified`/`log.md`) has no matching commit trail. Companion skill, usable anytime, safe to re-run (no-op if the KB has no pending changes).
---

# KB Commit

Commits whatever has piled up under `.hosa/kb/` since the last KB commit — inside the managed project's own repository (the KB lives there, per `using-hosa`'s KB Location rule), but as its own dedicated commit, kept separate from the rest of that repo's commits (`hosa-git`'s job) and from Hosa's own plugin development commits. One commit, KB paths only.

## Repository Targeting

Runs from the managed project's root — the parent of the resolved `.hosa/` directory — never from Hosa's own plugin checkout, even if this session started there. Same targeting discipline as `hosa-git`.

## Flow

```
Résout .hosa/kb/ (using-hosa) → se place à la racine du projet géré
        ↓
git status --short .hosa/kb/
        ↓ rien                              ↓ des changements
Rapporte "rien à committer"            Résume les bundles touchés
                                              ↓
                                        Confirme user.name/user.email
                                              ↓
                                        git add .hosa/kb/ (rien d'autre)
                                              ↓
                                        git commit (message résumant les
                                        bundles, nom de l'utilisateur seul)
```

## Trigger

Manual: `/kb-commit`. Auto: never — this skill doesn't fire on natural-language triggers, since "commit" alone is too ambiguous between the managed project, the KB, and Hosa's own tooling. Proposed as a Suite step by pipeline skills once a bundle write lands (`hosa`, `backlog`, `sprint`, `validation`, `bilan-sprint`, `qa`, `qualite`, `changement`), but only run when the user confirms.

---

## Step 1: Scope the Diff

```bash
git status --short .hosa/kb/
```

Nothing under `.hosa/kb/` → report "Rien à committer dans la KB." and stop. Anything else in the working tree (skill/agent edits, app code) is out of scope — never staged by this skill.

## Step 2: Confirm Identity

Same as every Hosa commit: check `git config user.name` and `git config user.email` first. Never add `Co-Authored-By` or any additional author — zero exceptions, per the Hosa core rule.

## Step 3: Stage and Commit

```bash
git add .hosa/kb/
git commit -m "kb: <résumé des bundles touchés, ex: update tickets, sprints>"
```

One commit for the whole pending KB diff — don't split it bundle by bundle unless the user asks for that granularity.

## No Other Commits

This skill never touches anything outside `.hosa/kb/` — no skill/agent file, no app code, no managed-project file. Those follow their own commit path (`hosa-git` for the managed project, a plain `git commit` for Hosa's own tooling).

## Output

```
## KB committée
- Bundles touchés : [liste, ex: tickets, sprints]
- Commit : <message>

[Si rien à committer : "Rien à committer dans la KB."]
```
