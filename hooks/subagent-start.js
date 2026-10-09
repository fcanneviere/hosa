#!/usr/bin/env node
// Hosa — SubagentStart hook. Les subagents ne voient pas `using-hosa` : on leur
// injecte la règle d'auto-audit, pour qu'ils remontent leurs retours sur Hosa.

const RULE = `## Retour Hosa (auto-audit — s'applique à ton rapport)
Si tu as rencontré un problème avec Hosa lui-même — deux consignes contradictoires, une étape manquante, un contournement inventé, un contrôle inutile, un modèle qui ne colle pas — ou vois une amélioration concrète de son processus, ajoute à la fin de ton rapport final :
## Retour Hosa
- Problème|Idée — <fichier Hosa concerné, étape> — <ce qui s'est passé> → <proposition>
Sinon : "None". Il s'agit de tes propres consignes Hosa, jamais du code du projet géré. N'écris pas ce retour toi-même dans la KB : le skill qui t'a lancé s'en charge.`;

function processPayload(payload) {
  if (!/(^|:)hosa-/.test(payload.agent_type || '')) return null;
  return { hookSpecificOutput: { hookEventName: 'SubagentStart', additionalContext: RULE } };
}

module.exports = { processPayload };

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
