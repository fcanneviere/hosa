const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const { resumeContext } = require('./avancement');

function kb(content) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-avancement-'));
  fs.mkdirSync(path.join(root, '.hosa', 'kb', 'project'), { recursive: true });
  if (content) fs.writeFileSync(path.join(root, '.hosa', 'kb', 'project', 'avancement.md'), content);
  return root;
}

test('returns the resume point and the stage in progress', () => {
  const root = kb([
    '---', 'type: Plan d\'avancement', '---',
    '## Point de reprise', '- En cours : `develop` (sprint s1) — ticket 2/3', '- Prochaine action : develop ticket-b', '',
    '## Sprint s1', '| Étape | Statut | Mis à jour | Détail |', '|---|---|---|---|',
    '| `qa-plan` | fait | 2026-10-08 |  |', '| `develop` | en cours | 2026-10-08 | ticket 2/3 |', '| `qa` | à faire |  |  |',
  ].join('\n'));
  const ctx = resumeContext(path.join(root, 'src'));
  assert.match(ctx, /Prochaine action : develop ticket-b/);
  assert.match(ctx, /Sprint s1 : `develop` en cours — ticket 2\/3/);
  assert.match(ctx, /Prochaine étape du plan : `develop` \(Sprint s1\)/);
});

test('points to the status skill when there is no plan yet', () => {
  assert.match(resumeContext(kb()), /No progress plan yet/);
});

test('says nothing outside a Hosa project', () => {
  assert.equal(resumeContext(fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-none-'))), '');
});

test('ignores the stale KB copy inside a sprint worktree', () => {
  const root = kb(['---', 'type: Plan d\'avancement', '---', '## Point de reprise', '- Prochaine action : vraie KB', ''].join('\n'));
  const wt = path.join(root, '.worktrees', 'sprint', 's1');
  fs.mkdirSync(path.join(wt, '.hosa', 'kb', 'project'), { recursive: true });
  fs.writeFileSync(path.join(wt, '.hosa', 'kb', 'project', 'avancement.md'), '---\ntype: x\n---\n## Point de reprise\n- Prochaine action : copie périmée\n');
  const ctx = resumeContext(path.join(wt, 'src'));
  assert.match(ctx, /vraie KB/);
  assert.doesNotMatch(ctx, /copie périmée/);
});

test('asks to migrate a KB still tracked in the code branches', () => {
  const root = kb();
  const { spawnSync } = require('child_process');
  const g = (...a) => spawnSync('git', ['-C', root, ...a], { encoding: 'utf8' });
  g('init', '-q'); fs.writeFileSync(path.join(root, '.hosa', 'kb', 'x.md'), '---\ntype: x\n---\n'); g('add', '.hosa/kb/x.md');
  assert.match(resumeContext(root), /still tracked in the code branches/);
});
