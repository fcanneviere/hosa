// Hosa — the session just cleared, at /clear. The progress plan knows the stage, not the task
// in hand: the last requests, the last answer, the files touched and the git state let
// « reprends » pick up the work itself, in a managed project or in Hosa's own checkout.
// Read-only, fail-open. Kill switch: HOSA_REPRISE=0.

const fs = require('fs');
const path = require('path');

const TAIL = 8 * 1024 * 1024; // a week-long session reaches 48 MB: its last requests sit in the tail
const SKIP_COMMANDS = new Set(['/clear', '/compact', '/resume', '/exit', '/context', '/cost']);

const cut = (s, n) => (s.length > n ? `${s.slice(0, n).trimEnd()}…` : s);
const oneLine = (s) => s.replace(/\s+/g, ' ').trim();

// The most recent other transcript of the same project folder: the session /clear just closed.
function previousTranscript(transcript, sessionId) {
  const dir = path.dirname(transcript);
  const own = new Set([path.basename(transcript), `${sessionId}.jsonl`]);
  let best = null;
  for (const name of fs.readdirSync(dir)) {
    if (!name.endsWith('.jsonl') || own.has(name)) continue;
    const file = path.join(dir, name);
    const t = fs.statSync(file).mtimeMs;
    if (!best || t > best.t) best = { file, t };
  }
  return best && best.file;
}

function tailLines(file) {
  const fd = fs.openSync(file, 'r');
  try {
    const size = fs.fstatSync(fd).size;
    const len = Math.min(size, TAIL);
    const buf = Buffer.alloc(len);
    fs.readSync(fd, buf, 0, len, size - len);
    const lines = buf.toString('utf8').split('\n');
    if (len < size) lines.shift(); // first line cut in the middle
    return lines;
  } finally { fs.closeSync(fd); }
}

// What the user typed: tags the harness adds (selection, reminders, command output) removed,
// a slash command kept as `/name args`.
function requestText(content) {
  const text = typeof content === 'string' ? content
    : Array.isArray(content) ? content.filter((b) => b && b.type === 'text').map((b) => b.text).join('\n') : '';
  const cmd = /<command-name>([^<]*)<\/command-name>/.exec(text);
  if (cmd) {
    const name = cmd[1].trim();
    if (SKIP_COMMANDS.has(name)) return '';
    const args = /<command-args>([\s\S]*?)<\/command-args>/.exec(text);
    return oneLine(`${name} ${args ? args[1] : ''}`);
  }
  return oneLine(text.replace(/<([\w-]+)[^>]*>[\s\S]*?<\/\1>/g, ''));
}

function readSession(file) {
  const s = { title: '', requests: [], answer: '', files: [] };
  for (const line of tailLines(file)) {
    if (!line.includes('"type":"user"') && !line.includes('"type":"assistant"') && !line.includes('"type":"ai-title"')) continue;
    let e;
    try { e = JSON.parse(line); } catch (err) { continue; }
    if (e.type === 'ai-title' && e.aiTitle) { s.title = e.aiTitle; continue; }
    if (e.isSidechain || e.isMeta || e.isCompactSummary || !e.message) continue;
    if (e.type === 'user') {
      const r = requestText(e.message.content);
      if (r) s.requests.push(r);
      continue;
    }
    for (const b of Array.isArray(e.message.content) ? e.message.content : []) {
      if (b.type === 'text' && b.text.trim()) s.answer = b.text.trim();
      const f = b.type === 'tool_use' && b.input && (b.input.file_path || b.input.notebook_path);
      if (f && /^(Edit|Write|MultiEdit|NotebookEdit)$/.test(b.name)) {
        s.files = s.files.filter((x) => x !== f);
        s.files.push(f);
      }
    }
  }
  return s;
}

function gitState(cwd) {
  const { spawnSync } = require('child_process');
  const run = (...a) => {
    const r = spawnSync('git', ['-C', cwd, ...a], { encoding: 'utf8', timeout: 2000, windowsHide: true });
    return r.status === 0 ? r.stdout.split(/\r?\n/).filter((l) => l.trim()) : null; // no trim: ` M path` keeps its columns
  };
  const branch = run('branch', '--show-current');
  if (!branch) return '';
  const status = run('status', '--short') || [];
  const log = (run('log', '--oneline', '-3') || []).map((l) => cut(l, 70));
  const changes = status.length
    ? `${status.length} fichier(s) modifié(s) non commité(s)${status.length > 5 ? ', dont' : ''} : ${status.slice(0, 5).map((l) => `\`${l.slice(3)}\``).join(', ')}`
    : 'arbre propre';
  return `- Git : branche \`${branch[0] || '(détachée)'}\`, ${changes}\n- Derniers commits : ${log.map((l) => `\`${l}\``).join(' · ')}`;
}

// Hook payload (source, session_id, transcript_path, cwd) → context block, or ''.
function previousSession(p) {
  if (process.env.HOSA_REPRISE === '0' || !p || p.source !== 'clear' || !p.transcript_path) return '';
  const file = previousTranscript(p.transcript_path, p.session_id);
  if (!file) return '';
  const s = readSession(file);
  if (!s.requests.length && !s.answer) return '';
  const cwd = p.cwd || process.cwd();
  const rel = (f) => { const r = path.relative(cwd, f); return (r && !r.startsWith('..') ? r : f).replace(/\\/g, '/'); };
  const out = [`## Session précédente${s.title ? ` — ${s.title}` : ''}`, ''];
  const asks = s.requests.slice(-2);
  if (asks.length) out.push(`- Dernières demandes : ${asks.map((r) => `« ${cut(r, 300)} »`).join(' puis ')}`);
  if (s.answer) out.push(`- Dernière réponse : ${cut(oneLine(s.answer), 500)}`);
  if (s.files.length) out.push(`- Fichiers modifiés : ${s.files.slice(-8).map((f) => `\`${rel(f)}\``).join(', ')}`);
  const git = gitState(cwd);
  if (git) out.push(git);
  out.push('', 'The user ran /clear: on « reprends » or a vague follow-up, continue this work — check the git state before redoing anything; ' +
    `a new topic → ignore this block. Full transcript: \`${file.replace(/\\/g, '/')}\` (read its tail only if this is not enough).`);
  return out.join('\n');
}

module.exports = { previousSession, readSession, requestText, previousTranscript };
