---
type: Module
title: skills/status/scripts
description: '!/usr/bin/env python3'
resource: skills/status/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-13T01:27:15Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/status/scripts/avancement.py` | !/usr/bin/env python3 |
| `skills/status/scripts/usage_report.py` | !/usr/bin/env python3 |

## Symboles publics

- `after` — `skills/status/scripts/avancement.py:1416` — The tasks `tid` waits for, from pipeline.json's `after` (`juge-2` after `securite-2` and `juridique-2`).
- `answer_stats` — `skills/status/scripts/avancement.py:1258` — What the journal says of the questions: how often the user takes the recommendation, per stage and
- `answers` — `skills/status/scripts/avancement.py:1230` — [(n, choice, question)] of `Q1 a, Q2 b` or of one `Qn <choice> — <question>` per line.
- `atelier` — `skills/status/scripts/avancement.py:1019` — The interface tools' module: the review's grid is checked by the code that computes its note.
- `back` — `skills/status/scripts/avancement.py:1589` — `back <from> <to>`: one more round of a loop. (exit code, message or new resume point)
- `card` — `skills/status/scripts/avancement.py:809` — Everything a resumed session needs, in one output: before it, a resume cost 11 calls and about
- `cell` — `skills/status/scripts/avancement.py:192`
- `check` — `skills/status/scripts/avancement.py:592` — What the KB lacks to prove a stage done: its proofs, then its agents' tasks still open.
- `clip` — `skills/status/scripts/avancement.py:805`
- `concept` — `skills/status/scripts/avancement.py:399` — Gap of one expected file: missing, wrong type, or without its `## <heading>`.
- `concepts` — `skills/status/scripts/avancement.py:389` — The `.md` files of `kb/<folder>/` whose `type:` is <ctype>, with their text.
- `control_value` — `skills/status/scripts/avancement.py:1136`
- `controlled` — `skills/status/scripts/avancement.py:1402` — (cause, gaps) of the first control that fails — a gap naming its question (`Q2 — …`) refines the
- `coverage` — `skills/status/scripts/avancement.py:371` — Criteria of a ticket proved by its technical plan (`[CAn]`) or a recette (`CAn — Oui`).
- `criteria` — `skills/status/scripts/avancement.py:356` — What a criterion is comes from `ticket_check.py`, the one definition: qa-plan counts what backlog counted.
- `ctl_choix` — `skills/status/scripts/avancement.py:981` — `interface` 3a: each round's choice is in `kb/interface/choix.md`, written by `atelier choisir` after the
- `ctl_grille` — `skills/status/scripts/avancement.py:1034` — `interface` revue: the filled grid given in `--sortie` passes the code that computes its note
- `ctl_interface` — `skills/status/scripts/avancement.py:965` — `interface` 3c: the scaffold passes `interface_check` and `lexique_check`. A missing `espace` is left out:
- `ctl_juge` — `skills/status/scripts/avancement.py:1102` — `hosa-juge`'s written verdicts, each ticket on its newest one, newer than the ticket: each question of
- `ctl_lot` — `skills/status/scripts/avancement.py:1140` — At most `lot` tickets per task: an agent's context, and the judge's after it, grow with each ticket
- `ctl_okf` — `skills/status/scripts/avancement.py:939` — The OKF errors of the task's own KB files: an older fault elsewhere in the KB is not the task's.
- `ctl_score` — `skills/status/scripts/avancement.py:1056` — `interface` revue: the last line of `## Revue visuelle` in `kb/interface/navigation.md` — `note N/10` at
- `ctl_sortie` — `skills/status/scripts/avancement.py:933` — Each output exists; a `.md` one is not empty (an empty code file, `__init__.py`, can be right).
- `ctl_verdict` — `skills/status/scripts/avancement.py:956` — A review task wrote its verdict: a `## Revue` line with PASS, PASS-WITH-NOTES or FAIL in each ticket.
- `edge` — `skills/status/scripts/avancement.py:156` — The loop of pipeline.json by which <frm> sends work back to <to>.
- `espace_gaps` — `skills/status/scripts/avancement.py:466` — `fondamentaux` reopened by `interface`: each exigence the loop named has its `espace` and is back in `draft`
- `field` — `skills/status/scripts/avancement.py:351`
- `first_open` — `skills/status/scripts/avancement.py:722`
- `front` — `skills/status/scripts/avancement.py:384`
- `infra_with` — `skills/status/scripts/avancement.py:409`
- `init` — `skills/status/scripts/avancement.py:1641` — A plan for a project begun before it: each stage done while its proof holds, in order,
- `init.walk` — `skills/status/scripts/avancement.py:1647`
- `inner_check` — `skills/status/scripts/avancement.py:574` — What the KB lacks to prove a loop inside a skill closed. `changement`: the exigence it
- `interface_gaps` — `skills/status/scripts/avancement.py:453` — The interface's completeness, one definition: the stage's proof and the `3c` task's control.
- `judged` — `skills/status/scripts/avancement.py:1153`
- `judgments` — `skills/status/scripts/avancement.py:1096` — (verdict file, section) of each judgment of one ticket, oldest first: the newest is its answer.
- `juge_extract` — `skills/status/scripts/avancement.py:1345` — What `hosa-juge` reads, and nothing else: each ticket's story, `Lié à :`, criteria, security and legal
- `juge_groups` — `skills/status/scripts/avancement.py:1379` — `slugs` in order, cut into groups whose extract fits `JUGE_MAX`: one judge per group.
- `juge_items` — `skills/status/scripts/avancement.py:1071`
- `juge_path` — `skills/status/scripts/avancement.py:1084`
- `juge_questions` — `skills/status/scripts/avancement.py:1075`
- `juge_stats` — `skills/status/scripts/avancement.py:1175` — What the journal says of the judge: tasks judged, validated at their first round, refusals and
- `kb_rel` — `skills/status/scripts/avancement.py:906`
- `keep_blocked` — `skills/status/scripts/avancement.py:1216` — The questions of a stage still `bloqué` live in the resume point only: an action elsewhere (`reprise`,
- `load` — `skills/status/scripts/avancement.py:119` — {section title: [[stage, status, updated, detail], …]}, resume point.
- `load_loops` — `skills/status/scripts/avancement.py:161` — The rounds of each loop, from `## Boucles`.
- `load_tasks` — `skills/status/scripts/avancement.py:181` — The agents' tasks of the open stages, from `## Tâches`.
- `locate` — `skills/status/scripts/avancement.py:315`
- `locked` — `skills/status/scripts/avancement.py:246` — One writer of the plan at a time: two `task done` sent together each read the plan, then wrote it, and
- `log_answers` — `skills/status/scripts/avancement.py:1239` — One line per answered question in `kb/questions/log.md` (OKF §9, like the judge's journal): whether the
- `log_juge` — `skills/status/scripts/avancement.py:1158` — One line per `task done` the judge decided, in `kb/jugements/log.md` (OKF §9: a heading per day,
- `loop_max` — `skills/status/scripts/avancement.py:176`
- `loop_name` — `skills/status/scripts/avancement.py:172`
- `lot_tickets` — `skills/status/scripts/avancement.py:1424` — The tickets the tasks `t` comes after wrote, and those before them: what the judge of a batch judges,
- `main` — `skills/status/scripts/avancement.py:1666`
- `merge_sprints` — `skills/status/scripts/avancement.py:289` — A section opened under a shortened slug joins its sprint's: per stage the most advanced status wins,
- `newer` — `skills/status/scripts/avancement.py:603` — A line's date is after `since` (the plan's UTC time). A date without its time counts only from the next day:
- `next_open` — `skills/status/scripts/avancement.py:732`
- `next_verdict` — `skills/status/scripts/avancement.py:1313` — The file this judgment writes: the task's verdict the first time, then `<verdict>.<n>.md`. Reserved at
- `now` — `skills/status/scripts/avancement.py:115`
- `numbered` — `skills/status/scripts/avancement.py:1327` — `### <rel>` then `<n>: <line>` for each non-empty body line whose `## ` section `keep` accepts (None:
- `open_loops` — `skills/status/scripts/avancement.py:740`
- `open_tasks` — `skills/status/scripts/avancement.py:588`
- `outputs` — `skills/status/scripts/avancement.py:913` — `--sortie` as the sessions write it: paths, and words around them. (paths, comment). rieki: 7 refusals, two
- `proofs` — `skills/status/scripts/avancement.py:626` — The files and checkers that prove a stage done.
- `read` — `skills/status/scripts/avancement.py:328`
- `refusals` — `skills/status/scripts/avancement.py:1463`
- `refused` — `skills/status/scripts/avancement.py:1468` — {cause: refusals} of a task. Each cause keeps its count: with the last cause only, two causes in turn
- `reopen` — `skills/status/scripts/avancement.py:1442` — Each Non goes back to the task pipeline.json names for its question (`to`), with its exact lines:
- `reopened` — `skills/status/scripts/avancement.py:612` — (when, ticket) of each open loop of this sprint that reran <stage>, or that <stage> sent back (`audit` →
- `resolve` — `skills/status/scripts/avancement.py:893` — An output path as an agent gives it: absolute, `kb/…`, `.hosa/kb/…`, from the project root
- `review_lines` — `skills/status/scripts/avancement.py:1029`
- `run` — `skills/status/scripts/avancement.py:1674`
- `run_script` — `skills/status/scripts/avancement.py:418` — A Hosa checker's run, or None when it could not run.
- `running_agents` — `skills/status/scripts/avancement.py:772` — The Hosa agents of this KB still running, from hooks/budget.js's state (any session: a /clear leaves them
- `save` — `skills/status/scripts/avancement.py:204`
- `script` — `skills/status/scripts/avancement.py:431` — Gaps a Hosa checker reports (exit 1), on one line. Any other failure is not the stage's: fail-open.
- `script_lines` — `skills/status/scripts/avancement.py:438` — Each gap a Hosa checker reports (exit 1), in full: a loop's next round gets them as they are.
- `section` — `skills/status/scripts/avancement.py:335` — Body of the last `## <heading>` (up to the next level-2 heading).
- `show` — `skills/status/scripts/avancement.py:759`
- `sprint_slug` — `skills/status/scripts/avancement.py:279` — The sprint's slug as its file names it. `--sprint sprint-2` for `sprints/sprint-2-fiabilite.md` opened a
- `suffixed` — `skills/status/scripts/avancement.py:1079` — `pattern`'s task for the batch of `tid` (glob `of`): `securite-*` for `juge-2b` is `securite-2b`.
- `task` — `skills/status/scripts/avancement.py:1475` — `task add\|done\|block\|skip <stage> <id>`. (exit code, message)
- `task_controls` — `skills/status/scripts/avancement.py:1397`
- `task_lines` — `skills/status/scripts/avancement.py:745` — Per stage: tasks done out of all, the next one to dispatch; each blocked task in full.
- `task_name` — `skills/status/scripts/avancement.py:200`
- `task_resume` — `skills/status/scripts/avancement.py:1575` — `task … --reprise "<next action>"`: the stage's detail and the resume point, in the task's own call. A second
- `task_where` — `skills/status/scripts/avancement.py:196`
- `ticket_check` — `skills/status/scripts/avancement.py:362`
- `tickets_of` — `skills/status/scripts/avancement.py:952`
- `unproved` — `skills/status/scripts/avancement.py:1283` — Why a `Oui — <fichier>:<ligne> « <extrait> »` proves nothing: no citation, no such line, or the
- `upstream_check` — `skills/status/scripts/avancement.py:487` — What the KB lacks to prove a stage of the cahier des charges or the structuration done:
- `verdict_files` — `skills/status/scripts/avancement.py:1088` — The task's verdict and its re-judgments (`<verdict>.<n>.md`, some tickets each), oldest name first.
- `verification_gaps` — `skills/status/scripts/avancement.py:996` — 3c's own verification: the last line of `## Vérification` in `kb/interface/navigation.md`, written in this
- `waiting` — `skills/status/scripts/avancement.py:1206` — {n: text} of the Q-numbered questions the resume point still holds for the blocked stage <where>.
- `add` — `skills/status/scripts/usage_report.py:117`
- `blocks` — `skills/status/scripts/usage_report.py:100`
- `context` — `skills/status/scripts/usage_report.py:63`
- `corrections` — `skills/status/scripts/usage_report.py:277` — `## Corrections` lines of the sprint's tickets (`develop` Correction Mode): their type, and
- `count_reads` — `skills/status/scripts/usage_report.py:371`
- `delivered` — `skills/status/scripts/usage_report.py:245` — Tickets with a commit carrying `Hosa-Ticket: <slug>` (the `develop` gate) in the period.
- `earlier_costs` — `skills/status/scripts/usage_report.py:296` — `Coût par ticket` of the other sprints' `## Mesures`.
- `fmt` — `skills/status/scripts/usage_report.py:381`
- `images` — `skills/status/scripts/usage_report.py:67`
- `lines` — `skills/status/scripts/usage_report.py:91`
- `main` — `skills/status/scripts/usage_report.py:394`
- `measures` — `skills/status/scripts/usage_report.py:306` — `## Mesures` of a sprint: the figures, then what crossed a threshold, as proposals.
- `meta_type` — `skills/status/scripts/usage_report.py:363`
- `outside` — `skills/status/scripts/usage_report.py:81`
- `project_dir` — `skills/status/scripts/usage_report.py:86`
- `scan` — `skills/status/scripts/usage_report.py:128`
- `scan.measure` — `skills/status/scripts/usage_report.py:142`
- `share` — `skills/status/scripts/usage_report.py:52`
- `sprint_file` — `skills/status/scripts/usage_report.py:258`
- `sprint_period` — `skills/status/scripts/usage_report.py:262` — From the sprint's creation day (`generated.at`) to its merge commit's day, and its tickets.
- `table` — `skills/status/scripts/usage_report.py:385`
- `usage_once` — `skills/status/scripts/usage_report.py:105` — The entry's usage, or {} if its message was already counted: Claude Code
- `usd` — `skills/status/scripts/usage_report.py:72`
- `wake_line` — `skills/status/scripts/usage_report.py:57`
- `write_section` — `skills/status/scripts/usage_report.py:354` — Replace the file's `## Mesures` section (heading to the next level-2 heading), or append it.

## Tickets et exigences

Aucun.
