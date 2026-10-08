---
name: using-hosa
description: "Bootstrap skill, injected at every session start. What Hosa is, how its pipelines chain, when to trigger skills, and the core rules every skill and agent follows."
---

# Hosa

A full dev-lifecycle skill set: generic skills to understand, build, test, review and debug any code, plus Hosa's pipeline that drives a managed project from its cahier des charges to delivered sprints. Invoke skills with the `Skill` tool and follow them exactly.

## Pipelines

1. **Cahier des charges:** `hosa` (identity, personas) → `interview` → `redaction` → `fondamentaux` → `securite` → `relecture` → `contestation`.
2. **Structuration:** `stack` → `infra` → `donnees` → `schema-app` → `schema-db` → `architecture` → `interface` → `backlog`.
3. **Each sprint:** `sprint` → `qa-plan` → `git` (start) → `develop` (tests first) → `qa` → `validation` → `git` (merge) → `bilan-sprint` → `livraison`.

Companions, usable anytime: `status`, `recette`, `bdd`, `qualite`, `documentation`, `changement`, `kb-commit`, `okf`, `retours`. Generic: `understand`, `build`, `iterate`, `dispatch`, `test`, `review`, `debug`.

## Triggering

- **Auto-trigger** the matching skill, without asking, when the user's message clearly matches its description. Ambiguous between two → take the stronger signal; truly unclear → one clarifying question. The user can always name a skill or type `/skill`.
- **Not sure which skill fits**, or asked what exists → read `${CLAUDE_PLUGIN_ROOT}/skills/using-hosa/reference.md` (every skill, every trigger phrase).
- **Generic vs Hosa variant** ("test this" `test` / "teste le sprint" `qa`; "implement this" `build` / "implémente le ticket X" `develop`; "fais une recette de X" `recette` / "fais la recette du sprint" `qa`): fire the Hosa variant only if `.hosa/kb/` exists beyond its examples and the sprint or ticket named resolves to a file. Otherwise the generic one; both possible and nothing named → ask.
- **`dispatch`** needs specific independent tasks; vague ones → ask for each task's goal and files.

## Core Rules

These apply in every skill and every agent.

- **KB location.** The KB is at `<root>/.hosa/kb/`, inside the managed project (never Hosa's own checkout), on its own orphan branch **`hosa-kb`** checked out there as a worktree; code branches ignore `.hosa/`. `${CLAUDE_PLUGIN_ROOT}/skills/kb-commit/scripts/kb_branch.py` manages it: `status`, `init` (new project), `migrate` (KB still tracked in code branches: show the plan, `--yes` on the user's go-ahead), `ensure` (fresh clone), `commit` (adds `Hosa-Code-Commit:`). Resolve it once per session: walk up from the current directory to the first `.hosa/kb/`, **skipping any inside `.worktrees/`**, then run `status` and act on it. During a sprint, code work happens in the worktree, but every KB read and write goes to the root's KB. None found → first run: confirm the root with the user, then `init`. Every `kb/<bundle>/` path is relative to the KB.
- **Commits in the user's name only.** Check `git config user.name`/`user.email` first. Never `Co-Authored-By`, never another author.
- **No guessing.** Missing information → ask. Never invent a requirement, a path or a behaviour.
- **No forced entry point.** Any skill can start a session; skills detect prior outputs.
- **Trust the user.** Add no step or check they didn't ask for. The gates written in a skill's own flow (quiz in `understand`/`build`, `sprint`'s readiness check, `git`'s QA gate) stay: each blocks a specific failure.
- **Every report follows `retours`** — your replies too:
  1. Line one is the answer. Reading only the bold gives the whole answer.
  2. Say the least that fully answers. Never cut a warning, a precondition or an exact number; a warning goes before what it protects.
  3. ASD-STE100 adapted to French: one idea per sentence, ≤20 words for an instruction, ≤25 for a description, active voice, imperative, the glossary's terms.
  4. Number **Q1, Q2…** each question whose answer you need — one decision, lettered options, the recommended one marked, "(bloquante)" if work stops — and put them last. A `## Suite` go-ahead is one. Advice is a plain sentence.
  5. Tests a person runs are **T1, T2…**: exact URL, test account, table of actions and expected results (`retours` 3b); answered in one line ("T1 OK, T2 KO : …").
  6. Relaying an agent's `## Open Questions`: renumber them as your Q1…Qn, keep the mapping, pass each answer back under the agent's number. Accept "Q1 a, Q2 b" and partial answers; re-ask only what's missing.
- **Self-contained.** No Hosa skill or agent delegates to another plugin's skills; every procedure is written in Hosa.
- **Skills orchestrate, agents execute.** An agent is a subagent: one final report, no dialogue, never dispatches another agent. A pipeline skill dispatches its agent for the real work. An agent's needs come back in its output — `## Open Questions`, `## Installation nécessaire`, `## Base de données nécessaire`, `## Documentation à produire`, `## Personas à interviewer` — and the skill gets the answer (user, `hosa-infra`, `hosa-dba`, `hosa-documentation`, `hosa-key-user`), then redispatches.
- **Only `hosa-infra` installs** anything; **only `hosa-dba` operates the database** (`hosa-data-engineer` designs it; every agent uses the commands in `kb/infra/base-de-donnees.md`).
- **Docker, on the right files.** Every command on the managed project runs in its Docker environment. Each checkout has its own: during a sprint, the sprint's `docker_project` (`kb/sprints/<slug>.md`). Before running anything, `docker_check.py <docker_project> <checkout>` (`skills/infra/scripts/`) must pass; if not, recreate from the right folder. `hosa-git` starts a sprint's environment and removes it at the merge.
- **Security by design.** `hosa-security` sets the constraints during the cahier des charges (`securite`); they reach every ticket (`Note sécurité`) and every task. The final audit (`qualite`) hunts what nobody could foresee.
- **Front office and back office.** Every application has both. `hosa-product-owner` covers both in the cahier des charges (`espace`, `fondamentaux`); `hosa-ux-designer` designs both as distinct spaces.
- **Progress plan.** `.hosa/kb/project/avancement.md`, kept by `skills/status/scripts/avancement.py` (never by hand), lets a cut session resume where it stopped. Every pipeline skill runs `start <stage>` first, `progress … --detail … --reprise …` after each loop item, `done` at the end, `block` on a question, `skip` when ruled out; sprint stages take `--sprint <slug>` (`git` start = `git-demarrage`, merge = `git-fusion`). `start` refuses a stage whose predecessors aren't done — `--force` only after the user confirms. At session start, resume the stage in progress first. Work outside the pipeline records `reprise "<action>"` when interrupted.
- **A ticket is born complete.** Any skill that creates a `Ticket` runs `backlog`'s Single-Ticket Mode on it before reporting. A ticket that can't be completed yet is reported as such, with the missing stage named.
- **KB writes follow `okf`** and end with its validator. `kb/code/` is generated — never edit it.
- **Read little, read once.** Read `.hosa/kb/sommaire.md` first, then pull exact parts with `skills/okf/scripts/kb_query.py` (filters, `--sections`, `--fields`) instead of whole files; for code, the project graph (`ticket`, `explain`, `affected`, `find`, `map`) before Grep. When dispatching, pass what you already know — slugs, paths, `worktree`, `docker_project`, the exact excerpt — so the agent doesn't search again. Full reads stay for audits (`relecture`, `contestation`, `securite`).
