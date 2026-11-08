---
name: reprendre
description: "Use to resume a Hosa project after a /clear, a limit or a new day: one call gives the stage, its skill, the agents' tasks and the next action, then the work goes on at once. Triggers: « reprends », « on reprend », « continue », « où on en était », /reprendre."
---

# Reprendre

A resume used to cost 11 calls and about 530 k tokens of context before its first action (median, rieki, pilot2, hosa-ui): `ls`, `cat`, `show`, `next`, then 2 or 3 skills loaded. The resume card replaces all of that.

1. **One call, nothing before it.** Run `<hosa> avancement "<kb>" reprendre`. The KB path is in the session context (`## Hosa`, its first lines); none there → walk up from the current folder to the first `.hosa/kb/`, skipping `.worktrees/`. No `ls`, `cat`, `git`, `show`, `next`, `sommaire.md` before it.
2. **Do its `Action` line, in the same turn.** It names the skill to invoke, with `args: "reprise"`, and the first thing to do in it (start the stage, dispatch a task, close the stage).
3. **The card is the skill's start-up.** In a skill invoked with `reprise`: the KB is resolved, the stage is started (never `start` again an `en cours` stage), the tasks marked done passed `task done` (never re-read their outputs to check them). Skip the skill's own preliminary reads and go to the step the card names. Read only the files that step needs.
4. **Agent still running** (`Agent encore actif`): an agent of the cleared session is still at work, and its report reaches this session. Never dispatch its work again; its hand-back received, do its bookkeeping (`task add` if the plan lacks it, then `task done`) and go on as the card says.
5. **Blocked** (a stage or a task `bloqué`): give the user its questions as Q1…, with their options and your recommendation (`retours`), from the card's detail and the files it names, then stop. Their answer received, invoke the skill as the card says.
6. **No plan** (`Pas de plan d'avancement`): invoke `status`. **Only a `Prochaine action`** (work outside the pipeline): do that action.

The session context also holds what the cleared session was doing (its last requests and answer, the files touched, the git state): use it to pick the exact point inside the step, never to redo a done task.
