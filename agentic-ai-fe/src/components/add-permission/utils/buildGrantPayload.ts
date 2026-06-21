import type { PermissionFormState, PermissionGrantPayload, ResourceNode } from '../types'
import { ResourceType } from '../types'
import { normalizeWizardActions } from './permissionActions'
import { sanitizeResourcePathForApi } from './sanitizeResourcePathForApi'

export const buildGrantPayload = (
  state: PermissionFormState,
  targetNode: ResourceNode | null,
): PermissionGrantPayload | null => {
  if (!state.selectedPath?.length || !targetNode) return null

  const payload: PermissionGrantPayload = {
    resourcePath: sanitizeResourcePathForApi(state.selectedPath),
    resourceType: targetNode.type,
    actions: normalizeWizardActions(state.selectedActions),
    effect: state.effect,
  }

  if (targetNode.type === ResourceType.Table && state.rowFilterEnabled) {
    payload.rowFilter = {
      enabled: true,
      conditionExpression: state.conditionExpression,
    }
  }

  if (targetNode.type === ResourceType.Column && state.columnMaskEnabled) {
    payload.columnMask = {
      enabled: true,
      maskType: state.maskType,
      maskPattern: state.maskPattern,
    }
  }

  return payload
}
