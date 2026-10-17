import { expect, mock, test } from 'claude-code/testing'

const row = (s: string, st: string) => `| \`${s}\` | ${st} | | |`
const UPSTREAM = ['hosa', 'interview', 'redaction', 'fondamentaux', 'securite', 'relecture', 'contestation',
  'stack', 'infra', 'donnees', 'schema-app', 'schema-db', 'architecture', 'menaces', 'interface', 'backlog']
const conception = [...UPSTREAM.slice(0, 15).map((s) => row(s, 'fait')), row('backlog', 'en cours')].join('\n')
const sprints = [...UPSTREAM.map((s) => row(s, 'fait')), '## Sprint s1', row('sprint', 'en cours')].join('\n')

// Plan text per call, so a test can close a stage between turns.
function project(on: any, plans: string[], env: Record<string, string> = {}) {
  mock.env(on, env)
  on('session.start', () => ({ cwd: '/work' }))
  on('session.cwd', () => ({ value: '/work/.worktrees/s1/src' }))
  on('fs.exists', ($: any, e: any) => ({ value: e.path.replaceAll('\\', '/').endsWith('work/.hosa/kb/project/avancement.md') }))
  on('fs.read', () => ({ value: plans.length > 1 ? plans.shift() : plans[0] }))
  on('ui.status', () => ({ value: undefined }))
  on('session.measure', ($: any, e: any) => ({ changed: e.changed }))
  on('turn.complete', () => ({ text: '' }))
  on('turn.step', async function* ($: any, e: any) {
    return { turnId: e.turnId, index: e.index, answer: e.model, toolUses: [], stopReason: 'end_turn', usage: null }
  })
}

async function step($: any, model: string, agentId?: string) {
  const stream = $.turn.step({ turnId: 't', index: 0, model, messageCount: 1, ...(agentId ? { agentId } : {}) })
  let s = await stream.next()
  while (s.done !== true) s = await stream.next()
  return s.value.answer
}

test('conception: main session goes to Opus, subagents keep theirs', async ($, on) => {
  project(on, [conception])
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  expect(await step($, 'claude-sonnet-5-5')).toBe('claude-opus-5-5')
  expect(await step($, 'claude-fable-5-1')).toBe('claude-fable-5-1')
  expect(await step($, 'claude-haiku-5-5', 'a1')).toBe('claude-haiku-5-5')
})

test('sprints: Opus drops to Sonnet, Haiku stays', async ($, on) => {
  project(on, [sprints])
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  expect(await step($, 'claude-opus-5-5')).toBe('claude-sonnet-5-5')
  expect(await step($, 'claude-haiku-5-5')).toBe('claude-haiku-5-5')
})

test('HOSA_MODELE=0 changes no model', async ($, on) => {
  project(on, [sprints], { HOSA_MODELE: '0' })
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  expect(await step($, 'claude-opus-5-5')).toBe('claude-opus-5-5')
})

test('a stage closed in a heavy session suggests /clear', async ($, on) => {
  const toasts: string[] = []
  const closed = conception.replace('`backlog` | en cours', '`backlog` | fait')
  project(on, [conception, conception, closed])
  on('ui.toast', ($: any, e: any) => { toasts.push(e.text); return { value: undefined } })
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  await $.session.measure({ context: { window: 200000, tokens: 60000, percent: 30 }, rateLimits: [], changed: ['context'] })
  await $.turn.complete({ turnId: 't1', answer: '', durationMs: 1, isAborted: false, usage: null })
  expect(toasts.length).toBe(0)
  await $.turn.complete({ turnId: 't2', answer: '', durationMs: 1, isAborted: false, usage: null })
  expect(toasts[0]).toContain('/clear')
})
