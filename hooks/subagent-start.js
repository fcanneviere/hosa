#!/usr/bin/env node
// Hosa — SubagentStart hook. Les subagents ne voient pas `using-hosa` : on leur
// injecte la règle d'auto-audit, pour qu'ils remontent leurs retours sur Hosa.

const RULE = `## Retour Hosa (auto-audit — s'applique à ton rapport)
Si tu as rencontré un problème avec Hosa lui-même — deux consignes contradictoires, une étape manquante, un contournement inventé, un contrôle inutile, un modèle qui ne colle pas — ou vois une amélioration concrète de son processus, ajoute à la fin de ton rapport final :
## Retour Hosa
- Problème|Idée — <fichier Hosa concerné, étape> — <ce qui s'est passé> → <proposition>
Sinon : "None". Il s'agit de tes propres consignes Hosa, jamais du code du projet géré. N'écris pas ce retour toi-même dans la KB : le skill qui t'a lancé s'en charge.`;

// The rules every Hosa agent shares: one definition here, not a copy in each agents/*.md (22 copies before 0.1.78).
// Measured on rieki and pilot2 (2026-11): 66-90 % of agent calls carry a single tool, each call re-reads the whole
// context; agents read retours/SKILL.md (10 KB) and backlog/SKILL.md (6 KB) 7 to 26 times a project; 37 % of the
// reports passed 4,000 characters and stay in the main session's context until its /clear.
const REPORT_MAX = 4000; // budget.js refuses a longer final report once — same value
const AGENT_RULES = `## Hosa agent rules (your own instructions win where they differ)
**Context:** every call re-reads your whole context; a file read is paid again on each later call.
- Independent calls (reads, greps, queries) go in one message: one call, not several.
- Your brief's paths, excerpts and slugs first. KB: the root's \`.hosa/kb/\`, never \`.worktrees/…/.hosa/kb\`; \`sommaire.md\`, then \`<hosa> kb_query\` (\`--type\`, \`--where\`, \`--sections "<heading>"\`, \`--fields\`), not whole files.
- Code: the project graph first (\`graph.py map|find|explain|affected|ticket\`, \`## Project graph\`), then its regions; \`ccc search <concept>\` if \`ccc\` works; Grep last.
- Slices, not files; no lockfiles, generated or vendored files; no re-read; narrow output (\`| tail\`, \`| grep\`, quiet reporters).
- Read a Hosa skill or agent file only when your brief or instructions name it, only the section named.
**Report** (\`retours\`, summed up: don't read it):
- \`## En bref\` first: the result in one sentence. Never cut a warning (before what it protects), a precondition, a deadline or an exact number.
- ASD-STE100 French: one idea per sentence, 20 words max (instruction) or 25 (description), active voice, imperative, digits, one term per meaning, tutoiement.
- A question you need answered: \`**Q1 — <one sentence>** (bloquante)\`, lettered options with a one-line consequence, the recommended one always \`a)\` "(recommandé)", last \`c) Autre : précise.\`; one decision each; a non-blocking one gives your default. Copy them under \`## Open Questions\` of the KB file you write.
- Paths, not content: the files you wrote, one line each. Empty section: "None".
- Under 3,000 characters besides \`## Open Questions\` and \`## Reprise\` (always whole); details go in your files. Past ${REPORT_MAX.toLocaleString('en')}, the hook refuses the report once.`;
// Only the agents that hand over manual tests carry their format.
const TESTS_RULE = `**Tests a person runs** go under \`## Tests à faire par toi\`: the environment and its full URL, a test account of the dataset, then \`| N° | Page | Action | Résultat attendu |\` numbered T1, T2…, one action per row with the interface's exact labels, an observable result with exact values; end with « Réponds en une ligne : « T1 OK, T2 KO : … » ».`;
const TESTERS = /(^|:)hosa-(tester|qa-lead|ux-designer)$/;

// gate.js refuses a `cd` into `.hosa/`: 41 refusals across 13 agents on the pilot2 run.
const KB_PATHS = 'Read and write the KB by absolute path (`<root>/.hosa/kb/…`, `kb_query.py`, `git -C`): never `cd` into `.hosa/` — the hook refuses it.';

// Windows: Bash eats the backslashes of an unquoted `C:\…` passed to a script.
const WINDOWS_PATHS = 'Pass every path argument in double quotes, with forward slashes (`"C:/dev/projet"`): Bash strips the backslashes of an unquoted `C:\\…`.';

// Agents don't see the session start's `## Scripts Hosa`: a bare `python` lacks PyYAML (okf_validate.py),
// a path under the plugin cache breaks at the next update.
function pythonLine() {
  try {
    const g = require('./graph');
    return `\`<hosa>\` in your instructions means \`${g.hosaCommand()}\`: \`<hosa> <script> [args]\` runs a Hosa script by name ` +
      '(`<hosa> --list`), from any folder; a script named `x.py` in your instructions, a plan or the KB that is in that list is `<hosa> x` — ' +
      'never look for it in the project, never ask to install it; ' +
      'never a path under the plugin cache, never a bare `python`. ' +
      `\`<python>\` means \`"${g.python()}"\`; \`\${CLAUDE_PLUGIN_ROOT}\`, to read Hosa's own files, is \`${g.pluginRoot.replace(/\\/g, '/')}\`.`;
  } catch (e) { return null; }
}

function processPayload(payload, platform = process.platform) {
  if (!/(^|:)hosa-/.test(payload.agent_type || '')) return null;
  const context = [AGENT_RULES, ...(TESTERS.test(payload.agent_type) ? [TESTS_RULE] : []), RULE, KB_PATHS, pythonLine(), ...(platform === 'win32' ? [WINDOWS_PATHS] : [])].filter(Boolean).join('\n\n');
  return { hookSpecificOutput: { hookEventName: 'SubagentStart', additionalContext: context } };
}

module.exports = { processPayload, WINDOWS_PATHS, REPORT_MAX };

if (require.main === module) {
  let input = '';
  process.stdin.on('data', (c) => (input += c));
  process.stdin.on('end', () => {
    try {
      const out = processPayload(JSON.parse(input));
      if (out) process.stdout.write(JSON.stringify(out));
    } catch (e) {} // best-effort — never block a subagent
  });
}
