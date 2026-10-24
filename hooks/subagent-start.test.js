const test = require('node:test');
const assert = require('node:assert/strict');
const { processPayload } = require('./subagent-start');

test('injects the auto-audit rule into Hosa agents only', () => {
  assert.match(processPayload({ agent_type: 'hosa-security' }).hookSpecificOutput.additionalContext, /## Retour Hosa/);
  assert.match(processPayload({ agent_type: 'hosa-security' }, 'linux').hookSpecificOutput.additionalContext, /never `cd` into `\.hosa\/`/);
  assert.ok(processPayload({ agent_type: 'hosa:hosa-git' }));
  assert.equal(processPayload({ agent_type: 'Explore' }), null);
  assert.equal(processPayload({}), null);
});

test('adds the path quoting rule on Windows only', () => {
  const ctx = (platform) => processPayload({ agent_type: 'hosa-git' }, platform).hookSpecificOutput.additionalContext;
  assert.match(ctx('win32'), /forward slashes/);
  assert.doesNotMatch(ctx('linux'), /forward slashes/);
});
