#!/usr/bin/env node
// Hosa — budget barriers: the token rules measured on hosa-ui (2026-10) become refusals.
// - PreToolUse Skill, main session: a stage of the progress plan closed in this session and the
//   context is heavy → the next pipeline stage is refused once: /clear then « reprends »
//   (README « Une session par étape »). The retry passes: the user chose to stay.
// - Same refusal for any Hosa skill once the context passes CEILING, stage closed or not.
// - Same refusal for an agent dispatch (Agent, SendMessage): a stage orchestrated by agents never calls
//   Skill (rieki's backlog: 28 agents, main session up to 260 k without one refusal).
// - PreToolUse, in a hosa- subagent: at WARN of its cap of tool calls, or of AGENT_MAX tokens of context,
//   a reminder (the call itself runs); past either, every further call is refused but the final report
//   (SubagentHandback), so the agent ends with it and `## Reprise`.
// - SendMessage to an agent idle past IDLE with a heavy context: refused once — its cache is gone, the
//   message would write it all again; a fresh dispatch with its `## Reprise` costs less.
// - Agent, while a stage pipeline.json's `dispatch` declares is under way: more Hosa agents running than its
//   `parallel`, or an agent type off its `model`, is refused.
// SubagentStart records each agent's type, SubagentStop its end. Fail-open. Kill switch: HOSA_BUDGET=0.

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { findKbRoot } = require('./graph');

// ponytail: calibrated on hosa-ui and the pilot, same caps as usage_report.py's CAPS/CAP
const CAPS = { 'hosa-ux-designer': 50 };
const CAP = 150;
// An agent stopped dead at its cap loses the step under way: it is told early, once (« wrap up at 25 of 30 »,
// github.com/drona23/claude-token-efficient).
const WARN = 0.8;
const HEAVY = Number(process.env.HOSA_CONTEXTE_MAX) || 60000; // tokens: /clear restarts at 20-30 k
// Past it, any Hosa skill is refused once, then again every HEAVY more: `changement` closes no stage,
// and a pilot2 session chained four skills up to 244 k without a single refusal.
const CEILING = 2 * HEAVY;
// A subagent's context: rieki's backlog passes reached 273 k at 41 tool calls, far from any call cap.
const AGENT_MAX = Number(process.env.HOSA_AGENT_CONTEXTE_MAX) || 120000;
// A subagent's prompt cache lives 5 min (measured 2026-11-05): resumed later, its whole context is written again
// (rieki: 460 k written to resume one agent after the 5-hour limit).
const IDLE = 5 * 60 * 1000;
// An agent silent this long no longer counts as running (stopped by a limit, no SubagentStop).
const SILENT = 15 * 60 * 1000;
// The one stage graph (avancement.py reads it too).
function graph() {
  try {
    return JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'skills', 'status', 'scripts', 'pipeline.json'), 'utf8'));
  } catch (e) { return null; } // fail-open: no stage refusal, the ceiling still applies to hosa: skills
}
const GRAPH = graph();
const STAGES = GRAPH ? new Set([...GRAPH.pipelines.flatMap((p) => p.stages), ...GRAPH.sprint].map((s) => GRAPH.skill[s] || s))
  : new Set();
const DISPATCH = (GRAPH && GRAPH.dispatch) || {};

const stateDir = () => process.env.HOSA_STATE_DIR || path.join(os.tmpdir(), 'hosa-compress');
const hash = (s, n) => crypto.createHash('sha256').update(String(s)).digest('hex').slice(0, n);
const stateFile = (session, agent) => path.join(stateDir(), `budget-${hash(session, 12)}-${agent ? hash(agent, 8) : 'main'}.json`);
const load = (f) => { try { return JSON.parse(fs.readFileSync(f, 'utf8')) || {}; } catch (e) { return {}; } };
const save = (f, s) => { fs.mkdirSync(stateDir(), { recursive: true }); fs.writeFileSync(f, JSON.stringify(s), { mode: 0o600 }); };
const deny = (reason) => ({ hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny',
  permissionDecisionReason: `[hosa budget] ${reason}` } });

// The managed project's plan (a worktree's copy is stale: findKbRoot skips it).
function planText(cwd) {
  const root = findKbRoot(cwd);
  if (!root) return null;
  try { return fs.readFileSync(path.join(root, '.hosa', 'kb', 'project', 'avancement.md'), 'utf8'); } catch (e) { return null; }
}

// Stages done or ruled out in the plan.
function closedStages(cwd) {
  const text = planText(cwd);
  return text == null ? null : [...text.matchAll(/^\|\s*`?[\w-]+`?\s*\|\s*(fait|non applicable)\s*\|/gm)].length;
}

// A subagent's transcript: given by the hook, or `<session>/subagents/agent-<id>.jsonl` beside the main one.
function agentTranscript(p, id) {
  if (p.agent_transcript_path) return p.agent_transcript_path;
  const t = p.transcript_path;
  if (!t || !id) return null;
  if (path.basename(t).startsWith('agent-')) return t;
  return path.join(path.dirname(t), path.basename(t, '.jsonl'), 'subagents', `agent-${id}.jsonl`);
}

// Context of the last call, from the tail of a transcript: the main session's lines, or a subagent's (sidechain).
function contextTokens(transcript, sidechain = false) {
  let fd;
  try {
    fd = fs.openSync(transcript, 'r');
    const size = fs.fstatSync(fd).size;
    const len = Math.min(size, 512 * 1024);
    const buf = Buffer.alloc(len);
    fs.readSync(fd, buf, 0, len, size - len);
    const lines = buf.toString('utf8').split('\n');
    for (let i = lines.length - 1; i >= 0; i--) {
      if (!lines[i].includes('"usage"')) continue;
      try {
        const e = JSON.parse(lines[i]);
        const u = e.type === 'assistant' && !!e.isSidechain === sidechain && e.message && e.message.usage;
        if (u) return (u.input_tokens || 0) + (u.cache_creation_input_tokens || 0) + (u.cache_read_input_tokens || 0);
      } catch (e) {} // a line cut by the 512 KB window
    }
  } catch (e) {} finally { if (fd !== undefined) fs.closeSync(fd); }
  return 0;
}

// Past CEILING, refused once, then again every HEAVY more: `again` is what passes on the retry.
function ceilingGate(p, file, s, now, again, before = '') {
  if (now < CEILING || now < (s.ceiling || 0) + HEAVY) return null;
  save(file, { ...s, ceiling: now });
  return deny(`the context is at ${Math.round(now / 1000)} k tokens. ` +
    `Stop here and tell the user, in one line: « Pour économiser les tokens : /clear, puis « reprends » — le plan d'avancement garde tout. » ` +
    `Before that, ${before}record where you are: \`avancement.py reprise "<next action>"\` (or \`progress\` inside a stage). ` +
    `Only if the user answers they want to go on in this session, ${again} again: it will pass.`);
}

function stageGate(p) {
  const raw = String((p.tool_input || {}).skill || '');
  const skill = raw.split(':').pop();
  if (!STAGES.has(skill) && !/^hosa:/.test(raw)) return null;
  const closed = closedStages(p.cwd || process.cwd());
  if (closed == null) return null;
  const file = stateFile(p.session_id);
  const s = load(file);
  const now = contextTokens(p.transcript_path);
  const ceiling = ceilingGate(p, file, s, now, `invoke \`${raw}\``);
  if (ceiling) return ceiling;
  if (!STAGES.has(skill)) return null;
  if (s.closed == null) { save(file, { ...s, closed }); return null; }
  if (closed <= s.closed || s.refused === closed) return null;
  const tokens = now;
  if (tokens < HEAVY) return null;
  save(file, { ...s, refused: closed });
  return deny(`a stage closed in this session and its context is at ${Math.round(tokens / 1000)} k tokens. ` +
    `Stop here and tell the user, in one line: « Pour économiser les tokens : /clear, puis « reprends » — le plan d'avancement garde tout. » ` +
    `Only if the user answers they want to go on in this session, invoke \`${skill}\` again: it will pass.`);
}

function agentGate(p) {
  const file = stateFile(p.session_id, p.agent_id);
  const s = load(file);
  const type = String(p.agent_type || s.type || '').split(':').pop();
  if (!/^hosa-/.test(type)) return null;
  if (p.tool_name === 'SubagentHandback') return null; // the final report: refusing it loses the pass
  const calls = (s.calls || 0) + 1;
  const cap = CAPS[type] || CAP;
  const ctx = contextTokens(agentTranscript(p, p.agent_id), true);
  const k = Math.round(ctx / 1000);
  const warn = !s.warned && (calls >= Math.floor(cap * WARN) || ctx >= AGENT_MAX * WARN);
  save(file, { type, calls, warned: s.warned || warn });
  const report = 'write your final report with what is done, and under `## Reprise` what is left and the files to read';
  if (calls > cap || ctx >= AGENT_MAX) {
    return deny(`this ${type} pass reached its cap of ` + (calls > cap ? `${cap} tool calls` :
      `${Math.round(AGENT_MAX / 1000)} k tokens of context (${k} k)`) + `. Stop now: no more tools — ${report}, ` +
      'so a fresh dispatch continues.');
  }
  if (!warn) return null;
  return { hookSpecificOutput: { hookEventName: 'PreToolUse', additionalContext: `[hosa budget] this ${type} pass has ` +
    (calls >= Math.floor(cap * WARN) ? `${cap - calls} tool calls left (cap ${cap})` :
      `${k} k tokens of context (cap ${Math.round(AGENT_MAX / 1000)} k)`) +
    `. Finish the step under way, start no new one, then ${report}.` } };
}

// Hosa agents of this session still running: started, not stopped, active within SILENT.
function running(session) {
  const prefix = path.basename(stateFile(session)).replace(/main\.json$/, '');
  let n = 0;
  try {
    for (const f of fs.readdirSync(stateDir())) {
      if (!f.startsWith(prefix) || f.endsWith('main.json')) continue;
      const full = path.join(stateDir(), f);
      const s = load(full);
      if (/(^|:)hosa-/.test(s.type || '') && !s.stopped && Date.now() - fs.statSync(full).mtimeMs < SILENT) n++;
    }
  } catch (e) {}
  return n;
}

// The main session dispatches: the ceiling, then an old agent's resume, then the stage's `dispatch` rules.
function dispatchGate(p) {
  const text = planText(p.cwd || process.cwd());
  if (text == null) return null;
  const file = stateFile(p.session_id);
  const s = load(file);
  const input = p.tool_input || {};
  const ceiling = ceilingGate(p, file, s, contextTokens(p.transcript_path), 'dispatch',
    'let the agents still running hand back, then ');
  if (ceiling) return ceiling;
  if (p.tool_name === 'SendMessage') {
    const to = String(input.to || '');
    const t = agentTranscript({ transcript_path: p.transcript_path }, to);
    let idle = 0;
    try { idle = Date.now() - fs.statSync(t).mtimeMs; } catch (e) { return null; }
    const ctx = contextTokens(t, true);
    const resumed = s.resumed || {};
    if (idle < IDLE || ctx < HEAVY || resumed[to]) return null;
    save(file, { ...s, resumed: { ...resumed, [to]: true } });
    return deny(`agent ${to} has been idle ${Math.round(idle / 60000)} min with ${Math.round(ctx / 1000)} k tokens of context: ` +
      `a subagent's cache lasts 5 min, this message would write its ${Math.round(ctx / 1000)} k again. Dispatch a fresh agent ` +
      'of its type instead, given its `## Reprise` (or its task in `avancement.py show`) and the files it wrote. ' +
      'Only if the user wants this agent itself resumed, send again: it will pass.');
  }
  const type = String(input.subagent_type || '').split(':').pop();
  if (!/^hosa-/.test(type)) return null;
  const stage = Object.keys(DISPATCH).find((st) =>
    new RegExp(`^\\|\\s*\`?${st}\`?\\s*\\|\\s*en cours\\s*\\|`, 'm').test(text));
  if (!stage) return null;
  const rule = DISPATCH[stage];
  const model = (rule.model || {})[type];
  if (model && input.model !== model) {
    return deny(`during \`${stage}\`, \`${type}\` runs on ${model} (pipeline.json \`dispatch\`): dispatch again with model: "${model}".`);
  }
  const n = running(p.session_id);
  if (rule.parallel && n >= rule.parallel) {
    return deny(`${n} Hosa agents are running during \`${stage}\`, ${rule.parallel} at most (pipeline.json \`dispatch\`): ` +
      'wait for one to hand back, then dispatch this one.');
  }
  return null;
}

function processPayload(p) {
  if (process.env.HOSA_BUDGET === '0' || !p || !p.session_id) return null;
  if (p.hook_event_name === 'SubagentStart') {
    if (p.agent_id && p.agent_type) save(stateFile(p.session_id, p.agent_id), { type: p.agent_type, calls: 0 });
    return null;
  }
  if (p.hook_event_name === 'SubagentStop') {
    if (p.agent_id) {
      const file = stateFile(p.session_id, p.agent_id);
      save(file, { ...load(file), stopped: true });
    }
    return null;
  }
  if (p.agent_id) return agentGate(p);
  if (p.tool_name === 'Skill') return stageGate(p);
  return ['Agent', 'Task', 'SendMessage'].includes(p.tool_name) ? dispatchGate(p) : null;
}

module.exports = { processPayload, contextTokens };

if (require.main === module) {
  let input = '';
  process.stdin.on('data', (c) => { input += c; });
  process.stdin.on('end', () => {
    try {
      const out = processPayload(JSON.parse(input.replace(/^﻿/, '')));
      if (out) process.stdout.write(JSON.stringify(out));
    } catch (e) {} // fail-open
  });
}
