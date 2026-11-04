const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const { previousSession, requestText } = require('./reprise');

const user = (content, extra = {}) => ({ type: 'user', message: { role: 'user', content }, ...extra });
const assistant = (content, extra = {}) => ({ type: 'assistant', message: { role: 'assistant', content }, ...extra });

// A project folder of transcripts: the cleared session, written first, and the new one.
function project(entries) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'hosa-reprise-'));
  const old = path.join(dir, 'old.jsonl');
  fs.writeFileSync(old, entries.map((e) => JSON.stringify(e)).join('\n') + '\n');
  fs.utimesSync(old, new Date(), new Date(Date.now() - 1000));
  const transcript = path.join(dir, 'new.jsonl');
  return { dir, transcript, payload: { source: 'clear', session_id: 'new', transcript_path: transcript, cwd: dir } };
}

test('gives the last requests, the last answer and the files touched', () => {
  const { payload } = project([
    { type: 'ai-title', aiTitle: 'Reprise après clear' },
    user('première demande'),
    user('ajoute la reprise au hook'),
    assistant([{ type: 'tool_use', name: 'Edit', input: { file_path: path.join(os.tmpdir(), 'x', 'hooks', 'a.js') } }]),
    user([{ type: 'tool_result', content: 'ok' }]),
    assistant([{ type: 'text', text: 'C\'est fait : le hook relit la session.' }]),
  ]);
  const ctx = previousSession(payload);
  assert.match(ctx, /## Session précédente — Reprise après clear/);
  assert.match(ctx, /« première demande » puis « ajoute la reprise au hook »/);
  assert.match(ctx, /Dernière réponse : C'est fait : le hook relit la session\./);
  assert.match(ctx, /Fichiers modifiés : `.*a\.js`/);
});

test('ignores subagents, harness messages and the transcript of the new session', () => {
  const { transcript, payload } = project([
    user('vraie demande'),
    user('demande d\'agent', { isSidechain: true }),
    user('<system-reminder>rappel</system-reminder>', { isMeta: true }),
    assistant([{ type: 'text', text: 'réponse principale' }]),
    assistant([{ type: 'text', text: 'rapport d\'agent' }], { isSidechain: true }),
  ]);
  fs.writeFileSync(transcript, JSON.stringify(user('session neuve')) + '\n');
  const ctx = previousSession(payload);
  assert.match(ctx, /« vraie demande »/);
  assert.match(ctx, /réponse principale/);
  assert.doesNotMatch(ctx, /agent|rappel|session neuve/);
});

test('says nothing outside a /clear, or with nothing to resume', () => {
  const { payload } = project([user('une demande')]);
  assert.equal(previousSession({ ...payload, source: 'startup' }), '');
  assert.equal(previousSession(project([]).payload), '');
  assert.equal(previousSession(null), '');
});

test('keeps what the user typed, not the tags around it', () => {
  assert.equal(requestText([{ type: 'text', text: '<ide_selection>code</ide_selection>' }, { type: 'text', text: 'corrige ça' }]), 'corrige ça');
  assert.equal(requestText('<command-message>kb-commit</command-message>\n<command-name>/kb-commit</command-name>\n<command-args>migrer</command-args>'), '/kb-commit migrer');
  assert.equal(requestText('<command-name>/clear</command-name>'), '');
  assert.equal(requestText([{ type: 'tool_result', content: 'sortie' }]), '');
});
