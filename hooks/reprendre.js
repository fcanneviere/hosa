#!/usr/bin/env node
// Hosa — UserPromptSubmit hook. « reprends » used to cost 2 or 3 calls before the first action (the `reprendre`
// skill, `avancement.py reprendre`, then the stage's skill — rieki, 12 resumes), each one re-reading the whole
// context. The resume card comes with the user's message instead: computed now, by `avancement.py` (the one reader
// of the plan), so the first call of the turn is the stage's own.
// Read-only, fail-open. Kill switch: HOSA_REPRISE=0.

const path = require('path');
const { spawnSync } = require('child_process');

// A short message that only asks to resume. A longer one is a request of its own: the session start's plan serves it.
const RESUME = /^\s*(\/(hosa:)?reprendre\b|(on\s+)?repren(d|ds|dre|ons|ez)\b|continu(e|es|er|ons|ez)\b|où\s+(on\s+)?en\s+(est|était|étions)\b)/i;
const MAX = 120;

function card(kb) {
  const g = require('./graph');
  const script = path.join(__dirname, '..', 'skills', 'status', 'scripts', 'avancement.py');
  const r = spawnSync(g.python(), [script, kb, 'reprendre'], { encoding: 'utf8', timeout: 4000, windowsHide: true,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' } });
  return r.status === 0 ? String(r.stdout || '').trim() : '';
}

function processPayload(p, getCard = card) {
  if (process.env.HOSA_REPRISE === '0' || !p || typeof p.prompt !== 'string') return null;
  const prompt = p.prompt.trim();
  if (prompt.length > MAX || !RESUME.test(prompt)) return null;
  const root = require('./graph').findKbRoot(p.cwd || process.cwd());
  if (!root) return null;
  const text = getCard(path.join(root, '.hosa', 'kb').replace(/\\/g, '/'));
  if (!text.startsWith('## Fiche de reprise')) return null; // no plan: the `reprendre` skill sends to `status`
  return { hookSpecificOutput: { hookEventName: 'UserPromptSubmit', additionalContext: `${text}\n\n` +
    'This card was computed now, with the user\'s message. Do its `Action` line at once, as the first call of this turn ' +
    '(a `start` and the skill it names: in the same message). Do not invoke the `reprendre` skill nor run ' +
    '`avancement … reprendre`: both give this same card. In the skill invoked with `args: "reprise"`, the card is the ' +
    'start-up: go to the step it names, never `start` again a stage `en cours`, never re-read a done task\'s output.' } };
}

module.exports = { processPayload, RESUME };

if (require.main === module) {
  let input = '';
  process.stdin.on('data', (c) => { input += c; });
  process.stdin.on('end', () => {
    try {
      const out = processPayload(JSON.parse(input.replace(/^﻿/, '')));
      if (out) process.stdout.write(JSON.stringify(out));
    } catch (e) {} // fail-open
  });
}
