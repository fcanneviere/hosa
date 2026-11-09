# Hosa project rules — détails

The full text of the rules `using-hosa` sums up under `## Hosa project rules`. Read only the section you need, when you need it: `using-hosa` is injected at every session start and stays under 10 KB (past it, Claude Code shows the model only the first 2 KB).

## KB

**KB location.** `<root>/.hosa/kb/`, inside the managed project (never Hosa's own checkout), on the orphan branch **`hosa-kb`** checked out there as a worktree; code branches ignore `.hosa/` and `.worktrees/`. `kb_branch.py` (`kb-commit`) manages it. Resolve it once per session: walk up to the first `.hosa/kb/`, **skipping any inside `.worktrees/`**, then `kb_branch.py status <root>` and act on it. During a sprint, code work happens in the worktree, every KB read and write in the root's KB. Never `cd` into `.hosa/`: use `git -C` and absolute paths. Every `kb/<bundle>/` path is relative to the KB.

## Enchaîner

**Chain, don't ask.** At the end of a stage, start the next stage of the same pipeline and say so in one line. Stop only for the user's real decisions: a product choice or validation the stage asks for (CDC sign-off, stack, identity and screens, sprint proposal), an agent's `## Open Questions`, a ticket's confirmation before its commit (`develop`), the sprint demo, the merge (`git-fusion`), the release (`livraison`), and anything blocking.

## Utilisateur

**Fit the user and the project** (`kb/project/identity.md`). `## Niveau de l'utilisateur`: débutant → no jargon without a one-line explanation, recommend rather than list, decide a technical choice they can't judge and say why; expert → terse, options with trade-offs; missing → intermédiaire. `## Taille`: `petit` → no stage or gate skipped, but each output the smallest that does the job (one ticket per user-visible capability, quick wins grouped, sprints of about two weeks, short documents); missing → standard.

## Checkpoints

**Git checkpoints.** Every skill that wrote files ends, before chaining, by dispatching `hosa-git` **with `model: haiku`** (Mode 3, checkpoint) with the files and a one-line summary: code outside a sprint on the base branch, the KB on `hosa-kb` (`kb_branch.py commit`). Never a question.

## Auto-audit

**Auto-audit of Hosa.** An agent's `## Retour Hosa` lines, and your own problems with Hosa itself (contradicting instructions, a missing step, an invented workaround, a useless check, a template that doesn't fit, a concrete improvement), go to `kb/retours-hosa/journal.md` (`type: Retour Hosa`, `## Ouverts` / `## Traités`, one dated line each: `Problème|Idée — <fichier Hosa, étape> — <constat> → <proposition>`, `(×N)` incremented instead of a duplicate), without asking or stopping. Never about the managed project's code. An entry moves to `## Traités` only when the user says so.

## Installation et base de données

**Only `hosa-infra` installs** anything; **only `hosa-dba` operates the database** (`hosa-data-engineer` designs it; everyone uses the commands in `kb/infra/base-de-donnees.md`).

## Docker

**Docker, on the right files.** Every command on the managed project runs in its checkout's Docker environment (during a sprint, the sprint's `docker_project` in `kb/sprints/<slug>.md`). `docker_check.py <docker_project> <checkout>` (`skills/infra/scripts/`) passes first; otherwise recreate with `docker compose -f "<checkout>/docker-compose.yml" -p <docker_project> up -d --build --force-recreate` — the `-f` ties the project to its checkout whatever the current folder (`gate.js` refuses a sprint's `up` from elsewhere).

## Dès la conception

**By design, not at the end.** Legal obligations (`juridique`), security constraints (`securite`), basic functions and both front and back office (`fondamentaux`) enter the cahier des charges before the stack. In `backlog`, `hosa-security` and `hosa-legal` turn each abuse case and each legal constraint into an acceptance criterion of the ticket that delivers it (`Note sécurité`, `Note juridique`, `→ CAn`), so it is built, tested and reviewed with it. `qualite`, the recette and `livraison` only catch what slipped.

## Plan

**Progress plan.** `.hosa/kb/project/avancement.md` is kept by `avancement.py` only (each pipeline skill names its calls). At session start, resume the stage in progress first: `reprendre` (`avancement.py reprendre`, the resume card in one call); a skill invoked with `args: "reprise"` starts at the step the card names, without its own preliminary reads. What comes next, and what the stage in progress still lacks → `avancement.py next`, never a guess. `done` refuses a stage whose proofs are missing (`check <stage> [--sprint <slug>]` lists them) — `--force` only after the user confirms. A stage that sends work back to an earlier one records it first: `back <from> <to> --detail "…"` (the loops of `skills/status/scripts/pipeline.json`). It reopens both and counts the round; refused past the loop's bound → the user decides, `--force` only on their word. `block --detail` carries the questions in full — a summary line, then each Q-numbered question with its options and your recommendation, one line each: after a `/clear` it is all that's left of them. A stage that dispatches agents lists each dispatch after its `start`: `task add <stage> <id> --agent <agent> --objet <ticket, persona…>`; when the agent returns, `task done <stage> <id> --sortie <the paths it wrote>` (refused without existing paths, or when a control of its outputs fails — not empty, OKF, the task's own controls in `pipeline.json`: re-dispatch the agent with the exact gaps; past 2 refusals of one cause the task is `bloqué`, the user decides), `task block … --detail` (its question) or `task skip … --detail`. `done <stage>` refuses while a task is open; after a `/clear`, resume at the first open task, never re-run a `fait` one. Work outside the pipeline records `reprise "<action>"` when interrupted.

## Une session par étape

**One session per stage.** The main session re-reads its whole history every turn: left open across stages, it costs more than all the agents. At each user stop point and after each ticket's commit, end the report with: « Pour économiser les tokens : `/clear`, puis « reprends » — le plan d'avancement garde tout. » Never open a screenshot in the main session: give its path. `budget.js` refuses once the next stage's skill when a stage closed and the context grew 20 k since the session's start, and any Hosa skill or agent dispatch past the start + 70 k → record the resume point, give the user that line, invoke again only if they stay. An agent stopped at its tool-call cap or at 120 k tokens of context returns `## Reprise` → dispatch a fresh agent with that section, not the previous report. Never resume with `SendMessage` an agent idle for more than 5 minutes (a limit, a pause): its cache is gone, the message writes its whole context again — dispatch a fresh one with its `## Reprise`.

## Réveils

**Agent wakes.** Each agent's hand-back, then its task-notification, wakes the main session, and each wake re-reads its whole context: 49-66 % of the main session's tokens on rieki and pilot2, a third of those wakes only to write « j'attends ». Dispatch a stage's independent agents in one message. On a hand-back, do its bookkeeping at once (`task done …` and the next dispatch, in one Bash call where you can): the notification that follows then rides on that call instead of waking you again. Other agents of the stage still running and nothing else to do → end the turn with no sentence. A task-notification of an agent whose hand-back you already handled: end the turn at once, no tool, no text. Never read an agent's output file: its hand-back is its report. Never do the agent's correction yourself: dispatch it.

## Mémoire

**Memory.** The KB and the progress plan are the project's memory. Claude Code's auto memory keeps only the user's preferences and ways of working, never project state. Agents with `memory: local` keep 50 lines max, never KB content.

## Ticket complet

**A ticket is born complete.** Any skill that creates a `Ticket` runs `backlog`'s Single-Ticket Mode on it before reporting; one that can't be completed yet is reported with the missing stage named.

## OKF

**KB writes follow `okf`** and end with its validator. `kb/code/` is generated — never edit it.

## Lecture

**Read little, read once.** `.hosa/kb/sommaire.md` first, then exact parts with `skills/okf/scripts/kb_query.py` (filters, `--sections`, `--fields`); for code, the project graph before Grep. If `ccc --version` works, `ccc search <concept>` finds code by meaning (in `.hosa/kb` with `--lang markdown` for the KB); never install it yourself. When dispatching, pass what you already know — slugs, paths, `worktree`, `docker_project`, the exact excerpt — so the agent doesn't search again. Full reads stay for audits (`relecture`, `contestation`, `securite`).
