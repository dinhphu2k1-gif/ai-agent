import { useCallback, useEffect, useMemo, useState } from 'react'
import { Box } from '@mui/material'

import {
  AdminApiError,
  USE_ADMIN_MOCK,
  getAdminErrorMessage,
  resourceAdminApi,
  roleAdminApi,
} from '@/api/admin'
import AdminErrorAlert from '@/components/admin/AdminErrorAlert'
import {
  AddPermissionDrawer,
  MOCK_RESOURCES,
} from '@/components/add-permission'
import type { PermissionGrantPayload, ResourceNode } from '@/components/add-permission'
import { useAppDispatch } from '@/redux/hooks'
import { setAlert } from '@/redux/reducers/AlertSlice'

import RoleManagementWorkspace from './components/RoleManagementWorkspace'
import RoleListPanel from './components/RoleListPanel'
import PermissionsPanel from './components/PermissionsPanel'
import ActorsPanel from './components/ActorsPanel'
import AddRoleDrawer from './components/AddRoleDrawer'
import type { RoleFormData } from './components/AddRoleDrawer'
import AssignGroupsToRoleDrawer from './components/AssignGroupsToRoleDrawer'
import AssignUsersToRoleDrawer from './components/AssignUsersToRoleDrawer'
import ConfirmDeletePermissionModal from './components/ConfirmDeletePermissionModal'
import ConfirmDeleteRoleModal from './components/ConfirmDeleteRoleModal'
import RenameRoleDialog from './components/RenameRoleDialog'
import { useRoleDetail } from './hooks/useRoleDetail'
import type { ResourceType, Role } from './types'
import { computeSummary, createDefaultExpandedGroups, groupPermissionsByResource } from './utils'
import { mapPermissionToFormState } from './utils/permissionMappers'

type PermissionDrawerState =
  | 'closed'
  | 'create'
  | { mode: 'edit'; permissionId: string }

const RoleManagementPage = () => {
  const dispatch = useAppDispatch()

  const [roles, setRoles] = useState<Role[]>([])
  const [rolesLoading, setRolesLoading] = useState(true)
  const [listError, setListError] = useState<string | null>(null)
  const [selectedRoleId, setSelectedRoleId] = useState<string | null>(null)
  const [roleSearchQuery, setRoleSearchQuery] = useState('')
  const [expandedGroups, setExpandedGroups] = useState(createDefaultExpandedGroups)
  const [showAllUsers, setShowAllUsers] = useState(false)

  const [resourceTree, setResourceTree] = useState<ResourceNode[] | null>(null)

  const [addRoleOpen, setAddRoleOpen] = useState(false)
  const [addRoleSubmitting, setAddRoleSubmitting] = useState(false)
  const [permissionDrawer, setPermissionDrawer] = useState<PermissionDrawerState>('closed')
  const [permissionSubmitting, setPermissionSubmitting] = useState(false)
  const [assignUsersOpen, setAssignUsersOpen] = useState(false)
  const [assignGroupsOpen, setAssignGroupsOpen] = useState(false)
  const [deletePermissionId, setDeletePermissionId] = useState<string | null>(null)
  const [deletePermissionSubmitting, setDeletePermissionSubmitting] = useState(false)
  const [deleteRoleId, setDeleteRoleId] = useState<string | null>(null)
  const [deleteRoleError, setDeleteRoleError] = useState<string | null>(null)
  const [deleteRoleSubmitting, setDeleteRoleSubmitting] = useState(false)
  const [actorMutationSubmitting, setActorMutationSubmitting] = useState(false)
  const [renameRoleId, setRenameRoleId] = useState<string | null>(null)
  const [renameSubmitting, setRenameSubmitting] = useState(false)

  const {
    permissions,
    permissionSummary,
    permissionsLoading,
    actors,
    actorsLoading,
    detailError,
    refetchPermissions,
    refetchActors,
    refetchDetail,
  } = useRoleDetail(selectedRoleId)

  const fetchRoles = useCallback(async () => {
    setRolesLoading(true)
    setListError(null)
    try {
      const { items } = await roleAdminApi.list({ page: 1, pageSize: 100 })
      setRoles(items)
      setSelectedRoleId((prev) => {
        if (prev && items.some((r) => r.id === prev)) return prev
        return items[0]?.id ?? null
      })
    } catch (error) {
      const message = getAdminErrorMessage(error)
      setListError(message)
      dispatch(setAlert({ children: message, severity: 'error' }))
    } finally {
      setRolesLoading(false)
    }
  }, [dispatch])

  useEffect(() => {
    if (USE_ADMIN_MOCK) {
      let cancelled = false
      setRolesLoading(true)
      setListError(null)
      void import('./mock-data.dev').then((mock) => {
        if (cancelled) return
        setRoles(mock.initialRoles)
        setSelectedRoleId((prev) => {
          if (prev && mock.initialRoles.some((r) => r.id === prev)) return prev
          return mock.INITIAL_ROLE_ID
        })
        setRolesLoading(false)
      })
      return () => {
        cancelled = true
      }
    }
    void fetchRoles()
  }, [fetchRoles])

  useEffect(() => {
    const controller = new AbortController()
    resourceAdminApi
      .getTree({ signal: controller.signal })
      .then(setResourceTree)
      .catch(() => setResourceTree(null))
    return () => controller.abort()
  }, [])

  const filteredRoles = useMemo(() => {
    const q = roleSearchQuery.trim().toLowerCase()
    if (!q) return roles
    return roles.filter((r) => r.name.toLowerCase().includes(q))
  }, [roles, roleSearchQuery])

  const selectedRole = useMemo(
    () => roles.find((r) => r.id === selectedRoleId) ?? null,
    [roles, selectedRoleId],
  )

  const resourceGroups = useMemo(
    () => groupPermissionsByResource(permissions),
    [permissions],
  )

  const displaySummary = permissionSummary ?? computeSummary(permissions)

  const patchSelectedRoleCounts = useCallback(
    (permCount: number, userCount: number, groupCount: number) => {
      if (!selectedRoleId) return
      setRoles((prev) =>
        prev.map((role) =>
          role.id === selectedRoleId
            ? {
                ...role,
                permissionCount: permCount,
                userCount,
                groupCount,
              }
            : role,
        ),
      )
    },
    [selectedRoleId],
  )

  const syncCountsFromDetail = useCallback(async () => {
    if (!selectedRoleId) return
    const [permRes, actorsRes] = await Promise.all([
      refetchPermissions(selectedRoleId),
      refetchActors(selectedRoleId),
    ])
    patchSelectedRoleCounts(
      permRes.permissions.length,
      actorsRes.users.length,
      actorsRes.groups.length,
    )
  }, [selectedRoleId, refetchPermissions, refetchActors, patchSelectedRoleCounts])

  const editingPermission = useMemo(() => {
    if (typeof permissionDrawer !== 'object') return null
    return permissions.find((p) => p.id === permissionDrawer.permissionId) ?? null
  }, [permissionDrawer, permissions])

  const editFormInitialState = useMemo(
    () => (editingPermission ? mapPermissionToFormState(editingPermission) : null),
    [editingPermission],
  )

  const permissionDrawerOpen = permissionDrawer !== 'closed'
  const permissionDrawerMode =
    permissionDrawer === 'create' || permissionDrawer === 'closed' ? 'create' : 'edit'

  const deletePermissionPath = useMemo(() => {
    if (!deletePermissionId) return ''
    const perm = permissions.find((p) => p.id === deletePermissionId)
    return perm ? perm.path.map((s) => s.label).join(' / ') : ''
  }, [deletePermissionId, permissions])

  const handleSelectRole = (roleId: string) => {
    setSelectedRoleId(roleId)
    setShowAllUsers(false)
    setExpandedGroups(createDefaultExpandedGroups())
    setPermissionDrawer('closed')
  }

  const handleRenameRole = useCallback(
    async (name: string) => {
      if (!renameRoleId) return
      setRenameSubmitting(true)
      try {
        const updated = await roleAdminApi.rename(renameRoleId, { name })
        dispatch(setAlert({ children: 'Role renamed successfully', severity: 'success' }))
        setRoles((prev) => prev.map((r) => (r.id === renameRoleId ? { ...r, name: updated.name } : r)))
        setRenameRoleId(null)
      } catch (error) {
        dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
        throw error
      } finally {
        setRenameSubmitting(false)
      }
    },
    [dispatch, renameRoleId],
  )

  const handleAddRole = useCallback(
    async (data: RoleFormData) => {
      setAddRoleSubmitting(true)
      try {
        const created = await roleAdminApi.create({ name: data.name })
        dispatch(setAlert({ children: 'Role created successfully', severity: 'success' }))
        setAddRoleOpen(false)
        await fetchRoles()
        setSelectedRoleId(created.id)
      } catch (error) {
        dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
        throw error
      } finally {
        setAddRoleSubmitting(false)
      }
    },
    [dispatch, fetchRoles],
  )

  const handleRequestDeleteRole = useCallback(
    (roleId: string) => {
      if (roles.length <= 1) {
        dispatch(
          setAlert({
            children: 'Cannot delete the last role in the system',
            severity: 'error',
          }),
        )
        return
      }
      setDeleteRoleError(null)
      setDeleteRoleId(roleId)
    },
    [roles.length, dispatch],
  )

  const handleCloseDeleteRoleModal = useCallback(() => {
    if (deleteRoleSubmitting) return
    setDeleteRoleId(null)
    setDeleteRoleError(null)
  }, [deleteRoleSubmitting])

  const handleConfirmDeleteRole = useCallback(async () => {
    if (!deleteRoleId) return

    setDeleteRoleSubmitting(true)
    try {
      await roleAdminApi.delete(deleteRoleId)
      dispatch(setAlert({ children: 'Role deleted', severity: 'success' }))
      const remaining = roles.filter((r) => r.id !== deleteRoleId)
      const nextSelected =
        selectedRoleId === deleteRoleId ? (remaining[0]?.id ?? null) : selectedRoleId
      setSelectedRoleId(nextSelected)
      await fetchRoles()
    } catch (error) {
      const message = getAdminErrorMessage(error)
      setDeleteRoleError(message)
      if (error instanceof AdminApiError && error.status === 409) {
        dispatch(
          setAlert({
            children: error.message || 'Role is in use and cannot be deleted',
            severity: 'error',
          }),
        )
        throw error
      }
      dispatch(setAlert({ children: message, severity: 'error' }))
      throw error
    } finally {
      setDeleteRoleSubmitting(false)
    }
  }, [deleteRoleId, roles, selectedRoleId, dispatch, fetchRoles])

  const handleToggleGroup = (type: ResourceType) => {
    setExpandedGroups((prev) => ({ ...prev, [type]: !prev[type] }))
  }

  const handleConfirmDeletePermission = useCallback(async () => {
    if (!deletePermissionId || !selectedRoleId) return
    setDeletePermissionSubmitting(true)
    try {
      await roleAdminApi.deletePermission(selectedRoleId, deletePermissionId)
      dispatch(setAlert({ children: 'Permission removed', severity: 'success' }))
      setDeletePermissionId(null)
      await syncCountsFromDetail()
    } catch (error) {
      dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
      throw error
    } finally {
      setDeletePermissionSubmitting(false)
    }
  }, [deletePermissionId, selectedRoleId, dispatch, syncCountsFromDetail])

  const handleUnassignUser = useCallback(
    async (userId: string) => {
      if (!selectedRoleId) return
      setActorMutationSubmitting(true)
      try {
        await roleAdminApi.unassignUser(selectedRoleId, userId)
        await syncCountsFromDetail()
      } catch (error) {
        dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
      } finally {
        setActorMutationSubmitting(false)
      }
    },
    [selectedRoleId, dispatch, syncCountsFromDetail],
  )

  const handleUnassignGroup = useCallback(
    async (groupId: string) => {
      if (!selectedRoleId) return
      setActorMutationSubmitting(true)
      try {
        await roleAdminApi.unassignGroup(selectedRoleId, groupId)
        await syncCountsFromDetail()
      } catch (error) {
        dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
      } finally {
        setActorMutationSubmitting(false)
      }
    },
    [selectedRoleId, dispatch, syncCountsFromDetail],
  )

  const handleAssignUsersToRole = useCallback(
    async (userIds: string[]) => {
      if (!selectedRoleId || userIds.length === 0) return
      setActorMutationSubmitting(true)
      try {
        await roleAdminApi.assignUsers(selectedRoleId, { userIds })
        dispatch(setAlert({ children: 'Users assigned to role', severity: 'success' }))
        setAssignUsersOpen(false)
        await syncCountsFromDetail()
      } catch (error) {
        dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
        throw error
      } finally {
        setActorMutationSubmitting(false)
      }
    },
    [selectedRoleId, dispatch, syncCountsFromDetail],
  )

  const handleAssignGroupsToRole = useCallback(
    async (groupIds: string[]) => {
      if (!selectedRoleId || groupIds.length === 0) return
      setActorMutationSubmitting(true)
      try {
        await roleAdminApi.assignGroups(selectedRoleId, { groupIds })
        dispatch(setAlert({ children: 'Groups assigned to role', severity: 'success' }))
        setAssignGroupsOpen(false)
        await syncCountsFromDetail()
      } catch (error) {
        dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
        throw error
      } finally {
        setActorMutationSubmitting(false)
      }
    },
    [selectedRoleId, dispatch, syncCountsFromDetail],
  )

  const handlePermissionMutation = useCallback(
    async (payload: PermissionGrantPayload) => {
      if (!selectedRoleId) return
      setPermissionSubmitting(true)
      try {
        if (permissionDrawer === 'create') {
          await roleAdminApi.grantPermission(selectedRoleId, payload)
          dispatch(setAlert({ children: 'Permission granted', severity: 'success' }))
        } else if (typeof permissionDrawer === 'object') {
          await roleAdminApi.updatePermission(
            selectedRoleId,
            permissionDrawer.permissionId,
            payload,
          )
          dispatch(setAlert({ children: 'Permission updated', severity: 'success' }))
        }
        setPermissionDrawer('closed')
        await syncCountsFromDetail()
      } catch (error) {
        dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
        throw error
      } finally {
        setPermissionSubmitting(false)
      }
    },
    [selectedRoleId, permissionDrawer, dispatch, syncCountsFromDetail],
  )

  const handleEditPermission = (permissionId: string) => {
    setPermissionDrawer({ mode: 'edit', permissionId })
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        overflow: 'hidden',
        bgcolor: 'background.default',
        position: 'relative',
      }}
    >
      {listError ? (
        <AdminErrorAlert
          message={listError}
          onRetry={() => void fetchRoles()}
          sx={{ borderRadius: 0 }}
        />
      ) : null}

      {detailError && selectedRoleId ? (
        <AdminErrorAlert
          message={detailError}
          onRetry={() => {
            if (selectedRoleId) void refetchDetail(selectedRoleId)
          }}
          sx={{ borderRadius: 0 }}
        />
      ) : null}

      <RoleManagementWorkspace
        roleList={
          <RoleListPanel
            roles={filteredRoles}
            selectedRoleId={selectedRoleId}
            searchQuery={roleSearchQuery}
            loading={rolesLoading}
            onSearchChange={setRoleSearchQuery}
            onSelectRole={handleSelectRole}
            onAddRole={() => setAddRoleOpen(true)}
            onRenameRole={(roleId) => setRenameRoleId(roleId)}
            canDeleteRoles={roles.length >= 1}
            onDeleteRole={handleRequestDeleteRole}
          />
        }
        permissions={
          <PermissionsPanel
            role={selectedRole}
            resourceGroups={resourceGroups}
            summary={displaySummary}
            loading={permissionsLoading}
            expandedGroups={expandedGroups}
            onToggleGroup={handleToggleGroup}
            onAddPermission={() => setPermissionDrawer('create')}
            onEditPermission={handleEditPermission}
            onDeletePermission={setDeletePermissionId}
          />
        }
        actors={
          <ActorsPanel
            role={selectedRole}
            users={actors.users}
            groups={actors.groups}
            totalAffectedUsers={actors.totalAffectedUsers}
            loading={actorsLoading || actorMutationSubmitting}
            showAllUsers={showAllUsers}
            onAssignUsers={() => setAssignUsersOpen(true)}
            onAssignGroups={() => setAssignGroupsOpen(true)}
            onUnassignUser={(id) => void handleUnassignUser(id)}
            onUnassignGroup={(id) => void handleUnassignGroup(id)}
            onShowMoreUsers={() => setShowAllUsers(true)}
          />
        }
      />

      <RenameRoleDialog
        open={Boolean(renameRoleId)}
        initialName={roles.find((r) => r.id === renameRoleId)?.name ?? ''}
        submitting={renameSubmitting}
        onClose={() => setRenameRoleId(null)}
        onSubmit={handleRenameRole}
      />

      <AddRoleDrawer
        open={addRoleOpen}
        onClose={() => setAddRoleOpen(false)}
        onAdd={handleAddRole}
        submitting={addRoleSubmitting}
      />

      <AddPermissionDrawer
        open={permissionDrawerOpen}
        mode={permissionDrawerMode}
        contextLabel={selectedRole?.name ?? 'Role'}
        contextIcon="shield"
        resourceTree={resourceTree ?? MOCK_RESOURCES}
        initialFormState={permissionDrawerMode === 'edit' ? editFormInitialState : null}
        submitDisabled={permissionSubmitting}
        onClose={() => setPermissionDrawer('closed')}
        onSubmit={(payload) => void handlePermissionMutation(payload)}
      />

      <AssignUsersToRoleDrawer
        open={assignUsersOpen}
        role={selectedRole}
        assignedUsers={actors.users}
        submitting={actorMutationSubmitting}
        onClose={() => setAssignUsersOpen(false)}
        onAssign={handleAssignUsersToRole}
      />

      <AssignGroupsToRoleDrawer
        open={assignGroupsOpen}
        role={selectedRole}
        assignedGroups={actors.groups}
        submitting={actorMutationSubmitting}
        onClose={() => setAssignGroupsOpen(false)}
        onAssign={handleAssignGroupsToRole}
      />

      <ConfirmDeletePermissionModal
        open={Boolean(deletePermissionId)}
        permissionPath={deletePermissionPath}
        submitting={deletePermissionSubmitting}
        onClose={() => setDeletePermissionId(null)}
        onConfirm={handleConfirmDeletePermission}
      />

      <ConfirmDeleteRoleModal
        open={Boolean(deleteRoleId)}
        roleName={roles.find((r) => r.id === deleteRoleId)?.name ?? ''}
        errorMessage={deleteRoleError}
        submitting={deleteRoleSubmitting}
        onClose={handleCloseDeleteRoleModal}
        onConfirm={handleConfirmDeleteRole}
      />
    </Box>
  )
}

export default RoleManagementPage
