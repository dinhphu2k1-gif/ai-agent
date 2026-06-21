import type { ActorsResponseDto } from '@/api/admin/types'
import type { RoleActors } from '@/pages/role-management/types'

export const mapRoleActors = (dto: ActorsResponseDto): RoleActors => ({
  users: dto.users.map((user) => ({
    id: user.id,
    name: user.name,
    email: user.email ?? '',
    avatarUrl: user.avatarUrl,
    isOnline: user.isOnline,
  })),
  groups: dto.groups.map((group) => ({
    id: group.id,
    name: group.name,
    memberCount: group.memberCount ?? 0,
  })),
  totalAffectedUsers: dto.totalAffectedUsers,
})
