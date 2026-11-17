---
type: Module
title: skills/status/scripts
description: '!/usr/bin/env python3'
resource: skills/status/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-17T17:26:14Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/status/scripts/avancement.py` | !/usr/bin/env python3 |
| `skills/status/scripts/usage_report.py` | !/usr/bin/env python3 |

## Symboles publics

- `accept` — `skills/status/scripts/avancement.py:474` — `state: done` and `verified` written by the script when the machine proof is complete; else its gaps.
- `acceptance_gaps` — `skills/status/scripts/avancement.py:448` — What keeps `accepte` from closing a ticket by itself: anything left is a judgment for `hosa-product-owner`.
- `after` — `skills/status/scripts/avancement.py:1666` — The tasks `tid` waits for, from pipeline.json's `after` (`juge-2` after `securite-2` and `juridique-2`).
- `answer_stats` — `skills/status/scripts/avancement.py:1508` — What the journal says of the questions: how often the user takes the recommendation, per stage and
- `answers` — `skills/status/scripts/avancement.py:1480` — [(n, choice, question)] of `Q1 a, Q2 b` or of one `Qn <choice> — <question>` per line.
- `atelier` — `skills/status/scripts/avancement.py:1269` — The interface tools' module: the review's grid is checked by the code that computes its note.
- `back` — `skills/status/scripts/avancement.py:1839` — `back <from> <to>`: one more round of a loop. (exit code, message or new resume point)
- `backlog_fixes` — `skills/status/scripts/avancement.py:786` — A sprint closes once every one-fix line of the backlog is applied, not only its own tickets' (rieki 0.1.107:
- `card` — `skills/status/scripts/avancement.py:1058` — Everything a resumed session needs, in one output: before it, a resume cost 11 calls and about
- `cell` — `skills/status/scripts/avancement.py:192`
- `check` — `skills/status/scripts/avancement.py:713` — What the KB lacks to prove a stage done: its proofs, then its agents' tasks still open.
- `clip` — `skills/status/scripts/avancement.py:1054`
- `close_remark` — `skills/status/scripts/avancement.py:1020` — `remarque <chemin> --detail`: the reply goes under `## Réponse de Claude`, `etat: traitee` in the frontmatter.
- `composition` — `skills/status/scripts/avancement.py:766` — A sprint holds what its tickets need: each `depends_on` done or listed before it, and each « label » a
- `concept` — `skills/status/scripts/avancement.py:517` — Gap of one expected file: missing, wrong type, or without its `## <heading>`.
- `concepts` — `skills/status/scripts/avancement.py:507` — The `.md` files of `kb/<folder>/` whose `type:` is <ctype>, with their text.
- `control_value` — `skills/status/scripts/avancement.py:1386`
- `controlled` — `skills/status/scripts/avancement.py:1652` — (cause, gaps) of the first control that fails — a gap naming its question (`Q2 — …`) refines the
- `coverage` — `skills/status/scripts/avancement.py:396` — Criteria of a ticket proved by its technical plan (`[CAn]`) or a recette (`CAn — Oui`).
- `criteria` — `skills/status/scripts/avancement.py:356` — What a criterion is comes from `ticket_check.py`, the one definition: qa-plan counts what backlog counted.
- `ctl_choix` — `skills/status/scripts/avancement.py:1231` — `interface` 3a: each round's choice is in `kb/interface/choix.md`, written by `atelier choisir` after the
- `ctl_grille` — `skills/status/scripts/avancement.py:1284` — `interface` revue: the filled grid given in `--sortie` passes the code that computes its note
- `ctl_interface` — `skills/status/scripts/avancement.py:1215` — `interface` 3c: the scaffold passes `interface_check` and `lexique_check`. A missing `espace` is left out:
- `ctl_juge` — `skills/status/scripts/avancement.py:1352` — `hosa-juge`'s written verdicts, each ticket on its newest one, newer than the ticket: each question of
- `ctl_lot` — `skills/status/scripts/avancement.py:1390` — At most `lot` tickets per task: an agent's context, and the judge's after it, grow with each ticket
- `ctl_okf` — `skills/status/scripts/avancement.py:1189` — The OKF errors of the task's own KB files: an older fault elsewhere in the KB is not the task's.
- `ctl_score` — `skills/status/scripts/avancement.py:1306` — `interface` revue: the last line of `## Revue visuelle` in `kb/interface/navigation.md` — `note N/10` at
- `ctl_sortie` — `skills/status/scripts/avancement.py:1183` — Each output exists; a `.md` one is not empty (an empty code file, `__init__.py`, can be right).
- `ctl_verdict` — `skills/status/scripts/avancement.py:1206` — A review task wrote its verdict: a `## Revue` line with PASS, PASS-WITH-NOTES or FAIL in each ticket.
- `edge` — `skills/status/scripts/avancement.py:156` — The loop of pipeline.json by which <frm> sends work back to <to>.
- `espace_gaps` — `skills/status/scripts/avancement.py:584` — `fondamentaux` reopened by `interface`: each exigence the loop named has its `espace` and is back in `draft`
- `field` — `skills/status/scripts/avancement.py:351`
- `first_open` — `skills/status/scripts/avancement.py:898`
- `front` — `skills/status/scripts/avancement.py:502`
- `infra_with` — `skills/status/scripts/avancement.py:527`
- `init` — `skills/status/scripts/avancement.py:1891` — A plan for a project begun before it: each stage done while its proof holds, in order,
- `init.walk` — `skills/status/scripts/avancement.py:1897`
- `inner_check` — `skills/status/scripts/avancement.py:695` — What the KB lacks to prove a loop inside a skill closed. `changement`: the exigence it
- `interface_gaps` — `skills/status/scripts/avancement.py:571` — The interface's completeness, one definition: the stage's proof and the `3c` task's control.
- `judged` — `skills/status/scripts/avancement.py:1403`
- `judgments` — `skills/status/scripts/avancement.py:1346` — (verdict file, section) of each judgment of one ticket, oldest first: the newest is its answer.
- `juge_extract` — `skills/status/scripts/avancement.py:1595` — What `hosa-juge` reads, and nothing else: each ticket's story, `Lié à :`, criteria, security and legal
- `juge_groups` — `skills/status/scripts/avancement.py:1629` — `slugs` in order, cut into groups whose extract fits `JUGE_MAX`: one judge per group.
- `juge_items` — `skills/status/scripts/avancement.py:1321`
- `juge_path` — `skills/status/scripts/avancement.py:1334`
- `juge_questions` — `skills/status/scripts/avancement.py:1325`
- `juge_stats` — `skills/status/scripts/avancement.py:1425` — What the journal says of the judge: tasks judged, validated at their first round, refusals and
- `kb_rel` — `skills/status/scripts/avancement.py:1156`
- `keep_blocked` — `skills/status/scripts/avancement.py:1466` — The questions of a stage still `bloqué` live in the resume point only: an action elsewhere (`reprise`,
- `last_verdict` — `skills/status/scripts/avancement.py:736` — A ticket's review verdict: the first PASS-WITH-NOTES, PASS or FAIL of the last `## Revue` line that has one —
- `load` — `skills/status/scripts/avancement.py:119` — {section title: [[stage, status, updated, detail], …]}, resume point.
- `load_loops` — `skills/status/scripts/avancement.py:161` — The rounds of each loop, from `## Boucles`.
- `load_tasks` — `skills/status/scripts/avancement.py:181` — The agents' tasks of the open stages, from `## Tâches`.
- `locate` — `skills/status/scripts/avancement.py:315`
- `locked` — `skills/status/scripts/avancement.py:246` — One writer of the plan at a time: two `task done` sent together each read the plan, then wrote it, and
- `log_answers` — `skills/status/scripts/avancement.py:1489` — One line per answered question in `kb/questions/log.md` (OKF §9, like the judge's journal): whether the
- `log_juge` — `skills/status/scripts/avancement.py:1408` — One line per `task done` the judge decided, in `kb/jugements/log.md` (OKF §9: a heading per day,
- `loop_max` — `skills/status/scripts/avancement.py:176`
- `loop_name` — `skills/status/scripts/avancement.py:172`
- `lot_tickets` — `skills/status/scripts/avancement.py:1674` — The tickets the tasks `t` comes after wrote, and those before them: what the judge of a batch judges,
- `main` — `skills/status/scripts/avancement.py:1916`
- `merge_sprints` — `skills/status/scripts/avancement.py:289` — A section opened under a shortened slug joins its sprint's: per stage the most advanced status wins,
- `newer` — `skills/status/scripts/avancement.py:724` — A line's date is after `since` (the plan's UTC time). A date without its time counts only from the next day:
- `next_open` — `skills/status/scripts/avancement.py:908`
- `next_verdict` — `skills/status/scripts/avancement.py:1563` — The file this judgment writes: the task's verdict the first time, then `<verdict>.<n>.md`. Reserved at
- `nothing_fixed` — `skills/status/scripts/avancement.py:747` — A `## Corrections` line where nothing was proved and no test was added: no code changed, no review ran.
- `now` — `skills/status/scripts/avancement.py:115`
- `numbered` — `skills/status/scripts/avancement.py:1577` — `### <rel>` then `<n>: <line>` for each non-empty body line whose `## ` section `keep` accepts (None:
- `observation_gaps` — `skills/status/scripts/avancement.py:364` — A plan's `## Observation`: each criterion whose effect the screen doesn't show (a failure, a volume, the
- `open_loops` — `skills/status/scripts/avancement.py:916`
- `open_remarks` — `skills/status/scripts/avancement.py:985` — The user's remarks written in the dashboard (`kb/remarques/`, type `Remarque`) not closed yet, oldest first.
- `open_tasks` — `skills/status/scripts/avancement.py:709`
- `outputs` — `skills/status/scripts/avancement.py:1163` — `--sortie` as the sessions write it: paths, and words around them. (paths, comment). rieki: 7 refusals, two
- `proofs` — `skills/status/scripts/avancement.py:795` — The files and checkers that prove a stage done.
- `read` — `skills/status/scripts/avancement.py:328`
- `recettes` — `skills/status/scripts/avancement.py:423` — A ticket's recette files (`kb/test/<ticket>-<persona>.md`) and their text.
- `refusals` — `skills/status/scripts/avancement.py:1713`
- `refused` — `skills/status/scripts/avancement.py:1718` — {cause: refusals} of a task. Each cause keeps its count: with the last cause only, two causes in turn
- `remark_lines` — `skills/status/scripts/avancement.py:1005`
- `reopen` — `skills/status/scripts/avancement.py:1692` — Each Non goes back to the task pipeline.json names for its question (`to`), with its exact lines:
- `reopened` — `skills/status/scripts/avancement.py:752` — (when, ticket) of each open loop of this sprint that reran <stage>, or that <stage> sent back (`audit` →
- `resolve` — `skills/status/scripts/avancement.py:1143` — An output path as an agent gives it: absolute, `kb/…`, `.hosa/kb/…`, from the project root
- `result_gaps` — `skills/status/scripts/avancement.py:431` — `qa`'s proof per criterion: a passed result line, or a recette `CAn — Oui`.
- `result_status` — `skills/status/scripts/avancement.py:412` — Each criterion's last status in `## Résultats techniques`: `- CAn (…) : réussi — <tests>` (`hosa-tester` step 7).
- `review_lines` — `skills/status/scripts/avancement.py:1279`
- `run` — `skills/status/scripts/avancement.py:1924`
- `run_script` — `skills/status/scripts/avancement.py:536` — A Hosa checker's run, or None when it could not run.
- `running_agents` — `skills/status/scripts/avancement.py:948` — The Hosa agents of this KB still running, from hooks/budget.js's state (any session: a /clear leaves them
- `save` — `skills/status/scripts/avancement.py:204`
- `script` — `skills/status/scripts/avancement.py:549` — Gaps a Hosa checker reports (exit 1), on one line. Any other failure is not the stage's: fail-open.
- `script_lines` — `skills/status/scripts/avancement.py:556` — Each gap a Hosa checker reports (exit 1), in full: a loop's next round gets them as they are.
- `section` — `skills/status/scripts/avancement.py:335` — Body of the last `## <heading>` (up to the next level-2 heading).
- `show` — `skills/status/scripts/avancement.py:935`
- `sprint_slug` — `skills/status/scripts/avancement.py:279` — The sprint's slug as its file names it. `--sprint sprint-2` for `sprints/sprint-2-fiabilite.md` opened a
- `suffixed` — `skills/status/scripts/avancement.py:1329` — `pattern`'s task for the batch of `tid` (glob `of`): `securite-*` for `juge-2b` is `securite-2b`.
- `task` — `skills/status/scripts/avancement.py:1725` — `task add\|done\|block\|skip <stage> <id>`. (exit code, message)
- `task_controls` — `skills/status/scripts/avancement.py:1647`
- `task_lines` — `skills/status/scripts/avancement.py:921` — Per stage: tasks done out of all, the next one to dispatch; each blocked task in full.
- `task_name` — `skills/status/scripts/avancement.py:200`
- `task_resume` — `skills/status/scripts/avancement.py:1825` — `task … --reprise "<next action>"`: the stage's detail and the resume point, in the task's own call. A second
- `task_where` — `skills/status/scripts/avancement.py:196`
- `ticket_check` — `skills/status/scripts/avancement.py:387`
- `tickets_of` — `skills/status/scripts/avancement.py:1202`
- `unproved` — `skills/status/scripts/avancement.py:1533` — Why a `Oui — <fichier>:<ligne> « <extrait> »` proves nothing: no citation, no such line, or the
- `upstream_check` — `skills/status/scripts/avancement.py:605` — What the KB lacks to prove a stage of the cahier des charges or the structuration done:
- `verdict_files` — `skills/status/scripts/avancement.py:1338` — The task's verdict and its re-judgments (`<verdict>.<n>.md`, some tickets each), oldest name first.
- `verification_gaps` — `skills/status/scripts/avancement.py:1246` — 3c's own verification: the last line of `## Vérification` in `kb/interface/navigation.md`, written in this
- `waiting` — `skills/status/scripts/avancement.py:1456` — {n: text} of the Q-numbered questions the resume point still holds for the blocked stage <where>.
- `add` — `skills/status/scripts/usage_report.py:117`
- `blocks` — `skills/status/scripts/usage_report.py:100`
- `context` — `skills/status/scripts/usage_report.py:63`
- `corrections` — `skills/status/scripts/usage_report.py:277` — `## Corrections` lines of the sprint's tickets (`develop` Correction Mode): their type, and
- `count_reads` — `skills/status/scripts/usage_report.py:377`
- `delivered` — `skills/status/scripts/usage_report.py:245` — Tickets with a commit carrying `Hosa-Ticket: <slug>` (the `develop` gate) in the period.
- `earlier_costs` — `skills/status/scripts/usage_report.py:300` — `Coût par ticket` of the other sprints' `## Mesures`.
- `fmt` — `skills/status/scripts/usage_report.py:387`
- `images` — `skills/status/scripts/usage_report.py:67`
- `lines` — `skills/status/scripts/usage_report.py:91`
- `main` — `skills/status/scripts/usage_report.py:400`
- `measures` — `skills/status/scripts/usage_report.py:310` — `## Mesures` of a sprint: the figures, then what crossed a threshold, as proposals.
- `meta_type` — `skills/status/scripts/usage_report.py:369`
- `outside` — `skills/status/scripts/usage_report.py:81`
- `project_dir` — `skills/status/scripts/usage_report.py:86`
- `scan` — `skills/status/scripts/usage_report.py:128`
- `scan.measure` — `skills/status/scripts/usage_report.py:142`
- `share` — `skills/status/scripts/usage_report.py:52`
- `sprint_file` — `skills/status/scripts/usage_report.py:258`
- `sprint_period` — `skills/status/scripts/usage_report.py:262` — From the sprint's creation day (`generated.at`) to its merge commit's day, and its tickets.
- `table` — `skills/status/scripts/usage_report.py:391`
- `usage_once` — `skills/status/scripts/usage_report.py:105` — The entry's usage, or {} if its message was already counted: Claude Code
- `usd` — `skills/status/scripts/usage_report.py:72`
- `wake_line` — `skills/status/scripts/usage_report.py:57`
- `write_section` — `skills/status/scripts/usage_report.py:360` — Replace the file's `## Mesures` section (heading to the next level-2 heading), or append it.

## Tickets et exigences

Aucun.
