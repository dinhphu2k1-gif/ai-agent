import { useCallback, useEffect, useState } from 'react'
import type { Dispatch, SetStateAction } from 'react'

import { USE_ADMIN_MOCK, getAdminErrorMessage, groupAdminApi, isAbortError } from '@/api/admin'
import type { PermissionSummary } from '@/pages/role-management/types'
import { computeSummary } from '@/pages/role-management/utils'

import type {
  EffectivePermission,
  GroupMember,
  GroupRoleAssignment,
  InheritedSummary,
} from '../types'
import { computeInheritedSummary, mergeEffectivePermissions } from '../utils'

export interface UseGroupDetailOptions {
  setMembersByGroupId: Dispatch<SetStateAction<Record<string, GroupMember[]>>>
  setRolesByGroupId: Dispatch<SetStateAction<Record<string, GroupRoleAssignment[]>>>
  patchGroupCounts: (groupId: string, memberCount: number, roleCount: number) => void
}

export const useGroupDetail = (
  selectedGroupId: string | null,
  { setMembersByGroupId, setRolesByGroupId, patchGroupCounts }: UseGroupDetailOptions,
) => {
  const [effectivePermissions, setEffectivePermissions] = useState<EffectivePermission[]>([])
  const [permissionSummary, setPermissionSummary] = useState<PermissionSummary | null>(null)
  const [inheritedSummary, setInheritedSummary] = useState<InheritedSummary | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState<string | null>(null)

  const refetchGroupDetail = useCallback(
    async (groupId: string, signal?: AbortSignal) => {
      setDetailLoading(true)
      setDetailError(null)
      try {
        const [members, roles, effective] = await Promise.all([
          groupAdminApi.getMembers(groupId, { signal }),
          groupAdminApi.getRoles(groupId, { signal }),
          groupAdminApi.getEffectivePermissions(groupId, { signal }),
        ])

        if (signal?.aborted) return

        setMembersByGroupId((prev) => ({ ...prev, [groupId]: members }))
        setRolesByGroupId((prev) => ({ ...prev, [groupId]: roles }))
        setEffectivePermissions(effective.permissions)
        setPermissionSummary(effective.summary)
        setInheritedSummary(effective.inheritedSummary)
        patchGroupCounts(groupId, members.length, roles.length)
      } catch (error) {
        if (isAbortError(error)) return
        setDetailError(getAdminErrorMessage(error))
      } finally {
        if (!signal?.aborted) setDetailLoading(false)
      }
    },
    [setMembersByGroupId, setRolesByGroupId, patchGroupCounts],
  )

  useEffect(() => {
    if (!selectedGroupId) {
      setEffectivePermissions([])
      setPermissionSummary(null)
      setInheritedSummary(null)
      setDetailLoading(false)
      setDetailError(null)
      return
    }

    if (USE_ADMIN_MOCK) {
      let cancelled = false
      setDetailLoading(true)
      setDetailError(null)
      setEffectivePermissions([])
      setPermissionSummary(null)
      setInheritedSummary(null)

      void Promise.all([
        import('../mock-data.dev'),
        import('@/pages/role-management/mock-data.dev'),
      ]).then(([groupMock, roleMock]) => {
        if (cancelled) return
        const groupId = selectedGroupId
        const members = groupMock.membersByGroupId[groupId] ?? []
        const roles = groupMock.rolesByGroupId[groupId] ?? []
        const merged = mergeEffectivePermissions(
          groupId,
          roles,
          roleMock.initialPermissionsByRoleId,
          groupMock.initialPermissionsByGroupId,
        )
        const roleOnlyPerms = merged.filter((p) => p.ownership === 'role')

        setMembersByGroupId((prev) => ({ ...prev, [groupId]: members }))
        setRolesByGroupId((prev) => ({ ...prev, [groupId]: roles }))
        setEffectivePermissions(merged)
        setPermissionSummary(computeSummary(merged))
        setInheritedSummary(computeInheritedSummary(roleOnlyPerms, roles.length))
        patchGroupCounts(groupId, members.length, roles.length)
        setDetailLoading(false)
      })

      return () => {
        cancelled = true
      }
    }

    const controller = new AbortController()
    setEffectivePermissions([])
    setPermissionSummary(null)
    setInheritedSummary(null)
    setDetailError(null)
    void refetchGroupDetail(selectedGroupId, controller.signal)

    return () => controller.abort()
  }, [selectedGroupId, refetchGroupDetail, patchGroupCounts, setMembersByGroupId, setRolesByGroupId])

  return {
    effectivePermissions,
    permissionSummary,
    inheritedSummary,
    detailLoading,
    detailError,
    refetchGroupDetail,
  }
}
