import type {
  Permission,
  PermissionSummary,
  ResourceGroupViewModel,
  ResourceType,
} from '@/pages/role-management/types'

export type { Permission, PermissionSummary, ResourceGroupViewModel, ResourceType }

export type PermissionOwnership = 'group' | 'role'

export interface EffectivePermission extends Permission {
  ownership: PermissionOwnership
  /** Set when `ownership === 'role'`; null for direct group grants */
  sourceRoleId: string | null
  sourceRoleName: string
}

export interface EffectiveResourceGroupViewModel extends Omit<ResourceGroupViewModel, 'permissions'> {
  permissions: EffectivePermission[]
}

export interface UserGroup {
  id: string
  name: string
  memberCount: number
  roleCount: number
  createdAt: string
  description?: string
}

export interface GroupMember {
  id: string
  name: string
  email: string
  initials: string
  status: 'Active' | 'Inactive'
  avatarUrl?: string
}

export interface GroupRoleAssignment {
  id: string
  name: string
  description: string
  permissionCount: number
}

export interface AssignableMember {
  id: string
  name: string
  email: string
  avatarUrl?: string
  isOnline?: boolean
}

export interface AssignableRoleOption {
  id: string
  name: string
  description: string
  permissionCount: number
}

export interface InheritedSummary {
  permissionCount: number
  resourceTypeCount: number
  roleCount: number
}
