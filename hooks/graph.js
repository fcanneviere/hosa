#!/usr/bin/env node
// Hosa — graph hooks. PostToolUse (Edit|Write|MultiEdit): reindexes the edited
// file in the project graph (.hosa/graph/) and, for a KB file, checks its header parses
// (an unreadable header is sent back to the agent to fix). PreToolUse (Grep|Glob): refuses once a
// tree-wide Grep for an identifier the graph already locates (answer in the refusal), and reminds the
// agent once per session that the graph answers "where is X / what does it
// impact" before grepping. Fail-open: never blocks, never errors out.
// Also used by session-start.js (graph command line + detached catch-up index).

const fs = require('fs');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || path.join(__dirname, '..');
const APP = path.join(pluginRoot, 'hosa', 'app');
const GRAPH_PY = path.join(APP, 'graph.py');
const KB_INDEX_PY = path.join(pluginRoot, 'skills', 'okf', 'scripts', 'kb_index.py');

// Rewrites `.hosa/kb/sommaire.md` (one line per KB concept) in the background.
function refreshSummary(kbDir) {
  spawn(pythonBackground(), [KB_INDEX_PY, kbDir], { detached: true, stdio: 'ignore', windowsHide: true })
    .on('error', () => {}).unref();
}

// Same place as run.py: ${CLAUDE_PLUGIN_DATA} survives plugin updates; hosa/app/.venv from the repo.
const VENV = process.env.CLAUDE_PLUGIN_DATA ? path.join(process.env.CLAUDE_PLUGIN_DATA, 'venv') : path.join(APP, '.venv');

function python() {
  const venv = process.platform === 'win32' ? path.join(VENV, 'Scripts', 'python.exe') : path.join(VENV, 'bin', 'python');
  return fs.existsSync(venv) ? venv : process.platform === 'win32' ? 'python' : 'python3';
}

// Detached on Windows: python.exe is a console program, and with no console to inherit it (and the venv launcher's child)
// opens a window. pythonw.exe never does; its stdout is None, which is fine for stdio: 'ignore'.
function pythonBackground() {
  const py = python();
  const w = py.replace(/python\.exe$/i, 'pythonw.exe');
  return process.platform === 'win32' && w !== py && fs.existsSync(w) ? w : py;
}

// Closest ancestor of `dir` containing `marker` (a relative path), or null.
function findUp(dir, marker) {
  for (let d = path.resolve(dir); ; d = path.dirname(d)) {
    if (fs.existsSync(path.join(d, marker))) return d;
    if (path.dirname(d) === d) return null;
  }
}

// The managed project's real KB root: a sprint worktree (`.worktrees/…`) carries a stale,
// committed copy of `.hosa/kb` — skip it and keep walking up to the project root.
function findKbRoot(dir) {
  let root = findUp(dir, path.join('.hosa', 'kb'));
  while (root) {
    const parts = path.resolve(root).split(path.sep);
    const i = parts.lastIndexOf('.worktrees');
    if (i < 0) return root;
    root = findUp(parts.slice(0, i).join(path.sep) || path.sep, path.join('.hosa', 'kb'));
  }
  return null;
}

// The KB file's header error as the app reports it ("Le fichier est illisible : …"), or ''.
const CHECK_PY = 'import sys; sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")\n' +
  'try:\n import kb\nexcept Exception: sys.exit(0)\n' +
  'try: kb.parse(open(sys.argv[2], encoding="utf-8").read())\nexcept kb.KbError as e: print(e)\nexcept Exception: pass';
function checkHeader(file) {
  // -I and cwd: a module in the managed project's folder never shadows the app's imports
  // (-I also drops PYTHONIOENCODING: CHECK_PY sets UTF-8 itself).
  const r = spawnSync(python(), ['-I', '-c', CHECK_PY, APP, file], { cwd: APP, timeout: 4000, encoding: 'utf8', windowsHide: true });
  return (r.stdout || '').trim();
}

// `<hosa>`: the one way to run a Hosa script — `<hosa> <name> [args]` (run.py). Its shim lives in
// ${CLAUDE_PLUGIN_DATA}, which survives plugin updates, as the venv does: the versioned cache path
// doesn't, and a session or a KB note that kept it broke at the next update (pilot2).
const DATA = process.env.CLAUDE_PLUGIN_DATA;
const SHIM = DATA ? path.join(DATA, 'hosa.py') : path.join(pluginRoot, 'run.py');
const shimText = (root) => `# Hosa — stable launcher, rewritten at each session start: python hosa.py <script> [args]
import glob, os, runpy, sys
root = ${JSON.stringify(root)}
if not os.path.isfile(os.path.join(root, "run.py")):  # plugin updated since: the newest installed version
    found = sorted(glob.glob(os.path.join(os.path.dirname(root), "*", "run.py")), key=os.path.getmtime)
    root = os.path.dirname(found[-1]) if found else root
sys.argv[0] = os.path.join(root, "run.py")
runpy.run_path(sys.argv[0], run_name="__main__")
`;
function writeShim() {
  if (!DATA) return;
  fs.mkdirSync(DATA, { recursive: true });
  fs.writeFileSync(SHIM, shimText(path.resolve(pluginRoot)));
}
const hosaCommand = () => `"${python()}" "${SHIM}"`;
const commandLine = () => `${hosaCommand()} graph`;

function runGraph(root, args) {
  spawnSync(python(), [GRAPH_PY, '--root', root, ...args], { timeout: 10000, stdio: 'ignore', windowsHide: true });
}

// `graph.py find` output, or '' on failure/no hit. Stays under the 5 s hook timeout.
function queryGraph(root, text) {
  const r = spawnSync(python(), [GRAPH_PY, '--root', root, '--budget', '500', 'find', text],
    { timeout: 4000, encoding: 'utf8', windowsHide: true });
  const out = (r.status === 0 && r.stdout || '').trim();
  return out === 'Aucun résultat.' ? '' : out;
}

// Grep over a whole tree for a bare identifier: the graph already knows where it
// lives. Refused once per pattern (the reason carries the answer); a retry passes,
// regexes and single-file greps too.
const IDENT_RE = /^[A-Za-z_][\w.]{2,}$/;
function broadIdentGrep(p) {
  const i = p.tool_input || {};
  if (p.tool_name !== 'Grep' || !IDENT_RE.test(i.pattern || '')) return false;
  try { return !i.path || fs.statSync(path.resolve(p.cwd || '.', i.path)).isDirectory(); } catch (e) { return false; }
}

function guardGrep(p, gdir, root, query) {
  const file = path.join(gdir, 'refused');
  let s = {};
  try { s = JSON.parse(fs.readFileSync(file, 'utf8')) || {}; } catch (e) {}
  if (s.session !== p.session_id) s = { session: p.session_id, keys: [] };
  const key = `${p.agent_id || ''}:${p.tool_input.pattern}`;
  if (s.keys.includes(key)) return null;
  s.keys.push(key);
  fs.writeFileSync(file, JSON.stringify(s));
  const hits = query(root, p.tool_input.pattern);
  if (!hits) return null;
  return { hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny', permissionDecisionReason:
    `[hosa] The project graph already locates "${p.tool_input.pattern}":\n${hits}\n` +
    `Read only those regions; \`${commandLine()} explain|affected <name>\` gives callers and impact. ` +
    'Need raw text matches anyway? Retry the Grep (it will pass), or scope it to a file.' } };
}

// SessionStart: marks the session start and rebuilds the graph in the background
// (a full first build can exceed the hook timeout). Returns the context line, or ''.
function sessionStart(cwd) {
  const root = findUp(cwd, path.join('.hosa', 'kb'));
  if (!root) return '';
  const gdir = path.join(root, '.hosa', 'graph');
  fs.mkdirSync(gdir, { recursive: true });
  fs.writeFileSync(path.join(gdir, 'session'), String(Date.now()));
  spawn(pythonBackground(), [GRAPH_PY, '--root', root, 'index'], { detached: true, stdio: 'ignore', windowsHide: true })
    .on('error', () => {}).unref(); // python introuvable : pas de graphe, la session démarre quand même
  return `\n\n## Project graph\n\nQuery it before grepping: \`${commandLine()} ticket <slug> | explain <name> | affected <name> | find <text> [--path <glob>] [--kind <kind>] [--offset <n>] | map | status\``;
}

const mtime = (p) => { try { return fs.statSync(p).mtimeMs; } catch (e) { return 0; } };

// Hook payload → hook output object, or null.
function processPayload(p, run = runGraph, summarize = refreshSummary, query = queryGraph, check = checkHeader) {
  if (!p) return null;
  if (p.hook_event_name === 'PostToolUse') {
    const file = p.tool_input && p.tool_input.file_path;
    const root = file && findUp(path.dirname(file), path.join('.hosa', 'graph', 'graph.json'));
    if (root) run(root, ['index', file]);
    const parts = file ? path.resolve(file).split(path.sep) : [];
    const i = parts.indexOf('.hosa');
    if (i >= 0 && parts[i + 1] === 'kb' && path.basename(file) !== 'sommaire.md') {
      summarize(parts.slice(0, i + 2).join(path.sep) || path.sep);
      const error = file.endsWith('.md') && check(file);
      if (error) return { decision: 'block', reason: `[hosa] ${file}: ${error}. ` +
        'Fix the YAML header: put a value containing ": " (or starting with a quote, [, {, # or &) in double quotes.' };
    }
    return null;
  }
  if (p.hook_event_name === 'PreToolUse') {
    const root = findUp(p.cwd || process.cwd(), path.join('.hosa', 'graph', 'graph.json'));
    if (!root) return null;
    const gdir = path.join(root, '.hosa', 'graph');
    if (broadIdentGrep(p)) {
      const refused = guardGrep(p, gdir, root, query);
      if (refused) return refused;
    }
    const nudged = path.join(gdir, 'nudged');
    const already = fs.existsSync(nudged) && fs.readFileSync(nudged, 'utf8') === String(p.session_id);
    if (already || mtime(path.join(gdir, 'last_query')) > mtime(path.join(gdir, 'session'))) return null;
    fs.writeFileSync(nudged, String(p.session_id));
    return { hookSpecificOutput: { hookEventName: 'PreToolUse', additionalContext:
      `The project graph is available: \`${commandLine()} explain|affected|ticket|find\` gives files, symbols, callers and impact in a few lines. Use it before grepping.` } };
  }
  return null;
}

if (require.main === module) {
  let input = '';
  process.stdin.on('data', (c) => { input += c; });
  process.stdin.on('end', () => {
    try {
      const out = processPayload(JSON.parse(input.replace(/^﻿/, '')));
      if (out) process.stdout.write(JSON.stringify(out));
    } catch (e) {} // best-effort — never break the tool pipeline
  });
}

module.exports = { pythonBackground, processPayload, sessionStart, findUp, findKbRoot, commandLine, refreshSummary, python, VENV,
  hosaCommand, writeShim, shimText, pluginRoot };
