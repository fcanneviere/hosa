import { expect, mock, test } from 'claude-code/testing'

const row = (s: string, st: string) => `| \`${s}\` | ${st} | | |`
const UPSTREAM = ['hosa', 'interview', 'redaction', 'fondamentaux', 'juridique', 'securite', 'relecture', 'contestation',
  'stack', 'infra', 'donnees', 'schema-app', 'schema-db', 'architecture', 'menaces', 'interface', 'backlog']
const conception = [...UPSTREAM.slice(0, 16).map((s) => row(s, 'fait')), row('backlog', 'en cours')].join('\n')
const sprints = [...UPSTREAM.map((s) => row(s, 'fait')), '## Sprint s1', row('sprint', 'en cours')].join('\n')

// Plan text per call, so a test can close a stage between turns.
let redrawn = 0 // the pane's redraws asked for, over the file
function project(on: any, plans: string[], env: Record<string, string> = {}) {
  mock.env(on, env)
  on('session.start', () => ({ cwd: '/work' }))
  on('session.cwd', () => ({ value: '/work/.worktrees/s1/src' }))
  on('fs.exists', ($: any, e: any) => ({ value: e.path.replaceAll('\\', '/').endsWith('work/.hosa/kb/project/avancement.md') }))
  on('fs.read', () => ({ value: plans.length > 1 ? plans.shift() : plans[0] }))
  on('ui.status', () => ({ value: undefined }))
  on('ui.invalidate', () => { redrawn++; return { value: undefined } })
  on('command.register', () => ({ value: { command: 'hosa-panneau' } }))
  on('tool.call', () => ({ result: {} }))
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

test('conception: main session goes to Sonnet too, subagents keep theirs', async ($, on) => {
  project(on, [conception])
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  expect(await step($, 'claude-opus-5-5')).toBe('claude-sonnet-5-5')
  expect(await step($, 'claude-sonnet-5-5')).toBe('claude-sonnet-5-5')
  expect(await step($, 'claude-opus-5-5', 'a1')).toBe('claude-opus-5-5')
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

test('HOSA_HAIKU=0 puts the Haiku execution agents back on Sonnet, only them', async ($, on) => {
  project(on, [sprints], { HOSA_HAIKU: '0' })
  on('agent.spawn', ($: any, e: any) => ({ model: e.model ?? 'own' }))
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  const spawn = (subagentType: string, model?: string) => $.agent.spawn({ subagentType, prompt: 'p', description: 'd', model })
  expect((await spawn('hosa:hosa-developer')).model).toBe('sonnet')
  expect((await spawn('hosa:hosa-git', 'haiku')).model).toBe('sonnet')
  expect((await spawn('hosa:hosa-reviewer')).model).toBe('own')
})

test('without HOSA_HAIKU the agents keep their own model', async ($, on) => {
  project(on, [sprints])
  on('agent.spawn', ($: any, e: any) => ({ model: e.model ?? 'own' }))
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  expect((await $.agent.spawn({ subagentType: 'hosa:hosa-developer', prompt: 'p', description: 'd' })).model).toBe('own')
})

const PANE = { plugin: 'hosa', component: 'Pane', requestId: 'hosa',
  props: { title: 'Hosa', isFocused: false, bodyColumns: 40, placement: 'dock', scroll: { offset: 0, bodyRows: 30 }, view: {} } } as const
const blocked = [...UPSTREAM.map((s) => row(s, 'fait')),
  '## Tâches', '| Tâche | Étape | Agent | Objet | Statut | Mis à jour | Sortie | Détail |', '|---|---|---|---|---|---|---|---|',
  '| lot-1 | `develop` (s1) | hosa-developer | t1 | bloqué | d | | Q1 : a) ou b) ? |',
  '## Sprint s1', row('sprint', 'fait'), row('develop', 'en cours')].join('\n')

test('the pane shows the open stage and the question that waits, on every surface', async ($, on) => {
  project(on, [blocked])
  on('ui.open', () => ({ value: { isPlaced: true } }))
  await $.session.start({ surface: 'desktop', isInteractive: true, cwd: '/work' })
  for (const surface of ['terminal', 'desktop', 'vscode', 'mobile'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /develop — en cours/ }))?.text).toContain('Sprint s1')
    expect((await ui.find({ type: 'Text', text: /Q1/ }))?.text).toBe('Q1 : a) ou b) ?')
    expect((await ui.find({ type: 'Text', text: /Sprint s1 1\/2/ }))?.text).toContain('1/2')
    await ui.unmount()
  }
})

test('HOSA_PANNEAU=0 keeps the pane closed at the start', async ($, on) => {
  const opened: string[] = []
  project(on, [sprints], { HOSA_PANNEAU: '0' })
  on('ui.open', ($: any, e: any) => { opened.push(e.id); return { value: { isPlaced: true } } })
  await $.session.start({ surface: 'desktop', isInteractive: true, cwd: '/work' })
  expect(opened.length).toBe(0)
})

test('the pane opens at the start of a Hosa project on the desktop, and follows an avancement call', async ($, on) => {
  const opened: string[] = []
  const closed = sprints.replace('`sprint` | en cours', '`sprint` | fait')
  project(on, [sprints, closed])
  on('ui.open', ($: any, e: any) => { opened.push(e.id); return { value: { isPlaced: true } } })
  await $.session.start({ surface: 'desktop', isInteractive: true, cwd: '/work' })
  expect(opened).toEqual(['hosa'])
  const before = redrawn
  await $.tool.call({ tool: 'Bash', command: 'hosa avancement "/work/.hosa/kb" done sprint' })
  expect(redrawn).toBe(before + 1)
})
