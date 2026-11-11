#!/usr/bin/env node
// Hosa — PostToolUse hook on Agent, main session. A Hosa agent launched in the background leaves the
// main session nothing to do, yet the launch result starts one more call that re-reads the whole
// context to say « ça tourne en arrière-plan » (rieki, 2026-11-09/10: 54 of 55 launches, ~4 M tokens
// re-read, a fifth of the main session's context). This hook ends the turn at the launch instead;
// the agent's hand-back wakes the session as before.
// An experiment, off until a sprint has measured it: HOSA_ARRET_LANCEMENT=1 turns it on. Fail-open.

const { findKbRoot } = require('./graph');

const HOSA_AGENT = /(^|:)hosa-/;

function processPayload(p) {
  if (process.env.HOSA_ARRET_LANCEMENT !== '1' || !p || p.agent_id) return null; // an agent never dispatches
  if (p.tool_name !== 'Agent' && p.tool_name !== 'Task') return null;
  const input = p.tool_input || {};
  const result = p.tool_response || {};
  if (!HOSA_AGENT.test(String(input.subagent_type || ''))) return null;
  if (result.status !== 'async_launched' && result.isAsync !== true) return null; // a report is here: go on
  if (!findKbRoot(p.cwd || process.cwd())) return null;
  return { continue: false, stopReason: `[hosa] Agent lancé (${input.description || input.subagent_type}) : ` +
    'la session attend son rapport sans relire son contexte.' };
}

module.exports = { processPayload };

if (require.main === module) {
  let input = '';
  process.stdin.on('data', (c) => (input += c));
  process.stdin.on('end', () => {
    try {
      const out = processPayload(JSON.parse(input));
      if (out) process.stdout.write(JSON.stringify(out));
    } catch (e) {} // fail-open — never stop a turn on the hook's own error
  });
}
