/** Actions exposed in the permission wizard (must match BE catalog for table/column). */
export const WIZARD_ACTION_NAMES = ['SELECT', 'DESCRIBE'] as const

export type WizardActionName = (typeof WIZARD_ACTION_NAMES)[number]

export const isWizardActionName = (value: string): value is WizardActionName =>
  (WIZARD_ACTION_NAMES as readonly string[]).includes(value)

/** At most one wizard action; empty array means "none selected". */
export const normalizeWizardActions = (actions: string[]): string[] => {
  const seen = new Set<string>()
  const normalized: string[] = []
  for (const action of actions) {
    if (!isWizardActionName(action) || seen.has(action)) continue
    seen.add(action)
    normalized.push(action)
    if (normalized.length >= 1) break
  }
  return normalized
}
