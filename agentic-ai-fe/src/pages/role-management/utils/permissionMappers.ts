import type { Permission, ResourceType as ProductionResourceType } from '../types'
import {
  MaskType,
  PermissionEffect,
  ResourceType as WizardResourceType,
} from '@/components/add-permission/types'
import type { PermissionFormState, PermissionGrantPayload } from '@/components/add-permission/types'
import { formatColumnMaskModifierLabel } from '@/components/add-permission/utils/formatColumnMaskModifierLabel'
import { normalizeWizardActions } from '@/components/add-permission/utils/permissionActions'

const PRODUCTION_TO_WIZARD_RESOURCE: Record<ProductionResourceType, WizardResourceType> = {
  DATABASE: WizardResourceType.Database,
  SCHEMA: WizardResourceType.Schema,
  TABLE: WizardResourceType.Table,
  COLUMN: WizardResourceType.Column,
}

const WIZARD_TO_PRODUCTION_RESOURCE: Record<WizardResourceType, ProductionResourceType> = {
  [WizardResourceType.Database]: 'DATABASE',
  [WizardResourceType.Schema]: 'SCHEMA',
  [WizardResourceType.Table]: 'TABLE',
  [WizardResourceType.Column]: 'COLUMN',
}

const RESOURCE_ORDER: WizardResourceType[] = [
  WizardResourceType.Database,
  WizardResourceType.Schema,
  WizardResourceType.Table,
  WizardResourceType.Column,
]

const pathToResourceNodes = (permission: Permission): { path: PermissionFormState['selectedPath']; leafType: WizardResourceType } => {
  const leafType = PRODUCTION_TO_WIZARD_RESOURCE[permission.resourceType]
  const leafIndex = RESOURCE_ORDER.indexOf(leafType)
  const path = permission.path.map((segment, index) => {
    const typeIndex = leafIndex - (permission.path.length - 1 - index)
    const type = RESOURCE_ORDER[Math.max(0, typeIndex)]
    return {
      id: segment.resourceId ?? `synthetic-path-${index}`,
      name: segment.label,
      type,
    }
  })
  return { path, leafType }
}

const parseColumnMaskModifier = (label: string): { maskType: MaskType; maskPattern: string } => {
  const trimmed = label.trim()
  const colonMatch = /^([A-Z_]+):\s*(.+)$/.exec(trimmed)
  if (colonMatch) {
    const maybeType = colonMatch[1] as MaskType
    if (Object.values(MaskType).includes(maybeType)) {
      return { maskType: maybeType, maskPattern: colonMatch[2] }
    }
  }
  const upper = trimmed.toUpperCase()
  if (Object.values(MaskType).includes(upper as MaskType)) {
    return { maskType: upper as MaskType, maskPattern: '' }
  }
  return { maskType: MaskType.Partial, maskPattern: '' }
}

export const mapPermissionToFormState = (permission: Permission): PermissionFormState => {
  const { path } = pathToResourceNodes(permission)

  let rowFilterEnabled = false
  let conditionExpression = ''
  let columnMaskEnabled = false
  let maskType = MaskType.Partial
  let maskPattern = ''

  if (permission.modifier?.type === 'ROW_FILTER') {
    rowFilterEnabled = true
    conditionExpression =
      permission.modifier.label === 'Row Filter' ? '' : permission.modifier.label
  } else if (permission.modifier?.type === 'COLUMN_MASK') {
    columnMaskEnabled = true
    const parsed = parseColumnMaskModifier(permission.modifier.label)
    maskType = parsed.maskType
    maskPattern = parsed.maskPattern
  }

  const effect =
    permission.effect === 'DENY' ? PermissionEffect.Deny : PermissionEffect.Allow

  return {
    activeStep: 0,
    selectedPath: path,
    selectedActions: normalizeWizardActions([permission.action]),
    effect,
    rowFilterEnabled,
    conditionExpression,
    columnMaskEnabled,
    maskType,
    maskPattern,
    testValue: '',
  }
}

export const mapGrantPayloadToPermission = (
  permissionId: string,
  payload: PermissionGrantPayload,
  existing?: Permission,
): Permission => {
  const resourceType = WIZARD_TO_PRODUCTION_RESOURCE[payload.resourceType]
  const path = payload.resourcePath.map((node) => ({ label: node.name }))
  const action = payload.actions[0] ?? 'SELECT'

  const permission: Permission = {
    id: permissionId,
    resourceType,
    path,
    effect: payload.effect,
    action: action as Permission['action'],
    isHighlighted: existing?.isHighlighted,
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
}
