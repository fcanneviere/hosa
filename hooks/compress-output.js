#!/usr/bin/env node
// Hosa — PostToolUse hook. Shrinks oversized tool output before the model reads
// it. Reduced port of Chisle's compressor (MIT, github.com/JayPokale/Chisle,
// hooks/chisle-compress-output.js v3.5.0): scrub + dedup + recoverable elision.
// Deterministic, no network. Read/Edit/Write are never touched (their output
// feeds exact-match edits); Agent is excluded because `develop` parses subagent
// reports (e.g. `Files Changed`) and must see them whole.
// Kill switch: HOSA_COMPRESS=0.

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');

const SAFE_TOOLS = ['Bash', 'Grep', 'Glob', 'WebFetch', 'WebSearch'];
const MAX_CHARS = 8000, HEAD = 60, TAIL = 40;
const SCRUB_MIN = 1024, DEDUP_MIN = 2048, MIN_WIN = 64, REPEAT_MIN = 4;
const MAX_SALVAGED = 12, MAX_LINE = 300, SPILL_KEEP = 40;
const ANSI_RE = /\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)/g;
const SALVAGE_RE = /\b(error|err!|fail(ed|ure|ing)?|exception|traceback|panic|fatal|denied|refused|timed?[ _-]?out|assert(ion)?|segfault|cannot find|not found|warning)\b/i;

const stateDir = () => process.env.HOSA_STATE_DIR || path.join(os.tmpdir(), 'hosa-compress');
const clip = l => (l.length > MAX_LINE ? l.slice(0, MAX_LINE) + '…' : l);

function extractText(r) {
  if (r == null) return null;
  if (typeof r === 'string') return r;
  if (typeof r === 'object' && !Array.isArray(r)) {
    const parts = ['stdout', 'stderr', 'output', 'content', 'text', 'result']
      .map(k => r[k]).filter(v => typeof v === 'string' && v);
    return parts.length ? parts.join('\n') : null;
  }
  return null;
}

// Claude Code validates updatedToolOutput against the tool's schema: Bash
// returns {stdout, stderr, ...}, so hand back that shape or skip entirely.
function rebuild(r, updated) {
  if (typeof r === 'string') return updated;
  if (r && typeof r === 'object' && !Array.isArray(r)) {
    for (const k of ['stdout', 'output', 'content', 'text', 'result']) {
      if (typeof r[k] === 'string') {
        const out = { ...r, [k]: updated };
        if (k === 'stdout' && typeof r.stderr === 'string') out.stderr = ''; // already folded in
        return out;
      }
    }
  }
  return null;
}

function scrub(text) {
  const lines = text.replace(ANSI_RE, '').replace(/[ \t]+$/gm, '').replace(/\n{3,}/g, '\n\n').split('\n');
  const out = [];
  for (let i = 0; i < lines.length;) {
    let j = i;
    while (j < lines.length && lines[j] === lines[i]) j++;
    if (j - i >= REPEAT_MIN && lines[i].trim()) out.push(lines[i], `... [hosa: line repeated ${j - i}×] ...`);
    else out.push(...lines.slice(i, j));
    i = j;
  }
  return out.join('\n');
}

// Same-session only: a fresh session's context doesn't hold the earlier copy.
function dedup(tool, text, sessionId, toolUseId) {
  if (!sessionId || text.length < DEDUP_MIN) return null;
  try {
    const p = path.join(stateDir(), 'last.json');
    let s = {};
    try { s = JSON.parse(fs.readFileSync(p, 'utf8')) || {}; } catch (e) {}
    if (s.session !== sessionId) s = { session: sessionId, tools: {} };
    const hash = crypto.createHash('sha256').update(text).digest('hex');
    const prev = s.tools[tool] || {};
    const dup = prev.hash === hash && !(toolUseId && prev.id === toolUseId);
    s.tools[tool] = { hash, id: toolUseId || null };
    fs.mkdirSync(stateDir(), { recursive: true });
    fs.writeFileSync(p, JSON.stringify(s), { mode: 0o600 });
    if (!dup) return null;
    const lines = text.split('\n');
    return `[hosa: output identical to the previous ${tool} result — ${lines.length} lines, unchanged. First lines:]\n` +
      lines.slice(0, 5).map(clip).join('\n');
  } catch (e) { return null; }
}

// Full text goes to disk first so the elided middle is grep-able, not re-run.
function spill(text, tool) {
  try {
    const dir = path.join(stateDir(), 'spill');
    fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
    const file = path.join(dir, `${tool}-${crypto.createHash('sha256').update(text).digest('hex').slice(0, 12)}.txt`);
    if (!fs.existsSync(file)) fs.writeFileSync(file, text, { mode: 0o600 });
    fs.readdirSync(dir).map(f => path.join(dir, f))
      .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs)
      .slice(SPILL_KEEP).forEach(f => { try { fs.unlinkSync(f); } catch (e) {} });
    return file;
  } catch (e) { return null; }
}

function elide(text, spillPath) {
  const recover = spillPath ? ` Full output: ${spillPath} (grep it, do not re-run)` : '';
  const lines = text.split('\n');
  if (lines.length <= HEAD + TAIL) {
    const keep = MAX_CHARS / 2;
    return `${text.slice(0, keep)}\n... [hosa: elided ${text.length - 2 * keep} chars.${recover}] ...\n${text.slice(-keep)}`;
  }
  const middle = lines.slice(HEAD, -TAIL);
  const salvaged = middle.filter(l => SALVAGE_RE.test(l)).slice(0, MAX_SALVAGED).map(clip);
  const marker = `... [hosa: elided ${middle.length} lines, kept first ${HEAD}, last ${TAIL}` +
    (salvaged.length ? `, and ${salvaged.length} error-like line(s) below` : '') + `.${recover}] ...`;
  return [...lines.slice(0, HEAD), marker, ...salvaged, ...lines.slice(-TAIL)].join('\n');
}

function transform(text, tool) {
  if (!text || text.length <= SCRUB_MIN) return null;
  let t = scrub(text);
  if (t.length > MAX_CHARS) t = elide(t, spill(t, tool));
  return text.length - t.length >= MIN_WIN ? t : null;
}

// Hook payload → replacement tool_response, or null to leave it untouched.
function processPayload(p) {
  if (process.env.HOSA_COMPRESS === '0' || !p || !SAFE_TOOLS.includes(p.tool_name)) return null;
  const text = extractText(p.tool_response);
  if (!text) return null;
  const updated = dedup(p.tool_name, text, p.session_id, p.tool_use_id) || transform(text, p.tool_name);
  return updated && updated.length < text.length ? rebuild(p.tool_response, updated) : null;
}

if (require.main === module) {
  let input = '';
  process.stdin.on('data', c => { input += c; });
  process.stdin.on('end', () => {
    try {
      const updatedToolOutput = processPayload(JSON.parse(input.replace(/^﻿/, '')));
      if (updatedToolOutput != null) {
        process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: 'PostToolUse', updatedToolOutput } }));
      }
    } catch (e) {} // best-effort — never break the tool pipeline
  });
}

module.exports = { processPayload, scrub, elide, transform };
