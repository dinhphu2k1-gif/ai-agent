import type { Permission, PermissionAction, ResourceType } from '@/pages/role-management/types'
import { ResourceType as WizardResourceType } from '../types'
import type { PermissionGrantPayload } from '../types'
import { formatColumnMaskModifierLabel } from './formatColumnMaskModifierLabel'

const WIZARD_TO_PRODUCTION_RESOURCE: Record<WizardResourceType, ResourceType> = {
  [WizardResourceType.Database]: 'DATABASE',
  [WizardResourceType.Schema]: 'SCHEMA',
  [WizardResourceType.Table]: 'TABLE',
  [WizardResourceType.Column]: 'COLUMN',
}

const toProductionAction = (action: string): PermissionAction => {
  const upper = action.toUpperCase()
  if (
    upper === 'USAGE' ||
    upper === 'SELECT' ||
    upper === 'INSERT' ||
    upper === 'UPDATE' ||
    upper === 'DELETE'
  ) {
    return upper as PermissionAction
  }
  return 'SELECT'
}

export const mapGrantPayloadToPermissions = (payload: PermissionGrantPayload): Permission[] => {
  const resourceType = WIZARD_TO_PRODUCTION_RESOURCE[payload.resourceType]
  const path = payload.resourcePath.map((node) => ({ label: node.name }))
  const baseId = Date.now()

  return payload.actions.map((action, index) => {
    const permission: Permission = {
      id: `perm-${baseId}-${index}`,
      resourceType,
      path,
      effect: payload.effect,
      action: toProductionAction(action),
    }

    if (payload.rowFilter?.enabled && payload.rowFilter.conditionExpression.trim()) {
      permission.modifier = {
        type: 'ROW_FILTER',
        label: payload.rowFilter.conditionExpression.trim(),
      }
    } else if (payload.columnMask?.enabled) {
      permission.modifier = {
        type: 'COLUMN_MASK',
        label: formatColumnMaskModifierLabel(
          payload.columnMask.maskType,
          payload.columnMask.maskPattern,
        ),
      }
    }

    return permission
  })
}
