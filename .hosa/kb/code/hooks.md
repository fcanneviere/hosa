---
type: Module
title: hooks
description: Hosa — progress plan at session start. Reads `.hosa/kb/project/avancement.md`
resource: hooks
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-10-17T06:52:30Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `hooks/avancement.js` | Hosa — progress plan at session start. Reads `.hosa/kb/project/avancement.md` |
| `hooks/avancement.test.js` |  |
| `hooks/compress-output.js` |  |
| `hooks/compress-output.test.js` |  |
| `hooks/gate.js` |  |
| `hooks/gate.test.js` |  |
| `hooks/graph.js` |  |
| `hooks/graph.test.js` |  |
| `hooks/read-guard.js` |  |
| `hooks/read-guard.test.js` |  |
| `hooks/register.mjs` | Hosa — mod (Claude Code ≥ 2.1.290; older versions ignore it, the classic hooks still run). |
| `hooks/register.test.ts` |  |
| `hooks/session-start.js` |  |
| `hooks/subagent-start.js` |  |
| `hooks/subagent-start.test.js` |  |

## Symboles publics

- `kbLayoutNote` — `hooks/avancement.js:13` — tracked in the code branches (to migrate). Fast, read-only, never blocks.
- `kbLayoutNote.run` — `hooks/avancement.js:18`
- `resumeContext` — `hooks/avancement.js:29`
- `g` — `hooks/avancement.test.js:50`
- `kb` — `hooks/avancement.test.js:9`
- `clip` — `hooks/compress-output.js:23`
- `dedup` — `hooks/compress-output.js:66` — Same-session only: a fresh session's context doesn't hold the earlier copy.
- `elide` — `hooks/compress-output.js:100`
- `extractText` — `hooks/compress-output.js:25`
- `processPayload` — `hooks/compress-output.js:122` — Hook payload → replacement tool_response, or null to leave it untouched.
- `rebuild` — `hooks/compress-output.js:38` — returns {stdout, stderr, ...}, so hand back that shape or skip entirely.
- `scrub` — `hooks/compress-output.js:52`
- `spill` — `hooks/compress-output.js:87` — Full text goes to disk first so the elided middle is grep-able, not re-run.
- `stateDir` — `hooks/compress-output.js:22`
- `transform` — `hooks/compress-output.js:114`
- `call` — `hooks/compress-output.test.js:41`
- `commitGate` — `hooks/gate.js:67`
- `gitCalls` — `hooks/gate.js:37` — Each git call: its directory (cd and -C applied), subcommand and arguments.
- `mergeGate` — `hooks/gate.js:86`
- `native` — `hooks/gate.js:19`
- `processPayload` — `hooks/gate.js:102`
- `read` — `hooks/gate.js:54`
- `section` — `hooks/gate.js:57` — Body of the last `## <heading>` section (up to the next level-2 heading).
- `segments` — `hooks/gate.js:22` — Shell words grouped by command (split on && || ; | newline); quotes kept together.
- `bash` — `hooks/gate.test.js:18`
- `commit` — `hooks/gate.test.js:22`
- `denied` — `hooks/gate.test.js:19`
- `project` — `hooks/gate.test.js:9`
- `sprint` — `hooks/gate.test.js:53`
- `ticket` — `hooks/gate.test.js:21`
- `wt` — `hooks/gate.test.js:33`
- `broadIdentGrep` — `hooks/graph.js:68`
- `commandLine` — `hooks/graph.js:50`
- `findKbRoot` — `hooks/graph.js:39` — committed copy of `.hosa/kb` — skip it and keep walking up to the project root.
- `findUp` — `hooks/graph.js:30` — Closest ancestor of `dir` containing `marker` (a relative path), or null.
- `guardGrep` — `hooks/graph.js:74`
- `mtime` — `hooks/graph.js:104`
- `processPayload` — `hooks/graph.js:107` — Hook payload → hook output object, or null.
- `python` — `hooks/graph.js:24`
- `queryGraph` — `hooks/graph.js:57` — `graph.py find` output, or '' on failure/no hit. Stays under the 5 s hook timeout.
- `refreshSummary` — `hooks/graph.js:19` — Rewrites `.hosa/kb/sommaire.md` (one line per KB concept) in the background.
- `runGraph` — `hooks/graph.js:52`
- `sessionStart` — `hooks/graph.js:93` — (a full first build can exceed the hook timeout). Returns the context line, or ''.
- `deny` — `hooks/graph.test.js:57`
- `hit` — `hooks/graph.test.js:56`
- `project` — `hooks/graph.test.js:9`
- `processPayload` — `hooks/read-guard.js:19`
- `stateDir` — `hooks/read-guard.js:15`
- `stateFile` — `hooks/read-guard.js:16`
- `denied` — `hooks/read-guard.test.js:13`
- `read` — `hooks/read-guard.test.js:12`
- `readPlan` — `hooks/register.mjs:20` — Same reading as skills/status/scripts/avancement.py: `| \`stage\` | statut | … |` rows.
- `refresh` — `hooks/register.mjs:36` — The managed project's plan: a sprint worktree's `.hosa/kb` copy is stale, so start above it.
- `register` — `hooks/register.mjs:53`
- `showStatus` — `hooks/register.mjs:47`
- `project` — `hooks/register.test.ts:10` — Plan text per call, so a test can close a stage between turns.
- `row` — `hooks/register.test.ts:3`
- `step` — `hooks/register.test.ts:23`
- `processPayload` — `hooks/subagent-start.js:11`

## Tickets et exigences

Aucun.
