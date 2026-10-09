const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

process.env.HOSA_STATE_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-read-guard-test-'));
const { processPayload } = require('./read-guard');

const file = path.join(process.env.HOSA_STATE_DIR, 'a.txt');
fs.writeFileSync(file, 'hello');
const read = (extra = {}) => processPayload({ hook_event_name: 'PreToolUse', tool_name: 'Read', session_id: 's1', tool_input: { file_path: file }, ...extra });
const denied = (out) => !!out && out.hookSpecificOutput.permissionDecision === 'deny';

test('refuses an unchanged re-read once, then lets the retry through', () => {
  assert.equal(read(), null);
  assert.ok(denied(read()));
  assert.equal(read(), null);
});

test('partial reads and subagents are never refused', () => {
  assert.equal(read({ tool_input: { file_path: file, offset: 1, limit: 5 } }), null);
  assert.equal(read({ agent_id: 'sub' }), null);
});

test('a modified file passes, PreCompact resets the session', () => {
  read();
  fs.writeFileSync(file, 'hello world');
  assert.equal(read(), null);
  processPayload({ hook_event_name: 'PreCompact', session_id: 's1' });
  assert.equal(read(), null);
  assert.equal(read({ agent_id: 'sub' }), null);
});
