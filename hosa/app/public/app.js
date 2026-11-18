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
// « non relu » est neutre : Hosa ne demande pas de relire chaque fichier, seulement les décisions de « À vous »
const trustWord = (c) => c.trust === 'human' ? 'validé par vous' : c.trust === 'machine' ? 'contrôlé automatiquement' : 'non relu';
const trustSt = (c) => c.trust === 'human' ? st('validé par vous', 'f', '✓') : c.trust === 'machine' ? st('contrôlé automatiquement', 'e', '✓') : st('non relu', 'a', '○');
const byDate = (a, b) => String(b.at || '').localeCompare(String(a.at || ''));
const canValidate = (c) => c.validable && c.trust !== 'human';
const validated = () => S.concepts.filter((c) => c.trust === 'human' && c.fm.verified && c.fm.verified.at).sort((a, b) => String(b.fm.verified.at).localeCompare(String(a.fm.verified.at)));
const isStable = (c) => c.fm.status === 'stable';
const statusSt = (c) => isStable(c) ? st('stable', 'f', '✓') : st('brouillon', 'a', '○');
const aVous = () => (S.ov && S.ov.aVous) || { bloque: [], anomalies: [], questions: [], schemas: [], total: 0 };
const cmdText = (text) => h('div', { class: 'cmdbox' }, h('code', {}, text), h('button', { class: 'btn s', type: 'button', onclick: () => copy(text) }, 'Copier'));
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
// lue seulement par l'écran qui la montre : sa lecture occupe le serveur, et l'écran ouvert (le graphe des tickets
// de rieki) attendait plus de 10 s derrière elle
const USAGE_PAGES = ['/', '/consommation'];
let usageLoading = false;
function ensureUsage() {
  if (S.usage !== undefined || usageLoading || !S.ov || !USAGE_PAGES.includes(here())) return;
  usageLoading = true;
  loadUsage().finally(() => { usageLoading = false; route(); });
}
// la consommation lit tous les transcripts (quelques secondes) : jamais attendue par le premier affichage ni par une écriture
const reload = async () => { S.depFor = undefined; S.usage = undefined; await load(); route(); toast('KB relue'); };

// --- filtres conservés d'un écran à l'autre --------------------------------------------------
const setF = (k, v) => {
  const typing = document.activeElement && document.activeElement.id === 'search';
  F[k] = v; store.set('hosa.filtres', JSON.stringify(F), 'session');
  if (k === 'periode') S.usage = undefined;
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
// La prochaine étape se reprend toujours par « reprends » : la fiche de reprise donne à Claude l'action exacte
// (start, tâche à relancer, questions en attente). Lancer le skill nu la sauterait.
const sectionName = (t) => /^Sprint /.test(t) ? `Sprint · ${sprintName(t.slice(7))}` : t;
function hero() {
  const p = S.ov.plan, n = next(), a = aVous();
  const box = (eyebrow, title, detail, cmd, extra, cls) => h('section', { class: `hero${cls ? ` ${cls}` : ''}`, 'aria-label': 'Prochaine étape' },
    h('div', {}, h('div', { class: 'eyebrow' }, eyebrow), h('h2', {}, title), detail ? h('p', {}, detail) : null), cmdText(cmd), extra);
  if (!p) return box('Pour commencer', 'Pas encore de plan d’avancement', 'Lancez cette commande dans Claude Code : elle écrit le plan depuis la KB.', '/status');
  if (!n) return box('Prochaine étape', 'Toutes les étapes connues sont faites', 'Dites « reprends » dans Claude Code : Claude compose le sprint suivant.', 'reprends');
  if (n.status === 'bloqué' || a.bloque.length) {
    return box(`Claude attend votre réponse · ${sectionName(n.section)}`, `Étape « ${n.stage} » bloquée`, 'Lisez les questions dans « À vous », puis dites « reprends » dans Claude Code et répondez-y.', 'reprends',
      h('p', {}, h('a', { href: '#/a-vous', style: 'color:inherit' }, `Voir ${plural(a.total, 'point qui vous attend', 'points qui vous attendent')}`)), 'wait');
  }
  const dec = a.decision;
  return box(`Prochaine étape · ${sectionName(n.section)}`, n.stage, n.status === 'en cours' ? 'En cours. Si la session est coupée, dites « reprends » dans Claude Code : il repart du point exact.'
    : 'Dites « reprends » dans Claude Code : Claude lance cette étape.', 'reprends',
    dec ? h('p', {}, h('b', {}, 'Ce que Claude vous demandera : '), dec.texte) : null);
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
  const ex = ofType('Exigence').filter((c) => c.status !== 'deprecated'), okEx = ex.filter(isStable).length, board = S.ov.board || [], sp = activeSprint(), u = S.usage;
  const done = board.filter((t) => t.state === 'done').length, blocked = board.filter((t) => t.state === 'blocked').length, cdc = S.ov.cahier;
  return h('div', { class: 'kpis' },
    kpi({ label: 'Exigences stables', value: ex.length ? `${okEx}` : '—', unit: ex.length ? `/ ${ex.length}` : '', bar: ex.length ? meter(okEx, ex.length, 'Exigences stables', true) : null,
      cmp: !ex.length ? 'pas encore rédigées' : cdc && cdc.signe ? '✓ cahier des charges signé' : cdc && cdc.trous ? `${plural(cdc.trous.length, 'trou', 'trous')} à combler avant signature` : `${ex.length - okEx} en brouillon`, href: '#/exigences' }),
    kpi({ label: 'Tickets faits', value: board.length ? `${done}` : '—', unit: board.length ? `/ ${board.length}` : '', bar: board.length ? meter(done, board.length, 'Tickets faits', true) : null,
      cmp: board.length ? (blocked ? `✕ ${plural(blocked, 'ticket bloqué', 'tickets bloqués')}` : 'aucun bloqué') : 'écrits à l’étape backlog', href: '#/tickets' }),
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
    return h('div', {}, h('div', { class: 'phase-h' }, h('b', {}, sectionName(s.title)), h('span', { class: 'muted num' }, s.stages.length ? `${d} / ${s.stages.length}` : 'pas commencé')),
      compact ? meter(d, s.stages.length, s.title, true) : null,
      h('div', { class: 'steps', style: compact ? 'margin-top:8px' : null }, s.stages.map((x) => {
        const [, sym] = ST[x.status] || ST['à faire'];
        return h('span', { class: `step ${cls(x)}`, title: `${x.status}${x.detail ? ` — ${x.detail}` : ''}` }, h('span', { 'aria-hidden': 'true' }, sym), x.stage, h('span', { class: 'vh' }, ` : ${x.status}`));
      })));
  }));
}
const LIVRER_KIND = { recette: 'recette échouée', ticket: 'ticket bloqué', audit: 'audit', sprint: 'sprint' };
function livrerCard() {
  const l = S.ov.livrer || { etat: 'rien', bloquants: [] };
  if (l.etat === 'rien') return h('section', { class: 'card verdict' }, h('div', { class: 'eyebrow' }, 'Peut-on livrer ?'), h('h3', {}, 'Rien à livrer pour l’instant'),
    h('p', { class: 'muted' }, 'Aucun ticket n’est encore fait. La question se pose après le premier sprint.'));
  const b = l.bloquants;
  return h('section', { class: `card verdict${b.length ? ' no' : ''}` }, h('div', { class: 'eyebrow' }, 'Peut-on livrer ?'),
    h('h3', {}, b.length ? `Pas encore — ${plural(b.length, 'point bloque', 'points bloquent')}` : `Oui — ${plural(l.faits, 'ticket fait', 'tickets faits')}, rien ne bloque`),
    b.length ? h('ul', { class: 'list' }, b.map((x) => h('li', {}, st(LIVRER_KIND[x.quoi] || x.quoi, 'b', '✕'), h('div', {}, h('a', { href: routeOf(x.path) }, x.texte)))))
      : h('p', { class: 'muted' }, 'Aucune recette échouée, aucun ticket bloqué, aucun audit en échec, aucun sprint en cours. Dites « livre le projet » dans Claude Code.'));
}
// les points de « À vous », dans l'ordre où ils bloquent le travail ; `max` : la vue d'ensemble n'en montre que quelques-uns
function aVousList(max) {
  const a = aVous(), items = [];
  for (const b of a.bloque) items.push(h('li', {}, st('Claude attend', 'r', '◷'), h('div', {}, h('b', {}, `Étape « ${b.stage} »${b.agent ? ` · ${b.agent}` : ''}`),
    b.lignes.map((l) => h('div', { class: 'm pre' }, l)))));
  for (const x of a.anomalies) items.push(h('li', {}, st('à trancher', 'r', '?'), h('div', {}, h('b', {}, `Anomalie ${x.id}`), h('div', { class: 'm' }, x.texte))));
  for (const x of a.questions) items.push(h('li', {}, st('question', 'r', '?'), h('div', {}, h('b', {}, x.id), h('div', { class: 'm' }, x.texte))));
  if (a.schemas.length) items.push(h('li', {}, st('à valider', 'r', '◎'), h('div', {}, h('b', {}, plural(a.schemas.length, 'schéma de processus à valider', 'schémas de processus à valider')),
    h('div', { class: 'm' }, 'Claude vous les montre dessinés pendant la rédaction du cahier des charges.'), h('ul', { class: 'flat' }, a.schemas.slice(0, max || 99).map((s) => h('li', {}, h('a', { href: routeOf(s.ou) }, docTitle(s.ou)), h('span', { class: 'muted' }, ` — ${s.manque}`)))))));
  return items;
}
const docTitle = (path) => { const c = S.concepts.find((x) => x.path === path); return c ? c.title : path; };
function yourTurn() {
  const a = aVous(), open = openRemarks(), answered = remarques().filter((r) => r.etat === 'traitee').sort((x, y) => String(y.traiteeAt).localeCompare(String(x.traiteeAt))).slice(0, 2);
  const all = aVousList(3), items = all.slice(0, 3);
  return cardH(`À vous${a.total ? ` · ${a.total}` : ''}`, h('a', { href: '#/a-vous' }, 'Tout voir'),
    h('ul', { class: 'list' },
      items.length ? items : h('li', {}, st('rien', 'f', '✓'), h('div', {}, 'Claude n’attend rien de vous.', a.decision ? h('div', { class: 'm' }, `À l’étape « ${a.decision.stage} », il vous demandera : ${a.decision.texte}`) : null)),
      all.length > items.length ? h('li', {}, h('span'), h('a', { href: '#/a-vous' }, `et ${plural(all.length - items.length, 'autre point', 'autres points')}`)) : null,
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
    : sec ? `${sectionName(n.section)} — étape ${sec.stages.findIndex((x) => x.stage === n.stage) + 1} sur ${sec.stages.length}.` : `${sectionName(n.section)}.`;
  return [pageH('Aujourd’hui', `Où en est ${projectTitle()} ?`, where), hero(),
    h('div', { class: 'cols w' }, h('div', { class: 'stack' }, yourTurn(), cardH('Plan d’avancement', h('a', { href: '#/avancement' }, 'Détail'), pipeline(true))),
      h('div', { class: 'stack' }, livrerCard(), sprintCard(), activityCard())),
    kpis()];
}

// --- plan d'avancement ------------------------------------------------------------------------
function vAvancement() {
  const p = S.ov.plan, n = next();
  if (!p) return [pageH('Suivi', 'Plan d’avancement'), hero()];
  const g = (n && n.gaps) || [];
  return [pageH('Suivi', 'Plan d’avancement', 'Les étapes de la méthode, leurs preuves et le travail des agents. Le plan est tenu par Claude ; il se lit ici.'), hero(),
    h('div', { class: 'cols w' },
      h('div', { class: 'stack' }, card('Toutes les étapes', pipeline(false)),
        ...p.sections.map((s) => h('details', { class: 'card' }, h('summary', {}, h('b', {}, sectionName(s.title)), ` · ${s.stages.filter(isClosed).length} / ${s.stages.length}`),
          h('div', { style: 'margin-top:12px' }, stagesTable(s))))),
      h('div', { class: 'stack' },
        card(`Ce qui reste à prouver · ${g.length}`, h('p', { class: 'muted' }, 'Ce que Claude doit encore produire pour clore l’étape en cours. Rien à faire de votre côté.'),
          g.length ? h('ul', { class: 'list' }, g.map((x) => h('li', {}, st('à prouver', 'a', '○'), h('div', { class: 'mono' }, x)))) : none('Rien : l’étape en cours a toutes ses preuves.')),
        card('Point de reprise', (p.resume.length ? p.resume : ['Aucun point de reprise.']).map((l) => h('p', {}, l))))),
    (p.taches || []).length ? card('Tâches des agents', table(['Étape', 'Agent', 'Objet', 'Statut', 'Sortie ou détail'], p.taches.map((t) => h('tr', { class: t.statut === 'bloqué' ? 'fail' : null },
      td(`${t.stage}${t.scope ? ` (${t.scope})` : ''}`), td(t.agent), td(t.objet || ''), td(st(t.statut)), td(t.sortie || t.detail || '', 'muted'))))) : null,
    (p.boucles || []).length ? card('Boucles de correction', h('p', { class: 'muted' }, 'Un retour en arrière entre deux étapes. Au-delà de la borne, Claude s’arrête et vous demande.'),
      table(['Boucle', 'Tours', 'État', 'Détail'], p.boucles.map((b) => h('tr', { class: b.etat === 'ouverte' && b.tours >= b.max ? 'fail' : null },
        td(`${b.from} → ${b.to}${b.scope ? ` (${b.scope})` : ''}`), td(`${b.tours} / ${b.max}`, 'num r'), td(st(b.etat)), td(b.detail || '', 'muted'))))) : null];
}

// les étapes d'une section du plan, avec la décision que chacune vous demandera (`decisions` de pipeline.json)
function stagesTable(s) {
  const dec = S.ov.decisions || {};
  return table(['Étape', 'Statut', 'Date', 'Votre décision', 'Détail'], s.stages.map((x) => h('tr', { class: x.status === 'bloqué' ? 'fail' : null },
    td(x.stage), td(st(x.status)), td(fmtDate(x.at), 'num'), td(dec[x.stage] || '—', dec[x.stage] ? null : 'muted'), td(x.detail || '', 'muted'))), { caption: `Étapes · ${sectionName(s.title)}` });
}
function phaseCard(title) {
  const s = S.ov.plan && S.ov.plan.sections.find((x) => x.title === title);
  return s ? cardH(`Étapes · ${s.stages.filter(isClosed).length} / ${s.stages.length}`, h('a', { href: '#/avancement' }, 'Plan d’avancement'), stagesTable(s))
    : card('Étapes', none('Pas encore de plan d’avancement : dites « reprends » ou lancez /status dans Claude Code.'));
}
const docList = (docs, emptyText) => docs.length ? h('ul', { class: 'list' }, docs.map((c) => h('li', {}, h('i', { class: `dot ${c.trust}`, style: 'margin-top:8px', title: trustWord(c) }),
  h('div', {}, h('a', { class: 't', href: routeOf(c.path) }, c.title), h('div', { class: 'm' }, `${c.type} · ${folderOf(c)}`))))) : none(emptyText);

// --- structuration : stack, données, architecture, menaces, interface ----------------------------------
function vStructuration() {
  const docs = (g) => S.concepts.filter((c) => groupOf(c) === g && c.status !== 'deprecated').sort(docOrder);
  return [pageH('Structuration', 'Structuration', 'Après la signature du cahier des charges : la stack, l’installation, les données, l’architecture, les menaces, l’interface, puis le backlog.'),
    phaseCard('Structuration'),
    h('div', { class: 'cols' }, card('Socle technique', docList(docs('Socle technique'), 'Rien encore : l’étape stack l’écrit.')),
      card('Conception', docList(docs('Conception'), 'Rien encore : les étapes architecture, menaces et interface l’écrivent.')))];
}

// --- sprints ------------------------------------------------------------------------------------
const sprintSt = (s) => s.state === 'done' ? st('terminé', 'f', '✓') : s.state === 'active' ? st('actif', 'e', '◐') : st('prévu', 'a', '○');
function vSprints() {
  const sp = S.ov.sprints || [], v = S.ov.velocite || {};
  if (!sp.length) return [pageH('Sprints', 'Sprints'), empty('Aucun sprint pour l’instant.', h('p', {}, 'Après le backlog, dites « reprends » dans Claude Code : il compose le premier sprint.'), cmdText('reprends'))];
  return [pageH('Sprints', 'Sprints', 'Un sprint est un groupe de tickets construits ensemble, puis montrés et fusionnés.'),
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

// --- planification : le graphe des tickets (`graphe_tickets.py`, le calcul du sprint-planner) ------------------------
function loadDep() {
  const obj = F.objectif || ''; S.depFor = obj; S.dep = undefined;
  return api(`dependances?objectif=${encodeURIComponent(obj)}`).catch((e) => ({ error: e })).then((d) => { if (S.depFor === obj) { S.dep = d; route(); } });
}
const depLink = (t) => h('a', { href: ticketHref(`tickets/${t.slug}.md`) }, t.title);
function vPlanification() {
  const head = [pageH('Sprints', 'Planification', 'Les dépendances entre tickets : ce qui peut se construire maintenant, et le chemin jusqu’à un objectif. Le même calcul compose les sprints.')];
  if (S.depFor !== (F.objectif || '')) { loadDep(); return [...head, none('Calcul du graphe…')]; }
  const d = S.dep;
  if (!d) return [...head, none('Calcul du graphe…')];
  if (d.error) return [...head, errBox(`Graphe indisponible : ${plain(d.error)}.`, true)];
  if (!d.objectifs.length) return [...head, empty('Aucun ticket à faire hors sprint.', h('p', {}, 'L’étape backlog crée les tickets à partir du cahier des charges : dites « reprends » dans Claude Code.'), cmdText('reprends'))];
  const c = d.composition || {}, inSprint = new Set((c.tickets || []).map((t) => t.slug));
  const pick = h('label', { class: 'flt' }, 'Objectif', h('select', { onchange: (e) => setF('objectif', e.target.value) },
    h('option', { value: '' }, 'le premier ticket atteignable'),
    d.objectifs.map((o) => h('option', { value: o.slug, selected: o.slug === F.objectif ? '' : null }, `${o.priority == null ? '—' : o.priority} · ${o.title}`))));
  const obj = d.objectifs.find((o) => o.slug === c.objectif);
  const f = d.feuille, tt = (slug) => (f && f.titres[slug]) || slug;
  const roadmap = f ? card(`Feuille de route · ${plural(f.sprints.length, 'sprint', 'sprints')} à venir`,
    h('p', { class: 'muted' }, `Les jalons validés, puis les sprints calculés depuis le graphe : ${f.plafond} tickets et ${f.demo_max} tests de démo au plus, ${f.tolerance} % de plus pour garder un jalon entier.`),
    table(['Sprint', 'Jalons', 'Tickets', 'Points', 'Démo'], f.sprints.map((sp, i) => h('tr', {}, td(String(i + 1), 'num r'),
      td(sp.jalons.length ? sp.jalons.map(tt).join(' · ') : sp.nature === 'hors parcours' ? 'hors parcours' : 'partie d’un jalon', sp.jalons.length ? null : 'muted'),
      td(String(sp.tickets.length), 'num r'), td(String(sp.points), 'num r'), td(String(sp.demo), 'num r'))), { caption: 'Sprints à venir' }),
    f.bloques.length ? h('div', { class: 'alert err', role: 'alert' }, h('span', {}, h('b', {}, `${plural(f.bloques.length, 'jalon bloqué', 'jalons bloqués')}. `), 'Un ticket de leur chemin est à compléter : Claude le fait à l’étape backlog.'),
      h('ul', { style: 'flex-basis:100%' }, f.bloques.map((b) => h('li', {}, tt(b.jalon))))) : null,
    f.a_completer.length ? h('p', { class: 'hint' }, `${plural(f.a_completer.length, 'ticket à compléter', 'tickets à compléter')}, ${plural(f.en_attente.length, 'ticket en attente', 'tickets en attente')} derrière eux.`) : null)
    : card('Feuille de route', none('Pas encore de jalons validés : le prochain /sprint les propose, une fois.'));
  return [...head, roadmap, h('div', { class: 'filters' }, pick, h('a', { class: 'btn o s', href: '#/planification/graphe' }, 'Naviguer dans le graphe des tickets')),
    c.obstacles && c.obstacles.length ? h('div', { class: 'alert err', role: 'alert' }, h('span', {}, h('b', {}, 'Objectif inatteignable pour l’instant. '), 'À régler d’abord :'),
      h('ul', { style: 'flex-basis:100%' }, c.obstacles.map((o) => h('li', { class: 'mono' }, o)))) : null,
    h('div', { class: 'kpis' },
      kpi({ label: 'Chemin jusqu’à l’objectif', value: String(c.chemin ?? '—'), unit: 'tickets', cmp: c.chemin_points == null ? '' : `${c.chemin_points} points`, href: '#/planification' }),
      kpi({ label: 'Sprint calculé', value: String((c.tickets || []).length), unit: 'tickets', cmp: `plafond ${c.plafond ?? '—'}`, href: '#/planification' }),
      kpi({ label: 'Tests de démo', value: String(c.demo ?? '—'), cmp: `au plus ${c.demo_max ?? '—'}, un par écran`, href: '#/planification' }),
      kpi({ label: 'Prêts maintenant', value: String(d.pret.length), cmp: 'dépendances toutes faites', href: '#/planification' })),
    h('p', { class: 'hint' }, 'Aperçu : les tickets des sprints déjà composés comptent comme livrés.'),
    c.jalon ? h('p', { class: 'hint' }, `L’objectif est trop loin pour un sprint : le sprint va jusqu’à ${plural(c.jalon.length, 'jalon', 'jalons')}, chacun avec tout ce qu’il attend. Il restera ${plural(c.reste, 'ticket', 'tickets')} vers l’objectif.`) : null,
    h('div', { class: 'cols w' },
      card(`Sprint calculé${obj ? ` · objectif « ${obj.title} »` : ''}`, (c.tickets || []).length
        ? table(['#', 'Ticket', 'Points', 'Démo', 'Rôle'], c.tickets.map((t, i) => h('tr', {}, td(String(i + 1), 'num r'), td(depLink(t)), td(String(t.points), 'num r'),
          td(t.ecran ? 'écran' : '—', 'muted'), td(t.objectif ? st('objectif', 'e', '◎') : st('hors objectif', 'a', '○')))), { caption: 'Sprint calculé, dans l’ordre de construction' })
        : none('Rien à mettre dans un sprint tant que les points ci-dessus ne sont pas réglés.')),
      card('Chemin jusqu’à l’objectif', (c.chemin_tickets || []).length
        ? h('ol', { class: 'list' }, c.chemin_tickets.map((t) => h('li', {}, depLink(t), ' ', inSprint.has(t.slug) ? st('ce sprint', 'f', '✓') : t.manques.length ? st('incomplet', 'b', '✕') : t.sprint ? st(`sprint ${t.sprint}`, 'a', '◐') : st('sprint suivant', 'a', '○'))))
        : none('Aucun ticket à construire.'))),
    card('Prêts maintenant', d.pret.length ? table(['Ticket', 'Priorité', 'Points'], d.pret.map((t) => h('tr', {}, td(depLink(t)), td(t.priority == null ? '—' : String(t.priority), 'num r'), td(String(t.points), 'num r'))), { caption: 'Tickets dont les dépendances sont faites' })
      : none('Aucun ticket prêt : chaque ticket à faire attend un autre, ou il est incomplet.'))];
}

// --- graphe des tickets : naviguer dans les dépendances (`depends_on`), le même graphe que la feuille de route ----------
const SVGNS = 'http://www.w3.org/2000/svg';
function sv(tag, attrs = {}, ...kids) {
  const el = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k.startsWith('on')) el.addEventListener(k.slice(2), v); else el.setAttribute(k, v);
  }
  el.append(...kids.flat(Infinity).filter((c) => c != null && c !== false));
  return el;
}
const cut = (s, n) => s.length > n ? `${s.slice(0, n - 1)}…` : s;
const tgState = (t) => t.state === 'done' ? ['fait', 'f', '✓', 'done'] : t.manques.length ? ['incomplet', 'b', '✕', 'bad']
  : t.sprint ? [`sprint ${t.sprint}`, 'e', '◐', 'sprint'] : t.a_detailler ? ['à détailler', 'w', '◌', 'det'] : ['à faire', 'a', '○', 'todo'];
const tgGo = (slug) => { location.hash = `#/planification/graphe/${encodeURIComponent(slug)}`; };

// tout ce qu'un ticket attend (ancêtres) et tout ce qui l'attend (descendants), dans le graphe entier
function tgClosure(by, slug) {
  const up = new Set(), down = new Set(), kids = {};
  for (const t of Object.values(by)) for (const d of t.depends_on) (kids[d] = kids[d] || []).push(t.slug);
  const walk = (s, next, seen) => { for (const x of next(s)) if (!seen.has(x) && by[x]) { seen.add(x); walk(x, next, seen); } };
  walk(slug, (s) => (by[s] ? by[s].depends_on : []), up);
  walk(slug, (s) => kids[s] || [], down);
  return { up, down, kids };
}

// colonnes : un ticket se place une colonne après la plus lointaine de ses dépendances visibles
function tgLayout(by, shown) {
  const col = {}, busy = new Set();
  const colOf = (s) => {
    if (col[s] != null) return col[s];
    if (busy.has(s)) return 0;  // une boucle : ticket_check la signale, le dessin continue
    busy.add(s);
    const deps = by[s].depends_on.filter((d) => shown.has(d));
    col[s] = deps.length ? 1 + Math.max(...deps.map(colOf)) : 0;
    busy.delete(s);
    return col[s];
  };
  shown.forEach(colOf);
  const cols = [];
  for (const s of shown) (cols[col[s]] = cols[col[s]] || []).push(s);
  const rank = (s) => [by[s].feuille ?? 999, by[s].priority ?? 9999, s];
  const cmp = (a, b) => { const x = rank(a), y = rank(b); return x[0] - y[0] || x[1] - y[1] || (x[2] < y[2] ? -1 : 1); };
  const row = {};
  cols.forEach((c, i) => {  // première colonne : ordre de la feuille ; ensuite, près de ses dépendances
    if (i === 0) c.sort(cmp);
    else {
      const bary = (s) => { const r = by[s].depends_on.filter((d) => row[d] != null).map((d) => row[d]); return r.length ? r.reduce((a, b) => a + b, 0) / r.length : 1e6; };
      c.sort((a, b) => bary(a) - bary(b) || cmp(a, b));
    }
    c.forEach((s, j) => { row[s] = j; });
  });
  return { col, row, cols };
}

// colonnes : les sprints — livrés, composés, puis ceux que la feuille de route calcule, puis les tickets qu'elle ne
// place pas ; dans une colonne, l'ordre de construction (profondeur dans le graphe, puis priorité)
function tgSprintLayout(by, shown) {
  const depth = tgLayout(by, shown).col;
  const composed = [...new Set([...shown].filter((s) => by[s].state !== 'done' && by[s].sprint).map((s) => by[s].sprint))].sort();
  const key = (t) => t.state === 'done' ? ['0', 'Livrés']
    : t.sprint ? [`1${t.sprint}`, `Sprint en cours · ${t.sprint}`]
    : t.feuille ? [`2${String(t.feuille).padStart(3, '0')}`, `Feuille de route · S${t.feuille}`]
    : ['3', t.manques.length ? 'Non placés · à compléter' : 'Non placés · en attente'];
  const groups = {};
  for (const s of shown) { const [k, label] = key(by[s]); (groups[k] = groups[k] || { label, items: [] }).items.push(s); }
  const keys = Object.keys(groups).sort();
  if (groups['3']) groups['3'].label = 'Non placés';
  const col = {}, row = {}, cols = [], labels = [];
  keys.forEach((k, i) => {
    const items = groups[k].items.sort((a, b) => depth[a] - depth[b] || (by[a].priority ?? 9999) - (by[b].priority ?? 9999) || (a < b ? -1 : 1));
    items.forEach((s, j) => { col[s] = i; row[s] = j; });
    cols.push(items);
    const pts = items.reduce((n, s) => n + by[s].points, 0);
    labels.push([groups[k].label, `${plural(items.length, 'ticket', 'tickets')} · ${pts} pts`]);
  });
  return { col, row, cols, labels, composed };
}

function vGraphe(sel) {
  const head = [crumbs(['Planification', '/planification'], ['Graphe des tickets']),
    pageH('Sprints', 'Graphe des tickets', 'Par sprint : une colonne par sprint, livrés, en cours, puis ceux que la feuille de route calcule. Par dépendance : chaque ticket après ce qu’il attend. Choisissez un ticket : ce qu’il attend et ce qui l’attend restent visibles, le reste s’efface.')];
  if (S.depFor !== (F.objectif || '')) { loadDep(); return [...head, none('Calcul du graphe…')]; }
  const d = S.dep;
  if (!d) return [...head, none('Calcul du graphe…')];
  if (d.error) return [...head, errBox(`Graphe indisponible : ${plain(d.error)}.`, true)];
  const all = d.tickets || [];
  if (!all.length) return [...head, empty('Aucun ticket.', h('p', {}, 'L’étape backlog crée les tickets à partir du cahier des charges : dites « reprends » dans Claude Code.'), cmdText('reprends'))];
  const by = Object.fromEntries(all.map((t) => [t.slug, t]));
  const cur = sel && by[sel] ? sel : null;
  const { up, down, kids } = cur ? tgClosure(by, cur) : { up: new Set(), down: new Set(), kids: {} };
  const near = new Set(cur ? [cur, ...up, ...down] : []);
  const showDone = F.gFaits === '1', focus = cur && F.gAutour === '1';
  const shown = new Set(all.filter((t) => (showDone || t.state !== 'done' || t.slug === cur) && (!focus || near.has(t.slug))).map((t) => t.slug));
  const q = norm(F.gq || ''), match = new Set(q ? [...shown].filter((s) => norm(`${by[s].title} ${s}`).includes(q)) : []);

  const bySprint = F.gAxe !== 'dependances';
  const W = 236, H = 42, GX = bySprint ? 96 : 84, GY = 12, P = 16, TOP = bySprint ? 46 : 0;
  const { col, row, cols, labels } = bySprint ? tgSprintLayout(by, shown) : tgLayout(by, shown);
  const width = P * 2 + cols.length * W + Math.max(0, cols.length - 1) * GX;
  const height = P * 2 + TOP + Math.max(1, ...cols.map((c) => c.length)) * (H + GY);
  const xy = (s) => [P + col[s] * (W + GX), P + TOP + row[s] * (H + GY)];
  const edges = [];
  for (const s of shown) for (const dep of by[s].depends_on) if (shown.has(dep)) {
    const [x1, y1] = xy(dep), [x2, y2] = xy(s);
    const on = cur && near.has(s) && near.has(dep) && (s === cur || dep === cur || (up.has(s) || s === cur) && up.has(dep) || down.has(s) && (down.has(dep) || dep === cur));
    let d;
    if (x1 < x2) { const a = x1 + W, b = y1 + H / 2, c = x2, e = y2 + H / 2, m = (c - a) / 2; d = `M${a},${b} C${a + m},${b} ${c - m},${e} ${c},${e}`; }
    else {  // même colonne (axe des sprints) : une anse à gauche, de la dépendance au ticket qui l'attend
      const b = y1 + H / 2, e = y2 + H / 2, k = Math.min(GX - 14, 18 + Math.abs(e - b) / 6);
      d = `M${x1},${b} C${x1 - k},${b} ${x2 - k},${e} ${x2},${e}`;
    }
    edges.push(sv('path', { class: `e${on ? ' hl' : ''}`, d, 'marker-end': 'url(#tg-arr)' }));
  }
  const heads = (labels || []).map(([l, sub], i) => sv('g', { class: 'ch', transform: `translate(${P + i * (W + GX)},${P})` },
    sv('text', { x: 0, y: 12, class: 'ct' }, cut(l, 34)), sv('text', { x: 0, y: 28, class: 'cs' }, sub), sv('line', { x1: 0, y1: 36, x2: W, y2: 36 })));
  const nodes = [...shown].map((s) => {
    const t = by[s], [x, y] = xy(s), [label, , sym, cls] = tgState(t);
    const sub = [t.feuille ? `feuille S${t.feuille}` : null, `${t.points} pt${t.points > 1 ? 's' : ''}`, t.priority != null ? `prio ${t.priority}` : null].filter(Boolean).join(' · ');
    const go = () => tgGo(s);
    return sv('g', { class: `n ${cls}${t.jalon ? ' jalon' : ''}${s === cur ? ' sel' : ''}${near.has(s) ? ' hl' : ''}${match.has(s) ? ' match' : ''}`,
      transform: `translate(${x},${y})`, tabindex: '0', role: 'button', 'data-slug': s,
      'aria-label': `${t.title} — ${label}${t.jalon ? ', jalon' : ''}${t.feuille ? `, sprint ${t.feuille} de la feuille de route` : ''}`,
      onclick: go, onkeydown: (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); go(); } } },
      sv('title', {}, `${t.title} (${s})`),
      sv('rect', { width: W, height: H, rx: 7 }),
      sv('text', { x: 10, y: 17, class: 't' }, `${t.jalon ? '◆ ' : ''}${sym} ${cut(t.title, t.jalon ? 29 : 31)}`),
      sv('text', { x: 10, y: 33, class: 'sub' }, sub));
  });
  const svg = sv('svg', { class: `tg${cur ? ' has-sel' : ''}`, width, height, viewBox: `0 0 ${width} ${height}`, role: 'group', 'aria-label': `Graphe de ${shown.size} tickets` },
    sv('defs', {}, sv('marker', { id: 'tg-arr', viewBox: '0 0 8 8', refX: '7', refY: '4', markerWidth: '7', markerHeight: '7', orient: 'auto' }, sv('path', { d: 'M0,0 L8,4 L0,8 z' }))),
    heads, edges, nodes);
  // le ticket choisi au centre du cadre du graphe, sans faire défiler la page (sur téléphone, le titre sortait)
  if (cur) requestAnimationFrame(() => { const w = document.querySelector('.tg-wrap'); if (!w || !shown.has(cur)) return;
    const [x, y] = xy(cur); w.scrollLeft = Math.max(0, x + W / 2 - w.clientWidth / 2); w.scrollTop = Math.max(0, y + H / 2 - w.clientHeight / 2); });

  const counts = all.reduce((k, t) => { const c = tgState(t)[3]; k[c] = (k[c] || 0) + 1; return k; }, {});
  const legend = h('div', { class: 'tg-legend' }, [['todo', 'à faire'], ['det', 'à détailler'], ['sprint', 'dans un sprint'], ['bad', 'incomplet'], ['done', 'fait']]
    .map(([c, l]) => h('span', {}, h('span', { class: `sw ${c}`, 'aria-hidden': 'true' }), `${l} (${counts[c] || 0})`)), h('span', {}, '◆ jalon de la feuille de route'));
  const check = (key, label) => h('label', { class: 'flt' }, h('input', { type: 'checkbox', checked: F[key] === '1' ? '' : null, onchange: (e) => setF(key, e.target.checked ? '1' : '') }), label);
  const axe = h('div', { class: 'seg', role: 'group', 'aria-label': 'Axe des colonnes' },
    [['', 'Par sprint'], ['dependances', 'Par dépendance']].map(([v, l]) =>
      h('button', { type: 'button', 'aria-pressed': String((F.gAxe || '') === v), onclick: () => setF('gAxe', v) }, l)));
  const filters = h('div', { class: 'filters' }, axe,
    h('input', { type: 'search', id: 'search', placeholder: 'Chercher un ticket…', value: F.gq || '', 'aria-label': 'Chercher un ticket',
      oninput: (e) => setF('gq', e.target.value), onkeydown: (e) => { if (e.key === 'Enter' && match.size) tgGo([...match][0]); } }),
    check('gFaits', 'Montrer les tickets faits'), cur ? check('gAutour', 'Seulement autour du ticket choisi') : null,
    cur ? h('a', { class: 'btn o s', href: '#/planification/graphe' }, 'Tout le graphe') : null,
    q ? h('span', { class: 'muted' }, `${plural(match.size, 'ticket trouvé', 'tickets trouvés')}${match.size ? ' — Entrée pour le choisir' : ''}`) : null);

  const t = cur && by[cur];
  const item = (s) => by[s] ? h('li', {}, h('a', { href: `#/planification/graphe/${encodeURIComponent(s)}` }, by[s].title), ' ', st(...tgState(by[s]).slice(0, 3))) : h('li', { class: 'mono' }, `${s} (introuvable)`);
  const panel = t ? card(t.title,
    h('p', {}, st(...tgState(t).slice(0, 3)), t.jalon ? [' ', st('jalon', 'r', '◆')] : null),
    h('ul', { class: 'list' },
      h('li', {}, `Feuille de route : ${t.feuille ? `sprint ${t.feuille}` : t.state === 'done' ? 'livré' : t.sprint ? `sprint composé ${t.sprint}` : 'pas encore placé'}`),
      h('li', {}, `${plural(t.points, 'point', 'points')} · priorité ${t.priority ?? '—'}`),
      h('li', {}, `Attend ${plural(up.size, 'ticket', 'tickets')} au total, ${plural(down.size, 'ticket attend', 'tickets attendent')} celui-ci`)),
    h('h3', {}, `Attend directement (${t.depends_on.length})`), t.depends_on.length ? h('ul', { class: 'list' }, t.depends_on.map(item)) : none('Rien : il peut partir dès qu’il est complet.'),
    h('h3', {}, `Attendu directement par (${(kids[cur] || []).length})`), (kids[cur] || []).length ? h('ul', { class: 'list' }, kids[cur].map(item)) : none('Aucun ticket.'),
    t.manques.length ? [h('h3', {}, 'À compléter'), h('ul', {}, t.manques.map((m) => h('li', { class: 'mono' }, m)))] : null,
    t.a_detailler && t.state !== 'done' ? h('p', { class: 'hint' }, 'Notes à écrire quand il entre dans un sprint (technique, architecture, interface, sécurité, juridique).') : null,
    h('p', {}, h('a', { class: 'btn o s', href: ticketHref(`tickets/${cur}.md`) }, 'Ouvrir le ticket')))
    : card('Choisir un ticket', none('Cliquez un ticket du graphe, ou cherchez-le. Entrée ou Espace le choisit au clavier.'));

  return [...head, filters, legend, h('div', { class: 'cols w tg-cols' }, h('div', { class: 'tg-wrap' }, shown.size ? svg : none('Aucun ticket à montrer avec ces filtres.')), panel)];
}

// --- documentation de Hosa : ses étapes et boucles (pipeline.json), ses skills et agents, le guide du README ----------
function vAide() {
  const head = [pageH('Base de connaissance', 'Documentation de Hosa', 'Comment Hosa mène un projet : les étapes, ce que chacune produit, les retours en arrière possibles, les agents, et le guide complet.')];
  if (S.aide === undefined) { S.aide = null; api('aide').then((d) => { S.aide = d; route(); }, (e) => { S.aide = { error: e }; route(); }); }
  const d = S.aide;
  if (!d) return [...head, none('Chargement de la documentation…')];
  if (d.error) return [...head, errBox(`Documentation indisponible : ${plain(d.error)}.`, true)];
  const n = next(), F0 = (s) => n && n.stage === s;
  const step = (e, i) => h('li', {}, h('details', { class: F0(e.stage) ? 'cur' : null },
    h('summary', {}, h('span', { class: 'num' }, String(i + 1)), h('b', {}, e.stage), e.skill !== e.stage ? h('span', { class: 'muted' }, ` · skill ${e.skill}`) : null,
      F0(e.stage) ? [' ', st('étape en cours', 'r', '●')] : null),
    h('p', {}, e.description || 'Pas de description.'),
    h('p', { class: 'muted' }, 'Lancer : ', h('code', {}, `/${e.skill}`)),
    e.boucles.length ? h('p', { class: 'muted' }, 'Peut renvoyer le travail vers : ',
      e.boucles.map((b, k) => [k ? ' ; ' : '', h('b', {}, b.vers.join(' ou ')), b.puis.length ? `, puis ${b.puis.join(', ')}` : '', ` (${b.max} tours au plus)`])) : null));
  const parcours = card('Le parcours',
    h('p', { class: 'muted' }, 'Hosa enchaîne ces étapes tout seul et ne s’arrête que pour vos décisions. Chaque étape a sa preuve dans la KB : sans elle, elle n’est pas marquée faite. Ouvrez une étape pour lire ce qu’elle fait.'),
    d.pipelines.map((p) => [h('h3', {}, p.titre), h('ol', { class: 'steps' }, p.etapes.map(step))]));
  const agents = card(`Les agents · ${d.agents.length}`,
    h('p', { class: 'muted' }, 'Les skills orchestrent, les agents font le travail, chacun dans son domaine et sur le modèle adapté.'),
    table(['Agent', 'Modèle', 'Rôle'], d.agents.map((a) => h('tr', {}, td(a.nom, 'mono'), td(a.modele || '—', 'muted'), td(a.description))), { caption: 'Les agents de Hosa' }));
  const guide = h('div', { class: 'doc' });
  guide.innerHTML = d.guide;  // HTML assaini par le serveur (nh3), depuis le README de Hosa
  return [...head, d.version ? h('p', { class: 'hint' }, `Version ${d.version}. Cette page lit les fichiers de Hosa lui-même : elle suit chaque mise à jour.`) : null,
    parcours, card('Guide', guide), agents];
}

// --- tickets : tableau en lecture seule — l'état d'un ticket suit ses preuves, Claude le change ----------
const BACKLOG = '__backlog__';
const VALIDATION = [['humain', 'validé par vous'], ['machine', 'contrôlé automatiquement'], ['aucune', 'non relu']];
function tcard(t) {
  return h('article', { class: 'tcard' },
    h('a', { class: 'tt', href: ticketHref(t.path) }, t.title),
    h('div', { class: 'meta' }, t.priority == null ? h('span', {}, 'sans priorité') : h('span', { class: 'prio' }, `P${t.priority}`), h('span', {}, t.points > 0 ? `${t.estimate} · ${plural(t.points, 'pt', 'pts')}` : 'non estimé'),
      h('span', {}, sprintName(t.sprint)), h('span', {}, `critères ${proof(t)}`)),
    t.origine === 'humain' ? h('div', { class: 'row', style: 'gap:6px' }, st('écrit par vous', 'a', '✎')) : null);
}
// sans choix de l'utilisateur, le sprint en cours (ou le prochain prévu) : 149 tickets d'un coup ne se lisent pas
const defaultSprint = () => { const sp = S.ov.sprints || [], a = sp.find((s) => s.state === 'active') || sp.find((s) => s.state === 'planned'); return a ? a.slug : ''; };
function vTickets() {
  const all = (S.ov && S.ov.board) || [];
  if (F.sprint === undefined) F.sprint = defaultSprint();
  const sprints = [...new Set(all.map((t) => t.sprint).filter(Boolean))].map((s) => [s, sprintName(s)]);
  const l = all.filter((t) => (!F.sprint || (F.sprint === BACKLOG ? !t.sprint : t.sprint === F.sprint)) && (!F.origine || t.origine === F.origine)
    && (!F.validation || t.validation === F.validation) && has(t.title + ' ' + t.path));
  const ill = (S.ov.illisibles || []);
  const col = (state) => {
    const list = l.filter((t) => t.state === state), pts = list.reduce((n, t) => n + t.points, 0);
    return h('section', { class: 'col', 'aria-label': stateName(state) },
      h('div', { class: 'col-h' }, st(stateName(state), ...ST[TICKET[state]]), h('span', { class: 'muted num' }, `${list.length} · ${plural(pts, 'pt', 'pts')}`)), list.map(tcard));
  };
  return [pageH('Sprints', 'Tickets', 'L’état d’un ticket suit ses preuves : Claude le passe à « fait » quand ses tests, sa revue et sa recette passent. Un désaccord ? Écrivez une remarque sur le ticket.'),
    filterBar(['q'], { sprint: [...sprints, [BACKLOG, 'Backlog non planifié']], origine: [['humain', 'vous'], ['agent', 'Claude']], validation: VALIDATION }, 'Rechercher un ticket'),
    all.length ? l.length ? h('div', { class: 'board' }, STATES.map(col)) : empty('Aucun ticket ne correspond.', clearBtn(['q', 'sprint', 'origine', 'validation']))
      : empty('Aucun ticket pour l’instant : l’étape backlog les crée à partir des exigences.', cmdText('reprends')),
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
      h('span', { class: 'sp' }), docActions(c))),
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
// la signature : un seul geste, à l'étape contestation, sur le cahier des charges entier — jamais exigence par exigence
function signatureCard() {
  const c = S.ov.cahier;
  if (!c) return null;
  if (c.erreur) return errBox(`Cahier des charges : ${c.erreur}.`);
  const doc = c.document && S.concepts.find((x) => x.path === c.document);
  const head = c.signe ? st('signé', 'f', '✓') : c.trous.length ? st(plural(c.trous.length, 'trou', 'trous'), 'b', '✕') : st('prêt à signer', 'r', '◎');
  const byMat = {}; for (const t of c.trous) (byMat[t.matrice] ||= []).push(t);
  return cardH('Le document', head,
    h('p', {}, c.signe ? 'Vous avez signé le cahier des charges. Une exigence stable change par l’étape changement : dites-le à Claude, ou écrivez une remarque.'
      : 'Vous le signerez une seule fois, en entier, à la fin de l’étape contestation. Claude comble d’abord chaque trou ci-dessous.'),
    doc ? h('p', {}, h('a', { class: 'btn o s', href: routeOf(doc.path) }, 'Lire le cahier des charges assemblé')) : none('Pas encore assemblé : Claude l’assemble pendant la rédaction.'),
    !c.signe && c.trous.length ? h('details', {}, h('summary', {}, `Les ${plural(c.trous.length, 'trou', 'trous')}, par rubrique`),
      Object.entries(byMat).map(([m, l]) => [h('h3', {}, `${m} · ${l.length}`), h('ul', { class: 'flat' }, l.map((t) => h('li', {}, h('span', { class: 'mono' }, t['où']), ` — ${t.trou}`)))])) : null);
}
function vExigences() {
  const ex = ofType('Exigence').filter((c) => c.status !== 'deprecated'), bad = (S.ov.illisibles || []).filter((x) => x.path.startsWith('cdc/'));
  const espaces = [...new Set(ex.map((c) => c.fm.espace).filter(Boolean))].sort().map((v) => [v, v]);
  const rows = ex.filter((c) => has(c.title + ' ' + (c.fm.description || '')) && (!F.statut || (F.statut === 'stable') === isStable(c)) && (!F.espace || c.fm.espace === F.espace) && (!F.persona || serves(c, F.persona)));
  const glossaire = S.concepts.find((c) => c.path === 'cdc/glossaire.md'), okN = ex.filter(isStable).length;
  const others = S.concepts.filter((c) => /^(cdc|juridique|project)\//.test(c.path) && c.type !== 'Exigence' && c.path !== 'cdc/glossaire.md').sort((a, b) => a.title.localeCompare(b.title));
  return [pageH('Cahier des charges', 'Cahier des charges', 'Ce que l’application doit permettre de faire. Une exigence qui ne vous convient pas : écrivez une remarque, Claude la corrige par la méthode.'),
    bad.map((x) => h('div', { class: 'alert', role: 'alert' }, h('span', {}, h('span', { class: 'mono' }, x.path), ` n’apparaît pas dans la liste : ${x.cause}.`))),
    h('div', { class: 'cols w' }, phaseCard('Cahier des charges'), signatureCard()),
    ex.length ? [h('div', { class: 'kpis' },
      kpi({ label: 'Stables', value: String(okN), unit: `/ ${ex.length}`, bar: meter(okN, ex.length, 'Exigences stables', true), cmp: `${ex.length - okN} en brouillon`, href: '#/exigences' }),
      kpi({ label: 'Personas', value: String(ofType('Persona').length), cmp: 'pour qui vous construisez', href: '#/personas' }),
      kpi({ label: 'Remarques ouvertes', value: String(openRemarks().filter((r) => /^cdc\//.test(r.cible || '')).length), cmp: 'sur le cahier des charges', href: '#/remarques' })),
    filterBar(['q'], { statut: [['stable', 'stable'], ['draft', 'brouillon']], espace: espaces, persona: ofType('Persona').map((p) => [p.slug, p.title]) }, 'Rechercher une exigence'),
    rows.length ? table(['Exigence', 'Statut', 'Remarques', ''], rows.map((c) => {
      const rem = remarksOf(c.path).filter((r) => r.etat === 'ouverte').length;
      return h('tr', {}, td([h('a', { href: `#/exigences/${encodeURIComponent(c.slug)}` }, c.title), c.fm.description ? h('div', { class: 'muted', style: 'font-size:13px' }, c.fm.description) : null]),
        td(statusSt(c)), td(rem ? st(`${rem} en attente`, 'r', '◷') : '—'),
        td(h('button', { class: 'btn o s', type: 'button', 'aria-label': `Remarque sur ${c.title}`, onclick: () => openDrawer({ path: c.path, title: c.title }) }, 'Remarque')));
    }), { caption: 'Exigences' }) : empty('Aucune exigence ne correspond.', clearBtn(['q', 'statut', 'espace', 'persona']))]
      : empty('Le cahier des charges n’est pas encore rédigé. Dites « reprends » dans Claude Code.', cmdText('reprends')),
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
  return [slug ? crumbs(['Personas', '/personas'], [ps[0].title]) : null, pageH('Cahier des charges', slug ? ps[0].title : 'Personas', slug ? ps[0].fm.description : 'Les personnes pour qui vous construisez l’application.'),
    ps.length ? h('div', { class: slug ? 'stack' : 'cols' }, ps.map((p) => h('section', { class: 'card' }, h('div', { class: 'card-h' }, h('h2', {}, slug ? 'Profil' : h('a', { href: `#/personas/${encodeURIComponent(p.slug)}` }, p.title)), trustSt(p)),
      slug ? null : h('p', { class: 'muted' }, p.fm.description || ''),
      [['Objectifs', 'Objectifs'], ['Besoins', 'Besoins'], ['Difficultés', 'Pain points']].map(([label, name]) => [h('h3', { style: 'margin-top:12px' }, label), bullets(secOf(p.body, name))]),
      h('div', { class: 'row', style: 'margin-top:12px' }, docActions(p))))) : empty('Aucun persona pour l’instant : la première étape les crée. Dites « reprends » dans Claude Code.', cmdText('reprends')),
    slug ? targetRemarks(ps[0]) : null];
}

// --- recettes et qualité --------------------------------------------------------------------------------
function vRecettes() {
  const r = recettes(), l = r.filter((x) => !F.verdict || x.verdict === F.verdict);
  const audit = (name, a) => h('div', { class: 'kpi', style: 'cursor:default' }, h('span', { class: 'l' }, `Dernier audit ${name}`), h('span', { class: 'v', style: 'font-size:20px' }, a ? (VERD[a.verdict] ? verdict(a.verdict) : a.verdict || 'sans verdict') : st('jamais audité', 'a', '○')),
    h('span', { class: 'c' }, a ? fmtDay(a.at) : 'lancez /qualite ou /securite'));
  const count = (v) => r.filter((x) => x.verdict === v).length;
  return [pageH('Sprints', 'Recettes et qualité', 'Une recette est un test de l’application, fait comme le ferait un utilisateur. Les audits vérifient le code.'),
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
  const head = [pageH('Suivi', 'Consommation', 'Ce que coûte le travail de Claude sur ce projet : par agent ou skill, par modèle. Coût estimé aux prix publics.'),
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
  return [pageH('Suivi', 'Traçabilité', 'Le lien entre une exigence, ses tickets et les fichiers de code. Une exigence finalisée sans fichier est signalée.'), card('Exigences → tickets → code', box),
    h('div', { class: 'cols' }, card('Rechercher un élément', h('div', { class: 'filters', role: 'search' }, h('input', { id: 'search', type: 'search', 'aria-label': 'Rechercher un élément', placeholder: 'fichier, fonction, ticket, exigence ( / )', value: S.gq || '', oninput: (e) => { clearTimeout(timer); timer = setTimeout(() => search(e.target.value), 250); } })), h('div', { style: 'margin-top:12px' }, results)), panel)];
}

// --- journal ----------------------------------------------------------------------------------------------------
function vJournal() {
  const l = S.activity.filter((a) => has(a.text + ' ' + a.bundle) && (!F.acteur || a.acteur === F.acteur) && (!F.dossier || a.bundle === F.dossier));
  const days = [...new Set(l.map((a) => a.date))];
  return [pageH('Suivi', 'Journal', 'Chaque écriture dans la KB, par Claude, par vous ou par l’application.'),
    filterBar(['q'], { acteur: Object.entries(ACTEUR), dossier: [...new Set(S.activity.map((a) => a.bundle))].sort().map((b) => [b, b || 'racine']) }, 'Rechercher dans le journal'),
    !S.activity.length ? empty('Aucune entrée dans les journaux de la KB.') : !l.length ? empty('Aucune entrée ne correspond.', clearBtn(['q', 'acteur', 'dossier']))
      : days.map((d) => cardH(isoDay(d), h('span', { class: 'muted' }, plural(l.filter((a) => a.date === d).length, 'entrée', 'entrées')),
        h('ul', { class: 'list' }, l.filter((a) => a.date === d).map((a) => h('li', {}, h('span', { class: `st ${a.acteur === 'humain' ? 'f' : a.acteur === 'agent' ? 'e' : 'a'}`, title: a.acteurNom }, ACTEUR[a.acteur] || a.acteur),
          h('div', {}, actText(a), h('div', { class: 'm' }, `${a.bundle || 'racine'} · ${a.acteurNom}`)))))))];
}

// --- à vous : ce que Hosa attend de vous, lu dans le plan et la KB ----------------------------------------------------
function vAVous() {
  const a = aVous(), items = aVousList(), done = validated();
  return [pageH('Aujourd’hui', 'À vous', 'Ce que Claude attend de vous pour avancer : les questions d’une étape bloquée, les anomalies et les questions du cahier des charges, les schémas à valider. Vous répondez dans Claude Code : dites « reprends ».'),
    items.length ? [cmdText('reprends'), h('ul', { class: 'list card' }, items)] : empty('Claude n’attend rien de vous pour l’instant.'),
    a.decision ? card('À la prochaine étape', h('p', {}, `L’étape « ${a.decision.stage} » (${sectionName(a.decision.section)}) vous demandera : `, h('b', {}, a.decision.texte))) : null,
    h('details', { class: 'card' }, h('summary', {}, h('b', {}, `Vos validations (${done.length})`)),
      h('div', { style: 'margin-top:12px' }, done.length ? table(['Document', 'Validé le', ''], done.map((c) => h('tr', {}, td(h('a', { href: routeOf(c.path), title: c.title }, c.title)),
        td(fmtDay(c.fm.verified.at), 'num'),
        td(c.validable ? h('button', { class: 'lnk', type: 'button', 'aria-label': `Annuler la validation de ${c.title}`, onclick: () => { if (confirm(`Annuler la validation de « ${c.title} » ?`)) unvalidate(c); } }, 'Annuler la validation') : null)))) : none('Rien encore.')))];
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
  return [pageH('Aujourd’hui', 'Remarques pour Claude', 'Vos corrections, questions et idées sur ce que Claude a produit. Elles sont écrites dans la KB ; Claude les lit et y répond.'),
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
// Valider et Modifier seulement là où le serveur l'accepte (`validable`, `protege` de kb.py) ; sinon la raison
function docActions(c) {
  return h('div', { class: 'row', style: 'gap:8px' },
    canValidate(c) ? h('button', { class: 'btn', type: 'button', onclick: () => validate(c) }, '✓ Valider') : null,
    c.protege ? null : h('a', { class: 'btn o', href: editHref(c) }, 'Modifier'),
    h('button', { class: c.protege ? 'btn act' : 'btn o', type: 'button', onclick: () => openDrawer({ path: c.path, title: c.title }) }, '✎ Remarque'),
    c.protege ? h('span', { class: 'muted', style: 'font-size:13px' }, `Lecture seule : ${c.protege}.`) : null);
}
const editHref = (c) => `#/modifier/${enc(c.path)}`;
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
  const aside = h('aside', { class: 'docnav', 'aria-label': 'Documents de la KB' }, c ? filterBar(['q'], {}, 'Filtrer les documents') : null,
    GROUPS.map((g) => { const docs = l.filter((x) => groupOf(x) === g); return docs.length ? h('details', { open: !c || groupOf(c) === g || !!F.q }, h('summary', {}, g, h('span', { class: 'muted' }, ` ${docs.length}`)), byType(docs)) : null; }),
    l.length ? null : none('Aucun document ne correspond.'));
  if (!c) {
    const cs = S.concepts, uniq = (f) => [...new Set(cs.flatMap(f).filter(Boolean))].sort().map((x) => [x, x]);
    const rows = cs.filter((x) => has(x.title + ' ' + x.path) && (!F.dossier || folderOf(x) === F.dossier) && (!F.type || x.type === F.type)
      && (!F.tag || (Array.isArray(x.fm.tags) && x.fm.tags.includes(F.tag))) && (!F.statut || x.fm.status === F.statut) && (!F.validation || TIER[x.trust] === F.validation)).sort(docOrder);
    return h('div', { class: 'reader-wrap' }, aside, h('article', { class: 'reader card' }, pageH('Base de connaissance', 'Base de connaissance', 'Tout ce que Claude a écrit sur le projet. Ouvrez un document pour le lire ou le commenter. Les fichiers que Hosa tient lui-même sont en lecture seule.'),
      filterBar(['q'], { dossier: uniq((x) => [folderOf(x)]), type: uniq((x) => [x.type]), tag: uniq((x) => Array.isArray(x.fm.tags) ? x.fm.tags.map(String) : []), statut: uniq((x) => [x.fm.status]), validation: VALIDATION }, 'Rechercher un document'),
      h('p', { class: 'muted num' }, plural(rows.length, 'document', 'documents')),
      rows.length ? table(['Document', 'Type', 'Dossier', 'Validation'], rows.map((x) => h('tr', {}, td(h('a', { href: readerHref(x) }, x.title)), td(x.type || '—'), td(folderOf(x) || 'racine', 'mono'),
        td([trustSt(x), x.protege ? h('span', { class: 'muted', title: x.protege }, ' · lecture seule') : null]))), { caption: 'Documents de la KB' })
        : empty('Aucun document ne correspond.', clearBtn(['q', 'dossier', 'type', 'tag', 'statut', 'validation'])),
      h('p', { class: 'muted', style: 'margin-top:14px' }, 'Pastilles : ', h('i', { class: 'dot human', style: 'display:inline-block' }), ' validé par vous · ', h('i', { class: 'dot machine', style: 'display:inline-block' }), ' contrôlé automatiquement · ', h('i', { class: 'dot none', style: 'display:inline-block' }), ' non relu')));
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
  return [crumbs(['Base de connaissance', '/kb'], [h('a', { href: routeOf(c.path) }, m.title)], ['Modifier']),
    pageH('Modifier', m.title, null, h('div', { class: 'row' }, h('span', { class: 'st a' }, c.frontmatter.type), trustSt(m), h('span', { class: 'mono muted' }, c.path))),
    h('div', { class: 'alert info' }, h('span', {}, 'Vous modifiez la KB directement. Pour que Claude fasse la correction lui-même, écrivez plutôt une remarque.'),
      h('button', { class: 'btn o s', type: 'button', onclick: () => openDrawer() }, '✎ Remarque pour Claude')),
    h('details', { class: 'card' }, h('summary', {}, h('b', {}, 'En-tête (YAML)'), h('span', { class: 'muted' }, ' — le type ne change jamais')), h('label', { class: 'vh', for: 'fm' }, 'En-tête'), h('div', { style: 'margin-top:10px' }, fmTa), fmMsg),
    h('div', { class: 'editor' }, h('div', {}, h('label', { class: 'f', for: 'body' }, 'Contenu (Markdown)'), ta), h('div', {}, h('div', { class: 'f', style: 'font-size:13.5px;font-weight:600;color:var(--ink-2);margin-bottom:4px' }, 'Aperçu'), pv)),
    h('div', { class: 'savebar' }, h('button', { class: 'btn', type: 'button', onclick: save }, 'Enregistrer'), h('a', { class: 'btn o', href: routeOf(c.path) }, 'Fermer'), state, msg),
    h('div', { class: 'cols' }, h('div', { class: 'stack' }, card('Liens sortants', list(c.liens.sortants, 'Aucun lien.')), card('Liens entrants', list(c.liens.entrants, 'Aucun lien.'))),
      card('Historique', c.historique.length ? table(['Date', 'Qui', 'Quoi'], c.historique.map((x) => h('tr', {}, td(isoDay(x.date), 'num'), td(agentLabel(x.acteur)), td(x.texte)))) : none('Aucun historique.')))];
}
function vModifier(path) {
  const box = h('div', { class: 'stack' }, none('Chargement…'));
  api(`concepts/${enc(path)}`).then((c) => box.replaceChildren(...(c.protege
    ? [crumbs(['Base de connaissance', '/kb'], [h('a', { href: routeOf(c.path) }, (c.frontmatter && c.frontmatter.title) || c.path)], ['Modifier']),
      h('div', { class: 'alert info' }, h('span', {}, `Ce document est en lecture seule : ${c.protege}. Écrivez une remarque : Claude le corrige par la méthode.`),
        h('button', { class: 'btn act s', type: 'button', onclick: () => openDrawer({ path: c.path, title: (c.frontmatter && c.frontmatter.title) || c.path }) }, '✎ Remarque pour Claude'))]
    : editor(c))), (e) => box.replaceChildren(e.status === 404 ? v404() : errBox(`Lecture impossible : ${plain(e)}.`)));
  return box;
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
// le menu suit le parcours de Hosa : ce qui vous attend, puis les phases de pipeline.json dans leur ordre
// (hosa/app/docs/interface.md liste ces écrans ; test_app.py vérifie qu'ils restent les mêmes)
const NAV = [
  ['Aujourd’hui', [['/', 'Vue d’ensemble', '⌂'], ['/a-vous', 'À vous', '◎'], ['/remarques', 'Remarques pour Claude', '✎']]],
  ['Cahier des charges', [['/exigences', 'Exigences', '☰'], ['/personas', 'Personas', '☺']]],
  ['Structuration', [['/structuration', 'Stack et conception', '▣']]],
  ['Sprints', [['/sprints', 'Sprints', '↻'], ['/planification', 'Planification', '⇶'], ['/tickets', 'Tickets', '▦'], ['/recettes', 'Recettes et qualité', '✓']]],
  ['Suivi', [['/avancement', 'Plan d’avancement', '▤'], ['/journal', 'Journal', '≡'], ['/consommation', 'Consommation', '◔'], ['/tracabilite', 'Traçabilité', '⇄']]],
  ['Base de connaissance', [['/kb', 'Documents', '❏'], ['/aide', 'Documentation de Hosa', '?']]],
];
const ROUTES = [
  [/^\/$/, home, 'Vue d’ensemble'], [/^\/a-vous$/, vAVous, 'À vous'], [/^\/avancement$/, vAvancement, 'Plan d’avancement'], [/^\/structuration$/, vStructuration, 'Stack et conception'],
  [/^\/tickets$/, vTickets, 'Tickets'], [/^\/tickets\/(.+)$/, (m) => vTicket(decodeURIComponent(m[1])), 'Ticket'],
  [/^\/sprints$/, vSprints, 'Sprints'], [/^\/planification$/, vPlanification, 'Planification'],
  [/^\/planification\/graphe(?:\/([^/]+))?$/, (m) => vGraphe(m[1] ? decodeURIComponent(m[1]) : null), 'Graphe des tickets'], [/^\/sprints\/([^/]+)$/, (m) => vSprint(decodeURIComponent(m[1])), 'Sprint'],
  [/^\/exigences$/, vExigences, 'Exigences'], [/^\/exigences\/([^/]+)$/, (m) => vExigence(decodeURIComponent(m[1])), 'Exigence'],
  [/^\/personas$/, () => vPersonas(), 'Personas'], [/^\/personas\/([^/]+)$/, (m) => vPersonas(decodeURIComponent(m[1])), 'Persona'],
  [/^\/recettes$/, vRecettes, 'Recettes et qualité'], [/^\/consommation$/, vConsommation, 'Consommation'], [/^\/tracabilite$/, vTracabilite, 'Traçabilité'], [/^\/journal$/, vJournal, 'Journal'],
  [/^\/remarques$/, vRemarques, 'Remarques pour Claude'], [/^\/aide$/, vAide, 'Documentation de Hosa'],
  [/^\/kb$/, () => vKb(), 'Documents'], [/^\/kb\/(.+)$/, (m) => vKb(decodeURIComponent(m[1])), 'Document'],
  [/^\/modifier\/(.+)$/, (m) => vModifier(decodeURIComponent(m[1])), 'Modifier'],
];
// les adresses d'avant la refonte du menu, gardées par un favori ou un lien d'une remarque
const LEGACY = [[/^\/gestion\/validation$/, '/a-vous'], [/^\/gestion\/tickets$/, '/tickets'], [/^\/gestion\/concepts\/(.+)$/, '/modifier/$1'], [/^\/gestion\/concepts$/, '/kb']];
const here = () => (location.hash.replace(/^#/, '') || '/').replace(/\/$/, '') || '/';
const WIDE = /^\/kb/;

function paintShell() {
  const p = here();
  const cur = (to) => p === to || (to !== '/' && p.startsWith(to + '/')) ? 'page' : null;
  const counts = { '/a-vous': [aVous().total, ''], '/remarques': [openRemarks().length, ' q'] };
  $('nav').replaceChildren(...NAV.map(([g, items]) => h('div', { class: 'grp' }, h('div', { class: 'gt' }, g),
    items.map(([to, label, ic]) => { const [n, cls] = counts[to] || [0];
      return h('a', { href: `#${to}`, 'aria-current': cur(to) }, h('span', { class: 'ic', 'aria-hidden': 'true' }, ic), h('span', {}, label),
        n ? h('span', { class: `badge${cls}`, 'aria-label': `${n} ${to === '/remarques' ? 'en attente de Claude' : 'qui vous attendent'}` }, String(n)) : null); }))));
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
  if (S.dirty && /^\/modifier\/./.test(here())) { paintShell(); return; }
  const legacy = LEGACY.find(([re]) => re.test(here()));
  if (legacy) { history.replaceState(null, '', `#${here().replace(legacy[0], legacy[1])}`); lastHash = location.hash; }
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
  ensureUsage();
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
load().then(route);
