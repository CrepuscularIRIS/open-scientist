import type { EngineInterface, Register } from 'claude-code'

import type { ForgeView } from '../types'

const PLUGIN = 'open-scientist'
const PANE = 'open-scientist'
// A const used only for $.state calls, as the state contract requires.
const VIEW = { plugin: 'open-scientist', key: 'view' } as const

// Ask the Python navigator for a read-only overview; never throws into a hook.
async function refresh($: EngineInterface, mode: string): Promise<ForgeView | null> {
  const project = await $.session.root()
  const script = `${$.plugin.root}/scripts/forge.py`
  let next: ForgeView | null
  try {
    const out = await $.process.run(['python3', script, 'overview', '--project', project, '--mode', mode], {
      timeoutMs: 20000,
    })
    next = out.exitCode === 0
      ? (JSON.parse(out.stdout) as ForgeView)
      : { project, mode, exists: true, domains: [], runs: [], attention: 0, error: out.stderr.trim().slice(0, 300) }
  } catch (err) {
    next = { project, mode, exists: true, domains: [], runs: [], attention: 0, error: String(err).slice(0, 300) }
  }
  await $.state.set(VIEW, next)
  return next
}

function statusText(v: ForgeView | null): string | undefined {
  if (!v || !v.exists) return undefined
  if (v.error) return 'open-scientist: error (see /open-scientist)'
  const parts = [`open-scientist ${v.mode}`]
  const study = (v.studies ?? []).find(s => s.type !== 'terminal')
  const active = v.runs.find(r => r.type !== 'terminal')
  if (study) parts.push(`${study.study}: ${study.step}`)
  else if (active) parts.push(`${active.run}: ${active.step}`)
  else if (v.domains.length) parts.push(`${v.domains.length} domain(s)`)
  if (v.attention) parts.push(`${v.attention} need you`)
  return parts.join(' · ')
}

function summary(v: ForgeView | null): string {
  if (!v || !v.exists) return 'Open Scientist: no .forge/ in this project yet. Ask a research question to start a study.'
  if (v.error) return `Open Scientist overview failed: ${v.error}`
  const lines = [`Open Scientist (${v.mode} mode)`]
  for (const st of v.studies ?? []) {
    lines.push(`- study ${st.study} (${st.deliverable ?? 'intake'}, ${st.actions} action(s)): next ${st.step}` +
      (st.needs_attention ? ' — needs you' : ''))
  }
  for (const d of v.domains) {
    lines.push(`- domain ${d.domain}: ${d.current ? `v${d.current}` : 'building'} — next ${d.step}` +
      (d.lessons_since_freeze ? ` — ${d.lessons_since_freeze} new lesson(s)` : ''))
  }
  for (const r of v.runs) {
    lines.push(`- run ${r.run} (${r.domain} v${r.version}, attempt ${r.attempts}): next ${r.step}` +
      (r.decision ? ` — decision ${r.decision}` : '') + (r.needs_attention ? ' — needs you' : ''))
  }
  return lines.join('\n')
}

export const register: Register = (on, options) => {
  const mode = typeof options.mode === 'string' ? options.mode : 'auto'

  on('session.start', async ($, e, next) => {
    const started = await next(e)
    await $.command.register({ name: 'open-scientist', description: 'Open Scientist: studies, domains, idea runs and the next step' })
    $.ui.status(statusText(await refresh($, mode)))
    return started
  })

  on('command.run', { command: 'open-scientist' }, async $ => {
    const v = await refresh($, mode)
    $.ui.status(statusText(v))
    void $.ui.open({ id: PANE, title: 'Open Scientist' })
    return {
      text: summary(v),
      context: [`Open Scientist default mode is ${mode}: pass --mode ${mode} on a new study's first \`forge next\`. ` +
        'Continue a study only when the person asks; follow the open-scientist skill loop.'],
    }
  })

  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    const { value: v } = await $.state.get(VIEW)
    if (v?.exists) $.ui.status(statusText(await refresh($, mode)))
    return done
  })

  on('prompt.compose', async ($, e, next) => {
    const composed = await next(e)
    const text = `Open Scientist plugin: default run mode is "${mode}". When driving the open-scientist skill, pass --mode ${mode} ` +
      'on a new run\'s first `forge next`; an existing run keeps the mode stored in its run.json. Stop at human_gate ' +
      'steps (run intake, decision) until the person answers, and record only their answer.'
    return { sections: [...composed.sections, { id: `${PLUGIN}:mode`, text, scope: 'session' }] }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button } = $.ui.resolve(e)
    const { value: v } = await $.state.get(VIEW)
    if (!v || !v.exists) {
      return (
        <Box flexDirection="column">
          <Text>No Open Scientist state in this project yet.</Text>
          <Text dimColor>Ask a research question; the open-scientist skill starts a study.</Text>
        </Box>
      )
    }
    return (
      <Box flexDirection="column">
        <Text bold>Mode: {v.mode}{v.attention ? `  ·  ${v.attention} waiting on you` : ''}</Text>
        {v.error ? <Text color="red">{v.error}</Text> : null}
        <Text bold>Studies</Text>
        {(v.studies ?? []).length === 0 ? <Text dimColor>none</Text> : null}
        {(v.studies ?? []).map(st => (
          <Box key={`s-${st.study}`} flexDirection="column">
            <Text color={st.needs_attention ? 'yellow' : undefined}>
              {st.study}  [{st.deliverable ?? 'intake'}, {st.actions} action(s){st.run_mode ? `, ${st.run_mode}` : ''}]  → {st.step}
              {st.executor ? `  (${st.executor})` : ''}
            </Text>
            <Text dimColor>  {st.goal.slice(0, 100)}</Text>
          </Box>
        ))}
        <Text bold>Domains</Text>
        {v.domains.length === 0 ? <Text dimColor>none</Text> : null}
        {v.domains.map(d => (
          <Text key={`d-${d.domain}`} color={d.needs_attention ? 'yellow' : undefined}>
            {d.domain}  {d.current ? `v${d.current}` : 'building'}  → {d.step}
            {d.lessons_since_freeze ? `  (${d.lessons_since_freeze} new lessons)` : ''}
          </Text>
        ))}
        <Text bold>Idea runs</Text>
        {v.runs.length === 0 ? <Text dimColor>none</Text> : null}
        {v.runs.map(r => (
          <Box key={`r-${r.run}`} flexDirection="column">
            <Text color={r.needs_attention ? 'yellow' : undefined}>
              {r.run}  [{r.domain} v{r.version}, attempt {r.attempts}{r.run_mode ? `, ${r.run_mode}` : ''}]  → {r.step}
              {r.executor ? `  (${r.executor})` : ''}{r.decision ? `  decision: ${r.decision}` : ''}
            </Text>
            {r.title ? <Text dimColor>  {r.title}</Text> : null}
          </Box>
        ))}
        <Button key="refresh" label="Refresh" onPress={async () => { $.ui.status(statusText(await refresh($, mode))) }} />
      </Box>
    )
  })
}
