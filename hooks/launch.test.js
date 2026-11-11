const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const { processPayload } = require('./launch');

const project = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-launch-proj-'));
fs.mkdirSync(path.join(project, '.hosa', 'kb'), { recursive: true });
const launched = (extra = {}) => ({
  hook_event_name: 'PostToolUse', tool_name: 'Agent', cwd: project,
  tool_input: { subagent_type: 'hosa:hosa-tester', description: 'Rejeu QA' },
  tool_response: { isAsync: true, status: 'async_launched', agentId: 'a1' }, ...extra,
});
const on = (fn) => { process.env.HOSA_ARRET_LANCEMENT = '1'; try { return fn(); } finally { delete process.env.HOSA_ARRET_LANCEMENT; } };

test('off unless switched on', () => {
  assert.equal(processPayload(launched()), null);
});

test('a Hosa agent launched in the background ends the main turn', () => {
  const out = on(() => processPayload(launched()));
  assert.equal(out.continue, false);
  assert.match(out.stopReason, /Rejeu QA/);
});

test('goes on for a report already here, another agent, a subagent, or outside a Hosa project', () => {
  on(() => {
    assert.equal(processPayload(launched({ tool_response: { status: 'completed', content: [] } })), null);
    assert.equal(processPayload(launched({ tool_input: { subagent_type: 'Explore' } })), null);
    assert.equal(processPayload(launched({ agent_id: 'a2' })), null);
    assert.equal(processPayload(launched({ tool_name: 'Bash' })), null);
    assert.equal(processPayload(launched({ cwd: fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-launch-none-')) })), null);
    assert.equal(processPayload(null), null);
  });
});

test('fail-open on a payload that is not JSON, and registered on Agent in hooks.json', () => {
  const run = spawnSync(process.execPath, [path.join(__dirname, 'launch.js')], { input: 'not json', encoding: 'utf8',
    env: { ...process.env, HOSA_ARRET_LANCEMENT: '1' } });
  assert.equal(run.status, 0);
  assert.equal(run.stdout, '');
  const hooks = JSON.parse(fs.readFileSync(path.join(__dirname, 'hooks.json'), 'utf8')).hooks.PostToolUse;
  const entry = hooks.find((h) => h.hooks.some((x) => x.command.includes('launch.js')));
  assert.equal(entry.matcher, 'Agent|Task');
});
