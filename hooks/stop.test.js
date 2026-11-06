const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

process.env.HOSA_STATE_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-stop-test-'));
const { processPayload } = require('./stop');

const project = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-stop-proj-'));
const plan = path.join(project, '.hosa', 'kb', 'project', 'avancement.md');
fs.mkdirSync(path.dirname(plan), { recursive: true });
const setPlan = (rows) => fs.writeFileSync(plan, '## Point de reprise\n- `develop` en cours\n\n## Sprint s1\n' +
  '| Étape | Statut | Mis à jour | Détail |\n|---|---|---|---|\n' + rows.map(([s, st]) => `| \`${s}\` | ${st} |  |  |`).join('\n') + '\n');
const stop = (session, extra = {}) => processPayload({ hook_event_name: 'Stop', session_id: session, cwd: project, ...extra });

test('a turn ending on a stage still in progress warns the user, without blocking', () => {
  setPlan([['sprint', 'fait'], ['develop', 'en cours'], ['qa', 'à faire']]);
  const out = stop('a1');
  assert.match(out.systemMessage, /`develop` \(Sprint s1\)/);
  assert.equal(out.decision, undefined);
});

test('warns once per stage and session', () => {
  setPlan([['develop', 'en cours']]);
  assert.ok(stop('b1'));
  assert.equal(stop('b1'), null);
  setPlan([['develop', 'fait'], ['audit', 'en cours']]);
  assert.match(stop('b1').systemMessage, /`audit`/);
  assert.ok(stop('b2'));                                 // a new session is warned again
});

test('says nothing when no stage is in progress, outside a KB, on a hook retry or when switched off', () => {
  setPlan([['develop', 'bloqué'], ['qa', 'à faire']]);
  assert.equal(stop('c1'), null);
  assert.equal(processPayload({ session_id: 'c2', cwd: fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-stop-none-')) }), null);
  setPlan([['develop', 'en cours']]);
  assert.equal(stop('c3', { stop_hook_active: true }), null);
  process.env.HOSA_STOP = '0';
  try { assert.equal(stop('c4'), null); } finally { delete process.env.HOSA_STOP; }
  assert.equal(processPayload(null), null);
});
