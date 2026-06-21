import { useCallback, useEffect, useState } from 'react'

import { USE_ADMIN_MOCK, getAdminErrorMessage, isAbortError, roleAdminApi } from '@/api/admin'

import type { Permission, PermissionSummary, RoleActors } from '../types'
import { computeSummary } from '../utils'

const emptyActors: RoleActors = { users: [], groups: [], totalAffectedUsers: 0 }

export const useRoleDetail = (selectedRoleId: string | null) => {
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [permissionSummary, setPermissionSummary] = useState<PermissionSummary | null>(null)
  const [permissionsLoading, setPermissionsLoading] = useState(false)

  const [actors, setActors] = useState<RoleActors>(emptyActors)
  const [actorsLoading, setActorsLoading] = useState(false)
  const [detailError, setDetailError] = useState<string | null>(null)

  const refetchPermissions = useCallback(async (roleId: string) => {
    const permRes = await roleAdminApi.getPermissions(roleId)
    setPermissions(permRes.permissions)
    setPermissionSummary(permRes.summary ?? computeSummary(permRes.permissions))
    return permRes
  }, [])

  const refetchActors = useCallback(async (roleId: string) => {
    const actorsRes = await roleAdminApi.getActors(roleId)
    setActors(actorsRes)
    return actorsRes
  }, [])

  const refetchDetail = useCallback(
    async (roleId: string) => {
      setDetailError(null)
      setPermissionsLoading(true)
      setActorsLoading(true)
      try {
        const [permRes, actorsRes] = await Promise.all([
          refetchPermissions(roleId),
          refetchActors(roleId),
        ])
        return { permRes, actorsRes }
      } catch (error) {
        if (!isAbortError(error)) {
          setDetailError(getAdminErrorMessage(error))
        }
        throw error
      } finally {
        setPermissionsLoading(false)
        setActorsLoading(false)
      }
    },
    [refetchPermissions, refetchActors],
  )

  useEffect(() => {
    if (!selectedRoleId) {
      setPermissions([])
      setPermissionSummary(null)
      setActors(emptyActors)
      setPermissionsLoading(false)
      setActorsLoading(false)
      setDetailError(null)
      return
    }

    if (USE_ADMIN_MOCK) {
      let cancelled = false
      setPermissionsLoading(true)
      setActorsLoading(true)
      setDetailError(null)
      setPermissions([])
      setPermissionSummary(null)
      setActors(emptyActors)

      void import('../mock-data.dev').then((mock) => {
        if (cancelled) return
        const perms = mock.initialPermissionsByRoleId[selectedRoleId] ?? []
        const roleActors = mock.initialActorsByRoleId[selectedRoleId] ?? emptyActors
        setPermissions(perms)
        setPermissionSummary(computeSummary(perms))
        setActors(roleActors)
        setPermissionsLoading(false)
        setActorsLoading(false)
      })

      return () => {
        cancelled = true
      }
    }

    const controller = new AbortController()
    setPermissionsLoading(true)
    setActorsLoading(true)
    setDetailError(null)
    setPermissions([])
    setPermissionSummary(null)
    setActors(emptyActors)

    Promise.all([
      roleAdminApi.getPermissions(selectedRoleId, { signal: controller.signal }),
      roleAdminApi.getActors(selectedRoleId, { signal: controller.signal }),
    ])
      .then(([permRes, actorsRes]) => {
        if (controller.signal.aborted) return
        setPermissions(permRes.permissions)
        setPermissionSummary(permRes.summary ?? computeSummary(permRes.permissions))
        setActors(actorsRes)
      })
      .catch((error) => {
        if (isAbortError(error)) return
        setDetailError(getAdminErrorMessage(error))
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setPermissionsLoading(false)
          setActorsLoading(false)
        }
      })

    return () => controller.abort()
  }, [selectedRoleId])

  return {
    permissions,
    permissionSummary,
    permissionsLoading,
    actors,
    actorsLoading,
    detailError,
    refetchPermissions,
    refetchActors,
    refetchDetail,
  }
}
