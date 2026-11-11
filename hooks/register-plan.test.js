const test = require('node:test');
const assert = require('node:assert');

test('readPlan: an agent task row is never an upstream stage', async () => {
  const { readPlan } = await import('./register.mjs');
  const plan = [
    '## Tâches', '| Tâche | Étape | Agent | Objet | Statut | Mis à jour | Sortie | Détail |', '|---|---|---|---|---|---|---|---|',
    '| lot-1 | `qa` (s1) | hosa-tester | t1 | à faire | d | | |',
    '## Structuration', '| Étape | Statut | Mis à jour | Détail |', '|---|---|---|---|', '| `backlog` | fait | d | |',
    '## Sprint s1', '| Étape | Statut | Mis à jour | Détail |', '|---|---|---|---|', '| `qa` | en cours | d | |',
  ].join('\n');
  assert.deepStrictEqual(readPlan(plan), { phase: 'sprints', closed: 1 });
});

test('readView: the pane gets the resume point, loops, tasks, sections and the first open stage', async () => {
  const { readView } = await import('./register.mjs');
  const view = readView([
    '---', 'type: Plan d\'avancement', '---',
    '## Point de reprise', '- En cours : `qa` (s2) — lot 2', '',
    '## Boucles', '| Boucle | Tours | État | Mis à jour | Cause | Détail |', '|---|---|---|---|---|---|',
    '| `qa` → `develop` (s2) | 1/2 | ouverte | d | test rouge | t3 |',
    '## Tâches', '| Tâche | Étape | Agent | Objet | Statut | Mis à jour | Sortie | Détail |', '|---|---|---|---|---|---|---|---|',
    '| lot-1 | `qa` (s2) | hosa-tester | t1 | fait | d | a.md | |',
    '| lot-2 | `qa` (s2) | hosa-tester | t3 | bloqué | d | | Q1 : a) ou b) ? |',
    '## Structuration', '| Étape | Statut | Mis à jour | Détail |', '|---|---|---|---|', '| `backlog` | fait | d | |',
    '## Sprint s1', '| Étape | Statut | Mis à jour | Détail |', '|---|---|---|---|', '| `qa` | fait | d | |',
    '## Sprint s2', '| Étape | Statut | Mis à jour | Détail |', '|---|---|---|---|',
    '| `develop` | fait | d | |', '| `qa` | en cours | d | lot 2 |',
  ].join('\n'));
  assert.deepStrictEqual(view.resume, ['En cours : qa (s2) — lot 2']);
  assert.deepStrictEqual(view.loops, [{ name: 'qa → develop (s2)', tours: '1/2', etat: 'ouverte', cause: 'test rouge', detail: 't3' }]);
  assert.deepStrictEqual(view.tasks[1], { id: 'lot-2', where: 'qa (s2)', agent: 'hosa-tester', objet: 't3', statut: 'bloqué', detail: 'Q1 : a) ou b) ?' });
  assert.deepStrictEqual(view.sections.map((s) => [s.title, s.done, s.rows.length]), [['Structuration', 1, 1], ['Sprint s1', 1, 1], ['Sprint s2', 1, 2]]);
  assert.deepStrictEqual(view.current, { stage: 'qa', statut: 'en cours', detail: 'lot 2', title: 'Sprint s2' });
});
