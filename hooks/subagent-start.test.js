const test = require('node:test');
const assert = require('node:assert/strict');
const { processPayload } = require('./subagent-start');

test('injects the auto-audit rule into Hosa agents only', () => {
  assert.match(processPayload({ agent_type: 'hosa-security' }).hookSpecificOutput.additionalContext, /## Retour Hosa/);
  assert.match(processPayload({ agent_type: 'hosa-security' }, 'linux').hookSpecificOutput.additionalContext, /A `cd` lasts one command/);
  const linux = processPayload({ agent_type: 'hosa-tester' }, 'linux').hookSpecificOutput.additionalContext;
  assert.match(linux, /Run every command in the foreground/);
  assert.doesNotMatch(linux, /PYTHONIOENCODING/);
  assert.match(processPayload({ agent_type: 'hosa-tester' }, 'win32').hookSpecificOutput.additionalContext, /PYTHONIOENCODING=utf-8/);
  assert.match(processPayload({ agent_type: 'hosa-dba' }).hookSpecificOutput.additionalContext, /`<hosa>` in your instructions means `".+" ".+"`/);
  assert.ok(processPayload({ agent_type: 'hosa:hosa-git' }));
  assert.equal(processPayload({ agent_type: 'Explore' }), null);
  assert.equal(processPayload({}), null);
});

test('gives every Hosa agent the shared rules once, in place of a copy in each agents/*.md', () => {
  const ctx = processPayload({ agent_type: 'hosa:hosa-tester' }, 'linux').hookSpecificOutput.additionalContext;
  assert.match(ctx, /## Hosa agent rules/);
  assert.match(ctx, /Independent calls .* in one message/);
  assert.match(ctx, /Past 4,000, the hook refuses the report once/);
  assert.match(ctx, /\| N° \| Page \| Action \| Résultat attendu \|/);       // a tester hands over manual tests
  const security = processPayload({ agent_type: 'hosa:hosa-security' }, 'linux').hookSpecificOutput.additionalContext;
  assert.doesNotMatch(security, /Résultat attendu/);                       // the others don't carry their format
  // the shared rules cost no more than the copy each agent file held (1,736 characters on average before 0.1.78)
  assert.ok(security.indexOf('## Retour Hosa') < 1850, `shared rules: ${security.indexOf('## Retour Hosa')} characters`);
  const fs = require('fs');
  const path = require('path');
  const dir = path.join(__dirname, '..', 'agents');
  for (const f of fs.readdirSync(dir).filter((n) => n.endsWith('.md'))) {
    const text = fs.readFileSync(path.join(dir, f), 'utf8');
    assert.doesNotMatch(text, /Every file you read is paid for again|skills\/retours\/SKILL\.md/, f);
  }
});

test('adds the path quoting rule on Windows only', () => {
  const ctx = (platform) => processPayload({ agent_type: 'hosa-git' }, platform).hookSpecificOutput.additionalContext;
  assert.match(ctx('win32'), /forward slashes/);
  assert.doesNotMatch(ctx('linux'), /forward slashes/);
});
