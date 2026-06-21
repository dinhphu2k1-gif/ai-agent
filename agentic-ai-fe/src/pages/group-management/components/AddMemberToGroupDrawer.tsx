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

import { getAdminErrorMessage, groupAdminApi, isAbortError } from '@/api/admin'
import { useAppDispatch } from '@/redux/hooks'
import { setAlert } from '@/redux/reducers/AlertSlice'

import type { AssignableMember, GroupMember, UserGroup } from '../types'

const CATALOG_DEBOUNCE_MS = 400

interface AddMemberToGroupDrawerProps {
  open: boolean
  group: UserGroup | null
  currentMembers: GroupMember[]
  submitting?: boolean
  onClose: () => void
  onAdd: (memberIds: string[]) => void | Promise<void>
}

const MemberItem = styled(Box, {
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

interface MemberSelectRowProps {
  member: AssignableMember
  selected: boolean
  onToggle: (id: string) => void
}

const MemberSelectRow = ({ member, selected, onToggle }: MemberSelectRowProps) => (
  <MemberItem component="label" selected={selected} onClick={() => onToggle(member.id)}>
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
      onChange={() => onToggle(member.id)}
    />
    <Box sx={{ position: 'relative', flexShrink: 0, mt: 0.25 }}>
      <Avatar
        src={member.avatarUrl}
        sx={{
          width: 36,
          height: 36,
          fontSize: 12,
          border: 1,
          borderColor: 'outlineVariant',
        }}
      >
        {getInitials(member.name)}
      </Avatar>
      {member.isOnline && (
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
        {member.name}
      </Typography>
      <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant' }} noWrap>
        {member.email}
      </Typography>
    </Box>
  </MemberItem>
)

const AddMemberToGroupDrawer = ({
  open,
  group,
  currentMembers,
  submitting = false,
  onClose,
  onAdd,
}: AddMemberToGroupDrawerProps) => {
  const dispatch = useAppDispatch()
  const [selectedMemberIds, setSelectedMemberIds] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [catalog, setCatalog] = useState<AssignableMember[]>([])
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
      .listMembersCatalog(
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

  const assignedIds = useMemo(() => new Set(currentMembers.map((m) => m.id)), [currentMembers])

  const availableMembers = useMemo(
    () => catalog.filter((m) => !assignedIds.has(m.id)),
    [catalog, assignedIds],
  )

  const handleToggleMember = (id: string) => {
    setSelectedMemberIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id],
    )
  }

  const handleClose = () => {
    setSelectedMemberIds([])
    setSearchQuery('')
    onClose()
  }

  const handleAdd = async () => {
    if (selectedMemberIds.length === 0) return
    try {
      await onAdd(selectedMemberIds)
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
          Add Members
        </Typography>
        <IconButton onClick={handleClose} size="small" aria-label="Close drawer">
          <span className="material-symbols-outlined">close</span>
        </IconButton>
      </Box>

      <Box sx={{ flex: 1, overflowY: 'auto', p: 2, minHeight: 0 }}>
        {!group ? (
          <Typography variant="bodyMain" sx={{ color: 'onSurfaceVariant' }}>
            Select a group to add members
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
                Available users
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
                ) : availableMembers.length === 0 ? (
                  <Typography
                    variant="bodyData"
                    sx={{ color: 'onSurfaceVariant', py: 2, textAlign: 'center' }}
                  >
                    {catalog.length === 0
                      ? 'No users match your search'
                      : 'All catalog users are already in this group'}
                  </Typography>
                ) : (
                  availableMembers.map((member) => (
                    <MemberSelectRow
                      key={member.id}
                      member={member}
                      selected={selectedMemberIds.includes(member.id)}
                      onToggle={handleToggleMember}
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
          disabled={!group || selectedMemberIds.length === 0 || submitting}
          onClick={() => void handleAdd()}
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
          Add to group
        </Button>
      </Box>
    </Drawer>
  )
}

export default AddMemberToGroupDrawer
