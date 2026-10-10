// Hosa — progress plan at session start. Reads `.hosa/kb/project/avancement.md`
// (kept by skills/status/scripts/avancement.py) and returns its resume point as
// session context, so a session cut short resumes where it stopped, in order.

const fs = require('fs');
const path = require('path');
const { findKbRoot } = require('./graph');

const SCRIPT = path.join(process.env.CLAUDE_PLUGIN_ROOT || path.join(__dirname, '..'), 'skills', 'status', 'scripts', 'avancement.py');

// Where the KB lives: on its own branch (worktree at .hosa/kb, with a .git file) or still
// tracked in the code branches (to migrate). Fast, read-only, never blocks.
function kbLayoutNote(root) {
  const kb = path.join(root, '.hosa', 'kb');
  if (fs.existsSync(path.join(root, '.claude-plugin', 'plugin.json'))) return ''; // Hosa's own checkout: its sample KB stays as is
  const { spawnSync } = require('child_process');
  const isWorktree = fs.existsSync(path.join(kb, '.git'));
  const run = (...a) => spawnSync('git', ['-C', root, ...a], { encoding: 'utf8', timeout: 2000, windowsHide: true });
  const tracked = isWorktree ? '' : (run('ls-files', '--', '.hosa/kb').stdout || '').trim();
  const branch = !isWorktree && (run('show-ref', '--verify', '--quiet', 'refs/heads/hosa-kb').status === 0
    || run('show-ref', '--verify', '--quiet', 'refs/remotes/origin/hosa-kb').status === 0);
  const oldMemory = fs.existsSync(path.join(root, '.claude', 'agent-memory'))
    ? `\n\nAgent memories are still under \`.claude/agent-memory/\` (old \`project\` scope): propose \`kb_branch.py memoire <root>\` (plan first, \`--yes\` on the user's go-ahead).` : '';
  if (tracked) return oldMemory + `\n\nThe KB is still tracked in the code branches: propose its migration to the \`hosa-kb\` branch (\`/kb-commit migrer\`, \`kb_branch.py migrate\` — plan first, \`--yes\` on the user's go-ahead).`;
  if (branch) return oldMemory + `\n\nThe KB branch \`hosa-kb\` exists but isn't checked out: run \`kb_branch.py ensure <root>\` before reading the KB.`;
  return oldMemory;
}

function resumeContext(cwd) {
  const root = findKbRoot(cwd);
  if (!root) return '';
  const note = kbLayoutNote(root);
  const kb = path.join(root, '.hosa', 'kb');
  const file = path.join(kb, 'project', 'avancement.md');
  const how = `Keep it current: \`${process.platform === 'win32' ? 'python' : 'python3'} "${SCRIPT}" "${kb}" start|progress|done|block|skip <étape> [--sprint <slug>] [--detail …] [--reprise …]\`; \`next\` gives the stage to run, its skill and what it still lacks.`;
  let text;
  try { text = fs.readFileSync(file, 'utf8'); } catch (e) {
    return `${note}\n\n## Plan d'avancement\n\nNo progress plan yet for this project — the \`status\` skill creates it from the KB. ${how}`;
  }
  const lines = text.split(/\r?\n/);
  const out = [];
  let section = null;
  let next = null;
  for (const line of lines) {
    if (line.startsWith('## ')) { section = line.slice(3).trim(); continue; }
    if (section === 'Point de reprise' && line.trim()) { out.push(line); continue; }
    const m = /^\|\s*`([\w-]+)`\s*\|\s*([^|]*?)\s*\|\s*[^|]*\|\s*([^|]*?)\s*\|$/.exec(line);
    if (!m) continue;
    const [, stage, status, detail] = m;
    if (status === 'en cours' || status === 'bloqué') out.push(`- ${section} : \`${stage}\` ${status}${detail ? ` — ${detail}` : ''}`);
    if (!next && status !== 'fait' && status !== 'non applicable') next = `\`${stage}\` (${section}) — ${status}`;
  }
  if (next) out.push(`- Prochaine étape du plan : ${next}`);
  return `${note}\n\n## Plan d'avancement — reprise\n\n${[...new Set(out)].join('\n')}\n\nResume from here before anything else: finish the stage in progress, or the next one, in order — never skip ahead. ${how}`;
}

module.exports = { resumeContext };
