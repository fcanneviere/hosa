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
