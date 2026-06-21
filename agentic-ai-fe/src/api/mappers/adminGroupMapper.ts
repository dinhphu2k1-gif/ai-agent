import type {
  AdminCatalogRoleDto,
  AdminCatalogUserDto,
  AdminGroupDto,
  AdminGroupMemberDto,
  AdminGroupRoleDto,
} from '@/api/admin/dto'
import type {
  AssignableMember,
  AssignableRoleOption,
  GroupMember,
  GroupRoleAssignment,
  UserGroup,
} from '@/pages/group-management/types'

export const mapCatalogMember = (dto: AdminCatalogUserDto): AssignableMember => ({
  id: dto.id,
  name: dto.name,
  email: dto.email,
  avatarUrl: dto.avatarUrl,
  isOnline: dto.isOnline,
})

export const mapCatalogRoleOption = (dto: AdminCatalogRoleDto): AssignableRoleOption => ({
  id: dto.id,
  name: dto.name,
  description: dto.description ?? '',
  permissionCount: dto.permissionCount ?? 0,
})

export const mapGroupListItem = (dto: AdminGroupDto): UserGroup => ({
  id: dto.id,
  name: dto.name,
  memberCount: dto.memberCount,
  roleCount: dto.roleCount,
  createdAt: dto.createdAtLabel ?? dto.createdAt ?? '',
  description: dto.description,
})

export const mapGroupMember = (dto: AdminGroupMemberDto): GroupMember => ({
  id: dto.id,
  name: dto.name,
  email: dto.email,
  initials: dto.initials ?? dto.name.slice(0, 2).toUpperCase(),
  status: dto.status === 'Inactive' || dto.status === 'inactive' ? 'Inactive' : 'Active',
  avatarUrl: dto.avatarUrl,
})

export const mapGroupRoleAssignment = (dto: AdminGroupRoleDto): GroupRoleAssignment => ({
  id: dto.id,
  name: dto.name,
  description: dto.description ?? '',
  permissionCount: dto.permissionCount,
})
