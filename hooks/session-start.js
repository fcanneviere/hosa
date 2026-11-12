#!/usr/bin/env node
// Hosa — SessionStart hook. Injects the `using-hosa` bootstrap skill as
// hidden context so its triggering rules and Core Rules apply without the
// user having to invoke it manually (fixes audit B2).
//
// Past 10 KB Claude Code saves a hook's context to a file and shows the model only its first 2 KB. Up to 0.1.78
// one hook gave 17-20 KB: the model never saw `using-hosa` nor `<hosa>` (rieki, 2026-11-08: a Grep in the saved
// file to find the KB, 2 gate refusals on script paths). Since 0.1.79 two hooks, each under LIMIT: this one
// with the essentials first (KB, `<hosa>`, the plan, the cleared session), then `--rules` with `using-hosa`.

const fs = require('fs');
const path = require('path');
const { WINDOWS_PATHS } = require('./subagent-start');

const LIMIT = 9500; // bytes, under Claude Code's 10 KB
const bytes = (s) => Buffer.byteLength(s, 'utf8');

// Cut `text` to `max` bytes at a line end, saying so.
function shorten(text, max, note) {
  if (bytes(text) <= max) return text;
  const lines = text.split('\n');
  const out = [];
  let size = bytes(note) + 1;
  for (const l of lines) {
    if (size + bytes(l) + 1 > max) break;
    out.push(l);
    size += bytes(l) + 1;
  }
  return `${out.join('\n')}\n${note}`;
}

// head (KB, scripts), plan, previous session, tail (graph, sommaire): under LIMIT, head and tail whole,
// the plan shortened past 60 % of the room, then the cleared session's recap.
function compose({ head = '', plan = '', previous = '', tail = '' }) {
  const parts = () => [head, plan, previous, tail].map((s) => s.trim()).filter(Boolean).join('\n\n');
  let room = LIMIT - bytes([head, tail].join('\n\n\n\n'));
  const keepPlan = Math.min(bytes(plan), Math.max(600, Math.floor(room * 0.6)));
  plan = shorten(plan, keepPlan, '- … (plan coupé : `<hosa> avancement "<kb>" reprendre` le donne entier)');
  room -= bytes(plan);
  previous = room > 300 ? shorten(previous, room - 4, '- … (session effacée coupée : son transcript est nommé plus haut)') : '';
  let out = parts();
  if (bytes(out) > LIMIT) { tail = ''; out = parts(); }
  return out;
}

// `using-hosa`, the second hook: whole, without its frontmatter; without the project rules where no KB is.
function rules(hasKb) {
  const root = process.env.CLAUDE_PLUGIN_ROOT || path.join(__dirname, '..');
  let skill = fs.readFileSync(path.join(root, 'skills', 'using-hosa', 'SKILL.md'), 'utf8')
    .replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, ''); // the frontmatter serves the Skill tool, not this context
  // No KB: the project rules weigh on every session and serve none (the skill tells when to read them).
  const cut = skill.indexOf('\n## Hosa project rules');
  if (cut > 0 && !hasKb) skill = skill.slice(0, cut);
  return skill.trim();
}

function main(payload) {
  const root = process.env.CLAUDE_PLUGIN_ROOT || path.join(__dirname, '..');
  const cwd = payload.cwd || process.cwd();
  const g = require('./graph');
  let kbRoot = null;
  try { kbRoot = g.findKbRoot(cwd); } catch (e) {}
  if (process.argv.includes('--rules')) return rules(!!kbRoot);
  let head = '';
  try {
    // Fresh install or plugin update: the app venv (graph, yaml for the scripts) isn't built yet.
    // run.py --setup builds it in the background; until then <python> is the system one.
    const venvReady = fs.existsSync(path.join(g.VENV, 'hosa-requirements.sha1'));
    if (!venvReady) {
      require('child_process').spawn(process.platform === 'win32' ? 'pythonw' : 'python3', [path.join(root, 'run.py'), '--setup'],
        { detached: true, stdio: 'ignore', windowsHide: true }).on('error', () => {}).unref();
    }
    g.writeShim();
    const kb = kbRoot && path.join(kbRoot, '.hosa', 'kb').replace(/\\/g, '/');
    head = '## Hosa\n\n' +
      (kb ? `- KB : \`${kb}\`. « reprends » → a \`## Fiche de reprise\` comes with that message: do its \`Action\`, nothing before it. None came → \`<hosa> avancement "${kb}" reprendre\`, one call.\n` : '') +
      `- \`<hosa>\` = \`${g.hosaCommand()}\` : \`<hosa> <script> [args]\` runs a Hosa script by name (\`avancement\`, \`kb_query\`, ` +
      '`kb_branch`, `okf_validate`, `ticket_check`, `docker_check`, `usage_report`, `graph`… — `<hosa> --list`), from any folder. ' +
      'A script `x.py` named in your instructions, a plan or the KB is `<hosa> x`: never look for it in the project, never install it, ' +
      'never its path under the plugin cache nor the project\'s Python (the hook refuses them).\n' +
      `- \`<python>\` = \`"${g.python()}"\`.` + (process.platform === 'win32' ? ` ${WINDOWS_PATHS}` : '') +
      (venvReady ? '' : ' Hosa is installing its Python dependencies in the background: a script failing on a missing module → wait a minute, retry.');
  } catch (e) {} // best-effort — never block session start
  let plan = '';
  try { plan = require('./avancement').resumeContext(cwd); } catch (e) {} // plan d'avancement optionnel
  let previous = '';
  try { previous = require('./reprise').previousSession(payload); } catch (e) {} // session précédente optionnelle
  let tail = '';
  try { tail += g.sessionStart(cwd); } catch (e) {} // graphe optionnel
  try {
    if (kbRoot) {
      g.refreshSummary(path.join(kbRoot, '.hosa', 'kb'));
      tail += '\n\n## Sommaire de la KB\n\nRead `.hosa/kb/sommaire.md` first (one line per concept, kept current), then open only the files you need.';
    }
  } catch (e) {} // sommaire optionnel
  return compose({ head, plan, previous, tail });
}

module.exports = { compose, rules, LIMIT };

if (require.main === module) {
  let payload = {};
  try { payload = JSON.parse(fs.readFileSync(0, 'utf8')); } catch (e) {} // no payload: no previous session
  let context = '';
  try { context = main(payload); } catch (e) { process.exit(0); } // best-effort — never block session start
  process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext: context } }));
}
