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
const usage = (n) => JSON.stringify({ type: 'assistant',
  message: { usage: { input_tokens: 1, cache_creation_input_tokens: 0, cache_read_input_tokens: n } } }) + '\n';
// The session's first call (its start), then its last one.
const setContext = (n, start = 30000) => fs.writeFileSync(transcript,
  JSON.stringify({ type: 'user', message: { content: 'x'.repeat(300 * 1024) } }) + '\n' + usage(start) + usage(n));
const skill = (name, session = 's1') => processPayload({ hook_event_name: 'PreToolUse', tool_name: 'Skill', session_id: session,
  cwd: project, transcript_path: transcript, tool_input: { skill: name } });

test('a heavy session that closed a stage is stopped once before the next stage', () => {
  setPlan(3); setContext(80000);
  assert.equal(skill('hosa:develop'), null);            // baseline of the session
  assert.equal(skill('hosa:develop'), null);            // nothing closed since
  setPlan(4);
  assert.equal(skill('status'), null);                  // not a pipeline stage
  assert.ok(denied(skill('hosa:qa')));
  assert.equal(skill('hosa:qa'), null);                 // the user chose to stay
});

test('a loop reopens stages: the ones closed again after it are seen', () => {
  setPlan(4); setContext(80000);
  assert.equal(skill('hosa:qa', 's-loop'), null);       // baseline: 4 closed
  setPlan(3);                                           // `back qa develop` reopened one
  assert.equal(skill('hosa:develop', 's-loop'), null);
  setPlan(4);                                           // closed again in this session
  assert.ok(denied(skill('hosa:qa', 's-loop')));
});

test('the stages come from pipeline.json: `audit` runs `qualite`, a stage too', () => {
  setPlan(3); setContext(80000);
  assert.equal(skill('hosa:develop', 's6'), null);
  setPlan(4);
  assert.ok(denied(skill('hosa:qualite', 's6')));      // missing from the old hand-kept list
});

test('a light session chains freely', () => {
  setPlan(3); setContext(80000);
  assert.equal(skill('develop', 's2'), null);
  setPlan(4); setContext(30000);
  assert.equal(skill('qa', 's2'), null);
});

test('the thresholds count above the session start: 54 k is no stage', () => {
  setPlan(3); setContext(54000, 54000);
  assert.equal(skill('hosa:develop', 's12'), null);
  setPlan(4); setContext(70000, 54000);
  assert.equal(skill('hosa:qa', 's12'), null);           // 16 k since the start
  setPlan(5); setContext(76000, 54000);
  assert.match(skill('hosa:qa', 's12').hookSpecificOutput.permissionDecisionReason, /76 k tokens \(22 k since its start\)/);
  setContext(118000, 54000);
  assert.equal(skill('hosa:changement', 's12'), null);   // under start + 70 k
  setContext(125000, 54000);
  assert.ok(denied(skill('hosa:changement', 's12')));
});

test('past the ceiling any Hosa skill is refused once, then every 50 k more', () => {
  setPlan(3); setContext(130000);
  assert.ok(denied(skill('hosa:changement', 's5')));
  assert.equal(skill('hosa:changement', 's5'), null);   // the user chose to stay
  assert.equal(skill('ponytail', 's5'), null);          // not a Hosa skill
  setContext(170000);
  assert.equal(skill('hosa:relecture', 's5'), null);
  setContext(195000);
  assert.ok(denied(skill('hosa:relecture', 's5')));
});

test('a hosa- subagent past its cap is refused every further call', () => {
  processPayload({ hook_event_name: 'SubagentStart', session_id: 's3', agent_id: 'a1', agent_type: 'hosa:hosa-ux-designer' });
  const call = () => processPayload({ hook_event_name: 'PreToolUse', tool_name: 'Bash', session_id: 's3', agent_id: 'a1' });
  for (let i = 1; i <= 50; i++) {
    const out = call();
    if (i === 40) assert.match(out.hookSpecificOutput.additionalContext, /10 tool calls left/); // warned once, not refused
    else assert.equal(out, null);
  }
  assert.ok(denied(call()));
  assert.ok(denied(call()));
  assert.equal(processPayload({ hook_event_name: 'PreToolUse', tool_name: 'SubagentHandback', session_id: 's3', agent_id: 'a1' }), null);
  const other = processPayload({ hook_event_name: 'PreToolUse', tool_name: 'Bash', session_id: 's3', agent_id: 'a2', agent_type: 'Explore' });
  assert.equal(other, null);
});

const agentFile = (id) => path.join(project, 't', 'subagents', `agent-${id}.jsonl`);
const setAgentContext = (id, n, ago = 0) => {
  fs.mkdirSync(path.dirname(agentFile(id)), { recursive: true });
  fs.writeFileSync(agentFile(id), JSON.stringify({ type: 'assistant', isSidechain: true,
    message: { usage: { input_tokens: 1, cache_creation_input_tokens: 0, cache_read_input_tokens: n } } }) + '\n');
  const t = (Date.now() - ago) / 1000;
  fs.utimesSync(agentFile(id), t, t);
};
const pre = (tool, session, input = {}, extra = {}) => processPayload({ hook_event_name: 'PreToolUse', tool_name: tool,
  session_id: session, cwd: project, transcript_path: transcript, tool_input: input, ...extra });

test('a hosa- subagent is warned, then stopped, on the size of its own context', () => {
  processPayload({ hook_event_name: 'SubagentStart', session_id: 's7', agent_id: 'a7', agent_type: 'hosa:hosa-product-owner' });
  setAgentContext('a7', 100000);
  const call = () => pre('Write', 's7', {}, { agent_id: 'a7' });
  assert.match(call().hookSpecificOutput.additionalContext, /100 k tokens of context \(cap 120 k\)/);
  assert.equal(call(), null);                                                    // warned once
  setAgentContext('a7', 125000);
  assert.match(call().hookSpecificOutput.permissionDecisionReason, /120 k tokens of context/);
  assert.equal(pre('SubagentHandback', 's7', {}, { agent_id: 'a7' }), null);
});

test('each Hosa agent records its KB and what its dispatch was for, for the resume card', () => {
  setPlan(0); setContext(10000);
  pre('Agent', 's12', { subagent_type: 'hosa:hosa-product-owner', description: 'Découpe tickets lot 5' });
  pre('Agent', 's12', { subagent_type: 'Explore', description: 'not Hosa' });
  processPayload({ hook_event_name: 'SubagentStart', session_id: 's12', agent_id: 'd1', agent_type: 'hosa:hosa-product-owner', cwd: project });
  const dir = process.env.HOSA_STATE_DIR;
  const state = fs.readdirSync(dir).filter((f) => f.startsWith('budget-')).map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')))
    .find((s) => s.what === 'Découpe tickets lot 5');
  assert.ok(state, 'the agent state holds its dispatch description');
  assert.equal(path.resolve(state.kb), path.resolve(project, '.hosa', 'kb'));
  assert.ok(state.started > 0);
});

test('a long final report is refused once, its questions and its resume point excluded', () => {
  processPayload({ hook_event_name: 'SubagentStart', session_id: 's11', agent_id: 'r1', agent_type: 'hosa:hosa-product-owner' });
  setAgentContext('r1', 30000);
  const report = (body, extra = '') => ({ message: `## En bref\nFait.\n\n## Sortie\n${body}\n${extra}` });
  const back = (input, id = 'r1') => pre('SubagentHandback', 's11', input, { agent_id: id });
  const questions = `## Open Questions\n${'**Q1 — choix ?** (bloquante)\n'.repeat(400)}\n## Reprise\n${'reste '.repeat(800)}`;
  assert.equal(back(report('- `kb/tickets/a.md`', questions)), null);   // long, but only questions and resume point
  const out = back(report('détail '.repeat(700)));
  assert.match(out.hookSpecificOutput.permissionDecisionReason, /4929 characters .*4000 at most/);
  assert.equal(pre('Write', 's11', {}, { agent_id: 'r1' }), null);     // moves its details into a file
  assert.equal(back(report('détail '.repeat(700))), null);              // the retry passes
  // the report is the deliverable: no Write in its tools
  processPayload({ hook_event_name: 'SubagentStart', session_id: 's11', agent_id: 'r2', agent_type: 'hosa:hosa-reviewer' });
  assert.equal(back(report('écart '.repeat(900)), 'r2'), null);
  // at its context cap the agent can't write a file any more
  processPayload({ hook_event_name: 'SubagentStart', session_id: 's11', agent_id: 'r3', agent_type: 'hosa:hosa-security' });
  setAgentContext('r3', 125000);
  assert.equal(back(report('détail '.repeat(700)), 'r3'), null);
});

test('past the ceiling an agent dispatch from the main session is refused once', () => {
  setPlan(3); setContext(130000);
  assert.ok(denied(pre('Agent', 's8', { subagent_type: 'hosa:hosa-product-owner' })));
  assert.equal(pre('Agent', 's8', { subagent_type: 'hosa:hosa-product-owner' }), null);
});

test('an agent idle past its cache with a heavy context is not resumed, once', () => {
  setPlan(3); setContext(10000);
  setAgentContext('old', 180000, 30 * 60000);
  assert.match(pre('SendMessage', 's9', { to: 'old' }).hookSpecificOutput.permissionDecisionReason, /idle 30 min with 180 k/);
  assert.equal(pre('SendMessage', 's9', { to: 'old' }), null);                   // the user wants it resumed
  setAgentContext('fresh', 180000, 60000);
  assert.equal(pre('SendMessage', 's9', { to: 'fresh' }), null);                 // its cache still holds
  setAgentContext('light', 20000, 30 * 60000);
  assert.equal(pre('SendMessage', 's9', { to: 'light' }), null);
});

test('during backlog: two Hosa agents at once, the security and legal notes on sonnet', () => {
  fs.writeFileSync(plan, '## Structuration\n| Étape | Statut | Mis à jour | Détail |\n|---|---|---|---|\n' +
    '| `interface` | fait |  |  |\n| `backlog` | en cours |  |  |\n');
  setContext(10000);
  const start = (id) => processPayload({ hook_event_name: 'SubagentStart', session_id: 's10', agent_id: id, agent_type: 'hosa:hosa-juge' });
  start('b1'); start('b2');
  const po = () => pre('Agent', 's10', { subagent_type: 'hosa:hosa-product-owner' });
  assert.match(po().hookSpecificOutput.permissionDecisionReason, /2 Hosa agents are running/);
  assert.equal(pre('Agent', 's10', { subagent_type: 'Explore' }), null);        // not a Hosa agent
  processPayload({ hook_event_name: 'SubagentStop', session_id: 's10', agent_id: 'b1' });
  assert.equal(po(), null);
  assert.match(pre('Agent', 's10', { subagent_type: 'hosa:hosa-security' }).hookSpecificOutput.permissionDecisionReason,
    /model: "sonnet"/);
  assert.equal(pre('Agent', 's10', { subagent_type: 'hosa:hosa-security', model: 'sonnet' }), null);
  setPlan(3);                                                                    // backlog no longer under way
  assert.equal(pre('Agent', 's10', { subagent_type: 'hosa:hosa-security' }), null);
});

test('kill switch', () => {
  process.env.HOSA_BUDGET = '0';
  assert.equal(skill('qa', 's4'), null);
  delete process.env.HOSA_BUDGET;
});

test('a message after a pause longer than the cache, in a heavy session, is refused once and given back', () => {
  const t = path.join(project, 'pause.jsonl');
  const call = (n, minutesAgo) => JSON.stringify({ type: 'assistant', timestamp: new Date(Date.now() - minutesAgo * 60000).toISOString(),
    message: { usage: { input_tokens: 1, cache_creation_input_tokens: 0, cache_read_input_tokens: n } } }) + '\n';
  const say = (prompt, session, extra = {}) => processPayload({ hook_event_name: 'UserPromptSubmit', session_id: session, cwd: project,
    transcript_path: t, prompt, ...extra });
  setPlan(3);
  fs.writeFileSync(t, call(30000, 200) + call(150000, 130));
  const out = say('développe le lot suivant', 'p1');
  assert.equal(out.decision, 'block');
  assert.match(out.reason, /Pause de 2 h 10 .* 150 k tokens .*\/clear, puis « reprends » .* 30 k .*« développe le lot suivant »/);
  assert.equal(say('développe le lot suivant', 'p1'), null);          // sent again: the user chose to stay
  assert.equal(say('/clear', 'p2'), null);                            // a command passes
  fs.writeFileSync(t, call(30000, 200) + call(150000, 20));
  assert.equal(say('la suite', 'p3'), null);                          // cache still alive
  fs.writeFileSync(t, call(30000, 200) + call(40000, 130));
  assert.equal(say('la suite', 'p4'), null);                          // light: a /clear saves nothing
  fs.writeFileSync(t, call(30000, 200) + call(150000, 130));
  assert.equal(say('la suite', 'p5', { cwd: os.tmpdir() }), null);    // no plan: not a Hosa pipeline session
  process.env.HOSA_BUDGET = '0';
  try { assert.equal(say('la suite', 'p6'), null); } finally { delete process.env.HOSA_BUDGET; }
});
