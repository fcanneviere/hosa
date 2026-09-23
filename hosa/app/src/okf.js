const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');

const RESERVED_FILENAMES = new Set(['index.md', 'log.md']);
const TICKET_STATES = new Set(['todo', 'doing', 'done', 'blocked']);

function walkConcepts(kbRoot) {
  const results = [];

  function walk(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
        continue;
      }
      if (!entry.isFile() || !entry.name.endsWith('.md') || RESERVED_FILENAMES.has(entry.name)) {
        continue;
      }
      const raw = fs.readFileSync(fullPath, 'utf8');
      let parsed;
      try {
        parsed = matter(raw);
      } catch (err) {
        continue; // malformed YAML frontmatter — skip, don't crash the listing
      }
      if (!parsed.data || !parsed.data.type) {
        continue; // OKF §11: `type` is the only required field
      }
      const relPath = path.relative(kbRoot, fullPath).split(path.sep).join('/');
      results.push({ path: relPath, frontmatter: parsed.data, body: parsed.content });
    }
  }

  walk(kbRoot);
  return results;
}

function listConcepts(kbRoot, type) {
  const all = walkConcepts(kbRoot);
  if (!type) return all;
  return all.filter((concept) => concept.frontmatter.type === type);
}

function getConcept(kbRoot, relPath) {
  const resolvedRoot = path.resolve(kbRoot);
  const resolvedTarget = path.resolve(kbRoot, relPath);
  if (resolvedTarget !== resolvedRoot && !resolvedTarget.startsWith(resolvedRoot + path.sep)) {
    return null; // path traversal outside kb root
  }
  if (!fs.existsSync(resolvedTarget) || !fs.statSync(resolvedTarget).isFile()) {
    return null;
  }
  const raw = fs.readFileSync(resolvedTarget, 'utf8');
  const parsed = matter(raw);
  const normalizedPath = path.relative(resolvedRoot, resolvedTarget).split(path.sep).join('/');
  return { path: normalizedPath, frontmatter: parsed.data, body: parsed.content };
}

function listTicketsByState(kbRoot) {
  const tickets = listConcepts(kbRoot, 'Ticket');
  const grouped = { todo: [], doing: [], done: [], blocked: [] };
  for (const ticket of tickets) {
    const state = TICKET_STATES.has(ticket.frontmatter.state) ? ticket.frontmatter.state : 'todo';
    grouped[state].push(ticket);
  }
  return grouped;
}

module.exports = { walkConcepts, listConcepts, getConcept, listTicketsByState };
