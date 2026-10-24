#!/usr/bin/env node
// Hosa — SessionStart hook. Injects the `using-hosa` bootstrap skill as
// hidden context so its triggering rules and Core Rules apply without the
// user having to invoke it manually (fixes audit B2).

const fs = require('fs');
const path = require('path');
const { WINDOWS_PATHS } = require('./subagent-start');

const root = process.env.CLAUDE_PLUGIN_ROOT || path.join(__dirname, '..');
const skillPath = path.join(root, 'skills', 'using-hosa', 'SKILL.md');

let context = '';
try {
  context = fs.readFileSync(skillPath, 'utf8');
} catch (e) {
  process.exit(0); // best-effort — never block session start
}
try {
  // No KB: the project rules weigh on every session and serve none (the skill tells when to read them).
  const cut = context.indexOf('\n## Hosa project rules');
  if (cut > 0 && !require('./graph').findKbRoot(process.cwd())) context = context.slice(0, cut);
} catch (e) {} // best-effort — never block session start
try {
  // Fresh install or plugin update: the app venv (graph, yaml for the scripts) isn't built yet.
  // run.py --setup builds it in the background; until then <python> is the system one.
  const g = require('./graph');
  const venvReady = fs.existsSync(path.join(g.VENV, 'hosa-requirements.sha1'));
  if (!venvReady) {
    require('child_process').spawn(process.platform === 'win32' ? 'pythonw' : 'python3', [path.join(root, 'run.py'), '--setup'],
      { detached: true, stdio: 'ignore', windowsHide: true }).on('error', () => {}).unref();
  }
  g.writeShim();
  context += `\n\n## Scripts Hosa\n\n\`<hosa>\` in skills and agents means \`${g.hosaCommand()}\`: \`<hosa> <script> [args]\` runs any Hosa script by name ` +
    '(`avancement`, `kb_query`, `kb_branch`, `okf_validate`, `ticket_check`, `docker_check`, `usage_report`, `graph`… — `<hosa> --list`), from any folder, ' +
    'with Hosa\'s own Python. A script named `x.py` in your instructions is `<hosa> x`. ' +
    'Never a script\'s path under the plugin cache, never the project\'s Python: the hook refuses them.' +
    `\n\`<python>\` means \`"${g.python()}"\`.` +
    (process.platform === 'win32' ? ` ${WINDOWS_PATHS}` : '') +
    (venvReady ? '' : ' Hosa is installing its Python dependencies in the background (first session after install or update): if a script fails on a missing module, wait a minute and retry.');
} catch (e) {} // best-effort — never block session start
try {
  context += require('./graph').sessionStart(process.cwd());
} catch (e) {} // graphe optionnel — never block session start
try {
  const g = require('./graph');
  const root = g.findKbRoot(process.cwd());
  if (root) {
    g.refreshSummary(path.join(root, '.hosa', 'kb'));
    context += '\n\n## Sommaire de la KB\n\nRead `.hosa/kb/sommaire.md` first (one line per concept, kept current), then open only the files you need.';
  }
} catch (e) {} // sommaire optionnel — never block session start
try {
  context += require('./avancement').resumeContext(process.cwd());
} catch (e) {} // plan d'avancement optionnel — never block session start

process.stdout.write(JSON.stringify({
  hookSpecificOutput: {
    hookEventName: 'SessionStart',
    additionalContext: context,
  },
}));
