export enum ResourceType {
  Database = 'database',
  Schema = 'schema',
  Table = 'table',
  Column = 'column',
}

export enum MaskType {
  Full = 'FULL',
  Partial = 'PARTIAL',
  Hash = 'HASH',
  Nullify = 'NULLIFY',
}

export enum PermissionEffect {
  Allow = 'ALLOW',
  Deny = 'DENY',
}

export interface ResourceNode {
  id: string
  name: string
  type: ResourceType
  children?: ResourceNode[]
  isPrimaryKey?: boolean
  isForeignKey?: boolean
}

export interface PermissionAction {
  name: string
  description: string
  icon: string
}

export interface RowFilterConfig {
  enabled: boolean
  conditionExpression: string
}

export interface ColumnMaskConfig {
  enabled: boolean
  maskType: MaskType
  maskPattern: string
  testValue: string
}

export interface PermissionFormState {
  activeStep: number
  selectedPath: ResourceNode[] | null
  selectedActions: string[]
  effect: PermissionEffect
  rowFilterEnabled: boolean
  conditionExpression: string
  columnMaskEnabled: boolean
  maskType: MaskType
  maskPattern: string
  testValue: string
}

export interface PermissionGrantPayload {
  resourcePath: ResourceNode[]
  resourceType: ResourceType
  actions: string[]
  effect: PermissionEffect
  rowFilter?: {
    enabled: boolean
    conditionExpression: string
  }
  columnMask?: {
    enabled: boolean
    maskType: MaskType
    maskPattern: string
  }
}

export type PermissionDrawerMode = 'create' | 'edit'

export interface AddPermissionDrawerProps {
  open: boolean
  onClose: () => void
  mode?: PermissionDrawerMode
  contextLabel: string
  contextIcon?: 'person' | 'groups' | 'shield'
  /** Pre-filled form state when mode === 'edit' (from page mapper) */
  initialFormState?: PermissionFormState | null
  onSubmit: (payload: PermissionGrantPayload) => void
  resourceTree?: ResourceNode[]
  submitDisabled?: boolean
}
