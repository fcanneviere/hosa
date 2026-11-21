#!/usr/bin/env node
// Hosa — the floor of a managed project's sessions. Every call re-reads the tools and skills Claude Code lists;
// in rieki an empty session weighed 38.0 k, 22.8 k once the tools and skills Hosa never uses were removed
// (`/context`, 2026-11-09: system tools 16.6 → 6.6 k, skills 9.8 → 4.9 k). Called by session-start.js: it writes
// the same settings into `<root>/.claude/settings.local.json` of every Hosa project, for the next session.
// - `permissions.deny` gets `Artifact` and `PowerShell` (a bare tool deny removes the tool from the context).
// - `skillOverrides` gets `"off"` for each skill outside Hosa that the project's last skill listing named.
// It only adds: a key the user set (an `"on"` included) stays, and an allow or ask rule on a tool keeps it.
// Never in Hosa's own repository (a `.claude-plugin/plugin.json`). Fail-open. HOSA_CONTEXTE=0 turns it off.

const fs = require('fs');
const path = require('path');

const DENY = ['Artifact', 'PowerShell'];
const HEAD = 512 * 1024; // the skill listing comes with the session's first message

// The skill names of the newest transcript of `dir` that lists them.
function skillNames(dir) {
  let files = [];
  try {
    files = fs.readdirSync(dir).filter((f) => f.endsWith('.jsonl'))
      .map((f) => ({ f: path.join(dir, f), t: fs.statSync(path.join(dir, f)).mtimeMs })).sort((a, b) => b.t - a.t);
  } catch (e) { return []; }
  for (const { f } of files.slice(0, 5)) {
    let text = '';
    try {
      const fd = fs.openSync(f, 'r');
      const buf = Buffer.alloc(HEAD);
      const n = fs.readSync(fd, buf, 0, HEAD, 0);
      fs.closeSync(fd);
      text = buf.toString('utf8', 0, n);
    } catch (e) { continue; }
    for (const line of text.split('\n')) {
      if (!line.includes('"skill_listing"')) continue;
      try {
        const names = (JSON.parse(line).attachment || {}).names;
        if (Array.isArray(names) && names.length) return names.filter((s) => typeof s === 'string');
      } catch (e) {} // a line cut by HEAD
    }
  }
  return [];
}

// The settings with Hosa's additions, and whether anything was added.
function merge(settings, names) {
  const s = settings && typeof settings === 'object' && !Array.isArray(settings) ? settings : {};
  let added = false;
  const perms = s.permissions && typeof s.permissions === 'object' ? s.permissions : (s.permissions = {});
  const listed = (k) => (Array.isArray(perms[k]) ? perms[k] : []);
  const named = new Set([...listed('allow'), ...listed('ask'), ...listed('deny')].map((r) => String(r).split('(')[0]));
  for (const tool of DENY) {
    if (named.has(tool)) continue;
    perms.deny = [...listed('deny'), tool];
    added = true;
  }
  const over = s.skillOverrides && typeof s.skillOverrides === 'object' ? s.skillOverrides : {};
  for (const name of names) {
    if (name.startsWith('hosa:') || name in over) continue;
    over[name] = 'off';
    added = true;
  }
  if (Object.keys(over).length) s.skillOverrides = over;
  return { settings: s, added };
}

// Writes the settings of `root` (a Hosa project) from the transcripts next to `transcriptPath`.
function ensure(root, transcriptPath) {
  if (process.env.HOSA_CONTEXTE === '0' || !root) return false;
  if (fs.existsSync(path.join(root, '.claude-plugin', 'plugin.json'))) return false; // Hosa itself
  const names = transcriptPath ? skillNames(path.dirname(transcriptPath)) : [];
  const file = path.join(root, '.claude', 'settings.local.json');
  let current = {};
  if (fs.existsSync(file)) {
    try { current = JSON.parse(fs.readFileSync(file, 'utf8')); } catch (e) { return false; } // the user's broken file: theirs to fix
  }
  const { settings, added } = merge(current, names);
  if (!added) return false;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(settings, null, 2)}\n`);
  const exclude = path.join(root, '.git', 'info', 'exclude'); // a local file stays out of the project's commits
  try {
    if (fs.statSync(path.join(root, '.git')).isDirectory()) {
      const text = fs.existsSync(exclude) ? fs.readFileSync(exclude, 'utf8') : '';
      if (!text.split(/\r?\n/).includes('.claude/settings.local.json')) {
        fs.mkdirSync(path.dirname(exclude), { recursive: true });
        fs.appendFileSync(exclude, `${text && !text.endsWith('\n') ? '\n' : ''}.claude/settings.local.json\n`);
      }
    }
  } catch (e) {}
  return true;
}

module.exports = { ensure, merge, skillNames, DENY };
