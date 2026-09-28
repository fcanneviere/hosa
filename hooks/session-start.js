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
  context += require('./graph').sessionStart(process.cwd());
} catch (e) {} // graphe optionnel — never block session start

process.stdout.write(JSON.stringify({
  hookSpecificOutput: {
    hookEventName: 'SessionStart',
    additionalContext: context,
  },
}));
