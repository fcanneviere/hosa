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

test('a tester that reads without writing is refused once, before its cap leaves it unable to write', () => {
  processPayload({ hook_event_name: 'SubagentStart', session_id: 's13', agent_id: 't1', agent_type: 'hosa:hosa-tester' });
  setAgentContext('t1', 85000);
  assert.equal(pre('Read', 's13', {}, { agent_id: 't1' }), null);
  setAgentContext('t1', 92000);
  assert.match(pre('Read', 's13', {}, { agent_id: 't1' }).hookSpecificOutput.permissionDecisionReason,
    /92 k tokens of context and written no file.*Plan de tâches/);
  assert.equal(pre('Read', 's13', {}, { agent_id: 't1' }), null);      // the retry passes
  // a tester that wrote a file early is never refused for its reads
  processPayload({ hook_event_name: 'SubagentStart', session_id: 's13', agent_id: 't2', agent_type: 'hosa:hosa-tester' });
  setAgentContext('t2', 20000);
  assert.equal(pre('Write', 's13', {}, { agent_id: 't2' }), null);
  setAgentContext('t2', 92000);
  assert.equal(pre('Read', 's13', {}, { agent_id: 't2' }), null);
  // another agent type reads as it likes
  processPayload({ hook_event_name: 'SubagentStart', session_id: 's13', agent_id: 't3', agent_type: 'hosa:hosa-developer' });
  setAgentContext('t3', 92000);
  assert.equal(pre('Read', 's13', {}, { agent_id: 't3' }), null);
});

test('a tester report with questions and no file written is refused once', () => {
  const back = (message, id) => pre('SubagentHandback', 's14', { message }, { agent_id: id });
  const start = (id, n) => {
    processPayload({ hook_event_name: 'SubagentStart', session_id: 's14', agent_id: id, agent_type: 'hosa:hosa-tester' });
    setAgentContext(id, n);
  };
  start('q1', 40000);
  const asks = '## En bref\nRien écrit.\n\n## Open Questions\n**Q1 — quel module ?**\n';
  assert.match(back(asks, 'q1').hookSpecificOutput.permissionDecisionReason, /no test file written.*first ticket/);
  assert.equal(back(asks, 'q1'), null);                                  // the retry passes
  start('q2', 40000);
  assert.ok(denied(back('## En bref\nLu.\n\n## Open Questions\nNone\n\n## Reprise\nÉcrire les tests.', 'q2')));
  start('q3', 40000);                                                    // nothing asked, nothing left: an install request
  assert.equal(back('## Installation nécessaire\npytest\n\n## Open Questions\nNone\n', 'q3'), null);
  start('q4', 40000);                                                    // it wrote its tests
  pre('Write', 's14', {}, { agent_id: 'q4' });
  assert.equal(back(asks, 'q4'), null);
  start('q5', 125000);                                                   // at its cap it can't write any more
  assert.equal(back(asks, 'q5'), null);
  process.env.HOSA_TESTER_ECRIT = '0';
  start('q6', 40000);
  assert.equal(back(asks, 'q6'), null);
  delete process.env.HOSA_TESTER_ECRIT;
});

test('a failure handed back without its output is refused once', () => {
  // rieki sprint-4: a browser test « à revérifier », its failure « à relire dans /tmp/r3.txt »
  const back = (message, id) => pre('SubagentHandback', 's15', { message }, { agent_id: id });
  const start = (id, type = 'hosa:hosa-developer') => {
    processPayload({ hook_event_name: 'SubagentStart', session_id: 's15', agent_id: id, agent_type: type });
    setAgentContext(id, 40000);
    pre('Write', 's15', {}, { agent_id: id });
  };
  const vague = '## Checks\n- navigateur : 3 passed, 1 failed, 1 error, à relire dans /tmp/r3.txt\n';
  start('f1');
  assert.match(back(vague, 'f1').hookSpecificOutput.permissionDecisionReason, /`file::test` and its error line/);
  assert.equal(back(vague, 'f1'), null);                                // the retry passes
  start('f2');
  assert.ok(denied(back('## Checks\n- `test_e2e` en échec, à revérifier après le teardown.\n', 'f2')));
  start('f3');                                                          // quoted: passes
  assert.equal(back('## Checks\n- 1 failed : `tests/t.py::test_a` — AssertionError: 3 != 4\n', 'f3'), null);
  start('f4');                                                          // nothing fails: a temp path is no matter
  assert.equal(back('## Checks\nsuite complète 120/120, sortie dans /tmp/r.txt\n', 'f4'), null);
  start('f5', 'hosa:hosa-product-owner');                               // other agents: not theirs
  assert.equal(back(vague, 'f5'), null);
  process.env.HOSA_ECHEC_CITE = '0';
  start('f6');
  assert.equal(back(vague, 'f6'), null);
  delete process.env.HOSA_ECHEC_CITE;
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

test('during backlog: two Hosa agents at once', () => {
  fs.writeFileSync(plan, '## Tâches\n| Tâche | Étape | Agent | Objet | Statut | Mis à jour | Sortie | Détail |\n' +
    '|---|---|---|---|---|---|---|---|\n| stories-2 | `backlog` | hosa-product-owner |  | à faire |  |  |  |\n\n' +
    '## Structuration\n| Étape | Statut | Mis à jour | Détail |\n|---|---|---|---|\n' +
    '| `interface` | fait |  |  |\n| `backlog` | en cours |  |  |\n');
  setContext(10000);
  const start = (id) => processPayload({ hook_event_name: 'SubagentStart', session_id: 's10', agent_id: id, agent_type: 'hosa:hosa-juge' });
  start('b1'); start('b2');
  const po = () => pre('Agent', 's10', { subagent_type: 'hosa:hosa-product-owner' });
  assert.match(po().hookSpecificOutput.permissionDecisionReason, /2 Hosa agents are running/);
  assert.equal(pre('Agent', 's10', { subagent_type: 'Explore' }), null);        // not a Hosa agent
  processPayload({ hook_event_name: 'SubagentStop', session_id: 's10', agent_id: 'b1' });
  assert.equal(po(), null);
});

test('during sprint: the notes of its tickets, two agents at once, security and legal on sonnet', () => {
  fs.writeFileSync(plan, '## Tâches\n| Tâche | Étape | Agent | Objet | Statut | Mis à jour | Sortie | Détail |\n' +
    '|---|---|---|---|---|---|---|---|\n| securite-1 | `sprint` (s4) | hosa-security |  | à faire |  |  |  |\n\n' +
    '## Sprint s4\n| Étape | Statut | Mis à jour | Détail |\n|---|---|---|---|\n' +
    '| `sprint` | en cours |  |  |\n');
  setContext(10000);
  assert.match(pre('Agent', 's12', { subagent_type: 'hosa:hosa-security' }).hookSpecificOutput.permissionDecisionReason,
    /model: "sonnet"/);
  assert.equal(pre('Agent', 's12', { subagent_type: 'hosa:hosa-security', model: 'sonnet' }), null);
  setPlan(3);                                                                    // sprint no longer under way
  assert.equal(pre('Agent', 's12', { subagent_type: 'hosa:hosa-security' }), null);
});

test('during qa-plan: two test-plan lots at once, a sprint of 20 tickets is 5 lots', () => {
  fs.writeFileSync(plan, '## Tâches\n| Tâche | Étape | Agent | Objet | Statut | Mis à jour | Sortie | Détail |\n' +
    '|---|---|---|---|---|---|---|---|\n| plans-3 | `qa-plan` (s4) | hosa-qa-lead |  | à faire |  |  |  |\n\n' +
    '## Sprint s4\n| Étape | Statut | Mis à jour | Détail |\n|---|---|---|---|\n' +
    '| `sprint` | fait |  |  |\n| `qa-plan` | en cours |  |  |\n');
  setContext(10000);
  const start = (id) => processPayload({ hook_event_name: 'SubagentStart', session_id: 's11', agent_id: id, agent_type: 'hosa:hosa-qa-lead' });
  start('q1'); start('q2');
  const lead = () => pre('Agent', 's11', { subagent_type: 'hosa:hosa-qa-lead' });
  assert.match(lead().hookSpecificOutput.permissionDecisionReason, /Hosa agents are running during `qa-plan`, 2 at most/);
  setPlan(3);                                                                    // qa-plan no longer under way
  assert.equal(lead(), null);
});

test('a dispatch during a stage with no task of its agent is refused once, with the command', () => {
  const head = '## Tâches\n| Tâche | Étape | Agent | Objet | Statut | Mis à jour | Sortie | Détail |\n|---|---|---|---|---|---|---|---|\n';
  const stages = '## Structuration\n| Étape | Statut | Mis à jour | Détail |\n|---|---|---|---|\n' +
    '| `stack` | fait |  |  |\n| `infra` | en cours |  |  |\n';
  setContext(10000);
  const infra = (type, session = 's20') => pre('Agent', session, { subagent_type: `hosa:${type}` });
  fs.writeFileSync(plan, head + '| environnement | `infra` | hosa-architect |  | fait |  |  |  |\n\n' + stages);
  const out = infra('hosa-architect');
  assert.ok(denied(out));                                                        // its only task is done
  assert.match(out.hookSpecificOutput.permissionDecisionReason, /task add infra <id> --agent hosa-architect/);
  assert.equal(infra('hosa-architect'), null);                                   // sent again: it writes nothing
  assert.equal(infra('hosa-git'), null);                                         // checkpoints and relays: exempt
  assert.equal(infra('hosa-key-user'), null);
  fs.writeFileSync(plan, head + '| conception | `infra` | hosa-architect |  | à faire |  |  |  |\n\n' + stages);
  assert.equal(infra('hosa-architect', 's21'), null);                            // its task is listed
  process.env.HOSA_TASKS = '0';
  assert.equal(infra('hosa-data-engineer', 's21'), null);                        // kill switch
  delete process.env.HOSA_TASKS;
  setPlan(3);                                                                    // no stage under way
  assert.equal(infra('hosa-data-engineer', 's22'), null);
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
