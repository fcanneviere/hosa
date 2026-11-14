#!/usr/bin/env node
// Hosa — gates. PreToolUse on Bash, PowerShell and Agent: a sprint's git commands pass only with
// their proof in the KB, so a skipped step is refused instead of trusted. A command is read through its
// `cd`s, bash subshells `(cd x && …)` and nested shells (`bash -c`, `powershell -Command`).
// - commit in a Hosa project: no `Co-Authored-By` line;
// - commit in a sprint worktree: carries `Hosa-Ticket: <slug>` and the ticket's
//   last `## Revue` is PASS or PASS-WITH-NOTES (`develop` Step 4c);
// - `git merge|pull … sprint/<slug>` (landing, `refs/heads/…` too): `git` Mode 2's QA gate, i.e.
//   `avancement.py check validation` — tickets done and verified, every CA
//   proved, no recette Refusé, `Bloquant : 0` audit, demo with no T-test KO;
// - `cd` into `.hosa/` (a subshell `(cd …)` passes): the session stays at the root;
// - `docker compose -p <projet>-sprint-<slug> up|create|run` from anywhere but that worktree;
// - a Hosa script run by its versioned path under the plugin cache, not through `<hosa>`.
// PreToolUse on Agent: a dispatch while the session's cwd is inside `.hosa/` (the agent's memory would land
// in the KB); `hosa-developer` or `hosa-debugger` dispatched on a ticket whose `## Revue` ends on two FAIL.
// Fail-open on any error. Kill switch: HOSA_GATE=0.

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { findKbRoot, python } = require('./graph');

const AVANCEMENT = path.join(__dirname, '..', 'skills', 'status', 'scripts', 'avancement.py');

// Git Bash paths (/c/dev/x) → C:/dev/x, so path.resolve works on Windows.
const native = (p) => (process.platform === 'win32' ? p.replace(/^\/([a-z])(\/|$)/i, '$1:/') : p);

// Shell words grouped by command (split on && || ; | & newline); quotes kept together. Each segment carries
// `depth` (inside how many parentheses it starts), `open` and `close` (the parentheses it opens and closes):
// `(cd x && git commit)` runs the commit in x, and the session's own directory stays where it was.
function segments(cmd) {
  const segs = [];
  const re = /"((?:\\.|[^"\\])*)"|'([^']*)'|(&&|\|\||[;|\n&])|([()])|([^\s"';|&()]+)/g;
  let m, last = -1, depth = 0, seg;
  const start = () => { seg = Object.assign([], { depth, open: 0, close: 0 }); segs.push(seg); };
  start();
  while ((m = re.exec(cmd))) {
    if (m[3]) { start(); last = -1; continue; }
    if (m[4] === '(') { if (seg.length) start(); depth++; seg.depth = depth; seg.open++; last = -1; continue; }
    if (m[4] === ')') { depth = Math.max(0, depth - 1); seg.close++; last = -1; continue; }
    const w = m[1] != null ? m[1].replace(/\\([$`"\\\n])/g, '$1') : m[2] != null ? m[2] : m[5];
    if (last === m.index && seg.length) seg[seg.length - 1] += w; else seg.push(w);
    last = re.lastIndex;
  }
  return segs.filter((s) => s.length);
}

// The directory a `cd` moves to: bash `cd`/`pushd`, PowerShell `Set-Location` and its aliases (`-Path x` too).
const CD = new Set(['cd', 'pushd', 'chdir', 'sl', 'set-location', 'push-location']);
function cdTarget(seg) {
  if (!CD.has(String(seg[0]).toLowerCase())) return null;
  for (let i = 1; i < seg.length; i++) {
    if (/^-(literal)?path$/i.test(seg[i])) return seg[i + 1] || null;
    if (!seg[i].startsWith('-')) return seg[i];
  }
  return null;
}

// A command run by a nested shell (`bash -c "…"`, `powershell -Command "…"`): its text, and whether it is PowerShell.
const SHELLS = /^(?:.*[\\/])?(bash|sh|zsh|dash|powershell|pwsh)(\.exe)?$/i;
function nested(seg) {
  const m = SHELLS.exec(seg[0] || '');
  if (!m) return null;
  const i = seg.findIndex((w, k) => k > 0 && /^-(?:[a-z]*c|command)$/i.test(w)); // -c, -lc, -Command
  return i > 0 && seg[i + 1] ? { cmd: seg[i + 1], ps: /^(powershell|pwsh)$/i.test(m[1]) } : null;
}

// Each segment with the directory it runs in: `cd` applied, a subshell's `cd` undone at its `)` (bash only:
// PowerShell's parentheses group, they don't fork), a nested shell's command walked too.
function walk(cmd, cwd, ps, fn) {
  let dir = cwd;
  const stack = [];
  for (const seg of segments(cmd)) {
    if (!ps) for (let k = 0; k < seg.open; k++) stack.push(dir);
    const to = cdTarget(seg);
    if (to) dir = path.resolve(dir, native(to));
    else {
      const inner = nested(seg);
      if (inner) walk(inner.cmd, dir, inner.ps, fn); else fn(seg, dir);
    }
    if (!ps) for (let k = 0; k < seg.close && stack.length; k++) dir = stack.pop();
  }
}

// Each git call: its directory (cd and -C applied), subcommand and arguments.
function gitCalls(cmd, cwd, ps = false) {
  const calls = [];
  walk(cmd, cwd, ps, (seg, dir) => {
    let i = seg.findIndex((w) => /^git(\.exe)?$/i.test(w));
    if (i < 0) return;
    let d = dir;
    for (i++; i < seg.length && seg[i].startsWith('-'); i++) {
      if (seg[i] === '-C') d = path.resolve(d, native(seg[++i] || '.'));
      else if (seg[i] === '-c') i++;
    }
    if (i < seg.length) calls.push({ dir: d, sub: seg[i], args: seg.slice(i + 1) });
  });
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

// A `## Revue` line's verdict: its first PASS-WITH-NOTES, PASS or FAIL — a note may quote another
// (`— FAIL — les tests PASS mais…`). The ticket's verdict is its last line's that has one. Same rule in
// avancement.py (`last_verdict`) and in the dashboard (hosa/app/public/app.js `reviewOf`).
const VERDICT = /\b(PASS-WITH-NOTES|PASS|FAIL)\b/;
const verdicts = (text) => (section(text, 'Revue') || '').split(/\r?\n/)
  .map((l) => (/—\s*DÉCISION\b/.test(l) ? 'DÉCISION' : (VERDICT.exec(l) || [])[1])).filter(Boolean);
const lastVerdict = (text) => verdicts(text).filter((v) => v !== 'DÉCISION').pop() || null;

function commitGate(call, cmd) {
  // the session's global attribution adds a co-author line; Hosa commits carry the user's identity only
  // (pilot2: 4 sprint commits carried `Co-Authored-By` despite the written rule)
  if (/co-authored-by:/i.test(cmd) && findKbRoot(call.dir)) {
    return 'a commit on a Hosa project carries the user\'s identity only: remove the `Co-Authored-By` line, then commit.';
  }
  const m = /[\\/]\.worktrees[\\/]sprint[\\/]([^\\/]+)/.exec(call.dir);
  if (!m) return null;
  // a lot commit (`develop` Lot Mode) carries one trailer per ticket: each must have passed review
  const tickets = [...cmd.matchAll(/Hosa-Ticket:\s*([\w.-]+)/g)].map((x) => x[1]);
  if (!tickets.length) {
    // develop Step 6b adds missed files to the ticket's commit, its message (and trailer) unchanged
    if (call.args.includes('--amend') && call.args.includes('--no-edit')) return null;
    return `a commit on sprint ${m[1]} must carry the trailer \`Hosa-Ticket: <slug>\` — code reaches a sprint through \`develop\` only` +
      (call.args.includes('--amend') ? ' (an amend keeps its message with `--no-edit`).' : '.');
  }
  const root = findKbRoot(call.dir);
  if (!root) return null;
  for (const ticket of tickets) {
    const text = read(path.join(root, '.hosa', 'kb', 'tickets', `${ticket}.md`));
    if (text == null) return `ticket \`${ticket}\` not found in kb/tickets/.`;
    const last = lastVerdict(text);
    if (last !== 'PASS' && last !== 'PASS-WITH-NOTES') {
      return `ticket \`${ticket}\` has no passed code review: its last \`## Revue\` line is ${last || 'missing'}. ` +
        'Run `develop` Step 4c (hosa-reviewer), record the verdict, then commit.';
    }
  }
  return null;
}

// A sprint branch however it is named: `sprint/x`, `refs/heads/sprint/x`, `heads/sprint/x`, `origin/sprint/x`.
const SPRINT_REF = /^(?:refs\/)?(?:heads\/|remotes\/[^/]+\/|[\w.-]+\/)?sprint\/(.+)$/;
function mergeGate(call) {
  if (call.args.some((a) => /^--(abort|continue|quit|skip)$/.test(a))) return null;
  const branch = call.args.map((a) => SPRINT_REF.exec(a)).find(Boolean);
  if (!branch) return null;
  const slug = branch[1];
  // inside that sprint's own worktree, `git pull origin sprint/x` syncs the branch with itself: no landing
  if (new RegExp(`[\\\\/]\\.worktrees[\\\\/]sprint[\\\\/]${slug.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}([\\\\/]|$)`).test(call.dir)) return null;
  const root = findKbRoot(call.dir);
  if (!root) return null;
  // One source of truth for a stage's proofs: avancement.py `check`.
  const r = spawnSync(python(), [AVANCEMENT, path.join(root, '.hosa', 'kb'), 'check', 'validation', '--sprint', slug],
    { encoding: 'utf8', timeout: 4000, windowsHide: true, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
  if (r.status !== 1) return null; // passed, or the check itself failed: fail-open
  return `sprint ${slug} can't land, the QA gate fails:
${r.stdout.trim()}
Fix each gap through its skill, then merge.`;
}

// A `cd` into `.hosa/` sticks to the session: agents dispatched next keep their memory
// (`.claude/agent-memory-local/`) inside the KB, and later git commands hit `hosa-kb`.
// A bash subshell `(cd …)` passes; PowerShell's parentheses don't fork, its `Set-Location` sticks either way.
function cdGate(cmd, cwd, ps) {
  const seg = segments(cmd).find((s) => (ps || !s.depth) && cdTarget(s) &&
    /[\\/]\.hosa([\\/]|$)/.test(path.resolve(cwd, native(cdTarget(s)))));
  return seg && `\`${seg[0]} ${cdTarget(seg)}\` would leave the session inside the KB. ` +
    (ps ? 'Stay at the project root: use `git -C <path>` and absolute paths.'
      : 'Stay at the project root: use `git -C <path>` and absolute paths, or a subshell — `(cd <path> && …)`.');
}

// `docker compose … up|create|run` builds containers from the project directory's files and `.env`:
// a sprint's project (`<projet>-sprint-<slug>`) from anywhere but its worktree runs another checkout's
// code on the sprint's name (pilot2: the tester started it from the root, Mailpit stayed there).
const COMPOSE_VALUE = new Set(['-p', '--project-name', '-f', '--file', '--project-directory', '--env-file',
  '--profile', '--ansi', '--progress', '--parallel']);
function composeGate(cmd, cwd, ps) {
  let reason = null;
  walk(cmd, cwd, ps, (seg, dir) => { reason = reason || composeSegment(seg, dir); });
  return reason;
}
function composeSegment(seg, dir) {
  const i = seg.indexOf('compose');
  if (i < 1 || !/^docker(\.exe)?$/i.test(seg[i - 1])) return null;
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
  if (!name || !['up', 'create', 'run'].includes(sub)) return null;
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
  return null;
}

// A Hosa script run by its path under the plugin cache: that path carries the version and breaks at the
// next update, and the Python picked (the project's .venv on pilot2) may lack the scripts' modules.
// Reading the files there (cat, grep, ls…) passes; a node tool (interface's capture.mjs) too.
const CACHE_RE = /plugins[\\/]+cache[\\/]+hosa[\\/]+hosa[\\/]+\d[^\\/\s"']*/;
const READERS = new Set(['cat', 'head', 'tail', 'sed', 'grep', 'rg', 'ls', 'less', 'wc', 'find', 'echo', 'test', 'stat', 'awk', 'diff', 'cd']);
function scriptGate(cmd) {
  if (!CACHE_RE.test(cmd)) return null;
  const script = /([\w-]+)\.py\b/.exec(cmd);
  if (!script) return null;
  const runs = segments(cmd).some((s) => !READERS.has(s[0]) && !/^\w+=/.test(s[0]));
  if (!runs) return null;
  let hosa = '<hosa>';
  try { hosa = require('./graph').hosaCommand(); } catch (e) {}
  return `Hosa scripts run through \`<hosa>\`, never by their path under the plugin cache (it changes at each update). ` +
    `Run: \`${hosa} ${script[1]} <args>\` — from any folder; \`${hosa} --list\` gives the names.`;
}

// The review loop's bound (`develop` Step 4c): two FAIL in a row on a ticket → the user decides, not a third
// correction. Counted on the ticket's `## Revue` lines; a `- <date> — DÉCISION — …` line restarts the count.
// The bound is the graph's (`tasks.controls`, `*.revue`, `fails`): one definition. Unreadable → 2.
const LOOP_MAX = (() => {
  try {
    const g = JSON.parse(fs.readFileSync(path.join(path.dirname(AVANCEMENT), 'pipeline.json'), 'utf8'));
    return g.tasks.controls.find((c) => c.stage === 'develop' && c.fails).fails || 2;
  } catch (e) { return 2; }
})();
function failRun(text) {
  let run = 0;
  for (const v of verdicts(text)) run = v === 'FAIL' ? run + 1 : 0;
  return run;
}

// `hosa-debugger` too: `develop` correction routes an unclear cause to `debug`, which must not escape the bound.
function reviewLoopGate(p, cwd) {
  const input = p.tool_input || {};
  if (!/(^|:)hosa-(developer|debugger)$/.test(String(input.subagent_type || ''))) return null;
  const root = findKbRoot(cwd);
  if (!root) return null;
  const dir = path.join(root, '.hosa', 'kb', 'tickets');
  let names;
  try { names = fs.readdirSync(dir).filter((f) => f.endsWith('.md')); } catch (e) { return null; }
  const prompt = String(input.prompt || '');
  for (const f of names) {
    const slug = f.slice(0, -3);
    if (!new RegExp(`(^|[^\\w-])${slug.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}([^\\w-]|$)`).test(prompt)) continue;
    const run = failRun(read(path.join(dir, f)));
    if (run >= LOOP_MAX) {
      return `ticket \`${slug}\` has ${run} FAIL reviews in a row: the correction loop stops here (\`develop\` Step 4c). ` +
        'Show the user the gaps of the last reviews and ask: go on correcting, change the ticket (`hosa-product-owner`), ' +
        'or fix the structure (`back develop architecture|schema-app|schema-db`, `develop/blocages.md`). Write their answer under the ticket\'s `## Revue` as ' +
        '`- <date> — DÉCISION — <their choice>` (without the words PASS or FAIL), then dispatch again.';
    }
  }
  return null;
}

// An agent's `memory:` folder (`.claude/agent-memory[-local]/`) is resolved from the session's cwd at dispatch:
// a session left inside `.hosa/` writes it into the KB (pilote, ui, pilote2: 6-18/10, before and around `cdGate`).
// `cdGate` closes one route (Bash `cd`); `pushd`, the PowerShell tool or any other move are caught here.
function dispatchCwdGate(cwd) {
  const m = /^(.*?)[\\/]\.hosa([\\/]|$)/.exec(cwd);
  return m && `the session's working directory is inside the KB (${cwd}): the agent would write its memory ` +
    `(\`.claude/agent-memory-local/\`) into the KB. Run \`cd "${m[1].replace(/\\/g, '/')}"\`, then dispatch again.`;
}

function processPayload(p) {
  if (process.env.HOSA_GATE === '0' || !p) return null;
  const deny = (reason) => ({ hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny',
    permissionDecisionReason: `[hosa gate] ${reason}` } });
  if (p.tool_name === 'Agent' || p.tool_name === 'Task') {
    const cwd = native(p.cwd || process.cwd());
    const reason = dispatchCwdGate(cwd) || reviewLoopGate(p, cwd);
    return reason ? deny(reason) : null;
  }
  // The PowerShell tool runs the same git commands (Windows): ungated, it skipped every rule below.
  if (p.tool_name !== 'Bash' && p.tool_name !== 'PowerShell') return null;
  const ps = p.tool_name === 'PowerShell';
  const cmd = (p.tool_input || {}).command;
  if (!cmd) return null;
  const cwd = native(p.cwd || process.cwd());
  // An agent's `cd` lasts one command (rieki: 337 of 337 left its cwd unchanged), and 79 of the 109 `cd` refusals
  // of that project were agents': each one a lost call that re-reads the agent's context. Main session only.
  const cd = (p.agent_id ? null : cdGate(cmd, cwd, ps)) || (/\bcompose\b/.test(cmd) ? composeGate(cmd, cwd, ps) : null) || scriptGate(cmd);
  if (cd) return deny(cd);
  if (!/\bgit\b/i.test(cmd)) return null;
  for (const call of gitCalls(cmd, cwd, ps)) {
    const reason = call.sub === 'commit' ? commitGate(call, cmd)
      : call.sub === 'merge' || call.sub === 'pull' ? mergeGate(call) : null;
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
