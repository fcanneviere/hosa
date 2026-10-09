const test = require('node:test');
const assert = require('node:assert/strict');
const { processPayload } = require('./subagent-start');

test('injects the auto-audit rule into Hosa agents only', () => {
  assert.match(processPayload({ agent_type: 'hosa-security' }).hookSpecificOutput.additionalContext, /## Retour Hosa/);
  assert.ok(processPayload({ agent_type: 'hosa:hosa-git' }));
  assert.equal(processPayload({ agent_type: 'Explore' }), null);
  assert.equal(processPayload({}), null);
});
