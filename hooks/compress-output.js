#!/usr/bin/env node
// Hosa — PostToolUse hook. Condenses tool output before the model reads it, in
// place of RTK. It knows the command that produced the output (git, test
// runners, installers, grep, path lists) and drops only what it can name:
// hint lines, passing tests, progress lines (installer lines where only
// numbers differ).
// Every drop is counted in a footer and the full text spilled to disk. Output
// still too big is indexed, not cut blind: every file of a grep stays named,
// hidden lines are given by number, error lines are kept with theirs.
// Started from Chisle's compressor (MIT, github.com/JayPokale/Chisle).
// Deterministic, no network. Read/Edit/Write are never touched (their output
// feeds exact-match edits); Agent is excluded because `develop` parses subagent
// reports (e.g. `Files Changed`) and must see them whole.
// Kill switch: HOSA_COMPRESS=0.

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');

const SAFE_TOOLS = ['Bash', 'Grep', 'Glob', 'WebFetch', 'WebSearch'];
const MAX_CHARS = 20000, MIN_LEN = 400, DEDUP_MIN = 2048, MIN_WIN = 64;
const REPEAT_MIN = 4, SIMILAR_MIN = 6, MAX_SALVAGED = 30, MAX_LINE = 300, MAX_INDEX = 300, SPILL_KEEP = 40;
const ANSI_RE = /\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)/g;
const SALVAGE_RE = /\b(error|err!|fail(ed|ure|ing)?|exception|traceback|panic|fatal|denied|refused|timed?[ _-]?out|assert(ion)?|segfault|cannot find|not found|warning)\b/i;

const stateDir = () => process.env.HOSA_STATE_DIR || path.join(os.tmpdir(), 'hosa-compress');
const clip = (l, n = MAX_LINE) => (l.length > n ? l.slice(0, n) + '…' : l);

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

// Lossless: colours, carriage-return progress (last state kept), trailing blanks, exact repeats.
function scrub(text) {
  const lines = text.replace(/\r\n/g, '\n').replace(/^[^\n]*\r(?=[^\r\n])/gm, '').replace(ANSI_RE, '')
    .replace(/[ \t\r]+$/gm, '').replace(/\n{3,}/g, '\n\n').split('\n');
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

// --- What produced the output -------------------------------------------------

// The program behind a Bash output: last `&&`/`;` step, first stage of its pipe,
// without env assignments or a runner prefix (rtk, npx, uv run, python -m…).
function program(cmd) {
  const step = String(cmd || '').split(/&&|\|\||;|\n/).map(s => s.trim()).filter(Boolean).pop() || '';
  return step.split('|')[0].trim()
    .replace(/^(\w+=\S*\s+)+/, '')
    .replace(/^(rtk(\s+proxy)?|npx|pnpm\s+exec|uv\s+run|poetry\s+run|\S*py(thon[\d.]*)?(\.exe)?\s+-m|docker\s+(compose\s+)?exec(\s+-\S+)*\s+\S+)\s+/, '');
}

const TEST_RE = /\b(pytest|jest|vitest|mocha|cargo\s+test|go\s+test|node\s+(.*\s)?--test|(npm|pnpm|yarn)\s+(run\s+)?test|unittest)\b/;
const INSTALL_RE = /^((npm|pnpm|yarn)\s+(install|i|ci|add)|pip3?\s+install|uv\s+(sync|add|pip\s+install)|poetry\s+(install|add)|cargo\s+(build|install|fetch|check)|docker\s+(build|pull|compose\s+.*\b(build|pull|up)\b))/;
const GIT_KINDS = { status: 'status', diff: 'diff', show: 'diff', log: 'log', push: 'transfer', pull: 'transfer', fetch: 'transfer', clone: 'transfer', grep: 'grep', 'ls-files': 'paths' };

function kindOf(tool, cmd) {
  if (tool === 'Grep') return 'grep';
  if (tool !== 'Bash') return null;
  const p = program(cmd);
  const git = /^git(?:\s+-[Cc]\s+\S+)*\s+([\w-]+)/.exec(p);
  if (git) return GIT_KINDS[git[1]] || null;
  if (TEST_RE.test(p)) return 'test';
  if (INSTALL_RE.test(p)) return 'install';
  if (/^(grep|rg|ag)\b/.test(p)) return 'grep';
  if (/^(find|fd)\b/.test(p)) return 'paths';
  return null;
}

// --- Condensers: each gets the lines and a ctx {notes, lossy, blocks} ------------

// Lines matching `res` go, unless they look like an error; the count goes in the footer.
function dropLines(lines, res, what, ctx) {
  let n = 0;
  const out = lines.filter(l => {
    const bare = l.replace(/^#\d+ \d+(\.\d+)? /, ''); // buildkit step output prefix
    const drop = !SALVAGE_RE.test(l) && res.some(r => r.test(bare));
    if (drop) n++;
    return !drop;
  });
  if (n) { ctx.notes.push(`${n} ${what} dropped`); ctx.lossy = true; }
  return out;
}

function gitStatus(lines) {
  return lines
    .filter(l => !/^\s*\((use|commit or discard) .*\)$/.test(l) && !/^(no changes added to commit|nothing added to commit but untracked)/.test(l))
    .map(l => l.replace(/^\t([a-z][a-z ]*):\s+/, '  $1: ').replace(/^\t/, '  '));
}

// File headers carry the path three times: keep `diff --git`, drop `index`/`---`/`+++`.
// One block per file (or commit header), so a diff too big keeps whole files.
function gitDiff(lines, ctx) {
  let header = false;
  const out = lines.filter(l => {
    if (/^diff --git /.test(l)) header = true;
    else if (/^@@ |^Binary files /.test(l)) header = false;
    return !(header && /^(index [0-9a-f]+\.\.[0-9a-f]+|--- |\+\+\+ )/.test(l));
  });
  const blocks = [];
  for (const l of out) {
    if (!blocks.length || /^diff --git |^[0-9a-f]{12}\b.* · /.test(l)) blocks.push([]);
    blocks[blocks.length - 1].push(l);
  }
  ctx.blocks = blocks.map(b => {
    const file = /^diff --git a\/(.*) b\//.exec(b[0]);
    const count = c => b.filter(l => l[0] === c).length;
    return { text: b.join('\n'), index: file ? `${file[1]} (+${count('+')} −${count('-')})` : clip(b[0], 120) };
  });
  return out;
}

// `git log` medium format → one header line per commit; `-p` diffs go through gitDiff.
function gitLog(lines, ctx) {
  if (!/^commit [0-9a-f]{40}/.test(lines[0] || '')) return gitDiff(lines, ctx);
  const out = [];
  for (let i = 0; i < lines.length; i++) {
    const m = /^commit ([0-9a-f]{40})(.*)$/.exec(lines[i]);
    if (m) {
      const meta = [];
      while (/^(Author|Date|Merge|Commit|AuthorDate|CommitDate):/.test(lines[i + 1] || '')) {
        const f = /^(\w+):\s+(.*)$/.exec(lines[++i]);
        meta.push(f[1] === 'Author' || f[1] === 'Date' ? f[2] : `${f[1]}: ${f[2]}`);
      }
      out.push(`${m[1].slice(0, 12)}${m[2]} · ${meta.join(' · ')}`);
      if (!(lines[i + 1] || '').trim()) i++; // blank line after the header
    } else if (lines[i].trim() || !/^commit /.test(lines[i + 1] || '')) {
      out.push(lines[i].replace(/^ {4}/, '  '));
    }
  }
  return gitDiff(out, ctx);
}

const PASS_RES = [
  /\sPASSED(\s+\[\s*\d+%\])?$/, // pytest -v
  /^(\S+\.py\s+)?[.sx]+\s*(\[\s*\d+%\])?$/, // pytest progress without F or E
  /^\s*(✓|✔|√)\s/, // jest, vitest, node spec reporter
  /^\s*PASS\s/, // jest file line
  /^\s*--- PASS: |^=== (RUN|PAUSE|CONT)\s/, // go test -v
  /\s\.\.\. ok$/, // cargo test, unittest -v
];

// node --test TAP: `# Subtest:` lines and each `ok` with its YAML block go;
// `not ok` keeps its block (it holds the error).
function tapPasses(lines, ctx) {
  const out = [];
  let n = 0;
  for (let i = 0; i < lines.length; i++) {
    if (/^\s*# Subtest: /.test(lines[i])) { n++; continue; }
    if (/^\s*ok \d+ - /.test(lines[i])) {
      let j = i;
      if ((lines[i + 1] || '').trim() === '---') { j = i + 2; while (j < lines.length && lines[j].trim() !== '...') j++; }
      n += j - i + 1;
      i = j;
      continue;
    }
    out.push(lines[i]);
  }
  if (n) { ctx.notes.push(`${n} TAP lines of passing tests dropped`); ctx.lossy = true; }
  return out;
}

const PROGRESS_RES = [
  /^\s*(Collecting|Downloading|Using cached|Requirement already satisfied|Obtaining|Preparing metadata|Building wheels? for|Created wheel|Stored in directory|Installing build dependencies|Getting requirements|Looking in indexes|Attempting uninstall|Found existing installation|Uninstalling|Successfully uninstalled)\b/, // pip
  /^npm (http|timing|sill|verb)\b/,
  /^\s*(Compiling|Checking|Fresh|Downloaded|Updating crates\.io index|Locking)\s/, // cargo
  /^#\d+ (DONE|CACHED|\[internal\]|transferring|resolve |sha256:|extracting|naming to|exporting|writing image|load (build definition|\.dockerignore|metadata))/, // buildkit
  /^\s*[\w.-]+ (Pulling( fs layer)?|Waiting|Downloading|Verifying Checksum|Download complete|Extracting|Pull complete|Already exists)\b/, // docker pull
  /━━|█|\[=+>?\s*\]/, // progress bars
];
const TRANSFER_RES = [/^(remote: )?(Enumerating|Counting|Compressing|Writing|Receiving|Resolving) (objects|deltas)/];

// `path:12:text` (and `path-12-text` context lines) → the path once, its lines under it. Lossless.
function grepGroup(lines, ctx) {
  const groups = [];
  let cur = null;
  for (const l of lines) {
    const m = /^((?:[A-Za-z]:)?[^:\n]+?):(\d+):(.*)$/.exec(l) || /^((?:[A-Za-z]:)?[\w.\/\\-]+\.\w+):()(.*)$/.exec(l);
    const ctxLine = !m && cur && l.startsWith(cur.name + '-') && /^-(\d+)-(.*)$/.exec(l.slice(cur.name.length));
    if (m || ctxLine) {
      const [name, num, rest, sep] = m ? [m[1], m[2], m[3], ':'] : [cur.name, ctxLine[1], ctxLine[2], '-'];
      if (!cur || cur.name !== name) groups.push(cur = { name, lines: [] });
      cur.lines.push(num ? `${num}${sep} ${rest}` : rest);
    } else if (l === '--' && cur) cur.lines.push('--');
    else { groups.push({ name: null, lines: [l] }); cur = null; }
  }
  ctx.blocks = groups.map(g => {
    if (!g.name) return { text: g.lines[0] };
    const hits = g.lines.filter(x => x !== '--').length;
    const text = g.lines.length === 1 ? `${g.name}:${g.lines[0]}` : [g.name, ...g.lines.map(x => '  ' + x)].join('\n');
    return { text, index: `${g.name} (${hits})` };
  });
  return ctx.blocks.map(b => b.text).join('\n').split('\n');
}

// A list of paths → one line per directory. Lossless.
function pathGroup(lines, ctx) {
  const groups = [];
  for (const l of lines) {
    const k = Math.max(l.lastIndexOf('/'), l.lastIndexOf('\\')) + 1;
    const [dir, name] = [l.slice(0, k), l.slice(k)];
    const g = groups[groups.length - 1];
    if (g && g.dir === dir && name && !name.includes(', ')) g.names.push(name);
    else groups.push({ dir, names: [name] });
  }
  ctx.blocks = groups.map(g => (g.names.length === 1
    ? { text: g.dir + g.names[0] }
    : { text: `${g.dir}: ${g.names.join(', ')}`, index: `${g.dir} (${g.names.length})` }));
  return ctx.blocks.map(b => b.text);
}

// Runs where only the numbers change (counters, timings, ids) → first two, last one, a count.
function similar(lines, ctx) {
  const tpl = l => l.replace(/\d+/g, '#');
  const out = [];
  let n = 0;
  for (let i = 0; i < lines.length;) {
    const t = tpl(lines[i]);
    let j = i + 1;
    while (j < lines.length && tpl(lines[j]) === t) j++;
    const digits = (lines[i].match(/\d/g) || []).length;
    if (j - i >= SIMILAR_MIN && lines[i].trim() && digits && digits <= 0.4 * lines[i].length && !SALVAGE_RE.test(lines[i])) {
      out.push(lines[i], lines[i + 1], `... [hosa: ${j - i - 3} similar lines, only numbers differ] ...`, lines[j - 1]);
      n += j - i - 3;
    } else out.push(...lines.slice(i, j));
    i = j;
  }
  if (n) { ctx.notes.push(`${n} lines where only numbers differ folded`); ctx.lossy = true; }
  return out;
}

function condense(text, kind, ctx) {
  let lines = text.split('\n');
  if (kind === 'status') lines = gitStatus(lines);
  if (kind === 'diff') lines = gitDiff(lines, ctx);
  if (kind === 'log') lines = gitLog(lines, ctx);
  if (kind === 'test') lines = dropLines(tapPasses(lines, ctx), PASS_RES, 'passing-test lines', ctx);
  // only in installer logs: elsewhere `file2.js`…`file10.js` differ by numbers too
  if (kind === 'install') lines = similar(dropLines(lines, PROGRESS_RES, 'progress lines', ctx), ctx);
  if (kind === 'transfer') lines = dropLines(lines, TRANSFER_RES, 'transfer progress lines', ctx);
  if (kind === 'grep') return grepGroup(lines, ctx).join('\n');
  if (kind === 'paths') return pathGroup(lines, ctx).join('\n');
  return lines.join('\n');
}

// --- Still too big: index, never a silent cut ----------------------------------

// Grep and path lists: whole groups up to the budget, then every remaining group by name.
function fitBlocks(blocks) {
  const out = [];
  let size = 0, i = 0;
  for (; i < blocks.length && size + blocks[i].text.length < MAX_CHARS * 0.8; i++) { out.push(blocks[i].text); size += blocks[i].text.length + 1; }
  if (!i && blocks.length) out.push(fitLines(blocks[i++].text)); // one block alone over budget
  const rest = blocks.slice(i);
  const names = rest.map(b => b.index || clip(b.text, 120));
  const more = names.length > MAX_INDEX ? ` … and ${names.length - MAX_INDEX} more` : '';
  out.push(`... [hosa: ${rest.length} more group(s) not shown, by name:] ...`, names.slice(0, MAX_INDEX).join(', ') + more);
  return out.join('\n');
}

// Anything else: head and tail, the hidden line range by number, its error lines with theirs.
function fitLines(t) {
  const lines = t.split('\n');
  let head = 0, tail = 0, size = 0;
  while (head < lines.length && size + lines[head].length < MAX_CHARS * 0.5) size += lines[head++].length + 1;
  size = 0;
  while (tail < lines.length - head && size + lines[lines.length - 1 - tail].length < MAX_CHARS * 0.25) size += lines[lines.length - 1 - tail++].length + 1;
  if (!head) return `${t.slice(0, MAX_CHARS / 2)}\n... [hosa: chars ${MAX_CHARS / 2}–${t.length - MAX_CHARS / 4} of ${t.length} not shown] ...\n${t.slice(-MAX_CHARS / 4)}`;
  const to = lines.length - tail;
  const salvaged = [];
  for (let k = head; k < to && salvaged.length < MAX_SALVAGED; k++) if (SALVAGE_RE.test(lines[k])) salvaged.push(`L${k + 1}: ${clip(lines[k])}`);
  const marker = `... [hosa: lines ${head + 1}–${to} of ${lines.length} not shown` +
    (salvaged.length ? `; their ${salvaged.length} error-like line(s), with line numbers:` : '') + '] ...';
  return [...lines.slice(0, head), marker, ...salvaged, ...lines.slice(to)].join('\n');
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
      lines.slice(0, 5).map(l => clip(l)).join('\n');
  } catch (e) { return null; }
}

// Full text goes to disk so whatever was dropped is read back, not re-run.
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

function transform(text, tool, cmd) {
  if (!text || text.length <= MIN_LEN) return null;
  const scrubbed = scrub(text);
  const ctx = { notes: [], lossy: false, blocks: null };
  const kind = kindOf(tool, cmd);
  let t = condense(scrubbed, kind, ctx);
  let saved = ctx.lossy ? scrubbed : null; // what the spill file must hold
  if (t.length > MAX_CHARS) {
    // line numbers in fitLines' marker count from the top of the spill file
    saved = saved ? `${t}\n\n=== hosa: full output before condensing ===\n${saved}` : t;
    t = ctx.blocks ? fitBlocks(ctx.blocks) : fitLines(t);
  }
  if (saved) {
    const file = spill(saved, tool);
    const where = file ? ` Full output: ${file} (Read or grep it, do not re-run)` : '';
    t += `\n[hosa: ${ctx.notes.length ? ctx.notes.join('; ') : 'condensed'}.${where}]`;
  }
  return text.length - t.length >= MIN_WIN ? t : null;
}

// A spill file's own name, as `spill()` writes it: searching it must not spill again.
const SPILL_RE = /spill[\\/]+\w+-[0-9a-f]{12}\.txt/;

// Hook payload → replacement tool_response, or null to leave it untouched.
function processPayload(p) {
  if (process.env.HOSA_COMPRESS === '0' || !p || !SAFE_TOOLS.includes(p.tool_name)) return null;
  const input = p.tool_input || {};
  if (SPILL_RE.test(JSON.stringify(input))) return null;
  const text = extractText(p.tool_response);
  if (!text) return null;
  const updated = dedup(p.tool_name, text, p.session_id, p.tool_use_id) || transform(text, p.tool_name, input.command);
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

module.exports = { processPayload, scrub, transform, kindOf, program };
