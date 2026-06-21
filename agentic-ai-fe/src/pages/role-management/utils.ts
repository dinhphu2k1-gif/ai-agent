import type {
  ActorGroup,
  ActorUser,
  AssignableGroup,
  AssignableUser,
  Permission,
  PermissionSummary,
  ResourceGroupViewModel,
  ResourceType,
  Role,
  RoleActors,
} from './types'
import { RESOURCE_TYPE_ICONS, RESOURCE_TYPE_ORDER } from './types'

export const groupPermissionsByResource = (permissions: Permission[]): ResourceGroupViewModel[] =>
  RESOURCE_TYPE_ORDER.map((type) => {
    const grouped = permissions.filter((p) => p.resourceType === type)
    return {
      type,
      icon: RESOURCE_TYPE_ICONS[type],
      permissions: grouped,
      count: grouped.length,
    }
  }).filter((g) => g.count > 0)

export const computeSummary = (permissions: Permission[]): PermissionSummary => {
  const allowCount = permissions.filter((p) => p.effect === 'ALLOW').length
  const denyCount = permissions.filter((p) => p.effect === 'DENY').length
  const modifierCount = permissions.filter((p) => p.modifier).length

  return {
    total: permissions.length,
    allowCount,
    denyCount,
    modifierCount,
  }
}

export const syncRoleCounts = (
  role: Role,
  permissions: Permission[],
  userCount: number,
  groupCount: number,
): Role => ({
  ...role,
  permissionCount: permissions.length,
  userCount,
  groupCount,
})

export const createDefaultExpandedGroups = (): Record<ResourceType, boolean> => ({
  DATABASE: true,
  SCHEMA: true,
  TABLE: true,
  COLUMN: true,
})

export const catalogGroupToActorGroup = (group: AssignableGroup): ActorGroup => ({
  id: group.id,
  name: group.name,
  memberCount: group.memberCount,
})

export const resolveGroupsFromCatalog = (
  groupIds: string[],
  catalog: AssignableGroup[],
): ActorGroup[] =>
  groupIds
    .map((id) => catalog.find((g) => g.id === id))
    .filter((g): g is AssignableGroup => g !== undefined)
    .map(catalogGroupToActorGroup)

export const mergeGroupsIntoRoleActors = (
  current: RoleActors,
  newGroups: ActorGroup[],
): RoleActors => {
  const merged = [...current.groups]
  let addedMembers = 0

  newGroups.forEach((group) => {
    if (merged.some((g) => g.id === group.id)) return
    merged.push(group)
    addedMembers += group.memberCount
  })

  return {
    ...current,
    groups: merged,
    totalAffectedUsers: current.totalAffectedUsers + addedMembers,
  }
}

export const catalogUserToActorUser = (user: AssignableUser): ActorUser => ({
  id: user.id,
  name: user.name,
  email: user.email,
  avatarUrl: user.avatarUrl,
  isOnline: user.isOnline,
})

export const resolveUsersFromCatalog = (
  userIds: string[],
  catalog: AssignableUser[],
): ActorUser[] =>
  userIds
    .map((id) => catalog.find((u) => u.id === id))
    .filter((u): u is AssignableUser => u !== undefined)
    .map(catalogUserToActorUser)

export const mergeUsersIntoRoleActors = (
  current: RoleActors,
  newUsers: ActorUser[],
): RoleActors => {
  const merged = [...current.users]
  let addedCount = 0

  newUsers.forEach((user) => {
    if (merged.some((u) => u.id === user.id)) return
    merged.push(user)
    addedCount += 1
  })

  return {
    ...current,
    users: merged,
    totalAffectedUsers: current.totalAffectedUsers + addedCount,
  }
}
