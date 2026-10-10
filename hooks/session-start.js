#!/usr/bin/env node
// Hosa — SessionStart hook. Injects the `using-hosa` bootstrap skill as
// hidden context so its triggering rules and Core Rules apply without the
// user having to invoke it manually (fixes audit B2).

const fs = require('fs');
const path = require('path');

const root = process.env.CLAUDE_PLUGIN_ROOT || path.join(__dirname, '..');
const skillPath = path.join(root, 'skills', 'using-hosa', 'SKILL.md');

let context = '';
try {
  context = fs.readFileSync(skillPath, 'utf8');
} catch (e) {
  process.exit(0); // best-effort — never block session start
}
try {
  // Fresh install or plugin update: the app venv (graph, yaml for the scripts) isn't built yet.
  // run.py --setup builds it in the background; until then <python> is the system one.
  const g = require('./graph');
  const venvReady = fs.existsSync(path.join(root, 'hosa', 'app', '.venv', 'hosa-requirements.sha1'));
  if (!venvReady) {
    require('child_process').spawn(process.platform === 'win32' ? 'python' : 'python3', [path.join(root, 'run.py'), '--setup'],
      { detached: true, stdio: 'ignore', windowsHide: true }).on('error', () => {}).unref();
  }
  context += `\n\n## Python\n\n\`<python>\` in skills and agents means \`"${g.python()}"\`.` +
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
