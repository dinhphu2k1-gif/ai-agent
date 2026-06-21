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
