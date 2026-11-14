'use strict';
// Hosa — tableau de bord. SPA native, routage par le hash, aucune ressource réseau, aucun appel à Claude :
// les remarques pour Claude sont des fichiers de la KB que la fiche de reprise lui donne.

const $ = (id) => document.getElementById(id);
const S = { concepts: [], ov: null, activity: [], kbStatus: undefined, usage: undefined, cov: undefined, loadedAt: null, err: null, target: null };

// --- utilitaires -------------------------------------------------------------------------
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'class') el.className = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  el.append(...kids.flat(Infinity).filter((c) => c != null && c !== false));  // texte seulement : jamais d'innerHTML ici
  return el;
}
const store = {
  get: (k, s = 'local') => { try { return window[`${s}Storage`].getItem(k); } catch (e) { return null; } },
  set: (k, v, s = 'local') => { try { window[`${s}Storage`].setItem(k, v); } catch (e) { /* stockage bloqué : sans effet */ } },
  del: (k) => { try { localStorage.removeItem(k); } catch (e) { /* idem */ } },
};
async function api(path, options = {}) {
  const init = { ...options };
  if (options.json) { init.body = JSON.stringify(options.json); init.headers = { 'Content-Type': 'application/json' }; }
  const res = await fetch(`/api/${path}`, init);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(data.error || `erreur ${res.status}`), { status: res.status, data });
  return data;
}
const enc = (p) => p.split('/').map(encodeURIComponent).join('/');
const fmtDate = (s) => { const d = new Date(s); return isNaN(d) ? '—' : d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' }); };
const fmtDay = (s) => { const d = new Date(s); return isNaN(d) ? '—' : d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' }); };
const isoDay = (s) => String(s || '').split('-').reverse().join('/');
const fmtNum = (x) => Number(x || 0).toLocaleString('fr-FR', { maximumFractionDigits: 1 });
const fmtTime = (d) => d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
const fmtUsd = (x) => Number(x || 0).toLocaleString('fr-FR', { style: 'currency', currency: 'USD', minimumFractionDigits: x > 0 && x < 0.1 ? 3 : x < 100 ? 2 : 0, maximumFractionDigits: x > 0 && x < 0.1 ? 3 : x < 100 ? 2 : 0 });
const fmtTok = (x) => x >= 1e6 ? `${fmtNum(x / 1e6)} M` : x >= 1e3 ? `${fmtNum(x / 1e3)} k` : String(Math.round(x || 0));
const plural = (n, one, many) => `${n} ${n > 1 ? many : one}`;
const norm = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
const ago = (s) => {
  const d = new Date(s); if (isNaN(d)) return '—';
  const m = Math.round((Date.now() - d) / 60000);
  return m < 1 ? 'à l’instant' : m < 60 ? `il y a ${m} min` : m < 1440 ? `il y a ${Math.round(m / 60)} h` : m < 2880 ? 'hier' : fmtDay(s);
};
let toastTimer;
function toast(msg) { const t = $('toast'); t.textContent = msg; t.className = 'show'; clearTimeout(toastTimer); toastTimer = setTimeout(() => (t.className = ''), 3800); }
function copy(text) {
  const done = () => toast(`Copié : ${text} — collez-le dans Claude Code.`);
  if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, () => toast('Copie impossible : sélectionnez le texte.'));
  else toast('Copie impossible : sélectionnez le texte.');
}
// erreurs : jamais de chemin, de route ni de code technique à l'écran
const plain = (e) => { const m = String((e && e.message) || e || ''); return /[\\/`]|\.py|\.md|api|HTTP|json/i.test(m) || !m ? 'une erreur est survenue' : m; };
const errBox = (text, retry) => h('div', { class: 'alert err', role: 'alert' }, h('span', {}, text), retry ? h('button', { class: 'btn o s', type: 'button', onclick: reload }, 'Réessayer') : null);
const none = (text, ...extra) => h('p', { class: 'hint' }, text, ...extra);
const empty = (text, ...extra) => h('div', { class: 'empty' }, h('p', {}, text), ...extra);
const card = (title, ...kids) => h('section', { class: 'card' }, title ? h('h2', {}, title) : null, ...kids);
const cardH = (title, side, ...kids) => h('section', { class: 'card' }, h('div', { class: 'card-h' }, h('h2', {}, title), side), ...kids);
const pageH = (eyebrow, title, lead, ...extra) => h('header', { class: 'page-h' }, eyebrow ? h('div', { class: 'eyebrow' }, eyebrow) : null, h('h1', {}, title), lead ? h('p', { class: 'lead' }, lead) : null, ...extra);
const crumbs = (...parts) => h('nav', { class: 'crumbs', 'aria-label': 'Fil d’Ariane' }, parts.flatMap((p, i) => [i ? ' › ' : '', p[1] ? h('a', { href: `#${p[1]}` }, p[0]) : p[0]]));
const table = (head, rows, opts = {}) => h('div', { class: 'tw' }, h('table', {}, opts.caption ? h('caption', { class: 'vh' }, opts.caption) : null,
  h('thead', {}, h('tr', {}, head.map((x) => h('th', { scope: 'col', class: /^(Appels|Part|Coût|Tokens|Entrée|Sortie|Tours|Points)/.test(x) ? 'r' : null }, x)))), h('tbody', {}, rows)));
const td = (x, cls) => h('td', { class: cls || null }, x);
const secOf = (body, name) => ((String(body || '').split(new RegExp(`^## ${name}`, 'm'))[1] || '').split(/^## /m)[0] || '').trim();
const meter = (value, max, label, ok) => h('div', { class: 'meter', role: 'progressbar', 'aria-valuenow': value, 'aria-valuemin': 0, 'aria-valuemax': max || 0, 'aria-label': label },
  h('i', { class: ok && max && value >= max ? 'ok' : null, style: `width:${max ? Math.min(100, 100 * value / max) : 0}%` }));
const cmdBox = (skill) => h('div', { class: 'cmdbox' }, h('code', {}, `/${skill}`), h('button', { class: 'btn s', type: 'button', onclick: () => copy(`/${skill}`) }, 'Copier'));

// statut : toujours un mot, un symbole et une couleur
const ST = { 'à faire': ['a', '○'], 'en cours': ['e', '◐'], fait: ['f', '✓'], 'bloqué': ['b', '✕'], 'non applicable': ['a', '—'], ouverte: ['r', '◷'], 'fermée': ['f', '✓'] };
const st = (label, kind, sym) => { const [k, s] = ST[label] || [kind || 'a', sym || '']; return h('span', { class: `st ${kind || k}` }, h('span', { 'aria-hidden': 'true' }, sym ?? s), label); };
const TICKET = { todo: 'à faire', doing: 'en cours', done: 'fait', blocked: 'bloqué' };
const STATES = ['todo', 'doing', 'blocked', 'done'];
const ticketSt = (t) => st(TICKET[t.state] || 'à faire');
const stateName = (s) => TICKET[s].replace(/^./, (m) => m.toUpperCase());
const VERD = { PASS: ['réussi', 'f', '✓'], 'PASS-WITH-NOTES': ['réussi avec remarques', 'w', '✓'], FAIL: ['échoué', 'b', '✕'] };
const verdict = (v) => !v || !VERD[v] ? st('non testé', 'a', '○') : st(...VERD[v]);
const NATURE = { correction: 'À corriger', question: 'Question', idee: 'Idée' };
const remSt = (r) => r.etat === 'traitee' ? st('traitée par Claude', 'f', '✓') : st('en attente de Claude', 'r', '◷');

// --- données -------------------------------------------------------------------------------
const meta = (c) => {
  const fm = c.frontmatter || {};
  const by = fm.verified && fm.verified.by;
  return { ...c, fm, title: fm.title || c.path, type: fm.type, slug: c.path.replace(/^.*\//, '').replace(/\.md$/, ''),
    trust: !by ? 'none' : String(by).startsWith('human:') ? 'human' : 'machine', status: fm.status || 'stable',
    state: fm.state || 'todo', at: (fm.verified && fm.verified.at) || (fm.generated && fm.generated.at) };
};
const ofType = (t) => S.concepts.filter((c) => c.type === t);
const TIER = { human: 'humain', machine: 'machine', none: 'aucune' };
const agentLabel = (by) => { const b = String(by || ''); if (b.startsWith('human:')) return `vous (${b.slice(6)})`; if (b.startsWith('claude-code/')) return 'Claude'; if (b.startsWith('process:')) return 'Application'; const m = b.match(/^hosa-([a-z-]+)\//); return m ? `Claude · ${m[1].replace(/-/g, ' ')}` : b; };
const verifier = (by) => by && !String(by).startsWith('human:') ? 'contrôlé automatiquement' : by ? agentLabel(by) : 'personne pour l’instant';
function routeOf(path) {
  const c = S.concepts.find((x) => x.path === path);
  if (c && c.type === 'Ticket') return `#/tickets/${enc(path.replace(/\.md$/, ''))}`;
  if (c && c.type === 'Exigence') return `#/exigences/${encodeURIComponent(c.slug)}`;
  if (c && c.type === 'Persona') return `#/personas/${encodeURIComponent(c.slug)}`;
  return `#/kb/${enc(path)}`;
}
function kbPath(from, href) {
  if (!href || /^[a-z]+:|^#|^\//i.test(href) || !/\.md(#.*)?$/.test(href)) return null;
  const out = from.split('/').slice(0, -1);
  for (const seg of href.replace(/#.*$/, '').split('/')) { if (seg === '..') { if (!out.length) return null; out.pop(); } else if (seg && seg !== '.') out.push(seg); }
  return out.join('/');
}
const trustWord = (c) => c.trust === 'human' ? 'validé par vous' : c.trust === 'machine' ? 'contrôlé automatiquement' : 'à valider';
const trustSt = (c) => c.trust === 'human' ? st('validé par vous', 'f', '✓') : c.trust === 'machine' ? st('contrôlé automatiquement', 'e', '✓') : st('à valider', 'r', '○');
const byDate = (a, b) => String(b.at || '').localeCompare(String(a.at || ''));
const isAgent = (c) => c.status !== 'deprecated' && c.fm.generated && c.fm.generated.by && !String(c.fm.generated.by).startsWith('human:');
const waitsForYou = (c) => isAgent(c) && (c.trust !== 'human' || c.status !== 'stable');
const toValidate = () => S.concepts.filter(waitsForYou).sort(byDate);
const validated = () => S.concepts.filter((c) => isAgent(c) && c.trust === 'human' && c.status === 'stable').sort(byDate);
const isStable = (c) => c.fm.status === 'stable';
const statusSt = (c) => isStable(c) ? st('finalisée', 'f', '✓') : st('brouillon', 'a', '○');
const remarques = () => (S.ov && S.ov.remarques) || [];
const openRemarks = () => remarques().filter((r) => r.etat === 'ouverte');
const remarksOf = (path) => remarques().filter((r) => r.cible === path);
const recettes = () => (S.ov && S.ov.recettes) || [];
const projectTitle = () => (S.ov && S.ov.project && S.ov.project.frontmatter && S.ov.project.frontmatter.title) || 'le projet';
const next = () => S.ov && S.ov.plan && S.ov.plan.next;
const isClosed = (x) => ['fait', 'non applicable'].includes(x.status);
const sprintName = (slug) => { const x = ((S.ov && S.ov.sprints) || []).find((y) => y.slug === slug); return x ? x.title : slug ? slug.replace(/-/g, ' ').replace(/^./, (m) => m.toUpperCase()) : 'Backlog'; };
const activeSprint = () => (S.ov.sprints || []).find((s) => s.state === 'active') || null;
const ticketHref = (path) => `#/tickets/${enc(path.replace(/\.md$/, ''))}`;
const stemOf = (t) => t.path.replace(/^.*\//, '').replace(/\.md$/, '');
const recettesOf = (t) => S.concepts.filter((c) => /^test\//.test(c.path) && !/-technique\.md$/.test(c.path) && c.path.replace(/^.*\//, '').startsWith(stemOf(t) + '-'));
const proof = (t) => {
  if (!S.cov) return '…';
  if (S.cov.error) return 'Couverture indisponible';
  const v = t && S.cov[t.path];
  return v && v.plan && v.total ? `${v.couverts.length}/${v.total}` : 'non testé';
};
const recetteName = (r) => { if (!r.persona) return r.titre; const p = S.concepts.find((c) => c.path === `personnas/${r.persona}.md`); return p && p.fm.title ? `${r.titre} — ${String(p.fm.title).split(/[\s,]/)[0]}` : r.titre; };
// the first verdict of the last `## Revue` line that has one: a note may quote another (same rule as hooks/gate.js)
const reviewOf = (t) => {
  const sec = (String(t.body || '').split(/^## Revue[ \t]*$/m)[1] || '').split(/^## /m)[0];
  const v = sec.split(/\r?\n/).filter((l) => !/^\s*-\s*[^—\s]+\s*—\s*DÉCISION\b/.test(l)).map((l) => (/\b(PASS-WITH-NOTES|PASS|FAIL)\b/.exec(l) || [])[1]).filter(Boolean);
  return v.length ? v[v.length - 1] : null;
};
const roundEven = (x) => { const f = Math.floor(x), d = x - f; return d < 0.5 ? f : d > 0.5 ? f + 1 : f % 2 === 0 ? f : f + 1; };
const ACTEUR = { humain: 'Vous', processus: 'Application', agent: 'Claude' };
// le texte d'une ligne de log sans le nom de son acteur, déjà affiché à côté
const actText = (a) => { const t = a.acteurNom && a.text.startsWith(a.acteurNom) ? a.text.slice(a.acteurNom.length).trim() : a.text; return a.lien ? linkSlug(t, a.lien) : t; };
const linkSlug = (text, path) => { const slug = path.replace(/^.*\//, '').replace(/\.md$/, ''), i = text.indexOf(`\`${slug}\``);
  return i < 0 ? text : [text.slice(0, i), h('a', { href: routeOf(path) }, slug), text.slice(i + slug.length + 2)]; };

const F = (() => { try { return JSON.parse(store.get('hosa.filtres', 'session') || '{"periode":"7"}'); } catch (e) { return { periode: '7' }; } })();

async function load() {
  S.err = null;
  try {
    const [ov, cs, act] = await Promise.all([api('overview'), api('concepts'), api('activity')]);
    S.ov = ov; S.concepts = cs.map(meta); S.activity = act; S.loadedAt = new Date();
  } catch (e) { S.err = `Impossible de lire la KB : ${plain(e)}.`; }
  const [k, cov] = await Promise.all([api('kb-status').catch(() => null), api('couverture').catch((e) => ({ error: e }))]);
  S.kbStatus = k; S.cov = cov;
}
async function loadUsage() {
  const days = F.periode || '7';
  const u = await api(`usage?days=${days}`).catch((e) => ({ error: e }));
  if (days === (F.periode || '7')) S.usage = u;
}
// la consommation lit tous les transcripts (quelques secondes) : jamais attendue par le premier affichage ni par une écriture
const reload = async () => { await load(); route(); toast('KB relue'); S.usage = undefined; loadUsage().then(route); };

// --- filtres conservés d'un écran à l'autre --------------------------------------------------
const setF = (k, v) => {
  const typing = document.activeElement && document.activeElement.id === 'search';
  F[k] = v; store.set('hosa.filtres', JSON.stringify(F), 'session');
  if (k === 'periode') { S.usage = undefined; loadUsage().then(route); }
  route();
  const s = $('search'); if (typing && s) { s.focus(); s.setSelectionRange(s.value.length, s.value.length); }
};
const LABELS = { statut: 'Statut', sprint: 'Sprint', q: 'Recherche', verdict: 'Résultat', origine: 'Écrit par', validation: 'Validation', espace: 'Espace', persona: 'Persona', acteur: 'Acteur', dossier: 'Dossier', type: 'Type', tag: 'Étiquette', etat: 'État', nature: 'Nature' };
let qTimer;
function filterBar(keys, selects = {}, placeholder = 'Rechercher') {
  return h('div', { class: 'filters', role: 'search' },
    keys.includes('q') ? h('input', { id: 'search', type: 'search', 'aria-label': placeholder, placeholder: `${placeholder} ( / )`, value: F.q || '', oninput: (e) => { clearTimeout(qTimer); qTimer = setTimeout(() => setF('q', e.target.value), 250); } }) : null,
    ...Object.entries(selects).map(([k, vals]) => {
      const lbl = (vals.find(([v]) => v === F[k]) || [])[1] || F[k];
      return F[k] ? h('button', { class: 'chip', type: 'button', 'aria-label': `Retirer le filtre ${LABELS[k]}`, onclick: () => setF(k, '') }, `${LABELS[k]} : ${lbl}`, h('span', { 'aria-hidden': 'true' }, '✕'))
        : h('label', { class: 'flt' }, LABELS[k], h('select', { onchange: (e) => setF(k, e.target.value) }, h('option', { value: '' }, 'tous'), vals.map(([v, l]) => h('option', { value: v }, l))));
    }));
}
const clearBtn = (keys) => h('button', { class: 'btn o s', type: 'button', onclick: () => { for (const k of keys) F[k] = ''; setF(keys[0], ''); } }, 'Retirer les filtres');
const has = (hay) => !F.q || norm(hay).includes(norm(F.q));
const seg = (label, options, value, onpick) => h('div', { class: 'seg', role: 'group', 'aria-label': label },
  options.map(([v, l]) => h('button', { type: 'button', 'aria-pressed': String(v === value), onclick: () => onpick(v) }, l)));

// --- vue d'ensemble -------------------------------------------------------------------------
function hero() {
  const p = S.ov.plan, n = next();
  const box = (eyebrow, title, detail, skill, extra) => h('section', { class: 'hero', 'aria-label': 'Prochaine étape' },
    h('div', {}, h('div', { class: 'eyebrow' }, eyebrow), h('h2', {}, title), detail ? h('p', {}, detail) : null), cmdBox(skill), extra);
  if (!p) return box('Pour commencer', 'Pas encore de plan d’avancement', 'Lancez cette commande dans Claude Code : elle écrit le plan depuis la KB.', 'status');
  if (!n) return box('Prochaine étape', 'Toutes les étapes connues sont faites', 'Composez le sprint suivant à partir du backlog.', 'sprint');
  const g = n.gaps || [];
  return box(`Prochaine étape · ${n.section}`, n.stage, n.detail ? `Point de reprise : ${n.detail}` : 'Copiez la commande, puis collez-la dans Claude Code.', n.skill,
    g.length ? h('ul', { 'aria-label': 'Preuves manquantes' }, g.slice(0, 5).map((x) => h('li', {}, `Preuve manquante : ${x}`)), g.length > 5 ? h('li', {}, h('a', { href: '#/avancement', style: 'color:inherit' }, `et ${g.length - 5} autres`)) : null) : null);
}
const kpi = ({ label, value, unit, cmp, href, bar }) => h('a', { class: 'kpi', href },
  h('span', { class: 'l' }, label), h('span', { class: 'v' }, value, unit ? h('small', {}, ` ${unit}`) : null), bar || null, h('span', { class: 'c' }, cmp));
function delta(cur, prev, days) {
  if (prev == null) return 'période d’avant inconnue';
  if (!prev) return `rien les ${days} jours d’avant`;
  const pct = Math.round(100 * (cur - prev) / prev);
  return `${pct >= 0 ? '▲' : '▼'} ${Math.abs(pct)} % sur les ${days} jours d’avant`;
}
function kpis() {
  const ex = ofType('Exigence'), okEx = ex.filter((c) => c.trust === 'human').length, board = S.ov.board || [], sp = activeSprint(), u = S.usage;
  const done = board.filter((t) => t.state === 'done').length, blocked = board.filter((t) => t.state === 'blocked').length;
  return h('div', { class: 'kpis' },
    kpi({ label: 'Exigences validées', value: ex.length ? `${okEx}` : '—', unit: ex.length ? `/ ${ex.length}` : '', bar: ex.length ? meter(okEx, ex.length, 'Exigences validées', true) : null,
      cmp: ex.length ? `${ex.filter((c) => !isStable(c)).length} en brouillon` : 'pas encore rédigées', href: '#/exigences' }),
    kpi({ label: 'Tickets faits', value: board.length ? `${done}` : '—', unit: board.length ? `/ ${board.length}` : '', bar: board.length ? meter(done, board.length, 'Tickets faits', true) : null,
      cmp: board.length ? (blocked ? `✕ ${plural(blocked, 'ticket bloqué', 'tickets bloqués')}` : 'aucun bloqué') : 'écrits par /backlog', href: '#/tickets' }),
    kpi({ label: sp ? `Sprint · ${sp.title}` : 'Sprint actif', value: sp ? `${sp.faits}` : '—', unit: sp ? `/ ${sp.engages} points` : '', bar: sp ? meter(sp.faits, sp.engages, 'Points faits du sprint', true) : null,
      cmp: sp ? `${sp.done} / ${sp.total} tickets faits` : 'aucun sprint en cours', href: sp ? `#/sprints/${sp.slug}` : '#/sprints' }),
    kpi({ label: `Consommation · ${F.periode || 7} j`, value: !u ? '…' : u.error ? '—' : fmtUsd(u.total ? u.total.usd : 0), unit: '',
      cmp: !u ? 'chargement' : u.error ? 'aucune donnée' : u.total ? delta(u.total.usd, u.previous && u.previous.usd, u.days) : `${(u.agents || []).length} agents`, href: '#/consommation' }));
}
function pipeline(compact) {
  const p = S.ov.plan;
  if (!p) return none('Pas encore de plan d’avancement : /status l’écrit.');
  const cls = (x) => x.status === 'fait' ? 'f' : x.status === 'en cours' ? 'e' : x.status === 'bloqué' ? 'b' : x.status === 'non applicable' ? 'n' : '';
  return h('div', { class: 'pipe' }, p.sections.map((s) => {
    const d = s.stages.filter(isClosed).length;
    return h('div', {}, h('div', { class: 'phase-h' }, h('b', {}, s.title), h('span', { class: 'muted num' }, s.stages.length ? `${d} / ${s.stages.length}` : 'pas commencé')),
      compact ? meter(d, s.stages.length, s.title, true) : null,
      h('div', { class: 'steps', style: compact ? 'margin-top:8px' : null }, s.stages.map((x) => {
        const [, sym] = ST[x.status] || ST['à faire'];
        return h('span', { class: `step ${cls(x)}`, title: `${x.status}${x.detail ? ` — ${x.detail}` : ''}` }, h('span', { 'aria-hidden': 'true' }, sym), x.stage, h('span', { class: 'vh' }, ` : ${x.status}`));
      })));
  }));
}
function livrerCard() {
  const fails = recettes().filter((r) => r.verdict === 'FAIL'), blocked = ofType('Ticket').filter((t) => t.state === 'blocked'), g = (next() && next().gaps) || [];
  const nb = fails.length + blocked.length + g.length;
  return h('section', { class: `card verdict${nb ? ' no' : ''}` }, h('div', { class: 'eyebrow' }, 'Peut-on livrer ?'),
    h('h3', {}, nb ? `Non — ${plural(nb, 'point bloque', 'points bloquent')}` : 'Oui — rien ne bloque'),
    nb ? h('ul', { class: 'list' }, fails.map((r) => h('li', {}, verdict('FAIL'), h('div', {}, 'Recette « ', recetteName(r), ' »'))),
      blocked.map((t) => h('li', {}, st('bloqué'), h('div', {}, h('a', { href: ticketHref(t.path) }, t.title)))),
      g.slice(0, 4).map((x) => h('li', {}, st('manquante', 'b', '✕'), h('div', {}, `Preuve : ${x}`))))
      : h('p', { class: 'muted' }, 'Aucune recette échouée, aucun ticket bloqué, aucune preuve manquante.'));
}
function yourTurn() {
  const v = toValidate(), open = openRemarks(), answered = remarques().filter((r) => r.etat === 'traitee').sort((a, b) => String(b.traiteeAt).localeCompare(String(a.traiteeAt))).slice(0, 3);
  return cardH('À vous', h('a', { href: '#/gestion/validation' }, 'Tout voir'),
    h('ul', { class: 'list' },
      h('li', {}, h('span', { class: `badge${v.length ? '' : ' q'}`, style: 'margin:0' }, String(v.length)), h('div', {}, h('a', { class: 't', href: '#/gestion/validation' }, plural(v.length, 'document à valider', 'documents à valider')),
        h('div', { class: 'm' }, v.length ? `Le plus récent : ${v[0].title}` : 'Tout ce que Claude a écrit est validé.'))),
      h('li', {}, h('span', { class: 'badge q', style: 'margin:0' }, String(open.length)), h('div', {}, h('a', { class: 't', href: '#/remarques' }, plural(open.length, 'remarque en attente de Claude', 'remarques en attente de Claude')),
        h('div', { class: 'm' }, open.length ? 'Claude les lit à la prochaine « reprends ».' : 'Une correction, une question ? Bouton « Remarque pour Claude ».'))),
      answered.map((r) => h('li', {}, st('réponse', 'f', '✓'), h('div', {}, h('a', { class: 't', href: '#/remarques' }, r.title), h('div', { class: 'm' }, `Claude : ${r.reponse || '—'}`))))));
}
function activityCard() {
  const l = S.activity.slice(0, 7);
  return cardH('Activité récente', h('a', { href: '#/journal' }, 'Journal'),
    l.length ? h('ol', { class: 'list' }, l.map((a) => h('li', {}, h('span', { class: 'when' }, isoDay(a.date).slice(0, 5)), h('div', {}, h('b', { title: a.acteurNom }, ACTEUR[a.acteur] || a.acteur), ' ', actText(a)))))
      : none('Aucune entrée dans les journaux de la KB.'));
}
function sprintCard() {
  const sp = activeSprint(); if (!sp) return null;
  return cardH(`Sprint en cours · ${sp.title}`, h('a', { href: `#/sprints/${sp.slug}` }, 'Détail du sprint'),
    table(['Ticket', 'Statut', 'Critères'], sp.tickets.map((t) => h('tr', { class: t.state === 'blocked' ? 'fail' : null }, td(h('a', { href: ticketHref(t.path) }, t.title)), td(ticketSt(t)), td(proof(t), 'num')))));
}
function home() {
  const p = S.ov.plan, n = next(), sec = n && p ? p.sections.find((s) => s.title === n.section) : null;
  const where = !p ? 'Pas encore de plan d’avancement.' : !n ? 'Toutes les étapes connues sont faites.'
    : sec ? `${n.section} — étape ${sec.stages.findIndex((x) => x.stage === n.stage) + 1} sur ${sec.stages.length}.` : `${n.section}.`;
  return [pageH('Vue d’ensemble', `Où en est ${projectTitle()} ?`, where), hero(), kpis(),
    h('div', { class: 'cols w' }, h('div', { class: 'stack' }, cardH('Plan d’avancement', h('a', { href: '#/avancement' }, 'Détail'), pipeline(true)), sprintCard()),
      h('div', { class: 'stack' }, yourTurn(), livrerCard())),
    h('div', { class: 'cols' }, activityCard(), remarksCard())];
}
function remarksCard() {
  const l = remarques().slice(0, 4);
  return cardH('Vos remarques', h('a', { href: '#/remarques' }, 'Toutes'), l.length ? h('div', { class: 'stack', style: 'gap:10px' }, l.map((r) => remarkItem(r, true)))
    : none('Aucune remarque. Sur chaque écran, le bouton « Remarque pour Claude » en écrit une.'));
}

// --- plan d'avancement ------------------------------------------------------------------------
function vAvancement() {
  const p = S.ov.plan, n = next();
  if (!p) return [pageH('Pilotage', 'Plan d’avancement'), hero()];
  const g = (n && n.gaps) || [];
  return [pageH('Pilotage', 'Plan d’avancement', 'Les étapes de la méthode, leurs preuves et le travail des agents. Le plan est tenu par Claude ; il se lit ici.'), hero(),
    h('div', { class: 'cols w' },
      h('div', { class: 'stack' }, card('Toutes les étapes', pipeline(false)),
        ...p.sections.map((s) => h('details', { class: 'card' }, h('summary', {}, h('b', {}, s.title), ` · ${s.stages.filter(isClosed).length} / ${s.stages.length}`),
          h('div', { style: 'margin-top:12px' }, table(['Étape', 'Statut', 'Date', 'Détail'], s.stages.map((x) => h('tr', { class: x.status === 'bloqué' ? 'fail' : null }, td(x.stage), td(st(x.status)), td(fmtDate(x.at), 'num'), td(x.detail || '', 'muted')))))))),
      h('div', { class: 'stack' },
        card(`Preuves manquantes · ${g.length}`, g.length ? h('ul', { class: 'list' }, g.map((x) => h('li', {}, st('manquante', 'b', '✕'), h('div', {}, x)))) : none('Aucune preuve manquante pour l’étape en cours.')),
        card('Point de reprise', (p.resume.length ? p.resume : ['Aucun point de reprise.']).map((l) => h('p', {}, l))))),
    (p.taches || []).length ? card('Tâches des agents', table(['Étape', 'Agent', 'Objet', 'Statut', 'Sortie ou détail'], p.taches.map((t) => h('tr', { class: t.statut === 'bloqué' ? 'fail' : null },
      td(`${t.stage}${t.scope ? ` (${t.scope})` : ''}`), td(t.agent), td(t.objet || ''), td(st(t.statut)), td(t.sortie || t.detail || '', 'muted'))))) : null,
    (p.boucles || []).length ? card('Boucles de correction', h('p', { class: 'muted' }, 'Un retour en arrière entre deux étapes. Au-delà de la borne, Claude s’arrête et vous demande.'),
      table(['Boucle', 'Tours', 'État', 'Détail'], p.boucles.map((b) => h('tr', { class: b.etat === 'ouverte' && b.tours >= b.max ? 'fail' : null },
        td(`${b.from} → ${b.to}${b.scope ? ` (${b.scope})` : ''}`), td(`${b.tours} / ${b.max}`, 'num r'), td(st(b.etat)), td(b.detail || '', 'muted'))))) : null];
}

// --- sprints ------------------------------------------------------------------------------------
const sprintSt = (s) => s.state === 'done' ? st('terminé', 'f', '✓') : s.state === 'active' ? st('actif', 'e', '◐') : st('prévu', 'a', '○');
function vSprints() {
  const sp = S.ov.sprints || [], v = S.ov.velocite || {};
  if (!sp.length) return [pageH('Pilotage', 'Sprints'), empty('Aucun sprint pour l’instant.', h('p', {}, '/sprint en compose un à partir du backlog.'), cmdBox('sprint'))];
  return [pageH('Pilotage', 'Sprints', 'Un sprint est un groupe de tickets construits ensemble, puis montrés et fusionnés.'),
    h('div', { class: 'kpis' },
      kpi({ label: 'Vitesse moyenne', value: v.moyenne == null ? '—' : fmtNum(v.moyenne), unit: v.moyenne == null ? '' : 'points / sprint', cmp: v.moyenne == null ? 'pas encore de sprint terminé' : 'sur les sprints terminés', href: '#/sprints' }),
      kpi({ label: 'Points ouverts', value: String(v.ouverts ?? '—'), cmp: 'dans le backlog et les sprints', href: '#/tickets' }),
      kpi({ label: 'Sprints restants', value: v.restants == null ? '—' : fmtNum(v.restants), cmp: v.restants == null ? 'impossible à estimer' : 'à la vitesse moyenne', href: '#/sprints' }),
      kpi({ label: 'Sprints', value: String(sp.length), cmp: `${sp.filter((s) => s.state === 'done').length} terminés`, href: '#/sprints' })),
    ...sp.map((s) => h('section', { class: 'card' }, h('div', { class: 'card-h' }, h('h2', {}, h('a', { href: `#/sprints/${s.slug}` }, s.title)), sprintSt(s)),
      s.description ? h('p', { class: 'muted' }, s.description) : null,
      h('div', { class: 'row' }, h('span', { class: 'num' }, `${s.faits} / ${s.engages} points faits`), h('span', { class: 'muted num' }, `${s.done} / ${s.total} tickets`), s.branch ? h('span', { class: 'mono muted' }, s.branch) : null),
      meter(s.faits, s.engages, `Points faits de ${s.title}`, true)))];
}
function vSprint(slug) {
  const s = (S.ov.sprints || []).find((x) => x.slug === slug); if (!s) return v404();
  const b = s.audit.bloquants;
  return [crumbs(['Sprints', '/sprints'], [s.title]), pageH(null, s.title, s.description, h('div', { class: 'row' }, sprintSt(s), h('span', { class: 'num' }, `${s.faits} / ${s.engages} points · reste ${s.restants}`))),
    meter(s.faits, s.engages, 'Points faits', true),
    h('div', { class: 'cols w' }, card(`Tickets · ${s.done} / ${s.total} faits`, table(['Ticket', 'Statut', 'Critères'], s.tickets.map((t) => h('tr', { class: t.state === 'blocked' ? 'fail' : null }, td(h('a', { href: routeOf(t.path) }, t.title)), td(ticketSt(t)), td(proof(t), 'num'))))),
      h('div', { class: 'stack' },
        card('Audit et démo', h('p', {}, 'Audit : ', b == null ? st('jamais audité', 'a', '○') : b ? st(plural(b, 'bloquant', 'bloquants'), 'b', '✕') : st('aucun bloquant', 'f', '✓')),
          h('p', { class: 'muted' }, 'Démo : les tests T1, T2… que vous faites avant de fusionner le sprint.'),
          s.demo.length ? h('ul', { class: 'list' }, s.demo.map((d) => h('li', {}, d.ok ? st('OK', 'f', '✓') : st('KO', 'b', '✕'), h('div', { class: 'mono' }, d.t)))) : none('Pas encore de démo.')),
        card('Mesures du bilan', (s.mesures || []).length ? h('ul', {}, s.mesures.map((m) => h('li', {}, m))) : none('Pas encore mesuré : le bilan du sprint écrit ces chiffres.'))))];
}

// --- tickets : tableau, glisser-déposer ou menu ---------------------------------------------------
async function moveTicket(path, state) {
  const t = (S.ov.board || []).find((x) => x.path === path); if (!t || t.state === state) return;
  try { await api(`concepts/${enc(path)}`, { method: 'PATCH', json: { frontmatter: { state } } }); await load(); toast(`${t.title} : ${TICKET[state]}`); }
  catch (e) { toast(`Rien n’a changé : ${plain(e)}.`); }
  route();
}
const BACKLOG = '__backlog__';
const VALIDATION = [['humain', 'validé par vous'], ['machine', 'contrôlé automatiquement'], ['aucune', 'à valider']];
function tcard(t) {
  return h('article', { class: 'tcard', draggable: 'true', ondragstart: (e) => { e.dataTransfer.setData('text/plain', t.path); e.currentTarget.classList.add('drag'); }, ondragend: (e) => e.currentTarget.classList.remove('drag') },
    h('a', { class: 'tt', href: ticketHref(t.path) }, t.title),
    h('div', { class: 'meta' }, t.priority == null ? h('span', {}, 'sans priorité') : h('span', { class: 'prio' }, `P${t.priority}`), h('span', {}, t.points > 0 ? `${t.estimate} · ${plural(t.points, 'pt', 'pts')}` : 'non estimé'),
      h('span', {}, sprintName(t.sprint)), h('span', {}, `critères ${proof(t)}`)),
    h('div', { class: 'row', style: 'gap:6px' }, trustSt({ trust: { humain: 'human', machine: 'machine' }[t.validation] || 'none' }), t.origine === 'humain' ? st('écrit par vous', 'a', '✎') : null,
      h('span', { class: 'sp' }), h('select', { 'aria-label': `Déplacer ${t.title} vers`, onchange: (e) => moveTicket(t.path, e.target.value) },
        h('option', { value: '' }, 'Déplacer…'), STATES.filter((s) => s !== t.state).map((s) => h('option', { value: s }, stateName(s))))));
}
function vTickets() {
  const all = (S.ov && S.ov.board) || [];
  const sprints = [...new Set(all.map((t) => t.sprint).filter(Boolean))].map((s) => [s, sprintName(s)]);
  const l = all.filter((t) => (!F.sprint || (F.sprint === BACKLOG ? !t.sprint : t.sprint === F.sprint)) && (!F.origine || t.origine === F.origine)
    && (!F.validation || t.validation === F.validation) && has(t.title + ' ' + t.path));
  const ill = (S.ov.illisibles || []);
  const col = (state) => {
    const list = l.filter((t) => t.state === state), pts = list.reduce((n, t) => n + t.points, 0);
    return h('section', { class: 'col', 'aria-label': stateName(state), ondragover: (e) => { e.preventDefault(); e.currentTarget.classList.add('over'); }, ondragleave: (e) => e.currentTarget.classList.remove('over'),
      ondrop: (e) => { e.preventDefault(); e.currentTarget.classList.remove('over'); moveTicket(e.dataTransfer.getData('text/plain'), state); } },
    h('div', { class: 'col-h' }, st(stateName(state), ...ST[TICKET[state]]), h('span', { class: 'muted num' }, `${list.length} · ${plural(pts, 'pt', 'pts')}`)), list.map(tcard));
  };
  return [pageH('Pilotage', 'Tickets', 'Glissez un ticket d’une colonne à l’autre, ou utilisez « Déplacer… ». Chaque changement est écrit dans la KB et journalisé.'),
    filterBar(['q'], { sprint: [...sprints, [BACKLOG, 'Backlog non planifié']], origine: [['humain', 'vous'], ['agent', 'Claude']], validation: VALIDATION }, 'Rechercher un ticket'),
    all.length ? l.length ? h('div', { class: 'board' }, STATES.map(col)) : empty('Aucun ticket ne correspond.', clearBtn(['q', 'sprint', 'origine', 'validation']))
      : empty('Aucun ticket pour l’instant : /backlog les crée à partir des exigences.', cmdBox('backlog')),
    ill.length ? card(`Fichiers illisibles · ${ill.length}`, h('p', { class: 'muted' }, 'Ces fichiers manquent dans les listes tant qu’ils ne sont pas réparés.'),
      table(['Fichier', 'Cause'], ill.map((x) => h('tr', {}, td(x.path, 'mono'), td(x.cause))))) : null];
}
function vTicket(path) {
  const c = S.concepts.find((x) => x.path === path + '.md'); if (!c) return v404();
  S.target = { path: c.path, title: c.title };
  const cv = S.cov && !S.cov.error ? S.cov[c.path] : null, tests = recettesOf(c);
  const rv = reviewOf(c), notes = secOf(c.body, 'Revue').replace(/^.*(PASS-WITH-NOTES|PASS|FAIL).*\n?/m, '').trim();
  return [crumbs(['Tickets', '/tickets'], [c.title]),
    pageH(null, c.title, c.fm.description || null, h('div', { class: 'row' }, ticketSt(c), h('span', { class: 'muted' }, sprintName(c.fm.sprint)), h('span', {}, 'Revue : ', verdict(rv)), trustSt(c),
      h('span', { class: 'sp' }), h('label', { class: 'flt' }, 'État', h('select', { onchange: (e) => moveTicket(c.path, e.target.value) }, STATES.map((s) => h('option', { value: s, selected: (c.fm.state || 'todo') === s }, stateName(s))))),
      docActions(c))),
    h('div', { class: 'cols w' },
      h('div', { class: 'stack' },
        card(`Critères d’acceptation · ${proof(c)}`, !cv ? none(proof(c)) : cv.criteres.length ? h('ul', { class: 'list' }, cv.criteres.map((a) => h('li', {}, cv.couverts.includes(a) ? st('couvert', 'f', '✓') : cv.plan ? st('non couvert', 'b', '✕') : st('non testé', 'a', '○'), h('div', { class: 'mono' }, a)))) : none('Aucun critère CAn dans ce ticket.')),
        h('details', { class: 'card', open: true }, h('summary', {}, h('b', {}, 'Contenu du ticket')), docBox(c))),
      h('div', { class: 'stack' },
        card('Preuves', h('p', {}, 'Plan technique : ', !cv ? st('non testé', 'a', '○') : cv.plan ? st('écrit', 'f', '✓') : st('manquant', 'b', '✕')),
          tests.length ? tests.map((t) => h('p', {}, verdict((((t.body || '').split(/^## Verdict/m)[1] || '').match(/PASS-WITH-NOTES|PASS|FAIL/) || [])[0]), ' ', h('a', { href: routeOf(t.path) }, t.title))) : h('p', {}, 'Recette : ', st('non testé', 'a', '○'))),
        card('Revue de code', notes ? h('pre', { class: 'plain' }, notes) : none('Pas encore de revue.')),
        targetRemarks(c)))];
}

// --- cahier des charges : exigences et personas ------------------------------------------------------
const serves = (c, persona) => kbLinks(c).includes(`personnas/${persona}.md`);
const kbLinks = (c) => [...String(c.body || '').matchAll(/\]\(([^)\s]+\.md)/g)].map((m) => kbPath(c.path, m[1])).filter(Boolean);
function vExigences() {
  const ex = ofType('Exigence'), bad = (S.ov.illisibles || []).filter((x) => x.path.startsWith('cdc/'));
  const espaces = [...new Set(ex.map((c) => c.fm.espace).filter(Boolean))].sort().map((v) => [v, v]);
  const rows = ex.filter((c) => has(c.title + ' ' + (c.fm.description || '')) && (!F.statut || (F.statut === 'stable') === isStable(c)) && (!F.espace || c.fm.espace === F.espace) && (!F.persona || serves(c, F.persona)));
  const glossaire = S.concepts.find((c) => c.path === 'cdc/glossaire.md'), okN = ex.filter((c) => c.trust === 'human').length;
  const others = S.concepts.filter((c) => /^(cdc|juridique|project)\//.test(c.path) && c.type !== 'Exigence' && c.path !== 'cdc/glossaire.md').sort((a, b) => a.title.localeCompare(b.title));
  return [pageH('Produit', 'Cahier des charges', 'Ce que l’application doit permettre de faire. Validez chaque exigence quand elle vous convient ; sinon, écrivez une remarque à Claude.'),
    bad.map((x) => h('div', { class: 'alert', role: 'alert' }, h('span', {}, h('span', { class: 'mono' }, x.path), ` n’apparaît pas dans la liste : ${x.cause}.`))),
    ex.length ? [h('div', { class: 'kpis' },
      kpi({ label: 'Validées par vous', value: String(okN), unit: `/ ${ex.length}`, bar: meter(okN, ex.length, 'Exigences validées', true), cmp: `${ex.length - okN} à valider`, href: '#/exigences' }),
      kpi({ label: 'Finalisées', value: String(ex.filter(isStable).length), unit: `/ ${ex.length}`, cmp: `${ex.filter((c) => !isStable(c)).length} en brouillon`, href: '#/exigences' }),
      kpi({ label: 'Personas', value: String(ofType('Persona').length), cmp: 'pour qui vous construisez', href: '#/personas' }),
      kpi({ label: 'Remarques ouvertes', value: String(openRemarks().filter((r) => /^cdc\//.test(r.cible || '')).length), cmp: 'sur le cahier des charges', href: '#/remarques' })),
    filterBar(['q'], { statut: [['stable', 'finalisée'], ['draft', 'brouillon']], espace: espaces, persona: ofType('Persona').map((p) => [p.slug, p.title]) }, 'Rechercher une exigence'),
    rows.length ? table(['Exigence', 'Statut', 'Validation', 'Remarques', ''], rows.map((c) => {
      const rem = remarksOf(c.path).filter((r) => r.etat === 'ouverte').length;
      return h('tr', {}, td([h('a', { href: `#/exigences/${encodeURIComponent(c.slug)}` }, c.title), c.fm.description ? h('div', { class: 'muted', style: 'font-size:13px' }, c.fm.description) : null]),
        td(statusSt(c)), td(trustSt(c)), td(rem ? st(`${rem} en attente`, 'r', '◷') : '—'),
        td(h('div', { class: 'row', style: 'flex-wrap:nowrap' }, c.trust === 'none' || !isStable(c) ? h('button', { class: 'btn s', type: 'button', 'aria-label': `Valider ${c.title}`, onclick: () => validate(c) }, 'Valider') : null,
          h('button', { class: 'btn o s', type: 'button', 'aria-label': `Remarque sur ${c.title}`, onclick: () => openDrawer({ path: c.path, title: c.title }) }, 'Remarque'))));
    }), { caption: 'Exigences' }) : empty('Aucune exigence ne correspond.', clearBtn(['q', 'statut', 'espace', 'persona']))]
      : empty('Le cahier des charges n’est pas encore rédigé.', cmdBox('interview')),
    others.length ? card('Autres documents du cahier des charges', h('ul', { class: 'list' }, others.map((c) => h('li', {}, h('i', { class: `dot ${c.trust}`, style: 'margin-top:8px', title: trustWord(c) }), h('div', {}, h('a', { class: 't', href: routeOf(c.path) }, c.title), h('div', { class: 'm' }, c.type)))))) : null,
    glossaire ? h('details', { class: 'card' }, h('summary', {}, h('b', {}, 'Glossaire'), ' — les termes du projet et leur sens'), docBox(glossaire)) : null];
}
function vExigence(slug) {
  const c = ofType('Exigence').find((x) => x.slug === slug); if (!c) return v404();
  S.target = { path: c.path, title: c.title };
  return [crumbs(['Cahier des charges', '/exigences'], [c.title]), pageH(null, c.title, c.fm.description || null, h('div', { class: 'row' }, statusSt(c), trustSt(c), h('span', { class: 'sp' }), docActions(c))),
    h('div', { class: 'cols w' }, card(null, docBox(c)), h('div', { class: 'stack' }, targetRemarks(c), provenance(c)))];
}
const bullets = (text) => text ? h('ul', {}, text.split('\n').map((l) => l.trim()).filter(Boolean).map((l) => h('li', {}, l.replace(/^[-*]\s+/, '').replace(/\*\*/g, '')))) : h('p', { class: 'muted' }, 'non documenté');
function vPersonas(slug) {
  const ps = ofType('Persona').filter((p) => !slug || p.slug === slug);
  if (slug && !ps.length) return v404();
  if (slug) S.target = { path: ps[0].path, title: ps[0].title };
  return [slug ? crumbs(['Personas', '/personas'], [ps[0].title]) : null, pageH('Produit', slug ? ps[0].title : 'Personas', slug ? ps[0].fm.description : 'Les personnes pour qui vous construisez l’application.'),
    ps.length ? h('div', { class: slug ? 'stack' : 'cols' }, ps.map((p) => h('section', { class: 'card' }, h('div', { class: 'card-h' }, h('h2', {}, slug ? 'Profil' : h('a', { href: `#/personas/${encodeURIComponent(p.slug)}` }, p.title)), trustSt(p)),
      slug ? null : h('p', { class: 'muted' }, p.fm.description || ''),
      [['Objectifs', 'Objectifs'], ['Besoins', 'Besoins'], ['Difficultés', 'Pain points']].map(([label, name]) => [h('h3', { style: 'margin-top:12px' }, label), bullets(secOf(p.body, name))]),
      h('div', { class: 'row', style: 'margin-top:12px' }, docActions(p))))) : empty('Aucun persona pour l’instant : /hosa les crée.', cmdBox('hosa')),
    slug ? targetRemarks(ps[0]) : null];
}

// --- recettes et qualité --------------------------------------------------------------------------------
function vRecettes() {
  const r = recettes(), l = r.filter((x) => !F.verdict || x.verdict === F.verdict);
  const audit = (name, a) => h('div', { class: 'kpi', style: 'cursor:default' }, h('span', { class: 'l' }, `Dernier audit ${name}`), h('span', { class: 'v', style: 'font-size:20px' }, a ? (VERD[a.verdict] ? verdict(a.verdict) : a.verdict || 'sans verdict') : st('jamais audité', 'a', '○')),
    h('span', { class: 'c' }, a ? fmtDay(a.at) : 'lancez /qualite ou /securite'));
  const count = (v) => r.filter((x) => x.verdict === v).length;
  return [pageH('Pilotage', 'Recettes et qualité', 'Une recette est un test de l’application, fait comme le ferait un utilisateur. Les audits vérifient le code.'),
    h('div', { class: 'kpis' },
      kpi({ label: 'Recettes réussies', value: String(count('PASS') + count('PASS-WITH-NOTES')), unit: `/ ${r.length}`, bar: meter(count('PASS') + count('PASS-WITH-NOTES'), r.length, 'Recettes réussies', true), cmp: `${count('PASS-WITH-NOTES')} avec remarques`, href: '#/recettes' }),
      kpi({ label: 'Recettes échouées', value: String(count('FAIL')), cmp: count('FAIL') ? '✕ à corriger avant de livrer' : '✓ aucune', href: '#/recettes' }),
      audit('qualité', S.ov.quality), audit('sécurité', S.ov.security)),
    seg('Résultat', [['', 'Toutes'], ['FAIL', 'Échouées'], ['PASS-WITH-NOTES', 'Avec remarques'], ['PASS', 'Réussies']], F.verdict || '', (v) => setF('verdict', v)),
    l.length ? table(['Recette', 'Date', 'Résultat'], l.map((x) => h('tr', { class: x.verdict === 'FAIL' ? 'fail' : null }, td(h('a', { href: routeOf(x.path) }, recetteName(x))), td(fmtDate(x.at), 'num'), td(verdict(x.verdict)))))
      : empty(r.length ? 'Aucune recette ne correspond.' : 'Aucune recette pour le moment : elles arrivent avec la QA d’un sprint.')];
}

// --- consommation ---------------------------------------------------------------------------------------
const EMPTY_USAGE = 'Aucune donnée de consommation trouvée pour ce projet';
function vConsommation() {
  const u = S.usage, days = F.periode || '7';
  const head = [pageH('Pilotage', 'Consommation', 'Ce que coûte le travail de Claude sur ce projet : par agent ou skill, par modèle. Coût estimé aux prix publics.'),
    seg('Période', [['7', '7 jours'], ['30', '30 jours'], ['90', '90 jours']], days, (v) => setF('periode', v))];
  if (!u) return [...head, none('Chargement…')];
  if (u.error && plain(u.error) !== EMPTY_USAGE) return [...head, errBox(`Consommation indisponible : ${plain(u.error)}.`, true)];
  if (u.error) return [...head, empty(`${EMPTY_USAGE}.`, h('p', {}, 'Les chiffres apparaissent quand des sessions de travail sont enregistrées sur ce poste. Travaillez dans Claude Code, puis cliquez sur « Relire ».'))];
  const t = u.total || {}, p = u.previous, cached = (t.cache_read || 0) / ((t.input || 0) + (t.cache_read || 0) + (t.cache_write || 0) || 1);
  const agents = u.agents || [], max = Math.max(...agents.map((a) => a.usd), 0.0001);
  const rows = (list) => list.map((r, i) => h('tr', {}, td([r.name, i < 2 && list.length > 3 ? [' ', st('gros consommateur', 'w', '▲')] : null]), td(String(r.calls), 'num r'),
    td(fmtTok((r.input || 0) + (r.cache_write || 0) + (r.cache_read || 0)), 'num r'), td(fmtTok(r.output || 0), 'num r'), td(fmtUsd(r.usd), 'num r'), td(`${roundEven(r.part)} %`, 'num r')));
  const head2 = ['', 'Appels', 'Entrée (tokens)', 'Sortie (tokens)', 'Coût estimé', 'Part'];
  return [...head,
    h('div', { class: 'kpis' },
      kpi({ label: 'Coût estimé', value: fmtUsd(t.usd), cmp: delta(t.usd || 0, p && p.usd, u.days), href: '#/consommation' }),
      kpi({ label: 'Appels au modèle', value: fmtNum(t.calls), cmp: delta(t.calls || 0, p && p.calls, u.days), href: '#/consommation' }),
      kpi({ label: 'Tokens écrits par Claude', value: fmtTok(t.output || 0), cmp: delta(t.output || 0, p && p.output, u.days), href: '#/consommation' }),
      kpi({ label: 'Lu depuis le cache', value: `${Math.round(100 * cached)} %`, cmp: 'du contexte relu à prix réduit', href: '#/consommation' })),
    cardH('Coût par agent ou skill', h('span', { class: 'muted' }, `${days} derniers jours`),
      h('div', { class: 'hbars', role: 'img', 'aria-label': 'Coût estimé par agent ou skill ; les valeurs exactes sont dans le tableau ci-dessous' },
        agents.slice(0, 12).map((a) => h('div', { class: 'hbar', title: `${a.name} : ${fmtUsd(a.usd)} · ${a.calls} appels · ${roundEven(a.part)} %` },
          h('span', { class: 'n' }, a.name), h('span', { class: 'tr', 'aria-hidden': 'true' }, h('i', { style: `width:${100 * a.usd / max}%` })), h('span', { class: 'v' }, fmtUsd(a.usd))))),
      agents.length > 12 ? h('p', { class: 'muted', style: 'margin-top:8px' }, `et ${agents.length - 12} autres dans le tableau.`) : null),
    card('Détail par agent ou skill', table(['Agent ou skill', ...head2.slice(1)], rows(agents))),
    card('Par modèle', table(['Modèle', ...head2.slice(1)], rows(u.models || []))),
    h('p', { class: 'muted' }, `Part : la part du coût estimé de la période. Historique lu depuis le ${isoDay(u.since)}.`)];
}

// --- traçabilité --------------------------------------------------------------------------------------------
const KIND = { exigence: 'exigence', ticket: 'ticket', file: 'fichier', class: 'classe', function: 'fonction', method: 'méthode' };
const nodeName = (n) => n.label || String(n.id).split(':').slice(1).join(':') || n.id;
const nodeLink = (n) => n.kb ? h('a', { href: routeOf(n.kb) }, nodeName(n)) : nodeName(n);
const flat = (nodes) => nodes.length ? h('ul', { class: 'flat', style: 'margin:0;padding-left:18px' }, nodes.map((n) => h('li', {}, nodeLink(n)))) : null;
function nodePanel(id, panel) {
  panel.replaceChildren(h('p', { class: 'muted' }, 'Chargement…'));
  api(`graph/node?id=${encodeURIComponent(id)}`).then((d) => {
    const rel = (l, dir) => l.length ? table(['Relation', 'Élément', 'Type'], l.map((e) => h('tr', {}, td(`${dir} ${e.rel}`), td(nodeLink(e.node)), td(KIND[e.node.kind] || e.node.kind)))) : null;
    panel.replaceChildren(h('h2', {}, `${KIND[d.node.kind] || d.node.kind} · ${nodeName(d.node)}`), d.node.file ? h('p', { class: 'mono muted' }, d.node.file + (d.node.line ? `:${d.node.line}` : '')) : null,
      h('h3', {}, 'Relations'), rel(d.out, '→'), rel(d.in, '←'), d.out.length + d.in.length ? null : none('Aucune relation.'),
      h('h3', { style: 'margin-top:14px' }, 'Impact'), d.affected.nodes.length ? table(['Profondeur', 'Élément', 'Type'], d.affected.nodes.map((x) => h('tr', {}, td(String(x.depth), 'num'), td(nodeLink(x.node)), td(KIND[x.node.kind] || x.node.kind)))) : none('Rien d’autre ne dépend de cet élément.'),
      h('h3', { style: 'margin-top:14px' }, 'Tickets concernés'), flat(d.affected.tickets) || none('Aucun ticket ne touche les fichiers impactés.'));
  }, (e) => panel.replaceChildren(errBox(e.status === 404 ? 'Élément introuvable' : `Traçabilité indisponible : ${plain(e)}.`)));
}
function vTracabilite() {
  const box = h('div', {}, none('Chargement…')), results = h('div'), panel = h('section', { class: 'card', 'aria-live': 'polite' }, none('Choisissez un élément pour voir ses relations et son impact.'));
  const search = (q) => { S.gq = q; if (!q.trim()) return results.replaceChildren(); results.replaceChildren(none('Chargement…'));
    api(`graph/find?q=${encodeURIComponent(q)}`).then((l) => results.replaceChildren(l.length ? table(['Élément', 'Type', 'Fichier'], l.map((n) => h('tr', {}, td(h('button', { class: 'lnk', type: 'button', onclick: () => nodePanel(n.id, panel) }, nodeName(n))), td(KIND[n.kind] || n.kind), td(n.file || '', 'mono muted')))) : none('Aucun élément ne correspond.')),
      (e) => results.replaceChildren(errBox(`Traçabilité indisponible : ${plain(e)}.`))); };
  let timer;
  if (S.gq) search(S.gq);
  api('graph/trace').then((t) => box.replaceChildren(t.length ? table(['Exigence', 'Statut', 'Tickets', 'Fichiers'], t.map((e) => {
    const n = e.tickets.reduce((k, x) => k + x.files.length, 0), alone = e.node.status === 'stable' && !n;
    return h('tr', { class: alone ? 'fail' : null }, td(nodeLink(e.node)), td([e.node.status === 'stable' ? st('finalisée', 'f', '✓') : st('brouillon', 'a', '○'), alone ? [' ', st('sans fichier lié', 'b', '✕')] : null]),
      td(flat(e.tickets.map((x) => x.node)) || st('aucun ticket', 'a', '—')), td(String(n), 'num r'));
  })) : none('Aucune exigence dans le graphe.')),
  (e) => box.replaceChildren(/graphe absent/i.test(e.message) ? errBox(`${e.message}.`, true) : errBox(`Traçabilité indisponible : ${plain(e)}.`, true)));
  return [pageH('Produit', 'Traçabilité', 'Le lien entre une exigence, ses tickets et les fichiers de code. Une exigence finalisée sans fichier est signalée.'), card('Exigences → tickets → code', box),
    h('div', { class: 'cols' }, card('Rechercher un élément', h('div', { class: 'filters', role: 'search' }, h('input', { id: 'search', type: 'search', 'aria-label': 'Rechercher un élément', placeholder: 'fichier, fonction, ticket, exigence ( / )', value: S.gq || '', oninput: (e) => { clearTimeout(timer); timer = setTimeout(() => search(e.target.value), 250); } })), h('div', { style: 'margin-top:12px' }, results)), panel)];
}

// --- journal ----------------------------------------------------------------------------------------------------
function vJournal() {
  const l = S.activity.filter((a) => has(a.text + ' ' + a.bundle) && (!F.acteur || a.acteur === F.acteur) && (!F.dossier || a.bundle === F.dossier));
  const days = [...new Set(l.map((a) => a.date))];
  return [pageH('Vos actions', 'Journal', 'Chaque écriture dans la KB, par Claude, par vous ou par l’application.'),
    filterBar(['q'], { acteur: Object.entries(ACTEUR), dossier: [...new Set(S.activity.map((a) => a.bundle))].sort().map((b) => [b, b || 'racine']) }, 'Rechercher dans le journal'),
    !S.activity.length ? empty('Aucune entrée dans les journaux de la KB.') : !l.length ? empty('Aucune entrée ne correspond.', clearBtn(['q', 'acteur', 'dossier']))
      : days.map((d) => cardH(isoDay(d), h('span', { class: 'muted' }, plural(l.filter((a) => a.date === d).length, 'entrée', 'entrées')),
        h('ul', { class: 'list' }, l.filter((a) => a.date === d).map((a) => h('li', {}, h('span', { class: `st ${a.acteur === 'humain' ? 'f' : a.acteur === 'agent' ? 'e' : 'a'}`, title: a.acteurNom }, ACTEUR[a.acteur] || a.acteur),
          h('div', {}, actText(a), h('div', { class: 'm' }, `${a.bundle || 'racine'} · ${a.acteurNom}`)))))))];
}

// --- à valider ----------------------------------------------------------------------------------------------------
function vValidation() {
  const l = toValidate(), done = validated();
  return [pageH('Vos actions', 'À valider', 'Ce que Claude a écrit et que vous n’avez pas encore validé, du plus récent au plus ancien. Lisez, puis validez — ou écrivez une remarque pour que Claude corrige.'),
    l.length ? table(['Document', 'Produit', 'Actions'], l.map((c) => h('tr', {},
      td([h('a', { href: routeOf(c.path) }, c.title), h('div', { class: 'muted', style: 'font-size:13px' }, `${c.type} · ${agentLabel(c.fm.generated.by)}`)]),
      td(fmtDay(c.fm.generated.at), 'num'),
      td(h('div', { class: 'row', style: 'flex-wrap:nowrap' }, h('button', { class: 'btn s', type: 'button', 'aria-label': `Valider ${c.title}`, onclick: () => validate(c) }, 'Valider'),
        h('button', { class: 'btn o s', type: 'button', 'aria-label': `Remarque sur ${c.title}`, onclick: () => openDrawer({ path: c.path, title: c.title }) }, 'Remarque'))))), { caption: 'Documents à valider' })
      : empty('Rien à valider : tout ce que Claude a écrit est validé.'),
    h('details', { class: 'card' }, h('summary', {}, h('b', {}, `Déjà validé (${done.length})`)),
      h('div', { style: 'margin-top:12px' }, done.length ? table(['Document', 'Validé le', 'Validé par', ''], done.map((c) => h('tr', {}, td([h('a', { href: routeOf(c.path), title: c.title }, c.title), h('div', { class: 'muted', style: 'font-size:13px' }, `Produit par ${agentLabel(c.fm.generated.by)}`)]),
        td(fmtDay(c.fm.verified.at), 'num'), td(verifier(c.fm.verified.by)),
        td(h('button', { class: 'lnk', type: 'button', 'aria-label': `Annuler la validation de ${c.title}`, onclick: () => { if (confirm(`Annuler la validation de « ${c.title} » ?`)) unvalidate(c); } }, 'Annuler la validation'))))) : none('Rien encore.')))];
}

// --- remarques pour Claude ------------------------------------------------------------------------------------------
function remarkItem(r, compact) {
  const target = r.cible ? S.concepts.find((c) => c.path === r.cible) : null;
  return h('article', { class: `rem ${r.etat === 'ouverte' ? 'open' : 'done'}` },
    h('div', { class: 'row' }, remSt(r), h('span', { class: 'st a' }, NATURE[r.nature] || r.nature), h('span', { class: 'muted', style: 'font-size:13px' },
      r.cible ? ['sur ', target ? h('a', { href: routeOf(r.cible) }, target.title) : h('span', { class: 'mono' }, r.cible)] : 'remarque générale'),
    h('span', { class: 'sp' }), h('span', { class: 'when', title: fmtDay(r.at) }, ago(r.at))),
    h('div', { class: 'txt' }, compact && r.texte.length > 220 ? `${r.texte.slice(0, 220)}…` : r.texte),
    r.reponse ? h('div', { class: 'reply' }, h('b', {}, `Réponse de Claude${r.traiteeAt ? ` · ${ago(r.traiteeAt)}` : ''}`), h('div', { class: 'txt' }, r.reponse)) : null);
}
function targetRemarks(c) {
  const l = remarksOf(c.path);
  return cardH(`Remarques · ${l.length}`, h('button', { class: 'btn act s', type: 'button', onclick: () => openDrawer({ path: c.path, title: c.title }) }, '✎ Écrire'),
    l.length ? h('div', { class: 'stack', style: 'gap:10px' }, l.map((r) => remarkItem(r))) : none('Une erreur, un oubli, une question sur ce document ? Écrivez-la : Claude la traitera.'));
}
function vRemarques() {
  const all = remarques(), l = all.filter((r) => (!F.etat || r.etat === F.etat) && (!F.nature || r.nature === F.nature) && has(r.texte + ' ' + (r.cible || '')));
  return [pageH('Vos actions', 'Remarques pour Claude', 'Vos corrections, questions et idées sur ce que Claude a produit. Elles sont écrites dans la KB ; Claude les lit et y répond.'),
    h('div', { class: 'how' }, h('div', {}, 'Écrivez une remarque depuis n’importe quel écran : bouton « Remarque pour Claude ».'),
      h('div', {}, ['Dans Claude Code, dites « reprends ». ', h('button', { class: 'lnk', type: 'button', onclick: () => copy('reprends') }, 'Copier')]),
      h('div', {}, 'Claude traite chaque remarque, puis sa réponse s’affiche ici.')),
    h('div', { class: 'row' }, seg('État', [['', `Toutes · ${all.length}`], ['ouverte', `En attente · ${openRemarks().length}`], ['traitee', 'Traitées']], F.etat || '', (v) => setF('etat', v)),
      filterBar(['q'], { nature: Object.entries(NATURE) }, 'Rechercher une remarque'), h('span', { class: 'sp' }),
      h('button', { class: 'btn act', type: 'button', onclick: () => openDrawer(null) }, '✎ Nouvelle remarque')),
    l.length ? h('div', { class: 'stack', style: 'gap:12px' }, l.map((r) => remarkItem(r)))
      : empty(all.length ? 'Aucune remarque ne correspond.' : 'Aucune remarque pour l’instant.', all.length ? clearBtn(['etat', 'nature', 'q']) : null)];
}

// tiroir : écrire une remarque, sur le document ouvert ou générale
const D = { target: null, nature: 'correction', text: '' };
function openDrawer(target) {
  D.target = target === undefined ? S.target : target;
  paintDrawer(); closeNav();
  const d = $('drawer'); d.classList.add('open'); d.setAttribute('aria-hidden', 'false'); d.removeAttribute('inert'); $('scrim').hidden = false;
  setTimeout(() => { const t = $('rem-text'); if (t) t.focus(); }, 60);
}
function closeDrawer() {
  const d = $('drawer'); if (!d.classList.contains('open')) return;
  d.classList.remove('open'); d.setAttribute('aria-hidden', 'true'); d.setAttribute('inert', ''); $('scrim').hidden = true; $('fab').focus();
}
function paintDrawer() {
  const t = D.target, msg = h('div'), count = h('span', { class: 'muted', style: 'font-size:12.5px' }, `${D.text.length} / 4000`);
  const ta = h('textarea', { id: 'rem-text', maxlength: '4000', 'aria-describedby': 'rem-help', placeholder: t ? 'Ce qui ne va pas, ce qui manque, votre question…' : 'Votre remarque pour Claude…',
    oninput: (e) => { D.text = e.target.value; count.textContent = `${D.text.length} / 4000`; },
    onkeydown: (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); send(); } } });
  ta.value = D.text;
  const btn = h('button', { class: 'btn act', type: 'button', id: 'rem-send', onclick: () => send() }, 'Envoyer à Claude');
  async function send() {
    if (!D.text.trim()) { msg.replaceChildren(errBox('Écrivez votre remarque avant de l’envoyer.')); ta.focus(); return; }
    const name = await me(); if (!name) return;
    btn.disabled = true;
    try {
      await api('remarques', { method: 'POST', json: { auteur: name, texte: D.text, cible: t ? t.path : '', nature: D.nature } });
      D.text = ''; await load(); route(); paintDrawer();
      toast('Remarque enregistrée. Claude la lira à la prochaine « reprends ».');
    } catch (e) { msg.replaceChildren(errBox(`Rien n’a été enregistré : ${plain(e)}.`)); btn.disabled = false; }
  }
  const prev = t ? remarksOf(t.path) : openRemarks().filter((r) => !r.cible);
  $('drawer').replaceChildren(
    h('div', { class: 'drawer-h' }, h('h2', { id: 'drawer-title' }, 'Remarque pour Claude'), h('button', { class: 'btn ghost', type: 'button', onclick: closeDrawer, 'aria-label': 'Fermer' }, '✕')),
    h('div', { class: 'drawer-b' },
      h('div', { class: 'target' }, t ? [h('div', { class: 'eyebrow' }, 'Sur le document'), h('b', {}, t.title), ' ', h('button', { class: 'lnk', type: 'button', onclick: () => { D.target = null; paintDrawer(); } }, 'en faire une remarque générale')]
        : [h('div', { class: 'eyebrow' }, 'Remarque générale'), 'Elle ne vise pas un document précis.', S.target ? [' ', h('button', { class: 'lnk', type: 'button', onclick: () => { D.target = S.target; paintDrawer(); } }, `Viser « ${S.target.title} »`)] : null]),
      h('div', {}, h('div', { class: 'eyebrow', style: 'margin-bottom:6px' }, 'Nature'), seg('Nature', Object.entries(NATURE), D.nature, (v) => { D.nature = v; paintDrawer(); })),
      h('label', { class: 'f', for: 'rem-text' }, 'Votre remarque'), ta,
      h('div', { class: 'row' }, btn, count, h('span', { class: 'sp' }), h('kbd', {}, 'Ctrl Entrée')), msg,
      h('p', { class: 'hint', id: 'rem-help' }, 'La remarque est enregistrée dans la KB, signée de votre nom. Claude la lit à la prochaine « reprends », la traite par la méthode, puis y répond ici.'),
      prev.length ? [h('h3', {}, t ? `Déjà écrit sur ce document · ${prev.length}` : `Remarques générales en attente · ${prev.length}`), prev.map((r) => remarkItem(r, true))] : null));
}

// --- base de connaissance : lecteur ------------------------------------------------------------------------------------
const DOC_GROUPS = [['Cahier des charges', ['project', 'cdc', 'personnas', 'juridique']], ['Socle technique', ['stack', 'infra', 'rules']],
  ['Conception', ['interface', 'securite', 'code', 'documentation']], ['Suivi', ['sprints', 'tickets', 'test', 'qualite', 'remarques']]];
const GROUPS = [...DOC_GROUPS.map(([g]) => g), 'Autres'];
const folderOf = (c) => c.path.includes('/') ? c.path.split('/')[0] : '';
const groupOf = (c) => (DOC_GROUPS.find(([, fs]) => fs.includes(folderOf(c))) || ['Autres'])[0];
const folderRank = (c) => { const f = DOC_GROUPS.flatMap(([, fs]) => fs).indexOf(folderOf(c)); return f < 0 ? 99 : f; };
const docOrder = (a, b) => folderRank(a) - folderRank(b) || folderOf(a).localeCompare(folderOf(b)) || (b.slug === 'index') - (a.slug === 'index')
  || String(a.type).localeCompare(String(b.type)) || a.title.localeCompare(b.title);
const readerHref = (c) => `#/kb/${enc(c.path)}`;
function docBox(c, body, done) {
  const box = h('div', { class: 'doc' }, none('Chargement…'));
  api('render', { method: 'POST', json: { body: body ?? c.body ?? '' } }).then((r) => {
    box.innerHTML = r.html || '';  // HTML assaini par le serveur (nh3)
    for (const a of box.querySelectorAll('a[href]')) { const p = kbPath(c.path, a.getAttribute('href')); if (p) a.setAttribute('href', routeOf(p)); }
    if (done) done(box);
  }, (e) => box.replaceChildren(errBox(`Rendu impossible : ${plain(e)}.`)));
  return box;
}
function docActions(c) {
  return h('div', { class: 'row', style: 'gap:8px' },
    waitsForYou(c) ? h('button', { class: 'btn', type: 'button', onclick: () => validate(c) }, '✓ Valider') : null,
    h('a', { class: 'btn o', href: `#/gestion/concepts/${enc(c.path)}` }, 'Modifier'),
    h('button', { class: 'btn o', type: 'button', onclick: () => openDrawer({ path: c.path, title: c.title }) }, '✎ Remarque'));
}
function provenance(c) {
  const g = c.fm.generated || {}, v = c.fm.verified || {};
  return card('Provenance', h('ul', { class: 'list' },
    h('li', {}, h('div', {}, h('div', { class: 'm' }, 'Écrit par'), g.by ? `${agentLabel(g.by)}${g.at ? `, le ${fmtDay(g.at)}` : ''}` : '—')),
    h('li', {}, h('div', {}, h('div', { class: 'm' }, 'Validation'), v.by ? `${verifier(v.by)}${v.at ? `, le ${fmtDay(v.at)}` : ''}` : 'personne pour l’instant')),
    h('li', {}, h('div', {}, h('div', { class: 'm' }, 'Fichier'), h('span', { class: 'mono' }, c.path), ' ', h('button', { class: 'lnk', type: 'button', onclick: () => copy(c.path) }, 'Copier')))));
}
function vKb(path) {
  const c = path ? S.concepts.find((x) => x.path === path) : null;
  if (path && !c) return v404();
  if (c) S.target = { path: c.path, title: c.title };
  const l = S.concepts.filter((x) => x === c || has(`${x.title} ${x.path}`)).sort(docOrder);
  const link = (x) => h('a', { class: 'dl', href: readerHref(x), title: x.title, 'aria-current': x === c ? 'page' : null }, h('i', { class: `dot ${x.trust}`, title: trustWord(x) }), h('span', {}, x.title));
  const byType = (docs) => {
    const types = {}; for (const x of docs) (types[x.type] ||= []).push(x);
    return Object.entries(types).flatMap(([t, xs]) => xs.length > 6 ? [h('details', { class: 'dt', open: xs.includes(c) || !!F.q }, h('summary', {}, `${t} · ${xs.length}`), xs.map(link))] : xs.map(link));
  };
  const aside = h('aside', { class: 'docnav', 'aria-label': 'Documents de la KB' }, filterBar(['q'], {}, 'Filtrer les documents'),
    GROUPS.map((g) => { const docs = l.filter((x) => groupOf(x) === g); return docs.length ? h('details', { open: !c || groupOf(c) === g || !!F.q }, h('summary', {}, g, h('span', { class: 'muted' }, ` ${docs.length}`)), byType(docs)) : null; }),
    l.length ? null : none('Aucun document ne correspond.'));
  if (!c) {
    return h('div', { class: 'reader-wrap' }, aside, h('article', { class: 'reader card' }, pageH('Produit', 'Base de connaissance', 'Tout ce que les agents ont écrit sur le projet. Choisissez un document pour le lire, le valider, le modifier ou le commenter.'),
      h('div', { style: 'margin-top:18px' }, table(['Groupe', 'Documents', 'À valider'], GROUPS.map((g) => { const docs = S.concepts.filter((x) => groupOf(x) === g), f = docs.sort(docOrder)[0];
        return docs.length ? h('tr', {}, td(f ? h('a', { href: readerHref(f) }, g) : g), td(String(docs.length), 'num'), td(String(docs.filter(waitsForYou).length), 'num')) : null; }))),
      h('p', { class: 'muted', style: 'margin-top:14px' }, 'Pastilles : ', h('i', { class: 'dot human', style: 'display:inline-block' }), ' validé par vous · ', h('i', { class: 'dot machine', style: 'display:inline-block' }), ' contrôlé automatiquement · ', h('i', { class: 'dot none', style: 'display:inline-block' }), ' à valider')));
  }
  const toc = h('nav', { class: 'toc', 'aria-label': 'Sommaire du document' });
  const fillToc = (box) => {
    const heads = [...box.querySelectorAll('h2, h3')];
    toc.replaceChildren(...(heads.length ? [h('div', { class: 'gt' }, 'Sur cette page'), ...heads.map((x) => h('button', { type: 'button', class: x.tagName === 'H3' ? 'sub' : '', onclick: () => x.scrollIntoView({ block: 'start' }) }, x.textContent))] : []));
  };
  const i = l.indexOf(c), prev = l[i - 1], nxt = l[i + 1], gen = c.fm.generated || {}, rem = remarksOf(c.path);
  return h('div', { class: 'reader-wrap' }, aside,
    h('article', { class: 'reader card' }, crumbs(['Base de connaissance', '/kb'], [groupOf(c)], [folderOf(c) || 'racine']), h('h1', {}, c.title),
      h('div', { class: 'row', style: 'margin-bottom:10px' }, trustSt(c), c.type === 'Exigence' ? statusSt(c) : null, h('span', { class: 'st a' }, c.type || 'document'),
        gen.by ? h('span', { class: 'muted' }, `Écrit par ${agentLabel(gen.by)}${gen.at ? ` le ${fmtDay(gen.at)}` : ''}`) : null),
      c.fm.description ? h('p', { class: 'lead' }, c.fm.description) : null, docActions(c),
      h('hr', { style: 'border:0;border-top:1px solid var(--line);margin:18px 0' }), docBox(c, undefined, fillToc),
      rem.length ? h('div', { style: 'margin-top:24px' }, h('h2', {}, `Remarques · ${rem.length}`), h('div', { class: 'stack', style: 'gap:10px;margin-top:10px' }, rem.map((r) => remarkItem(r)))) : null,
      h('div', { class: 'row', style: 'margin-top:24px;justify-content:space-between' }, prev ? h('a', { class: 'btn o', href: readerHref(prev) }, `← ${prev.title}`) : h('span'), nxt ? h('a', { class: 'btn o', href: readerHref(nxt) }, `${nxt.title} →`) : null)),
    toc);
}

// --- édition des concepts ----------------------------------------------------------------------------------------------
function editor(c) {
  const m = meta(c); S.target = { path: c.path, title: m.title };
  const fmTa = h('textarea', { id: 'fm', class: 'fm', 'aria-describedby': 'fm-msg', spellcheck: 'false' }), ta = h('textarea', { id: 'body', 'aria-label': 'Contenu (Markdown)' });
  fmTa.value = c.frontmatterYaml || ''; ta.value = c.body || '';
  const fmMsg = h('div', { id: 'fm-msg' }), msg = h('div'), state = h('span', { class: 'muted', role: 'status' }, 'Aucune modification'), pv = h('div', { class: 'pv', 'aria-label': 'Aperçu' });
  let base = c.version, pvTimer;
  const preview = () => { clearTimeout(pvTimer); pvTimer = setTimeout(() => pv.replaceChildren(docBox(c, ta.value)), 350); };
  const dirty = () => { S.dirty = true; state.textContent = 'Modifié, pas encore enregistré'; };
  fmTa.addEventListener('input', dirty); ta.addEventListener('input', () => { dirty(); preview(); });
  const save = async (e) => {
    const btn = e.currentTarget; btn.disabled = true; fmMsg.replaceChildren(); msg.replaceChildren();
    try {
      const r = await api(`concepts/${enc(c.path)}`, { method: 'PUT', json: { frontmatter: fmTa.value, body: ta.value, baseline: base } });
      base = r.version; S.dirty = false; state.textContent = `Enregistré à ${fmtTime(new Date())}`; await load(); toast('Enregistré dans la KB.');
    } catch (err) {
      const text = err.status === 409 ? 'Claude a modifié ce fichier entre-temps. Copiez vos changements, puis rechargez la page.' : err.data && err.data.champ ? err.message : plain(err);
      (err.data && err.data.champ === 'frontmatter' ? fmMsg : msg).replaceChildren(errBox(`Rien n’a changé : ${text}.`));
    }
    btn.disabled = false;
  };
  const list = (l, empty) => l.length ? h('ul', { class: 'list' }, l.map((x) => h('li', {}, h('a', { href: routeOf(x.path) }, x.title)))) : none(empty);
  pv.replaceChildren(docBox(c, ta.value));
  return [crumbs(['Concepts', '/gestion/concepts'], [h('a', { href: routeOf(c.path) }, m.title)], ['Modifier']),
    pageH('Modifier', m.title, null, h('div', { class: 'row' }, h('span', { class: 'st a' }, c.frontmatter.type), trustSt(m), h('span', { class: 'mono muted' }, c.path))),
    h('div', { class: 'alert info' }, h('span', {}, 'Vous modifiez la KB directement. Pour que Claude fasse la correction lui-même, écrivez plutôt une remarque.'),
      h('button', { class: 'btn o s', type: 'button', onclick: () => openDrawer() }, '✎ Remarque pour Claude')),
    h('details', { class: 'card' }, h('summary', {}, h('b', {}, 'En-tête (YAML)'), h('span', { class: 'muted' }, ' — le type ne change jamais')), h('label', { class: 'vh', for: 'fm' }, 'En-tête'), h('div', { style: 'margin-top:10px' }, fmTa), fmMsg),
    h('div', { class: 'editor' }, h('div', {}, h('label', { class: 'f', for: 'body' }, 'Contenu (Markdown)'), ta), h('div', {}, h('div', { class: 'f', style: 'font-size:13.5px;font-weight:600;color:var(--ink-2);margin-bottom:4px' }, 'Aperçu'), pv)),
    h('div', { class: 'savebar' }, h('button', { class: 'btn', type: 'button', onclick: save }, 'Enregistrer'), h('a', { class: 'btn o', href: routeOf(c.path) }, 'Fermer'), state, msg),
    h('div', { class: 'cols' }, h('div', { class: 'stack' }, card('Liens sortants', list(c.liens.sortants, 'Aucun lien.')), card('Liens entrants', list(c.liens.entrants, 'Aucun lien.'))),
      card('Historique', c.historique.length ? table(['Date', 'Qui', 'Quoi'], c.historique.map((x) => h('tr', {}, td(isoDay(x.date), 'num'), td(agentLabel(x.acteur)), td(x.texte)))) : none('Aucun historique.')))];
}
function createForm() {
  const v = (id) => $(id).value.trim(), msg = h('div'), opts = (id, l) => h('datalist', { id }, l.map((x) => h('option', { value: x })));
  const uniq = (f) => [...new Set(S.concepts.map(f).filter(Boolean))].sort();
  const submit = async (e) => {
    e.preventDefault(); const btn = e.submitter; if (btn) btn.disabled = true; msg.replaceChildren();
    const body = { bundle: v('new-bundle'), type: v('new-type'), title: v('new-title'), slug: v('new-slug') };
    const bad = !body.bundle || !body.type || !body.title ? 'dossier, type et titre sont requis' : !/^[a-z0-9][a-z0-9-]*$/.test(body.slug) ? 'identifiant : minuscules, chiffres et tirets uniquement' : null;
    try {
      if (bad) throw new Error(bad);
      const r = await api('concepts', { method: 'POST', json: body });
      await load(); toast(`« ${body.title} » créé.`); location.hash = `#/gestion/concepts/${enc(r.path)}`;
    } catch (err) { msg.replaceChildren(errBox(`Rien n’a été créé : ${err.status === 409 ? `${body.slug} existe déjà dans ${body.bundle}` : err.status === 400 || bad ? err.message : plain(err)}.`)); }
    if (btn) btn.disabled = false;
  };
  const field = (id, label, attrs = {}) => h('label', { class: 'f', for: id }, label, h('input', { id, required: true, ...attrs }));
  return h('details', { class: 'card' }, h('summary', {}, h('b', {}, '+ Nouveau concept')), h('form', { class: 'kpis', style: 'margin-top:12px;align-items:end', onsubmit: submit },
    field('new-bundle', 'Dossier', { list: 'dl-bundle', placeholder: 'tickets' }), opts('dl-bundle', uniq((c) => c.path.includes('/') ? c.path.split('/')[0] : '')),
    field('new-type', 'Type', { list: 'dl-type', placeholder: 'Ticket' }), opts('dl-type', uniq((c) => c.type)),
    field('new-title', 'Titre'), field('new-slug', 'Identifiant', { pattern: '[a-z0-9][a-z0-9\\-]*', placeholder: 'export-csv', title: 'minuscules, chiffres et tirets' }),
    h('div', {}, h('button', { class: 'btn', title: 'Créer le concept' }, 'Créer')), msg));
}
function vConcepts(path) {
  if (path) {
    const box = h('div', { class: 'stack' }, none('Chargement…'));
    api(`concepts/${enc(path)}`).then((c) => box.replaceChildren(...editor(c)), (e) => box.replaceChildren(e.status === 404 ? v404() : errBox(`Lecture impossible : ${plain(e)}.`)));
    return box;
  }
  const cs = S.concepts, uniq = (f) => [...new Set(cs.flatMap(f).filter(Boolean))].sort().map((x) => [x, x]);
  const l = cs.filter((c) => has(c.title + ' ' + c.path) && (!F.dossier || folderOf(c) === F.dossier) && (!F.type || c.type === F.type)
    && (!F.tag || (Array.isArray(c.fm.tags) && c.fm.tags.includes(F.tag))) && (!F.statut || c.fm.status === F.statut) && (!F.validation || TIER[c.trust] === F.validation));
  return [pageH('Vos actions', 'Concepts', 'Tous les fichiers de la KB, pour les modifier directement ou en créer un.'), createForm(),
    filterBar(['q'], { dossier: uniq((c) => [folderOf(c)]), type: uniq((c) => [c.type]), tag: uniq((c) => Array.isArray(c.fm.tags) ? c.fm.tags.map(String) : []), statut: uniq((c) => [c.fm.status]), validation: VALIDATION }, 'Rechercher un concept'),
    h('p', { class: 'muted num' }, plural(l.length, 'concept', 'concepts')),
    l.length ? table(['Concept', 'Type', 'Dossier', 'Validation', ''], l.map((c) => h('tr', {}, td(h('a', { href: routeOf(c.path) }, c.title)), td(c.type || '—'), td(folderOf(c) || 'racine', 'mono'), td(trustSt(c)),
      td(h('a', { class: 'btn o s', href: `#/gestion/concepts/${enc(c.path)}`, 'aria-label': `Modifier ${c.title}` }, 'Modifier')))))
      : empty('Aucun concept ne correspond.', clearBtn(['q', 'dossier', 'type', 'tag', 'statut', 'validation']))];
}
const v404 = () => h('section', { class: 'card' }, h('h1', {}, 'Écran introuvable'), h('p', {}, 'Cet écran n’existe pas, ou le document a été déplacé.'), h('a', { class: 'btn', href: '#/' }, 'Retour à la vue d’ensemble'));

// --- nom (demandé une fois), validation ------------------------------------------------------------------------------------
const slugName = (s) => norm(s).trim().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40);
function me() {
  return new Promise((ok) => {
    const n = store.get('hosa.me'); if (n) return ok(n);
    const d = $('name-dialog'); $('name-input').value = '';
    d.onclose = () => { if (d.returnValue !== 'ok') return ok(''); const v = slugName($('name-input').value); if (v) store.set('hosa.me', v); paintShell(); ok(v); };
    d.returnValue = ''; d.showModal();
  });
}
async function setVerified(c, verified, patch, okMsg) {
  try { await api(`concepts/${enc(c.path)}`, { method: 'PATCH', json: { frontmatter: { ...patch, verified } } }); await load(); toast(okMsg); }
  catch (e) { toast(`Rien n’a changé : ${plain(e)}.`); }
  route();
}
async function validate(c) {
  const name = await me(); if (!name) return;
  await setVerified(c, { by: `human:${name}`, at: `${new Date().toISOString().slice(0, 19)}Z` }, c.type === 'Exigence' ? { status: 'stable' } : {}, `« ${c.title} » validé par vous.`);
}
const unvalidate = (c) => setVerified(c, { by: null, at: null }, {}, `Validation de « ${c.title} » annulée.`);

// --- coque, menu, palette, routes ---------------------------------------------------------------------------------------------
const NAV = [
  ['Pilotage', [['/', 'Vue d’ensemble', '⌂'], ['/avancement', 'Plan d’avancement', '▤'], ['/sprints', 'Sprints', '↻'], ['/tickets', 'Tickets', '▦'], ['/recettes', 'Recettes et qualité', '✓'], ['/consommation', 'Consommation', '◔']]],
  ['Produit', [['/exigences', 'Cahier des charges', '☰'], ['/personas', 'Personas', '☺'], ['/kb', 'Base de connaissance', '❏'], ['/tracabilite', 'Traçabilité', '⇄']]],
  ['Vos actions', [['/gestion/validation', 'À valider', '◎'], ['/remarques', 'Remarques pour Claude', '✎'], ['/journal', 'Journal', '≡'], ['/gestion/concepts', 'Concepts', '✐']]],
];
const ROUTES = [
  [/^\/$/, home, 'Vue d’ensemble'], [/^\/avancement$/, vAvancement, 'Plan d’avancement'],
  [/^\/tickets$/, vTickets, 'Tickets'], [/^\/gestion\/tickets$/, vTickets, 'Tickets'], [/^\/tickets\/(.+)$/, (m) => vTicket(decodeURIComponent(m[1])), 'Ticket'],
  [/^\/sprints$/, vSprints, 'Sprints'], [/^\/sprints\/([^/]+)$/, (m) => vSprint(decodeURIComponent(m[1])), 'Sprint'],
  [/^\/exigences$/, vExigences, 'Cahier des charges'], [/^\/exigences\/([^/]+)$/, (m) => vExigence(decodeURIComponent(m[1])), 'Exigence'],
  [/^\/personas$/, () => vPersonas(), 'Personas'], [/^\/personas\/([^/]+)$/, (m) => vPersonas(decodeURIComponent(m[1])), 'Persona'],
  [/^\/recettes$/, vRecettes, 'Recettes et qualité'], [/^\/consommation$/, vConsommation, 'Consommation'], [/^\/tracabilite$/, vTracabilite, 'Traçabilité'], [/^\/journal$/, vJournal, 'Journal'],
  [/^\/remarques$/, vRemarques, 'Remarques pour Claude'],
  [/^\/kb$/, () => vKb(), 'Base de connaissance'], [/^\/kb\/(.+)$/, (m) => vKb(decodeURIComponent(m[1])), 'Document'],
  [/^\/gestion\/validation$/, vValidation, 'À valider'], [/^\/gestion\/concepts$/, () => vConcepts(), 'Concepts'], [/^\/gestion\/concepts\/(.+)$/, (m) => vConcepts(decodeURIComponent(m[1])), 'Modifier'],
];
const here = () => (location.hash.replace(/^#/, '') || '/').replace(/\/$/, '') || '/';
const WIDE = /^\/kb/;

function paintShell() {
  const p = here();
  const cur = (to) => p === to || (to !== '/' && p.startsWith(to + '/')) || (to === '/tickets' && p === '/gestion/tickets') ? 'page' : null;
  const counts = { '/gestion/validation': [toValidate().length, ''], '/remarques': [openRemarks().length, ' q'] };
  $('nav').replaceChildren(...NAV.map(([g, items]) => h('div', { class: 'grp' }, h('div', { class: 'gt' }, g),
    items.map(([to, label, ic]) => { const [n, cls] = counts[to] || [0];
      return h('a', { href: `#${to}`, 'aria-current': cur(to) }, h('span', { class: 'ic', 'aria-hidden': 'true' }, ic), h('span', {}, label),
        n ? h('span', { class: `badge${cls}`, 'aria-label': `${n} ${to === '/remarques' ? 'en attente' : 'à valider'}` }, String(n)) : null); }))));
  const n = next();
  $('proj').replaceChildren(...(S.ov ? [h('b', {}, projectTitle()), h('div', { class: 'muted' }, n ? `${n.section} · ${n.stage}` : S.ov.plan ? 'Étapes connues faites' : 'Plan à créer')] : [h('span', { class: 'muted' }, 'Lecture de la KB…')]));
  const k = S.kbStatus;
  $('banner').replaceChildren(...(k === undefined ? [] : k && k.git && k.changed > 0 ? [h('div', { class: 'alert', role: 'alert' },
    h('span', {}, h('b', {}, `${plural(k.changed, 'changement', 'changements')} de la KB non sauvegardé${k.changed > 1 ? 's' : ''}.`), ' Lancez ', h('code', {}, '/kb-commit'), ' dans Claude Code pour les enregistrer dans git.'),
    h('button', { class: 'btn o s', type: 'button', onclick: () => copy('/kb-commit') }, 'Copier /kb-commit'),
    h('details', { class: 'files', style: 'flex-basis:100%' }, h('summary', {}, 'Voir les fichiers'),
      h('ul', {}, (k.files || []).slice(0, 20).map((f) => h('li', {}, h('span', { class: 'mono' }, f.path), ' ', st(f.state, f.state === 'supprimé' ? 'b' : f.state === 'nouveau' ? 'e' : 'a', f.state === 'supprimé' ? '✕' : f.state === 'nouveau' ? '+' : '◐'))),
        (k.files || []).length > 20 ? h('li', {}, `et ${k.files.length - 20} autres`) : null)))]
    : k ? [] : [h('div', { class: 'alert info', role: 'status' }, h('span', {}, h('b', {}, 'Sauvegarde de la KB : état inconnu.'), ' Le serveur n’a pas pu le lire pour le moment.'), h('button', { class: 'btn o s', type: 'button', onclick: reload }, 'Réessayer'))]));
  $('freshness').textContent = S.loadedAt ? `KB lue à ${fmtTime(S.loadedAt)}` : '';
  $('user-label').textContent = store.get('hosa.me') || 'Mon nom';
  const th = store.get('hosa.theme');
  $('theme-label').textContent = `Thème : ${th === 'dark' ? 'sombre' : th === 'light' ? 'clair' : 'système'}`;
}
function route() {
  // l'éditeur a des changements non enregistrés : « Relire » ou une remarque envoyée ne le reconstruisent pas
  if (S.dirty && /^\/gestion\/concepts\/./.test(here())) { paintShell(); return; }
  S.target = null;
  paintShell();
  const p = here(), view = $('view');
  const x = ROUTES.map(([re, fn, title]) => [re.exec(p), fn, title]).find(([m]) => m);
  let node, title = 'Écran introuvable';
  if (S.err) node = errBox(S.err, true);
  else if (!S.ov) node = none('Chargement…');
  else if (!x) node = v404();
  else {
    try { node = x[1](x[0]); title = x[2]; }
    catch (e) { console.error(e); node = errBox('Cet écran ne peut pas s’afficher pour le moment.', true); }
  }
  view.className = `view${WIDE.test(p) ? ' wide' : ''}`;
  const act = document.activeElement, keep = act && act.id && view.contains(act) ? [act.id, act.selectionStart] : null;
  view.replaceChildren(...[node].flat(Infinity).filter(Boolean));
  if (keep && $(keep[0])) { const el = $(keep[0]); el.focus({ preventScroll: true }); if (keep[1] != null && el.setSelectionRange) el.setSelectionRange(keep[1], keep[1]); }
  document.title = `${S.target ? S.target.title : title} — Hosa`;
  $('fab').textContent = S.target ? '✎ Remarque sur ce document' : '✎ Remarque pour Claude';
}

// palette de recherche : écrans et documents
let palSel = 0;
function paletteItems(q) {
  const n = norm(q);
  const screens = NAV.flatMap(([, items]) => items.map(([to, label, ic]) => ({ label, kind: 'Écran', href: `#${to}`, ic })));
  const docs = S.concepts.map((c) => ({ label: c.title, kind: c.type || 'Document', href: routeOf(c.path), ic: '·', extra: c.path }));
  return [...screens, ...docs].filter((x) => !n || norm(`${x.label} ${x.kind} ${x.extra || ''}`).includes(n)).slice(0, 40);
}
function paintPalette() {
  const items = paletteItems($('palette-input').value);
  palSel = Math.min(palSel, Math.max(items.length - 1, 0));
  $('palette-list').replaceChildren(...(items.length ? items.map((x, i) => h('li', {}, h('a', { href: x.href, role: 'option', 'aria-selected': String(i === palSel), onclick: () => $('palette').close() },
    h('span', { 'aria-hidden': 'true', style: 'width:18px;text-align:center;color:var(--muted)' }, x.ic), h('span', {}, x.label), h('span', { class: 'k' }, x.kind))))
    : [h('li', { class: 'hint', style: 'padding:12px' }, 'Rien ne correspond.')]));
  const sel = $('palette-list').querySelector('[aria-selected="true"]'); if (sel) sel.scrollIntoView({ block: 'nearest' });
}
function openPalette() { const d = $('palette'); if (d.open) return; $('palette-input').value = ''; palSel = 0; paintPalette(); d.showModal(); $('palette-input').focus(); }
$('palette-input').addEventListener('input', () => { palSel = 0; paintPalette(); });
$('palette-input').addEventListener('keydown', (e) => {
  const n = $('palette-list').querySelectorAll('a').length;
  if (e.key === 'ArrowDown') { e.preventDefault(); palSel = (palSel + 1) % Math.max(n, 1); paintPalette(); }
  else if (e.key === 'ArrowUp') { e.preventDefault(); palSel = (palSel - 1 + n) % Math.max(n, 1); paintPalette(); }
  else if (e.key === 'Enter') { e.preventDefault(); const a = $('palette-list').querySelector('[aria-selected="true"]'); if (a) { location.hash = a.getAttribute('href'); $('palette').close(); } }
});
$('palette').addEventListener('click', (e) => { if (e.target === $('palette')) $('palette').close(); });

// menu mobile et thème
function closeNav() { document.body.classList.remove('nav-open'); $('menu').setAttribute('aria-expanded', 'false'); if (!$('drawer').classList.contains('open')) $('scrim').hidden = true; }
$('menu').addEventListener('click', () => { const open = !document.body.classList.contains('nav-open'); document.body.classList.toggle('nav-open', open); $('menu').setAttribute('aria-expanded', String(open)); $('scrim').hidden = !open; });
$('scrim').addEventListener('click', () => { closeNav(); closeDrawer(); });
$('theme').addEventListener('click', () => {
  const order = [null, 'light', 'dark'], cur = store.get('hosa.theme'), nx = order[(order.indexOf(cur) + 1) % 3];
  if (nx) { store.set('hosa.theme', nx); document.documentElement.dataset.theme = nx; } else { store.del('hosa.theme'); delete document.documentElement.dataset.theme; }
  paintShell();
});
$('drawer').setAttribute('inert', '');
$('fab').addEventListener('click', () => openDrawer());
$('open-palette').addEventListener('click', openPalette);
$('rename').addEventListener('click', () => { const old = store.get('hosa.me'); store.del('hosa.me'); me().then((v) => { if (!v && old) store.set('hosa.me', old); toast(v ? 'Nom enregistré' : 'Nom inchangé'); paintShell(); }); });
$('reload').addEventListener('click', reload);

let lastHash = location.hash;
window.addEventListener('hashchange', () => {
  if (S.dirty && !confirm('Des modifications ne sont pas enregistrées. Quitter quand même ?')) { history.replaceState(null, '', lastHash || '#/'); return; }
  S.dirty = false; lastHash = location.hash; closeNav(); route(); window.scrollTo(0, 0); $('main').focus({ preventScroll: true });
});
window.addEventListener('beforeunload', (e) => { if (S.dirty) { e.preventDefault(); e.returnValue = ''; } });
document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openPalette(); return; }
  if (e.key === 'Escape' && $('drawer').classList.contains('open')) { closeDrawer(); return; }
  if (e.key === 'Escape' && document.body.classList.contains('nav-open')) { closeNav(); return; }
  if (e.key === '/' && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) && !$('palette').open) { e.preventDefault(); const s = $('search'); if (s) s.focus(); else openPalette(); }
});
route();
load().then(route).then(loadUsage).then(route);
