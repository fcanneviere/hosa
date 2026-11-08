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

test('an open loop survives a later resume point, a closed one is not shown', () => {
  const root = kb([
    '---', 'type: Plan d\'avancement', '---',
    '## Point de reprise', '- En cours : `redaction` — A2', '',
    '## Boucles', '| Boucle | Tours | État | Mis à jour | Cause | Détail |', '|---|---|---|---|---|---|',
    '| `relecture` → `redaction` | 2/2 | ouverte | 2026-11-05 |  | A2 : cas d\'erreur manquant |',
    '| `qa` → `develop` (s1, t1) | 1/2 | fermée | 2026-11-04 | test_a | KO |', '',
    '## Cahier des charges', '| Étape | Statut | Mis à jour | Détail |', '|---|---|---|---|',
    '| `redaction` | en cours | 2026-11-05 | A2 |', '| `relecture` | à faire |  |  |',
  ].join('\n'));
  const ctx = resumeContext(root);
  assert.match(ctx, /Boucle ouverte : `relecture` → `redaction` — tour 2\/2 — A2 : cas d'erreur manquant/);
  assert.doesNotMatch(ctx, /`qa` → `develop`/);
  assert.match(ctx, /Prochaine étape du plan : `redaction` \(Cahier des charges\)/);
  assert.match(ctx, /`reprendre` gives the resume card/);
});

test('a detail the resume point and the stage row share is said once, on the row', () => {
  const detail = `Découpe des 20 tickets ${'x'.repeat(500)}`;
  const root = kb([
    '---', 'type: Plan d\'avancement', '---',
    '## Point de reprise', `- En cours : \`backlog\` — ${detail}`, '',
    '## Structuration', '| Étape | Statut | Mis à jour | Détail |', '|---|---|---|---|', `| \`backlog\` | en cours | 2026-11-08 | ${detail} |`,
  ].join('\n'));
  const ctx = resumeContext(root);
  assert.equal(ctx.split('Découpe des 20 tickets').length - 1, 1);
  assert.match(ctx, /Structuration : `backlog` en cours — Découpe/);
  assert.match(ctx, /… \(`reprendre` : le détail entier\)/);           // a line is bounded at 400 characters
});

test('resumes at the next agent task of each stage and shows the blocked ones', () => {
  const root = kb([
    '---', 'type: Plan d\'avancement', '---',
    '## Point de reprise', '- En cours : `qa` (sprint s1) — t1 testé', '',
    '## Tâches', '| Tâche | Étape | Agent | Objet | Statut | Mis à jour | Sortie | Détail |', '|---|---|---|---|---|---|---|---|',
    '| t1 | `qa` (s1) | hosa-tester | t1 | fait | 2026-11-06 | kb/test/t1-technique.md |  |',
    '| t2 | `qa` (s1) | hosa-tester | t2 | à faire | 2026-11-06 |  |  |',
    '| t3 | `qa` (s1) | hosa-tester | t3 | à faire | 2026-11-06 |  |  |',
    '| r1 | `qa` (s1) | hosa-key-user | t1, parent | bloqué | 2026-11-06 |  | Q1. Compte de test ? |', '',
    '## Sprint s1', '| Étape | Statut | Mis à jour | Détail |', '|---|---|---|---|', '| `qa` | en cours | 2026-11-06 | t1 testé |',
  ].join('\n'));
  const ctx = resumeContext(root);
  assert.match(ctx, /Prochaine tâche : `t2` hosa-tester → t2 \(`qa` \(s1\)\)/);
  assert.doesNotMatch(ctx, /`t3`|`t1` hosa-tester/);
  assert.match(ctx, /Tâche bloquée : `r1` hosa-key-user → t1, parent \(`qa` \(s1\)\) — Q1\. Compte de test \?/);
  assert.match(ctx, /Prochaine étape du plan : `qa` \(Sprint s1\)/);
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

test('asks to move agent memories left under the old project scope', () => {
  const root = kb();
  fs.mkdirSync(path.join(root, '.claude', 'agent-memory', 'hosa-tester'), { recursive: true });
  assert.match(resumeContext(root), /kb_branch\.py memoire/);
});
