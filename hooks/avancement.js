// Hosa — progress plan at session start. Reads `.hosa/kb/project/avancement.md`
// (kept by skills/status/scripts/avancement.py) and returns its resume point as
// session context, so a session cut short resumes where it stopped, in order.

const fs = require('fs');
const path = require('path');
const { findUp } = require('./graph');

const SCRIPT = path.join(process.env.CLAUDE_PLUGIN_ROOT || path.join(__dirname, '..'), 'skills', 'status', 'scripts', 'avancement.py');

function resumeContext(cwd) {
  const root = findUp(cwd, path.join('.hosa', 'kb'));
  if (!root) return '';
  const kb = path.join(root, '.hosa', 'kb');
  const file = path.join(kb, 'project', 'avancement.md');
  const how = `Keep it current: \`${process.platform === 'win32' ? 'python' : 'python3'} "${SCRIPT}" "${kb}" start|progress|done|block|skip <étape> [--sprint <slug>] [--detail …] [--reprise …]\`.`;
  let text;
  try { text = fs.readFileSync(file, 'utf8'); } catch (e) {
    return `\n\n## Plan d'avancement\n\nNo progress plan yet for this project — the \`status\` skill creates it from the KB. ${how}`;
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
  return `\n\n## Plan d'avancement — reprise\n\n${[...new Set(out)].join('\n')}\n\nResume from here before anything else: finish the stage in progress, or the next one, in order — never skip ahead. ${how}`;
}

module.exports = { resumeContext };
