#!/usr/bin/env node
// Hosa — budget barriers: the token rules measured on hosa-ui (2026-10) become refusals.
// - PreToolUse Skill, main session: a stage of the progress plan closed in this session and the
//   context is heavy → the next pipeline stage is refused once: /clear then « reprends »
//   (README « Une session par étape »). The retry passes: the user chose to stay.
// - Same refusal for any Hosa skill once the context passes start + CEILING, stage closed or not.
// - Same refusal for an agent dispatch (Agent, SendMessage): a stage orchestrated by agents never calls
//   Skill (rieki's backlog: 28 agents, main session up to 260 k without one refusal).
// - PreToolUse, in a hosa- subagent: at WARN of its cap of tool calls, or of AGENT_MAX tokens of context,
//   a reminder (the call itself runs); past either, every further call is refused but the final report
//   (SubagentHandback), so the agent ends with it and `## Reprise`.
// - SendMessage to an agent idle past IDLE with a heavy context: refused once — its cache is gone, the
//   message would write it all again; a fresh dispatch with its `## Reprise` costs less.
// - Agent, while a stage pipeline.json's `dispatch` declares is under way: more Hosa agents running than its
//   `parallel`, or an agent type off its `model`, is refused.
// - UserPromptSubmit, main session: a message sent after a pause longer than the prompt cache lives, in a heavy
//   session, is refused once — it would write the whole context again; /clear then « reprends » writes 17 k.
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
// The main session's thresholds count above its start: a /clear saves only what grew since. The start moved
// from 29 k to 54 k on 2026-11-08 (Claude Code's system prompt and tools, not Hosa), and an absolute 50 k then
// refused after every stage. 45 % of the main context was spent past 120 k (rieki, pilot2).
const HEAVY = Number(process.env.HOSA_CONTEXTE_MARGE) || 20000;
// Past start + CEILING, any Hosa skill is refused once, then again every STEP more: `changement` closes no stage,
// and a pilot2 session chained four skills up to 244 k without a single refusal.
const CEILING = 70000;
const STEP = 50000;
// The start when the transcript gives none (the pre-2026-11-08 one).
const START = 30000;
// An agent's context past which an idle one is not resumed: agents start at 16 k, their own floor.
const AGENT_RESUME = 50000;
// A subagent's context: rieki's backlog passes reached 273 k at 41 tool calls, far from any call cap.
const AGENT_MAX = Number(process.env.HOSA_AGENT_CONTEXTE_MAX) || 120000;
// A subagent's prompt cache lives 5 min (measured 2026-11-05): resumed later, its whole context is written again
// (rieki: 460 k written to resume one agent after the 5-hour limit).
const IDLE = 5 * 60 * 1000;
// An agent silent this long no longer counts as running (stopped by a limit, no SubagentStop).
const SILENT = 15 * 60 * 1000;
// The main session's prompt cache lives 1 h (rieki, 2026-11: every call writes `ephemeral_1h`). A message sent after
// a longer pause writes the whole context again, at twice the price of plain input: on rieki 9 such messages wrote
// 1.2 M tokens (up to 197 k at once), where the first call after a /clear writes 17 k.
const PAUSE = (Number(process.env.HOSA_PAUSE_MIN) || 60) * 60 * 1000;
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
const { REPORT_MAX } = require('./subagent-start'); // the agents are told the same value

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

// The last call, from the tail of a transcript — the main session's lines, or a subagent's (sidechain): its context
// and its time.
function lastCall(transcript, sidechain = false) {
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
        if (u) {
          return { tokens: (u.input_tokens || 0) + (u.cache_creation_input_tokens || 0) + (u.cache_read_input_tokens || 0),
            at: Date.parse(e.timestamp) || 0 };
        }
      } catch (e) {} // a line cut by the 512 KB window
    }
  } catch (e) {} finally { if (fd !== undefined) fs.closeSync(fd); }
  return { tokens: 0, at: 0 };
}
const contextTokens = (transcript, sidechain = false) => lastCall(transcript, sidechain).tokens;

// Context of the session's first call, from the head of its transcript (the start after /clear).
function startTokens(transcript) {
  let fd;
  try {
    fd = fs.openSync(transcript, 'r');
    const chunk = Buffer.alloc(256 * 1024);
    let rest = '';
    for (let pos = 0, n; pos < 4 * 1024 * 1024 && (n = fs.readSync(fd, chunk, 0, chunk.length, pos)) > 0; pos += n) {
      const lines = (rest + chunk.toString('utf8', 0, n)).split('\n');
      rest = lines.pop();
      for (const line of lines) {
        if (!line.includes('"usage"')) continue;
        try {
          const e = JSON.parse(line);
          const u = e.type === 'assistant' && !e.isSidechain && e.message && e.message.usage;
          if (u) return (u.input_tokens || 0) + (u.cache_creation_input_tokens || 0) + (u.cache_read_input_tokens || 0);
        } catch (e) {}
      }
    }
  } catch (e) {} finally { if (fd !== undefined) fs.closeSync(fd); }
  return 0;
}

// The session's start, read once and kept in its state.
function sessionStart(p, file, s) {
  if (s.start) return s.start;
  const start = startTokens(p.transcript_path);
  if (!start) return START;
  save(file, { ...s, start });
  return start;
}

// Past start + CEILING, refused once, then again every STEP more: `again` is what passes on the retry.
function ceilingGate(p, file, s, now, again, before = '') {
  const start = sessionStart(p, file, s);
  s = load(file);
  if (now < start + CEILING || now < (s.ceiling || 0) + STEP) return null;
  save(file, { ...s, ceiling: now });
  return deny(`the context is at ${Math.round(now / 1000)} k tokens. ` +
    `Stop here and tell the user, in one line: « Pour économiser les tokens : /clear, puis « reprends » — le plan d'avancement garde tout. » ` +
    `Before that, ${before}record where you are: \`avancement.py reprise "<next action>"\` (or \`progress\` inside a stage). ` +
    `Only if the user answers they want to go on in this session, ${again} again: it will pass.`);
}

// A message after a pause longer than the cache: refused once per pause, before the call that would pay for it.
// The refusal erases the message: it is given back, to send again. A slash command passes (/clear, /compact).
function pauseGate(p) {
  const prompt = String(p.prompt || '').trim();
  if (!prompt || prompt.startsWith('/') || planText(p.cwd || process.cwd()) == null) return null;
  const { tokens, at } = lastCall(p.transcript_path);
  const idle = Date.now() - at;
  if (!at || idle < PAUSE) return null;
  const file = stateFile(p.session_id);
  const s = load(file);
  const start = sessionStart(p, file, s);
  if (tokens < start + HEAVY || s.pause === at) return null;
  save(file, { ...load(file), pause: at });
  const k = (n) => Math.round(n / 1000);
  const h = idle >= 3600000 ? `${Math.floor(idle / 3600000)} h ${String(Math.round((idle % 3600000) / 60000)).padStart(2, '0')}` : `${Math.round(idle / 60000)} min`;
  return { decision: 'block', reason: `[hosa budget] Pause de ${h} : le cache de cette session a expiré. Ce message ferait réécrire ` +
    `tout son contexte, ${k(tokens)} k tokens au prix fort. Fais plutôt /clear, puis « reprends » : la session repart de ` +
    `${k(start)} k et le plan d'avancement garde tout. Pour continuer ici quand même, renvoie ton message, il passera : ` +
    `« ${prompt.length > 300 ? `${prompt.slice(0, 300)}…` : prompt} »` };
}

function stageGate(p) {
  const raw = String((p.tool_input || {}).skill || '');
  const skill = raw.split(':').pop();
  if (!STAGES.has(skill) && !/^hosa:/.test(raw)) return null;
  const closed = closedStages(p.cwd || process.cwd());
  if (closed == null) return null;
  const file = stateFile(p.session_id);
  const now = contextTokens(p.transcript_path);
  const ceiling = ceilingGate(p, file, load(file), now, `invoke \`${raw}\``);
  if (ceiling) return ceiling;
  if (!STAGES.has(skill)) return null;
  const s = load(file);
  if (s.closed == null) { save(file, { ...s, closed }); return null; }
  if (closed <= s.closed || s.refused === closed) return null;
  const start = sessionStart(p, file, s);
  if (now < start + HEAVY) return null;
  save(file, { ...load(file), refused: closed });
  return deny(`a stage closed in this session and its context is at ${Math.round(now / 1000)} k tokens ` +
    `(${Math.round((now - start) / 1000)} k since its start). ` +
    `Stop here and tell the user, in one line: « Pour économiser les tokens : /clear, puis « reprends » — le plan d'avancement garde tout. » ` +
    `Only if the user answers they want to go on in this session, invoke \`${skill}\` again: it will pass.`);
}

// An agent whose tools hold Write can move its details into a file; the others' report is their deliverable
// (hosa-challenger, hosa-reviewer, hosa-tech-lead).
function canWrite(type) {
  try {
    const head = fs.readFileSync(path.join(__dirname, '..', 'agents', `${type.replace(/^hosa-/, '')}.md`), 'utf8').split('\n---', 1)[0];
    return /^tools:.*\bWrite\b/m.test(head);
  } catch (e) { return false; } // fail-open: no refusal
}

// The final report stays in the main session's context until its /clear, re-read on every later call:
// longer than REPORT_MAX besides `## Open Questions` and `## Reprise` (kept whole), it is refused once.
function reportGate(p, file, s, type) {
  if (s.reportRefused || !canWrite(type)) return null;
  if ((s.calls || 0) >= (CAPS[type] || CAP)) return null; // at its cap the agent can't write a file any more
  const body = String((p.tool_input || {}).message || '')
    .replace(/^## (Open Questions|Reprise)\b[\s\S]*?(?=^## |(?![\s\S]))/gm, '');
  if (body.length <= REPORT_MAX) return null;
  if (contextTokens(agentTranscript(p, p.agent_id), true) >= AGENT_MAX) return null; // same: its tools are refused
  save(file, { ...s, reportRefused: true });
  return deny(`this report is ${body.length} characters besides \`## Open Questions\` and \`## Reprise\` (${REPORT_MAX} at most): ` +
    'it stays in the main session\'s context and is re-read on every later call. Move the details into the files you wrote ' +
    '(or one file next to them), keep `## En bref`, the paths written, `## Open Questions` and `## Reprise` in full, ' +
    'then call SubagentHandback again. Nothing to move (the report is the deliverable)? Call it again unchanged: it will pass.');
}

function agentGate(p) {
  const file = stateFile(p.session_id, p.agent_id);
  const s = load(file);
  const type = String(p.agent_type || s.type || '').split(':').pop();
  if (!/^hosa-/.test(type)) return null;
  if (p.tool_name === 'SubagentHandback') return reportGate(p, file, s, type);
  const calls = (s.calls || 0) + 1;
  const cap = CAPS[type] || CAP;
  const ctx = contextTokens(agentTranscript(p, p.agent_id), true);
  const k = Math.round(ctx / 1000);
  const warn = !s.warned && (calls >= Math.floor(cap * WARN) || ctx >= AGENT_MAX * WARN);
  save(file, { ...s, type, calls, warned: s.warned || warn });
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
  const input = p.tool_input || {};
  const ceiling = ceilingGate(p, file, load(file), contextTokens(p.transcript_path), 'dispatch',
    'let the agents still running hand back, then ');
  if (ceiling) return ceiling;
  const s = load(file);
  if (p.tool_name === 'SendMessage') {
    const to = String(input.to || '');
    const t = agentTranscript({ transcript_path: p.transcript_path }, to);
    let idle = 0;
    try { idle = Date.now() - fs.statSync(t).mtimeMs; } catch (e) { return null; }
    const ctx = contextTokens(t, true);
    const resumed = s.resumed || {};
    if (idle < IDLE || ctx < AGENT_RESUME || resumed[to]) return null;
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

// What each dispatch is for, so the resume card names an agent still running after a /clear (rieki, 0.1.78: an
// agent dispatched without `task add` was dispatched again by the next session, then stopped). The main session's
// Agent call knows the description, SubagentStart the agent's id: the oldest pending dispatch of its type is its.
const pendingFile = (session) => path.join(stateDir(), `pending-${hash(session, 12)}.json`);
const short = (type) => String(type || '').split(':').pop();

function recordDispatch(p) {
  const input = p.tool_input || {};
  const type = short(input.subagent_type);
  if (!/^hosa-/.test(type)) return;
  const list = load(pendingFile(p.session_id)).list || [];
  list.push({ type, what: String(input.description || '').slice(0, 120), at: Date.now() });
  save(pendingFile(p.session_id), { list: list.filter((d) => Date.now() - d.at < SILENT) });
}

function takeDispatch(session, type) {
  const list = load(pendingFile(session)).list || [];
  const i = list.findIndex((d) => d.type === short(type));
  if (i < 0) return '';
  const [d] = list.splice(i, 1);
  save(pendingFile(session), { list });
  return d.what;
}

function processPayload(p) {
  if (process.env.HOSA_BUDGET === '0' || !p || !p.session_id) return null;
  if (p.hook_event_name === 'UserPromptSubmit') return p.agent_id ? null : pauseGate(p);
  if (p.hook_event_name === 'SubagentStart') {
    if (p.agent_id && p.agent_type) {
      let kb = null;
      try { const r = findKbRoot(p.cwd || process.cwd()); kb = r && path.join(r, '.hosa', 'kb'); } catch (e) {}
      save(stateFile(p.session_id, p.agent_id), { type: p.agent_type, calls: 0, kb, started: Date.now(),
        what: takeDispatch(p.session_id, p.agent_type) });
    }
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
  if (!['Agent', 'Task', 'SendMessage'].includes(p.tool_name)) return null;
  const out = dispatchGate(p);
  if (!out && p.tool_name !== 'SendMessage') recordDispatch(p);
  return out;
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
