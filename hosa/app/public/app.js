'use strict';

const STATES = { todo: 'To do', doing: 'In progress', done: 'Done', blocked: 'Blocked' };
const SPRINT_STATES = { planned: 'Planned', active: 'Active', done: 'Done' };
const TRUST = {
  human: { label: 'Human-verified', short: 'Human' },
  machine: { label: 'Machine-checked', short: 'Machine' },
  none: { label: 'Unverified', short: 'Unverified' },
};
const KIND = { human: ['H', 'Human'], agent: ['A', 'Agent'], process: ['P', 'Process'] };
const PTS = { S: 1, M: 3, L: 5 };
const VIEWS = [['', 'Home'], ['steering', 'Steering'], ['personas', 'Personas'], ['board', 'Board'], ['sprints', 'Sprints'], ['kb', 'Knowledge'], ['graph', 'Graph'], ['journal', 'Journal']];
const MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ');

const store = {}; // concepts (décorés), byPath, activity, overview — rechargés ensemble
const view = () => document.getElementById('view');

// --- utilitaires -----------------------------------------------------------

function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'class') el.className = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  el.append(...children.flat(Infinity).filter((c) => c != null && c !== false));
  return el;
}

async function api(path, options = {}) {
  const init = { ...options };
  if (options.json) {
    init.body = JSON.stringify(options.json);
    init.headers = { 'Content-Type': 'application/json' };
  }
  const res = await fetch(`/api/${path}`, init);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Error ${res.status}`);
  return data;
}

const encodePath = (p) => p.split('/').map(encodeURIComponent).join('/');

function showError(message) {
  const el = document.getElementById('error');
  el.textContent = message || '';
  el.hidden = !message;
}

let toastTimer;
function toast(message) {
  const el = document.getElementById('toast');
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2600);
}

const fd = (d) => (d ? `${+d.slice(8, 10)} ${MONTHS[+d.slice(5, 7) - 1]}` : '');
const today = () => new Date().toLocaleDateString('en-CA'); // AAAA-MM-JJ en heure locale
const slugify = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
const initials = (s) => s.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join('');
const sum = (ts) => ts.reduce((a, t) => a + t.pts, 0);
const byPrio = (a, b) => (a.fm.priority ?? Infinity) - (b.fm.priority ?? Infinity) || a.title.localeCompare(b.title);
const last = (c) => (c.verAt > c.byAt ? c.verAt : c.byAt);
const isTicket = (c) => c.type === 'Ticket';
const num = (t) => t.fm.id || t.slug;

// --- provenance ------------------------------------------------------------

// `generated`/`verified` valent { by, at } ; les skills écrivent aussi la forme courte `verified: human:x`.
function actorId(v) {
  if (v && typeof v === 'object') return v.by ? String(v.by) : null;
  return typeof v === 'string' && /^[a-z]/i.test(v) ? v : null;
}
const atOf = (v) => (v && typeof v === 'object' && v.at ? String(v.at).slice(0, 10) : '');
const kindOf = (id) => (id.startsWith('human:') ? 'human' : id.startsWith('process:') ? 'process' : 'agent');
function shortOf(id) {
  if (kindOf(id) !== 'agent') return id.split(':').pop();
  const parts = id.split('/');
  return parts.length > 1 && /^[\d.]+$/.test(parts.at(-1)) ? parts.at(-2) : parts.at(-1);
}
const trustOf = (ver) => (!ver ? 'none' : kindOf(ver) === 'human' ? 'human' : 'machine');

function linksOf(c) {
  return [...c.body.matchAll(/\]\(([^)\s#]+?\.md)(?:#[^)]*)?\)/g)]
    .filter((m) => !/^[a-z]+:/i.test(m[1]))
    .map((m) => decodeURIComponent(new URL(m[1], `http://kb/${c.path}`).pathname.slice(1)));
}

function deco(c) {
  const fm = c.frontmatter;
  const i = c.path.lastIndexOf('/');
  const by = actorId(fm.generated);
  const ver = actorId(fm.verified);
  return {
    ...c, fm,
    folder: i < 0 ? '.' : c.path.slice(0, i),
    slug: c.path.slice(i + 1, -3),
    title: fm.title || c.path,
    type: fm.type,
    status: fm.status || 'stable',
    tags: [].concat(fm.tags || []),
    by, byAt: atOf(fm.generated), ver, verAt: atOf(fm.verified), trust: trustOf(ver),
    state: fm.state in STATES ? fm.state : 'todo',
    pts: PTS[fm.estimate] ?? (+fm.estimate || 0),
    links: linksOf(c),
  };
}

// Les log.md OKF : « <acteur> <texte avec `slug`> ».
function parseEntry(e) {
  const m = /^([a-z][\w.-]*(?::[\w.@-]+|\/[\w.-]+))\s+(.*)$/i.exec(e.text);
  const slug = /`([^`]+)`/.exec(e.text)?.[1];
  return { ...e, actor: m ? m[1] : null, rest: m ? m[2] : e.text, path: slug && `${e.bundle ? `${e.bundle}/` : ''}${slug}.md` };
}

async function load(force = false) {
  if (store.concepts && !force) return;
  const [cs, activity, overview] = await Promise.all([api('concepts'), api('activity'), api('overview')]);
  store.concepts = cs.map(deco);
  store.byPath = Object.fromEntries(store.concepts.map((c) => [c.path, c]));
  store.activity = activity.map(parseEntry);
  store.overview = overview;
  renderSide();
}

// --- petits composants -------------------------------------------------------

const tdot = (t, lg) => h('span', { class: `tdot t-${t}${lg ? ' lg' : ''}`, title: TRUST[t].label });
const trust = (t, long) => h('span', { class: `trust t-${t}` }, tdot(t), TRUST[t][long ? 'label' : 'short']);
const sdot = (s) => h('span', { class: `sdot s-${s}`, title: STATES[s] });
const statusPill = (s) => h('span', { class: `status ${s}` }, s);
const prio = (p) => (p != null ? h('span', { class: `prio p${p}` }, `P${p}`) : null);
const cap = (text) => h('span', { class: 'cap' }, text);
const none = (text) => h('span', { class: 'none' }, text);
const head = (title, ...rest) => h('header', { class: 'page-head' }, h('h1', {}, title), rest);

function actor(id, full) {
  if (!id) return null;
  const k = kindOf(id);
  return h('span', { class: 'actor', title: id }, h('span', { class: `glyph g-${k}`, 'aria-hidden': 'true' }, KIND[k][0]), full ? id : shortOf(id));
}

function est(t) {
  const e = t.fm.estimate;
  if (e == null || e === '') return null;
  return PTS[e] ? `${e} · ${t.pts} pt${t.pts > 1 ? 's' : ''}` : `${t.pts} pts`;
}

function stack(parts, total, cls = 'stack') {
  return h('div', { class: cls }, parts.filter(([, n]) => n).map(([c, n, title]) =>
    h('span', { class: c, style: `width:${(n / total) * 100}%`, title: `${title}: ${n}` })));
}
const trustStack = (cs, cls) => stack(Object.keys(TRUST).map((t) => [`f-${t}`, cs.filter((c) => c.trust === t).length, TRUST[t].label]), cs.length || 1, cls);

function chip(label, on, onclick, dot) {
  return h('button', { type: 'button', class: 'chip', 'aria-pressed': String(on), onclick }, dot, label);
}

function select(value, onchange, opts, label) {
  const s = h('select', {
    class: `sel${value ? ' on' : ''}`, 'aria-label': label,
    onchange: (e) => { s.classList.toggle('on', !!e.target.value); onchange(e.target.value); },
  }, opts.map(([v, l]) => h('option', { value: v }, l)));
  s.value = value;
  return s;
}

// Les slugs cités entre backticks deviennent des liens vers le concept quand il existe.
function logText(e) {
  return h('span', { class: 'logtext' }, e.rest.split('`').map((part, i) => {
    if (!(i % 2)) return part;
    const c = store.byPath[`${e.bundle ? `${e.bundle}/` : ''}${part}.md`];
    return c ? h('a', { href: `#/kb/${c.path}` }, c.title) : h('code', {}, part);
  }));
}

const verifyBtn = (c, cls, label = 'Verify') => h('button', { type: 'button', class: cls, onclick: () => verify(c) }, label);

// Le serveur ne connaît pas l'utilisateur : on demande son nom une fois (clé `hosa.me`).
function me() {
  let name = localStorage.getItem('hosa.me');
  if (!name) {
    name = slugify(prompt('Your name, recorded as human:<name> in `verified`') || '');
    if (name) localStorage.setItem('hosa.me', name);
  }
  return name;
}

async function verify(c) {
  const name = me();
  if (!name) return;
  try {
    const at = `${new Date().toISOString().slice(0, 19)}Z`;
    await api(`concepts/${encodePath(c.path)}`, { method: 'PATCH', json: { frontmatter: { verified: { by: `human:${name}`, at } } } });
    await load(true);
    toast(`“${c.title}” verified`);
  } catch (err) {
    showError(`Verification failed: ${err.message}`);
  }
  route();
}

async function moveTicket(t, state) {
  if (t.state === state) return;
  try {
    await api(`concepts/${encodePath(t.path)}`, { method: 'PATCH', json: { frontmatter: { state } } });
    await load(true);
    toast(`“${t.title}” moved to ${STATES[state]}`);
  } catch (err) {
    showError(`Move failed: ${err.message}`);
  }
  route();
}

// --- barre latérale ------------------------------------------------------------

function renderSide() {
  const cs = store.concepts;
  const tickets = cs.filter(isTicket);
  const blocked = tickets.filter((t) => t.state === 'blocked').length;
  const counts = {
    steering: blocked ? `${blocked} blocked` : '',
    personas: cs.filter((c) => c.type === 'Persona').length,
    board: tickets.filter((t) => t.state !== 'done').length,
    kb: cs.length,
    journal: store.activity.length,
  };
  document.getElementById('nav').replaceChildren(...VIEWS.map(([k, label], i) =>
    h('a', { href: `#/${k}`, 'data-nav': k }, h('span', { class: 'k' }, i + 1), label, h('span', { class: 'n' }, counts[k] || ''))));
  document.getElementById('legend').replaceChildren(cap('Trust'), ...Object.keys(TRUST).map((t) =>
    h('div', {}, tdot(t), h('span', { class: `l c-${t}` }, TRUST[t].label), h('span', { class: 'n' }, cs.filter((c) => c.trust === t).length))));
}

// --- Home -------------------------------------------------------------------------

function renderHome() {
  const cs = store.concepts;
  const tickets = cs.filter(isTicket);
  const project = store.byPath[store.overview.project?.path];
  const types = [...new Set(cs.map((c) => c.type))].filter((t) => t !== 'Project').sort();
  const active = tickets.filter((t) => t.state === 'doing' || t.state === 'blocked')
    .sort((a, b) => (a.state === b.state ? byPrio(a, b) : a.state === 'blocked' ? -1 : 1));
  const unverified = cs.filter((c) => c.trust === 'none' && c.status !== 'deprecated').sort((a, b) => b.byAt.localeCompare(a.byAt));

  view().replaceChildren(h('div', { class: 'home' },
    h('section', { class: 'hero' },
      project ? h('div', { class: 'bar' }, project.path, trust(project.trust, true)) : null,
      h('h1', {}, project ? project.title : 'Project not initialised'),
      h('p', { class: 'vision' }, project
        ? project.fm.description || ''
        : 'Run /hosa in Claude Code: it asks for the project name, goal and audience, then creates its personas.')),
    h('section', { class: 'counters' }, types.map((t) => {
      const of = cs.filter((c) => c.type === t);
      return h('a', { class: 'counter', href: '#/kb', onclick: () => Object.assign(kbFilter, KB_RESET, { folder: '', type: t }) },
        h('span', { class: 'n' }, of.length), h('span', { class: 't' }, t), trustStack(of));
    })),
    h('div', { class: 'two' },
      h('section', {},
        h('h2', { class: 'sub' }, 'In progress and blocked'),
        active.length ? active.map((t) => h('a', { class: `line${t.trust === 'none' ? ' unv' : ''}`, href: `#/kb/${t.path}` },
          sdot(t.state), h('span', { class: 'num' }, num(t)), h('span', { class: 't' }, t.title), prio(t.fm.priority), tdot(t.trust)))
          : none('Nothing in progress.')),
      h('section', {},
        h('h2', { class: 'sub' }, 'To review', h('small', { class: 'c-none' }, `${unverified.length} unverified`)),
        unverified.length ? unverified.slice(0, 6).map((c) => h('div', { class: 'review' },
          tdot(c.trust),
          h('a', { href: `#/kb/${c.path}` }, h('span', { class: 't' }, c.title), h('span', { class: 'p' }, c.path, c.by ? ` · by ${shortOf(c.by)}` : '')),
          verifyBtn(c, 'btn sm')))
          : none('Everything is verified.'))),
    h('section', { class: 'feed' },
      h('div', { class: 'hd' }, h('h2', { class: 'sub' }, 'Recent activity'), h('a', { href: '#/journal' }, 'Open journal')),
      store.activity.length
        ? store.activity.slice(0, 7).map((e) => h('div', { class: 'e' }, h('span', { class: 'when' }, fd(e.date)), actor(e.actor) || h('span'), logText(e)))
        : none('No entries yet in the KB logs.'))));
}

// --- Steering ---------------------------------------------------------------------

// Statuts écrits par avancement.py → états des pastilles du board.
const PLAN_STATES = { 'à faire': 'todo', 'en cours': 'doing', fait: 'done', bloqué: 'blocked', 'non applicable': 'skipped' };
const PLAN_LABELS = { todo: 'To do', doing: 'In progress', done: 'Done', blocked: 'Blocked', skipped: 'Not applicable' };

// Le plan d'avancement (`project/avancement.md`) : la méthode telle que les skills la tiennent.
function planPanel(plan) {
  const n = plan.next;
  const row = (s) => {
    const st = PLAN_STATES[s.status] || 'todo';
    return h('div', { class: `pstage ps-${st}${n && s.stage === n.stage ? ' cur' : ''}`, title: s.detail || null },
      h('span', { class: `sdot s-${st === 'skipped' ? 'todo' : st}`, title: PLAN_LABELS[st] }),
      h('code', {}, s.stage), h('span', { class: 'st' }, PLAN_LABELS[st]),
      h('span', { class: 'd' }, [s.detail, s.at && fd(s.at.slice(0, 10))].filter(Boolean).join(' · ')));
  };
  return h('section', { class: 'plan' },
    n ? h('p', { class: 'next' }, 'Next step: ', h('strong', {}, n.stage), ` (${n.section}, ${n.status.toLowerCase()}) — run `,
      h('code', {}, `/${n.skill}`), ' in Claude Code.')
      : h('p', { class: 'next' }, 'Every known stage is done — plan a new sprint with ', h('code', {}, '/sprint'), '.'),
    n?.gaps.length ? h('div', { class: 'blocked' }, h('b', {}, 'Still to prove before it is done'),
      n.gaps.map((g) => h('div', { class: 'd' }, g))) : null,
    plan.resume.length ? h('div', { class: 'resume' }, cap('Resume point'), plan.resume.map((l) => h('div', {}, l))) : null,
    h('div', { class: 'psections' }, plan.sections.map((s) => {
      const closed = s.stages.filter((x) => ['fait', 'non applicable'].includes(x.status)).length;
      return h('div', { class: 'psection' },
        h('div', { class: 'hd' }, h('b', {}, s.title), h('span', { class: 'mono muted' }, `${closed}/${s.stages.length}`)),
        s.stages.map(row));
    })));
}

function nextStep(ov) {
  if (ov.plan) return planPanel(ov.plan);
  const stage = ov.pipelines.flatMap((l) => l.stages).find((s) => s.skill === ov.next);
  return h('p', { class: 'next' }, stage
    ? ['Next step: ', h('strong', {}, stage.label), ' — run ', h('code', {}, `/${stage.skill}`), ' in Claude Code.']
    : 'Every step of the method has left its trace in the KB.',
    ' No progress plan yet: ', h('code', {}, '/status'), ' creates it.');
}

function split(label, legend, bar) {
  return h('div', {}, h('div', { class: 'split-hd' }, h('span', {}, label), h('span', { class: 'mono' }, legend)), bar);
}

function renderSteering() {
  const ov = store.overview;
  const tickets = store.concepts.filter(isTicket);
  const blocked = tickets.filter((t) => t.state === 'blocked').sort(byPrio);
  const slugs = ov.sprints.map((s) => s.slug);
  const groups = [
    ...ov.sprints.map((s) => ({ key: s.slug, name: s.title, path: s.path, phase: SPRINT_STATES[s.state] || s.state, ts: tickets.filter((t) => t.fm.sprint === s.slug) })),
    { key: null, name: 'Backlog', phase: 'Not planned', ts: tickets.filter((t) => !slugs.includes(t.fm.sprint)) },
  ].filter((g) => g.ts.length || g.path);

  const group = (g) => {
    const tot = sum(g.ts);
    const done = sum(g.ts.filter((t) => t.state === 'done'));
    const pct = tot ? Math.round((done / tot) * 100) : 0;
    const byHuman = g.ts.filter((t) => t.by && kindOf(t.by) === 'human').length;
    const n = (t) => g.ts.filter((x) => x.trust === t).length;
    return h('div', { class: 'group' },
      h('div', {},
        h('div', { class: 'hd' },
          g.key ? h('span', { class: 'k' }, g.key) : null,
          g.path ? h('a', { class: 'nm', href: `#/kb/${g.path}` }, g.name) : h('span', { class: 'nm' }, g.name),
          h('span', { class: 'ph' }, g.phase)),
        h('div', { class: 'bar-row' }, h('div', { class: 'track' }, h('span', { style: `width:${pct}%` })), h('span', { class: 'pct' }, `${pct}%`)),
        h('div', { class: 'counts' }, h('span', { class: 'mono' }, `${done} / ${tot} pts`), Object.keys(STATES).map((s) => {
          const k = g.ts.filter((t) => t.state === s).length;
          return k ? h('span', {}, sdot(s), `${k} ${STATES[s].toLowerCase()}`) : null;
        }))),
      h('div', {},
        split('Requested by', `${byHuman} human · ${g.ts.length - byHuman} agent`,
          stack([['f-byhuman', byHuman, 'Human'], ['f-byagent', g.ts.length - byHuman, 'Agent']], g.ts.length || 1, 'stack tall')),
        split('Validated by', `${n('human')} human · ${n('machine')} machine · ${n('none')} none`, trustStack(g.ts, 'stack tall'))));
  };

  const agents = tickets.filter((t) => !t.by || kindOf(t.by) !== 'human').length;
  view().replaceChildren(h('div', { class: 'page' },
    head('Steering', h('span', { class: 'sum' }, `${tickets.length} tickets · ${agents} requested by agents · ${tickets.filter((t) => t.trust === 'none').length} unverified`)),
    nextStep(ov),
    blocked.length ? h('section', { class: 'blocked' },
      h('b', {}, `${blocked.length} blocked ticket${blocked.length > 1 ? 's' : ''}`),
      blocked.map((t) => h('a', { href: `#/kb/${t.path}` },
        h('span', { class: 'mono muted' }, num(t)),
        h('div', {}, h('div', {}, t.title), t.fm.description ? h('div', { class: 'd' }, t.fm.description) : null),
        h('span', { class: 'mono muted' }, [t.fm.sprint || 'backlog', t.fm.priority != null ? `P${t.fm.priority}` : null].filter(Boolean).join(' · '))))) : null,
    groups.length ? h('section', { class: 'groups' }, groups.map(group)) : none('No ticket yet. /backlog creates them from the requirements.'),
    h('div', { class: 'keys' },
      h('span', {}, h('span', { class: 'swatch f-byhuman' }), 'Requested by human'),
      h('span', {}, h('span', { class: 'swatch f-byagent' }), 'Requested by agent'),
      Object.keys(TRUST).map((t) => h('span', {}, h('span', { class: `swatch f-${t}` }), TRUST[t].label)))));
}

// --- Personas -----------------------------------------------------------------------

// Puces de la section `## <nom>` ; à défaut, le paragraphe entier.
function listUnder(body, names) {
  const sec = body.split(/^##\s+/m).slice(1).find((s) => names.test(s.split('\n')[0]));
  if (!sec) return [];
  const lines = sec.split('\n').slice(1).map((l) => l.trim()).filter(Boolean);
  const bullets = lines.filter((l) => /^[-*]\s/.test(l)).map((l) => l.slice(2));
  return (bullets.length ? bullets : [lines.join(' ')]).map((l) => l.replace(/[*_`]/g, '')).filter(Boolean);
}

function renderPersonas() {
  const people = store.concepts.filter((c) => c.type === 'Persona').sort((a, b) => a.title.localeCompare(b.title));
  view().replaceChildren(h('div', { class: 'page' },
    head('Personas', h('span', { class: 'sum' }, 'personnas/')),
    people.length ? h('div', { class: 'personas' }, people.map((p) => h('article', { class: `persona${p.trust === 'none' ? ' unv' : ''}` },
      h('div', { class: 'hd' },
        h('div', { class: 'avatar', 'aria-hidden': 'true' }, initials(p.title)),
        h('div', { class: 'who' }, h('a', { href: `#/kb/${p.path}` }, p.title), h('span', {}, p.fm.description || '')),
        trust(p.trust)),
      h('div', { class: 'lists' }, [['Goals', /^(objectifs|goals)\b/i], ['Frustrations', /^(pain points|frustrations)\b/i]].map(([label, rx]) => {
        const items = listUnder(p.body, rx);
        return h('div', {}, cap(label), items.length ? items.map((x) => h('div', { class: 'dash' }, x)) : none('Not documented'));
      })),
      h('div', { class: 'ft' }, p.path, p.by ? h('span', { class: 'end' }, actor(p.by), p.byAt ? ` · ${fd(p.byAt)}` : '') : null))))
      : none('No persona. Run /hosa in Claude Code to create them from the target audience.')));
}

// --- Board ----------------------------------------------------------------------------

const boardFilter = { sprint: 'all', by: 'all', trust: 'all' };

function card(t) {
  return h('article', {
    class: `card${t.trust === 'none' ? ' unv' : ''}`, draggable: 'true',
    onclick: (e) => { if (!e.target.closest('a')) location.hash = `#/kb/${t.path}`; },
    ondragstart: (e) => { e.dataTransfer.setData('text/plain', t.path); e.currentTarget.classList.add('dragging'); },
    ondragend: (e) => e.currentTarget.classList.remove('dragging'),
  },
  h('div', { class: 'top' }, h('span', { class: 'num' }, num(t)), prio(t.fm.priority)),
  h('a', { class: 'ttl', href: `#/kb/${t.path}`, style: 'text-decoration:none' }, t.title),
  t.state === 'blocked' && t.fm.description ? h('div', { class: 'why' }, t.fm.description) : null,
  est(t) || t.fm.sprint ? h('div', { class: 'tags' },
    est(t) ? h('span', { class: 'tag' }, est(t)) : null,
    t.fm.sprint ? h('span', { class: 'tag o' }, t.fm.sprint) : null) : null,
  h('div', { class: 'foot' }, actor(t.by), trust(t.trust)));
}

function column(state, cards) {
  return h('section', {
    class: `col s-${state}`, 'aria-label': STATES[state],
    ondragover: (e) => { e.preventDefault(); e.currentTarget.classList.add('over'); },
    ondragleave: (e) => e.currentTarget.classList.remove('over'),
    ondrop: (e) => {
      e.preventDefault();
      e.currentTarget.classList.remove('over');
      const t = store.byPath[e.dataTransfer.getData('text/plain')];
      if (t) moveTicket(t, state);
    },
  },
  h('header', {}, sdot(state), h('b', {}, STATES[state]), h('span', { class: 'n' }, cards.length), h('span', { class: 'pts' }, `${sum(cards)} pts`)),
  cards.length ? cards.map(card) : h('div', { class: 'empty' }, state === 'todo' ? 'No tickets. /backlog creates them.' : 'No tickets'));
}

function renderBoard() {
  const f = boardFilter;
  const tickets = store.concepts.filter(isTicket);
  const sprints = [...new Set(tickets.map((t) => t.fm.sprint).filter(Boolean))].sort();
  const shown = tickets.filter((t) => (f.sprint === 'all' || (f.sprint === '-' ? !t.fm.sprint : t.fm.sprint === f.sprint))
    && (f.by === 'all' || (f.by === 'human') === (!!t.by && kindOf(t.by) === 'human'))
    && (f.trust === 'all' || t.trust === f.trust));
  const chips = (label, key, opts) => h('div', {}, h('span', { class: 'lbl' }, label),
    opts.map(([v, l, dot]) => chip(l, f[key] === v, () => { f[key] = v; renderBoard(); }, dot)));

  view().replaceChildren(h('div', { class: 'page', style: 'max-width:none;padding:20px 24px 32px;gap:16px' },
    head('Board', h('span', { class: 'sum' }, `tickets/ · ${shown.length} tickets · ${sum(shown)} pts`)),
    h('div', { class: 'chips' },
      chips('Sprint', 'sprint', [['all', 'All'], ...sprints.map((s) => [s, s]), ['-', 'Backlog']]),
      chips('Requested by', 'by', [['all', 'All'], ['human', 'Human'], ['agent', 'Agent']]),
      chips('Trust', 'trust', [['all', 'All'], ...Object.keys(TRUST).map((t) => [t, TRUST[t].short, tdot(t)])])),
    h('div', { class: 'board' }, Object.keys(STATES).map((s) => column(s, shown.filter((t) => t.state === s).sort(byPrio))))));
}

// --- Sprints --------------------------------------------------------------------------

let sprintSel = null;

function renderSprints() {
  const tickets = store.concepts.filter(isTicket);
  const sprints = [...store.overview.sprints].sort((a, b) => a.slug.localeCompare(b.slug, undefined, { numeric: true }));
  if (!sprints.length) {
    return view().replaceChildren(h('div', { class: 'page' }, head('Sprints'),
      none('No sprint yet. Run /sprint in Claude Code to plan one from the backlog.')));
  }
  const cur = sprints.find((s) => s.slug === sprintSel) || sprints.find((s) => s.state === 'active') || sprints[0];
  const of = (s) => tickets.filter((t) => t.fm.sprint === s.slug);
  const doneOf = (s) => sum(of(s).filter((t) => t.state === 'done'));
  const order = ['blocked', 'doing', 'todo', 'done'];
  const ts = of(cur).sort((a, b) => order.indexOf(a.state) - order.indexOf(b.state) || byPrio(a, b));
  const committed = sum(ts);
  const done = doneOf(cur);
  const closed = sprints.filter((s) => s.state === 'done').map(doneOf);
  const avg = closed.length ? closed.reduce((a, b) => a + b, 0) / closed.length : 0;
  const open = sum(tickets.filter((t) => t.state !== 'done'));
  const capacity = store.byPath[cur.path]?.fm.capacity;
  const maxC = Math.max(1, ...sprints.map((s) => sum(of(s))));
  const stat = (k, v, s) => h('div', {}, cap(k), h('span', { class: 'v' }, v), h('span', { class: 's' }, s));

  view().replaceChildren(h('div', { class: 'page' },
    h('header', { class: 'page-head', style: 'align-items:center' },
      h('h1', {}, 'Sprints'),
      h('div', { style: 'display:flex;gap:4px;margin-left:8px;flex-wrap:wrap' }, sprints.map((s) =>
        chip(`${s.title}${s.state === 'active' ? ' · current' : ''}`, s === cur, () => { sprintSel = s.slug; renderSprints(); })))),
    h('div', { class: 'stats' },
      stat('Committed', `${committed} pts`, `${ts.length} tickets${capacity != null ? ` · capacity ${capacity}` : ''}`),
      stat('Done', `${done} pts`, committed ? `${Math.round((done / committed) * 100)}% of commitment` : 'Nothing estimated'),
      stat(cur.state === 'done' ? 'Carried over' : 'Remaining', `${committed - done} pts`, SPRINT_STATES[cur.state] || cur.state),
      stat('Avg velocity', `${avg.toFixed(1)} pts`, avg ? `Open backlog ${open} pts ≈ ${(open / avg).toFixed(1)} sprints` : 'No closed sprint yet')),
    h('section', { class: 'panel' },
      h('h2', { class: 'sub' }, 'Velocity'),
      h('div', { class: 'velo' }, sprints.map((s) => {
        const c = sum(of(s));
        const d = doneOf(s);
        return h('div', {}, `${d}/${c}`,
          h('div', { class: `outer${s === cur ? ' cur' : ''}`, style: `height:${(c / maxC) * 110}px` },
            h('div', { class: 'inner', style: `height:${c ? (d / c) * 100 : 0}%` })));
      })),
      h('div', { class: 'velo-lbl' }, sprints.map((s) => h('span', {}, s.slug))),
      h('span', { class: 's muted' }, 'Done / committed points. S=1, M=3, L=5.')),
    h('section', { class: 'tlist' },
      h('h2', { class: 'sub', style: 'margin-bottom:8px' }, 'Tickets in ', h('a', { href: `#/kb/${cur.path}` }, cur.title)),
      cur.branch ? h('p', { class: 'muted', style: 'margin:0 0 8px' }, 'Branch ', h('code', {}, cur.branch)) : null,
      ts.length ? ts.map((t) => h('a', { class: 'trow', href: `#/kb/${t.path}` },
        sdot(t.state), h('span', { class: 'num' }, num(t)), h('span', {}, t.title), prio(t.fm.priority) || h('span'),
        h('span', { class: 'mono', style: 'font-size:11px;color:var(--ink3)' }, est(t) || ''), actor(t.by) || h('span'), trust(t.trust)))
        : none('No ticket in this sprint.'))));
}

// --- Knowledge ------------------------------------------------------------------------

const KB_RESET = { q: '', type: '', tag: '', status: '', trust: '' };
const kbFilter = { folder: '', ...KB_RESET };

function wireInternalLinks(container, basePath) {
  container.addEventListener('click', (e) => {
    const a = e.target.closest('a[href]');
    const href = a && a.getAttribute('href');
    if (!href || /^[a-z]+:|^#/i.test(href) || !href.split('#')[0].endsWith('.md')) return;
    e.preventDefault();
    const resolved = new URL(href, `http://kb/${basePath}`).pathname.slice(1);
    location.hash = `#/kb/${decodeURIComponent(resolved)}`;
  });
}

function facts(t) {
  const sel = h('select', { class: 'sel', 'aria-label': 'State', onchange: (e) => moveTicket(t, e.target.value) },
    Object.entries(STATES).map(([v, l]) => h('option', { value: v }, l)));
  sel.value = t.state;
  const fact = (k, v) => h('div', {}, cap(k), h('span', { class: 'v' }, v));
  return h('div', { class: 'facts' },
    fact('State', [sdot(t.state), sel]),
    fact('Priority', t.fm.priority != null ? `P${t.fm.priority}` : '—'),
    fact('Estimate', est(t) || '—'),
    fact('Sprint', t.fm.sprint || 'Backlog'));
}

function detail(c, full) {
  const body = h('div', { class: 'prose' });
  body.innerHTML = full.bodyHtml; // assaini côté serveur (nh3)
  wireInternalLinks(body, c.path);
  const on = (at) => (at ? ` on ${fd(at)}` : '');
  const sentence = {
    human: `Validated by ${c.ver}${on(c.verAt)}.`,
    machine: `Checked by ${c.ver}${on(c.verAt)}. No human has reviewed it.`,
    none: `${c.by ? `Generated by ${c.by}${on(c.byAt)}` : 'No author recorded'}. Nobody has validated it yet.`,
  }[c.trust];
  const who = (id, at) => id && [actor(id, true), h('span', { class: 'when' }, `${KIND[kindOf(id)][1]}${at ? ` · ${fd(at)}` : ''}`)];
  const cell = (label, content, empty) => h('div', {}, cap(label), content || none(empty));
  const sources = [].concat(c.fm.sources || []).map(String);
  const rel = c.links.map((p) => store.byPath[p]).filter(Boolean);
  const back = store.concepts.filter((x) => x.links.includes(c.path) && !c.links.includes(x.path));
  const relGroup = (label, xs) => h('div', {}, cap(label), xs.length
    ? xs.map((x) => h('a', { href: `#/kb/${x.path}` }, tdot(x.trust), h('span', { class: 't' }, x.title), h('span', { class: 'ty' }, x.type)))
    : none('None'));
  const hist = store.activity.filter((e) => e.path === c.path);

  return h('article', { class: 'detail' },
    h('div', { class: 'bar' },
      h('span', { class: 'path' }, c.path), h('span', { class: 'type' }, c.type), statusPill(c.status),
      h('button', { type: 'button', class: 'btn sm', onclick: () => { location.hash = `#/kb/${c.path}?edit`; } }, 'Edit')),
    h('h1', { class: 'title' }, c.title),
    isTicket(c) ? facts(c) : null,
    h('section', { class: 'prov' },
      h('div', { class: `head t-${c.trust}` },
        tdot(c.trust, true),
        h('div', { class: 'txt' }, h('b', { class: `c-${c.trust}` }, TRUST[c.trust].label), h('span', {}, sentence)),
        c.trust !== 'human' ? verifyBtn(c, 'btn dark', localStorage.getItem('hosa.me') ? `Verify as ${localStorage.getItem('hosa.me')}` : 'Verify') : null),
      h('div', { class: 'cells' },
        cell('Generated by', who(c.by, c.byAt), 'Not recorded'),
        cell('Verified by', who(c.ver, c.verAt), 'Not verified'),
        cell('Sources', sources.length && sources.map((s) => {
          const x = store.byPath[s] || store.byPath[`${s}.md`];
          return x ? h('a', { class: 'src', href: `#/kb/${x.path}` }, s) : h('span', { class: 'src' }, s);
        }), 'None recorded'))),
    body,
    h('div', { class: 'rel' }, relGroup('Links to', rel), relGroup('Referenced by', back)),
    h('div', { class: 'hist' },
      cap(`History · ${c.folder === '.' ? '' : `${c.folder}/`}log.md`),
      hist.length ? hist.map((e) => h('div', { class: 'e' }, h('span', { class: 'when' }, fd(e.date)), actor(e.actor) || h('span'), logText(e)))
        : none('No entries yet')));
}

function editor(c) {
  const fmInput = h('textarea', { spellcheck: 'false', rows: 12 });
  fmInput.value = c.frontmatterYaml;
  const bodyInput = h('textarea', { rows: 24 });
  bodyInput.value = c.body;
  const preview = h('div', { class: 'prose preview', 'aria-live': 'polite' });
  preview.innerHTML = c.bodyHtml; // assaini côté serveur (nh3)
  let timer;
  bodyInput.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      try { preview.innerHTML = (await api('render', { method: 'POST', json: { body: bodyInput.value } })).html; } catch { /* aperçu best-effort */ }
    }, 300);
  });
  const status = h('p', { class: 'form-error', role: 'alert' });
  const leave = () => { location.hash = `#/kb/${c.path}`; };
  const save = async (e) => {
    e.preventDefault();
    try {
      await api(`concepts/${encodePath(c.path)}`, { method: 'PUT', json: { frontmatter: fmInput.value, body: bodyInput.value } });
      await load(true);
      toast('Changes saved');
      leave();
    } catch (err) {
      status.textContent = err.message;
    }
  };
  return h('form', { class: 'editor', onsubmit: save, onkeydown: (e) => { if ((e.ctrlKey || e.metaKey) && e.key === 's') save(e); } },
    h('div', { class: 'bar' },
      h('span', { class: 'path' }, c.path),
      h('div', { class: 'actions' },
        h('button', { type: 'button', class: 'btn', onclick: leave }, 'Cancel'),
        h('button', { type: 'submit', class: 'btn dark' }, 'Save'))),
    h('h1', { class: 'title', style: 'font:500 26px var(--serif)' }, `Edit ${c.frontmatter.title || c.path}`),
    status,
    h('label', {}, h('span', {}, 'Frontmatter ', h('span', { class: 'muted' }, '— YAML; the type cannot change')), fmInput),
    h('div', { class: 'split' },
      h('label', {}, h('span', {}, 'Content ', h('span', { class: 'muted' }, '— Markdown')), bodyInput),
      h('div', { class: 'field' }, h('span', {}, 'Preview'), preview)));
}

async function renderKb(path, editing) {
  const f = kbFilter;
  const cs = store.concepts;
  const sel = path && store.byPath[path];
  const matches = (c) => (!f.folder || c.folder === f.folder) && (!f.type || c.type === f.type) && (!f.tag || c.tags.includes(f.tag))
    && (!f.status || c.status === f.status) && (!f.trust || c.trust === f.trust)
    && (!f.q || `${c.title} ${c.path}`.toLowerCase().includes(f.q.toLowerCase()));
  // Arrivée sur un concept masqué par les filtres (lien depuis une autre vue) : on montre son dossier.
  if (sel && !matches(sel)) Object.assign(f, KB_RESET, { folder: sel.folder });
  const shown = () => cs.filter(matches).sort((a, b) => last(b).localeCompare(last(a)));
  const current = path || shown()[0]?.path;

  const folders = [...new Set(cs.map((c) => c.folder))].sort();
  const count = h('span', { class: 'muted' });
  const clear = h('button', { type: 'button', class: 'linkbtn', onclick: () => { Object.assign(f, KB_RESET); renderKb(path, editing); } }, 'Clear filters');
  const rows = h('div', { class: 'rows' });
  const refill = () => {
    const list = shown();
    count.textContent = `${list.length} concepts`;
    clear.hidden = !(f.q || f.type || f.tag || f.status || f.trust);
    rows.replaceChildren(...(list.length ? list.map((c) => h('a', { class: 'row', href: `#/kb/${c.path}`, 'aria-current': c.path === current ? 'page' : null },
      h('span', { class: 'ic' }, tdot(c.trust)),
      h('span', { class: 'body' },
        h('span', { class: `ttl${c.status === 'deprecated' ? ' dep' : ''}` }, c.title),
        h('span', { class: 'path' }, c.path),
        h('span', { class: 'meta' }, h('span', { class: 'type' }, c.type), statusPill(c.status), h('span', { class: 'date' }, fd(last(c)))))))
      : [h('div', { class: 'empty' }, 'No concept matches these filters.')]));
  };
  const setFolder = (v) => { f.folder = v; renderKb(path, editing); };
  const filterSel = (key, opts, label) => select(f[key], (v) => { f[key] = v; refill(); }, opts, label);

  let pane = none('Empty knowledge base. Create a concept with N.');
  if (current) {
    try {
      const full = await api(`concepts/${encodePath(current)}`);
      pane = editing ? editor(full) : detail(store.byPath[current] || deco(full), full);
    } catch {
      pane = h('p', { class: 'empty' }, `Concept not found: ${current}`);
    }
  }

  const scroll = document.querySelector('.rows')?.scrollTop;
  view().replaceChildren(h('div', { class: 'kb' },
    h('nav', { class: 'kb-folders', 'aria-label': 'Folders' }, cap('Folders'),
      [['', 'all', cs.length], ...folders.map((x) => [x, `${x}/`, cs.filter((c) => c.folder === x).length])].map(([k, label, n]) =>
        h('a', { href: '#/kb', 'aria-current': f.folder === k ? 'true' : null, onclick: (e) => { e.preventDefault(); setFolder(k); } }, label, h('span', { class: 'n' }, n)))),
    h('div', { class: 'kb-list' },
      h('div', { class: 'kb-tools' },
        h('div', { class: 'hd' }, h('h1', {}, f.folder ? `${f.folder}/` : 'all'), count, clear),
        h('div', { class: 'folder-sel' }, select(f.folder, setFolder, [['', 'All folders'], ...folders.map((x) => [x, `${x}/`])], 'Folder')),
        h('input', { type: 'search', value: f.q, placeholder: 'Filter by title or path', 'aria-label': 'Filter', oninput: (e) => { f.q = e.target.value; refill(); } }),
        h('div', { class: 'grid' },
          filterSel('type', [['', 'All types'], ...[...new Set(cs.map((c) => c.type))].sort().map((t) => [t, t])], 'Type'),
          filterSel('tag', [['', 'All tags'], ...[...new Set(cs.flatMap((c) => c.tags))].sort().map((t) => [t, `#${t}`])], 'Tag'),
          filterSel('status', [['', 'Any status'], ['draft', 'draft'], ['stable', 'stable'], ['deprecated', 'deprecated']], 'Status'),
          filterSel('trust', [['', 'Any trust'], ...Object.keys(TRUST).map((t) => [t, TRUST[t].label])], 'Trust'))),
      rows),
    h('div', { class: 'pane' }, pane)));
  refill();
  if (scroll) rows.scrollTop = scroll;
}

// --- Journal --------------------------------------------------------------------------

const jFilter = { actor: '', folder: '' };

function renderJournal() {
  const all = store.activity;
  const actors = [...new Set(all.map((e) => e.actor).filter(Boolean))].sort();
  const folders = [...new Set(all.map((e) => e.bundle || '.'))].sort();
  const shown = all.filter((e) => (!jFilter.actor || e.actor === jFilter.actor) && (!jFilter.folder || (e.bundle || '.') === jFilter.folder));
  const days = [];
  for (const e of shown) {
    if (days.at(-1)?.date !== e.date) days.push({ date: e.date, entries: [] });
    days.at(-1).entries.push(e);
  }
  const t = today();
  const yesterday = new Date(Date.now() - 864e5).toLocaleDateString('en-CA');
  const label = (d) => (d === t ? 'Today' : d === yesterday ? 'Yesterday' : new Date(`${d}T12:00:00`).toLocaleDateString('en-GB', { weekday: 'long' }));
  const refilter = (key) => (v) => { jFilter[key] = v; renderJournal(); };

  view().replaceChildren(h('div', { class: 'page', style: 'max-width:900px;gap:18px' },
    h('header', { class: 'page-head', style: 'align-items:center' },
      h('h1', {}, 'Journal'),
      h('span', { class: 'sum' }, `${shown.length} entries from ${new Set(all.map((e) => e.bundle)).size} log.md files`),
      h('div', { style: 'margin-left:auto;display:flex;gap:6px' },
        select(jFilter.actor, refilter('actor'), [['', 'All actors'], ...actors.map((a) => [a, a])], 'Actor'),
        select(jFilter.folder, refilter('folder'), [['', 'All folders'], ...folders.map((x) => [x, `${x}/`])], 'Folder'))),
    days.length ? days.map((d) => h('section', { class: 'jday' },
      h('div', { class: 'd' }, h('b', {}, label(d.date)), h('span', {}, `${fd(d.date)} ${d.date.slice(0, 4)}`)),
      h('div', { class: 'es' }, d.entries.map((e) => h('div', { class: 'e' },
        h('div', { class: 'top' }, actor(e.actor), logText(e)),
        h('span', { class: 'f' }, `${e.bundle ? `${e.bundle}/` : ''}log.md`))))))
      : h('div', { class: 'empty' }, 'No entries for this filter.')));
}

// --- Graphe -------------------------------------------------------------------------------

const GKIND = { file: 'File', class: 'Class', function: 'Function', method: 'Method', ticket: 'Ticket', exigence: 'Requirement' };
const gLink = (n) => (n.kb ? `#/kb/${n.kb}` : `#/graph/${encodeURIComponent(n.id)}`);
const gLoc = (n) => (n.line ? `${n.file}:${n.line}` : n.file || '');

function gItem(n, extra) {
  return h('a', { class: 'g-item', href: gLink(n) },
    h('span', { class: `g-kind k-${n.kind}` }, GKIND[n.kind]),
    h('span', { class: 'g-label' }, n.label),
    h('span', { class: 'g-loc' }, gLoc(n)),
    extra && h('span', { class: 'g-extra' }, extra));
}

// Voisinage en étoile : le nœud au centre, ses voisins directs en cercle, sans bibliothèque.
function gSvg(center, edges) {
  const R = 130, W = 420, H = 320, cx = W / 2, cy = H / 2;
  const seen = new Map();
  for (const e of edges) if (!seen.has(e.node.id)) seen.set(e.node.id, e);
  const around = [...seen.values()].slice(0, 16);
  const ns = 'http://www.w3.org/2000/svg';
  const el = (tag, attrs, text) => {
    const x = document.createElementNS(ns, tag);
    for (const [k, v] of Object.entries(attrs)) x.setAttribute(k, v);
    if (text) x.textContent = text;
    return x;
  };
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, class: 'g-svg', role: 'img', 'aria-label': `Neighbourhood of ${center.label}` });
  const short = (s) => (s.length > 22 ? `${s.slice(0, 21)}…` : s);
  around.forEach((e, i) => {
    const a = (2 * Math.PI * i) / around.length - Math.PI / 2;
    const x = cx + R * Math.cos(a), y = cy + R * 0.85 * Math.sin(a);
    svg.append(el('line', { x1: cx, y1: cy, x2: x, y2: y, class: `g-edge${e.conf === 'ambiguous' ? ' amb' : ''}` }));
    const g = el('a', { href: gLink(e.node) });
    g.append(el('circle', { cx: x, cy: y, r: 6, class: `k-${e.node.kind}` }), el('text', { x, y: y - 10, 'text-anchor': 'middle' }, short(e.node.label)));
    g.append(el('title', {}, `${e.rel} — ${e.node.id}`));
    svg.append(g);
  });
  svg.append(el('circle', { cx, cy, r: 9, class: `k-${center.kind} center` }), el('text', { x: cx, y: cy + 24, 'text-anchor': 'middle', class: 'center' }, short(center.label)));
  return svg;
}

function gGroups(edges, arrow) {
  const rels = [...new Set(edges.map((e) => e.rel))].sort();
  return rels.map((rel) => h('section', { class: 'g-group' },
    cap(`${arrow} ${rel}`),
    edges.filter((e) => e.rel === rel).map((e) => gItem(e.node, [e.line ? `L${e.line}` : '', e.conf === 'ambiguous' ? 'ambiguous' : ''].filter(Boolean).join(' ')))));
}

async function renderGraph(rest) {
  const id = rest && rest !== 'trace' ? rest : null; // route() a déjà décodé le hash
  const results = h('div', { class: 'g-results' });
  const search = h('input', { type: 'search', class: 'g-search', placeholder: 'File, function, ticket, requirement…', 'aria-label': 'Search the graph' });
  let timer;
  search.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const q = search.value.trim();
      if (!q) return results.replaceChildren();
      try {
        const found = await api(`graph/find?q=${encodeURIComponent(q)}`);
        results.replaceChildren(...(found.length ? found.map((n) => gItem(n, n.doc)) : [h('div', { class: 'empty' }, 'No match.')]));
      } catch (err) {
        results.replaceChildren(h('div', { class: 'empty' }, err.message));
      }
    }, 200);
  });

  let body;
  try {
    if (rest === 'trace') body = gTrace(await api('graph/trace'));
    else if (id) body = gCard(await api(`graph/node?id=${encodeURIComponent(id)}`));
    else body = h('div', { class: 'empty' }, 'Search for an element, or open the traceability view.');
  } catch (err) {
    body = h('div', { class: 'empty' }, err.message);
  }
  view().replaceChildren(h('div', { class: 'page', style: 'gap:18px' },
    h('header', { class: 'page-head', style: 'align-items:center' },
      h('h1', {}, 'Graph'),
      h('div', { style: 'margin-left:auto;display:flex;gap:6px' },
        h('a', { class: 'btn sm', href: '#/graph', 'aria-current': rest ? null : 'page' }, 'Explore'),
        h('a', { class: 'btn sm', href: '#/graph/trace', 'aria-current': rest === 'trace' ? 'page' : null }, 'Traceability'))),
    rest === 'trace' ? null : search, results, body));
  if (rest !== 'trace') search.focus();
}

function gCard(d) {
  const n = d.node;
  const a = d.affected;
  return h('div', { class: 'g-card' },
    h('div', { class: 'g-head' },
      h('span', { class: `g-kind k-${n.kind}` }, GKIND[n.kind]),
      h('h2', { class: 'mono' }, n.label),
      h('span', { class: 'g-loc' }, gLoc(n)),
      n.state || n.status ? h('span', { class: 'g-extra' }, n.state || n.status) : null),
    n.doc ? h('p', { class: 'g-doc' }, n.doc) : null,
    h('div', { class: 'g-cols' },
      gSvg(n, [...d.out, ...d.in]),
      h('div', { class: 'g-rels' },
        gGroups(d.out, '→'), gGroups(d.in, '←'),
        !d.out.length && !d.in.length ? h('div', { class: 'none' }, 'No relation.') : null)),
    h('section', { class: 'g-group' }, cap(`Impact (depth 2) — ${a.nodes.length} dependents`),
      a.nodes.length ? a.nodes.map((x) => gItem(x.node, `depth ${x.depth}`)) : h('div', { class: 'none' }, 'Nothing depends on it.')),
    h('section', { class: 'g-group' }, cap('Tickets touching the impacted files'),
      a.tickets.length ? a.tickets.map((t) => gItem(t, t.state)) : h('div', { class: 'none' }, 'None.')));
}

function gTrace(rows) {
  if (!rows.length) return h('div', { class: 'empty' }, 'No requirement in the knowledge base.');
  return h('div', { class: 'g-trace' }, rows.map((r) => {
    const orphan = r.node.status === 'stable' && !r.tickets.some((t) => t.files.length);
    return h('section', { class: `g-req${orphan ? ' orphan' : ''}` },
      gItem(r.node, orphan ? 'stable, no code linked' : r.node.status),
      r.tickets.length ? r.tickets.map((t) => h('div', { class: 'g-ticket' },
        gItem(t.node, t.node.state),
        h('div', { class: 'g-files' }, t.files.length ? t.files.map((f) => gItem(f)) : h('span', { class: 'none' }, 'No file linked yet.'))))
        : h('div', { class: 'none g-ticket' }, 'No ticket.'));
  }));
}

// --- Nouveau concept --------------------------------------------------------------------

const dialog = document.getElementById('new-dialog');
const form = document.getElementById('new-form');
const touched = { slug: false, type: false };
let tried = false;

// Type dominant d'un dossier : pré-remplit le type quand on choisit un dossier connu.
function typeIn(folder) {
  const n = {};
  for (const c of store.concepts) if (c.folder === folder) n[c.type] = (n[c.type] || 0) + 1;
  return Object.keys(n).sort((a, b) => n[b] - n[a])[0] || '';
}

const bundleOf = () => form.elements.bundle.value.trim().replace(/^\/+|\/+$/g, '');

function validate() {
  const el = form.elements;
  const bundle = bundleOf();
  const slug = el.slug.value;
  document.getElementById('prefix').textContent = `${bundle || '…'}/`;
  let slugErr = '';
  let suggestion = '';
  if (!slug) slugErr = tried ? 'Slug is required.' : '';
  else if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) { slugErr = 'Use lowercase letters, digits and single hyphens.'; suggestion = slugify(slug); }
  else if (store.byPath[`${bundle}/${slug}.md`]) slugErr = `${bundle}/${slug}.md already exists.`;
  const hints = {
    bundle: tried && !bundle ? ['Choose a folder.', true] : [bundle && !store.concepts.some((c) => c.folder === bundle) ? 'New folder. It will be created with its own log.md.' : ''],
    type: [tried && !el.type.value.trim() ? 'Type is required.' : '', true],
    title: [tried && !el.title.value.trim() ? 'Title is required.' : '', true],
    slug: slugErr ? [slugErr, true] : ['Lowercase letters, digits and hyphens.'],
  };
  for (const [k, [msg, isErr]] of Object.entries(hints)) {
    const hint = form.querySelector(`[data-for=${k}]`);
    hint.className = `hint${isErr && msg ? ' err' : ''}`;
    hint.replaceChildren(msg, ...(k === 'slug' && suggestion && suggestion !== slug
      ? [' ', h('button', { type: 'button', onclick: () => { el.slug.value = suggestion; validate(); } }, `Use ${suggestion}`)] : []));
    (k === 'slug' ? el.slug.parentElement : el[k]).classList.toggle('bad', !!(isErr && msg));
  }
  return !!(bundle && el.type.value.trim() && el.title.value.trim() && slug && !slugErr);
}

async function openNew() {
  await load();
  const folders = [...new Set(store.concepts.map((c) => c.folder))].filter((f) => f !== '.').sort();
  document.getElementById('bundles').replaceChildren(...folders.map((f) => h('option', { value: f }, typeIn(f))));
  document.getElementById('types').replaceChildren(...[...new Set(store.concepts.map((c) => c.type))].sort().map((t) => h('option', { value: t })));
  form.reset();
  form.querySelector('.form-error').textContent = '';
  tried = false;
  touched.slug = touched.type = false;
  validate();
  dialog.showModal();
}

form.addEventListener('input', (e) => {
  const el = form.elements;
  if (e.target === el.slug) touched.slug = true;
  if (e.target === el.type) touched.type = true;
  if (e.target === el.title && !touched.slug) el.slug.value = slugify(el.title.value);
  if (e.target === el.bundle && !touched.type) el.type.value = typeIn(bundleOf());
  validate();
});
form.querySelector('[value=cancel]').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', (e) => { if (e.target === dialog) dialog.close(); }); // clic sur le fond
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  tried = true;
  if (!validate()) return;
  const data = { ...Object.fromEntries(new FormData(form)), bundle: bundleOf() };
  try {
    const c = await api('concepts', { method: 'POST', json: data });
    dialog.close();
    await load(true);
    toast(`“${data.title}” created`);
    location.hash = `#/kb/${c.path}?edit`;
  } catch (err) {
    form.querySelector('.form-error').textContent = err.message;
  }
});
document.getElementById('new').addEventListener('click', openNew);

// --- Routage ----------------------------------------------------------------------------

async function route() {
  const [path, query] = decodeURIComponent(location.hash.slice(1) || '/').split('?');
  const section = path.split('/')[1] || '';
  showError('');
  try {
    await load();
    for (const a of document.querySelectorAll('[data-nav]')) {
      if (a.dataset.nav === section) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    }
    if (section === 'kb') await renderKb(path.slice('/kb/'.length) || null, query === 'edit');
    else if (section === 'graph') await renderGraph(path.slice('/graph/'.length) || null);
    else ({ steering: renderSteering, personas: renderPersonas, board: renderBoard, sprints: renderSprints, journal: renderJournal }[section] || renderHome)();
  } catch (err) {
    showError(`Could not load: ${err.message}. Is the Hosa server still running?`);
  }
}

window.addEventListener('keydown', (e) => {
  if (e.target.closest?.('input, select, textarea') || e.metaKey || e.ctrlKey || e.altKey || dialog.open) return;
  const v = VIEWS[+e.key - 1];
  if (v) location.hash = `#/${v[0]}`;
  else if (e.key === 'n' || e.key === 'N') { e.preventDefault(); openNew(); }
});
document.getElementById('refresh').addEventListener('click', async () => {
  await load(true).catch(() => {});
  await route();
  toast('KB reloaded');
});
window.addEventListener('hashchange', route);
route();
