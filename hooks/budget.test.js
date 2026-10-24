const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

process.env.HOSA_STATE_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-budget-test-'));
const { processPayload } = require('./budget');

const denied = (out) => !!out && out.hookSpecificOutput.permissionDecision === 'deny';
const project = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-budget-proj-'));
const plan = path.join(project, '.hosa', 'kb', 'project', 'avancement.md');
fs.mkdirSync(path.dirname(plan), { recursive: true });
const setPlan = (done) => fs.writeFileSync(plan, `## Sprint s1\n| Étape | Statut | Mis à jour | Détail |\n|---|---|---|---|\n` +
  ['sprint', 'qa-plan', 'git-demarrage', 'develop', 'qa'].map((s, i) => `| \`${s}\` | ${i < done ? 'fait' : 'à faire'} |  |  |`).join('\n'));
const transcript = path.join(project, 't.jsonl');
const setContext = (n) => fs.writeFileSync(transcript, JSON.stringify({ type: 'assistant',
  message: { usage: { input_tokens: 1, cache_creation_input_tokens: 0, cache_read_input_tokens: n } } }) + '\n');
const skill = (name, session = 's1') => processPayload({ hook_event_name: 'PreToolUse', tool_name: 'Skill', session_id: session,
  cwd: project, transcript_path: transcript, tool_input: { skill: name } });

test('a heavy session that closed a stage is stopped once before the next stage', () => {
  setPlan(3); setContext(100000);
  assert.equal(skill('hosa:develop'), null);            // baseline of the session
  assert.equal(skill('hosa:develop'), null);            // nothing closed since
  setPlan(4);
  assert.equal(skill('status'), null);                  // not a pipeline stage
  assert.ok(denied(skill('hosa:qa')));
  assert.equal(skill('hosa:qa'), null);                 // the user chose to stay
});

test('a light session chains freely', () => {
  setPlan(3); setContext(100000);
  assert.equal(skill('develop', 's2'), null);
  setPlan(4); setContext(30000);
  assert.equal(skill('qa', 's2'), null);
});

test('a hosa- subagent past its cap is refused every further call', () => {
  processPayload({ hook_event_name: 'SubagentStart', session_id: 's3', agent_id: 'a1', agent_type: 'hosa:hosa-ux-designer' });
  const call = () => processPayload({ hook_event_name: 'PreToolUse', tool_name: 'Bash', session_id: 's3', agent_id: 'a1' });
  for (let i = 0; i < 50; i++) assert.equal(call(), null);
  assert.ok(denied(call()));
  assert.ok(denied(call()));
  assert.equal(processPayload({ hook_event_name: 'PreToolUse', tool_name: 'SubagentHandback', session_id: 's3', agent_id: 'a1' }), null);
  const other = processPayload({ hook_event_name: 'PreToolUse', tool_name: 'Bash', session_id: 's3', agent_id: 'a2', agent_type: 'Explore' });
  assert.equal(other, null);
});

test('kill switch', () => {
  process.env.HOSA_BUDGET = '0';
  assert.equal(skill('qa', 's4'), null);
  delete process.env.HOSA_BUDGET;
});
