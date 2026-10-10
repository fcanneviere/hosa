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

test('a sprint commit without a ticket is refused, except an amend', () => {
  const r = project({});
  const wt = path.join(r, '.worktrees', 'sprint', 's1');
  assert.match(denied(bash(r, 'git commit -m "wip"', wt)), /Hosa-Ticket/);
  assert.equal(bash(r, 'git commit --amend --no-edit', wt), null);
});

test('commits outside a sprint worktree pass', () => {
  assert.equal(bash(project({}), 'git commit -m "chore: x"'), null);
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
  for (const gap of [/not done and verified/, /recette Refusé/, /criterion answered Non/, /Bloquant : 1/, /T2 still KO/]) assert.match(why, gap);
  assert.match(denied(bash(project({ ...full, '.hosa/kb/sprints/s1.md': sprint('') }), 'git merge sprint/s1')), /no `## Audit`[\s\S]*no `## Démo`/);
});

test('other git commands pass', () => {
  const r = project({ '.hosa/kb/sprints/s1.md': sprint('') });
  assert.equal(bash(r, 'git merge-base --is-ancestor main sprint/s1'), null);
  assert.equal(bash(r, 'git merge --abort'), null);
  assert.equal(bash(r, 'git -C .worktrees/sprint/s1 merge --no-ff main'), null);
  assert.equal(bash(r, 'git status'), null);
});
