export type ForgeItem = {
  step: string
  type: string
  executor: string | null
  needs_attention: boolean
}

export type ForgeDomain = ForgeItem & {
  domain: string
  current: number | null
  versions: number[]
  lessons_since_freeze: number
}

export type ForgeRun = ForgeItem & {
  run: string
  domain: string
  version: number
  question: string
  attempts: number
  run_mode?: string
  title: string | null
  decision: string | null
  card: string | null
}

export type ForgeStudy = ForgeItem & {
  study: string
  goal: string
  deliverable: string | null
  actions: number
  run_mode?: string
}

export type ForgeView = {
  project: string
  mode: string
  exists: boolean
  studies?: ForgeStudy[]
  domains: ForgeDomain[]
  runs: ForgeRun[]
  attention: number
  error?: string
}

declare module 'claude-code' {
  interface PluginState {
    'open-scientist': { view: ForgeView | null }
  }
}
