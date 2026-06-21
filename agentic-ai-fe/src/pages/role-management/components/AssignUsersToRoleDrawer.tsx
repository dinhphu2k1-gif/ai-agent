import {
  Drawer,
  Box,
  Typography,
  IconButton,
  Button,
  TextField,
  InputAdornment,
  Stack,
  Checkbox,
  Avatar,
  Skeleton,
  styled,
} from '@mui/material'
import { useEffect, useMemo, useState } from 'react'

import { getAdminErrorMessage, isAbortError, roleAdminApi } from '@/api/admin'
import { useAppDispatch } from '@/redux/hooks'
import { setAlert } from '@/redux/reducers/AlertSlice'

import type { ActorUser, AssignableUser, Role } from '../types'

const CATALOG_DEBOUNCE_MS = 400

interface AssignUsersToRoleDrawerProps {
  open: boolean
  role: Role | null
  assignedUsers: ActorUser[]
  submitting?: boolean
  onClose: () => void
  onAssign: (userIds: string[]) => void | Promise<void>
}

const UserItem = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'selected',
})<{ selected?: boolean }>(({ theme, selected }) => ({
  display: 'flex',
  alignItems: 'flex-start',
  gap: theme.spacing(1),
  padding: theme.spacing(1),
  backgroundColor: 'var(--mui-palette-surface)',
  borderRadius: theme.shape.borderRadius,
  border: '1px solid',
  borderColor: selected ? 'var(--mui-palette-primary-main)' : 'var(--mui-palette-outlineVariant)',
  cursor: 'pointer',
  transition: 'background-color 0.15s ease, border-color 0.15s ease',
  position: 'relative',
  overflow: 'hidden',
  '&:hover': {
    backgroundColor: 'var(--mui-palette-surfaceContainerHighest)',
  },
  ...(selected && {
    '&::before': {
      content: '""',
      position: 'absolute',
      left: 0,
      top: 0,
      bottom: 0,
      width: 2,
      backgroundColor: 'var(--mui-palette-primary-main)',
    },
  }),
}))

const getInitials = (name: string) =>
  name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

interface UserSelectRowProps {
  user: AssignableUser
  selected: boolean
  onToggle: (id: string) => void
}

const UserSelectRow = ({ user, selected, onToggle }: UserSelectRowProps) => (
  <UserItem component="label" selected={selected} onClick={() => onToggle(user.id)}>
    <Checkbox
      checked={selected}
      size="small"
      sx={{
        p: 0,
        mt: 0.75,
        color: 'outline',
        '&.Mui-checked': { color: 'primaryContainer' },
      }}
      onClick={(e) => e.stopPropagation()}
      onChange={() => onToggle(user.id)}
    />
    <Box sx={{ position: 'relative', flexShrink: 0, mt: 0.25 }}>
      <Avatar
        src={user.avatarUrl}
        sx={{
          width: 36,
          height: 36,
          fontSize: 12,
          border: 1,
          borderColor: 'outlineVariant',
        }}
      >
        {getInitials(user.name)}
      </Avatar>
      {user.isOnline && (
        <Box
          sx={{
            position: 'absolute',
            bottom: 0,
            right: 0,
            width: 10,
            height: 10,
            borderRadius: '50%',
            bgcolor: 'success.main',
            border: 2,
            borderColor: 'surface',
          }}
        />
      )}
    </Box>
    <Box sx={{ flex: 1, minWidth: 0 }}>
      <Typography variant="headlineAgent" sx={{ color: 'onSurface', fontSize: 14 }} noWrap>
        {user.name}
      </Typography>
      <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant' }} noWrap>
        {user.email}
      </Typography>
    </Box>
  </UserItem>
)

const AssignUsersToRoleDrawer = ({
  open,
  role,
  assignedUsers,
  submitting = false,
  onClose,
  onAssign,
}: AssignUsersToRoleDrawerProps) => {
  const dispatch = useAppDispatch()
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [catalog, setCatalog] = useState<AssignableUser[]>([])
  const [catalogLoading, setCatalogLoading] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchQuery), CATALOG_DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [searchQuery])

  useEffect(() => {
    if (!open) return

    const controller = new AbortController()
    setCatalogLoading(true)

    roleAdminApi
      .listUsersCatalog(
        { page: 1, pageSize: 50, search: debouncedSearch.trim() || undefined },
        { signal: controller.signal },
      )
      .then((result) => {
        if (!controller.signal.aborted) setCatalog(result.items)
      })
      .catch((error) => {
        if (isAbortError(error)) return
        dispatch(setAlert({ children: getAdminErrorMessage(error), severity: 'error' }))
      })
      .finally(() => {
        if (!controller.signal.aborted) setCatalogLoading(false)
      })

    return () => controller.abort()
  }, [open, debouncedSearch, dispatch])

  const assignedIds = useMemo(() => new Set(assignedUsers.map((u) => u.id)), [assignedUsers])

  const availableUsers = useMemo(
    () => catalog.filter((u) => !assignedIds.has(u.id)),
    [catalog, assignedIds],
  )

  const handleToggleUser = (id: string) => {
    setSelectedUserIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id],
    )
  }

  const handleClose = () => {
    setSelectedUserIds([])
    setSearchQuery('')
    onClose()
  }

  const handleAssign = async () => {
    if (selectedUserIds.length === 0) return
    try {
      await onAssign(selectedUserIds)
      handleClose()
    } catch {
      // Parent shows toast; keep drawer open
    }
  }

  const roleIcon = role?.icon === 'shield_lock' ? 'shield_lock' : 'shield'

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={handleClose}
      slotProps={{
        paper: {
          sx: {
            width: { xs: '100%', sm: 450 },
            maxWidth: '100%',
            bgcolor: 'surfaceContainerLow',
            display: 'flex',
            flexDirection: 'column',
            backgroundImage: 'none',
          },
        },
      }}
    >
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: 1,
          borderColor: 'outlineVariant',
          bgcolor: 'surface',
          flexShrink: 0,
        }}
      >
        <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
          Bulk Assign Users
        </Typography>
        <IconButton onClick={handleClose} size="small" aria-label="Close drawer">
          <span className="material-symbols-outlined">close</span>
        </IconButton>
      </Box>

      <Box sx={{ flex: 1, overflowY: 'auto', p: 2, minHeight: 0 }}>
        {!role ? (
          <Typography variant="bodyMain" sx={{ color: 'onSurfaceVariant' }}>
            Select a role to assign users
          </Typography>
        ) : (
          <Stack spacing={3}>
            <Box>
              <Typography
                variant="labelMono"
                sx={{
                  color: 'onSurfaceVariant',
                  mb: 0.5,
                  display: 'block',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                }}
              >
                Assigning to role
              </Typography>
              <Box
                sx={{
                  p: 1.5,
                  bgcolor: 'surface',
                  borderRadius: 1,
                  border: 1,
                  borderColor: 'outlineVariant',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 1.5,
                }}
              >
                <Box
                  sx={{
                    mt: 0.25,
                    p: 0.75,
                    borderRadius: '50%',
                    bgcolor: 'roleViewerBg',
                    color: 'roleViewerText',
                    border: 1,
                    borderColor: 'roleViewerBorder',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                    {roleIcon}
                  </span>
                </Box>
                <Box sx={{ minWidth: 0, display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                  <Typography variant="headlineAgent" sx={{ color: 'onSurface' }} noWrap>
                    {role.name}
                  </Typography>
                  <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant', mt: 0.5 }}>
                    Add one or more users to this role.
                  </Typography>
                </Box>
              </Box>
            </Box>

            <Box>
              <Typography
                variant="labelMono"
                sx={{
                  color: 'onSurfaceVariant',
                  mb: 0.5,
                  display: 'block',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                }}
              >
                Available Users
              </Typography>
              <TextField
                fullWidth
                size="small"
                placeholder="Search users..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                sx={{ mb: 2 }}
                slotProps={{
                  input: {
                    sx: { fontSize: 13 },
                    startAdornment: (
                      <InputAdornment position="start">
                        <span
                          className="material-symbols-outlined"
                          style={{
                            fontSize: 18,
                            color: 'var(--mui-palette-onSurfaceVariant)',
                          }}
                        >
                          search
                        </span>
                      </InputAdornment>
                    ),
                  },
                }}
              />

              <Stack spacing={1}>
                {catalogLoading ? (
                  [1, 2, 3, 4].map((key) => (
                    <Skeleton
                      key={key}
                      variant="rounded"
                      height={52}
                      sx={{ bgcolor: 'surfaceContainerHigh', borderRadius: 1 }}
                    />
                  ))
                ) : availableUsers.length === 0 ? (
                  <Typography
                    variant="bodyData"
                    sx={{ color: 'onSurfaceVariant', py: 2, textAlign: 'center' }}
                  >
                    {catalog.length === 0
                      ? 'No users match your search'
                      : 'All catalog users are already assigned to this role'}
                  </Typography>
                ) : (
                  availableUsers.map((user) => (
                    <UserSelectRow
                      key={user.id}
                      user={user}
                      selected={selectedUserIds.includes(user.id)}
                      onToggle={handleToggleUser}
                    />
                  ))
                )}
              </Stack>
            </Box>
          </Stack>
        )}
      </Box>

      <Box
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'outlineVariant',
          bgcolor: 'surface',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 1,
          flexShrink: 0,
        }}
      >
        <Button
          onClick={handleClose}
          sx={{
            color: 'onSurfaceVariant',
            textTransform: 'none',
            fontWeight: 600,
            border: '1px solid transparent',
            '&:hover': {
              color: 'onSurface',
              bgcolor: 'surfaceContainerHighest',
            },
          }}
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          disabled={!role || selectedUserIds.length === 0 || submitting}
          onClick={() => void handleAssign()}
          startIcon={
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
              check
            </span>
          }
          sx={{
            textTransform: 'none',
            fontWeight: 600,
            bgcolor: 'primaryContainer',
            color: 'onPrimaryContainer',
            boxShadow: 1,
            '&:hover:not(.Mui-disabled)': {
              bgcolor: 'primaryContainer',
              filter: 'brightness(0.92)',
            },
            '&.Mui-disabled': {
              bgcolor: 'surfaceContainerHigh',
              color: 'onSurfaceVariant',
            },
          }}
        >
          Assign Users
        </Button>
      </Box>
    </Drawer>
  )
}

export default AssignUsersToRoleDrawer
