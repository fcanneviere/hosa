const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { createApp, startServer } = require('../server');

function makeFixtureKb() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'okf-route-test-'));
  fs.mkdirSync(path.join(root, 'tickets'));
  fs.writeFileSync(
    path.join(root, 'tickets', 'ticket-1.md'),
    '---\ntype: Ticket\ntitle: Premier ticket\nstate: doing\n---\nCorps du ticket.\n'
  );
  return root;
}

function startTestServer(kbRoot) {
  return new Promise((resolve) => {
    const app = createApp(kbRoot);
    const server = app.listen(0, () => resolve(server));
  });
}

test('GET /api/tickets groups tickets by state', async () => {
  const kbRoot = makeFixtureKb();
  const server = await startTestServer(kbRoot);
  const { port } = server.address();
  const res = await fetch(`http://localhost:${port}/api/tickets`);
  const body = await res.json();
  assert.equal(res.status, 200);
  assert.equal(body.doing.length, 1);
  assert.equal(body.doing[0].frontmatter.title, 'Premier ticket');
  server.close();
});

test('GET /api/concepts/*path returns a concept for a valid path', async () => {
  const kbRoot = makeFixtureKb();
  const server = await startTestServer(kbRoot);
  const { port } = server.address();
  const res = await fetch(`http://localhost:${port}/api/concepts/tickets/ticket-1.md`);
  const body = await res.json();
  assert.equal(res.status, 200);
  assert.equal(body.frontmatter.type, 'Ticket');
  server.close();
});

test('GET /api/concepts/*path includes bodyHtml and trustTier', async () => {
  const kbRoot = makeFixtureKb();
  const server = await startTestServer(kbRoot);
  const { port } = server.address();
  const res = await fetch(`http://localhost:${port}/api/concepts/tickets/ticket-1.md`);
  const body = await res.json();
  assert.match(body.bodyHtml, /<p>Corps du ticket\.<\/p>/);
  assert.equal(body.trustTier, 'unverified');
  server.close();
});

test('GET /api/concepts/*path returns 404 for a nonexistent concept', async () => {
  const kbRoot = makeFixtureKb();
  const server = await startTestServer(kbRoot);
  const { port } = server.address();
  const res = await fetch(`http://localhost:${port}/api/concepts/tickets/does-not-exist.md`);
  assert.equal(res.status, 404);
  server.close();
});

test('startServer binds to localhost only, not all network interfaces', async () => {
  const kbRoot = makeFixtureKb();
  const server = await new Promise((resolve) => {
    const s = startServer(kbRoot, 0);
    s.on('listening', () => resolve(s));
  });
  assert.equal(server.address().address, '127.0.0.1');
  server.close();
});
