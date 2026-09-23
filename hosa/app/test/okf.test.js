const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { listConcepts, getConcept, listTicketsByState } = require('../src/okf');

function makeFixtureKb() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'okf-test-'));
  fs.mkdirSync(path.join(root, 'cdc'));
  fs.mkdirSync(path.join(root, 'tickets'));
  fs.mkdirSync(path.join(root, 'rules', 'design'), { recursive: true });

  fs.writeFileSync(path.join(root, 'index.md'), '# Bundles\n');
  fs.writeFileSync(path.join(root, 'cdc', 'log.md'), '# Log\n');
  fs.writeFileSync(
    path.join(root, 'cdc', 'exigence-1.md'),
    '---\ntype: Exigence\ntitle: Exemple\n---\nCorps.\n'
  );
  fs.writeFileSync(
    path.join(root, 'rules', 'design', 'regle-1.md'),
    '---\ntype: Design Rule\ntitle: Nested\n---\nCorps.\n'
  );
  fs.writeFileSync(
    path.join(root, 'tickets', 'ticket-todo.md'),
    '---\ntype: Ticket\ntitle: A faire\nstate: todo\n---\nCorps.\n'
  );
  fs.writeFileSync(
    path.join(root, 'tickets', 'ticket-no-state.md'),
    '---\ntype: Ticket\ntitle: Sans etat\n---\nCorps.\n'
  );
  fs.writeFileSync(
    path.join(root, 'tickets', 'ticket-bad-frontmatter.md'),
    '---\ntype: Ticket\ntitle: [unterminated\n---\nCorps.\n'
  );
  fs.writeFileSync(path.join(root, 'tickets', 'no-type.md'), '---\ntitle: Sans type\n---\nCorps.\n');
  return root;
}

test('listConcepts excludes reserved filenames (index.md, log.md)', () => {
  const root = makeFixtureKb();
  const all = listConcepts(root);
  const paths = all.map((c) => c.path);
  assert.ok(!paths.includes('index.md'));
  assert.ok(!paths.includes('cdc/log.md'));
});

test('listConcepts recurses into nested subdirectories', () => {
  const root = makeFixtureKb();
  const all = listConcepts(root);
  assert.ok(all.some((c) => c.path === 'rules/design/regle-1.md'));
});

test('listConcepts filters by type', () => {
  const root = makeFixtureKb();
  const exigences = listConcepts(root, 'Exigence');
  assert.equal(exigences.length, 1);
  assert.equal(exigences[0].frontmatter.title, 'Exemple');
});

test('listConcepts skips files with malformed frontmatter or missing type', () => {
  const root = makeFixtureKb();
  const all = listConcepts(root);
  const paths = all.map((c) => c.path);
  assert.ok(!paths.includes('tickets/ticket-bad-frontmatter.md'));
  assert.ok(!paths.includes('tickets/no-type.md'));
});

test('listTicketsByState groups tickets, defaulting missing state to todo', () => {
  const root = makeFixtureKb();
  const grouped = listTicketsByState(root);
  const todoTitles = grouped.todo.map((t) => t.frontmatter.title);
  assert.ok(todoTitles.includes('A faire'));
  assert.ok(todoTitles.includes('Sans etat'));
  assert.equal(grouped.doing.length, 0);
});

test('getConcept refuses to read outside the kb root', () => {
  const root = makeFixtureKb();
  const result = getConcept(root, '../../../etc/passwd');
  assert.equal(result, null);
});

test('getConcept returns frontmatter and body for a valid path', () => {
  const root = makeFixtureKb();
  const result = getConcept(root, 'cdc/exigence-1.md');
  assert.equal(result.frontmatter.type, 'Exigence');
  assert.match(result.body, /Corps\./);
});
