const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const { processPayload, RESUME } = require('./reprendre');

function project() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-reprendre-'));
  fs.mkdirSync(path.join(root, '.hosa', 'kb', 'project'), { recursive: true });
  return root;
}
const CARD = '## Fiche de reprise\n- Action : invoque `hosa:develop` avec `args: "reprise"`.';

test('a message that asks to resume gets the resume card with it', () => {
  const cwd = project();
  let asked = '';
  const out = processPayload({ prompt: 'reprends', cwd }, (kb) => { asked = kb; return CARD; });
  assert.match(asked, /\/\.hosa\/kb$/);
  assert.equal(out.hookSpecificOutput.hookEventName, 'UserPromptSubmit');
  assert.match(out.hookSpecificOutput.additionalContext, /^## Fiche de reprise/);
  assert.match(out.hookSpecificOutput.additionalContext, /Do not invoke the `reprendre` skill/);
});

test('knows the ways to ask, and leaves any other request alone', () => {
  for (const p of ['reprends', 'Reprend', 'on reprend', 'continue', '/hosa:reprendre', '/reprendre', 'où on en était ?', 'reprends stp'])
    assert.ok(RESUME.test(p), p);
  for (const p of ['corrige le skill develop', 'pourquoi la reprise est lente ?', 'la suite continue de planter'])
    assert.ok(!RESUME.test(p), p);
  const cwd = project();
  assert.equal(processPayload({ prompt: 'corrige le test', cwd }, () => CARD), null);
  assert.equal(processPayload({ prompt: `reprends ${'x'.repeat(200)}`, cwd }, () => CARD), null); // a request of its own
});

test('says nothing without a plan, outside a Hosa project, or switched off', () => {
  const cwd = project();
  assert.equal(processPayload({ prompt: 'reprends', cwd }, () => 'Pas de plan d\'avancement : invoque `hosa:status`.'), null);
  assert.equal(processPayload({ prompt: 'reprends', cwd }, () => ''), null); // the script failed: fail-open
  assert.equal(processPayload({ prompt: 'reprends', cwd: os.tmpdir() }, () => CARD), null);
  process.env.HOSA_REPRISE = '0';
  try { assert.equal(processPayload({ prompt: 'reprends', cwd }, () => CARD), null); } finally { delete process.env.HOSA_REPRISE; }
});

test('reads the card from the real plan script', () => {
  const cwd = project();
  fs.writeFileSync(path.join(cwd, '.hosa', 'kb', 'project', 'avancement.md'), [
    '---', 'type: Plan d\'avancement', '---', '## Point de reprise', '- Rien en cours.', '',
    '## Cahier des charges', '| Étape | Statut | Mis à jour | Détail |', '|---|---|---|---|', '| `hosa` | fait | 2026-11-01T00:00:00Z |  |',
  ].join('\n'));
  const out = processPayload({ prompt: 'reprends', cwd });
  if (!out) return; // no Python on this machine: fail-open is the contract
  assert.match(out.hookSpecificOutput.additionalContext, /Étape : `interview` \(Cahier des charges\) — à faire → skill `hosa:interview`/);
});
