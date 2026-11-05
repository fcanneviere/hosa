#!/usr/bin/env node
// Hosa — re-read guard. Port of token-optimizer-mcp's main win (MIT,
// github.com/ooples/token-optimizer-mcp): a full Read of a file already read in
// this context and unchanged since (same mtime + size) is refused once, the
// content is already above. Partial reads (offset/limit/pages) pass through.
// Keyed by session + agent_id: a subagent has its own context. PreCompact wipes
// the session state (compaction drops the earlier copies).
// Size guard (« skip files over 100KB unless required », github.com/drona23/claude-token-efficient): a
// first full Read of a file over BIG bytes is refused once too, for the part the task needs. Images are
// resized by the Read tool, a PDF needs its pages; `sommaire.md` is the KB's entry point, read whole.
// Fail-open; a retry after refusal always passes. Kill switch: HOSA_READ_GUARD=0.

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');

const stateDir = () => process.env.HOSA_STATE_DIR || path.join(os.tmpdir(), 'hosa-compress');
const stateFile = (session, agent) => path.join(stateDir(),
  `reads-${crypto.createHash('sha256').update(String(session)).digest('hex').slice(0, 12)}-${agent ? crypto.createHash('sha256').update(String(agent)).digest('hex').slice(0, 8) : 'main'}.json`);
// ponytail: about 10 k tokens; on pilot2 only `sommaire.md` (52 KB) went past it, recalibrate on real reads
const BIG = Number(process.env.HOSA_READ_MAX) || 40000;
const WHOLE = /\.(png|jpe?g|gif|webp|bmp|pdf)$|(^|[\\/])sommaire\.md$/i;
const deny = (reason) => ({ hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny',
  permissionDecisionReason: `[hosa] ${reason}` } });

function processPayload(p) {
  if (process.env.HOSA_READ_GUARD === '0' || !p || !p.session_id) return null;
  if (p.hook_event_name === 'PreCompact') {
    const prefix = path.basename(stateFile(p.session_id)).replace(/main\.json$/, '');
    for (const f of fs.readdirSync(stateDir())) if (f.startsWith(prefix)) fs.unlinkSync(path.join(stateDir(), f));
    return null;
  }
  const i = p.tool_input || {};
  if (p.tool_name !== 'Read' || !i.file_path || i.offset != null || i.limit != null || i.pages != null) return null;
  const st = fs.statSync(i.file_path);
  const sig = `${st.mtimeMs}:${st.size}`;
  const file = stateFile(p.session_id, p.agent_id);
  let s = {};
  try { s = JSON.parse(fs.readFileSync(file, 'utf8')) || {}; } catch (e) {}
  const prev = s[i.file_path];
  const big = st.size > BIG && !WHOLE.test(i.file_path);
  const save = () => { fs.mkdirSync(stateDir(), { recursive: true }); fs.writeFileSync(file, JSON.stringify(s), { mode: 0o600 }); };
  if (big && !(prev && prev.big)) {
    s[i.file_path] = { big: true };
    save();
    const kb = /[\\/]\.hosa[\\/]kb[\\/]/.test(i.file_path)
      ? '`<hosa> kb_query <kb> --slug <name> --sections "…"` (or `--fields`), ' : 'the project graph or Grep to find the range, then ';
    return deny(`${i.file_path} is ${Math.round(st.size / 1000)} KB, about ${Math.round(st.size / 4000)} k tokens kept in this context ` +
      `for the rest of the pass. Read only the part the task needs: ${kb}a Read with offset/limit. ` +
      'Need it whole (an audit, a full rewrite)? Retry the Read: it will pass.');
  }
  const refuse = prev && prev.sig === sig && !prev.refused;
  s[i.file_path] = { sig, refused: !!refuse, ...(prev && prev.big ? { big: true } : {}) };
  save();
  if (!refuse) return null;
  return deny(`${i.file_path} is unchanged since you read it earlier in this conversation — use that copy. ` +
    'Need a fresh view anyway? Retry the Read (it will pass), or read a range with offset/limit.');
}

if (require.main === module) {
  let input = '';
  process.stdin.on('data', (c) => { input += c; });
  process.stdin.on('end', () => {
    try {
      const out = processPayload(JSON.parse(input.replace(/^﻿/, '')));
      if (out) process.stdout.write(JSON.stringify(out));
    } catch (e) {} // best-effort — never block a Read
  });
}

module.exports = { processPayload };
