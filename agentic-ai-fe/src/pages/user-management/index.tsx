import { useCallback, useEffect, useState } from 'react'
import { Box } from '@mui/material'

import { USE_ADMIN_MOCK, getAdminErrorMessage, roleAdminApi, userAdminApi } from '@/api/admin'
import AdminErrorAlert from '@/components/admin/AdminErrorAlert'
import { useAppDispatch } from '@/redux/hooks'
import { setAlert } from '@/redux/reducers/AlertSlice'

import TopAppBar from './components/TopAppBar'
import Toolbar from './components/Toolbar'
import UserTable from './components/UserTable'
import type { User } from './components/UserTable'
import BulkActionBar from './components/BulkActionBar'
import UserDetailDrawer from './components/UserDetailDrawer'
import AddUserDrawer from './components/AddUserDrawer'
import type { UserFormData } from './components/AddUserDrawer'
import AddGroupDrawer from './components/AddGroupDrawer'
import AddRoleDrawer from './components/AddRoleDrawer'
import ConfirmDeactivateModal from './components/ConfirmDeactivateModal'

const SEARCH_DEBOUNCE_MS = 400

const UserManagementPage = () => {
  const dispatch = useAppDispatch()

  const [users, setUsers] = useState<User[]>([])
  const [usersLoading, setUsersLoading] = useState(true)
  const [listError, setListError] = useState<string | null>(null)
  const [totalItems, setTotalItems] = useState(0)
  const [groupOptions, setGroupOptions] = useState<string[]>([])
  const [roleOptions, setRoleOptions] = useState<string[]>([])
  const [optionsLoading, setOptionsLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [detailLoading, setDetailLoading] = useState(false)

  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [addUserOpen, setAddUserOpen] = useState(false)
  const [isBulkGroupOpen, setIsBulkGroupOpen] = useState(false)
  const [isBulkRoleOpen, setIsBulkRoleOpen] = useState(false)
  const [isDetailRoleOpen, setIsDetailRoleOpen] = useState(false)
  const [isBulkDeactivateOpen, setIsBulkDeactivateOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [bulkSubmitting, setBulkSubmitting] = useState(false)
  const [detailRoleSubmitting, setDetailRoleSubmitting] = useState(false)
  const [addUserSubmitting, setAddUserSubmitting] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchQuery), SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [searchQuery])

  const fetchUsers = useCallback(
    async (params?: { search?: string }) => {
      setUsersLoading(true)
      setListError(null)
      try {
        const result = await userAdminApi.list({
          page: 1,
          pageSize: 50,
          search: params?.search?.trim() || undefined,
        })
        setUsers(result.items)
        setSelectedIds((prev) => prev.filter((id) => result.items.some((u) => u.id === id)))
      } catch (error) {
        const message = getAdminErrorMessage(error)
        setListError(message)
        dispatch(setAlert({ children: message, severity: 'error' }))
      } finally {
        setUsersLoading(false)
      }
    },
    [dispatch],
  )

  useEffect(() => {
    if (USE_ADMIN_MOCK) {
      let cancelled = false
      setUsersLoading(true)
      setListError(null)
      void import('./mock-data.dev').then((mock) => {
        if (cancelled) return
        setUsers(mock.mockUsers)
        setTotalItems(mock.mockUsers.length)
        setUsersLoading(false)
      })
      return () => {
        cancelled = true
      }
    }
    void fetchUsers({ search: debouncedSearch })
  }, [fetchUsers, debouncedSearch])

  useEffect(() => {
    if (!addUserOpen && !isBulkGroupOpen && !isBulkRoleOpen && !isDetailRoleOpen) return

    let cancelled = false
    setOptionsLoading(true)

    Promise.all([userAdminApi.getGroupOptions(), userAdminApi.getRoleOptions()])
      .then(([groupsRes, rolesRes]) => {
        if (cancelled) return
        setGroupOptions(groupsRes.groups ?? [])
        setRoleOptions(rolesRes.roles ?? [])
      })
      .catch((error) => {
        if (cancelled) return
        dispatch(
          setAlert({ children: getAdminErrorMessage(error), severity: 'error' }),
        )
      })
      .finally(() => {
        if (!cancelled) setOptionsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [addUserOpen, isBulkGroupOpen, isBulkRoleOpen, isDetailRoleOpen, dispatch])

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelectedIds(users.map((u) => u.id))
    } else {
      setSelectedIds([])
    }
  }

  const handleSelectOne = (id: string) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]))
  }

  const handleRowClick = async (user: User) => {
    setSelectedUser(user)
    setDrawerOpen(true)
    setDetailLoading(true)

    try {
      const detail = await userAdminApi.getById(user.id)
      setSelectedUser(detail)
    } catch (error) {
      dispatch(
        setAlert({ children: getAdminErrorMessage(error), severity: 'error' }),
      )
    } finally {
      setDetailLoading(false)
    }
  }

  const handleAddUser = useCallback(
    async (data: UserFormData) => {
      setAddUserSubmitting(true)
      try {
        await userAdminApi.create({
          fullName: data.fullName,
          email: data.email,
          username: data.username,
          groups: data.groups,
          roles: data.roles,
          isActive: data.isActive,
        })
        dispatch(
          setAlert({ children: 'User created successfully', severity: 'success' }),
        )
        setAddUserOpen(false)
        await fetchUsers({ search: debouncedSearch })
      } catch (error) {
        dispatch(
          setAlert({ children: getAdminErrorMessage(error), severity: 'error' }),
        )
        throw error
      } finally {
        setAddUserSubmitting(false)
      }
    },
    [dispatch, fetchUsers, debouncedSearch],
  )

  const handleBulkGroupAssign = useCallback(
    async (groupNames: string[]) => {
      if (selectedIds.length === 0 || groupNames.length === 0) return

      setBulkSubmitting(true)
      try {
        await userAdminApi.bulkAssignGroups({
          userIds: selectedIds,
          groupNames,
        })
        dispatch(
          setAlert({ children: 'Groups assigned successfully', severity: 'success' }),
        )
        setIsBulkGroupOpen(false)
        setSelectedIds([])
        await fetchUsers({ search: debouncedSearch })
      } catch (error) {
        dispatch(
          setAlert({ children: getAdminErrorMessage(error), severity: 'error' }),
        )
        throw error
      } finally {
        setBulkSubmitting(false)
      }
    },
    [selectedIds, dispatch, fetchUsers, debouncedSearch],
  )

  const handleBulkRoleAssign = useCallback(
    async (roleNames: string[]) => {
      if (selectedIds.length === 0 || roleNames.length === 0) return

      setBulkSubmitting(true)
      try {
        await userAdminApi.bulkAssignRoles({
          userIds: selectedIds,
          roleNames,
        })
        dispatch(
          setAlert({ children: 'Roles assigned successfully', severity: 'success' }),
        )
        setIsBulkRoleOpen(false)
        setSelectedIds([])
        await fetchUsers({ search: debouncedSearch })
      } catch (error) {
        dispatch(
          setAlert({ children: getAdminErrorMessage(error), severity: 'error' }),
        )
        throw error
      } finally {
        setBulkSubmitting(false)
      }
    },
    [selectedIds, dispatch, fetchUsers, debouncedSearch],
  )

  const refreshUserDetail = useCallback(
    async (userId: string) => {
      setDetailLoading(true)
      try {
        const detail = await userAdminApi.getById(userId)
        setSelectedUser(detail)
      } catch (error) {
        dispatch(
          setAlert({ children: getAdminErrorMessage(error), severity: 'error' }),
        )
      } finally {
        setDetailLoading(false)
      }
    },
    [dispatch],
  )

  const handleDetailRoleAssign = useCallback(
    async (roleNames: string[]) => {
      if (!selectedUser || roleNames.length === 0) return

      setDetailRoleSubmitting(true)
      try {
        await userAdminApi.bulkAssignRoles({
          userIds: [selectedUser.id],
          roleNames,
        })
        dispatch(
          setAlert({ children: 'Roles assigned successfully', severity: 'success' }),
        )
        setIsDetailRoleOpen(false)
        await refreshUserDetail(selectedUser.id)
        await fetchUsers({ search: debouncedSearch })
      } catch (error) {
        dispatch(
          setAlert({ children: getAdminErrorMessage(error), severity: 'error' }),
        )
        throw error
      } finally {
        setDetailRoleSubmitting(false)
      }
    },
    [selectedUser, dispatch, refreshUserDetail, fetchUsers, debouncedSearch],
  )

  const handleRemoveRoleFromUser = useCallback(
    async (roleName: string) => {
      if (!selectedUser) return

      const roleRef = selectedUser.roleRefs?.find((ref) => ref.name === roleName)
      if (!roleRef?.id) {
        dispatch(
          setAlert({
            children:
              'Cannot remove role: role ID not found. Close the drawer and open the user again.',
            severity: 'error',
          }),
        )
        return
      }

      setDetailRoleSubmitting(true)
      try {
        await roleAdminApi.unassignUser(roleRef.id, selectedUser.id)
        dispatch(
          setAlert({ children: 'Role removed successfully', severity: 'success' }),
        )
        await refreshUserDetail(selectedUser.id)
        await fetchUsers({ search: debouncedSearch })
      } catch (error) {
        dispatch(
          setAlert({ children: getAdminErrorMessage(error), severity: 'error' }),
        )
      } finally {
        setDetailRoleSubmitting(false)
      }
    },
    [selectedUser, dispatch, refreshUserDetail, fetchUsers, debouncedSearch],
  )

  const handleBulkDeactivate = useCallback(async () => {
    if (selectedIds.length === 0) return

    setBulkSubmitting(true)
    try {
      await userAdminApi.bulkDeactivate({ userIds: selectedIds })
      dispatch(
        setAlert({ children: 'Users deactivated successfully', severity: 'success' }),
      )
      setIsBulkDeactivateOpen(false)
      setSelectedIds([])
      await fetchUsers({ search: debouncedSearch })
    } catch (error) {
      dispatch(
        setAlert({ children: getAdminErrorMessage(error), severity: 'error' }),
      )
      throw error
    } finally {
      setBulkSubmitting(false)
    }
  }, [selectedIds, dispatch, fetchUsers, debouncedSearch])

  const selectedUsers = users.filter((u) => selectedIds.includes(u.id))

  const bulkGroupItems = groupOptions.map((name) => ({
    id: name,
    name,
    members: 0,
    description: '',
  }))

  const bulkRoleItems = roleOptions.map((name) => ({
    id: name,
    name,
    description: '',
  }))

  const detailRoleItems = roleOptions
    .filter((name) => !selectedUser?.roles.includes(name))
    .map((name) => ({
      id: name,
      name,
      description: '',
    }))

  const detailSelectedUsers = selectedUser ? [selectedUser] : []

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
      <TopAppBar />

      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          p: 2,
          gap: 2,
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <Toolbar
          searchValue={searchQuery}
          onSearchChange={setSearchQuery}
          onAddClick={() => setAddUserOpen(true)}
        />

        {listError ? (
          <AdminErrorAlert
            message={listError}
            onRetry={() => void fetchUsers({ search: debouncedSearch })}
            sx={{ flexShrink: 0 }}
          />
        ) : null}

        <UserTable
          users={users}
          usersLoading={usersLoading}
          selectedIds={selectedIds}
          onSelectAll={handleSelectAll}
          onSelectOne={handleSelectOne}
          onRowClick={handleRowClick}
        />

        <BulkActionBar
          selectedCount={selectedIds.length}
          onClear={() => setSelectedIds([])}
          onBulkGroupClick={() => setIsBulkGroupOpen(true)}
          onBulkRoleClick={() => setIsBulkRoleOpen(true)}
          onBulkDeactivateClick={() => setIsBulkDeactivateOpen(true)}
        />
      </Box>

      <UserDetailDrawer
        user={selectedUser}
        open={drawerOpen}
        loading={detailLoading}
        roleMutationSubmitting={detailRoleSubmitting}
        onClose={() => setDrawerOpen(false)}
        onAddRole={() => setIsDetailRoleOpen(true)}
        onRemoveRole={(roleName) => void handleRemoveRoleFromUser(roleName)}
      />

      <AddUserDrawer
        open={addUserOpen}
        onClose={() => setAddUserOpen(false)}
        onAdd={handleAddUser}
        groupOptions={groupOptions}
        roleOptions={roleOptions}
        optionsLoading={optionsLoading}
        submitting={addUserSubmitting}
      />

      <AddGroupDrawer
        open={isBulkGroupOpen}
        onClose={() => setIsBulkGroupOpen(false)}
        selectedUsers={selectedUsers}
        groups={bulkGroupItems}
        optionsLoading={optionsLoading}
        submitting={bulkSubmitting}
        onAssign={handleBulkGroupAssign}
      />

      <AddRoleDrawer
        open={isBulkRoleOpen}
        onClose={() => setIsBulkRoleOpen(false)}
        selectedUsers={selectedUsers}
        roles={bulkRoleItems}
        optionsLoading={optionsLoading}
        submitting={bulkSubmitting}
        onAssign={handleBulkRoleAssign}
      />

      <AddRoleDrawer
        open={isDetailRoleOpen}
        onClose={() => setIsDetailRoleOpen(false)}
        selectedUsers={detailSelectedUsers}
        roles={detailRoleItems}
        optionsLoading={optionsLoading}
        submitting={detailRoleSubmitting}
        onAssign={handleDetailRoleAssign}
      />

      <ConfirmDeactivateModal
        open={isBulkDeactivateOpen}
        onClose={() => setIsBulkDeactivateOpen(false)}
        selectedCount={selectedIds.length}
        submitting={bulkSubmitting}
        onConfirm={handleBulkDeactivate}
      />
    </Box>
  )
}

export default UserManagementPage
