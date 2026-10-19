import type { On } from 'claude-code'
import { expect, test } from 'claude-code/testing'

import type { ForgeView } from '../types'

const SAMPLE: ForgeView = {
  project: '/p', mode: 'web+hitl', exists: true, attention: 1,
  studies: [{ study: 'memory-loss', goal: 'Why does the agent lose memories?', deliverable: 'diagnosis', actions: 4,
              step: 'propose', type: 'llm', executor: 'local:forge-core', needs_attention: false }],
  domains: [{ domain: 'world-model-planning', current: 2, versions: [1, 2], lessons_since_freeze: 3,
              step: 'domain_ready', type: 'terminal', executor: null, needs_attention: false }],
  runs: [{ run: 'budgeted-pruning', domain: 'world-model-planning', version: 2, question: 'q', attempts: 2,
           title: 'Budgeted rollout pruning', decision: null, card: null,
           step: 'audit', type: 'web_handoff', executor: 'web:Extra High', needs_attention: true }],
}

const PANE = {
  plugin: 'open-scientist', component: 'Pane', requestId: 'open-scientist',
  props: { title: 'Open Scientist', isFocused: true, bodyColumns: 80, placement: 'dock',
           scroll: { offset: 0, bodyRows: 30 }, view: {} },
} as const

const RUN = { command: 'open-scientist', args: '', origin: { kind: 'composer' },
              presentation: { isFullscreen: true, columns: 160 } } as const

function host(on: On, statuses: (string | undefined)[]) {
  on('session.root', () => ({ value: '/p' }))
  on('ui.status', ($, e) => { statuses.push(e.text); return { value: undefined } })
  on('ui.open', () => ({ value: { isPlaced: true as const } }))
}

test('/open-scientist asks the navigator for an overview and the pane shows what waits on the person', async ($, on) => {
  const calls: string[][] = []
  const statuses: (string | undefined)[] = []
  // Bottom hooks answer as { value } (the test kit's contract); they stand for the host and the Python navigator.
  host(on, statuses)
  on('process.run', ($, e) => {
    calls.push([...e.argv])
    return { value: { exitCode: 0, stdout: JSON.stringify(SAMPLE), stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  const out = await $.command.run(RUN as never)
  expect(out.text).toContain('run budgeted-pruning (world-model-planning v2, attempt 2): next audit — needs you')
  expect(out.text).toContain('study memory-loss (diagnosis, 4 action(s)): next propose')
  expect(calls[0]?.slice(2)).toEqual(['overview', '--project', '/p', '--mode', 'auto'])
  expect(statuses.at(-1)).toBe('open-scientist web+hitl · memory-loss: propose · 1 need you')
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect(await ui.find({ type: 'Text', text: /1 waiting on you/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /budgeted-pruning/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /memory-loss/ })).toBeDefined()
    expect(await ui.find({ key: 'refresh' })).toBeDefined()
    await ui.unmount()
  }
})

test('a failing navigator is shown as an error, not as an empty project', async ($, on) => {
  host(on, [])
  on('process.run', () => ({ value: { exitCode: 2, stdout: '', stderr: 'forge: boom', isStdoutTruncated: false, isStderrTruncated: false } }))
  const out = await $.command.run(RUN as never)
  expect(out.text).toContain('Open Scientist overview failed: forge: boom')
})
