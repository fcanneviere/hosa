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
