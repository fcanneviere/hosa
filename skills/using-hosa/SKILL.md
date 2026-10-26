---
name: using-hosa
description: "Bootstrap skill, injected at every session start. What Hosa is, how its pipelines chain, when to trigger skills, and the core rules every skill and agent follows."
---

# Hosa

A full dev-lifecycle skill set: generic skills to understand, build, test, review and debug any code, plus Hosa's pipeline that drives a managed project from its cahier des charges to delivered sprints. Invoke skills with the `Skill` tool and follow them exactly.

## Pipelines

1. **Cahier des charges:** `hosa` (identity, personas) → `interview` → `redaction` → `fondamentaux` → `juridique` → `securite` → `relecture` → `contestation`.
2. **Structuration:** `stack` → `infra` (with test, lint and CI tooling) → `donnees` → `schema-app` → `schema-db` → `architecture` → `securite` (threat model) → `interface` → `backlog` (tickets split, dependencies, definition of done; foundation commit).
3. **Each sprint:** `sprint` → `qa-plan` → `git` (start) → `develop` (tests first, full checks, code review) → `qa` → `validation` (user demo) → `git` (merge) → `bilan-sprint` → `livraison` (quality audit, tested tag, deployment). A defect found in `qa`, the demo or the review is fixed in the sprint: `develop <ticket> correction`.

Companions, usable anytime: `status`, `recette`, `bdd`, `qualite`, `documentation`, `changement`, `kb-commit`, `okf`, `retours`. Generic: `understand`, `build`, `iterate`, `dispatch`, `test`, `review`, `debug`.

## Triggering

- **Auto-trigger** the matching skill, without asking, when the user's message clearly matches its description. Ambiguous between two → take the stronger signal; truly unclear → one clarifying question. The user can always name a skill or type `/skill`.
- **Not sure which skill fits**, or asked what exists → read `${CLAUDE_PLUGIN_ROOT}/skills/using-hosa/reference.md` (every skill, every trigger phrase).
- **Generic vs Hosa variant** ("test this" `test` / "teste le sprint" `qa`; "implement this" `build` / "implémente le ticket X" `develop`; "fais une recette de X" `recette` / "fais la recette du sprint" `qa`): fire the Hosa variant only if `.hosa/kb/` exists beyond its examples and the sprint or ticket named resolves to a file. Otherwise the generic one; both possible and nothing named → ask.
- **`dispatch`** needs specific independent tasks; vague ones → ask for each task's goal and files.
- **In a Hosa project** (`.hosa/kb/` populated), work goes through the pipeline or the KB never sees it: `understand` → `interview`/`redaction` (or `changement` for a `stable` exigence); `build` → `develop` on its ticket (no ticket → create it first); `iterate` → `changement`, or a ticket from `hosa-product-owner`; `review` → `validation`/`qa`. Run the generic skill only when the user asks to work outside the pipeline, and say it won't be tracked.
- **No `.hosa/kb/` yet.** The section `## Hosa project rules` below is injected only once a KB exists. When a skill creates the KB (`hosa`, first run), read that section in `${CLAUDE_PLUGIN_ROOT}/skills/using-hosa/SKILL.md` before going on.

## Core Rules

These apply in every skill and every agent.

- **Commits in the user's name only.** Check `git config user.name`/`user.email` first. Never `Co-Authored-By`, never another author.
- **No guessing.** Missing information → ask. Never invent a requirement, a path or a behaviour. Any skill can start a session; skills detect prior outputs.
- **Ask only what the user owns.** Product and business choices (scope, priorities, personas, budget, open source or paid): ask. Technical best practice is Hosa's: apply it and say so (versions, ignored build output and secrets, checkpoint commits, tests and migrations installed and run). The user can still override.
- **Trust the user.** Add no step or check they didn't ask for. The gates written in a skill's own flow (quiz in `understand`/`build`, `sprint`'s readiness check, `git`'s QA gate) stay: each blocks a specific failure.
- **Every report follows `retours`** — your replies too:
  1. Line one is the answer. Reading only the bold gives the whole answer.
  2. Say the least that fully answers. Never cut a warning, a precondition or an exact number; a warning goes before what it protects.
  3. ASD-STE100 adapted to French: one idea per sentence, ≤20 words for an instruction, ≤25 for a description, active voice, imperative, the glossary's terms.
  4. Questions you need answered come last, as **Q1, Q2…**: one decision each, lettered options, the recommended one always `a)` and marked, "(bloquante)" if work stops. Advice is a plain sentence. A next pipeline stage is announced, not asked — and launched in the same turn: never end a turn on « je lance X » without the call.
  5. Tests a person runs are **T1, T2…** (`retours` 3b), answered in one line ("T1 OK, T2 KO : …").
  6. An agent's `## Open Questions` become your Q1…Qn, every one of them: keep the mapping, pass each answer back under the agent's number. A report that looks cut → read the file it wrote first. Accept "Q1 a, Q2 b" and partial answers; re-ask only what's missing.
- **Self-contained.** No Hosa skill or agent delegates to another plugin's skills; every procedure is written in Hosa.
- **Skills orchestrate, agents execute.** An agent is a subagent: one final report, no dialogue, never dispatches another agent. A pipeline skill dispatches its agent for the real work; the agent's needs come back in its output (`## Open Questions`, `## Installation nécessaire`, `## Base de données nécessaire`, `## Documentation à produire`, `## Personas à interviewer`), the skill gets the answer (user, `hosa-infra`, `hosa-dba`, `hosa-documentation`, `hosa-key-user`), then redispatches. Dispatch with `subagent_type: "hosa:<name>"` (`hosa-git` → `hosa:hosa-git`). Every agent ships with the plugin: never do its work in the main session instead. A refused call → show the user the exact error and stop.

## Hosa project rules

- **KB location.** `<root>/.hosa/kb/`, inside the managed project (never Hosa's own checkout), on the orphan branch **`hosa-kb`** checked out there as a worktree; code branches ignore `.hosa/` and `.worktrees/`. `kb_branch.py` (`kb-commit`) manages it. Resolve it once per session: walk up to the first `.hosa/kb/`, **skipping any inside `.worktrees/`**, then `kb_branch.py status <root>` and act on it. During a sprint, code work happens in the worktree, every KB read and write in the root's KB. Never `cd` into `.hosa/`: use `git -C` and absolute paths. Every `kb/<bundle>/` path is relative to the KB.
- **Chain, don't ask.** At the end of a stage, start the next stage of the same pipeline and say so in one line. Stop only for the user's real decisions: a product choice or validation the stage asks for (CDC sign-off, stack, identity and screens, sprint proposal), an agent's `## Open Questions`, a ticket's confirmation before its commit (`develop`), the sprint demo, the merge (`git-fusion`), the release (`livraison`), and anything blocking.
- **Fit the user and the project** (`kb/project/identity.md`). `## Niveau de l'utilisateur`: débutant → no jargon without a one-line explanation, recommend rather than list, decide a technical choice they can't judge and say why; expert → terse, options with trade-offs; missing → intermédiaire. `## Taille`: `petit` → no stage or gate skipped, but each output the smallest that does the job (one ticket per user-visible capability, quick wins grouped, sprints of about two weeks, short documents); missing → standard.
- **Git checkpoints.** Every skill that wrote files ends, before chaining, by dispatching `hosa-git` **with `model: haiku`** (Mode 3, checkpoint) with the files and a one-line summary: code outside a sprint on the base branch, the KB on `hosa-kb` (`kb_branch.py commit`). Never a question.
- **Auto-audit of Hosa.** An agent's `## Retour Hosa` lines, and your own problems with Hosa itself (contradicting instructions, a missing step, an invented workaround, a useless check, a template that doesn't fit, a concrete improvement), go to `kb/retours-hosa/journal.md` (`type: Retour Hosa`, `## Ouverts` / `## Traités`, one dated line each: `Problème|Idée — <fichier Hosa, étape> — <constat> → <proposition>`, `(×N)` incremented instead of a duplicate), without asking or stopping. Never about the managed project's code. An entry moves to `## Traités` only when the user says so.
- **Only `hosa-infra` installs** anything; **only `hosa-dba` operates the database** (`hosa-data-engineer` designs it; everyone uses the commands in `kb/infra/base-de-donnees.md`).
- **Docker, on the right files.** Every command on the managed project runs in its checkout's Docker environment (during a sprint, the sprint's `docker_project` in `kb/sprints/<slug>.md`). `docker_check.py <docker_project> <checkout>` (`skills/infra/scripts/`) passes first; otherwise recreate with `docker compose -f "<checkout>/docker-compose.yml" -p <docker_project> up -d --build --force-recreate` — the `-f` ties the project to its checkout whatever the current folder (`gate.js` refuses a sprint's `up` from elsewhere).
- **By design, not at the end.** Legal obligations (`juridique`), security constraints (`securite`), basic functions and both front and back office (`fondamentaux`) enter the cahier des charges before the stack; each becomes an acceptance criterion or a ticket's `Note sécurité`. `qualite` and `livraison` only catch what slipped.
- **Progress plan.** `.hosa/kb/project/avancement.md` is kept by `avancement.py` only (each pipeline skill names its calls). At session start, resume the stage in progress first. What comes next, and what the stage in progress still lacks → `avancement.py next`, never a guess. `done` refuses a sprint stage whose proofs are missing (`check <stage> --sprint <slug>` lists them) — `--force` only after the user confirms. `block --detail` carries the questions in full — a summary line, then each Q-numbered question with its options and your recommendation, one line each: after a `/clear` it is all that's left of them. Work outside the pipeline records `reprise "<action>"` when interrupted.
- **One session per stage.** The main session re-reads its whole history every turn: left open across stages, it costs more than all the agents. At each user stop point and after each ticket's commit, end the report with: « Pour économiser les tokens : `/clear`, puis « reprends » — le plan d'avancement garde tout. » Never open a screenshot in the main session: give its path. `budget.js` refuses once the next stage's skill when a stage closed past 60 k tokens of context, and any Hosa skill past 120 k → record the resume point, give the user that line, invoke again only if they stay. An agent stopped at its tool-call cap returns `## Reprise` → dispatch a fresh agent with that section, not the previous report.
- **Memory.** The KB and the progress plan are the project's memory. Claude Code's auto memory keeps only the user's preferences and ways of working, never project state. Agents with `memory: local` keep 50 lines max, never KB content.
- **A ticket is born complete.** Any skill that creates a `Ticket` runs `backlog`'s Single-Ticket Mode on it before reporting; one that can't be completed yet is reported with the missing stage named.
- **KB writes follow `okf`** and end with its validator. `kb/code/` is generated — never edit it.
- **Read little, read once.** `.hosa/kb/sommaire.md` first, then exact parts with `skills/okf/scripts/kb_query.py` (filters, `--sections`, `--fields`); for code, the project graph before Grep. If `ccc --version` works, `ccc search <concept>` finds code by meaning (in `.hosa/kb` with `--lang markdown` for the KB); never install it yourself. When dispatching, pass what you already know — slugs, paths, `worktree`, `docker_project`, the exact excerpt — so the agent doesn't search again. Full reads stay for audits (`relecture`, `contestation`, `securite`).
