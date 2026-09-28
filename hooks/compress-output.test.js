const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

process.env.HOSA_STATE_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-compress-test-'));
const { processPayload } = require('./compress-output');

const bigLog = Array.from({ length: 500 }, (_, i) => (i === 250 ? 'FAILED test_login: AssertionError' : `ok ${i} ${'x'.repeat(40)}`)).join('\n');

test('elides a big Bash output, salvages the error line, spills the full text', () => {
  const out = processPayload({ tool_name: 'Bash', tool_response: { stdout: bigLog, stderr: 'warn', interrupted: false } });
  assert.ok(out.stdout.length < bigLog.length);
  assert.match(out.stdout, /FAILED test_login/);
  assert.equal(out.stderr, '');
  assert.equal(out.interrupted, false);
  const spilled = out.stdout.match(/Full output: (\S+)/)[1];
  assert.match(fs.readFileSync(spilled, 'utf8'), /ok 499/);
});

test('never touches Read, Edit, Write or Agent', () => {
  for (const tool_name of ['Read', 'Edit', 'Write', 'Agent']) {
    assert.equal(processPayload({ tool_name, tool_response: bigLog }), null);
  }
});

test('leaves small output alone', () => {
  assert.equal(processPayload({ tool_name: 'Bash', tool_response: { stdout: 'hello' } }), null);
});

test('collapses repeated lines losslessly', () => {
  const text = 'start\n' + 'same line\n'.repeat(200) + 'end';
  const out = processPayload({ tool_name: 'Grep', tool_response: text });
  assert.match(out, /line repeated 200×/);
  assert.match(out, /end$/);
});

test('dedups identical output within a session, not across sessions or the same call', () => {
  const text = 'y'.repeat(3000);
  const call = id => processPayload({ tool_name: 'WebFetch', tool_response: text, session_id: 's1', tool_use_id: id });
  call('a');
  assert.equal(call('a'), null);
  assert.match(call('b'), /identical to the previous WebFetch/);
  assert.equal(processPayload({ tool_name: 'WebFetch', tool_response: text, session_id: 's2', tool_use_id: 'c' }), null);
});

test('HOSA_COMPRESS=0 disables everything', () => {
  process.env.HOSA_COMPRESS = '0';
  assert.equal(processPayload({ tool_name: 'Bash', tool_response: { stdout: bigLog } }), null);
  delete process.env.HOSA_COMPRESS;
});
