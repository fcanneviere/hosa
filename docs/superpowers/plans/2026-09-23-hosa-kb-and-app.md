# Hosa KB (OKF) + Pilotage App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the OKF-based knowledge base under `hosa/kb/` and build a read-only Node/Express app under `hosa/app/` that visualizes it (ticket kanban + KB explorer).

**Architecture:** A dependency-free-as-possible Node/Express backend walks the `kb/` directory tree on each request, parses frontmatter with `gray-matter`, and serves JSON from two endpoints. A vanilla HTML/CSS/JS frontend (no build step, no framework) renders a ticket kanban board and a KB browser from that JSON. No database — the markdown files are the only store. This iteration is read-only by design (see spec for the write-mode upgrade path).

**Tech Stack:** Node.js (`node:test` for tests, `node --test`), Express 4, `gray-matter` for YAML frontmatter parsing, vanilla JS/HTML/CSS frontend.

**Spec:** `docs/simflow/specs/2026-09-23-hosa-pilotage-design.md` — this plan implements sections 1 (KB structure) and 3 (app). Section 2 (the `hosa` skill) is out of scope for this plan (deferred phase).

## Global Constraints

- No database — `hosa/kb/` markdown files are the sole source of truth.
- App is read-only in this iteration — no endpoint may write to `kb/`.
- Backend and storage layer must stay decoupled from the frontend so write endpoints can be added later without restructuring (per spec §3, "Chemin d'évolution vers l'écriture").
- No frontend framework/build step — plain HTML/CSS/JS served as static files.
- KB root path must be configurable via `HOSA_KB_ROOT` env var (defaults to `../kb` relative to the app), so tests never touch the real `hosa/kb/` directory.
- Reserved OKF filenames (`index.md`, `log.md`) must never be treated as concepts (spec §1, OKF §3.1).
- A concept without a `type` field is not OKF-conformant and must be excluded from listings (OKF §11).

## Review Focus

- A concept file with malformed YAML frontmatter must not crash the whole listing — it should be skipped. → Task 3 test.
- A request for `/api/concepts/*path` must not be able to escape `kb/` via `../` segments (path traversal). → Task 3 test (`getConcept` unit test, deterministic — HTTP-level traversal tests are unreliable because URL parsers normalize `..` before the server sees them).
- A concept missing the required `type` field must be excluded from results, per OKF conformance rules. → Task 3 test.
- Nested subdirectories (e.g. `kb/rules/design/`, `kb/rules/security/`) must be walked recursively, not just the top level. → Task 3 test.
- A `Ticket` concept missing the `state` field must default into a sensible column (`todo`) instead of crashing the grouping logic or vanishing from the board. → Task 3 test.

---

### Task 1: KB scaffolding

**Files:**
- Create: `hosa/kb/tickets/.gitkeep`
- Create: `hosa/kb/index.md`
- Create: `hosa/kb/cdc/exemple-exigence.md`
- Create: `hosa/kb/personnas/exemple-persona.md`
- Create: `hosa/kb/tickets/exemple-ticket.md`

**Interfaces:**
- Produces: a non-empty `hosa/kb/` tree that Task 3's parser and Task 5's manual browser check can render against.

This task creates only static content — no logic, no test needed (ponytail: trivial file creation).

- [ ] **Step 1: Create the `tickets/` bundle folder**

```bash
mkdir -p hosa/kb/tickets
touch hosa/kb/tickets/.gitkeep
```

- [ ] **Step 2: Create the KB root index**

Write `hosa/kb/index.md`:

```markdown
---
okf_version: "0.2"
---

# Hosa — base de connaissance

* [cdc](cdc/) - Exigences extraites du cahier des charges
* [personnas](personnas/) - Personas des parties prenantes (product owners, utilisateurs...)
* [rules/design](rules/design/) - Règles de conception
* [rules/security](rules/security/) - Règles de sécurité
* [stack](stack/) - Décisions techniques
* [infra](infra/) - Notes d'infrastructure
* [test](test/) - Plans de test
* [tickets](tickets/) - Tickets de suivi
```

- [ ] **Step 3: Create one example concept per bundle used by the app's manual check**

Write `hosa/kb/cdc/exemple-exigence.md`:

```markdown
---
type: Exigence
title: Exemple d'exigence
description: Ceci est un exemple pour vérifier que l'app affiche bien la KB.
tags: [exemple]
status: draft
generated: { by: human:fcanneviere, at: 2026-09-23T00:00:00Z }
---

Ceci est un exemple d'exigence. Remplace-le par de vraies exigences issues du
cahier des charges.
```

Write `hosa/kb/personnas/exemple-persona.md`:

```markdown
---
type: Persona
title: Exemple de persona
description: Persona d'exemple pour vérifier l'affichage dans l'app.
tags: [exemple]
status: draft
generated: { by: human:fcanneviere, at: 2026-09-23T00:00:00Z }
---

Ceci est un persona d'exemple.
```

Write `hosa/kb/tickets/exemple-ticket.md`:

```markdown
---
type: Ticket
title: Exemple de ticket
description: Ticket d'exemple pour vérifier le kanban de l'app.
tags: [exemple]
state: todo
generated: { by: human:fcanneviere, at: 2026-09-23T00:00:00Z }
---

Ceci est un ticket d'exemple. Supprime-le une fois que de vrais tickets
existent.
```

- [ ] **Step 4: Commit**

```bash
git add hosa/kb/
git commit -m "feat: scaffold OKF knowledge base structure with example concepts"
```

---

### Task 2: Node project setup for the app

**Files:**
- Create: `hosa/app/package.json`
- Create: `hosa/app/.gitignore`

**Interfaces:**
- Produces: an `npm test` script (`node --test test/`) and an `npm start` script, and the `express`/`gray-matter` dependencies later tasks import.

- [ ] **Step 1: Create `package.json`**

Write `hosa/app/package.json`:

```json
{
  "name": "hosa-app",
  "version": "0.1.0",
  "private": true,
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "test": "node --test test/"
  },
  "dependencies": {
    "express": "^4.19.2",
    "gray-matter": "^4.0.3"
  }
}
```

- [ ] **Step 2: Create `.gitignore`**

Write `hosa/app/.gitignore`:

```
node_modules/
```

- [ ] **Step 3: Install dependencies**

Run: `cd hosa/app && npm install`
Expected: `node_modules/` created, `package-lock.json` generated, no errors.

- [ ] **Step 4: Commit**

```bash
git add hosa/app/package.json hosa/app/package-lock.json hosa/app/.gitignore
git commit -m "chore: scaffold hosa app Node project"
```

---

### Task 3: OKF parser module

**Files:**
- Create: `hosa/app/src/okf.js`
- Test: `hosa/app/test/okf.test.js`

**Interfaces:**
- Consumes: `gray-matter` (npm package from Task 2).
- Produces (used by Task 4):
  - `listConcepts(kbRoot, type)` → `Array<{ path: string, frontmatter: object, body: string }>`. `type` is optional; omit it to get every concept.
  - `getConcept(kbRoot, relPath)` → `{ path, frontmatter, body } | null`. Returns `null` for a missing file or a path that resolves outside `kbRoot`.
  - `listTicketsByState(kbRoot)` → `{ todo: [...], doing: [...], done: [...], blocked: [...] }`, each array holding the same shape as `listConcepts`.

- [ ] **Step 1: Write failing tests**

Write `hosa/app/test/okf.test.js`:

```js
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
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `cd hosa/app && npm test`
Expected: FAIL — `Cannot find module '../src/okf'`

- [ ] **Step 3: Write the implementation**

Write `hosa/app/src/okf.js`:

```js
const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');

const RESERVED_FILENAMES = new Set(['index.md', 'log.md']);
const TICKET_STATES = new Set(['todo', 'doing', 'done', 'blocked']);

function walkConcepts(kbRoot) {
  const results = [];

  function walk(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
        continue;
      }
      if (!entry.isFile() || !entry.name.endsWith('.md') || RESERVED_FILENAMES.has(entry.name)) {
        continue;
      }
      const raw = fs.readFileSync(fullPath, 'utf8');
      let parsed;
      try {
        parsed = matter(raw);
      } catch (err) {
        continue; // malformed YAML frontmatter — skip, don't crash the listing
      }
      if (!parsed.data || !parsed.data.type) {
        continue; // OKF §11: `type` is the only required field
      }
      const relPath = path.relative(kbRoot, fullPath).split(path.sep).join('/');
      results.push({ path: relPath, frontmatter: parsed.data, body: parsed.content });
    }
  }

  walk(kbRoot);
  return results;
}

function listConcepts(kbRoot, type) {
  const all = walkConcepts(kbRoot);
  if (!type) return all;
  return all.filter((concept) => concept.frontmatter.type === type);
}

function getConcept(kbRoot, relPath) {
  const resolvedRoot = path.resolve(kbRoot);
  const resolvedTarget = path.resolve(kbRoot, relPath);
  if (resolvedTarget !== resolvedRoot && !resolvedTarget.startsWith(resolvedRoot + path.sep)) {
    return null; // path traversal outside kb root
  }
  if (!fs.existsSync(resolvedTarget) || !fs.statSync(resolvedTarget).isFile()) {
    return null;
  }
  const raw = fs.readFileSync(resolvedTarget, 'utf8');
  const parsed = matter(raw);
  const normalizedPath = path.relative(resolvedRoot, resolvedTarget).split(path.sep).join('/');
  return { path: normalizedPath, frontmatter: parsed.data, body: parsed.content };
}

function listTicketsByState(kbRoot) {
  const tickets = listConcepts(kbRoot, 'Ticket');
  const grouped = { todo: [], doing: [], done: [], blocked: [] };
  for (const ticket of tickets) {
    const state = TICKET_STATES.has(ticket.frontmatter.state) ? ticket.frontmatter.state : 'todo';
    grouped[state].push(ticket);
  }
  return grouped;
}

module.exports = { walkConcepts, listConcepts, getConcept, listTicketsByState };
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `cd hosa/app && npm test`
Expected: PASS — all 7 tests green.

- [ ] **Step 5: Commit**

```bash
git add hosa/app/src/okf.js hosa/app/test/okf.test.js
git commit -m "feat: add OKF concept parser with type/path-safety guards"
```

---

### Task 4: Express API routes

**Files:**
- Create: `hosa/app/src/routes.js`
- Create: `hosa/app/server.js`
- Test: `hosa/app/test/routes.test.js`

**Interfaces:**
- Consumes: `listConcepts`, `getConcept`, `listTicketsByState` from `hosa/app/src/okf.js` (Task 3).
- Produces (used by Task 5's frontend):
  - `GET /api/concepts?type=<Type>` → JSON array of concepts (all concepts if `type` omitted).
  - `GET /api/concepts/*path` → JSON concept object, or HTTP 404 `{ error: 'not found' }`.
  - `GET /api/tickets` → JSON `{ todo, doing, done, blocked }`.
  - `createApp(kbRoot)` exported from `server.js`, used directly by tests (no network needed beyond an ephemeral port).

- [ ] **Step 1: Write failing tests**

Write `hosa/app/test/routes.test.js`:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { createApp } = require('../server');

function makeFixtureKb() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'okf-route-test-'));
  fs.mkdirSync(path.join(root, 'tickets'));
  fs.writeFileSync(
    path.join(root, 'tickets', 'ticket-1.md'),
    '---\ntype: Ticket\ntitle: Premier ticket\nstate: doing\n---\nCorps du ticket.\n'
  );
  return root;
}

function startServer(kbRoot) {
  return new Promise((resolve) => {
    const app = createApp(kbRoot);
    const server = app.listen(0, () => resolve(server));
  });
}

test('GET /api/tickets groups tickets by state', async () => {
  const kbRoot = makeFixtureKb();
  const server = await startServer(kbRoot);
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
  const server = await startServer(kbRoot);
  const { port } = server.address();
  const res = await fetch(`http://localhost:${port}/api/concepts/tickets/ticket-1.md`);
  const body = await res.json();
  assert.equal(res.status, 200);
  assert.equal(body.frontmatter.type, 'Ticket');
  server.close();
});

test('GET /api/concepts/*path returns 404 for a nonexistent concept', async () => {
  const kbRoot = makeFixtureKb();
  const server = await startServer(kbRoot);
  const { port } = server.address();
  const res = await fetch(`http://localhost:${port}/api/concepts/tickets/does-not-exist.md`);
  assert.equal(res.status, 404);
  server.close();
});
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `cd hosa/app && npm test`
Expected: FAIL — `Cannot find module '../server'`

- [ ] **Step 3: Write the implementation**

Write `hosa/app/src/routes.js`:

```js
const express = require('express');
const { listConcepts, getConcept, listTicketsByState } = require('./okf');

function createRouter(kbRoot) {
  const router = express.Router();

  router.get('/concepts', (req, res) => {
    res.json(listConcepts(kbRoot, req.query.type));
  });

  router.get('/tickets', (req, res) => {
    res.json(listTicketsByState(kbRoot));
  });

  router.get('/concepts/*', (req, res) => {
    const relPath = req.params[0];
    const concept = getConcept(kbRoot, relPath);
    if (!concept) {
      res.status(404).json({ error: 'not found' });
      return;
    }
    res.json(concept);
  });

  return router;
}

module.exports = { createRouter };
```

Write `hosa/app/server.js`:

```js
const path = require('path');
const express = require('express');
const { createRouter } = require('./src/routes');

function createApp(kbRoot) {
  const app = express();
  app.use('/api', createRouter(kbRoot));
  app.use(express.static(path.join(__dirname, 'public')));
  return app;
}

if (require.main === module) {
  const kbRoot = process.env.HOSA_KB_ROOT || path.join(__dirname, '..', 'kb');
  const port = process.env.PORT || 3000;
  createApp(kbRoot).listen(port, () => {
    console.log(`hosa app listening on http://localhost:${port}`);
  });
}

module.exports = { createApp };
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `cd hosa/app && npm test`
Expected: PASS — all tests green (7 from Task 3 + 3 new ones).

- [ ] **Step 5: Commit**

```bash
git add hosa/app/src/routes.js hosa/app/server.js hosa/app/test/routes.test.js
git commit -m "feat: add read-only Express API for concepts and tickets"
```

---

### Task 5: Static frontend (kanban + KB explorer)

**Files:**
- Create: `hosa/app/public/index.html`
- Create: `hosa/app/public/style.css`
- Create: `hosa/app/public/app.js`

**Interfaces:**
- Consumes: `GET /api/tickets`, `GET /api/concepts?type=` (Task 4).
- Produces: nothing consumed by later tasks — this is the last task in the plan.

This task is UI rendering with no pure business logic worth unit-testing in isolation (ponytail: trivial DOM wiring). Verification is manual, in a browser, per the UI-change checklist.

- [ ] **Step 1: Write the HTML shell**

Write `hosa/app/public/index.html`:

```html
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <title>Hosa — pilotage de projet</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <header>
    <h1>Hosa</h1>
    <nav>
      <button data-view="tickets" class="active">Tickets</button>
      <button data-view="kb">Base de connaissance</button>
    </nav>
    <button id="refresh">Rafraîchir</button>
  </header>

  <main>
    <section id="view-tickets">
      <div class="board">
        <div class="column" data-state="todo"><h2>À faire</h2><div class="cards"></div></div>
        <div class="column" data-state="doing"><h2>En cours</h2><div class="cards"></div></div>
        <div class="column" data-state="done"><h2>Fait</h2><div class="cards"></div></div>
        <div class="column" data-state="blocked"><h2>Bloqué</h2><div class="cards"></div></div>
      </div>
    </section>

    <section id="view-kb" hidden>
      <label for="type-filter">Type :</label>
      <select id="type-filter">
        <option value="">Tous</option>
      </select>
      <ul id="concept-list"></ul>
    </section>
  </main>

  <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write the stylesheet**

Write `hosa/app/public/style.css`:

```css
body { font-family: system-ui, sans-serif; margin: 0; color: #1a1a1a; }
header { display: flex; align-items: center; gap: 1rem; padding: 1rem; border-bottom: 1px solid #ddd; }
header h1 { margin: 0; font-size: 1.2rem; }
nav button.active { font-weight: bold; }
main { padding: 1rem; }
.board { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.column { background: #f5f5f5; border-radius: 8px; padding: 0.5rem; min-height: 200px; }
.column h2 { font-size: 0.9rem; text-transform: uppercase; color: #666; }
.card { background: white; border: 1px solid #ddd; border-radius: 6px; padding: 0.5rem; margin-bottom: 0.5rem; }
#concept-list { list-style: none; padding: 0; }
#concept-list li { padding: 0.5rem; border-bottom: 1px solid #eee; }
```

- [ ] **Step 3: Write the client script**

Write `hosa/app/public/app.js`:

```js
const state = { view: 'tickets' };

async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request failed: ${url}`);
  return res.json();
}

function renderTickets(grouped) {
  for (const columnState of ['todo', 'doing', 'done', 'blocked']) {
    const column = document.querySelector(`.column[data-state="${columnState}"] .cards`);
    column.innerHTML = '';
    for (const ticket of grouped[columnState] || []) {
      const card = document.createElement('div');
      card.className = 'card';
      card.textContent = ticket.frontmatter.title || ticket.path;
      column.appendChild(card);
    }
  }
}

function renderConceptList(concepts) {
  const list = document.getElementById('concept-list');
  list.innerHTML = '';
  for (const concept of concepts) {
    const item = document.createElement('li');
    const title = concept.frontmatter.title || concept.path;
    const description = concept.frontmatter.description || '';
    item.textContent = `[${concept.frontmatter.type}] ${title} — ${description}`;
    list.appendChild(item);
  }
}

async function loadTickets() {
  const grouped = await fetchJson('/api/tickets');
  renderTickets(grouped);
}

async function loadKb(type) {
  const url = type ? `/api/concepts?type=${encodeURIComponent(type)}` : '/api/concepts';
  const concepts = await fetchJson(url);
  renderConceptList(concepts);
  return concepts;
}

function populateTypeFilter(concepts) {
  const select = document.getElementById('type-filter');
  const types = [...new Set(concepts.map((c) => c.frontmatter.type))].sort();
  for (const type of types) {
    const option = document.createElement('option');
    option.value = type;
    option.textContent = type;
    select.appendChild(option);
  }
}

function switchView(view) {
  state.view = view;
  document.getElementById('view-tickets').hidden = view !== 'tickets';
  document.getElementById('view-kb').hidden = view !== 'kb';
  for (const button of document.querySelectorAll('nav button')) {
    button.classList.toggle('active', button.dataset.view === view);
  }
}

async function refresh() {
  if (state.view === 'tickets') {
    await loadTickets();
  } else {
    const typeFilter = document.getElementById('type-filter').value;
    await loadKb(typeFilter);
  }
}

document.querySelectorAll('nav button').forEach((button) => {
  button.addEventListener('click', () => {
    switchView(button.dataset.view);
    refresh();
  });
});

document.getElementById('type-filter').addEventListener('change', refresh);
document.getElementById('refresh').addEventListener('click', refresh);

(async function init() {
  const allConcepts = await loadKb();
  populateTypeFilter(allConcepts);
  await loadTickets();
})();
```

- [ ] **Step 4: Manual verification in a browser**

Run: `cd hosa/app && npm start`
Open `http://localhost:3000` and confirm:
- The "Tickets" view shows the example ticket from Task 1 in the "À faire" column.
- Switching to "Base de connaissance" lists the example exigence and persona, and the type filter dropdown offers `Exigence`, `Persona`, `Ticket`.
- Clicking "Rafraîchir" re-fetches without a full page reload.
- No errors in the browser console.

- [ ] **Step 5: Commit**

```bash
git add hosa/app/public/
git commit -m "feat: add read-only frontend (ticket kanban + KB explorer)"
```
