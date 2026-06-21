import type { AdminUserDetailDto, AdminUserDto } from '@/api/admin/dto'
import type { User } from '@/pages/user-management/components/UserTable'

export const deriveInitials = (name: string): string => {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0] ?? ''}${parts[parts.length - 1][0] ?? ''}`.toUpperCase()
}

const mapStatus = (status: string): User['status'] => {
  const normalized = status.toLowerCase()
  if (normalized === 'inactive') return 'Inactive'
  return 'Active'
}

export const mapUserListItem = (dto: AdminUserDto): User => ({
  id: dto.id,
  name: dto.name,
  email: dto.email,
  status: mapStatus(dto.status),
  groups: dto.groups ?? [],
  roles: dto.roles ?? [],
  lastActive: dto.lastActive ?? '',
  initials: dto.initials ?? deriveInitials(dto.name),
})

const mapNamedRefList = (items: AdminUserDetailDto['groups']) =>
  (items ?? []).map((item) =>
    typeof item === 'string' ? { id: item, name: item } : { id: item.id, name: item.name },
  )

export const mapUserDetail = (dto: AdminUserDetailDto): User => {
  const groupRefs = mapNamedRefList(dto.groups)
  const roleRefs = mapNamedRefList(dto.roles)

  return {
    ...mapUserListItem(dto),
    groups: groupRefs.map((ref) => ref.name),
    roles: roleRefs.map((ref) => ref.name),
    groupRefs,
    roleRefs,
  }
}
