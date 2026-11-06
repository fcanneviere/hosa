#!/usr/bin/env node
// Hosa — Stop hook, main session. A turn that ends while a stage of the progress plan is
// still `en cours` — no `block`, no `done` — may be a progress note, not the stage's end.
// Warns the user once per stage and session, never blocks. Fail-open. Kill switch: HOSA_STOP=0.

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { findKbRoot } = require('./graph');

const stateDir = () => process.env.HOSA_STATE_DIR || path.join(os.tmpdir(), 'hosa-compress');
const stateFile = (session) => path.join(stateDir(), `stop-${crypto.createHash('sha256').update(String(session)).digest('hex').slice(0, 12)}.json`);

// `| \`stage\` | en cours | … |` rows of avancement.md, with the section they sit in (a sprint, a pipeline).
function stagesInProgress(text) {
  const out = [];
  let section = '';
  for (const line of text.split(/\r?\n/)) {
    if (line.startsWith('## ')) { section = line.slice(3).trim(); continue; }
    if (section === 'Boucles' || section === 'Point de reprise') continue;
    const m = /^\|\s*`([\w-]+)`\s*\|\s*en cours\s*\|/.exec(line);
    if (m) out.push({ stage: m[1], section });
  }
  return out;
}

function processPayload(p) {
  if (process.env.HOSA_STOP === '0' || !p || p.stop_hook_active) return null;
  const root = findKbRoot(p.cwd || process.cwd());
  if (!root) return null;
  let text;
  try { text = fs.readFileSync(path.join(root, '.hosa', 'kb', 'project', 'avancement.md'), 'utf8'); } catch (e) { return null; }
  const file = stateFile(p.session_id);
  let warned = [];
  try { warned = JSON.parse(fs.readFileSync(file, 'utf8')) || []; } catch (e) {}
  const fresh = stagesInProgress(text).filter((s) => !warned.includes(`${s.section}/${s.stage}`));
  if (!fresh.length) return null;
  fs.mkdirSync(stateDir(), { recursive: true });
  fs.writeFileSync(file, JSON.stringify([...warned, ...fresh.map((s) => `${s.section}/${s.stage}`)]), { mode: 0o600 });
  const names = fresh.map((s) => `\`${s.stage}\` (${s.section})`).join(', ');
  return { systemMessage: `[hosa] Étape encore en cours : ${names}. Le tour finit sans \`block\` ni \`done\` : ` +
    'le travail n\'est peut-être pas fini. Dis « continue » pour le reprendre.' };
}

module.exports = { processPayload, stagesInProgress };

if (require.main === module) {
  let input = '';
  process.stdin.on('data', (c) => (input += c));
  process.stdin.on('end', () => {
    try {
      const out = processPayload(JSON.parse(input));
      if (out) process.stdout.write(JSON.stringify(out));
    } catch (e) {} // fail-open — never block the end of a turn
  });
}
