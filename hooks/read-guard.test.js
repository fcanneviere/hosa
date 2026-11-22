const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

process.env.HOSA_STATE_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-read-guard-test-'));
const { processPayload } = require('./read-guard');

const file = path.join(process.env.HOSA_STATE_DIR, 'a.txt');
fs.writeFileSync(file, 'hello');
const read = (extra = {}) => processPayload({ hook_event_name: 'PreToolUse', tool_name: 'Read', session_id: 's1', tool_input: { file_path: file }, ...extra });
const denied = (out) => !!out && out.hookSpecificOutput.permissionDecision === 'deny';

test('refuses an unchanged re-read once, then lets the retry through', () => {
  assert.equal(read(), null);
  assert.ok(denied(read()));
  assert.equal(read(), null);
});

test('partial reads and subagents are never refused', () => {
  assert.equal(read({ tool_input: { file_path: file, offset: 1, limit: 5 } }), null);
  assert.equal(read({ agent_id: 'sub' }), null);
});

test('a big file is refused once for a part, then its re-read guard works as usual', () => {
  const big = path.join(process.env.HOSA_STATE_DIR, '.hosa', 'kb', 'cdc', 'gros.md');
  fs.mkdirSync(path.dirname(big), { recursive: true });
  fs.writeFileSync(big, 'x'.repeat(50000));
  const readBig = (extra = {}) => read({ session_id: 's2', tool_input: { file_path: big }, ...extra });
  const out = readBig();
  assert.ok(denied(out));
  assert.match(out.hookSpecificOutput.permissionDecisionReason, /kb_query/);
  assert.equal(readBig(), null);                         // the agent needs it whole
  assert.ok(denied(readBig()));                          // unchanged re-read
  fs.appendFileSync(big, 'y');
  assert.equal(readBig(), null);                         // changed: no second size refusal
  assert.equal(readBig({ tool_input: { file_path: big, offset: 1, limit: 50 } }), null);
});

test('the summary and images are read whole whatever their size', () => {
  for (const name of ['sommaire.md', 'page.png']) {
    const f = path.join(process.env.HOSA_STATE_DIR, name);
    fs.writeFileSync(f, 'x'.repeat(50000));
    assert.equal(read({ session_id: 's3', tool_input: { file_path: f } }), null);
  }
});

test('a modified file passes, PreCompact resets the session', () => {
  read();
  fs.writeFileSync(file, 'hello world');
  assert.equal(read(), null);
  processPayload({ hook_event_name: 'PreCompact', session_id: 's1' });
  assert.equal(read(), null);
  assert.equal(read({ agent_id: 'sub' }), null);
});

// --- Bash reads by a hosa-* agent in a Hosa project ---
const proj = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-read-guard-proj-'));
const tickets = path.join(proj, '.hosa', 'kb', 'tickets');
const fwd = (p) => p.split(path.sep).join('/');
fs.mkdirSync(tickets, { recursive: true });
fs.mkdirSync(path.join(proj, '.hosa', 'graph'), { recursive: true });
fs.writeFileSync(path.join(proj, '.hosa', 'graph', 'graph.json'), '{}');
fs.mkdirSync(path.join(proj, 'src'));
const src = path.join(proj, 'src', 'app.py');
fs.writeFileSync(src, Array.from({ length: 40 }, (_, i) => `ligne ${i + 1}`).join('\n'));
for (const n of ['a', 'b', 'c']) fs.writeFileSync(path.join(tickets, `${n}.md`), 'x'.repeat(8000));
let n = 0;
const bash = (command, extra = {}, query = () => '') => processPayload({ hook_event_name: 'PreToolUse', tool_name: 'Bash',
  session_id: 'sb', agent_id: extra.agent_id || `ag${n}`, agent_type: 'hosa:hosa-developer', cwd: proj,
  tool_input: { command }, ...extra }, query);
const reason = (out) => out.hookSpecificOutput.permissionDecisionReason;

test('Bash: an unchanged re-read is refused once, by cat or after a Read, and its retry passes', () => {
  n++;
  assert.equal(bash(`cat "${src}"`), null);
  const out = bash(`cd src && cat app.py`);
  assert.ok(denied(out));
  assert.match(reason(out), /Already read/);
  assert.equal(bash(`cd src && cat app.py`), null);
  const viaRead = processPayload({ hook_event_name: 'PreToolUse', tool_name: 'Read', session_id: 'sb', agent_id: `ag${n}`,
    tool_input: { file_path: src } });
  assert.ok(denied(viaRead), 'a Read after a cat of the same unchanged file is a re-read');
});

test('Bash: a range inside one already read is a re-read, a wider one is not', () => {
  n++;
  assert.equal(bash(`sed -n 1,20p "${src}"`), null);
  assert.ok(denied(bash(`sed -n '5,10p' "${src}"`)));
  n++;
  assert.equal(bash(`head -n 5 "${src}"`), null);
  assert.equal(bash(`sed -n 3,30p "${src}"`), null);
});

test('Bash: a loop printing many KB files is refused for kb_query, then passes', () => {
  n++;
  const cmd = `T="${fwd(tickets)}"; for f in a b c; do echo "== $f"; cat "$T/$f.md"; done`;
  const out = bash(cmd);
  assert.ok(denied(out));
  assert.match(reason(out), /kb_query/);
  assert.match(reason(out), /lire/);
  assert.equal(bash(cmd), null);
  n++;
  assert.ok(denied(bash(`cat ${fwd(tickets)}/*.md`)), 'a glob expands to its files');
});

test('Bash: piped, redirected, heredoc or unresolved output is left alone', () => {
  n++;
  for (const cmd of [`cat "${src}" | grep ligne`, `cat "${src}" | head -5 | cut -c1-9`, `cat "${src}" > /dev/null`, `cat "$UNKNOWN/app.py"`,
    `python - <<'EOF'\ncat "${src}"\nEOF`]) {
    assert.equal(bash(cmd), null, cmd);
    assert.equal(bash(cmd), null, cmd);
  }
});

test('Bash: main session, other agents and non-Hosa folders are never guarded', () => {
  assert.equal(bash(`cat "${src}"`, { agent_id: 'x1', agent_type: 'general-purpose' }), null);
  assert.equal(bash(`cat "${src}"`, { agent_id: 'x1', agent_type: 'general-purpose' }), null);
  const main = { hook_event_name: 'PreToolUse', tool_name: 'Bash', session_id: 'sb', cwd: proj, tool_input: { command: `cat "${src}"` } };
  assert.equal(processPayload(main), null);
  assert.equal(processPayload(main), null);
  const outside = { ...main, agent_id: 'x2', agent_type: 'hosa:hosa-developer', cwd: os.tmpdir() };
  assert.equal(processPayload(outside), null);
  assert.equal(processPayload(outside), null);
});

test('Bash: a tree-wide grep for an identifier gets the graph answer once', () => {
  n++;
  const query = (root, pattern) => (pattern === 'calcul_total' ? 'src/app.py:12 calcul_total (function)' : '');
  const out = bash('grep -rn "calcul_total" src tests', {}, query);
  assert.ok(denied(out));
  assert.match(reason(out), /src\/app.py:12/);
  assert.equal(bash('grep -rn "calcul_total" src tests', {}, query), null);
  assert.equal(bash(`grep -n "autre_nom" "${src}"`, {}, query), null, 'one file: not tree-wide');
  assert.equal(bash('grep -rn "a.*b" src', {}, query), null, 'a regex: not an identifier');
});

// rieki sprint-4: the guard saw 52 of 1 134 agent reads; these three forms made most of the rest.
test('Bash: `cat f | head -n N` and `cat f | sed -n a,bp` are reads of those lines', () => {
  n++;
  assert.equal(bash(`cat "${src}" 2>/dev/null | head -30`), null);
  assert.ok(denied(bash(`sed -n 5,10p "${src}"`)), 'inside the 30 lines already read');
  n++;
  assert.equal(bash(`cat "${src}" | sed -n 1,20p`), null);
  assert.ok(denied(bash(`head -n 10 "${src}"`)));
});

test('Bash: a tree-wide grep of identifiers as alternatives gets the graph answer once', () => {
  n++;
  const query = (root, pattern) => (pattern === 'calcul_total' ? 'src/app.py:12 calcul_total (function)' : '');
  const out = bash('grep -rn "calcul_total\\|Facture" src --include=*.py | head -20', {}, query);
  assert.ok(denied(out));
  assert.match(reason(out), /src\/app.py:12/);
  assert.equal(bash('grep -rn "calcul_total\\|a.*b" src', {}, query), null, 'one alternative is a regex');
});

test('Bash: a grep of one code file for its def/class lines gets its outline once per file', () => {
  n++;
  const asked = [];
  const query = (root, term, sub) => { asked.push([term, sub]); return sub === 'explain' ? 'file src/app.py\n→ contains\n  function calcul_total src/app.py:12' : ''; };
  const out = bash(`grep -n "def \\|class " "${src}"`, {}, query);
  assert.ok(denied(out));
  assert.match(reason(out), /outline of src\/app.py/);
  assert.deepEqual(asked, [['src/app.py', 'explain']]);
  assert.equal(bash(`grep -n "def \\|class " "${src}"`, {}, query), null, 'its retry passes');
  assert.equal(bash(`grep -n "^class " "${src}"`, {}, query), null, 'once per file');
  n++;
  assert.equal(bash(`grep -n "ligne 3" "${src}"`, {}, query), null, 'a text grep of one file passes');
  assert.equal(bash(`grep -n "def " "${fwd(tickets)}/a.md"`, {}, query), null, 'not a code file');
});

test('Bash: a worktree file\'s outline is asked by its path in the main checkout', () => {
  n++;
  const wt = path.join(proj, '.worktrees', 'sprint', 's1', 'src');
  fs.mkdirSync(wt, { recursive: true });
  fs.writeFileSync(path.join(wt, 'app.py'), 'def f():\n  pass\n');
  const asked = [];
  const query = (root, term, sub) => { asked.push(term); return 'file src/app.py'; };
  assert.ok(denied(bash(`cd "${fwd(wt)}" && grep -n "def " app.py`, {}, query)));
  assert.deepEqual(asked, ['src/app.py']);
});

test('Bash: HOSA_READ_GUARD=0 turns it off', () => {
  n++;
  process.env.HOSA_READ_GUARD = '0';
  try {
    assert.equal(bash(`cat "${src}"`), null);
    assert.equal(bash(`cat "${src}"`), null);
  } finally { delete process.env.HOSA_READ_GUARD; }
});

test('Bash: a grep in the KB is not sent to the graph', () => {
  n++;
  const query = () => 'src/app.py:1 hit';
  assert.equal(bash('grep -rn "commentaire" .hosa/kb/tickets', {}, query), null);
  assert.equal(bash('cd .hosa/kb && grep -rn "commentaire" .', {}, query), null);
});
