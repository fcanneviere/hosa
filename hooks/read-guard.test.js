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

test('a big file is refused once for a part, then its re-read guard works as usual', () => {
  const big = path.join(process.env.HOSA_STATE_DIR, '.hosa', 'kb', 'cdc', 'gros.md');
  fs.mkdirSync(path.dirname(big), { recursive: true });
  fs.writeFileSync(big, 'x'.repeat(50000));
  const readBig = (extra = {}) => read({ session_id: 's2', tool_input: { file_path: big }, ...extra });
  const out = readBig();
  assert.ok(denied(out));
  assert.match(out.hookSpecificOutput.permissionDecisionReason, /kb_query/);
  assert.equal(readBig(), null);                         // the agent needs it whole
  assert.ok(denied(readBig()));                          // unchanged re-read
  fs.appendFileSync(big, 'y');
  assert.equal(readBig(), null);                         // changed: no second size refusal
  assert.equal(readBig({ tool_input: { file_path: big, offset: 1, limit: 50 } }), null);
});

test('the summary and images are read whole whatever their size', () => {
  for (const name of ['sommaire.md', 'page.png']) {
    const f = path.join(process.env.HOSA_STATE_DIR, name);
    fs.writeFileSync(f, 'x'.repeat(50000));
    assert.equal(read({ session_id: 's3', tool_input: { file_path: f } }), null);
  }
});

test('a modified file passes, PreCompact resets the session', () => {
  read();
  fs.writeFileSync(file, 'hello world');
  assert.equal(read(), null);
  processPayload({ hook_event_name: 'PreCompact', session_id: 's1' });
  assert.equal(read(), null);
  assert.equal(read({ agent_id: 'sub' }), null);
});
