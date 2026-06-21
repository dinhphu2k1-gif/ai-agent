import { ResourceType } from './types'
import type { PermissionAction } from './types'

export const STEPS_CREATE = ['Resource', 'Actions & Effect', 'Modifier', 'Review'] as const

/** Same labels as create; edit mode shows step 0 (Resource) read-only */
export const STEPS_EDIT = [...STEPS_CREATE] as const

/** Edit opens on step 2 — Actions & Effect (0-based index 1) */
export const EDIT_INITIAL_ACTIVE_STEP = 1

/** @deprecated Use STEPS_CREATE */
export const STEPS = [...STEPS_CREATE]

export const TYPE_ICONS: Record<ResourceType, { icon: string; color: string }> = {
  [ResourceType.Database]: { icon: 'database', color: 'var(--mui-palette-secondary-main)' },
  [ResourceType.Schema]: { icon: 'folder', color: 'var(--mui-palette-tertiary)' },
  [ResourceType.Table]: { icon: 'table_view', color: 'var(--mui-palette-onSecondaryContainer)' },
  [ResourceType.Column]: { icon: 'view_column', color: 'var(--mui-palette-onSurfaceVariant)' },
}

export const AVAILABLE_ACTIONS: PermissionAction[] = [
  { name: 'SELECT', description: 'Read rows', icon: 'visibility' },
  { name: 'DESCRIBE', description: 'View structure', icon: 'info' },
]
