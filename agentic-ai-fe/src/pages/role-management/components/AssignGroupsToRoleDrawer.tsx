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

import { getAdminErrorMessage, isAbortError, roleAdminApi } from '@/api/admin'
import { useAppDispatch } from '@/redux/hooks'
import { setAlert } from '@/redux/reducers/AlertSlice'

import type { ActorGroup, AssignableGroup, Role } from '../types'

const CATALOG_DEBOUNCE_MS = 400

interface AssignGroupsToRoleDrawerProps {
  open: boolean
  role: Role | null
  assignedGroups: ActorGroup[]
  submitting?: boolean
  onClose: () => void
  onAssign: (groupIds: string[]) => void | Promise<void>
}

const GroupItem = styled(Box, {
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

interface GroupSelectRowProps {
  group: AssignableGroup
  selected: boolean
  onToggle: (id: string) => void
}

const GroupSelectRow = ({ group, selected, onToggle }: GroupSelectRowProps) => (
  <GroupItem as="label" selected={selected} onClick={() => onToggle(group.id)}>
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
      onChange={() => onToggle(group.id)}
    />
    <Box sx={{ flex: 1, minWidth: 0 }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 1,
          mb: 0.5,
        }}
      >
        <Typography variant="headlineAgent" sx={{ color: 'onSurface' }} noWrap>
          {group.name}
        </Typography>
        <Box
          sx={{
            flexShrink: 0,
            bgcolor: 'surfaceContainer',
            px: 1,
            py: 0.25,
            borderRadius: 0.5,
          }}
        >
          <Typography variant="labelMono" sx={{ color: 'onSurfaceVariant', fontSize: 10 }}>
            {group.memberCount} members
          </Typography>
        </Box>
      </Box>
      <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant' }}>
        {group.description}
      </Typography>
    </Box>
  </GroupItem>
)

const AssignGroupsToRoleDrawer = ({
  open,
  role,
  assignedGroups,
  submitting = false,
  onClose,
  onAssign,
}: AssignGroupsToRoleDrawerProps) => {
  const dispatch = useAppDispatch()
  const [selectedGroupIds, setSelectedGroupIds] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [catalog, setCatalog] = useState<AssignableGroup[]>([])
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
      .listGroupsCatalog(
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

  const assignedIds = useMemo(
    () => new Set(assignedGroups.map((g) => g.id)),
    [assignedGroups],
  )

  const availableGroups = useMemo(
    () => catalog.filter((g) => !assignedIds.has(g.id)),
    [catalog, assignedIds],
  )

  const handleToggleGroup = (id: string) => {
    setSelectedGroupIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id],
    )
  }

  const handleClose = () => {
    setSelectedGroupIds([])
    setSearchQuery('')
    onClose()
  }

  const handleAssign = async () => {
    if (selectedGroupIds.length === 0) return
    try {
      await onAssign(selectedGroupIds)
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
          Bulk Assign Groups
        </Typography>
        <IconButton onClick={handleClose} size="small" aria-label="Close drawer">
          <span className="material-symbols-outlined">close</span>
        </IconButton>
      </Box>

      <Box sx={{ flex: 1, overflowY: 'auto', p: 2, minHeight: 0 }}>
        {!role ? (
          <Typography variant="bodyMain" sx={{ color: 'onSurfaceVariant' }}>
            Select a role to assign groups
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
                Assigning to group
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
                    Add one or more groups to this role.
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
                Available Groups
              </Typography>
              <TextField
                fullWidth
                size="small"
                placeholder="Search groups..."
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
                ) : availableGroups.length === 0 ? (
                  <Typography
                    variant="bodyData"
                    sx={{ color: 'onSurfaceVariant', py: 2, textAlign: 'center' }}
                  >
                    {catalog.length === 0
                      ? 'No groups match your search'
                      : 'All catalog groups are already assigned to this role'}
                  </Typography>
                ) : (
                  availableGroups.map((group) => (
                    <GroupSelectRow
                      key={group.id}
                      group={group}
                      selected={selectedGroupIds.includes(group.id)}
                      onToggle={handleToggleGroup}
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
          disabled={!role || selectedGroupIds.length === 0 || submitting}
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
          Assign to Groups
        </Button>
      </Box>
    </Drawer>
  )
}

export default AssignGroupsToRoleDrawer
