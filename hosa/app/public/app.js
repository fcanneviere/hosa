'use strict';
// Application Hosa — SPA native, routage par le hash, sans réseau externe.

const $ = (id) => document.getElementById(id);
const S = { concepts: [], ov: null, activity: [], kbStatus: undefined, usage: undefined, loadedAt: null, err: null };
// Un seul utilisateur : tout est accessible. Menu : Suivi (lecture) puis Gestion (écriture).
const MENU = [['/', 'Accueil'], ['/avancement', "Plan d'avancement"], ['/exigences', 'Exigences'], ['/tickets', 'Tickets'], ['/sprints', 'Sprints'], ['/recettes', 'Recettes'], ['/consommation', 'Consommation'], ['/tracabilite', 'Traçabilité'], ['/journal', 'Journal'], ['/personas', 'Personas']];
const GESTION = [['/gestion/validation', 'À valider'], ['/gestion/concepts', 'Concepts'], ['/gestion/tickets', 'Tickets']];

// --- utilitaires -----------------------------------------------------------
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'class') el.className = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  el.append(...kids.flat(Infinity).filter((c) => c != null && c !== false));
  return el;
}
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
// date avec l'année (horodatage ISO) ; `isoDay` pour une date AAAA-MM-JJ, sans fuseau
const fmtDay = (s) => { const d = new Date(s); return isNaN(d) ? '—' : d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' }); };
const isoDay = (s) => String(s || '').split('-').reverse().join('/');
const fmtNum = (x) => x.toLocaleString('fr-FR', { maximumFractionDigits: 1 });
const fmtTime = (d) => d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
const plural = (n, one, many) => `${n} ${n > 1 ? many : one}`;
function toast(msg) { const t = $('toast'); t.textContent = msg; t.className = 'show'; setTimeout(() => (t.className = ''), 3500); }
function copy(text) {
  const done = () => toast(`Copié : ${text}`);
  if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, () => toast('Copie impossible : sélectionnez le texte.'));
  else toast('Copie impossible : sélectionnez le texte.');
}
const cmd = (skill) => h('div', { class: 'cmd' }, h('span', {}, `/${skill}`), h('button', { class: 'btn', type: 'button', onclick: () => copy(`/${skill}`) }, 'Copier'));
// statut : toujours mot + symbole + couleur
const ST = { 'à faire': ['a', '○'], 'en cours': ['e', '◐'], fait: ['f', '✓'], 'bloqué': ['b', '✕'], 'non applicable': ['a', '—'] };
const st = (label, kind, sym) => { const [k, s] = ST[label] || [kind || 'a', sym || '']; return h('span', { class: `st ${kind || k}` }, `${label} ${sym ?? s}`.trim()); };
const TICKET = { todo: 'à faire', doing: 'en cours', done: 'fait', blocked: 'bloqué' };
const ticketSt = (t) => st(TICKET[t.state] || 'à faire');
const VERD = { PASS: ['réussi', 'f', '✓'], 'PASS-WITH-NOTES': ['réussi avec remarques', 'a', '✓'], FAIL: ['échoué', 'b', '✕'] };
const verdict = (v) => !v || !VERD[v] ? st('non testé', 'a', '') : st(VERD[v][0], VERD[v][1], VERD[v][2]);
const plain = (e) => { const m = String((e && e.message) || e || ''); return /[\\/`]|\.py|\.md|api|HTTP|json/i.test(m) || !m ? 'une erreur est survenue' : m; };
const pl = (n, one, many) => (n > 1 ? many : one);
const sect = (title, ...kids) => h('section', { class: 'sect' }, title ? h('h2', {}, title) : null, ...kids);
const none = (text, ...extra) => h('p', { class: 'hint' }, text, ...extra);
const errBox = (text, retry) => h('div', { class: 'alert err', role: 'alert' }, h('span', {}, text), retry ? h('button', { class: 'btn warn', onclick: reload }, 'Réessayer') : null);
const subnav = (cur) => h('nav', { class: 'subnav', 'aria-label': 'Gestion' }, GESTION.map(([to, l]) => h('a', { href: `#${to}`, 'aria-current': cur === to ? 'page' : null }, l)));
const crumbs = (...parts) => h('div', { class: 'crumbs' }, parts.flatMap((p, i) => [i ? ' › ' : '', p[1] ? h('a', { href: `#${p[1]}` }, p[0]) : p[0]]));
const copyBtn = (text, label) => h('button', { class: 'lnk', type: 'button', 'aria-label': label || `Copier ${text}`, onclick: () => copy(text) }, 'Copier');
const secOf = (body, name) => ((String(body || '').split(new RegExp(`^## ${name}`, 'm'))[1] || '').split(/^## /m)[0] || '').trim();
const card = (title, ...kids) => h('section', { class: 'card' }, title ? h('h2', {}, title) : null, ...kids);
const table = (head, rows, cls) => h('div', { class: 'tw' }, h('table', { class: cls || '' }, h('thead', {}, h('tr', {}, head.map((x) => h('th', { scope: 'col' }, x)))), h('tbody', {}, rows)));

// --- données ----------------------------------------------------------------
const meta = (c) => {
  const fm = c.frontmatter || {};
  const by = fm.verified && fm.verified.by;
  return { ...c, fm, title: fm.title || c.path, type: fm.type, slug: c.path.replace(/^.*\//, '').replace(/\.md$/, ''),
    trust: !by ? 'none' : String(by).startsWith('human:') ? 'human' : 'machine', status: fm.status || 'stable',
    state: fm.state || 'todo', at: (fm.verified && fm.verified.at) || (fm.generated && fm.generated.at) };
};
const ofType = (t) => S.concepts.filter((c) => c.type === t);
const TIER = { human: 'humain', machine: 'machine', none: 'aucune' };  // mêmes valeurs que `board.validation`
// `hosa-product-owner/1.0` → « Claude · product owner » ; `human:fabien` → « vous (fabien) »
const agentLabel = (by) => { const b = String(by || ''); if (b.startsWith('human:')) return `vous (${b.slice(6)})`; if (b.startsWith('claude-code/')) return 'Claude'; if (b.startsWith('process:')) return 'Application'; const m = b.match(/^hosa-([a-z-]+)\//); return m ? `Claude · ${m[1].replace(/-/g, ' ')}` : b; };
const who = (by, empty) => h('td', { title: by || null }, by ? agentLabel(by) : empty || '—');
const verifier = (by) => by && !String(by).startsWith('human:') ? 'contrôlé automatiquement' : by ? agentLabel(by) : 'personne pour l’instant';
// l'écran d'un concept de la KB : fiche du ticket, de l'exigence, personas, sinon Gestion > Concepts
function routeOf(path) {
  const c = S.concepts.find((x) => x.path === path);
  if (c && c.type === 'Ticket') return `#/tickets/${enc(path.replace(/\.md$/, ''))}`;
  if (c && c.type === 'Exigence') return `#/exigences/${encodeURIComponent(c.slug)}`;
  if (c && c.type === 'Persona') return `#/personas/${encodeURIComponent(c.slug)}`;
  return `#/gestion/concepts/${enc(path)}`;
}
// lien relatif d'un corps Markdown (`../personnas/x.md`) → chemin dans la KB, ou null hors KB
function kbPath(from, href) {
  if (!href || /^[a-z]+:|^#|^\//i.test(href) || !/\.md(#.*)?$/.test(href)) return null;
  const out = from.split('/').slice(0, -1);
  for (const seg of href.replace(/#.*$/, '').split('/')) { if (seg === '..') { if (!out.length) return null; out.pop(); } else if (seg && seg !== '.') out.push(seg); }
  return out.join('/');
}
const trustWord = (c) => c.trust === 'human' ? 'validé par vous' : c.trust === 'machine' ? 'contrôlé automatiquement' : 'à valider';
const trustSt = (c) => st(trustWord(c), c.trust === 'none' ? 'a' : 'f', c.trust === 'none' ? '○' : '✓');
const byDate = (a, b) => String(b.at || '').localeCompare(String(a.at || ''));
const isAgent = (c) => c.status !== 'deprecated' && c.fm.generated && c.fm.generated.by && !String(c.fm.generated.by).startsWith('human:');
const toValidate = () => S.concepts.filter((c) => isAgent(c) && (c.trust !== 'human' || c.status !== 'stable')).sort(byDate);
const validated = () => S.concepts.filter((c) => isAgent(c) && c.trust === 'human' && c.status === 'stable').sort(byDate);

async function load() {
  S.err = null;
  try {
    const [ov, cs, act] = await Promise.all([api('overview'), api('concepts'), api('activity')]);
    S.ov = ov; S.concepts = cs.map(meta); S.activity = act; S.loadedAt = new Date();
  } catch (e) { S.err = `Impossible de lire la KB : ${plain(e)}.`; }
  // état git et consommation : routes à ajouter côté serveur ; absentes → mention explicite
  S.kbStatus = await api('kb-status').catch(() => null);
  S.cov = await api('couverture').catch((e) => ({ error: e }));
  await loadUsage();
}
const loadUsage = async () => {
  const days = F.periode || 7;
  const u = await api('usage?days=' + days).catch((e) => ({ error: e }));
  if (days == (F.periode || 7)) S.usage = u;
};
const reload = async () => { await load(); paint(); toast('KB relue'); };

// --- filtres conservés entre écrans ------------------------------------------
const F = JSON.parse(sessionStorage.getItem('hosa.filtres') || '{"periode":"7"}');
const setF = (k, v) => {
  const typing = document.activeElement && document.activeElement.id === 'search';
  F[k] = v; sessionStorage.setItem('hosa.filtres', JSON.stringify(F)); if (k === 'periode') { S.usage = undefined; loadUsage().then(route); } route();
  const s = $('search'); if (typing && s) { s.focus(); s.setSelectionRange(s.value.length, s.value.length); }
};
const LABELS = { statut: 'Statut', sprint: 'Sprint', q: 'Recherche', periode: 'Période', verdict: 'Verdict', origine: 'Écrit par', validation: 'Validation', espace: 'Espace', persona: 'Persona', acteur: 'Acteur', dossier: 'Dossier', type: 'Type', tag: 'Étiquette' };
let qTimer;
function filterBar(keys, opts = {}) {
  return h('div', { class: 'filters', role: 'search' },
    keys.includes('q') ? h('input', { id: 'search', type: 'search', 'aria-label': 'Rechercher', placeholder: 'Rechercher ( / )', value: F[`q`] || '', oninput: (e) => { clearTimeout(qTimer); qTimer = setTimeout(() => setF('q', e.target.value), 250); } }) : null,
    ...Object.entries(opts.selects || {}).map(([k, vals]) => {
      const set = F[k] && !(k === 'periode' && F[k] === '7');
      const lbl = (vals.find(([v]) => v === F[k]) || [])[1] || F[k];
      return set
        ? h('button', { class: 'chip', type: 'button', 'aria-label': `Retirer le filtre ${LABELS[k]}`, onclick: () => setF(k, k === 'periode' ? '7' : '') }, `${LABELS[k]} : ${lbl} ✕`)
        : h('label', { class: 'flt' }, LABELS[k], ' ', h('select', { onchange: (e) => setF(k, e.target.value) }, k === 'periode' ? null : h('option', { value: '' }, 'tous'), vals.map(([v, l]) => h('option', { value: v, selected: (F[k] || (k === 'periode' ? '7' : '')) === v }, l))));
    }));
}

// --- vues --------------------------------------------------------------------
const sprintName = (slug) => { const x = ((S.ov && S.ov.sprints) || []).find((y) => y.slug === slug); return x ? x.title : slug ? slug.replace(/-/g, ' ').replace(/^./, (m) => m.toUpperCase()) : 'backlog'; };
const next = () => S.ov && S.ov.plan && S.ov.plan.next;
function planCount() {
  const p = S.ov.plan; if (!p) return null;
  const all = p.sections.flatMap((s) => s.stages);
  return { done: all.filter((x) => ['fait', 'non applicable'].includes(x.status)).length, total: all.length };
}
function planCard() {
  const p = S.ov.plan;
  if (!p) return card("Plan d'avancement", none("Pas encore de plan d'avancement, lancer /status"));
  const c = planCount();
  return card(`Plan d'avancement · ${c.done}/${c.total}`, h('div', { class: 'bar', role: 'progressbar', 'aria-valuenow': c.done, 'aria-valuemax': c.total, 'aria-label': 'Étapes closes' }, h('i', { style: `width:${c.total ? (100 * c.done / c.total) : 0}%` })),
    table(['Section', 'Étapes', 'Statut'], p.sections.map((s) => {
      const d = s.stages.filter((x) => ['fait', 'non applicable'].includes(x.status)).length;
      const blocked = s.stages.some((x) => x.status === 'bloqué');
      const doing = s.stages.some((x) => x.status === 'en cours');
      return h('tr', { class: blocked ? 'fail' : '' }, h('td', {}, s.title), h('td', { class: 'num' }, `${d}/${s.stages.length}`),
        h('td', {}, st(blocked ? 'bloqué' : d === s.stages.length ? 'fait' : doing ? 'en cours' : 'à faire')));
    })));
}
function nextCard() {
  const n = next(), p = S.ov.plan;
  if (!p) return card('Prochaine étape', none("Pas encore de plan d'avancement, lancer /status"), cmd('status'));
  if (!n) return card('Prochaine étape', h('p', {}, 'Toutes les étapes connues sont faites. Lancez /sprint pour en composer un nouveau.'), cmd('sprint'));
  return card(`Prochaine étape · ${n.section}`, h('h3', {}, `${n.stage}`), cmd(n.skill), h('p', { class: 'muted' }, 'Copiez cette commande, puis collez-la dans Claude Code.'), n.detail ? h('p', {}, h('b', {}, 'Point de reprise : '), n.detail) : null);
}
function gapsCard() {
  const n = next(), g = (n && n.gaps) || [];
  return sect(`Preuves manquantes · ${g.length}`, g.length ? h('ul', {}, g.map((x) => h('li', {}, st('manquante', 'b', '✕'), ' ', x))) : none('Aucune preuve manquante pour l’étape en cours.'));
}
function ticketRows(list, withSprint) {
  return list.map((t) => h('tr', { class: t.state === 'blocked' ? 'fail' : '' },
    h('td', {}, h('a', { href: `#/tickets/${enc(t.path.replace(/\.md$/, ''))}` }, t.title)), h('td', {}, ticketSt(t)),
    withSprint ? h('td', {}, sprintName(t.fm.sprint)) : null, h('td', { class: /\d/.test(proof(t)) ? 'num' : '' }, proof(t))));
}
const stemOf = (t) => t.path.replace(/^.*\//, '').replace(/\.md$/, '');
const recettesOf = (t) => S.concepts.filter((c) => /^test\//.test(c.path) && !/-technique\.md$/.test(c.path) && c.path.replace(/^.*\//, '').startsWith(stemOf(t) + '-'));
// couverture calculée côté serveur (GET /api/couverture) : `…` pendant le chargement
const proof = (t) => {
  if (!S.cov) return '…';
  if (S.cov.error) return 'Couverture indisponible';
  const v = t && S.cov[t.path];
  return v && v.plan && v.total ? `${v.couverts.length}/${v.total}` : 'non testé';
};
function activeSprint() { return (S.ov.sprints || []).find((s) => s.state === 'active') || (S.ov.sprints || [])[0]; }
function ticketsCard() {
  const sp = activeSprint();
  const list = sp ? sp.tickets.map((x) => ({ ...(S.concepts.find((c) => c.path === x.path) || {}), title: x.title, path: x.path, state: x.state, fm: (S.concepts.find((c) => c.path === x.path) || {}).fm || {} })) : [];
  return card(`Tickets du sprint actif · ${list.length}`, sp ? table(['Ticket', 'Statut', 'Critères'], ticketRows(list)) : none('Aucun sprint — /sprint en compose un à partir du backlog'));
}
function validateCard(title) {
  const l = toValidate();
  return sect(`${title} · ${l.length}`, l.length ? validateList(l.slice(0, 3)) : none('Rien à valider : tout est validé.'),
    l.length > 3 ? h('p', {}, h('a', { href: '#/gestion/validation' }, `Voir les ${l.length}`)) : null);
}
// Titre, Valider, Produit le d'abord : ce qui reste visible sur 390 px ; auteur et validateur passent sous le titre
const byLine = (c) => h('div', { class: 'muted mob' }, `Produit par ${agentLabel(c.fm.generated.by)} · validé par ${verifier(c.fm.verified && c.fm.verified.by)}`);
function validateList(l, detail) {
  return table(detail ? ['Titre', '', 'Produit le', 'Produit par', 'Validé par'] : ['Titre', '', 'Produit le'], l.map((c) => h('tr', {}, h('td', {}, c.title, detail ? byLine(c) : null),
    h('td', {}, h('button', { class: 'btn o', type: 'button', 'aria-label': `Valider ${c.title}`, onclick: () => validate(c) }, 'Valider')),
    h('td', { class: 'num' }, fmtDay(c.fm.generated.at)),
    detail ? who(c.fm.generated.by) : null, detail ? h('td', { title: (c.fm.verified && c.fm.verified.by) || null }, verifier(c.fm.verified && c.fm.verified.by)) : null)), detail ? 'v' : '');
}

function livrerCard() {
  const rec = recettes(), fails = rec.filter((r) => r.verdict === 'FAIL'), blocked = ofType('Ticket').filter((t) => t.state === 'blocked');
  const g = (next() && next().gaps) || [];
  const nb = fails.length + blocked.length + g.length;
  return h('section', { class: 'card', style: `border-color:var(${nb ? '--warn' : '--ok'})` }, h('h2', {}, 'Peut-on livrer ?'),
    h('h3', {}, nb ? `Non — ${plural(nb, 'point bloque', 'points bloquent')}` : 'Oui — rien ne bloque'),
    nb ? h('ul', {}, fails.map((r) => h('li', {}, 'Recette « ', recetteName(r), ' » ', verdict('FAIL'))), blocked.map((t) => h('li', {}, 'Ticket « ', t.title, ' » ', st('bloqué'))), g.map((x) => h('li', {}, 'Preuve manquante : ', x))) : h('p', { class: 'muted' }, 'Aucune recette échouée, aucun ticket bloqué.'));
}
function home() {
  const rec = recettes().slice(0, 3);
  return h('div', { class: 'grid' }, h('div', { class: 'cols' }, nextCard(), livrerCard()),
    h('div', { class: 'cols' }, h('div', { class: 'grid' }, planCard(), gapsCard()), validateCard('À valider')),
    ticketsCard(),
    h('div', { class: 'cols2' }, sect('Dernières recettes', rec.length ? table(['Recette', 'Date', 'Résultat'], rec.map((r) => h('tr', { class: r.verdict === 'FAIL' ? 'fail' : '' }, h('td', {}, recetteName(r)), h('td', { class: 'muted' }, fmtDate(r.at)), h('td', {}, verdict(r.verdict))))) : none('Aucune recette pour le moment.')), usageCard(true)));
}
const reviewOf = (t) => { const m = (String(t.body || '').split(/^## Revue/m)[1] || '').match(/PASS-WITH-NOTES|PASS|FAIL/g); return m ? m[m.length - 1] : null; };
const recettes = () => (S.ov && S.ov.recettes) || [];
// « Export CSV — Martine » : premier mot du titre du persona, sinon son identifiant, sinon le titre seul
const recetteName = (r) => { if (!r.persona) return r.titre; const p = S.concepts.find((c) => c.path === `personnas/${r.persona}.md`); return p && p.fm.title ? `${r.titre} — ${String(p.fm.title).split(/[\s,]/)[0]}` : r.titre; };
const EMPTY_USAGE = 'Aucune donnée de consommation trouvée pour ce projet';
function usageCard(compact) {
  const u = S.usage;
  const title = `Consommation · ${F.periode || 7} jours`;
  if (!u) return sect(title, none('Chargement…'));
  if (u.error && plain(u.error) !== EMPTY_USAGE) return sect(title, none(`Consommation indisponible : ${plain(u.error)}.`));
  if (u.error) return sect(title, none(EMPTY_USAGE + '.'), compact ? h('p', {}, h('a', { href: '#/consommation' }, 'Voir quand les chiffres apparaissent →')) : h('p', {}, 'Les chiffres apparaissent quand des sessions de travail sont enregistrées sur ce poste. Travaillez dans Claude Code, puis cliquez sur « Relire ».'));
  // les deux plus gros consommateurs : mot + symbole + couleur (pas sur la carte compacte, qui n'en montre que deux)
  const tbl = (head, list) => table([head, 'Appels', 'Part'], list.map((r, i) => h('tr', { class: !compact && i < 2 ? 'top' : '' },
    h('td', {}, r.name, !compact && i < 2 ? [' ', st('gros consommateur', 'e', '▲')] : null), h('td', { class: 'num' }, String(r.calls)), h('td', { class: 'num' }, `${roundEven(r.part)} %`))));
  if (compact) return sect(title, tbl('Agent', (u.agents || []).slice(0, 2)), h('a', { href: '#/consommation' }, 'Voir le détail agent · skill · modèle →'));
  return sect(title, h('h3', {}, 'Par agent et skill'), tbl('Agent ou skill', u.agents || []), h('h3', {}, 'Par modèle'), tbl('Modèle', u.models || []),
    h('p', { class: 'muted' }, 'Part : la part du coût estimé de la période.'), u.since ? h('p', { class: 'muted' }, `Source : usage_report.py, historique depuis le ${isoDay(u.since)}`) : null);
}

function vAvancement() {
  const p = S.ov.plan;
  return h('div', { class: 'grid' }, h('h1', {}, "Plan d'avancement"), !p ? none("Pas encore de plan d'avancement, lancer /status") : h('div', { class: 'cols' }, h('div', { class: 'grid' }, nextCard(), gapsCard(),
    card('Point de reprise', (p.resume.length ? p.resume : ['Aucun point de reprise.']).map((l) => h('p', {}, l)))),
    h('div', { class: 'grid' }, p.sections.map((s) => card(s.title, table(['Étape', 'Statut', 'Date', 'Détail'], s.stages.map((x) => h('tr', { class: x.status === 'bloqué' ? 'fail' : '' }, h('td', {}, x.stage), h('td', {}, st(x.status)), h('td', { class: 'num' }, fmtDate(x.at)), h('td', { class: 'muted' }, x.detail || '')))))))));
}
const stateName = (s) => TICKET[s].replace(/^./, (m) => m.toUpperCase());
// arrondi à l'entier pair le plus proche sur .5, comme `:.0f` de usage_report.py
const roundEven = (x) => { const f = Math.floor(x), d = x - f; return d < 0.5 ? f : d > 0.5 ? f + 1 : f % 2 === 0 ? f : f + 1; };
async function moveTicket(t, sel) {
  sel.disabled = true;
  try { await api(`concepts/${enc(t.path)}`, { method: 'PATCH', json: { frontmatter: { state: sel.value } } }); toast(`${t.slug} : ${TICKET[sel.value]}`); await load(); }
  catch (e) { toast(`Rien n'a changé : ${plain(e)}.`); S.err = null; }
  route();
}
const col = (state, list, manage) => {
  const p = list.reduce((n, t) => n + t.points, 0);
  return h('section', { class: 'card col' }, h('h2', {}, st(stateName(state), ...ST[TICKET[state]])),
    h('p', { class: 'muted' }, `${plural(list.length, 'ticket', 'tickets')} · ${plural(p, 'point', 'points')}`),
    ...list.map((t) => h('div', { class: 'tcard' },
      h('span', { class: 'mono' }, t.slug), ' ', copyBtn(t.slug, `Copier le numéro de ${t.slug}`), ' ', h('a', { href: `#/tickets/${enc(t.path.replace(/\.md$/, ''))}` }, t.title),
      h('div', { class: 'muted' }, t.priority == null ? 'sans priorité' : `priorité ${t.priority}`, ' · ', t.points > 0 ? `estimation ${t.estimate}` : 'non estimé', ' · ', sprintName(t.sprint)),
      h('div', { class: 'muted' }, t.origine === 'humain' ? 'écrit par un humain' : 'écrit par Claude'),
      h('div', { class: 'muted' }, `Critères : ${proof(t)}`),
      trustSt({ trust: { humain: 'human', machine: 'machine' }[t.validation] || 'none' }),
      manage ? h('select', { 'aria-label': `Déplacer ${t.slug} vers`, onchange: (e) => moveTicket(t, e.target) },
        h('option', { value: '' }, 'Déplacer vers'), ...['todo', 'doing', 'blocked', 'done'].filter((s) => s !== state).map((s) => h('option', { value: s }, stateName(s)))) : null)));
};
const BACKLOG = '__backlog__';
const VALIDATION = [['humain', 'validé par vous'], ['machine', 'contrôlé automatiquement'], ['aucune', 'à valider']];
const clearBtn = (keys) => h('button', { class: 'btn o', onclick: () => { for (const k of keys) F[k] = ''; setF(keys[0], ''); } }, 'Retirer les filtres');
const has = (hay) => !F.q || hay.toLowerCase().includes(F.q.toLowerCase());
function illisiblesSect() {
  const l = (S.ov && S.ov.illisibles) || [];
  return l.length ? sect(`Fichiers illisibles · ${l.length}`, h('p', { class: 'muted' }, 'Ces fichiers de la KB ne peuvent pas être lus : ils manquent dans les listes tant qu’ils ne sont pas réparés.'),
    table(['Fichier', 'Cause', ''], l.map((x) => h('tr', {}, h('td', { class: 'mono' }, x.path), h('td', {}, x.cause), h('td', {}, copyBtn(x.path)))))) : null;
}
function vTickets(manage) {
  const all = (S.ov && S.ov.board) || [];
  const sprints = [...new Set(all.map((t) => t.sprint).filter(Boolean))].map((s) => [s, sprintName(s)]);
  const l = all.filter((t) => (!F.sprint || (F.sprint === BACKLOG ? !t.sprint : t.sprint === F.sprint)) && (!F.origine || t.origine === F.origine)
    && (!F.validation || t.validation === F.validation) && has(t.title + t.path));
  return h('div', { class: 'grid' }, manage ? subnav('/gestion/tickets') : null, h('h1', {}, 'Tickets'),
    filterBar(['q'], { selects: { sprint: [...sprints, [BACKLOG, 'Backlog non planifié']], origine: [['humain', 'Vous'], ['agent', 'Claude']], validation: VALIDATION } }),
    all.length ? l.length ? h('div', { class: 'board' }, ['todo', 'doing', 'blocked', 'done'].map((s) => col(s, l.filter((t) => t.state === s), manage)))
      : none('Aucun ticket ne correspond.', ' ', clearBtn(['q', 'sprint', 'origine', 'validation']))
      : none('Aucun ticket — /backlog les crée à partir des exigences'), illisiblesSect());
}
function vTicket(path) {
  const c = S.concepts.find((x) => x.path === path + '.md');
  if (!c) return v404();
  const sec = (name) => secOf(c.body, name);
  const cv = S.cov && !S.cov.error ? S.cov[c.path] : null, tests = recettesOf(c);
  const rv = reviewOf(c), notes = sec('Revue').replace(/^.*(PASS-WITH-NOTES|PASS|FAIL).*\n?/m, '').trim();
  return h('div', { class: 'grid' }, crumbs(['Tickets', '/tickets'], [c.title]), h('h1', {}, c.title),
    h('div', { class: 'row' }, ticketSt(c), h('span', { class: 'muted' }, sprintName(c.fm.sprint)), h('span', {}, 'Revue : ', verdict(rv))),
    h('div', { class: 'cols' }, h('div', { class: 'grid' },
      card(`Critères d'acceptation · ${proof(c)}`, !cv ? none(proof(c)) : cv.criteres.length ? h('ul', {}, cv.criteres.map((a) => h('li', {}, h('span', { class: 'mono' }, a), ' ', cv.couverts.includes(a) ? st('couvert', 'f', '✓') : cv.plan ? st('non couvert', 'b', '✕') : st('non testé', 'a', '')))) : none('Aucun critère CAn dans ce ticket.')),
      sect('Revue', notes ? h('pre', { class: 'plain' }, notes) : none('Pas encore de revue.'))),
      h('div', { class: 'grid' }, sect('Preuves', h('p', {}, 'Plan technique : ', !cv ? st('non testé', 'a', '') : cv.plan ? st('écrit', 'f', '✓') : st('manquant', 'b', '✕')),
        tests.length ? tests.map((t) => h('p', {}, verdict((((t.body || '').split(/^## Verdict/m)[1] || '').match(/PASS-WITH-NOTES|PASS|FAIL/) || [])[0]), ' ', t.title)) : h('p', {}, 'Recette : ', st('non testé', 'a', ''))),
        h('details', { class: 'card' }, h('summary', {}, 'Contenu complet'), doc(c)))));
}
// corps rendu et assaini par le serveur (nh3) ; les liens vers la KB ouvrent l'écran du concept
function doc(c, body) {
  const box = h('div', { class: 'doc card' }, 'Chargement…');
  api('render', { method: 'POST', json: { body: body ?? c.body ?? '' } }).then((r) => {
    box.innerHTML = r.html || '';
    for (const a of box.querySelectorAll('a[href]')) { const p = kbPath(c.path, a.getAttribute('href')); if (p) a.setAttribute('href', routeOf(p)); }
  }, (e) => box.replaceChildren(errBox(`Rendu impossible : ${plain(e)}.`)));
  return box;
}
const sprintSt = (s) => s.state === 'done' ? st('terminé', 'f', '✓') : s.state === 'active' ? st('actif', 'e', '◐') : st('prévu', 'a', '○');
const pointsLine = (s) => h('p', {}, sprintSt(s), ` ${plural(s.engages, 'point prévu', 'points prévus')} · ${plural(s.faits, 'point fait', 'points faits')} · reste ${s.restants} · ${s.done}/${s.total} tickets faits`, s.branch ? [' · branche ', h('span', { class: 'mono' }, s.branch)] : null);
function velociteCard() {
  const v = S.ov.velocite || {};
  return card('Vitesse', h('p', { class: 'muted' }, 'Sprint : un groupe de tickets construits ensemble.'), v.moyenne == null ? none('Vitesse moyenne : pas encore de sprint terminé.')
    : [h('p', {}, `vitesse moyenne (points par sprint) : ${fmtNum(v.moyenne)}`), h('p', {}, v.restants == null ? `sprints restants : impossible à estimer, aucun point fait dans les sprints terminés (${plural(v.ouverts, 'point ouvert', 'points ouverts')})` : `sprints restants : ${fmtNum(v.restants)} pour ${plural(v.ouverts, 'point ouvert', 'points ouverts')}`)]);
}
function vSprints() {
  const sp = S.ov.sprints || [];
  return h('div', { class: 'grid' }, h('h1', {}, 'Sprints'), sp.length ? [velociteCard(), ...sp.map((s) => card(null, h('h3', {}, h('a', { href: `#/sprints/${s.slug}` }, s.title)), h('p', { class: 'muted' }, s.description),
    pointsLine(s), h('div', { class: 'bar' }, h('i', { style: `width:${s.engages ? 100 * s.faits / s.engages : 0}%` }))))] : none('Aucun sprint — /sprint en compose un à partir du backlog'));
}
function vSprint(slug) {
  const s = (S.ov.sprints || []).find((x) => x.slug === slug); if (!s) return v404();
  const b = s.audit.bloquants;
  return h('div', { class: 'grid' }, crumbs(['Sprints', '/sprints'], [s.title]), h('h1', {}, s.title), h('p', {}, s.description), pointsLine(s),
    table(['Ticket', 'Statut'], s.tickets.map((t) => h('tr', {}, h('td', {}, h('a', { href: routeOf(t.path) }, t.title)), h('td', {}, ticketSt(t))))),
    card('Audit et démo', h('p', {}, 'Bloquants : ', b == null ? st('Jamais audité', 'a', '○') : b ? st(plural(b, 'bloquant', 'bloquants'), 'b', '✕') : st('aucun bloquant', 'f', '✓')),
      h('p', { class: 'muted' }, 'Démo : les tests T1, T2… que vous faites vous-même avant de fusionner un sprint.'),
      s.demo.length ? h('ul', {}, s.demo.map((d) => h('li', {}, h('span', { class: 'mono' }, d.t), ' ', d.ok ? st('OK', 'f', '✓') : st('KO', 'b', '✕')))) : none('Pas encore de démo.')),
    card('Mesures', (s.mesures || []).length ? h('ul', {}, s.mesures.map((m) => h('li', {}, m))) : none('Pas encore mesuré : le bilan du sprint écrit ces chiffres.')));
}
const isStable = (c) => c.fm.status === 'stable';
const statusSt = (c) => isStable(c) ? st('finalisée', 'f', '✓') : st('brouillon', 'a', '○');
const serves = (c, persona) => kbLinks(c).includes(`personnas/${persona}.md`);
const kbLinks = (c) => [...String(c.body || '').matchAll(/\]\(([^)\s]+\.md)/g)].map((m) => kbPath(c.path, m[1])).filter(Boolean);
function vExigences() {
  const ex = ofType('Exigence'), bad = ((S.ov && S.ov.illisibles) || []).filter((x) => x.path.startsWith('cdc/'));
  const espaces = [...new Set(ex.map((c) => c.fm.espace).filter(Boolean))].sort().map((v) => [v, v]);
  const rows = ex.filter((c) => has(c.title) && (!F.statut || (F.statut === 'stable') === isStable(c)) && (!F.espace || c.fm.espace === F.espace) && (!F.persona || serves(c, F.persona)));
  const waiting = (c) => c.trust === 'none' || !isStable(c);
  const glossaire = S.concepts.find((c) => c.path === 'cdc/glossaire.md');
  return h('div', { class: 'grid' }, h('h1', {}, 'Exigences'), h('p', { class: 'muted' }, 'Ce que l’application doit permettre de faire. Vous validez chacune une fois qu’elle vous convient.'),
    bad.map((x) => h('div', { class: 'alert', role: 'alert' }, h('span', {}, h('span', { class: 'mono' }, x.path), ` n’apparaît pas dans la liste : ${x.cause}.`))),
    ex.length ? [h('p', {}, h('b', {}, `${ex.filter((c) => c.trust === 'human').length} / ${ex.length} validées par vous`), h('span', { class: 'muted' }, ` · ${ex.filter(isStable).length} finalisées`)),
      filterBar(['q'], { selects: { statut: [['stable', 'finalisée'], ['draft', 'brouillon']], espace: espaces, persona: ofType('Persona').map((p) => [p.slug, p.title]) } }),
      rows.length ? table(['Exigence', 'Statut', 'Validation', ''], rows.map((c) => h('tr', {}, h('td', {}, h('a', { href: `#/exigences/${encodeURIComponent(c.slug)}` }, c.title)), h('td', {}, statusSt(c)), h('td', {}, trustSt(c)),
        h('td', {}, waiting(c) ? h('button', { class: 'btn o', type: 'button', 'aria-label': `Valider ${c.title}`, onclick: () => validate(c) }, 'Valider') : null))))
        : none('Aucune exigence ne correspond.', ' ', clearBtn(['q', 'statut', 'espace', 'persona']))]
      : none('Le cahier des charges n’est pas encore rédigé — lancer /interview puis /redaction'),
    glossaire ? h('details', { class: 'card' }, h('summary', {}, 'Glossaire — les termes du projet et leur sens'), doc(glossaire)) : null);
}
function vExigence(slug) {
  const c = ofType('Exigence').find((x) => x.slug === slug); if (!c) return v404();
  return h('div', { class: 'grid' }, crumbs(['Exigences', '/exigences'], [c.title]), h('h1', {}, c.title), h('p', {}, c.fm.description || ''), h('div', { class: 'row' }, statusSt(c), trustSt(c)),
    doc(c));
}
// listes Markdown d'une section, sans balisage : une ligne par puce
const bullets = (text) => text ? h('ul', {}, text.split('\n').map((l) => l.trim()).filter(Boolean).map((l) => h('li', {}, l.replace(/^[-*]\s+/, '').replace(/\*\*/g, '')))) : h('p', { class: 'muted' }, 'non documenté');
function vPersonas(slug) {
  const ps = ofType('Persona').filter((p) => !slug || p.slug === slug);
  if (slug && !ps.length) return v404();
  return h('div', { class: 'grid' }, h('h1', {}, 'Personas'), h('p', { class: 'muted' }, 'Les personnes pour qui vous construisez l’application.'), ps.length ? ps.map((p) => card(null, h('h3', {}, p.title), h('p', {}, p.fm.description || ''), h('div', { class: 'row' }, trustSt(p)),
    [['Objectifs', 'Objectifs'], ['Besoins', 'Besoins'], ['Difficultés', 'Pain points']].map(([label, name]) => [h('h2', {}, label), bullets(secOf(p.body, name))]))) : none('Aucun persona — /hosa les crée'));
}
function vRecettes() {
  const r = recettes(), v = F.verdict;
  const l = r.filter((x) => !v || x.verdict === v);
  const audit = (a) => a ? [fmtDay(a.at), ' — ', VERD[a.verdict] ? verdict(a.verdict) : a.verdict || 'sans verdict'] : st('Jamais audité', 'a', '');
  return h('div', { class: 'grid' }, h('h1', {}, 'Recettes'), h('p', { class: 'muted' }, 'Une recette est un test de l’application, fait comme le ferait un utilisateur.'),
    filterBar(['verdict'], { selects: { verdict: ['PASS', 'PASS-WITH-NOTES', 'FAIL'].map((x) => [x, VERD[x][0]]) } }),
    l.length ? table(['Recette', 'Date', 'Résultat'], l.map((x) => h('tr', { class: x.verdict === 'FAIL' ? 'fail' : '' }, h('td', {}, recetteName(x)), h('td', { class: 'num' }, fmtDate(x.at)), h('td', {}, verdict(x.verdict))))) : none(r.length ? 'Aucune recette ne correspond.' : 'Aucune recette pour le moment.'),
    sect('Derniers audits', h('p', {}, 'Qualité : ', audit(S.ov.quality)), h('p', {}, 'Sécurité : ', audit(S.ov.security))));
}
function vConsommation() {
  return h('div', { class: 'grid' }, h('h1', {}, 'Consommation'), filterBar(['periode'], { selects: { periode: [['7', '7 derniers jours'], ['30', '30 derniers jours']] } }), usageCard(false));
}
const KIND = { exigence: 'exigence', ticket: 'ticket', file: 'fichier', class: 'classe', function: 'fonction', method: 'méthode' };
const nodeName = (n) => n.label || String(n.id).split(':').slice(1).join(':') || n.id;
const nodeLink = (n) => n.kb ? h('a', { href: routeOf(n.kb) }, nodeName(n)) : nodeName(n);
const flat = (nodes) => nodes.length ? h('ul', { class: 'flat' }, nodes.map((n) => h('li', {}, nodeLink(n)))) : null;
function nodePanel(id, panel) {
  panel.replaceChildren(h('p', { class: 'muted' }, 'Chargement…'));
  api(`graph/node?id=${encodeURIComponent(id)}`).then((d) => {
    const rel = (l, dir) => l.length ? table(['Relation', 'Élément', 'Type'], l.map((e) => h('tr', {}, h('td', {}, `${dir} ${e.rel}`), h('td', {}, nodeLink(e.node)), h('td', {}, KIND[e.node.kind] || e.node.kind)))) : null;
    panel.replaceChildren(h('h2', {}, `${KIND[d.node.kind] || d.node.kind} · ${nodeName(d.node)}`), d.node.file ? h('p', { class: 'mono muted' }, d.node.file + (d.node.line ? `:${d.node.line}` : '')) : null,
      sect('Relations', rel(d.out, '→'), rel(d.in, '←'), d.out.length + d.in.length ? null : none('Aucune relation.')),
      sect('Impact', d.affected.nodes.length ? table(['Profondeur', 'Élément', 'Type'], d.affected.nodes.map((x) => h('tr', {}, h('td', { class: 'num' }, String(x.depth)), h('td', {}, nodeLink(x.node)), h('td', {}, KIND[x.node.kind] || x.node.kind)))) : none('Rien d’autre ne dépend de cet élément.')),
      sect('Tickets concernés', flat(d.affected.tickets) || none('Aucun ticket ne touche les fichiers impactés.')));
  }, (e) => panel.replaceChildren(errBox(e.status === 404 ? 'Élément introuvable' : `Traçabilité indisponible : ${plain(e)}.`)));
}
function vTracabilite() {
  const box = h('div', {}, h('p', { class: 'muted' }, 'Chargement…')), results = h('div'), panel = h('div', { class: 'card', 'aria-live': 'polite' }, none('Choisissez un élément pour voir ses relations et son impact.'));
  // recherche pendant la frappe ; la saisie survit aux redessins de l'écran (S.gq)
  const search = (q) => { S.gq = q; if (!q.trim()) return results.replaceChildren(); results.replaceChildren(h('p', { class: 'muted' }, 'Chargement…'));
    api(`graph/find?q=${encodeURIComponent(q)}`).then((l) => results.replaceChildren(l.length ? table(['Élément', 'Type', 'Fichier'], l.map((n) => h('tr', {}, h('td', {}, h('button', { class: 'lnk', type: 'button', onclick: () => nodePanel(n.id, panel) }, nodeName(n))), h('td', {}, KIND[n.kind] || n.kind), h('td', { class: 'mono muted' }, n.file || '')))) : none('Aucun élément ne correspond')),
      (e) => results.replaceChildren(errBox(`Traçabilité indisponible : ${plain(e)}.`))); };
  let timer;
  if (S.gq) search(S.gq);
  api('graph/trace').then((t) => box.replaceChildren(t.length ? table(['Exigence', 'Statut', 'Tickets', 'Fichiers'], t.map((e) => {
    const n = e.tickets.reduce((k, x) => k + x.files.length, 0), alone = e.node.status === 'stable' && !n;
    return h('tr', { class: alone ? 'fail' : '' }, h('td', {}, nodeLink(e.node)), h('td', {}, e.node.status === 'stable' ? st('finalisée', 'f', '✓') : st('brouillon', 'a', '○'), alone ? [' ', st('Sans fichier lié', 'b', '✕')] : null),
      h('td', {}, flat(e.tickets.map((x) => x.node)) || st('aucun ticket', 'a', '—')), h('td', { class: 'num' }, String(n)));
  })) : none('Aucune exigence dans le graphe')),
    (e) => box.replaceChildren(/graphe absent/i.test(e.message) ? errBox(`${e.message}.`, true) : errBox(`Traçabilité indisponible : ${plain(e)}.`, true)));
  return h('div', { class: 'grid' }, h('h1', {}, 'Traçabilité'), h('p', { class: 'muted' }, 'Traçabilité : le lien entre une exigence, ses tickets et les fichiers de code.'), box,
    sect('Rechercher un élément', h('div', { class: 'filters', role: 'search' }, h('input', { id: 'search', type: 'search', 'aria-label': 'Rechercher un élément', placeholder: 'fichier, fonction, ticket, exigence ( / )', value: S.gq || '', oninput: (e) => { clearTimeout(timer); timer = setTimeout(() => search(e.target.value), 250); } })), results), panel);
}
// seul le slug cité devient un lien, le reste de la phrase reste du texte
const linkSlug = (text, path) => { const slug = path.replace(/^.*\//, '').replace(/\.md$/, ''), i = text.indexOf(`\`${slug}\``);
  return i < 0 ? text : [text.slice(0, i), h('a', { href: routeOf(path) }, slug), text.slice(i + slug.length + 2)]; };
const ACTEUR = { humain: 'Vous', processus: 'Application', agent: 'Claude' };
function vJournal() {
  const l = S.activity.filter((a) => has(a.text + a.bundle) && (!F.acteur || a.acteur === F.acteur) && (!F.dossier || a.bundle === F.dossier));
  const days = [...new Set(l.map((a) => a.date))];
  return h('div', { class: 'grid' }, h('h1', {}, 'Journal'),
    filterBar(['q'], { selects: { acteur: Object.entries(ACTEUR), dossier: [...new Set(S.activity.map((a) => a.bundle))].sort().map((b) => [b, b || 'racine']) } }),
    !S.activity.length ? none('Aucune entrée dans les journaux de la KB') : !l.length ? none('Aucune entrée ne correspond', ' ', clearBtn(['q', 'acteur', 'dossier']))
      : days.map((d) => sect(isoDay(d), table(['Acteur', 'Dossier', 'Action'], l.filter((a) => a.date === d).map((a) => h('tr', {},
        h('td', { title: a.acteurNom }, ACTEUR[a.acteur] || a.acteur), h('td', {}, a.bundle || 'racine'), h('td', {}, a.lien ? linkSlug(a.text, a.lien) : a.text)))))));
}
function vValidation() {
  const l = toValidate();
  const done = validated();
  return h('div', { class: 'grid' }, subnav('/gestion/validation'), h('h1', {}, 'À valider'), h('p', { class: 'muted' }, 'Ce que Claude a produit et que vous n’avez pas encore validé.'),
    l.length ? validateList(l, true) : none('Rien à valider : tout est validé.'),
    h('details', { class: 'card' }, h('summary', {}, `Déjà validé (${done.length})`),
      table(['Titre', '', 'Validé le', 'Produit par', 'Validé par'], done.map((c) => h('tr', {}, h('td', {}, c.title, byLine(c)),
        h('td', {}, h('button', { class: 'lnk', type: 'button', 'aria-label': `Annuler la validation de ${c.title}`, onclick: () => { if (confirm(`Annuler la validation de « ${c.title} » ?`)) unvalidate(c); } }, 'Annuler la validation')),
        h('td', { class: 'num' }, fmtDay(c.fm.verified.at)), who(c.fm.generated.by), h('td', { title: c.fm.verified.by }, verifier(c.fm.verified.by)))), 'v')));
}
function editor(c) {
  const fmTa = h('textarea', { id: 'fm', class: 'fm', 'aria-label': 'En-tête', 'aria-describedby': 'fm-msg' }), ta = h('textarea', { id: 'body', 'aria-label': 'Contenu' });
  fmTa.value = c.frontmatterYaml || ''; ta.value = c.body || '';
  const fmMsg = h('div', { id: 'fm-msg' }), msg = h('div'), state = h('span', { class: 'muted' }, 'Aucune modification'), prev = h('div');
  let base = c.version;
  const dirty = () => { S.dirty = true; state.textContent = 'Modifié, pas encore enregistré'; };
  fmTa.addEventListener('input', dirty); ta.addEventListener('input', dirty);
  const save = async (e) => {
    const btn = e.target; btn.disabled = true; fmMsg.replaceChildren(); msg.replaceChildren();
    try {
      const r = await api(`concepts/${enc(c.path)}`, { method: 'PUT', json: { frontmatter: fmTa.value, body: ta.value, baseline: base } });
      base = r.version; S.dirty = false; state.textContent = `Enregistré à ${fmtTime(new Date())}`; await load();
    } catch (err) {
      const box = errBox(`Rien n'a changé : ${err.data && err.data.champ ? err.message : plain(err)}.`);
      (err.data && err.data.champ === 'frontmatter' ? fmMsg : msg).replaceChildren(box);
    }
    btn.disabled = false;
  };
  const list = (l, empty) => l.length ? h('ul', {}, l.map((x) => h('li', {}, h('a', { href: routeOf(x.path) }, x.title)))) : none(empty);
  return [h('h1', {}, c.frontmatter.title || c.path), h('p', { class: 'muted' }, `${c.frontmatter.type} · ${trustWord(meta(c))} · `, h('span', { class: 'mono' }, c.path)),
    h('label', { for: 'fm' }, 'En-tête (le type ne change jamais)'), fmTa, fmMsg, h('label', { for: 'body' }, 'Contenu'), ta, msg,
    h('div', { class: 'row' }, h('button', { class: 'btn', onclick: save }, 'Enregistrer'),
      h('button', { class: 'btn o', onclick: () => prev.replaceChildren(doc(c, ta.value)) }, 'Aperçu'),
      h('span', { class: 'sp' }), h('a', { href: '#/gestion/concepts' }, 'Retour à la liste')), h('p', { role: 'status' }, state), prev,
    h('div', { class: 'cols' }, h('div', {}, sect('Liens sortants', list(c.liens.sortants, 'Aucun lien')), sect('Liens entrants', list(c.liens.entrants, 'Aucun lien'))),
      sect('Historique', c.historique.length ? table(['Date', 'Qui', 'Quoi'], c.historique.map((x) => h('tr', {}, h('td', { class: 'num' }, isoDay(x.date)), who(x.acteur), h('td', {}, x.texte)))) : none('Aucun historique')))];
}
function createForm() {
  const v = (id) => $(id).value.trim(), msg = h('div'), opts = (id, l) => h('datalist', { id }, l.map((x) => h('option', { value: x })));
  const uniq = (f) => [...new Set(S.concepts.map(f).filter(Boolean))].sort();
  const submit = async (e) => {
    e.preventDefault(); const btn = e.submitter; if (btn) btn.disabled = true; msg.replaceChildren();
    const body = { bundle: v('new-bundle'), type: v('new-type'), title: v('new-title'), slug: v('new-slug') };
    const bad = !body.bundle || !body.type || !body.title ? 'dossier, type et titre sont requis'
      : !/^[a-z0-9][a-z0-9-]*$/.test(body.slug) ? 'identifiant : minuscules, chiffres et tirets uniquement' : null;
    try {
      if (bad) throw new Error(bad);
      const r = await api('concepts', { method: 'POST', json: body });
      await load(); toast(`« ${body.title} » créé.`); location.hash = `#/gestion/concepts/${enc(r.path)}`;
    } catch (err) { msg.replaceChildren(errBox(`Rien n'a été créé : ${err.status === 409 ? `${body.slug} existe déjà dans ${body.bundle}` : err.status === 400 || bad ? err.message : plain(err)}.`)); }
    if (btn) btn.disabled = false;
  };
  const field = (id, label, attrs = {}) => h('label', { for: id }, label, h('br'), h('input', { id, required: true, ...attrs }));
  return h('details', { class: 'card' }, h('summary', {}, 'Nouveau concept'), h('form', { class: 'grid', onsubmit: submit },
    field('new-bundle', 'Dossier', { list: 'dl-bundle', placeholder: 'tickets' }), opts('dl-bundle', uniq((c) => c.path.includes('/') ? c.path.split('/')[0] : '')),
    field('new-type', 'Type', { list: 'dl-type', placeholder: 'Ticket' }), opts('dl-type', uniq((c) => c.type)),
    field('new-title', 'Titre'), field('new-slug', 'Identifiant (slug)', { pattern: '[a-z0-9][a-z0-9\\-]*', placeholder: 'export-csv', title: 'minuscules, chiffres et tirets' }),
    h('div', {}, h('button', { class: 'btn' }, 'Créer')), msg));
}
const folderOf = (c) => c.path.includes('/') ? c.path.split('/')[0] : '';
function vConcepts(path) {
  if (path) {
    const box = h('div', { class: 'grid' }, h('p', { class: 'muted' }, 'Chargement…'));
    api(`concepts/${enc(path)}`).then((c) => box.replaceChildren(...editor(c)), (e) => box.replaceChildren(e.status === 404 ? v404() : errBox(`Rendu impossible : ${plain(e)}.`)));
    return h('div', { class: 'grid' }, subnav('/gestion/concepts'), crumbs(['Concepts', '/gestion/concepts'], [path]), box);
  }
  const cs = S.concepts, uniq = (f) => [...new Set(cs.flatMap(f).filter(Boolean))].sort().map((x) => [x, x]);
  const l = cs.filter((c) => has(c.title + c.path) && (!F.dossier || folderOf(c) === F.dossier) && (!F.type || c.type === F.type)
    && (!F.tag || (Array.isArray(c.fm.tags) && c.fm.tags.includes(F.tag))) && (!F.statut || c.fm.status === F.statut) && (!F.validation || TIER[c.trust] === F.validation));
  return h('div', { class: 'grid' }, subnav('/gestion/concepts'), h('h1', {}, 'Concepts'), createForm(),
    filterBar(['q'], { selects: { dossier: uniq((c) => [folderOf(c)]), type: uniq((c) => [c.type]), tag: uniq((c) => Array.isArray(c.fm.tags) ? c.fm.tags.map(String) : []), statut: uniq((c) => [c.fm.status]), validation: VALIDATION } }),
    l.length ? table(['Concept', 'Type', 'Validation'], l.map((c) => h('tr', {}, h('td', {}, h('a', { href: `#/gestion/concepts/${enc(c.path)}` }, c.title)), h('td', {}, c.type), h('td', {}, trustSt(c)))))
      : none('Aucun concept ne correspond', ' ', clearBtn(['q', 'dossier', 'type', 'tag', 'statut', 'validation'])));
}
const v404 = () => h('section', { class: 'card' }, h('h1', {}, 'Écran introuvable'), h('p', {}, 'Cet écran n’existe pas.'), h('p', {}, h('a', { class: 'btn', href: '#/' }, 'Retour à l’accueil')));

// --- validation (nom demandé une fois, retenu) ----------------------------------
function me() {
  return new Promise((ok) => {
    const n = localStorage.getItem('hosa.me'); if (n) return ok(n);
    const d = $('name-dialog'); d.showModal();
    $('name-form').onsubmit = () => { const v = $('name-input').value.trim().toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, ''); if (v) localStorage.setItem('hosa.me', v); ok(v); };
  });
}
async function setVerified(c, verified, patch, okMsg) {
  try { await api(`concepts/${enc(c.path)}`, { method: 'PATCH', json: { frontmatter: { ...patch, verified } } }); await load(); toast(okMsg); }
  catch (e) { toast(`Rien n'a changé : ${plain(e)}.`); S.err = null; }
  route();
}
async function validate(c) {
  const name = await me(); if (!name) return;
  const patch = c.type === 'Exigence' ? { status: 'stable' } : {};
  await setVerified(c, { by: `human:${name}`, at: `${new Date().toISOString().slice(0, 19)}Z` }, patch, `« ${c.title} » validée par vous.`);
}
const unvalidate = (c) => setVerified(c, { by: null, at: null }, {}, `Validation de « ${c.title} » annulée.`);

// --- coque, routes ---------------------------------------------------------------
const ROUTES = [
  [/^\/$/, home, 'Accueil'],
  [/^\/avancement$/, vAvancement, "Plan d'avancement"], [/^\/tickets$/, () => vTickets(false), 'Tickets'], [/^\/tickets\/(.+)$/, (m) => vTicket(decodeURIComponent(m[1])), 'Ticket'],
  [/^\/sprints$/, vSprints, 'Sprints'], [/^\/sprints\/([^/]+)$/, (m) => vSprint(m[1]), 'Sprint'], [/^\/exigences$/, vExigences, 'Exigences'], [/^\/exigences\/([^/]+)$/, (m) => vExigence(m[1]), 'Exigence'],
  [/^\/personas$/, () => vPersonas(), 'Personas'], [/^\/personas\/([^/]+)$/, (m) => vPersonas(decodeURIComponent(m[1])), 'Persona'], [/^\/recettes$/, vRecettes, 'Recettes'], [/^\/consommation$/, vConsommation, 'Consommation'], [/^\/tracabilite$/, vTracabilite, 'Traçabilité'], [/^\/journal$/, vJournal, 'Journal'],
  [/^\/gestion\/validation$/, vValidation, 'À valider'], [/^\/gestion\/concepts$/, () => vConcepts(), 'Concepts'], [/^\/gestion\/concepts\/(.+)$/, (m) => vConcepts(decodeURIComponent(m[1])), 'Concept'], [/^\/gestion\/tickets$/, () => vTickets(true), 'Tickets'],
];
const here = () => (location.hash.replace(/^#/, '') || '/').replace(/\/$/, '') || '/';

function paintShell() {
  $('brand').textContent = 'Hosa';
  const p0 = here(), p = ROUTES.some(([re]) => re.test(p0)) ? p0 : '\0';
  const cur = (to) => p === to || (to !== '/' && p.startsWith(to + '/')) ? 'page' : null;
  $('nav').replaceChildren(...MENU.map(([to, label]) => h('a', { href: `#${to}`, 'aria-current': cur(to) }, label)),
    ...GESTION.map(([to, label]) => h('a', { class: 'mo', href: `#${to}`, 'aria-current': cur(to) }, `Gestion : ${label}`)));
  $('more').hidden = false; $('more').querySelector('summary').classList.toggle('on', p.startsWith('/gestion'));
  $('more-list').replaceChildren(...GESTION.map(([to, label]) => h('a', { href: `#${to}`, 'aria-current': cur(to) }, label)));
  const k = S.kbStatus;
  $('banner').replaceChildren(...(k === undefined ? [] : k && k.git && k.changed > 0 ? [h('div', { class: 'alert', role: 'alert' },
    h('span', {}, h('b', {}, `${plural(k.changed, 'changement', 'changements')} de la KB non sauvegardé${k.changed > 1 ? 's' : ''}`), ' — lancer ', h('code', {}, '/kb-commit'), '. La KB est la base de connaissance du projet, écrite par les agents.'),
    h('button', { class: 'btn warn', onclick: () => copy('/kb-commit') }, 'Copier /kb-commit'),
    h('details', { class: 'files', ontoggle: (e) => { e.target.firstChild.textContent = e.target.open ? 'Masquer les fichiers' : 'Voir les fichiers'; } }, h('summary', {}, 'Voir les fichiers'),
      h('ul', {}, (k.files || []).slice(0, 20).map((f) => h('li', {}, h('span', { class: 'mono' }, f.path), ' ', st(f.state, f.state === 'supprimé' ? 'b' : f.state === 'nouveau' ? 'e' : 'a', f.state === 'supprimé' ? '✕' : f.state === 'nouveau' ? '+' : '◐'))),
        (k.files || []).length > 20 ? h('li', {}, `et ${k.files.length - 20} autres`) : null)))]
    : k && !k.git ? [h('p', { class: 'muted', style: 'padding:4px 12px' }, 'KB hors git')] : k ? [] : [h('div', { class: 'alert info', role: 'status' }, h('span', {}, h('b', {}, 'Sauvegarde de la KB : état inconnu.'), ' Le serveur n’a pas pu le lire pour le moment.'), h('button', { class: 'btn o', onclick: reload }, 'Réessayer'))]));
  $('freshness').textContent = `Dernière lecture de la KB (la base de connaissance du projet) : ${S.loadedAt ? fmtTime(S.loadedAt) : '—'}`;
  $('user-label').textContent = localStorage.getItem('hosa.me') || 'Mon nom';
}
function route() {
  paintShell();
  const p = here(), view = $('view'), main = $('main');
  const x = ROUTES.map(([re, fn, title]) => [re.exec(p), fn, title]).find(([m]) => m);
  let node, title = 'Écran introuvable';
  if (S.err) node = errBox(S.err, true);
  else if (!S.ov) node = h('p', { class: 'muted' }, 'Chargement…');
  else if (!x) node = v404();
  else { try { node = x[1](x[0]); title = x[2]; } catch (e) { node = errBox('Cet écran ne peut pas s’afficher pour le moment.', true); } }
  view.replaceChildren(node);
  document.title = `${title} — Hosa`;
}
const paint = route;
let lastHash = location.hash;
window.addEventListener('hashchange', () => {
  if (S.dirty && !confirm('Des modifications ne sont pas enregistrées. Quitter quand même ?')) { location.hash = lastHash; return; }
  S.dirty = false; lastHash = location.hash; route(); $('main').focus();
});
$('rename').addEventListener('click', () => { localStorage.removeItem('hosa.me'); me().then(() => { toast('Nom enregistré'); paintShell(); }); });
$('reload').addEventListener('click', reload);
document.addEventListener('keydown', (e) => {
  if (e.key === '/' && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) { const s = $('search'); if (s) { e.preventDefault(); s.focus(); } }
});
route();
load().then(route);
