export interface AdminUserDto {
  id: string
  name: string
  email: string
  status: string
  groups: string[]
  roles: string[]
  initials?: string
  lastActive?: string
  lastActiveAt?: string
  username?: string
}

export interface AdminUserDetailDto extends AdminUserDto {
  groups: Array<string | { id: string; name: string }>
  roles: Array<string | { id: string; name: string }>
}

export interface AdminRoleDto {
  id: string
  name: string
  displayName?: string
  permissionCount: number
  userCount: number
  groupCount: number
  icon?: 'shield' | 'shield_lock'
}

export interface AdminGroupDto {
  id: string
  name: string
  memberCount: number
  roleCount: number
  description?: string
  createdAt?: string
  createdAtLabel?: string
}

export interface AdminGroupMemberDto {
  id: string
  name: string
  email: string
  initials?: string
  status: string
  avatarUrl?: string
}

export interface AdminGroupRoleDto {
  id: string
  name: string
  description?: string
  permissionCount: number
}

export interface AdminPermissionPathDto {
  label: string
  resourceId?: string
}

export interface AdminPermissionModifierDto {
  type: string
  label: string
  conditionExpression?: string
  maskType?: string | null
  maskPattern?: string | null
}

export interface AdminPermissionDto {
  id: string
  resourceType: string
  path: AdminPermissionPathDto[]
  effect: string
  action: string
  modifier?: AdminPermissionModifierDto
  isHighlighted?: boolean
}

export interface AdminEffectivePermissionDto extends AdminPermissionDto {
  ownership: string
  sourceRoleId?: string | null
  sourceRoleName: string
}

export interface AdminCatalogUserDto {
  id: string
  name: string
  email: string
  isOnline?: boolean
  avatarUrl?: string
}

export interface AdminCatalogGroupDto {
  id: string
  name: string
  memberCount?: number
  description?: string
}

export interface AdminCatalogRoleDto {
  id: string
  name: string
  description?: string
  permissionCount?: number
}

export interface AdminResourceNodeDto {
  id: string
  name: string
  type: string
  children?: AdminResourceNodeDto[]
  isPrimaryKey?: boolean
  isForeignKey?: boolean
}
