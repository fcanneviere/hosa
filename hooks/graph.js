#!/usr/bin/env node
// Hosa — graph hooks. PostToolUse (Edit|Write|MultiEdit): reindexes the edited
// file in the project graph (.hosa/graph/). PreToolUse (Grep|Glob): reminds the
// agent once per session that the graph answers "where is X / what does it
// impact" before grepping. Fail-open: never blocks, never errors out.
// Also used by session-start.js (graph command line + detached catch-up index).

const fs = require('fs');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || path.join(__dirname, '..');
const APP = path.join(pluginRoot, 'hosa', 'app');
const GRAPH_PY = path.join(APP, 'graph.py');

function python() {
  const venv = process.platform === 'win32' ? path.join(APP, '.venv', 'Scripts', 'python.exe') : path.join(APP, '.venv', 'bin', 'python');
  return fs.existsSync(venv) ? venv : process.platform === 'win32' ? 'python' : 'python3';
}

// Closest ancestor of `dir` containing `marker` (a relative path), or null.
function findUp(dir, marker) {
  for (let d = path.resolve(dir); ; d = path.dirname(d)) {
    if (fs.existsSync(path.join(d, marker))) return d;
    if (path.dirname(d) === d) return null;
  }
}

const commandLine = () => `"${python()}" "${GRAPH_PY}"`;

function runGraph(root, args) {
  spawnSync(python(), [GRAPH_PY, '--root', root, ...args], { timeout: 10000, stdio: 'ignore', windowsHide: true });
}

// SessionStart: marks the session start and rebuilds the graph in the background
// (a full first build can exceed the hook timeout). Returns the context line, or ''.
function sessionStart(cwd) {
  const root = findUp(cwd, path.join('.hosa', 'kb'));
  if (!root) return '';
  const gdir = path.join(root, '.hosa', 'graph');
  fs.mkdirSync(gdir, { recursive: true });
  fs.writeFileSync(path.join(gdir, 'session'), String(Date.now()));
  spawn(python(), [GRAPH_PY, '--root', root, 'index'], { detached: true, stdio: 'ignore', windowsHide: true })
    .on('error', () => {}).unref(); // python introuvable : pas de graphe, la session démarre quand même
  return `\n\n## Project graph\n\nQuery it before grepping: \`${commandLine()} ticket <slug> | explain <name> | affected <name> | find <text> | map\``;
}

const mtime = (p) => { try { return fs.statSync(p).mtimeMs; } catch (e) { return 0; } };

// Hook payload → hook output object, or null.
function processPayload(p, run = runGraph) {
  if (!p) return null;
  if (p.hook_event_name === 'PostToolUse') {
    const file = p.tool_input && p.tool_input.file_path;
    const root = file && findUp(path.dirname(file), path.join('.hosa', 'graph', 'graph.json'));
    if (root) run(root, ['index', file]);
    return null;
  }
  if (p.hook_event_name === 'PreToolUse') {
    const root = findUp(p.cwd || process.cwd(), path.join('.hosa', 'graph', 'graph.json'));
    if (!root) return null;
    const gdir = path.join(root, '.hosa', 'graph');
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

module.exports = { processPayload, sessionStart, findUp, commandLine };
