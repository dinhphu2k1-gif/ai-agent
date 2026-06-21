import type { AdminCatalogGroupDto, AdminCatalogUserDto, AdminRoleDto } from '@/api/admin/dto'
import type { AssignableGroup, AssignableUser, Role } from '@/pages/role-management/types'

export const mapCatalogUser = (dto: AdminCatalogUserDto): AssignableUser => ({
  id: dto.id,
  name: dto.name,
  email: dto.email,
  avatarUrl: dto.avatarUrl,
  isOnline: dto.isOnline,
})

export const mapCatalogGroup = (dto: AdminCatalogGroupDto): AssignableGroup => ({
  id: dto.id,
  name: dto.name,
  memberCount: dto.memberCount ?? 0,
  description: dto.description ?? '',
})

export const mapRoleListItem = (dto: AdminRoleDto): Role => ({
  id: dto.id,
  name: dto.name,
  permissionCount: dto.permissionCount,
  userCount: dto.userCount,
  groupCount: dto.groupCount,
  icon: dto.icon,
})
