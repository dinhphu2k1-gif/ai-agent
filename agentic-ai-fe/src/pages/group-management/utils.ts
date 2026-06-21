import {
  computeSummary,
  groupPermissionsByResource,
} from '@/pages/role-management/utils'
import type { Permission, ResourceType } from '@/pages/role-management/types'
import type {
  AssignableMember,
  AssignableRoleOption,
  EffectivePermission,
  EffectiveResourceGroupViewModel,
  GroupMember,
  GroupRoleAssignment,
  InheritedSummary,
  UserGroup,
} from './types'

export const filterGroups = (groups: UserGroup[], query: string): UserGroup[] => {
  const q = query.trim().toLowerCase()
  if (!q) return groups
  return groups.filter((g) => g.name.toLowerCase().includes(q))
}

export const filterMembers = (members: GroupMember[], query: string): GroupMember[] => {
  const q = query.trim().toLowerCase()
  if (!q) return members
  return members.filter(
    (m) => m.name.toLowerCase().includes(q) || m.email.toLowerCase().includes(q),
  )
}

export const mergeEffectivePermissions = (
  groupId: string | null,
  roles: GroupRoleAssignment[],
  permissionsByRoleId: Record<string, Permission[]>,
  permissionsByGroupId: Record<string, Permission[]>,
): EffectivePermission[] => {
  const seen = new Set<string>()
  const merged: EffectivePermission[] = []

  if (groupId) {
    const direct = permissionsByGroupId[groupId] ?? []
    direct.forEach((perm) => {
      if (seen.has(perm.id)) return
      seen.add(perm.id)
      merged.push({
        ...perm,
        ownership: 'group',
        sourceRoleId: null,
        sourceRoleName: 'Direct',
      })
    })
  }

  roles.forEach((role) => {
    const perms = permissionsByRoleId[role.id] ?? []
    perms.forEach((perm) => {
      if (seen.has(perm.id)) return
      seen.add(perm.id)
      merged.push({
        ...perm,
        ownership: 'role',
        sourceRoleId: role.id,
        sourceRoleName: role.name,
      })
    })
  })

  return merged
}

/** @deprecated Use mergeEffectivePermissions */
export const mergePermissionsFromRoles = mergeEffectivePermissions

export const refreshRolePermissionCounts = (
  roles: GroupRoleAssignment[],
  permissionsByRoleId: Record<string, Permission[]>,
): GroupRoleAssignment[] =>
  roles.map((role) => ({
    ...role,
    permissionCount: (permissionsByRoleId[role.id] ?? []).length,
  }))

export const groupEffectivePermissionsByResource = (
  permissions: EffectivePermission[],
): EffectiveResourceGroupViewModel[] =>
  groupPermissionsByResource(permissions).map((group) => ({
    ...group,
    permissions: group.permissions as EffectivePermission[],
  }))

export const computeInheritedSummary = (
  permissions: Permission[],
  roleCount: number,
): InheritedSummary => ({
  permissionCount: permissions.length,
  resourceTypeCount: new Set(permissions.map((p) => p.resourceType)).size,
  roleCount,
})

export const syncGroupCounts = (
  group: UserGroup,
  memberCount: number,
  roleCount: number,
): UserGroup => ({
  ...group,
  memberCount,
  roleCount,
})

export const createDefaultExpandedGroups = (): Record<ResourceType, boolean> => ({
  DATABASE: true,
  SCHEMA: true,
  TABLE: true,
  COLUMN: true,
})

export const catalogMemberToGroupMember = (member: AssignableMember): GroupMember => ({
  id: member.id,
  name: member.name,
  email: member.email,
  initials: member.name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase(),
  status: member.isOnline ? 'Active' : 'Inactive',
  avatarUrl: member.avatarUrl,
})

export const resolveMembersFromCatalog = (
  memberIds: string[],
  catalog: AssignableMember[],
): GroupMember[] =>
  memberIds
    .map((id) => catalog.find((m) => m.id === id))
    .filter((m): m is AssignableMember => m !== undefined)
    .map(catalogMemberToGroupMember)

export const mergeMembersIntoGroup = (
  current: GroupMember[],
  newMembers: GroupMember[],
): GroupMember[] => {
  const merged = [...current]
  newMembers.forEach((member) => {
    if (merged.some((m) => m.id === member.id)) return
    merged.push(member)
  })
  return merged
}

export const catalogRoleToAssignment = (role: AssignableRoleOption): GroupRoleAssignment => ({
  id: role.id,
  name: role.name,
  description: role.description,
  permissionCount: role.permissionCount,
})

export const resolveRolesFromCatalog = (
  roleIds: string[],
  catalog: AssignableRoleOption[],
): GroupRoleAssignment[] =>
  roleIds
    .map((id) => catalog.find((r) => r.id === id))
    .filter((r): r is AssignableRoleOption => r !== undefined)
    .map(catalogRoleToAssignment)

export const mergeRolesIntoGroup = (
  current: GroupRoleAssignment[],
  newRoles: GroupRoleAssignment[],
): GroupRoleAssignment[] => {
  const merged = [...current]
  newRoles.forEach((role) => {
    if (merged.some((r) => r.id === role.id)) return
    merged.push(role)
  })
  return merged
}

export { groupPermissionsByResource, computeSummary }
