import { normalizePermissionId } from '@/api/admin/permissionId'
import type {
  AdminEffectivePermissionDto,
  AdminPermissionDto,
  AdminPermissionModifierDto,
} from '@/api/admin/dto'
import type { InheritedSummaryDto, PermissionSummaryDto } from '@/api/admin/types'
import type { EffectivePermission } from '@/pages/group-management/types'
import type {
  Permission,
  PermissionAction,
  PermissionEffect,
  PermissionModifier,
  PermissionSummary,
  ResourceType,
} from '@/pages/role-management/types'
import type { InheritedSummary } from '@/pages/group-management/types'

const RESOURCE_TYPE_MAP: Record<string, ResourceType> = {
  database: 'DATABASE',
  schema: 'SCHEMA',
  table: 'TABLE',
  column: 'COLUMN',
  DATABASE: 'DATABASE',
  SCHEMA: 'SCHEMA',
  TABLE: 'TABLE',
  COLUMN: 'COLUMN',
}

const mapResourceType = (value: string): ResourceType =>
  RESOURCE_TYPE_MAP[value] ?? 'TABLE'

const mapEffect = (value: string): PermissionEffect =>
  value.toUpperCase() === 'DENY' ? 'DENY' : 'ALLOW'

const mapAction = (value: string): PermissionAction => {
  const upper = value.toUpperCase()
  if (upper === 'USAGE') return 'USAGE'
  if (upper === 'SELECT') return 'SELECT'
  if (upper === 'DESCRIBE') return 'DESCRIBE'
  if (upper === 'INSERT') return 'INSERT'
  if (upper === 'UPDATE') return 'UPDATE'
  if (upper === 'DELETE') return 'DELETE'
  return 'SELECT'
}

const mapModifier = (modifier?: AdminPermissionModifierDto): PermissionModifier | undefined => {
  if (!modifier) return undefined

  const type = modifier.type === 'COLUMN_MASK' ? 'COLUMN_MASK' : 'ROW_FILTER'

  return {
    type,
    label: modifier.label,
  }
}

export const mapPermission = (dto: AdminPermissionDto): Permission => ({
  id: normalizePermissionId(dto.id),
  resourceType: mapResourceType(dto.resourceType),
  path: (dto.path ?? []).map((segment) => ({
    label: segment.label,
    ...(segment.resourceId ? { resourceId: segment.resourceId } : {}),
  })),
  effect: mapEffect(dto.effect),
  action: mapAction(dto.action),
  modifier: mapModifier(dto.modifier),
  isHighlighted: dto.isHighlighted ?? dto.effect.toUpperCase() === 'DENY',
})

export const mapEffectivePermission = (dto: AdminEffectivePermissionDto): EffectivePermission => {
  const ownership = dto.ownership?.toLowerCase() === 'group' ? 'group' : 'role'

  return {
    ...mapPermission(dto),
    ownership,
    sourceRoleId: dto.sourceRoleId ?? null,
    sourceRoleName: dto.sourceRoleName,
  }
}

export const mapPermissionSummary = (summary?: PermissionSummaryDto): PermissionSummary | null => {
  if (!summary) return null

  return {
    total: summary.total,
    allowCount: summary.allowCount,
    denyCount: summary.denyCount,
    modifierCount: summary.modifierCount,
  }
}

export const mapInheritedSummary = (summary?: InheritedSummaryDto): InheritedSummary | null => {
  if (!summary) return null

  return {
    permissionCount: summary.permissionCount,
    resourceTypeCount: summary.resourceTypeCount,
    roleCount: summary.roleCount,
  }
}
