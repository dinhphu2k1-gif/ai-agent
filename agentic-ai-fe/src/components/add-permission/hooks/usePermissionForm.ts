import { useReducer, useEffect } from 'react'
import { MaskType, PermissionEffect, ResourceType } from '../types'
import type { PermissionDrawerMode } from '../types'
import { EDIT_INITIAL_ACTIVE_STEP, STEPS_CREATE } from '../constants'
import type { ResourceNode, PermissionFormState, PermissionGrantPayload } from '../types'
import { buildGrantPayload } from '../utils/buildGrantPayload'
import { normalizeWizardActions } from '../utils/permissionActions'

type Action =
  | { type: 'SET_STEP'; payload: number }
  | { type: 'SET_PATH'; payload: ResourceNode[] | null }
  | { type: 'SET_ACTIONS'; payload: string[] }
  | { type: 'SET_EFFECT'; payload: PermissionEffect }
  | { type: 'SET_ROW_FILTER_ENABLED'; payload: boolean }
  | { type: 'SET_CONDITION_EXPR'; payload: string }
  | { type: 'SET_COLUMN_MASK_ENABLED'; payload: boolean }
  | { type: 'SET_MASK_TYPE'; payload: MaskType }
  | { type: 'SET_MASK_PATTERN'; payload: string }
  | { type: 'SET_TEST_VALUE'; payload: string }
  | { type: 'HYDRATE'; payload: PermissionFormState }
  | { type: 'RESET' }

const initialState: PermissionFormState = {
  activeStep: 0,
  selectedPath: null,
  selectedActions: ['SELECT'],
  effect: PermissionEffect.Allow,
  rowFilterEnabled: false,
  conditionExpression: '',
  columnMaskEnabled: false,
  maskType: MaskType.Partial,
  maskPattern: '091-XXX-XXXX',
  testValue: '',
}

function reducer(state: PermissionFormState, action: Action): PermissionFormState {
  switch (action.type) {
    case 'SET_STEP':
      return { ...state, activeStep: action.payload }
    case 'SET_PATH':
      return { ...state, selectedPath: action.payload }
    case 'SET_ACTIONS':
      return { ...state, selectedActions: normalizeWizardActions(action.payload) }
    case 'SET_EFFECT':
      return { ...state, effect: action.payload }
    case 'SET_ROW_FILTER_ENABLED':
      return { ...state, rowFilterEnabled: action.payload }
    case 'SET_CONDITION_EXPR':
      return { ...state, conditionExpression: action.payload }
    case 'SET_COLUMN_MASK_ENABLED':
      return { ...state, columnMaskEnabled: action.payload }
    case 'SET_MASK_TYPE':
      return { ...state, maskType: action.payload }
    case 'SET_MASK_PATTERN':
      return { ...state, maskPattern: action.payload }
    case 'SET_TEST_VALUE':
      return { ...state, testValue: action.payload }
    case 'HYDRATE':
      return action.payload
    case 'RESET':
      return initialState
    default:
      return state
  }
}

type StepKind = 'resource' | 'action' | 'modifier' | 'review'

const getStepKind = (activeStep: number): StepKind =>
  (['resource', 'action', 'modifier', 'review'] as const)[activeStep] ?? 'resource'

export interface UsePermissionFormOptions {
  open: boolean
  mode?: PermissionDrawerMode
  initialFormState?: PermissionFormState | null
  onSubmit?: (payload: PermissionGrantPayload) => void
}

export const usePermissionForm = ({
  open,
  mode = 'create',
  initialFormState = null,
  onSubmit,
}: UsePermissionFormOptions) => {
  const [state, dispatch] = useReducer(reducer, initialState)

  const steps = [...STEPS_CREATE]
  const targetNode = state.selectedPath ? state.selectedPath[state.selectedPath.length - 1] : null
  const resourceType = targetNode?.type ?? null
  const stepKind = getStepKind(state.activeStep)
  const isResourceLocked = mode === 'edit'

  useEffect(() => {
    if (!open) {
      dispatch({ type: 'RESET' })
      return
    }
    if (mode === 'edit' && initialFormState) {
      dispatch({
        type: 'HYDRATE',
        payload: { ...initialFormState, activeStep: EDIT_INITIAL_ACTIVE_STEP },
      })
    } else if (mode === 'create') {
      dispatch({ type: 'RESET' })
    }
  }, [open, mode, initialFormState])

  const isStepValid = (() => {
    switch (stepKind) {
      case 'resource':
        return state.selectedPath !== null && state.selectedPath.length > 0
      case 'action':
        return state.selectedActions.length <= 1
      case 'modifier':
        if (resourceType === ResourceType.Column) {
          if (state.columnMaskEnabled && state.maskType === MaskType.Partial) {
            return state.maskPattern.trim().length > 0
          }
          return true
        }
        if (resourceType === ResourceType.Table) {
          if (state.rowFilterEnabled) {
            return state.conditionExpression.trim().length > 0
          }
          return true
        }
        return true
      case 'review':
        return true
      default:
        return false
    }
  })()

  const canSubmit =
    isStepValid &&
    state.selectedPath !== null &&
    state.selectedPath.length > 0 &&
    state.selectedActions.length === 1

  const handleNext = () => {
    if (!isStepValid) return

    if (state.activeStep < steps.length - 1) {
      dispatch({ type: 'SET_STEP', payload: state.activeStep + 1 })
      return
    }

    const payload = buildGrantPayload(state, targetNode)
    if (payload && onSubmit) {
      onSubmit(payload)
    }
  }

  const handleBack = () => {
    if (state.activeStep > 0) dispatch({ type: 'SET_STEP', payload: state.activeStep - 1 })
  }

  const setSelectedPath = (path: ResourceNode[] | null) => {
    if (mode === 'edit') return
    dispatch({ type: 'SET_PATH', payload: path })
  }

  return {
    ...state,
    mode,
    isResourceLocked,
    targetNode,
    resourceType,
    stepKind,
    steps,
    isStepValid,
    canSubmit,
    handleNext,
    handleBack,
    setSelectedPath,
    setStep: (step: number) => dispatch({ type: 'SET_STEP', payload: step }),
    setSelectedActions: (actions: string[]) => dispatch({ type: 'SET_ACTIONS', payload: actions }),
    setEffect: (effect: PermissionEffect) => dispatch({ type: 'SET_EFFECT', payload: effect }),
    rowFilter: {
      enabled: state.rowFilterEnabled,
      conditionExpression: state.conditionExpression,
    },
    onChangeRowFilter: (patch: Partial<{ enabled: boolean; conditionExpression: string }>) => {
      if (patch.enabled !== undefined) dispatch({ type: 'SET_ROW_FILTER_ENABLED', payload: patch.enabled })
      if (patch.conditionExpression !== undefined) {
        dispatch({ type: 'SET_CONDITION_EXPR', payload: patch.conditionExpression })
      }
    },
    columnMask: {
      enabled: state.columnMaskEnabled,
      maskType: state.maskType,
      maskPattern: state.maskPattern,
      testValue: state.testValue,
    },
    onChangeColumnMask: (
      patch: Partial<{ enabled: boolean; maskType: MaskType; maskPattern: string; testValue: string }>,
    ) => {
      if (patch.enabled !== undefined) dispatch({ type: 'SET_COLUMN_MASK_ENABLED', payload: patch.enabled })
      if (patch.maskType !== undefined) dispatch({ type: 'SET_MASK_TYPE', payload: patch.maskType })
      if (patch.maskPattern !== undefined) dispatch({ type: 'SET_MASK_PATTERN', payload: patch.maskPattern })
      if (patch.testValue !== undefined) dispatch({ type: 'SET_TEST_VALUE', payload: patch.testValue })
    },
  }
}
