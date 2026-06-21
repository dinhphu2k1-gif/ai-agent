import { useReducer, useEffect } from 'react'
import { MaskType, PermissionEffect, ResourceType } from '../../types'
import { STEPS } from '../../constants'
import type { ResourceNode, PermissionFormState } from '../../types'

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
      return { ...state, selectedActions: action.payload }
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
    case 'RESET':
      return initialState
    default:
      return state
  }
}

export const usePermissionForm = (open: boolean) => {
  const [state, dispatch] = useReducer(reducer, initialState)

  const targetNode = state.selectedPath ? state.selectedPath[state.selectedPath.length - 1] : null
  const resourceType = targetNode?.type ?? null


  // Reset form when drawer closes
  useEffect(() => {
    if (!open) dispatch({ type: 'RESET' })
  }, [open])

  const isStepValid = (() => {
    switch (state.activeStep) {
      case 0:
        return state.selectedPath !== null && state.selectedPath.length > 0
      case 1:
        return state.selectedActions.length > 0
      case 2:
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
      case 3:
        return true
      default:
        return false
    }
  })()

  const handleNext = () => {
    if (isStepValid && state.activeStep < STEPS.length - 1)
      dispatch({ type: 'SET_STEP', payload: state.activeStep + 1 })
  }

  const handleBack = () => {
    if (state.activeStep > 0) dispatch({ type: 'SET_STEP', payload: state.activeStep - 1 })
  }

  return {
    ...state,
    targetNode,
    resourceType,
    steps: STEPS,
    isStepValid,
    handleNext,
    handleBack,
    setSelectedPath: (path: ResourceNode[] | null) => dispatch({ type: 'SET_PATH', payload: path }),
    setStep: (step: number) => dispatch({ type: 'SET_STEP', payload: step }),
    setSelectedActions: (actions: string[]) => dispatch({ type: 'SET_ACTIONS', payload: actions }),
    setEffect: (effect: PermissionEffect) => dispatch({ type: 'SET_EFFECT', payload: effect }),
    // Grouped config objects (Option A)
    rowFilter: {
      enabled: state.rowFilterEnabled,
      conditionExpression: state.conditionExpression,
    },
    onChangeRowFilter: (patch: Partial<{ enabled: boolean; conditionExpression: string }>) => {
      if (patch.enabled !== undefined) dispatch({ type: 'SET_ROW_FILTER_ENABLED', payload: patch.enabled })
      if (patch.conditionExpression !== undefined) dispatch({ type: 'SET_CONDITION_EXPR', payload: patch.conditionExpression })
    },
    columnMask: {
      enabled: state.columnMaskEnabled,
      maskType: state.maskType,
      maskPattern: state.maskPattern,
      testValue: state.testValue,
    },
    onChangeColumnMask: (patch: Partial<{ enabled: boolean; maskType: MaskType; maskPattern: string; testValue: string }>) => {
      if (patch.enabled !== undefined) dispatch({ type: 'SET_COLUMN_MASK_ENABLED', payload: patch.enabled })
      if (patch.maskType !== undefined) dispatch({ type: 'SET_MASK_TYPE', payload: patch.maskType })
      if (patch.maskPattern !== undefined) dispatch({ type: 'SET_MASK_PATTERN', payload: patch.maskPattern })
      if (patch.testValue !== undefined) dispatch({ type: 'SET_TEST_VALUE', payload: patch.testValue })
    },
  }
}
