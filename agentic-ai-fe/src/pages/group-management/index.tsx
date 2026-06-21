import { useCallback, useEffect, useMemo, useState } from 'react'
import { Box } from '@mui/material'

import {
  AdminApiError,
  USE_ADMIN_MOCK,
  getAdminErrorMessage,
  groupAdminApi,
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
import ConfirmDeletePermissionModal from '@/pages/role-management/components/ConfirmDeletePermissionModal'
import { mapPermissionToFormState } from '@/pages/role-management/utils/permissionMappers'

import TopAppBar from './components/TopAppBar'
import GroupManagementWorkspace from './components/GroupManagementWorkspace'
import GroupListPanel from './components/GroupListPanel'
import GroupDetailPanel from './components/GroupDetailPanel'
import GroupPermissionsPanel from './components/GroupPermissionsPanel'
import AddGroupDrawer from './components/AddGroupDrawer'
import type { GroupFormData } from './components/AddGroupDrawer'
import AddMemberToGroupDrawer from './components/AddMemberToGroupDrawer'
import AssignRolesToGroupDrawer from './components/AssignRolesToGroupDrawer'
import ConfirmDeleteGroupModal from './components/ConfirmDeleteGroupModal'
import { useGroupDetail } from './hooks/useGroupDetail'
import type {
  EffectivePermission,
  GroupMember,
  GroupRoleAssignment,
  InheritedSummary,
  PermissionOwnership,
  ResourceType,
  UserGroup,
} from './types'
import {
  computeSummary,
  createDefaultExpandedGroups,
  filterGroups,
  groupEffectivePermissionsByResource,
  syncGroupCounts,
} from './utils'

type GroupPermissionDrawerState =
  | 'closed'
  | { mode: 'create' }
  | { mode: 'edit'; ownership: PermissionOwnership; permissionId: string; roleId?: string }

type DeletePermissionTarget = {
  ownership: PermissionOwnership
  permissionId: string
  roleId?: string
}

const emptyInheritedSummary = (): InheritedSummary => ({
  permissionCount: 0,
  resourceTypeCount: 0,
  roleCount: 0,
})

const GroupManagementPage = () => {
  const dispatch = useAppDispatch()

  const [groups, setGroups] = useState<UserGroup[]>([])
  const [groupsLoading, setGroupsLoading] = useState(true)
  const [listError, setListError] = useState<string | null>(null)
  const [membersByGroupId, setMembersByGroupId] = useState<Record<string, GroupMember[]>>({})
  const [rolesByGroupId, setRolesByGroupId] = useState<Record<string, GroupRoleAssignment[]>>({})

  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null)
  const [groupSearchQuery, setGroupSearchQuery] = useState('')
  const [expandedGroups, setExpandedGroups] = useState(createDefaultExpandedGroups)
  const [resourceTree, setResourceTree] = useState<ResourceNode[] | null>(null)

  const [addGroupOpen, setAddGroupOpen] = useState(false)
  const [addGroupSubmitting, setAddGroupSubmitting] = useState(false)
  const [addMemberOpen, setAddMemberOpen] = useState(false)
  const [assignRolesOpen, setAssignRolesOpen] = useState(false)
  const [deleteGroupOpen, setDeleteGroupOpen] = useState(false)
  const [deleteGroupSubmitting, setDeleteGroupSubmitting] = useState(false)
  const [memberMutationSubmitting, setMemberMutationSubmitting] = useState(false)
  const [roleMutationSubmitting, setRoleMutationSubmitting] = useState(false)

  const [permissionDrawer, setPermissionDrawer] = useState<GroupPermissionDrawerState>('closed')
  const [permissionSubmitting, setPermissionSubmitting] = useState(false)
  const [deletePermissionTarget, setDeletePermissionTarget] = useState<DeletePermissionTarget | null>(
    null,
  )
  const [deletePermissionSubmitting, setDeletePermissionSubmitting] = useState(false)

  const patchGroupCounts = useCallback((groupId: string, memberCount: number, roleCount: number) => {
    setGroups((prev) =>
      prev.map((group) =>
        group.id === groupId ? syncGroupCounts(group, memberCount, roleCount) : group,
      ),
    )
  }, [])

  const {
    effectivePermissions,
    permissionSummary,
    inheritedSummary,
    detailLoading,
    detailError,
    refetchGroupDetail,
  } = useGroupDetail(selectedGroupId, {
    setMembersByGroupId,
    setRolesByGroupId,
    patchGroupCounts,
  })

  const fetchGroups = useCallback(async () => {
    setGroupsLoading(true)
    setListError(null)
    try {
      const { items } = await groupAdminApi.list({ page: 1, pageSize: 100 })
      setGroups(items)
      setSelectedGroupId((prev) => {
        if (prev && items.some((g) => g.id === prev)) return prev
        return items[0]?.id ?? null
      })
    } catch (error) {
      const message = getAdminErrorMessage(error)
      setListError(message)
      dispatch(setAlert({ children: message, severity: 'error' }))
    } finally {
      setGroupsLoading(false)
    }
  }, [dispatch])

  useEffect(() => {
    if (USE_ADMIN_MOCK) {
      let cancelled = false
      setGroupsLoading(true)
      setListError(null)
      void import('./mock-data.dev').then((mock) => {
        if (cancelled) return
        setGroups(mock.initialGroups)
        setSelectedGroupId((prev) => {
          if (prev && mock.initialGroups.some((g) => g.id === prev)) return prev
          return mock.INITIAL_GROUP_ID
        })
        setGroupsLoading(false)
      })
      return () => {
        cancelled = true
      }
    }
    void fetchGroups()
  }, [fetchGroups])

  useEffect(() => {
    const controller = new AbortController()
    resourceAdminApi
      .getTree({ signal: controller.signal })
      .then(setResourceTree)
      .catch(() => setResourceTree(null))
    return () => controller.abort()
  }, [])

  const filteredGroupList = useMemo(
    () => filterGroups(groups, groupSearchQuery),
    [groups, groupSearchQuery],
  )

  const selectedGroup = useMemo(
    () => groups.find((g) => g.id === selectedGroupId) ?? null,
    [groups, selectedGroupId],
  )

  const currentMembers = useMemo(
    () => (selectedGroupId ? (membersByGroupId[selectedGroupId] ?? []) : []),
    [membersByGroupId, selectedGroupId],
  )

  const currentRoles = useMemo(
    () => (selectedGroupId ? (rolesByGroupId[selectedGroupId] ?? []) : []),
    [rolesByGroupId, selectedGroupId],
  )

  const resourceGroups = useMemo(
    () => groupEffectivePermissionsByResource(effectivePermissions),
    [effectivePermissions],
  )

  const displaySummary = permissionSummary ?? computeSummary(effectivePermissions)

  const displayInheritedSummary = useMemo(
    () => inheritedSummary ?? emptyInheritedSummary(),
    [inheritedSummary],
  )

  const editingPermission = useMemo(() => {
    if (permissionDrawer === 'closed' || permissionDrawer.mode === 'create') return null
    return effectivePermissions.find((p) => p.id === permissionDrawer.permissionId) ?? null
  }, [permissionDrawer, effectivePermissions])

  const editFormInitialState = useMemo(
    () => (editingPermission ? mapPermissionToFormState(editingPermission) : null),
    [editingPermission],
  )

  const permissionDrawerOpen = permissionDrawer !== 'closed'
  const permissionDrawerMode = permissionDrawer === 'closed' ? 'create' : permissionDrawer.mode

  const permissionContextLabel = selectedGroup?.name ?? 'Group'

  const deletePermissionPath = useMemo(() => {
    if (!deletePermissionTarget) return ''
    const perm = effectivePermissions.find((p) => p.id === deletePermissionTarget.permissionId)
    return perm ? perm.path.map((s) => s.label).join(' / ') : ''
  }, [deletePermissionTarget, effectivePermissions])

  const resetPermissionUi = () => {
    setPermissionDrawer('closed')
    setDeletePermissionTarget(null)
  }

  const handleSelectGroup = (groupId: string) => {
    setSelectedGroupId(groupId)
    setExpandedGroups(createDefaultExpandedGroups())
    resetPermissionUi()
  }

  const handleAddGroup = useCallback(
    async (data: GroupFormData) => {
      setAddGroupSubmitting(true)
      try {
        const created = await groupAdminApi.create({
          name: data.name,
          description: data.description,
        })
        dispatch(setAlert({ children: 'Group created successfully', severity: 'success' }))
        setAddGroupOpen(false)
        await fetchGroups()
        setSelectedGroupId(created.id)
        await refetchGroupDetail(created.id)
      } catch (error) {
        dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
        throw error
      } finally {
        setAddGroupSubmitting(false)
      }
    },
    [dispatch, fetchGroups, refetchGroupDetail],
  )

  const handleDeleteGroup = useCallback(async () => {
    if (!selectedGroupId) return
    setDeleteGroupSubmitting(true)
    try {
      const deletingId = selectedGroupId
      await groupAdminApi.delete(deletingId)
      dispatch(setAlert({ children: 'Group deleted', severity: 'success' }))
      setDeleteGroupOpen(false)
      setMembersByGroupId((prev) => {
        const next = { ...prev }
        delete next[deletingId]
        return next
      })
      setRolesByGroupId((prev) => {
        const next = { ...prev }
        delete next[deletingId]
        return next
      })
      resetPermissionUi()
      await fetchGroups()
    } catch (error) {
      dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
      throw error
    } finally {
      setDeleteGroupSubmitting(false)
    }
  }, [selectedGroupId, dispatch, fetchGroups])

  const handleAddMembers = useCallback(
    async (memberIds: string[]) => {
      if (!selectedGroupId || memberIds.length === 0) return
      setMemberMutationSubmitting(true)
      try {
        await groupAdminApi.addMembers(selectedGroupId, { memberIds })
        dispatch(setAlert({ children: 'Members added to group', severity: 'success' }))
        setAddMemberOpen(false)
        await refetchGroupDetail(selectedGroupId)
      } catch (error) {
        dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
        throw error
      } finally {
        setMemberMutationSubmitting(false)
      }
    },
    [selectedGroupId, dispatch, refetchGroupDetail],
  )

  const handleRemoveMember = useCallback(
    async (memberId: string) => {
      if (!selectedGroupId) return
      setMemberMutationSubmitting(true)
      try {
        await groupAdminApi.removeMember(selectedGroupId, memberId)
        await refetchGroupDetail(selectedGroupId)
      } catch (error) {
        dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
      } finally {
        setMemberMutationSubmitting(false)
      }
    },
    [selectedGroupId, dispatch, refetchGroupDetail],
  )

  const handleAssignRoles = useCallback(
    async (roleIds: string[]) => {
      if (!selectedGroupId || roleIds.length === 0) return
      setRoleMutationSubmitting(true)
      try {
        await groupAdminApi.assignRoles(selectedGroupId, { roleIds })
        dispatch(setAlert({ children: 'Roles assigned to group', severity: 'success' }))
        setAssignRolesOpen(false)
        await refetchGroupDetail(selectedGroupId)
      } catch (error) {
        dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
        throw error
      } finally {
        setRoleMutationSubmitting(false)
      }
    },
    [selectedGroupId, dispatch, refetchGroupDetail],
  )

  const handleRemoveRole = useCallback(
    async (roleId: string) => {
      if (!selectedGroupId) return
      setRoleMutationSubmitting(true)
      try {
        await groupAdminApi.unassignRole(selectedGroupId, roleId)
        if (
          permissionDrawer !== 'closed' &&
          permissionDrawer.mode === 'edit' &&
          permissionDrawer.ownership === 'role' &&
          permissionDrawer.roleId === roleId
        ) {
          setPermissionDrawer('closed')
        }
        if (
          deletePermissionTarget?.ownership === 'role' &&
          deletePermissionTarget.roleId === roleId
        ) {
          setDeletePermissionTarget(null)
        }
        await refetchGroupDetail(selectedGroupId)
      } catch (error) {
        dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
      } finally {
        setRoleMutationSubmitting(false)
      }
    },
    [selectedGroupId, dispatch, refetchGroupDetail, permissionDrawer, deletePermissionTarget],
  )

  const handleTogglePermissionGroup = (type: ResourceType) => {
    setExpandedGroups((prev) => ({ ...prev, [type]: !prev[type] }))
  }

  const handleOpenAddPermission = () => {
    if (!selectedGroupId) return
    setPermissionDrawer({ mode: 'create' })
  }

  const handleEditPermission = (permission: EffectivePermission) => {
    if (permission.ownership === 'group') {
      setPermissionDrawer({
        mode: 'edit',
        ownership: 'group',
        permissionId: permission.id,
      })
      return
    }
    if (!permission.sourceRoleId) return
    setPermissionDrawer({
      mode: 'edit',
      ownership: 'role',
      permissionId: permission.id,
      roleId: permission.sourceRoleId,
    })
  }

  const handlePermissionMutation = useCallback(
    async (payload: PermissionGrantPayload) => {
      if (!selectedGroupId || permissionDrawer === 'closed') return
      setPermissionSubmitting(true)
      try {
        if (permissionDrawer.mode === 'create') {
          await groupAdminApi.grantPermission(selectedGroupId, payload)
          dispatch(setAlert({ children: 'Permission granted', severity: 'success' }))
        } else if (permissionDrawer.ownership === 'group') {
          await groupAdminApi.updatePermission(
            selectedGroupId,
            permissionDrawer.permissionId,
            payload,
          )
          dispatch(setAlert({ children: 'Permission updated', severity: 'success' }))
        } else {
          const roleId = permissionDrawer.roleId
          if (!roleId) return
          await roleAdminApi.updatePermission(roleId, permissionDrawer.permissionId, payload)
          dispatch(setAlert({ children: 'Permission updated', severity: 'success' }))
        }
        setPermissionDrawer('closed')
        await refetchGroupDetail(selectedGroupId)
      } catch (error) {
        if (error instanceof AdminApiError && error.code === 'PERMISSION_NOT_DIRECT') {
          dispatch(
            setAlert({
              children: 'Cannot modify inherited permission on group endpoint.',
              severity: 'error',
            }),
          )
        } else {
          dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
        }
        throw error
      } finally {
        setPermissionSubmitting(false)
      }
    },
    [selectedGroupId, permissionDrawer, dispatch, refetchGroupDetail],
  )

  const handleDeletePermission = (permission: EffectivePermission) => {
    if (permission.ownership === 'group') {
      setDeletePermissionTarget({
        ownership: 'group',
        permissionId: permission.id,
      })
      return
    }
    if (!permission.sourceRoleId) return
    setDeletePermissionTarget({
      ownership: 'role',
      permissionId: permission.id,
      roleId: permission.sourceRoleId,
    })
  }

  const handleConfirmDeletePermission = useCallback(async () => {
    if (!deletePermissionTarget || !selectedGroupId) return
    const { ownership, permissionId } = deletePermissionTarget
    setDeletePermissionSubmitting(true)
    try {
      if (ownership === 'group') {
        await groupAdminApi.deletePermission(selectedGroupId, permissionId)
      } else {
        const roleId = deletePermissionTarget.roleId
        if (!roleId) return
        await roleAdminApi.deletePermission(roleId, permissionId)
      }
      dispatch(setAlert({ children: 'Permission removed', severity: 'success' }))
      setDeletePermissionTarget(null)
      await refetchGroupDetail(selectedGroupId)
    } catch (error) {
      if (error instanceof AdminApiError && error.code === 'PERMISSION_NOT_DIRECT') {
        dispatch(
          setAlert({
            children: 'Cannot modify inherited permission on group endpoint.',
            severity: 'error',
          }),
        )
      } else {
        dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
      }
      throw error
    } finally {
      setDeletePermissionSubmitting(false)
    }
  }, [deletePermissionTarget, selectedGroupId, dispatch, refetchGroupDetail])

  const detailBusy = detailLoading || memberMutationSubmitting || roleMutationSubmitting

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
          onRetry={() => void fetchGroups()}
          sx={{ borderRadius: 0 }}
        />
      ) : null}

      {detailError && selectedGroupId ? (
        <AdminErrorAlert
          message={detailError}
          onRetry={() => {
            if (selectedGroupId) void refetchGroupDetail(selectedGroupId)
          }}
          sx={{ borderRadius: 0 }}
        />
      ) : null}

      <TopAppBar />
      <GroupManagementWorkspace
        groupList={
          <GroupListPanel
            groups={filteredGroupList}
            selectedGroupId={selectedGroupId}
            searchQuery={groupSearchQuery}
            loading={groupsLoading}
            onSearchChange={setGroupSearchQuery}
            onSelectGroup={handleSelectGroup}
            onAddGroup={() => setAddGroupOpen(true)}
          />
        }
        groupDetail={
          <GroupDetailPanel
            group={selectedGroup}
            members={currentMembers}
            roles={currentRoles}
            inheritedSummary={displayInheritedSummary}
            detailLoading={detailBusy}
            onDeleteGroup={() => setDeleteGroupOpen(true)}
            onAddMember={() => setAddMemberOpen(true)}
            onRemoveMember={(id) => void handleRemoveMember(id)}
            onAssignRoles={() => setAssignRolesOpen(true)}
            onRemoveRole={(id) => void handleRemoveRole(id)}
          />
        }
        permissions={
          <GroupPermissionsPanel
            group={selectedGroup}
            roleCount={currentRoles.length}
            resourceGroups={resourceGroups}
            summary={displaySummary}
            loading={detailLoading}
            expandedGroups={expandedGroups}
            onToggleGroup={handleTogglePermissionGroup}
            onAddPermission={handleOpenAddPermission}
            onEditPermission={handleEditPermission}
            onDeletePermission={handleDeletePermission}
          />
        }
      />

      <AddGroupDrawer
        open={addGroupOpen}
        onClose={() => setAddGroupOpen(false)}
        onAdd={handleAddGroup}
        submitting={addGroupSubmitting}
      />
      <AddMemberToGroupDrawer
        open={addMemberOpen}
        group={selectedGroup}
        currentMembers={currentMembers}
        submitting={memberMutationSubmitting}
        onClose={() => setAddMemberOpen(false)}
        onAdd={handleAddMembers}
      />
      <AssignRolesToGroupDrawer
        open={assignRolesOpen}
        group={selectedGroup}
        assignedRoles={currentRoles}
        submitting={roleMutationSubmitting}
        onClose={() => setAssignRolesOpen(false)}
        onAssign={handleAssignRoles}
      />
      <ConfirmDeleteGroupModal
        open={deleteGroupOpen}
        groupName={selectedGroup?.name ?? ''}
        submitting={deleteGroupSubmitting}
        onClose={() => setDeleteGroupOpen(false)}
        onConfirm={handleDeleteGroup}
      />

      <AddPermissionDrawer
        open={permissionDrawerOpen}
        mode={permissionDrawerMode}
        contextLabel={permissionContextLabel}
        contextIcon="groups"
        resourceTree={resourceTree ?? MOCK_RESOURCES}
        initialFormState={permissionDrawerMode === 'edit' ? editFormInitialState : null}
        submitDisabled={permissionSubmitting}
        onClose={() => setPermissionDrawer('closed')}
        onSubmit={(payload) => void handlePermissionMutation(payload)}
      />

      <ConfirmDeletePermissionModal
        open={Boolean(deletePermissionTarget)}
        permissionPath={deletePermissionPath}
        submitting={deletePermissionSubmitting}
        onClose={() => setDeletePermissionTarget(null)}
        onConfirm={handleConfirmDeletePermission}
      />
    </Box>
  )
}

export default GroupManagementPage
