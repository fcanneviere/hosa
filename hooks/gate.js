#!/usr/bin/env node
// Hosa — gates. PreToolUse on Bash: a sprint's git commands pass only with
// their proof in the KB, so a skipped step is refused instead of trusted.
// - commit in a sprint worktree: carries `Hosa-Ticket: <slug>` and the ticket's
//   last `## Revue` is PASS or PASS-WITH-NOTES (`develop` Step 4c);
// - `git merge … sprint/<slug>` (landing): `git` Mode 2's QA gate, i.e.
//   `avancement.py check validation` — tickets done and verified, every CA
//   proved, no recette Refusé, `Bloquant : 0` audit, demo with no T-test KO;
// - `cd` into `.hosa/` (a subshell `(cd …)` passes): the session stays at the root;
// - `docker compose -p <projet>-sprint-<slug> up|create|run` from anywhere but that worktree.
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
  // a lot commit (`develop` Lot Mode) carries one trailer per ticket: each must have passed review
  const tickets = [...cmd.matchAll(/Hosa-Ticket:\s*([\w.-]+)/g)].map((x) => x[1]);
  if (!tickets.length) {
    if (call.args.includes('--amend')) return null; // develop Step 6b adds missed files to the ticket's commit
    return `a commit on sprint ${m[1]} must carry the trailer \`Hosa-Ticket: <slug>\` — code reaches a sprint through \`develop\` only.`;
  }
  const root = findKbRoot(call.dir);
  if (!root) return null;
  for (const ticket of tickets) {
    const text = read(path.join(root, '.hosa', 'kb', 'tickets', `${ticket}.md`));
    if (text == null) return `ticket \`${ticket}\` not found in kb/tickets/.`;
    const verdicts = (section(text, 'Revue') || '').match(/\b(PASS-WITH-NOTES|PASS|FAIL)\b/g);
    const last = verdicts && verdicts[verdicts.length - 1];
    if (last !== 'PASS' && last !== 'PASS-WITH-NOTES') {
      return `ticket \`${ticket}\` has no passed code review: its last \`## Revue\` line is ${last || 'missing'}. ` +
        'Run `develop` Step 4c (hosa-reviewer), record the verdict, then commit.';
    }
  }
  return null;
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

// A `cd` into `.hosa/` sticks to the session: agents dispatched next keep their memory
// (`.claude/agent-memory-local/`) inside the KB, and later git commands hit `hosa-kb`.
function cdGate(cmd, cwd) {
  const seg = segments(cmd).find((s) => s[0] === 'cd' && s[1] && /[\\/]\.hosa([\\/]|$)/.test(path.resolve(cwd, native(s[1]))));
  return seg && `\`cd ${seg[1]}\` would leave the session inside the KB. ` +
    'Stay at the project root: use `git -C <path>` and absolute paths.';
}

// `docker compose … up|create|run` builds containers from the project directory's files and `.env`:
// a sprint's project (`<projet>-sprint-<slug>`) from anywhere but its worktree runs another checkout's
// code on the sprint's name (pilot2: the tester started it from the root, Mailpit stayed there).
const COMPOSE_VALUE = new Set(['-p', '--project-name', '-f', '--file', '--project-directory', '--env-file',
  '--profile', '--ansi', '--progress', '--parallel']);
function composeGate(cmd, cwd) {
  let dir = cwd;
  for (const seg of segments(cmd)) {
    if (seg[0] === 'cd' && seg[1]) { dir = path.resolve(dir, native(seg[1])); continue; }
    const i = seg.indexOf('compose');
    if (i < 1 || seg[i - 1] !== 'docker') continue;
    let name = null, file = null, projectDir = null, sub = null;
    for (let j = i + 1; j < seg.length && !sub; j++) {
      const [opt, inline] = seg[j].split(/=(.*)/s);
      if (!seg[j].startsWith('-')) { sub = seg[j]; break; }
      if (!COMPOSE_VALUE.has(opt)) continue;
      const v = inline != null ? inline : seg[++j];
      if (opt === '-p' || opt === '--project-name') name = v;
      else if ((opt === '-f' || opt === '--file') && file == null) file = v;
      else if (opt === '--project-directory') projectDir = v;
    }
    if (!name || !['up', 'create', 'run'].includes(sub)) continue;
    const from = path.resolve(dir, native(projectDir || (file ? path.dirname(native(file)) : '.')));
    const where = from.replace(/\\/g, '/');
    const m = /-sprint-(.+)$/.exec(name);
    if (m && !where.includes(`/.worktrees/sprint/${m[1]}`)) {
      return `\`docker compose -p ${name} ${sub}\` would build the sprint's containers from ${from}, not from its worktree. ` +
        `Use \`docker compose -f "<root>/.worktrees/sprint/${m[1]}/docker-compose.yml" -p ${name} ${sub} …\`.`;
    }
    if (!m && where.includes('/.worktrees/')) {
      return `\`docker compose -p ${name} ${sub}\` would build the base environment from a sprint worktree (${from}). ` +
        'Use `docker compose -f "<root>/docker-compose.yml" …`.';
    }
  }
  return null;
}

function processPayload(p) {
  if (process.env.HOSA_GATE === '0' || !p || p.tool_name !== 'Bash') return null;
  const cmd = (p.tool_input || {}).command;
  if (!cmd) return null;
  const cwd = native(p.cwd || process.cwd());
  const deny = (reason) => ({ hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny',
    permissionDecisionReason: `[hosa gate] ${reason}` } });
  const cd = cdGate(cmd, cwd) || (/\bcompose\b/.test(cmd) ? composeGate(cmd, cwd) : null);
  if (cd) return deny(cd);
  if (!/\bgit\b/.test(cmd)) return null;
  for (const call of gitCalls(cmd, cwd)) {
    const reason = call.sub === 'commit' ? commitGate(call, cmd) : call.sub === 'merge' ? mergeGate(call) : null;
    if (reason) return deny(reason);
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
