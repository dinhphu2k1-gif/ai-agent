export type PermissionEffect = 'ALLOW' | 'DENY'

export type PermissionAction = 'USAGE' | 'SELECT' | 'DESCRIBE' | 'INSERT' | 'UPDATE' | 'DELETE'

export type PermissionModifierType = 'ROW_FILTER' | 'COLUMN_MASK'

export type ResourceType = 'DATABASE' | 'SCHEMA' | 'TABLE' | 'COLUMN'

export interface PermissionModifier {
  type: PermissionModifierType
  label: string
}

export interface PermissionPathSegment {
  label: string
  resourceId?: string
}

export interface Permission {
  id: string
  resourceType: ResourceType
  path: PermissionPathSegment[]
  effect: PermissionEffect
  action: PermissionAction
  modifier?: PermissionModifier
  isHighlighted?: boolean
}

export interface Role {
  id: string
  name: string
  permissionCount: number
  userCount: number
  groupCount: number
  icon?: 'shield' | 'shield_lock'
}

export interface ActorUser {
  id: string
  name: string
  email: string
  avatarUrl?: string
  isOnline?: boolean
}

export interface ActorGroup {
  id: string
  name: string
  memberCount: number
}

export interface AssignableGroup {
  id: string
  name: string
  memberCount: number
  description: string
}

export interface AssignableUser {
  id: string
  name: string
  email: string
  avatarUrl?: string
  isOnline?: boolean
}

export interface RoleActors {
  users: ActorUser[]
  groups: ActorGroup[]
  totalAffectedUsers: number
}

export interface ResourceGroupViewModel {
  type: ResourceType
  icon: string
  permissions: Permission[]
  count: number
}

export interface PermissionSummary {
  total: number
  allowCount: number
  denyCount: number
  modifierCount: number
}

export const RESOURCE_TYPE_ORDER: ResourceType[] = ['DATABASE', 'SCHEMA', 'TABLE', 'COLUMN']

export const RESOURCE_TYPE_ICONS: Record<ResourceType, string> = {
  DATABASE: 'database',
  SCHEMA: 'folder',
  TABLE: 'table_chart',
  COLUMN: 'view_column',
}
