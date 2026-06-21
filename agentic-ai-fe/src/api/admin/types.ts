import type { PermissionGrantPayload } from '@/components/add-permission'
import type { PageableResponse } from '@/types/type'

export type { PageableResponse }

export type { PermissionGrantPayload }

export interface AdminPageParams {
  page: number
  pageSize: number
  search?: string
  sort?: string
  orderBy?: string
  status?: string
}

export interface AdminListMeta {
  currentPage: number
  totalItems: number
  totalPages: number
}

export interface AdminListResult<T> {
  items: T[]
  currentPage: number
  totalItems: number
  totalPages: number
}

export interface PermissionSummaryDto {
  total: number
  allowCount: number
  denyCount: number
  modifierCount: number
}

export interface PermissionListResponse<TPermission = unknown> {
  permissions: TPermission[]
  summary?: PermissionSummaryDto
}

export interface InheritedSummaryDto {
  permissionCount: number
  resourceTypeCount: number
  roleCount: number
}

export interface EffectivePermissionListResponse<T = unknown> {
  permissions: T[]
  summary?: PermissionSummaryDto
  inheritedSummary?: InheritedSummaryDto
}

export interface ActorsResponseDto {
  users: Array<{ id: string; name: string; email?: string; avatarUrl?: string; isOnline?: boolean }>
  groups: Array<{ id: string; name: string; memberCount?: number }>
  totalAffectedUsers: number
}

export interface CreateUserBody {
  fullName: string
  email: string
  username: string
  groups: string[]
  roles: string[]
  isActive: boolean
}

export interface BulkAssignGroupsBody {
  userIds: string[]
  groupIds?: string[]
  groupNames?: string[]
}

export interface BulkAssignRolesBody {
  userIds: string[]
  roleIds?: string[]
  roleNames?: string[]
}

export interface BulkDeactivateBody {
  userIds: string[]
}

export interface BulkMutationResult {
  updatedCount?: number
}

export interface NameOptionsResponse {
  groups?: string[]
  roles?: string[]
}

export interface CreateGroupBody {
  name: string
  description?: string
}

export interface CreateRoleBody {
  name: string
}

export interface RenameRoleBody {
  name: string
}

export interface IdListBody {
  userIds?: string[]
  groupIds?: string[]
  roleIds?: string[]
  memberIds?: string[]
}
