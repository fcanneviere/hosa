// Hosa — mod (Claude Code ≥ 2.1.290; older versions ignore it, the classic hooks still run).
// A. The main session's model follows the progress plan: Opus while the cahier des charges
//    or the structuration is open, Sonnet once both are closed (README « Quel modèle pour ta
//    session »). It changes only when the phase does, so the prompt cache holds.
//    Subagents keep their own `model:`. Kill switch: HOSA_MODELE=0.
// B. A status line with the phase and the context fill, and a toast when a stage closes in a
//    heavy session: /clear then « reprends » (README « Une session par étape »).

const PLAN = '.hosa/kb/project/avancement.md'
const UPSTREAM = ['hosa', 'interview', 'redaction', 'fondamentaux', 'securite', 'relecture', 'contestation',
  'stack', 'infra', 'donnees', 'schema-app', 'schema-db', 'architecture', 'menaces', 'interface', 'backlog']
const CLOSED = ['fait', 'non applicable']
// ponytail: fixed ids, bump them with each model generation
const MODEL = { conception: 'claude-opus-5-5', sprints: 'claude-sonnet-5-5' }
// Families each phase accepts as they are: a stronger model the user chose for conception stays.
const KEEP = { conception: /opus|fable/, sprints: /sonnet|haiku/ }
const HEAVY = 20 // context %, from which a closed stage suggests /clear

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
  const model = plan.phase === 'sprints' ? 'Sonnet' : 'Opus'
  $.ui.status(`Hosa · ${plan.phase} (${enabled ? model : '/model libre'})${percent == null ? '' : ` · contexte ${percent} %`}`)
}

export function register(on) {
  on('session.start', async ($, e, next) => {
    enabled = (await $.env.get('HOSA_MODELE')) !== '0'
    await refresh($)
    showStatus($)
    return next(e)
  })

  on('turn.step', async function* ($, e, next) {
    const want = enabled && !e.agentId && plan ? plan.phase : null
    return yield* next(want && !KEEP[want].test(e.model) ? { ...e, model: MODEL[want] } : e)
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
