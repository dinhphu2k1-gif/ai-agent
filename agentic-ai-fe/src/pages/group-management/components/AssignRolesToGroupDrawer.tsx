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
  Skeleton,
  styled,
} from '@mui/material'
import { useEffect, useMemo, useState } from 'react'

import { getAdminErrorMessage, groupAdminApi, isAbortError } from '@/api/admin'
import { useAppDispatch } from '@/redux/hooks'
import { setAlert } from '@/redux/reducers/AlertSlice'

import type { AssignableRoleOption, GroupRoleAssignment, UserGroup } from '../types'

const CATALOG_DEBOUNCE_MS = 400

interface AssignRolesToGroupDrawerProps {
  open: boolean
  group: UserGroup | null
  assignedRoles: GroupRoleAssignment[]
  submitting?: boolean
  onClose: () => void
  onAssign: (roleIds: string[]) => void | Promise<void>
}

const RoleItem = styled(Box, {
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

interface RoleSelectRowProps {
  role: AssignableRoleOption
  selected: boolean
  onToggle: (id: string) => void
}

const RoleSelectRow = ({ role, selected, onToggle }: RoleSelectRowProps) => (
  <RoleItem component="label" selected={selected} onClick={() => onToggle(role.id)}>
    <Checkbox
      checked={selected}
      size="small"
      sx={{
        p: 0,
        mt: 0.25,
        color: 'outline',
        '&.Mui-checked': { color: 'primaryContainer' },
      }}
      onClick={(e) => e.stopPropagation()}
      onChange={() => onToggle(role.id)}
    />
    <Box sx={{ flex: 1, minWidth: 0 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1, mb: 0.5 }}>
        <Typography variant="headlineAgent" sx={{ color: 'onSurface' }} noWrap>
          {role.name}
        </Typography>
        <Box sx={{ flexShrink: 0, bgcolor: 'surfaceContainer', px: 1, py: 0.25, borderRadius: 0.5 }}>
          <Typography variant="labelMono" sx={{ color: 'onSurfaceVariant', fontSize: 10 }}>
            {role.permissionCount} perms
          </Typography>
        </Box>
      </Box>
      <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant' }}>
        {role.description}
      </Typography>
    </Box>
  </RoleItem>
)

const AssignRolesToGroupDrawer = ({
  open,
  group,
  assignedRoles,
  submitting = false,
  onClose,
  onAssign,
}: AssignRolesToGroupDrawerProps) => {
  const dispatch = useAppDispatch()
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [catalog, setCatalog] = useState<AssignableRoleOption[]>([])
  const [catalogLoading, setCatalogLoading] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchQuery), CATALOG_DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [searchQuery])

  useEffect(() => {
    if (!open) return

    const controller = new AbortController()
    setCatalogLoading(true)

    groupAdminApi
      .listRolesCatalog(
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

  const assignedIds = useMemo(() => new Set(assignedRoles.map((r) => r.id)), [assignedRoles])

  const availableRoles = useMemo(
    () => catalog.filter((r) => !assignedIds.has(r.id)),
    [catalog, assignedIds],
  )

  const handleToggleRole = (id: string) => {
    setSelectedRoleIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id],
    )
  }

  const handleClose = () => {
    setSelectedRoleIds([])
    setSearchQuery('')
    onClose()
  }

  const handleAssign = async () => {
    if (selectedRoleIds.length === 0) return
    try {
      await onAssign(selectedRoleIds)
      handleClose()
    } catch {
      // Parent shows toast; keep drawer open
    }
  }

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
          Assign Roles
        </Typography>
        <IconButton onClick={handleClose} size="small" aria-label="Close drawer">
          <span className="material-symbols-outlined">close</span>
        </IconButton>
      </Box>

      <Box sx={{ flex: 1, overflowY: 'auto', p: 2, minHeight: 0 }}>
        {!group ? (
          <Typography variant="bodyMain" sx={{ color: 'onSurfaceVariant' }}>
            Select a group to assign roles
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
                Target group
              </Typography>
              <Box
                sx={{
                  p: 1.5,
                  bgcolor: 'surface',
                  borderRadius: 1,
                  border: 1,
                  borderColor: 'outlineVariant',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.5,
                }}
              >
                <Box
                  sx={{
                    p: 0.75,
                    borderRadius: '50%',
                    bgcolor: 'secondaryContainer',
                    color: 'onSecondaryContainer',
                    display: 'flex',
                  }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                    groups
                  </span>
                </Box>
                <Typography variant="headlineAgent" sx={{ color: 'onSurface' }} noWrap>
                  {group.name}
                </Typography>
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
                Available roles
              </Typography>
              <TextField
                fullWidth
                size="small"
                placeholder="Search roles..."
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
                ) : availableRoles.length === 0 ? (
                  <Typography
                    variant="bodyData"
                    sx={{ color: 'onSurfaceVariant', py: 2, textAlign: 'center' }}
                  >
                    {catalog.length === 0
                      ? 'No roles match your search'
                      : 'All catalog roles are already assigned to this group'}
                  </Typography>
                ) : (
                  availableRoles.map((role) => (
                    <RoleSelectRow
                      key={role.id}
                      role={role}
                      selected={selectedRoleIds.includes(role.id)}
                      onToggle={handleToggleRole}
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
          sx={{ color: 'onSurfaceVariant', textTransform: 'none', fontWeight: 600 }}
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          disabled={!group || selectedRoleIds.length === 0 || submitting}
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
            '&.Mui-disabled': {
              bgcolor: 'surfaceContainerHigh',
              color: 'onSurfaceVariant',
            },
          }}
        >
          Assign roles
        </Button>
      </Box>
    </Drawer>
  )
}

export default AssignRolesToGroupDrawer
