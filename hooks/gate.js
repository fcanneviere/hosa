#!/usr/bin/env node
// Hosa — gates. PreToolUse on Bash: a sprint's git commands pass only with
// their proof in the KB, so a skipped step is refused instead of trusted.
// - commit in a sprint worktree: carries `Hosa-Ticket: <slug>` and the ticket's
//   last `## Revue` is PASS or PASS-WITH-NOTES (`develop` Step 4c);
// - `git merge … sprint/<slug>` (landing): `git` Mode 2's QA gate — every
//   ticket done and verified, technical results recorded, no recette Refusé or
//   criterion "Non", `## Audit` with `Bloquant : 0`, `## Démo` with no T-test KO.
// Fail-open on any error. Kill switch: HOSA_GATE=0.

const fs = require('fs');
const path = require('path');
const { findKbRoot } = require('./graph');

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

const field = (text, name) => (new RegExp(`^${name}:\\s*(.+)$`, 'm').exec(text || '') || [])[1];

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
  const kb = path.join(root, '.hosa', 'kb');
  const sprint = read(path.join(kb, 'sprints', `${slug}.md`));
  if (sprint == null) return `sprint \`${slug}\` not found in kb/sprints/.`;
  const gaps = [];
  const tickets = [...(section(sprint, 'Tickets') || '').matchAll(/\(\.\.\/tickets\/([^)]+)\.md\)/g)].map((x) => x[1]);
  if (!tickets.length) gaps.push('`## Tickets` lists no ticket');
  const tests = fs.existsSync(path.join(kb, 'test')) ? fs.readdirSync(path.join(kb, 'test')) : [];
  for (const t of tickets) {
    const text = read(path.join(kb, 'tickets', `${t}.md`));
    if (field(text, 'state') !== 'done' || !field(text, 'verified')) gaps.push(`${t}: not done and verified (\`validation\`)`);
    if (section(read(path.join(kb, 'test', `${t}-technique.md`)), 'Résultats techniques') == null) gaps.push(`${t}: no \`## Résultats techniques\` (\`qa\`)`);
    for (const f of tests.filter((x) => x.startsWith(`${t}-`) && x !== `${t}-technique.md`)) {
      const r = read(path.join(kb, 'test', f));
      if (/^\s*Refusé/m.test(section(r, 'Verdict') || '')) gaps.push(`${f}: recette Refusé`);
      if (/^-\s*CA\d+\s*—\s*Non\s*—/m.test(r || '')) gaps.push(`${f}: a criterion answered Non`);
    }
  }
  const audit = section(sprint, 'Audit');
  const bloquants = audit && [...audit.matchAll(/Bloquant\s*:\s*(\d+)/g)].pop();
  if (!bloquants) gaps.push('no `## Audit` with its `Bloquant : N` line (`validation` Step 3a)');
  else if (bloquants[1] !== '0') gaps.push(`\`## Audit\`: Bloquant : ${bloquants[1]}`);
  const demo = section(sprint, 'Démo');
  if (demo == null) gaps.push('no `## Démo` (`validation` Step 3b)');
  else {
    const status = {};
    for (const x of demo.matchAll(/\b(T\d+)\b[^\n]*?\b(OK|KO)\b/g)) status[x[1]] = x[2];
    const ko = Object.keys(status).filter((k) => status[k] === 'KO');
    if (ko.length) gaps.push(`\`## Démo\`: ${ko.join(', ')} still KO`);
  }
  if (!gaps.length) return null;
  return `sprint ${slug} can't land, the QA gate fails:\n- ${gaps.join('\n- ')}\nFix each gap through its skill, then merge.`;
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
