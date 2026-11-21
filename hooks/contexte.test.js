const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const { ensure, merge, skillNames } = require('./contexte');

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-contexte-'));
const listing = (names) => JSON.stringify({ type: 'attachment', attachment: { type: 'skill_listing', names } });

function project() {
  const root = tmp();
  fs.mkdirSync(path.join(root, '.hosa', 'kb'), { recursive: true });
  fs.mkdirSync(path.join(root, '.git', 'info'), { recursive: true });
  const transcripts = tmp();
  fs.writeFileSync(path.join(transcripts, 'old.jsonl'), `{"type":"user"}\n${listing(['hosa:develop', 'graphify', 'anthropic-skills:docx'])}\n`);
  return { root, transcript: path.join(transcripts, 'new.jsonl') };
}

test('a Hosa project gets the tools and the skills outside Hosa turned off, out of its commits', () => {
  const { root, transcript } = project();
  assert.equal(ensure(root, transcript), true);
  const s = JSON.parse(fs.readFileSync(path.join(root, '.claude', 'settings.local.json'), 'utf8'));
  assert.deepEqual(s.permissions.deny, ['Artifact', 'PowerShell']);
  assert.deepEqual(s.skillOverrides, { graphify: 'off', 'anthropic-skills:docx': 'off' });
  assert.match(fs.readFileSync(path.join(root, '.git', 'info', 'exclude'), 'utf8'), /^\.claude\/settings\.local\.json$/m);
  assert.equal(ensure(root, transcript), false);                       // nothing new: the file is not rewritten
});

test('only adds: the user\'s keys, an "on" skill and an allowed tool stay', () => {
  const { settings, added } = merge({ env: { X: '1' }, permissions: { allow: ['PowerShell(git:*)'], deny: ['Read(.env)'] },
    skillOverrides: { graphify: 'on' } }, ['graphify', 'pytest', 'hosa:qa']);
  assert.equal(added, true);
  assert.deepEqual(settings.env, { X: '1' });
  assert.deepEqual(settings.permissions.deny, ['Read(.env)', 'Artifact']);
  assert.deepEqual(settings.skillOverrides, { graphify: 'on', pytest: 'off' });
});

test('never in Hosa\'s own repository, never with HOSA_CONTEXTE=0, never over a broken file', () => {
  const a = project();
  fs.mkdirSync(path.join(a.root, '.claude-plugin'));
  fs.writeFileSync(path.join(a.root, '.claude-plugin', 'plugin.json'), '{}');
  assert.equal(ensure(a.root, a.transcript), false);
  const b = project();
  process.env.HOSA_CONTEXTE = '0';
  try { assert.equal(ensure(b.root, b.transcript), false); } finally { delete process.env.HOSA_CONTEXTE; }
  fs.mkdirSync(path.join(b.root, '.claude'));
  fs.writeFileSync(path.join(b.root, '.claude', 'settings.local.json'), '{ broken');
  assert.equal(ensure(b.root, b.transcript), false);
  assert.equal(fs.readFileSync(path.join(b.root, '.claude', 'settings.local.json'), 'utf8'), '{ broken');
});

test('the skill names come from the newest transcript that lists them', () => {
  const dir = tmp();
  fs.writeFileSync(path.join(dir, 'a.jsonl'), `${listing(['old-skill'])}\n`);
  const later = Date.now() / 1000 + 10;
  fs.writeFileSync(path.join(dir, 'b.jsonl'), '{"type":"user"}\n');   // newest, no listing: skipped
  fs.utimesSync(path.join(dir, 'b.jsonl'), later, later);
  assert.deepEqual(skillNames(dir), ['old-skill']);
  assert.deepEqual(skillNames(path.join(dir, 'missing')), []);
});
