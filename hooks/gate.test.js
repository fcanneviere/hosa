const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const { processPayload, gitCalls } = require('./gate');

function project(files) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-gate-'));
  for (const [f, content] of Object.entries(files)) {
    fs.mkdirSync(path.dirname(path.join(root, f)), { recursive: true });
    fs.writeFileSync(path.join(root, f), content);
  }
  fs.mkdirSync(path.join(root, '.worktrees', 'sprint', 's1'), { recursive: true });
  return root;
}
const bash = (root, command, cwd = root) => processPayload({ tool_name: 'Bash', cwd, tool_input: { command } });
const denied = (out) => out && out.hookSpecificOutput.permissionDecisionReason;

const ticket = (revue) => `---\ntype: Ticket\nstate: doing\n---\n## Revue\n${revue}\n`;
const commit = (wt) => `git -C "${wt}" commit -m "feat: x" -m "Hosa-Ticket: t1"`;

test('parses -C, cd and quoted arguments', () => {
  const [a, b] = gitCalls('cd /tmp/x && git -C sub -c a=b commit -m "a; b" && git merge --no-ff sprint/s1', '/r');
  assert.equal(a.sub, 'commit');
  assert.ok(a.dir.endsWith(path.join('x', 'sub')));
  assert.deepEqual(a.args, ['-m', 'a; b']);
  assert.deepEqual(b.args, ['--no-ff', 'sprint/s1']);
});

test('a ticket commit needs a passed review', () => {
  const wt = (r) => path.join(r, '.worktrees', 'sprint', 's1');
  let r = project({ '.hosa/kb/tickets/t1.md': ticket('- 2026-10-10 — FAIL — CA2 manque') });
  assert.match(denied(bash(r, commit(wt(r)))), /last `## Revue` line is FAIL/);
  r = project({ '.hosa/kb/tickets/t1.md': ticket('- 2026-10-09 — FAIL — x\n- 2026-10-10 — PASS-WITH-NOTES — y') });
  assert.equal(bash(r, commit(wt(r))), null);
  r = project({ '.hosa/kb/tickets/t1.md': '---\ntype: Ticket\n---\n' });
  assert.match(denied(bash(r, commit(wt(r)))), /is missing/);
});

test('a lot commit needs a passed review on every ticket it names', () => {
  const r = project({ '.hosa/kb/tickets/t1.md': ticket('- 2026-10-10 — PASS — ok'), '.hosa/kb/tickets/t2.md': ticket('- 2026-10-10 — FAIL — CA1') });
  const wt = path.join(r, '.worktrees', 'sprint', 's1');
  const lot = (b) => `git -C "${wt}" commit -m "feat: lot" -m "Hosa-Ticket: t1" -m "Hosa-Ticket: ${b}"`;
  assert.match(denied(bash(r, lot('t2'))), /ticket `t2`.*FAIL/);
  fs.writeFileSync(path.join(r, '.hosa/kb/tickets/t2.md'), ticket('- 2026-10-11 — PASS — ok'));
  assert.equal(bash(r, lot('t2')), null);
});

test('a sprint commit without a ticket is refused, except an amend', () => {
  const r = project({});
  const wt = path.join(r, '.worktrees', 'sprint', 's1');
  assert.match(denied(bash(r, 'git commit -m "wip"', wt)), /Hosa-Ticket/);
  assert.equal(bash(r, 'git commit --amend --no-edit', wt), null);
});

test('commits outside a sprint worktree pass', () => {
  assert.equal(bash(project({}), 'git commit -m "chore: x"'), null);
});

test('a co-author line is refused in a Hosa project, anywhere else it passes', () => {
  const r = project({ '.hosa/kb/index.md': '' });
  const heredoc = 'git commit -F - <<\'EOF\'\nfix(infra): x\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\nEOF';
  assert.match(denied(bash(r, heredoc)), /Co-Authored-By/);                              // the pilot2 case
  assert.match(denied(bash(r, commit(path.join(r, '.worktrees', 'sprint', 's1')) + ' -m "co-authored-by: x"')), /identity only/);
  assert.equal(bash(project({}), heredoc), null);
});

const sprint = (extra) => `---\ntype: Sprint\n---\n## Tickets\n- [T1](../tickets/t1.md)\n${extra}`;
const done = '---\ntype: Ticket\nstate: done\nverified: { by: hosa-product-owner/1.0, at: x }\n---\n';
const full = {
  '.hosa/kb/tickets/t1.md': done,
  '.hosa/kb/test/t1-technique.md': '## Résultats techniques\n12/12 passés\n',
  '.hosa/kb/test/t1-les-parents.md': '### Critères\n- CA1 — Oui — capture\n## Verdict\nAccepté\n',
};

test('a sprint lands once its QA gate is met', () => {
  const r = project({ ...full, '.hosa/kb/sprints/s1.md': sprint('## Audit\nBloquant : 0 — À corriger : 2 — Mineur : 1\n## Démo\n- T1 KO : bouton\n- T1 OK\n') });
  assert.equal(bash(r, 'git merge --no-ff sprint/s1 -m "Merge sprint s1"'), null);
});

test('the merge lists every missing proof', () => {
  const r = project({
    ...full,
    '.hosa/kb/tickets/t1.md': '---\nstate: doing\n---\n',
    '.hosa/kb/test/t1-les-parents.md': '### Critères\n- CA1 — Non — rien\n## Verdict\nRefusé\n',
    '.hosa/kb/sprints/s1.md': sprint('## Audit\nBloquant : 1\n## Démo\n- T2 KO\n'),
  });
  const why = denied(bash(r, 'git merge --no-ff sprint/s1'));
  for (const gap of [/pas `done` et `verified`/, /recette Refusé/, /critère répondu Non/, /Bloquant : 1/, /T2 encore KO/]) assert.match(why, gap);
  assert.match(denied(bash(project({ ...full, '.hosa/kb/sprints/s1.md': sprint('') }), 'git merge sprint/s1')), /pas de `## Audit`[\s\S]*pas de `## Démo`/);
});

test('every acceptance criterion needs a proof', () => {
  const files = {
    ...full,
    '.hosa/kb/tickets/t1.md': `${done}## Critères d'acceptation\n- CA1 — Étant donné…\n- CA2 — Étant donné…\n- CA3 — Étant donné…\n`,
    '.hosa/kb/test/t1-technique.md': '## Cas\n- [CA2] liste vide\n## Résultats techniques\nok\n',
    '.hosa/kb/sprints/s1.md': sprint('## Audit\nBloquant : 0\n## Démo\n- T1 OK\n'),
  };
  assert.match(denied(bash(project(files), 'git merge sprint/s1')), /t1 : CA3 prouvé\(s\) par aucun cas/);
  files['.hosa/kb/test/t1-technique.md'] += '- [CA3] notification différée\n';
  assert.equal(bash(project(files), 'git merge sprint/s1'), null);
});

test('other git commands pass', () => {
  const r = project({ '.hosa/kb/sprints/s1.md': sprint('') });
  assert.equal(bash(r, 'git merge-base --is-ancestor main sprint/s1'), null);
  assert.equal(bash(r, 'git merge --abort'), null);
  assert.equal(bash(r, 'git -C .worktrees/sprint/s1 merge --no-ff main'), null);
  assert.equal(bash(r, 'git status'), null);
});

test('a sprint environment is built only from its worktree', () => {
  const r = project({});
  const wt = path.join(r, '.worktrees', 'sprint', 's1');
  const up = 'docker compose -p courses-sprint-s1 up -d --build --force-recreate';
  assert.match(denied(bash(r, `cd "${r}" && ${up}`)), /not from its worktree/);         // the pilot2 case
  assert.equal(bash(r, `cd "${wt}" && ${up}`), null);
  assert.equal(bash(r, `docker compose -f "${wt}/docker-compose.yml" -p courses-sprint-s1 up -d`), null);
  assert.equal(bash(r, 'docker compose -p courses-sprint-s1 exec -T app pytest'), null); // no new container
  assert.match(denied(bash(r, 'docker compose -p courses up -d', wt)), /base environment from a sprint worktree/);
  assert.equal(bash(r, 'docker compose -p courses up -d'), null);
});

test('a Hosa script by its cache path is refused, reading the cache passes', () => {
  const r = project({});
  const S = 'C:/Users/u/.claude/plugins/cache/hosa/hosa/0.1.53/skills';
  // the pilot2 command: a variable, the project's venv, a guessed folder
  assert.match(denied(bash(r, `S="${S}"; PY=.venv/Scripts/python; ls $S/qa/scripts; $PY $S/status/scripts/avancement.py .hosa/kb start qa`)),
    /avancement <args>/);
  assert.match(denied(bash(r, `python "${S}/okf/scripts/okf_validate.py" .hosa/kb`)), /okf_validate/);
  assert.equal(bash(r, `cat "${S}/qa/SKILL.md"`), null);
  assert.equal(bash(r, `grep -n x "${S}/okf/scripts/kb_query.py"`), null);
  assert.equal(bash(r, `node "${S}/interface/scripts/capture.mjs" page.html`), null);
});

test('a cd into the KB is refused, a subshell or another folder passes', () => {
  const r = project({});
  assert.match(denied(bash(r, 'cd .hosa/kb/cdc && ls')), /inside the KB/);
  assert.match(denied(bash(r, `cd "${path.join(r, '.hosa')}"`)), /git -C/);
  assert.match(denied(bash(r, 'cd .hosa/kb/cdc && ls')), /\(cd <path> && …\)/);          // the form that passes, named
  assert.equal(bash(r, '(cd .hosa/kb && git status)'), null);
  // an agent's cd lasts one command: nothing to protect, no call to lose
  assert.equal(processPayload({ tool_name: 'Bash', cwd: r, agent_id: 'a1', tool_input: { command: 'cd .hosa/kb/cdc && ls' } }), null);
  assert.equal(bash(r, 'cd .worktrees/sprint/s1 && ls'), null);
});

test('a dispatch from a session left inside the KB is refused: the agent\'s memory would land there', () => {
  const r = project({});
  const agent = (cwd) => processPayload({ tool_name: 'Agent', cwd, tool_input: { subagent_type: 'hosa:hosa-tester', prompt: 'x' } });
  assert.match(denied(agent(path.join(r, '.hosa', 'kb'))), /inside the KB.*agent-memory-local/s);
  const out = denied(agent(path.join(r, '.hosa', 'kb', 'tickets')));
  assert.ok(out.includes(`cd "${r.replace(/\\/g, '/')}"`), out);              // names the root to go back to
  assert.match(denied(processPayload({ tool_name: 'Task', cwd: '/c/dev/p/.hosa/kb', tool_input: {} })), /inside the KB/);
  assert.equal(agent(r), null);
  assert.equal(agent(path.join(r, '.worktrees', 'sprint', 's1')), null);
  assert.equal(agent(path.join(r, '.hosacode')), null);                        // a name starting with .hosa is not the KB
  process.env.HOSA_GATE = '0';
  try { assert.equal(agent(path.join(r, '.hosa', 'kb')), null); } finally { delete process.env.HOSA_GATE; }
});

test('two FAIL reviews in a row stop the correction loop until the user decides', () => {
  const dev = (r, prompt, type = 'hosa:hosa-developer') =>
    processPayload({ tool_name: 'Agent', cwd: r, tool_input: { subagent_type: type, prompt } });
  const two = '- 2026-10-09 — FAIL — CA2 manque\n- 2026-10-10 — FAIL — CA2 manque encore';
  let r = project({ '.hosa/kb/tickets/t1.md': ticket(two), '.hosa/kb/tickets/t10.md': ticket('') });
  assert.match(denied(dev(r, 'correction du ticket t1, manques : CA2')), /2 FAIL reviews in a row/);
  assert.equal(dev(r, 'ticket t10'), null);                                  // t1 inside t10 is not t1
  assert.equal(dev(r, 'ticket t1', 'hosa:hosa-reviewer'), null);            // only the developer is held
  r = project({ '.hosa/kb/tickets/t1.md': ticket('- 2026-10-09 — PASS — ok\n- 2026-10-10 — FAIL — CA2') });
  assert.equal(dev(r, 'correction t1'), null);                               // one FAIL: the loop goes on
  r = project({ '.hosa/kb/tickets/t1.md': ticket(`${two}\n- 2026-10-11 — DÉCISION — continuer, une correction de plus`) });
  assert.equal(dev(r, 'correction t1'), null);                               // the user chose: count restarts
});

test('the review loop\'s bound is the graph\'s, not a second number in the hook', () => {
  const g = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'skills', 'status', 'scripts', 'pipeline.json'), 'utf8'));
  assert.equal(g.tasks.controls.find((c) => c.stage === 'develop' && c.id === '*.revue').fails, 2);
  assert.doesNotMatch(fs.readFileSync(path.join(__dirname, 'gate.js'), 'utf8'), /LOOP_MAX = \d/);
});

const ps = (root, command, cwd = root) => processPayload({ tool_name: 'PowerShell', cwd, tool_input: { command } });

test('the PowerShell tool meets the same gates as Bash', () => {
  const r = project({ '.hosa/kb/tickets/t1.md': ticket('- 2026-10-10 — FAIL — CA2'), '.hosa/kb/sprints/s1.md': sprint('') });
  const wt = path.join(r, '.worktrees', 'sprint', 's1');
  assert.match(denied(ps(r, commit(wt))), /no passed code review/);
  assert.match(denied(ps(r, 'git commit -m "x`n`nCo-Authored-By: C <n@a.com>"')), /identity only/);
  assert.match(denied(ps(r, 'git merge --no-ff sprint/s1')), /QA gate fails/);
  assert.match(denied(ps(r, 'Set-Location -Path .hosa/kb')), /inside the KB/);
  assert.match(denied(ps(r, '(cd .hosa/kb); git status')), /inside the KB/);  // PowerShell parentheses don't fork
  assert.doesNotMatch(denied(ps(r, 'cd .hosa/kb')), /subshell/);             // no advice PowerShell refuses
  const hooks = JSON.parse(fs.readFileSync(path.join(__dirname, 'hooks.json'), 'utf8')).hooks.PreToolUse;
  const gate = hooks.find((h) => h.hooks.some((x) => /gate\.js/.test(x.command)));
  for (const tool of ['Bash', 'PowerShell', 'Agent', 'Task']) assert.match(tool, new RegExp(`^(${gate.matcher})$`));
  assert.equal(ps(r, 'Set-Location C:/dev; git status'), null);
});

test('a subshell or a nested shell does not hide a commit from its gate', () => {
  const r = project({ '.hosa/kb/tickets/t1.md': ticket('- 2026-10-10 — FAIL — CA2') });
  assert.match(denied(bash(r, '(cd .worktrees/sprint/s1 && git commit -m x -m "Hosa-Ticket: t1")')), /no passed code review/);
  assert.match(denied(bash(r, 'bash -c "cd .worktrees/sprint/s1 && git commit -m x"')), /Hosa-Ticket/);
  assert.match(denied(bash(r, 'bash -lc "cd .worktrees/sprint/s1 && git commit -m x"')), /Hosa-Ticket/);
  assert.match(denied(bash(r, 'powershell -Command "cd .worktrees/sprint/s1; git commit -m x"')), /Hosa-Ticket/);
  const [a, b] = gitCalls('(cd sub && git status) && git log', '/r');
  assert.ok(a.dir.endsWith('sub'));
  assert.equal(path.resolve(b.dir), path.resolve('/r'));                    // the subshell's cd ends at its `)`
  assert.equal(bash(r, '(cd .hosa/kb && git status)'), null);              // a subshell cd into the KB passes
  assert.equal(bash(r, 'git log --format="%H (x)" -1 && echo "$(date -u)"'), null);
});

test('an amend without a trailer keeps its message, or is refused', () => {
  const r = project({});
  const wt = path.join(r, '.worktrees', 'sprint', 's1');
  assert.equal(bash(r, 'git commit --amend --no-edit', wt), null);
  assert.match(denied(bash(r, 'git commit --amend -m "other"', wt)), /--no-edit/);
});

test('a review line\'s verdict is its first one: a note quoting PASS does not pass a FAIL', () => {
  const wt = (r) => path.join(r, '.worktrees', 'sprint', 's1');
  let r = project({ '.hosa/kb/tickets/t1.md': ticket('- 2026-10-10 — FAIL — les tests PASS mais CA2 manque') });
  assert.match(denied(bash(r, commit(wt(r)))), /last `## Revue` line is FAIL/);
  r = project({ '.hosa/kb/tickets/t1.md': ticket('- 2026-10-10 — PASS-WITH-NOTES — un ancien FAIL corrigé') });
  assert.equal(bash(r, commit(wt(r))), null);
  r = project({ '.hosa/kb/tickets/t1.md': ticket('- 2026-10-09 — FAIL — x\n- 2026-10-10 — PASS — ok\n- 2026-10-11 — DÉCISION — garder') });
  assert.equal(bash(r, commit(wt(r))), null);                               // a decision line has no verdict
  r = project({ '.hosa/kb/tickets/t1.md': ticket('- 2026-10-09 — PASS — x\n- 2026-10-10 — FAIL — voir — DÉCISION à venir') });
  assert.match(denied(bash(r, commit(wt(r)))), /FAIL/);                    // DÉCISION quoted in a note is no decision
});

test('hardened reading: escapes, cmd /c, eval, refspecs, another repository', () => {
  const r = project({ '.hosa/kb/tickets/t1.md': ticket('- 2026-10-10 — FAIL — CA2'), '.hosa/kb/sprints/s1.md': sprint('') });
  const wt = path.join(r, '.worktrees', 'sprint', 's1');
  assert.match(denied(bash(r, 'cd .worktrees/sprint/s1 && git commit -m x \\( -m "Hosa-Ticket: t1"')), /no passed code review/);
  assert.match(denied(bash(r, 'cmd /c "cd .worktrees\\sprint\\s1 && git commit -m x"')), /Hosa-Ticket/);
  assert.match(denied(bash(r, 'eval "cd .worktrees/sprint/s1 && git commit -m x"')), /Hosa-Ticket/);
  assert.match(denied(ps(r, 'iex "cd .worktrees/sprint/s1; git commit -m x"')), /Hosa-Ticket/);
  for (const ref of ['+sprint/s1:main', 'sprint/s1~0', 'sprint/s1^{commit}', 'sprint/s1@{1}']) {
    assert.match(denied(bash(r, `git pull . ${ref}`)), /QA gate fails/, ref);
  }
  assert.match(denied(bash(r, `git --git-dir="${r}/.git" pull . sprint/s1`, wt)), /QA gate fails/);
  assert.equal(ps(r, 'git -C C:\\dev\\x status'), null);                    // a PowerShell backslash is a path
});

test('a sprint branch lands through its gate whatever its ref name', () => {
  const r = project({ '.hosa/kb/sprints/s1.md': sprint('') });
  for (const ref of ['refs/heads/sprint/s1', 'heads/sprint/s1', 'origin/sprint/s1']) {
    assert.match(denied(bash(r, `git merge --no-ff ${ref}`)), /QA gate fails/, ref);
  }
  assert.match(denied(bash(r, 'git pull . sprint/s1')), /QA gate fails/);
  assert.equal(bash(r, 'git merge --no-ff main -m "Merge main into sprint/s1"', path.join(r, '.worktrees', 'sprint', 's1')), null);
  assert.equal(bash(r, 'git pull origin sprint/s1', path.join(r, '.worktrees', 'sprint', 's1')), null); // a sync, not a landing
});

test('the review loop\'s bound holds for a correction routed to debug', () => {
  const r = project({ '.hosa/kb/tickets/t1.md': ticket('- 2026-10-09 — FAIL — a\n- 2026-10-10 — FAIL — b') });
  const out = processPayload({ tool_name: 'Agent', cwd: r, tool_input: { subagent_type: 'hosa:hosa-debugger', prompt: 'ticket t1' } });
  assert.match(denied(out), /2 FAIL reviews in a row/);
});
