---
type: Module
title: hooks
description: Hosa — progress plan at session start. Reads `.hosa/kb/project/avancement.md`
resource: hooks
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-13T12:45:46Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `hooks/avancement.js` | Hosa — progress plan at session start. Reads `.hosa/kb/project/avancement.md` |
| `hooks/avancement.test.js` |  |
| `hooks/budget.js` |  |
| `hooks/budget.test.js` |  |
| `hooks/compress-output.js` |  |
| `hooks/compress-output.test.js` |  |
| `hooks/gate.js` |  |
| `hooks/gate.test.js` |  |
| `hooks/graph.js` |  |
| `hooks/graph.test.js` |  |
| `hooks/launch.js` |  |
| `hooks/launch.test.js` |  |
| `hooks/read-guard.js` |  |
| `hooks/read-guard.test.js` |  |
| `hooks/register-plan.test.js` |  |
| `hooks/register.mjs` | Hosa — mod (Claude Code ≥ 2.1.290; older versions ignore it, the classic hooks still run). |
| `hooks/register.test.ts` |  |
| `hooks/reprendre.js` |  |
| `hooks/reprendre.test.js` |  |
| `hooks/reprise.js` | Hosa — the session just cleared, at /clear. The progress plan knows the stage, not the task |
| `hooks/reprise.test.js` |  |
| `hooks/session-start.js` |  |
| `hooks/session-start.test.js` |  |
| `hooks/stop.js` |  |
| `hooks/stop.test.js` |  |
| `hooks/subagent-start.js` |  |
| `hooks/subagent-start.test.js` |  |

## Symboles publics

- `kbLayoutNote` — `hooks/avancement.js:11` — tracked in the code branches (to migrate). Fast, read-only, never blocks.
- `kbLayoutNote.run` — `hooks/avancement.js:16`
- `resumeContext` — `hooks/avancement.js:27`
- `g` — `hooks/avancement.test.js:115`
- `kb` — `hooks/avancement.test.js:9`
- `plan` — `hooks/avancement.test.js:30`
- `agentGate` — `hooks/budget.js:239`
- `agentTranscript` — `hooks/budget.js:89` — A subagent's transcript: given by the hook, or `<session>/subagents/agent-<id>.jsonl` beside the main one.
- `canWrite` — `hooks/budget.js:216` — (hosa-challenger, hosa-reviewer, hosa-tech-lead).
- `ceilingGate` — `hooks/budget.js:157` — Past start + CEILING, refused once, then again every STEP more: `again` is what passes on the retry.
- `closedStages` — `hooks/budget.js:83` — Stages done or ruled out in the plan.
- `contextTokens` — `hooks/budget.js:122`
- `deny` — `hooks/budget.js:72`
- `dispatchGate` — `hooks/budget.js:308` — stage's `dispatch` rules.
- `graph` — `hooks/budget.js:56` — The one stage graph (avancement.py reads it too).
- `hash` — `hooks/budget.js:68`
- `lastCall` — `hooks/budget.js:99` — and its time.
- `load` — `hooks/budget.js:70`
- `pauseGate` — `hooks/budget.js:170` — The refusal erases the message: it is given back, to send again. A slash command passes (/clear, /compact).
- `pauseGate.k` — `hooks/budget.js:181`
- `pendingFile` — `hooks/budget.js:354`
- `planText` — `hooks/budget.js:76` — The managed project's plan (a worktree's copy is stale: findKbRoot skips it).
- `processPayload` — `hooks/budget.js:375`
- `recordDispatch` — `hooks/budget.js:357`
- `reportGate` — `hooks/budget.js:225` — longer than REPORT_MAX besides `## Open Questions` and `## Reprise` (kept whole), it is refused once.
- `running` — `hooks/budget.js:265` — Hosa agents of this session still running: started, not stopped, active within SILENT.
- `save` — `hooks/budget.js:71`
- `sessionStart` — `hooks/budget.js:148` — The session's start, read once and kept in its state.
- `short` — `hooks/budget.js:355`
- `stageGate` — `hooks/budget.js:189`
- `startTokens` — `hooks/budget.js:125` — Context of the session's first call, from the head of its transcript (the start after /clear).
- `stateDir` — `hooks/budget.js:67`
- `stateFile` — `hooks/budget.js:69`
- `takeDispatch` — `hooks/budget.js:366`
- `taskGate` — `hooks/budget.js:285`
- `agentFile` — `hooks/budget.test.js:97`
- `back` — `hooks/budget.test.js:136`
- `call` — `hooks/budget.test.js:220`
- `denied` — `hooks/budget.test.js:10`
- `infra` — `hooks/budget.test.js:195`
- `po` — `hooks/budget.test.js:178`
- `pre` — `hooks/budget.test.js:105`
- `report` — `hooks/budget.test.js:135`
- `say` — `hooks/budget.test.js:222`
- `setAgentContext` — `hooks/budget.test.js:98`
- `setContext` — `hooks/budget.test.js:20`
- `setPlan` — `hooks/budget.test.js:14`
- `skill` — `hooks/budget.test.js:22`
- `start` — `hooks/budget.test.js:176`
- `usage` — `hooks/budget.test.js:17`
- `clip` — `hooks/compress-output.js:28`
- `condense` — `hooks/compress-output.js:262`
- `dedup` — `hooks/compress-output.js:308` — Same-session only: a fresh session's context doesn't hold the earlier copy.
- `dropLines` — `hooks/compress-output.js:103` — Lines matching `res` go, unless they look like an error; the count goes in the footer.
- `extractText` — `hooks/compress-output.js:30`
- `fitBlocks` — `hooks/compress-output.js:279` — Grep and path lists: whole groups up to the budget, then every remaining group by name.
- `fitLines` — `hooks/compress-output.js:292` — Anything else: head and tail, the hidden line range by number, its error lines with theirs.
- `gitDiff` — `hooks/compress-output.js:123` — One block per file (or commit header), so a diff too big keeps whole files.
- `gitDiff.count` — `hooks/compress-output.js:137`
- `gitLog` — `hooks/compress-output.js:144` — `git log` medium format → one header line per commit; `-p` diffs go through gitDiff.
- `gitStatus` — `hooks/compress-output.js:115`
- `grepGroup` — `hooks/compress-output.js:204` — `path:12:text` (and `path-12-text` context lines) → the path once, its lines under it. Lossless.
- `kindOf` — `hooks/compress-output.js:87`
- `pathGroup` — `hooks/compress-output.js:227` — A list of paths → one line per directory. Lossless.
- `processPayload` — `hooks/compress-output.js:366` — Hook payload → replacement tool_response, or null to leave it untouched.
- `program` — `hooks/compress-output.js:76` — without env assignments or a runner prefix (rtk, npx, uv run, python -m…).
- `rebuild` — `hooks/compress-output.js:43` — returns {stdout, stderr, ...}, so hand back that shape or skip entirely.
- `scrub` — `hooks/compress-output.js:58` — Lossless: colours, carriage-return progress (last state kept), trailing blanks, exact repeats.
- `similar` — `hooks/compress-output.js:243` — Runs where only the numbers change (counters, timings, ids) → first two, last one, a count.
- `similar.tpl` — `hooks/compress-output.js:244`
- `spill` — `hooks/compress-output.js:329` — Full text goes to disk so whatever was dropped is read back, not re-run.
- `stateDir` — `hooks/compress-output.js:27`
- `tapPasses` — `hooks/compress-output.js:175` — `not ok` keeps its block (it holds the error).
- `transform` — `hooks/compress-output.js:342`
- `bash` — `hooks/compress-output.test.js:10`
- `call` — `hooks/compress-output.test.js:157`
- `file` — `hooks/compress-output.test.js:106`
- `ok` — `hooks/compress-output.test.js:63`
- `pad` — `hooks/compress-output.test.js:12`
- `spillOf` — `hooks/compress-output.test.js:11`
- `cdGate` — `hooks/gate.js:120` — (`.claude/agent-memory-local/`) inside the KB, and later git commands hit `hosa-kb`.
- `commitGate` — `hooks/gate.js:73`
- `composeGate` — `hooks/gate.js:131`
- `dispatchCwdGate` — `hooks/gate.js:225` — `cdGate` closes one route (Bash `cd`); `pushd`, the PowerShell tool or any other move are caught here.
- `failRun` — `hooks/gate.js:189`
- `gitCalls` — `hooks/gate.js:43` — Each git call: its directory (cd and -C applied), subcommand and arguments.
- `mergeGate` — `hooks/gate.js:102`
- `native` — `hooks/gate.js:25`
- `processPayload` — `hooks/gate.js:231`
- `processPayload.deny` — `hooks/gate.js:233`
- `read` — `hooks/gate.js:60`
- `reviewLoopGate` — `hooks/gate.js:199`
- `scriptGate` — `hooks/gate.js:168`
- `section` — `hooks/gate.js:63` — Body of the last `## <heading>` section (up to the next level-2 heading).
- `segments` — `hooks/gate.js:28` — Shell words grouped by command (split on && \|\| ; \| newline); quotes kept together.
- `agent` — `hooks/gate.test.js:152`
- `bash` — `hooks/gate.test.js:18`
- `commit` — `hooks/gate.test.js:22`
- `denied` — `hooks/gate.test.js:19`
- `dev` — `hooks/gate.test.js:165`
- `lot` — `hooks/gate.test.js:45`
- `project` — `hooks/gate.test.js:9`
- `sprint` — `hooks/gate.test.js:70`
- `ticket` — `hooks/gate.test.js:21`
- `wt` — `hooks/gate.test.js:33`
- `broadIdentGrep` — `hooks/graph.js:111`
- `checkHeader` — `hooks/graph.js:66`
- `commandLine` — `hooks/graph.js:93`
- `findKbRoot` — `hooks/graph.js:51` — committed copy of `.hosa/kb` — skip it and keep walking up to the project root.
- `findUp` — `hooks/graph.js:42` — Closest ancestor of `dir` containing `marker` (a relative path), or null.
- `guardGrep` — `hooks/graph.js:117`
- `hosaCommand` — `hooks/graph.js:92`
- `mtime` — `hooks/graph.js:147`
- `processPayload` — `hooks/graph.js:150` — Hook payload → hook output object, or null.
- `python` — `hooks/graph.js:28`
- `pythonBackground` — `hooks/graph.js:35` — opens a window. pythonw.exe never does; its stdout is None, which is fine for stdio: 'ignore'.
- `queryGraph` — `hooks/graph.js:100` — `graph.py find` output, or '' on failure/no hit. Stays under the 5 s hook timeout.
- `refreshSummary` — `hooks/graph.js:20` — Rewrites `.hosa/kb/sommaire.md` (one line per KB concept) in the background.
- `runGraph` — `hooks/graph.js:95`
- `sessionStart` — `hooks/graph.js:136` — (a full first build can exceed the hook timeout). Returns the context line, or ''.
- `shimText` — `hooks/graph.js:78`
- `writeShim` — `hooks/graph.js:87`
- `deny` — `hooks/graph.test.js:57`
- `hit` — `hooks/graph.test.js:56`
- `ok` — `hooks/graph.test.js:97`
- `project` — `hooks/graph.test.js:9`
- `processPayload` — `hooks/launch.js:13`
- `launched` — `hooks/launch.test.js:12`
- `on` — `hooks/launch.test.js:17`
- `deny` — `hooks/read-guard.js:24`
- `processPayload` — `hooks/read-guard.js:27`
- `processPayload.save` — `hooks/read-guard.js:43`
- `stateDir` — `hooks/read-guard.js:18`
- `stateFile` — `hooks/read-guard.js:19`
- `denied` — `hooks/read-guard.test.js:13`
- `read` — `hooks/read-guard.test.js:12`
- `readBig` — `hooks/read-guard.test.js:30`
- `bare` — `hooks/register.mjs:45`
- `dashboard` — `hooks/register.mjs:238` — The dashboard's row: one button to open it, then its link and a button to stop it.
- `dashboard.onPress` — `hooks/register.mjs:245`
- `dashboard.start` — `hooks/register.mjs:239`
- `pane` — `hooks/register.mjs:174` — Everything the user needs, from the plan alone: what waits for them first, then where the project is.
- `pane.group` — `hooks/register.mjs:177`
- `pane.mark` — `hooks/register.mjs:178`
- `pane.para` — `hooks/register.mjs:176`
- `pane.row` — `hooks/register.mjs:175`
- `python` — `hooks/register.mjs:110` — (no console window opens); else the Python on the PATH, and run.py builds what it lacks.
- `readPlan` — `hooks/register.mjs:26` — the rows above the first `## Sprint` heading are the upstream stages, no list to keep in step here.
- `readView` — `hooks/register.mjs:46`
- `redraw` — `hooks/register.mjs:167` — Fail-open: a pane that cannot be drawn again never stops a hook.
- `refresh` — `hooks/register.mjs:88` — The managed project's plan: a sprint worktree's `.hosa/kb` copy is stale, so start above it.
- `register` — `hooks/register.mjs:260`
- `showStatus` — `hooks/register.mjs:255`
- `startDashboard` — `hooks/register.mjs:121` — The server lives for the session (the stream's loop is its life); 3000 taken → a free port. Fail-open.
- `stopDashboard` — `hooks/register.mjs:158`
- `project` — `hooks/register.test.ts:11`
- `row` — `hooks/register.test.ts:3`
- `spawn` — `hooks/register.test.ts:74`
- `step` — `hooks/register.test.ts:29`
- `card` — `hooks/reprendre.js:15`
- `processPayload` — `hooks/reprendre.js:23`
- `project` — `hooks/reprendre.test.js:9`
- `cut` — `hooks/reprise.js:12`
- `gitState` — `hooks/reprise.js:82`
- `gitState.run` — `hooks/reprise.js:84`
- `oneLine` — `hooks/reprise.js:13`
- `previousSession` — `hooks/reprise.js:99` — Hook payload (source, session_id, transcript_path, cwd) → context block, or ''.
- `previousSession.rel` — `hooks/reprise.js:106`
- `previousTranscript` — `hooks/reprise.js:16` — The most recent other transcript of the same project folder: the session /clear just closed.
- `readSession` — `hooks/reprise.js:57`
- `requestText` — `hooks/reprise.js:44` — a slash command kept as `/name args`.
- `tailLines` — `hooks/reprise.js:29`
- `assistant` — `hooks/reprise.test.js:10`
- `project` — `hooks/reprise.test.js:13` — A project folder of transcripts: the cleared session, written first, and the new one.
- `user` — `hooks/reprise.test.js:9`
- `bytes` — `hooks/session-start.js:16`
- `compose` — `hooks/session-start.js:34` — the plan shortened past 60 % of the room, then the cleared session's recap.
- `compose.parts` — `hooks/session-start.js:35`
- `main` — `hooks/session-start.js:57`
- `rules` — `hooks/session-start.js:47` — `using-hosa`, the second hook: whole, without its frontmatter; without the project rules where no KB is.
- `shorten` — `hooks/session-start.js:19` — Cut `text` to `max` bytes at a line end, saying so.
- `bytes` — `hooks/session-start.test.js:8`
- `processPayload` — `hooks/stop.js:28`
- `stagesInProgress` — `hooks/stop.js:16` — `\| \`stage\` \| en cours \| … \|` rows of avancement.md, with the section they sit in (a sprint, a pipeline).
- `stateDir` — `hooks/stop.js:12`
- `stateFile` — `hooks/stop.js:13`
- `setPlan` — `hooks/stop.test.js:13`
- `stop` — `hooks/stop.test.js:15`
- `processPayload` — `hooks/subagent-start.js:58`
- `pythonLine` — `hooks/subagent-start.js:47` — a path under the plugin cache breaks at the next update.
- `ctx` — `hooks/subagent-start.test.js:38`

## Tickets et exigences

Aucun.
