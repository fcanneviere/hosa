#!/usr/bin/env node
// Hosa — budget barriers: the token rules measured on hosa-ui (2026-10) become refusals.
// - PreToolUse Skill, main session: a stage of the progress plan closed in this session and the
//   context is heavy → the next pipeline stage is refused once: /clear then « reprends »
//   (README « Une session par étape »). The retry passes: the user chose to stay.
// - PreToolUse, in a hosa- subagent: past its cap of tool calls, every further call is refused
//   but the final report (SubagentHandback), so the agent ends with it and `## Reprise`.
// SubagentStart records each agent's type. Fail-open. Kill switch: HOSA_BUDGET=0.

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { findKbRoot } = require('./graph');

// ponytail: calibrated on hosa-ui and the pilot, same caps as usage_report.py's CAPS/CAP
const CAPS = { 'hosa-ux-designer': 50 };
const CAP = 150;
const HEAVY = Number(process.env.HOSA_CONTEXTE_MAX) || 60000; // tokens: /clear restarts at 20-30 k
const STAGES = new Set(['hosa', 'interview', 'redaction', 'fondamentaux', 'juridique', 'securite', 'relecture', 'contestation',
  'stack', 'infra', 'donnees', 'schema-app', 'schema-db', 'architecture', 'interface', 'backlog',
  'sprint', 'qa-plan', 'git', 'develop', 'qa', 'validation', 'bilan-sprint', 'livraison']);

const stateDir = () => process.env.HOSA_STATE_DIR || path.join(os.tmpdir(), 'hosa-compress');
const hash = (s, n) => crypto.createHash('sha256').update(String(s)).digest('hex').slice(0, n);
const stateFile = (session, agent) => path.join(stateDir(), `budget-${hash(session, 12)}-${agent ? hash(agent, 8) : 'main'}.json`);
const load = (f) => { try { return JSON.parse(fs.readFileSync(f, 'utf8')) || {}; } catch (e) { return {}; } };
const save = (f, s) => { fs.mkdirSync(stateDir(), { recursive: true }); fs.writeFileSync(f, JSON.stringify(s), { mode: 0o600 }); };
const deny = (reason) => ({ hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny',
  permissionDecisionReason: `[hosa budget] ${reason}` } });

// Stages done or ruled out in the managed project's plan (a worktree's copy is stale: findKbRoot skips it).
function closedStages(cwd) {
  const root = findKbRoot(cwd);
  if (!root) return null;
  try {
    const text = fs.readFileSync(path.join(root, '.hosa', 'kb', 'project', 'avancement.md'), 'utf8');
    return [...text.matchAll(/^\|\s*`?[\w-]+`?\s*\|\s*(fait|non applicable)\s*\|/gm)].length;
  } catch (e) { return null; }
}

// Context of the main session's last call, from the tail of its transcript.
function contextTokens(transcript) {
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
        const u = e.type === 'assistant' && !e.isSidechain && e.message && e.message.usage;
        if (u) return (u.input_tokens || 0) + (u.cache_creation_input_tokens || 0) + (u.cache_read_input_tokens || 0);
      } catch (e) {} // a line cut by the 512 KB window
    }
  } catch (e) {} finally { if (fd !== undefined) fs.closeSync(fd); }
  return 0;
}

function stageGate(p) {
  const skill = String((p.tool_input || {}).skill || '').split(':').pop();
  if (!STAGES.has(skill)) return null;
  const closed = closedStages(p.cwd || process.cwd());
  if (closed == null) return null;
  const file = stateFile(p.session_id);
  const s = load(file);
  if (s.closed == null) { save(file, { closed }); return null; }
  if (closed <= s.closed || s.refused === closed) return null;
  const tokens = contextTokens(p.transcript_path);
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
  save(file, { type, calls });
  const cap = CAPS[type] || CAP;
  if (calls <= cap) return null;
  return deny(`this ${type} pass reached its cap of ${cap} tool calls. Stop now: no more tools. Write your final report ` +
    'with what is done, and under `## Reprise` what is left and the files to read, so a fresh dispatch continues.');
}

function processPayload(p) {
  if (process.env.HOSA_BUDGET === '0' || !p || !p.session_id) return null;
  if (p.hook_event_name === 'SubagentStart') {
    if (p.agent_id && p.agent_type) save(stateFile(p.session_id, p.agent_id), { type: p.agent_type, calls: 0 });
    return null;
  }
  if (p.agent_id) return agentGate(p);
  return p.tool_name === 'Skill' ? stageGate(p) : null;
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
