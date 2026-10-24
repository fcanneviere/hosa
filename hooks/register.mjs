// Hosa — mod (Claude Code ≥ 2.1.290; older versions ignore it, the classic hooks still run).
// A. The main session runs on Sonnet in every phase: it orchestrates, the hard judgements stay
//    in the Opus agents (pilot2, 2026-10: Opus in the main session was 81 % of its cost).
//    README « Quel modèle pour ta session ». Subagents keep their own `model:`.
//    Kill switch: HOSA_MODELE=0.
// B. A status line with the phase and the context fill, and a toast when a stage closes in a
//    heavy session: /clear then « reprends » (README « Une session par étape »).
// C. Rollback of the execution agents moved to Haiku (2026-10-17): HOSA_HAIKU=0 runs them on
//    Sonnet again, without a release. Measure with `usage_report.py --since/--until`.

const PLAN = '.hosa/kb/project/avancement.md'
const UPSTREAM = ['hosa', 'interview', 'redaction', 'fondamentaux', 'juridique', 'securite', 'relecture', 'contestation',
  'stack', 'infra', 'donnees', 'schema-app', 'schema-db', 'architecture', 'menaces', 'interface', 'backlog']
const CLOSED = ['fait', 'non applicable']
// ponytail: fixed id, bump it with each model generation
const MODEL = 'claude-sonnet-5-5'
const KEEP = /sonnet|haiku/ // families accepted as they are
const HEAVY = 20 // context %, from which a closed stage suggests /clear
const ON_HAIKU = /(^|:)hosa-(developer|implementer|tester|qa-lead|key-user|git|documentation|infra|dba)$/

// Same reading as skills/status/scripts/avancement.py: `| \`stage\` | statut | … |` rows.
export function readPlan(text) {
  const status = {}
  let closed = 0
  for (const m of text.matchAll(/^\|\s*`?([\w-]+)`?\s*\|\s*([^|]*?)\s*\|/gm)) {
    if (CLOSED.includes(m[2])) closed++
    if (UPSTREAM.includes(m[1])) status[m[1]] = m[2]
  }
  const phase = UPSTREAM.every((s) => CLOSED.includes(status[s])) ? 'sprints' : 'conception'
  return { phase, closed }
}

let enabled = true
let haiku = true
let plan = null // { phase, closed } of the managed project, null outside one
let percent = null

// The managed project's plan: a sprint worktree's `.hosa/kb` copy is stale, so start above it.
async function refresh($) {
  let dir = (await $.session.cwd()).split(/[\\/]\.worktrees[\\/]/)[0].replace(/[\\/]+$/, '')
  for (;;) {
    const file = `${dir}/${PLAN}`
    if (await $.fs.exists(file)) return (plan = readPlan(await $.fs.read(file)))
    const up = dir.replace(/[\\/][^\\/]*$/, '')
    if (!up || up === dir) return (plan = null)
    dir = up
  }
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
    return next(e)
  })

  on('agent.spawn', async ($, e, next) =>
    next(!haiku && ON_HAIKU.test(e.subagentType) ? { ...e, model: 'sonnet' } : e))

  on('turn.step', async function* ($, e, next) {
    const want = enabled && !e.agentId && plan
    return yield* next(want && !KEEP.test(e.model) ? { ...e, model: MODEL } : e)
  })

  on('session.measure', async ($, e, next) => {
    percent = e.context.percent ?? null
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
