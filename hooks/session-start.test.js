const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');

const { compose, rules, LIMIT } = require('./session-start');

const bytes = (s) => Buffer.byteLength(s, 'utf8');

test('the first hook stays under 10 KB, its essentials first, the cleared session cut before the plan', () => {
  const head = '## Hosa\n\n- KB : `c:/p/.hosa/kb`. « reprends » → skill `reprendre`\n- `<hosa>` = `x`';
  const plan = `## Plan d'avancement — reprise\n\n${Array.from({ length: 60 }, (_, i) => `- ligne ${i} ${'é'.repeat(90)}`).join('\n')}`;
  const previous = `## Session précédente\n\n${Array.from({ length: 80 }, (_, i) => `- demande ${i} ${'d'.repeat(90)}`).join('\n')}`;
  const out = compose({ head, plan, previous, tail: '## Project graph\n\nQuery it.' });
  assert.ok(bytes(out) <= LIMIT, `${bytes(out)} bytes`);
  assert.ok(out.startsWith('## Hosa'));
  assert.ok(bytes(out.slice(0, out.indexOf('## Plan'))) < 2000, 'KB and <hosa> sit in the first 2 KB');
  assert.match(out, /plan coupé : `<hosa> avancement "<kb>" reprendre` le donne entier/);
  assert.match(out, /## Project graph/);
  const small = compose({ head, plan: '## Plan\n\n- Rien en cours.', previous: '## Session précédente\n\n- court' });
  assert.match(small, /- court/);                                      // nothing cut when it fits
  assert.doesNotMatch(small, /coupé/);
});

test('the second hook gives using-hosa whole, under 10 KB, without its frontmatter', () => {
  const withKb = rules(true);
  assert.ok(bytes(withKb) <= LIMIT, `using-hosa is ${bytes(withKb)} bytes: move details to regles.md`);
  assert.ok(withKb.startsWith('# Hosa'));
  assert.match(withKb, /## Hosa project rules/);
  assert.doesNotMatch(rules(false), /## Hosa project rules\n/);         // no KB: the project rules serve nothing
  assert.ok(fs.existsSync(path.join(__dirname, '..', 'skills', 'using-hosa', 'regles.md')));
});

test('hooks.json runs both session-start hooks, the essentials first', () => {
  const hooks = JSON.parse(fs.readFileSync(path.join(__dirname, 'hooks.json'), 'utf8')).hooks.SessionStart[0].hooks;
  assert.deepEqual(hooks.map((h) => /--rules/.test(h.command)), [false, true]);
});
