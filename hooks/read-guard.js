#!/usr/bin/env node
// Hosa — re-read guard. Port of token-optimizer-mcp's main win (MIT,
// github.com/ooples/token-optimizer-mcp): a full Read of a file already read in
// this context and unchanged since (same mtime + size) is refused once, the
// content is already above. Partial reads (offset/limit/pages) pass through.
// Keyed by session + agent_id: a subagent has its own context. PreCompact wipes
// the session state (compaction drops the earlier copies).
// Size guard (« skip files over 100KB unless required », github.com/drona23/claude-token-efficient): a
// first full Read of a file over BIG bytes is refused once too, for the part the task needs. Images are
// resized by the Read tool, a PDF needs its pages; `sommaire.md` is the KB's entry point, read whole.
// Bash reads (`cat`, `head`, `sed -n a,bp`, `grep -r`) by a `hosa-*` agent in a Hosa project get the same guards:
// measured on pilot2 and rieki (2026-11), agents read through Bash, which no guard saw — 4 668 reads, about a
// quarter of their context; 1 772 files read twice or more by the same agent; 17 agents of 708 queried the graph.
// A command is refused once when it re-reads an unchanged file or range (by Read or Bash), prints more than
// BASH_BIG bytes of files (→ `<hosa> lire`, `kb_query`), or greps the whole tree for an identifier the graph
// locates (the answer in the refusal). Its retry, same text, passes. Output piped or redirected, heredocs and
// variables it can't resolve are left alone: the guard reads what it can name, never more.
// Fail-open; a retry after refusal always passes. Kill switch: HOSA_READ_GUARD=0.

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { findKbRoot, findUp, guardGrep, queryGraph, IDENT_RE } = require('./graph');
const { walk, native } = require('./gate');

const stateDir = () => process.env.HOSA_STATE_DIR || path.join(os.tmpdir(), 'hosa-compress');
const stateFile = (session, agent) => path.join(stateDir(),
  `reads-${crypto.createHash('sha256').update(String(session)).digest('hex').slice(0, 12)}-${agent ? crypto.createHash('sha256').update(String(agent)).digest('hex').slice(0, 8) : 'main'}.json`);
// ponytail: about 10 k tokens; on pilot2 only `sommaire.md` (52 KB) went past it, recalibrate on real reads
const BIG = Number(process.env.HOSA_READ_MAX) || 40000;
const WHOLE = /\.(png|jpe?g|gif|webp|bmp|pdf)$|(^|[\\/])sommaire\.md$/i;
const deny = (reason) => ({ hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny',
  permissionDecisionReason: `[hosa] ${reason}` } });

// One key per file whichever tool names it: `C:\x` (Read) and `/c/x` or `c:/x` (Bash).
const keyOf = (f) => { const r = path.resolve(native(f)); return process.platform === 'win32' ? r.toLowerCase() : r; };
const load = (file) => { try { return JSON.parse(fs.readFileSync(file, 'utf8')) || {}; } catch (e) { return {}; } };
const store = (file, s) => { fs.mkdirSync(stateDir(), { recursive: true }); fs.writeFileSync(file, JSON.stringify(s), { mode: 0o600 }); };

// --- Bash reads -------------------------------------------------------------------------------------------
// ponytail: about 5 k tokens; one Bash command often prints several files (a `for` over the tickets)
const BASH_BIG = Number(process.env.HOSA_BASH_READ_MAX) || 20000;
const OPT_ARG = /^-(?:[ABCmefd]|-include|-exclude|-exclude-dir|-max-count|-context|-after-context|-before-context|-regexp|-file|-glob|-type|-g|t)$/;

// A word with `*` in its last part only → the files it names, sorted like bash; otherwise the word itself.
function glob(word, dir) {
  const base = path.basename(word);
  if (!base.includes('*') || path.dirname(word).includes('*')) return [word];
  const d = path.resolve(dir, native(path.dirname(word)));
  const re = new RegExp(`^${base.replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*')}$`);
  try { return fs.readdirSync(d).filter((n) => re.test(n)).sort().map((n) => path.join(d, n)); } catch (e) { return []; }
}

// The files a command prints whole or in part, and the patterns it greps the whole tree for — or null.
// Reads through `cd`, `K="…"` assignments and `for f in …; do … done` loops; skips what it can't name.
function bashReads(cmd, cwd) {
  if (/<</.test(cmd)) return null; // a heredoc's lines are not commands
  const vars = {}, reads = [], greps = [];
  let loop = null;
  const expand = (w, dir) => {
    let outs = [w];
    for (const n of new Set([...w.matchAll(/\$\{?(\w+)\}?/g)].map((m) => m[1]))) {
      const vals = loop && loop.name === n ? loop.values : n in vars ? [vars[n]] : null;
      if (!vals) return null;
      const re = new RegExp(`\\$\\{?${n}\\}?`, 'g');
      outs = outs.flatMap((o) => vals.map((v) => o.replace(re, () => v)));
    }
    return outs.flatMap((o) => glob(o, dir));
  };
  walk(cmd, cwd, false, (seg, dir) => {
    let w = [...seg];
    if (w[0] === 'export') w.shift();
    if (w.length === 1 && /^\w+=/.test(w[0])) {
      const [n, ...v] = w[0].split('=');
      const e = expand(v.join('='), dir);
      if (e && e.length === 1) vars[n] = e[0]; else delete vars[n];
      return;
    }
    if (w[0] === 'for' && w[2] === 'in') {
      const values = w.slice(3).map((x) => expand(x, dir));
      loop = { name: w[1], values: values.includes(null) ? null : values.flat() };
      return;
    }
    if (w[0] === 'done') { loop = null; return; }
    while (/^(do|then|else|elif|if|time)$/.test(w[0]) || /^\w+=/.test(w[0] || '')) w.shift();
    const name = path.basename(String(w[0] || '')).toLowerCase();
    const args = w.slice(1);
    const files = (list) => {
      const out = [];
      for (const a of list) {
        const e = expand(a, dir);
        if (!e) continue;
        for (const f of e) {
          const full = path.resolve(dir, native(f));
          try { if (fs.statSync(full).isFile()) out.push(full); } catch (err) {}
        }
      }
      return out;
    };
    if (name === 'grep' || name === 'rg') {
      const flags = args.filter((a) => /^-[^-]/.test(a)).join('');
      if (name === 'grep' && !/[rR]/.test(flags) && !args.includes('--recursive')) return;
      const rest = [];
      let pattern = null;
      for (let k = 0; k < args.length; k++) {
        if (args[k] === '-e' || args[k] === '--regexp') { pattern = args[++k]; continue; }
        if (OPT_ARG.test(args[k])) { k++; continue; }
        if (args[k].startsWith('-')) continue;
        if (pattern == null) pattern = args[k]; else rest.push(args[k]);
      }
      const targets = rest.length ? rest.map((r) => path.resolve(dir, native(r))) : [dir];
      const isDir = (t) => { try { return fs.statSync(t).isDirectory(); } catch (e) { return false; } };
      // the graph indexes the code: a grep in the KB (`.hosa/`) is not one it answers
      const inKb = targets.some((t) => /[\\/]\.hosa([\\/]|$)/.test(t));
      if (pattern && IDENT_RE.test(pattern) && !inKb && targets.some(isDir)) greps.push(pattern);
      return;
    }
    // output piped (`cat f | head`) or redirected (`> f`): not what lands in the context
    if (seg.pipeOut || args.some((a) => /^(>|1>)/.test(a))) return;
    if (name === 'cat') {
      for (const f of files(args.filter((a) => !a.startsWith('-')))) reads.push({ file: f, a: 1, b: null });
    } else if (name === 'head') {
      let n = 10;
      const rest = [];
      for (let k = 0; k < args.length; k++) {
        const m = /^-(?:n)?(\d+)$/.exec(args[k]) || /^--lines=(\d+)$/.exec(args[k]);
        if (m) n = Number(m[1]);
        else if (args[k] === '-n') n = Number(args[++k]);
        else if (args[k].startsWith('-')) return; // -c (bytes), a negative count: left alone
        else rest.push(args[k]);
      }
      if (n > 0) for (const f of files(rest)) reads.push({ file: f, a: 1, b: n });
    } else if (name === 'sed') {
      if (!args.includes('-n')) return;
      const rest = args.filter((a) => !a.startsWith('-'));
      const m = /^(\d+)(?:,(\d+|\$))?p$/.exec(rest.shift() || '');
      if (!m) return;
      const a = Number(m[1]);
      const b = m[2] === '$' ? null : m[2] ? Number(m[2]) : a;
      for (const f of files(rest)) reads.push({ file: f, a, b });
    }
  });
  return { reads, greps };
}

const sliceOf = (file, a, b) => fs.readFileSync(file, 'utf8').split('\n').slice(a - 1, b == null ? undefined : b).join('\n');

function bashGuard(p, query = queryGraph) {
  if (!p.agent_id || (p.agent_type && !/(^|:)hosa-/.test(p.agent_type))) return null;
  const cmd = (p.tool_input || {}).command;
  const cwd = native(p.cwd || process.cwd());
  if (!cmd || !findKbRoot(cwd)) return null;
  const file = stateFile(p.session_id, p.agent_id);
  const s = load(file);
  const h = crypto.createHash('sha256').update(cmd).digest('hex').slice(0, 16);
  const retry = s['~retry'] === h;
  const found = bashReads(cmd, cwd);
  if (!found) return null;
  const again = [], fresh = [];
  let bytes = 0;
  for (const r of found.reads) {
    try {
      const st = fs.statSync(r.file);
      r.sig = `${st.mtimeMs}:${st.size}`;
      r.key = keyOf(r.file);
      const whole = s[r.key], parts = s[`range:${r.key}`];
      const covered = (whole && whole.sig === r.sig) ||
        (r.b != null && parts && parts.sig === r.sig && parts.ranges.some(([x, y]) => x <= r.a && r.b <= y));
      if (covered) { again.push(r); continue; }
      r.bytes = r.b == null && r.a === 1 ? st.size : Buffer.byteLength(sliceOf(r.file, r.a, r.b));
      fresh.push(r);
      if (!WHOLE.test(r.file)) bytes += r.bytes;
    } catch (e) {}
  }
  const remember = () => {
    for (const r of fresh) {
      if (r.b == null && r.a === 1) { s[r.key] = { sig: r.sig, refused: false }; continue; }
      const k = `range:${r.key}`;
      const ranges = s[k] && s[k].sig === r.sig ? s[k].ranges : [];
      ranges.push([r.a, r.b == null ? 1e9 : r.b]); // JSON has no Infinity
      s[k] = { sig: r.sig, ranges };
    }
  };
  if (retry) { delete s['~retry']; remember(); store(file, s); return null; }
  const reasons = [];
  if (again.length) {
    reasons.push('Already read in this pass and unchanged since: ' +
      again.map((r) => `\`${r.file}${r.b == null && r.a === 1 ? '' : `:${r.a}-${r.b == null ? 'fin' : r.b}`}\``).join(', ') +
      '. Use that copy: drop them from the command.');
  }
  if (bytes > BASH_BIG) {
    const kb = fresh.some((r) => /[\\/]\.hosa[\\/]kb[\\/]/.test(r.file));
    const top = fresh.filter((r) => !WHOLE.test(r.file)).sort((x, y) => y.bytes - x.bytes).slice(0, 5)
      .map((r) => `${r.file} (${Math.round(r.bytes / 1000)} KB)`).join(', ');
    reasons.push(`This command prints about ${Math.round(bytes / 4000)} k tokens of files, kept in your context for the ` +
      `rest of the pass: ${top}. Read only what the task needs: \`<hosa> lire "<file>#<section>"\` or ` +
      '`"<file>:<start>-<end>"` (numbered, capped; a file too big gives its outline)' +
      (kb ? '; in the KB, `<hosa> kb_query <kb> --slug <slug> --sections "<heading>"` or `--fields`, several tickets in one call.' : '.'));
  }
  const groot = found.greps.length && findUp(cwd, path.join('.hosa', 'graph', 'graph.json'));
  for (const pattern of groot ? found.greps.slice(0, 1) : []) { // one graph query: it takes up to 4 s, the hook 5 s
    const out = guardGrep({ session_id: p.session_id, agent_id: p.agent_id, tool_input: { pattern } },
      path.join(groot, '.hosa', 'graph'), groot, query);
    if (out) reasons.push(out.hookSpecificOutput.permissionDecisionReason.replace(/^\[hosa\] /, '').replace(/Need raw text.*$/s, '').trim());
  }
  if (!reasons.length) { remember(); store(file, s); return null; }
  s['~retry'] = h;
  store(file, s);
  return deny(`${reasons.join('\n')}\nNeed it as written anyway? Run the same command again: it passes.`);
}

function processPayload(p, query = queryGraph) {
  if (process.env.HOSA_READ_GUARD === '0' || !p || !p.session_id) return null;
  if (p.hook_event_name === 'PreCompact') {
    const prefix = path.basename(stateFile(p.session_id)).replace(/main\.json$/, '');
    for (const f of fs.readdirSync(stateDir())) if (f.startsWith(prefix)) fs.unlinkSync(path.join(stateDir(), f));
    return null;
  }
  if (p.tool_name === 'Bash') return bashGuard(p, query);
  const i = p.tool_input || {};
  if (p.tool_name !== 'Read' || !i.file_path || i.offset != null || i.limit != null || i.pages != null) return null;
  const st = fs.statSync(i.file_path);
  const sig = `${st.mtimeMs}:${st.size}`;
  const file = stateFile(p.session_id, p.agent_id);
  const s = load(file);
  const key = keyOf(i.file_path);
  const prev = s[key];
  const big = st.size > BIG && !WHOLE.test(i.file_path);
  const save = () => store(file, s);
  if (big && !(prev && prev.big)) {
    s[key] = { big: true };
    save();
    const kb = /[\\/]\.hosa[\\/]kb[\\/]/.test(i.file_path)
      ? '`<hosa> kb_query <kb> --slug <name> --sections "…"` (or `--fields`), ' : 'the project graph or Grep to find the range, then ';
    return deny(`${i.file_path} is ${Math.round(st.size / 1000)} KB, about ${Math.round(st.size / 4000)} k tokens kept in this context ` +
      `for the rest of the pass. Read only the part the task needs: ${kb}a Read with offset/limit. ` +
      'Need it whole (an audit, a full rewrite)? Retry the Read: it will pass.');
  }
  const refuse = prev && prev.sig === sig && !prev.refused;
  s[key] = { sig, refused: !!refuse, ...(prev && prev.big ? { big: true } : {}) };
  save();
  if (!refuse) return null;
  return deny(`${i.file_path} is unchanged since you read it earlier in this conversation — use that copy. ` +
    'Need a fresh view anyway? Retry the Read (it will pass), or read a range with offset/limit.');
}

if (require.main === module) {
  let input = '';
  process.stdin.on('data', (c) => { input += c; });
  process.stdin.on('end', () => {
    try {
      const out = processPayload(JSON.parse(input.replace(/^﻿/, '')));
      if (out) process.stdout.write(JSON.stringify(out));
    } catch (e) {} // best-effort — never block a Read
  });
}

module.exports = { processPayload };
