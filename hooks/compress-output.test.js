const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

process.env.HOSA_STATE_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-compress-test-'));
const { processPayload, program } = require('./compress-output');

const bash = (command, stdout) => processPayload({ tool_name: 'Bash', tool_input: { command }, tool_response: { stdout, stderr: '', interrupted: false } });
const spillOf = out => fs.readFileSync(out.match(/Full output: (.+?) \(Read/)[1], 'utf8');
const pad = (s, n = 40) => s + ' ' + 'x'.repeat(n);

test('finds the program behind runners, env and cd', () => {
  assert.equal(program('cd /x && FOO=1 rtk proxy git status'), 'git status');
  assert.equal(program('.venv/Scripts/python.exe -m pytest -q | tail -5'), 'pytest -q');
  assert.equal(program('docker compose exec -T web pytest'), 'pytest');
});

test('git status: hints go, every file stays', () => {
  const out = bash('git status', ['On branch master', 'Changes not staged for commit:',
    '  (use "git add <file>..." to update what will be committed)',
    '  (use "git restore <file>..." to discard changes in working directory)',
    ...Array.from({ length: 12 }, (_, i) => `\tmodified:   src/file${i}.js`), '',
    'no changes added to commit (use "git add" and/or "git commit -a")'].join('\n')).stdout;
  assert.doesNotMatch(out, /use "git/);
  for (let i = 0; i < 12; i++) assert.match(out, new RegExp(`  modified: src/file${i}\\.js`));
});

test('git diff: header noise goes, hunks stay whole', () => {
  const hunk = Array.from({ length: 30 }, (_, i) => `-old line ${i}\n+new line ${i}`).join('\n');
  const diff = ['a', 'b'].map(f => `diff --git a/${f}.js b/${f}.js\nindex 1234abc..5678def 100644\n--- a/${f}.js\n+++ b/${f}.js\n@@ -1,30 +1,30 @@\n${hunk}\n--- not a header`).join('\n');
  const out = bash('git diff', diff).stdout;
  assert.doesNotMatch(out, /^index |^\+\+\+ /m);
  assert.match(out, /diff --git a\/b\.js b\/b\.js/);
  assert.equal(out.match(/^[-+](old|new) line/gm).length, 120);
  assert.match(out, /^--- not a header$/m);
});

test('git log: one header line per commit, messages kept', () => {
  const log = Array.from({ length: 8 }, (_, i) => `commit ${String(i).repeat(40)}\nAuthor: Fabien <f@x.io>\nDate:   Mon Oct 26 1${i}:00:00 2026 +0100\n\n    Release 0.1.${i}: subject\n\n    body ${i}\n`).join('\n');
  const out = bash('git log', log).stdout;
  assert.match(out, /^000000000000 · Fabien <f@x\.io> · Mon Oct 26 10:00:00 2026 \+0100$/m);
  assert.match(out, /Release 0\.1\.7: subject/);
  assert.match(out, /body 7/);
  assert.doesNotMatch(out, /^(Author|Date):/m);
});

test('tests: passing lines go and are counted, failures and summary stay, spill has all', () => {
  const lines = Array.from({ length: 200 }, (_, i) => `tests/test_a.py::test_${i} PASSED  [ ${Math.floor(i / 2)}%]`);
  lines.splice(100, 0, 'tests/test_a.py::test_login FAILED', 'E   AssertionError: 1 != 2');
  lines.push('=== 1 failed, 200 passed in 3.2s ===');
  const out = bash('python -m pytest -v', lines.join('\n')).stdout;
  assert.match(out, /test_login FAILED/);
  assert.match(out, /AssertionError: 1 != 2/);
  assert.match(out, /1 failed, 200 passed/);
  assert.match(out, /200 passing-test lines dropped/);
  assert.doesNotMatch(out, /test_5 PASSED/);
  assert.match(spillOf(out), /test_5 PASSED/);
});

test('node --test TAP: ok blocks go, not ok keeps its YAML', () => {
  const ok = i => `# Subtest: case ${i}\nok ${i} - case ${i}\n  ---\n  duration_ms: 1.${i}\n  ...`;
  const tap = [...Array.from({ length: 30 }, (_, i) => ok(i + 1)),
    '# Subtest: broken\nnot ok 31 - broken\n  ---\n  error: \'expected 2\'\n  ...', '# pass 30', '# fail 1'].join('\n');
  const out = bash('node --test hooks/', tap).stdout;
  assert.doesNotMatch(out, /^ok \d+/m);
  assert.match(out, /not ok 31 - broken\n  ---\n  error: 'expected 2'/);
  assert.match(out, /# fail 1/);
});

test('installers: progress goes, errors and the result stay', () => {
  const pip = [...Array.from({ length: 40 }, (_, i) => pad(`Collecting pkg${i}`)), 'ERROR: Could not find a version that satisfies foo', 'Successfully installed pkg1 pkg2'].join('\n');
  const out = bash('pip install -r requirements.txt', pip).stdout;
  assert.match(out, /ERROR: Could not find/);
  assert.match(out, /Successfully installed/);
  assert.match(out, /40 progress lines dropped/);
});

test('grep: the path once per file, every match kept', () => {
  const hits = [];
  for (const f of ['src/a.js', 'C:/dev/b.js']) for (let n = 1; n <= 15; n++) hits.push(`${f}:${n}:const v${n} = call(${n});`);
  const out = bash('grep -rn call src', hits.join('\n')).stdout;
  assert.match(out, /^src\/a\.js\n  1: const v1 = call\(1\);/m);
  assert.match(out, /^C:\/dev\/b\.js\n/m);
  assert.equal(out.match(/= call\(/g).length, 30);
  assert.doesNotMatch(out, /Full output/); // lossless: nothing to spill
});

test('find: one line per directory', () => {
  const out = bash('find . -name "*.js"', Array.from({ length: 40 }, (_, i) => `./src/hooks/module-${i}.js`).join('\n')).stdout;
  assert.match(out, /^\.\/src\/hooks\/: module-0\.js, module-1\.js/);
  assert.equal(out.match(/module-\d+\.js/g).length, 40);
});

test('over budget, grep names every file it does not show', () => {
  const hits = [];
  for (let f = 0; f < 400; f++) for (let n = 1; n <= 3; n++) hits.push(`src/dir/file${f}.py:${n}:${'y'.repeat(30)}`);
  const out = processPayload({ tool_name: 'Grep', tool_input: { pattern: 'y' }, tool_response: { mode: 'content', content: hits.join('\n') } }).content;
  assert.ok(out.length < 25000);
  assert.match(out, /more group\(s\) not shown/);
  for (let f = 0; f < 400; f++) assert.match(out, new RegExp(`src/dir/file${f}\\.py`));
});

test('over budget, a diff keeps whole files and names the others with their counts', () => {
  const file = f => `diff --git a/${f} b/${f}\nindex 1..2 100644\n--- a/${f}\n+++ b/${f}\n@@ -1,40 +1,40 @@\n` +
    Array.from({ length: 40 }, (_, i) => `-${'o'.repeat(30)} ${i}\n+${'n'.repeat(30)} ${i}`).join('\n');
  const out = bash('git diff', Array.from({ length: 60 }, (_, i) => file(`src/f${i}.js`)).join('\n')).stdout;
  assert.ok(out.length < 25000);
  assert.match(out, /^diff --git a\/src\/f0\.js[\s\S]*n{30} 39$/m); // first file whole
  assert.match(out, /src\/f59\.js \(\+40 −40\)/);
});

test('over budget, plain output: hidden range by number, its errors with their line, spill has it', () => {
  const lines = Array.from({ length: 2000 }, (_, i) => `step ${String.fromCharCode(97 + (i % 26))}${i % 7} ${'z'.repeat(i % 13)} done`);
  lines[1000] = 'fatal: lost connection to db';
  const out = bash('make all', lines.join('\n')).stdout;
  const [, from, to] = out.match(/lines (\d+)–(\d+) of \d+ not shown/);
  assert.ok(+from < 1001 && +to > 1001);
  assert.match(out, /L1001: fatal: lost connection to db/);
  assert.equal(spillOf(out).split('\n')[1000], 'fatal: lost connection to db');
});

test('numeric data and numbered names are never folded', () => {
  const csv = Array.from({ length: 100 }, (_, i) => `${i},${i * 3},${i * 7}.5`).join('\n');
  assert.equal(bash('cat data.csv', csv), null);
  const names = Array.from({ length: 100 }, (_, i) => `-rw-r--r-- 1 me 197609 ${1000 + i} Oct 26 12:00 migration_${i}.sql`).join('\n');
  assert.equal(bash('ls -l', names), null);
});

test('never touches Read, Edit, Write or Agent', () => {
  const big = 'line\n'.repeat(5000);
  for (const tool_name of ['Read', 'Edit', 'Write', 'Agent']) {
    assert.equal(processPayload({ tool_name, tool_response: big }), null);
  }
});

test('leaves small output alone', () => {
  assert.equal(bash('echo', 'hello'), null);
});

test('collapses repeated lines losslessly', () => {
  const text = 'start\n' + 'same line\n'.repeat(200) + 'end';
  const out = processPayload({ tool_name: 'Grep', tool_response: text });
  assert.match(out, /line repeated 200×/);
  assert.match(out, /end$/);
});

test('searching a spill file returns it whole', () => {
  const out = bash('pytest -v', Array.from({ length: 50 }, (_, i) => `t::test_${i} PASSED`).join('\n') + '\n1 failed').stdout;
  const file = out.match(/Full output: (.+?) \(Read/)[1];
  assert.equal(processPayload({ tool_name: 'Grep', tool_input: { path: file }, tool_response: 'x\n'.repeat(3000) }), null);
});

test('dedups identical output within a session, not across sessions or the same call', () => {
  const text = 'y'.repeat(3000);
  const call = id => processPayload({ tool_name: 'WebFetch', tool_response: text, session_id: 's1', tool_use_id: id });
  call('a');
  assert.equal(call('a'), null);
  assert.match(call('b'), /identical to the previous WebFetch/);
  assert.equal(processPayload({ tool_name: 'WebFetch', tool_response: text, session_id: 's2', tool_use_id: 'c' }), null);
});

test('HOSA_COMPRESS=0 disables everything', () => {
  process.env.HOSA_COMPRESS = '0';
  assert.equal(bash('pytest -v', Array.from({ length: 50 }, (_, i) => `t::test_${i} PASSED`).join('\n')), null);
  delete process.env.HOSA_COMPRESS;
});
