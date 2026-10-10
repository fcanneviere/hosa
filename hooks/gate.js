#!/usr/bin/env node
// Hosa — gates. PreToolUse on Bash: a sprint's git commands pass only with
// their proof in the KB, so a skipped step is refused instead of trusted.
// - commit in a sprint worktree: carries `Hosa-Ticket: <slug>` and the ticket's
//   last `## Revue` is PASS or PASS-WITH-NOTES (`develop` Step 4c);
// - `git merge … sprint/<slug>` (landing): `git` Mode 2's QA gate, i.e.
//   `avancement.py check validation` — tickets done and verified, every CA
//   proved, no recette Refusé, `Bloquant : 0` audit, demo with no T-test KO.
// Fail-open on any error. Kill switch: HOSA_GATE=0.

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { findKbRoot, python } = require('./graph');

const AVANCEMENT = path.join(__dirname, '..', 'skills', 'status', 'scripts', 'avancement.py');

// Git Bash paths (/c/dev/x) → C:/dev/x, so path.resolve works on Windows.
const native = (p) => (process.platform === 'win32' ? p.replace(/^\/([a-z])(\/|$)/i, '$1:/') : p);

// Shell words grouped by command (split on && || ; | newline); quotes kept together.
function segments(cmd) {
  const segs = [[]];
  const re = /"((?:\\.|[^"\\])*)"|'([^']*)'|(&&|\|\||[;|\n&])|([^\s"';|&]+)/g;
  let m, last = -1;
  while ((m = re.exec(cmd))) {
    if (m[3]) { segs.push([]); last = -1; continue; }
    const w = m[1] != null ? m[1].replace(/\\([$`"\\\n])/g, '$1') : m[2] != null ? m[2] : m[4];
    const seg = segs[segs.length - 1];
    if (last === m.index && seg.length) seg[seg.length - 1] += w; else seg.push(w);
    last = re.lastIndex;
  }
  return segs.filter((s) => s.length);
}

// Each git call: its directory (cd and -C applied), subcommand and arguments.
function gitCalls(cmd, cwd) {
  const calls = [];
  let dir = cwd;
  for (const seg of segments(cmd)) {
    if (seg[0] === 'cd' && seg[1]) { dir = path.resolve(dir, native(seg[1])); continue; }
    let i = seg.indexOf('git');
    if (i < 0) continue;
    let d = dir;
    for (i++; i < seg.length && seg[i].startsWith('-'); i++) {
      if (seg[i] === '-C') d = path.resolve(d, native(seg[++i] || '.'));
      else if (seg[i] === '-c') i++;
    }
    if (i < seg.length) calls.push({ dir: d, sub: seg[i], args: seg.slice(i + 1) });
  }
  return calls;
}

const read = (f) => { try { return fs.readFileSync(f, 'utf8'); } catch (e) { return null; } };

// Body of the last `## <heading>` section (up to the next level-2 heading).
function section(text, heading) {
  const lines = (text || '').split(/\r?\n/);
  let start = -1;
  lines.forEach((l, i) => { if (l.trim() === `## ${heading}`) start = i; });
  if (start < 0) return null;
  const out = [];
  for (const l of lines.slice(start + 1)) { if (/^## /.test(l)) break; out.push(l); }
  return out.join('\n');
}

function commitGate(call, cmd) {
  const m = /[\\/]\.worktrees[\\/]sprint[\\/]([^\\/]+)/.exec(call.dir);
  if (!m) return null;
  const ticket = (/Hosa-Ticket:\s*([\w.-]+)/.exec(cmd) || [])[1];
  if (!ticket) {
    if (call.args.includes('--amend')) return null; // develop Step 6b adds missed files to the ticket's commit
    return `a commit on sprint ${m[1]} must carry the trailer \`Hosa-Ticket: <slug>\` — code reaches a sprint through \`develop\` only.`;
  }
  const root = findKbRoot(call.dir);
  if (!root) return null;
  const text = read(path.join(root, '.hosa', 'kb', 'tickets', `${ticket}.md`));
  if (text == null) return `ticket \`${ticket}\` not found in kb/tickets/.`;
  const verdicts = (section(text, 'Revue') || '').match(/\b(PASS-WITH-NOTES|PASS|FAIL)\b/g);
  const last = verdicts && verdicts[verdicts.length - 1];
  if (last === 'PASS' || last === 'PASS-WITH-NOTES') return null;
  return `ticket \`${ticket}\` has no passed code review: its last \`## Revue\` line is ${last || 'missing'}. ` +
    'Run `develop` Step 4c (hosa-reviewer), record the verdict, then commit.';
}

function mergeGate(call) {
  if (call.args.some((a) => /^--(abort|continue|quit)$/.test(a))) return null;
  const branch = call.args.find((a) => /^sprint\//.test(a));
  if (!branch) return null;
  const slug = branch.slice('sprint/'.length);
  const root = findKbRoot(call.dir);
  if (!root) return null;
  // One source of truth for a stage's proofs: avancement.py `check`.
  const r = spawnSync(python(), [AVANCEMENT, path.join(root, '.hosa', 'kb'), 'check', 'validation', '--sprint', slug],
    { encoding: 'utf8', timeout: 10000, windowsHide: true, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
  if (r.status !== 1) return null; // passed, or the check itself failed: fail-open
  return `sprint ${slug} can't land, the QA gate fails:
${r.stdout.trim()}
Fix each gap through its skill, then merge.`;
}

function processPayload(p) {
  if (process.env.HOSA_GATE === '0' || !p || p.tool_name !== 'Bash') return null;
  const cmd = (p.tool_input || {}).command;
  if (!cmd || !/\bgit\b/.test(cmd)) return null;
  for (const call of gitCalls(cmd, native(p.cwd || process.cwd()))) {
    const reason = call.sub === 'commit' ? commitGate(call, cmd) : call.sub === 'merge' ? mergeGate(call) : null;
    if (reason) return { hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny',
      permissionDecisionReason: `[hosa gate] ${reason}` } };
  }
  return null;
}

module.exports = { processPayload, gitCalls };

if (require.main === module) {
  let input = '';
  process.stdin.on('data', (c) => { input += c; });
  process.stdin.on('end', () => {
    try {
      const out = processPayload(JSON.parse(input));
      if (out) process.stdout.write(JSON.stringify(out));
    } catch (e) {} // fail-open
  });
}
