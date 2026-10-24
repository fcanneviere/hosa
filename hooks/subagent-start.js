#!/usr/bin/env node
// Hosa — SubagentStart hook. Les subagents ne voient pas `using-hosa` : on leur
// injecte la règle d'auto-audit, pour qu'ils remontent leurs retours sur Hosa.

const RULE = `## Retour Hosa (auto-audit — s'applique à ton rapport)
Si tu as rencontré un problème avec Hosa lui-même — deux consignes contradictoires, une étape manquante, un contournement inventé, un contrôle inutile, un modèle qui ne colle pas — ou vois une amélioration concrète de son processus, ajoute à la fin de ton rapport final :
## Retour Hosa
- Problème|Idée — <fichier Hosa concerné, étape> — <ce qui s'est passé> → <proposition>
Sinon : "None". Il s'agit de tes propres consignes Hosa, jamais du code du projet géré. N'écris pas ce retour toi-même dans la KB : le skill qui t'a lancé s'en charge.`;

// gate.js refuses a `cd` into `.hosa/`: 41 refusals across 13 agents on the pilot2 run.
const KB_PATHS = 'Read and write the KB by absolute path (`<root>/.hosa/kb/…`, `kb_query.py`, `git -C`): never `cd` into `.hosa/` — the hook refuses it.';

// Windows: Bash eats the backslashes of an unquoted `C:\…` passed to a script.
const WINDOWS_PATHS = 'Pass every path argument in double quotes, with forward slashes (`"C:/dev/projet"`): Bash strips the backslashes of an unquoted `C:\\…`.';

// Agents don't see the session start's `## Python`: a bare `python` lacks PyYAML (okf_validate.py).
function pythonLine() {
  try {
    return `\`<python>\` in your instructions means \`"${require('./graph').python()}"\` — never a bare \`python\`, which may lack the scripts' modules.`;
  } catch (e) { return null; }
}

function processPayload(payload, platform = process.platform) {
  if (!/(^|:)hosa-/.test(payload.agent_type || '')) return null;
  const context = [RULE, KB_PATHS, pythonLine(), ...(platform === 'win32' ? [WINDOWS_PATHS] : [])].filter(Boolean).join('\n\n');
  return { hookSpecificOutput: { hookEventName: 'SubagentStart', additionalContext: context } };
}

module.exports = { processPayload, WINDOWS_PATHS };

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
