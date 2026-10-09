const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const { processPayload } = require('./graph');

function project() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-graph-hook-'));
  fs.mkdirSync(path.join(root, '.hosa', 'graph'), { recursive: true });
  fs.mkdirSync(path.join(root, 'src'));
  fs.writeFileSync(path.join(root, '.hosa', 'graph', 'graph.json'), '{}');
  fs.writeFileSync(path.join(root, '.hosa', 'graph', 'session'), '1');
  return root;
}

test('reindexes an edited file of a project that has a graph', () => {
  const root = project();
  const calls = [];
  const file = path.join(root, 'src', 'a.py');
  processPayload({ hook_event_name: 'PostToolUse', tool_name: 'Edit', tool_input: { file_path: file } }, (...a) => calls.push(a));
  assert.deepEqual(calls, [[root, ['index', file]]]);
});

test('ignores edits outside a graphed project', () => {
  const calls = [];
  const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-nograph-')), 'a.py');
  processPayload({ hook_event_name: 'PostToolUse', tool_name: 'Write', tool_input: { file_path: file } }, (...a) => calls.push(a));
  assert.deepEqual(calls, []);
});

test('nudges once per session, never blocks', () => {
  const root = project();
  const p = { hook_event_name: 'PreToolUse', tool_name: 'Grep', cwd: path.join(root, 'src'), session_id: 's1' };
  const out = processPayload(p);
  assert.match(out.hookSpecificOutput.additionalContext, /graph\.py" explain\|affected\|ticket\|find/);
  assert.equal(out.hookSpecificOutput.permissionDecision, undefined);
  assert.equal(processPayload(p), null);
  assert.ok(processPayload({ ...p, session_id: 's2' }));
});

test('refuses a tree-wide identifier Grep once, with the graph answer in the reason', () => {
  const root = project();
  const hit = () => 'function src/a.py:login  src/a.py:3';
  const p = { hook_event_name: 'PreToolUse', tool_name: 'Grep', cwd: root, session_id: 's1', tool_input: { pattern: 'login' } };
  const out = processPayload(p, undefined, undefined, hit);
  assert.equal(out.hookSpecificOutput.permissionDecision, 'deny');
  assert.match(out.hookSpecificOutput.permissionDecisionReason, /src\/a\.py:3/);
  assert.notEqual(processPayload(p, undefined, undefined, hit)?.hookSpecificOutput.permissionDecision, 'deny');
});

test('regex, single-file and no-hit greps are never refused', () => {
  const root = project();
  fs.writeFileSync(path.join(root, 'src', 'a.py'), '');
  const hit = () => 'x';
  const deny = (input, q = hit) => processPayload({ hook_event_name: 'PreToolUse', tool_name: 'Grep', cwd: root, session_id: 's9', tool_input: input }, undefined, undefined, q)?.hookSpecificOutput.permissionDecision === 'deny';
  assert.equal(deny({ pattern: 'def \\w+' }), false);
  assert.equal(deny({ pattern: 'login', path: 'src/a.py' }), false);
  assert.equal(deny({ pattern: 'logout' }, () => ''), false);
});

test('no nudge when the graph was already queried this session', () => {
  const root = project();
  const later = new Date(Date.now() + 5000);
  fs.writeFileSync(path.join(root, '.hosa', 'graph', 'last_query'), '1');
  fs.utimesSync(path.join(root, '.hosa', 'graph', 'last_query'), later, later);
  assert.equal(processPayload({ hook_event_name: 'PreToolUse', tool_name: 'Glob', cwd: root, session_id: 's1' }), null);
});

test('session start marks the session and returns the command line, only inside a Hosa project', () => {
  const { sessionStart } = require('./graph');
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-session-'));
  assert.equal(sessionStart(root), '');
  fs.mkdirSync(path.join(root, '.hosa', 'kb'), { recursive: true });
  fs.mkdirSync(path.join(root, 'src'));
  assert.match(sessionStart(path.join(root, 'src')), /## Project graph[\s\S]*graph\.py" ticket <slug>/);
  assert.ok(fs.existsSync(path.join(root, '.hosa', 'graph', 'session')));
});

test('refreshes the KB summary when a KB file is written', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-kb-'));
  const kb = path.join(root, '.hosa', 'kb');
  const seen = [];
  processPayload({ hook_event_name: 'PostToolUse', tool_name: 'Write', tool_input: { file_path: path.join(kb, 'tickets', 'a.md') } }, () => {}, (d) => seen.push(d));
  processPayload({ hook_event_name: 'PostToolUse', tool_name: 'Write', tool_input: { file_path: path.join(kb, 'sommaire.md') } }, () => {}, (d) => seen.push(d));
  processPayload({ hook_event_name: 'PostToolUse', tool_name: 'Write', tool_input: { file_path: path.join(root, 'src', 'a.py') } }, () => {}, (d) => seen.push(d));
  assert.deepEqual(seen, [kb]);
});
