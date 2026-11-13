// Hosa — mod (Claude Code ≥ 2.1.290; older versions ignore it, the classic hooks still run).
// A. The main session runs on Sonnet in every phase: it orchestrates, the hard judgements stay
//    in the Opus agents (pilot2, 2026-10: Opus in the main session was 81 % of its cost).
//    README « Quel modèle pour ta session ». Subagents keep their own `model:`.
//    Kill switch: HOSA_MODELE=0.
// B. A status line with the phase and the context fill, and a toast when a stage closes in a
//    heavy session: /clear then « reprends » (README « Une session par étape »).
// C. Rollback of the execution agents moved to Haiku (2026-10-17): HOSA_HAIKU=0 runs them on
//    Sonnet again, without a release. Measure with `usage_report.py --since/--until`.
// D. A pane « Hosa » with what the user needs: the open stage, the questions waiting for them, the resume
//    point, the open loops, the agents' tasks, each pipeline's progress. It reads the plan avancement.py
//    writes, nothing else. /hosa-panneau opens it. Kill switch of the unasked opening: HOSA_PANNEAU=0.
// E. In the pane, « Ouvrir le tableau de bord » starts run.py (the /hosa:pilotage server) for the session.

const PLAN = '.hosa/kb/project/avancement.md'
const CLOSED = ['fait', 'non applicable']
// ponytail: fixed id, bump it with each model generation
const MODEL = 'claude-sonnet-5-5'
const KEEP = /sonnet|haiku/ // families accepted as they are
const HEAVY = 20 // context %, from which a closed stage suggests /clear
const ON_HAIKU = /(^|:)hosa-(developer|implementer|tester|qa-lead|key-user|git|documentation|infra|dba)$/

// Same reading as skills/status/scripts/avancement.py: `| \`stage\` | statut | … |` rows. avancement.py
// writes every stage of skills/status/scripts/pipeline.json, the upstream pipelines before the sprints:
// the rows above the first `## Sprint` heading are the upstream stages, no list to keep in step here.
export function readPlan(text) {
  const upstream = []
  let closed = 0
  for (const block of text.split(/^(?=## )/m)) {
    if (block.startsWith('## Boucles') || block.startsWith('## Tâches')) continue // loop rounds, agents' tasks: not stages
    const sprint = block.startsWith('## Sprint ')
    for (const m of block.matchAll(/^\|\s*`?([\w-]+)`?\s*\|\s*([^|]*?)\s*\|/gm)) {
      if (/^-+$/.test(m[1])) continue // the |---| separator
      if (CLOSED.includes(m[2])) closed++
      if (!sprint) upstream.push(m[2])
    }
  }
  const phase = upstream.length && upstream.every((s) => CLOSED.includes(s)) ? 'sprints' : 'conception'
  return { phase, closed }
}

// The same plan in full, for the pane: resume point, loops, agents' tasks, every section's stages and the
// first open stage (as avancement.py's first_open: a sprint with every stage closed is behind us).
const HEADS = ['Étape', 'Etape', 'Tâche', 'Boucle']
const bare = (s) => s.replace(/`/g, '')
export function readView(text) {
  const view = { resume: [], loops: [], tasks: [], sections: [], current: null }
  for (const block of text.split(/^(?=## )/m)) {
    if (!block.startsWith('## ')) continue // the front matter
    const [head, ...lines] = block.split(/\r?\n/)
    const title = head.slice(3).trim()
    if (title === 'Point de reprise') {
      view.resume = lines.map((l) => bare(l.trim().replace(/^- /, ''))).filter((l) => l && l !== 'Rien en cours.')
      continue
    }
    const rows = lines.filter((l) => l.startsWith('|')).map((l) => l.split('|').slice(1, -1).map((c) => bare(c.trim())))
      .filter((c) => c[0] && !HEADS.includes(c[0]) && !/^-+$/.test(c[0]))
    if (title === 'Boucles') view.loops = rows.map((c) => ({ name: c[0], tours: c[1], etat: c[2], cause: c[4] ?? '', detail: c[5] ?? '' }))
    else if (title === 'Tâches') view.tasks = rows.map((c) => ({ id: c[0], where: c[1], agent: c[2], objet: c[3], statut: c[4], detail: c[7] ?? '' }))
    else view.sections.push({ title, rows: rows.map((c) => ({ stage: c[0], statut: c[1], detail: c[3] ?? '' })) })
  }
  for (const s of view.sections) {
    s.done = s.rows.filter((r) => CLOSED.includes(r.statut)).length
    if (view.current || (s.title.startsWith('Sprint ') && s.done === s.rows.length)) continue
    const row = s.rows.find((r) => !CLOSED.includes(r.statut))
    if (row) view.current = { ...row, title: s.title }
  }
  return view
}

const PANE = 'hosa'
const COMMAND = 'hosa-panneau'
const MARK = { fait: '✓', 'non applicable': '–', 'en cours': '▶', 'bloqué': '✗', 'à faire': '·' }
const COLOR = { fait: 'success', 'en cours': 'suggestion', 'bloqué': 'error' }
const MANY = 10 // open tasks listed one by one; the rest is a count

let enabled = true
let haiku = true
let plan = null // { phase, closed } of the managed project, null outside one
let view = null // readView of the same file, for the pane
let seen = null // the plan's text as last read: the pane is drawn again only when it changes
let percent = null
let project = null // the managed project's root, where `run.py` finds its `.hosa/kb`
// The dashboard (E): off, starting, on (its url) or stopped with the reason; the server lives as long as `child`.
let dash = { state: 'off' }

// The managed project's plan: a sprint worktree's `.hosa/kb` copy is stale, so start above it.
async function refresh($) {
  let dir = (await $.session.cwd()).split(/[\\/]\.worktrees[\\/]/)[0].replace(/[\\/]+$/, '')
  for (;;) {
    const file = `${dir}/${PLAN}`
    if (await $.fs.exists(file)) {
      const text = await $.fs.read(file)
      project = dir
      plan = readPlan(text)
      if (text !== seen) {
        view = readView((seen = text))
        redraw($)
      }
      return plan
    }
    const up = dir.replace(/[\\/][^\\/]*$/, '')
    if (!up || up === dir) return (plan = view = seen = null)
    dir = up
  }
}

// Hosa's Python: the venv the SessionStart hook builds in the plugin's data folder, `pythonw` on Windows
// (no console window opens); else the Python on the PATH, and run.py builds what it lacks.
async function python($) {
  const home = (await $.env.get('USERPROFILE')) || (await $.env.get('HOME')) || ''
  const data = (await $.env.get('CLAUDE_PLUGIN_DATA')) || (home && `${home}/.claude/plugins/data/hosa-hosa`)
  const win = /^[A-Za-z]:|\\/.test($.plugin.root)
  const venv = data && `${data}/venv/${win ? 'Scripts/pythonw.exe' : 'bin/python'}`
  if (venv && (await $.fs.exists(venv))) return { exe: venv, data, venv: true }
  return { exe: win ? 'python' : 'python3', data: null, venv: false }
}

// E. The dashboard (/hosa:pilotage) from a button of the pane: run.py serves the project's KB and opens the browser.
// The server lives for the session (the stream's loop is its life); PORT left empty: server.py takes 3000, or a free
// port when 3000 is taken, and opens the browser on its own address. Fail-open.
export async function startDashboard($, port = '') {
  if (dash.state === 'starting' || dash.state === 'on' || !project) return
  dash = { state: 'starting' }
  redraw($)
  let busy = false
  let last = ''
  try {
    // With the venv, server.py itself: stopping the child stops the server (on Windows, stopping run.py would leave
    // its server.py running on the port). Without it, run.py, which builds the venv first.
    const { exe, data, venv } = await python($)
    const env = { PORT: port, PYTHONUTF8: '1', HOSA_OPEN_BROWSER: '1', HOSA_KB_ROOT: `${project}/.hosa/kb`,
      ...(data ? { CLAUDE_PLUGIN_DATA: data } : {}) }
    const script = venv ? `${$.plugin.root}/hosa/app/server.py` : `${$.plugin.root}/run.py`
    // cwd: the plugin's folder, never the project's — Windows looks up a bare `python` in the current folder first,
    // and a project's tree is not ours to trust. The project reaches the server through HOSA_KB_ROOT alone.
    const child = $.process.spawn({ argv: [exe, script], cwd: $.plugin.root, env })
    dash.child = child
    for await (const { text } of child) {
      const url = /http:\/\/127\.0\.0\.1:\d+/.exec(text)
      if (url && dash.state === 'starting') {
        // the desktop links http only on `localhost`; server.py accepts that host (its DNS-rebinding guard)
        dash = { state: 'on', url: url[0].replace('127.0.0.1', 'localhost'), child }
        redraw($)
      }
      if (/déjà utilisé/.test(text)) busy = true
      else if (text.trim()) last = text.trim().split(/\r?\n/).pop()
    }
  } catch (err) {
    last = String((err && err.message) || err)
  }
  const asked = dash.stopping
  dash = { state: 'off' }
  if (busy && port !== '0' && !asked) return startDashboard($, '0')
  if (!asked) dash = { state: 'stopped', reason: busy ? 'aucun port libre' : last || 'le serveur s\'est arrêté' }
  redraw($)
}

export function stopDashboard($) {
  dash.stopping = true
  try {
    Promise.resolve(dash.child && dash.child.return && dash.child.return()).catch(() => {})
  } catch {}
  redraw($)
}

// Fail-open: a pane that cannot be drawn again never stops a hook.
function redraw($) {
  try {
    Promise.resolve($.ui.invalidate('ui.render')).catch(() => {})
  } catch {}
}

// Everything the user needs, from the plan alone: what waits for them first, then where the project is.
function pane($, { Box, Text, Button, Link }) {
  const row = (text, props) => h(Text, { wrap: 'truncate-end', ...props }, text)
  const para = (text, props) => h(Text, { wrap: 'wrap', ...props }, text)
  const group = (title, ...rows) => h(Box, { flexDirection: 'column' }, h(Text, { weight: 'bold' }, title), ...rows)
  const mark = (statut, text) => h(Text, { wrap: 'truncate-end' }, h(Text, { color: COLOR[statut] }, MARK[statut] ?? '?'), ` ${text}`)
  if (!view || !plan) {
    return h(Box, { flexDirection: 'column' }, para('Pas de plan d\'avancement dans ce dossier.'),
      para('Dans un projet Hosa, /hosa:status le crée à partir de la KB.', { dimColor: true }))
  }
  const out = []
  const now = view.current
  const head = [h(Text, { weight: 'bold' }, `Hosa · ${plan.phase}`)]
  if (now) {
    head.push(mark(now.statut, `${now.stage} — ${now.statut} (${now.title})`))
    if (now.detail && now.statut !== 'bloqué') head.push(para(now.detail, { dimColor: true }))
  } else head.push(para('Toutes les étapes connues sont faites : compose un nouveau sprint.'))
  if (percent != null) {
    head.push(percent >= HEAVY
      ? para(`Contexte ${percent} % : à la fin de l'étape, /clear puis « reprends ».`, { color: 'warning' })
      : row(`Contexte ${percent} %`, { dimColor: true }))
  }
  out.push(h(Box, { flexDirection: 'column' }, ...head))
  out.push(dashboard($, { Box, Text, Button, Link }, row, para))

  const blocked = [
    ...view.sections.flatMap((s) => s.rows.filter((r) => r.statut === 'bloqué').map((r) => [`${r.stage} (${s.title})`, r.detail])),
    ...view.tasks.filter((t) => t.statut === 'bloqué').map((t) => [`${t.id} ${t.agent} — ${t.where}`, t.detail]),
  ]
  if (blocked.length) {
    out.push(group('À toi : une réponse est attendue', ...blocked.flatMap(([what, detail]) =>
      [mark('bloqué', what), ...(detail ? [para(detail)] : [])])))
  }
  if (view.resume.length) out.push(group('Point de reprise', ...view.resume.map((l) => para(l))))

  const open = view.loops.filter((l) => l.etat === 'ouverte')
  if (open.length) {
    out.push(group('Boucles ouvertes', ...open.flatMap((l) =>
      [row(`↺ ${l.name} — tour ${l.tours}`), ...(l.cause || l.detail ? [para(l.cause || l.detail, { dimColor: true })] : [])])))
  }

  for (const where of [...new Set(view.tasks.map((t) => t.where))]) {
    const mine = view.tasks.filter((t) => t.where === where)
    const left = mine.filter((t) => !CLOSED.includes(t.statut))
    const rows = left.slice(0, MANY).map((t) => mark(t.statut, `${t.id} ${t.agent}${t.objet ? ` → ${t.objet}` : ''}`))
    if (left.length > MANY) rows.push(row(`+ ${left.length - MANY} autres`, { dimColor: true }))
    out.push(group(`Tâches ${where} : ${mine.length - left.length}/${mine.length} faites`, ...rows))
  }

  const past = view.sections.filter((s) => s.title.startsWith('Sprint ') && s.done === s.rows.length && s.title !== now?.title)
  const rows = []
  for (const s of view.sections.filter((x) => !past.includes(x))) {
    const full = s.done === s.rows.length
    rows.push(row(`${full ? '✓' : ' '} ${s.title} ${s.done}/${s.rows.length}`, full ? { dimColor: true } : { weight: 'bold' }))
    if (s.title === now?.title) rows.push(...s.rows.map((r) => h(Box, { paddingLeft: 2 }, mark(r.statut, r.stage))))
  }
  if (past.length) rows.push(row(`✓ ${past.length} sprint${past.length > 1 ? 's' : ''} terminé${past.length > 1 ? 's' : ''}`, { dimColor: true }))
  out.push(group('Avancement', ...rows))

  out.push(group('Commandes', row('« reprends » : continuer où le plan s\'arrête', { dimColor: true }),
    row('/hosa:status : le point complet', { dimColor: true })))
  return h(Box, { flexDirection: 'column', gap: 1 }, ...out)
}

// The dashboard's row: one button to open it, then its link and a button to stop it.
function dashboard($, { Box, Text, Button, Link }, row, para) {
  const start = () => { void startDashboard($) }
  const lines = [h(Text, { weight: 'bold' }, 'Tableau de bord')]
  if (dash.state === 'on') {
    lines.push(h(Text, {}, h(Link, { href: dash.url }, dash.url)),
      para('Suivi, KB, validations, remarques pour Claude.', { dimColor: true }),
      h(Box, { flexDirection: 'row', gap: 1 }, h(Button, { key: 'pilotage-ouvrir', onPress: (press) => $.ui.copy({ text: dash.url, surface: press.surface }) }, 'Copier l’adresse'),
        h(Button, { key: 'pilotage-arreter', onPress: () => stopDashboard($) }, 'Arrêter')))
  } else if (dash.state === 'starting') {
    lines.push(row('Démarrage…', { dimColor: true }))
  } else {
    lines.push(h(Button, { key: 'pilotage', variant: 'primary', onPress: start }, 'Ouvrir le tableau de bord'))
    if (dash.state === 'stopped') lines.push(para(`Arrêté : ${dash.reason}`, { color: 'warning' }))
  }
  return h(Box, { flexDirection: 'column' }, ...lines)
}

function showStatus($) {
  if (!plan) return
  $.ui.status(`Hosa · ${plan.phase} (${enabled ? 'Sonnet' : '/model libre'})${percent == null ? '' : ` · contexte ${percent} %`}`)
}

export function register(on) {
  on('session.start', async ($, e, next) => {
    enabled = (await $.env.get('HOSA_MODELE')) !== '0'
    haiku = (await $.env.get('HOSA_HAIKU')) !== '0'
    await refresh($)
    showStatus($)
    // The pane: asked for with /hosa-panneau anywhere; opened unasked only in a Hosa project and where it sits
    // beside the chat (the terminal would put it above the prompt). Fail-open, kill switch HOSA_PANNEAU=0.
    try {
      await $.command.register({ name: COMMAND, description: 'Hosa : le panneau du projet (étape, questions en attente, tâches, avancement)' })
      if (plan && e.surface && e.surface !== 'terminal' && (await $.env.get('HOSA_PANNEAU')) !== '0') {
        await $.ui.open({ id: PANE, title: 'Hosa' })
      }
    } catch {}
    return next(e)
  })

  on('command.run', { command: COMMAND }, async ($) => {
    await refresh($)
    const { isPlaced } = await $.ui.open({ id: PANE, title: 'Hosa' })
    return { text: isPlaced ? 'Panneau Hosa ouvert.' : 'Cette interface n\'affiche pas de panneau : /hosa:status donne le même point.' }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => pane($, $.ui.resolve(e)))

  // The plan moves during a turn, at each `avancement` call: the pane follows it without waiting for the turn's end.
  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    try {
      if (plan && /avancement/.test(String(e.command ?? ''))) await refresh($)
    } catch {}
    return ran
  })

  on('agent.spawn', async ($, e, next) =>
    next(!haiku && ON_HAIKU.test(e.subagentType) ? { ...e, model: 'sonnet' } : e))

  on('turn.step', async function* ($, e, next) {
    const want = enabled && !e.agentId && plan
    return yield* next(want && !KEEP.test(e.model) ? { ...e, model: MODEL } : e)
  })

  on('session.measure', async ($, e, next) => {
    const was = percent
    percent = e.context.percent ?? null
    if (percent !== was && view) redraw($)
    showStatus($)
    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    if (e.agentId) return next(e)
    const before = plan
    await refresh($)
    if (before && plan && plan.closed > before.closed && percent >= HEAVY) {
      $.ui.toast(`Étape terminée, contexte à ${percent} % : /clear puis « reprends » pour repartir léger.`, { timeoutMs: 15000 })
    }
    showStatus($)
    return next(e)
  })
}
